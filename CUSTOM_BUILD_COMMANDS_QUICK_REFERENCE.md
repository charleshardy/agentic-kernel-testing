# Custom Build Commands - Quick Reference

## Feature Overview
Build jobs can now use either **Standard Kernel Build** mode or **Custom Build Commands** mode, allowing you to run any build script or command sequence.

## Accessing the Feature

### Web GUI
1. Go to `http://localhost:3000/`
2. Navigate to **Infrastructure** → **Build Jobs**
3. Click **Submit Build** button
4. Scroll to **Advanced Settings** section
5. Find **Build Mode** dropdown (first field in Advanced Settings)

### If You Don't See the Build Mode Dropdown
The dashboard dev server should have hot-reloaded automatically, but if you don't see the changes:
1. Try a hard refresh: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac)
2. Or restart the dev server:
   ```bash
   # Kill the current dev server
   ps aux | grep vite | grep -v grep | awk '{print $2}' | xargs kill
   
   # Start it again
   cd dashboard && npm run dev
   ```

## Build Modes

### 1. Standard Kernel Build (Default)
Traditional kernel compilation with make commands.

**Configuration Options:**
- **Kernel Config**: defconfig name or path (e.g., `defconfig`, `x86_64_defconfig`)
- **Extra Make Arguments**: Comma-separated (e.g., `ARCH=arm64, CROSS_COMPILE=aarch64-linux-gnu-`)
- **Artifact Patterns**: One per line, supports glob patterns
  ```
  arch/*/boot/bzImage
  vmlinux
  *.dtb
  ```

### 2. Custom Build Commands
Run any custom build script or command sequence.

**Configuration Options:**
- **Pre-Build Commands** (optional): Setup commands run before build
  ```bash
  export CROSS_COMPILE=aarch64-linux-gnu-
  export ARCH=arm64
  ./apply-patches.sh
  ```

- **Build Commands** (required): Main build commands
  ```bash
  make qemu_arm64_defconfig
  make -j$(nproc)
  make modules
  ```

- **Post-Build Commands** (optional): Cleanup or verification commands
  ```bash
  ls -lh u-boot.bin
  file u-boot.bin
  ./run-tests.sh
  ```

- **Artifact Patterns**: Files to collect after build
  ```
  u-boot.bin
  u-boot
  *.dtb
  build/*
  ```

## Example Use Cases

### U-Boot Build
```
Build Mode: Custom Build Commands
Pre-Build Commands:
  export CROSS_COMPILE=aarch64-linux-gnu-
  export ARCH=arm64

Build Commands:
  make qemu_arm64_defconfig
  make -j$(nproc)

Post-Build Commands:
  ls -lh u-boot.bin

Artifact Patterns:
  u-boot.bin
  u-boot
  *.dtb
```

### Kernel with Custom Patches
```
Build Mode: Custom Build Commands
Pre-Build Commands:
  curl -O https://example.com/my-patch.patch
  git apply my-patch.patch

Build Commands:
  make defconfig
  make -j$(nproc)
  make modules

Artifact Patterns:
  arch/x86/boot/bzImage
  vmlinux
  System.map
```

### Simple Build Script
```
Build Mode: Custom Build Commands
Build Commands:
  ./build.sh
  ls -lh build/

Artifact Patterns:
  build/*
  dist/*
```

## API Testing

You can also test via curl:

```bash
# Standard kernel build
curl -X POST http://localhost:8000/api/v1/infrastructure/build-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_repository": "https://github.com/torvalds/linux.git",
    "branch": "master",
    "target_architecture": "x86_64",
    "build_config": {
      "build_mode": "kernel",
      "kernel_config": "defconfig"
    }
  }'

# Custom build
curl -X POST http://localhost:8000/api/v1/infrastructure/build-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_repository": "https://github.com/u-boot/u-boot.git",
    "branch": "master",
    "target_architecture": "arm64",
    "build_config": {
      "build_mode": "custom",
      "build_commands": ["make qemu_arm64_defconfig", "make -j$(nproc)"],
      "artifact_patterns": ["u-boot.bin", "*.dtb"]
    }
  }'
```

## Status Check

### API Server
```bash
# Check if running
ps aux | grep "api.server" | grep -v grep

# Should show: venv/bin/python -m api.server
```

### Dashboard Dev Server
```bash
# Check if running
ps aux | grep vite | grep dashboard | grep -v grep

# Should show: node .../vite
```

### Test the Feature
```bash
# Run automated tests
python3 test_custom_build_commands.py

# All 4 tests should pass:
# ✅ Standard Kernel Build
# ✅ Custom U-Boot Build
# ✅ Custom Build with Patches
# ✅ Simple Custom Script
```

## Troubleshooting

### Build Mode dropdown not visible
1. Hard refresh browser (Ctrl+Shift+R)
2. Check browser console for errors (F12)
3. Verify dev server is running: `ps aux | grep vite`
4. Restart dev server if needed

### API returns 500 error
1. Check API server logs
2. Verify API server is running with latest code
3. Restart API server: `kill <PID> && venv/bin/python -m api.server`

### Build job stays in "queued" status
- This is expected - no actual build servers are registered yet
- The feature is working correctly if the job is created with status "queued"
- To execute builds, you need to register a build server first

## Current Status
✅ Backend implementation complete
✅ Frontend UI complete  
✅ API tests passing (4/4)
✅ Both servers running
✅ Feature ready to use
