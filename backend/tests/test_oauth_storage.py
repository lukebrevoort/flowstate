#!/usr/bin/env python3
"""
Test Notion OAuth token storage directly
"""
import asyncio
import sys
import pytest
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from services.notion_oauth import NotionOAuthService


@pytest.mark.asyncio
async def test_token_storage():
    """Test the actual token storage function"""
    print("🔧 Testing Notion OAuth Token Storage")
    print("=" * 40)

    try:
        # Create service instance
        oauth_service = NotionOAuthService()

        # Test data (similar to what Notion would return)
        test_token_data = {
            "access_token": "test_token_123456",
            "token_type": "bearer",
            "bot_id": "test_bot_id",
            "workspace_name": "Test Workspace",
            "workspace_icon": "https://example.com/icon.png",
            "workspace_id": "test_workspace_id",
            "owner": {"type": "user", "user": {"object": "user", "id": "test_user_id"}},
        }

        # Test user ID (use a valid UUID format)
        test_user_id = "93f2ef33-aa8e-421f-934c-f1b964786bc4"  # Same as in your error

        print(f"🔄 Attempting to store tokens for user: {test_user_id}")

        # Call the storage function
        result = await oauth_service.store_user_tokens(test_user_id, test_token_data)

        if result:
            print("✅ Token storage successful!")

            # Try to retrieve the token to verify it was stored
            stored_token = await oauth_service.get_user_notion_token(test_user_id)
            if stored_token:
                print(f"✅ Token retrieval successful: {stored_token[:20]}...")
            else:
                print("⚠️  Token storage successful but retrieval failed")
        else:
            print("❌ Token storage failed")

    except Exception as e:
        print(f"❌ Error during token storage test: {e}")
        return False

    return result


async def main():
    success = await test_token_storage()

    if success:
        print("\n🎉 OAuth token storage is working correctly!")
    else:
        print("\n❌ OAuth token storage failed. Check:")
        print("1. Supabase service key configuration")
        print("2. RLS policies in Supabase")
        print("3. Backend server restart")


if __name__ == "__main__":
    asyncio.run(main())
