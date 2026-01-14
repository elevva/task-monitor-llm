#!/usr/bin/env python3
"""
Database configuration module.
Loads credentials from environment variables or .env file.

IMPORTANT: This module requires python-dotenv to be installed.
Install it with: pip install -r requirements.txt
"""
import os
import sys
from pathlib import Path

# Check if python-dotenv is installed
try:
    from dotenv import load_dotenv
except ImportError:
    print("\n❌ ERROR: python-dotenv is not installed")
    print("   This is REQUIRED for the scripts to work.")
    print("\n   Install it with:")
    print("   pip install -r requirements.txt")
    print("\n   Or manually:")
    print("   pip install python-dotenv\n")
    sys.exit(1)

# Load .env file
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    print("\n❌ ERROR: .env file not found")
    print(f"   Expected location: {env_path}")
    print("\n   Create it by copying .env.example:")
    print("   cp .env.example .env")
    print("\n   Then edit .env with your database credentials.\n")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)

def get_db_connection_params():
    """
    Get database connection parameters from environment variables.
    Validates that required credentials are present.

    Returns:
        dict: Connection parameters for mysql.connector
    """
    password = os.environ.get('DB_PASSWORD', '')

    # Validate that password is set
    if not password:
        print("\n❌ ERROR: DB_PASSWORD is not set in .env file")
        print(f"   Check your .env file at: {env_path}")
        print("\n   Make sure it contains:")
        print("   DB_PASSWORD=your_actual_password\n")
        sys.exit(1)

    return {
        'host': os.environ.get('DB_HOST', 'elevvate-prod.ctfjifz3kyak.us-east-1.rds.amazonaws.com'),
        'port': int(os.environ.get('DB_PORT', '3306')),
        'user': os.environ.get('DB_USER', 'claude_rcollados'),
        'password': password,
        'database': os.environ.get('DB_NAME', 'elevvate')
    }
