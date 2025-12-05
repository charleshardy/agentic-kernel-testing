#!/usr/bin/env python3
"""Example: Bootloader Deployment and Verification

This script demonstrates how to deploy and verify bootloaders (e.g., U-Boot)
on physical hardware boards before kernel boot.
"""

import sys
sys.path.insert(0, '.')

from execution.physical_hardware_lab import (
    PhysicalHardwareLab,
    PhysicalHardware,
    BootloaderConfig,
    BootloaderType
)
from ai_generator.models import HardwareConfig, Credentials


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def example_uboot_deployment_tftp():
    """Example: Deploy U-Boot via TFTP."""
    print_section("Example 1: Deploy U-Boot via TFTP")
    
    # Create hardware configuration
    config = HardwareConfig(
        architecture="arm64",
        cpu_model="ARM Cortex-A72",
        memory_mb=4096,
        storage_type="sd",
        is_virtual=False
    )
    
    # Create physical hardware with serial console
    hardware = PhysicalHardware(
        hardware_id="rpi-001",
        config=config,
        ip_address="192.168.1.100",
        ssh_credentials=Credentials(username="pi", password="raspberry"),
        serial_console_host="console-server.lab",
        serial_console_port=7001,
        power_control_type="pdu",
        power_control_address="192.168.1.10"
    )
    
    # Create lab
    lab = PhysicalHardwareLab(hardware_inventory=[hardware])
    
    # Reserve hardware
    print("\n1. Reserving hardware...")
    reservation = lab.reserve_hardware("rpi-001", "bootloader-deployment")
    print(f"   ✓ Reserved: {reservation.reservation_id}")
    
    # Create bootloader configuration for TFTP deployment
    print("\n2. Configuring U-Boot deployment via TFTP...")
    bootloader_config = BootloaderConfig(
        bootloader_type=BootloaderType.UBOOT,
        bootloader_image_path="/path/to/u-boot.bin",
        deployment_method="tftp",
        deployment_address="192.168.1.50",  # TFTP server
        environment_vars={
            "serverip": "192.168.1.50",
            "ipaddr": "192.168.1.100",
            "bootfile": "u-boot.bin"
        }
    )
    
    # Note: Create placeholder file for demonstration
    from pathlib import Path
    Path("/tmp/u-boot.bin").touch()
    bootloader_config.bootloader_image_path = "/tmp/u-boot.bin"
    
    # Deploy bootloader
    print("\n3. Deploying U-Boot...")
    success = lab.deploy_bootloader("rpi-001", bootloader_config)
    if success:
        print("   ✓ U-Boot deployed successfully")
    
    # Verify bootloader
    print("\n4. Verifying U-Boot functionality...")
    result = lab.verify_bootloader("rpi-001", BootloaderType.UBOOT)
    
    print(f"\n5. Verification Results:")
    print(f"   Functional: {result.is_functional}")
    print(f"   Version: {result.bootloader_version}")
    print(f"   Boot Time: {result.boot_time_seconds:.2f}s")
    print(f"   Checks Performed: {len(result.checks_performed)}")
    for check in result.checks_performed:
        print(f"     - {check}")
    
    if result.issues:
        print(f"   Issues Found: {len(result.issues)}")
        for issue in result.issues:
            print(f"     ⚠ {issue}")
    
    # Release hardware
    print("\n6. Releasing hardware...")
    lab.release_reservation(reservation.reservation_id)
    print("   ✓ Released")
    
    # Cleanup
    Path("/tmp/u-boot.bin").unlink(missing_ok=True)


