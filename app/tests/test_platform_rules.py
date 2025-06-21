"""
Comprehensive tests for platform-specific content rules and validation.
Tests character limits, tag constraints, and content style enforcement.
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import pytest
from models.platform_rules import (
    PlatformType, get_platform_rules, 
    YouTubeRules, InstagramRules, FacebookRules, TikTokRules,
    XTwitterRules, LinkedInRules, TwitchRules
)
from models.content import PlatformContent


class TestYouTubeRules:
    """Test YouTube platform-specific content rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = YouTubeRules()
        
    def test_youtube_character_limits(self):
        """Test YouTube title character limit enforcement."""
        # Valid title (within 100 characters)
        valid_content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="How to Build AI Applications: Complete Tutorial for Beginners in 2024",  # 70 chars
            tags=["#AI", "#tutorial", "#programming", "#machinelearning", 
                  "#python", "#development", "#coding", "#tech", "#beginners", "#2024"],
            confidence_score=0.9
        )
        
        assert valid_content.character_count <= self.rules.title_max_length
        assert valid_content.validate_against_platform_rules(self.rules) == True
        
        # Invalid title (exceeds 100 characters)
        invalid_content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="This is an extremely long YouTube title that definitely exceeds the 100 character limit for YouTube videos",  # 107 chars
            tags=["#AI"] * 12,  # Valid tag count
            confidence_score=0.8
        )
        
        assert invalid_content.character_count > self.rules.title_max_length
        assert invalid_content.validate_against_platform_rules(self.rules) == False
        assert any("exceeds maximum length" in note for note in invalid_content.validation_notes)
    
    def test_youtube_tag_count_constraints(self):
        """Test YouTube tag count requirements (10-15 tags)."""
        # Valid tag count (12 tags)
        valid_content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Great AI Tutorial",
            tags=["#AI", "#tutorial", "#programming", "#machinelearning", 
                  "#python", "#development", "#coding", "#tech", "#beginners", 
                  "#education", "#learning", "#software"],
            confidence_score=0.9
        )
        
        assert self.rules.tag_min_count <= valid_content.tag_count <= self.rules.tag_max_count
        assert valid_content.validate_against_platform_rules(self.rules) == True
        
        # Too few tags (8 tags)
        too_few_tags = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="AI Tutorial",
            tags=["#AI", "#tutorial", "#programming", "#machinelearning", 
                  "#python", "#development", "#coding", "#tech"],
            confidence_score=0.8
        )
        
        assert too_few_tags.tag_count < self.rules.tag_min_count
        assert too_few_tags.validate_against_platform_rules(self.rules) == False
        assert any("Too few tags" in note for note in too_few_tags.validation_notes)
        
        # Too many tags (18 tags)
        too_many_tags = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="AI Tutorial",
            tags=["#AI", "#tutorial", "#programming", "#machinelearning", 
                  "#python", "#development", "#coding", "#tech", "#beginners",
                  "#education", "#learning", "#software", "#data", "#science",
                  "#analytics", "#deep", "#neural", "#networks"],
            confidence_score=0.8
        )
        
        assert too_many_tags.tag_count > self.rules.tag_max_count
        assert too_many_tags.validate_against_platform_rules(self.rules) == False
        assert any("Too many tags" in note for note in too_many_tags.validation_notes)
    
    def test_youtube_content_style_guidelines(self):
        """Test YouTube content style requirements."""
        assert "educational" in str(self.rules.content_style).lower()
        assert "entertainment" in str(self.rules.content_style).lower()
        assert len(self.rules.style_guidelines) >= 3
        assert len(self.rules.special_requirements) >= 2
        
        # Check key guidelines are present
        guidelines_text = " ".join(self.rules.style_guidelines).lower()
        assert "seo" in guidelines_text or "search" in guidelines_text
        assert "trending" in guidelines_text or "keyword" in guidelines_text


