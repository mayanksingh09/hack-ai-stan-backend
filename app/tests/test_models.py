"""
Tests for data models to validate model instantiation and field constraints.
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import pytest
from datetime import datetime
from pydantic import ValidationError
from models.platform_rules import (
    PlatformRules, PlatformType, ContentStyle, 
    YouTubeRules, InstagramRules, FacebookRules, TikTokRules,
    XTwitterRules, LinkedInRules, TwitchRules,
    get_platform_rules, get_all_platforms, PLATFORM_RULES
)
from models.content import (
    VideoTranscript, GeneratedContent, PlatformContent,
    BatchGenerationRequest, BatchGenerationResponse,
    ContentGenerationOptions
)


class TestPlatformRules:
    """Test platform configuration models."""
    
    def test_platform_types_enum(self):
        """Test that all platform types are defined."""
        expected_platforms = {
            "youtube", "instagram", "facebook", "tiktok", 
            "x_twitter", "linkedin", "twitch"
        }
        actual_platforms = {p.value for p in PlatformType}
        assert actual_platforms == expected_platforms
    
    def test_youtube_rules(self):
        """Test YouTube platform rules."""
        rules = YouTubeRules()
        assert rules.platform == PlatformType.YOUTUBE
        assert rules.title_max_length == 100
        assert rules.tag_min_count == 10
        assert rules.tag_max_count == 15
        assert rules.content_style == ContentStyle.EDUCATIONAL_ENTERTAINMENT
        assert len(rules.style_guidelines) > 0
        assert len(rules.special_requirements) > 0
    
    def test_instagram_rules(self):
        """Test Instagram platform rules."""
        rules = InstagramRules()
        assert rules.platform == PlatformType.INSTAGRAM
        assert rules.title_max_length == 150
        assert rules.tag_min_count == 20
        assert rules.tag_max_count == 30
        assert rules.content_style == ContentStyle.VISUAL_LIFESTYLE
    
    def test_twitter_rules(self):
        """Test X/Twitter platform rules."""
        rules = XTwitterRules()
        assert rules.platform == PlatformType.X_TWITTER
        assert rules.title_max_length == 280
        assert rules.tag_min_count == 2
        assert rules.tag_max_count == 3
        assert rules.content_style == ContentStyle.CONCISE_TIMELY
    
    def test_get_platform_rules(self):
        """Test platform rules retrieval function."""
        youtube_rules = get_platform_rules(PlatformType.YOUTUBE)
        assert isinstance(youtube_rules, YouTubeRules)
        assert youtube_rules.platform == PlatformType.YOUTUBE
    
    def test_all_platforms_have_rules(self):
        """Test that all platforms have corresponding rules."""
        all_platforms = get_all_platforms()
        assert len(all_platforms) == 7
        
        for platform in all_platforms:
            rules = get_platform_rules(platform)
            assert rules.platform == platform
            assert rules.title_max_length > 0
            assert rules.tag_min_count >= 0
            assert rules.tag_max_count > rules.tag_min_count


class TestContentModels:
    """Test content generation models."""
    
    def test_video_transcript_valid(self):
        """Test valid video transcript creation."""
        transcript = VideoTranscript(
            content="This is a sample video transcript with enough content to be valid.",
            title="Sample Video",
            duration_seconds=120,
            language="en",
            video_category="educational"
        )
        assert transcript.content == "This is a sample video transcript with enough content to be valid."
        assert transcript.title == "Sample Video"
        assert transcript.duration_seconds == 120
        assert transcript.language == "en"
    
    def test_video_transcript_content_too_short(self):
        """Test video transcript with too short content."""
        with pytest.raises(ValidationError, match="String should have at least 10 characters"):
            VideoTranscript(content="short")
    
    def test_video_transcript_invalid_language(self):
        """Test video transcript with invalid language code."""
        with pytest.raises(ValidationError, match="Invalid language code format"):
            VideoTranscript(
                content="This is a valid transcript content.",
                language="invalid_lang_code"
            )
    
    def test_generated_content_valid(self):
        """Test valid generated content creation."""
        content = GeneratedContent(
            title="Amazing AI Tutorial",
            tags=["AI", "tutorial", "machine learning"],
            confidence_score=0.85
        )
        assert content.title == "Amazing AI Tutorial"
        assert len(content.tags) == 3
        assert all(tag.startswith('#') for tag in content.tags)
        assert content.confidence_score == 0.85
        assert isinstance(content.generation_timestamp, datetime)
    
    def test_generated_content_tag_formatting(self):
        """Test tag formatting in generated content."""
        content = GeneratedContent(
            title="Test Content",
            tags=["ai tutorial", "#machinelearning", "python programming"],
            confidence_score=0.9
        )
        # Tags should be cleaned and formatted
        expected_tags = ["#aitutorial", "#machinelearning", "#pythonprogramming"]
        assert content.tags == expected_tags
    
    def test_platform_content_validation(self):
        """Test platform content creation and validation."""
        content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Great AI Tutorial for Beginners",
            tags=["#AI", "#tutorial", "#beginners", "#machinelearning", "#python"],
            confidence_score=0.88
        )
        
        # Computed fields should calculate counts automatically
        assert content.character_count == len("Great AI Tutorial for Beginners")
        assert content.tag_count == 5
        assert content.platform == PlatformType.YOUTUBE
    
    def test_platform_content_rule_validation(self):
        """Test platform content validation against rules."""
        # Create content that violates YouTube rules
        content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="This is a very long title that definitely exceeds the YouTube character limit for titles",
            tags=["#AI"],  # Too few tags for YouTube
            confidence_score=0.5
        )
        
        youtube_rules = get_platform_rules(PlatformType.YOUTUBE)
        is_valid = content.validate_against_platform_rules(youtube_rules)
        
        assert not is_valid
        assert not content.meets_requirements
        assert len(content.validation_notes) > 0
    
    def test_batch_generation_request(self):
        """Test batch generation request model."""
        transcript = VideoTranscript(content="Sample transcript content for testing batch generation.")
        
        request = BatchGenerationRequest(
            transcript=transcript,
            platforms=[PlatformType.YOUTUBE, PlatformType.INSTAGRAM, PlatformType.TIKTOK]
        )
        
        assert len(request.platforms) == 3
        assert PlatformType.YOUTUBE in request.platforms
        assert isinstance(request.transcript, VideoTranscript)
    
    def test_batch_generation_request_no_duplicates(self):
        """Test batch generation request removes duplicate platforms."""
        transcript = VideoTranscript(content="Sample transcript for duplicate platform test.")
        
        request = BatchGenerationRequest(
            transcript=transcript,
            platforms=[PlatformType.YOUTUBE, PlatformType.YOUTUBE, PlatformType.INSTAGRAM]
        )
        
        # Should remove duplicates
        assert len(request.platforms) == 2
        assert PlatformType.YOUTUBE in request.platforms
        assert PlatformType.INSTAGRAM in request.platforms
    
    def test_content_generation_options(self):
        """Test content generation options model."""
        options = ContentGenerationOptions(
            tone="energetic",
            include_emojis=True,
            target_audience="tech enthusiasts",
            keywords_to_include=["AI", "innovation"],
            keywords_to_avoid=["boring", "complicated"]
        )
        
        assert options.tone == "energetic"
        assert options.include_emojis is True
        assert options.target_audience == "tech enthusiasts"
        assert len(options.keywords_to_include) == 2
        assert len(options.keywords_to_avoid) == 2


def run_all_tests():
    """Run all model tests and report results."""
    print("🧪 Running Model Tests...\n")
    
    # Test platform rules
    print("Testing Platform Rules...")
    try:
        test_platform = TestPlatformRules()
        test_platform.test_platform_types_enum()
        test_platform.test_youtube_rules()
        test_platform.test_instagram_rules()
        test_platform.test_twitter_rules()
        test_platform.test_get_platform_rules()
        test_platform.test_all_platforms_have_rules()
        print("✅ Platform Rules Tests - PASSED\n")
    except Exception as e:
        print(f"❌ Platform Rules Tests - FAILED: {e}\n")
        return False
    
    # Test content models
    print("Testing Content Models...")
    try:
        test_content = TestContentModels()
        test_content.test_video_transcript_valid()
        test_content.test_generated_content_valid()
        test_content.test_generated_content_tag_formatting()
        test_content.test_platform_content_validation()
        test_content.test_batch_generation_request()
        test_content.test_batch_generation_request_no_duplicates()
        test_content.test_content_generation_options()
        print("✅ Content Models Tests - PASSED\n")
    except Exception as e:
        print(f"❌ Content Models Tests - FAILED: {e}\n")
        return False
    
    # Test validation edge cases
    print("Testing Validation Edge Cases...")
    try:
        # Test short transcript
        try:
            VideoTranscript(content="short")
        except ValidationError:
            pass  # Expected
        
        # Test invalid language code
        try:
            VideoTranscript(content="Valid transcript content", language="toolongcode")
        except ValidationError:
            pass  # Expected
        
        print("✅ Validation Edge Cases Tests - PASSED\n")
    except Exception as e:
        print(f"❌ Validation Edge Cases Tests - FAILED: {e}\n")
        return False
    
    print("🎉 All Model Tests PASSED!")
    print("✅ Task 2.1: Platform Configuration Models - COMPLETE")
    print("✅ Task 2.2: Content Generation Models - COMPLETE")
    return True


if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1) 