def example_uboot_deployment_sd():
    """Example: Deploy U-Boot to SD card."""
    print_section("Example 2: Deploy U-Boot to SD Card")
    
    # Create hardware
    config = HardwareConfig(
        architecture="arm64",
        cpu_model="ARM Cortex-A72",
        memory_mb=2048,
        storage_type="sd",
        is_virtual=False
    )
    
    hardware = PhysicalHardware(
        hardware_id="beaglebone-001",
        config=config,
        ip_address="192.168.1.101",
        ssh_credentials=Credentials(username="debian"),
        serial_console_host="console-server.lab",
        serial_console_port=7002
    )
    
    lab = PhysicalHardwareLab(hardware_inventory=[hardware])
    
    # Reserve hardware
    print("\n1. Reserving hardware...")
    reservation = lab.reserve_hardware("beaglebone-001", "bootloader-deployment")
    print(f"   ✓ Reserved: {reservation.reservation_id}")
    
    # Create bootloader configuration for SD card deployment
    print("\n2. Configuring U-Boot deployment to SD card...")
    
    # Create placeholder file
    from pathlib import Path
    Path("/tmp/u-boot-beaglebone.bin").touch()
    
    bootloader_config = BootloaderConfig(
        bootloader_type=BootloaderType.UBOOT,
        bootloader_image_path="/tmp/u-boot-beaglebone.bin",
        deployment_method="sd",
        deployment_address="/dev/mmcblk0",  # SD card device
        boot_script_path="/path/to/boot.scr",
        environment_vars={
            "bootdelay": "3",
            "baudrate": "115200",
            "console": "ttyS0,115200n8"
        }
    )
    
    # Deploy bootloader
    print("\n3. Deploying U-Boot to SD card...")
    success = lab.deploy_bootloader("beaglebone-001", bootloader_config)
    if success:
        print("   ✓ U-Boot written to SD card")
    
    # Verify bootloader
    print("\n4. Verifying U-Boot functionality...")
    result = lab.verify_bootloader("beaglebone-001", BootloaderType.UBOOT)
    
    print(f"\n5. Verification Results:")
    print(f"   Functional: {'✓ Yes' if result.is_functional else '✗ No'}")
    if result.bootloader_version:
        print(f"   Version: {result.bootloader_version}")
    print(f"   Boot Time: {result.boot_time_seconds:.2f}s")
    
    # Release hardware
    print("\n6. Releasing hardware...")
    lab.release_reservation(reservation.reservation_id)
    print("   ✓ Released")
    
    # Cleanup
    Path("/tmp/u-boot-beaglebone.bin").unlink(missing_ok=True)


def example_uboot_deployment_serial():
    """Example: Deploy U-Boot via serial console."""
    print_section("Example 3: Deploy U-Boot via Serial Console")
    
    # Create hardware
    config = HardwareConfig(
        architecture="arm",
        cpu_model="ARM Cortex-A8",
        memory_mb=512,
        storage_type="emmc",
        is_virtual=False
    )
    
    hardware = PhysicalHardware(
        hardware_id="embedded-001",
        config=config,
        ip_address="192.168.1.102",
        ssh_credentials=Credentials(username="root"),
        serial_console_host="console-server.lab",
        serial_console_port=7003,
        power_control_type="manual"
    )
    
    lab = PhysicalHardwareLab(hardware_inventory=[hardware])
    
    # Reserve hardware
    print("\n1. Reserving hardware...")
    reservation = lab.reserve_hardware("embedded-001", "bootloader-deployment")
    print(f"   ✓ Reserved: {reservation.reservation_id}")
    
    # Create bootloader configuration for serial deployment
    print("\n2. Configuring U-Boot deployment via serial console...")
    
    # Create placeholder file
    from pathlib import Path
    Path("/tmp/u-boot-embedded.bin").touch()
    
    bootloader_config = BootloaderConfig(
        bootloader_type=BootloaderType.UBOOT,
        bootloader_image_path="/tmp/u-boot-embedded.bin",
        deployment_method="serial",
        environment_vars={
            "bootcmd": "run distro_bootcmd",
            "bootdelay": "2"
        }
    )
    
    # Deploy bootloader
    print("\n3. Deploying U-Boot via serial console...")
    print("   Note: This uses X/Y/ZMODEM protocol over serial")
    success = lab.deploy_bootloader("embedded-001", bootloader_config)
    if success:
        print("   ✓ U-Boot deployed via serial console")
    
    # Verify bootloader
    print("\n4. Verifying U-Boot functionality...")
    result = lab.verify_bootloader("embedded-001", BootloaderType.UBOOT)
    
    print(f"\n5. Verification Results:")
    print(f"   Functional: {'✓ Yes' if result.is_functional else '✗ No'}")
    if result.bootloader_version:
        print(f"   Version: {result.bootloader_version}")
    print(f"   Checks: {', '.join(result.checks_performed)}")
    
    # Release hardware
    print("\n6. Releasing hardware...")
    lab.release_reservation(reservation.reservation_id)
    print("   ✓ Released")
    
    # Cleanup
    Path("/tmp/u-boot-embedded.bin").unlink(missing_ok=True)


