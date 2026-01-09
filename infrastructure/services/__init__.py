"""
Infrastructure Services

This module contains all service classes for managing infrastructure resources.
"""

from infrastructure.services.build_server_service import BuildServerManagementService
from infrastructure.services.build_job_manager import BuildJobManager
from infrastructure.services.artifact_manager import ArtifactRepositoryManager
from infrastructure.services.host_service import HostManagementService
from infrastructure.services.board_service import BoardManagementService
from infrastructure.services.deployment_manager import (
    DeploymentManager,
    VMConfig,
    DeploymentResult,
    DeploymentStatusResult,
    VerificationResult,
    RollbackResult,
)
from infrastructure.services.health_monitor import (
    HealthMonitorService,
    HealthCheckResult,
    HealthRecord,
    HealthThresholds,
    HealthStatus,
    ResourceType,
    TimeRange,
)
from infrastructure.services.alert_service import (
    AlertService,
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertCategory,
    AlertRule,
    NotificationChannel,
    NotificationConfig,
)
from infrastructure.services.resource_group_manager import (
    ResourceGroupManager,
    ResourceGroup,
    ResourceType as GroupResourceType,
    AllocationPolicy,
    GroupStatistics,
    AllocationResult,
    Allocation,
)
from infrastructure.services.pipeline_manager import (
    PipelineManager,
    Pipeline,
    PipelineConfig,
    PipelineStage,
    PipelineStatus,
    StageStatus,
    StageType,
    EnvironmentType,
    PipelineResult,
    CancelResult as PipelineCancelResult,
    PipelineFilters,
)

__all__ = [
    # Build Server Management
    "BuildServerManagementService",
    "BuildJobManager",
    "ArtifactRepositoryManager",
    # Host and Board Management
    "HostManagementService",
    "BoardManagementService",
    # Deployment
    "DeploymentManager",
    "VMConfig",
    "DeploymentResult",
    "DeploymentStatusResult",
    "VerificationResult",
    "RollbackResult",
    # Health Monitoring
    "HealthMonitorService",
    "HealthCheckResult",
    "HealthRecord",
    "HealthThresholds",
    "HealthStatus",
    "ResourceType",
    "TimeRange",
    # Alerting
    "AlertService",
    "Alert",
    "AlertSeverity",
    "AlertStatus",
    "AlertCategory",
    "AlertRule",
    "NotificationChannel",
    "NotificationConfig",
    # Resource Groups
    "ResourceGroupManager",
    "ResourceGroup",
    "GroupResourceType",
    "AllocationPolicy",
    "GroupStatistics",
    "AllocationResult",
    "Allocation",
    # Pipeline Management
    "PipelineManager",
    "Pipeline",
    "PipelineConfig",
    "PipelineStage",
    "PipelineStatus",
    "StageStatus",
    "StageType",
    "EnvironmentType",
    "PipelineResult",
    "PipelineCancelResult",
    "PipelineFilters",
]
