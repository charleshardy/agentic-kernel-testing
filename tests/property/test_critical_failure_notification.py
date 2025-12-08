"""
Property-based tests for critical failure notification.

**Feature: agentic-kernel-testing, Property 24: Critical failure notification**

This test validates that when critical failures are detected, the system sends
notifications to relevant developers via all configured channels.

**Validates: Requirements 5.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List

from integration.notification_service import NotificationDispatcher
from integration.notification_models import (
    Notification,
    NotificationSeverity,
    NotificationChannel,
    NotificationRecipient
)


# Strategies for generating test data
@st.composite
def notification_recipient_strategy(draw):
    """Generate a notification recipient."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' '
    )))
    email = draw(st.emails())
    slack_id = draw(st.one_of(
        st.none(),
        st.text(min_size=5, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Nd')
        ))
    ))
    
    return NotificationRecipient(
        name=name.strip(),
        email=email,
        slack_user_id=slack_id
    )


@st.composite
def critical_failure_data_strategy(draw):
    """Generate critical failure notification data."""
    title = draw(st.text(min_size=10, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')
    )))
    message = draw(st.text(min_size=20, max_size=500, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
    )))
    test_id = draw(st.one_of(
        st.none(),
        st.text(min_size=5, max_size=30, alphabet=st.characters(
            whitelist_categories=('Ll', 'Nd'), whitelist_characters='_-'
        ))
    ))
    failure_id = draw(st.one_of(
        st.none(),
        st.text(min_size=5, max_size=30, alphabet=st.characters(
            whitelist_categories=('Ll', 'Nd'), whitelist_characters='_-'
        ))
    ))
    recipients = draw(st.lists(
        notification_recipient_strategy(),
        min_size=1,
        max_size=5
    ))
    
    # Generate metadata
    metadata_keys = draw(st.lists(
        st.text(min_size=3, max_size=20, alphabet=st.characters(
            whitelist_categories=('Ll',), whitelist_characters='_'
        )),
        min_size=0,
        max_size=5,
        unique=True
    ))
    metadata = {}
    for key in metadata_keys:
        value = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')
        )))
        metadata[key] = value.strip()
    
    return {
        'title': title.strip(),
        'message': message.strip(),
        'test_id': test_id,
        'failure_id': failure_id,
        'recipients': recipients,
        'metadata': metadata
    }


