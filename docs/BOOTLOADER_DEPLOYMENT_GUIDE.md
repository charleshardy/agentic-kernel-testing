# Bootloader Deployment and Verification Guide

## Overview

The Physical Hardware Lab Interface provides comprehensive support for deploying and verifying bootloaders (e.g., U-Boot, GRUB) on physical hardware boards before kernel boot. This enables automated bootloader testing and validation as part of the BSP testing workflow.

## Supported Bootloaders

- **U-Boot** - Primary support with full verification
- **GRUB** - Extensible support
- **UEFI** - Extensible support
- **Custom** - Support for custom bootloaders

## Deployment Methods

### 1. TFTP Deployment

Network-based deployment using TFTP server.

**Use Cases:**
- Development environments with network boot
- Rapid bootloader updates during development
- Centralized bootloader management

**Requirements:**
- TFTP server accessible from hardware
- Serial console access for boot interruption
- Network connectivity during boot

**Example:**
```python
from execution.physical_hardware_lab import BootloaderConfig, BootloaderType

bootloader_config = BootloaderConfig(
    bootloader_type=BootloaderType.UBOOT,
    bootloader_image_path="/path/to/u-boot.bin",
    deployment_method="tftp",
    deployment_address="192.168.1.50",  # TFTP server IP
    environment_vars={
        "serverip": "192.168.1.50",
        "ipaddr": "192.168.1.100",
        "bootfile": "u-boot.bin"
    }
)

lab.deploy_bootloader("rpi-001", bootloader_config)
```

### 2. Storage Deployment (USB/SD/eMMC)

Direct write to storage device.

**Use Cases:**
- Production bootloader installation
- Offline deployment
- Storage device preparation

**Requirements:**
- Access to storage device
- Appropriate write permissions
- Storage device path/identifier

**Example:**
```python
bootloader_config = BootloaderConfig(
    bootloader_type=BootloaderType.UBOOT,
    bootloader_image_path="/path/to/u-boot.bin",
    deployment_method="sd",  # or "usb", "emmc"
    deployment_address="/dev/mmcblk0",  # Storage device
    boot_script_path="/path/to/boot.scr"
)

lab.deploy_bootloader("beaglebone-001", bootloader_config)
```

### 3. Serial Console Deployment

Deployment via serial console using file transfer protocols.

**Use Cases:**
- Embedded systems without network
- Recovery scenarios
- Minimal hardware setups

**Requirements:**
- Serial console access
- X/Y/ZMODEM protocol support
- Serial console server

**Example:**
```python
bootloader_config = BootloaderConfig(
    bootloader_type=BootloaderType.UBOOT,
    bootloader_image_path="/path/to/u-boot.bin",
    deployment_method="serial",
    environment_vars={
        "bootcmd": "run distro_bootcmd",
        "bootdelay": "2"
    }
)

lab.deploy_bootloader("embedded-001", bootloader_config)
```

## Bootloader Verification

### Overview

Bootloader verification ensures the bootloader is functional before proceeding with kernel testing. The verification process includes:

1. **Version Check** - Verify bootloader version and banner
2. **Command Test** - Test basic bootloader commands
3. **Environment Check** - Verify environment variables are accessible
4. **Boot Script Test** - Verify boot script execution
5. **Boot Time Measurement** - Measure bootloader boot time

### Basic Verification

```python
from execution.physical_hardware_lab import BootloaderType

# Verify U-Boot
result = lab.verify_bootloader("rpi-001", BootloaderType.UBOOT)

# Check results
if result.is_functional:
    print(f"✓ Bootloader functional: {result.bootloader_version}")
    print(f"  Boot time: {result.boot_time_seconds:.2f}s")
else:
    print(f"✗ Bootloader issues found:")
    for issue in result.issues:
        print(f"  - {issue}")
```

### Verification Result

The `BootloaderVerificationResult` contains:

```python
@dataclass
class BootloaderVerificationResult:
    is_functional: bool              # Overall functional status
    bootloader_version: str          # Detected version
    checks_performed: List[str]      # List of checks performed
    issues: List[str]                # List of issues found
    boot_time_seconds: float         # Boot time measurement
    console_output: str              # Full console output
    timestamp: datetime              # Verification timestamp
```

