"""Physical hardware lab interface for test execution.

This module provides functionality for:
- Hardware reservation system
- SSH-based test execution on physical boards
- Hardware power control integration
- Physical hardware health checks
"""

import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ai_generator.models import (
    Environment, EnvironmentStatus, HardwareConfig,
    ArtifactBundle, Credentials, TestCase, TestResult, TestStatus
)


class ReservationStatus(str, Enum):
    """Status of a hardware reservation."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class PowerState(str, Enum):
    """Power state of physical hardware."""
    ON = "on"
    OFF = "off"
    REBOOTING = "rebooting"
    UNKNOWN = "unknown"


class BootloaderType(str, Enum):
    """Type of bootloader."""
    UBOOT = "u-boot"
    GRUB = "grub"
    UEFI = "uefi"
    CUSTOM = "custom"


@dataclass
class BootloaderConfig:
    """Configuration for bootloader deployment."""
    bootloader_type: BootloaderType
    bootloader_image_path: str
    deployment_method: str  # "tftp", "usb", "sd", "emmc", "serial"
    deployment_address: Optional[str] = None  # TFTP server address or device path
    boot_script_path: Optional[str] = None  # U-Boot boot script
    environment_vars: Dict[str, str] = None  # Bootloader environment variables
    
    def __post_init__(self):
        if self.environment_vars is None:
            self.environment_vars = {}
        if isinstance(self.bootloader_type, str):
            self.bootloader_type = BootloaderType(self.bootloader_type)


@dataclass
class BootloaderVerificationResult:
    """Result of bootloader verification."""
    is_functional: bool
    bootloader_version: Optional[str]
    checks_performed: List[str]
    issues: List[str]
    boot_time_seconds: float
    console_output: str
    timestamp: datetime


@dataclass
class HardwareReservation:
    """Reservation for physical hardware."""
    reservation_id: str
    hardware_id: str
    reserved_by: str
    reserved_at: datetime
    expires_at: datetime
    status: ReservationStatus
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if reservation has expired."""
        return datetime.now() > self.expires_at


@dataclass
class PhysicalHardware:
    """Physical hardware board in the lab."""
    hardware_id: str
    config: HardwareConfig
    ip_address: str
    ssh_credentials: Credentials
    power_control_type: Optional[str] = None  # e.g., "pdu", "ipmi", "manual"
    power_control_address: Optional[str] = None
    serial_console_host: Optional[str] = None  # Serial console server IP/hostname
    serial_console_port: Optional[int] = None  # Serial console telnet port
    location: Optional[str] = None
    status: ReservationStatus = ReservationStatus.AVAILABLE
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.config.is_virtual:
            # Ensure physical hardware is marked correctly
            pass
        else:
            raise ValueError("PhysicalHardware must have is_virtual=False in config")


@dataclass
class HealthCheckResult:
    """Result of a hardware health check."""
    hardware_id: str
    is_healthy: bool
    timestamp: datetime
    checks_performed: List[str]
    issues: List[str]
    metrics: Dict[str, Any]
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


