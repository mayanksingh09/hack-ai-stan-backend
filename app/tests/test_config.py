"""
Test script to verify OpenAI API connectivity and configuration setup.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path so we can import from app
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from config import settings


def test_openai_connection():
    """Test basic OpenAI connectivity with a simple ping/test call."""
    try:
        # Create OpenAI model instance
        model = OpenAIModel('gpt-4o', provider=OpenAIProvider(api_key=settings.openai_api_key))
        
        # Create a simple agent for testing
        agent = Agent(model=model)
        
        # Test with a simple prompt using sync method
        result = agent.run_sync("Say 'Hello, OpenAI connection successful!'")
        
        print("✅ OpenAI API Connection Test PASSED")
        print(f"Response: {result.output}")
        return True
        
    except Exception as e:
        print("❌ OpenAI API Connection Test FAILED")
        print(f"Error: {str(e)}")
        return False


def test_settings_load():
    """Test that settings are loaded correctly."""
    try:
        print("🔧 Testing Settings Configuration...")
        print(f"Debug Mode: {settings.debug}")
        print(f"Log Level: {settings.log_level}")
        print(f"API Host: {settings.api_host}")
        print(f"API Port: {settings.api_port}")
        
        # Check if OpenAI API key is loaded (without exposing it)
        if settings.openai_api_key and len(settings.openai_api_key) > 10:
            print("✅ OpenAI API Key loaded successfully")
        else:
            print("❌ OpenAI API Key not found or invalid")
            return False
            
        print("✅ Settings Configuration Test PASSED")
        return True
        
    except Exception as e:
        print("❌ Settings Configuration Test FAILED")
        print(f"Error: {str(e)}")
        return False


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