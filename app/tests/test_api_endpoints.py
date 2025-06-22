"""
Tests for simplified API endpoints.
"""
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import pytest
from fastapi.testclient import TestClient
from pydantic_ai import models
from pydantic_ai.models.test import TestModel
from models.platform_rules import PlatformType
from models.content import VideoTranscript, PlatformContent
from main import app

# Configure Pydantic AI for testing
models.ALLOW_MODEL_REQUESTS = False

# Create test client
client = TestClient(app)


class TestAPIEndpoints:
    """Test simplified API endpoints for content generation."""
    
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
        assert "special_requirements" in data
        
        rules = data["rules"]
        assert "title_max_length" in rules
        assert "tag_min_count" in rules
        assert "tag_max_count" in rules
        assert rules["title_max_length"] == 100
        assert rules["tag_min_count"] == 10
        assert rules["tag_max_count"] == 15
        
        # Check special requirements
        assert isinstance(data["special_requirements"], list)
        assert len(data["special_requirements"]) > 0
    
    def test_get_platform_rules_invalid_platform(self):
        """Test getting rules for an invalid platform."""
        response = client.get("/api/v1/platforms/invalid_platform/rules")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not supported" in data["detail"]
    
    def test_generate_single_platform_success(self):
        """Test successful single platform content generation using TestModel."""
        from services.orchestrator import get_content_orchestrator
        
        orchestrator = get_content_orchestrator()
        
        # Create custom test output
        test_output = """Title: AI Tutorial: Complete Guide
Tags: #AI, #Tutorial, #MachineLearning, #Python, #Programming, #Education, #Technology, #Coding, #DataScience, #Development, #Learning, #Tech"""
        
        with orchestrator.agent.override(model=TestModel(custom_output_text=test_output)):
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
            assert data["validation_passed"] in [True, False]
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
        assert response.status_code == 422  # Pydantic validation error
        
        data = response.json()
        assert "detail" in data
    
    def test_validate_existing_content_valid(self):
        """Test validation of existing content."""
        content_data = {
            "platform": "youtube",
            "title": "Great AI Tutorial",
            "tags": ["#AI", "#tutorial", "#tech", "#programming", "#python",
                    "#education", "#learning", "#code", "#development", "#beginner"],
            "confidence_score": 0.9
        }
        
        response = client.post("/api/v1/validate/youtube", json=content_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["platform"] == "youtube"
        assert "is_valid" in data
        assert "quality_score" in data
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
        
        response = client.post("/api/v1/validate/youtube", json=content_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "doesn't match" in data["detail"]
    
    def test_health_check_healthy(self):
        """Test health check endpoint when services are healthy."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "supported_platforms" in data


def run_api_tests():
    """Run all API endpoint tests."""
    print("🧪 Running Simplified API Endpoint Tests...\n")
    
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
        print("Testing content generation...")
        test_api.test_generate_single_platform_success()
        test_api.test_generate_single_platform_invalid_platform()
        test_api.test_generate_single_platform_short_transcript()
        print("✅ Content generation tests - PASSED\n")
        
        # Test validation
        print("Testing content validation...")
        test_api.test_validate_existing_content_valid()
        test_api.test_validate_existing_content_platform_mismatch()
        print("✅ Content validation tests - PASSED\n")
        
        # Test health check
        print("Testing health check...")
        test_api.test_health_check_healthy()
        print("✅ Health check tests - PASSED\n")
        
        print("🎉 All Simplified API Endpoint Tests PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ API Endpoint Tests - FAILED: {e}")
        return False


if __name__ == "__main__":
    success = run_api_tests()
    if not success:
        exit(1) 