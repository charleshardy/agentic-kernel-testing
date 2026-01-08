"""
Health Monitoring Data Models

Models for health monitoring and alerting.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from infrastructure.models.board import HealthLevel


class AlertSeverity(Enum):
    """Severity level of an alert."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status of an alert."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class HealthThresholds:
    """Thresholds for health monitoring."""
    cpu_warning_percent: float = 75.0
    cpu_critical_percent: float = 90.0
    memory_warning_percent: float = 80.0
    memory_critical_percent: float = 95.0
    storage_warning_percent: float = 80.0
    storage_critical_percent: float = 95.0
    disk_space_warning_gb: float = 10.0
    disk_space_critical_gb: float = 5.0
    temperature_warning_celsius: float = 70.0
    temperature_critical_celsius: float = 85.0
    response_time_warning_ms: int = 5000
    response_time_critical_ms: int = 10000
    unreachable_timeout_seconds: int = 30

    def get_cpu_level(self, percent: float) -> HealthLevel:
        """Get health level based on CPU usage."""
        if percent >= self.cpu_critical_percent:
            return HealthLevel.UNHEALTHY
        elif percent >= self.cpu_warning_percent:
            return HealthLevel.DEGRADED
        return HealthLevel.HEALTHY

    def get_memory_level(self, percent: float) -> HealthLevel:
        """Get health level based on memory usage."""
        if percent >= self.memory_critical_percent:
            return HealthLevel.UNHEALTHY
        elif percent >= self.memory_warning_percent:
            return HealthLevel.DEGRADED
        return HealthLevel.HEALTHY

    def get_storage_level(self, percent: float) -> HealthLevel:
        """Get health level based on storage usage."""
        if percent >= self.storage_critical_percent:
            return HealthLevel.UNHEALTHY
        elif percent >= self.storage_warning_percent:
            return HealthLevel.DEGRADED
        return HealthLevel.HEALTHY


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    resource_id: str
    resource_type: str
    timestamp: datetime
    is_healthy: bool
    health_level: HealthLevel = HealthLevel.UNKNOWN
    response_time_ms: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    storage_percent: Optional[float] = None
    temperature_celsius: Optional[float] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthRecord:
    """Historical health record."""
    id: str
    resource_id: str
    resource_type: str
    timestamp: datetime
    health_level: HealthLevel
    metrics: Dict[str, float] = field(default_factory=dict)
    notes: Optional[str] = None


@dataclass
class Alert:
    """An infrastructure alert."""
    id: str
    resource_id: str
    resource_type: str
    severity: AlertSeverity
    title: str
    message: str
    created_at: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def acknowledge(self, user: str) -> None:
        """Acknowledge the alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user

    def resolve(self, user: str) -> None:
        """Resolve the alert."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user

    def is_active(self) -> bool:
        """Check if alert is still active."""
        return self.status == AlertStatus.ACTIVE
