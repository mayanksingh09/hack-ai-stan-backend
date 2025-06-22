"""
FastAPI application main entry point for Video Transcript to Social Media Content Generator.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from config import settings
from routers.content_generation import router as content_router
from routers.audio_transcription import router as audio_router

# Create rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.rate_limit_storage_uri,
    default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_window}"]
)

# Create FastAPI application instance
app = FastAPI(
    title="Video Transcript to Social Media Content Generator",
    description="Generate platform-specific titles and tags from video transcripts using AI",
    version="1.0.0",
    debug=settings.debug
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(content_router)
app.include_router(audio_router)


@app.get("/")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}")
async def root(request: Request):
    """Root endpoint for health check."""
    return {
        "message": "Video Transcript to Social Media Content Generator API",
        "status": "running",
        "version": "1.0.0",
        "supported_platforms": ["YouTube", "Instagram", "Facebook", "TikTok", "X (Twitter)", "LinkedIn", "Twitch"],
        "api_endpoints": {
            "platforms": "/api/v1/platforms",
            "generate": "/api/v1/generate/{platform}",
            "validate": "/api/v1/validate/{platform}",
            "platform_rules": "/api/v1/platforms/{platform}/rules",
            "health": "/api/v1/health",
            "docs": "/docs"
        },
        "rate_limits": {
            "default": f"{settings.rate_limit_requests}/{settings.rate_limit_window}",
            "ai_generation": f"{settings.ai_generation_rate_limit}/{settings.ai_generation_window}"
        }
    }


@app.get("/health")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}")
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 