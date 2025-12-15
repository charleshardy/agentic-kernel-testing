#!/bin/bash

# AWS SSO Setup Script for Amazon Q Developer Pro
# This script helps configure AWS SSO for the Agentic AI Testing System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Configuration
SSO_START_URL="https://d-926706e585.awsapps.com/start"
SSO_REGION="us-west-2"
ACCOUNT_ID="926706e585"
ROLE_NAME="AmazonQDeveloperAccess"
PROFILE_NAME="default"

echo "🚀 AWS SSO Setup for Amazon Q Developer Pro"
echo "============================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    error "AWS CLI is not installed"
    echo "Please install AWS CLI v2 from: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

log "AWS CLI found: $(aws --version)"

# Check if already configured
if aws configure list-profiles | grep -q "^${PROFILE_NAME}$"; then
    warn "Profile '${PROFILE_NAME}' already exists"
    read -p "Do you want to reconfigure it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Skipping configuration"
        exit 0
    fi
fi

# Configure AWS SSO
log "Configuring AWS SSO profile..."

# Create the SSO configuration
aws configure sso \
    --profile "${PROFILE_NAME}" \
    --sso-session "${PROFILE_NAME}" \
    --sso-start-url "${SSO_START_URL}" \
    --sso-region "${SSO_REGION}" \
    --sso-account-id "${ACCOUNT_ID}" \
    --sso-role-name "${ROLE_NAME}" \
    --region "${SSO_REGION}" \
    --output json

if [ $? -eq 0 ]; then
    log "AWS SSO profile configured successfully"
else
    error "Failed to configure AWS SSO profile"
    exit 1
fi

# Attempt to login
log "Attempting to login to AWS SSO..."
if aws sso login --profile "${PROFILE_NAME}"; then
    log "AWS SSO login successful"
else
    warn "AWS SSO login failed or was cancelled"
    echo "You can login later using: aws sso login --profile ${PROFILE_NAME}"
fi

# Verify the setup
log "Verifying AWS SSO setup..."
if aws sts get-caller-identity --profile "${PROFILE_NAME}" &> /dev/null; then
    log "✅ AWS SSO verification successful"
    
    # Show caller identity
    info "Current AWS identity:"
    aws sts get-caller-identity --profile "${PROFILE_NAME}"
else
    warn "AWS SSO verification failed"
    echo "You may need to login: aws sso login --profile ${PROFILE_NAME}"
fi

echo
log "🎉 AWS SSO setup completed!"
echo
info "Next steps:"
echo "1. The .env file is already configured for Amazon Q Developer Pro"
echo "2. Run the verification script: python3 verify_aws_sso.py"
echo "3. Start using the Agentic AI Testing System with Amazon Q Developer Pro"
echo
info "Useful commands:"
echo "• Login: aws sso login --profile ${PROFILE_NAME}"
echo "• Check identity: aws sts get-caller-identity --profile ${PROFILE_NAME}"
echo "• Logout: aws sso logout"