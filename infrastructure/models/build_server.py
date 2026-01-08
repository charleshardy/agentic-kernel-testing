"""
Build Server Data Models

Models for build server registration, monitoring, and job management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class BuildServerStatus(Enum):
    """Status of a build server."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class BuildJobStatus(Enum):
    """Status of a build job."""
    QUEUED = "queued"
    BUILDING = "building"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Toolchain:
    """Cross-compilation toolchain configuration."""
    name: str  # e.g., gcc-arm-none-eabi, aarch64-linux-gnu-gcc
    version: str
    target_architecture: str  # x86_64, arm64, armv7, riscv64
    path: str
    available: bool = True

    def supports_architecture(self, arch: str) -> bool:
        """Check if this toolchain supports the given architecture."""
        return self.target_architecture.lower() == arch.lower() and self.available


@dataclass
class ResourceUtilization:
    """Current resource utilization metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    storage_percent: float = 0.0
    network_bytes_in: int = 0
    network_bytes_out: int = 0

    def is_overloaded(self, threshold: float = 85.0) -> bool:
        """Check if any resource exceeds the threshold."""
        return (
            self.cpu_percent > threshold or
            self.memory_percent > threshold or
            self.storage_percent > threshold
        )


@dataclass
class BuildServerCapacity:
    """Available capacity on a build server."""
    available_cpu_cores: int
    available_memory_mb: int
    available_storage_gb: int
    can_accept_build: bool
    estimated_queue_time_seconds: int = 0

    def meets_requirements(self, cpu: int, memory: int, storage: int) -> bool:
        """Check if capacity meets the given requirements."""
        return (
            self.can_accept_build and
            self.available_cpu_cores >= cpu and
            self.available_memory_mb >= memory and
            self.available_storage_gb >= storage
        )


@dataclass
class BuildServer:
    """A build server for compiling kernel/BSP source code."""
    id: str
    hostname: str
    ip_address: str
    ssh_username: str
    supported_architectures: List[str]
    toolchains: List[Toolchain]
    total_cpu_cores: int
    total_memory_mb: int
    total_storage_gb: int
    created_at: datetime
    updated_at: datetime
    ssh_port: int = 22
    ssh_key_path: Optional[str] = None
    status: BuildServerStatus = BuildServerStatus.UNKNOWN
    current_utilization: ResourceUtilization = field(default_factory=ResourceUtilization)
    active_build_count: int = 0
    max_concurrent_builds: int = 4
    queue_depth: int = 0
    group_id: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    maintenance_mode: bool = False
    last_health_check: Optional[datetime] = None

    def has_toolchain_for(self, architecture: str) -> bool:
        """Check if server has a toolchain for the given architecture."""
        return any(tc.supports_architecture(architecture) for tc in self.toolchains)

    def get_toolchain_for(self, architecture: str) -> Optional[Toolchain]:
        """Get the toolchain for the given architecture."""
        for tc in self.toolchains:
            if tc.supports_architecture(architecture):
                return tc
        return None

    def can_accept_build(self) -> bool:
        """Check if server can accept a new build."""
        return (
            self.status == BuildServerStatus.ONLINE and
            not self.maintenance_mode and
            self.active_build_count < self.max_concurrent_builds and
            not self.current_utilization.is_overloaded()
        )

    def get_capacity(self) -> BuildServerCapacity:
        """Get current capacity of the server."""
        available_cpu = max(0, self.total_cpu_cores - int(
            self.total_cpu_cores * self.current_utilization.cpu_percent / 100
        ))
        available_memory = max(0, self.total_memory_mb - int(
            self.total_memory_mb * self.current_utilization.memory_percent / 100
        ))
        available_storage = max(0, self.total_storage_gb - int(
            self.total_storage_gb * self.current_utilization.storage_percent / 100
        ))
        
        return BuildServerCapacity(
            available_cpu_cores=available_cpu,
            available_memory_mb=available_memory,
            available_storage_gb=available_storage,
            can_accept_build=self.can_accept_build(),
            estimated_queue_time_seconds=self.queue_depth * 300  # Estimate 5 min per queued job
        )


@dataclass
class BuildConfig:
    """Configuration for a build job."""
    kernel_config: Optional[str] = None  # defconfig name or path
    extra_make_args: List[str] = field(default_factory=list)
    enable_modules: bool = True
    build_dtbs: bool = True
    custom_env: Dict[str, str] = field(default_factory=dict)


@dataclass
class BuildJob:
    """A kernel/BSP build job."""
    id: str
    source_repository: str
    branch: str
    commit_hash: str
    target_architecture: str
    build_config: BuildConfig
    created_at: datetime
    updated_at: datetime
    server_id: Optional[str] = None
    status: BuildJobStatus = BuildJobStatus.QUEUED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    artifacts: List[str] = field(default_factory=list)
    log_path: Optional[str] = None
    error_message: Optional[str] = None

    def is_active(self) -> bool:
        """Check if the build is currently active."""
        return self.status in (BuildJobStatus.QUEUED, BuildJobStatus.BUILDING)

    def is_completed(self) -> bool:
        """Check if the build has completed (success or failure)."""
        return self.status in (BuildJobStatus.COMPLETED, BuildJobStatus.FAILED, BuildJobStatus.CANCELLED)


@dataclass
class BuildRequirements:
    """Requirements for selecting a build server."""
    target_architecture: str
    required_toolchain: Optional[str] = None
    min_cpu_cores: int = 1
    min_memory_mb: int = 2048
    min_storage_gb: int = 10
    preferred_server_id: Optional[str] = None
    required_labels: Dict[str, str] = field(default_factory=dict)
    group_id: Optional[str] = None


@dataclass
class BuildServerSelectionResult:
    """Result of build server selection."""
    success: bool
    server: Optional[BuildServer] = None
    reservation_id: Optional[str] = None
    error_message: Optional[str] = None
    alternative_servers: List[BuildServer] = field(default_factory=list)
    estimated_wait_time: Optional[int] = None  # seconds
