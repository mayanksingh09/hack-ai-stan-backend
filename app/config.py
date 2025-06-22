"""
Configuration module for the Video Transcript to Social Media Content Generator.
Handles environment variables and application settings.
"""
import os
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Application Configuration  
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Configuration
    api_host: str = Field(default="localhost", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


def get_settings() -> Settings:
    """Get application settings instance."""
    settings = Settings()
    # Ensure OpenAI API key is set in environment for Pydantic AI
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    return settings


# Global settings instance
settings = get_settings() 