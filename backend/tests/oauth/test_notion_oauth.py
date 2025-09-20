#!/usr/bin/env python3
"""
Notion OAuth Integration Tests

This module contains comprehensive tests for the Notion OAuth functionality,
including URL generation, token exchange, and integration with Supabase.
"""

import os
import sys
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from urllib.parse import quote, parse_qs, urlparse

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

from services.notion_oauth import NotionOAuthService
from services.user_tokens import UserTokenService


class NotionOAuthTests:
    """Test suite for Notion OAuth functionality"""

    def __init__(self):
        self.oauth_service = NotionOAuthService()
        self.user_token_service = UserTokenService()

    def test_environment_config(self) -> bool:
        """Test that all required environment variables are properly configured"""
        print("🔧 Testing Environment Configuration...")

        client_id = os.getenv("NOTION_OAUTH_CLIENT_ID")
        client_secret = os.getenv("NOTION_OAUTH_CLIENT_SECRET")
        redirect_uri = os.getenv("NOTION_OAUTH_REDIRECT_URI")

        print(f"  Client ID: {client_id}")
        print(
            f"  Client Secret: {'*' * len(client_secret) if client_secret else 'None'}"
        )
        print(f"  Redirect URI: {redirect_uri}")

        if not all([client_id, client_secret, redirect_uri]):
            print("  ❌ Missing required environment variables!")
            return False

        # Validate redirect URI format
        if "oauth/authorize" in redirect_uri:
            print(
                "  ❌ REDIRECT_URI contains the full OAuth URL instead of just the callback endpoint!"
            )
            return False

        if not redirect_uri.startswith("https://"):
            print("  ❌ REDIRECT_URI should use HTTPS in production!")
            return False

        print("  ✅ Environment configuration is valid!")
        return True

    def test_oauth_url_generation(self) -> bool:
        """Test OAuth authorization URL generation"""
        print("🚀 Testing OAuth URL Generation...")

        try:
            # Test with a sample user ID
            test_user_id = "test-user-123"
            oauth_response = self.oauth_service.generate_auth_url(test_user_id)

            # Validate response structure
            if not isinstance(oauth_response, dict):
                print("  ❌ OAuth response is not a dictionary!")
                return False

            if "auth_url" not in oauth_response or "state" not in oauth_response:
                print("  ❌ OAuth response missing required keys!")
                return False

            auth_url = oauth_response["auth_url"]
            state = oauth_response["state"]

            print(f"  Generated URL: {auth_url}")
            print(f"  State: {state}")

            # Parse and validate URL components
            parsed_url = urlparse(auth_url)
            query_params = parse_qs(parsed_url.query)

            # Check required parameters
            required_params = [
                "client_id",
                "response_type",
                "owner",
                "redirect_uri",
                "state",
            ]
            for param in required_params:
                if param not in query_params:
                    print(f"  ❌ Missing required parameter: {param}")
                    return False

            # Validate parameter values
            if query_params["response_type"][0] != "code":
                print("  ❌ response_type should be 'code'")
                return False

            if query_params["owner"][0] != "user":
                print("  ❌ owner should be 'user'")
                return False

            # Check that state contains user ID
            if test_user_id not in state:
                print("  ❌ State does not contain user ID")
                return False

            print("  ✅ OAuth URL generation is working correctly!")
            return True

        except Exception as e:
            print(f"  ❌ Error generating OAuth URL: {e}")
            return False

    async def test_token_service_integration(self) -> bool:
        """Test integration with user token service"""
        print("🔗 Testing Token Service Integration...")

        try:
            # Test getting integration status for a non-existent user
            test_user_id = "test-user-nonexistent"
            is_connected = await self.user_token_service.is_integration_connected(
                test_user_id, "notion"
            )

            if is_connected:
                print("  ❌ Expected False for non-existent user, got True")
                return False

            print("  ✅ Token service correctly handles non-existent users!")
            return True

        except Exception as e:
            print(f"  ❌ Error testing token service: {e}")
            return False

    def test_oauth_security(self) -> bool:
        """Test OAuth security features"""
        print("🔒 Testing OAuth Security Features...")

        try:
            # Generate multiple auth URLs and ensure states are unique
            states = []
            for i in range(5):
                oauth_response = self.oauth_service.generate_auth_url(f"user-{i}")
                states.append(oauth_response["state"])

            # Check that all states are unique
            if len(set(states)) != len(states):
                print("  ❌ Generated states are not unique!")
                return False

            # Check state format (should contain user ID and random token)
            for state in states:
                if ":" not in state:
                    print("  ❌ State format is incorrect (missing separator)")
                    return False

                user_part, token_part = state.split(":", 1)
                if not user_part.startswith("user-"):
                    print("  ❌ State doesn't contain expected user ID")
                    return False

                if (
                    len(token_part) < 32
                ):  # URL-safe base64 tokens should be at least 32 chars
                    print("  ❌ State token part seems too short")
                    return False

            print("  ✅ OAuth security features are working correctly!")
            return True

        except Exception as e:
            print(f"  ❌ Error testing OAuth security: {e}")
            return False

    async def run_all_tests(self) -> bool:
        """Run all OAuth tests"""
        print("🧪 Running Notion OAuth Test Suite")
        print("=" * 50)

        tests = [
            ("Environment Config", self.test_environment_config),
            ("OAuth URL Generation", self.test_oauth_url_generation),
            ("Token Service Integration", self.test_token_service_integration),
            ("OAuth Security", self.test_oauth_security),
        ]

        results = []
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                results.append(result)
            except Exception as e:
                print(f"  ❌ Test failed with exception: {e}")
                results.append(False)

        # Summary
        passed = sum(results)
        total = len(results)

        print(f"\n📊 Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! OAuth integration is ready for production.")
            return True
        else:
            print("💥 Some tests failed. Please review the issues above.")
            return False


async def main():
    """Main test runner"""
    test_suite = NotionOAuthTests()
    success = await test_suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
