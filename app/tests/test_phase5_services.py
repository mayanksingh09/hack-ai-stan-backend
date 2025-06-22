"""
Tests for Phase 5 Core Business Logic services - simplified version.
Tests the simplified orchestrator and content validation services.
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import pytest
import asyncio
from unittest.mock import Mock, patch
from pydantic_ai import models
from pydantic_ai.models.test import TestModel
from models.platform_rules import PlatformType
from models.content import VideoTranscript, PlatformContent
from services.orchestrator import ContentOrchestrator
from services.content_validator import ContentValidator, ValidationSeverity, ValidationResult

# Configure Pydantic AI for testing
models.ALLOW_MODEL_REQUESTS = False

# Use pytest-asyncio for async tests
pytestmark = pytest.mark.asyncio


class TestContentOrchestrator:
    """Test simplified content generation orchestrator."""
    
    async def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly."""
        orchestrator = ContentOrchestrator()
        
        assert orchestrator.model_name == "gpt-4o"
        assert orchestrator.agent is not None
    
    async def test_generate_content_success(self):
        """Test successful content generation using TestModel."""
        transcript = VideoTranscript(
            content="Learn about AI and machine learning in this comprehensive tutorial."
        )
        
        orchestrator = ContentOrchestrator()
        
        # Create custom TestModel output in JSON format that will parse correctly
        test_output = """
        ```json
        {
          "title": "Complete AI Tutorial: Master Machine Learning",
          "description": "Learn about AI and machine learning in this comprehensive tutorial covering all the essential concepts.",
          "tags": ["#AI", "#MachineLearning", "#Tutorial", "#Python", "#Programming", "#Education", "#Technology", "#Coding", "#DataScience", "#Development", "#Learning", "#Tech"]
        }
        ```
        """
        
        test_model = TestModel(custom_output_text=test_output)
        
        # Override the agent with TestModel
        with orchestrator.agent.override(model=test_model):
            content = await orchestrator.generate_content(PlatformType.YOUTUBE, transcript)
            
            assert isinstance(content, PlatformContent)
            assert content.platform == PlatformType.YOUTUBE
            assert "AI Tutorial" in content.title
            assert len(content.tags) >= 10  # YouTube requires 10-15 tags
            assert content.confidence_score > 0.5
    
    async def test_generate_content_fallback(self):
        """Test fallback content generation when AI fails."""
        transcript = VideoTranscript(
            content="Test transcript for error handling."
        )
        
        orchestrator = ContentOrchestrator()
        
        # Mock the agent to raise an exception
        with patch.object(orchestrator.agent, 'run', side_effect=Exception("AI service error")):
            content = await orchestrator.generate_content(PlatformType.INSTAGRAM, transcript)
            
            # Should return fallback content
            assert isinstance(content, PlatformContent)
            assert content.platform == PlatformType.INSTAGRAM
            assert content.title == "Instagram Post"
            assert len(content.tags) >= 1
            assert content.confidence_score < 0.5  # Low confidence for fallback
    
    async def test_generate_content_different_platforms(self):
        """Test content generation for different platforms."""
        transcript = VideoTranscript(
            content="This video covers web development with modern frameworks."
        )
        
        orchestrator = ContentOrchestrator()
        
        # Test outputs for different platforms in JSON format
        platform_outputs = {
            PlatformType.YOUTUBE: """
            ```json
            {
              "title": "Web Development Tutorial: Modern Frameworks Guide",
              "description": "Master modern web development frameworks in this comprehensive guide covering React, Vue, Angular and more.",
              "tags": ["#WebDevelopment", "#Programming", "#JavaScript", "#React", "#Vue", "#Angular", "#Tutorial", "#Coding", "#Frontend", "#Backend", "#FullStack", "#Tech"]
            }
            ```
            """,
            PlatformType.INSTAGRAM: """
            {
              "title": "Modern Web Dev Magic ✨🚀",
              "caption": "Ready to level up your web dev skills? This tutorial covers the hottest frameworks! 🔥💻",
              "tags": [""" + ", ".join([f'"#tag{i}"' for i in range(1, 26)]) + """]
            }
            """,
            PlatformType.TIKTOK: """
            {
              "title": "Web Dev in 60 seconds! 🔥",
              "caption": "Quick web development tips and tricks! Follow for more coding content 💻✨",
              "tags": ["#WebDev", "#Coding", "#TechTok", "#Programming"]
            }
            """
        }
        
        for platform, output in platform_outputs.items():
            test_model = TestModel(custom_output_text=output)
            
            with orchestrator.agent.override(model=test_model):
                content = await orchestrator.generate_content(platform, transcript)
                
                assert content.platform == platform
                assert len(content.title) > 0
                assert len(content.tags) > 0


