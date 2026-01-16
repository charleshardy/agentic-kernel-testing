#!/bin/bash
# Script to restart the API server

echo "Finding API server process..."
API_PID=$(ps aux | grep "python.*api.server" | grep -v grep | awk '{print $2}')

if [ -z "$API_PID" ]; then
    echo "No API server process found"
else
    echo "Found API server process: $API_PID"
    echo "Killing process..."
    kill $API_PID
    sleep 2
    
    # Check if process is still running
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "Process still running, forcing kill..."
        kill -9 $API_PID
    fi
    
    echo "API server stopped"
fi

echo ""
echo "Starting API server..."
echo "Run this command in a separate terminal:"
echo "  venv/bin/python -m api.server"
echo ""
echo "Or run in background:"
echo "  nohup venv/bin/python -m api.server > api_server.log 2>&1 &"
