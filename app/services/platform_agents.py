"""
Platform-specific AI agents for generating tailored social media content.
Each agent is specialized for a specific platform's audience, style, and requirements.
"""
from typing import Dict, List, Optional
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import logging

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from config import settings
from models.platform_rules import PlatformType, get_platform_rules
from models.content import VideoTranscript, PlatformContent

logger = logging.getLogger(__name__)


class PlatformSpecificAgent:
    """Base class for platform-specific AI agents."""
    
    def __init__(self, platform: PlatformType, model_name: str = "gpt-4o"):
        self.platform = platform
        self.model_name = model_name
        self.rules = get_platform_rules(platform)
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create platform-specific AI agent."""
        provider = OpenAIProvider(api_key=settings.openai_api_key)
        model = OpenAIModel(self.model_name, provider=provider)
        
        return Agent(
            model=model,
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        """Get platform-specific system prompt. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _get_system_prompt")
    
    def _build_prompt(self, transcript: VideoTranscript, tone: str = "neutral", 
                     include_emojis: bool = True) -> str:
        """Build platform-specific content generation prompt."""
        raise NotImplementedError("Subclasses must implement _build_prompt")


class YouTubeAgent(PlatformSpecificAgent):
    """Specialized AI agent for YouTube content generation."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(PlatformType.YOUTUBE, model_name)
    
    def _get_system_prompt(self) -> str:
        return """You are a YouTube content optimization expert with deep knowledge of YouTube's algorithm and audience behavior.

Your expertise includes:
- SEO optimization for YouTube search and discovery
- Creating compelling, click-worthy titles that don't feel clickbait
- Understanding trending topics and keywords
- Balancing educational value with entertainment
- YouTube-specific engagement strategies

Focus on:
- Educational/entertainment balance
- SEO-friendly titles with trending keywords
- 10-15 relevant, searchable tags
- Content that encourages views, likes, and subscriptions
- Titles that work well with thumbnail optimization

Always create content that YouTube's algorithm will favor while maintaining authenticity."""
    
    def _build_prompt(self, transcript: VideoTranscript, tone: str = "neutral", 
                     include_emojis: bool = True) -> str:
        emoji_instruction = "Include 1-2 relevant emojis" if include_emojis else "No emojis"
        
        return f"""
Create a YouTube-optimized title and tags for this video transcript.

TRANSCRIPT: "{transcript.content}"
ORIGINAL TITLE: {transcript.title or 'Not provided'}
CATEGORY: {transcript.video_category or 'General'}
TONE: {tone}
EMOJIS: {emoji_instruction}

YouTube Optimization Requirements:
- Title: Maximum 100 characters, SEO-optimized, engaging but not clickbait
- Tags: Exactly 10-15 hashtags focused on searchability and trending keywords
- Consider: What would make someone click while accurately representing the content?
- Include trending keywords relevant to the topic
- Think about what the target audience searches for

Respond with JSON:
{{
    "title": "your SEO-optimized YouTube title",
    "tags": ["#keyword1", "#keyword2", "#keyword3", "#keyword4", "#keyword5", "#keyword6", "#keyword7", "#keyword8", "#keyword9", "#keyword10"],
    "confidence": 0.9
}}
"""


class InstagramAgent(PlatformSpecificAgent):
    """Specialized AI agent for Instagram content generation."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(PlatformType.INSTAGRAM, model_name)
    
    def _get_system_prompt(self) -> str:
        return """You are an Instagram content creator expert who understands visual storytelling and Instagram culture.

Your expertise includes:
- Visual-first content strategy
- Instagram's aesthetic and lifestyle focus
- Hashtag strategy for maximum reach
- Community engagement tactics
- Instagram Reels and Stories optimization

Focus on:
- Visual appeal and lifestyle branding
- 20-30 strategic hashtags (mix of popular and niche)
- Content that encourages saves, shares, and comments
- Authentic, relatable captions
- Trend awareness and aesthetic consistency