class TestContentValidator:
    """Test content validation service."""
    
    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        validator = ContentValidator()
        assert validator.quality_weights is not None
        assert len(validator.quality_weights) == 5
    
    def test_validate_content_success(self):
        """Test successful content validation."""
        content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Great AI Tutorial for Beginners",
            tags=["#AI", "#tutorial", "#programming", "#machinelearning", 
                  "#python", "#development", "#coding", "#tech", "#beginners", "#education"],
            confidence_score=0.9
        )
        
        validator = ContentValidator()
        result = validator.validate_content(content)
        
        assert isinstance(result, ValidationResult)
        assert result.platform == PlatformType.YOUTUBE
        assert result.content == content
        # Should be valid since it meets YouTube requirements
        assert result.is_valid is True
        assert result.score > 70  # Should have a good score
    
    def test_validate_content_character_limit_violation(self):
        """Test validation with character limit violation."""
        content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="This is an extremely long title that definitely exceeds the YouTube character limit for titles and should trigger a validation error",  # >100 chars
            tags=["#AI"] * 12,  # Valid tag count
            confidence_score=0.8
        )
        
        validator = ContentValidator()
        result = validator.validate_content(content)
        
        assert result.is_valid is False
        assert any(issue.severity == ValidationSeverity.ERROR for issue in result.issues)
        # Check for the actual error message
        assert any("exceeds maximum length" in issue.message.lower() for issue in result.issues)
    
    def test_validate_content_tag_count_issues(self):
        """Test validation with tag count issues."""
        # Too few tags for YouTube
        content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Valid Title",
            tags=["#AI", "#tutorial"],  # Only 2 tags, YouTube needs 10-15
            confidence_score=0.8
        )
        
        validator = ContentValidator()
        result = validator.validate_content(content)
        
        assert result.is_valid is False
        assert any(issue.field == "tags" and issue.severity == ValidationSeverity.ERROR 
                  for issue in result.issues)
        assert any("few tags" in issue.message.lower() for issue in result.issues)
    
    def test_validate_platform_specific_linkedin(self):
        """Test LinkedIn-specific validation (professional tone)."""
        content = PlatformContent(
            platform=PlatformType.LINKEDIN,
            title="Hey guys! This is awesome! OMG check this out!",  # Too casual for LinkedIn
            tags=["#professional", "#business", "#career"],
            confidence_score=0.8
        )
        
        validator = ContentValidator()
        result = validator.validate_content(content)
        
        # Should have warnings about casual language
        assert any(issue.field == "tone" for issue in result.issues)
        assert any("casual" in issue.message.lower() for issue in result.issues)
    
    def test_validate_platform_specific_twitter(self):
        """Test X/Twitter-specific validation (total character limit)."""
        content = PlatformContent(
            platform=PlatformType.X_TWITTER,
            title="This is a very long tweet that when combined with hashtags will definitely exceed the 280 character limit that Twitter enforces for all content including both the main text and any hashtags that are included in the post content",  # Long title
            tags=["#verylonghashtag", "#anotherlonghashtag", "#yetanotherlonghashtag"],  # Added third tag to exceed limit
            confidence_score=0.8
        )
        
        validator = ContentValidator()
        result = validator.validate_content(content)
        
        # Should fail due to total character limit
        assert result.is_valid is False
        assert any("total" in issue.message.lower() and ("character" in issue.message.lower() or "content" in issue.message.lower()) 
                  for issue in result.issues)


async def run_phase5_tests():
    """Run all Phase 5 service tests."""
    print("🧪 Running Phase 5 Simplified Tests...\n")
    
    # Test ContentOrchestrator
    print("Testing ContentOrchestrator...")
    try:
        test_orchestrator = TestContentOrchestrator()
        await test_orchestrator.test_orchestrator_initialization()
        await test_orchestrator.test_generate_content_success()
        await test_orchestrator.test_generate_content_fallback()
        await test_orchestrator.test_generate_content_different_platforms()
        print("✅ ContentOrchestrator Tests - PASSED\n")
    except Exception as e:
        print(f"❌ ContentOrchestrator Tests - FAILED: {e}\n")
        return False
    
    # Test ContentValidator
    print("Testing ContentValidator...")
    try:
        test_validator = TestContentValidator()
        test_validator.test_validator_initialization()
        test_validator.test_validate_content_success()
        test_validator.test_validate_content_character_limit_violation()
        test_validator.test_validate_content_tag_count_issues()
        test_validator.test_validate_platform_specific_linkedin()
        test_validator.test_validate_platform_specific_twitter()
        print("✅ ContentValidator Tests - PASSED\n")
    except Exception as e:
        print(f"❌ ContentValidator Tests - FAILED: {e}\n")
        return False
    
    print("🎉 All Phase 5 Simplified Tests PASSED!")
    return True


if __name__ == "__main__":
    success = asyncio.run(run_phase5_tests())
    if not success:
        exit(1) 