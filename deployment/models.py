"""
Data models for the Test Deployment System

Enhanced data models with comprehensive validation, state management,
and deployment configuration support.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any, Union
import hashlib
import json
import uuid


class DeploymentStatus(Enum):
    """Deployment status enumeration with comprehensive states"""
    PENDING = "pending"
    PREPARING = "preparing"
    CONNECTING = "connecting"
    INSTALLING_DEPS = "installing_dependencies"
    DEPLOYING_SCRIPTS = "deploying_scripts"
    CONFIGURING_INSTRUMENTATION = "configuring_instrumentation"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    @property
    def is_final(self) -> bool:
        """Check if this is a final status"""
        return self in [self.COMPLETED, self.FAILED, self.CANCELLED]
    
    @property
    def is_active(self) -> bool:
        """Check if deployment is actively running"""
        return self in [
            self.PREPARING, self.CONNECTING, self.INSTALLING_DEPS,
            self.DEPLOYING_SCRIPTS, self.CONFIGURING_INSTRUMENTATION, self.VALIDATING
        ]


class ArtifactType(Enum):
    """Test artifact type enumeration"""
    SCRIPT = "script"
    BINARY = "binary"
    CONFIG = "config"
    DATA = "data"
    LIBRARY = "library"
    DOCUMENTATION = "documentation"


class Priority(Enum):
    """Deployment priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class TestArtifact:
    """
    Represents a test artifact to be deployed.
    
    Enhanced with validation, metadata, and deployment tracking.
    """
    artifact_id: str
    name: str
    type: ArtifactType
    content: bytes
    checksum: str
    permissions: str
    target_path: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_bytes: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and initialize artifact after creation"""
        # Validate required fields
        if not self.artifact_id:
            self.artifact_id = f"artifact_{uuid.uuid4().hex[:8]}"
        
        if not self.name:
            raise ValueError("Artifact name is required")
        
        if not self.content:
            raise ValueError("Artifact content is required")
        
        # Calculate size
        self.size_bytes = len(self.content)
        
        # Set creation time if not provided
        if not self.created_at:
            self.created_at = datetime.now()
        
        # Calculate and validate checksum
        calculated_checksum = hashlib.sha256(self.content).hexdigest()
        if not self.checksum:
            self.checksum = calculated_checksum
        elif self.checksum != calculated_checksum:
            raise ValueError(f"Checksum mismatch for artifact {self.name}")
        
        # Validate permissions format
        if self.permissions and not self._is_valid_permissions(self.permissions):
            raise ValueError(f"Invalid permissions format: {self.permissions}")
        
        # Set default permissions if not provided
        if not self.permissions:
            self.permissions = "0755" if self.type == ArtifactType.SCRIPT else "0644"
    
    def _is_valid_permissions(self, permissions: str) -> bool:
        """Validate Unix permissions format"""
        if not permissions:
            return False
        
        # Check octal format (e.g., "0755")
        if len(permissions) == 4 and permissions.startswith('0'):
            try:
                int(permissions, 8)
                return True
            except ValueError:
                return False
        
        # Check symbolic format (e.g., "rwxr-xr-x")
        if len(permissions) == 9:
            valid_chars = set('rwx-')
            return all(c in valid_chars for c in permissions)
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert artifact to dictionary representation"""
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "type": self.type.value,
            "checksum": self.checksum,
            "permissions": self.permissions,
            "target_path": self.target_path,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], content: bytes) -> 'TestArtifact':
        """Create artifact from dictionary representation"""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        return cls(
            artifact_id=data["artifact_id"],
            name=data["name"],
            type=ArtifactType(data["type"]),
            content=content,
            checksum=data["checksum"],
            permissions=data["permissions"],
            target_path=data["target_path"],
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            created_at=created_at
        )


@dataclass
class Dependency:
    """Represents a dependency to be installed"""
    name: str
    version: Optional[str] = None
    package_manager: str = "apt"  # apt, pip, yum, etc.
    install_command: Optional[str] = None
    verify_command: Optional[str] = None


@dataclass
class InstrumentationConfig:
    """Configuration for environment instrumentation"""
    enable_kasan: bool = False
    enable_ktsan: bool = False
    enable_lockdep: bool = False
    enable_coverage: bool = False
    enable_profiling: bool = False
    enable_fuzzing: bool = False
    custom_kernel_params: List[str] = field(default_factory=list)
    monitoring_tools: List[str] = field(default_factory=list)


