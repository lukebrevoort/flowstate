# Test configuration and fixtures
import pytest
import os
import sys
from unittest.mock import Mock

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_agent_app():
    """Mock the LangGraph agent app."""
    mock_app = Mock()
    mock_app.ainvoke = Mock()
    mock_app.astream = Mock()
    return mock_app

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    mock_session = Mock()
    return mock_session

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com", 
        "password": "testpassword123",
        "name": "Test User"
    }

@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing."""
    return {
        "message": "Test message",
        "user_id": "test-user-id"
    }

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["ENV"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db" 
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    
    # Mock API keys for testing
    os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["NOTION_API_KEY"] = "test-notion-key"
    
    yield
    
    # Cleanup after test - remove test env vars
    test_vars = ["ENV", "DATABASE_URL", "SECRET_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "NOTION_API_KEY"]
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]