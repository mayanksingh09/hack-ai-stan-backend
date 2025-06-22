"""
FastAPI application main entry point for Video Transcript to Social Media Content Generator.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers.content_generation import router as content_router

# Create FastAPI application instance
app = FastAPI(
    title="Video Transcript to Social Media Content Generator",
    description="Generate platform-specific titles and tags from video transcripts using AI",
    version="1.0.0",
    debug=settings.debug
)

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


@app.get("/")
async def root():
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
        }
    }


@app.get("/health")
async def health_check():
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