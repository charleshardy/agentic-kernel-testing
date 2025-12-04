# Physical Hardware Lab Interface Guide

## Overview

The Physical Hardware Lab Interface provides comprehensive management and testing capabilities for physical hardware boards in the Agentic AI Testing System. This guide covers setup, usage, and best practices.

## Quick Start

### 1. Define Hardware Configuration

```python
from ai_generator.models import HardwareConfig, Credentials, Peripheral
from execution.physical_hardware_lab import PhysicalHardware, PhysicalHardwareLab

# Create hardware configuration
config = HardwareConfig(
    architecture="arm64",
    cpu_model="ARM Cortex-A72",
    memory_mb=4096,
    storage_type="emmc",
    peripherals=[
        Peripheral(name="eth0", type="network", model="bcm-genet"),
        Peripheral(name="uart0", type="serial", model="pl011")
    ],
    is_virtual=False,  # Must be False for physical hardware
    emulator=None
)

# Create SSH credentials
credentials = Credentials(
    username="pi",
    password="raspberry",
    private_key_path="/path/to/key.pem"  # Optional
)
```

### 2. Register Physical Hardware

```python
# Create physical hardware instance with SSH and serial console
hardware = PhysicalHardware(
    hardware_id="rpi-001",
    config=config,
    ip_address="192.168.1.100",
    ssh_credentials=credentials,
    power_control_type="pdu",  # or "ipmi", "manual"
    power_control_address="192.168.1.10",
    serial_console_host="console-server.lab",  # Serial console server
    serial_console_port=7001,  # Telnet port for this board
    location="Lab Rack 1, Slot 3"
)

# Create lab and add hardware
lab = PhysicalHardwareLab()
lab.add_hardware(hardware)
```

### 3. Reserve and Use Hardware

```python
# Reserve hardware
reservation = lab.reserve_hardware(
    hardware_id="rpi-001",
    reserved_by="test-job-12345",
    duration_minutes=60,
    metadata={"priority": "high", "job_id": "12345"}
)

# Execute test
from ai_generator.models import TestCase, TestType

test_case = TestCase(
    id="test-001",
    name="Kernel Boot Test",
    description="Test kernel boot sequence",
    test_type=TestType.INTEGRATION,
    target_subsystem="kernel/boot",
    test_script="#!/bin/bash\n./run_test.sh"
)

result = lab.execute_test_ssh("rpi-001", test_case, timeout_seconds=300)

# Release hardware
lab.release_reservation(reservation.reservation_id)
```

## Hardware Reservation System

### Reserving Hardware

```python
# Basic reservation
reservation = lab.reserve_hardware("rpi-001", "user@example.com")

# Reservation with custom duration
reservation = lab.reserve_hardware(
    "rpi-001",
    "test-job-456",
    duration_minutes=120
)

# Reservation with metadata
reservation = lab.reserve_hardware(
    "rpi-001",
    "ci-pipeline",
    duration_minutes=30,
    metadata={
        "job_id": "456",
        "priority": "high",
        "branch": "feature/new-driver"
    }
)
```

### Managing Reservations

```python
# Get reservation details
reservation = lab.get_reservation(reservation_id)
print(f"Reserved by: {reservation.reserved_by}")
print(f"Expires at: {reservation.expires_at}")

# Release reservation
lab.release_reservation(reservation_id)

# Clean up expired reservations
cleaned_count = lab.cleanup_expired_reservations()
print(f"Cleaned up {cleaned_count} expired reservations")
```

### Listing Available Hardware

```python
# List all available hardware
available = lab.list_available_hardware()

# Filter by architecture
arm_hardware = lab.list_available_hardware(architecture="arm64")
x86_hardware = lab.list_available_hardware(architecture="x86_64")

# Filter by minimum memory
high_mem = lab.list_available_hardware(min_memory_mb=8192)

# Combined filters
available = lab.list_available_hardware(
    architecture="arm64",
    min_memory_mb=4096
)
```

## Test Execution Methods

The Physical Hardware Lab supports two methods for test execution:
1. **SSH-based execution** - For normal testing when network is available
2. **Serial console execution** - For early boot testing, kernel debugging, and when network is unavailable

## SSH-Based Test Execution

### Basic Test Execution

```python
# Reserve hardware first
reservation = lab.reserve_hardware("rpi-001", "test-runner")

# Create test case
test_case = TestCase(
    id="test-001",
    name="Memory Test",
    description="Test memory subsystem",
    test_type=TestType.UNIT,
    target_subsystem="mm",
    test_script="#!/bin/bash\nmemtester 1G 1"
)

# Execute test
result = lab.execute_test_ssh("rpi-001", test_case)

# Check result
if result.status == TestStatus.PASSED:
    print("Test passed!")
else:
    print(f"Test failed: {result.failure_info.error_message}")

# Release hardware
lab.release_reservation(reservation.reservation_id)
```