@dataclass
class DeploymentConfig:
    """Configuration for deployment process"""
    timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    parallel_deployments: bool = True
    validate_checksums: bool = True
    cleanup_on_failure: bool = True


@dataclass
class DeploymentPlan:
    """Represents a complete deployment plan"""
    plan_id: str
    environment_id: str
    test_artifacts: List[TestArtifact]
    dependencies: List[Dependency]
    instrumentation_config: InstrumentationConfig
    deployment_config: DeploymentConfig
    created_at: datetime
    status: DeploymentStatus = DeploymentStatus.PENDING
    
    def __post_init__(self):
        """Validate deployment plan after initialization"""
        if not self.plan_id:
            raise ValueError("plan_id is required")
        if not self.environment_id:
            raise ValueError("environment_id is required")
        if not self.test_artifacts:
            raise ValueError("At least one test artifact is required")


@dataclass
class DeploymentStep:
    """Represents a single deployment step"""
    step_id: str
    name: str
    status: DeploymentStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate step duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    deployment_id: str
    plan_id: str
    environment_id: str
    status: DeploymentStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[DeploymentStep] = field(default_factory=list)
    error_message: Optional[str] = None
    artifacts_deployed: int = 0
    dependencies_installed: int = 0
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate total deployment duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_successful(self) -> bool:
        """Check if deployment was successful"""
        return self.status == DeploymentStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if deployment failed"""
        return self.status == DeploymentStatus.FAILED


@dataclass
class ValidationResult:
    """Result of environment readiness validation"""
    environment_id: str
    is_ready: bool
    checks_performed: List[str]
    failed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Dependency:
    """
    Represents a dependency to be installed.
    
    Enhanced with version constraints and installation options.
    """
    name: str
    version: Optional[str] = None
    version_constraint: Optional[str] = None  # e.g., ">=1.0.0", "~=2.1.0"
    package_manager: str = "apt"  # apt, pip, yum, dnf, pacman, etc.
    install_command: Optional[str] = None
    verify_command: Optional[str] = None
    optional: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate dependency after creation"""
        if not self.name:
            raise ValueError("Dependency name is required")
        
        # Generate install command if not provided
        if not self.install_command:
            self.install_command = self._generate_install_command()
        
        # Generate verify command if not provided
        if not self.verify_command:
            self.verify_command = self._generate_verify_command()
    
    def _generate_install_command(self) -> str:
        """Generate installation command based on package manager"""
        version_spec = f"={self.version}" if self.version else ""
        
        if self.package_manager == "apt":
            return f"apt-get install -y {self.name}{version_spec}"
        elif self.package_manager == "pip":
            return f"pip install {self.name}{version_spec}"
        elif self.package_manager == "yum":
            return f"yum install -y {self.name}{version_spec}"
        elif self.package_manager == "dnf":
            return f"dnf install -y {self.name}{version_spec}"
        else:
            return f"{self.package_manager} install {self.name}{version_spec}"
    
    def _generate_verify_command(self) -> str:
        """Generate verification command"""
        if self.package_manager == "pip":
            return f"pip show {self.name}"
        elif self.package_manager in ["apt", "yum", "dnf"]:
            return f"which {self.name} || dpkg -l {self.name} || rpm -q {self.name}"
        else:
            return f"which {self.name}"


