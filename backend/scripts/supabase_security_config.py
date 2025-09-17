#!/usr/bin/env python3
"""
Supabase Security Configuration Script
This script addresses the security warnings identified by Supabase linter.
"""

import os
import asyncio
import json
from typing import Dict, Any
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseSecurityConfig:
    """Configure Supabase security settings"""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.project_ref = self.url.split("//")[1].split(".")[0] if self.url else ""

        if not self.url or not self.service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

        self.headers = {
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
            "apikey": self.service_key,
        }

    async def enable_leaked_password_protection(self) -> Dict[str, Any]:
        """Enable leaked password protection via Auth settings"""
        print("🔐 Enabling leaked password protection...")

        auth_config_url = f"{self.url}/auth/v1/admin/settings"

        # Configuration to enable leaked password protection
        config = {
            "SECURITY_LEAKED_PASSWORD_PROTECTION_ENABLED": True,
            "SECURITY_PASSWORD_MIN_LENGTH": 8,
            "SECURITY_PASSWORD_REQUIRE_LETTERS": True,
            "SECURITY_PASSWORD_REQUIRE_NUMBERS": True,
            "SECURITY_PASSWORD_REQUIRE_SYMBOLS": True,
            "SECURITY_PASSWORD_REQUIRE_UPPER": True,
            "SECURITY_PASSWORD_REQUIRE_LOWER": True,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(auth_config_url, headers=self.headers, json=config, timeout=30.0)

                if response.status_code in [200, 204]:
                    print("✅ Leaked password protection enabled successfully")
                    return {"status": "success", "message": "Leaked password protection enabled"}
                else:
                    print(f"⚠️ Failed to enable leaked password protection: {response.status_code}")
                    print(f"Response: {response.text}")
                    return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            print(f"❌ Error enabling leaked password protection: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def configure_mfa_settings(self) -> Dict[str, Any]:
        """Configure Multi-Factor Authentication settings"""
        print("🛡️ Configuring MFA settings...")

        auth_config_url = f"{self.url}/auth/v1/admin/settings"

        # Configuration to enable multiple MFA options
        mfa_config = {
            "MFA_ENABLED": True,
            "MFA_MAX_ENROLLED_FACTORS": 5,
            "MFA_CHALLENGE_EXPIRY_DURATION": "3600",  # 1 hour
            "MFA_TOTP_ENABLED": True,
            "MFA_PHONE_ENABLED": True,
            "MFA_PHONE_AUTOCONFIRM": False,
            "MFA_PHONE_MAX_FREQUENCY": "5m",  # Rate limiting
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(auth_config_url, headers=self.headers, json=mfa_config, timeout=30.0)

                if response.status_code in [200, 204]:
                    print("✅ MFA settings configured successfully")
                    return {"status": "success", "message": "MFA settings configured"}
                else:
                    print(f"⚠️ Failed to configure MFA settings: {response.status_code}")
                    print(f"Response: {response.text}")
                    return {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            print(f"❌ Error configuring MFA settings: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def configure_auth_security(self) -> Dict[str, Any]:
        """Configure additional authentication security settings"""
        print("🔒 Configuring additional auth security...")

        auth_config_url = f"{self.url}/auth/v1/admin/settings"

        # Enhanced security configuration
        security_config = {
            "SECURITY_CAPTCHA_ENABLED": True,
            "SECURITY_CAPTCHA_PROVIDER": "turnstile",
            "RATE_LIMIT_EMAIL_SENT": "100/hour",
            "RATE_LIMIT_SMS_SENT": "60/hour",
            "RATE_LIMIT_TOKEN_REFRESH": "150/hour",
            "RATE_LIMIT_ANONYMOUS_USERS": "30/hour",
            "SESSION_TIMEBOX": "7200",  # 2 hours
            "SECURITY_REFRESH_TOKEN_ROTATION_ENABLED": True,
            "SECURITY_REFRESH_TOKEN_REUSE_INTERVAL": "60",  # 1 minute
            "JWT_EXP": "3600",  # 1 hour JWT expiry
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(auth_config_url, headers=self.headers, json=security_config, timeout=30.0)

                if response.status_code in [200, 204]:
                    print("✅ Additional auth security configured successfully")
                    return {"status": "success", "message": "Auth security configured"}
                else:
                    print(f"⚠️ Failed to configure auth security: {response.status_code}")
                    print(f"Response: {response.text}")
                    return {"status": "warning", "message": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            print(f"❌ Error configuring auth security: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def check_postgres_version(self) -> Dict[str, Any]:
        """Check PostgreSQL version and provide upgrade guidance"""
        print("🐘 Checking PostgreSQL version...")

        try:
            # Use REST API to execute a SQL query
            sql_url = f"{self.url}/rest/v1/rpc/get_postgres_version"

            # First, let's try to get version via a simple query
            query_url = f"{self.url}/rest/v1/"

            async with httpx.AsyncClient() as client:
                # Try to get database info
                response = await client.get(query_url, headers=self.headers, timeout=10.0)

                if response.status_code == 200:
                    print("✅ Connected to PostgreSQL database")
                    print("⚠️ PostgreSQL version check requires manual action:")
                    print("   1. Log into your Supabase dashboard")
                    print("   2. Go to Settings > Infrastructure")
                    print("   3. Check for available PostgreSQL updates")
                    print("   4. Schedule an upgrade during maintenance window")
                    return {
                        "status": "manual_action_required",
                        "message": "PostgreSQL upgrade requires manual action via Supabase dashboard",
                    }
                else:
                    return {"status": "error", "message": f"Cannot connect to database: {response.status_code}"}

        except Exception as e:
            print(f"❌ Error checking PostgreSQL version: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def run_security_configuration(self) -> Dict[str, Any]:
        """Run all security configurations"""
        print("🚀 Starting Supabase security configuration...\n")

        results = {}

        # 1. Enable leaked password protection
        results["leaked_password_protection"] = await self.enable_leaked_password_protection()
        print()

        # 2. Configure MFA settings
        results["mfa_configuration"] = await self.configure_mfa_settings()
        print()

        # 3. Configure additional auth security
        results["auth_security"] = await self.configure_auth_security()
        print()

        # 4. Check PostgreSQL version
        results["postgres_version"] = await self.check_postgres_version()
        print()

        # Summary
        print("📋 Security Configuration Summary:")
        print("=" * 50)

        success_count = 0
        total_count = len(results)

        for feature, result in results.items():
            status_icon = "✅" if result["status"] == "success" else "⚠️" if result["status"] == "warning" else "❌"
            print(f"{status_icon} {feature.replace('_', ' ').title()}: {result['message']}")
            if result["status"] == "success":
                success_count += 1

        print(f"\n🎯 Configuration completed: {success_count}/{total_count} successful")

        if success_count == total_count:
            print("🎉 All security configurations applied successfully!")
        else:
            print("⚠️ Some configurations may require manual intervention.")
            print("   Please check the Supabase dashboard for additional settings.")

        return results


def print_manual_steps():
    """Print manual steps for remaining security configurations"""
    print("\n🔧 Additional Manual Steps Required:")
    print("=" * 50)

    print("\n1. PostgreSQL Version Upgrade:")
    print("   • Log into your Supabase dashboard")
    print("   • Navigate to Settings > Infrastructure")
    print("   • Check for available PostgreSQL updates")
    print("   • Schedule upgrade during maintenance window")

    print("\n2. Enable Additional MFA Options (if needed):")
    print("   • Go to Authentication > Settings in Supabase dashboard")
    print("   • Enable additional MFA providers (SMS, Phone, etc.)")
    print("   • Configure rate limiting for MFA attempts")

    print("\n3. Review Security Policies:")
    print("   • Check RLS policies are working correctly")
    print("   • Test authentication flows")
    print("   • Verify data access permissions")

    print("\n4. Monitor Security Events:")
    print("   • Set up monitoring for the security_log table")
    print("   • Configure alerts for suspicious activities")
    print("   • Regular security audits")


async def main():
    """Main function to run security configuration"""
    try:
        config = SupabaseSecurityConfig()
        results = await config.run_security_configuration()

        print_manual_steps()

        # Save results to file
        with open("security_config_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Results saved to security_config_results.json")

    except Exception as e:
        print(f"❌ Failed to run security configuration: {str(e)}")
        print("Please check your environment variables and try again.")


if __name__ == "__main__":
    asyncio.run(main())
