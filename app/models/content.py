"""
Content generation models for video transcript processing and social media content output.
Defines input/output structures for the AI content generation API.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, computed_field
from datetime import datetime
from .platform_rules import PlatformType


class VideoTranscript(BaseModel):
    """Input model for video transcript content."""
    
    content: str = Field(..., description="The full video transcript text", min_length=10)
    title: Optional[str] = Field(None, description="Original video title (if available)")
    duration_seconds: Optional[int] = Field(None, description="Video duration in seconds", ge=0)
    language: str = Field(default="en", description="Language code (ISO 639-1)")
    video_category: Optional[str] = Field(None, description="Video category or topic")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('content')
    def validate_content_length(cls, v):
        """Ensure transcript content is not too short or excessively long."""
        if len(v.strip()) < 10:
            raise ValueError("Transcript content too short (minimum 10 characters)")
        if len(v) > 50000:  # ~50KB text limit
            raise ValueError("Transcript content too long (maximum 50,000 characters)")
        return v.strip()
    
    @field_validator('language')
    def validate_language_code(cls, v):
        """Basic language code validation."""
        if len(v) not in [2, 5]:  # Accept 'en' or 'en-US' format
            raise ValueError("Invalid language code format")
        return v.lower()


class GeneratedContent(BaseModel):
    """Output model for generated social media content."""
    
    title: str = Field(..., description="Generated title/caption")
    tags: List[str] = Field(..., description="Generated hashtags/tags")
    confidence_score: float = Field(..., description="AI confidence score (0-1)", ge=0, le=1)
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('tags')
    def validate_tags_format(cls, v):
        """Ensure tags are properly formatted."""
        cleaned_tags = []
        for tag in v:
            tag = tag.strip()
            if tag:
                # Ensure hashtag format
                if not tag.startswith('#'):
                    tag = f"#{tag}"
                # Remove spaces and special chars except underscores
                tag = ''.join(char for char in tag if char.isalnum() or char in ['#', '_'])
                if len(tag) > 1:  # Must have content after #
                    cleaned_tags.append(tag)
        return cleaned_tags
    
    @field_validator('title')
    def validate_title_not_empty(cls, v):
        """Ensure title is not empty."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class PlatformContent(BaseModel):
    """Platform-specific generated content with validation against platform rules."""
    
    platform: PlatformType
    title: str
    tags: List[str]
    confidence_score: float = Field(ge=0, le=1)
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    meets_requirements: bool = Field(default=False, description="Whether content meets platform requirements")
    validation_notes: Optional[List[str]] = Field(default_factory=list, description="Validation notes or warnings")
    
    # Optional platform-specific text fields
    description: Optional[str] = Field(None, description="Long-form description (YouTube, etc.)")
    caption: Optional[str] = Field(None, description="Post caption (Instagram, TikTok, etc.)")
    post_body: Optional[str] = Field(None, description="Main post text (Facebook, LinkedIn, X, etc.)")
    bio: Optional[str] = Field(None, description="Profile bio/about section")
    username: Optional[str] = Field(None, description="Suggested username")
    profile_name: Optional[str] = Field(None, description="Profile display name")
    headline: Optional[str] = Field(None, description="Professional headline (LinkedIn) or ad headline (Facebook)")
    about_section: Optional[str] = Field(None, description="About section (LinkedIn)")
    connection_message: Optional[str] = Field(None, description="LinkedIn connection message")
    stream_category: Optional[str] = Field(None, description="Twitch stream category")
    
    @computed_field
    @property
    def character_count(self) -> int:
        """Calculate character count from title."""
        return len(self.title)
    
    @computed_field
    @property
    def tag_count(self) -> int:
        """Calculate tag count from tags list."""
        return len(self.tags)
    
    @computed_field
    @property
    def description_character_count(self) -> int:
        """Calculate character count from description."""
        return len(self.description) if self.description else 0
    
    @computed_field
    @property
    def caption_character_count(self) -> int:
        """Calculate character count from caption."""
        return len(self.caption) if self.caption else 0
    
    @computed_field
    @property
    def post_body_character_count(self) -> int:
        """Calculate character count from post body."""
        return len(self.post_body) if self.post_body else 0
    
    @computed_field
    @property
    def bio_character_count(self) -> int:
        """Calculate character count from bio."""
        return len(self.bio) if self.bio else 0
    
    def validate_against_platform_rules(self, rules) -> bool:
        """Validate content against specific platform rules."""
        validation_notes = []
        meets_requirements = True
        
        # Check title length
        if self.character_count > rules.title_max_length:
            meets_requirements = False
            validation_notes.append(f"Title exceeds maximum length ({self.character_count}/{rules.title_max_length})")
        
        # Check description length
        if self.description and rules.description_max_length:
            if len(self.description) > rules.description_max_length:
                meets_requirements = False
                validation_notes.append(f"Description exceeds maximum length ({len(self.description)}/{rules.description_max_length})")
        
        # Check caption length
        if self.caption and rules.caption_max_length:
            if len(self.caption) > rules.caption_max_length:
                meets_requirements = False
                validation_notes.append(f"Caption exceeds maximum length ({len(self.caption)}/{rules.caption_max_length})")
        
        # Check post body length
        if self.post_body and rules.post_max_length:
            if len(self.post_body) > rules.post_max_length:
                meets_requirements = False
                validation_notes.append(f"Post body exceeds maximum length ({len(self.post_body)}/{rules.post_max_length})")
        
        # Check bio length
        if self.bio and rules.bio_max_length:
            if len(self.bio) > rules.bio_max_length:
                meets_requirements = False
                validation_notes.append(f"Bio exceeds maximum length ({len(self.bio)}/{rules.bio_max_length})")
        
        # Check username length
        if self.username and rules.username_max_length:
            if len(self.username) > rules.username_max_length:
                meets_requirements = False
                validation_notes.append(f"Username exceeds maximum length ({len(self.username)}/{rules.username_max_length})")
        
        # Check profile name length
        if self.profile_name and rules.profile_name_max_length:
            if len(self.profile_name) > rules.profile_name_max_length:
                meets_requirements = False
                validation_notes.append(f"Profile name exceeds maximum length ({len(self.profile_name)}/{rules.profile_name_max_length})")
        
        # Check headline length
        if self.headline and rules.headline_max_length:
            if len(self.headline) > rules.headline_max_length:
                meets_requirements = False
                validation_notes.append(f"Headline exceeds maximum length ({len(self.headline)}/{rules.headline_max_length})")
        
        # Check about section length
        if self.about_section and rules.about_max_length:
            if len(self.about_section) > rules.about_max_length:
                meets_requirements = False
                validation_notes.append(f"About section exceeds maximum length ({len(self.about_section)}/{rules.about_max_length})")
        
        # Check connection message length
        if self.connection_message and rules.connection_message_max_length:
            if len(self.connection_message) > rules.connection_message_max_length:
                meets_requirements = False
                validation_notes.append(f"Connection message exceeds maximum length ({len(self.connection_message)}/{rules.connection_message_max_length})")
        
        # Check tag count
        if self.tag_count < rules.tag_min_count:
            meets_requirements = False
            validation_notes.append(f"Too few tags ({self.tag_count}/{rules.tag_min_count} minimum)")
        elif self.tag_count > rules.tag_max_count:
            meets_requirements = False
            validation_notes.append(f"Too many tags ({self.tag_count}/{rules.tag_max_count} maximum)")
        
        # Special case for X/Twitter - total character limit includes hashtags
        if self.platform == PlatformType.X_TWITTER:
            content_text = self.post_body or self.title
            total_chars = len(content_text) + sum(len(tag) + 1 for tag in self.tags)  # +1 for space before each tag
            if total_chars > rules.post_max_length:
                meets_requirements = False
                validation_notes.append(f"Total content exceeds character limit ({total_chars}/{rules.post_max_length})")
        
        self.meets_requirements = meets_requirements
        self.validation_notes = validation_notes
        
        return meets_requirements


