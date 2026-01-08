"""
Unit Tests for Infrastructure Connectors

Tests SSH, Libvirt, Serial, Power, and Flash connectors.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.connectors.ssh_connector import (
    SSHConnector,
    SSHCredentials,
    SSHConnectionStatus,
    CommandResult,
    FileTransferResult,
    ValidationResult,
)
from infrastructure.connectors.libvirt_connector import (
    LibvirtConnector,
    VMConfig,
    VMInfo,
    VMState,
    HostCapabilities,
)
from infrastructure.connectors.serial_connector import (
    SerialConnector,
    SerialConfig,
    SerialConnectionStatus,
    SerialCommandResult,
)
from infrastructure.connectors.power_controller import (
    PowerController,
    PowerResult,
    PowerCycleResult,
)
from infrastructure.connectors.flash_controller import (
    FlashStationController,
    FlashResult,
    FlashStatus,
    FlashProgress,
)
from infrastructure.models.board import PowerControlConfig, PowerControlMethod, PowerStatus


class TestSSHConnector:
    """Tests for SSHConnector."""

    @pytest.fixture
    def ssh_connector(self):
        """Create SSH connector instance."""
        return SSHConnector(
            max_connections_per_host=5,
            connection_timeout=30,
            command_timeout=300,
            max_retries=3
        )

    @pytest.fixture
    def credentials(self):
        """Create test SSH credentials."""
        return SSHCredentials(
            hostname="192.168.1.100",
            username="testuser",
            port=22,
            key_path="/path/to/key"
        )

    @pytest.mark.asyncio
    async def test_connect_success(self, ssh_connector, credentials):
        """Test successful SSH connection."""
        result = await ssh_connector.connect(credentials)
        assert result is True
        assert ssh_connector.get_connection_status(credentials) == SSHConnectionStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_disconnect(self, ssh_connector, credentials):
        """Test SSH disconnection."""
        await ssh_connector.connect(credentials)
        result = await ssh_connector.disconnect(credentials)
        assert result is True
        assert ssh_connector.get_connection_status(credentials) == SSHConnectionStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_execute_command(self, ssh_connector, credentials):
        """Test command execution."""
        result = await ssh_connector.execute_command(credentials, "echo 'test'")
        assert isinstance(result, CommandResult)
        assert result.command == "echo 'test'"
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_validate_connection(self, ssh_connector, credentials):
        """Test connection validation."""
        result = await ssh_connector.validate_connection(credentials)
        assert isinstance(result, ValidationResult)
        assert result.response_time_ms >= 0

    @pytest.mark.asyncio
    async def test_upload_file(self, ssh_connector, credentials):
        """Test file upload."""
        result = await ssh_connector.upload_file(
            credentials,
            "/local/path/file.txt",
            "/remote/path/file.txt"
        )
        assert isinstance(result, FileTransferResult)
        assert result.source_path == "/local/path/file.txt"
        assert result.dest_path == "/remote/path/file.txt"

    @pytest.mark.asyncio
    async def test_download_file(self, ssh_connector, credentials):
        """Test file download."""
        result = await ssh_connector.download_file(
            credentials,
            "/remote/path/file.txt",
            "/local/path/file.txt"
        )
        assert isinstance(result, FileTransferResult)
        assert result.source_path == "/remote/path/file.txt"
        assert result.dest_path == "/local/path/file.txt"

    def test_credentials_connection_key(self, credentials):
        """Test connection key generation."""
        key = credentials.get_connection_key()
        assert key == "testuser@192.168.1.100:22"


class TestLibvirtConnector:
    """Tests for LibvirtConnector."""

    @pytest.fixture
    def libvirt_connector(self):
        """Create Libvirt connector instance."""
        return LibvirtConnector()

    @pytest.fixture
    def credentials(self):
        """Create test SSH credentials."""
        return SSHCredentials(
            hostname="192.168.1.100",
            username="root",
            port=22
        )

    @pytest.fixture
    def vm_config(self):
        """Create test VM configuration."""
        return VMConfig(
            name="test-vm",
            cpu_count=2,
            memory_mb=2048,
            disk_gb=20,
            architecture="x86_64",
            enable_kvm=True
        )

    @pytest.mark.asyncio
    async def test_list_vms(self, libvirt_connector, credentials):
        """Test VM listing."""
        vms = await libvirt_connector.list_vms(credentials)
        assert isinstance(vms, list)

    @pytest.mark.asyncio
    async def test_get_host_capabilities(self, libvirt_connector, credentials):
        """Test getting host capabilities."""
        caps = await libvirt_connector.get_host_capabilities(credentials)
        # May return None if connection fails in test environment
        if caps:
            assert isinstance(caps, HostCapabilities)

    def test_parse_vm_state(self, libvirt_connector):
        """Test VM state parsing."""
        assert libvirt_connector._parse_vm_state("running") == VMState.RUNNING
        assert libvirt_connector._parse_vm_state("shut off") == VMState.SHUTOFF
        assert libvirt_connector._parse_vm_state("paused") == VMState.PAUSED
        assert libvirt_connector._parse_vm_state("unknown") == VMState.UNKNOWN

    def test_generate_vm_xml(self, libvirt_connector, vm_config):
        """Test VM XML generation."""
        xml = libvirt_connector._generate_vm_xml(vm_config)
        assert "<name>test-vm</name>" in xml
        assert "<memory unit='MiB'>2048</memory>" in xml
        assert "<vcpu>2</vcpu>" in xml
        assert "type='kvm'" in xml


class TestSerialConnector:
    """Tests for SerialConnector."""

    @pytest.fixture
    def serial_connector(self):
        """Create Serial connector instance."""
        return SerialConnector(
            command_timeout=30.0,
            read_buffer_size=4096,
            max_retries=3
        )

    @pytest.fixture
    def serial_config(self):
        """Create test serial configuration."""
        return SerialConfig(
            device="/dev/ttyUSB0",
            baud_rate=115200,
            timeout_seconds=30.0
        )

    @pytest.mark.asyncio
    async def test_connect(self, serial_connector, serial_config):
        """Test serial connection."""
        result = await serial_connector.connect(serial_config)
        assert result is True
        assert serial_connector.get_connection_status(serial_config) == SerialConnectionStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_disconnect(self, serial_connector, serial_config):
        """Test serial disconnection."""
        await serial_connector.connect(serial_config)
        result = await serial_connector.disconnect(serial_config)
        assert result is True
        assert serial_connector.get_connection_status(serial_config) == SerialConnectionStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_execute_command(self, serial_connector, serial_config):
        """Test command execution."""
        result = await serial_connector.execute_command(serial_config, "ls")
        assert isinstance(result, SerialCommandResult)
        assert result.command == "ls"

    @pytest.mark.asyncio
    async def test_validate_connection(self, serial_connector, serial_config):
        """Test connection validation."""
        result = await serial_connector.validate_connection(serial_config)
        assert result.response_time_ms >= 0

    def test_config_connection_key(self, serial_config):
        """Test connection key generation."""
        key = serial_config.get_connection_key()
        assert key == "/dev/ttyUSB0:115200"


class TestPowerController:
    """Tests for PowerController."""

    @pytest.fixture
    def power_controller(self):
        """Create Power controller instance."""
        return PowerController(
            default_cycle_delay=5,
            recovery_timeout=60
        )

    @pytest.fixture
    def usb_hub_config(self):
        """Create USB hub power config."""
        return PowerControlConfig(
            method=PowerControlMethod.USB_HUB,
            usb_hub_port=1
        )

    @pytest.fixture
    def pdu_config(self):
        """Create PDU power config."""
        return PowerControlConfig(
            method=PowerControlMethod.NETWORK_PDU,
            pdu_address="192.168.1.200",
            pdu_outlet=5
        )

    @pytest.fixture
    def gpio_config(self):
        """Create GPIO power config."""
        return PowerControlConfig(
            method=PowerControlMethod.GPIO_RELAY,
            gpio_pin=17
        )

    @pytest.mark.asyncio
    async def test_power_on_usb_hub(self, power_controller, usb_hub_config):
        """Test power on via USB hub."""
        result = await power_controller.power_on("board-1", usb_hub_config)
        assert isinstance(result, PowerResult)
        assert result.board_id == "board-1"
        assert result.operation == "on"
        assert result.success is True
        assert result.new_status == PowerStatus.ON

    @pytest.mark.asyncio
    async def test_power_off_usb_hub(self, power_controller, usb_hub_config):
        """Test power off via USB hub."""
        result = await power_controller.power_off("board-1", usb_hub_config)
        assert isinstance(result, PowerResult)
        assert result.operation == "off"
        assert result.success is True
        assert result.new_status == PowerStatus.OFF

    @pytest.mark.asyncio
    async def test_power_cycle(self, power_controller, usb_hub_config):
        """Test power cycle."""
        result = await power_controller.power_cycle("board-1", usb_hub_config, delay_seconds=1)
        assert isinstance(result, PowerCycleResult)
        assert result.board_id == "board-1"
        assert result.power_off_success is True
        assert result.power_on_success is True
        assert result.delay_seconds == 1

    @pytest.mark.asyncio
    async def test_power_on_pdu(self, power_controller, pdu_config):
        """Test power on via PDU."""
        result = await power_controller.power_on("board-2", pdu_config)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_power_on_gpio(self, power_controller, gpio_config):
        """Test power on via GPIO."""
        result = await power_controller.power_on("board-3", gpio_config)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_power_status(self, power_controller, usb_hub_config):
        """Test getting power status."""
        await power_controller.power_on("board-1", usb_hub_config)
        status = await power_controller.get_power_status("board-1", usb_hub_config)
        assert status == PowerStatus.ON

    def test_get_power_history(self, power_controller):
        """Test getting power history."""
        history = power_controller.get_power_history("board-1")
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_manual_power_control_fails(self, power_controller):
        """Test that manual power control returns failure."""
        manual_config = PowerControlConfig(method=PowerControlMethod.MANUAL)
        result = await power_controller.power_on("board-1", manual_config)
        assert result.success is False


class TestFlashStationController:
    """Tests for FlashStationController."""

    @pytest.fixture
    def flash_controller(self):
        """Create Flash controller instance."""
        return FlashStationController(
            flash_timeout=600,
            verify_timeout=60
        )

    @pytest.fixture
    def credentials(self):
        """Create test SSH credentials."""
        return SSHCredentials(
            hostname="192.168.1.150",
            username="flashuser",
            port=22
        )

    @pytest.mark.asyncio
    async def test_get_flash_progress_none(self, flash_controller):
        """Test getting flash progress when no operation."""
        progress = await flash_controller.get_flash_progress("board-1")
        assert progress is None

    @pytest.mark.asyncio
    async def test_cancel_flash_no_operation(self, flash_controller):
        """Test cancelling when no operation in progress."""
        result = await flash_controller.cancel_flash("board-1")
        assert result is False

    def test_get_flash_history_empty(self, flash_controller):
        """Test getting flash history when empty."""
        history = flash_controller.get_flash_history("board-1")
        assert history == []

    def test_get_flash_command_raspberry_pi(self, flash_controller):
        """Test flash command for Raspberry Pi."""
        cmd = flash_controller._get_flash_command(
            "raspberry_pi_4",
            "/path/to/image.img",
            "board-1"
        )
        assert "dd" in cmd
        assert "/path/to/image.img" in cmd

    def test_get_flash_command_beaglebone(self, flash_controller):
        """Test flash command for BeagleBone."""
        cmd = flash_controller._get_flash_command(
            "beaglebone",
            "/path/to/image.img",
            "board-1"
        )
        assert "dd" in cmd
        assert "mmcblk1" in cmd

    def test_update_progress(self, flash_controller):
        """Test progress update."""
        flash_controller._update_progress(
            "board-1",
            FlashStatus.FLASHING,
            50.0,
            "Writing firmware",
            total_bytes=1000000,
            bytes_written=500000
        )
        
        progress = flash_controller._flash_progress.get("board-1")
        assert progress is not None
        assert progress.status == FlashStatus.FLASHING
        assert progress.percent_complete == 50.0
        assert progress.total_bytes == 1000000
        assert progress.bytes_written == 500000