class TestInstagramRules:
    """Test Instagram platform-specific content rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = InstagramRules()
    
    def test_instagram_character_limits(self):
        """Test Instagram caption character limit (150 chars)."""
        # Valid caption
        valid_content = PlatformContent(
            platform=PlatformType.INSTAGRAM,
            title="Amazing sunset vibes! 🌅 Perfect way to end the day with nature's beauty. What's your favorite time to watch sunsets?",  # 128 chars
            tags=["#sunset", "#nature", "#photography", "#vibes", "#golden",
                  "#beautiful", "#peaceful", "#evening", "#sky", "#colors"] * 3,  # 30 tags
            confidence_score=0.9
        )
        
        assert valid_content.character_count <= self.rules.title_max_length
        assert valid_content.validate_against_platform_rules(self.rules) == True
    
    def test_instagram_hashtag_requirements(self):
        """Test Instagram hashtag requirements (20-30 hashtags)."""
        # Valid hashtag count (25 tags)
        valid_content = PlatformContent(
            platform=PlatformType.INSTAGRAM,
            title="Beautiful sunset!",
            tags=["#sunset", "#nature", "#photography", "#vibes", "#golden",
                  "#beautiful", "#peaceful", "#evening", "#sky", "#colors",
                  "#landscape", "#travel", "#wanderlust", "#explore", "#adventure",
                  "#outdoor", "#scenic", "#breathtaking", "#amazing", "#stunning",
                  "#picoftheday", "#photooftheday", "#instagood", "#love", "#life"],
            confidence_score=0.9
        )
        
        assert self.rules.tag_min_count <= valid_content.tag_count <= self.rules.tag_max_count
        assert valid_content.validate_against_platform_rules(self.rules) == True
    
    def test_instagram_content_style(self):
        """Test Instagram visual-lifestyle content style."""
        assert "visual" in str(self.rules.content_style).lower()
        assert "lifestyle" in str(self.rules.content_style).lower()
        
        guidelines_text = " ".join(self.rules.style_guidelines).lower()
        assert "visual" in guidelines_text
        assert "hashtag" in guidelines_text


class TestFacebookRules:
    """Test Facebook platform-specific content rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = FacebookRules()
    
    def test_facebook_character_limits(self):
        """Test Facebook post character limit (255 chars)."""
        # Valid post (200 chars)
        valid_content = PlatformContent(
            platform=PlatformType.FACEBOOK,
            title="Join our amazing community of learners! We're excited to share knowledge, support each other, and grow together. What topics would you like to explore with us?",  # 168 chars
            tags=["#community", "#learning", "#growth", "#support"],
            confidence_score=0.9
        )
        
        assert valid_content.character_count <= self.rules.title_max_length
        assert valid_content.validate_against_platform_rules(self.rules) == True
    
    def test_facebook_minimal_hashtags(self):
        """Test Facebook minimal hashtag approach (3-5 hashtags)."""
        # Valid hashtag count (4 tags)
        valid_content = PlatformContent(
            platform=PlatformType.FACEBOOK,
            title="Great community event!",
            tags=["#community", "#event", "#networking", "#growth"],
            confidence_score=0.9
        )
        
        assert self.rules.tag_min_count <= valid_content.tag_count <= self.rules.tag_max_count
        assert valid_content.validate_against_platform_rules(self.rules) == True


class TestTikTokRules:
    """Test TikTok platform-specific content rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = TikTokRules()
    
    def test_tiktok_character_limits(self):
        """Test TikTok caption character limit (150 chars)."""
        # Valid caption with trendy language
        valid_content = PlatformContent(
            platform=PlatformType.TIKTOK,
            title="This AI hack is absolutely mind-blowing! 🤯 You won't believe how easy it is to automate your workflow ✨",  # 104 chars
            tags=["#AIhack", "#productivity", "#trending"],
            confidence_score=0.9
        )
        
        assert valid_content.character_count <= self.rules.title_max_length
        assert valid_content.validate_against_platform_rules(self.rules) == True
    
    def test_tiktok_trending_focus(self):
        """Test TikTok trending and Gen-Z focused content style."""
        assert "trend" in str(self.rules.content_style).lower()
        
        guidelines_text = " ".join(self.rules.style_guidelines).lower()
        assert "trend" in guidelines_text
        assert "gen-z" in guidelines_text or "viral" in guidelines_text


class TestXTwitterRules:
    """Test X (Twitter) platform-specific content rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = XTwitterRules()
    
    def test_twitter_total_character_limit(self):
        """Test X/Twitter total character limit including hashtags (280 chars)."""
        # Valid tweet with hashtags within limit
        valid_content = PlatformContent(
            platform=PlatformType.X_TWITTER,
            title="Just discovered an amazing AI tool that's revolutionizing content creation! The possibilities are endless when technology meets creativity. What's your favorite AI application?",  # 182 chars
            tags=["#AI", "#tech"],  # ~8 additional chars with spaces
            confidence_score=0.9
        )
        
        # Validate against special Twitter rule (total character limit)
        is_valid = valid_content.validate_against_platform_rules(self.rules)
        total_chars = len(valid_content.title) + sum(len(tag) + 1 for tag in valid_content.tags)
        
        assert total_chars <= self.rules.title_max_length
        assert is_valid == True
    
    def test_twitter_hashtag_integration(self):
        """Test X/Twitter hashtag integration requirements."""
        guidelines_text = " ".join(self.rules.style_guidelines).lower()
        assert "hashtag" in guidelines_text
        assert "integrated" in guidelines_text or "conversation" in guidelines_text