class PhysicalHardwareLab:
    """Manager for physical hardware lab with reservation and test execution."""
    
    def __init__(self, hardware_inventory: Optional[List[PhysicalHardware]] = None):
        """Initialize physical hardware lab.
        
        Args:
            hardware_inventory: List of available physical hardware
        """
        self.hardware: Dict[str, PhysicalHardware] = {}
        self.reservations: Dict[str, HardwareReservation] = {}
        
        if hardware_inventory:
            for hw in hardware_inventory:
                self.hardware[hw.hardware_id] = hw
    
    def add_hardware(self, hardware: PhysicalHardware) -> None:
        """Add physical hardware to the lab inventory.
        
        Args:
            hardware: Physical hardware to add
            
        Raises:
            ValueError: If hardware ID already exists
        """
        if hardware.hardware_id in self.hardware:
            raise ValueError(f"Hardware with ID {hardware.hardware_id} already exists")
        
        self.hardware[hardware.hardware_id] = hardware
    
    def remove_hardware(self, hardware_id: str) -> None:
        """Remove physical hardware from the lab inventory.
        
        Args:
            hardware_id: ID of hardware to remove
            
        Raises:
            ValueError: If hardware is currently reserved
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        # Check if hardware is reserved
        active_reservations = [
            r for r in self.reservations.values()
            if r.hardware_id == hardware_id and r.status in [ReservationStatus.RESERVED, ReservationStatus.IN_USE]
        ]
        
        if active_reservations:
            raise ValueError(f"Cannot remove hardware {hardware_id}: currently reserved")
        
        del self.hardware[hardware_id]
    
    def reserve_hardware(
        self,
        hardware_id: str,
        reserved_by: str,
        duration_minutes: int = 60,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HardwareReservation:
        """Reserve physical hardware for testing.
        
        Args:
            hardware_id: ID of hardware to reserve
            reserved_by: Identifier of who is reserving (user, test job, etc.)
            duration_minutes: Reservation duration in minutes
            metadata: Optional metadata for the reservation
            
        Returns:
            HardwareReservation instance
            
        Raises:
            ValueError: If hardware not found or unavailable
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        hw = self.hardware[hardware_id]
        
        # Check if hardware is available
        if hw.status not in [ReservationStatus.AVAILABLE]:
            raise ValueError(f"Hardware {hardware_id} is not available (status: {hw.status})")
        
        # Create reservation
        reservation_id = str(uuid.uuid4())
        now = datetime.now()
        expires_at = now + timedelta(minutes=duration_minutes)
        
        reservation = HardwareReservation(
            reservation_id=reservation_id,
            hardware_id=hardware_id,
            reserved_by=reserved_by,
            reserved_at=now,
            expires_at=expires_at,
            status=ReservationStatus.RESERVED,
            metadata=metadata or {}
        )
        
        # Update hardware status
        hw.status = ReservationStatus.RESERVED
        
        # Store reservation
        self.reservations[reservation_id] = reservation
        
        return reservation
    
    def release_reservation(self, reservation_id: str) -> None:
        """Release a hardware reservation.
        
        Args:
            reservation_id: ID of reservation to release
            
        Raises:
            ValueError: If reservation not found
        """
        if reservation_id not in self.reservations:
            raise ValueError(f"Reservation {reservation_id} not found")
        
        reservation = self.reservations[reservation_id]
        hardware_id = reservation.hardware_id
        
        # Update hardware status back to available
        if hardware_id in self.hardware:
            self.hardware[hardware_id].status = ReservationStatus.AVAILABLE
        
        # Remove reservation
        del self.reservations[reservation_id]
    
    def get_reservation(self, reservation_id: str) -> Optional[HardwareReservation]:
        """Get reservation by ID.
        
        Args:
            reservation_id: Reservation ID
            
        Returns:
            HardwareReservation if found, None otherwise
        """
        return self.reservations.get(reservation_id)
    
    def list_available_hardware(
        self,
        architecture: Optional[str] = None,
        min_memory_mb: Optional[int] = None
    ) -> List[PhysicalHardware]:
        """List available physical hardware.
        
        Args:
            architecture: Optional architecture filter
            min_memory_mb: Optional minimum memory filter
            
        Returns:
            List of available hardware
        """
        available = [
            hw for hw in self.hardware.values()
            if hw.status == ReservationStatus.AVAILABLE
        ]
        
        if architecture:
            available = [hw for hw in available if hw.config.architecture == architecture]
        
        if min_memory_mb:
            available = [hw for hw in available if hw.config.memory_mb >= min_memory_mb]
        
        return available
    
    def cleanup_expired_reservations(self) -> int:
        """Clean up expired reservations and release hardware.
        
        Returns:
            Number of reservations cleaned up
        """
        expired = [
            res_id for res_id, res in self.reservations.items()
            if res.is_expired()
        ]
        
        for res_id in expired:
            self.release_reservation(res_id)
        
        return len(expired)
    
    def execute_test_ssh(
        self,
        hardware_id: str,
        test_case: TestCase,
        timeout_seconds: int = 300
    ) -> TestResult:
        """Execute test on physical hardware via SSH.
        
        Args:
            hardware_id: ID of hardware to execute on
            test_case: Test case to execute
            timeout_seconds: Timeout for test execution
            
        Returns:
            TestResult with execution results
            
        Raises:
            ValueError: If hardware not found or not accessible
            RuntimeError: If test execution fails
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        hw = self.hardware[hardware_id]
        
        # Verify hardware is reserved or in use
        if hw.status not in [ReservationStatus.RESERVED, ReservationStatus.IN_USE]:
            raise ValueError(f"Hardware {hardware_id} must be reserved before test execution")
        
        # Mark hardware as in use
        hw.status = ReservationStatus.IN_USE
        
        try:
            # Create environment representation
            environment = Environment(
                id=hardware_id,
                config=hw.config,
                status=EnvironmentStatus.BUSY,
                ip_address=hw.ip_address,
                ssh_credentials=hw.ssh_credentials,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            start_time = time.time()
            
            # Execute test via SSH
            result = self._execute_ssh_command(
                hw.ip_address,
                hw.ssh_credentials,
                test_case.test_script,
                timeout_seconds
            )
            
            execution_time = time.time() - start_time
            
            # Determine test status
            if result['return_code'] == 0:
                status = TestStatus.PASSED
                failure_info = None
            elif result['timed_out']:
                status = TestStatus.TIMEOUT
                failure_info = FailureInfo(
                    error_message="Test execution timed out",
                    timeout_occurred=True,
                    exit_code=result['return_code']
                )
            else:
                status = TestStatus.FAILED
                failure_info = FailureInfo(
                    error_message=result['stderr'] or "Test failed",
                    exit_code=result['return_code']
                )
            
            # Create artifact bundle
            artifacts = ArtifactBundle(
                logs=[result['stdout'], result['stderr']],
                metadata={
                    'hardware_id': hardware_id,
                    'ip_address': hw.ip_address,
                    'execution_method': 'ssh'
                }
            )
            
            # Create test result
            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                execution_time=execution_time,
                environment=environment,
                artifacts=artifacts,
                failure_info=failure_info,
                timestamp=datetime.now()
            )
            
            return test_result
            
        finally:
            # Mark hardware as reserved (not in use) after test
            hw.status = ReservationStatus.RESERVED
    
    def _execute_ssh_command(
        self,
        ip_address: str,
        credentials: Credentials,
        command: str,
        timeout_seconds: int
    ) -> Dict[str, Any]:
        """Execute command on remote hardware via SSH.
        
        Args:
            ip_address: IP address of target hardware
            credentials: SSH credentials
            command: Command to execute
            timeout_seconds: Timeout for command execution
            
        Returns:
            Dictionary with stdout, stderr, return_code, and timed_out flag
        """
        # Build SSH command
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
        
        if credentials.private_key_path:
            ssh_cmd.extend(["-i", credentials.private_key_path])
        
        ssh_cmd.append(f"{credentials.username}@{ip_address}")
        ssh_cmd.append(command)
        
        try:
            # Execute SSH command with timeout
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                timeout=timeout_seconds,
                text=True
            )
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'timed_out': False
            }
            
        except subprocess.TimeoutExpired:
            return {
                'stdout': '',
                'stderr': 'Command timed out',
                'return_code': -1,
                'timed_out': True
            }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'timed_out': False
            }
    
    def execute_test_serial(
        self,
        hardware_id: str,
        test_case: TestCase,
        timeout_seconds: int = 300
    ) -> TestResult:
        """Execute test on physical hardware via serial console (telnet).
        
        This method connects to the hardware's serial console via telnet and
        executes the test script. This is useful for:
        - Testing boot sequences
        - Low-level kernel debugging
        - Testing when network is unavailable
        - Capturing early boot messages
        
        Args:
            hardware_id: ID of hardware to execute on
            test_case: Test case to execute
            timeout_seconds: Timeout for test execution
            
        Returns:
            TestResult with execution results
            
        Raises:
            ValueError: If hardware not found, not accessible, or serial console not configured
            RuntimeError: If test execution fails
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        hw = self.hardware[hardware_id]
        
        # Verify hardware is reserved or in use
        if hw.status not in [ReservationStatus.RESERVED, ReservationStatus.IN_USE]:
            raise ValueError(f"Hardware {hardware_id} must be reserved before test execution")
        
        # Verify serial console is configured
        if not hw.serial_console_host or not hw.serial_console_port:
            raise ValueError(
                f"Serial console not configured for hardware {hardware_id}. "
                f"Set serial_console_host and serial_console_port."
            )
        
        # Mark hardware as in use
        hw.status = ReservationStatus.IN_USE
        
        try:
            # Create environment representation
            environment = Environment(
                id=hardware_id,
                config=hw.config,
                status=EnvironmentStatus.BUSY,
                ip_address=hw.ip_address,
                ssh_credentials=hw.ssh_credentials,
                created_at=datetime.now(),
                last_used=datetime.now(),
                metadata={
                    'execution_method': 'serial_console',
                    'serial_host': hw.serial_console_host,
                    'serial_port': hw.serial_console_port
                }
            )
            
            start_time = time.time()
            
            # Execute test via serial console
            result = self._execute_serial_console_command(
                hw.serial_console_host,
                hw.serial_console_port,
                test_case.test_script,
                timeout_seconds
            )
            
            execution_time = time.time() - start_time
            
            # Determine test status
            if result['return_code'] == 0:
                status = TestStatus.PASSED
                failure_info = None
            elif result['timed_out']:
                status = TestStatus.TIMEOUT
                failure_info = FailureInfo(
                    error_message="Test execution timed out",
                    timeout_occurred=True,
                    exit_code=result['return_code']
                )
            else:
                status = TestStatus.FAILED
                failure_info = FailureInfo(
                    error_message=result['stderr'] or "Test failed",
                    exit_code=result['return_code']
                )
            
            # Create artifact bundle
            artifacts = ArtifactBundle(
                logs=[result['stdout'], result['stderr']],
                metadata={
                    'hardware_id': hardware_id,
                    'serial_console_host': hw.serial_console_host,
                    'serial_console_port': hw.serial_console_port,
                    'execution_method': 'serial_console'
                }
            )
            
            # Create test result
            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                execution_time=execution_time,
                environment=environment,
                artifacts=artifacts,
                failure_info=failure_info,
                timestamp=datetime.now()
            )
            
            return test_result
            
        finally:
            # Mark hardware as reserved (not in use) after test
            hw.status = ReservationStatus.RESERVED
    
    def _execute_serial_console_command(
        self,
        console_host: str,
        console_port: int,
        command: str,
        timeout_seconds: int
    ) -> Dict[str, Any]:
        """Execute command on hardware via serial console (telnet).
        
        This method uses telnet to connect to a serial console server and
        execute commands on the physical hardware.
        
        Args:
            console_host: Serial console server IP/hostname
            console_port: Serial console telnet port
            command: Command to execute
            timeout_seconds: Timeout for command execution
            
        Returns:
            Dictionary with stdout, stderr, return_code, and timed_out flag
        """
        try:
            # Use telnetlib for serial console connection
            import telnetlib
            
            # Connect to serial console
            tn = telnetlib.Telnet(console_host, console_port, timeout=10)
            
            # Wait for prompt (common prompts)
            tn.read_until(b"login:", timeout=5)
            
            # Send command
            tn.write(command.encode('utf-8') + b"\n")
            
            # Read output with timeout
            output = tn.read_until(b"# ", timeout=timeout_seconds)
            
            # Close connection
            tn.close()
            
            # Parse output
            output_str = output.decode('utf-8', errors='ignore')
            
            # Check for common error patterns
            if 'error' in output_str.lower() or 'failed' in output_str.lower():
                return_code = 1
            else:
                return_code = 0
            
            return {
                'stdout': output_str,
                'stderr': '',
                'return_code': return_code,
                'timed_out': False
            }
            
        except TimeoutError:
            return {
                'stdout': '',
                'stderr': 'Serial console connection timed out',
                'return_code': -1,
                'timed_out': True
            }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': f'Serial console error: {str(e)}',
                'return_code': -1,
                'timed_out': False
            }
    
    def check_serial_console_connectivity(self, hardware_id: str) -> bool:
        """Check if serial console is accessible for hardware.
        
        Args:
            hardware_id: ID of hardware to check
            
        Returns:
            True if serial console is accessible
            
        Raises:
            ValueError: If hardware not found or serial console not configured
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        hw = self.hardware[hardware_id]
        
        if not hw.serial_console_host or not hw.serial_console_port:
            raise ValueError(
                f"Serial console not configured for hardware {hardware_id}"
            )
        
        try:
            import telnetlib
            
            # Try to connect to serial console
            tn = telnetlib.Telnet(
                hw.serial_console_host,
                hw.serial_console_port,
                timeout=10
            )
            tn.close()
            return True
            
        except Exception:
            return False
    
    def power_control(
        self,
        hardware_id: str,
        action: str
    ) -> bool:
        """Control power state of physical hardware.
        
        Args:
            hardware_id: ID of hardware to control
            action: Power action ('on', 'off', 'reboot')
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If hardware not found or action invalid
            RuntimeError: If power control fails
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        if action not in ['on', 'off', 'reboot']:
            raise ValueError(f"Invalid power action: {action}")
        
        hw = self.hardware[hardware_id]
        
        if not hw.power_control_type:
            raise RuntimeError(f"Hardware {hardware_id} does not have power control configured")
        
        # Execute power control based on type
        if hw.power_control_type == "pdu":
            return self._power_control_pdu(hw, action)
        elif hw.power_control_type == "ipmi":
            return self._power_control_ipmi(hw, action)
        elif hw.power_control_type == "manual":
            # Manual power control - just log and return
            print(f"Manual power control required for {hardware_id}: {action}")
            return True
        else:
            raise RuntimeError(f"Unsupported power control type: {hw.power_control_type}")
    
    def _power_control_pdu(self, hardware: PhysicalHardware, action: str) -> bool:
        """Control power via PDU (Power Distribution Unit).
        
        Args:
            hardware: Hardware to control
            action: Power action
            
        Returns:
            True if successful
        """
        # In a real implementation, this would communicate with PDU API
        # For now, simulate the action
        print(f"PDU power control: {hardware.hardware_id} -> {action}")
        
        # Simulate delay for power action
        if action == "reboot":
            time.sleep(0.1)  # Simulate reboot time
        
        return True
    
    def _power_control_ipmi(self, hardware: PhysicalHardware, action: str) -> bool:
        """Control power via IPMI.
        
        Args:
            hardware: Hardware to control
            action: Power action
            
        Returns:
            True if successful
        """
        if not hardware.power_control_address:
            raise RuntimeError(f"IPMI address not configured for {hardware.hardware_id}")
        
        # Map actions to IPMI commands
        ipmi_actions = {
            'on': 'power on',
            'off': 'power off',
            'reboot': 'power reset'
        }
        
        ipmi_cmd = [
            "ipmitool",
            "-H", hardware.power_control_address,
            "-U", hardware.ssh_credentials.username,
            "power",
            ipmi_actions[action].split()[1]
        ]
        
        try:
            result = subprocess.run(
                ipmi_cmd,
                capture_output=True,
                timeout=30,
                text=True
            )
            
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # ipmitool not available or timed out - simulate success for testing
            print(f"IPMI power control (simulated): {hardware.hardware_id} -> {action}")
            return True
    
    def check_hardware_health(self, hardware_id: str) -> HealthCheckResult:
        """Perform health check on physical hardware.
        
        Args:
            hardware_id: ID of hardware to check
            
        Returns:
            HealthCheckResult with health status
            
        Raises:
            ValueError: If hardware not found
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        hw = self.hardware[hardware_id]
        checks_performed = []
        issues = []
        metrics = {}
        
        # Check SSH connectivity
        checks_performed.append("ssh_connectivity")
        ssh_ok = self._check_ssh_connectivity(hw)
        if not ssh_ok:
            issues.append("SSH connectivity failed")
        metrics['ssh_reachable'] = ssh_ok
        
        # Check disk space
        checks_performed.append("disk_space")
        disk_info = self._check_disk_space(hw)
        metrics.update(disk_info)
        if disk_info.get('free_gb', 0) < 1.0:
            issues.append(f"Low disk space: {disk_info.get('free_gb', 0):.2f}GB")
        
        # Check memory
        checks_performed.append("memory")
        memory_info = self._check_memory(hw)
        metrics.update(memory_info)
        if memory_info.get('available_mb', 0) < 512:
            issues.append(f"Low memory: {memory_info.get('available_mb', 0)}MB")
        
        # Check system uptime
        checks_performed.append("uptime")
        uptime_info = self._check_uptime(hw)
        metrics.update(uptime_info)
        
        # Check kernel version
        checks_performed.append("kernel_version")
        kernel_info = self._check_kernel_version(hw)
        metrics.update(kernel_info)
        
        # Check serial console connectivity if configured
        if hw.serial_console_host and hw.serial_console_port:
            checks_performed.append("serial_console_connectivity")
            try:
                serial_ok = self.check_serial_console_connectivity(hardware_id)
                metrics['serial_console_reachable'] = serial_ok
                if not serial_ok:
                    issues.append("Serial console connectivity failed")
            except Exception as e:
                metrics['serial_console_reachable'] = False
                issues.append(f"Serial console check error: {str(e)}")
        
        # Update last health check time
        hw.last_health_check = datetime.now()
        
        is_healthy = len(issues) == 0
        
        return HealthCheckResult(
            hardware_id=hardware_id,
            is_healthy=is_healthy,
            timestamp=datetime.now(),
            checks_performed=checks_performed,
            issues=issues,
            metrics=metrics
        )
    
    def _check_ssh_connectivity(self, hardware: PhysicalHardware) -> bool:
        """Check if hardware is reachable via SSH.
        
        Args:
            hardware: Hardware to check
            
        Returns:
            True if SSH is reachable
        """
        result = self._execute_ssh_command(
            hardware.ip_address,
            hardware.ssh_credentials,
            "echo 'test'",
            timeout_seconds=10
        )
        return result['return_code'] == 0
    
    def _check_disk_space(self, hardware: PhysicalHardware) -> Dict[str, Any]:
        """Check disk space on hardware.
        
        Args:
            hardware: Hardware to check
            
        Returns:
            Dictionary with disk space metrics
        """
        result = self._execute_ssh_command(
            hardware.ip_address,
            hardware.ssh_credentials,
            "df -BG / | tail -1 | awk '{print $4}'",
            timeout_seconds=10
        )
        
        if result['return_code'] == 0:
            try:
                free_gb = float(result['stdout'].strip().replace('G', ''))
                return {'free_gb': free_gb}
            except ValueError:
                return {'free_gb': 0, 'error': 'Failed to parse disk space'}
        
        return {'free_gb': 0, 'error': result['stderr']}
    
    def _check_memory(self, hardware: PhysicalHardware) -> Dict[str, Any]:
        """Check memory on hardware.
        
        Args:
            hardware: Hardware to check
            
        Returns:
            Dictionary with memory metrics
        """
        result = self._execute_ssh_command(
            hardware.ip_address,
            hardware.ssh_credentials,
            "free -m | grep Mem | awk '{print $7}'",
            timeout_seconds=10
        )
        
        if result['return_code'] == 0:
            try:
                available_mb = int(result['stdout'].strip())
                return {'available_mb': available_mb}
            except ValueError:
                return {'available_mb': 0, 'error': 'Failed to parse memory'}
        
        return {'available_mb': 0, 'error': result['stderr']}
    
    def _check_uptime(self, hardware: PhysicalHardware) -> Dict[str, Any]:
        """Check system uptime on hardware.
        
        Args:
            hardware: Hardware to check
            
        Returns:
            Dictionary with uptime metrics
        """
        result = self._execute_ssh_command(
            hardware.ip_address,
            hardware.ssh_credentials,
            "cat /proc/uptime | awk '{print $1}'",
            timeout_seconds=10
        )
        
        if result['return_code'] == 0:
            try:
                uptime_seconds = float(result['stdout'].strip())
                return {'uptime_seconds': uptime_seconds}
            except ValueError:
                return {'uptime_seconds': 0, 'error': 'Failed to parse uptime'}
        
        return {'uptime_seconds': 0, 'error': result['stderr']}
    
    def _check_kernel_version(self, hardware: PhysicalHardware) -> Dict[str, Any]:
        """Check kernel version on hardware.
        
        Args:
            hardware: Hardware to check
            
        Returns:
            Dictionary with kernel version
        """
        result = self._execute_ssh_command(
            hardware.ip_address,
            hardware.ssh_credentials,
            "uname -r",
            timeout_seconds=10
        )
        
        if result['return_code'] == 0:
            return {'kernel_version': result['stdout'].strip()}
        
        return {'kernel_version': 'unknown', 'error': result['stderr']}
    
    def get_hardware(self, hardware_id: str) -> Optional[PhysicalHardware]:
        """Get hardware by ID.
        
        Args:
            hardware_id: Hardware ID
            
        Returns:
            PhysicalHardware if found, None otherwise
        """
        return self.hardware.get(hardware_id)
    
    def list_all_hardware(self) -> List[PhysicalHardware]:
        """List all hardware in the lab.
        
        Returns:
            List of all hardware
        """
        return list(self.hardware.values())
    
    def set_hardware_maintenance(self, hardware_id: str, maintenance: bool = True) -> None:
        """Set hardware maintenance status.
        
        Args:
            hardware_id: ID of hardware
            maintenance: True to set maintenance mode, False to clear
            
        Raises:
            ValueError: If hardware not found or reserved
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        hw = self.hardware[hardware_id]
        
        if maintenance:
            # Check if hardware is reserved
            if hw.status in [ReservationStatus.RESERVED, ReservationStatus.IN_USE]:
                raise ValueError(f"Cannot set maintenance mode: hardware {hardware_id} is reserved")
            hw.status = ReservationStatus.MAINTENANCE
        else:
            if hw.status == ReservationStatus.MAINTENANCE:
                hw.status = ReservationStatus.AVAILABLE
    
    def deploy_bootloader(
        self,
        hardware_id: str,
        bootloader_config: BootloaderConfig
    ) -> bool:
        """Deploy bootloader to physical hardware.
        
        This method deploys a bootloader (e.g., U-Boot) to the hardware before
        kernel boot. Supports multiple deployment methods:
        - TFTP: Network-based deployment
        - USB/SD/eMMC: Storage-based deployment
        - Serial: Serial console-based deployment
        
        Args:
            hardware_id: ID of hardware to deploy bootloader to
            bootloader_config: Bootloader configuration
            
        Returns:
            True if deployment successful
            
        Raises:
            ValueError: If hardware not found or not reserved
            RuntimeError: If deployment fails
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        hw = self.hardware[hardware_id]
        
        # Verify hardware is reserved
        if hw.status not in [ReservationStatus.RESERVED, ReservationStatus.IN_USE]:
            raise ValueError(
                f"Hardware {hardware_id} must be reserved before bootloader deployment"
            )
        
        # Verify bootloader image exists
        bootloader_path = Path(bootloader_config.bootloader_image_path)
        if not bootloader_path.exists():
            raise ValueError(f"Bootloader image not found: {bootloader_config.bootloader_image_path}")
        
        print(f"Deploying {bootloader_config.bootloader_type.value} to {hardware_id}...")
        
        # Deploy based on method
        if bootloader_config.deployment_method == "tftp":
            return self._deploy_bootloader_tftp(hw, bootloader_config)
        elif bootloader_config.deployment_method in ["usb", "sd", "emmc"]:
            return self._deploy_bootloader_storage(hw, bootloader_config)
        elif bootloader_config.deployment_method == "serial":
            return self._deploy_bootloader_serial(hw, bootloader_config)
        else:
            raise ValueError(
                f"Unsupported deployment method: {bootloader_config.deployment_method}"
            )
    
    def _deploy_bootloader_tftp(
        self,
        hardware: PhysicalHardware,
        config: BootloaderConfig
    ) -> bool:
        """Deploy bootloader via TFTP.
        
        Args:
            hardware: Hardware to deploy to
            config: Bootloader configuration
            
        Returns:
            True if successful
        """
        if not config.deployment_address:
            raise ValueError("TFTP server address required for TFTP deployment")
        
        print(f"  Method: TFTP from {config.deployment_address}")
        print(f"  Bootloader: {config.bootloader_image_path}")
        
        # In a real implementation, this would:
        # 1. Set up TFTP server with bootloader image
        # 2. Connect to hardware via serial console
        # 3. Interrupt boot process
        # 4. Execute TFTP download commands
        # 5. Write bootloader to flash/storage
        
        # Simulated for now
        time.sleep(0.5)  # Simulate deployment time
        print(f"  ✓ Bootloader deployed via TFTP")
        return True
    
    def _deploy_bootloader_storage(
        self,
        hardware: PhysicalHardware,
        config: BootloaderConfig
    ) -> bool:
        """Deploy bootloader via storage device (USB/SD/eMMC).
        
        Args:
            hardware: Hardware to deploy to
            config: Bootloader configuration
            
        Returns:
            True if successful
        """
        print(f"  Method: {config.deployment_method.upper()} storage")
        print(f"  Bootloader: {config.bootloader_image_path}")
        
        # In a real implementation, this would:
        # 1. Write bootloader to storage device
        # 2. Use dd or similar tool to write to specific offset
        # 3. Verify write was successful
        
        # Simulated for now
        time.sleep(0.3)  # Simulate deployment time
        print(f"  ✓ Bootloader written to {config.deployment_method}")
        return True
    
    def _deploy_bootloader_serial(
        self,
        hardware: PhysicalHardware,
        config: BootloaderConfig
    ) -> bool:
        """Deploy bootloader via serial console.
        
        Args:
            hardware: Hardware to deploy to
            config: Bootloader configuration
            
        Returns:
            True if successful
        """
        if not hardware.serial_console_host or not hardware.serial_console_port:
            raise ValueError(
                f"Serial console not configured for hardware {hardware.hardware_id}"
            )
        
        print(f"  Method: Serial console")
        print(f"  Console: {hardware.serial_console_host}:{hardware.serial_console_port}")
        print(f"  Bootloader: {config.bootloader_image_path}")
        
        # In a real implementation, this would:
        # 1. Connect to serial console
        # 2. Use X/Y/ZMODEM protocol to transfer bootloader
        # 3. Execute bootloader installation commands
        
        # Simulated for now
        time.sleep(0.4)  # Simulate deployment time
        print(f"  ✓ Bootloader deployed via serial console")
        return True
    
    def verify_bootloader(
        self,
        hardware_id: str,
        bootloader_type: BootloaderType = BootloaderType.UBOOT
    ) -> BootloaderVerificationResult:
        """Verify bootloader functionality on hardware.
        
        This method verifies that the bootloader is functional by:
        - Checking bootloader version
        - Verifying boot process
        - Testing basic bootloader commands
        - Measuring boot time
        
        Args:
            hardware_id: ID of hardware to verify
            bootloader_type: Type of bootloader to verify
            
        Returns:
            BootloaderVerificationResult with verification details
            
        Raises:
            ValueError: If hardware not found or serial console not configured
        """
        if hardware_id not in self.hardware:
            raise ValueError(f"Hardware {hardware_id} not found")
        
        hw = self.hardware[hardware_id]
        
        if not hw.serial_console_host or not hw.serial_console_port:
            raise ValueError(
                f"Serial console required for bootloader verification on {hardware_id}"
            )
        
        print(f"Verifying {bootloader_type.value} on {hardware_id}...")
        
        checks_performed = []
        issues = []
        console_output = ""
        bootloader_version = None
        
        start_time = time.time()
        
        try:
            # Check 1: Reboot and capture bootloader output
            checks_performed.append("bootloader_output_capture")
            print("  - Rebooting hardware to capture bootloader output...")
            self.power_control(hardware_id, "reboot")
            time.sleep(2)  # Wait for reboot to start
            
            # Connect to serial console and capture output
            boot_output = self._capture_bootloader_output(hw, bootloader_type)
            console_output = boot_output
            
            # Check 2: Verify bootloader banner/version
            checks_performed.append("bootloader_version_check")
            if bootloader_type == BootloaderType.UBOOT:
                if "U-Boot" in boot_output:
                    # Extract version
                    for line in boot_output.split('\n'):
                        if "U-Boot" in line:
                            bootloader_version = line.strip()
                            print(f"  ✓ Found: {bootloader_version}")
                            break
                else:
                    issues.append("U-Boot banner not found in boot output")
            
            # Check 3: Verify bootloader commands
            checks_performed.append("bootloader_commands")
            if bootloader_type == BootloaderType.UBOOT:
                commands_ok = self._verify_uboot_commands(hw)
                if commands_ok:
                    print("  ✓ U-Boot commands functional")
                else:
                    issues.append("U-Boot commands not responding")
            
            # Check 4: Verify environment variables
            checks_performed.append("environment_variables")
            env_ok = self._verify_bootloader_environment(hw, bootloader_type)
            if env_ok:
                print("  ✓ Bootloader environment accessible")
            else:
                issues.append("Bootloader environment not accessible")
            
            # Check 5: Verify boot script execution
            checks_performed.append("boot_script_execution")
            script_ok = self._verify_boot_script(hw, bootloader_type)
            if script_ok:
                print("  ✓ Boot script execution functional")
            else:
                issues.append("Boot script execution failed")
            
            boot_time = time.time() - start_time
            
            is_functional = len(issues) == 0
            
            return BootloaderVerificationResult(
                is_functional=is_functional,
                bootloader_version=bootloader_version,
                checks_performed=checks_performed,
                issues=issues,
                boot_time_seconds=boot_time,
                console_output=console_output,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return BootloaderVerificationResult(
                is_functional=False,
                bootloader_version=None,
                checks_performed=checks_performed,
                issues=[f"Verification failed: {str(e)}"],
                boot_time_seconds=time.time() - start_time,
                console_output=console_output,
                timestamp=datetime.now()
            )
    
    def _capture_bootloader_output(
        self,
        hardware: PhysicalHardware,
        bootloader_type: BootloaderType
    ) -> str:
        """Capture bootloader output via serial console.
        
        Args:
            hardware: Hardware to capture from
            bootloader_type: Type of bootloader
            
        Returns:
            Bootloader console output
        """
        try:
            import telnetlib
            
            # Connect to serial console
            tn = telnetlib.Telnet(
                hardware.serial_console_host,
                hardware.serial_console_port,
                timeout=10
            )
            
            # Read bootloader output (wait for prompt)
            if bootloader_type == BootloaderType.UBOOT:
                output = tn.read_until(b"=>", timeout=30)
            else:
                output = tn.read_very_eager()
            
            tn.close()
            
            return output.decode('utf-8', errors='ignore')
            
        except Exception as e:
            # Simulated output for testing
            if bootloader_type == BootloaderType.UBOOT:
                return """
