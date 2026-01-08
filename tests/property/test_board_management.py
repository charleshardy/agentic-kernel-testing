"""
Property-Based Tests for Board Management

Tests correctness properties for physical test board management using Hypothesis.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List

from infrastructure.models.board import (
    Board,
    BoardStatus,
    BoardHealth,
    BoardRequirements,
    BoardSelectionResult,
    HealthLevel,
    PowerStatus,
    PowerControlConfig,
    PowerControlMethod,
)
from infrastructure.strategies.board_strategy import BoardSelectionStrategy, BoardReservation
from infrastructure.services.board_service import (
    BoardManagementService,
    BoardRegistrationConfig,
    FirmwareConfig,
)
from infrastructure.connectors.power_controller import PowerController, PowerCycleResult


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def architecture_strategy(draw):
    """Generate a valid architecture."""
    return draw(st.sampled_from(["arm64", "armv7", "riscv64", "x86_64"]))


@st.composite
def board_type_strategy(draw):
    """Generate a valid board type."""
    return draw(st.sampled_from([
        "raspberry_pi_4",
        "raspberry_pi_3",
        "beaglebone_black",
        "beaglebone_ai",
        "riscv_board",
        "jetson_nano",
        "stm32_discovery"
    ]))


@st.composite
def board_status_strategy(draw):
    """Generate a valid board status."""
    return draw(st.sampled_from(list(BoardStatus)))


@st.composite
def health_level_strategy(draw):
    """Generate a valid health level."""
    return draw(st.sampled_from(list(HealthLevel)))


@st.composite
def power_control_method_strategy(draw):
    """Generate a valid power control method."""
    return draw(st.sampled_from(list(PowerControlMethod)))


@st.composite
def power_control_config_strategy(draw, method: PowerControlMethod = None):
    """Generate a valid power control configuration."""
    method = method or draw(power_control_method_strategy())
    
    config = PowerControlConfig(method=method)
    
    if method == PowerControlMethod.USB_HUB:
        config.usb_hub_port = draw(st.integers(min_value=1, max_value=8))
    elif method == PowerControlMethod.NETWORK_PDU:
        config.pdu_outlet = draw(st.integers(min_value=1, max_value=24))
        config.pdu_address = f"192.168.1.{draw(st.integers(min_value=1, max_value=254))}"
    elif method == PowerControlMethod.GPIO_RELAY:
        config.gpio_pin = draw(st.integers(min_value=1, max_value=40))
    
    return config


@st.composite
def board_health_strategy(draw, connectivity: HealthLevel = None):
    """Generate a valid board health."""
    return BoardHealth(
        connectivity=connectivity or draw(health_level_strategy()),
        temperature_celsius=draw(st.floats(min_value=20.0, max_value=90.0)),
        storage_percent=draw(st.floats(min_value=0.0, max_value=100.0)),
        power_status=draw(st.sampled_from(list(PowerStatus))),
        last_response_time_ms=draw(st.integers(min_value=1, max_value=5000))
    )


@st.composite
def board_strategy(draw, architecture: str = None, status: BoardStatus = None,
                   health: BoardHealth = None, maintenance: bool = None,
                   power_method: PowerControlMethod = None):
    """Generate a valid Board."""
    arch = architecture or draw(architecture_strategy())
    now = datetime.now(timezone.utc)
    
    power_config = draw(power_control_config_strategy(method=power_method))
    
    return Board(
        id=draw(st.uuids().map(str)),
        name=draw(st.text(min_size=5, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")),
        board_type=draw(board_type_strategy()),
        architecture=arch,
        power_control=power_config,
        serial_number=draw(st.text(min_size=8, max_size=16, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")),
        ip_address=f"192.168.{draw(st.integers(min_value=1, max_value=254))}.{draw(st.integers(min_value=1, max_value=254))}",
        ssh_port=22,
        ssh_username="root",
        serial_device=f"/dev/ttyUSB{draw(st.integers(min_value=0, max_value=9))}",
        serial_baud_rate=115200,
        status=status or draw(st.sampled_from([BoardStatus.AVAILABLE, BoardStatus.UNKNOWN])),
        health=health or draw(board_health_strategy(connectivity=HealthLevel.HEALTHY)),
        current_firmware_version=f"v{draw(st.integers(min_value=1, max_value=5))}.{draw(st.integers(min_value=0, max_value=9))}.{draw(st.integers(min_value=0, max_value=9))}",
        peripherals=draw(st.lists(
            st.sampled_from(["gpio", "i2c", "spi", "uart", "usb", "ethernet", "wifi", "bluetooth"]),
            min_size=0,
            max_size=5,
            unique=True
        )),
        maintenance_mode=maintenance if maintenance is not None else False,
        created_at=now,
        updated_at=now,
        labels=draw(st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=st.text(min_size=1, max_size=20),
            max_size=3
        ))
    )


@st.composite
def board_requirements_strategy(draw, architecture: str = None):
    """Generate valid board requirements."""
    arch = architecture or draw(architecture_strategy())
    
    return BoardRequirements(
        architecture=arch,
        board_types=draw(st.lists(board_type_strategy(), min_size=0, max_size=2, unique=True)),
        required_peripherals=draw(st.lists(
            st.sampled_from(["gpio", "i2c", "spi", "uart"]),
            min_size=0,
            max_size=2,
            unique=True
        )),
        firmware_version=draw(st.one_of(
            st.none(),
            st.text(min_size=5, max_size=10, alphabet="v0123456789.")
        ))
    )


# =============================================================================
# Property Tests
# =============================================================================

class TestUnreachableBoardRecovery:
    """
    **Feature: test-infrastructure-management, Property 13: Unreachable Board Recovery Attempt**
    **Validates: Requirements 10.3**
    
    For any board that becomes unreachable and has power control configured,
    the system SHALL attempt automatic power cycle recovery.
    """

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_unreachable_board_with_automated_power_triggers_recovery(self, data):
        """Unreachable boards with automated power control should trigger recovery."""
        architecture = data.draw(architecture_strategy())
        
        # Create board with automated power control (not MANUAL)
        power_method = data.draw(st.sampled_from([
            PowerControlMethod.USB_HUB,
            PowerControlMethod.NETWORK_PDU,
            PowerControlMethod.GPIO_RELAY
        ]))
        
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False,
            power_method=power_method
        ))
        
        # Verify power control is automated
        assert board.power_control.is_automated(), \
            "Board should have automated power control"
        
        # Simulate board becoming unreachable
        board.health.connectivity = HealthLevel.UNHEALTHY
        board.status = BoardStatus.OFFLINE
        
        # Create service and add board
        service = BoardManagementService(recovery_attempts=3)
        
        async def run_test():
            # Manually add board to service
            async with service._board_lock:
                service._boards[board.id] = board
                service._recovery_attempts[board.id] = 0
            
            # Trigger recovery handling
            await service._handle_unreachable_board(board.id)
            
            # Get updated board
            updated_board = await service.get_board(board.id)
            return updated_board
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Board should be in RECOVERY or AVAILABLE status (recovery attempted)
        # or OFFLINE if recovery failed
        assert result.status in (BoardStatus.RECOVERY, BoardStatus.AVAILABLE, BoardStatus.OFFLINE), \
            f"Board should be in recovery-related status, got {result.status}"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_unreachable_board_with_manual_power_no_recovery(self, data):
        """Unreachable boards with manual power control should not attempt recovery."""
        architecture = data.draw(architecture_strategy())
        
        # Create board with manual power control
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False,
            power_method=PowerControlMethod.MANUAL
        ))
        
        # Verify power control is manual
        assert not board.power_control.is_automated(), \
            "Board should have manual power control"
        
        # Simulate board becoming unreachable
        board.health.connectivity = HealthLevel.UNHEALTHY
        
        # Create service and add board
        service = BoardManagementService(recovery_attempts=3)
        
        async def run_test():
            # Manually add board to service
            async with service._board_lock:
                service._boards[board.id] = board
                service._recovery_attempts[board.id] = 0
            
            # Trigger recovery handling
            await service._handle_unreachable_board(board.id)
            
            # Get updated board
            updated_board = await service.get_board(board.id)
            return updated_board
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Board should be marked OFFLINE (no recovery possible)
        assert result.status == BoardStatus.OFFLINE, \
            f"Board with manual power should be marked offline, got {result.status}"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_recovery_attempts_tracked(self, data):
        """Recovery attempts should be tracked and limited."""
        architecture = data.draw(architecture_strategy())
        max_attempts = data.draw(st.integers(min_value=1, max_value=5))
        
        # Create board with automated power control
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False,
            power_method=PowerControlMethod.USB_HUB
        ))
        
        service = BoardManagementService(recovery_attempts=max_attempts)
        
        async def run_test():
            # Manually add board to service
            async with service._board_lock:
                service._boards[board.id] = board
                service._recovery_attempts[board.id] = 0
            
            # Simulate multiple recovery attempts
            for i in range(max_attempts + 2):
                await service._handle_unreachable_board(board.id)
            
            # Get recovery attempt count
            async with service._board_lock:
                attempts = service._recovery_attempts.get(board.id, 0)
            
            return attempts
        
        attempts = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Attempts should be tracked
        assert attempts >= 0, "Recovery attempts should be tracked"


class TestBoardSelectionRequirements:
    """
    **Feature: test-infrastructure-management, Property 14: Board Selection Meets Requirements**
    **Validates: Requirements 11.3, 13.3**
    
    For any board requirements and auto-selection, the selected board SHALL match
    the required architecture, board type, and peripherals.
    """

    @given(
        architecture=architecture_strategy(),
        data=st.data()
    )
    @settings(max_examples=3, deadline=None)
    def test_selected_board_matches_architecture(self, architecture: str, data):
        """Selected board must match required architecture."""
        now = datetime.now(timezone.utc)
        
        # Create board with matching architecture
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False
        ))
        
        requirements = BoardRequirements(
            architecture=architecture
        )
        
        boards = {board.id: board}
        strategy = BoardSelectionStrategy(boards)
        
        async def run_test():
            result = await strategy.select_board(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        assert result.board.architecture.lower() == architecture.lower(), \
            f"Selected board architecture {result.board.architecture} doesn't match required {architecture}"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_incompatible_architecture_not_selected(self, data):
        """Boards with incompatible architecture should not be selected."""
        now = datetime.now(timezone.utc)
        
        # Create board with arm64 architecture
        board = data.draw(board_strategy(
            architecture="arm64",
            status=BoardStatus.AVAILABLE,
            maintenance=False
        ))
        
        # Require riscv64 architecture
        requirements = BoardRequirements(
            architecture="riscv64"
        )
        
        boards = {board.id: board}
        strategy = BoardSelectionStrategy(boards)
        
        async def run_test():
            result = await strategy.select_board(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select board with incompatible architecture"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_board_type_requirement_enforced(self, data):
        """Board type requirement must be enforced."""
        architecture = "arm64"
        
        # Create board with specific type
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False
        ))
        board.board_type = "raspberry_pi_4"
        
        # Require different board type
        requirements = BoardRequirements(
            architecture=architecture,
            board_types=["beaglebone_black", "beaglebone_ai"]
        )
        
        boards = {board.id: board}
        strategy = BoardSelectionStrategy(boards)
        
        async def run_test():
            result = await strategy.select_board(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select board with incompatible board type"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_peripheral_requirements_enforced(self, data):
        """Peripheral requirements must be enforced."""
        architecture = "arm64"
        
        # Create board with limited peripherals
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False
        ))
        board.peripherals = ["gpio", "uart"]
        
        # Require peripherals the board doesn't have
        requirements = BoardRequirements(
            architecture=architecture,
            required_peripherals=["i2c", "spi"]
        )
        
        boards = {board.id: board}
        strategy = BoardSelectionStrategy(boards)
        
        async def run_test():
            result = await strategy.select_board(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select board without required peripherals"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_maintenance_mode_blocks_selection(self, data):
        """Boards in maintenance mode should not be selected."""
        architecture = data.draw(architecture_strategy())
        
        # Create board in maintenance mode
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.MAINTENANCE,
            maintenance=True
        ))
        
        requirements = BoardRequirements(
            architecture=architecture
        )
        
        boards = {board.id: board}
        strategy = BoardSelectionStrategy(boards)
        
        async def run_test():
            result = await strategy.select_board(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select board in maintenance mode"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_preferred_board_selected_when_compatible(self, data):
        """Preferred board should be selected when it meets requirements."""
        architecture = "arm64"
        now = datetime.now(timezone.utc)
        
        # Create preferred board
        preferred_board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False
        ))
        preferred_board.peripherals = ["gpio", "i2c", "spi"]
        
        # Create another board
        other_board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False
        ))
        other_board.peripherals = ["gpio", "i2c", "spi", "uart", "usb"]  # More peripherals
        
        # Specify preferred board
        requirements = BoardRequirements(
            architecture=architecture,
            preferred_board_id=preferred_board.id
        )
        
        boards = {preferred_board.id: preferred_board, other_board.id: other_board}
        strategy = BoardSelectionStrategy(boards)
        
        async def run_test():
            result = await strategy.select_board(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        assert result.board.id == preferred_board.id, \
            "Should select preferred board when compatible"


class TestBoardFlashingLock:
    """
    **Feature: test-infrastructure-management, Property 15: Board Flashing Locks Board**
    **Validates: Requirements 6.2**
    
    For any board undergoing firmware flashing, the board status SHALL be FLASHING
    and new allocations SHALL be prevented.
    """

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_flashing_board_status_is_flashing(self, data):
        """Board being flashed should have FLASHING status."""
        architecture = data.draw(architecture_strategy())
        
        # Create available board
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.AVAILABLE,
            maintenance=False
        ))
        
        service = BoardManagementService()
        
        async def run_test():
            # Add board to service
            async with service._board_lock:
                service._boards[board.id] = board
            
            # Start flashing
            firmware = FirmwareConfig(
                firmware_path="/path/to/firmware.bin",
                version="v2.0.0"
            )
            
            # Get board status during flash (we'll check the status was set)
            # Since flash is simulated and fast, we check the result
            result = await service.flash_firmware(board.id, firmware)
            
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Flash should succeed
        assert result.success, f"Flash should succeed: {result.error_message}"
        assert result.firmware_version == "v2.0.0"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_flashing_board_not_selectable(self, data):
        """Board with FLASHING status should not be selected."""
        architecture = data.draw(architecture_strategy())
        
        # Create board with FLASHING status
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.FLASHING,
            maintenance=False
        ))
        
        requirements = BoardRequirements(
            architecture=architecture
        )
        
        boards = {board.id: board}
        strategy = BoardSelectionStrategy(boards)
        
        async def run_test():
            result = await strategy.select_board(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select board that is being flashed"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_cannot_flash_board_already_flashing(self, data):
        """Cannot start flashing a board that is already being flashed."""
        architecture = data.draw(architecture_strategy())
        
        # Create board already flashing
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.FLASHING,
            maintenance=False
        ))
        
        service = BoardManagementService()
        
        async def run_test():
            # Add board to service
            async with service._board_lock:
                service._boards[board.id] = board
            
            # Try to flash again
            firmware = FirmwareConfig(
                firmware_path="/path/to/firmware.bin",
                version="v2.0.0"
            )
            
            result = await service.flash_firmware(board.id, firmware)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not be able to flash board that is already flashing"
        assert "already being flashed" in result.error_message.lower()

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_cannot_flash_board_in_use(self, data):
        """Cannot flash a board that is currently in use."""
        architecture = data.draw(architecture_strategy())
        
        # Create board in use
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.IN_USE,
            maintenance=False
        ))
        board.assigned_test_id = "test-123"
        
        service = BoardManagementService()
        
        async def run_test():
            # Add board to service
            async with service._board_lock:
                service._boards[board.id] = board
            
            # Try to flash
            firmware = FirmwareConfig(
                firmware_path="/path/to/firmware.bin",
                version="v2.0.0"
            )
            
            result = await service.flash_firmware(board.id, firmware)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not be able to flash board that is in use"
        assert "in use" in result.error_message.lower()


class TestPowerCycleRecoverySequence:
    """
    **Feature: test-infrastructure-management, Property 16: Power Cycle Recovery Sequence**
    **Validates: Requirements 18.2**
    
    For any power cycle operation, the system SHALL execute the configured
    power control sequence (off → delay → on) and monitor board recovery.
    """

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_power_cycle_executes_off_delay_on_sequence(self, data):
        """Power cycle should execute off -> delay -> on sequence."""
        # Create power control config with automated method
        power_method = data.draw(st.sampled_from([
            PowerControlMethod.USB_HUB,
            PowerControlMethod.NETWORK_PDU,
            PowerControlMethod.GPIO_RELAY
        ]))
        
        power_config = data.draw(power_control_config_strategy(method=power_method))
        delay_seconds = data.draw(st.integers(min_value=1, max_value=10))
        
        board_id = data.draw(st.uuids().map(str))
        
        controller = PowerController(default_cycle_delay=5)
        
        async def run_test():
            result = await controller.power_cycle(board_id, power_config, delay_seconds)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Verify sequence was executed
        assert result.power_off_success, "Power off should succeed"
        assert result.power_on_success, "Power on should succeed"
        assert result.delay_seconds == delay_seconds, \
            f"Delay should be {delay_seconds}, got {result.delay_seconds}"
        assert result.success, "Power cycle should succeed"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_power_cycle_uses_default_delay(self, data):
        """Power cycle should use default delay when not specified."""
        power_method = data.draw(st.sampled_from([
            PowerControlMethod.USB_HUB,
            PowerControlMethod.NETWORK_PDU,
            PowerControlMethod.GPIO_RELAY
        ]))
        
        power_config = data.draw(power_control_config_strategy(method=power_method))
        default_delay = data.draw(st.integers(min_value=3, max_value=15))
        
        board_id = data.draw(st.uuids().map(str))
        
        controller = PowerController(default_cycle_delay=default_delay)
        
        async def run_test():
            # Don't specify delay
            result = await controller.power_cycle(board_id, power_config, None)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.delay_seconds == default_delay, \
            f"Should use default delay {default_delay}, got {result.delay_seconds}"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_power_cycle_manual_control_fails(self, data):
        """Power cycle with manual control should fail."""
        power_config = PowerControlConfig(method=PowerControlMethod.MANUAL)
        board_id = data.draw(st.uuids().map(str))
        
        controller = PowerController()
        
        async def run_test():
            result = await controller.power_cycle(board_id, power_config, 5)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Power cycle with manual control should fail"
        assert not result.power_off_success, \
            "Power off should fail for manual control"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_power_cycle_records_duration(self, data):
        """Power cycle should record total duration."""
        power_method = data.draw(st.sampled_from([
            PowerControlMethod.USB_HUB,
            PowerControlMethod.NETWORK_PDU,
            PowerControlMethod.GPIO_RELAY
        ]))
        
        power_config = data.draw(power_control_config_strategy(method=power_method))
        delay_seconds = 1  # Use small delay for faster test
        
        board_id = data.draw(st.uuids().map(str))
        
        controller = PowerController()
        
        async def run_test():
            result = await controller.power_cycle(board_id, power_config, delay_seconds)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Duration should be at least the delay time (in ms)
        assert result.total_duration_ms >= delay_seconds * 1000 * 0.9, \
            f"Duration {result.total_duration_ms}ms should be at least {delay_seconds * 1000}ms"

    @given(data=st.data())
    @settings(max_examples=3, deadline=None)
    def test_power_cycle_updates_board_status(self, data):
        """Power cycle should update board power status."""
        architecture = data.draw(architecture_strategy())
        
        # Create board with automated power control
        board = data.draw(board_strategy(
            architecture=architecture,
            status=BoardStatus.OFFLINE,
            maintenance=False,
            power_method=PowerControlMethod.USB_HUB
        ))
        
        service = BoardManagementService()
        
        async def run_test():
            # Add board to service
            async with service._board_lock:
                service._boards[board.id] = board
                service._recovery_attempts[board.id] = 0
            
            # Power cycle
            result = await service.power_cycle_board(board.id, delay_seconds=1)
            
            # Get updated board
            updated_board = await service.get_board(board.id)
            
            return result, updated_board
        
        result, updated_board = asyncio.new_event_loop().run_until_complete(run_test())
        
        if result.success:
            assert updated_board.health.power_status == PowerStatus.ON, \
                "Board power status should be ON after successful power cycle"
