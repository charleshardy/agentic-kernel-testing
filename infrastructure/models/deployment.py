"""
Deployment Data Models

Models for deploying build artifacts to test environments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class DeploymentTargetType(Enum):
    """Type of deployment target."""
    QEMU_HOST = "qemu_host"
    PHYSICAL_BOARD = "physical_board"


class DeploymentStatus(Enum):
    """Status of a deployment."""
    PENDING = "pending"
    TRANSFERRING = "transferring"
    FLASHING = "flashing"
    BOOTING = "booting"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Deployment:
    """A deployment of build artifacts to a test environment."""
    id: str
    target_type: DeploymentTargetType
    target_id: str  # host_id or board_id
    artifacts: List[str]  # artifact IDs
    build_id: str
    created_at: datetime
    status: DeploymentStatus = DeploymentStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    boot_verified: bool = False
    error_message: Optional[str] = None

    def is_active(self) -> bool:
        """Check if deployment is currently active."""
        return self.status in (
            DeploymentStatus.PENDING,
            DeploymentStatus.TRANSFERRING,
            DeploymentStatus.FLASHING,
            DeploymentStatus.BOOTING,
            DeploymentStatus.VERIFYING
        )

    def is_completed(self) -> bool:
        """Check if deployment has completed (success or failure)."""
        return self.status in (
            DeploymentStatus.COMPLETED,
            DeploymentStatus.FAILED,
            DeploymentStatus.ROLLED_BACK
        )

    def is_successful(self) -> bool:
        """Check if deployment completed successfully."""
        return self.status == DeploymentStatus.COMPLETED and self.boot_verified

    def can_rollback(self) -> bool:
        """Check if deployment can be rolled back."""
        return self.status in (
            DeploymentStatus.COMPLETED,
            DeploymentStatus.FAILED,
            DeploymentStatus.VERIFYING
        )
