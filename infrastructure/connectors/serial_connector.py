"""
Serial Connector for Board Communication

Provides serial console connectivity for physical test boards.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)


class SerialConnectionStatus(Enum):
    """Status of a serial connection."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class SerialConfig:
    """Serial port configuration."""
    device: str  # e.g., /dev/ttyUSB0
    baud_rate: int = 115200
    data_bits: int = 8
    parity: str = "N"  # N, E, O
    stop_bits: int = 1
    timeout_seconds: float = 30.0
    read_timeout: float = 1.0

    def get_connection_key(self) -> str:
        """Get a unique key for this connection."""
        return f"{self.device}:{self.baud_rate}"


@dataclass
class SerialCommandResult:
    """Result of a serial command execution."""
    success: bool
    output: str
    duration_ms: int
    command: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None


@dataclass
class SerialValidationResult:
    """Result of serial connection validation."""
    success: bool
    response_time_ms: int = 0
    error_message: Optional[str] = None
    board_response: Optional[str] = None


class SerialConnector:
    """
    Serial connector for physical test board communication.
    
    Provides methods for connection, command execution, and log capture
    via serial console.
    """

    def __init__(
        self,
        command_timeout: float = 30.0,
        read_buffer_size: int = 4096,
        max_retries: int = 3
    ):
        """
        Initialize Serial connector.
        
        Args:
            command_timeout: Default command timeout in seconds
            read_buffer_size: Size of read buffer
            max_retries: Maximum retry attempts
        """
        self.command_timeout = command_timeout
        self.read_buffer_size = read_buffer_size
        self.max_retries = max_retries
        
        # Track connections
        self._connections: Dict[str, Any] = {}
        self._connection_status: Dict[str, SerialConnectionStatus] = {}
        self._log_buffers: Dict[str, List[str]] = {}

    async def connect(self, config: SerialConfig) -> bool:
        """
        Establish serial connection.
        
        Args:
            config: Serial port configuration
            
        Returns:
            True if connection successful
        """
        connection_key = config.get_connection_key()
        self._connection_status[connection_key] = SerialConnectionStatus.CONNECTING
        
        try:
            logger.info(f"Connecting to serial port {config.device} at {config.baud_rate} baud")
            
            # In a real implementation, this would use pyserial
            # For now, we simulate the connection
            await asyncio.sleep(0.1)
            
            self._connection_status[connection_key] = SerialConnectionStatus.CONNECTED
            self._log_buffers[connection_key] = []
            
            logger.info(f"Connected to {config.device}")
            return True
            
        except Exception as e:
            self._connection_status[connection_key] = SerialConnectionStatus.ERROR
            logger.error(f"Failed to connect to {config.device}: {e}")
            return False

    async def disconnect(self, config: SerialConfig) -> bool:
        """
        Close serial connection.
        
        Args:
            config: Serial port configuration
            
        Returns:
            True if disconnection successful
        """
        connection_key = config.get_connection_key()
        
        try:
            if connection_key in self._connections:
                # Close the connection
                del self._connections[connection_key]
            
            self._connection_status[connection_key] = SerialConnectionStatus.DISCONNECTED
            
            if connection_key in self._log_buffers:
                del self._log_buffers[connection_key]
            
            logger.info(f"Disconnected from {config.device}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from {config.device}: {e}")
            return False

    async def execute_command(
        self,
        config: SerialConfig,
        command: str,
        timeout: Optional[float] = None,
        wait_for_prompt: bool = True,
        prompt_pattern: str = r"[$#>]\s*$"
    ) -> SerialCommandResult:
        """
        Execute a command on the serial console.
        
        Args:
            config: Serial port configuration
            command: Command to execute
            timeout: Command timeout in seconds
            wait_for_prompt: Wait for shell prompt after command
            prompt_pattern: Regex pattern for shell prompt
            
        Returns:
            SerialCommandResult with output
        """
        timeout = timeout or self.command_timeout
        start_time = datetime.now(timezone.utc)
        connection_key = config.get_connection_key()
        
        try:
            # Ensure connection
            if self._connection_status.get(connection_key) != SerialConnectionStatus.CONNECTED:
                await self.connect(config)
            
            logger.debug(f"Executing command on {config.device}: {command}")
            
            # In a real implementation, this would:
            # 1. Write command + newline to serial port
            # 2. Read response until prompt or timeout
            # For now, we simulate
            await asyncio.sleep(0.05)
            
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Simulate successful execution
            return SerialCommandResult(
                success=True,
                output="",
                duration_ms=duration_ms,
                command=command
            )
            
        except asyncio.TimeoutError:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            return SerialCommandResult(
                success=False,
                output="",
                duration_ms=duration_ms,
                command=command,
                error_message="Command timed out"
            )
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            return SerialCommandResult(
                success=False,
                output="",
                duration_ms=duration_ms,
                command=command,
                error_message=str(e)
            )

    async def read_output(
        self,
        config: SerialConfig,
        timeout: float = 5.0,
        until_pattern: Optional[str] = None
    ) -> str:
        """
        Read output from serial console.
        
        Args:
            config: Serial port configuration
            timeout: Read timeout in seconds
            until_pattern: Stop reading when pattern is matched
            
        Returns:
            Output string
        """
        connection_key = config.get_connection_key()
        
        try:
            if self._connection_status.get(connection_key) != SerialConnectionStatus.CONNECTED:
                await self.connect(config)
            
            # In a real implementation, this would read from serial port
            await asyncio.sleep(0.01)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error reading from {config.device}: {e}")
            return ""

    async def write_raw(
        self,
        config: SerialConfig,
        data: bytes
    ) -> bool:
        """
        Write raw bytes to serial port.
        
        Args:
            config: Serial port configuration
            data: Bytes to write
            
        Returns:
            True if successful
        """
        connection_key = config.get_connection_key()
        
        try:
            if self._connection_status.get(connection_key) != SerialConnectionStatus.CONNECTED:
                await self.connect(config)
            
            # In a real implementation, this would write to serial port
            await asyncio.sleep(0.01)
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing to {config.device}: {e}")
            return False

    async def send_break(self, config: SerialConfig) -> bool:
        """
        Send a break signal on the serial line.
        
        Args:
            config: Serial port configuration
            
        Returns:
            True if successful
        """
        connection_key = config.get_connection_key()
        
        try:
            if self._connection_status.get(connection_key) != SerialConnectionStatus.CONNECTED:
                return False
            
            # In a real implementation, this would send break signal
            logger.info(f"Sending break signal on {config.device}")
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending break on {config.device}: {e}")
            return False

    async def validate_connection(
        self,
        config: SerialConfig
    ) -> SerialValidationResult:
        """
        Validate serial connection to a board.
        
        Args:
            config: Serial port configuration
            
        Returns:
            SerialValidationResult with connection status
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Try to connect
            connected = await self.connect(config)
            if not connected:
                return SerialValidationResult(
                    success=False,
                    error_message="Failed to open serial port"
                )
            
            # Send a newline and wait for response
            result = await self.execute_command(
                config,
                "",  # Just send newline
                timeout=5.0
            )
            
            end_time = datetime.now(timezone.utc)
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Check if we got any response
            if result.success:
                return SerialValidationResult(
                    success=True,
                    response_time_ms=response_time_ms,
                    board_response=result.output
                )
            else:
                return SerialValidationResult(
                    success=False,
                    response_time_ms=response_time_ms,
                    error_message=result.error_message
                )
                
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            return SerialValidationResult(
                success=False,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )

    async def capture_boot_log(
        self,
        config: SerialConfig,
        timeout: float = 120.0,
        boot_complete_pattern: str = r"login:|#|\$"
    ) -> AsyncIterator[str]:
        """
        Capture boot log from serial console.
        
        Args:
            config: Serial port configuration
            timeout: Maximum time to wait for boot
            boot_complete_pattern: Pattern indicating boot is complete
            
        Yields:
            Log lines as they are received
        """
        connection_key = config.get_connection_key()
        
        try:
            if self._connection_status.get(connection_key) != SerialConnectionStatus.CONNECTED:
                await self.connect(config)
            
            start_time = datetime.now(timezone.utc)
            
            while True:
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                if elapsed > timeout:
                    logger.warning(f"Boot log capture timed out after {timeout}s")
                    break
                
                # In a real implementation, this would read from serial
                await asyncio.sleep(0.1)
                
                # Simulate end of boot
                break
                
        except Exception as e:
            logger.error(f"Error capturing boot log: {e}")

    def get_connection_status(self, config: SerialConfig) -> SerialConnectionStatus:
        """Get the current connection status for a serial port."""
        connection_key = config.get_connection_key()
        return self._connection_status.get(connection_key, SerialConnectionStatus.DISCONNECTED)

    def get_log_buffer(self, config: SerialConfig) -> List[str]:
        """Get the log buffer for a serial connection."""
        connection_key = config.get_connection_key()
        return self._log_buffers.get(connection_key, [])

    async def close_all(self) -> None:
        """Close all serial connections."""
        for connection_key in list(self._connections.keys()):
            if connection_key in self._connections:
                del self._connections[connection_key]
            self._connection_status[connection_key] = SerialConnectionStatus.DISCONNECTED
        
        self._log_buffers.clear()
        logger.info("Closed all serial connections")
