# Submit Build Form - Quick Reference

## Form Layout

### Basic Settings
```
┌─────────────────────────────────────────────────────┐
│ Load Template: [Dropdown with Custom/Kernel tags]  │
│ Save as Template: [Button]                         │
├─────────────────────────────────────────────────────┤
│ Build Mode: [Custom Build Commands ▼] (default)    │
├─────────────────────────────────────────────────────┤
│ Repository URL (Optional): [________________]       │
│ Branch (Optional): [_______] Commit: [_______]     │
│ Architecture: [x86_64 ▼]                           │
└─────────────────────────────────────────────────────┘
```

### Build Configuration (Custom Mode - Default)
```
┌─────────────────────────────────────────────────────┐
│ Pre-Build Commands (Optional):                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ # Optional setup commands                       │ │
│ │ export CROSS_COMPILE=aarch64-linux-gnu-         │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Build Commands: *Required                          │
│ ┌─────────────────────────────────────────────────┐ │
│ │ # Main build commands (required)                │ │
│ │ make clean                                      │ │
│ │ make defconfig                                  │ │
│ │ make -j$(nproc)                                 │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Post-Build Commands (Optional):                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ # Optional post-build commands                  │ │
│ │ ./run-tests.sh                                  │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Advanced Settings (Optional)
```
┌─────────────────────────────────────────────────────┐
│ Build Server: [Auto (recommended) ▼]               │
│ Workspace Root: [_______] Output Dir: [_______]    │
│ Git Depth: [___] Submodules: [☐] Keep WS: [☐]     │
│ Environment Variables:                              │
│ ┌─────────────────────────────────────────────────┐ │
│ │ {"CC": "gcc-12", "CFLAGS": "-O2"}               │ │
│ │ or                                              │ │
│ │ CC=gcc-12                                       │ │
│ │ CFLAGS=-O2                                      │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Field Requirements

### Custom Build Mode (Default)
| Field | Required | Notes |
|-------|----------|-------|
| Repository URL | ❌ Optional | Only if you need to clone code |
| Branch | ❌ Optional | Only if repository is provided |
| Commit | ❌ Optional | Specific commit hash |
| Architecture | ✅ Required | Target architecture |
| Build Commands | ✅ Required | Main build commands |
| Pre-Build Commands | ❌ Optional | Setup commands |
| Post-Build Commands | ❌ Optional | Cleanup/packaging |

### Kernel Build Mode
| Field | Required | Notes |
|-------|----------|-------|
| Repository URL | ✅ Required | Git repository URL |
| Branch | ✅ Required | Git branch name |
| Commit | ❌ Optional | Specific commit hash |
| Architecture | ✅ Required | Target architecture |
| Kernel Config | ❌ Optional | defconfig or custom |
| Extra Make Args | ❌ Optional | Additional make arguments |
| Artifact Patterns | ❌ Optional | Files to collect |

### Advanced Settings (Both Modes)
| Field | Required | Notes |
|-------|----------|-------|
| Build Server | ❌ Optional | Auto-select if empty |
| Workspace Root | ❌ Optional | Build directory |
| Output Directory | ❌ Optional | Artifact location |
| Git Clone Depth | ❌ Optional | Shallow clone |
| Git Submodules | ❌ Optional | Clone submodules |
| Keep Workspace | ❌ Optional | Don't cleanup |
| Environment Variables | ❌ Optional | Custom env vars |

## Quick Examples

### Minimal Custom Build (3 fields!)
```
Architecture: x86_64
Build Commands:
  cd /existing/code
  make -j$(nproc)
```

### Custom Build with Git
```
Repository URL: https://github.com/u-boot/u-boot.git
Branch: master
Architecture: arm64
Build Commands:
  make qemu_arm64_defconfig
  make -j$(nproc)
```

### Kernel Build
```
Build Mode: Standard Kernel Build
Repository URL: https://github.com/torvalds/linux.git
Branch: master
Architecture: x86_64
Kernel Config: defconfig
```

### Custom Build on Specific Server
```
Architecture: arm64
Build Commands: ./build.sh
Advanced Settings:
  Build Server: pek-lpgtest16
```

## Tips

1. **Use Templates**: Save common configurations as templates
2. **Custom is Default**: No need to switch modes for custom builds
3. **Skip Git**: For custom builds, repository fields are optional
4. **Auto Server**: Leave Build Server empty for automatic selection
5. **Environment Vars**: Use JSON or KEY=VALUE format
6. **Validation**: Form shows clear errors for required fields
