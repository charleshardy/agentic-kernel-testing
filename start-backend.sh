#!/bin/bash

echo "🚀 Starting Agentic AI Testing System Backend API..."

# Kill any existing processes on port 8000
echo "🔄 Stopping existing processes on port 8000..."
pkill -f "uvicorn.*8000" 2>/dev/null || echo "   No existing processes found"

# Wait a moment for processes to stop
sleep 2

# Check if port is free
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is still in use. Trying to kill process..."
    PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    kill -9 $PID 2>/dev/null || echo "   Could not kill process $PID"
    sleep 1
fi

echo "📋 Starting API server..."
echo "   Host: 0.0.0.0"
echo "   Port: 8000"
echo "   Mode: Development (auto-reload enabled)"
echo ""
echo "📱 API will be available at:"
echo "   • Health check: http://localhost:8000/api/v1/health"
echo "   • Documentation: http://localhost:8000/docs"
echo "   • OpenAPI spec: http://localhost:8000/openapi.json"
echo ""
echo "🔧 Starting server..."

# Start the API server
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload