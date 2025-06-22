"""
Tests for Phase 5 Core Business Logic services.
Tests orchestrator and content validation services.
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import pytest
from unittest.mock import Mock, patch, MagicMock
from models.platform_rules import PlatformType
from models.content import VideoTranscript, PlatformContent, BatchGenerationRequest, ContentGenerationOptions
from services.orchestrator import ContentOrchestrator, GenerationResult
from services.content_validator import ContentValidator, ValidationSeverity, ValidationResult


class TestContentOrchestrator:
    """Test content generation orchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly."""
        with patch('services.orchestrator.ContentGeneratorService'):
            with patch('services.orchestrator.PlatformAgentManager'):
                with patch('services.orchestrator.TranscriptProcessor'):
                    orchestrator = ContentOrchestrator()
                    
                    assert orchestrator.max_retries == 3
                    assert orchestrator.timeout_seconds == 30
                    assert orchestrator.content_generator is not None
                    assert orchestrator.platform_agents is not None
                    assert orchestrator.transcript_processor is not None
    
    def test_process_transcript(self):
        """Test transcript processing functionality."""
        transcript = VideoTranscript(
            content="This is a test video about artificial intelligence and machine learning."
        )
        
        with patch('services.orchestrator.ContentGeneratorService'):
            with patch('services.orchestrator.PlatformAgentManager'):
                with patch('services.orchestrator.TranscriptProcessor') as mock_processor_class:
                    # Mock the processor instance
                    mock_processor = Mock()
                    mock_processor.process_transcript.return_value = (transcript, Mock())
                    mock_processor_class.return_value = mock_processor
                    
                    orchestrator = ContentOrchestrator()
                    
                    enhanced_transcript, analysis = orchestrator.process_transcript(transcript)
                    
                    assert enhanced_transcript is not None
                    assert analysis is not None
                    mock_processor.process_transcript.assert_called_once_with(transcript)
    
    def test_generate_content_for_platform_success(self):
        """Test successful content generation for a single platform."""
        transcript = VideoTranscript(
            content="Learn about AI and machine learning in this comprehensive tutorial."
        )
        
        # Mock successful content generation
        mock_content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="AI Tutorial for Beginners",
            tags=["#AI", "#tutorial", "#machinelearning", "#education", "#programming",
                  "#python", "#beginner", "#learn", "#tech", "#coding"],
            confidence_score=0.9
        )
        
        with patch('services.orchestrator.ContentGeneratorService'):
            with patch('services.orchestrator.PlatformAgentManager') as mock_agent_class:
                with patch('services.orchestrator.TranscriptProcessor'):
                    # Mock the agents manager
                    mock_agents = Mock()
                    mock_agents.generate_content.return_value = mock_content
                    mock_agent_class.return_value = mock_agents
                    
                    # Mock content validation using patch
                    with patch.object(PlatformContent, 'validate_against_platform_rules', return_value=True):
                        orchestrator = ContentOrchestrator()
                        result = orchestrator.generate_content_for_platform(
                            PlatformType.YOUTUBE, transcript
                        )
                        
                        assert result.success is True
                        assert result.platform == PlatformType.YOUTUBE
                        assert result.content == mock_content
                        assert result.error is None
    
    def test_generate_content_for_platform_with_retries(self):
        """Test content generation with retry logic."""
        transcript = VideoTranscript(
            content="Test content for retry logic."
        )
        
        with patch('services.orchestrator.ContentGeneratorService'):
            with patch('services.orchestrator.PlatformAgentManager') as mock_agent_class:
                with patch('services.orchestrator.TranscriptProcessor'):
                    with patch('time.sleep'):  # Mock sleep to speed up test
                        # Mock agents to fail twice then succeed
                        mock_agents = Mock()
                        mock_agents.generate_content.side_effect = [
                            Exception("First failure"),
                            Exception("Second failure"),
                            PlatformContent(
                                platform=PlatformType.YOUTUBE,
                                title="Success",
                                tags=["#test"] * 10,
                                confidence_score=0.8
                            )
                        ]
                        mock_agent_class.return_value = mock_agents
                        
                        orchestrator = ContentOrchestrator(max_retries=3)
                        
                        # Mock successful validation on third attempt
                        with patch.object(PlatformContent, 'validate_against_platform_rules', return_value=True):
                            result = orchestrator.generate_content_for_platform(
                                PlatformType.YOUTUBE, transcript
                            )
                        
                        assert result.success is True
                        assert result.retry_count == 2  # Two retries before success
                        assert mock_agents.generate_content.call_count == 3
    
    def test_batch_generation_sequential(self):
        """Test sequential batch content generation."""
        transcript = VideoTranscript(
            content="Test content for batch generation."
        )
        
        request = BatchGenerationRequest(
            transcript=transcript,
            platforms=[PlatformType.YOUTUBE, PlatformType.INSTAGRAM]
        )
        
        # Mock successful content for both platforms
        youtube_content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="YouTube Title",
            tags=["#test"] * 10,
            confidence_score=0.9
        )
        
        instagram_content = PlatformContent(
            platform=PlatformType.INSTAGRAM,
            title="Instagram Caption",
            tags=["#test"] * 25,
            confidence_score=0.85
        )
        
        with patch('services.orchestrator.ContentGeneratorService'):
            with patch('services.orchestrator.PlatformAgentManager') as mock_agent_class:
                with patch('services.orchestrator.TranscriptProcessor') as mock_processor_class:
                    # Mock processor
                    mock_processor = Mock()
                    mock_processor.process_transcript.return_value = (transcript, Mock())
                    mock_processor_class.return_value = mock_processor
                    
                    # Mock agent manager
                    mock_agents = Mock()
                    mock_agents.generate_content.side_effect = [youtube_content, instagram_content]
                    mock_agent_class.return_value = mock_agents
                    
                    # Mock content validation
                    with patch.object(PlatformContent, 'validate_against_platform_rules', return_value=True):
                        orchestrator = ContentOrchestrator()
                        response = orchestrator.generate_batch_content(request, concurrent=False)
                    
                    assert response.success_count == 2
                    assert response.error_count == 0
                    assert len(response.generated_content) == 2
                    assert PlatformType.YOUTUBE.value in response.generated_content
                    assert PlatformType.INSTAGRAM.value in response.generated_content
    
    def test_performance_stats_tracking(self):
        """Test performance statistics tracking."""
        with patch('services.orchestrator.ContentGeneratorService'):
            with patch('services.orchestrator.PlatformAgentManager'):
                with patch('services.orchestrator.TranscriptProcessor'):
                    orchestrator = ContentOrchestrator()
                    
                    # Initially no stats
                    stats = orchestrator.get_performance_stats()
                    assert "No requests processed yet" in stats.get("message", "")
                    
                    # Simulate some statistics
                    orchestrator.generation_stats["total_requests"] = 10
                    orchestrator.generation_stats["successful_generations"] = 8
                    orchestrator.generation_stats["failed_generations"] = 2
                    orchestrator.generation_stats["total_processing_time"] = 50.0
                    
                    stats = orchestrator.get_performance_stats()
                    assert stats["total_requests"] == 10
                    assert stats["average_processing_time"] == 5.0
                    assert stats["overall_success_rate"] == 0.8


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
    
    def test_suggest_improvements(self):
        """Test improvement suggestions generation."""
        content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Short",  # Too short
            tags=["#AI"],  # Too few tags
            confidence_score=0.4  # Low confidence
        )
        
        validator = ContentValidator()
        result = validator.validate_content(content)
        suggestions = validator.suggest_improvements(result)
        
        assert len(suggestions) > 0
        assert any("title" in suggestion.lower() for suggestion in suggestions)
        assert any("tags" in suggestion.lower() for suggestion in suggestions)
    
    def test_create_fallback_content(self):
        """Test fallback content creation."""
        transcript = VideoTranscript(
            content="This is a comprehensive tutorial about artificial intelligence and machine learning applications.",
            title="Original Long Title That Exceeds Character Limits"
        )
        
        # Mock original validation result with issues
        original_validation = Mock()
        original_validation.issues = [
            Mock(field="title", message="character limit exceeded"),
            Mock(field="tags", message="too few tags")
        ]
        
        validator = ContentValidator()
        fallback_content = validator.create_fallback_content(
            PlatformType.YOUTUBE, transcript, original_validation
        )
        
        assert isinstance(fallback_content, PlatformContent)
        assert fallback_content.platform == PlatformType.YOUTUBE
        assert len(fallback_content.title) <= 100  # YouTube limit
        assert len(fallback_content.tags) >= 10   # YouTube minimum
        assert fallback_content.confidence_score < 1.0  # Lower confidence for fallback
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        # High quality content
        good_content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Complete AI Tutorial: Learn Machine Learning from Scratch",  # Good length
            tags=["#AI", "#tutorial", "#machinelearning", "#python", "#programming",
                  "#education", "#beginner", "#tech", "#coding", "#development"],  # Good count
            confidence_score=0.95
        )
        
        # Low quality content
        bad_content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Bad",  # Too short
            tags=["#tag"],  # Too few
            confidence_score=0.3
        )
        
        validator = ContentValidator()
        good_result = validator.validate_content(good_content)
        bad_result = validator.validate_content(bad_content)
        
        assert good_result.score > bad_result.score
        assert good_result.score >= 80  # Should be high quality
        assert bad_result.score < 50   # Should be low quality


def run_phase5_tests():
    """Run all Phase 5 service tests."""
    print("🧪 Running Phase 5 Core Business Logic Tests...\n")
    
    # Test ContentOrchestrator
    print("Testing ContentOrchestrator...")
    try:
        test_orchestrator = TestContentOrchestrator()
        test_orchestrator.test_orchestrator_initialization()
        test_orchestrator.test_process_transcript()
        test_orchestrator.test_generate_content_for_platform_success()
        test_orchestrator.test_generate_content_for_platform_with_retries()
        test_orchestrator.test_batch_generation_sequential()
        test_orchestrator.test_performance_stats_tracking()
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
        test_validator.test_suggest_improvements()
        test_validator.test_create_fallback_content()
        test_validator.test_quality_score_calculation()
        print("✅ ContentValidator Tests - PASSED\n")
    except Exception as e:
        print(f"❌ ContentValidator Tests - FAILED: {e}\n")
        return False
    
    print("🎉 All Phase 5 Core Business Logic Tests PASSED!")
    print("✅ Task 5.1: Content Generation Orchestrator - COMPLETE")
    print("✅ Task 5.2: Content Validation Service - COMPLETE")
    return True


if __name__ == "__main__":
    success = run_phase5_tests()
    if not success:
        exit(1) 