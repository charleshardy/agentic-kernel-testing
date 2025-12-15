#!/bin/bash

echo "🔧 Fixing common dashboard issues and starting development server..."

# Kill any existing Vite processes
echo "🔄 Stopping existing Vite processes..."
pkill -f "vite" 2>/dev/null || echo "   No existing Vite processes found"

# Check TypeScript compilation
echo "📝 Checking TypeScript compilation..."
if npm run type-check; then
    echo "✅ TypeScript compilation successful"
else
    echo "⚠️  TypeScript compilation has warnings/errors, but continuing..."
fi

# Find available port
echo "🌐 Finding available port..."
PORT=3000
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    echo "   Port $PORT is in use, trying $((PORT+1))..."
    PORT=$((PORT+1))
done

echo "✅ Using port $PORT"

# Set environment variables for headless operation
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/runtime-$USER}
export QT_QPA_PLATFORM=offscreen
export QT_LOGGING_RULES='*=false'
mkdir -p "$XDG_RUNTIME_DIR" 2>/dev/null

echo "🚀 Starting Vite development server on port $PORT..."
echo "📱 Dashboard will be available at: http://localhost:$PORT"
echo "🔧 Environment configured for headless operation"
echo ""

# Start the development server
npm run dev:clean -- --port $PORT