"""
Test Infrastructure Host Management Module

This module provides a unified interface for managing the complete test infrastructure lifecycle:
- Build Servers: Hosts that compile kernel/BSP source code into deployable artifacts
- QEMU Hosts: Physical servers that run QEMU virtual machines for virtualized testing
- Physical Test Boards: Real hardware devices for native kernel and BSP testing

The system enables registration, monitoring, selection, and lifecycle management of all
infrastructure resources, providing an end-to-end pipeline from source code compilation
through deployment and test execution.
"""

from infrastructure.models import (
    # Build Server Models
    BuildServer,
    BuildServerStatus,
    BuildServerCapacity,
    Toolchain,
    BuildJob,
    BuildJobStatus,
    BuildConfig,
    BuildRequirements,
    BuildServerSelectionResult,
    # Artifact Models
    Artifact,
    ArtifactType,
    ArtifactSelection,
    # Host Models
    Host,
    HostStatus,
    HostCapacity,
    ResourceUtilization,
    # Board Models
    Board,
    BoardStatus,
    BoardHealth,
    PowerControlConfig,
    PowerControlMethod,
    HealthLevel,
    # Selection Models
    VMRequirements,
    BoardRequirements,
    HostSelectionResult,
    BoardSelectionResult,
    # Resource Group Models
    ResourceGroup,
    ResourceType,
    AllocationPolicy,
    # Deployment Models
    Deployment,
    DeploymentTargetType,
    DeploymentStatus,
    # Pipeline Models
    Pipeline,
    PipelineStatus,
    PipelineStage,
    StageStatus,
    EnvironmentType,
    # Health Models
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
    # Board Models
    "Board",
    "BoardStatus",
    "BoardHealth",
    "PowerControlConfig",
    "PowerControlMethod",
    "HealthLevel",
    # Selection Models
    "VMRequirements",
    "BoardRequirements",
    "HostSelectionResult",
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

__version__ = "0.1.0"
