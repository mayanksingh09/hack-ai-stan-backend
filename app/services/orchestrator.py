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
        
        system_prompt = """You are an expert social media content creator and platform specialist.
        
Your task is to generate comprehensive, platform-specific content from video transcripts.
You understand each platform's unique requirements, audience expectations, and text field needs.

For each platform, you generate ALL relevant text fields required for direct publishing:
- Titles/captions with optimal lengths for engagement
- Descriptions/post bodies with platform-appropriate detail
- Professional headlines and bios when relevant
- Platform-specific content like usernames, categories, etc.
- Strategic hashtags that maximize reach and engagement

Always respond with valid JSON containing all requested fields for the platform."""
        
        return Agent(model=model, system_prompt=system_prompt)
    
    def _get_platform_fields(self, platform: PlatformType) -> dict:
        """Get the required fields for each platform based on our research."""
        platform_fields = {
            PlatformType.YOUTUBE: {
                "title": "Video title (max 100 chars, optimal 70)",
                "description": "Video description (max 5000 chars, first 157 crucial)",
                "tags": "Hashtags for discoverability"
            },
            PlatformType.INSTAGRAM: {
                "title": "Post title/caption preview",
                "caption": "Full post caption (max 2200 chars, truncated at 125)",
                "tags": "Hashtags (20-30 for reach, 5-10 for engagement)"
            },
            PlatformType.FACEBOOK: {
                "title": "Post title",
                "post_body": "Main post content (optimal ≤80 chars for engagement)",
                "tags": "Hashtags (3-5 only, not hashtag-heavy)"
            },
            PlatformType.TIKTOK: {
                "title": "Video title",
                "caption": "Video caption (max 2200 chars)",
                "tags": "Trending hashtags (3-5 optimal)"
            },
            PlatformType.X_TWITTER: {
                "title": "Tweet preview",
                "post_body": "Full tweet content (280 chars max, optimal <100)",
                "tags": "Hashtags (1-2 optimal, integrated into text)"
            },
            PlatformType.LINKEDIN: {
                "title": "Post title",
                "post_body": "Professional post content (max 3000 chars, truncated at 200)",
                "headline": "Professional headline if profile content",
                "tags": "Professional hashtags (3-5)"
            },
            PlatformType.TWITCH: {
                "title": "Stream title (max 140 chars)",
                "stream_category": "Game/category for the stream",
                "tags": "Gaming-related tags"
            }
        }
        return platform_fields.get(platform, {})
    
    def _process_tags(self, raw_tags):
        """Process tags to handle cases where multiple hashtags are in one string."""
        import re
        processed_tags = []
        
        logger.debug(f"Processing raw tags: {raw_tags}")
        
        if isinstance(raw_tags, str):
            # If tags is a string, split by common separators
            raw_tags = [tag.strip() for tag in re.split(r'[,\s]+', raw_tags) if tag.strip()]
        
        for tag in raw_tags:
            if tag:
                # First, extract any existing hashtags
                found_hashtags = re.findall(r'#[A-Za-z0-9_]+', tag)
                
                if found_hashtags:
                    # If we found hashtags, use them
                    processed_tags.extend(found_hashtags)
                    
                    # Also extract any remaining words that aren't already hashtags
                    remaining_text = tag
                    for hashtag in found_hashtags:
                        remaining_text = remaining_text.replace(hashtag, '')
                    
                    # Extract individual words from remaining text
                    words = [word.strip() for word in remaining_text.split() if word.strip()]
                    for word in words:
                        if word and not word.startswith('#'):
                            clean_word = f"#{word}"
                            if clean_word not in processed_tags:
                                processed_tags.append(clean_word)
                else:
                    # If no hashtags found, treat as single tag and add # if needed
                    clean_tag = tag.strip()
                    if clean_tag and not clean_tag.startswith('#'):
                        clean_tag = f"#{clean_tag}"
                    if clean_tag and clean_tag != "#":  # Avoid empty hashtags
                        processed_tags.append(clean_tag)
                
                logger.debug(f"Tag: '{tag}' -> Result: {[t for t in processed_tags if t not in processed_tags[:-10]]}")
        
        # Remove duplicates while preserving order
        seen = set()
        processed_tags = [tag for tag in processed_tags if tag not in seen and not seen.add(tag)]
        
        logger.debug(f"Final processed tags: {processed_tags}")
        
        return processed_tags or ["#content"]
    
    def _parse_response(self, response_text: str, platform: PlatformType) -> dict:
        """Parse AI response and extract all fields safely with fallbacks."""
        import json
        import re
        
        logger.debug(f"Parsing response for {platform.value}: {response_text[:200]}...")
        
        # Try to extract JSON from the response
        json_content = None
        
        # First, try to find JSON block in the response
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON in code block
            r'```\s*(\{.*?\})\s*```',      # JSON in generic code block
            r'(\{.*?\})',                   # Standalone JSON object
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                try:
                    json_content = json.loads(match.group(1))
                    logger.debug(f"Successfully parsed JSON: {json_content}")
                    break
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse JSON with pattern {pattern}: {e}")
                    continue
        
        # If JSON parsing failed, try to extract fields with text parsing
        if not json_content:
            logger.debug("JSON parsing failed, falling back to text parsing")
            json_content = {}
            
            # Extract title
            title_match = re.search(r'["\']?title["\']?\s*:\s*["\']([^"\']+)["\']', response_text, re.IGNORECASE)
            if title_match:
                json_content['title'] = title_match.group(1)
            
            # Extract tags
            tags_match = re.search(r'["\']?tags["\']?\s*:\s*\[([^\]]+)\]', response_text, re.IGNORECASE)
            if tags_match:
                tags_text = tags_match.group(1)
                json_content['tags'] = [tag.strip().strip('"\'') for tag in tags_text.split(',')]
            
            # Extract other common fields
            for field in ['description', 'caption', 'post_body', 'headline', 'stream_category']:
                field_match = re.search(rf'["\']?{field}["\']?\s*:\s*["\']([^"\']+)["\']', response_text, re.IGNORECASE)
                if field_match:
                    json_content[field] = field_match.group(1)
        
        # Process and clean the extracted data
        result = {}
        
        # Process title
        result['title'] = json_content.get('title', f"{platform.value.title()} Post")
        
        # Process tags
        raw_tags = json_content.get('tags', [])
        result['tags'] = self._process_tags(raw_tags)
        
        # Process other fields based on platform
        platform_fields = self._get_platform_fields(platform)
        for field_name in platform_fields.keys():
            if field_name not in ['title', 'tags'] and field_name in json_content:
                result[field_name] = json_content[field_name]
        
        logger.debug(f"Final parsed result: {result}")
        return result
    
    async def generate_content(self, platform: PlatformType, transcript: VideoTranscript) -> PlatformContent:
        """Generate content for a specific platform from a video transcript."""
        rules = get_platform_rules(platform)
        platform_fields = self._get_platform_fields(platform)
        
        # Build JSON schema for the expected response
        response_schema = {field: description for field, description in platform_fields.items()}
        
        # Build the comprehensive prompt
        prompt = f"""
Generate comprehensive {platform.value} content from this video transcript.

Platform: {platform.value.upper()}
Content Style: {rules.content_style}

Platform Rules:
- Title: Maximum {rules.title_max_length} characters
- Tags: {rules.tag_min_count} to {rules.tag_max_count} tags
- Style Guidelines: {', '.join(rules.style_guidelines)}
{f"- Special Requirements: {', '.join(rules.special_requirements)}" if rules.special_requirements else ""}

Video Transcript:
"{transcript.content}"

{f'Original Title: {transcript.title}' if transcript.title else ''}
{f'Video Category: {transcript.video_category}' if transcript.video_category else ''}

REQUIRED FIELDS FOR {platform.value.upper()}:
{chr(10).join([f"- {field}: {desc}" for field, desc in platform_fields.items()])}

Requirements:
1. Create content optimized for {platform.value} audience and algorithm
2. Use platform-appropriate tone, style, and formatting
3. Include {rules.tag_min_count}-{rules.tag_max_count} strategic hashtags
4. Ensure all text fits within platform character limits
5. Focus on engagement and discoverability

RESPOND WITH VALID JSON ONLY:
```json
{{
{chr(10).join([f'  "{field}": "your generated {field} here",' for field in platform_fields.keys() if field != 'tags'])}
{f'  "tags": ["#tag1", "#tag2", "#tag3"]' if 'tags' in platform_fields else ''}
}}
```

IMPORTANT: 
- Use proper JSON format with double quotes
- Ensure all fields are present and non-empty
- Make hashtags realistic and relevant to the content
- Optimize content length for maximum engagement on {platform.value}
"""
        
        try:
            # Get AI response
            result = await self.agent.run(prompt)
            content_text = result.output
            
            # Parse the response using new robust parser
            parsed_data = self._parse_response(content_text, platform)
            
            # Create platform content with all fields
            content_kwargs = {
                'platform': platform,
                'title': parsed_data.get('title', f"{platform.value.title()} Post"),
                'tags': parsed_data.get('tags', [f"#{platform.value}"]),
                'confidence_score': 0.85 if parsed_data.get('title') and parsed_data.get('tags') else 0.5
            }
            
            # Add platform-specific fields
            field_mapping = {
                'description': 'description',
                'caption': 'caption', 
                'post_body': 'post_body',
                'headline': 'headline',
                'stream_category': 'stream_category'
            }
            
            for field_key, content_field in field_mapping.items():
                if field_key in parsed_data:
                    content_kwargs[content_field] = parsed_data[field_key]
            
            content = PlatformContent(**content_kwargs)
            
            logger.info(f"Generated content for {platform.value}: {len(content.title)} chars title, {len(content.tags)} tags")
            if content.description:
                logger.info(f"  Description: {len(content.description)} chars")
            if content.caption:
                logger.info(f"  Caption: {len(content.caption)} chars")
            if content.post_body:
                logger.info(f"  Post body: {len(content.post_body)} chars")
                
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed for {platform.value}: {e}")
            # Return fallback content with minimal fields
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