Create content that fits Instagram's visual-first, lifestyle-focused environment."""
    
    def _build_prompt(self, transcript: VideoTranscript, tone: str = "neutral", 
                     include_emojis: bool = True) -> str:
        emoji_instruction = "Include 3-5 relevant emojis for visual appeal" if include_emojis else "No emojis"
        
        return f"""
Create Instagram-optimized caption and hashtags for this video content.

TRANSCRIPT: "{transcript.content}"
ORIGINAL TITLE: {transcript.title or 'Not provided'}
CATEGORY: {transcript.video_category or 'General'}
TONE: {tone}
EMOJIS: {emoji_instruction}

Instagram Optimization Requirements:
- Caption: Maximum 150 characters, visually appealing, lifestyle-focused
- Hashtags: Exactly 20-30 hashtags (mix trending + niche + community hashtags)
- Consider: Visual storytelling, community engagement, shareability
- Think lifestyle and aesthetic appeal
- Include call-to-action for engagement

Mix hashtag types:
- Trending hashtags (high volume)
- Niche hashtags (targeted audience)
- Community hashtags (specific interests)
- Branded/content hashtags

Respond with JSON:
{{
    "title": "your Instagram caption",
    "tags": ["#hashtag1", "#hashtag2", ... "hashtag20-30"],
    "confidence": 0.9
}}
"""


class FacebookAgent(PlatformSpecificAgent):
    """Specialized AI agent for Facebook content generation."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(PlatformType.FACEBOOK, model_name)
    
    def _get_system_prompt(self) -> str:
        return """You are a Facebook community engagement specialist who understands how to create shareable, discussion-worthy content.

Your expertise includes:
- Community building and engagement
- Content that encourages meaningful discussions
- Facebook's algorithm preferences for social interaction
- Cross-generational appeal
- Share-worthy content creation

Focus on:
- Community building and conversation starters
- Shareable, relatable content
- Minimal hashtag usage (3-5 only)
- Content that generates comments and shares
- Family-friendly, inclusive messaging

Create content that brings people together and encourages community interaction."""
    
    def _build_prompt(self, transcript: VideoTranscript, tone: str = "neutral", 
                     include_emojis: bool = True) -> str:
        emoji_instruction = "Include 1-2 emojis for warmth" if include_emojis else "No emojis"
        
        return f"""
Create Facebook-optimized post for this video content.

TRANSCRIPT: "{transcript.content}"
ORIGINAL TITLE: {transcript.title or 'Not provided'}
CATEGORY: {transcript.video_category or 'General'}
TONE: {tone}
EMOJIS: {emoji_instruction}

Facebook Optimization Requirements:
- Post: Maximum 255 characters, community-focused, conversation-starting
- Hashtags: Only 3-5 hashtags (Facebook users prefer minimal hashtag usage)
- Consider: What would make people share this with friends/family?
- Include question or call-to-action to encourage comments
- Focus on building community and sparking discussion

Create content that people want to share and discuss with their network.

Respond with JSON:
{{
    "title": "your Facebook post",
    "tags": ["#hashtag1", "#hashtag2", "#hashtag3"],
    "confidence": 0.9
}}
"""


class TikTokAgent(PlatformSpecificAgent):
    """Specialized AI agent for TikTok content generation."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(PlatformType.TIKTOK, model_name)
    
    def _get_system_prompt(self) -> str:
        return """You are a TikTok content creator who understands viral trends, Gen-Z culture, and the TikTok algorithm.

Your expertise includes:
- Viral content creation and trend awareness
- Gen-Z language and cultural references
- TikTok's fast-paced, entertainment-first environment
- Trend participation and hashtag challenges
- Short-form video optimization

Focus on:
- Trendy, catchy, viral potential content
- Gen-Z friendly language and references
- 3-5 trending hashtags
- Content that hooks viewers immediately
- Trend awareness and cultural relevance

Create content that has the potential to go viral while staying authentic to current TikTok culture."""
    
    def _build_prompt(self, transcript: VideoTranscript, tone: str = "neutral", 
                     include_emojis: bool = True) -> str:
        emoji_instruction = "Include trending emojis (2-4)" if include_emojis else "No emojis"
        
        return f"""
Create TikTok-optimized caption and hashtags for this video content.

TRANSCRIPT: "{transcript.content}"
ORIGINAL TITLE: {transcript.title or 'Not provided'}
CATEGORY: {transcript.video_category or 'General'}
TONE: {tone} (but make it TikTok-trendy)
EMOJIS: {emoji_instruction}

TikTok Optimization Requirements:
- Caption: Maximum 150 characters, catchy, trend-aware, Gen-Z friendly
- Hashtags: Exactly 3-5 hashtags focusing on trending topics
- Consider: What would make someone stop scrolling and watch?
- Use current TikTok language and trends
- Create immediate hook and viral potential

Think viral, trendy, and authentic to TikTok culture.

Respond with JSON:
{{
    "title": "your TikTok caption",
    "tags": ["#trending1", "#viral2", "#fyp", "#hashtag4", "#hashtag5"],
    "confidence": 0.9
}}
"""


