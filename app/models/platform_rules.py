"""
Platform-specific rules and configuration models for social media content generation.
Defines character limits, tag requirements, and content style guidelines for each platform.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ContentStyle(str, Enum):
    """Content style categories for different platforms."""
    EDUCATIONAL_ENTERTAINMENT = "educational_entertainment"
    VISUAL_LIFESTYLE = "visual_lifestyle"
    COMMUNITY_BUILDING = "community_building"
    TREND_FOCUSED = "trend_focused"
    PROFESSIONAL = "professional"
    GAMING_COMMUNITY = "gaming_community"
    CONCISE_TIMELY = "concise_timely"


class PlatformType(str, Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    X_TWITTER = "x_twitter"
    LINKEDIN = "linkedin"
    TWITCH = "twitch"


class PlatformRules(BaseModel):
    """Base model for platform-specific content generation rules."""
    
    platform: PlatformType
    title_max_length: int
    tag_min_count: int
    tag_max_count: int
    content_style: ContentStyle
    style_guidelines: List[str]
    special_requirements: Optional[List[str]] = None
    
    model_config = ConfigDict(use_enum_values=True)


class YouTubeRules(PlatformRules):
    """Content rules for YouTube platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.YOUTUBE,
            title_max_length=100,
            tag_min_count=10,
            tag_max_count=15,
            content_style=ContentStyle.EDUCATIONAL_ENTERTAINMENT,
            style_guidelines=[
                "Engaging and SEO-friendly titles",
                "Balance educational and entertainment value",
                "Use trending keywords for discoverability",
                "Clear, descriptive content that matches video topic"
            ],
            special_requirements=[
                "Focus on trending keywords",
                "Optimize for YouTube search algorithm",
                "Consider video thumbnail compatibility"
            ],
            **data
        )


class InstagramRules(PlatformRules):
    """Content rules for Instagram platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.INSTAGRAM,
            title_max_length=150,
            tag_min_count=20,
            tag_max_count=30,
            content_style=ContentStyle.VISUAL_LIFESTYLE,
            style_guidelines=[
                "Visually appealing and lifestyle-focused",
                "Use mix of popular and niche hashtags",
                "Encourage engagement and interaction",
                "Visual-first content approach"
            ],
            special_requirements=[
                "Hashtag-heavy approach (20-30 tags)",
                "Mix trending and niche hashtags",
                "Consider Instagram Reels format"
            ],
            **data
        )


class FacebookRules(PlatformRules):
    """Content rules for Facebook platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.FACEBOOK,
            title_max_length=255,
            tag_min_count=3,
            tag_max_count=5,
            content_style=ContentStyle.COMMUNITY_BUILDING,
            style_guidelines=[
                "Engagement-focused and shareable",
                "Community-building approach",
                "Moderate hashtag usage",
                "Encourage comments and shares"
            ],
            special_requirements=[
                "Not hashtag-heavy (3-5 only)",
                "Focus on shareability",
                "Encourage community interaction"
            ],
            **data
        )


class TikTokRules(PlatformRules):
    """Content rules for TikTok platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.TIKTOK,
            title_max_length=150,
            tag_min_count=3,
            tag_max_count=5,
            content_style=ContentStyle.TREND_FOCUSED,
            style_guidelines=[
                "Trend-aware and catchy",
                "Gen-Z friendly language",
                "Viral potential focus",
                "Current trend integration"
            ],
            special_requirements=[
                "Use trending hashtags",
                "Consider current TikTok trends",
                "Appeal to younger demographics"
            ],
            **data
        )


class XTwitterRules(PlatformRules):
    """Content rules for X (Twitter) platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.X_TWITTER,
            title_max_length=280,  # Total character limit including hashtags
            tag_min_count=2,
            tag_max_count=3,
            content_style=ContentStyle.CONCISE_TIMELY,
            style_guidelines=[
                "Concise and timely",
                "Conversation-starting",
                "Hashtags integrated into text",
                "Current events awareness"
            ],
            special_requirements=[
                "280 character total limit (including hashtags)",
                "Hashtags integrated into main text",
                "Focus on current conversations"
            ],
            **data
        )


class LinkedInRules(PlatformRules):
    """Content rules for LinkedIn platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.LINKEDIN,
            title_max_length=210,
            tag_min_count=3,
            tag_max_count=5,
            content_style=ContentStyle.PROFESSIONAL,
            style_guidelines=[
                "Professional and thought-leadership focused",
                "Industry-relevant content",
                "Professional networking approach",
                "Value-driven messaging"
            ],
            special_requirements=[
                "Professional tone mandatory",
                "Industry-specific hashtags",
                "Thought leadership angle"
            ],
            **data
        )


class TwitchRules(PlatformRules):
    """Content rules for Twitch platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.TWITCH,
            title_max_length=140,
            tag_min_count=3,
            tag_max_count=8,
            content_style=ContentStyle.GAMING_COMMUNITY,
            style_guidelines=[
                "Gaming and streaming focused",
                "Community-oriented",
                "Interactive content emphasis",
                "Gaming terminology usage"
            ],
            special_requirements=[
                "Gaming categories focus",
                "Community interaction emphasis",
                "Streaming-specific language"
            ],
            **data
        )


# Platform rules instances
PLATFORM_RULES = {
    PlatformType.YOUTUBE: YouTubeRules(),
    PlatformType.INSTAGRAM: InstagramRules(),
    PlatformType.FACEBOOK: FacebookRules(),
    PlatformType.TIKTOK: TikTokRules(),
    PlatformType.X_TWITTER: XTwitterRules(),
    PlatformType.LINKEDIN: LinkedInRules(),
    PlatformType.TWITCH: TwitchRules(),
}


def get_platform_rules(platform: PlatformType) -> PlatformRules:
    """Get rules for a specific platform."""
    return PLATFORM_RULES[platform]


def get_all_platforms() -> List[PlatformType]:
    """Get list of all supported platforms."""
    return list(PlatformType) 