def example_bootloader_verification_workflow():
    """Example: Complete bootloader verification workflow."""
    print_section("Example 4: Complete Bootloader Verification Workflow")
    
    # Create hardware
    config = HardwareConfig(
        architecture="arm64",
        cpu_model="ARM Cortex-A53",
        memory_mb=1024,
        storage_type="emmc",
        is_virtual=False
    )
    
    hardware = PhysicalHardware(
        hardware_id="odroid-001",
        config=config,
        ip_address="192.168.1.103",
        ssh_credentials=Credentials(username="odroid"),
        serial_console_host="console-server.lab",
        serial_console_port=7004,
        power_control_type="pdu",
        power_control_address="192.168.1.10"
    )
    
    lab = PhysicalHardwareLab(hardware_inventory=[hardware])
    
    print("\n1. Reserve hardware")
    reservation = lab.reserve_hardware("odroid-001", "bootloader-workflow")
    print(f"   ✓ Reserved: {reservation.reservation_id}")
    
    print("\n2. Deploy U-Boot")
    from pathlib import Path
    Path("/tmp/u-boot-odroid.bin").touch()
    
    bootloader_config = BootloaderConfig(
        bootloader_type=BootloaderType.UBOOT,
        bootloader_image_path="/tmp/u-boot-odroid.bin",
        deployment_method="emmc",
        deployment_address="/dev/mmcblk0boot0"
    )
    
    success = lab.deploy_bootloader("odroid-001", bootloader_config)
    print(f"   ✓ Deployed: {success}")
    
    print("\n3. Verify bootloader functionality")
    result = lab.verify_bootloader("odroid-001", BootloaderType.UBOOT)
    
    print(f"\n4. Detailed Verification Report:")
    print(f"   Status: {'✓ PASS' if result.is_functional else '✗ FAIL'}")
    print(f"   Bootloader: {result.bootloader_version or 'Unknown'}")
    print(f"   Boot Time: {result.boot_time_seconds:.2f} seconds")
    print(f"   Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n   Checks Performed ({len(result.checks_performed)}):")
    for i, check in enumerate(result.checks_performed, 1):
        print(f"     {i}. {check.replace('_', ' ').title()}")
    
    if result.issues:
        print(f"\n   Issues Found ({len(result.issues)}):")
        for i, issue in enumerate(result.issues, 1):
            print(f"     {i}. {issue}")
    else:
        print(f"\n   ✓ No issues found - bootloader is fully functional")
    
    print(f"\n   Console Output Preview:")
    output_lines = result.console_output.strip().split('\n')[:5]
    for line in output_lines:
        print(f"     {line}")
    if len(result.console_output.split('\n')) > 5:
        print(f"     ... ({len(result.console_output.split('\n')) - 5} more lines)")
    
    print("\n5. Release hardware")
    lab.release_reservation(reservation.reservation_id)
    print("   ✓ Released")
    
    # Cleanup
    Path("/tmp/u-boot-odroid.bin").unlink(missing_ok=True)


def main():
    """Run all bootloader deployment examples."""
    print("\n" + "="*70)
    print("  Bootloader Deployment and Verification Examples")
    print("="*70)
    
    try:
        # Example 1: TFTP deployment
        example_uboot_deployment_tftp()
        
        # Example 2: SD card deployment
        example_uboot_deployment_sd()
        
        # Example 3: Serial console deployment
        example_uboot_deployment_serial()
        
        # Example 4: Complete verification workflow
        example_bootloader_verification_workflow()
        
        # Summary
        print_section("Summary")
        print("\n✅ All bootloader deployment examples completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  1. ✓ TFTP-based bootloader deployment")
        print("  2. ✓ Storage-based deployment (SD/eMMC)")
        print("  3. ✓ Serial console-based deployment")
        print("  4. ✓ Bootloader verification (version, commands, environment)")
        print("  5. ✓ Boot time measurement")
        print("  6. ✓ Comprehensive verification reporting")
        
        print("\nSupported Bootloaders:")
        print("  - U-Boot (primary support)")
        print("  - GRUB (extensible)")
        print("  - UEFI (extensible)")
        print("  - Custom bootloaders (extensible)")
        
        print("\nDeployment Methods:")
        print("  - TFTP: Network-based deployment")
        print("  - USB/SD/eMMC: Storage-based deployment")
        print("  - Serial: Console-based deployment with X/Y/ZMODEM")
        
        print("\n" + "="*70)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
