#!/usr/bin/env python3
"""
AWS SSO Configuration Verification Script
Verifies that AWS SSO is properly configured for Amazon Q Developer Pro
"""

import os
import subprocess
import sys
from pathlib import Path

def check_aws_cli():
    """Check if AWS CLI v2 is installed."""
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ AWS CLI installed: {version}")
            return True
        else:
            print("❌ AWS CLI not found")
            return False
    except FileNotFoundError:
        print("❌ AWS CLI not installed")
        return False

def check_sso_config():
    """Check if AWS SSO is configured."""
    aws_config_path = Path.home() / '.aws' / 'config'
    
    if not aws_config_path.exists():
        print("❌ AWS config file not found")
        return False
    
    config_content = aws_config_path.read_text()
    
    # Check for SSO configuration
    if 'sso_start_url' in config_content and 'd-926706e585.awsapps.com' in config_content:
        print("✅ AWS SSO configuration found")
        return True
    else:
        print("❌ AWS SSO not configured for the specified URL")
        return False

def check_sso_login():
    """Check if user is logged into AWS SSO."""
    try:
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity', '--profile', 'default'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ AWS SSO login active")
            print(f"   Identity: {result.stdout.strip()}")
            return True
        else:
            print("❌ AWS SSO login required")
            print("   Run: aws sso login --profile default")
            return False
    except Exception as e:
        print(f"❌ Error checking SSO login: {e}")
        return False

def check_environment_variables():
    """Check if required environment variables are set."""
    required_vars = [
        'AWS_SSO_START_URL',
        'AWS_SSO_REGION', 
        'AWS_SSO_ACCOUNT_ID',
        'AWS_SSO_ROLE_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def main():
    """Main verification function."""
    print("🔍 Verifying AWS SSO Configuration for Amazon Q Developer Pro")
    print("=" * 60)
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping .env file loading")
    
    checks = [
        ("AWS CLI Installation", check_aws_cli),
        ("AWS SSO Configuration", check_sso_config),
        ("Environment Variables", check_environment_variables),
        ("AWS SSO Login Status", check_sso_login),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    
    if all(results):
        print("🎉 All checks passed! AWS SSO is properly configured.")
        print("\n🚀 You can now use Amazon Q Developer Pro with the Agentic AI Testing System.")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        print("\n📖 Setup Instructions:")
        print("1. Install AWS CLI v2: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        print("2. Configure SSO: aws configure sso --profile default")
        print("3. Login: aws sso login --profile default")
        print("4. Verify: aws sts get-caller-identity --profile default")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)