#!/usr/bin/env python3
"""
Test Runner for Flowstate Backend

This script runs all tests in the correct order and provides a comprehensive
test report for the Notion OAuth integration.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --oauth-only       # Run only OAuth tests
    python run_tests.py --integration-only # Run only integration tests
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from tests.oauth.test_notion_oauth import NotionOAuthTests
from tests.integration.test_backend_integration import BackendIntegrationTests


async def run_oauth_tests() -> bool:
    """Run OAuth-specific tests"""
    print("🔑 Running OAuth Test Suite...")
    oauth_tests = NotionOAuthTests()
    return await oauth_tests.run_all_tests()


def run_integration_tests() -> bool:
    """Run backend integration tests"""
    print("🔧 Running Integration Test Suite...")
    integration_tests = BackendIntegrationTests()
    return integration_tests.run_all_tests()


async def run_all_tests() -> bool:
    """Run all test suites"""
    print("🧪 Flowstate Backend Test Suite")
    print("=" * 60)

    # Run integration tests first (these check if backend is running)
    print("\n" + "=" * 60)
    integration_success = run_integration_tests()

    if not integration_success:
        print("\n❌ Integration tests failed. Skipping OAuth tests.")
        print("Please ensure your backend is running and properly configured.")
        return False

    # Run OAuth tests
    print("\n" + "=" * 60)
    oauth_success = await run_oauth_tests()

    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)

    if integration_success and oauth_success:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Your Notion OAuth integration is ready for production!")
        print("\n📋 Next Steps:")
        print("  1. Commit your changes to git")
        print("  2. Deploy to your production environment")
        print("  3. Test the OAuth flow in production")
        print("  4. Monitor the logs for any issues")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("\n🔍 Issues found:")
        if not integration_success:
            print("  • Backend integration issues")
        if not oauth_success:
            print("  • OAuth configuration issues")
        print("\nPlease fix these issues before deploying to production.")
        return False


def main():
    """Main test runner with command line options"""
    parser = argparse.ArgumentParser(description="Run Flowstate backend tests")
    parser.add_argument("--oauth-only", action="store_true", help="Run only OAuth tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")

    args = parser.parse_args()

    if args.oauth_only:
        success = asyncio.run(run_oauth_tests())
    elif args.integration_only:
        success = run_integration_tests()
    else:
        success = asyncio.run(run_all_tests())

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
