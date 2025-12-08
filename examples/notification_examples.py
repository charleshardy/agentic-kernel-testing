"""Examples of using the notification system."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from integration.notification_models import (
    Notification,
    NotificationSeverity,
    NotificationChannel,
    NotificationRecipient
)
from integration.notification_service import NotificationDispatcher


def example_basic_notification():
    """Example: Send a basic notification."""
    print("Example 1: Basic notification")
    
    # Create notification dispatcher
    dispatcher = NotificationDispatcher()
    
    # Create a notification
    notification = Notification(
        id="test_001",
        title="Test Execution Started",
        message="Test suite for kernel module xyz has started execution.",
        severity=NotificationSeverity.INFO,
        channels=[NotificationChannel.SLACK],
        recipients=[
            NotificationRecipient(
                name="Developer",
                email="dev@example.com",
                slack_user_id="U12345"
            )
        ],
        test_id="test_xyz_001"
    )
    
    # Send notification
    results = dispatcher.send_notification(notification)
    
    for result in results:
        print(f"  Channel: {result.channel.value}")
        print(f"  Success: {result.success}")
        if result.error_message:
            print(f"  Error: {result.error_message}")
    print()


def example_critical_failure():
    """Example: Send a critical failure notification."""
    print("Example 2: Critical failure notification")
    
    dispatcher = NotificationDispatcher()
    
    # Send critical failure notification (uses convenience method)
    results = dispatcher.send_critical_failure_notification(
        title="Kernel Panic Detected",
        message="A kernel panic was detected during test execution. "
                "The system crashed while testing the network driver module.",
        test_id="test_network_driver_042",
        failure_id="failure_20231208_001",
        recipients=[
            NotificationRecipient(
                name="Kernel Team Lead",
                email="kernel-lead@example.com"
            ),
            NotificationRecipient(
                name="Network Driver Maintainer",
                email="network-maintainer@example.com"
            )
        ],
        metadata={
            "subsystem": "network",
            "driver": "e1000e",
            "kernel_version": "6.5.0",
            "crash_type": "NULL pointer dereference"
        }
    )
    
    for result in results:
        print(f"  Channel: {result.channel.value}")
        print(f"  Success: {result.success}")
        if result.error_message:
            print(f"  Error: {result.error_message}")
    print()


def example_severity_routing():
    """Example: Automatic routing based on severity."""
    print("Example 3: Severity-based routing")
    
    dispatcher = NotificationDispatcher()
    
    # Create notifications with different severities
    severities = [
        NotificationSeverity.INFO,
        NotificationSeverity.WARNING,
        NotificationSeverity.ERROR,
        NotificationSeverity.CRITICAL
    ]
    
    for severity in severities:
        notification = Notification(
            id=f"test_{severity.value}",
            title=f"{severity.value.upper()} Test Event",
            message=f"This is a {severity.value} level notification.",
            severity=severity,
            recipients=[
                NotificationRecipient(
                    name="Test User",
                    email="test@example.com"
                )
            ]
        )
        
        # Route based on severity
        notification = dispatcher.route_notification(notification)
        
        print(f"  Severity: {severity.value}")
        print(f"  Channels: {[ch.value for ch in notification.channels]}")
    print()


def example_custom_routing():
    """Example: Custom routing rules."""
    print("Example 4: Custom routing rules")
    
    dispatcher = NotificationDispatcher()
    
    # Define custom routing rules
    custom_rules = {
        NotificationSeverity.INFO: [NotificationChannel.SLACK],
        NotificationSeverity.WARNING: [NotificationChannel.EMAIL],
        NotificationSeverity.ERROR: [NotificationChannel.EMAIL, NotificationChannel.TEAMS],
        NotificationSeverity.CRITICAL: [
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
            NotificationChannel.TEAMS
        ]
    }
    
    notification = Notification(
        id="custom_001",
        title="Custom Routing Test",
        message="Testing custom routing rules.",
        severity=NotificationSeverity.ERROR,
        recipients=[
            NotificationRecipient(
                name="Admin",
                email="admin@example.com"
            )
        ]
    )
    
    # Apply custom routing
    notification = dispatcher.route_notification(notification, custom_rules)
    
    print(f"  Severity: {notification.severity.value}")
    print(f"  Channels: {[ch.value for ch in notification.channels]}")
    print()


def example_severity_filtering():
    """Example: Filter notifications by severity."""
    print("Example 5: Severity filtering")
    
    dispatcher = NotificationDispatcher()
    
    notifications = [
        Notification(
            id="info_001",
            title="Info Message",
            message="Informational message",
            severity=NotificationSeverity.INFO
        ),
        Notification(
            id="warning_001",
            title="Warning Message",
            message="Warning message",
            severity=NotificationSeverity.WARNING
        ),
        Notification(
            id="error_001",
            title="Error Message",
            message="Error message",
            severity=NotificationSeverity.ERROR
        )
    ]
    
    # Filter for ERROR and above
    min_severity = NotificationSeverity.ERROR
    
    for notification in notifications:
        should_send = dispatcher.filter_by_severity(notification, min_severity)
        print(f"  {notification.severity.value}: Send = {should_send}")
    print()


def example_metadata_enrichment():
    """Example: Enrich notifications with metadata."""
    print("Example 6: Metadata enrichment")
    
    dispatcher = NotificationDispatcher()
    
    notification = Notification(
        id="metadata_001",
        title="Performance Regression Detected",
        message="A performance regression was detected in the I/O subsystem.",
        severity=NotificationSeverity.WARNING,
        channels=[NotificationChannel.SLACK],
        recipients=[
            NotificationRecipient(
                name="Performance Team",
                email="perf@example.com"
            )
        ],
        test_id="perf_io_test_001",
        metadata={
            "subsystem": "I/O",
            "benchmark": "FIO sequential write",
            "baseline_throughput": "500 MB/s",
            "current_throughput": "350 MB/s",
            "regression_percentage": "30%",
            "commit_range": "abc123..def456",
            "test_duration": "300s"
        }
    )
    
    print(f"  Title: {notification.title}")
    print(f"  Metadata:")
    for key, value in notification.metadata.items():
        print(f"    {key}: {value}")
    print()


def main():
    """Run all examples."""
    print("=" * 60)
    print("Notification System Examples")
    print("=" * 60)
    print()
    
    example_basic_notification()
    example_critical_failure()
    example_severity_routing()
    example_custom_routing()
    example_severity_filtering()
    example_metadata_enrichment()
    
    print("=" * 60)
    print("Note: Actual sending requires proper configuration in .env")
    print("=" * 60)


if __name__ == "__main__":
    main()