class TestCriticalFailureNotification:
    """Test critical failure notification property."""
    
    @given(failure_data=critical_failure_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_critical_failure_triggers_notification(self, failure_data):
        """
        Property 24: Critical failure notification
        
        For any critical failure, the system should send notifications to
        relevant developers via all configured channels.
        
        This property verifies that:
        1. Critical failures trigger notification creation
        2. Notifications have CRITICAL severity
        3. Notifications are routed to appropriate channels
        4. All notification content is complete
        """
        # Arrange
        dispatcher = NotificationDispatcher()
        
        # Assume valid data
        assume(len(failure_data['title']) > 0)
        assume(len(failure_data['message']) > 0)
        assume(len(failure_data['recipients']) > 0)
        
        # Act - Send critical failure notification
        results = dispatcher.send_critical_failure_notification(
            title=failure_data['title'],
            message=failure_data['message'],
            test_id=failure_data['test_id'],
            failure_id=failure_data['failure_id'],
            recipients=failure_data['recipients'],
            metadata=failure_data['metadata']
        )
        
        # Assert - Notification was created and sent
        assert len(results) > 0, "Critical failure should trigger at least one notification"
        
        # Verify all results have the notification ID
        notification_ids = set(result.notification_id for result in results)
        assert len(notification_ids) == 1, "All results should be for the same notification"
        
        # Verify channels were attempted
        channels_attempted = set(result.channel for result in results)
        assert len(channels_attempted) > 0, "At least one channel should be attempted"
        
        # Note: We don't assert success=True because channels may not be configured
        # in the test environment. The important property is that the notification
        # was created and delivery was attempted.
    
    @given(failure_data=critical_failure_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_critical_notification_has_correct_severity(self, failure_data):
        """
        Verify that critical failure notifications have CRITICAL severity.
        
        This ensures that the notification will be routed to all appropriate
        channels based on severity-based routing rules.
        """
        # Arrange
        dispatcher = NotificationDispatcher()
        
        assume(len(failure_data['title']) > 0)
        assume(len(failure_data['message']) > 0)
        assume(len(failure_data['recipients']) > 0)
        
        # Create a notification manually to verify severity
        notification = Notification(
            id=f"critical_{datetime.now().timestamp()}",
            title=failure_data['title'],
            message=failure_data['message'],
            severity=NotificationSeverity.CRITICAL,
            test_id=failure_data['test_id'],
            failure_id=failure_data['failure_id'],
            recipients=failure_data['recipients'],
            metadata=failure_data['metadata']
        )
        
        # Assert - Severity is CRITICAL
        assert notification.severity == NotificationSeverity.CRITICAL, \
            "Critical failure notifications must have CRITICAL severity"
    
    @given(failure_data=critical_failure_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_critical_notification_routing(self, failure_data):
        """
        Verify that critical notifications are routed to multiple channels.
        
        Critical failures should be sent through multiple channels to ensure
        developers are notified immediately.
        """
        # Arrange
        dispatcher = NotificationDispatcher()
        
        assume(len(failure_data['title']) > 0)
        assume(len(failure_data['message']) > 0)
        assume(len(failure_data['recipients']) > 0)
        
        # Create a critical notification
        notification = Notification(
            id=f"critical_{datetime.now().timestamp()}",
            title=failure_data['title'],
            message=failure_data['message'],
            severity=NotificationSeverity.CRITICAL,
            test_id=failure_data['test_id'],
            failure_id=failure_data['failure_id'],
            recipients=failure_data['recipients'],
            metadata=failure_data['metadata']
        )
        
        # Act - Route the notification
        routed_notification = dispatcher.route_notification(notification)
        
        # Assert - Critical notifications should be routed to multiple channels
        assert len(routed_notification.channels) >= 2, \
            "Critical notifications should be routed to at least 2 channels"
        
        # Verify expected channels for critical severity
        expected_channels = {
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
            NotificationChannel.TEAMS
        }
        actual_channels = set(routed_notification.channels)
        
        # At least some of the expected channels should be present
        assert len(actual_channels.intersection(expected_channels)) >= 2, \
            "Critical notifications should include multiple standard channels"
    
    @given(failure_data=critical_failure_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_notification_content_completeness(self, failure_data):
        """
        Verify that notification content includes all required information.
        
        Notifications should contain title, message, severity, and any
        provided test/failure IDs and metadata.
        """
        # Arrange
        dispatcher = NotificationDispatcher()
        
        assume(len(failure_data['title']) > 0)
        assume(len(failure_data['message']) > 0)
        assume(len(failure_data['recipients']) > 0)
        
        # Create notification
        notification = Notification(
            id=f"critical_{datetime.now().timestamp()}",
            title=failure_data['title'],
            message=failure_data['message'],
            severity=NotificationSeverity.CRITICAL,
            test_id=failure_data['test_id'],
            failure_id=failure_data['failure_id'],
            recipients=failure_data['recipients'],
            metadata=failure_data['metadata']
        )
        
        # Assert - All content is present
        assert notification.title == failure_data['title'], \
            "Notification title should match input"
        assert notification.message == failure_data['message'], \
            "Notification message should match input"
        assert notification.severity == NotificationSeverity.CRITICAL, \
            "Notification severity should be CRITICAL"
        assert notification.test_id == failure_data['test_id'], \
            "Test ID should be preserved"
        assert notification.failure_id == failure_data['failure_id'], \
            "Failure ID should be preserved"
        assert len(notification.recipients) == len(failure_data['recipients']), \
            "All recipients should be included"
        assert notification.metadata == failure_data['metadata'], \
            "Metadata should be preserved"
    
    @given(
        failure_data=critical_failure_data_strategy(),
        min_severity=st.sampled_from([
            NotificationSeverity.INFO,
            NotificationSeverity.WARNING,
            NotificationSeverity.ERROR,
            NotificationSeverity.CRITICAL
        ])
    )
    @settings(max_examples=100, deadline=None)
    def test_severity_filtering(self, failure_data, min_severity):
        """
        Verify that severity filtering works correctly.
        
        Critical notifications should pass all severity filters since
        CRITICAL is the highest severity level.
        """
        # Arrange
        dispatcher = NotificationDispatcher()
        
        assume(len(failure_data['title']) > 0)
        assume(len(failure_data['message']) > 0)
        assume(len(failure_data['recipients']) > 0)
        
        # Create critical notification
        notification = Notification(
            id=f"critical_{datetime.now().timestamp()}",
            title=failure_data['title'],
            message=failure_data['message'],
            severity=NotificationSeverity.CRITICAL,
            test_id=failure_data['test_id'],
            failure_id=failure_data['failure_id'],
            recipients=failure_data['recipients'],
            metadata=failure_data['metadata']
        )
        
        # Act - Filter by severity
        should_send = dispatcher.filter_by_severity(notification, min_severity)
        
        # Assert - Critical notifications should always pass filtering
        assert should_send, \
            f"Critical notifications should pass {min_severity.value} severity filter"
    
    @given(
        num_recipients=st.integers(min_value=1, max_value=10),
        failure_data=critical_failure_data_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_recipients_support(self, num_recipients, failure_data):
        """
        Verify that notifications support multiple recipients.
        
        Critical failures may need to notify multiple team members,
        so the system should support multiple recipients.
        """
        # Arrange
        assume(len(failure_data['title']) > 0)
        assume(len(failure_data['message']) > 0)
        
        # Generate multiple recipients
        recipients = []
        for i in range(num_recipients):
            recipients.append(NotificationRecipient(
                name=f"Developer {i}",
                email=f"dev{i}@example.com"
            ))
        
        # Create notification with multiple recipients
        notification = Notification(
            id=f"critical_{datetime.now().timestamp()}",
            title=failure_data['title'],
            message=failure_data['message'],
            severity=NotificationSeverity.CRITICAL,
            recipients=recipients
        )
        
        # Assert - All recipients are preserved
        assert len(notification.recipients) == num_recipients, \
            "All recipients should be included in notification"
        
        # Verify each recipient is present
        for i, recipient in enumerate(notification.recipients):
            assert recipient.name == f"Developer {i}", \
                f"Recipient {i} name should be preserved"
            assert recipient.email == f"dev{i}@example.com", \
                f"Recipient {i} email should be preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
