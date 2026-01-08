"""
Pipeline Data Models

Models for end-to-end build and test pipelines.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EnvironmentType(Enum):
    """Type of test environment."""
    QEMU = "qemu"
    PHYSICAL_BOARD = "physical_board"


class PipelineStatus(Enum):
    """Status of a pipeline."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(Enum):
    """Status of a pipeline stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineStage:
    """A stage in a pipeline."""
    name: str  # build, deploy, boot, test
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    output_id: Optional[str] = None  # build_id, deployment_id, etc.
    error_message: Optional[str] = None

    def is_active(self) -> bool:
        """Check if stage is currently active."""
        return self.status == StageStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if stage has completed (success or failure)."""
        return self.status in (StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.SKIPPED)

    def is_successful(self) -> bool:
        """Check if stage completed successfully."""
        return self.status == StageStatus.COMPLETED

    def can_start(self) -> bool:
        """Check if stage can be started."""
        return self.status == StageStatus.PENDING


@dataclass
class Pipeline:
    """An end-to-end build and test pipeline."""
    id: str
    source_repository: str
    branch: str
    commit_hash: str
    target_architecture: str
    environment_type: EnvironmentType
    created_at: datetime
    name: Optional[str] = None
    environment_config: Dict[str, Any] = field(default_factory=dict)
    stages: List[PipelineStage] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Initialize default stages if not provided."""
        if not self.stages:
            self.stages = [
                PipelineStage(name="build"),
                PipelineStage(name="deploy"),
                PipelineStage(name="boot"),
                PipelineStage(name="test"),
            ]

    def get_stage(self, name: str) -> Optional[PipelineStage]:
        """Get a stage by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def get_current_stage(self) -> Optional[PipelineStage]:
        """Get the currently running stage."""
        if self.current_stage:
            return self.get_stage(self.current_stage)
        return None

    def get_next_stage(self) -> Optional[PipelineStage]:
        """Get the next stage to run."""
        for stage in self.stages:
            if stage.status == StageStatus.PENDING:
                return stage
        return None

    def is_active(self) -> bool:
        """Check if pipeline is currently active."""
        return self.status in (PipelineStatus.PENDING, PipelineStatus.RUNNING)

    def is_completed(self) -> bool:
        """Check if pipeline has completed."""
        return self.status in (
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED
        )

    def is_successful(self) -> bool:
        """Check if pipeline completed successfully."""
        return self.status == PipelineStatus.COMPLETED

    def all_stages_completed(self) -> bool:
        """Check if all stages have completed."""
        return all(stage.is_completed() for stage in self.stages)

    def any_stage_failed(self) -> bool:
        """Check if any stage has failed."""
        return any(stage.status == StageStatus.FAILED for stage in self.stages)
