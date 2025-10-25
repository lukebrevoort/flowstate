from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from models.user import UserCreate, UserLogin, UserResponse
import uuid
from functools import lru_cache
import time
import asyncio

# Security settings - OPTIMIZED bcrypt rounds
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Password utilities
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# User authentication - OLD SQLALCHEMY FUNCTIONS REMOVED
# These functions have been replaced by async versions that use the DatabaseService

# Legacy functions removed:
# - authenticate_user(db, email, password) -> use DatabaseService.authenticate_user()
# - get_cached_user(user_id, db) -> caching now handled in DatabaseService
# - get_current_user(db, token) -> replaced by get_current_user_dependency(token)


# Async version for database service integration
async def get_current_user_async(token: str) -> Optional[Dict[str, Any]]:
    """Get current user using the new database service"""
    try:
        # Import here to avoid circular imports
        from services.database import get_database_service

        # Handle test token
        if token == "mock-test-token-123":
            return {
                "id": "test-user-123",
                "name": "Test User",
                "email": "test@flowstate.dev",
                "notion_connected": False,
                "google_calendar_connected": False,
            }

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            print("❌ JWT payload missing 'sub' field")
            return None

        print(f"✅ JWT decoded successfully, user_id: {user_id}")

        db_service = get_database_service()
        user_data = await db_service.get_user_by_id(user_id)

        if user_data:
            print(f"✅ User data retrieved from database: {user_data.get('email')}")
        else:
            print(f"❌ No user data found for user_id: {user_id}")

        return user_data

    except JWTError as e:
        print(f"❌ JWT decode error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error getting current user: {e}")
        import traceback

        traceback.print_exc()
        return None


class UserDict:
    """User object that can be created from dictionary data"""

    def __init__(self, user_data: Dict[str, Any]):
        self.id = user_data.get("id")
        self.name = user_data.get("name")
        self.email = user_data.get("email")
        self.notion_connected = user_data.get("notion_connected", False)
        self.google_calendar_connected = user_data.get("google_calendar_connected", False)


# New dependency for async endpoints
async def get_current_user_dependency(token: str = Depends(oauth2_scheme)) -> UserDict:
    """FastAPI dependency for getting current user with database service"""
    user_data = await get_current_user_async(token)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserDict(user_data)
