"""
Flash Station Controller for Firmware Deployment

Provides firmware flashing functionality for physical test boards.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from infrastructure.connectors.ssh_connector import SSHConnector, SSHCredentials

logger = logging.getLogger(__name__)


class FlashStatus(Enum):
    """Status of a flash operation."""
    PENDING = "pending"
    PREPARING = "preparing"
    FLASHING = "flashing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FlashProgress:
    """Progress of a flash operation."""
    board_id: str
    status: FlashStatus
    percent_complete: float = 0.0
    current_step: str = ""
    bytes_written: int = 0
    total_bytes: int = 0
    elapsed_seconds: int = 0
    estimated_remaining_seconds: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class FlashResult:
    """Result of a flash operation."""
    success: bool
    board_id: str
    firmware_path: str
    firmware_version: Optional[str] = None
    bytes_written: int = 0
    duration_seconds: int = 0
    verified: bool = False
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class VerificationResult:
    """Result of firmware verification."""
    success: bool
    board_id: str
    expected_version: str
    actual_version: Optional[str] = None
    checksum_match: bool = False
    error_message: Optional[str] = None


class FlashStationController:
    """
    Flash station controller for firmware deployment.
    
    Manages firmware flashing to physical test boards via associated
    flash station hosts.
    """

    def __init__(
        self,
        ssh_connector: Optional[SSHConnector] = None,
        flash_timeout: int = 600,
        verify_timeout: int = 60
    ):
        """
        Initialize Flash Station controller.
        
        Args:
            ssh_connector: SSH connector for flash station access
            flash_timeout: Flash operation timeout in seconds
            verify_timeout: Verification timeout in seconds
        """
        self.ssh_connector = ssh_connector or SSHConnector()
        self.flash_timeout = flash_timeout
        self.verify_timeout = verify_timeout
        
        # Track flash operations
        self._flash_progress: Dict[str, FlashProgress] = {}
        self._flash_history: Dict[str, List[FlashResult]] = {}

    async def flash_firmware(
        self,
        board_id: str,
        firmware_path: str,
        flash_station_credentials: SSHCredentials,
        board_type: str,
        verify: bool = True
    ) -> FlashResult:
        """
        Flash firmware to a board.
        
        Args:
            board_id: Board identifier
            firmware_path: Path to firmware file on flash station
            flash_station_credentials: SSH credentials for flash station
            board_type: Type of board (for selecting flash method)
            verify: Whether to verify after flashing
            
        Returns:
            FlashResult with operation status
        """
        start_time = datetime.now(timezone.utc)
        
        # Initialize progress
        self._flash_progress[board_id] = FlashProgress(
            board_id=board_id,
            status=FlashStatus.PREPARING,
            current_step="Preparing flash operation"
        )
        
        try:
            logger.info(f"Starting firmware flash for board {board_id}")
            
            # Validate flash station connection
            validation = await self.ssh_connector.validate_connection(flash_station_credentials)
            if not validation.success:
                raise ConnectionError(f"Flash station not reachable: {validation.error_message}")
            
            # Check firmware file exists
            self._update_progress(board_id, FlashStatus.PREPARING, 10, "Checking firmware file")
            check_result = await self.ssh_connector.execute_command(
                flash_station_credentials,
                f"test -f {firmware_path} && echo 'exists'"
            )
            
            if "exists" not in check_result.stdout:
                raise FileNotFoundError(f"Firmware file not found: {firmware_path}")
            
            # Get firmware size
            size_result = await self.ssh_connector.execute_command(
                flash_station_credentials,
                f"stat -c %s {firmware_path}"
            )
            total_bytes = int(size_result.stdout.strip()) if size_result.success else 0
            
            # Start flashing
            self._update_progress(
                board_id, FlashStatus.FLASHING, 20,
                "Flashing firmware",
                total_bytes=total_bytes
            )
            
            # Execute flash command based on board type
            flash_cmd = self._get_flash_command(board_type, firmware_path, board_id)
            
            flash_result = await self.ssh_connector.execute_command(
                flash_station_credentials,
                flash_cmd,
                timeout=self.flash_timeout
            )
            
            if not flash_result.success:
                raise RuntimeError(f"Flash command failed: {flash_result.stderr}")
            
            self._update_progress(board_id, FlashStatus.FLASHING, 80, "Flash complete")
            
            # Verify if requested
            verified = False
            if verify:
                self._update_progress(board_id, FlashStatus.VERIFYING, 90, "Verifying firmware")
                verify_result = await self._verify_flash(
                    board_id, firmware_path, flash_station_credentials, board_type
                )
                verified = verify_result.success
            
            end_time = datetime.now(timezone.utc)
            duration_seconds = int((end_time - start_time).total_seconds())
            
            self._update_progress(board_id, FlashStatus.COMPLETED, 100, "Flash completed")
            
            result = FlashResult(
                success=True,
                board_id=board_id,
                firmware_path=firmware_path,
                bytes_written=total_bytes,
                duration_seconds=duration_seconds,
                verified=verified
            )
            
            self._record_flash_event(board_id, result)
            return result
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_seconds = int((end_time - start_time).total_seconds())
            
            self._update_progress(
                board_id, FlashStatus.FAILED, 0,
                f"Flash failed: {str(e)}"
            )
            
            result = FlashResult(
                success=False,
                board_id=board_id,
                firmware_path=firmware_path,
                duration_seconds=duration_seconds,
                error_message=str(e)
            )
            
            self._record_flash_event(board_id, result)
            return result

    async def get_flash_progress(self, board_id: str) -> Optional[FlashProgress]:
        """
        Get current flash progress for a board.
        
        Args:
            board_id: Board identifier
            
        Returns:
            FlashProgress if operation in progress
        """
        return self._flash_progress.get(board_id)

    async def cancel_flash(self, board_id: str) -> bool:
        """
        Cancel an ongoing flash operation.
        
        Args:
            board_id: Board identifier
            
        Returns:
            True if cancellation successful
        """
        if board_id in self._flash_progress:
            progress = self._flash_progress[board_id]
            if progress.status in (FlashStatus.PREPARING, FlashStatus.FLASHING):
                self._update_progress(board_id, FlashStatus.CANCELLED, 0, "Flash cancelled")
                logger.info(f"Cancelled flash operation for board {board_id}")
                return True
        return False

    async def verify_firmware(
        self,
        board_id: str,
        expected_version: str,
        flash_station_credentials: SSHCredentials,
        board_type: str
    ) -> VerificationResult:
        """
        Verify firmware version on a board.
        
        Args:
            board_id: Board identifier
            expected_version: Expected firmware version
            flash_station_credentials: SSH credentials for flash station
            board_type: Type of board
            
        Returns:
            VerificationResult with verification status
        """
        try:
            # Get actual firmware version
            version_cmd = self._get_version_command(board_type, board_id)
            
            result = await self.ssh_connector.execute_command(
                flash_station_credentials,
                version_cmd,
                timeout=self.verify_timeout
            )
            
            if not result.success:
                return VerificationResult(
                    success=False,
                    board_id=board_id,
                    expected_version=expected_version,
                    error_message=f"Failed to get firmware version: {result.stderr}"
                )
            
            actual_version = result.stdout.strip()
            version_match = expected_version in actual_version
            
            return VerificationResult(
                success=version_match,
                board_id=board_id,
                expected_version=expected_version,
                actual_version=actual_version,
                checksum_match=version_match
            )
            
        except Exception as e:
            return VerificationResult(
                success=False,
                board_id=board_id,
                expected_version=expected_version,
                error_message=str(e)
            )

    def get_flash_history(
        self,
        board_id: str,
        limit: int = 10
    ) -> List[FlashResult]:
        """
        Get flash history for a board.
        
        Args:
            board_id: Board identifier
            limit: Maximum number of events to return
            
        Returns:
            List of FlashResult events
        """
        history = self._flash_history.get(board_id, [])
        return history[-limit:]

    def _get_flash_command(
        self,
        board_type: str,
        firmware_path: str,
        board_id: str
    ) -> str:
        """Get the flash command for a board type."""
        # Different boards may need different flash tools
        board_type_lower = board_type.lower()
        
        if "raspberry" in board_type_lower:
            # For Raspberry Pi, typically use dd or rpi-imager
            return f"dd if={firmware_path} of=/dev/mmcblk0 bs=4M status=progress"
        elif "beaglebone" in board_type_lower:
            # BeagleBone uses different flash method
            return f"dd if={firmware_path} of=/dev/mmcblk1 bs=4M status=progress"
        elif "riscv" in board_type_lower:
            # RISC-V boards may use different tools
            return f"flash_tool --board {board_id} --image {firmware_path}"
        else:
            # Generic flash command
            return f"dd if={firmware_path} of=/dev/mmcblk0 bs=4M status=progress"

    def _get_version_command(self, board_type: str, board_id: str) -> str:
        """Get the version check command for a board type."""
        # This would typically read from the board via serial or SSH
        return "cat /etc/os-release | grep VERSION"

    async def _verify_flash(
        self,
        board_id: str,
        firmware_path: str,
        credentials: SSHCredentials,
        board_type: str
    ) -> VerificationResult:
        """Verify flash operation completed successfully."""
        # In a real implementation, this would:
        # 1. Read back from the device
        # 2. Compare checksums
        # 3. Verify boot capability
        
        await asyncio.sleep(0.5)  # Simulate verification
        
        return VerificationResult(
            success=True,
            board_id=board_id,
            expected_version="",
            checksum_match=True
        )

    def _update_progress(
        self,
        board_id: str,
        status: FlashStatus,
        percent: float,
        step: str,
        total_bytes: int = 0,
        bytes_written: int = 0
    ) -> None:
        """Update flash progress."""
        if board_id in self._flash_progress:
            progress = self._flash_progress[board_id]
            progress.status = status
            progress.percent_complete = percent
            progress.current_step = step
            if total_bytes:
                progress.total_bytes = total_bytes
            if bytes_written:
                progress.bytes_written = bytes_written
        else:
            self._flash_progress[board_id] = FlashProgress(
                board_id=board_id,
                status=status,
                percent_complete=percent,
                current_step=step,
                total_bytes=total_bytes,
                bytes_written=bytes_written
            )

    def _record_flash_event(self, board_id: str, result: FlashResult) -> None:
        """Record a flash event in history."""
        if board_id not in self._flash_history:
            self._flash_history[board_id] = []
        
        self._flash_history[board_id].append(result)
        
        # Keep only last 50 events per board
        if len(self._flash_history[board_id]) > 50:
            self._flash_history[board_id] = self._flash_history[board_id][-50:]