## Complete Workflow Example

### 1. Deploy and Verify U-Boot

```python
from execution.physical_hardware_lab import (
    PhysicalHardwareLab,
    PhysicalHardware,
    BootloaderConfig,
    BootloaderType
)
from ai_generator.models import HardwareConfig, Credentials

# Create hardware
config = HardwareConfig(
    architecture="arm64",
    cpu_model="ARM Cortex-A72",
    memory_mb=4096,
    storage_type="sd",
    is_virtual=False
)

hardware = PhysicalHardware(
    hardware_id="rpi-001",
    config=config,
    ip_address="192.168.1.100",
    ssh_credentials=Credentials(username="pi"),
    serial_console_host="console-server.lab",
    serial_console_port=7001,
    power_control_type="pdu"
)

lab = PhysicalHardwareLab(hardware_inventory=[hardware])

# Reserve hardware
reservation = lab.reserve_hardware("rpi-001", "bootloader-test")

# Deploy bootloader
bootloader_config = BootloaderConfig(
    bootloader_type=BootloaderType.UBOOT,
    bootloader_image_path="/path/to/u-boot.bin",
    deployment_method="tftp",
    deployment_address="192.168.1.50"
)

success = lab.deploy_bootloader("rpi-001", bootloader_config)

# Verify bootloader
if success:
    result = lab.verify_bootloader("rpi-001", BootloaderType.UBOOT)
    
    print(f"Functional: {result.is_functional}")
    print(f"Version: {result.bootloader_version}")
    print(f"Boot Time: {result.boot_time_seconds:.2f}s")
    
    for check in result.checks_performed:
        print(f"  ✓ {check}")
    
    if result.issues:
        for issue in result.issues:
            print(f"  ⚠ {issue}")

# Release hardware
lab.release_reservation(reservation.reservation_id)
```

## U-Boot Specific Features

### Environment Variables

Configure U-Boot environment variables during deployment:

```python
bootloader_config = BootloaderConfig(
    bootloader_type=BootloaderType.UBOOT,
    bootloader_image_path="/path/to/u-boot.bin",
    deployment_method="sd",
    environment_vars={
        "bootdelay": "3",
        "baudrate": "115200",
        "console": "ttyS0,115200n8",
        "bootcmd": "run distro_bootcmd",
        "serverip": "192.168.1.50",
        "ipaddr": "192.168.1.100"
    }
)
```

### Boot Script

Specify custom boot script:

```python
bootloader_config = BootloaderConfig(
    bootloader_type=BootloaderType.UBOOT,
    bootloader_image_path="/path/to/u-boot.bin",
    deployment_method="sd",
    boot_script_path="/path/to/boot.scr"
)
```

### Verification Checks

U-Boot verification includes:

1. **Banner Detection** - Looks for "U-Boot" in boot output
2. **Version Extraction** - Extracts version from banner
3. **Command Test** - Tests `version`, `help`, `printenv` commands
4. **Environment Access** - Verifies environment variables are readable
5. **Boot Script** - Verifies boot script execution

## Integration with Testing Workflow

### Pre-Kernel Testing

Deploy and verify bootloader before kernel tests:

```python
# 1. Reserve hardware
reservation = lab.reserve_hardware("rpi-001", "kernel-test")

# 2. Deploy bootloader
bootloader_config = BootloaderConfig(
    bootloader_type=BootloaderType.UBOOT,
    bootloader_image_path="/path/to/u-boot.bin",
    deployment_method="tftp",
    deployment_address="192.168.1.50"
)
lab.deploy_bootloader("rpi-001", bootloader_config)

# 3. Verify bootloader
result = lab.verify_bootloader("rpi-001", BootloaderType.UBOOT)
if not result.is_functional:
    raise RuntimeError("Bootloader verification failed")

# 4. Deploy kernel
lab.deploy_kernel("rpi-001", kernel_image)

# 5. Run kernel tests
test_result = lab.execute_test_ssh("rpi-001", test_case)

# 6. Release hardware
lab.release_reservation(reservation.reservation_id)
```

