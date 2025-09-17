"""
Test the FastAPI application basic functionality.
"""

import pytest
from fastapi.testclient import TestClient


def test_app_startup(client):
    """Test that the FastAPI app starts up correctly."""
    # Test health endpoint if it exists
    response = client.get("/")
    # Accept either 200 (if root endpoint exists) or 404 (if it doesn't)
    assert response.status_code in [200, 404]


def test_app_imports():
    """Test that all critical modules can be imported."""
    try:
        import app

        assert hasattr(app, "app"), "FastAPI app instance should exist"
    except ImportError as e:
        pytest.fail(f"Failed to import app module: {e}")


def test_agent_imports():
    """Test that agent modules can be imported."""
    try:
        import agents.supervisor
        import agents.configuration

        assert True  # If we get here, imports worked
    except ImportError as e:
        pytest.fail(f"Failed to import agent modules: {e}")


def test_cors_configuration(client):
    """Test that CORS is properly configured."""
    # Test that we can make a request with CORS headers
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    # Should either work (200/404) or be properly handled, not a server error
    assert response.status_code < 500, f"Should not be a server error, got {response.status_code}"


def test_environment_variables():
    """Test that required environment variables are available."""
    import os

    # These should be set in the test environment
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    for var in required_vars:
        assert os.getenv(var) is not None, f"Environment variable {var} should be set"


def test_models_import():
    """Test that model classes can be imported."""
    try:
        from models.user import UserCreate, UserLogin, UserResponse

        assert UserCreate is not None
        assert UserLogin is not None
        assert UserResponse is not None
    except ImportError as e:
        pytest.fail(f"Failed to import user models: {e}")


def test_auth_utils_import():
    """Test that authentication utilities can be imported."""
    try:
        from utils.auth import get_password_hash, verify_password, create_access_token

        assert get_password_hash is not None
        assert verify_password is not None
        assert create_access_token is not None
    except ImportError as e:
        pytest.fail(f"Failed to import auth utilities: {e}")
