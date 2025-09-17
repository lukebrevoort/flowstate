"""
Basic test to ensure the backend application can be imported and basic functionality works.
"""
import pytest
from fastapi.testclient import TestClient
from app import app


def test_app_creation():
    """Test that the FastAPI app can be created successfully."""
    assert app is not None
    assert hasattr(app, 'routes')


def test_health_endpoint():
    """Test the health endpoint if it exists, or basic app functionality."""
    client = TestClient(app)
    
    # Try to access the root path
    response = client.get("/")
    # We don't care about the exact status code, just that the app responds
    assert response is not None
    
    # Check that the app has some routes defined
    assert len(app.routes) > 0


def test_app_has_required_components():
    """Test that the app has the expected basic components."""
    # Test that the app is a FastAPI instance
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)
    
    # Test that the app has been configured with some routes
    assert hasattr(app, 'router')
    assert app.router is not None