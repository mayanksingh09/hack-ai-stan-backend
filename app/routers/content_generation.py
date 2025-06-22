"""
API endpoints for content generation.
Provides REST API for generating social media content from video transcripts.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import logging

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from models.platform_rules import PlatformType, get_platform_rules, get_all_platforms
from models.content import (
    VideoTranscript, PlatformContent, BatchGenerationRequest, 
    BatchGenerationResponse, ContentGenerationOptions
)
from services.orchestrator import get_content_orchestrator
from services.content_validator import get_content_validator

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["content-generation"])


# Request/Response Models for API
from pydantic import BaseModel, Field


class SinglePlatformRequest(BaseModel):
    """Request model for single platform content generation."""
    transcript: VideoTranscript
    options: Optional[ContentGenerationOptions] = None


class SinglePlatformResponse(BaseModel):
    """Response model for single platform content generation."""
    platform: str
    content: PlatformContent
    processing_time_seconds: float
    validation_passed: bool
    quality_score: Optional[float] = None
    suggestions: Optional[list] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class PlatformInfoResponse(BaseModel):
    """Platform information response model."""
    platform: str
    rules: Dict[str, Any]
    examples: Dict[str, Any]


# API Endpoints

@router.get("/platforms", response_model=Dict[str, Any])
async def get_supported_platforms():
    """Get list of all supported platforms and their basic info."""
    try:
        platforms = {}
        for platform in get_all_platforms():
            rules = get_platform_rules(platform)
            platforms[platform.value] = {
                "name": platform.value.replace('_', ' ').title(),
                "title_max_length": rules.title_max_length,
                "tag_range": f"{rules.tag_min_count}-{rules.tag_max_count}",
                "content_style": rules.content_style,
                "description": f"{platform.value.replace('_', ' ').title()} platform with specific content requirements"
            }
        
        return {
            "platforms": platforms,
            "total_supported": len(platforms)
        }
        
    except Exception as e:
        logger.error(f"Error getting supported platforms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supported platforms"
        )


@router.get("/platforms/{platform}/rules", response_model=PlatformInfoResponse)
async def get_platform_rules_info(platform: str):
    """Get detailed rules and requirements for a specific platform."""
    try:
        # Validate platform
        try:
            platform_type = PlatformType(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform '{platform}' not supported. Use /platforms to see supported platforms."
            )
        
        rules = get_platform_rules(platform_type)
        
        # Create examples based on platform
        examples = {
            "title_examples": [],
            "tag_examples": []
        }
        
        if platform_type == PlatformType.YOUTUBE:
            examples["title_examples"] = [
                "How to Build AI Applications: Complete Tutorial for Beginners",
                "Master Machine Learning in 30 Minutes | Step-by-Step Guide"
            ]
            examples["tag_examples"] = [
                "#AI", "#MachineLearning", "#Tutorial", "#Programming", "#Python",
                "#Education", "#Tech", "#Coding", "#DataScience", "#Beginner"
            ]
        elif platform_type == PlatformType.INSTAGRAM:
            examples["title_examples"] = [
                "Amazing AI breakthrough! 🤖✨ This changes everything we know about technology 💫",
                "Sunday vibes with some coding ✨ Building the future one line at a time 🚀"
            ]
            examples["tag_examples"] = [
                "#AI", "#Technology", "#Innovation", "#Future", "#TechLife",
                "#Coding", "#Programming", "#Developer", "#TechNews", "#Startup"
            ]
        elif platform_type == PlatformType.LINKEDIN:
            examples["title_examples"] = [
                "Key insights from our latest AI research: implications for enterprise adoption",
                "Excited to share learnings from implementing machine learning at scale"
            ]
            examples["tag_examples"] = [
                "#ArtificialIntelligence", "#MachineLearning", "#TechLeadership",
                "#Innovation", "#DigitalTransformation"
            ]
        
        return PlatformInfoResponse(
            platform=platform,
            rules={
                "title_max_length": rules.title_max_length,
                "tag_min_count": rules.tag_min_count,
                "tag_max_count": rules.tag_max_count,
                "content_style": rules.content_style,
                "style_guidelines": rules.style_guidelines,
                "special_requirements": rules.special_requirements
            },
            examples=examples
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting platform rules for {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rules for platform '{platform}'"
        )


@router.post("/generate/{platform}", response_model=SinglePlatformResponse)
async def generate_content_for_platform(
    platform: str,
    request: SinglePlatformRequest
):
    """Generate content for a specific platform from video transcript."""
    start_time = time.time()
    
    try:
        # Validate platform
        try:
            platform_type = PlatformType(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform '{platform}' not supported. Use /platforms to see supported platforms."
            )
        
        # Validate transcript
        if not request.transcript.content or len(request.transcript.content.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcript content must be at least 10 characters long"
            )
        
        # Get services
        orchestrator = get_content_orchestrator()
        validator = get_content_validator()
        
        # Generate content
        logger.info(f"Generating content for {platform} platform")
        try:
            content = orchestrator.generate_single_platform(
                platform_type, 
                request.transcript, 
                request.options
            )
        except RuntimeError as e:
            logger.error(f"Content generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Content generation failed: {str(e)}"
            )
        
        # Validate generated content
        validation_result = validator.validate_content(content)
        suggestions = validator.suggest_improvements(validation_result) if not validation_result.is_valid else None
        
        processing_time = time.time() - start_time
        
        logger.info(f"Content generated for {platform} in {processing_time:.2f}s, valid: {validation_result.is_valid}")
        
        return SinglePlatformResponse(
            platform=platform,
            content=content,
            processing_time_seconds=round(processing_time, 2),
            validation_passed=validation_result.is_valid,
            quality_score=validation_result.score,
            suggestions=suggestions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating content for {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during content generation"
        )


@router.post("/generate/batch", response_model=BatchGenerationResponse)
async def generate_batch_content(request: BatchGenerationRequest):
    """Generate content for multiple platforms in batch."""
    try:
        # Validate transcript
        if not request.transcript.content or len(request.transcript.content.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcript content must be at least 10 characters long"
            )
        
        # Validate platforms
        valid_platforms = []
        for platform in request.platforms:
            if platform in PlatformType:
                valid_platforms.append(platform)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Platform '{platform.value}' not supported"
                )
        
        if not valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one valid platform must be specified"
            )
        
        # Get orchestrator
        orchestrator = get_content_orchestrator()
        
        # Generate batch content
        logger.info(f"Generating batch content for {len(valid_platforms)} platforms")
        response = orchestrator.generate_batch_content(request, concurrent=True)
        
        logger.info(f"Batch generation completed: {response.success_count} successful, {response.error_count} failed")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during batch content generation"
        )


@router.post("/generate/{platform}/validate", response_model=Dict[str, Any])
async def validate_existing_content(platform: str, content: PlatformContent):
    """Validate existing content against platform rules."""
    try:
        # Validate platform
        try:
            platform_type = PlatformType(platform)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform '{platform}' not supported"
            )
        
        # Ensure content platform matches endpoint platform
        if content.platform != platform_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content platform ({content.platform.value}) doesn't match endpoint platform ({platform})"
            )
        
        # Validate content
        validator = get_content_validator()
        validation_result = validator.validate_content(content)
        suggestions = validator.suggest_improvements(validation_result)
        
        return {
            "platform": platform,
            "is_valid": validation_result.is_valid,
            "quality_score": validation_result.score,
            "issues": [
                {
                    "field": issue.field,
                    "severity": issue.severity.value,
                    "message": issue.message,
                    "suggestion": issue.suggestion
                }
                for issue in validation_result.issues
            ],
            "suggestions": suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating content for {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate content"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the content generation service."""
    try:
        # Test basic service availability
        orchestrator = get_content_orchestrator()
        validator = get_content_validator()
        
        # Get performance stats
        stats = orchestrator.get_performance_stats()
        
        return {
            "status": "healthy",
            "services": {
                "orchestrator": "operational",
                "validator": "operational",
                "platform_rules": "operational"
            },
            "supported_platforms": len(get_all_platforms()),
            "performance_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Error handlers
@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="Invalid Input",
            message=str(exc)
        ).model_dump()
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred"
        ).model_dump()
    )


# Add missing import
import time 