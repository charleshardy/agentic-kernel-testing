#!/bin/bash
# Setup script for test environment

echo "Setting up test environment..."

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "pip3 not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# Install required packages
echo "Installing required packages..."
pip3 install --user hypothesis openai anthropic boto3 pydantic pydantic-settings python-dotenv

echo "Test environment setup complete!"
echo "Run tests with: pytest tests/property/"
