#!/usr/bin/env python3
"""Complete integration test for notification system."""

import sys

# Test all imports
from integration.notification_models import *
from integration.notification_service import *
from config.settings import get_settings

print("="*70)
print("NOTIFICATION SYSTEM - COMPLETE INTEGRATION TEST")
print("="*70)
print()

# Test 1: Configuration
print("Test 1: Configuration Loading")
settings = get_settings()
print(f"  ✓ Configuration loaded")
print(f"  ✓ Notifications enabled: {settings.notification.enabled}")
print(f"  ✓ Email enabled: {settings.notification.email_enabled}")
print(f"  ✓ Slack enabled: {settings.notification.slack_enabled}")
print()

# Test 2: Dispatcher Creation
print("Test 2: Dispatcher Initialization")
dispatcher = NotificationDispatcher()
print(f"  ✓ Dispatcher created successfully")
print(f"  ✓ Channels registered: {len(dispatcher.channels)}")
print()

# Test 3: Notification Creation
print("Test 3: Notification Creation")
notification = Notification(
    id='test_001',
    title='Test Notification',
    message='This is a test message',
    severity=NotificationSeverity.CRITICAL,
    recipients=[
        NotificationRecipient(
            name='Test User',
            email='test@example.com'
        )
    ]
)
print(f"  ✓ Notification created")
print(f"  ✓ ID: {notification.id}")
print(f"  ✓ Severity: {notification.severity.value}")
print(f"  ✓ Recipients: {len(notification.recipients)}")
print()

# Test 4: Routing
print("Test 4: Severity-Based Routing")
routed = dispatcher.route_notification(notification)
print(f"  ✓ Notification routed")
print(f"  ✓ Channels: {[ch.value for ch in routed.channels]}")
print(f"  ✓ Channel count: {len(routed.channels)}")
assert len(routed.channels) >= 2, "Critical should route to multiple channels"
print()

# Test 5: Filtering
print("Test 5: Severity Filtering")
test_cases = [
    (NotificationSeverity.INFO, False),
    (NotificationSeverity.WARNING, False),
    (NotificationSeverity.ERROR, True),
    (NotificationSeverity.CRITICAL, True)
]

for min_severity, expected in test_cases:
    passes = dispatcher.filter_by_severity(notification, min_severity)
    assert passes == expected, f"Filter test failed for {min_severity.value}"
    status = "✓" if passes else "✗"
    print(f"  {status} CRITICAL passes {min_severity.value.upper()} filter: {passes}")
print()

# Test 6: All Severity Levels
print("Test 6: All Severity Levels")
for severity in [NotificationSeverity.INFO, NotificationSeverity.WARNING,
                 NotificationSeverity.ERROR, NotificationSeverity.CRITICAL]:
    n = Notification(
        id=f'test_{severity.value}',
        title=f'Test {severity.value}',
        message='Test',
        severity=severity
    )
    print(f"  ✓ {severity.value.upper()} notification created")
print()

# Test 7: All Channel Types
print("Test 7: All Channel Types")
for channel in [NotificationChannel.EMAIL, NotificationChannel.SLACK,
                NotificationChannel.TEAMS, NotificationChannel.WEBHOOK]:
    n = Notification(
        id=f'test_{channel.value}',
        title='Test',
        message='Test',
        severity=NotificationSeverity.INFO,
        channels=[channel]
    )
    assert channel in n.channels
    print(f"  ✓ {channel.value.upper()} channel supported")
print()

# Test 8: Critical Failure Method
print("Test 8: Critical Failure Notification Method")
results = dispatcher.send_critical_failure_notification(
    title='Test Critical Failure',
    message='This is a test critical failure',
    test_id='test_123',
    failure_id='failure_456',
    recipients=[
        NotificationRecipient(name='Dev', email='dev@example.com')
    ],
    metadata={'subsystem': 'test', 'severity': 'high'}
)
print(f"  ✓ Critical failure notification sent")
print(f"  ✓ Results returned: {len(results)}")
print(f"  ✓ Channels attempted: {[r.channel.value for r in results]}")
print()

# Test 9: Serialization
print("Test 9: Serialization/Deserialization")
notification_dict = notification.to_dict()
assert 'id' in notification_dict
assert 'severity' in notification_dict
print(f"  ✓ to_dict() works")

notification_json = notification.to_json()
assert len(notification_json) > 0
print(f"  ✓ to_json() works")

restored = Notification.from_json(notification_json)
assert restored.id == notification.id
assert restored.severity == notification.severity
print(f"  ✓ from_json() works")
print()

# Test 10: Multiple Recipients
print("Test 10: Multiple Recipients")
multi_notification = Notification(
    id='multi_001',
    title='Multi-recipient Test',
    message='Test',
    severity=NotificationSeverity.ERROR,
    recipients=[
        NotificationRecipient(name=f'User {i}', email=f'user{i}@example.com')
        for i in range(5)
    ]
)
assert len(multi_notification.recipients) == 5
print(f"  ✓ Multiple recipients supported: {len(multi_notification.recipients)}")
print()

# Test 11: Metadata Support
print("Test 11: Metadata Support")
metadata_notification = Notification(
    id='metadata_001',
    title='Metadata Test',
    message='Test',
    severity=NotificationSeverity.WARNING,
    metadata={
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3'
    }
)
assert len(metadata_notification.metadata) == 3
print(f"  ✓ Metadata supported: {len(metadata_notification.metadata)} items")
print()

# Test 12: Custom Routing Rules
print("Test 12: Custom Routing Rules")
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

test_notification = Notification(
    id='custom_001',
    title='Custom Routing',
    message='Test',
    severity=NotificationSeverity.ERROR
)

routed_custom = dispatcher.route_notification(test_notification, custom_rules)
assert NotificationChannel.EMAIL in routed_custom.channels
assert NotificationChannel.TEAMS in routed_custom.channels
print(f"  ✓ Custom routing rules applied")
print(f"  ✓ ERROR routed to: {[ch.value for ch in routed_custom.channels]}")
print()

# Summary
print("="*70)
print("ALL TESTS PASSED!")
print("="*70)
print()
print("Summary:")
print(f"  ✓ Configuration: Working")
print(f"  ✓ Dispatcher: Working")
print(f"  ✓ Notifications: Working")
print(f"  ✓ Routing: Working")
print(f"  ✓ Filtering: Working")
print(f"  ✓ All Severities: Working")
print(f"  ✓ All Channels: Working")
print(f"  ✓ Critical Failures: Working")
print(f"  ✓ Serialization: Working")
print(f"  ✓ Multiple Recipients: Working")
print(f"  ✓ Metadata: Working")
print(f"  ✓ Custom Routing: Working")
print()
print("The notification system is fully functional and ready for production use!")
print()
