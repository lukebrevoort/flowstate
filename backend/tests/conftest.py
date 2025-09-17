import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Configure pytest with custom settings."""
    os.environ.setdefault("TESTING", "true")
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_flowstate"
    )
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from app import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "username": "testuser",
    }
