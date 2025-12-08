"""Data models for build system integration."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import json


class BuildStatus(str, Enum):
    """Build status states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class BuildType(str, Enum):
    """Types of builds."""
    KERNEL = "kernel"
    BSP = "bsp"
    MODULE = "module"
    FULL_SYSTEM = "full_system"


class BuildSystem(str, Enum):
    """Supported build systems."""
    JENKINS = "jenkins"
    GITLAB_CI = "gitlab_ci"
    GITHUB_ACTIONS = "github_actions"
    CUSTOM = "custom"


@dataclass
class BuildArtifact:
    """Build artifact information."""
    name: str
    path: str
    artifact_type: str  # kernel_image, bsp_package, module, config
    size_bytes: int
    checksum: str
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BuildArtifact':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class KernelImage:
    """Kernel image information."""
    version: str
    architecture: str
    image_path: str
    config_path: Optional[str] = None
    modules_path: Optional[str] = None
    build_timestamp: datetime = field(default_factory=datetime.now)
    commit_sha: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['build_timestamp'] = self.build_timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KernelImage':
        """Create from dictionary."""
        timestamp = datetime.fromisoformat(data.pop('build_timestamp'))
        return cls(**data, build_timestamp=timestamp)


@dataclass
class BSPPackage:
    """BSP package information."""
    name: str
    version: str
    target_board: str
    architecture: str
    package_path: str
    kernel_version: Optional[str] = None
    build_timestamp: datetime = field(default_factory=datetime.now)
    commit_sha: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['build_timestamp'] = self.build_timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BSPPackage':
        """Create from dictionary."""
        timestamp = datetime.fromisoformat(data.pop('build_timestamp'))
        return cls(**data, build_timestamp=timestamp)


@dataclass
class BuildInfo:
    """Build information."""
    build_id: str
    build_number: int
    build_system: BuildSystem
    build_type: BuildType
    status: BuildStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    artifacts: List[BuildArtifact] = field(default_factory=list)
    kernel_image: Optional[KernelImage] = None
    bsp_package: Optional[BSPPackage] = None
    build_log_url: Optional[str] = None
    triggered_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate build info."""
        if not self.build_id:
            raise ValueError("build_id cannot be empty")
        if isinstance(self.build_system, str):
            self.build_system = BuildSystem(self.build_system)
        if isinstance(self.build_type, str):
            self.build_type = BuildType(self.build_type)
        if isinstance(self.status, str):
            self.status = BuildStatus(self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['build_system'] = self.build_system.value
        data['build_type'] = self.build_type.value
        data['status'] = self.status.value
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['artifacts'] = [a.to_dict() for a in self.artifacts]
        if self.kernel_image:
            data['kernel_image'] = self.kernel_image.to_dict()
        if self.bsp_package:
            data['bsp_package'] = self.bsp_package.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BuildInfo':
        """Create from dictionary."""
        start_time = datetime.fromisoformat(data.pop('start_time'))
        end_time_str = data.pop('end_time', None)
        end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
        
        artifacts_data = data.pop('artifacts', [])
        artifacts = [BuildArtifact.from_dict(a) for a in artifacts_data]
        
        kernel_data = data.pop('kernel_image', None)
        kernel_image = KernelImage.from_dict(kernel_data) if kernel_data else None
        
        bsp_data = data.pop('bsp_package', None)
        bsp_package = BSPPackage.from_dict(bsp_data) if bsp_data else None
        
        return cls(
            **data,
            start_time=start_time,
            end_time=end_time,
            artifacts=artifacts,
            kernel_image=kernel_image,
            bsp_package=bsp_package
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BuildInfo':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class BuildEvent:
    """Build system event."""
    event_id: str
    build_system: BuildSystem
    build_info: BuildInfo
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate build event."""
        if not self.event_id:
            raise ValueError("event_id cannot be empty")
        if isinstance(self.build_system, str):
            self.build_system = BuildSystem(self.build_system)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['build_system'] = self.build_system.value
        data['build_info'] = self.build_info.to_dict()
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BuildEvent':
        """Create from dictionary."""
        build_info_data = data.pop('build_info')
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        build_info = BuildInfo.from_dict(build_info_data)
        return cls(**data, build_info=build_info, timestamp=timestamp)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BuildEvent':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