class BatchGenerationRequest(BaseModel):
    """Request model for generating content for multiple platforms."""
    
    transcript: VideoTranscript
    platforms: List[PlatformType] = Field(..., description="List of platforms to generate content for")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Generation options")
    
    @field_validator('platforms')
    def validate_platforms_not_empty(cls, v):
        """Ensure at least one platform is specified."""
        if not v:
            raise ValueError("At least one platform must be specified")
        return list(set(v))  # Remove duplicates


class BatchGenerationResponse(BaseModel):
    """Response model for batch content generation."""
    
    request_id: str = Field(..., description="Unique request identifier")
    generated_content: Dict[str, PlatformContent] = Field(..., description="Generated content by platform")
    processing_time_seconds: float = Field(..., description="Total processing time")
    success_count: int = Field(..., description="Number of successful generations")
    error_count: int = Field(..., description="Number of failed generations")
    errors: Optional[Dict[str, str]] = Field(default_factory=dict, description="Errors by platform")
    
    @field_validator('generated_content')
    def validate_content_keys(cls, v):
        """Ensure all keys are valid platform types."""
        for platform_key in v.keys():
            if platform_key not in [p.value for p in PlatformType]:
                raise ValueError(f"Invalid platform key: {platform_key}")
        return v


class ContentGenerationOptions(BaseModel):
    """Options for content generation customization."""
    
    tone: Optional[str] = Field(default="neutral", description="Content tone (casual, professional, energetic, etc.)")
    include_emojis: bool = Field(default=True, description="Whether to include emojis in generated content")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    keywords_to_include: Optional[List[str]] = Field(default_factory=list, description="Specific keywords to include")
    keywords_to_avoid: Optional[List[str]] = Field(default_factory=list, description="Keywords to avoid")
    brand_voice: Optional[str] = Field(None, description="Brand voice guidelines")
    custom_instructions: Optional[str] = Field(None, description="Additional custom instructions for AI") 