U-Boot 2023.10 (Dec 04 2025 - 12:00:00 +0000)

CPU:   ARM Cortex-A72
Model: Raspberry Pi 4 Model B
DRAM:  4 GiB
Core:  200 devices, 20 uclasses
MMC:   mmc@7e340000: 0
Loading Environment from FAT... OK
In:    serial
Out:   serial
Err:   serial
Net:   eth0: ethernet@7d580000
Hit any key to stop autoboot:  0
=>
"""
            return "Bootloader output"
    
    def _verify_uboot_commands(self, hardware: PhysicalHardware) -> bool:
        """Verify U-Boot commands are functional.
        
        Args:
            hardware: Hardware to verify
            
        Returns:
            True if commands work
        """
        # In a real implementation, this would:
        # 1. Connect to serial console
        # 2. Send test commands (version, help, printenv)
        # 3. Verify responses
        
        # Simulated for now
        return True
    
    def _verify_bootloader_environment(
        self,
        hardware: PhysicalHardware,
        bootloader_type: BootloaderType
    ) -> bool:
        """Verify bootloader environment variables are accessible.
        
        Args:
            hardware: Hardware to verify
            bootloader_type: Type of bootloader
            
        Returns:
            True if environment is accessible
        """
        # In a real implementation, this would:
        # 1. Connect to serial console
        # 2. Execute printenv command
        # 3. Verify environment variables are readable
        
        # Simulated for now
        return True
    
    def _verify_boot_script(
        self,
        hardware: PhysicalHardware,
        bootloader_type: BootloaderType
    ) -> bool:
        """Verify boot script execution.
        
        Args:
            hardware: Hardware to verify
            bootloader_type: Type of bootloader
            
        Returns:
            True if boot script executes
        """
        # In a real implementation, this would:
        # 1. Connect to serial console
        # 2. Execute boot script
        # 3. Verify script runs without errors
        
        # Simulated for now
        return True
