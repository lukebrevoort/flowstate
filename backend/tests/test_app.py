"""Unit tests for the main FastAPI application."""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FlowState API"
    assert "agent_loaded" in data
    assert "configuration_loaded" in data


@pytest.mark.unit
def test_cors_headers(test_client):
    """Test that CORS headers are properly set."""
    response = test_client.options("/")
    assert "access-control-allow-origin" in response.headers
    

@pytest.mark.unit
def test_signup_endpoint_with_test_user(test_client):
    """Test the signup endpoint with test user."""
    test_user = {
        "email": "test@flowstate.dev",
        "name": "Test User",
        "password": "testpassword123"
    }
    
    response = test_client.post("/api/auth/signup", json=test_user)
    assert response.status_code == 200
    
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == test_user["email"]
    assert data["user"]["name"] == test_user["name"]


@pytest.mark.unit
def test_invalid_signup_data(test_client):
    """Test signup endpoint with invalid data."""
    invalid_user = {"invalid": "data"}
    response = test_client.post("/api/auth/signup", json=invalid_user)
    
    # Should return validation error
    assert response.status_code == 422


@pytest.mark.unit
def test_chat_endpoint_without_auth(test_client):
    """Test chat endpoint without authentication."""
    chat_message = {"message": "Test message", "user_id": "test"}
    response = test_client.post("/api/chat", json=chat_message)
    
    # Should return authentication error
    assert response.status_code == 401


@pytest.mark.unit
def test_app_startup():
    """Test that the app can be created without errors."""
    from app import app
    assert app is not None
    assert hasattr(app, 'routes')


@pytest.mark.unit
def test_environment_configuration():
    """Test that test environment is properly configured."""
    import os
    assert os.getenv("ENV") == "test"
    assert os.getenv("DATABASE_URL") == "sqlite:///./test.db"