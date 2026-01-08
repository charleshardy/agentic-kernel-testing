"""
Board Management Service

Manages physical test board registration, monitoring, and lifecycle.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
from infrastructure.connectors.ssh_connector import SSHConnector, SSHCredentials
from infrastructure.connectors.serial_connector import SerialConnector
from infrastructure.connectors.power_controller import PowerController, PowerCycleResult

logger = logging.getLogger(__name__)


@dataclass
class BoardRegistrationConfig:
    """Configuration for registering a physical test board."""
    name: str
    board_type: str  # raspberry_pi_4, beaglebone, riscv_board
    architecture: str  # arm64, armv7, riscv64
    power_control: PowerControlConfig
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    ssh_port: int = 22
    ssh_username: Optional[str] = None
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None
    serial_device: Optional[str] = None  # /dev/ttyUSB0
    serial_baud_rate: int = 115200
    flash_station_id: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    peripherals: List[str] = field(default_factory=list)
    group_id: Optional[str] = None


@dataclass
class BoardRegistrationResult:
    """Result of board registration."""
    success: bool
    board: Optional[Board] = None
    error_message: Optional[str] = None
    detected_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BoardUpdate:
    """Update fields for a board."""
    name: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    peripherals: Optional[List[str]] = None
    group_id: Optional[str] = None
    flash_station_id: Optional[str] = None


@dataclass
class DecommissionResult:
    """Result of decommissioning a resource."""
    success: bool
    resource_id: str
    error_message: Optional[str] = None
    active_workloads: int = 0


@dataclass
class BoardFilters:
    """Filters for querying boards."""
    status: Optional[BoardStatus] = None
    architecture: Optional[str] = None
    board_type: Optional[str] = None
    group_id: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    maintenance_mode: Optional[bool] = None
    has_peripherals: Optional[List[str]] = None


@dataclass
class ValidationResult:
    """Result of validation operation."""
    success: bool
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlashResult:
    """Result of firmware flashing operation."""
    success: bool
    board_id: str
    firmware_version: Optional[str] = None
    duration_seconds: int = 0
    error_message: Optional[str] = None
    verified: bool = False


@dataclass
class FirmwareConfig:
    """Configuration for firmware flashing."""
    firmware_path: str
    version: str
    verify_after_flash: bool = True
    backup_current: bool = False


class BoardManagementService:
    """
    Service for managing physical test boards.
    
    Handles registration, monitoring, status tracking, power control,
    firmware flashing, and lifecycle management.
    """

    def __init__(
        self,
        ssh_connector: Optional[SSHConnector] = None,
        serial_connector: Optional[SerialConnector] = None,
        power_controller: Optional[PowerController] = None,
        health_check_interval: int = 60,
        recovery_attempts: int = 3
    ):
        """
        Initialize Board Management Service.
        
        Args:
            ssh_connector: SSH connector for board communication
            serial_connector: Serial connector for console access
            power_controller: Power controller for power management
            health_check_interval: Interval between health checks in seconds
            recovery_attempts: Number of recovery attempts before marking offline
        """
        self.ssh_connector = ssh_connector or SSHConnector()
        self.serial_connector = serial_connector or SerialConnector()
        self.power_controller = power_controller or PowerController()
        self.health_check_interval = health_check_interval
        self.recovery_attempts = recovery_attempts
        
        # Board pool: {board_id: Board}
        self._boards: Dict[str, Board] = {}
        self._board_lock = asyncio.Lock()
        
        # Track recovery attempts: {board_id: attempt_count}
        self._recovery_attempts: Dict[str, int] = {}

    async def register_board(
        self,
        config: BoardRegistrationConfig
    ) -> BoardRegistrationResult:
        """
        Register a new physical test board.
        
        Args:
            config: Registration configuration
            
        Returns:
            BoardRegistrationResult with board details
        """
        try:
            logger.info(f"Registering board: {config.name} ({config.board_type})")
            
            detected_info: Dict[str, Any] = {}
            
            # Validate connectivity (SSH or Serial)
            if config.ip_address and config.ssh_username:
                # Validate SSH connectivity
                credentials = SSHCredentials(
                    hostname=config.ip_address,
                    username=config.ssh_username,
                    port=config.ssh_port,
                    key_path=config.ssh_key_path,
                    password=config.ssh_password
                )
                
                validation = await self.ssh_connector.validate_connection(credentials)
                if not validation.success:
                    return BoardRegistrationResult(
                        success=False,
                        error_message=f"SSH validation failed: {validation.error_message}"
                    )
                
                # Detect board info via SSH
                detected_info = await self._detect_board_info_ssh(credentials)
                
            elif config.serial_device:
                # Validate serial connectivity
                validation = await self.serial_connector.validate_connection(
                    config.serial_device,
                    config.serial_baud_rate
                )
                if not validation.success:
                    return BoardRegistrationResult(
                        success=False,
                        error_message=f"Serial validation failed: {validation.error_message}"
                    )
                
                detected_info["connection_type"] = "serial"
            else:
                return BoardRegistrationResult(
                    success=False,
                    error_message="Either SSH (ip_address + ssh_username) or serial_device must be provided"
                )
            
            # Create board instance
            now = datetime.now(timezone.utc)
            board_id = str(uuid.uuid4())
            
            board = Board(
                id=board_id,
                name=config.name,
                board_type=config.board_type,
                architecture=config.architecture,
                power_control=config.power_control,
                serial_number=config.serial_number,
                ip_address=config.ip_address,
                ssh_port=config.ssh_port,
                ssh_username=config.ssh_username,
                serial_device=config.serial_device,
                serial_baud_rate=config.serial_baud_rate,
                flash_station_id=config.flash_station_id,
                labels=config.labels,
                peripherals=config.peripherals,
                group_id=config.group_id,
                status=BoardStatus.AVAILABLE,
                health=BoardHealth(
                    connectivity=HealthLevel.HEALTHY,
                    power_status=PowerStatus.ON
                ),
                created_at=now,
                updated_at=now,
                last_health_check=now
            )
            
            # Add to pool
            async with self._board_lock:
                self._boards[board_id] = board
                self._recovery_attempts[board_id] = 0
            
            logger.info(f"Registered board {board_id}: {config.name}")
            
            return BoardRegistrationResult(
                success=True,
                board=board,
                detected_info=detected_info
            )
            
        except Exception as e:
            logger.error(f"Failed to register board: {e}")
            return BoardRegistrationResult(
                success=False,
                error_message=str(e)
            )

    async def validate_board_connectivity(
        self,
        board_id: str
    ) -> ValidationResult:
        """
        Validate connectivity to a board.
        
        Args:
            board_id: Board identifier
            
        Returns:
            ValidationResult with status
        """
        board = await self.get_board(board_id)
        if not board:
            return ValidationResult(
                success=False,
                error_message="Board not found"
            )
        
        # Try SSH first if configured
        if board.ip_address and board.ssh_username:
            credentials = self._get_ssh_credentials(board)
            validation = await self.ssh_connector.validate_connection(credentials)
            return ValidationResult(
                success=validation.success,
                error_message=validation.error_message if not validation.success else None,
                details={"connection_type": "ssh"}
            )
        
        # Try serial if configured
        if board.serial_device:
            validation = await self.serial_connector.validate_connection(
                board.serial_device,
                board.serial_baud_rate
            )
            return ValidationResult(
                success=validation.success,
                error_message=validation.error_message if not validation.success else None,
                details={"connection_type": "serial"}
            )
        
        return ValidationResult(
            success=False,
            error_message="No connection method configured"
        )

    async def get_board_status(
        self,
        board_id: str
    ) -> Optional[BoardStatus]:
        """
        Get current status of a board.
        
        Args:
            board_id: Board identifier
            
        Returns:
            BoardStatus or None if not found
        """
        board = await self.get_board(board_id)
        return board.status if board else None

    async def get_board(self, board_id: str) -> Optional[Board]:
        """Get a board by ID."""
        async with self._board_lock:
            return self._boards.get(board_id)

    async def get_all_boards(
        self,
        filters: Optional[BoardFilters] = None
    ) -> List[Board]:
        """
        Get all boards, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of Board objects
        """
        async with self._board_lock:
            boards = list(self._boards.values())
        
        if not filters:
            return boards
        
        # Apply filters
        result = []
        for board in boards:
            if filters.status and board.status != filters.status:
                continue
            if filters.architecture and not board.supports_architecture(filters.architecture):
                continue
            if filters.board_type and not board.matches_type([filters.board_type]):
                continue
            if filters.group_id and board.group_id != filters.group_id:
                continue
            if filters.maintenance_mode is not None and board.maintenance_mode != filters.maintenance_mode:
                continue
            if filters.has_peripherals and not board.has_peripherals(filters.has_peripherals):
                continue
            if filters.labels:
                if not all(board.labels.get(k) == v for k, v in filters.labels.items()):
                    continue
            result.append(board)
        
        return result

    async def update_board(
        self,
        board_id: str,
        updates: BoardUpdate
    ) -> Optional[Board]:
        """
        Update a board.
        
        Args:
            board_id: Board identifier
            updates: Fields to update
            
        Returns:
            Updated Board or None if not found
        """
        async with self._board_lock:
            board = self._boards.get(board_id)
            if not board:
                return None
            
            if updates.name is not None:
                board.name = updates.name
            if updates.labels is not None:
                board.labels = updates.labels
            if updates.peripherals is not None:
                board.peripherals = updates.peripherals
            if updates.group_id is not None:
                board.group_id = updates.group_id
            if updates.flash_station_id is not None:
                board.flash_station_id = updates.flash_station_id
            
            board.updated_at = datetime.now(timezone.utc)
            return board

    async def set_maintenance_mode(
        self,
        board_id: str,
        enabled: bool
    ) -> Optional[Board]:
        """
        Set maintenance mode for a board.
        
        Args:
            board_id: Board identifier
            enabled: Whether to enable maintenance mode
            
        Returns:
            Updated Board or None if not found
        """
        async with self._board_lock:
            board = self._boards.get(board_id)
            if not board:
                return None
            
            board.maintenance_mode = enabled
            if enabled:
                board.status = BoardStatus.MAINTENANCE
            elif board.health.is_healthy():
                board.status = BoardStatus.AVAILABLE
            else:
                board.status = BoardStatus.OFFLINE
            
            board.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Board {board_id} maintenance mode: {enabled}")
            return board

    async def decommission_board(
        self,
        board_id: str,
        force: bool = False
    ) -> DecommissionResult:
        """
        Decommission (remove) a board.
        
        Args:
            board_id: Board identifier
            force: Force removal even with active tests
            
        Returns:
            DecommissionResult with status
        """
        async with self._board_lock:
            board = self._boards.get(board_id)
            if not board:
                return DecommissionResult(
                    success=False,
                    resource_id=board_id,
                    error_message="Board not found"
                )
            
            # Check for active tests
            if board.assigned_test_id and not force:
                return DecommissionResult(
                    success=False,
                    resource_id=board_id,
                    error_message="Board has active test",
                    active_workloads=1
                )
            
            # Check if board is flashing
            if board.status == BoardStatus.FLASHING and not force:
                return DecommissionResult(
                    success=False,
                    resource_id=board_id,
                    error_message="Board is currently flashing firmware",
                    active_workloads=1
                )
            
            # Remove from pool
            del self._boards[board_id]
            if board_id in self._recovery_attempts:
                del self._recovery_attempts[board_id]
            
            logger.info(f"Decommissioned board {board_id}")
            return DecommissionResult(
                success=True,
                resource_id=board_id
            )

    async def power_cycle_board(
        self,
        board_id: str,
        delay_seconds: Optional[int] = None
    ) -> PowerCycleResult:
        """
        Power cycle a board.
        
        Args:
            board_id: Board identifier
            delay_seconds: Delay between off and on
            
        Returns:
            PowerCycleResult with status
        """
        board = await self.get_board(board_id)
        if not board:
            return PowerCycleResult(
                success=False,
                board_id=board_id,
                power_off_success=False,
                power_on_success=False,
                delay_seconds=delay_seconds or 5,
                error_message="Board not found"
            )
        
        if not board.power_control.is_automated():
            return PowerCycleResult(
                success=False,
                board_id=board_id,
                power_off_success=False,
                power_on_success=False,
                delay_seconds=delay_seconds or 5,
                error_message="Board requires manual power control"
            )
        
        logger.info(f"Power cycling board {board_id}")
        
        # Execute power cycle
        result = await self.power_controller.power_cycle(
            board_id,
            board.power_control,
            delay_seconds
        )
        
        # Update board health
        async with self._board_lock:
            if board_id in self._boards:
                self._boards[board_id].health.power_status = (
                    PowerStatus.ON if result.success else PowerStatus.UNKNOWN
                )
                self._boards[board_id].updated_at = datetime.now(timezone.utc)
        
        return result

    async def flash_firmware(
        self,
        board_id: str,
        firmware: FirmwareConfig
    ) -> FlashResult:
        """
        Flash firmware to a board.
        
        Args:
            board_id: Board identifier
            firmware: Firmware configuration
            
        Returns:
            FlashResult with status
        """
        board = await self.get_board(board_id)
        if not board:
            return FlashResult(
                success=False,
                board_id=board_id,
                error_message="Board not found"
            )
        
        # Check if board is available for flashing
        if board.status == BoardStatus.FLASHING:
            return FlashResult(
                success=False,
                board_id=board_id,
                error_message="Board is already being flashed"
            )
        
        if board.status == BoardStatus.IN_USE:
            return FlashResult(
                success=False,
                board_id=board_id,
                error_message="Board is currently in use"
            )
        
        # Set board to flashing status
        async with self._board_lock:
            if board_id in self._boards:
                self._boards[board_id].status = BoardStatus.FLASHING
                self._boards[board_id].updated_at = datetime.now(timezone.utc)
        
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Flashing firmware {firmware.version} to board {board_id}")
            
            # Simulate firmware flashing (in real implementation, use flash station)
            await asyncio.sleep(0.1)  # Simulated flash time
            
            end_time = datetime.now(timezone.utc)
            duration = int((end_time - start_time).total_seconds())
            
            # Update board with new firmware version
            async with self._board_lock:
                if board_id in self._boards:
                    self._boards[board_id].current_firmware_version = firmware.version
                    self._boards[board_id].last_flash_timestamp = end_time
                    self._boards[board_id].status = BoardStatus.AVAILABLE
                    self._boards[board_id].updated_at = end_time
            
            return FlashResult(
                success=True,
                board_id=board_id,
                firmware_version=firmware.version,
                duration_seconds=duration,
                verified=firmware.verify_after_flash
            )
            
        except Exception as e:
            logger.error(f"Failed to flash firmware to board {board_id}: {e}")
            
            # Reset board status
            async with self._board_lock:
                if board_id in self._boards:
                    self._boards[board_id].status = BoardStatus.AVAILABLE
                    self._boards[board_id].updated_at = datetime.now(timezone.utc)
            
            return FlashResult(
                success=False,
                board_id=board_id,
                error_message=str(e)
            )

    async def get_board_health(
        self,
        board_id: str
    ) -> Optional[BoardHealth]:
        """
        Get health status of a board.
        
        Args:
            board_id: Board identifier
            
        Returns:
            BoardHealth or None if not found
        """
        board = await self.get_board(board_id)
        return board.health if board else None

    async def refresh_board_status(
        self,
        board_id: str
    ) -> Optional[Board]:
        """
        Refresh status and health of a board.
        
        Args:
            board_id: Board identifier
            
        Returns:
            Updated Board or None if not found
        """
        board = await self.get_board(board_id)
        if not board:
            return None
        
        # Skip if board is flashing
        if board.status == BoardStatus.FLASHING:
            return board
        
        # Check connectivity
        validation = await self.validate_board_connectivity(board_id)
        
        if not validation.success:
            # Board is unreachable - attempt recovery if power control is available
            await self._handle_unreachable_board(board_id)
            return await self.get_board(board_id)
        
        # Update health
        async with self._board_lock:
            if board_id in self._boards:
                self._boards[board_id].health.connectivity = HealthLevel.HEALTHY
                self._boards[board_id].last_health_check = datetime.now(timezone.utc)
                self._boards[board_id].updated_at = datetime.now(timezone.utc)
                
                # Reset recovery attempts on successful connection
                self._recovery_attempts[board_id] = 0
                
                # Update status if not in maintenance or in use
                if not self._boards[board_id].maintenance_mode:
                    if self._boards[board_id].status == BoardStatus.OFFLINE:
                        self._boards[board_id].status = BoardStatus.AVAILABLE
                    elif self._boards[board_id].status == BoardStatus.RECOVERY:
                        self._boards[board_id].status = BoardStatus.AVAILABLE
        
        return await self.get_board(board_id)

    async def _handle_unreachable_board(
        self,
        board_id: str
    ) -> None:
        """
        Handle an unreachable board by attempting recovery.
        
        Args:
            board_id: Board identifier
        """
        board = await self.get_board(board_id)
        if not board:
            return
        
        async with self._board_lock:
            # Update health status
            self._boards[board_id].health.connectivity = HealthLevel.UNHEALTHY
            self._boards[board_id].updated_at = datetime.now(timezone.utc)
            
            # Increment recovery attempts
            attempts = self._recovery_attempts.get(board_id, 0) + 1
            self._recovery_attempts[board_id] = attempts
        
        # Attempt power cycle recovery if configured
        if board.power_control.is_automated() and attempts <= self.recovery_attempts:
            logger.info(f"Attempting recovery for board {board_id} (attempt {attempts})")
            
            async with self._board_lock:
                self._boards[board_id].status = BoardStatus.RECOVERY
            
            # Power cycle
            result = await self.power_cycle_board(board_id)
            
            if result.success:
                # Wait for board to boot
                await asyncio.sleep(5)
                
                # Check connectivity again
                validation = await self.validate_board_connectivity(board_id)
                
                if validation.success:
                    async with self._board_lock:
                        self._boards[board_id].status = BoardStatus.AVAILABLE
                        self._boards[board_id].health.connectivity = HealthLevel.HEALTHY
                        self._recovery_attempts[board_id] = 0
                    logger.info(f"Board {board_id} recovered successfully")
                    return
        
        # Mark as offline if recovery failed or not possible
        async with self._board_lock:
            if board_id in self._boards:
                self._boards[board_id].status = BoardStatus.OFFLINE
                logger.warning(f"Board {board_id} marked as offline")

    async def allocate_board(
        self,
        board_id: str,
        test_id: str
    ) -> bool:
        """
        Allocate a board for a test.
        
        Args:
            board_id: Board identifier
            test_id: Test identifier
            
        Returns:
            True if allocation successful
        """
        async with self._board_lock:
            board = self._boards.get(board_id)
            if not board:
                return False
            
            if not board.can_be_allocated():
                return False
            
            board.status = BoardStatus.IN_USE
            board.assigned_test_id = test_id
            board.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Allocated board {board_id} to test {test_id}")
            return True

    async def release_board(
        self,
        board_id: str
    ) -> bool:
        """
        Release a board from a test.
        
        Args:
            board_id: Board identifier
            
        Returns:
            True if release successful
        """
        async with self._board_lock:
            board = self._boards.get(board_id)
            if not board:
                return False
            
            board.status = BoardStatus.AVAILABLE
            board.assigned_test_id = None
            board.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Released board {board_id}")
            return True

    def _get_ssh_credentials(self, board: Board) -> SSHCredentials:
        """Get SSH credentials for a board."""
        return SSHCredentials(
            hostname=board.ip_address or "",
            username=board.ssh_username or "",
            port=board.ssh_port
        )

    async def _detect_board_info_ssh(
        self,
        credentials: SSHCredentials
    ) -> Dict[str, Any]:
        """Detect board information via SSH."""
        info: Dict[str, Any] = {"connection_type": "ssh"}
        
        # Get architecture
        arch_result = await self.ssh_connector.execute_command(credentials, "uname -m")
        if arch_result.success:
            info["detected_architecture"] = arch_result.stdout.strip()
        
        # Get kernel version
        kernel_result = await self.ssh_connector.execute_command(credentials, "uname -r")
        if kernel_result.success:
            info["kernel_version"] = kernel_result.stdout.strip()
        
        # Get hostname
        hostname_result = await self.ssh_connector.execute_command(credentials, "hostname")
        if hostname_result.success:
            info["hostname"] = hostname_result.stdout.strip()
        
        return info
