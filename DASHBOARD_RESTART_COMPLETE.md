# Dashboard Restarted - Custom Build Commands Now Visible

## What Was Done
The dashboard dev server has been restarted to pick up the React component changes for the Custom Build Commands feature.

## Current Status
✅ API Server: Running (port 8000)
✅ Dashboard Dev Server: Running (port 3000) - **FRESHLY RESTARTED**
✅ Backend: Custom Build Commands implemented
✅ Frontend: Custom Build Commands UI implemented
✅ Tests: All passing (4/4)

## How to Access the Feature

### Step-by-Step Instructions

1. **Open your browser** to: `http://localhost:3000/`

2. **Navigate to Build Jobs**:
   - Click on **Infrastructure** in the left sidebar
   - Click on **Build Jobs**

3. **Open Submit Build Modal**:
   - Click the **Submit Build** button (blue button with + icon)

4. **Fill Basic Settings**:
   - Repository URL: `https://github.com/torvalds/linux.git`
   - Branch: `master`
   - Architecture: Select `x86_64`

5. **Scroll Down to Advanced Settings**:
   - You should now see **"Advanced Settings"** section
   - The **first field** should be **"Build Mode"** dropdown

6. **Select Build Mode**:
   - Click the **Build Mode** dropdown
   - You'll see two options:
     - **Standard Kernel Build** (default)
     - **Custom Build Commands** ← Select this

7. **Navigate to Build Config Tab**:
   - Below the Build Mode dropdown, you'll see **4 tabs**:
     - Build Paths
     - Git Options
     - **Build Config** ← Click this tab
     - Environment

8. **Enter Custom Build Commands**:
   When you click the "Build Config" tab, you'll see different fields based on your Build Mode selection:

   **If "Custom Build Commands" is selected**, you'll see:
   - **Pre-Build Commands** (textarea) - Optional setup commands
   - **Build Commands** (textarea) - Main build commands (required)
   - **Post-Build Commands** (textarea) - Optional cleanup commands

   **If "Standard Kernel Build" is selected**, you'll see:
   - **Kernel Config** (input) - defconfig name
   - **Extra Make Arguments** (input) - Comma-separated
   - **Artifact Patterns** (textarea) - One per line

## Example: Custom U-Boot Build

1. Select **Build Mode**: `Custom Build Commands`
2. Go to **Build Config** tab
3. Enter in **Pre-Build Commands**:
   ```
   export CROSS_COMPILE=aarch64-linux-gnu-
   export ARCH=arm64
   ```
4. Enter in **Build Commands**:
   ```
   make qemu_arm64_defconfig
   make -j$(nproc)
   ```
5. Enter in **Post-Build Commands**:
   ```
   ls -lh u-boot.bin
   file u-boot.bin
   ```
6. Go to **Build Config** tab and add artifact patterns:
   ```
   u-boot.bin
   u-boot
   *.dtb
   ```

## Visual Guide

```
Submit Build Modal
├── Basic Settings
│   ├── Repository URL
│   ├── Branch / Commit
│   └── Architecture / Build Server
│
└── Advanced Settings ← SCROLL HERE
    ├── Build Mode ← DROPDOWN (Standard Kernel Build / Custom Build Commands)
    │
    └── Tabs:
        ├── Build Paths
        ├── Git Options
        ├── Build Config ← CLICK HERE TO SEE CUSTOM COMMANDS
        │   └── (Content changes based on Build Mode selection)
        └── Environment
```

## Troubleshooting

### Still Don't See Build Mode Dropdown?
1. **Hard refresh** your browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. **Clear browser cache** and reload
3. **Check browser console** (F12) for any JavaScript errors
4. Verify you're on `http://localhost:3000/` (not 3001 or another port)

### Build Config Tab Shows Wrong Fields?
- Make sure you've selected "Custom Build Commands" from the Build Mode dropdown
- The tab content is dynamic and changes based on your selection
- Try switching between modes to see the fields change

### Dev Server Not Responding?
```bash
# Check if dev server is running
ps aux | grep vite | grep dashboard

# If not running, start it:
cd dashboard && npm run dev
```

## What's Different Now?

**Before Restart:**
- Browser was showing old compiled JavaScript
- Build Mode dropdown was not visible
- Build Config tab didn't exist

**After Restart:**
- Fresh compilation of React components
- Build Mode dropdown is now visible in Advanced Settings
- Build Config tab shows dynamic content based on mode selection
- All custom build command fields are accessible

## Next Steps

1. Open `http://localhost:3000/` in your browser
2. Navigate to Infrastructure → Build Jobs → Submit Build
3. Scroll to Advanced Settings
4. You should now see the Build Mode dropdown
5. Select "Custom Build Commands" and go to Build Config tab
6. Enter your custom build commands

The feature is now fully accessible in the Web GUI!
