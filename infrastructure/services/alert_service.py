"""
Alert Service

Generates and manages alerts for infrastructure resource issues.

**Feature: test-infrastructure-management**
**Validates: Requirements 16.1-16.5**
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from uuid import uuid4

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertCategory(Enum):
    """Categories of alerts."""
    CONNECTIVITY = "connectivity"
    RESOURCE_UTILIZATION = "resource_utilization"
    HEALTH = "health"
    PROVISIONING = "provisioning"
    DEPLOYMENT = "deployment"
    BUILD = "build"
    POWER = "power"
    TEMPERATURE = "temperature"


class NotificationChannel(Enum):
    """Notification channels."""
    DASHBOARD = "dashboard"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"


@dataclass
class Alert:
    """Represents an infrastructure alert."""
    id: str
    resource_id: str
    resource_type: str
    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    notification_sent: Dict[str, bool] = field(default_factory=dict)
    auto_recovery_attempted: bool = False
    recovery_successful: bool = False


@dataclass
class NotificationConfig:
    """Configuration for a notification channel."""
    channel: NotificationChannel
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    # Email config: {"recipients": ["admin@example.com"], "smtp_server": "..."}
    # Webhook config: {"url": "https://...", "headers": {...}}
    # Slack config: {"webhook_url": "https://hooks.slack.com/..."}


@dataclass
class AlertRule:
    """Rule for generating alerts."""
    id: str
    name: str
    description: str
    category: AlertCategory
    severity: AlertSeverity
    condition: str  # Description of condition
    enabled: bool = True
    cooldown_seconds: int = 300  # Minimum time between alerts
    auto_resolve_seconds: Optional[int] = None  # Auto-resolve after this time
    notification_channels: List[NotificationChannel] = field(default_factory=list)


class AlertService:
    """
    Manages alerts for infrastructure resources.
    
    Provides alert generation, notification, acknowledgment, and resolution
    tracking for all infrastructure issues.
    
    **Requirement 16.1**: Generate alerts within 30 seconds of resource issues
    **Requirement 16.5**: Support dashboard, email, and webhook notifications
    """
    
    # Maximum time to generate alert after issue detection (Requirement 16.1)
    MAX_ALERT_GENERATION_TIME_SECONDS = 30
    
    def __init__(self):
        """Initialize the alert service."""
        # Active alerts by ID
        self._alerts: Dict[str, Alert] = {}
        
        # Alert history (resolved alerts)
        self._alert_history: List[Alert] = []
        self._max_history = 10000
        
        # Notification configurations
        self._notification_configs: Dict[NotificationChannel, NotificationConfig] = {}
        
        # Alert rules
        self._alert_rules: Dict[str, AlertRule] = {}
        
        # Cooldown tracking (resource_id -> last alert time)
        self._cooldowns: Dict[str, Dict[AlertCategory, datetime]] = {}
        
        # Notification handlers
        self._notification_handlers: Dict[NotificationChannel, Callable[[Alert], Awaitable[bool]]] = {}
        
        # Alert generation timestamp tracking for timing validation
        self._alert_generation_times: Dict[str, datetime] = {}
        
        # Initialize default notification config
        self._notification_configs[NotificationChannel.DASHBOARD] = NotificationConfig(
            channel=NotificationChannel.DASHBOARD,
            enabled=True
        )
    
    def configure_notification(self, config: NotificationConfig) -> None:
        """
        Configure a notification channel.
        
        Args:
            config: Notification configuration
        """
        self._notification_configs[config.channel] = config
        logger.info(f"Configured notification channel: {config.channel.value}")
    
    def register_notification_handler(
        self,
        channel: NotificationChannel,
        handler: Callable[[Alert], Awaitable[bool]]
    ) -> None:
        """
        Register a handler for a notification channel.
        
        Args:
            channel: Notification channel
            handler: Async handler function that returns True on success
        """
        self._notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for: {channel.value}")
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self._alert_rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        if rule_id in self._alert_rules:
            del self._alert_rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
            return True
        return False
    
    async def generate_alert(
        self,
        resource_id: str,
        resource_type: str,
        severity: AlertSeverity,
        category: AlertCategory,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        issue_detected_at: Optional[datetime] = None
    ) -> Alert:
        """
        Generate a new alert.
        
        **Requirement 16.1**: Alert SHALL be generated within 30 seconds
        
        Args:
            resource_id: ID of the affected resource
            resource_type: Type of resource (build_server, qemu_host, physical_board)
            severity: Alert severity
            category: Alert category
            title: Alert title
            message: Alert message
            metadata: Additional metadata
            issue_detected_at: When the issue was first detected
            
        Returns:
            Generated Alert
        """
        now = datetime.now(timezone.utc)
        
        # Track alert generation timing for Property 23 validation
        if issue_detected_at:
            generation_delay = (now - issue_detected_at).total_seconds()
            if generation_delay > self.MAX_ALERT_GENERATION_TIME_SECONDS:
                logger.warning(
                    f"Alert generation exceeded {self.MAX_ALERT_GENERATION_TIME_SECONDS}s limit: "
                    f"{generation_delay:.2f}s for resource {resource_id}"
                )
        
        # Check cooldown
        if self._is_in_cooldown(resource_id, category):
            # Find existing active alert for this resource/category
            existing = self._find_active_alert(resource_id, category)
            if existing:
                logger.debug(f"Alert in cooldown for {resource_id}/{category.value}")
                return existing
        
        # Create new alert
        alert = Alert(
            id=str(uuid4()),
            resource_id=resource_id,
            resource_type=resource_type,
            severity=severity,
            category=category,
            title=title,
            message=message,
            metadata=metadata or {},
            created_at=now,
            updated_at=now
        )
        
        # Store alert
        self._alerts[alert.id] = alert
        
        # Update cooldown
        self._update_cooldown(resource_id, category, now)
        
        # Track generation time
        self._alert_generation_times[alert.id] = now
        
        logger.info(f"Generated alert: {alert.id} - {title} for {resource_id}")
        
        # Send notifications
        await self._send_notifications(alert)
        
        return alert
    
    async def generate_connectivity_alert(
        self,
        resource_id: str,
        resource_type: str,
        error_message: str,
        issue_detected_at: Optional[datetime] = None
    ) -> Alert:
        """
        Generate a connectivity alert for an unreachable resource.
        
        **Requirement 16.1**: Alert within 30 seconds of resource becoming unreachable
        
        Args:
            resource_id: Resource ID
            resource_type: Resource type
            error_message: Error details
            issue_detected_at: When connectivity was lost
            
        Returns:
            Generated Alert
        """
        return await self.generate_alert(
            resource_id=resource_id,
            resource_type=resource_type,
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.CONNECTIVITY,
            title=f"Resource Unreachable: {resource_id}",
            message=f"Resource {resource_id} ({resource_type}) is unreachable. {error_message}",
            metadata={"error": error_message},
            issue_detected_at=issue_detected_at
        )
    
    async def generate_resource_alert(
        self,
        resource_id: str,
        resource_type: str,
        resource_name: str,
        current_value: float,
        threshold: float,
        is_critical: bool = False
    ) -> Alert:
        """
        Generate a resource utilization alert.
        
        **Requirement 16.2**: Alert for critically low resources
        
        Args:
            resource_id: Resource ID
            resource_type: Resource type
            resource_name: Name of the resource metric (CPU, Memory, Disk)
            current_value: Current utilization value
            threshold: Threshold that was exceeded
            is_critical: Whether this is a critical alert
            
        Returns:
            Generated Alert
        """
        severity = AlertSeverity.CRITICAL if is_critical else AlertSeverity.WARNING
        
        return await self.generate_alert(
            resource_id=resource_id,
            resource_type=resource_type,
            severity=severity,
            category=AlertCategory.RESOURCE_UTILIZATION,
            title=f"{resource_name} {'Critical' if is_critical else 'Warning'}: {resource_id}",
            message=f"{resource_name} utilization at {current_value:.1f}% (threshold: {threshold:.1f}%)",
            metadata={
                "resource_name": resource_name,
                "current_value": current_value,
                "threshold": threshold
            }
        )
    
    async def generate_temperature_alert(
        self,
        resource_id: str,
        resource_type: str,
        temperature: float,
        threshold: float,
        is_critical: bool = False
    ) -> Alert:
        """
        Generate a temperature alert for a board.
        
        **Requirement 16.3**: Alert for temperature issues
        
        Args:
            resource_id: Board ID
            resource_type: Resource type
            temperature: Current temperature
            threshold: Temperature threshold
            is_critical: Whether this is critical
            
        Returns:
            Generated Alert
        """
        severity = AlertSeverity.CRITICAL if is_critical else AlertSeverity.WARNING
        
        return await self.generate_alert(
            resource_id=resource_id,
            resource_type=resource_type,
            severity=severity,
            category=AlertCategory.TEMPERATURE,
            title=f"Temperature {'Critical' if is_critical else 'Warning'}: {resource_id}",
            message=f"Board temperature at {temperature:.1f}°C (threshold: {threshold:.1f}°C)",
            metadata={
                "temperature": temperature,
                "threshold": threshold
            }
        )
    
    async def generate_provisioning_failure_alert(
        self,
        resource_id: str,
        resource_type: str,
        operation: str,
        error_message: str,
        will_retry: bool = False,
        alternative_resource: Optional[str] = None
    ) -> Alert:
        """
        Generate a provisioning failure alert.
        
        **Requirement 16.4**: Alert on provisioning failure with recovery info
        
        Args:
            resource_id: Resource ID
            resource_type: Resource type
            operation: Operation that failed
            error_message: Error details
            will_retry: Whether retry will be attempted
            alternative_resource: Alternative resource if available
            
        Returns:
            Generated Alert
        """
        message = f"{operation} failed on {resource_id}: {error_message}"
        if will_retry:
            message += f" Will retry on alternative resource: {alternative_resource}"
        
        return await self.generate_alert(
            resource_id=resource_id,
            resource_type=resource_type,
            severity=AlertSeverity.ERROR,
            category=AlertCategory.PROVISIONING,
            title=f"Provisioning Failed: {resource_id}",
            message=message,
            metadata={
                "operation": operation,
                "error": error_message,
                "will_retry": will_retry,
                "alternative_resource": alternative_resource
            }
        )
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        notes: Optional[str] = None
    ) -> Optional[Alert]:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            acknowledged_by: User who acknowledged
            notes: Optional notes
            
        Returns:
            Updated Alert or None if not found
        """
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        
        now = datetime.now(timezone.utc)
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = now
        alert.acknowledged_by = acknowledged_by
        alert.updated_at = now
        
        if notes:
            alert.metadata["acknowledgment_notes"] = notes
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return alert
    
    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None
    ) -> Optional[Alert]:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert ID
            resolved_by: User or system that resolved
            resolution_notes: Resolution notes
            
        Returns:
            Updated Alert or None if not found
        """
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        
        now = datetime.now(timezone.utc)
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = now
        alert.resolved_by = resolved_by
        alert.resolution_notes = resolution_notes
        alert.updated_at = now
        
        # Move to history
        self._alert_history.append(alert)
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]
        
        # Remove from active alerts
        del self._alerts[alert_id]
        
        logger.info(f"Alert {alert_id} resolved by {resolved_by}")
        return alert
    
    async def auto_resolve_for_resource(
        self,
        resource_id: str,
        category: Optional[AlertCategory] = None,
        resolution_notes: str = "Auto-resolved: resource recovered"
    ) -> List[Alert]:
        """
        Auto-resolve alerts for a resource that has recovered.
        
        Args:
            resource_id: Resource ID
            category: Optional category filter
            resolution_notes: Resolution notes
            
        Returns:
            List of resolved alerts
        """
        resolved = []
        
        for alert_id, alert in list(self._alerts.items()):
            if alert.resource_id == resource_id:
                if category is None or alert.category == category:
                    resolved_alert = await self.resolve_alert(
                        alert_id,
                        resolved_by="system",
                        resolution_notes=resolution_notes
                    )
                    if resolved_alert:
                        resolved.append(resolved_alert)
        
        return resolved
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self._alerts.get(alert_id)
    
    def get_active_alerts(
        self,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        category: Optional[AlertCategory] = None
    ) -> List[Alert]:
        """
        Get active alerts with optional filters.
        
        Args:
            resource_id: Filter by resource ID
            resource_type: Filter by resource type
            severity: Filter by severity
            category: Filter by category
            
        Returns:
            List of matching alerts
        """
        alerts = list(self._alerts.values())
        
        if resource_id:
            alerts = [a for a in alerts if a.resource_id == resource_id]
        if resource_type:
            alerts = [a for a in alerts if a.resource_type == resource_type]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    def get_alert_history(
        self,
        resource_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            resource_id: Filter by resource ID
            limit: Maximum number of alerts to return
            
        Returns:
            List of historical alerts
        """
        history = self._alert_history
        
        if resource_id:
            history = [a for a in history if a.resource_id == resource_id]
        
        return sorted(history, key=lambda a: a.created_at, reverse=True)[:limit]
    
    def get_alert_count_by_severity(self) -> Dict[AlertSeverity, int]:
        """Get count of active alerts by severity."""
        counts = {s: 0 for s in AlertSeverity}
        for alert in self._alerts.values():
            counts[alert.severity] += 1
        return counts
    
    def get_alert_generation_time(self, alert_id: str) -> Optional[datetime]:
        """Get the timestamp when an alert was generated."""
        return self._alert_generation_times.get(alert_id)
    
    def _is_in_cooldown(self, resource_id: str, category: AlertCategory) -> bool:
        """Check if alert generation is in cooldown."""
        if resource_id not in self._cooldowns:
            return False
        
        if category not in self._cooldowns[resource_id]:
            return False
        
        last_alert = self._cooldowns[resource_id][category]
        cooldown_seconds = 300  # Default 5 minutes
        
        # Check if there's a rule with custom cooldown
        for rule in self._alert_rules.values():
            if rule.category == category and rule.enabled:
                cooldown_seconds = rule.cooldown_seconds
                break
        
        elapsed = (datetime.now(timezone.utc) - last_alert).total_seconds()
        return elapsed < cooldown_seconds
    
    def _update_cooldown(
        self,
        resource_id: str,
        category: AlertCategory,
        timestamp: datetime
    ) -> None:
        """Update cooldown timestamp."""
        if resource_id not in self._cooldowns:
            self._cooldowns[resource_id] = {}
        self._cooldowns[resource_id][category] = timestamp
    
    def _find_active_alert(
        self,
        resource_id: str,
        category: AlertCategory
    ) -> Optional[Alert]:
        """Find an active alert for a resource and category."""
        for alert in self._alerts.values():
            if alert.resource_id == resource_id and alert.category == category:
                return alert
        return None
    
    async def _send_notifications(self, alert: Alert) -> None:
        """
        Send notifications for an alert.
        
        **Requirement 16.5**: Support dashboard, email, and webhook notifications
        """
        for channel, config in self._notification_configs.items():
            if not config.enabled:
                continue
            
            try:
                handler = self._notification_handlers.get(channel)
                if handler:
                    success = await handler(alert)
                    alert.notification_sent[channel.value] = success
                else:
                    # Default handling for dashboard (always succeeds)
                    if channel == NotificationChannel.DASHBOARD:
                        alert.notification_sent[channel.value] = True
                    else:
                        logger.warning(f"No handler for notification channel: {channel.value}")
                        
            except Exception as e:
                logger.error(f"Failed to send {channel.value} notification: {e}")
                alert.notification_sent[channel.value] = False
    
    async def mark_recovery_attempted(
        self,
        alert_id: str,
        successful: bool
    ) -> Optional[Alert]:
        """
        Mark that auto-recovery was attempted for an alert.
        
        Args:
            alert_id: Alert ID
            successful: Whether recovery was successful
            
        Returns:
            Updated Alert or None
        """
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        
        alert.auto_recovery_attempted = True
        alert.recovery_successful = successful
        alert.updated_at = datetime.now(timezone.utc)
        
        if successful:
            await self.resolve_alert(
                alert_id,
                resolved_by="auto_recovery",
                resolution_notes="Automatically recovered"
            )
        
        return alert
    
    @property
    def active_alert_count(self) -> int:
        """Get count of active alerts."""
        return len(self._alerts)
    
    @property
    def critical_alert_count(self) -> int:
        """Get count of critical alerts."""
        return sum(1 for a in self._alerts.values() if a.severity == AlertSeverity.CRITICAL)
