#!/usr/bin/env python3
"""
Setup script for Supabase integration
This script helps configure your project to use Supabase
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None


def check_file_exists(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        print(f"✅ {description} found")
        return True
    else:
        print(f"❌ {description} not found")
        return False


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    if env_example.exists():
        print("🔄 Creating .env file from template...")
        with open(env_example, "r") as f:
            content = f.read()

        with open(env_file, "w") as f:
            f.write(content)

        print("✅ .env file created from template")
        print("⚠️  Please update the .env file with your actual Supabase credentials")
        return True
    else:
        print("❌ .env.example not found")
        return False


def install_dependencies():
    """Install required Python packages"""
    print("🔄 Installing Supabase dependencies...")

    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Warning: Not in a virtual environment")
        print("   Consider running: python -m venv venv && source venv/bin/activate")

    # Install Supabase packages
    packages = ["supabase>=2.4.0", "postgrest-py>=0.13.0"]

    for package in packages:
        result = run_command(f"pip install {package}", f"Installing {package}")
        if result is None:
            return False

    return True


def test_supabase_connection():
    """Test Supabase connection with current environment variables"""
    print("🔄 Testing Supabase connection...")

    try:
        # Import after installation
        from config.supabase import test_connection

        if test_connection():
            print("✅ Supabase connection successful")
            return True
        else:
            print("❌ Supabase connection failed")
            print("   Please check your SUPABASE_URL and SUPABASE_ANON_KEY in .env")
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure Supabase packages are installed")
        return False
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Setting up Supabase integration for FlowState")
    print("=" * 50)

    # Step 1: Check if we're in the right directory
    if not check_file_exists("app.py", "FlowState app.py"):
        print("❌ Please run this script from the backend directory")
        sys.exit(1)

    # Step 2: Create .env file
    if not create_env_file():
        print("❌ Failed to create .env file")
        sys.exit(1)

    # Step 3: Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Step 4: Check required files
    required_files = [
        ("config/supabase.py", "Supabase configuration"),
        ("services/database.py", "Database service layer"),
        ("database/supabase_schema.sql", "Database schema"),
    ]

    all_files_exist = True
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_files_exist = False

    if not all_files_exist:
        print("❌ Some required files are missing")
        sys.exit(1)

    print("=" * 50)
    print("🎉 Setup completed!")
    print()
    print("Next steps:")
    print("1. Create a Supabase project at https://supabase.com/dashboard")
    print("2. Update your .env file with:")
    print("   - SUPABASE_URL (from your project settings)")
    print("   - SUPABASE_ANON_KEY (from your project API settings)")
    print("   - SUPABASE_SERVICE_KEY (from your project API settings, optional)")
    print()
    print("3. Run the SQL schema in your Supabase SQL editor:")
    print("   Copy the contents of database/supabase_schema.sql")
    print()
    print("4. Test the connection:")
    print('   python -c "from config.supabase import test_connection; test_connection()"')
    print()
    print("5. Start your application:")
    print("   python app.py")


if __name__ == "__main__":
    main()
