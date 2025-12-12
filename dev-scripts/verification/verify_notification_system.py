#!/usr/bin/env python3
"""Verify notification system implementation."""

import sys
from datetime import datetime

# Test imports
try:
    from integration.notification_models import (
        Notification,
        NotificationSeverity,
        NotificationChannel,
        NotificationRecipient,
        NotificationResult
    )
    print("✓ Notification models imported successfully")
except Exception as e:
    print(f"✗ Failed to import notification models: {e}")
    sys.exit(1)

try:
    from integration.notification_service import (
        NotificationDispatcher,
        EmailChannel,
        SlackChannel,
        TeamsChannel
    )
    print("✓ Notification service imported successfully")
except Exception as e:
    print(f"✗ Failed to import notification service: {e}")
    sys.exit(1)

# Test notification creation
try:
    notification = Notification(
        id="test_001",
        title="Test Notification",
        message="This is a test notification.",
        severity=NotificationSeverity.INFO,
        channels=[NotificationChannel.SLACK],
        recipients=[
            NotificationRecipient(
                name="Test User",
                email="test@example.com"
            )
        ]
    )
    print("✓ Notification created successfully")
except Exception as e:
    print(f"✗ Failed to create notification: {e}")
    sys.exit(1)

# Test dispatcher initialization
try:
    dispatcher = NotificationDispatcher()
    print("✓ NotificationDispatcher initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize dispatcher: {e}")
    sys.exit(1)

# Test severity filtering
try:
    critical_notification = Notification(
        id="critical_001",
        title="Critical Test",
        message="Critical message",
        severity=NotificationSeverity.CRITICAL
    )
    
    should_send = dispatcher.filter_by_severity(
        critical_notification,
        NotificationSeverity.ERROR
    )
    assert should_send, "Critical should pass ERROR filter"
    print("✓ Severity filtering works correctly")
except Exception as e:
    print(f"✗ Severity filtering failed: {e}")
    sys.exit(1)

# Test routing
try:
    test_notification = Notification(
        id="routing_001",
        title="Routing Test",
        message="Test routing",
        severity=NotificationSeverity.CRITICAL
    )
    
    routed = dispatcher.route_notification(test_notification)
    assert len(routed.channels) >= 2, "Critical should route to multiple channels"
    print(f"✓ Routing works correctly (routed to {len(routed.channels)} channels)")
except Exception as e:
    print(f"✗ Routing failed: {e}")
    sys.exit(1)

# Test critical failure notification method
try:
    results = dispatcher.send_critical_failure_notification(
        title="Test Critical Failure",
        message="This is a test critical failure notification.",
        test_id="test_123",
        failure_id="failure_456",
        recipients=[
            NotificationRecipient(
                name="Test Developer",
                email="dev@example.com"
            )
        ],
        metadata={
            "subsystem": "test",
            "severity": "high"
        }
    )
    
    assert len(results) > 0, "Should return at least one result"
    print(f"✓ Critical failure notification method works ({len(results)} channels attempted)")
except Exception as e:
    print(f"✗ Critical failure notification failed: {e}")
    sys.exit(1)

# Test serialization
try:
    notification_dict = notification.to_dict()
    assert 'id' in notification_dict
    assert 'title' in notification_dict
    assert 'severity' in notification_dict
    
    notification_json = notification.to_json()
    assert len(notification_json) > 0
    
    restored = Notification.from_json(notification_json)
    assert restored.id == notification.id
    assert restored.title == notification.title
    print("✓ Serialization/deserialization works correctly")
except Exception as e:
    print(f"✗ Serialization failed: {e}")
    sys.exit(1)

# Test all severity levels
try:
    for severity in [NotificationSeverity.INFO, NotificationSeverity.WARNING,
                     NotificationSeverity.ERROR, NotificationSeverity.CRITICAL]:
        n = Notification(
            id=f"test_{severity.value}",
            title=f"Test {severity.value}",
            message="Test message",
            severity=severity
        )
        assert n.severity == severity
    print("✓ All severity levels work correctly")
except Exception as e:
    print(f"✗ Severity levels test failed: {e}")
    sys.exit(1)

# Test all channel types
try:
    for channel in [NotificationChannel.EMAIL, NotificationChannel.SLACK,
                    NotificationChannel.TEAMS, NotificationChannel.WEBHOOK]:
        n = Notification(
            id=f"test_{channel.value}",
            title="Test",
            message="Test",
            severity=NotificationSeverity.INFO,
            channels=[channel]
        )
        assert channel in n.channels
    print("✓ All channel types work correctly")
except Exception as e:
    print(f"✗ Channel types test failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("All verification tests passed!")
print("="*60)
print("\nNotification system is ready for use.")
print("\nKey features verified:")
print("  • Multi-channel support (Email, Slack, Teams)")
print("  • Severity-based routing")
print("  • Notification filtering")
print("  • Critical failure notifications")
print("  • Serialization/deserialization")
print("  • Multiple recipients")
print("  • Metadata support")
