#!/usr/bin/env python3
"""
GhostNet Setup Script
Initializes project, creates necessary directories, and validates dependencies
"""

import os
import sys
import subprocess
from pathlib import Path


def setup_project():
    """Setup GhostNet project"""
    
    print("🎭 GhostNet Setup Wizard")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    print("✓ Python version check passed")
    
    # Create directories
    print("\n📁 Creating project directories...")
    dirs = [
        "logs",
        "ssh_listener",
        "agents",
        "state_manager",
        "dashboard"
    ]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    print("✓ Directories created")
    
    # Check for .env
    print("\n🔐 Checking environment configuration...")
    if not os.path.exists(".env"):
        print("⚠️  .env file not found. Creating from template...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as f:
                template = f.read()
            with open(".env", "w") as f:
                f.write(template)
            print("✓ Created .env (please update with your API key)")
        else:
            print("❌ .env.example not found")
    else:
        print("✓ .env file found")
    
    # Check for OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-your-key-here":
        print("⚠️  OPENAI_API_KEY not configured. Please update .env")
        return False
    else:
        print("✓ OPENAI_API_KEY is configured")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Update .env with your actual OpenAI API key")
    print("2. Run: python main.py")
    print("3. In another terminal: streamlit run dashboard/app.py")
    
    return True


if __name__ == "__main__":
    setup_project()
