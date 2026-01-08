"""
Build Artifact Data Models

Models for managing build artifacts (kernel images, rootfs, device trees, etc.).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class ArtifactType(Enum):
    """Type of build artifact."""
    KERNEL_IMAGE = "kernel_image"
    INITRD = "initrd"
    ROOTFS = "rootfs"
    DEVICE_TREE = "device_tree"
    KERNEL_MODULES = "kernel_modules"
    BUILD_LOG = "build_log"


@dataclass
class Artifact:
    """A build artifact stored in the repository."""
    id: str
    build_id: str
    artifact_type: ArtifactType
    filename: str
    path: str
    size_bytes: int
    checksum_sha256: str
    architecture: str
    created_at: datetime
    metadata: Dict[str, str] = field(default_factory=dict)

    def matches_architecture(self, arch: str) -> bool:
        """Check if artifact matches the given architecture."""
        return self.architecture.lower() == arch.lower()

    def verify_checksum(self, computed_checksum: str) -> bool:
        """Verify the artifact checksum."""
        return self.checksum_sha256 == computed_checksum


@dataclass
class ArtifactSelection:
    """Criteria for selecting build artifacts."""
    build_id: Optional[str] = None
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    use_latest: bool = False
    architecture: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if selection criteria is valid (at least one selector specified)."""
        return bool(
            self.build_id or
            self.commit_hash or
            (self.branch and self.use_latest)
        )
