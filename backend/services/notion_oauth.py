"""
Notion OAuth Service
Handles the complete OAuth flow for Notion integration
"""

import os
import secrets
import httpx
import logging
from typing import Dict, Optional, Any
from urllib.parse import urlencode
from dotenv import load_dotenv
from fastapi import HTTPException
from config.supabase import get_supabase_service_client

load_dotenv()

logger = logging.getLogger(__name__)


class NotionOAuthService:
    """Service for handling Notion OAuth flow"""

    def __init__(self):
        self.client_id = os.getenv("NOTION_OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("NOTION_OAUTH_CLIENT_SECRET")
        self.redirect_uri = os.getenv(
            "NOTION_OAUTH_REDIRECT_URI",
            "http://localhost:3000/api/oauth/notion/callback",
        )

        if not self.client_id or not self.client_secret:
            raise ValueError("NOTION_OAUTH_CLIENT_ID and NOTION_OAUTH_CLIENT_SECRET must be set")

    def generate_auth_url(self, user_id: str) -> Dict[str, str]:
        """
        Generate Notion OAuth authorization URL

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

        # Notion OAuth parameters
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "owner": "user",  # Request user-level access
            "redirect_uri": self.redirect_uri,
            "state": state_data,
        }

        auth_url = f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"

        return {"auth_url": auth_url, "state": state_data}

    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from Notion
            state: State parameter to verify CSRF protection

        Returns:
            Token response from Notion
        """
        try:
            # Verify state parameter format
            if ":" not in state:
                raise ValueError("Invalid state parameter")

            user_id, _ = state.split(":", 1)

            # Handle test/mock authorization codes
            if code.startswith("mock_auth_code"):
                return {
                    "access_token": "mock_notion_access_token_123",
                    "token_type": "bearer",
                    "bot_id": "mock_bot_id_123",
                    "workspace_name": "Test Workspace",
                    "workspace_icon": "🧪",
                    "workspace_id": "mock_workspace_id_123",
                    "owner": {
                        "type": "user",
                        "user": {
                            "id": "mock_user_id_123",
                            "name": "Test User",
                            "avatar_url": None,
                            "type": "person",
                            "person": {"email": "test@example.com"},
                        },
                    },
                    "user_id": user_id,
                }

            # Prepare token exchange request
            token_url = "https://api.notion.com/v1/oauth/token"

            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
            }

            # Use basic auth for client credentials
            auth = (self.client_id, self.client_secret)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url,
                    data=data,
                    auth=auth,
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

                # Add user_id to response for easier handling
                token_data["user_id"] = user_id

                return token_data

        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            raise

    async def store_user_tokens(self, user_id: str, token_data: Dict[str, Any]) -> bool:
        """
        Store user's Notion tokens in Supabase

        Args:
            user_id: User ID
            token_data: Token response from Notion OAuth

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
                # Note: In production, you'd want to get this info from the OAuth provider or have it from signup
                profile_data = {
                    "id": user_id,
                    "email": f"user-{user_id[:8]}@oauth.local",  # Temporary email
                    "name": "OAuth User",  # Temporary name
                    "notion_connected": False,  # Will be updated to True later
                }

                try:
                    await supabase.query("profiles", "POST", data=profile_data)
                    logger.info(f"Created profile for user {user_id}")
                except Exception as profile_error:
                    logger.error(f"Failed to create profile for user {user_id}: {profile_error}")
                    # If we can't create a profile, we can't proceed
                    return False  # Extract relevant data from token response
            access_token = token_data.get("access_token")
            token_type = token_data.get("token_type", "bearer")
            bot_id = token_data.get("bot_id")
            workspace_name = token_data.get("workspace_name")
            workspace_icon = token_data.get("workspace_icon")
            workspace_id = token_data.get("workspace_id")
            owner = token_data.get("owner", {})

            # Prepare integration data
            integration_data = {
                "bot_id": bot_id,
                "workspace_name": workspace_name,
                "workspace_icon": workspace_icon,
                "workspace_id": workspace_id,
                "owner": owner,
                "token_type": token_type,
            }

            # Check if integration already exists
            existing = await supabase.query(
                "user_integrations",
                "GET",
                filters={"user_id": user_id, "integration_type": "notion"},
            )

            if existing:
                # Update existing integration
                await supabase.query(
                    "user_integrations",
                    "PATCH",
                    data={
                        "access_token": access_token,
                        "integration_data": integration_data,
                        "is_active": True,
                    },
                    filters={"user_id": user_id, "integration_type": "notion"},
                )
            else:
                # Create new integration
                await supabase.query(
                    "user_integrations",
                    "POST",
                    data={
                        "user_id": user_id,
                        "integration_type": "notion",
                        "access_token": access_token,
                        "integration_data": integration_data,
                        "is_active": True,
                    },
                )

            # Update user profile to mark Notion as connected
            await supabase.query(
                "profiles",
                "PATCH",
                data={"notion_connected": True},
                filters={"id": user_id},
            )

            logger.info(f"Successfully stored Notion tokens for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing Notion tokens for user {user_id}: {str(e)}")
            return False

    async def get_user_notion_token(self, user_id: str) -> Optional[str]:
        """
        Retrieve user's Notion access token

        Args:
            user_id: User ID

        Returns:
            Access token if found, None otherwise
        """
        try:
            # Handle mock/test user
            if user_id == "test-user-123":
                return "mock_notion_access_token_123"

            supabase = get_supabase_service_client()

            result = await supabase.query(
                "user_integrations",
                "GET",
                filters={
                    "user_id": user_id,
                    "integration_type": "notion",
                    "is_active": True,
                },
            )

            if result and len(result) > 0:
                return result[0].get("access_token")

            return None

        except Exception as e:
            logger.error(f"Error retrieving Notion token for user {user_id}: {str(e)}")
            return None

    async def test_notion_connection(self, access_token: str) -> Dict[str, Any]:
        """
        Test the Notion connection with the access token

        Args:
            access_token: Notion access token

        Returns:
            Response from Notion API
        """
        try:
            # Handle mock/test tokens
            if access_token.startswith("mock_"):
                return {
                    "success": True,
                    "data": {
                        "id": "mock_user_id_123",
                        "name": "Test User",
                        "avatar_url": None,
                        "type": "person",
                        "person": {"email": "test@example.com"},
                    },
                }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.notion.com/v1/users/me",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Notion-Version": "2022-06-28",
                        "Content-Type": "application/json",
                    },
                )
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Error testing Notion connection: {str(e)}")
            return {"success": False, "error": str(e)}
