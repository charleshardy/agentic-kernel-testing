# Dashboard Troubleshooting Guide

## XDG_RUNTIME_DIR Warning

### Issue
When running `npm run dev`, you see warnings like:
```
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-wruser'
```

### Explanation
This is a **warning, not an error**. The Vite development server is still working correctly. This warning appears because:

1. **XDG_RUNTIME_DIR** is an environment variable used by Linux desktop environments
2. In headless/server environments, it's often not set
3. Vite (via Electron/Chromium components) expects this directory for temporary files
4. The system automatically falls back to `/tmp/runtime-<username>`

### Solutions

#### Option 1: Use the Fixed Script (Recommended)
```bash
npm run dev  # Now includes XDG_RUNTIME_DIR fix
```

#### Option 2: Set Environment Variable Manually
```bash
export XDG_RUNTIME_DIR=/tmp/runtime-$USER
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
npm run dev:clean
```

#### Option 3: Use the Shell Script
```bash
./run-dev.sh
```

#### Option 4: Add to Your Shell Profile
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/runtime-$USER}
mkdir -p "$XDG_RUNTIME_DIR" 2>/dev/null
chmod 700 "$XDG_RUNTIME_DIR" 2>/dev/null
```

### Verification
After applying any solution, you should see:
```bash
$ npm run dev

> agentic-testing-dashboard@1.0.0 dev
> export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/runtime-wruser} && mkdir -p "$XDG_RUNTIME_DIR" && vite

  VITE v4.1.0  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Other Common Issues

### Port Already in Use
If you see "Port 5173 is already in use":
```bash
# Kill existing process
pkill -f vite
# Or use a different port
npm run dev -- --port 3000
```

### Node.js Version Issues
Ensure you have Node.js 18+ installed:
```bash
node --version  # Should be 18.0.0 or higher
npm --version   # Should be 8.0.0 or higher
```

### Dependencies Not Installed
If you see module not found errors:
```bash
npm install
```

### TypeScript Errors
Check TypeScript configuration:
```bash
npm run type-check
```

### Build Issues
For production build problems:
```bash
npm run build
```

## Getting Help

1. **Check the console output** - Most issues are clearly described in error messages
2. **Verify system requirements** - Node.js 18+, npm 8+
3. **Clear cache** - `rm -rf node_modules package-lock.json && npm install`
4. **Check network** - Ensure no firewall blocking localhost:5173

## Development Workflow

```bash
# 1. Install dependencies (first time only)
npm install

# 2. Start development server
npm run dev

# 3. Open browser to http://localhost:5173

# 4. Make changes to src/ files - Vite will auto-reload

# 5. Build for production
npm run build
```

The dashboard should now run without warnings and provide a smooth development experience!