@dataclass
class InstrumentationConfig:
    """
    Configuration for environment instrumentation.
    
    Enhanced with detailed tool configurations and validation.
    """
    enable_kasan: bool = False
    enable_ktsan: bool = False
    enable_lockdep: bool = False
    enable_coverage: bool = False
    enable_profiling: bool = False
    enable_fuzzing: bool = False
    custom_kernel_params: List[str] = field(default_factory=list)
    monitoring_tools: List[str] = field(default_factory=list)
    
    # Detailed configurations
    kasan_config: Dict[str, Any] = field(default_factory=dict)
    coverage_config: Dict[str, Any] = field(default_factory=dict)
    profiling_config: Dict[str, Any] = field(default_factory=dict)
    fuzzing_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set default configurations"""
        if self.enable_coverage and not self.coverage_config:
            self.coverage_config = {
                "gcov_enabled": True,
                "lcov_enabled": True,
                "output_dir": "/tmp/coverage"
            }
        
        if self.enable_profiling and not self.profiling_config:
            self.profiling_config = {
                "perf_enabled": True,
                "ftrace_enabled": True,
                "sample_rate": 1000
            }
    
    @property
    def has_any_instrumentation(self) -> bool:
        """Check if any instrumentation is enabled"""
        return any([
            self.enable_kasan, self.enable_ktsan, self.enable_lockdep,
            self.enable_coverage, self.enable_profiling, self.enable_fuzzing
        ])
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled instrumentation tools"""
        tools = []
        if self.enable_kasan:
            tools.append("KASAN")
        if self.enable_ktsan:
            tools.append("KTSAN")
        if self.enable_lockdep:
            tools.append("LOCKDEP")
        if self.enable_coverage:
            tools.append("Coverage")
        if self.enable_profiling:
            tools.append("Profiling")
        if self.enable_fuzzing:
            tools.append("Fuzzing")
        
        return tools


@dataclass
class DeploymentConfig:
    """
    Configuration for deployment process.
    
    Enhanced with comprehensive deployment options and validation.
    """
    timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    retry_backoff_multiplier: float = 2.0
    parallel_deployments: bool = True
    validate_checksums: bool = True
    cleanup_on_failure: bool = True
    preserve_permissions: bool = True
    create_backup: bool = False
    priority: Priority = Priority.NORMAL
    
    # Advanced options
    connection_timeout: int = 30
    transfer_timeout: int = 120
    max_transfer_size_mb: int = 100
    compression_enabled: bool = True
    encryption_enabled: bool = False
    
    def __post_init__(self):
        """Validate configuration after creation"""
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts cannot be negative")
        
        if self.retry_delay_seconds < 0:
            raise ValueError("Retry delay cannot be negative")
        
        if self.max_transfer_size_mb <= 0:
            raise ValueError("Max transfer size must be positive")
    
    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff"""
        if attempt <= 0:
            return 0
        
        delay = self.retry_delay_seconds * (self.retry_backoff_multiplier ** (attempt - 1))
        return min(delay, 60)  # Cap at 60 seconds


@dataclass
class DeploymentPlan:
    """
    Represents a complete deployment plan.
    
    Enhanced with validation, state tracking, and metadata.
    """
    plan_id: str
    environment_id: str
    test_artifacts: List[TestArtifact]
    dependencies: List[Dependency]
    instrumentation_config: InstrumentationConfig
    deployment_config: DeploymentConfig
    created_at: datetime
    status: DeploymentStatus = DeploymentStatus.PENDING
    
    # Additional metadata
    created_by: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    estimated_duration_seconds: Optional[int] = None
    
    def __post_init__(self):
        """Validate deployment plan after initialization"""
        if not self.plan_id:
            self.plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        
        if not self.environment_id:
            raise ValueError("environment_id is required")
        
        if not self.test_artifacts:
            raise ValueError("At least one test artifact is required")
        
        # Estimate duration if not provided
        if not self.estimated_duration_seconds:
            self.estimated_duration_seconds = self._estimate_duration()
    
    def _estimate_duration(self) -> int:
        """Estimate deployment duration based on artifacts and configuration"""
        base_time = 30  # Base deployment time in seconds
        
        # Add time based on number of artifacts
        artifact_time = len(self.test_artifacts) * 5
        
        # Add time based on dependencies
        dependency_time = len(self.dependencies) * 10
        
        # Add time for instrumentation
        instrumentation_time = 0
        if self.instrumentation_config.has_any_instrumentation:
            instrumentation_time = 30
        
        # Add time based on total artifact size
        total_size_mb = sum(artifact.size_bytes or 0 for artifact in self.test_artifacts) / (1024 * 1024)
        size_time = int(total_size_mb * 2)  # 2 seconds per MB
        
        return base_time + artifact_time + dependency_time + instrumentation_time + size_time
    
    @property
    def total_artifact_size(self) -> int:
        """Get total size of all artifacts in bytes"""
        return sum(artifact.size_bytes or 0 for artifact in self.test_artifacts)
    
    @property
    def artifact_count_by_type(self) -> Dict[str, int]:
        """Get count of artifacts by type"""
        counts = {}
        for artifact in self.test_artifacts:
            artifact_type = artifact.type.value
            counts[artifact_type] = counts.get(artifact_type, 0) + 1
        return counts
    
    def validate(self) -> List[str]:
        """
        Validate the deployment plan and return list of validation errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate artifacts
        for i, artifact in enumerate(self.test_artifacts):
            try:
                # Check for duplicate artifact IDs
                artifact_ids = [a.artifact_id for a in self.test_artifacts]
                if artifact_ids.count(artifact.artifact_id) > 1:
                    errors.append(f"Duplicate artifact ID: {artifact.artifact_id}")
                
                # Validate artifact content
                if not artifact.content:
                    errors.append(f"Artifact {artifact.name} has no content")
                
                # Check artifact size limits
                max_size = self.deployment_config.max_transfer_size_mb * 1024 * 1024
                if artifact.size_bytes and artifact.size_bytes > max_size:
                    errors.append(f"Artifact {artifact.name} exceeds size limit")
                
            except Exception as e:
                errors.append(f"Artifact {i} validation error: {e}")
        
        # Validate dependencies
        for i, dependency in enumerate(self.dependencies):
            if not dependency.name:
                errors.append(f"Dependency {i} has no name")
        
        # Validate configuration
        if self.deployment_config.timeout_seconds < self.estimated_duration_seconds:
            errors.append("Deployment timeout is less than estimated duration")
        
        return errors