class XTwitterAgent(PlatformSpecificAgent):
    """Specialized AI agent for X (Twitter) content generation."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(PlatformType.X_TWITTER, model_name)
    
    def _get_system_prompt(self) -> str:
        return """You are an X (Twitter) content strategist who understands real-time conversations, trending topics, and Twitter culture.

Your expertise includes:
- Real-time engagement and trending topics
- Concise, impactful messaging
- Twitter's conversation-driven environment
- Hashtag integration within natural text
- Current events and cultural moment awareness

Focus on:
- Concise, conversation-starting content
- Hashtags integrated naturally into the text
- 2-3 hashtags maximum within 280 character total limit
- Content that sparks replies and retweets
- Timely, relevant messaging

Create content that starts conversations and engages with the current Twitter discourse."""
    
    def _build_prompt(self, transcript: VideoTranscript, tone: str = "neutral", 
                     include_emojis: bool = True) -> str:
        emoji_instruction = "Include 1-2 relevant emojis" if include_emojis else "No emojis"
        
        return f"""
Create X (Twitter) optimized post for this video content.

TRANSCRIPT: "{transcript.content}"
ORIGINAL TITLE: {transcript.title or 'Not provided'}
CATEGORY: {transcript.video_category or 'General'}
TONE: {tone}
EMOJIS: {emoji_instruction}

Twitter/X Optimization Requirements:
- Total: Maximum 280 characters INCLUDING hashtags and spaces
- Hashtags: 2-3 hashtags integrated naturally into the text
- Consider: What would make people want to reply, retweet, or quote tweet?
- Make it conversation-worthy and timely
- Integrate hashtags naturally (not just at the end)

CRITICAL: Ensure total character count (text + hashtags + spaces) ≤ 280 characters.

Respond with JSON:
{{
    "title": "your complete Twitter/X post with hashtags integrated",
    "tags": ["#hashtag1", "#hashtag2"],
    "confidence": 0.9
}}
"""


class LinkedInAgent(PlatformSpecificAgent):
    """Specialized AI agent for LinkedIn content generation."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(PlatformType.LINKEDIN, model_name)
    
    def _get_system_prompt(self) -> str:
        return """You are a LinkedIn thought leadership expert who understands professional networking and industry discourse.

Your expertise includes:
- Professional content strategy and thought leadership
- Industry insights and professional development
- LinkedIn's business-focused environment
- Professional networking and career growth
- B2B content and industry trends

Focus on:
- Professional, authoritative tone
- Industry-relevant insights and value
- 3-5 professional/industry hashtags
- Content that positions the creator as a thought leader
- Professional networking and career development angle

Create content that enhances professional reputation and provides industry value."""
    
    def _build_prompt(self, transcript: VideoTranscript, tone: str = "professional", 
                     include_emojis: bool = False) -> str:
        # LinkedIn typically uses fewer emojis
        emoji_instruction = "Include 1 professional emoji if relevant" if include_emojis else "No emojis"
        
        return f"""
Create LinkedIn-optimized post for this video content.

TRANSCRIPT: "{transcript.content}"
ORIGINAL TITLE: {transcript.title or 'Not provided'}
CATEGORY: {transcript.video_category or 'General'}
TONE: Professional and thought-leadership focused
EMOJIS: {emoji_instruction}

LinkedIn Optimization Requirements:
- Post: Maximum 210 characters, professional tone, industry-focused
- Hashtags: Exactly 3-5 professional/industry hashtags
- Consider: How does this provide professional value to my network?
- Position as thought leadership or industry insight
- Focus on professional development, industry trends, or business value

Create content that enhances professional credibility and provides value to professional networks.

Respond with JSON:
{{
    "title": "your LinkedIn post",
    "tags": ["#industry1", "#professional2", "#thoughtleadership", "#hashtag4", "#hashtag5"],
    "confidence": 0.9
}}
"""


