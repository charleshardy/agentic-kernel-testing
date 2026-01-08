"""
Build Server Management Service

Manages build server registration, monitoring, and lifecycle.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from infrastructure.models.build_server import (
    BuildServer,
    BuildServerStatus,
    BuildServerCapacity,
    Toolchain,
    ResourceUtilization,
)
from infrastructure.connectors.ssh_connector import SSHConnector, SSHCredentials

logger = logging.getLogger(__name__)


@dataclass
class BuildServerRegistrationConfig:
    """Configuration for registering a build server."""
    hostname: str
    ip_address: str
    ssh_username: str
    ssh_port: int = 22
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None
    supported_architectures: List[str] = field(default_factory=list)
    max_concurrent_builds: int = 4
    labels: Dict[str, str] = field(default_factory=dict)
    group_id: Optional[str] = None


@dataclass
class BuildServerRegistrationResult:
    """Result of build server registration."""
    success: bool
    server: Optional[BuildServer] = None
    error_message: Optional[str] = None
    detected_capabilities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildServerUpdate:
    """Update fields for a build server."""
    max_concurrent_builds: Optional[int] = None
    labels: Optional[Dict[str, str]] = None
    group_id: Optional[str] = None


@dataclass
class DecommissionResult:
    """Result of decommissioning a resource."""
    success: bool
    resource_id: str
    error_message: Optional[str] = None
    active_workloads: int = 0


@dataclass
class BuildServerFilters:
    """Filters for querying build servers."""
    status: Optional[BuildServerStatus] = None
    architecture: Optional[str] = None
    group_id: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    maintenance_mode: Optional[bool] = None


class BuildServerManagementService:
    """
    Service for managing build servers.
    
    Handles registration, monitoring, status tracking, and lifecycle management.
    """

    def __init__(
        self,
        ssh_connector: Optional[SSHConnector] = None,
        health_check_interval: int = 60
    ):
        """
        Initialize Build Server Management Service.
        
        Args:
            ssh_connector: SSH connector for server communication
            health_check_interval: Interval between health checks in seconds
        """
        self.ssh_connector = ssh_connector or SSHConnector()
        self.health_check_interval = health_check_interval
        
        # Server pool: {server_id: BuildServer}
        self._servers: Dict[str, BuildServer] = {}
        self._server_lock = asyncio.Lock()

    async def register_server(
        self,
        config: BuildServerRegistrationConfig
    ) -> BuildServerRegistrationResult:
        """
        Register a new build server.
        
        Args:
            config: Registration configuration
            
        Returns:
            BuildServerRegistrationResult with server details
        """
        try:
            logger.info(f"Registering build server: {config.hostname}")
            
            # Create SSH credentials
            credentials = SSHCredentials(
                hostname=config.ip_address,
                username=config.ssh_username,
                port=config.ssh_port,
                key_path=config.ssh_key_path,
                password=config.ssh_password
            )
            
            # Validate SSH connectivity
            validation = await self.ssh_connector.validate_connection(credentials)
            if not validation.success:
                return BuildServerRegistrationResult(
                    success=False,
                    error_message=f"SSH validation failed: {validation.error_message}"
                )
            
            # Detect server capabilities
            capabilities = await self._detect_capabilities(credentials)
            
            # Detect installed toolchains
            toolchains = await self._detect_toolchains(credentials)
            
            # Determine supported architectures
            supported_archs = config.supported_architectures or list(set(
                tc.target_architecture for tc in toolchains if tc.available
            ))
            
            # Create server instance
            now = datetime.now(timezone.utc)
            server_id = str(uuid.uuid4())
            
            server = BuildServer(
                id=server_id,
                hostname=config.hostname,
                ip_address=config.ip_address,
                ssh_username=config.ssh_username,
                ssh_port=config.ssh_port,
                ssh_key_path=config.ssh_key_path,
                supported_architectures=supported_archs,
                toolchains=toolchains,
                total_cpu_cores=capabilities.get("cpu_cores", 0),
                total_memory_mb=capabilities.get("memory_mb", 0),
                total_storage_gb=capabilities.get("storage_gb", 0),
                max_concurrent_builds=config.max_concurrent_builds,
                labels=config.labels,
                group_id=config.group_id,
                status=BuildServerStatus.ONLINE,
                created_at=now,
                updated_at=now,
                last_health_check=now
            )
            
            # Add to pool
            async with self._server_lock:
                self._servers[server_id] = server
            
            logger.info(f"Registered build server {server_id}: {config.hostname}")
            
            return BuildServerRegistrationResult(
                success=True,
                server=server,
                detected_capabilities=capabilities
            )
            
        except Exception as e:
            logger.error(f"Failed to register build server: {e}")
            return BuildServerRegistrationResult(
                success=False,
                error_message=str(e)
            )

    async def validate_server_connectivity(
        self,
        server_id: str
    ) -> bool:
        """
        Validate connectivity to a build server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if server is reachable
        """
        server = await self.get_server(server_id)
        if not server:
            return False
        
        credentials = self._get_credentials(server)
        validation = await self.ssh_connector.validate_connection(credentials)
        return validation.success

    async def get_server_status(
        self,
        server_id: str
    ) -> Optional[BuildServerStatus]:
        """
        Get current status of a build server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            BuildServerStatus or None if not found
        """
        server = await self.get_server(server_id)
        return server.status if server else None

    async def get_server(self, server_id: str) -> Optional[BuildServer]:
        """Get a build server by ID."""
        async with self._server_lock:
            return self._servers.get(server_id)

    async def get_all_servers(
        self,
        filters: Optional[BuildServerFilters] = None
    ) -> List[BuildServer]:
        """
        Get all build servers, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of BuildServer objects
        """
        async with self._server_lock:
            servers = list(self._servers.values())
        
        if not filters:
            return servers
        
        # Apply filters
        result = []
        for server in servers:
            if filters.status and server.status != filters.status:
                continue
            if filters.architecture and not server.has_toolchain_for(filters.architecture):
                continue
            if filters.group_id and server.group_id != filters.group_id:
                continue
            if filters.maintenance_mode is not None and server.maintenance_mode != filters.maintenance_mode:
                continue
            if filters.labels:
                if not all(server.labels.get(k) == v for k, v in filters.labels.items()):
                    continue
            result.append(server)
        
        return result

    async def update_server(
        self,
        server_id: str,
        updates: BuildServerUpdate
    ) -> Optional[BuildServer]:
        """
        Update a build server.
        
        Args:
            server_id: Server identifier
            updates: Fields to update
            
        Returns:
            Updated BuildServer or None if not found
        """
        async with self._server_lock:
            server = self._servers.get(server_id)
            if not server:
                return None
            
            if updates.max_concurrent_builds is not None:
                server.max_concurrent_builds = updates.max_concurrent_builds
            if updates.labels is not None:
                server.labels = updates.labels
            if updates.group_id is not None:
                server.group_id = updates.group_id
            
            server.updated_at = datetime.now(timezone.utc)
            return server

    async def set_maintenance_mode(
        self,
        server_id: str,
        enabled: bool
    ) -> Optional[BuildServer]:
        """
        Set maintenance mode for a build server.
        
        Args:
            server_id: Server identifier
            enabled: Whether to enable maintenance mode
            
        Returns:
            Updated BuildServer or None if not found
        """
        async with self._server_lock:
            server = self._servers.get(server_id)
            if not server:
                return None
            
            server.maintenance_mode = enabled
            server.status = BuildServerStatus.MAINTENANCE if enabled else BuildServerStatus.ONLINE
            server.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Build server {server_id} maintenance mode: {enabled}")
            return server

    async def decommission_server(
        self,
        server_id: str,
        force: bool = False
    ) -> DecommissionResult:
        """
        Decommission (remove) a build server.
        
        Args:
            server_id: Server identifier
            force: Force removal even with active builds
            
        Returns:
            DecommissionResult with status
        """
        async with self._server_lock:
            server = self._servers.get(server_id)
            if not server:
                return DecommissionResult(
                    success=False,
                    resource_id=server_id,
                    error_message="Server not found"
                )
            
            # Check for active builds
            if server.active_build_count > 0 and not force:
                return DecommissionResult(
                    success=False,
                    resource_id=server_id,
                    error_message="Server has active builds",
                    active_workloads=server.active_build_count
                )
            
            # Remove from pool
            del self._servers[server_id]
            
            logger.info(f"Decommissioned build server {server_id}")
            return DecommissionResult(
                success=True,
                resource_id=server_id
            )

    async def get_server_capacity(
        self,
        server_id: str
    ) -> Optional[BuildServerCapacity]:
        """
        Get current capacity of a build server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            BuildServerCapacity or None if not found
        """
        server = await self.get_server(server_id)
        return server.get_capacity() if server else None

    async def get_installed_toolchains(
        self,
        server_id: str
    ) -> List[Toolchain]:
        """
        Get installed toolchains on a build server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            List of Toolchain objects
        """
        server = await self.get_server(server_id)
        return server.toolchains if server else []

    async def refresh_server_status(
        self,
        server_id: str
    ) -> Optional[BuildServer]:
        """
        Refresh status and utilization of a build server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Updated BuildServer or None if not found
        """
        server = await self.get_server(server_id)
        if not server:
            return None
        
        credentials = self._get_credentials(server)
        
        try:
            # Check connectivity
            validation = await self.ssh_connector.validate_connection(credentials)
            
            if not validation.success:
                async with self._server_lock:
                    server.status = BuildServerStatus.OFFLINE
                    server.updated_at = datetime.now(timezone.utc)
                return server
            
            # Get current utilization
            utilization = await self._get_utilization(credentials)
            
            async with self._server_lock:
                server.current_utilization = utilization
                server.status = BuildServerStatus.ONLINE if not server.maintenance_mode else BuildServerStatus.MAINTENANCE
                server.last_health_check = datetime.now(timezone.utc)
                server.updated_at = datetime.now(timezone.utc)
            
            return server
            
        except Exception as e:
            logger.error(f"Failed to refresh server status: {e}")
            async with self._server_lock:
                server.status = BuildServerStatus.DEGRADED
                server.updated_at = datetime.now(timezone.utc)
            return server

    def _get_credentials(self, server: BuildServer) -> SSHCredentials:
        """Get SSH credentials for a server."""
        return SSHCredentials(
            hostname=server.ip_address,
            username=server.ssh_username,
            port=server.ssh_port,
            key_path=server.ssh_key_path
        )

    async def _detect_capabilities(
        self,
        credentials: SSHCredentials
    ) -> Dict[str, Any]:
        """Detect server capabilities via SSH."""
        capabilities = {}
        
        # Get CPU cores
        cpu_result = await self.ssh_connector.execute_command(credentials, "nproc")
        if cpu_result.success:
            try:
                capabilities["cpu_cores"] = int(cpu_result.stdout.strip())
            except ValueError:
                capabilities["cpu_cores"] = 0
        
        # Get memory
        mem_result = await self.ssh_connector.execute_command(
            credentials,
            "free -m | grep Mem | awk '{print $2}'"
        )
        if mem_result.success:
            try:
                capabilities["memory_mb"] = int(mem_result.stdout.strip())
            except ValueError:
                capabilities["memory_mb"] = 0
        
        # Get storage
        storage_result = await self.ssh_connector.execute_command(
            credentials,
            "df -BG / | tail -1 | awk '{print $2}' | tr -d 'G'"
        )
        if storage_result.success:
            try:
                capabilities["storage_gb"] = int(storage_result.stdout.strip())
            except ValueError:
                capabilities["storage_gb"] = 0
        
        # Get architecture
        arch_result = await self.ssh_connector.execute_command(credentials, "uname -m")
        if arch_result.success:
            capabilities["architecture"] = arch_result.stdout.strip()
        
        return capabilities

    async def _detect_toolchains(
        self,
        credentials: SSHCredentials
    ) -> List[Toolchain]:
        """Detect installed toolchains via SSH."""
        toolchains = []
        
        # Common toolchain patterns to check
        toolchain_checks = [
            ("gcc", "x86_64", "gcc --version | head -1"),
            ("aarch64-linux-gnu-gcc", "arm64", "aarch64-linux-gnu-gcc --version | head -1"),
            ("arm-linux-gnueabihf-gcc", "armv7", "arm-linux-gnueabihf-gcc --version | head -1"),
            ("riscv64-linux-gnu-gcc", "riscv64", "riscv64-linux-gnu-gcc --version | head -1"),
        ]
        
        for name, arch, cmd in toolchain_checks:
            result = await self.ssh_connector.execute_command(credentials, cmd, timeout=10)
            if result.success and result.stdout.strip():
                # Parse version from output
                version = result.stdout.strip().split()[-1] if result.stdout else "unknown"
                
                # Get path
                which_result = await self.ssh_connector.execute_command(
                    credentials,
                    f"which {name}"
                )
                path = which_result.stdout.strip() if which_result.success else f"/usr/bin/{name}"
                
                toolchains.append(Toolchain(
                    name=name,
                    version=version,
                    target_architecture=arch,
                    path=path,
                    available=True
                ))
        
        return toolchains

    async def _get_utilization(
        self,
        credentials: SSHCredentials
    ) -> ResourceUtilization:
        """Get current resource utilization via SSH."""
        utilization = ResourceUtilization()
        
        # Get CPU usage
        cpu_result = await self.ssh_connector.execute_command(
            credentials,
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
        )
        if cpu_result.success:
            try:
                utilization.cpu_percent = float(cpu_result.stdout.strip())
            except ValueError:
                pass
        
        # Get memory usage
        mem_result = await self.ssh_connector.execute_command(
            credentials,
            "free | grep Mem | awk '{print ($3/$2)*100}'"
        )
        if mem_result.success:
            try:
                utilization.memory_percent = float(mem_result.stdout.strip())
            except ValueError:
                pass
        
        # Get storage usage
        storage_result = await self.ssh_connector.execute_command(
            credentials,
            "df / | tail -1 | awk '{print $5}' | tr -d '%'"
        )
        if storage_result.success:
            try:
                utilization.storage_percent = float(storage_result.stdout.strip())
            except ValueError:
                pass
        
        return utilization
