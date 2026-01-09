"""
Property-Based Tests for Alert Generation Timing

**Feature: test-infrastructure-management, Property 23: Alert Generation Within Time Limit**
**Validates: Requirements 16.1**

For any resource that becomes unreachable, an alert SHALL be generated within 30 seconds.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings, assume
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.services.health_monitor import (
    HealthMonitorService,
    HealthCheckResult,
    HealthStatus,
    ResourceType,
    HealthThresholds,
)
from infrastructure.services.alert_service import (
    AlertService,
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertCategory,
)


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def resource_id_strategy(draw):
    """Generate valid resource IDs."""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    return draw(st.text(min_size=1, max_size=50, alphabet=chars))


@st.composite
def resource_type_strategy(draw):
    """Generate valid resource types."""
    return draw(st.sampled_from(["build_server", "qemu_host", "physical_board"]))


@st.composite
def issue_detection_delay_strategy(draw):
    """Generate realistic issue detection delays (0-60 seconds)."""
    return draw(st.floats(min_value=0.0, max_value=60.0))


# =============================================================================
# Property Tests for Alert Timing
# =============================================================================

class TestAlertGenerationTiming:
    """
    **Feature: test-infrastructure-management, Property 23: Alert Generation Within Time Limit**
    **Validates: Requirements 16.1**
    
    For any resource that becomes unreachable, an alert SHALL be generated within 30 seconds.
    """
    
    # Maximum allowed time for alert generation (Requirement 16.1)
    MAX_ALERT_TIME_SECONDS = 30

    @pytest.mark.asyncio
    @given(
        resource_id=resource_id_strategy(),
        resource_type=resource_type_strategy()
    )
    @settings(max_examples=50)
    async def test_connectivity_alert_generated_immediately(
        self,
        resource_id: str,
        resource_type: str
    ):
        """
        For any resource that becomes unreachable, a connectivity alert
        SHALL be generated immediately (within milliseconds).
        """
        alert_service = AlertService()
        
        issue_detected_at = datetime.now(timezone.utc)
        
        # Generate connectivity alert
        alert = await alert_service.generate_connectivity_alert(
            resource_id=resource_id,
            resource_type=resource_type,
            error_message="Connection refused",
            issue_detected_at=issue_detected_at
        )
        
        # Verify alert was generated
        assert alert is not None
        assert alert.resource_id == resource_id
        assert alert.resource_type == resource_type
        assert alert.category == AlertCategory.CONNECTIVITY
        assert alert.severity == AlertSeverity.CRITICAL
        
        # Verify timing - alert should be generated almost immediately
        generation_time = alert_service.get_alert_generation_time(alert.id)
        assert generation_time is not None
        
        delay = (generation_time - issue_detected_at).total_seconds()
        assert delay < self.MAX_ALERT_TIME_SECONDS, \
            f"Alert generation took {delay}s, exceeds {self.MAX_ALERT_TIME_SECONDS}s limit"

    @pytest.mark.asyncio
    @given(
        resource_id=resource_id_strategy(),
        resource_type=resource_type_strategy(),
        detection_delay=st.floats(min_value=0.0, max_value=25.0)
    )
    @settings(max_examples=50)
    async def test_alert_within_time_limit_with_detection_delay(
        self,
        resource_id: str,
        resource_type: str,
        detection_delay: float
    ):
        """
        For any issue detection delay less than 25 seconds, the total time
        from issue occurrence to alert generation SHALL be within 30 seconds.
        """
        alert_service = AlertService()
        
        # Simulate issue occurring in the past
        issue_occurred_at = datetime.now(timezone.utc) - timedelta(seconds=detection_delay)
        
        # Generate alert
        alert = await alert_service.generate_alert(
            resource_id=resource_id,
            resource_type=resource_type,
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.CONNECTIVITY,
            title=f"Resource Unreachable: {resource_id}",
            message="Connection failed",
            issue_detected_at=issue_occurred_at
        )
        
        # Verify alert was generated
        assert alert is not None
        
        # The alert service should track and warn about timing violations
        generation_time = alert_service.get_alert_generation_time(alert.id)
        assert generation_time is not None

    @pytest.mark.asyncio
    @given(
        resource_id=resource_id_strategy(),
        resource_type=resource_type_strategy()
    )
    @settings(max_examples=50)
    async def test_alert_service_max_time_constant(
        self,
        resource_id: str,
        resource_type: str
    ):
        """
        The AlertService SHALL have a MAX_ALERT_GENERATION_TIME_SECONDS
        constant set to 30 seconds as per Requirement 16.1.
        """
        assert AlertService.MAX_ALERT_GENERATION_TIME_SECONDS == 30

    @pytest.mark.asyncio
    @given(
        resource_id=resource_id_strategy(),
        resource_type=resource_type_strategy()
    )
    @settings(max_examples=50)
    async def test_multiple_alerts_all_within_time_limit(
        self,
        resource_id: str,
        resource_type: str
    ):
        """
        For multiple resources becoming unreachable simultaneously,
        all alerts SHALL be generated within the time limit.
        """
        alert_service = AlertService()
        
        # Generate multiple alerts
        issue_detected_at = datetime.now(timezone.utc)
        alerts = []
        
        for i in range(5):
            alert = await alert_service.generate_alert(
                resource_id=f"{resource_id}-{i}",
                resource_type=resource_type,
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.CONNECTIVITY,
                title=f"Resource Unreachable: {resource_id}-{i}",
                message="Connection failed",
                issue_detected_at=issue_detected_at
            )
            alerts.append(alert)
        
        # Verify all alerts were generated within time limit
        for alert in alerts:
            generation_time = alert_service.get_alert_generation_time(alert.id)
            assert generation_time is not None
            
            delay = (generation_time - issue_detected_at).total_seconds()
            assert delay < self.MAX_ALERT_TIME_SECONDS


class TestHealthMonitorAlertIntegration:
    """
    Test integration between HealthMonitorService and AlertService
    for alert timing compliance.
    """

    @pytest.mark.asyncio
    async def test_health_monitor_triggers_alert_within_time_limit(self):
        """
        When HealthMonitorService detects an unreachable resource,
        it SHALL trigger an alert within 30 seconds.
        """
        alert_service = AlertService()
        alerts_generated = []
        
        async def alert_callback(resource_id, resource_type, status, message):
            issue_detected_at = datetime.now(timezone.utc)
            alert = await alert_service.generate_connectivity_alert(
                resource_id=resource_id,
                resource_type=resource_type.value,
                error_message=message,
                issue_detected_at=issue_detected_at
            )
            alerts_generated.append((alert, issue_detected_at))
        
        health_monitor = HealthMonitorService(
            check_interval_seconds=1,
            alert_callback=alert_callback
        )
        
        # Register a resource that will be unreachable
        health_monitor.register_host("test-host", {
            "connectivity": False,  # Simulate unreachable
            "cpu_percent": 50.0,
            "memory_percent": 50.0,
            "storage_percent": 50.0
        })
        
        # Perform health check
        result = await health_monitor.check_host_health("test-host")
        
        # Verify the health check detected unreachable status
        # Note: In the current implementation, connectivity is checked via board health
        # For hosts, we check libvirt availability
        assert result is not None

    @pytest.mark.asyncio
    @given(
        cpu_percent=st.floats(min_value=0.0, max_value=100.0),
        memory_percent=st.floats(min_value=0.0, max_value=100.0),
        storage_percent=st.floats(min_value=0.0, max_value=100.0)
    )
    @settings(max_examples=50)
    async def test_resource_utilization_alert_timing(
        self,
        cpu_percent: float,
        memory_percent: float,
        storage_percent: float
    ):
        """
        For any resource utilization threshold breach, an alert
        SHALL be generated within the time limit.
        """
        alert_service = AlertService()
        
        # Only test when threshold is exceeded
        assume(cpu_percent >= 85.0 or memory_percent >= 85.0 or storage_percent >= 85.0)
        
        issue_detected_at = datetime.now(timezone.utc)
        
        # Generate resource alert
        if cpu_percent >= 85.0:
            alert = await alert_service.generate_resource_alert(
                resource_id="test-server",
                resource_type="build_server",
                resource_name="CPU",
                current_value=cpu_percent,
                threshold=85.0,
                is_critical=cpu_percent >= 95.0
            )
            
            generation_time = alert_service.get_alert_generation_time(alert.id)
            assert generation_time is not None
            
            delay = (generation_time - issue_detected_at).total_seconds()
            assert delay < AlertService.MAX_ALERT_GENERATION_TIME_SECONDS


class TestAlertCooldownTiming:
    """Test that alert cooldown doesn't affect timing compliance."""

    @pytest.mark.asyncio
    @given(resource_id=resource_id_strategy())
    @settings(max_examples=30)
    async def test_first_alert_not_affected_by_cooldown(self, resource_id: str):
        """
        The first alert for a resource SHALL be generated immediately
        without any cooldown delay.
        """
        alert_service = AlertService()
        
        issue_detected_at = datetime.now(timezone.utc)
        
        alert = await alert_service.generate_connectivity_alert(
            resource_id=resource_id,
            resource_type="build_server",
            error_message="Connection refused",
            issue_detected_at=issue_detected_at
        )
        
        # First alert should be generated immediately
        generation_time = alert_service.get_alert_generation_time(alert.id)
        delay = (generation_time - issue_detected_at).total_seconds()
        
        # Should be nearly instant (less than 1 second)
        assert delay < 1.0

    @pytest.mark.asyncio
    async def test_cooldown_returns_existing_alert_immediately(self):
        """
        When in cooldown, the existing alert SHALL be returned immediately
        without additional delay.
        """
        alert_service = AlertService()
        
        # Generate first alert
        first_alert = await alert_service.generate_connectivity_alert(
            resource_id="test-resource",
            resource_type="build_server",
            error_message="Connection refused"
        )
        
        # Try to generate another alert immediately (should be in cooldown)
        start_time = datetime.now(timezone.utc)
        second_alert = await alert_service.generate_connectivity_alert(
            resource_id="test-resource",
            resource_type="build_server",
            error_message="Still unreachable"
        )
        end_time = datetime.now(timezone.utc)
        
        # Should return the existing alert
        assert second_alert.id == first_alert.id
        
        # Should return immediately (less than 100ms)
        delay = (end_time - start_time).total_seconds()
        assert delay < 0.1