### Handling Test Results

```python
# Execute test
result = lab.execute_test_ssh("rpi-001", test_case, timeout_seconds=600)

# Access result details
print(f"Status: {result.status.value}")
print(f"Execution time: {result.execution_time:.2f}s")
print(f"Environment: {result.environment.id}")

# Access artifacts
for log in result.artifacts.logs:
    print(f"Log: {log}")

# Handle failures
if result.failure_info:
    print(f"Error: {result.failure_info.error_message}")
    print(f"Exit code: {result.failure_info.exit_code}")
    if result.failure_info.timeout_occurred:
        print("Test timed out")
```

## Serial Console Test Execution

### Overview

Serial console execution uses telnet to connect to a serial console server and execute tests directly on the hardware's serial port. This is particularly useful for:

- **Early boot testing** - Capture boot messages before network is available
- **Kernel panic debugging** - See kernel panics and stack traces
- **Low-level debugging** - Access hardware when network fails
- **Boot sequence validation** - Test bootloader and kernel initialization

### Configuring Serial Console

```python
# Configure hardware with serial console access
hardware = PhysicalHardware(
    hardware_id="rpi-001",
    config=config,
    ip_address="192.168.1.100",
    ssh_credentials=credentials,
    serial_console_host="console-server.lab",  # Console server IP/hostname
    serial_console_port=7001  # Telnet port for this board
)
```

### Basic Serial Console Test Execution

```python
# Reserve hardware first
reservation = lab.reserve_hardware("rpi-001", "test-runner")

# Create test case for early boot
test_case = TestCase(
    id="test-boot-001",
    name="Early Boot Test",
    description="Test early boot sequence",
    test_type=TestType.INTEGRATION,
    target_subsystem="kernel/boot",
    test_script="dmesg | head -20"  # Get early boot messages
)

# Execute test via serial console
result = lab.execute_test_serial("rpi-001", test_case)

# Check result
if result.status == TestStatus.PASSED:
    print("Boot test passed!")
    print(f"Boot messages: {result.artifacts.logs[0]}")

# Release hardware
lab.release_reservation(reservation.reservation_id)
```

### Serial Console Use Cases

#### 1. Boot Sequence Testing

```python
# Test kernel boot
boot_test = TestCase(
    id="test-boot-sequence",
    name="Kernel Boot Sequence",
    description="Validate kernel boots successfully",
    test_type=TestType.INTEGRATION,
    target_subsystem="kernel/boot",
    test_script="dmesg | grep 'Linux version'"
)

result = lab.execute_test_serial("rpi-001", boot_test)
```

#### 2. Kernel Panic Debugging

```python
# Test that triggers kernel panic (for debugging)
panic_test = TestCase(
    id="test-panic-handling",
    name="Kernel Panic Test",
    description="Test kernel panic handling",
    test_type=TestType.INTEGRATION,
    target_subsystem="kernel/panic",
    test_script="echo c > /proc/sysrq-trigger"  # Trigger crash
)

result = lab.execute_test_serial("rpi-001", panic_test, timeout_seconds=120)
# Serial console will capture the panic output
```

#### 3. Bootloader Testing

```python
# Test bootloader configuration
bootloader_test = TestCase(
    id="test-bootloader",
    name="Bootloader Test",
    description="Test bootloader configuration",
    test_type=TestType.INTEGRATION,
    target_subsystem="boot/loader",
    test_script="cat /proc/cmdline"  # Check kernel command line
)

result = lab.execute_test_serial("rpi-001", bootloader_test)
```

### Checking Serial Console Connectivity

```python
# Check if serial console is accessible
is_reachable = lab.check_serial_console_connectivity("rpi-001")

if is_reachable:
    print("Serial console is accessible")
else:
    print("Serial console connection failed")
    print("Check:")
    print("  - Console server is running")
    print("  - Port is correct")
    print("  - Network connectivity to console server")
```

### Serial Console vs SSH Execution

| Feature | SSH Execution | Serial Console Execution |
|---------|--------------|-------------------------|
| **Network Required** | Yes | No (uses serial port) |
| **Early Boot Access** | No | Yes |
| **Kernel Panic Capture** | Limited | Full capture |
| **Performance** | Fast | Slower (serial bandwidth) |
| **Use Case** | Normal testing | Boot/debug testing |
| **Setup Complexity** | Simple | Requires console server |

### Serial Console Best Practices

1. **Use for Early Boot Testing**
   ```python
   # Good: Use serial console for boot tests
   result = lab.execute_test_serial("rpi-001", boot_test)
   
   # Better: Use SSH for normal tests
   result = lab.execute_test_ssh("rpi-001", normal_test)
   ```

