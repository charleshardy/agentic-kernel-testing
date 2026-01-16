# Custom Build Commands - Quick Start Guide

## What is it?
Build **any project** (not just Linux kernels) with full control over the build process using custom shell commands.

## When to use it?
- Building U-Boot bootloader
- Building with Yocto/OpenEmbedded
- Building with Buildroot
- Applying custom patches before build
- Running tests after build
- Building custom BSP projects
- Any non-standard build process

## How to use it?

### Via Web GUI

1. **Navigate**: Infrastructure → Build Jobs → Submit Build

2. **Fill Basic Settings**:
   - Repository URL
   - Branch
   - Architecture
   - Build Server (optional)

3. **Select Build Mode**:
   - In "Advanced Settings" section
   - Change "Build Mode" from "Standard Kernel Build" to "Custom Build Commands"

4. **Enter Commands**:
   - **Pre-Build Commands** (optional): Setup, patches, configuration
   - **Build Commands** (required): Main build steps
   - **Post-Build Commands** (optional): Tests, packaging, verification

5. **Configure Artifacts** (optional):
   - Specify glob patterns for files to collect
   - Example: `build/*.bin`, `output/images/*.img`

6. **Submit**: Click OK to start the build

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/infrastructure/build-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "source_repository": "https://github.com/u-boot/u-boot.git",
    "branch": "master",
    "target_architecture": "arm64",
    "build_config": {
      "build_mode": "custom",
      "pre_build_commands": [
        "export CROSS_COMPILE=aarch64-linux-gnu-"
      ],
      "build_commands": [
        "make qemu_arm64_defconfig",
        "make -j$(nproc)"
      ],
      "post_build_commands": [
        "ls -lh u-boot.bin"
      ],
      "artifact_patterns": [
        "u-boot.bin",
        "*.dtb"
      ]
    }
  }'
```

## Examples

### Example 1: U-Boot Build
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
file u-boot.bin

Artifact Patterns:
u-boot.bin
u-boot
*.dtb
```

### Example 2: Kernel with Patches
```
Build Mode: Custom Build Commands

Pre-Build Commands:
curl -O https://example.com/my-patch.patch
git apply my-patch.patch

Build Commands:
make defconfig
make -j$(nproc)
make modules

Post-Build Commands:
./run-tests.sh
ls -lh arch/x86/boot/bzImage

Artifact Patterns:
arch/x86/boot/bzImage
vmlinux
System.map
```

### Example 3: Custom Build Script
```
Build Mode: Custom Build Commands

Build Commands:
./build.sh --target=production --arch=arm64
ls -lh output/

Artifact Patterns:
output/*.img
output/*.tar.gz
```

### Example 4: Buildroot
```
Build Mode: Custom Build Commands

Build Commands:
make raspberrypi4_64_defconfig
make -j$(nproc)

Artifact Patterns:
output/images/*
```

## Tips

### ✅ Do's
- ✅ One command per line
- ✅ Use `$(nproc)` for parallel builds
- ✅ Use pre-build for setup and patches
- ✅ Use post-build for tests and verification
- ✅ Use specific artifact patterns
- ✅ Add comments with `#` for clarity

### ❌ Don'ts
- ❌ Don't use command chaining (`&&`, `||`, `;`)
- ❌ Don't use interactive commands
- ❌ Don't use multi-line commands
- ❌ Don't use overly broad artifact patterns (`*`)
- ❌ Don't put complex logic inline (use scripts)

## Command Syntax

### Valid
```bash
# Comments are supported
make clean
make -j$(nproc)
./build-script.sh --option=value
ls -lh output/
```

### Invalid
```bash
# Don't chain commands
make clean && make -j$(nproc)  # ❌

# Don't use multi-line
if [ -f config ]; then
  make config
fi  # ❌

# Use a script instead
./build-with-logic.sh  # ✅
```

## Troubleshooting

### Build fails immediately
- Check that build commands are valid shell commands
- Verify toolchains are installed on build server
- Check pre-build commands for errors

### No artifacts collected
- Verify artifact patterns match actual output files
- Check build commands actually produce files
- Use post-build commands to list files: `ls -lh output/`

### Commands not running
- Ensure one command per line
- Remove command chaining (`&&`, `;`)
- Check for syntax errors

## Need Help?

### Standard Kernel Build
If you just need a standard kernel build, use "Standard Kernel Build" mode instead:
- Simpler interface
- Automatic configuration
- Optimized for kernel builds

### Documentation
- Full documentation: `CUSTOM_BUILD_COMMANDS_FEATURE.md`
- Advanced settings: `ADVANCED_BUILD_CONFIG_IMPLEMENTATION.md`
- Test examples: `test_custom_build_commands.py`

## Next Steps

After implementing custom build commands:
1. Restart API server to apply changes
2. Test with `python3 test_custom_build_commands.py`
3. Try building your project via Web GUI
4. Monitor build logs for any issues
5. Adjust commands and artifact patterns as needed
