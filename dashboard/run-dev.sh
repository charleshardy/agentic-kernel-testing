#!/bin/bash

# Fix Qt and XDG warnings for Vite development server in headless environments

echo "🔧 Configuring environment for headless Vite development..."

# Fix XDG_RUNTIME_DIR warning
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/runtime-$USER}
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

# Fix Qt session management warnings
export QT_QPA_PLATFORM=offscreen
export QT_LOGGING_RULES='*=false'

# Disable display for headless environments
export DISPLAY=${DISPLAY:-}

echo "✅ Environment configured:"
echo "   📁 XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
echo "   🖥️  QT_QPA_PLATFORM: $QT_QPA_PLATFORM"
echo "   🔇 Qt logging disabled"

echo "🚀 Starting Vite development server..."

# Run Vite dev server with clean environment
npm run dev:clean