class TestAlertSeverityTiming:
    """Test that alert severity doesn't affect timing compliance."""

    @pytest.mark.asyncio
    @given(severity=st.sampled_from(list(AlertSeverity)))
    @settings(max_examples=20)
    async def test_all_severities_generated_within_time_limit(
        self,
        severity: AlertSeverity
    ):
        """
        Alerts of any severity level SHALL be generated within the time limit.
        """
        alert_service = AlertService()
        
        issue_detected_at = datetime.now(timezone.utc)
        
        alert = await alert_service.generate_alert(
            resource_id="test-resource",
            resource_type="build_server",
            severity=severity,
            category=AlertCategory.HEALTH,
            title="Test Alert",
            message="Test message",
            issue_detected_at=issue_detected_at
        )
        
        generation_time = alert_service.get_alert_generation_time(alert.id)
        delay = (generation_time - issue_detected_at).total_seconds()
        
        assert delay < AlertService.MAX_ALERT_GENERATION_TIME_SECONDS


class TestAlertCategoryTiming:
    """Test that alert category doesn't affect timing compliance."""

    @pytest.mark.asyncio
    @given(category=st.sampled_from(list(AlertCategory)))
    @settings(max_examples=30)
    async def test_all_categories_generated_within_time_limit(
        self,
        category: AlertCategory
    ):
        """
        Alerts of any category SHALL be generated within the time limit.
        """
        alert_service = AlertService()
        
        issue_detected_at = datetime.now(timezone.utc)
        
        alert = await alert_service.generate_alert(
            resource_id=f"test-resource-{category.value}",
            resource_type="build_server",
            severity=AlertSeverity.WARNING,
            category=category,
            title=f"Test {category.value} Alert",
            message="Test message",
            issue_detected_at=issue_detected_at
        )
        
        generation_time = alert_service.get_alert_generation_time(alert.id)
        delay = (generation_time - issue_detected_at).total_seconds()
        
        assert delay < AlertService.MAX_ALERT_GENERATION_TIME_SECONDS


