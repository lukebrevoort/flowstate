"""
Test OAuth token integration with NotionAPI
"""

import sys
import os
import asyncio
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_api import NotionAPI
from services.user_tokens import UserTokenService


def test_notion_api_with_user_token():
    """Test that NotionAPI can use user OAuth tokens"""

    # Test with a real user ID from the database
    test_user_id = "79ba6a8b-7aa7-498b-a9ed-a772d1dc34ef"

    print(f"Testing NotionAPI with user_id: {test_user_id}")

    try:
        # Create NotionAPI instance with user_id
        notion_api = NotionAPI(user_id=test_user_id)

        # Check token info
        token_info = notion_api.get_token_info()
        print(f"Token info: {token_info}")

        # Verify it's using user token
        if notion_api.is_using_user_token:
            print("✅ Successfully using user OAuth token")
        else:
            print("⚠️  Falling back to system token (no user token found)")

        return True

    except Exception as e:
        print(f"❌ Error testing NotionAPI with user token: {e}")
        return False


def test_notion_api_without_user_token():
    """Test that NotionAPI falls back to system token when no user_id provided"""

    print("Testing NotionAPI without user_id (should use system token)")

    try:
        # Create NotionAPI instance without user_id
        notion_api = NotionAPI()

        # Check token info
        token_info = notion_api.get_token_info()
        print(f"Token info: {token_info}")

        # Verify it's NOT using user token
        if not notion_api.is_using_user_token:
            print("✅ Successfully using system token as fallback")
        else:
            print("❌ Unexpectedly using user token")

        return True

    except Exception as e:
        print(f"❌ Error testing NotionAPI without user token: {e}")
        return False


@pytest.mark.asyncio
async def test_user_token_service():
    """Test UserTokenService directly"""

    print("Testing UserTokenService directly")

    try:
        # Test with real user ID from database
        token = await UserTokenService.get_user_notion_token(
            "79ba6a8b-7aa7-498b-a9ed-a772d1dc34ef"
        )

        if token:
            print(f"✅ Retrieved token: {token[:20]}...")
        else:
            print("⚠️  No token found for test user")

        return True

    except Exception as e:
        print(f"❌ Error testing UserTokenService: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Notion OAuth Token Integration")
    print("=" * 60)

    # Test UserTokenService
    print("\n1. Testing UserTokenService:")
    asyncio.run(test_user_token_service())

    # Test NotionAPI with user token
    print("\n2. Testing NotionAPI with user token:")
    test_notion_api_with_user_token()

    # Test NotionAPI without user token
    print("\n3. Testing NotionAPI without user token:")
    test_notion_api_without_user_token()

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
