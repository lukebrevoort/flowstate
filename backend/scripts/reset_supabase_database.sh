#!/bin/bash

# Supabase Database Reset Script
# This script uses the Supabase CLI to reset and recreate your database schema

echo "🚀 Supabase Database Reset Script"
echo "=================================="

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Error: Supabase CLI is not installed."
    echo "Install it with: npm install -g supabase"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# File paths
RESET_FILE="$SCRIPT_DIR/reset_supabase_tables.sql"
SCHEMA_FILE="$BACKEND_DIR/database/supabase_schema.sql"

# Check if files exist
if [ ! -f "$RESET_FILE" ]; then
    echo "❌ Error: Reset file not found at $RESET_FILE"
    exit 1
fi

if [ ! -f "$SCHEMA_FILE" ]; then
    echo "❌ Error: Schema file not found at $SCHEMA_FILE"
    exit 1
fi

echo ""
echo "⚠️  WARNING: This will DELETE all existing tables and data!"
echo "Make sure you have a backup of any important data."
echo "Reset file: $RESET_FILE"
echo "Schema file: $SCHEMA_FILE"
echo ""

read -p "Do you want to proceed? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled."
    exit 0
fi

echo ""
echo "🔄 Starting database reset process..."

# Check if we're in a Supabase project
if [ ! -f "supabase/config.toml" ]; then
    echo "❌ Error: Not in a Supabase project directory or supabase/config.toml not found"
    echo "Make sure you're in your project root and have run 'supabase init'"
    exit 1
fi

# Step 1: Reset existing tables
echo "🔄 Executing table reset..."
if supabase db reset --db-url "$(supabase status | grep 'DB URL' | awk '{print $3}')" < "$RESET_FILE"; then
    echo "✅ Existing tables and functions dropped successfully"
else
    echo "❌ Failed to reset tables using reset file. Trying alternative method..."
    
    # Alternative: Use supabase db reset (this will reset everything)
    echo "🔄 Performing full database reset..."
    supabase db reset
fi

# Step 2: Apply new schema
echo "🔄 Applying new schema..."
if supabase db push; then
    echo "✅ New schema applied successfully"
else
    echo "⚠️  Schema push failed. Trying to apply schema file directly..."
    
    # Apply schema file directly
    if supabase db reset --db-url "$(supabase status | grep 'DB URL' | awk '{print $3}')" < "$SCHEMA_FILE"; then
        echo "✅ Schema applied successfully"
    else
        echo "❌ Failed to apply schema"
        exit 1
    fi
fi

echo ""
echo "🎉 Database reset completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test your application to ensure everything works"
echo "2. Run 'supabase db diff' to see any changes"
echo "3. Update your Supabase Auth settings for the security enhancements"
echo "4. Consider enabling MFA and leaked password protection in Supabase dashboard"
echo "5. Update your Postgres version if possible"
