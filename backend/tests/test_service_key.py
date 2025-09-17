#!/usr/bin/env python3
"""
Test script to verify Supabase service key configuration
"""
import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from config.supabase import get_supabase_service_client, get_supabase_config
from dotenv import load_dotenv

load_dotenv()


async def test_service_key():
    """Test if service key is properly configured"""
    print("🔧 Testing Supabase Service Key Configuration")
    print("=" * 50)

    try:
        # Test configuration
        config = get_supabase_config()
        print(f"✅ Supabase URL: {config.url}")

        # Check if service key exists
        if not config.service_key:
            print("❌ SUPABASE_SERVICE_KEY not found in environment")
            return False

        # Check if service key looks correct (contains service_role)
        if "service_role" not in config.service_key:
            print("❌ Service key doesn't contain 'service_role'")
            return False
        else:
            print("✅ Service key contains 'service_role'")

        # Test service client
        service_client = get_supabase_service_client()
        auth_header = service_client.headers.get("Authorization", "")
        print(f"✅ Service client auth header: {auth_header[:50]}...")

        # Test a simple query
        print("\n🔄 Testing service client with a simple query...")

        try:
            # Try to query profiles table (should work with service role)
            result = await service_client.query("profiles", "GET")
            print(f"✅ Service query successful! Found {len(result)} profiles")
            return True

        except Exception as e:
            print(f"❌ Service query failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


async def test_token_storage():
    """Test token storage with service key"""
    print("\n🔧 Testing Token Storage")
    print("=" * 30)

    try:
        service_client = get_supabase_service_client()

        # Test data
        test_data = {
            "user_id": "00000000-0000-0000-0000-000000000000",  # Dummy UUID
            "integration_type": "notion",
            "access_token": "test_token_123",
            "integration_data": {"test": "data"},
            "is_active": True,
        }

        print(f"🔄 Attempting to insert test integration...")
        result = await service_client.query("user_integrations", "POST", data=test_data)
        print(f"✅ Test insertion successful!")

        # Clean up - delete the test record
        await service_client.query(
            "user_integrations",
            "DELETE",
            filters={"user_id": test_data["user_id"], "integration_type": "notion"},
        )
        print(f"✅ Cleanup successful!")

        return True

    except Exception as e:
        print(f"❌ Token storage test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Supabase Service Key Test Suite")
    print("=" * 60)

    # Test 1: Service key configuration
    config_ok = await test_service_key()

    if config_ok:
        # Test 2: Token storage
        storage_ok = await test_token_storage()

        if storage_ok:
            print("\n🎉 All tests passed! Service key is properly configured.")
        else:
            print("\n❌ Token storage test failed. Check RLS policies.")
    else:
        print("\n❌ Service key configuration failed.")

    print("\n📋 Next steps if tests failed:")
    print("1. Verify SUPABASE_SERVICE_KEY in .env file")
    print("2. Run the RLS policy fix in Supabase dashboard")
    print("3. Restart your backend server")


if __name__ == "__main__":
    asyncio.run(main())
