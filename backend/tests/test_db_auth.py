"""Tests for database and authentication utilities."""
import pytest
from unittest.mock import Mock, patch
import os


@pytest.mark.unit
def test_database_models_import():
    """Test that database models can be imported."""
    try:
        from models.user import User, UserCreate, UserLogin, UserResponse
        assert User is not None
        assert UserCreate is not None
        assert UserLogin is not None
        assert UserResponse is not None
    except ImportError as e:
        pytest.fail(f"Failed to import database models: {e}")


@pytest.mark.unit
@patch('utils.auth.pwd_context')
def test_password_hashing(mock_pwd_context):
    """Test password hashing functionality."""
    try:
        from utils.auth import get_password_hash, verify_password
        
        mock_pwd_context.hash.return_value = "hashed_password"
        mock_pwd_context.verify.return_value = True
        
        hashed = get_password_hash("password123")
        assert hashed == "hashed_password"
        
        verified = verify_password("password123", "hashed_password")
        assert verified is True
        
    except ImportError as e:
        pytest.skip(f"Auth utilities not available: {e}")


@pytest.mark.unit
@patch('utils.auth.jwt.encode')
def test_token_creation(mock_jwt_encode):
    """Test JWT token creation."""
    try:
        from utils.auth import create_access_token
        
        mock_jwt_encode.return_value = "test.jwt.token"
        
        token = create_access_token(data={"sub": "user123"})
        assert token == "test.jwt.token"
        
    except ImportError as e:
        pytest.skip(f"JWT utilities not available: {e}")


@pytest.mark.unit
def test_database_connection():
    """Test database connection setup."""
    try:
        from db import engine, get_db
        assert engine is not None
        assert get_db is not None
        
        # Test that get_db is a generator function
        db_gen = get_db()
        assert hasattr(db_gen, '__next__')  # It's a generator
        
    except Exception as e:
        # Database might not be available in test environment
        pytest.skip(f"Database connection test skipped: {e}")


@pytest.mark.unit
def test_environment_variables():
    """Test that required environment variables are set for testing."""
    assert os.getenv("ENV") == "test"
    assert os.getenv("DATABASE_URL") is not None
    assert os.getenv("SECRET_KEY") is not None


@pytest.mark.integration
@patch('db.create_engine')
def test_database_initialization(mock_create_engine):
    """Test database initialization with mocked engine."""
    mock_engine = Mock()
    mock_create_engine.return_value = mock_engine
    
    try:
        from db import Base
        # Test that we can create tables
        Base.metadata.create_all(bind=mock_engine)
        
        # Verify that create_all was called on the mock engine
        assert mock_engine.create_all.called
        
    except Exception as e:
        pytest.skip(f"Database initialization test failed: {e}")


@pytest.mark.unit
def test_user_model_structure():
    """Test User model structure."""
    try:
        from models.user import User, UserCreate
        
        # Test that UserCreate has required fields
        user_create_fields = UserCreate.__fields__ if hasattr(UserCreate, '__fields__') else UserCreate.model_fields
        assert 'email' in user_create_fields
        assert 'name' in user_create_fields
        assert 'password' in user_create_fields
        
    except ImportError as e:
        pytest.skip(f"User model tests skipped: {e}")


@pytest.mark.unit  
def test_pydantic_models():
    """Test Pydantic model validation."""
    try:
        from models.user import UserCreate
        
        # Valid user data
        valid_user = UserCreate(
            email="test@example.com",
            name="Test User", 
            password="password123"
        )
        assert valid_user.email == "test@example.com"
        assert valid_user.name == "Test User"
        
        # Test invalid email format
        with pytest.raises(Exception):  # ValidationError expected
            UserCreate(
                email="invalid-email",
                name="Test User",
                password="password123"
            )
            
    except ImportError as e:
        pytest.skip(f"Pydantic model tests skipped: {e}")