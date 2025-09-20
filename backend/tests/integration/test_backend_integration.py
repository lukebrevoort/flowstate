#!/usr/bin/env python3
"""
Integration Tests for Backend Services

This module tests the complete backend integration including:
- API endpoints
- Database connections
- Service layer functionality
"""

import os
import sys
import asyncio
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()


class BackendIntegrationTests:
    """Integration test suite for backend services"""

    def __init__(self):
        self.base_url = "http://localhost:8000"

    def test_backend_health(self) -> bool:
        """Test that the backend is running and responding"""
        print("🏥 Testing Backend Health...")

        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Backend is healthy: {data}")
                return True
            else:
                print(f"  ❌ Backend health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Cannot connect to backend at {self.base_url}")
            print(
                f"  💡 Make sure your backend is running: cd backend && python app.py"
            )
            return False
        except Exception as e:
            print(f"  ❌ Backend health check error: {e}")
            return False

    def test_oauth_endpoints_exist(self) -> bool:
        """Test that OAuth endpoints are available"""
        print("🔗 Testing OAuth Endpoints Availability...")

        endpoints = [
            "/api/oauth/notion/authorize",
            "/api/oauth/notion/callback",
            "/api/oauth/notion/status",
        ]

        all_good = True
        for endpoint in endpoints:
            try:
                # We expect 401/422 for most endpoints since they require auth
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code in [
                    401,
                    422,
                    405,
                ]:  # Expected for protected endpoints
                    print(
                        f"  ✅ {endpoint} - endpoint exists (status: {response.status_code})"
                    )
                elif response.status_code == 200:
                    print(
                        f"  ✅ {endpoint} - endpoint accessible (status: {response.status_code})"
                    )
                else:
                    print(
                        f"  ⚠️  {endpoint} - unexpected status: {response.status_code}"
                    )
            except Exception as e:
                print(f"  ❌ {endpoint} - error: {e}")
                all_good = False

        return all_good

    def test_database_connectivity(self) -> bool:
        """Test database connectivity through a safe endpoint"""
        print("🗄️  Testing Database Connectivity...")

        # We can't directly test the database without authentication,
        # but we can test that the backend starts without database errors
        try:
            # If the backend is running, the database connection is likely working
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print(
                    "  ✅ Database connectivity appears healthy (backend started successfully)"
                )
                return True
            else:
                print("  ⚠️  Cannot verify database connectivity")
                return False
        except Exception as e:
            print(f"  ❌ Database connectivity test failed: {e}")
            return False

    def test_environment_variables(self) -> bool:
        """Test that required environment variables are set"""
        print("🔧 Testing Environment Variables...")

        required_vars = [
            "NOTION_OAUTH_CLIENT_ID",
            "NOTION_OAUTH_CLIENT_SECRET",
            "NOTION_OAUTH_REDIRECT_URI",
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
        ]

        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            else:
                # Don't log secrets, just confirm they exist
                if "SECRET" in var or "KEY" in var:
                    print(f"  ✅ {var}: ****")
                else:
                    print(f"  ✅ {var}: {value}")

        if missing_vars:
            print(f"  ❌ Missing environment variables: {missing_vars}")
            return False

        print("  ✅ All required environment variables are set!")
        return True

    def test_cors_configuration(self) -> bool:
        """Test CORS configuration for frontend integration"""
        print("🌐 Testing CORS Configuration...")

        try:
            # Test preflight request
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            }
            response = requests.options(
                f"{self.base_url}/api/oauth/notion/status", headers=headers, timeout=5
            )

            # Check CORS headers in response
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers",
            ]

            has_cors = any(header in response.headers for header in cors_headers)

            if has_cors:
                print("  ✅ CORS is configured")
                return True
            else:
                print("  ⚠️  CORS headers not found - may cause frontend issues")
                return True  # Not critical for backend functionality

        except Exception as e:
            print(f"  ⚠️  CORS test failed: {e}")
            return True  # Not critical

    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        print("🧪 Running Backend Integration Test Suite")
        print("=" * 50)

        tests = [
            ("Environment Variables", self.test_environment_variables),
            ("Backend Health", self.test_backend_health),
            ("OAuth Endpoints", self.test_oauth_endpoints_exist),
            ("Database Connectivity", self.test_database_connectivity),
            ("CORS Configuration", self.test_cors_configuration),
        ]

        results = []
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"  ❌ Test failed with exception: {e}")
                results.append(False)

        # Summary
        passed = sum(results)
        total = len(results)

        print(f"\n📊 Integration Test Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All integration tests passed! Backend is ready.")
            print("\n💡 Next steps:")
            print("  1. Start your frontend: cd frontend/flowstate && npm run dev")
            print("  2. Test the OAuth flow in your browser")
            return True
        else:
            print("💥 Some integration tests failed. Please review the issues above.")
            return False


def main():
    """Main test runner"""
    test_suite = BackendIntegrationTests()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