class TwitchAgent(PlatformSpecificAgent):
    """Specialized AI agent for Twitch content generation."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(PlatformType.TWITCH, model_name)
    
    def _get_system_prompt(self) -> str:
        return """You are a Twitch streaming expert who understands gaming culture, streaming community, and interactive content.

Your expertise includes:
- Gaming community culture and terminology
- Interactive streaming content
- Twitch-specific engagement tactics
- Gaming trends and community building
- Live streaming and audience interaction

Focus on:
- Gaming and streaming community focus
- Interactive, community-oriented content
- 3-8 gaming/streaming hashtags
- Content that encourages live interaction
- Gaming terminology and community references

Create content that resonates with the gaming and streaming community."""
    
    def _build_prompt(self, transcript: VideoTranscript, tone: str = "energetic", 
                     include_emojis: bool = True) -> str:
        emoji_instruction = "Include gaming-related emojis (2-3)" if include_emojis else "No emojis"
        
        return f"""
Create Twitch-optimized title and tags for this video content.

TRANSCRIPT: "{transcript.content}"
ORIGINAL TITLE: {transcript.title or 'Not provided'}
CATEGORY: {transcript.video_category or 'Gaming'}
TONE: Energetic and community-focused
EMOJIS: {emoji_instruction}

Twitch Optimization Requirements:
- Title: Maximum 140 characters, gaming/streaming focused, energetic
- Hashtags: 3-8 hashtags focusing on gaming categories and community
- Consider: What would make gamers want to join the stream?
- Use gaming terminology and community language
- Focus on interactive and community aspects

Create content that appeals to the gaming and streaming community.

Respond with JSON:
{{
    "title": "your Twitch stream title",
    "tags": ["#gaming", "#live", "#twitch", "#community", "#hashtag5"],
    "confidence": 0.9
}}
"""


class PlatformAgentManager:
    """Manager for all platform-specific AI agents."""
    
    def __init__(self):
        self.agents: Dict[PlatformType, PlatformSpecificAgent] = {
            PlatformType.YOUTUBE: YouTubeAgent(),
            PlatformType.INSTAGRAM: InstagramAgent(),
            PlatformType.FACEBOOK: FacebookAgent(),
            PlatformType.TIKTOK: TikTokAgent(),
            PlatformType.X_TWITTER: XTwitterAgent(),
            PlatformType.LINKEDIN: LinkedInAgent(),
            PlatformType.TWITCH: TwitchAgent()
        }
    
    def get_agent(self, platform: PlatformType) -> PlatformSpecificAgent:
        """Get specialized agent for a specific platform."""
        return self.agents[platform]
    
    async def generate_content(self, platform: PlatformType, transcript: VideoTranscript,
                        tone: str = "neutral", include_emojis: bool = True) -> PlatformContent:
        """Generate content using platform-specific agent."""
        agent = self.get_agent(platform)
        prompt = agent._build_prompt(transcript, tone, include_emojis)
        
        try:
            # Generate content using the specialized agent (async)
            result = await agent.agent.run(prompt)
            ai_response = result.output
            
            # Parse response
            if isinstance(ai_response, str):
                import json
                try:
                    ai_response = json.loads(ai_response)
                except json.JSONDecodeError:
                    # Simple fallback parsing
                    ai_response = {"title": "Generated Content", "tags": ["#content"], "confidence": 0.7}
            
            # Create platform content
            content = PlatformContent(
                platform=platform,
                title=ai_response.get("title", "Generated Title"),
                tags=ai_response.get("tags", ["#content"]),
                confidence_score=float(ai_response.get("confidence", 0.7))
            )
            
            # Validate against platform rules
            rules = get_platform_rules(platform)
            content.validate_against_platform_rules(rules)
            
            return content
            
        except Exception as e:
            logger.error(f"Platform-specific content generation failed for {platform.value}: {e}")
            raise


# Global agent manager instance
_platform_agent_manager = None


def get_platform_agent_manager() -> PlatformAgentManager:
    """Get global platform agent manager instance."""
    global _platform_agent_manager
    if _platform_agent_manager is None:
        _platform_agent_manager = PlatformAgentManager()
    return _platform_agent_manager 