2. **Set Appropriate Timeouts**
   ```python
   # Boot tests may take longer
   result = lab.execute_test_serial(
       "rpi-001",
       boot_test,
       timeout_seconds=300  # 5 minutes for boot
   )
   ```

3. **Combine with Power Control**
   ```python
   # Reboot and capture boot sequence
   lab.power_control("rpi-001", "reboot")
   time.sleep(5)  # Wait for reboot to start
   result = lab.execute_test_serial("rpi-001", boot_test)
   ```

## Power Control

### PDU Power Control

```python
# Configure hardware with PDU
hardware = PhysicalHardware(
    hardware_id="rpi-001",
    config=config,
    ip_address="192.168.1.100",
    ssh_credentials=credentials,
    power_control_type="pdu",
    power_control_address="192.168.1.10"  # PDU IP address
)

# Power operations
lab.power_control("rpi-001", "on")
lab.power_control("rpi-001", "off")
lab.power_control("rpi-001", "reboot")
```

### IPMI Power Control

```python
# Configure hardware with IPMI
hardware = PhysicalHardware(
    hardware_id="server-001",
    config=config,
    ip_address="192.168.1.101",
    ssh_credentials=credentials,
    power_control_type="ipmi",
    power_control_address="192.168.1.50"  # BMC IP address
)

# Power operations (requires ipmitool)
lab.power_control("server-001", "on")
lab.power_control("server-001", "off")
lab.power_control("server-001", "reboot")
```

### Manual Power Control

```python
# Configure hardware with manual power control
hardware = PhysicalHardware(
    hardware_id="custom-board",
    config=config,
    ip_address="192.168.1.102",
    ssh_credentials=credentials,
    power_control_type="manual"
)

# Power operations (logs message for operator)
lab.power_control("custom-board", "reboot")
# Output: "Manual power control required for custom-board: reboot"
```

## Health Checks

### Performing Health Checks

```python
# Check hardware health
health = lab.check_hardware_health("rpi-001")

# Check health status
if health.is_healthy:
    print("Hardware is healthy")
else:
    print("Hardware has issues:")
    for issue in health.issues:
        print(f"  - {issue}")

# Access metrics
print(f"SSH reachable: {health.metrics['ssh_reachable']}")
print(f"Free disk space: {health.metrics['free_gb']}GB")
print(f"Available memory: {health.metrics['available_mb']}MB")
print(f"Uptime: {health.metrics['uptime_seconds']}s")
print(f"Kernel version: {health.metrics['kernel_version']}")
```

### Automated Health Monitoring

```python
# Check all hardware health
for hw_id in lab.hardware.keys():
    health = lab.check_hardware_health(hw_id)
    if not health.is_healthy:
        print(f"⚠️  {hw_id} has issues:")
        for issue in health.issues:
            print(f"    - {issue}")
        
        # Set to maintenance if critical
        if any("connectivity" in issue.lower() for issue in health.issues):
            lab.set_hardware_maintenance(hw_id, maintenance=True)
            print(f"    → Set to maintenance mode")
```

## Maintenance Mode

### Setting Maintenance Mode

```python
# Set hardware to maintenance
lab.set_hardware_maintenance("rpi-001", maintenance=True)

# Hardware is now unavailable for reservation
available = lab.list_available_hardware()
# rpi-001 will not appear in available list

# Clear maintenance mode
lab.set_hardware_maintenance("rpi-001", maintenance=False)
```

### Maintenance Workflow

```python
# Perform maintenance
hw_id = "rpi-001"

# 1. Check if hardware is reserved
hw = lab.get_hardware(hw_id)
if hw.status in [ReservationStatus.RESERVED, ReservationStatus.IN_USE]:
    print("Cannot set maintenance: hardware is in use")
else:
    # 2. Set maintenance mode
    lab.set_hardware_maintenance(hw_id, maintenance=True)
    
    # 3. Perform maintenance tasks
    print("Performing maintenance...")
    # ... maintenance operations ...
    
    # 4. Verify health
    health = lab.check_hardware_health(hw_id)
    if health.is_healthy:
        # 5. Clear maintenance mode
        lab.set_hardware_maintenance(hw_id, maintenance=False)
        print("Hardware back in service")
```

## Hardware Inventory Management

### Adding Hardware

```python
# Create new hardware
new_hardware = PhysicalHardware(
    hardware_id="rpi-002",
    config=config,
    ip_address="192.168.1.103",
    ssh_credentials=credentials,
    location="Lab Rack 1, Slot 4"
)

# Add to lab
lab.add_hardware(new_hardware)
```

### Removing Hardware

```python
# Remove hardware (must not be reserved)
lab.remove_hardware("rpi-002")
```