### Bootloader-Specific Tests

Create tests specifically for bootloader functionality:

```python
from ai_generator.models import TestCase, TestType

# Test bootloader commands
bootloader_test = TestCase(
    id="test-uboot-commands",
    name="U-Boot Command Test",
    description="Test U-Boot basic commands",
    test_type=TestType.INTEGRATION,
    target_subsystem="bootloader",
    test_script="version; help; printenv"
)

# Execute via serial console
result = lab.execute_test_serial("rpi-001", bootloader_test)
```

## Best Practices

### 1. Always Verify After Deployment

```python
# Good: Verify after deployment
success = lab.deploy_bootloader("rpi-001", config)
if success:
    result = lab.verify_bootloader("rpi-001", BootloaderType.UBOOT)
    if not result.is_functional:
        # Handle verification failure
        pass
```

### 2. Use Serial Console for Verification

Bootloader verification requires serial console access:

```python
# Ensure serial console is configured
hardware = PhysicalHardware(
    hardware_id="rpi-001",
    config=config,
    ip_address="192.168.1.100",
    ssh_credentials=credentials,
    serial_console_host="console-server.lab",  # Required
    serial_console_port=7001  # Required
)
```

### 3. Measure Boot Time

Use boot time measurements to detect performance issues:

```python
result = lab.verify_bootloader("rpi-001", BootloaderType.UBOOT)

if result.boot_time_seconds > 10.0:
    print(f"⚠ Slow boot time: {result.boot_time_seconds:.2f}s")
```

### 4. Save Console Output

Save console output for debugging:

```python
result = lab.verify_bootloader("rpi-001", BootloaderType.UBOOT)

# Save to file
with open("bootloader_output.log", "w") as f:
    f.write(result.console_output)
```

## Troubleshooting

### Deployment Fails

**Issue:** Bootloader deployment fails

**Solutions:**
1. Verify bootloader image path exists
2. Check deployment method is supported
3. Verify hardware is reserved
4. Check network connectivity (for TFTP)
5. Verify storage device path (for storage deployment)

### Verification Fails

**Issue:** Bootloader verification reports issues

**Solutions:**
1. Check serial console connectivity
2. Verify bootloader was deployed correctly
3. Check power control is working
4. Review console output for errors
5. Verify bootloader version is compatible

### Serial Console Not Responding

**Issue:** Cannot capture bootloader output

**Solutions:**
1. Verify serial console configuration
2. Check baud rate settings
3. Test serial console connectivity
4. Verify hardware is powered on
5. Check serial console server is running

## API Reference

### BootloaderConfig

```python
@dataclass
class BootloaderConfig:
    bootloader_type: BootloaderType
    bootloader_image_path: str
    deployment_method: str  # "tftp", "usb", "sd", "emmc", "serial"
    deployment_address: Optional[str] = None
    boot_script_path: Optional[str] = None
    environment_vars: Dict[str, str] = None
```

### BootloaderType

```python
class BootloaderType(str, Enum):
    UBOOT = "u-boot"
    GRUB = "grub"
    UEFI = "uefi"
    CUSTOM = "custom"
```

### Methods

#### deploy_bootloader()

```python
def deploy_bootloader(
    self,
    hardware_id: str,
    bootloader_config: BootloaderConfig
) -> bool
```

Deploy bootloader to physical hardware.

#### verify_bootloader()

```python
def verify_bootloader(
    self,
    hardware_id: str,
    bootloader_type: BootloaderType = BootloaderType.UBOOT
) -> BootloaderVerificationResult
```

Verify bootloader functionality on hardware.

## Examples

See `examples/bootloader_deployment_example.py` for complete working examples.

## Future Enhancements

Potential improvements:
1. Support for more bootloader types (GRUB, UEFI)
2. Automated boot script generation
3. Bootloader configuration backup/restore
4. Multi-stage bootloader support
5. Bootloader update verification
6. Performance benchmarking
7. Automated recovery procedures

## Support

For issues or questions:
1. Check bootloader image is valid
2. Verify serial console configuration
3. Review console output logs
4. Test deployment method manually
5. Consult bootloader documentation
