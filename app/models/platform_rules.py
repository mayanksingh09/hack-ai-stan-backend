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
    
    # Optional text field limits - platforms can override these
    description_max_length: Optional[int] = None
    caption_max_length: Optional[int] = None
    post_max_length: Optional[int] = None
    bio_max_length: Optional[int] = None
    username_max_length: Optional[int] = None
    profile_name_max_length: Optional[int] = None
    comments_max_length: Optional[int] = None
    headline_max_length: Optional[int] = None
    about_max_length: Optional[int] = None
    connection_message_max_length: Optional[int] = None
    stream_category_max_length: Optional[int] = None
    
    # Optimal lengths for better engagement
    title_optimal_length: Optional[int] = None
    description_optimal_length: Optional[int] = None
    caption_optimal_length: Optional[int] = None
    post_optimal_length: Optional[int] = None
    
    model_config = ConfigDict(use_enum_values=True)


class YouTubeRules(PlatformRules):
    """Content rules for YouTube platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.YOUTUBE,
            title_max_length=100,
            title_optimal_length=70,
            description_max_length=5000,
            description_optimal_length=157,
            bio_max_length=1000,
            comments_max_length=10000,
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
                "Consider video thumbnail compatibility",
                "Title truncated after 70 chars in search results",
                "Description preview shows first 157 chars"
            ],
            **data
        )


class InstagramRules(PlatformRules):
    """Content rules for Instagram platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.INSTAGRAM,
            title_max_length=150,  # Keep existing for backwards compatibility
            caption_max_length=2200,
            caption_optimal_length=125,
            bio_max_length=150,
            username_max_length=30,
            profile_name_max_length=30,
            comments_max_length=2200,
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
                "Consider Instagram Reels format",
                "Caption truncated after 125 chars with 'more' button",
                "Max 30 hashtags per post, optimal 5-10 for engagement"
            ],
            **data
        )


class FacebookRules(PlatformRules):
    """Content rules for Facebook platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.FACEBOOK,
            title_max_length=255,  # Keep existing for backwards compatibility
            post_max_length=63206,
            post_optimal_length=80,
            bio_max_length=255,  # Page description
            headline_max_length=40,  # Ad headline
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
                "Encourage community interaction",
                "Posts ≤80 chars get 66% higher engagement",
                "Algorithm favors shorter posts in news feed"
            ],
            **data
        )


class TikTokRules(PlatformRules):
    """Content rules for TikTok platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.TIKTOK,
            title_max_length=150,  # Keep existing for backwards compatibility
            caption_max_length=2200,
            bio_max_length=80,
            username_max_length=24,
            comments_max_length=150,
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
                "Appeal to younger demographics",
                "Max 30 hashtags within caption limit",
                "Optimal 3-5 hashtags for engagement"
            ],
            **data
        )


class XTwitterRules(PlatformRules):
    """Content rules for X (Twitter) platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.X_TWITTER,
            title_max_length=280,  # Total character limit including hashtags
            post_max_length=280,  # Free users
            post_optimal_length=100,  # 17% higher engagement under 100 chars
            bio_max_length=160,
            username_max_length=15,
            profile_name_max_length=50,
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
                "Focus on current conversations",
                "Emojis count as 2 characters",
                "URLs count as 23 characters regardless of length",
                "Premium users get 25,000 character limit"
            ],
            **data
        )


class LinkedInRules(PlatformRules):
    """Content rules for LinkedIn platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.LINKEDIN,
            title_max_length=210,  # Keep existing for backwards compatibility
            post_max_length=3000,
            post_optimal_length=200,
            headline_max_length=220,
            about_max_length=2600,
            comments_max_length=1250,
            connection_message_max_length=300,
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
                "Thought leadership angle",
                "Posts truncated at ~200 chars with 'See more'",
                "Professional keywords important for search"
            ],
            **data
        )


class TwitchRules(PlatformRules):
    """Content rules for Twitch platform."""
    
    def __init__(self, **data):
        super().__init__(
            platform=PlatformType.TWITCH,
            title_max_length=140,  # Stream title
            bio_max_length=300,  # Channel description/about
            stream_category_max_length=50,  # Game/category selection
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
                "Streaming-specific language",
                "Stream title should be descriptive of content",
                "Category selection affects discoverability"
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