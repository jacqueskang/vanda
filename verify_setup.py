#!/usr/bin/env python
"""
Quick setup verification script for the Business Team project.

Run this to verify your environment is correctly configured.
"""

import sys
import os

def check_python_version():
    """Verify Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"❌ Python {version.major}.{version.minor} detected. Need Python 3.10+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Verify all required packages are installed."""
    required = [
        'agent_framework',
        'azure.identity',
        'azure.ai.agentserver',
        'dotenv',
    ]
    
    all_ok = True
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_env_file():
    """Check if .env file exists and has GitHub token."""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    print("✅ .env file found")
    
    # Check for token
    with open('.env', 'r') as f:
        content = f.read()
        if 'your_github_token_here' in content or 'GITHUB_TOKEN=' not in content:
            print("⚠️  GitHub token not configured in .env")
            print("   Get one at: https://github.com/settings/tokens")
            print("   Then edit .env and set GITHUB_TOKEN=ghp_xxxxx")
            return False
        else:
            print("✅ GitHub token configured")
            return True


def main():
    """Run all checks."""
    print("\n" + "="*50)
    print("🔍 BUSINESS TEAM - Setup Verification")
    print("="*50 + "\n")
    
    print("Checking Python version...")
    py_ok = check_python_version()
    
    print("\nChecking dependencies...")
    deps_ok = check_dependencies()
    
    print("\nChecking configuration...")
    env_ok = check_env_file()
    
    print("\n" + "="*50)
    if py_ok and deps_ok:
        if env_ok:
            print("✅ All checks passed! Ready to run:")
            print("   python scripts/business_team.py")
        else:
            print("⚠️  Partial: Code is ready, but configuration incomplete")
            print("\nTo complete setup:")
            print("1. Get GitHub token: https://github.com/settings/tokens")
            print("2. Edit .env and set GITHUB_TOKEN=your_token")
            print("3. Run: python scripts/business_team.py")
    else:
        print("❌ Setup incomplete. Run: pip install -r requirements.txt")
    
    print("="*50 + "\n")
    return 0 if (py_ok and deps_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
