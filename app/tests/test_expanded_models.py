"""
Tests for expanded PlatformContent and PlatformRules models with new text fields.
"""
import pytest
from app.models.platform_rules import get_platform_rules, PlatformType
from app.models.content import PlatformContent


class TestExpandedModels:
    """Tests for the expanded model functionality."""
    
    def test_platform_content_with_new_fields(self):
        """Test that PlatformContent can handle new optional fields."""
        content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Test Video Title",
            tags=["#education", "#tutorial"],
            confidence_score=0.95,
            description="This is a comprehensive tutorial about Python programming for beginners",
            bio="Educational content creator",
            meets_requirements=True
        )
        
        assert content.title == "Test Video Title"
        assert content.description == "This is a comprehensive tutorial about Python programming for beginners"
        assert content.bio == "Educational content creator"
        assert content.description_character_count == 71
        assert content.bio_character_count == 27
        assert content.character_count == 16  # title length
    
    def test_instagram_content_with_caption(self):
        """Test Instagram content with caption field."""
        content = PlatformContent(
            platform=PlatformType.INSTAGRAM,
            title="Amazing sunset photo",
            tags=["#sunset", "#photography", "#nature"],
            confidence_score=0.88,
            caption="Caught this beautiful sunset today! Nature never fails to amaze me 🌅",
            bio="Travel photographer | Nature lover",
            username="nature_shots_daily",
            profile_name="Nature Photography"
        )
        
        assert content.caption_character_count == 68  # Emoji counts as 2 chars
        assert content.bio_character_count == 34
        assert len(content.username) == 18
        assert len(content.profile_name) == 18
    
    def test_linkedin_content_with_professional_fields(self):
        """Test LinkedIn content with professional fields."""
        content = PlatformContent(
            platform=PlatformType.LINKEDIN,
            title="Professional Update",
            tags=["#leadership", "#career"],
            confidence_score=0.92,
            post_body="Excited to share my thoughts on leadership in the modern workplace...",
            headline="Senior Software Engineer | Tech Lead | Mentor",
            about_section="Passionate software engineer with 10+ years of experience in building scalable systems.",
            connection_message="Hi! I'd love to connect and discuss opportunities in tech."
        )
        
        assert content.post_body_character_count == 69
        assert len(content.headline) == 45
        assert len(content.about_section) == 87
        assert len(content.connection_message) == 58
    
    def test_platform_rules_expanded_fields(self):
        """Test that platform rules include the new field limits."""
        youtube_rules = get_platform_rules(PlatformType.YOUTUBE)
        assert youtube_rules.description_max_length == 5000
        assert youtube_rules.description_optimal_length == 157
        assert youtube_rules.bio_max_length == 1000
        
        instagram_rules = get_platform_rules(PlatformType.INSTAGRAM)
        assert instagram_rules.caption_max_length == 2200
        assert instagram_rules.caption_optimal_length == 125
        assert instagram_rules.bio_max_length == 150
        assert instagram_rules.username_max_length == 30
        
        linkedin_rules = get_platform_rules(PlatformType.LINKEDIN)
        assert linkedin_rules.post_max_length == 3000
        assert linkedin_rules.post_optimal_length == 200
        assert linkedin_rules.headline_max_length == 220
        assert linkedin_rules.about_max_length == 2600
    
    def test_validation_with_new_fields(self):
        """Test validation works with new fields."""
        # Test YouTube content that violates description limit
        content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Test Title",
            tags=["#test1", "#test2", "#test3", "#test4", "#test5", 
                  "#test6", "#test7", "#test8", "#test9", "#test10"],
            confidence_score=0.85,
            description="x" * 6000  # Exceeds 5000 char limit
        )
        
        rules = get_platform_rules(PlatformType.YOUTUBE)
        is_valid = content.validate_against_platform_rules(rules)
        
        assert not is_valid
        assert not content.meets_requirements
        assert any("Description exceeds maximum length" in note for note in content.validation_notes)
    
    def test_validation_passes_with_valid_new_fields(self):
        """Test validation passes with valid new fields."""
        content = PlatformContent(
            platform=PlatformType.INSTAGRAM,
            title="Great photo!",
            tags=["#photo"] * 25,  # 25 tags within limit
            confidence_score=0.90,
            caption="Beautiful day for photography! " * 2,  # Well within limit
            bio="Photographer",
            username="test_user"
        )
        
        rules = get_platform_rules(PlatformType.INSTAGRAM)
        is_valid = content.validate_against_platform_rules(rules)
        
        assert is_valid
        assert content.meets_requirements
        assert len(content.validation_notes) == 0
    
    def test_x_twitter_total_character_validation(self):
        """Test X/Twitter total character limit validation with post_body."""
        content = PlatformContent(
            platform=PlatformType.X_TWITTER,
            title="",  # Empty title
            tags=["#tech", "#ai"],
            confidence_score=0.85,
            post_body="This is a test post that should work within limits"
        )
        
        rules = get_platform_rules(PlatformType.X_TWITTER)
        is_valid = content.validate_against_platform_rules(rules)
        
        # Should be valid as total is: 51 + 5 + 3 + 2 spaces = 61 chars (well under 280)
        assert is_valid
        assert content.meets_requirements 