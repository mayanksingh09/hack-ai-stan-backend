"""
Transcript processing service for cleaning, summarizing, and extracting key themes
from video transcripts before content generation.
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from config import settings
from models.content import VideoTranscript

logger = logging.getLogger(__name__)


class TranscriptAnalysis(BaseModel):
    """Analysis results for a processed transcript."""
    
    cleaned_content: str
    key_themes: List[str]
    summary: str
    tone: str
    category: Optional[str] = None
    keywords: List[str]
    sentiment: str
    word_count: int
    estimated_reading_time: int  # in seconds


class TranscriptProcessor:
    """Service for processing and analyzing video transcripts."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.agent = self._create_analysis_agent()
        
        # Common words to filter out from keywords
        self.stop_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
            'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my',
            'one', 'all', 'would', 'there', 'their', 'what', 'so',
            'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
            'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
            'him', 'know', 'take', 'people', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than',
            'then', 'now', 'look', 'only', 'come', 'its', 'over',
            'think', 'also', 'back', 'after', 'use', 'two', 'how',
            'our', 'work', 'first', 'well', 'way', 'even', 'new',
            'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
        }
    
    def _create_analysis_agent(self) -> Agent:
        """Create AI agent for transcript analysis."""
        provider = OpenAIProvider(api_key=settings.openai_api_key)
        model = OpenAIModel(self.model_name, provider=provider)
        
        system_prompt = """You are an expert content analyst specializing in video transcript analysis.

Your expertise includes:
- Identifying key themes and topics in video content
- Extracting relevant keywords for social media optimization
- Determining content tone and sentiment
- Categorizing content types
- Creating concise, accurate summaries
- Understanding context and meaning

Focus on:
- Accuracy in theme identification
- Relevant keyword extraction for social media
- Appropriate tone and sentiment analysis
- Clear, concise summaries
- Content categorization for better targeting

Always provide structured, actionable insights for social media content creation."""
        
        return Agent(model=model, system_prompt=system_prompt)
    
    def clean_transcript(self, raw_content: str) -> str:
        """Clean and normalize transcript content."""
        if not raw_content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', raw_content.strip())
        
        # Remove common transcript artifacts
        content = re.sub(r'\[.*?\]', '', content)  # Remove [music], [applause] etc.
        content = re.sub(r'\(.*?\)', '', content)  # Remove (inaudible), (laughter) etc.
        
        # Remove speaker indicators like "Speaker 1:", "Host:", etc.
        content = re.sub(r'^[A-Za-z0-9\s]+:\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\s+[A-Za-z0-9\s]+:\s*', ' ', content)  # Remove mid-line speaker indicators
        
        # Remove timestamps like "00:12" or "1:23:45"
        content = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', '', content)
        
        # Remove filler words and hesitations
        filler_words = ['um', 'uh', 'hmm', 'er', 'ah', 'like', 'you know', 'so']
        for filler in filler_words:
            content = re.sub(rf'\b{filler}\b', '', content, flags=re.IGNORECASE)
        
        # Clean up multiple spaces and punctuation
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'[,;]\s*[,;]+', ',', content)  # Multiple commas/semicolons
        content = re.sub(r'\.\s*\.+', '.', content)  # Multiple periods
        
        # Ensure proper sentence structure
        content = re.sub(r'(?<=[a-z])\s+(?=[A-Z])', '. ', content)
        
        return content.strip()
    
    def extract_keywords(self, content: str, max_keywords: int = 15) -> List[str]:
        """Extract relevant keywords from content."""
        # Convert to lowercase and split into words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
        
        # Filter out stop words
        keywords = [word for word in words if word not in self.stop_words]
        
        # Count frequency
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # For shorter content, include single-occurrence words; for longer content, require freq > 1
        min_freq = 1 if len(keywords) < 50 else 2
        return [word for word, freq in sorted_keywords[:max_keywords] if freq >= min_freq]
    
    def estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in seconds (average 200 WPM)."""
        word_count = len(content.split())
        # Average reading speed: 200 words per minute
        return int((word_count / 200) * 60)
    
    def determine_basic_tone(self, content: str) -> str:
        """Determine basic tone from content using simple heuristics."""
        content_lower = content.lower()
        
        # Positive indicators
        positive_words = ['great', 'amazing', 'excellent', 'fantastic', 'wonderful', 
                         'awesome', 'brilliant', 'perfect', 'love', 'best']
        
        # Negative indicators
        negative_words = ['terrible', 'awful', 'horrible', 'worst', 'hate', 
                         'bad', 'problem', 'issue', 'difficult', 'challenging']
        
        # Professional indicators
        professional_words = ['research', 'analysis', 'strategy', 'methodology',
                             'framework', 'implementation', 'optimization']
        
        # Casual indicators
        casual_words = ['hey', 'guys', 'folks', 'cool', 'fun', 'awesome', 'epic']
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        professional_count = sum(1 for word in professional_words if word in content_lower)
        casual_count = sum(1 for word in casual_words if word in content_lower)
        
        if professional_count > casual_count:
            return "professional"
        elif casual_count > professional_count:
            return "casual"
        elif positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "serious"
        else:
            return "neutral"
    
    def analyze_transcript_with_ai(self, transcript: VideoTranscript) -> TranscriptAnalysis:
        """Analyze transcript using AI for detailed insights."""
        cleaned_content = self.clean_transcript(transcript.content)
        
        # Check if content needs summarization (>1000 words)
        word_count = len(cleaned_content.split())
        needs_summary = word_count > 1000
        
        analysis_prompt = f"""
