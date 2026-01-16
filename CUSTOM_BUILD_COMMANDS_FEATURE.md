# Custom Build Commands Feature

## Overview
Added flexible custom build commands support to the Build Job system, allowing users to build any project (not just Linux kernels) with complete control over the build process.

## Features

### 1. Build Mode Selection
Users can now choose between two build modes:
- **Standard Kernel Build**: Traditional kernel build with make defconfig, make, make modules, make dtbs
- **Custom Build Commands**: Full control with custom pre-build, build, and post-build commands

### 2. Custom Command Stages
When using Custom Build mode, users can define commands for three stages:

#### Pre-Build Commands (Optional)
- Run before the main build
- Use cases:
  - Apply patches
  - Download dependencies
  - Configure toolchains
  - Set up environment
  - Run configuration scripts

#### Build Commands (Required)
- Main build commands
- Use cases:
  - Run make with custom targets
  - Execute build scripts
  - Compile with custom compilers
  - Run multi-step builds

#### Post-Build Commands (Optional)
- Run after the main build
- Use cases:
  - Run tests
  - Package artifacts
  - Generate documentation
  - Verify build outputs
  - Create checksums

### 3. Flexible Artifact Collection
- Custom artifact patterns work with both modes
- Support glob patterns for flexible file matching
- Collect any files produced by the build

## Use Cases

### 1. U-Boot Bootloader
```json
{
  "build_mode": "custom",
  "pre_build_commands": [
    "export CROSS_COMPILE=aarch64-linux-gnu-",
    "export ARCH=arm64"
  ],
  "build_commands": [
    "make qemu_arm64_defconfig",
    "make -j$(nproc)"
  ],
  "artifact_patterns": [
    "u-boot.bin",
    "u-boot",
    "*.dtb"
  ]
}
```

### 2. Kernel with Custom Patches
```json
{
  "build_mode": "custom",
  "pre_build_commands": [
    "curl -O https://example.com/my-patch.patch",
    "git apply my-patch.patch"
  ],
  "build_commands": [
    "make defconfig",
    "make -j$(nproc)",
    "make modules"
  ],
  "post_build_commands": [
    "ls -lh arch/x86/boot/bzImage",
    "./run-smoke-tests.sh"
  ]
}
```

### 3. Custom BSP Build Script
```json
{
  "build_mode": "custom",
  "build_commands": [
    "./build-bsp.sh --target=rpi4 --config=production",
    "ls -lh output/"
  ],
  "artifact_patterns": [
    "output/*.img",
    "output/*.tar.gz"
  ]
}
```

### 4. Yocto/OpenEmbedded Build
```json
{
  "build_mode": "custom",
  "pre_build_commands": [
    "source oe-init-build-env",
    "bitbake-layers add-layer ../meta-custom"
  ],
  "build_commands": [
    "bitbake core-image-minimal"
  ],
  "artifact_patterns": [
    "tmp/deploy/images/*/*.wic",
    "tmp/deploy/images/*/*.tar.gz"
  ]
}
```

### 5. Buildroot
```json
{
  "build_mode": "custom",
  "build_commands": [
    "make raspberrypi4_64_defconfig",
    "make -j$(nproc)"
  ],
  "artifact_patterns": [
    "output/images/*"
  ]
}
```

## Implementation Details

### Backend Changes

#### 1. BuildConfig Model (`infrastructure/models/build_server.py`)
Added new fields:
```python
build_mode: str = "kernel"  # "kernel" or "custom"
pre_build_commands: List[str] = field(default_factory=list)
build_commands: List[str] = field(default_factory=list)
post_build_commands: List[str] = field(default_factory=list)
```

#### 2. SSHBuildExecutor (`infrastructure/services/ssh_build_executor.py`)
Added new method:
```python
async def execute_custom_commands(
    commands: List[str],
    source_path: str,
    env: Optional[dict] = None,
    command_type: str = "custom"
) -> AsyncIterator[str]
```

Updated `execute_full_build` to:
- Check `build_mode` field
- Execute custom commands if mode is "custom"
- Fall back to standard kernel build if mode is "kernel"
- Stream logs for all command stages

#### 3. API Endpoint (`api/routers/infrastructure.py`)
Updated `submit_build_job` to:
- Accept `build_mode` parameter
- Accept `pre_build_commands`, `build_commands`, `post_build_commands` arrays
- Pass all fields to BuildConfig

### Frontend Changes

#### 1. Build Mode Selector
Added dropdown to select build mode:
- Standard Kernel Build (default)
- Custom Build Commands

#### 2. Dynamic Build Config Tab
The "Build Config" tab now shows different fields based on selected mode:

**Kernel Mode**:
- Kernel Config
- Extra Make Arguments
- Artifact Patterns

**Custom Mode**:
- Pre-Build Commands (textarea, one command per line)
- Build Commands (textarea, one command per line, required)
- Post-Build Commands (textarea, one command per line)

