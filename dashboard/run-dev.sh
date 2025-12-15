#!/bin/bash

# Fix XDG_RUNTIME_DIR warning for Vite development server
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/runtime-$USER}
mkdir -p "$XDG_RUNTIME_DIR"

# Set proper permissions
chmod 700 "$XDG_RUNTIME_DIR"

echo "🚀 Starting Vite development server..."
echo "📁 XDG_RUNTIME_DIR set to: $XDG_RUNTIME_DIR"

# Run Vite dev server
npm run dev