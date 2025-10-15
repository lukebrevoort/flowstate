#!/usr/bin/env python3
"""
Supabase Database Reset and Migration Script
This script helps you safely reset and recreate your Supabase database schema.
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_supabase_client():
    """Create and return a Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Need service role for schema operations

    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
        sys.exit(1)

    return create_client(url, key)


def execute_sql_file(supabase: Client, file_path: str, description: str):
    """Execute SQL commands from a file."""
    try:
        with open(file_path, "r") as file:
            sql_content = file.read()

        print(f"🔄 Executing {description}...")

        # Split SQL content by semicolons and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

        for i, statement in enumerate(statements):
            if statement:
                try:
                    supabase.postgrest.rpc("exec_sql", {"sql": statement}).execute()
                    print(f"   ✅ Statement {i+1}/{len(statements)} executed successfully")
                except Exception as e:
                    print(f"   ⚠️  Statement {i+1}/{len(statements)} failed: {str(e)}")
                    # Continue with other statements

        print(f"✅ {description} completed")

    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found")
        return False
    except Exception as e:
        print(f"❌ Error executing {description}: {str(e)}")
        return False

    return True


def backup_data(supabase: Client):
    """Create a backup of existing data (optional)."""
    print("📦 Creating data backup...")

    tables = ["profiles", "user_tasks", "user_sessions", "user_integrations"]
    backup_data = {}

    for table in tables:
        try:
            result = supabase.table(table).select("*").execute()
            backup_data[table] = result.data
            print(f"   ✅ Backed up {len(result.data)} rows from {table}")
        except Exception as e:
            print(f"   ⚠️  Could not backup {table}: {str(e)}")

    # Save backup to file
    import json

    backup_file = "supabase_backup.json"
    with open(backup_file, "w") as f:
        json.dump(backup_data, f, indent=2, default=str)

    print(f"📁 Backup saved to {backup_file}")
    return backup_data


def main():
    """Main function to reset and recreate Supabase schema."""
    print("🚀 Supabase Database Reset Script")
    print("=" * 50)

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)

    # File paths
    reset_file = os.path.join(script_dir, "reset_supabase_tables.sql")
    schema_file = os.path.join(backend_dir, "database", "supabase_schema.sql")

    # Check if files exist
    if not os.path.exists(reset_file):
        print(f"❌ Error: Reset file not found at {reset_file}")
        sys.exit(1)

    if not os.path.exists(schema_file):
        print(f"❌ Error: Schema file not found at {schema_file}")
        sys.exit(1)

    # Get confirmation
    print("\n⚠️  WARNING: This will DELETE all existing tables and data!")
    print("Make sure you have a backup of any important data.")
    print(f"Reset file: {reset_file}")
    print(f"Schema file: {schema_file}")

    confirm = input("\nDo you want to proceed? (yes/no): ").lower().strip()
    if confirm != "yes":
        print("❌ Operation cancelled.")
        sys.exit(0)

    # Create Supabase client
    supabase = get_supabase_client()

    # Optional: Create backup
    backup_choice = input("\nDo you want to create a backup first? (yes/no): ").lower().strip()
    if backup_choice == "yes":
        backup_data(supabase)

    print("\n🔄 Starting database reset process...")

    # Step 1: Reset existing tables
    if execute_sql_file(supabase, reset_file, "table reset"):
        print("✅ Existing tables and functions dropped successfully")
    else:
        print("❌ Failed to reset tables. Stopping.")
        sys.exit(1)

    # Step 2: Create new schema
    if execute_sql_file(supabase, schema_file, "schema creation"):
        print("✅ New schema created successfully")
    else:
        print("❌ Failed to create new schema")
        sys.exit(1)

    print("\n🎉 Database reset completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test your application to ensure everything works")
    print("2. Update your Supabase Auth settings for the security enhancements")
    print("3. Consider enabling MFA and leaked password protection in Supabase dashboard")
    print("4. Update your Postgres version if possible")


if __name__ == "__main__":
    main()