#### 3. Form Submission Handler
Updated to:
- Split command textareas by newline into arrays
- Filter out empty lines
- Include `build_mode` in payload

## Testing

### Test Script
Created `test_custom_build_commands.py` with 4 test cases:
1. Standard kernel build
2. Custom U-Boot build
3. Custom kernel build with patches
4. Simple custom script build

### Running Tests
```bash
# After restarting API server
python3 test_custom_build_commands.py
```

### Manual Testing via Web GUI
1. Navigate to Infrastructure → Build Jobs
2. Click "Submit Build"
3. Fill in basic settings
4. In Advanced Settings, select "Build Mode"
5. Choose "Custom Build Commands"
6. Enter commands in Pre-Build, Build, and Post-Build fields
7. Submit and verify execution

## Command Execution Details

### Command Environment
- All commands run in the source directory
- Custom environment variables are applied
- Commands run sequentially (not parallel)
- Each command's output is streamed in real-time

### Command Syntax
- One command per line
- Comments supported (lines starting with #)
- Shell variables supported (e.g., `$(nproc)`, `$HOME`)
- Multi-line commands not supported (use scripts instead)

### Error Handling
- If any command fails, the build fails
- Exit codes are captured and logged
- Stderr and stdout are both captured
- Build stops on first error

## Migration Guide

### Existing Builds
- All existing builds continue to work (default mode is "kernel")
- No changes required to existing build configurations
- BuildConfig is backward compatible

### Converting to Custom Mode
To convert an existing kernel build to custom mode:

**Before (Kernel Mode)**:
```json
{
  "kernel_config": "defconfig",
  "extra_make_args": ["ARCH=arm64"]
}
```

**After (Custom Mode)**:
```json
{
  "build_mode": "custom",
  "build_commands": [
    "make defconfig ARCH=arm64",
    "make -j$(nproc) ARCH=arm64"
  ]
}
```

## Best Practices

### 1. Use Pre-Build for Setup
```bash
# Good: Setup in pre-build
pre_build_commands:
  - export CROSS_COMPILE=arm-linux-gnueabihf-
  - ./download-toolchain.sh
  - ./apply-patches.sh

build_commands:
  - make defconfig
  - make -j$(nproc)
```

### 2. Keep Commands Simple
```bash
# Good: Simple, clear commands
build_commands:
  - make clean
  - make -j$(nproc)
  - make install

# Avoid: Complex one-liners
build_commands:
  - make clean && make -j$(nproc) && make install || exit 1
```

### 3. Use Scripts for Complex Logic
```bash
# Good: Use a script
build_commands:
  - ./build-all.sh

# Avoid: Inline complex logic
build_commands:
  - if [ -f config.txt ]; then make config; else make defconfig; fi
```

### 4. Verify Outputs in Post-Build
```bash
post_build_commands:
  - ls -lh build/output.bin
  - file build/output.bin
  - md5sum build/output.bin
  - ./run-tests.sh
```

### 5. Use Artifact Patterns Wisely
```bash
# Good: Specific patterns
artifact_patterns:
  - "build/*.bin"
  - "output/images/*.img"

# Avoid: Too broad
artifact_patterns:
  - "*"  # Collects everything!
```

## Limitations

1. **No Interactive Commands**: Commands must run non-interactively
2. **No Command Chaining**: Use separate lines instead of `&&` or `;`
3. **No Multi-Line Commands**: Use scripts for complex logic
4. **Sequential Execution**: Commands run one at a time (not parallel)
5. **Timeout**: Long-running commands may timeout (default: 2 hours)

## Future Enhancements

Potential future improvements:
1. **Command Templates**: Pre-defined templates for common build systems
2. **Parallel Execution**: Run independent commands in parallel
3. **Conditional Commands**: Skip commands based on conditions
4. **Command Timeout Control**: Per-command timeout settings
5. **Build Caching**: Cache intermediate build artifacts
6. **Local Source Upload**: Upload local source instead of git clone

## Files Modified

### Backend
- `infrastructure/models/build_server.py` - Added build_mode and command fields
- `infrastructure/services/ssh_build_executor.py` - Added custom command execution
- `api/routers/infrastructure.py` - Updated endpoint to handle new fields

### Frontend
- `dashboard/src/components/infrastructure/BuildJobDashboard.tsx` - Added build mode selector and custom commands UI

### Tests
- `test_custom_build_commands.py` - Comprehensive test suite

### Documentation
- `CUSTOM_BUILD_COMMANDS_FEATURE.md` - This document

## Summary

The Custom Build Commands feature provides:
- ✅ Flexibility to build any project, not just kernels
- ✅ Full control over build process with pre/build/post stages
- ✅ Backward compatibility with existing builds
- ✅ Easy-to-use UI with mode selector
- ✅ Comprehensive testing and documentation
- ✅ Support for common use cases (U-Boot, Yocto, Buildroot, custom scripts)

This feature transforms the build system from a kernel-specific tool into a general-purpose build automation platform!
