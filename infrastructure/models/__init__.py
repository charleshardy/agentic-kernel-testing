"""
Infrastructure Data Models

This module contains all data models for the test infrastructure management system.
"""

from infrastructure.models.build_server import (
    BuildServer,
    BuildServerStatus,
    BuildServerCapacity,
    Toolchain,
    BuildJob,
    BuildJobStatus,
    BuildConfig,
    BuildRequirements,
    BuildServerSelectionResult,
)

from infrastructure.models.artifact import (
    Artifact,
    ArtifactType,
    ArtifactSelection,
)

from infrastructure.models.host import (
    Host,
    HostStatus,
    HostCapacity,
    ResourceUtilization,
    VMRequirements,
    HostSelectionResult,
)

from infrastructure.models.board import (
    Board,
    BoardStatus,
    BoardHealth,
    PowerControlConfig,
    PowerControlMethod,
    HealthLevel,
    BoardRequirements,
    BoardSelectionResult,
)

from infrastructure.models.resource_group import (
    ResourceGroup,
    ResourceType,
    AllocationPolicy,
)

from infrastructure.models.deployment import (
    Deployment,
    DeploymentTargetType,
    DeploymentStatus,
)

from infrastructure.models.pipeline import (
    Pipeline,
    PipelineStatus,
    PipelineStage,
    StageStatus,
    EnvironmentType,
)

from infrastructure.models.health import (
    HealthThresholds,
    HealthCheckResult,
    HealthRecord,
)

__all__ = [
    # Build Server Models
    "BuildServer",
    "BuildServerStatus",
    "BuildServerCapacity",
    "Toolchain",
    "BuildJob",
    "BuildJobStatus",
    "BuildConfig",
    "BuildRequirements",
    "BuildServerSelectionResult",
    # Artifact Models
    "Artifact",
    "ArtifactType",
    "ArtifactSelection",
    # Host Models
    "Host",
    "HostStatus",
    "HostCapacity",
    "ResourceUtilization",
    "VMRequirements",
    "HostSelectionResult",
    # Board Models
    "Board",
    "BoardStatus",
    "BoardHealth",
    "PowerControlConfig",
    "PowerControlMethod",
    "HealthLevel",
    "BoardRequirements",
    "BoardSelectionResult",
    # Resource Group Models
    "ResourceGroup",
    "ResourceType",
    "AllocationPolicy",
    # Deployment Models
    "Deployment",
    "DeploymentTargetType",
    "DeploymentStatus",
    # Pipeline Models
    "Pipeline",
    "PipelineStatus",
    "PipelineStage",
    "StageStatus",
    "EnvironmentType",
    # Health Models
    "HealthThresholds",
    "HealthCheckResult",
    "HealthRecord",
]
