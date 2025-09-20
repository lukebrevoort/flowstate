"""
Check what OAuth tokens are stored in the database
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.supabase import get_supabase_service_client


async def check_stored_tokens():
    """Check what tokens are in the database"""

    print("Checking stored OAuth tokens in database...")

    try:
        supabase = get_supabase_service_client()

        # Get all user integrations
        result = await supabase.query("user_integrations", "GET")

        if result:
            print(f"Found {len(result)} integrations:")
            for integration in result:
                print(f"  - User ID: {integration.get('user_id')}")
                print(f"    Type: {integration.get('integration_type')}")
                print(f"    Active: {integration.get('is_active')}")
                print(f"    Has Token: {'Yes' if integration.get('access_token') else 'No'}")
                if integration.get("access_token"):
                    token = integration.get("access_token")
                    print(f"    Token (first 20 chars): {token[:20]}...")
                print()
        else:
            print("No integrations found")

        # Also check for Notion-specific integrations
        print("\nChecking specifically for Notion integrations:")
        notion_result = await supabase.query("user_integrations", "GET", filters={"integration_type": "notion"})

        if notion_result:
            print(f"Found {len(notion_result)} Notion integrations:")
            for integration in notion_result:
                print(f"  - User ID: {integration.get('user_id')}")
                print(f"    Active: {integration.get('is_active')}")
                print(f"    Has Token: {'Yes' if integration.get('access_token') else 'No'}")
        else:
            print("No Notion integrations found")

    except Exception as e:
        print(f"Error checking tokens: {e}")


if __name__ == "__main__":
    asyncio.run(check_stored_tokens())
