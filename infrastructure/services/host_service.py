"""
Host Management Service

Manages QEMU host registration, monitoring, and lifecycle.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from infrastructure.models.host import (
    Host,
    HostStatus,
    HostCapacity,
    VMRequirements,
    HostSelectionResult,
)
from infrastructure.models.build_server import ResourceUtilization
from infrastructure.connectors.ssh_connector import SSHConnector, SSHCredentials
from infrastructure.connectors.libvirt_connector import LibvirtConnector

logger = logging.getLogger(__name__)


@dataclass
class HostRegistrationConfig:
    """Configuration for registering a QEMU host."""
    hostname: str
    ip_address: str
    ssh_username: str
    architecture: str
    ssh_port: int = 22
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None
    max_vms: int = 10
    labels: Dict[str, str] = field(default_factory=dict)
    group_id: Optional[str] = None


@dataclass
class HostRegistrationResult:
    """Result of host registration."""
    success: bool
    host: Optional[Host] = None
    error_message: Optional[str] = None
    detected_capabilities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HostUpdate:
    """Update fields for a host."""
    max_vms: Optional[int] = None
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
class HostFilters:
    """Filters for querying hosts."""
    status: Optional[HostStatus] = None
    architecture: Optional[str] = None
    group_id: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    maintenance_mode: Optional[bool] = None
    kvm_enabled: Optional[bool] = None


@dataclass
class VMInfo:
    """Information about a running VM."""
    id: str
    name: str
    state: str
    cpu_count: int
    memory_mb: int
    host_id: str


@dataclass
class ValidationResult:
    """Result of validation operation."""
    success: bool
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)



class HostManagementService:
    """
    Service for managing QEMU hosts.
    
    Handles registration, monitoring, status tracking, and lifecycle management.
    """

    def __init__(
        self,
        ssh_connector: Optional[SSHConnector] = None,
        libvirt_connector: Optional[LibvirtConnector] = None,
        health_check_interval: int = 60
    ):
        """
        Initialize Host Management Service.
        
        Args:
            ssh_connector: SSH connector for host communication
            libvirt_connector: Libvirt connector for VM management
            health_check_interval: Interval between health checks in seconds
        """
        self.ssh_connector = ssh_connector or SSHConnector()
        self.libvirt_connector = libvirt_connector or LibvirtConnector()
        self.health_check_interval = health_check_interval
        
        # Host pool: {host_id: Host}
        self._hosts: Dict[str, Host] = {}
        self._host_lock = asyncio.Lock()
        
        # VM tracking: {host_id: [VMInfo]}
        self._running_vms: Dict[str, List[VMInfo]] = {}

    async def register_host(
        self,
        config: HostRegistrationConfig
    ) -> HostRegistrationResult:
        """
        Register a new QEMU host.
        
        Args:
            config: Registration configuration
            
        Returns:
            HostRegistrationResult with host details
        """
        try:
            logger.info(f"Registering QEMU host: {config.hostname}")
            
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
                return HostRegistrationResult(
                    success=False,
                    error_message=f"SSH validation failed: {validation.error_message}"
                )
            
            # Detect host capabilities
            capabilities = await self._detect_capabilities(credentials)
            
            # Validate libvirt connectivity
            libvirt_valid = await self._validate_libvirt(credentials)
            if not libvirt_valid:
                logger.warning(f"Libvirt validation failed for {config.hostname}, continuing without VM support")
            
            # Create host instance
            now = datetime.now(timezone.utc)
            host_id = str(uuid.uuid4())
            
            host = Host(
                id=host_id,
                hostname=config.hostname,
                ip_address=config.ip_address,
                ssh_username=config.ssh_username,
                ssh_port=config.ssh_port,
                ssh_key_path=config.ssh_key_path,
                architecture=config.architecture,
                total_cpu_cores=capabilities.get("cpu_cores", 0),
                total_memory_mb=capabilities.get("memory_mb", 0),
                total_storage_gb=capabilities.get("storage_gb", 0),
                kvm_enabled=capabilities.get("kvm_enabled", False),
                nested_virt_enabled=capabilities.get("nested_virt", False),
                max_vms=config.max_vms,
                labels=config.labels,
                group_id=config.group_id,
                status=HostStatus.ONLINE,
                created_at=now,
                updated_at=now,
                last_health_check=now
            )
            
            # Add to pool
            async with self._host_lock:
                self._hosts[host_id] = host
                self._running_vms[host_id] = []
            
            logger.info(f"Registered QEMU host {host_id}: {config.hostname}")
            
            return HostRegistrationResult(
                success=True,
                host=host,
                detected_capabilities=capabilities
            )
            
        except Exception as e:
            logger.error(f"Failed to register QEMU host: {e}")
            return HostRegistrationResult(
                success=False,
                error_message=str(e)
            )

    async def validate_host_connectivity(
        self,
        host_id: str
    ) -> ValidationResult:
        """
        Validate connectivity to a QEMU host.
        
        Args:
            host_id: Host identifier
            
        Returns:
            ValidationResult with status
        """
        host = await self.get_host(host_id)
        if not host:
            return ValidationResult(
                success=False,
                error_message="Host not found"
            )
        
        credentials = self._get_credentials(host)
        validation = await self.ssh_connector.validate_connection(credentials)
        
        return ValidationResult(
            success=validation.success,
            error_message=validation.error_message if not validation.success else None
        )

    async def get_host_status(
        self,
        host_id: str
    ) -> Optional[HostStatus]:
        """
        Get current status of a QEMU host.
        
        Args:
            host_id: Host identifier
            
        Returns:
            HostStatus or None if not found
        """
        host = await self.get_host(host_id)
        return host.status if host else None

    async def get_host(self, host_id: str) -> Optional[Host]:
        """Get a host by ID."""
        async with self._host_lock:
            return self._hosts.get(host_id)

    async def get_all_hosts(
        self,
        filters: Optional[HostFilters] = None
    ) -> List[Host]:
        """
        Get all hosts, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of Host objects
        """
        async with self._host_lock:
            hosts = list(self._hosts.values())
        
        if not filters:
            return hosts
        
        # Apply filters
        result = []
        for host in hosts:
            if filters.status and host.status != filters.status:
                continue
            if filters.architecture and not host.supports_architecture(filters.architecture):
                continue
            if filters.group_id and host.group_id != filters.group_id:
                continue
            if filters.maintenance_mode is not None and host.maintenance_mode != filters.maintenance_mode:
                continue
            if filters.kvm_enabled is not None and host.kvm_enabled != filters.kvm_enabled:
                continue
            if filters.labels:
                if not all(host.labels.get(k) == v for k, v in filters.labels.items()):
                    continue
            result.append(host)
        
        return result

    async def update_host(
        self,
        host_id: str,
        updates: HostUpdate
    ) -> Optional[Host]:
        """
        Update a host.
        
        Args:
            host_id: Host identifier
            updates: Fields to update
            
        Returns:
            Updated Host or None if not found
        """
        async with self._host_lock:
            host = self._hosts.get(host_id)
            if not host:
                return None
            
            if updates.max_vms is not None:
                host.max_vms = updates.max_vms
            if updates.labels is not None:
                host.labels = updates.labels
            if updates.group_id is not None:
                host.group_id = updates.group_id
            
            host.updated_at = datetime.now(timezone.utc)
            return host

    async def set_maintenance_mode(
        self,
        host_id: str,
        enabled: bool
    ) -> Optional[Host]:
        """
        Set maintenance mode for a host.
        
        Args:
            host_id: Host identifier
            enabled: Whether to enable maintenance mode
            
        Returns:
            Updated Host or None if not found
        """
        async with self._host_lock:
            host = self._hosts.get(host_id)
            if not host:
                return None
            
            host.maintenance_mode = enabled
            host.status = HostStatus.MAINTENANCE if enabled else HostStatus.ONLINE
            host.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Host {host_id} maintenance mode: {enabled}")
            return host

    async def decommission_host(
        self,
        host_id: str,
        force: bool = False
    ) -> DecommissionResult:
        """
        Decommission (remove) a host.
        
        Args:
            host_id: Host identifier
            force: Force removal even with running VMs
            
        Returns:
            DecommissionResult with status
        """
        async with self._host_lock:
            host = self._hosts.get(host_id)
            if not host:
                return DecommissionResult(
                    success=False,
                    resource_id=host_id,
                    error_message="Host not found"
                )
            
            # Check for running VMs
            running_vms = len(self._running_vms.get(host_id, []))
            if running_vms > 0 and not force:
                return DecommissionResult(
                    success=False,
                    resource_id=host_id,
                    error_message="Host has running VMs",
                    active_workloads=running_vms
                )
            
            # Remove from pool
            del self._hosts[host_id]
            if host_id in self._running_vms:
                del self._running_vms[host_id]
            
            logger.info(f"Decommissioned host {host_id}")
            return DecommissionResult(
                success=True,
                resource_id=host_id
            )

    async def get_host_capacity(
        self,
        host_id: str
    ) -> Optional[HostCapacity]:
        """
        Get current capacity of a host.
        
        Args:
            host_id: Host identifier
            
        Returns:
            HostCapacity or None if not found
        """
        host = await self.get_host(host_id)
        return host.get_capacity() if host else None

    async def get_running_vms(
        self,
        host_id: str
    ) -> List[VMInfo]:
        """
        Get running VMs on a host.
        
        Args:
            host_id: Host identifier
            
        Returns:
            List of VMInfo objects
        """
        async with self._host_lock:
            return list(self._running_vms.get(host_id, []))

    async def refresh_host_status(
        self,
        host_id: str
    ) -> Optional[Host]:
        """
        Refresh status and utilization of a host.
        
        Args:
            host_id: Host identifier
            
        Returns:
            Updated Host or None if not found
        """
        host = await self.get_host(host_id)
        if not host:
            return None
        
        credentials = self._get_credentials(host)
        
        try:
            # Check connectivity
            validation = await self.ssh_connector.validate_connection(credentials)
            
            if not validation.success:
                async with self._host_lock:
                    host.status = HostStatus.OFFLINE
                    host.updated_at = datetime.now(timezone.utc)
                return host
            
            # Get current utilization
            utilization = await self._get_utilization(credentials)
            
            # Check if utilization exceeds threshold (85%)
            is_overloaded = utilization.is_overloaded()
            
            async with self._host_lock:
                host.current_utilization = utilization
                
                if host.maintenance_mode:
                    host.status = HostStatus.MAINTENANCE
                elif is_overloaded:
                    host.status = HostStatus.DEGRADED
                else:
                    host.status = HostStatus.ONLINE
                
                host.last_health_check = datetime.now(timezone.utc)
                host.updated_at = datetime.now(timezone.utc)
            
            return host
            
        except Exception as e:
            logger.error(f"Failed to refresh host status: {e}")
            async with self._host_lock:
                host.status = HostStatus.DEGRADED
                host.updated_at = datetime.now(timezone.utc)
            return host

    async def update_vm_count(
        self,
        host_id: str,
        vm_info: Optional[VMInfo] = None,
        remove_vm_id: Optional[str] = None
    ) -> bool:
        """
        Update VM count for a host.
        
        Args:
            host_id: Host identifier
            vm_info: VM to add (if adding)
            remove_vm_id: VM ID to remove (if removing)
            
        Returns:
            True if successful
        """
        async with self._host_lock:
            host = self._hosts.get(host_id)
            if not host:
                return False
            
            if vm_info:
                # Add VM
                if host_id not in self._running_vms:
                    self._running_vms[host_id] = []
                self._running_vms[host_id].append(vm_info)
                host.running_vm_count = len(self._running_vms[host_id])
            
            if remove_vm_id:
                # Remove VM
                if host_id in self._running_vms:
                    self._running_vms[host_id] = [
                        vm for vm in self._running_vms[host_id]
                        if vm.id != remove_vm_id
                    ]
                    host.running_vm_count = len(self._running_vms[host_id])
            
            host.updated_at = datetime.now(timezone.utc)
            return True

    def _get_credentials(self, host: Host) -> SSHCredentials:
        """Get SSH credentials for a host."""
        return SSHCredentials(
            hostname=host.ip_address,
            username=host.ssh_username,
            port=host.ssh_port,
            key_path=host.ssh_key_path
        )

    async def _detect_capabilities(
        self,
        credentials: SSHCredentials
    ) -> Dict[str, Any]:
        """Detect host capabilities via SSH."""
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
        
        # Check KVM support
        kvm_result = await self.ssh_connector.execute_command(
            credentials,
            "test -e /dev/kvm && echo 'yes' || echo 'no'"
        )
        if kvm_result.success:
            capabilities["kvm_enabled"] = kvm_result.stdout.strip() == "yes"
        
        # Check nested virtualization
        nested_result = await self.ssh_connector.execute_command(
            credentials,
            "cat /sys/module/kvm_intel/parameters/nested 2>/dev/null || cat /sys/module/kvm_amd/parameters/nested 2>/dev/null || echo 'N'"
        )
        if nested_result.success:
            capabilities["nested_virt"] = nested_result.stdout.strip() in ["Y", "1"]
        
        # Get architecture
        arch_result = await self.ssh_connector.execute_command(credentials, "uname -m")
        if arch_result.success:
            capabilities["architecture"] = arch_result.stdout.strip()
        
        return capabilities

    async def _validate_libvirt(
        self,
        credentials: SSHCredentials
    ) -> bool:
        """Validate libvirt is available on the host."""
        # Check if libvirtd is running
        result = await self.ssh_connector.execute_command(
            credentials,
            "systemctl is-active libvirtd 2>/dev/null || virsh version 2>/dev/null"
        )
        return result.success and result.exit_code == 0

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