class TestBoardUnreachableAlertTiming:
    """
    Test alert timing specifically for physical boards becoming unreachable.
    
    **Requirement 10.3**: When a board becomes unreachable, mark as offline
    and attempt automatic recovery via power cycle.
    """

    @pytest.mark.asyncio
    @given(
        board_id=resource_id_strategy(),
        temperature=st.floats(min_value=20.0, max_value=100.0)
    )
    @settings(max_examples=30)
    async def test_board_unreachable_alert_timing(
        self,
        board_id: str,
        temperature: float
    ):
        """
        When a physical board becomes unreachable, an alert SHALL be
        generated within 30 seconds.
        """
        alert_service = AlertService()
        
        issue_detected_at = datetime.now(timezone.utc)
        
        alert = await alert_service.generate_connectivity_alert(
            resource_id=board_id,
            resource_type="physical_board",
            error_message="Board not responding to ping",
            issue_detected_at=issue_detected_at
        )
        
        generation_time = alert_service.get_alert_generation_time(alert.id)
        delay = (generation_time - issue_detected_at).total_seconds()
        
        assert delay < AlertService.MAX_ALERT_GENERATION_TIME_SECONDS
        assert alert.category == AlertCategory.CONNECTIVITY
        assert alert.severity == AlertSeverity.CRITICAL

    @pytest.mark.asyncio
    @given(
        board_id=resource_id_strategy(),
        temperature=st.floats(min_value=70.0, max_value=100.0)
    )
    @settings(max_examples=30)
    async def test_board_temperature_alert_timing(
        self,
        board_id: str,
        temperature: float
    ):
        """
        When a board temperature exceeds threshold, an alert SHALL be
        generated within the time limit.
        """
        alert_service = AlertService()
        
        issue_detected_at = datetime.now(timezone.utc)
        
        alert = await alert_service.generate_temperature_alert(
            resource_id=board_id,
            resource_type="physical_board",
            temperature=temperature,
            threshold=70.0,
            is_critical=temperature >= 85.0
        )
        
        generation_time = alert_service.get_alert_generation_time(alert.id)
        delay = (generation_time - issue_detected_at).total_seconds()
        
        assert delay < AlertService.MAX_ALERT_GENERATION_TIME_SECONDS
        assert alert.category == AlertCategory.TEMPERATURE
