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
    
    def validate_against_platform_rules(self, rules) -> bool:
        """Validate content against specific platform rules."""
        validation_notes = []
        meets_requirements = True
        
        # Check title length
        if self.character_count > rules.title_max_length:
            meets_requirements = False
            validation_notes.append(f"Title exceeds maximum length ({self.character_count}/{rules.title_max_length})")
        
        # Check tag count
        if self.tag_count < rules.tag_min_count:
            meets_requirements = False
            validation_notes.append(f"Too few tags ({self.tag_count}/{rules.tag_min_count} minimum)")
        elif self.tag_count > rules.tag_max_count:
            meets_requirements = False
            validation_notes.append(f"Too many tags ({self.tag_count}/{rules.tag_max_count} maximum)")
        
        # Special case for X/Twitter - total character limit includes hashtags
        if self.platform == PlatformType.X_TWITTER:
            total_chars = len(self.title) + sum(len(tag) + 1 for tag in self.tags)  # +1 for space before each tag
            if total_chars > rules.title_max_length:
                meets_requirements = False
                validation_notes.append(f"Total content exceeds character limit ({total_chars}/{rules.title_max_length})")
        
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