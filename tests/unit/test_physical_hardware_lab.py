"""Unit tests for physical hardware lab interface."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import subprocess

from execution.physical_hardware_lab import (
    PhysicalHardwareLab,
    PhysicalHardware,
    HardwareReservation,
    ReservationStatus,
    PowerState,
    HealthCheckResult
)
from ai_generator.models import (
    HardwareConfig,
    Credentials,
    TestCase,
    TestType,
    TestStatus,
    ExpectedOutcome
)


@pytest.fixture
def sample_hardware_config():
    """Create a sample physical hardware configuration."""
    return HardwareConfig(
        architecture="arm64",
        cpu_model="ARM Cortex-A72",
        memory_mb=4096,
        storage_type="emmc",
        is_virtual=False,
        emulator=None
    )


@pytest.fixture
def sample_credentials():
    """Create sample SSH credentials."""
    return Credentials(
        username="testuser",
        password="testpass",
        private_key_path="/path/to/key"
    )


@pytest.fixture
def sample_physical_hardware(sample_hardware_config, sample_credentials):
    """Create a sample physical hardware instance."""
    return PhysicalHardware(
        hardware_id="rpi-001",
        config=sample_hardware_config,
        ip_address="192.168.1.100",
        ssh_credentials=sample_credentials,
        power_control_type="pdu",
        power_control_address="192.168.1.10",
        location="Lab Rack 1",
        status=ReservationStatus.AVAILABLE
    )


@pytest.fixture
def hardware_lab(sample_physical_hardware):
    """Create a hardware lab with sample hardware."""
    return PhysicalHardwareLab(hardware_inventory=[sample_physical_hardware])


class TestPhysicalHardwareLab:
    """Tests for PhysicalHardwareLab class."""
    
    def test_init_empty(self):
        """Test initialization with no hardware."""
        lab = PhysicalHardwareLab()
        assert len(lab.hardware) == 0
        assert len(lab.reservations) == 0
    
    def test_init_with_inventory(self, sample_physical_hardware):
        """Test initialization with hardware inventory."""
        lab = PhysicalHardwareLab(hardware_inventory=[sample_physical_hardware])
        assert len(lab.hardware) == 1
        assert "rpi-001" in lab.hardware
    
    def test_add_hardware(self, sample_physical_hardware):
        """Test adding hardware to lab."""
        lab = PhysicalHardwareLab()
        lab.add_hardware(sample_physical_hardware)
        
        assert len(lab.hardware) == 1
        assert lab.hardware["rpi-001"] == sample_physical_hardware
    
    def test_add_duplicate_hardware(self, sample_physical_hardware):
        """Test adding hardware with duplicate ID raises error."""
        lab = PhysicalHardwareLab(hardware_inventory=[sample_physical_hardware])
        
        with pytest.raises(ValueError, match="already exists"):
            lab.add_hardware(sample_physical_hardware)
    
    def test_remove_hardware(self, hardware_lab):
        """Test removing hardware from lab."""
        hardware_lab.remove_hardware("rpi-001")
        assert len(hardware_lab.hardware) == 0
    
    def test_remove_reserved_hardware(self, hardware_lab):
        """Test removing reserved hardware raises error."""
        # Reserve the hardware
        hardware_lab.reserve_hardware("rpi-001", "test-user")
        
        with pytest.raises(ValueError, match="currently reserved"):
            hardware_lab.remove_hardware("rpi-001")
    
    def test_reserve_hardware(self, hardware_lab):
        """Test reserving hardware."""
        reservation = hardware_lab.reserve_hardware(
            "rpi-001",
            "test-user",
            duration_minutes=30
        )
        
        assert reservation.hardware_id == "rpi-001"
        assert reservation.reserved_by == "test-user"
        assert reservation.status == ReservationStatus.RESERVED
        assert hardware_lab.hardware["rpi-001"].status == ReservationStatus.RESERVED
    
    def test_reserve_unavailable_hardware(self, hardware_lab):
        """Test reserving unavailable hardware raises error."""
        # Reserve once
        hardware_lab.reserve_hardware("rpi-001", "user1")
        
        # Try to reserve again
        with pytest.raises(ValueError, match="not available"):
            hardware_lab.reserve_hardware("rpi-001", "user2")
    
    def test_reserve_nonexistent_hardware(self, hardware_lab):
        """Test reserving nonexistent hardware raises error."""
        with pytest.raises(ValueError, match="not found"):
            hardware_lab.reserve_hardware("nonexistent", "test-user")
    
    def test_release_reservation(self, hardware_lab):
        """Test releasing a reservation."""
        reservation = hardware_lab.reserve_hardware("rpi-001", "test-user")
        reservation_id = reservation.reservation_id
        
        hardware_lab.release_reservation(reservation_id)
        
        assert reservation_id not in hardware_lab.reservations
        assert hardware_lab.hardware["rpi-001"].status == ReservationStatus.AVAILABLE
    
    def test_release_nonexistent_reservation(self, hardware_lab):
        """Test releasing nonexistent reservation raises error."""
        with pytest.raises(ValueError, match="not found"):
            hardware_lab.release_reservation("nonexistent")
    
    def test_get_reservation(self, hardware_lab):
        """Test getting reservation by ID."""
        reservation = hardware_lab.reserve_hardware("rpi-001", "test-user")
        
        retrieved = hardware_lab.get_reservation(reservation.reservation_id)
        assert retrieved == reservation
    
    def test_list_available_hardware(self, hardware_lab, sample_hardware_config, sample_credentials):
        """Test listing available hardware."""
        # Add more hardware
        hw2 = PhysicalHardware(
            hardware_id="rpi-002",
            config=sample_hardware_config,
            ip_address="192.168.1.101",
            ssh_credentials=sample_credentials,
            status=ReservationStatus.AVAILABLE
        )
        hardware_lab.add_hardware(hw2)
        
        # Reserve one
        hardware_lab.reserve_hardware("rpi-001", "test-user")
        
        available = hardware_lab.list_available_hardware()
        assert len(available) == 1
        assert available[0].hardware_id == "rpi-002"
    
    def test_list_available_hardware_with_filters(self, hardware_lab):
        """Test listing available hardware with filters."""
        # Add x86_64 hardware
        x86_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel i7",
            memory_mb=8192,
            is_virtual=False
        )
        x86_hw = PhysicalHardware(
            hardware_id="x86-001",
            config=x86_config,
            ip_address="192.168.1.102",
            ssh_credentials=Credentials(username="test"),
            status=ReservationStatus.AVAILABLE
        )
        hardware_lab.add_hardware(x86_hw)
        
        # Filter by architecture
        arm_hw = hardware_lab.list_available_hardware(architecture="arm64")
        assert len(arm_hw) == 1
        assert arm_hw[0].hardware_id == "rpi-001"
        
        # Filter by memory
        high_mem = hardware_lab.list_available_hardware(min_memory_mb=8000)
        assert len(high_mem) == 1
        assert high_mem[0].hardware_id == "x86-001"
    
    def test_cleanup_expired_reservations(self, hardware_lab):
        """Test cleaning up expired reservations."""
        # Create reservation with past expiration
        reservation = hardware_lab.reserve_hardware("rpi-001", "test-user", duration_minutes=1)
        
        # Manually expire it
        reservation.expires_at = datetime.now() - timedelta(minutes=1)
        
        cleaned = hardware_lab.cleanup_expired_reservations()
        
        assert cleaned == 1
        assert len(hardware_lab.reservations) == 0
        assert hardware_lab.hardware["rpi-001"].status == ReservationStatus.AVAILABLE
    
    @patch('execution.physical_hardware_lab.subprocess.run')
    def test_execute_test_ssh_success(self, mock_run, hardware_lab):
        """Test successful test execution via SSH."""
        # Reserve hardware first
        hardware_lab.reserve_hardware("rpi-001", "test-user")
        
        # Mock SSH command success
        mock_run.return_value = Mock(
            stdout="Test passed",
            stderr="",
            returncode=0
        )
        
        # Create test case
        test_case = TestCase(
            id="test-001",
            name="Sample Test",
            description="Test description",
            test_type=TestType.UNIT,
            target_subsystem="kernel",
            test_script="./run_test.sh"
        )
        
        result = hardware_lab.execute_test_ssh("rpi-001", test_case, timeout_seconds=60)
        
        assert result.test_id == "test-001"
        assert result.status == TestStatus.PASSED
        assert result.failure_info is None
        assert result.execution_time > 0
    
    @patch('execution.physical_hardware_lab.subprocess.run')
    def test_execute_test_ssh_failure(self, mock_run, hardware_lab):
        """Test failed test execution via SSH."""
        hardware_lab.reserve_hardware("rpi-001", "test-user")
        
        # Mock SSH command failure
        mock_run.return_value = Mock(
            stdout="",
            stderr="Test failed: assertion error",
            returncode=1
        )
        
        test_case = TestCase(
            id="test-002",
            name="Failing Test",
            description="Test that fails",
            test_type=TestType.UNIT,
            target_subsystem="kernel",
            test_script="./failing_test.sh"
        )
        
        result = hardware_lab.execute_test_ssh("rpi-001", test_case)
        
        assert result.status == TestStatus.FAILED
        assert result.failure_info is not None
        assert result.failure_info.exit_code == 1
    
    @patch('execution.physical_hardware_lab.subprocess.run')
    def test_execute_test_ssh_timeout(self, mock_run, hardware_lab):
        """Test test execution timeout via SSH."""
        hardware_lab.reserve_hardware("rpi-001", "test-user")
        
        # Mock SSH timeout
        mock_run.side_effect = subprocess.TimeoutExpired("ssh", 60)
        
        test_case = TestCase(
            id="test-003",
            name="Timeout Test",
            description="Test that times out",
            test_type=TestType.UNIT,
            target_subsystem="kernel",
            test_script="./long_test.sh"
        )
        
        result = hardware_lab.execute_test_ssh("rpi-001", test_case, timeout_seconds=60)
        
        assert result.status == TestStatus.TIMEOUT
        assert result.failure_info.timeout_occurred
    
    def test_execute_test_unreserved_hardware(self, hardware_lab):
        """Test executing test on unreserved hardware raises error."""
        test_case = TestCase(
            id="test-004",
            name="Test",
            description="Test",
            test_type=TestType.UNIT,
            target_subsystem="kernel",
            test_script="./test.sh"
        )
        
        with pytest.raises(ValueError, match="must be reserved"):
            hardware_lab.execute_test_ssh("rpi-001", test_case)
    
    @patch('execution.physical_hardware_lab.subprocess.run')
    def test_power_control_pdu(self, mock_run, hardware_lab):
        """Test power control via PDU."""
        result = hardware_lab.power_control("rpi-001", "reboot")
        assert result is True
    
    @patch('execution.physical_hardware_lab.subprocess.run')
    def test_power_control_ipmi(self, mock_run, hardware_lab):
        """Test power control via IPMI."""
        # Set hardware to use IPMI
        hardware_lab.hardware["rpi-001"].power_control_type = "ipmi"
        hardware_lab.hardware["rpi-001"].power_control_address = "192.168.1.50"
        
        # Mock ipmitool command
        mock_run.return_value = Mock(returncode=0)
        
        result = hardware_lab.power_control("rpi-001", "on")
        assert result is True
    
    def test_power_control_invalid_action(self, hardware_lab):
        """Test power control with invalid action raises error."""
        with pytest.raises(ValueError, match="Invalid power action"):
            hardware_lab.power_control("rpi-001", "invalid")
    
    def test_power_control_no_config(self, hardware_lab):
        """Test power control without configuration raises error."""
        hardware_lab.hardware["rpi-001"].power_control_type = None
        
        with pytest.raises(RuntimeError, match="does not have power control"):
            hardware_lab.power_control("rpi-001", "on")
    
    @patch('execution.physical_hardware_lab.PhysicalHardwareLab._execute_ssh_command')
    def test_check_hardware_health(self, mock_ssh, hardware_lab):
        """Test hardware health check."""
        # Mock SSH commands for health checks
        mock_ssh.side_effect = [
            {'stdout': 'test', 'stderr': '', 'return_code': 0, 'timed_out': False},  # connectivity
            {'stdout': '10G', 'stderr': '', 'return_code': 0, 'timed_out': False},  # disk
            {'stdout': '2048', 'stderr': '', 'return_code': 0, 'timed_out': False},  # memory
            {'stdout': '3600.5', 'stderr': '', 'return_code': 0, 'timed_out': False},  # uptime
            {'stdout': '5.10.0', 'stderr': '', 'return_code': 0, 'timed_out': False},  # kernel
        ]
        
        result = hardware_lab.check_hardware_health("rpi-001")
        
        assert result.is_healthy
        assert len(result.issues) == 0
        assert result.metrics['ssh_reachable'] is True
        assert result.metrics['free_gb'] == 10.0
        assert result.metrics['available_mb'] == 2048
        assert result.metrics['uptime_seconds'] == 3600.5
        assert result.metrics['kernel_version'] == '5.10.0'
    
    @patch('execution.physical_hardware_lab.PhysicalHardwareLab._execute_ssh_command')
    def test_check_hardware_health_with_issues(self, mock_ssh, hardware_lab):
        """Test hardware health check with issues."""
        # Mock SSH commands with low resources
        mock_ssh.side_effect = [
            {'stdout': 'test', 'stderr': '', 'return_code': 0, 'timed_out': False},  # connectivity
            {'stdout': '0.5G', 'stderr': '', 'return_code': 0, 'timed_out': False},  # low disk
            {'stdout': '256', 'stderr': '', 'return_code': 0, 'timed_out': False},  # low memory
            {'stdout': '100.0', 'stderr': '', 'return_code': 0, 'timed_out': False},  # uptime
            {'stdout': '5.10.0', 'stderr': '', 'return_code': 0, 'timed_out': False},  # kernel
        ]
        
        result = hardware_lab.check_hardware_health("rpi-001")
        
        assert not result.is_healthy
        assert len(result.issues) == 2
        assert any("disk space" in issue.lower() for issue in result.issues)
        assert any("memory" in issue.lower() for issue in result.issues)
    
    def test_get_hardware(self, hardware_lab):
        """Test getting hardware by ID."""
        hw = hardware_lab.get_hardware("rpi-001")
        assert hw is not None
        assert hw.hardware_id == "rpi-001"
    
    def test_list_all_hardware(self, hardware_lab):
        """Test listing all hardware."""
        all_hw = hardware_lab.list_all_hardware()
        assert len(all_hw) == 1
        assert all_hw[0].hardware_id == "rpi-001"
    
    def test_set_hardware_maintenance(self, hardware_lab):
        """Test setting hardware to maintenance mode."""
        hardware_lab.set_hardware_maintenance("rpi-001", maintenance=True)
        assert hardware_lab.hardware["rpi-001"].status == ReservationStatus.MAINTENANCE
        
        hardware_lab.set_hardware_maintenance("rpi-001", maintenance=False)
        assert hardware_lab.hardware["rpi-001"].status == ReservationStatus.AVAILABLE
    
    def test_set_maintenance_reserved_hardware(self, hardware_lab):
        """Test setting maintenance on reserved hardware raises error."""
        hardware_lab.reserve_hardware("rpi-001", "test-user")
        
        with pytest.raises(ValueError, match="is reserved"):
            hardware_lab.set_hardware_maintenance("rpi-001", maintenance=True)


class TestHardwareReservation:
    """Tests for HardwareReservation class."""
    
    def test_is_expired(self):
        """Test checking if reservation is expired."""
        # Create expired reservation
        expired = HardwareReservation(
            reservation_id="res-001",
            hardware_id="hw-001",
            reserved_by="user",
            reserved_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1),
            status=ReservationStatus.RESERVED
        )
        
        assert expired.is_expired()
        
        # Create active reservation
        active = HardwareReservation(
            reservation_id="res-002",
            hardware_id="hw-002",
            reserved_by="user",
            reserved_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
            status=ReservationStatus.RESERVED
        )
        
        assert not active.is_expired()


class TestPhysicalHardware:
    """Tests for PhysicalHardware class."""
    
    def test_create_physical_hardware(self, sample_hardware_config, sample_credentials):
        """Test creating physical hardware instance."""
        hw = PhysicalHardware(
            hardware_id="test-hw",
            config=sample_hardware_config,
            ip_address="192.168.1.1",
            ssh_credentials=sample_credentials
        )
        
        assert hw.hardware_id == "test-hw"
        assert hw.config == sample_hardware_config
        assert hw.status == ReservationStatus.AVAILABLE
    
    def test_create_with_virtual_config_raises_error(self, sample_credentials):
        """Test creating physical hardware with virtual config raises error."""
        virtual_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="QEMU",
            memory_mb=2048,
            is_virtual=True,
            emulator="qemu"
        )
        
        with pytest.raises(ValueError, match="is_virtual=False"):
            PhysicalHardware(
                hardware_id="test-hw",
                config=virtual_config,
                ip_address="192.168.1.1",
                ssh_credentials=sample_credentials
            )
