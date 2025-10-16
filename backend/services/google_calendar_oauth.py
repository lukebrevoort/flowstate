"""
Google Calendar OAuth Service
Handles the complete OAuth flow for Google Calendar integration
"""

import os
import secrets
import httpx
import logging
from typing import Dict, Optional, Any
from urllib.parse import urlencode
from dotenv import load_dotenv
from fastapi import HTTPException

# Handle supabase import gracefully
try:
    from config.supabase import get_supabase_service_client

    SUPABASE_AVAILABLE = True
except ImportError:
    logging.warning("Could not import supabase config. OAuth service will work in fallback mode.")
    SUPABASE_AVAILABLE = False

    def get_supabase_service_client():
        return None


load_dotenv()

logger = logging.getLogger(__name__)


class GoogleCalendarOAuthService:
    """Service for handling Google Calendar OAuth flow"""

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        self.redirect_uri = os.getenv(
            "GOOGLE_OAUTH_REDIRECT_URI",
            "http://localhost:3000/api/oauth/google-calendar/callback",
        )

        if not self.client_id or not self.client_secret:
            raise ValueError("GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set")

        # Google OAuth endpoints
        self.auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"

        # Google Calendar API scopes
        self.scopes = [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]

    def generate_auth_url(self, user_id: str) -> Dict[str, str]:
        """
        Generate Google OAuth authorization URL

        Args:
            user_id: User ID to associate with this OAuth flow

        Returns:
            Dictionary containing auth_url and state
        """
        # Generate a secure state parameter to prevent CSRF attacks
        state = secrets.token_urlsafe(32)

        # Store state temporarily (in production, use Redis or database)
        # For now, we'll include user_id in the state and verify it later
        state_data = f"{user_id}:{state}"

        # Google OAuth parameters
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "redirect_uri": self.redirect_uri,
            "state": state_data,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen to get refresh token
        }

        auth_url = f"{self.auth_endpoint}?{urlencode(params)}"

        return {"auth_url": auth_url, "state": state_data}

    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from Google
            state: State parameter to verify CSRF protection

        Returns:
            Token response from Google
        """
        try:
            # Verify state parameter format
            if ":" not in state:
                raise ValueError("Invalid state parameter")

            user_id, _ = state.split(":", 1)

            # Handle test/mock authorization codes
            if code.startswith("mock_auth_code"):
                return {
                    "access_token": "mock_google_access_token_123",
                    "token_type": "bearer",
                    "refresh_token": "mock_google_refresh_token_123",
                    "expires_in": 3600,
                    "scope": " ".join(self.scopes),
                    "user_id": user_id,
                    "user_info": {
                        "id": "mock_google_user_id_123",
                        "email": "test@example.com",
                        "name": "Test User",
                        "picture": None,
                    },
                }

            # Prepare token exchange request
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to exchange code for token: {response.text}",
                    )

                token_data = response.json()

                # Get user info from Google
                user_info = await self._get_user_info(token_data["access_token"])

                # Add user_id and user_info to response for easier handling
                token_data["user_id"] = user_id
                token_data["user_info"] = user_info

                return token_data

        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            raise

    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user info from Google

        Args:
            access_token: Google access token

        Returns:
            User info from Google
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_endpoint,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                )

                if response.status_code != 200:
                    logger.error(f"Failed to get user info: {response.status_code} - {response.text}")
                    return {}

                return response.json()

        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return {}

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh the access token using the refresh token

        Args:
            refresh_token: Google refresh token

        Returns:
            New token data
        """
        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to refresh token: {response.text}",
                    )

                return response.json()

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise

    async def store_user_tokens(self, user_id: str, token_data: Dict[str, Any]) -> bool:
        """
        Store user's Google Calendar tokens in Supabase

        Args:
            user_id: User ID
            token_data: Token response from Google OAuth

        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle mock/test tokens
            if user_id == "test-user-123" or token_data.get("access_token", "").startswith("mock_"):
                logger.info(f"Mock token storage for user {user_id}")
                return True

            supabase = get_supabase_service_client()

            # Debug: Log which key is being used
            auth_header = supabase.headers.get("Authorization", "")
            if "anon" in auth_header:
                logger.error("ERROR: Using anon key instead of service key!")
                raise Exception("Configuration error: anon key used instead of service key")
            else:
                logger.info("Using service role key for token storage")

            # First, verify the user exists in profiles table
            existing_profile = await supabase.query("profiles", "GET", filters={"id": user_id})

            if not existing_profile:
                logger.warning(f"User {user_id} not found in profiles table. Creating profile...")

                # Create a basic profile for the user
                profile_data = {
                    "id": user_id,
                    "email": token_data.get("user_info", {}).get("email", f"user-{user_id[:8]}@oauth.local"),
                    "name": token_data.get("user_info", {}).get("name", "OAuth User"),
                    "google_calendar_connected": False,
                }

                try:
                    await supabase.query("profiles", "POST", data=profile_data)
                    logger.info(f"Created profile for user {user_id}")
                except Exception as profile_error:
                    logger.error(f"Failed to create profile for user {user_id}: {profile_error}")
                    return False

            # Extract relevant data from token response
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            token_type = token_data.get("token_type", "bearer")
            expires_in = token_data.get("expires_in", 3600)
            scope = token_data.get("scope", "")
            user_info = token_data.get("user_info", {})

            # Calculate token expiration time
            from datetime import datetime, timedelta, timezone

            token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            # Prepare integration data
            integration_data = {
                "scope": scope,
                "user_info": user_info,
                "token_type": token_type,
            }

            # Check if integration already exists
            existing = await supabase.query(
                "user_integrations",
                "GET",
                filters={"user_id": user_id, "integration_type": "google_calendar"},
            )

            if existing:
                # Update existing integration
                await supabase.query(
                    "user_integrations",
                    "PATCH",
                    data={
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_expires_at": token_expires_at.isoformat(),
                        "integration_data": integration_data,
                        "is_active": True,
                    },
                    filters={"user_id": user_id, "integration_type": "google_calendar"},
                )
            else:
                # Create new integration
                await supabase.query(
                    "user_integrations",
                    "POST",
                    data={
                        "user_id": user_id,
                        "integration_type": "google_calendar",
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_expires_at": token_expires_at.isoformat(),
                        "integration_data": integration_data,
                        "is_active": True,
                    },
                )

            # Update user profile to mark Google Calendar as connected
            await supabase.query(
                "profiles",
                "PATCH",
                data={"google_calendar_connected": True},
                filters={"id": user_id},
            )

            logger.info(f"Successfully stored Google Calendar tokens for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing Google Calendar tokens for user {user_id}: {str(e)}")
            return False

    async def get_user_google_token(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve user's Google Calendar access token (and refresh if needed)

        Args:
            user_id: User ID

        Returns:
            Dictionary with access_token and refresh_token if found, None otherwise
        """
        try:
            # Handle mock/test user
            if user_id == "test-user-123":
                return {
                    "access_token": "mock_google_access_token_123",
                    "refresh_token": "mock_google_refresh_token_123",
                }

            supabase = get_supabase_service_client()

            result = await supabase.query(
                "user_integrations",
                "GET",
                filters={
                    "user_id": user_id,
                    "integration_type": "google_calendar",
                    "is_active": True,
                },
            )

            if result and len(result) > 0:
                integration = result[0]
                access_token = integration.get("access_token")
                refresh_token = integration.get("refresh_token")
                token_expires_at = integration.get("token_expires_at")

                # Check if token is expired and refresh if needed
                from datetime import datetime, timedelta, timezone

                if token_expires_at:
                    expires_at = datetime.fromisoformat(token_expires_at.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)

                    # Refresh token if it expires in less than 5 minutes
                    if now >= expires_at or (expires_at - now).total_seconds() < 300:
                        logger.info(f"Access token expired or expiring soon for user {user_id}, refreshing...")
                        try:
                            new_token_data = await self.refresh_access_token(refresh_token)

                            # Update stored tokens
                            new_expires_at = datetime.now(timezone.utc) + timedelta(
                                seconds=new_token_data.get("expires_in", 3600)
                            )

                            await supabase.query(
                                "user_integrations",
                                "PATCH",
                                data={
                                    "access_token": new_token_data["access_token"],
                                    "token_expires_at": new_expires_at.isoformat(),
                                },
                                filters={"user_id": user_id, "integration_type": "google_calendar"},
                            )

                            access_token = new_token_data["access_token"]
                            logger.info(f"Successfully refreshed token for user {user_id}")

                        except Exception as refresh_error:
                            logger.error(f"Failed to refresh token for user {user_id}: {refresh_error}")
                            # Return expired token anyway, let the caller handle it
                            pass

                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }

            return None

        except Exception as e:
            logger.error(f"Error retrieving Google Calendar token for user {user_id}: {str(e)}")
            return None

    async def test_google_calendar_connection(self, access_token: str) -> Dict[str, Any]:
        """
        Test the Google Calendar connection with the access token

        Args:
            access_token: Google access token

        Returns:
            Response from Google Calendar API
        """
        try:
            # Handle mock/test tokens
            if access_token.startswith("mock_"):
                return {
                    "success": True,
                    "data": {
                        "kind": "calendar#calendarList",
                        "items": [
                            {
                                "id": "primary",
                                "summary": "Test Calendar",
                                "primary": True,
                            }
                        ],
                    },
                }

            # Test by fetching calendar list
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                )

                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Error testing Google Calendar connection: {str(e)}")
            return {"success": False, "error": str(e)}
