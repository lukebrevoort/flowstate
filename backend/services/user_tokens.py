"""
User Token Service
Provides easy access to user tokens for agents and services
"""
import logging
from typing import Optional, Dict, Any
from config.supabase import get_supabase_client

logger = logging.getLogger(__name__)

class UserTokenService:
    """Service for managing user integration tokens"""
    
    @staticmethod
    async def get_user_notion_token(user_id: str) -> Optional[str]:
        """
        Get user's Notion access token
        
        Args:
            user_id: User ID
            
        Returns:
            Access token if found and valid, None otherwise
        """
        try:
            supabase = get_supabase_client()
            
            result = await supabase.query(
                "user_integrations",
                "GET",
                filters={
                    "user_id": user_id,
                    "integration_type": "notion",
                    "is_active": True
                }
            )
            
            if result and len(result) > 0:
                integration = result[0]
                token = integration.get("access_token")
                
                # TODO: Add token validation/refresh logic here
                # For now, just return the token if it exists
                return token
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving Notion token for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    async def get_user_google_token(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's Google Calendar tokens
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with access_token, refresh_token, expires_at if found, None otherwise
        """
        try:
            supabase = get_supabase_client()
            
            result = await supabase.query(
                "user_integrations",
                "GET",
                filters={
                    "user_id": user_id,
                    "integration_type": "google_calendar",
                    "is_active": True
                }
            )
            
            if result and len(result) > 0:
                integration = result[0]
                return {
                    "access_token": integration.get("access_token"),
                    "refresh_token": integration.get("refresh_token"),
                    "expires_at": integration.get("token_expires_at")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving Google tokens for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    async def is_integration_connected(user_id: str, integration_type: str) -> bool:
        """
        Check if user has a specific integration connected
        
        Args:
            user_id: User ID
            integration_type: Type of integration ('notion', 'google_calendar', etc.)
            
        Returns:
            True if connected and active, False otherwise
        """
        try:
            supabase = get_supabase_client()
            
            result = await supabase.query(
                "user_integrations",
                "GET",
                filters={
                    "user_id": user_id,
                    "integration_type": integration_type,
                    "is_active": True
                }
            )
            
            return bool(result and len(result) > 0)
            
        except Exception as e:
            logger.error(f"Error checking integration {integration_type} for user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    async def get_user_integrations_status(user_id: str) -> Dict[str, bool]:
        """
        Get status of all integrations for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dict mapping integration types to their connection status
        """
        try:
            supabase = get_supabase_client()
            
            result = await supabase.query(
                "user_integrations",
                "GET",
                filters={"user_id": user_id, "is_active": True}
            )
            
            status = {
                "notion": False,
                "google_calendar": False,
                "google_drive": False
            }
            
            if result:
                for integration in result:
                    integration_type = integration.get("integration_type")
                    if integration_type in status:
                        status[integration_type] = True
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting integrations status for user {user_id}: {str(e)}")
            return {
                "notion": False,
                "google_calendar": False,
                "google_drive": False
            }

# Factory function for creating NotionAPI with user token
def create_notion_api_for_user(user_id: str):
    """
    Create a NotionAPI instance configured for a specific user
    
    Args:
        user_id: User ID
        
    Returns:
        NotionAPI instance configured with user's token
    """
    from notion_api import NotionAPI
    return NotionAPI(user_id=user_id)
