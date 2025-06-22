"""
Simplified Content Generation Orchestrator for creating platform-specific content.
"""
import logging
from typing import Optional
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from config import settings
from models.platform_rules import PlatformType, get_platform_rules
from models.content import VideoTranscript, PlatformContent

logger = logging.getLogger(__name__)


class ContentOrchestrator:
    """Simplified orchestrator for generating platform-specific content from video transcripts."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the AI agent for content generation."""
        model = OpenAIModel(self.model_name)
        
        system_prompt = """You are an expert social media content creator.
        
Your task is to generate platform-specific titles and tags from video transcripts.
You understand each platform's unique requirements and audience expectations.

Always respond with a title and appropriate tags for the requested platform."""
        
        return Agent(model=model, system_prompt=system_prompt)
    
    def _process_tags(self, raw_tags):
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
    
    async def generate_content(self, platform: PlatformType, transcript: VideoTranscript) -> PlatformContent:
        """Generate content for a specific platform from a video transcript."""
        rules = get_platform_rules(platform)
        
        # Build the prompt with platform rules
        prompt = f"""
Generate a {platform.value} post from this video transcript.

Platform Rules:
- Title: Maximum {rules.title_max_length} characters
- Tags: {rules.tag_min_count} to {rules.tag_max_count} tags
- Style: {rules.content_style}

Video Transcript:
"{transcript.content}"

{f'Original Title: {transcript.title}' if transcript.title else ''}

Requirements:
1. Create an engaging title that fits the platform's style
2. Generate {rules.tag_min_count}-{rules.tag_max_count} relevant hashtags
3. Match the platform's content style

Respond in this exact format:
Title: [your title here]
Tags: #tag1, #tag2, #tag3, etc.

IMPORTANT: Make sure tags are comma-separated. Do not put all hashtags in one continuous string.
"""
        
        try:
            # Get AI response
            result = await self.agent.run(prompt)
            content_text = result.output
            
            # Parse the response
            lines = content_text.strip().split('\n')
            title = ""
            tags = []
            
            for line in lines:
                if line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
                elif line.startswith("Tags:"):
                    tags_text = line.replace("Tags:", "").strip()
                    # Extract hashtags using robust processing
                    raw_tags = [tag.strip() for tag in tags_text.split(',')]
                    tags = self._process_tags(raw_tags)
            
            # Create platform content
            content = PlatformContent(
                platform=platform,
                title=title or "Generated Content",
                tags=tags or [f"#{platform.value}"],
                confidence_score=0.85 if title and tags else 0.5
            )
            
            logger.info(f"Generated content for {platform.value}: {len(content.title)} chars, {len(content.tags)} tags")
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed for {platform.value}: {e}")
            # Return fallback content
            return PlatformContent(
                platform=platform,
                title=f"{platform.value.title()} Post",
                tags=[f"#{platform.value}", "#video", "#content"],
                confidence_score=0.3
            )


# Global orchestrator instance
_content_orchestrator = None


def get_content_orchestrator() -> ContentOrchestrator:
    """Get global content orchestrator instance."""
    global _content_orchestrator
    if _content_orchestrator is None:
        _content_orchestrator = ContentOrchestrator()
    return _content_orchestrator 