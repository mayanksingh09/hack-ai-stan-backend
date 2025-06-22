"""
Tests for Phase 6 API endpoints.
Tests single platform generation, batch generation, and platform rules endpoints.
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from models.platform_rules import PlatformType
from models.content import VideoTranscript, PlatformContent, BatchGenerationRequest
from main import app

# Create test client
client = TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints for content generation."""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns correct information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "supported_platforms" in data
        assert "api_endpoints" in data
        assert len(data["supported_platforms"]) == 7
    
    def test_get_supported_platforms(self):
        """Test getting supported platforms list."""
        response = client.get("/api/v1/platforms")
        assert response.status_code == 200
        
        data = response.json()
        assert "platforms" in data
        assert "total_supported" in data
        assert data["total_supported"] == 7
        
        # Check that all expected platforms are present
        expected_platforms = ["youtube", "instagram", "facebook", "tiktok", "x_twitter", "linkedin", "twitch"]
        for platform in expected_platforms:
            assert platform in data["platforms"]
            platform_info = data["platforms"][platform]
            assert "name" in platform_info
            assert "title_max_length" in platform_info
            assert "tag_range" in platform_info
    
    def test_get_platform_rules_valid_platform(self):
        """Test getting rules for a valid platform."""
        response = client.get("/api/v1/platforms/youtube/rules")
        assert response.status_code == 200
        
        data = response.json()
        assert data["platform"] == "youtube"
        assert "rules" in data
        assert "examples" in data
        
        rules = data["rules"]
        assert "title_max_length" in rules
        assert "tag_min_count" in rules
        assert "tag_max_count" in rules
        assert rules["title_max_length"] == 100
        assert rules["tag_min_count"] == 10
        assert rules["tag_max_count"] == 15
        
        examples = data["examples"]
        assert "title_examples" in examples
        assert "tag_examples" in examples
        assert len(examples["title_examples"]) > 0
        assert len(examples["tag_examples"]) > 0
    
    def test_get_platform_rules_invalid_platform(self):
        """Test getting rules for an invalid platform."""
        response = client.get("/api/v1/platforms/invalid_platform/rules")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not supported" in data["detail"]
    
    @patch('routers.content_generation.get_content_orchestrator')
    @patch('routers.content_generation.get_content_validator')
    def test_generate_single_platform_success(self, mock_validator_getter, mock_orchestrator_getter):
        """Test successful single platform content generation."""
        # Mock services
        mock_orchestrator = Mock()
        mock_validator = Mock()
        mock_orchestrator_getter.return_value = mock_orchestrator
        mock_validator_getter.return_value = mock_validator
        
        # Mock successful generation
        mock_content = PlatformContent(
            platform=PlatformType.YOUTUBE,
            title="Test AI Tutorial",
            tags=["#AI", "#tutorial", "#tech", "#programming", "#python",
                  "#education", "#learning", "#code", "#development", "#beginner"],
            confidence_score=0.9
        )
        mock_orchestrator.generate_single_platform.return_value = mock_content
        
        # Mock validation
        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.score = 85.0
        mock_validator.validate_content.return_value = mock_validation
        mock_validator.suggest_improvements.return_value = []
        
        # Test request
        request_data = {
            "transcript": {
                "content": "This is a comprehensive tutorial about artificial intelligence and machine learning."
            }
        }
        
        response = client.post("/api/v1/generate/youtube", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["platform"] == "youtube"
        assert "content" in data
        assert data["validation_passed"] is True
        assert data["quality_score"] == 85.0
        assert "processing_time_seconds" in data
    
    def test_generate_single_platform_invalid_platform(self):
        """Test single platform generation with invalid platform."""
        request_data = {
            "transcript": {
                "content": "This is a test transcript."
            }
        }
        
        response = client.post("/api/v1/generate/invalid_platform", json=request_data)
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not supported" in data["detail"]
    
    def test_generate_single_platform_short_transcript(self):
        """Test single platform generation with too short transcript."""
        request_data = {
            "transcript": {
                "content": "Short"
            }
        }
        
        response = client.post("/api/v1/generate/youtube", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "at least 10 characters" in data["detail"]
    
    @patch('routers.content_generation.get_content_orchestrator')
    def test_generate_batch_content_success(self, mock_orchestrator_getter):
        """Test successful batch content generation."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator_getter.return_value = mock_orchestrator
        
        # Mock successful batch response
        mock_response = Mock()
        mock_response.request_id = "test-123"
        mock_response.generated_content = {
            "youtube": PlatformContent(
                platform=PlatformType.YOUTUBE,
                title="YouTube Title",
                tags=["#test"] * 10,
                confidence_score=0.9
            ),
            "instagram": PlatformContent(
                platform=PlatformType.INSTAGRAM,
                title="Instagram Caption",
                tags=["#test"] * 25,
                confidence_score=0.8
            )
        }
        mock_response.processing_time_seconds = 5.2
        mock_response.success_count = 2
        mock_response.error_count = 0
        mock_response.errors = None
        
        mock_orchestrator.generate_batch_content.return_value = mock_response
        
        # Test request
        request_data = {
            "transcript": {
                "content": "This is a comprehensive tutorial about artificial intelligence and machine learning."
            },
            "platforms": ["youtube", "instagram"]
        }
        
        response = client.post("/api/v1/generate/batch", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success_count"] == 2
        assert data["error_count"] == 0
        assert "generated_content" in data
        assert len(data["generated_content"]) == 2
    
    def test_generate_batch_content_invalid_platforms(self):
        """Test batch generation with invalid platforms."""
        request_data = {
            "transcript": {
                "content": "This is a test transcript for batch generation."
            },
            "platforms": ["invalid_platform"]
        }
        
        response = client.post("/api/v1/generate/batch", json=request_data)
        assert response.status_code == 400
    
    def test_generate_batch_content_short_transcript(self):
        """Test batch generation with too short transcript."""
        request_data = {
            "transcript": {
                "content": "Short"
            },
            "platforms": ["youtube", "instagram"]
        }
        
        response = client.post("/api/v1/generate/batch", json=request_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "at least 10 characters" in data["detail"]
    
    @patch('routers.content_generation.get_content_validator')
    def test_validate_existing_content_valid(self, mock_validator_getter):
        """Test validation of existing content."""
        # Mock validator
        mock_validator = Mock()
        mock_validator_getter.return_value = mock_validator
        
        # Mock validation result
        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.score = 95.0
        mock_validation.issues = []
        mock_validator.validate_content.return_value = mock_validation
        mock_validator.suggest_improvements.return_value = []
        
        # Test content
        content_data = {
            "platform": "youtube",
            "title": "Great AI Tutorial",
            "tags": ["#AI", "#tutorial", "#tech", "#programming", "#python",
                    "#education", "#learning", "#code", "#development", "#beginner"],
            "confidence_score": 0.9
        }
        
        response = client.post("/api/v1/generate/youtube/validate", json=content_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["platform"] == "youtube"
        assert data["is_valid"] is True
        assert data["quality_score"] == 95.0
        assert "issues" in data
        assert "suggestions" in data
    
    def test_validate_existing_content_platform_mismatch(self):
        """Test validation with platform mismatch."""
        content_data = {
            "platform": "instagram",  # Different from URL
            "title": "Test Title",
            "tags": ["#test"],
            "confidence_score": 0.8
        }
        
        response = client.post("/api/v1/generate/youtube/validate", json=content_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "doesn't match" in data["detail"]
    
    @patch('routers.content_generation.get_content_orchestrator')
    @patch('routers.content_generation.get_content_validator')
    def test_health_check_healthy(self, mock_validator_getter, mock_orchestrator_getter):
        """Test health check endpoint when services are healthy."""
        # Mock services
        mock_orchestrator = Mock()
        mock_validator = Mock()
        mock_orchestrator_getter.return_value = mock_orchestrator
        mock_validator_getter.return_value = mock_validator
        
        # Mock performance stats
        mock_orchestrator.get_performance_stats.return_value = {
            "total_requests": 10,
            "overall_success_rate": 0.9
        }
        
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "supported_platforms" in data
        assert "performance_stats" in data


def run_api_tests():
    """Run all API endpoint tests."""
    print("🧪 Running Phase 6 API Endpoint Tests...\n")
    
    try:
        test_api = TestAPIEndpoints()
        
        # Test basic endpoints
        print("Testing basic endpoints...")
        test_api.test_root_endpoint()
        test_api.test_get_supported_platforms()
        test_api.test_get_platform_rules_valid_platform()
        test_api.test_get_platform_rules_invalid_platform()
        print("✅ Basic endpoint tests - PASSED\n")
        
        # Test single platform generation
        print("Testing single platform generation...")
        test_api.test_generate_single_platform_success()
        test_api.test_generate_single_platform_invalid_platform()
        test_api.test_generate_single_platform_short_transcript()
        print("✅ Single platform generation tests - PASSED\n")
        
        # Test batch generation
        print("Testing batch generation...")
        test_api.test_generate_batch_content_success()
        test_api.test_generate_batch_content_invalid_platforms()
        test_api.test_generate_batch_content_short_transcript()
        print("✅ Batch generation tests - PASSED\n")
        
        # Test validation
        print("Testing content validation...")
        test_api.test_validate_existing_content_valid()
        test_api.test_validate_existing_content_platform_mismatch()
        print("✅ Content validation tests - PASSED\n")
        
        # Test health check
        print("Testing health check...")
        test_api.test_health_check_healthy()
        print("✅ Health check tests - PASSED\n")
        
        print("🎉 All Phase 6 API Endpoint Tests PASSED!")
        print("✅ Task 6.1: Single Platform Generation Endpoint - COMPLETE")
        print("✅ Task 6.2: Multi-Platform Generation Endpoint - COMPLETE")
        print("✅ Task 6.3: Platform Rules Information Endpoint - COMPLETE")
        return True
        
    except Exception as e:
        print(f"❌ API Endpoint Tests - FAILED: {e}")
        return False


if __name__ == "__main__":
    success = run_api_tests()
    if not success:
        exit(1) 