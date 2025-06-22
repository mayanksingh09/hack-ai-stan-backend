"""
API endpoints for content generation - simplified version.
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Dict, Any
import time
import logging

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from models.platform_rules import PlatformType, get_platform_rules
from models.content import VideoTranscript, PlatformContent
from services.orchestrator import get_content_orchestrator
from services.content_validator import ContentValidator
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["content-generation"])

# Create limiter instance for this router
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.rate_limit_storage_uri
)

# Simple request model
from pydantic import BaseModel

class GenerateContentRequest(BaseModel):
    """Request model for content generation."""
    transcript: VideoTranscript


@router.get("/platforms")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}")
async def get_supported_platforms(request: Request):
    """Get list of all supported platforms with their basic information."""
    platforms = {}
    
    for platform in PlatformType:
        rules = get_platform_rules(platform)
        platforms[platform.value] = {
            "name": platform.value.replace("_", " ").title(),
            "title_max_length": rules.title_max_length,
            "tag_range": f"{rules.tag_min_count}-{rules.tag_max_count}",
            "style": rules.content_style
        }
    
    return {
        "platforms": platforms,
        "total_supported": len(platforms)
    }


@router.get("/platforms/{platform}/rules")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}")
async def get_platform_rules_endpoint(platform: str, request: Request):
    """Get detailed rules and guidelines for a specific platform."""
    try:
        platform_type = PlatformType(platform)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")
    
    rules = get_platform_rules(platform_type)
    
    # Build response with all available fields
    response_rules = {
        "title_max_length": rules.title_max_length,
        "tag_min_count": rules.tag_min_count,
        "tag_max_count": rules.tag_max_count,
        "content_style": rules.content_style,
        "style_guidelines": rules.style_guidelines
    }
    
    # Add optional length fields if they exist
    optional_fields = [
        ("description_max_length", "description"),
        ("caption_max_length", "caption"),
        ("post_max_length", "post_body"),
        ("bio_max_length", "bio"),
        ("username_max_length", "username"),
        ("profile_name_max_length", "profile_name"),
        ("comments_max_length", "comments"),
        ("headline_max_length", "headline"),
        ("about_max_length", "about_section"),
        ("connection_message_max_length", "connection_message"),
        ("stream_category_max_length", "stream_category")
    ]
    
    available_fields = ["title", "tags"]  # Always available
    for field_name, response_field in optional_fields:
        field_value = getattr(rules, field_name, None)
        if field_value is not None:
            response_rules[field_name] = field_value
            available_fields.append(response_field)
    
    # Add optimal length fields if they exist
    optimal_fields = [
        ("title_optimal_length", "title_optimal_length"),
        ("description_optimal_length", "description_optimal_length"),
        ("caption_optimal_length", "caption_optimal_length"),
        ("post_optimal_length", "post_optimal_length")
    ]
    
    for field_name, response_field in optimal_fields:
        field_value = getattr(rules, field_name, None)
        if field_value is not None:
            response_rules[response_field] = field_value
    
    return {
        "platform": platform,
        "rules": response_rules,
        "available_fields": available_fields,
        "special_requirements": rules.special_requirements if rules.special_requirements else []
    }


@router.post("/generate/{platform}")
@limiter.limit(f"{settings.ai_generation_rate_limit}/{settings.ai_generation_window}")
async def generate_content_for_platform(platform: str, data: GenerateContentRequest, request: Request):
    """Generate content for a specific platform from a video transcript."""
    start_time = time.time()
    
    # Validate platform
    try:
        platform_type = PlatformType(platform)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")
    
    # Get orchestrator and generate content
    orchestrator = get_content_orchestrator()
    
    try:
        # Generate content with simplified orchestrator
        content = await orchestrator.generate_content(platform_type, data.transcript)
        
        # Validate the generated content
        validator = ContentValidator()
        validation_result = validator.validate_content(content)
        
        processing_time = time.time() - start_time
        
        return {
            "platform": platform,
            "content": content.model_dump(),
            "validation_passed": validation_result.is_valid,
            "quality_score": validation_result.score,
            "issues": [
                {"field": issue.field, "message": issue.message}
                for issue in validation_result.issues
            ] if validation_result.issues else [],
            "processing_time_seconds": round(processing_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Content generation failed for {platform}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Content generation failed: {str(e)}"
        )


@router.post("/validate/{platform}")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}")
async def validate_content(platform: str, content: PlatformContent, request: Request):
    """Validate existing content against platform rules."""
    # Validate platform
    try:
        platform_type = PlatformType(platform)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not supported")
    
    # Check platform match
    if content.platform != platform_type:
        raise HTTPException(
            status_code=400,
            detail=f"Content platform '{content.platform.value}' doesn't match endpoint platform '{platform}'"
        )
    
    # Validate content
    validator = ContentValidator()
    validation_result = validator.validate_content(content)
    suggestions = validator.suggest_improvements(validation_result)
    
    return {
        "platform": platform,
        "is_valid": validation_result.is_valid,
        "quality_score": validation_result.score,
        "issues": [
            {
                "severity": issue.severity.value,
                "field": issue.field,
                "message": issue.message
            }
            for issue in validation_result.issues
        ],
        "suggestions": suggestions
    }


@router.get("/health")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}")
async def health_check(request: Request):
    """Check if the content generation service is healthy."""
    try:
        # Simple health check
        orchestrator = get_content_orchestrator()
        
        return {
            "status": "healthy",
            "services": {
                "orchestrator": "active",
                "validator": "active"
            },
            "supported_platforms": [p.value for p in PlatformType]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")