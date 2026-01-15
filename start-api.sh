#!/bin/bash
# Startup script for the Agentic AI Testing System API server

# Activate virtual environment and start the API server
if [ -d "venv" ]; then
    echo "Using virtual environment..."
    venv/bin/python -m api.server "$@"
else
    echo "Virtual environment not found. Please create one with: python3 -m venv venv"
    echo "Then install dependencies with: venv/bin/pip install -r requirements.txt"
    exit 1
fi
