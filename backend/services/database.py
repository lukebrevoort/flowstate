"""
Database Service Layer
Handles both local SQLAlchemy operations and Supabase cloud database
"""
import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from config.supabase import get_supabase_client, get_supabase_service_client, test_connection
from models.user import User, UserCreate, UserLogin, UserResponse
from utils.auth import get_password_hash, verify_password
from db import get_db


class DatabaseService:
    """
    Unified database service that can work with both SQLAlchemy and Supabase
    """
    
    def __init__(self):
        self.use_supabase = self._should_use_supabase()
        self.supabase_client = None
        self.supabase_service_client = None
        
        if self.use_supabase:
            try:
                self.supabase_client = get_supabase_client()
                self.supabase_service_client = get_supabase_service_client()
                print("✅ Database service initialized with Supabase")
            except Exception as e:
                print(f"⚠️  Supabase initialization failed: {e}")
                print("🔧 Falling back to SQLAlchemy")
                self.use_supabase = False
    
    def _should_use_supabase(self) -> bool:
        """Determine if we should use Supabase based on environment"""
        return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))
    
    # User Management Methods
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user"""
        if self.use_supabase:
            return await self._create_user_supabase(user_data)
        else:
            return await self._create_user_sqlalchemy(user_data)
    
    async def authenticate_user(self, user_data: UserLogin) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        if self.use_supabase:
            return await self._authenticate_user_supabase(user_data)
        else:
            return await self._authenticate_user_sqlalchemy(user_data)
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if self.use_supabase:
            return await self._get_user_by_id_supabase(user_id)
        else:
            return await self._get_user_by_id_sqlalchemy(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        if self.use_supabase:
            return await self._get_user_by_email_supabase(email)
        else:
            return await self._get_user_by_email_sqlalchemy(email)
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        if self.use_supabase:
            return await self._update_user_preferences_supabase(user_id, preferences)
        else:
            return await self._update_user_preferences_sqlalchemy(user_id, preferences)
    
    # Supabase Implementation Methods
    
    async def _create_user_supabase(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create user using Supabase Auth and Database"""
        try:
            # Use Supabase Auth for authentication
            auth_response = await self.supabase_client.auth_signup(
                email=user_data.email,
                password=user_data.password,
                user_metadata={"name": user_data.name}
            )
            
            # The auth response IS the user object in Supabase
            if auth_response and auth_response.get("id"):
                user_id = auth_response["id"]
                
                # The profile should be automatically created by the trigger function
                # Let's wait a moment and then verify the profile was created
                import asyncio
                await asyncio.sleep(2)  # Give trigger time to execute
                
                # Verify the profile was created by the trigger using service client
                try:
                    # Use service client to check if profile exists (bypasses RLS)
                    profile_response = await self.supabase_service_client.query(
                        "profiles", "GET", filters={"id": user_id}
                    )
                    
                    if profile_response and isinstance(profile_response, list) and len(profile_response) > 0:
                        profile = profile_response[0]
                        print("✅ Profile found after trigger execution")
                        return {
                            "id": profile.get("id"),
                            "name": profile.get("name"),
                            "email": profile.get("email"),
                            "notion_connected": profile.get("notion_connected", False),
                            "google_calendar_connected": profile.get("google_calendar_connected", False)
                        }
                    else:
                        # If trigger didn't work, we need to handle this differently
                        print("Warning: Profile not auto-created by trigger, this needs to be fixed in Supabase")
                        return {
                            "id": user_id,
                            "name": user_data.name,
                            "email": user_data.email,
                            "notion_connected": False,
                            "google_calendar_connected": False
                        }
                except Exception as profile_check_error:
                    print(f"Profile verification failed: {profile_check_error}")
                    # Return basic user info even if profile check fails
                    return {
                        "id": user_id,
                        "name": user_data.name,
                        "email": user_data.email,
                        "notion_connected": False,
                        "google_calendar_connected": False
                    }
            else:
                raise Exception("Failed to create user in Supabase Auth")
                
        except Exception as e:
            print(f"Supabase user creation error: {e}")
            raise e
    
    async def _authenticate_user_supabase(self, user_data: UserLogin) -> Optional[Dict[str, Any]]:
        """Authenticate user using Supabase Auth"""
        try:
            auth_response = await self.supabase_client.auth_signin(
                email=user_data.email,
                password=user_data.password
            )
            
            if auth_response.get("user"):
                user_id = auth_response["user"]["id"]
                
                # Get additional user data from profiles table using service client (bypasses RLS)
                profile_response = await self.supabase_service_client.query(
                    "profiles", "GET", filters={"id": user_id}
                )
                
                if profile_response and isinstance(profile_response, list) and len(profile_response) > 0:
                    profile = profile_response[0]
                    return {
                        "id": user_id,
                        "name": profile.get("name"),
                        "email": profile.get("email"),
                        "notion_connected": profile.get("notion_connected", False),
                        "google_calendar_connected": profile.get("google_calendar_connected", False),
                        "access_token": auth_response.get("access_token")
                    }
                else:
                    # If no profile found, return basic user info from auth response
                    user = auth_response["user"]
                    return {
                        "id": user_id,
                        "name": user.get("user_metadata", {}).get("name", ""),
                        "email": user.get("email"),
                        "notion_connected": False,
                        "google_calendar_connected": False,
                        "access_token": auth_response.get("access_token")
                    }
            
            return None
            
        except Exception as e:
            print(f"Supabase authentication error: {e}")
            return None
    
    async def _get_user_by_id_supabase(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID from Supabase"""
        try:
            # Use service client to bypass RLS policies
            response = await self.supabase_service_client.query(
                "profiles", "GET", filters={"id": user_id}
            )
            
            if response and isinstance(response, list) and len(response) > 0:
                profile = response[0]
                return {
                    "id": profile.get("id"),
                    "name": profile.get("name"),
                    "email": profile.get("email"),
                    "notion_connected": profile.get("notion_connected", False),
                    "google_calendar_connected": profile.get("google_calendar_connected", False)
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting user by ID from Supabase: {e}")
            return None
    
    async def _get_user_by_email_supabase(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from Supabase"""
        try:
            # Use service client to bypass RLS policies
            response = await self.supabase_service_client.query(
                "profiles", "GET", filters={"email": email}
            )
            
            if response and isinstance(response, list) and len(response) > 0:
                profile = response[0]
                return {
                    "id": profile.get("id"),
                    "name": profile.get("name"),
                    "email": profile.get("email"),
                    "notion_connected": profile.get("notion_connected", False),
                    "google_calendar_connected": profile.get("google_calendar_connected", False)
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting user by email from Supabase: {e}")
            return None
    
    async def _update_user_preferences_supabase(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences in Supabase"""
        try:
            response = await self.supabase_client.query(
                "profiles", "PATCH", data=preferences, filters={"id": user_id}
            )
            return response is not None
            
        except Exception as e:
            print(f"Error updating user preferences in Supabase: {e}")
            return False
    
    # SQLAlchemy Implementation Methods (Fallback)
    
    async def _create_user_sqlalchemy(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create user using SQLAlchemy (fallback)"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Check if user exists
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise Exception("Email already registered")
            
            # Create new user
            hashed_password = get_password_hash(user_data.password)
            new_user = User(
                email=user_data.email,
                name=user_data.name,
                hashed_password=hashed_password
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "notion_connected": new_user.notion_connected,
                "google_calendar_connected": new_user.google_calendar_connected
            }
            
        finally:
            db.close()
    
    async def _authenticate_user_sqlalchemy(self, user_data: UserLogin) -> Optional[Dict[str, Any]]:
        """Authenticate user using SQLAlchemy (fallback)"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            user = db.query(User).filter(User.email == user_data.email).first()
            
            if user and verify_password(user_data.password, user.hashed_password):
                return {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "notion_connected": user.notion_connected,
                    "google_calendar_connected": user.google_calendar_connected
                }
            
            return None
            
        finally:
            db.close()
    
    async def _get_user_by_id_sqlalchemy(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID using SQLAlchemy (fallback)"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if user:
                return {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "notion_connected": user.notion_connected,
                    "google_calendar_connected": user.google_calendar_connected
                }
            
            return None
            
        finally:
            db.close()
    
    async def _get_user_by_email_sqlalchemy(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email using SQLAlchemy (fallback)"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                return {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "notion_connected": user.notion_connected,
                    "google_calendar_connected": user.google_calendar_connected
                }
            
            return None
            
        finally:
            db.close()
    
    async def _update_user_preferences_sqlalchemy(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences using SQLAlchemy (fallback)"""
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if user:
                for key, value in preferences.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                db.commit()
                return True
            
            return False
            
        finally:
            db.close()


# Global database service instance
_db_service: Optional[DatabaseService] = None

def get_database_service() -> DatabaseService:
    """Get database service singleton"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
