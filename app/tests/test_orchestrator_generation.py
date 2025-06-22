"""
Tests for the updated ContentOrchestrator with expanded field generation and parsing.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.orchestrator import ContentOrchestrator
from app.models.platform_rules import PlatformType
from app.models.content import VideoTranscript, PlatformContent


class TestOrchestratorGeneration:
    """Tests for the expanded orchestrator functionality."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator instance."""
        return ContentOrchestrator()
    
    @pytest.fixture
    def sample_transcript(self):
        """Create a sample video transcript for testing."""
        return VideoTranscript(
            content="This is a tutorial about Python programming. We'll cover variables, functions, and best practices for beginners.",
            title="Python Programming Tutorial",
            video_category="Education",
            duration_seconds=600
        )
    
    def test_get_platform_fields_youtube(self, orchestrator):
        """Test that YouTube platform fields are correctly defined."""
        fields = orchestrator._get_platform_fields(PlatformType.YOUTUBE)
        
        assert "title" in fields
        assert "description" in fields
        assert "tags" in fields
        assert "5000 chars" in fields["description"]
        assert "157 crucial" in fields["description"]
    
    def test_get_platform_fields_instagram(self, orchestrator):
        """Test that Instagram platform fields are correctly defined."""
        fields = orchestrator._get_platform_fields(PlatformType.INSTAGRAM)
        
        assert "title" in fields
        assert "caption" in fields
        assert "tags" in fields
        assert "truncated at 125" in fields["caption"]
        assert "20-30 for reach" in fields["tags"]
    
    def test_get_platform_fields_linkedin(self, orchestrator):
        """Test that LinkedIn platform fields are correctly defined."""
        fields = orchestrator._get_platform_fields(PlatformType.LINKEDIN)
        
        assert "title" in fields
        assert "post_body" in fields
        assert "headline" in fields
        assert "tags" in fields
        assert "Professional" in fields["headline"]
    
    def test_parse_response_valid_json(self, orchestrator):
        """Test parsing a valid JSON response."""
        mock_response = '''
        ```json
        {
          "title": "Amazing Python Tutorial",
          "description": "Learn Python programming from scratch with this comprehensive guide",
          "tags": ["#python", "#programming", "#tutorial", "#coding"]
        }
        ```
        '''
        
        result = orchestrator._parse_response(mock_response, PlatformType.YOUTUBE)
        
        assert result["title"] == "Amazing Python Tutorial"
        assert result["description"] == "Learn Python programming from scratch with this comprehensive guide"
        assert len(result["tags"]) == 4
        assert "#python" in result["tags"]
        assert "#programming" in result["tags"]
    
    def test_parse_response_malformed_json_fallback(self, orchestrator):
        """Test parsing when JSON is malformed but fields can be extracted."""
        mock_response = '''
        title: "Python Programming Guide"
        description: "A comprehensive tutorial for beginners"
        tags: ["#python", "#tutorial", "#beginner"]
        '''
        
        result = orchestrator._parse_response(mock_response, PlatformType.YOUTUBE)
        
        assert result["title"] == "Python Programming Guide"
        assert result["description"] == "A comprehensive tutorial for beginners"
        assert "#python" in result["tags"]
    
    def test_parse_response_instagram_with_caption(self, orchestrator):
        """Test parsing Instagram response with caption field."""
        mock_response = '''
        {
          "title": "Beautiful Sunset",
          "caption": "Caught this amazing sunset today! Nature never fails to inspire creativity and peace. 🌅✨",
          "tags": ["#sunset", "#nature", "#photography", "#inspiration", "#peaceful"]
        }
        '''
        
        result = orchestrator._parse_response(mock_response, PlatformType.INSTAGRAM)
        
        assert result["title"] == "Beautiful Sunset"
        assert result["caption"] == "Caught this amazing sunset today! Nature never fails to inspire creativity and peace. 🌅✨"
        assert len(result["tags"]) == 5
        assert "#sunset" in result["tags"]
        assert "#photography" in result["tags"]
    
    def test_parse_response_linkedin_with_professional_fields(self, orchestrator):
        """Test parsing LinkedIn response with professional fields."""
        mock_response = '''
        ```json
        {
          "title": "Leadership Insights",
          "post_body": "Excited to share key insights from my journey in tech leadership. Building great teams starts with trust.",
          "headline": "Senior Software Engineer | Tech Lead | Mentor",
          "tags": ["#leadership", "#technology", "#teamwork"]
        }
        ```
        '''
        
        result = orchestrator._parse_response(mock_response, PlatformType.LINKEDIN)
        
        assert result["title"] == "Leadership Insights"
        assert result["post_body"] == "Excited to share key insights from my journey in tech leadership. Building great teams starts with trust."
        assert result["headline"] == "Senior Software Engineer | Tech Lead | Mentor"
        assert "#leadership" in result["tags"]
    
    def test_parse_response_twitch_with_stream_category(self, orchestrator):
        """Test parsing Twitch response with stream category."""
        mock_response = '''
        {
          "title": "Epic Minecraft Build Stream",
          "stream_category": "Minecraft",
          "tags": ["#minecraft", "#building", "#creative", "#stream"]
        }
        '''
        
        result = orchestrator._parse_response(mock_response, PlatformType.TWITCH)
        
        assert result["title"] == "Epic Minecraft Build Stream"
        assert result["stream_category"] == "Minecraft"
        assert "#minecraft" in result["tags"]
        assert "#building" in result["tags"]
    
    def test_parse_response_facebook_with_post_body(self, orchestrator):
        """Test parsing Facebook response with post body."""
        mock_response = '''
        ```json
        {
          "title": "Community Update",
          "post_body": "Great news everyone! Our community is growing strong. Thanks for all your support! 🎉",
          "tags": ["#community", "#grateful", "#support"]
        }
        ```
        '''
        
        result = orchestrator._parse_response(mock_response, PlatformType.FACEBOOK)
        
        assert result["title"] == "Community Update"
        assert result["post_body"] == "Great news everyone! Our community is growing strong. Thanks for all your support! 🎉"
        assert "#community" in result["tags"]
    
    def test_parse_response_x_twitter_with_post_body(self, orchestrator):
        """Test parsing X/Twitter response with post body."""
        mock_response = '''
        {
          "title": "Tech News",
          "post_body": "Just discovered this amazing new Python library! Game changer for data processing 🚀",
          "tags": ["#python", "#tech"]
        }
        '''
        
        result = orchestrator._parse_response(mock_response, PlatformType.X_TWITTER)
        
        assert result["title"] == "Tech News"
        assert result["post_body"] == "Just discovered this amazing new Python library! Game changer for data processing 🚀"
        assert "#python" in result["tags"]
        assert "#tech" in result["tags"]
    
    def test_parse_response_empty_fallback(self, orchestrator):
        """Test parsing when response is empty or unparseable."""
        mock_response = "This is not a valid response format at all"
        
        result = orchestrator._parse_response(mock_response, PlatformType.YOUTUBE)
        
        # Should still return basic structure with fallback values
        assert "title" in result
        assert "tags" in result
        assert result["title"] == "Youtube Post"  # Default fallback
        assert len(result["tags"]) > 0
    
    def test_process_tags_string_input(self, orchestrator):
        """Test tag processing with string input."""
        raw_tags = "#python #programming #tutorial"
        processed = orchestrator._process_tags(raw_tags)
        
        assert "#python" in processed
        assert "#programming" in processed
        assert "#tutorial" in processed
        assert len(processed) == 3
    
    def test_process_tags_list_input(self, orchestrator):
        """Test tag processing with list input."""
        raw_tags = ["#python", "#programming", "tutorial", "#coding"]
        processed = orchestrator._process_tags(raw_tags)
        
        assert "#python" in processed
        assert "#programming" in processed
        assert "#tutorial" in processed  # Should add # prefix
        assert "#coding" in processed
        assert len(processed) == 4
    
    def test_process_tags_mixed_formats(self, orchestrator):
        """Test tag processing with mixed hashtag formats."""
        raw_tags = ["#python programming", "tutorial", "#coding #data"]
        processed = orchestrator._process_tags(raw_tags)
        
        # Should extract individual hashtags properly
        assert "#python" in processed
        assert "#programming" in processed
        assert "#tutorial" in processed
        assert "#coding" in processed
        assert "#data" in processed
    
    def test_process_tags_removes_duplicates(self, orchestrator):
        """Test that tag processing removes duplicates."""
        raw_tags = ["#python", "#python", "#coding", "#python"]
        processed = orchestrator._process_tags(raw_tags)
        
        assert processed.count("#python") == 1
        assert processed.count("#coding") == 1
        assert len(processed) == 2
    
    @pytest.mark.asyncio
    async def test_generate_content_mock_response_youtube(self, orchestrator, sample_transcript):
        """Test content generation with mocked AI response for YouTube."""
        mock_response = '''
        ```json
        {
          "title": "Python Programming Tutorial for Beginners",
          "description": "Learn Python programming from scratch! This comprehensive tutorial covers variables, functions, and best practices. Perfect for beginners who want to start their coding journey with Python.",
          "tags": ["#python", "#programming", "#tutorial", "#coding", "#beginners", "#learn", "#variables", "#functions", "#bestpractices", "#education"]
        }
        ```
        '''
        
        # Mock the agent response
        orchestrator.agent = AsyncMock()
        orchestrator.agent.run.return_value = MagicMock(output=mock_response)
        
        result = await orchestrator.generate_content(PlatformType.YOUTUBE, sample_transcript)
        
        assert hasattr(result, 'platform')
        assert result.platform == PlatformType.YOUTUBE
        assert result.title == "Python Programming Tutorial for Beginners"
        assert result.description is not None
        assert len(result.description) > 100  # Should have substantial description
        assert len(result.tags) == 10
        assert "#python" in result.tags
        assert "#programming" in result.tags
        assert result.confidence_score > 0.8
    
    @pytest.mark.asyncio
    async def test_generate_content_mock_response_instagram(self, orchestrator, sample_transcript):
        """Test content generation with mocked AI response for Instagram."""
        mock_response = '''
        {
          "title": "Python Programming Magic ✨",
          "caption": "Ready to dive into the world of Python programming? 🐍✨ This tutorial covers everything you need to know as a beginner - from variables to functions and beyond! Swipe to see some code examples 👆 Who else is learning Python? Drop a 🐍 in the comments!",
          "tags": ["#python", "#programming", "#coding", "#tutorial", "#learntocode", "#pythonprogramming", "#codinglife", "#developer", "#tech", "#education", "#beginnercoder", "#pythontutorial", "#codingbootcamp", "#programminglife", "#webdeveloper", "#dataprscience", "#machinelearning", "#pythonbasics", "#codingcommunity", "#programmerlife"]
        }
        '''
        
        # Mock the agent response
        orchestrator.agent = AsyncMock()
        orchestrator.agent.run.return_value = MagicMock(output=mock_response)
        
        result = await orchestrator.generate_content(PlatformType.INSTAGRAM, sample_transcript)
        
        assert hasattr(result, 'platform')
        assert result.platform == PlatformType.INSTAGRAM
        assert result.title == "Python Programming Magic ✨"
        assert result.caption is not None
        assert len(result.caption) > 200  # Should have substantial caption
        assert len(result.tags) >= 15  # Instagram should have many tags
        assert "#python" in result.tags
        assert "#programming" in result.tags
    
    @pytest.mark.asyncio
    async def test_generate_content_mock_response_linkedin(self, orchestrator, sample_transcript):
        """Test content generation with mocked AI response for LinkedIn."""
        mock_response = '''
        ```json
        {
          "title": "Python Programming Fundamentals",
          "post_body": "Excited to share this comprehensive Python programming tutorial! As technology continues to evolve, programming skills become increasingly valuable across all industries. This tutorial covers essential concepts like variables, functions, and best practices - perfect for professionals looking to expand their technical skillset. What programming languages are you currently learning?",
          "headline": "Software Developer | Python Enthusiast | Tech Educator",
          "tags": ["#python", "#programming", "#professionaldevelopment", "#technology", "#coding"]
        }
        ```
        '''
        
        # Mock the agent response
        orchestrator.agent = AsyncMock()
        orchestrator.agent.run.return_value = MagicMock(output=mock_response)
        
        result = await orchestrator.generate_content(PlatformType.LINKEDIN, sample_transcript)
        
        assert hasattr(result, 'platform')
        assert result.platform == PlatformType.LINKEDIN
        assert result.title == "Python Programming Fundamentals"
        assert result.post_body is not None
        assert result.headline is not None
        assert "Software Developer" in result.headline
        assert len(result.tags) <= 5  # LinkedIn should have fewer tags
        assert "#professionaldevelopment" in result.tags
    
    @pytest.mark.asyncio
    async def test_generate_content_error_handling(self, orchestrator, sample_transcript):
        """Test content generation error handling with fallback."""
        # Mock the agent to raise an exception
        orchestrator.agent = AsyncMock()
        orchestrator.agent.run.side_effect = Exception("AI service unavailable")
        
        result = await orchestrator.generate_content(PlatformType.YOUTUBE, sample_transcript)
        
        assert hasattr(result, 'platform')
        assert result.platform == PlatformType.YOUTUBE
        assert result.title == "Youtube Post"  # Fallback title
        assert len(result.tags) >= 3  # Should have fallback tags
        assert result.confidence_score < 0.5  # Low confidence for fallback 