### Listing Hardware

```python
# List all hardware
all_hardware = lab.list_all_hardware()
for hw in all_hardware:
    print(f"{hw.hardware_id}: {hw.config.architecture}, "
          f"Status: {hw.status.value}")

# Get specific hardware
hw = lab.get_hardware("rpi-001")
print(f"Location: {hw.location}")
print(f"IP: {hw.ip_address}")
```

## Best Practices

### 1. Always Reserve Before Use

```python
# ✅ Good: Reserve before use
reservation = lab.reserve_hardware("rpi-001", "test-job")
result = lab.execute_test_ssh("rpi-001", test_case)
lab.release_reservation(reservation.reservation_id)

# ❌ Bad: Execute without reservation
result = lab.execute_test_ssh("rpi-001", test_case)  # Will fail
```

### 2. Use Context Managers (Future Enhancement)

```python
# Future pattern with context manager
with lab.reserve("rpi-001", "test-job") as hw_id:
    result = lab.execute_test_ssh(hw_id, test_case)
    # Automatic release on exit
```

### 3. Handle Timeouts Appropriately

```python
# Set realistic timeouts
result = lab.execute_test_ssh(
    "rpi-001",
    test_case,
    timeout_seconds=600  # 10 minutes for long tests
)

if result.status == TestStatus.TIMEOUT:
    print("Test timed out - may need longer timeout")
```

### 4. Regular Health Checks

```python
# Schedule regular health checks
import schedule

def check_all_hardware():
    for hw_id in lab.hardware.keys():
        health = lab.check_hardware_health(hw_id)
        if not health.is_healthy:
            # Alert or take action
            pass

schedule.every(1).hour.do(check_all_hardware)
```

### 5. Clean Up Expired Reservations

```python
# Periodically clean up
import schedule

schedule.every(5).minutes.do(lab.cleanup_expired_reservations)
```

## Troubleshooting

### SSH Connection Issues

```python
# Check SSH connectivity
health = lab.check_hardware_health("rpi-001")
if not health.metrics.get('ssh_reachable'):
    print("SSH connection failed")
    print("Check:")
    print("  - IP address is correct")
    print("  - SSH service is running")
    print("  - Credentials are valid")
    print("  - Network connectivity")
```

### Power Control Issues

```python
# Verify power control configuration
hw = lab.get_hardware("rpi-001")
if not hw.power_control_type:
    print("Power control not configured")
elif hw.power_control_type == "ipmi":
    if not hw.power_control_address:
        print("IPMI address not configured")
```

### Reservation Conflicts

```python
# Check hardware status before reserving
hw = lab.get_hardware("rpi-001")
if hw.status != ReservationStatus.AVAILABLE:
    print(f"Hardware not available: {hw.status.value}")
    
    # Find alternative
    available = lab.list_available_hardware(
        architecture=hw.config.architecture
    )
    if available:
        print(f"Alternative: {available[0].hardware_id}")
```

## Integration Examples

### With Test Orchestrator

```python
# Orchestrator requests hardware
def allocate_hardware_for_test(test_case):
    # Find suitable hardware
    available = lab.list_available_hardware(
        architecture=test_case.required_hardware.architecture,
        min_memory_mb=test_case.required_hardware.memory_mb
    )
    
    if not available:
        return None
    
    # Reserve hardware
    hw_id = available[0].hardware_id
    reservation = lab.reserve_hardware(hw_id, f"test-{test_case.id}")
    
    return hw_id, reservation
```

### With CI/CD Pipeline

```python
# CI/CD integration
def run_hardware_tests(commit_sha):
    # Reserve hardware
    reservation = lab.reserve_hardware("rpi-001", f"ci-{commit_sha}")
    
    try:
        # Run tests
        results = []
        for test_case in test_suite:
            result = lab.execute_test_ssh("rpi-001", test_case)
            results.append(result)
        
        # Report results
        return all(r.status == TestStatus.PASSED for r in results)
    
    finally:
        # Always release
        lab.release_reservation(reservation.reservation_id)
```

## API Reference

See `execution/physical_hardware_lab.py` for complete API documentation.

### Key Classes

- `PhysicalHardwareLab` - Main lab management class
- `PhysicalHardware` - Physical hardware representation
- `HardwareReservation` - Reservation tracking
- `HealthCheckResult` - Health check results

### Key Enums

- `ReservationStatus` - Hardware status (AVAILABLE, RESERVED, IN_USE, MAINTENANCE, OFFLINE)
- `PowerState` - Power state (ON, OFF, REBOOTING, UNKNOWN)

## Support

For issues or questions:
1. Check hardware health status
2. Verify SSH connectivity
3. Review power control configuration
4. Check reservation status
5. Consult implementation documentation
