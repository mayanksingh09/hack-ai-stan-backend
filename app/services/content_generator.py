"""
Base AI Content Generation Service using Pydantic AI and OpenAI.
Provides core functionality for generating social media content from video transcripts.
"""
from typing import List, Dict, Optional, Any
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel, Field
import asyncio
import logging
from datetime import datetime

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from config import settings
from models.platform_rules import PlatformType, get_platform_rules
from models.content import VideoTranscript, PlatformContent, GeneratedContent

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)


class ContentGenerationRequest(BaseModel):
    """Request model for content generation."""
    transcript: VideoTranscript
    platform: PlatformType
    additional_context: Optional[str] = None
    tone: Optional[str] = "neutral"
    include_emojis: bool = True


class ContentGeneratorService:
    """Base AI service for generating social media content from video transcripts."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize the content generator service."""
        self.model_name = model_name
        self.model = None
        self.agent = None
        self._initialize_ai_service()
    
    def _initialize_ai_service(self):
        """Initialize the Pydantic AI service with OpenAI."""
        try:
            # Create OpenAI model with provider
            provider = OpenAIProvider(api_key=settings.openai_api_key)
            self.model = OpenAIModel(self.model_name, provider=provider)
            
            # Create AI agent with base system prompt
            self.agent = Agent(
                model=self.model,
                system_prompt=self._get_base_system_prompt()
            )
            
            logger.info(f"AI service initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise
    
    def _get_base_system_prompt(self) -> str:
        """Get the base system prompt for content generation."""
        return """You are an expert social media content creator and marketing specialist. 
Your job is to analyze video transcripts and generate engaging, platform-appropriate titles and hashtags.

Key principles:
1. Always match the platform's specific style and requirements
2. Create engaging, clickable titles that capture the essence of the content
3. Use relevant, trending hashtags that will increase discoverability
4. Maintain authenticity while optimizing for engagement
5. Consider the target audience for each platform

You will be provided with:
- Video transcript content
- Target platform specifications
- Platform-specific rules and constraints
- Optional tone and style preferences

Generate content that:
- Meets all platform character limits and tag counts
- Reflects the actual content of the video
- Uses appropriate tone for the platform
- Maximizes engagement potential
- Follows current social media best practices

Always return your response in the exact JSON format requested, with proper title and tags arrays."""
    
    def _build_platform_prompt(self, platform: PlatformType, transcript: VideoTranscript, 
                             tone: str = "neutral", include_emojis: bool = True) -> str:
        """Build platform-specific prompt for content generation."""
        rules = get_platform_rules(platform)
        
        platform_context = {
            PlatformType.YOUTUBE: "YouTube audience expects educational, entertaining content with SEO-optimized titles",
            PlatformType.INSTAGRAM: "Instagram users love visual, lifestyle-focused content with plenty of hashtags",
            PlatformType.FACEBOOK: "Facebook prioritizes community engagement and shareable content",
            PlatformType.TIKTOK: "TikTok thrives on trendy, viral content that appeals to Gen-Z",
            PlatformType.X_TWITTER: "X/Twitter users want concise, timely content that sparks conversation",
            PlatformType.LINKEDIN: "LinkedIn requires professional, industry-focused, thought-leadership content",
            PlatformType.TWITCH: "Twitch focuses on gaming, streaming, and interactive community content"
        }
        
        emoji_instruction = "Include relevant emojis to enhance engagement" if include_emojis else "Do not include emojis"
        
        prompt = f"""
PLATFORM: {platform.value.upper()}
PLATFORM CONTEXT: {platform_context[platform]}

PLATFORM REQUIREMENTS:
- Maximum title length: {rules.title_max_length} characters
- Required tags: {rules.tag_min_count}-{rules.tag_max_count} hashtags
    - Content style: {str(rules.content_style).replace('_', ' ').title()}
- Style guidelines: {', '.join(rules.style_guidelines)}

CONTENT TONE: {tone}
EMOJI USAGE: {emoji_instruction}

VIDEO TRANSCRIPT:
"{transcript.content}"

ADDITIONAL CONTEXT:
- Original title: {transcript.title or 'Not provided'}
- Video category: {transcript.video_category or 'General'}
- Duration: {transcript.duration_seconds or 'Unknown'} seconds
- Language: {transcript.language}

Generate a {platform.value} post with:
1. An engaging title/caption that captures the video's essence
2. Relevant hashtags that will maximize discoverability
3. Content that follows {platform.value} best practices

CRITICAL: Ensure the title does not exceed {rules.title_max_length} characters and you provide exactly {rules.tag_min_count}-{rules.tag_max_count} hashtags.

Respond with a JSON object in this exact format:
{{
    "title": "your generated title here",
    "tags": ["#hashtag1", "#hashtag2", "#hashtag3"],
    "confidence": 0.85
}}

IMPORTANT: The "tags" array must contain comma-separated hashtag strings, each enclosed in quotes. Do not generate tags without proper comma separation.
"""
        return prompt
    
    async def generate_content(self, request: ContentGenerationRequest) -> PlatformContent:
        """Generate platform-specific content from video transcript."""
        if not self.agent:
            raise RuntimeError("AI service not properly initialized")
        
        try:
            # Build platform-specific prompt
            prompt = self._build_platform_prompt(
                platform=request.platform,
                transcript=request.transcript,
                tone=request.tone,
                include_emojis=request.include_emojis
            )
            
            # Generate content using AI
            logger.info(f"Generating content for {request.platform.value}")
            result = await self.agent.run(prompt)
            
            # Parse AI response
            ai_response = result.output
            
            # Handle both string and dict responses
            if isinstance(ai_response, str):
                import json
                try:
                    ai_response = json.loads(ai_response)
                except json.JSONDecodeError:
                    # Fallback parsing if JSON is malformed
                    ai_response = self._parse_fallback_response(ai_response)
            
            # Process tags to handle cases where multiple hashtags are in one string
            raw_tags = ai_response.get("tags", ["content"])
            processed_tags = self._process_tags(raw_tags)
            
            # Create platform content
            content = PlatformContent(
                platform=request.platform,
                title=ai_response.get("title", "Generated Title"),
                tags=processed_tags,
                confidence_score=float(ai_response.get("confidence", 0.7))
            )
            
            # Validate against platform rules
            rules = get_platform_rules(request.platform)
            content.validate_against_platform_rules(rules)
            
            logger.info(f"Content generated successfully for {request.platform.value}")
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed for {request.platform.value}: {e}")
            raise
    
    def _process_tags(self, raw_tags: List[str]) -> List[str]:
        """Process tags to handle cases where multiple hashtags are in one string."""
        import re
        processed_tags = []
        
        logger.debug(f"Processing raw tags: {raw_tags}")
        
        for tag in raw_tags:
            if tag:
                # Always try to extract hashtags using regex first
                # More permissive pattern to handle various hashtag formats
                found_hashtags = re.findall(r'#[A-Za-z0-9_]+', tag)
                
                logger.debug(f"Tag: '{tag}' -> Found hashtags: {found_hashtags}")
                
                if found_hashtags:
                    # If we found hashtags, use them
                    processed_tags.extend(found_hashtags)
                else:
                    # If no hashtags found, treat as single tag and add # if needed
                    clean_tag = tag.strip()
                    if clean_tag and not clean_tag.startswith('#'):
                        clean_tag = f"#{clean_tag}"
                    if clean_tag and clean_tag != "#":  # Avoid empty hashtags
                        processed_tags.append(clean_tag)
        
        # Remove duplicates while preserving order
        seen = set()
        processed_tags = [tag for tag in processed_tags if tag not in seen and not seen.add(tag)]
        
        logger.debug(f"Final processed tags: {processed_tags}")
        
        return processed_tags or ["#content"]
    
    def _parse_fallback_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON response is malformed."""
        # Simple regex-based extraction as fallback
        import re
        
        title_match = re.search(r'"title":\s*"([^"]*)"', response_text)
        tags_match = re.search(r'"tags":\s*\[(.*?)\]', response_text)
        confidence_match = re.search(r'"confidence":\s*([0-9.]+)', response_text)
        
        title = title_match.group(1) if title_match else "Generated Content"
        
        tags = []
        if tags_match:
            tags_str = tags_match.group(1)
            # Handle comma-separated tags
            raw_tags = [tag.strip(' "') for tag in tags_str.split(',')]
            # Use the same tag processing logic
            tags = self._process_tags(raw_tags)
        
        confidence = float(confidence_match.group(1)) if confidence_match else 0.7
        
        return {
            "title": title,
            "tags": tags or ["#content"],
            "confidence": confidence
        }
    
    def generate_content_sync(self, request: ContentGenerationRequest) -> PlatformContent:
        """Synchronous wrapper for content generation."""
        try:
            # Use run_sync method for synchronous execution
            if not self.agent:
                raise RuntimeError("AI service not properly initialized")
            
            # Build platform-specific prompt
            prompt = self._build_platform_prompt(
                platform=request.platform,
                transcript=request.transcript,
                tone=request.tone,
                include_emojis=request.include_emojis
            )
            
            # Generate content using AI synchronously
            logger.info(f"Generating content for {request.platform.value} (sync)")
            result = self.agent.run_sync(prompt)
            
            # Parse AI response
            ai_response = result.output
            
            # Handle both string and dict responses
            if isinstance(ai_response, str):
                import json
                try:
                    ai_response = json.loads(ai_response)
                except json.JSONDecodeError:
                    # Fallback parsing if JSON is malformed
                    ai_response = self._parse_fallback_response(ai_response)
            
            # Process tags to handle cases where multiple hashtags are in one string
            raw_tags = ai_response.get("tags", ["#content"])
            processed_tags = self._process_tags(raw_tags)
            
            # Create platform content
            content = PlatformContent(
                platform=request.platform,
                title=ai_response.get("title", "Generated Title"),
                tags=processed_tags,
                confidence_score=float(ai_response.get("confidence", 0.7))
            )
            
            # Validate against platform rules
            rules = get_platform_rules(request.platform)
            content.validate_against_platform_rules(rules)
            
            logger.info(f"Content generated successfully for {request.platform.value} (sync)")
            return content
            
        except Exception as e:
            logger.error(f"Sync content generation failed for {request.platform.value}: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test the AI service connection."""
        try:
            if not self.agent:
                return False
                
            test_prompt = "Respond with exactly: 'AI service is working correctly'"
            result = await self.agent.run(test_prompt)
            
            return "working correctly" in str(result.output).lower()
            
        except Exception as e:
            logger.error(f"AI service connection test failed: {e}")
            return False
    
    def test_tag_processing(self) -> None:
        """Test the tag processing functionality."""
        test_cases = [
            ["#AdviceHub #TechExperts #AICommunity #ExpertSignup"],
            ["#single"],
            ["#tag1", "#tag2 #tag3", "#tag4"],
            ["nohashtag"],
        ]
        
        for test_case in test_cases:
            result = self._process_tags(test_case)
            logger.info(f"Test input: {test_case} -> Output: {result}")
    
    def test_connection_sync(self) -> bool:
        """Synchronous test of AI service connection."""
        try:
            if not self.agent:
                return False
                
            test_prompt = "Respond with exactly: 'AI service is working correctly'"
            result = self.agent.run_sync(test_prompt)
            
            return "working correctly" in str(result.output).lower()
            
        except Exception as e:
            logger.error(f"Sync AI service connection test failed: {e}")
            return False


# Global service instance
_content_generator_service = None


def get_content_generator() -> ContentGeneratorService:
    """Get global content generator service instance."""
    global _content_generator_service
    if _content_generator_service is None:
        _content_generator_service = ContentGeneratorService()
    return _content_generator_service 