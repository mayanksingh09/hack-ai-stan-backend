"""
Test script to verify OpenAI API connectivity and configuration setup.
"""
import sys
import os
import pytest
from pathlib import Path

# Add the parent directory to Python path so we can import from app
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from pydantic_ai import Agent, models
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from config import settings

# Allow model requests for config tests (we want to test real API connectivity)
models.ALLOW_MODEL_REQUESTS = True


@pytest.mark.skip(reason="OpenAI connection test skipped during full test runs to avoid model request conflicts")
def test_openai_connection():
    """Test basic OpenAI connectivity with a simple ping/test call."""
    # Create OpenAI model instance
    model = OpenAIModel('gpt-4o', provider=OpenAIProvider(api_key=settings.openai_api_key))
    
    # Create a simple agent for testing
    agent = Agent(model=model)
    
    # Test with a simple prompt using sync method
    result = agent.run_sync("Say 'Hello, OpenAI connection successful!'")
    
    print("✅ OpenAI API Connection Test PASSED")
    print(f"Response: {result.output}")
    
    # Assert that we got a response
    assert result.output is not None
    assert len(result.output) > 0


def test_settings_load():
    """Test that settings are loaded correctly."""
    print("🔧 Testing Settings Configuration...")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    print(f"API Host: {settings.api_host}")
    print(f"API Port: {settings.api_port}")
    
    # Check if OpenAI API key is loaded (without exposing it)
    assert settings.openai_api_key is not None, "OpenAI API Key not found"
    assert len(settings.openai_api_key) > 10, "OpenAI API Key appears to be invalid"
    print("✅ OpenAI API Key loaded successfully")
        
    print("✅ Settings Configuration Test PASSED")
    
    # Basic assertions
    assert settings.debug is not None
    assert settings.log_level is not None
    assert settings.api_host is not None
    assert settings.api_port is not None


if __name__ == "__main__":
    print("🚀 Starting Configuration Tests...\n")
    
    # Test settings configuration
    settings_ok = test_settings_load()
    print()
    
    if settings_ok:
        # Test OpenAI connection
        connection_ok = test_openai_connection()
        
        if connection_ok:
            print("\n🎉 All tests passed! Configuration is ready.")
        else:
            print("\n⚠️  Settings loaded but OpenAI connection failed.")
    else:
        print("\n⚠️  Settings configuration failed. Please check your .env file.") 