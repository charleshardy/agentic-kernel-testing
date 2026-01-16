# Custom Build - Minimal Guide

## Simplest Possible Build

Only **2 required fields**:

```
1. Build Commands
2. Build Server
```

That's it!

## Quick Example

```
Build Mode: Custom Build Commands (default)

Build Configuration:
  Build Commands:
    cd /path/to/code
    make -j$(nproc)

Build Server Settings:
  Build Server: pek-lpgtest16
```

Click Submit → Done!

## Common Scenarios

### Scenario 1: Build Existing Code on Server
```
Build Commands:
  cd /opt/myproject
  ./build.sh

Build Server: pek-lpgtest16
```

### Scenario 2: Clone and Build
```
Build Commands:
  make defconfig
  make -j$(nproc)

Repository Settings:
  Repository URL: https://github.com/org/project.git
  Branch: main

Build Server: pek-lpgtest16
```

### Scenario 3: Custom Toolchain
```
Build Commands:
  export PATH=/opt/toolchain/bin:$PATH
  ./configure --host=arm-linux
  make

Build Server: pek-lpgtest16

Build Server Settings:
  Environment Variables:
    CC=arm-linux-gcc
    CXX=arm-linux-g++
```

### Scenario 4: Multi-Step Build
```
Pre-Build Commands:
  ./apply-patches.sh
  ./setup-env.sh

Build Commands:
  make clean
  make config
  make -j$(nproc)

Post-Build Commands:
  ./run-tests.sh
  ./package-artifacts.sh

Build Server: pek-lpgtest16
```

## What You DON'T Need

For custom builds, these are **optional**:
- ❌ Architecture (not needed - specify in your commands if needed)
- ❌ Repository URL (not needed if code already on server)
- ❌ Branch (not needed if not cloning)
- ❌ Workspace Root (auto-generated)
- ❌ Environment Variables (only if you need custom env)

## Tips

1. **Keep it Simple**: Start with just Build Commands and Build Server
2. **Add as Needed**: Only add repository/env vars if you actually need them
3. **Use Templates**: Save common configurations as templates
4. **Pre/Post Commands**: Use for setup and cleanup tasks
5. **Environment Variables**: Use for custom toolchains or compiler flags

## Form Layout

```
┌─────────────────────────────────────┐
│ Build Mode: Custom (default)       │
├─────────────────────────────────────┤
│ Build Configuration                 │
│   Build Commands: (required)       │
├─────────────────────────────────────┤
│ Repository Settings (optional)      │
│   Repository URL, Branch, Commit   │
├─────────────────────────────────────┤
│ Build Server Settings               │
│   Build Server: (required)         │
│   Other settings (optional)        │
└─────────────────────────────────────┘
```

## Remember

- **Custom builds are flexible**: Run any commands you want
- **No architecture needed**: Specify toolchain in your commands
- **Repository is optional**: Use existing code on server
- **Build Server is required**: Must choose where to run
- **Only 2 required fields**: Build Commands + Build Server

That's all you need to know!
