"""
Tests for AI content generation services.
Tests base AI service, platform-specific agents, and transcript processing.
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import pytest
from unittest.mock import Mock, patch
from models.platform_rules import PlatformType
from models.content import VideoTranscript, PlatformContent
from services.content_generator import ContentGeneratorService, ContentGenerationRequest
from services.platform_agents import PlatformAgentManager, get_platform_agent_manager
from services.transcript_processor import TranscriptProcessor, TranscriptAnalysis


class TestContentGeneratorService:
    """Test base AI content generation service."""
    
    def test_service_initialization(self):
        """Test that the service initializes correctly."""
        # Mock to avoid actual API calls
        with patch('services.content_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.content_generator.OpenAIProvider') as mock_provider:
                with patch('services.content_generator.OpenAIModel') as mock_model:
                    with patch('services.content_generator.Agent') as mock_agent:
                        service = ContentGeneratorService()
                        
                        assert service.model_name == "gpt-4o"
                        assert service.model is not None
                        assert service.agent is not None
    
    def test_base_system_prompt(self):
        """Test base system prompt contains key elements."""
        with patch('services.content_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.content_generator.OpenAIProvider'):
                with patch('services.content_generator.OpenAIModel'):
                    with patch('services.content_generator.Agent'):
                        service = ContentGeneratorService()
                        prompt = service._get_base_system_prompt()
                        
                        # Check key elements are present
                        assert "social media" in prompt.lower()
                        assert "platform" in prompt.lower()
                        assert "engagement" in prompt.lower()
                        assert "json" in prompt.lower()
    
    def test_platform_prompt_building(self):
        """Test platform-specific prompt building."""
        transcript = VideoTranscript(
            content="This is a test video about artificial intelligence and machine learning.",
            title="AI Tutorial",
            video_category="technology"
        )
        
        with patch('services.content_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.content_generator.OpenAIProvider'):
                with patch('services.content_generator.OpenAIModel'):
                    with patch('services.content_generator.Agent'):
                        service = ContentGeneratorService()
                        
                        prompt = service._build_platform_prompt(
                            PlatformType.YOUTUBE, transcript, "energetic", True
                        )
                        
                        # Check platform-specific elements
                        assert "YOUTUBE" in prompt
                        assert "100 characters" in prompt  # YouTube title limit
                        assert "10-15" in prompt  # YouTube tag range
                        assert "energetic" in prompt
                        assert transcript.content in prompt
    
    def test_fallback_response_parsing(self):
        """Test fallback response parsing when JSON is malformed."""
        with patch('services.content_generator.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.content_generator.OpenAIProvider'):
                with patch('services.content_generator.OpenAIModel'):
                    with patch('services.content_generator.Agent'):
                        service = ContentGeneratorService()
                        
                        # Test malformed JSON response
                        malformed_response = '''
                        "title": "Great AI Tutorial",
                        "tags": ["#AI", "#tutorial", "#tech"],
                        "confidence": 0.9
                        '''
                        
                        parsed = service._parse_fallback_response(malformed_response)
                        
                        assert "title" in parsed
                        assert "tags" in parsed
                        assert "confidence" in parsed
                        assert isinstance(parsed["tags"], list)


class TestPlatformAgentManager:
    """Test platform-specific AI agents."""
    
    def test_agent_manager_initialization(self):
        """Test that agent manager initializes all platform agents."""
        with patch('services.platform_agents.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.platform_agents.OpenAIProvider'):
                with patch('services.platform_agents.OpenAIModel'):
                    with patch('services.platform_agents.Agent'):
                        manager = PlatformAgentManager()
                        
                        # Check all platforms have agents
                        assert len(manager.agents) == 7
                        
                        for platform in PlatformType:
                            assert platform in manager.agents
                            agent = manager.get_agent(platform)
                            assert agent is not None
                            assert agent.platform == platform
    
    def test_youtube_agent_prompts(self):
        """Test YouTube agent creates appropriate prompts."""
        transcript = VideoTranscript(
            content="Learn how to build AI applications from scratch in this comprehensive tutorial."
        )
        
        with patch('services.platform_agents.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.platform_agents.OpenAIProvider'):
                with patch('services.platform_agents.OpenAIModel'):
                    with patch('services.platform_agents.Agent'):
                        manager = PlatformAgentManager()
                        youtube_agent = manager.get_agent(PlatformType.YOUTUBE)
                        
                        prompt = youtube_agent._build_prompt(transcript)
                        
                        # Check YouTube-specific elements
                        assert "YouTube" in prompt
                        assert "SEO" in prompt
                        assert "100 characters" in prompt
                        assert "10-15" in prompt
    
    def test_instagram_agent_prompts(self):
        """Test Instagram agent creates appropriate prompts."""
        transcript = VideoTranscript(
            content="Check out this amazing sunset view from my latest travel adventure!"
        )
        
        with patch('services.platform_agents.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.platform_agents.OpenAIProvider'):
                with patch('services.platform_agents.OpenAIModel'):
                    with patch('services.platform_agents.Agent'):
                        manager = PlatformAgentManager()
                        instagram_agent = manager.get_agent(PlatformType.INSTAGRAM)
                        
                        prompt = instagram_agent._build_prompt(transcript)
                        
                        # Check Instagram-specific elements
                        assert "Instagram" in prompt
                        assert "150 characters" in prompt
                        assert "20-30" in prompt
                        assert "visual" in prompt.lower()
    
    def test_twitter_agent_character_limit(self):
        """Test X/Twitter agent emphasizes character limit."""
        transcript = VideoTranscript(
            content="Breaking news in the AI world: new developments that will change everything!"
        )
        
        with patch('services.platform_agents.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.platform_agents.OpenAIProvider'):
                with patch('services.platform_agents.OpenAIModel'):
                    with patch('services.platform_agents.Agent'):
                        manager = PlatformAgentManager()
                        twitter_agent = manager.get_agent(PlatformType.X_TWITTER)
                        
                        prompt = twitter_agent._build_prompt(transcript)
                        
                        # Check Twitter-specific elements
                        assert "280 characters" in prompt
                        assert "total character count" in prompt.lower()
                        assert "hashtags integrated" in prompt.lower()


class TestTranscriptProcessor:
    """Test transcript processing service."""
    
    def test_transcript_cleaning(self):
        """Test transcript cleaning functionality."""
        with patch('services.transcript_processor.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.transcript_processor.OpenAIProvider'):
                with patch('services.transcript_processor.OpenAIModel'):
                    with patch('services.transcript_processor.Agent'):
                        processor = TranscriptProcessor()
                        
                        raw_transcript = """
                        [music] Host: Welcome everyone um to this uh amazing tutorial.
                        Speaker 1: Yes, like, you know, this is going to be great!
                        00:12 [applause] (inaudible) Let's get started with AI.
                        """
                        
                        cleaned = processor.clean_transcript(raw_transcript)
                        
                        # Check cleaning worked
                        assert "[music]" not in cleaned
                        assert "[applause]" not in cleaned
                        assert "(inaudible)" not in cleaned
                        assert "Host:" not in cleaned
                        assert "Speaker 1:" not in cleaned
                        assert "00:12" not in cleaned
                        assert "um" not in cleaned
                        assert "uh" not in cleaned
                        assert "like" not in cleaned
                        assert len(cleaned) > 0
    
    def test_keyword_extraction(self):
        """Test keyword extraction from content."""
        with patch('services.transcript_processor.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.transcript_processor.OpenAIProvider'):
                with patch('services.transcript_processor.OpenAIModel'):
                    with patch('services.transcript_processor.Agent'):
                        processor = TranscriptProcessor()
                        
                        content = """
                        Artificial intelligence machine learning deep neural networks
                        technology programming python artificial intelligence algorithms
                        machine learning data science artificial intelligence
                        """
                        
                        keywords = processor.extract_keywords(content, 5)
                        
                        # Check keywords are extracted
                        assert len(keywords) > 0
                        assert "artificial" in keywords
                        assert "intelligence" in keywords
                        assert "machine" in keywords
                        assert "learning" in keywords
                        
                        # Check stop words are filtered
                        assert "the" not in keywords
                        assert "and" not in keywords
                        assert "to" not in keywords
    
    def test_tone_determination(self):
        """Test basic tone determination."""
        with patch('services.transcript_processor.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.transcript_processor.OpenAIProvider'):
                with patch('services.transcript_processor.OpenAIModel'):
                    with patch('services.transcript_processor.Agent'):
                        processor = TranscriptProcessor()
                        
                        # Test positive tone
                        positive_content = "This is amazing! Fantastic results! Great work! Excellent progress!"
                        assert processor.determine_basic_tone(positive_content) == "positive"
                        
                        # Test professional tone
                        professional_content = "Our research methodology framework implementation optimization strategy analysis"
                        assert processor.determine_basic_tone(professional_content) == "professional"
                        
                        # Test casual tone
                        casual_content = "Hey guys! This is so cool and fun! Epic stuff folks!"
                        assert processor.determine_basic_tone(casual_content) == "casual"
    
    def test_reading_time_estimation(self):
        """Test reading time estimation."""
        with patch('services.transcript_processor.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.transcript_processor.OpenAIProvider'):
                with patch('services.transcript_processor.OpenAIModel'):
                    with patch('services.transcript_processor.Agent'):
                        processor = TranscriptProcessor()
                        
                        # Test with known word count
                        content = " ".join(["word"] * 200)  # 200 words
                        reading_time = processor.estimate_reading_time(content)
                        
                        # Should be approximately 60 seconds (200 words / 200 WPM * 60)
                        assert 55 <= reading_time <= 65
    
    def test_basic_analysis_creation(self):
        """Test basic analysis when AI fails."""
        transcript = VideoTranscript(
            content="This is a comprehensive tutorial about artificial intelligence and machine learning applications in modern technology."
        )
        
        with patch('services.transcript_processor.settings') as mock_settings:
            mock_settings.openai_api_key = "test_key"
            
            with patch('services.transcript_processor.OpenAIProvider'):
                with patch('services.transcript_processor.OpenAIModel'):
                    with patch('services.transcript_processor.Agent'):
                        processor = TranscriptProcessor()
                        
                        analysis = processor._create_basic_analysis(transcript.content, transcript)
                        
                        assert isinstance(analysis, TranscriptAnalysis)
                        assert analysis.word_count > 0
                        assert len(analysis.keywords) > 0
                        assert analysis.tone in ["professional", "casual", "positive", "serious", "neutral"]
                        assert analysis.sentiment == "neutral"
                        assert analysis.estimated_reading_time > 0


def run_ai_service_tests():
    """Run all AI service tests."""
    print("🧪 Running AI Service Tests...\n")
    
    # Test ContentGeneratorService
    print("Testing ContentGeneratorService...")
    try:
        test_service = TestContentGeneratorService()
        test_service.test_service_initialization()
        test_service.test_base_system_prompt()
        test_service.test_platform_prompt_building()
        test_service.test_fallback_response_parsing()
        print("✅ ContentGeneratorService Tests - PASSED\n")
    except Exception as e:
        print(f"❌ ContentGeneratorService Tests - FAILED: {e}\n")
        return False
    
    # Test PlatformAgentManager
    print("Testing PlatformAgentManager...")
    try:
        test_manager = TestPlatformAgentManager()
        test_manager.test_agent_manager_initialization()
        test_manager.test_youtube_agent_prompts()
        test_manager.test_instagram_agent_prompts()
        test_manager.test_twitter_agent_character_limit()
        print("✅ PlatformAgentManager Tests - PASSED\n")
    except Exception as e:
        print(f"❌ PlatformAgentManager Tests - FAILED: {e}\n")
        return False
    
    # Test TranscriptProcessor
    print("Testing TranscriptProcessor...")
    try:
        test_processor = TestTranscriptProcessor()
        test_processor.test_transcript_cleaning()
        test_processor.test_keyword_extraction()
        test_processor.test_tone_determination()
        test_processor.test_reading_time_estimation()
        test_processor.test_basic_analysis_creation()
        print("✅ TranscriptProcessor Tests - PASSED\n")
    except Exception as e:
        print(f"❌ TranscriptProcessor Tests - FAILED: {e}\n")
        return False
    
    print("🎉 All AI Service Tests PASSED!")
    print("✅ Task 4.1: Base AI Service Setup - COMPLETE")
    print("✅ Task 4.2: Platform-Specific AI Agents - COMPLETE") 
    print("✅ Task 4.3: Transcript Processing Service - COMPLETE")
    return True


if __name__ == "__main__":
    success = run_ai_service_tests()
    if not success:
        exit(1) 