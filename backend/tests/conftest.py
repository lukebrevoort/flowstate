"""
Test configuration and fixtures for the FlowState backend tests.
Focuses on Supabase integration and FastAPI testing.
"""
import os
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import supabase
from supabase import Client, create_client

# Import your FastAPI app
from app import app

# Test environment variables
TEST_SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:54321")
TEST_SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "test-key")
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/flowstate_test")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client

@pytest.fixture
def supabase_client() -> Client:
    """Create a Supabase client for testing."""
    client = create_client(TEST_SUPABASE_URL, TEST_SUPABASE_KEY)
    return client

@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }

@pytest.fixture
def mock_assignment_data():
    """Mock assignment data for testing."""
    return {
        "title": "Test Assignment",
        "description": "Test assignment description",
        "due_date": "2024-12-31T23:59:59",
        "priority": "high",
        "status": "pending"
    }

@pytest.fixture
def auth_headers(client: TestClient, mock_user_data):
    """Create authentication headers for testing."""
    # First register a user
    response = client.post("/auth/register", json=mock_user_data)
    assert response.status_code == 201
    
    # Then login to get token
    login_data = {
        "email": mock_user_data["email"],
        "password": mock_user_data["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class MockLangGraphAgent:
    """Mock LangGraph agent for testing."""
    
    async def ainvoke(self, input_data, config=None):
        return {
            "messages": [
                {"role": "assistant", "content": "Mock agent response"}
            ]
        }
    
    async def astream(self, input_data, config=None):
        yield {
            "messages": [
                {"role": "assistant", "content": "Mock streaming response"}
            ]
        }

@pytest.fixture
def mock_agent():
    """Provide a mock LangGraph agent for testing."""
    return MockLangGraphAgent()

# Test database setup/teardown
@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up test database before each test and clean up after."""
    # This would typically involve:
    # 1. Creating test tables in Supabase
    # 2. Seeding with test data if needed
    # 3. Cleaning up after tests
    
    yield
    
    # Cleanup code would go here
    # For example, truncating test tables