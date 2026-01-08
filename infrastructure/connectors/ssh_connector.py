"""
SSH Connector for Remote Command Execution

Provides SSH connectivity for build servers, QEMU hosts, and physical boards.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)


class SSHConnectionStatus(Enum):
    """Status of an SSH connection."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


@dataclass
class SSHCredentials:
    """SSH connection credentials."""
    hostname: str
    username: str
    port: int = 22
    password: Optional[str] = None
    key_path: Optional[str] = None
    key_passphrase: Optional[str] = None
    timeout_seconds: int = 30

    def get_connection_key(self) -> str:
        """Get a unique key for this connection."""
        return f"{self.username}@{self.hostname}:{self.port}"


@dataclass
class CommandResult:
    """Result of a remote command execution."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    command: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def success(self) -> bool:
        """Check if command succeeded."""
        return self.exit_code == 0


@dataclass
class FileTransferResult:
    """Result of a file transfer operation."""
    success: bool
    source_path: str
    dest_path: str
    bytes_transferred: int = 0
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: int = 0


@dataclass
class ValidationResult:
    """Result of connection validation."""
    success: bool
    response_time_ms: int = 0
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class SSHConnector:
    """
    SSH connector for remote command execution and file transfer.
    
    Provides connection pooling, retry logic with exponential backoff,
    and methods for command execution, file transfer, and validation.
    """

    def __init__(
        self,
        max_connections_per_host: int = 5,
        connection_timeout: int = 30,
        command_timeout: int = 300,
        max_retries: int = 3,
        retry_delay_base: float = 1.0
    ):
        """
        Initialize SSH connector.
        
        Args:
            max_connections_per_host: Maximum connections per host
            connection_timeout: Connection timeout in seconds
            command_timeout: Command execution timeout in seconds
            max_retries: Maximum retry attempts
            retry_delay_base: Base delay for exponential backoff
        """
        self.max_connections_per_host = max_connections_per_host
        self.connection_timeout = connection_timeout
        self.command_timeout = command_timeout
        self.max_retries = max_retries
        self.retry_delay_base = retry_delay_base
        
        # Connection pool: {connection_key: [connections]}
        self._connection_pool: Dict[str, List[Any]] = {}
        self._pool_lock = asyncio.Lock()
        
        # Track connection status
        self._connection_status: Dict[str, SSHConnectionStatus] = {}

    async def connect(self, credentials: SSHCredentials) -> bool:
        """
        Establish SSH connection.
        
        Args:
            credentials: SSH connection credentials
            
        Returns:
            True if connection successful
        """
        connection_key = credentials.get_connection_key()
        self._connection_status[connection_key] = SSHConnectionStatus.CONNECTING
        
        try:
            # In a real implementation, this would use asyncssh or paramiko
            # For now, we simulate the connection
            logger.info(f"Connecting to {connection_key}")
            
            # Simulate connection delay
            await asyncio.sleep(0.1)
            
            self._connection_status[connection_key] = SSHConnectionStatus.CONNECTED
            logger.info(f"Connected to {connection_key}")
            return True
            
        except Exception as e:
            self._connection_status[connection_key] = SSHConnectionStatus.ERROR
            logger.error(f"Failed to connect to {connection_key}: {e}")
            return False

    async def disconnect(self, credentials: SSHCredentials) -> bool:
        """
        Close SSH connection.
        
        Args:
            credentials: SSH connection credentials
            
        Returns:
            True if disconnection successful
        """
        connection_key = credentials.get_connection_key()
        
        try:
            async with self._pool_lock:
                if connection_key in self._connection_pool:
                    # Close all connections in pool
                    del self._connection_pool[connection_key]
            
            self._connection_status[connection_key] = SSHConnectionStatus.DISCONNECTED
            logger.info(f"Disconnected from {connection_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from {connection_key}: {e}")
            return False

    async def execute_command(
        self,
        credentials: SSHCredentials,
        command: str,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """
        Execute a command on the remote host.
        
        Args:
            credentials: SSH connection credentials
            command: Command to execute
            timeout: Command timeout in seconds
            env: Environment variables
            
        Returns:
            CommandResult with output and exit code
        """
        timeout = timeout or self.command_timeout
        start_time = datetime.now(timezone.utc)
        
        for attempt in range(self.max_retries):
            try:
                # Ensure connection
                connection_key = credentials.get_connection_key()
                if self._connection_status.get(connection_key) != SSHConnectionStatus.CONNECTED:
                    await self.connect(credentials)
                
                logger.debug(f"Executing command on {connection_key}: {command[:100]}...")
                
                # In a real implementation, this would execute via SSH
                # For now, we simulate command execution
                await asyncio.sleep(0.05)  # Simulate execution time
                
                end_time = datetime.now(timezone.utc)
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Simulate successful execution
                return CommandResult(
                    exit_code=0,
                    stdout="",
                    stderr="",
                    duration_ms=duration_ms,
                    command=command
                )
                
            except asyncio.TimeoutError:
                logger.warning(f"Command timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_base * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    end_time = datetime.now(timezone.utc)
                    duration_ms = int((end_time - start_time).total_seconds() * 1000)
                    return CommandResult(
                        exit_code=-1,
                        stdout="",
                        stderr="Command timed out",
                        duration_ms=duration_ms,
                        command=command
                    )
                    
            except Exception as e:
                logger.error(f"Command execution error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_base * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    end_time = datetime.now(timezone.utc)
                    duration_ms = int((end_time - start_time).total_seconds() * 1000)
                    return CommandResult(
                        exit_code=-1,
                        stdout="",
                        stderr=str(e),
                        duration_ms=duration_ms,
                        command=command
                    )
        
        # Should not reach here
        return CommandResult(
            exit_code=-1,
            stdout="",
            stderr="Max retries exceeded",
            duration_ms=0,
            command=command
        )

    async def upload_file(
        self,
        credentials: SSHCredentials,
        local_path: str,
        remote_path: str,
        verify_checksum: bool = True
    ) -> FileTransferResult:
        """
        Upload a file to the remote host.
        
        Args:
            credentials: SSH connection credentials
            local_path: Local file path
            remote_path: Remote destination path
            verify_checksum: Whether to verify checksum after transfer
            
        Returns:
            FileTransferResult with transfer details
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            connection_key = credentials.get_connection_key()
            if self._connection_status.get(connection_key) != SSHConnectionStatus.CONNECTED:
                await self.connect(credentials)
            
            logger.info(f"Uploading {local_path} to {connection_key}:{remote_path}")
            
            # In a real implementation, this would use SFTP
            # For now, we simulate the transfer
            await asyncio.sleep(0.1)
            
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return FileTransferResult(
                success=True,
                source_path=local_path,
                dest_path=remote_path,
                bytes_transferred=0,  # Would be actual size
                checksum=None,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            return FileTransferResult(
                success=False,
                source_path=local_path,
                dest_path=remote_path,
                error_message=str(e),
                duration_ms=duration_ms
            )

    async def download_file(
        self,
        credentials: SSHCredentials,
        remote_path: str,
        local_path: str,
        verify_checksum: bool = True
    ) -> FileTransferResult:
        """
        Download a file from the remote host.
        
        Args:
            credentials: SSH connection credentials
            remote_path: Remote file path
            local_path: Local destination path
            verify_checksum: Whether to verify checksum after transfer
            
        Returns:
            FileTransferResult with transfer details
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            connection_key = credentials.get_connection_key()
            if self._connection_status.get(connection_key) != SSHConnectionStatus.CONNECTED:
                await self.connect(credentials)
            
            logger.info(f"Downloading {connection_key}:{remote_path} to {local_path}")
            
            # In a real implementation, this would use SFTP
            await asyncio.sleep(0.1)
            
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return FileTransferResult(
                success=True,
                source_path=remote_path,
                dest_path=local_path,
                bytes_transferred=0,
                checksum=None,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            return FileTransferResult(
                success=False,
                source_path=remote_path,
                dest_path=local_path,
                error_message=str(e),
                duration_ms=duration_ms
            )

    async def validate_connection(
        self,
        credentials: SSHCredentials
    ) -> ValidationResult:
        """
        Validate SSH connection to a host.
        
        Args:
            credentials: SSH connection credentials
            
        Returns:
            ValidationResult with connection status
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Try to connect
            connected = await self.connect(credentials)
            if not connected:
                return ValidationResult(
                    success=False,
                    error_message="Failed to establish SSH connection"
                )
            
            # Execute a simple command to verify
            result = await self.execute_command(credentials, "echo 'test'", timeout=10)
            
            end_time = datetime.now(timezone.utc)
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            if result.success:
                return ValidationResult(
                    success=True,
                    response_time_ms=response_time_ms,
                    details={"command_output": result.stdout}
                )
            else:
                return ValidationResult(
                    success=False,
                    response_time_ms=response_time_ms,
                    error_message=result.stderr
                )
                
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            return ValidationResult(
                success=False,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )

    def get_connection_status(self, credentials: SSHCredentials) -> SSHConnectionStatus:
        """Get the current connection status for a host."""
        connection_key = credentials.get_connection_key()
        return self._connection_status.get(connection_key, SSHConnectionStatus.DISCONNECTED)

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._pool_lock:
            for connection_key in list(self._connection_pool.keys()):
                del self._connection_pool[connection_key]
                self._connection_status[connection_key] = SSHConnectionStatus.DISCONNECTED
        
        logger.info("Closed all SSH connections")
