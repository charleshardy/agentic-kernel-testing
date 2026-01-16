# UI Changes Guide

## Build Job Submission Form - Before and After

### BEFORE (Original)
```
┌─────────────────────────────────────────────────────┐
│ Submit Build Job                                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Repository URL: [_____________________________]    │
│                                                     │
│ Branch: [__________]  Commit: [__________]        │
│                                                     │
│ Architecture: [Select ▼]  Build Server: [Select ▼]│
│                                                     │
│                                                     │
│                                    [Cancel] [OK]   │
└─────────────────────────────────────────────────────┘
```

### AFTER (With Advanced Settings + Custom Commands)
```
┌──────────────────────────────────────────────────────────────┐
│ Submit Build Job                                             │
├──────────────────────────────────────────────────────────────┤
│ Basic Settings                                               │
│ ─────────────                                                │
│ Repository URL: [________________________________________]   │
│                                                              │
│ Branch: [__________]  Commit: [__________]                 │
│                                                              │
│ Architecture: [Select ▼]  Build Server: [Select ▼]         │
│                                                              │
│ Advanced Settings                                            │
│ ────────────────                                             │
│ Build Mode: [Standard Kernel Build ▼]                       │
│             └─ Standard Kernel Build                         │
│             └─ Custom Build Commands  ← NEW!                │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ [Build Paths] [Git Options] [Build Config] [Environment]│ │
│ ├────────────────────────────────────────────────────────┤  │
│ │                                                        │  │
│ │ IF Build Mode = "Standard Kernel Build":              │  │
│ │   Kernel Config: [defconfig_____________]             │  │
│ │   Extra Make Args: [ARCH=arm64, CC=gcc___]            │  │
│ │   Artifact Patterns: [                                │  │
│ │     arch/*/boot/Image                                 │  │
│ │     vmlinux                                           │  │
│ │     *.dtb                                             │  │
│ │   ]                                                   │  │
│ │                                                        │  │
│ │ IF Build Mode = "Custom Build Commands":  ← NEW!      │  │
│ │   Pre-Build Commands: [                               │  │
│ │     # Optional setup commands                         │  │
│ │     export CROSS_COMPILE=aarch64-linux-gnu-           │  │
│ │     ./apply-patches.sh                                │  │
│ │   ]                                                   │  │
│ │   Build Commands: [                                   │  │
│ │     # Main build commands (required)                  │  │
│ │     make qemu_arm64_defconfig                         │  │
│ │     make -j$(nproc)                                   │  │
│ │   ]                                                   │  │
│ │   Post-Build Commands: [                              │  │
│ │     # Optional post-build commands                    │  │
│ │     ls -lh u-boot.bin                                 │  │
│ │     ./run-tests.sh                                    │  │
│ │   ]                                                   │  │
│ │                                                        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│                                          [Cancel] [OK]      │
└──────────────────────────────────────────────────────────────┘
```

## UI Flow

### Standard Kernel Build Mode
```
1. User selects "Standard Kernel Build"
   ↓
2. Build Config tab shows:
   - Kernel Config field
   - Extra Make Arguments field
   - Artifact Patterns textarea
   ↓
3. User fills in kernel-specific settings
   ↓
4. System executes:
   - make <kernel_config>
   - make <extra_args>
   - make modules
   - make dtbs
```

### Custom Build Commands Mode
```
1. User selects "Custom Build Commands"
   ↓
2. Build Config tab shows:
   - Pre-Build Commands textarea
   - Build Commands textarea (required)
   - Post-Build Commands textarea
   ↓
3. User enters custom shell commands
   ↓
4. System executes:
   - Pre-build commands (if any)
   - Build commands (required)
   - Post-build commands (if any)
```

## Tab Layout

### Build Paths Tab
```
┌────────────────────────────────────────┐
│ Workspace Root                         │
│ [/tmp/builds___________________]       │
│ Root directory for builds              │
│                                        │
│ Output Directory                       │
│ [Auto-generated if not specified___]   │
│ Where to place build artifacts         │
│                                        │
│ ☐ Keep Workspace                       │
│   Keep workspace after build completes │
└────────────────────────────────────────┘
```

### Git Options Tab
```
┌────────────────────────────────────────┐
│ Clone Depth                            │
│ [1_____]                               │
│ Shallow clone depth (1 = latest only)  │
│                                        │
│ ☐ Clone Submodules                     │
│   Clone git submodules                 │
└────────────────────────────────────────┘
```

### Build Config Tab (Kernel Mode)
```
┌────────────────────────────────────────┐
│ Kernel Config                          │
│ [defconfig_____________________]       │
│ defconfig name or path to config file  │
│                                        │
│ Extra Make Arguments                   │
│ [ARCH=arm64, CROSS_COMPILE=...___]     │
│ Comma-separated make arguments         │
│                                        │
│ Artifact Patterns                      │
│ [                                      │
│   arch/*/boot/Image                    │
│   vmlinux                              │
│   *.dtb                                │
│ ]                                      │
│ One pattern per line (glob patterns)   │
└────────────────────────────────────────┘
```