@dataclass
class DeploymentStep:
    """
    Represents a single deployment step.
    
    Enhanced with detailed progress tracking and error handling.
    """
    step_id: str
    name: str
    status: DeploymentStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    progress_percentage: float = 0.0
    retry_count: int = 0
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate step duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if step is completed"""
        return self.status == DeploymentStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if step failed"""
        return self.status == DeploymentStatus.FAILED
    
    def mark_started(self):
        """Mark step as started"""
        self.start_time = datetime.now()
        self.status = DeploymentStatus.PREPARING
    
    def mark_completed(self):
        """Mark step as completed"""
        self.end_time = datetime.now()
        self.status = DeploymentStatus.COMPLETED
        self.progress_percentage = 100.0
    
    def mark_failed(self, error_message: str):
        """Mark step as failed"""
        self.end_time = datetime.now()
        self.status = DeploymentStatus.FAILED
        self.error_message = error_message


@dataclass
class DeploymentResult:
    """
    Result of a deployment operation.
    
    Enhanced with comprehensive metrics and analysis.
    """
    deployment_id: str
    plan_id: str
    environment_id: str
    status: DeploymentStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[DeploymentStep] = field(default_factory=list)
    error_message: Optional[str] = None
    artifacts_deployed: int = 0
    dependencies_installed: int = 0
    
    # Performance metrics
    total_transfer_bytes: int = 0
    average_transfer_speed_mbps: float = 0.0
    retry_count: int = 0
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate total deployment duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_successful(self) -> bool:
        """Check if deployment was successful"""
        return self.status == DeploymentStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if deployment failed"""
        return self.status == DeploymentStatus.FAILED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if deployment was cancelled"""
        return self.status == DeploymentStatus.CANCELLED
    
    @property
    def completion_percentage(self) -> float:
        """Calculate overall completion percentage"""
        if not self.steps:
            return 0.0
        
        if self.is_successful:
            return 100.0
        
        completed_steps = sum(1 for step in self.steps if step.is_completed)
        return (completed_steps / len(self.steps)) * 100.0


@dataclass
class ValidationResult:
    """
    Result of environment readiness validation.
    
    Enhanced with detailed validation information and recommendations.
    """
    environment_id: str
    is_ready: bool
    checks_performed: List[str]
    failed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def success_rate(self) -> float:
        """Calculate validation success rate"""
        if not self.checks_performed:
            return 0.0
        
        failed_count = len(self.failed_checks)
        total_count = len(self.checks_performed)
        return ((total_count - failed_count) / total_count) * 100.0
    
    @property
    def has_failures(self) -> bool:
        """Check if there are any failed checks"""
        return len(self.failed_checks) > 0