Analyze this video transcript and provide structured insights for social media content creation.

TRANSCRIPT: "{cleaned_content}"
ORIGINAL TITLE: {transcript.title or 'Not provided'}
CATEGORY: {transcript.video_category or 'Not specified'}

Please analyze and provide:

1. KEY THEMES: Identify 3-5 main themes or topics discussed
2. SUMMARY: Create a concise summary (2-3 sentences) capturing the essence
3. TONE: Determine the overall tone (professional, casual, energetic, educational, entertaining, etc.)
4. CONTENT CATEGORY: Categorize the content (tech, lifestyle, education, gaming, business, etc.)
5. KEYWORDS: Extract 8-12 important keywords relevant for social media hashtags
6. SENTIMENT: Overall sentiment (positive, neutral, negative, mixed)

{"If the content is very long, focus on the most important themes and create a condensed summary." if needs_summary else ""}

Respond with JSON in this exact format:
{{
    "key_themes": ["theme1", "theme2", "theme3"],
    "summary": "2-3 sentence summary of the main content",
    "tone": "content tone",
    "category": "content category",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"],
    "sentiment": "overall sentiment"
}}
"""
        
        try:
            # Get AI analysis
            result = self.agent.run_sync(analysis_prompt)
            ai_response = result.output
            
            # Parse AI response
            if isinstance(ai_response, str):
                import json
                try:
                    analysis_data = json.loads(ai_response)
                except json.JSONDecodeError:
                    # Fallback to basic analysis
                    return self._create_basic_analysis(cleaned_content, transcript)
            else:
                analysis_data = ai_response
            
            # Create analysis object
            analysis = TranscriptAnalysis(
                cleaned_content=cleaned_content,
                key_themes=analysis_data.get("key_themes", ["general"]),
                summary=analysis_data.get("summary", "Content summary not available"),
                tone=analysis_data.get("tone", self.determine_basic_tone(cleaned_content)),
                category=analysis_data.get("category", transcript.video_category),
                keywords=analysis_data.get("keywords", self.extract_keywords(cleaned_content, 10)),
                sentiment=analysis_data.get("sentiment", "neutral"),
                word_count=word_count,
                estimated_reading_time=self.estimate_reading_time(cleaned_content)
            )
            
            logger.info(f"Transcript analyzed successfully: {word_count} words, {len(analysis.key_themes)} themes")
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed, falling back to basic analysis: {e}")
            return self._create_basic_analysis(cleaned_content, transcript)
    
    def _create_basic_analysis(self, cleaned_content: str, transcript: VideoTranscript) -> TranscriptAnalysis:
        """Create basic analysis when AI analysis fails."""
        word_count = len(cleaned_content.split())
        keywords = self.extract_keywords(cleaned_content, 10)
        
        # Simple summary (first 2 sentences)
        sentences = re.split(r'[.!?]+', cleaned_content)
        summary = '. '.join(sentences[:2]).strip()
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return TranscriptAnalysis(
            cleaned_content=cleaned_content,
            key_themes=keywords[:3] if keywords else ["content"],
            summary=summary or "Content summary not available",
            tone=self.determine_basic_tone(cleaned_content),
            category=transcript.video_category or "general",
            keywords=keywords,
            sentiment="neutral",
            word_count=word_count,
            estimated_reading_time=self.estimate_reading_time(cleaned_content)
        )
    
    def process_transcript(self, transcript: VideoTranscript) -> Tuple[VideoTranscript, TranscriptAnalysis]:
        """Process transcript and return cleaned version with analysis."""
        try:
            # Analyze transcript
            analysis = self.analyze_transcript_with_ai(transcript)
            
            # Create enhanced transcript
            enhanced_transcript = VideoTranscript(
                content=analysis.cleaned_content,
                title=transcript.title,
                duration_seconds=transcript.duration_seconds,
                language=transcript.language,
                video_category=analysis.category or transcript.video_category,
                metadata={
                    **transcript.metadata,
                    "word_count": analysis.word_count,
                    "estimated_reading_time": analysis.estimated_reading_time,
                    "key_themes": analysis.key_themes,
                    "tone": analysis.tone,
                    "sentiment": analysis.sentiment
                }
            )
            
            logger.info("Transcript processing completed successfully")
            return enhanced_transcript, analysis
            
        except Exception as e:
            logger.error(f"Transcript processing failed: {e}")
            # Return original transcript with basic cleaning
            cleaned_content = self.clean_transcript(transcript.content)
            basic_analysis = self._create_basic_analysis(cleaned_content, transcript)
            
            enhanced_transcript = VideoTranscript(
                content=cleaned_content,
                title=transcript.title,
                duration_seconds=transcript.duration_seconds,
                language=transcript.language,
                video_category=transcript.video_category,
                metadata=transcript.metadata
            )
            
            return enhanced_transcript, basic_analysis
    
    def get_content_suggestions(self, analysis: TranscriptAnalysis) -> Dict[str, List[str]]:
        """Get content suggestions based on transcript analysis."""
        suggestions = {
            "title_keywords": analysis.keywords[:5],
            "hashtag_suggestions": [f"#{keyword}" for keyword in analysis.keywords[:8]],
            "tone_recommendations": [],
            "platform_suggestions": []
        }
        
        # Tone recommendations based on analysis
        if analysis.tone == "professional":
            suggestions["tone_recommendations"] = ["LinkedIn", "formal", "business-focused"]
            suggestions["platform_suggestions"] = ["LinkedIn", "Facebook"]
        elif analysis.tone == "casual":
            suggestions["tone_recommendations"] = ["Instagram", "TikTok", "friendly"]
            suggestions["platform_suggestions"] = ["Instagram", "TikTok", "X/Twitter"]
        elif analysis.tone == "educational":
            suggestions["tone_recommendations"] = ["YouTube", "informative", "tutorial"]
            suggestions["platform_suggestions"] = ["YouTube", "LinkedIn"]
        else:
            suggestions["tone_recommendations"] = ["adaptable", "versatile"]
            suggestions["platform_suggestions"] = ["YouTube", "Instagram", "Facebook"]
        
        # Category-based suggestions
        if analysis.category:
            category_lower = analysis.category.lower()
            if "tech" in category_lower or "ai" in category_lower:
                suggestions["platform_suggestions"].extend(["LinkedIn", "X/Twitter"])
            elif "gaming" in category_lower:
                suggestions["platform_suggestions"].extend(["Twitch", "TikTok"])
            elif "lifestyle" in category_lower:
                suggestions["platform_suggestions"].extend(["Instagram", "Facebook"])
        
        # Remove duplicates
        suggestions["platform_suggestions"] = list(set(suggestions["platform_suggestions"]))
        
        return suggestions


# Global transcript processor instance
_transcript_processor = None


def get_transcript_processor() -> TranscriptProcessor:
    """Get global transcript processor instance."""
    global _transcript_processor
    if _transcript_processor is None:
        _transcript_processor = TranscriptProcessor()
    return _transcript_processor 