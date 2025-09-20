"""
Database Service Layer
Handles Supabase cloud database operations
"""

import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from config.supabase import (
    get_supabase_client,
    get_supabase_service_client,
    test_connection,
)
from models.user import UserCreate, UserLogin, UserResponse
from utils.auth import get_password_hash, verify_password


class DatabaseService:
    """
    Database service that uses Supabase for all operations
    """

    def __init__(self):
        self.supabase_client = None
        self.supabase_service_client = None

        try:
            self.supabase_client = get_supabase_client()
            self.supabase_service_client = get_supabase_service_client()
            print("✅ Database service initialized with Supabase")
        except Exception as e:
            print(f"❌ Supabase initialization failed: {e}")
            raise Exception("Supabase is required for database operations")

    # User Management Methods

    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user"""
        return await self._create_user_supabase(user_data)

    async def authenticate_user(self, user_data: UserLogin) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        return await self._authenticate_user_supabase(user_data)

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return await self._get_user_by_id_supabase(user_id)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return await self._get_user_by_email_supabase(email)

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        return await self._update_user_preferences_supabase(user_id, preferences)

    # Supabase Implementation Methods

    async def _create_user_supabase(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create user using Supabase Auth and Database"""
        try:
            # Use Supabase Auth for authentication
            auth_response = await self.supabase_client.auth_signup(
                email=user_data.email,
                password=user_data.password,
                user_metadata={"name": user_data.name},
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
                    profile_response = await self.supabase_service_client.query("profiles", "GET", filters={"id": user_id})

                    if profile_response and isinstance(profile_response, list) and len(profile_response) > 0:
                        profile = profile_response[0]
                        print("✅ Profile found after trigger execution")
                        return {
                            "id": profile.get("id"),
                            "name": profile.get("name"),
                            "email": profile.get("email"),
                            "notion_connected": profile.get("notion_connected", False),
                            "google_calendar_connected": profile.get("google_calendar_connected", False),
                        }
                    else:
                        # If trigger didn't work, we need to handle this differently
                        print("Warning: Profile not auto-created by trigger, this needs to be fixed in Supabase")
                        return {
                            "id": user_id,
                            "name": user_data.name,
                            "email": user_data.email,
                            "notion_connected": False,
                            "google_calendar_connected": False,
                        }
                except Exception as profile_check_error:
                    print(f"Profile verification failed: {profile_check_error}")
                    # Return basic user info even if profile check fails
                    return {
                        "id": user_id,
                        "name": user_data.name,
                        "email": user_data.email,
                        "notion_connected": False,
                        "google_calendar_connected": False,
                    }
            else:
                raise Exception("Failed to create user in Supabase Auth")

        except Exception as e:
            print(f"Supabase user creation error: {e}")
            raise e

    async def _authenticate_user_supabase(self, user_data: UserLogin) -> Optional[Dict[str, Any]]:
        """Authenticate user using Supabase Auth"""
        try:
            auth_response = await self.supabase_client.auth_signin(email=user_data.email, password=user_data.password)

            if auth_response.get("user"):
                user_id = auth_response["user"]["id"]

                # Get additional user data from profiles table using service client (bypasses RLS)
                profile_response = await self.supabase_service_client.query("profiles", "GET", filters={"id": user_id})

                if profile_response and isinstance(profile_response, list) and len(profile_response) > 0:
                    profile = profile_response[0]
                    return {
                        "id": user_id,
                        "name": profile.get("name"),
                        "email": profile.get("email"),
                        "notion_connected": profile.get("notion_connected", False),
                        "google_calendar_connected": profile.get("google_calendar_connected", False),
                        "access_token": auth_response.get("access_token"),
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
                        "access_token": auth_response.get("access_token"),
                    }

            return None

        except Exception as e:
            print(f"Supabase authentication error: {e}")
            return None

    async def _get_user_by_id_supabase(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID from Supabase"""
        try:
            # Use service client to bypass RLS policies
            response = await self.supabase_service_client.query("profiles", "GET", filters={"id": user_id})

            if response and isinstance(response, list) and len(response) > 0:
                profile = response[0]
                return {
                    "id": profile.get("id"),
                    "name": profile.get("name"),
                    "email": profile.get("email"),
                    "notion_connected": profile.get("notion_connected", False),
                    "google_calendar_connected": profile.get("google_calendar_connected", False),
                }

            return None

        except Exception as e:
            print(f"Error getting user by ID from Supabase: {e}")
            return None

    async def _get_user_by_email_supabase(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email from Supabase"""
        try:
            # Use service client to bypass RLS policies
            response = await self.supabase_service_client.query("profiles", "GET", filters={"email": email})

            if response and isinstance(response, list) and len(response) > 0:
                profile = response[0]
                return {
                    "id": profile.get("id"),
                    "name": profile.get("name"),
                    "email": profile.get("email"),
                    "notion_connected": profile.get("notion_connected", False),
                    "google_calendar_connected": profile.get("google_calendar_connected", False),
                }

            return None

        except Exception as e:
            print(f"Error getting user by email from Supabase: {e}")
            return None

    async def _update_user_preferences_supabase(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences in Supabase"""
        try:
            response = await self.supabase_client.query("profiles", "PATCH", data=preferences, filters={"id": user_id})
            return response is not None

        except Exception as e:
            print(f"Error updating user preferences in Supabase: {e}")
            return False


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get database service singleton"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
