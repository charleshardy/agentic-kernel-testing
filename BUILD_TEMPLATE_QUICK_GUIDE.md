# Build Template Quick Guide

## What are Build Templates?

Build templates let you save your build configurations (custom commands, environment variables, build settings) and reuse them later. No more re-typing complex build commands!

## How to Use

### Save a Template

1. Go to **Infrastructure → Build Jobs**
2. Click **Submit Build** button
3. Fill out your build configuration:
   - Select Build Mode (Kernel or Custom)
   - Enter your commands, environment variables, etc.
4. Click **Save as Template** button (top right of form)
5. Enter a name and description
6. Click **OK**

Your template is now saved!

### Load a Template

1. Go to **Infrastructure → Build Jobs**
2. Click **Submit Build** button
3. Select your template from the **Load Template** dropdown
4. All settings are automatically filled in!
5. Just add Repository URL and Branch
6. Click **OK** to submit

## Example Templates

### U-Boot Build
```
Name: U-Boot QEMU ARM64
Build Mode: Custom Build Commands

Pre-Build Commands:
export CROSS_COMPILE=aarch64-linux-gnu-
export ARCH=arm64

Build Commands:
make clean
make qemu_arm64_defconfig
make -j$(nproc)

Post-Build Commands:
ls -lh u-boot.bin
```

### Kernel Build
```
Name: ARM64 Kernel
Build Mode: Standard Kernel Build

Kernel Config: defconfig
Extra Make Args: ARCH=arm64, CROSS_COMPILE=aarch64-linux-gnu-
Artifact Patterns:
arch/arm64/boot/Image
vmlinux
*.dtb

Git Depth: 1
```

### Custom Script Build
```
Name: Custom Build Script
Build Mode: Custom Build Commands

Build Commands:
./configure --enable-optimizations
make -j$(nproc)
make test
make install DESTDIR=/tmp/install

Environment Variables:
{
  "CC": "gcc-12",
  "CXX": "g++-12",
  "CFLAGS": "-O3 -march=native"
}
```

## Tips

- **Descriptive Names**: Use clear names like "U-Boot ARM64" instead of "Template 1"
- **Add Descriptions**: Help your future self remember what each template does
- **Test First**: Test your build configuration before saving as a template
- **Update Templates**: You can update templates via the API if needed
- **Multiple Templates**: Save different templates for different projects

## Where Templates are Stored

Templates are saved in:
```
infrastructure_state/build_templates/templates.json
```

They persist across server restarts.
