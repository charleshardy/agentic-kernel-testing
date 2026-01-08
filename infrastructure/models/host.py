"""
QEMU Host Data Models

Models for QEMU host registration, monitoring, and VM management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from infrastructure.models.build_server import ResourceUtilization


class HostStatus(Enum):
    """Status of a QEMU host."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


@dataclass
class HostCapacity:
    """Available capacity on a QEMU host."""
    available_cpu_cores: int
    available_memory_mb: int
    available_storage_gb: int
    can_allocate_vm: bool
    max_vm_cpu: int
    max_vm_memory_mb: int

    def meets_requirements(self, cpu: int, memory: int, storage: int) -> bool:
        """Check if capacity meets the given requirements."""
        return (
            self.can_allocate_vm and
            self.available_cpu_cores >= cpu and
            self.available_memory_mb >= memory and
            self.available_storage_gb >= storage
        )


@dataclass
class Host:
    """A QEMU host for running virtual machines."""
    id: str
    hostname: str
    ip_address: str
    ssh_username: str
    architecture: str  # x86_64, arm64
    total_cpu_cores: int
    total_memory_mb: int
    total_storage_gb: int
    created_at: datetime
    updated_at: datetime
    ssh_port: int = 22
    ssh_key_path: Optional[str] = None
    status: HostStatus = HostStatus.UNKNOWN
    kvm_enabled: bool = False
    nested_virt_enabled: bool = False
    current_utilization: ResourceUtilization = field(default_factory=ResourceUtilization)
    running_vm_count: int = 0
    max_vms: int = 10
    group_id: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    maintenance_mode: bool = False
    last_health_check: Optional[datetime] = None

    def can_allocate_vm(self) -> bool:
        """Check if host can allocate a new VM."""
        return (
            self.status == HostStatus.ONLINE and
            not self.maintenance_mode and
            self.running_vm_count < self.max_vms and
            not self.current_utilization.is_overloaded()
        )

    def get_capacity(self) -> HostCapacity:
        """Get current capacity of the host."""
        available_cpu = max(0, self.total_cpu_cores - int(
            self.total_cpu_cores * self.current_utilization.cpu_percent / 100
        ))
        available_memory = max(0, self.total_memory_mb - int(
            self.total_memory_mb * self.current_utilization.memory_percent / 100
        ))
        available_storage = max(0, self.total_storage_gb - int(
            self.total_storage_gb * self.current_utilization.storage_percent / 100
        ))
        
        # Max VM resources (leave some headroom for host)
        max_vm_cpu = max(1, available_cpu - 1)
        max_vm_memory = max(512, available_memory - 1024)
        
        return HostCapacity(
            available_cpu_cores=available_cpu,
            available_memory_mb=available_memory,
            available_storage_gb=available_storage,
            can_allocate_vm=self.can_allocate_vm(),
            max_vm_cpu=max_vm_cpu,
            max_vm_memory_mb=max_vm_memory
        )

    def supports_architecture(self, arch: str) -> bool:
        """Check if host supports the given architecture."""
        # x86_64 hosts can run x86_64 VMs
        # arm64 hosts can run arm64 VMs
        return self.architecture.lower() == arch.lower()


@dataclass
class VMRequirements:
    """Requirements for selecting a QEMU host."""
    architecture: str
    min_cpu_cores: int
    min_memory_mb: int
    min_storage_gb: int
    require_kvm: bool = False
    require_nested_virt: bool = False
    preferred_host_id: Optional[str] = None
    required_labels: Dict[str, str] = field(default_factory=dict)
    group_id: Optional[str] = None


@dataclass
class HostSelectionResult:
    """Result of host selection."""
    success: bool
    host: Optional[Host] = None
    reservation_id: Optional[str] = None
    error_message: Optional[str] = None
    alternative_hosts: List[Host] = field(default_factory=list)
    estimated_wait_time: Optional[int] = None  # seconds