class TestLinkedInRules:
    """Test LinkedIn platform-specific content rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = LinkedInRules()
    
    def test_linkedin_professional_tone(self):
        """Test LinkedIn professional content requirements."""
        # Valid professional post
        valid_content = PlatformContent(
            platform=PlatformType.LINKEDIN,
            title="Excited to share insights from our latest industry research on AI adoption in enterprise environments.",  # 109 chars
            tags=["#AI", "#enterprise", "#research", "#innovation"],
            confidence_score=0.9
        )
        
        assert valid_content.character_count <= self.rules.title_max_length
        assert valid_content.validate_against_platform_rules(self.rules) == True
    
    def test_linkedin_professional_style(self):
        """Test LinkedIn professional content style requirements."""
        assert "professional" in str(self.rules.content_style).lower()
        
        guidelines_text = " ".join(self.rules.style_guidelines).lower()
        assert "professional" in guidelines_text
        assert "industry" in guidelines_text or "thought" in guidelines_text


class TestTwitchRules:
    """Test Twitch platform-specific content rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = TwitchRules()
    
    def test_twitch_gaming_focus(self):
        """Test Twitch gaming and streaming content requirements."""
        # Valid gaming stream title
        valid_content = PlatformContent(
            platform=PlatformType.TWITCH,
            title="Epic AI vs Human showdown! Come watch the ultimate coding battle live!",  # 75 chars
            tags=["#gaming", "#AI", "#coding", "#live", "#battle"],
            confidence_score=0.9
        )
        
        assert valid_content.character_count <= self.rules.title_max_length
        assert valid_content.validate_against_platform_rules(self.rules) == True
    
    def test_twitch_gaming_community_style(self):
        """Test Twitch gaming community content style."""
        assert "gaming" in str(self.rules.content_style).lower()
        
        guidelines_text = " ".join(self.rules.style_guidelines).lower()
        assert "gaming" in guidelines_text
        assert "community" in guidelines_text or "interactive" in guidelines_text


def run_platform_tests():
    """Run all platform-specific rule tests."""
    print("🧪 Running Platform-Specific Rule Tests...\n")
    
    test_classes = [
        TestYouTubeRules,
        TestInstagramRules, 
        TestFacebookRules,
        TestTikTokRules,
        TestXTwitterRules,
        TestLinkedInRules,
        TestTwitchRules
    ]
    
    for test_class in test_classes:
        platform_name = test_class.__name__.replace("Test", "").replace("Rules", "")
        print(f"Testing {platform_name}...")
        
        try:
            test_instance = test_class()
            test_instance.setup_method()
            
            # Run all test methods
            for method_name in dir(test_instance):
                if method_name.startswith('test_'):
                    getattr(test_instance, method_name)()
            
            print(f"✅ {platform_name} Rules Tests - PASSED")
            
        except Exception as e:
            print(f"❌ {platform_name} Rules Tests - FAILED: {e}")
            return False
        
        print()
    
    print("🎉 All Platform-Specific Rule Tests PASSED!")
    print("✅ Phase 3: Platform-Specific Content Rules - COMPLETE")
    return True


if __name__ == "__main__":
    success = run_platform_tests()
    if not success:
        exit(1) 