### Build Config Tab (Custom Mode) ← NEW!
```
┌────────────────────────────────────────┐
│ Pre-Build Commands                     │
│ [                                      │
│   # Optional commands before build     │
│   export CROSS_COMPILE=aarch64-...     │
│   ./apply-patches.sh                   │
│ ]                                      │
│ Commands to run before build           │
│                                        │
│ Build Commands                         │
│ [                                      │
│   # Main build commands (required)     │
│   make qemu_arm64_defconfig            │
│   make -j$(nproc)                      │
│ ]                                      │
│ Main build commands                    │
│                                        │
│ Post-Build Commands                    │
│ [                                      │
│   # Optional commands after build      │
│   ls -lh u-boot.bin                    │
│   ./run-tests.sh                       │
│ ]                                      │
│ Commands to run after build            │
└────────────────────────────────────────┘
```

### Environment Tab
```
┌────────────────────────────────────────┐
│ Custom Environment Variables           │
│ [                                      │
│   {"CC": "gcc-12", "CFLAGS": "-O2"}    │
│   or                                   │
│   CC=gcc-12                            │
│   CFLAGS=-O2                           │
│ ]                                      │
│ JSON object or KEY=VALUE pairs         │
└────────────────────────────────────────┘
```

## User Interaction Examples

### Example 1: Simple Kernel Build
```
User Action:
1. Fill Repository URL: https://github.com/torvalds/linux.git
2. Fill Branch: master
3. Select Architecture: x86_64
4. Keep default "Standard Kernel Build" mode
5. Click OK

Result:
- Standard kernel build with defconfig
- Collects standard kernel artifacts
```

### Example 2: U-Boot Build
```
User Action:
1. Fill Repository URL: https://github.com/u-boot/u-boot.git
2. Fill Branch: master
3. Select Architecture: arm64
4. Change Build Mode to "Custom Build Commands"
5. In Build Config tab, enter:
   Pre-Build Commands:
     export CROSS_COMPILE=aarch64-linux-gnu-
   Build Commands:
     make qemu_arm64_defconfig
     make -j$(nproc)
6. In Build Paths tab, set Artifact Patterns:
     u-boot.bin
     *.dtb
7. Click OK

Result:
- Clones U-Boot repository
- Sets cross-compiler
- Configures for QEMU ARM64
- Builds U-Boot
- Collects u-boot.bin and device trees
```

### Example 3: Kernel with Patches
```
User Action:
1. Fill Repository URL: https://github.com/torvalds/linux.git
2. Fill Branch: master
3. Select Architecture: x86_64
4. Change Build Mode to "Custom Build Commands"
5. In Build Config tab, enter:
   Pre-Build Commands:
     curl -O https://example.com/my-patch.patch
     git apply my-patch.patch
   Build Commands:
     make defconfig
     make -j$(nproc)
   Post-Build Commands:
     ./run-tests.sh
     ls -lh arch/x86/boot/bzImage
6. Click OK

Result:
- Clones kernel
- Downloads and applies patch
- Builds kernel
- Runs tests
- Lists build output
- Collects artifacts
```

## Visual Indicators

### Build Mode Selector
```
┌─────────────────────────────────────┐
│ Build Mode: [Standard Kernel Build ▼]│
│                                     │
│ When clicked:                       │
│ ┌─────────────────────────────────┐ │
│ │ ● Standard Kernel Build         │ │
│ │   Custom Build Commands         │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Dynamic Tab Content
```
Build Config Tab Changes Based on Mode:

Mode: Standard Kernel Build
┌─────────────────────────────┐
│ [Kernel Config Field]       │
│ [Extra Make Args Field]     │
│ [Artifact Patterns Field]   │
└─────────────────────────────┘

Mode: Custom Build Commands
┌─────────────────────────────┐
│ [Pre-Build Commands Field]  │
│ [Build Commands Field]      │
│ [Post-Build Commands Field] │
└─────────────────────────────┘
```

## Tooltips

Helpful tooltips appear on hover:

- **Build Mode**: "Choose between standard kernel build or custom commands"
- **Pre-Build Commands**: "Commands to run before build (one per line)"
- **Build Commands**: "Main build commands (one per line, required for custom mode)"
- **Post-Build Commands**: "Commands to run after build (one per line)"
- **Workspace Root**: "Root directory for builds on the build server"
- **Git Depth**: "Shallow clone depth (1 = latest commit only)"
- **Artifact Patterns**: "One pattern per line (glob patterns)"

## Responsive Design

The modal width is increased to 800px to accommodate the new fields comfortably:
- Before: 600px (default)
- After: 800px (more space for textareas)

## Accessibility

All form fields include:
- Clear labels
- Helpful tooltips
- Placeholder text with examples
- Validation (required fields marked)
- Error messages (if validation fails)

## Summary

The UI changes provide:
- ✅ Clear mode selection
- ✅ Dynamic form fields
- ✅ Organized tabs
- ✅ Helpful tooltips
- ✅ Example placeholders
- ✅ Intuitive workflow
- ✅ Professional appearance
