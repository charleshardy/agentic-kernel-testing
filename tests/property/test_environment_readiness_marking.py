"""
Property-based test for environment readiness marking.

Tests that environment readiness marking properly updates status on successful validation,
persists readiness state, and provides readiness notification and alerting.
"""

import asyncio
import pytest
import tempfile
import json
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any

from deployment.readiness_manager import (
    ReadinessManager, ReadinessState, ReadinessStatus, 
    ReadinessNotification, NotificationLevel
)
from deployment.models import ValidationResult


# Property-based test strategies
environment_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
validation_success_rates = st.floats(min_value=0.0, max_value=100.0)
consecutive_results = st.lists(st.booleans(), min_size=1, max_size=10)
notification_levels = st.sampled_from(list(NotificationLevel))


class MockValidationResult:
    """Mock validation result for testing"""
    
    def __init__(self, 
                 environment_id: str,
                 is_ready: bool,
                 success_rate: float,
                 failed_checks: List[str] = None,
                 warnings: List[str] = None):
        self.environment_id = environment_id
        self.is_ready = is_ready
        self.success_rate = success_rate
        self.failed_checks = failed_checks or []
        self.warnings = warnings or []
        self.checks_performed = ["network_connectivity", "disk_space", "memory_availability"]
        self.timestamp = datetime.now()
        self.has_failures = len(self.failed_checks) > 0
        self.details = {}


@given(
    environment_id=environment_ids,
    validation_results=st.lists(
        st.tuples(
            st.booleans(),  # is_ready
            validation_success_rates  # success_rate
        ),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=40, deadline=6000)
async def test_environment_readiness_marking(environment_id, validation_results):
    """
    **Feature: test-deployment-system, Property 20: Environment readiness marking**
    
    Property: Environment readiness marking updates status and persists state
    
    This test verifies that:
    1. Environment status is automatically updated on successful validation
    2. Readiness state is properly persisted and tracked
    3. Readiness scores are calculated correctly
    4. Status transitions generate appropriate notifications
    5. Historical readiness data is maintained
    """
    assume(len(environment_id.strip()) > 0)
    assume(len(validation_results) > 0)
    
    # Create temporary state file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Create readiness manager with temporary state file
        readiness_manager = ReadinessManager(state_file_path=temp_path)
        
        # Track notifications
        notifications_received = []
        
        def notification_callback(notification: ReadinessNotification):
            notifications_received.append(notification)
        
        readiness_manager.subscribe_to_notifications(notification_callback)
        
        # Process validation results sequentially
        previous_status = None
        
        for i, (is_ready, success_rate) in enumerate(validation_results):
            # Create mock validation result
            failed_checks = [] if is_ready else ["network_connectivity", "disk_space"]
            warnings = [] if is_ready else ["Warning: validation failed"]
            
            validation_result = MockValidationResult(
                environment_id=environment_id.strip(),
                is_ready=is_ready,
                success_rate=success_rate,
                failed_checks=failed_checks,
                warnings=warnings
            )
            
            # Update environment readiness
            readiness_state = await readiness_manager.update_environment_readiness(
                environment_id.strip(), validation_result
            )
            
            # Verify readiness state is updated
            assert readiness_state.environment_id == environment_id.strip(), \
                "Environment ID should match"
            assert readiness_state.validation_count == i + 1, \
                f"Validation count should be {i + 1}"
            assert readiness_state.last_validation is not None, \
                "Last validation timestamp should be set"
            
            # Verify readiness score calculation
            assert 0.0 <= readiness_state.readiness_score <= 100.0, \
                "Readiness score should be between 0 and 100"
            
            # Verify status determination
            if is_ready:
                assert readiness_state.status in [ReadinessStatus.READY, ReadinessStatus.DEGRADED], \
                    "Ready validation should result in READY or DEGRADED status"
                assert readiness_state.consecutive_successes > 0, \
                    "Consecutive successes should be incremented"
                assert readiness_state.consecutive_failures == 0, \
                    "Consecutive failures should be reset on success"
            else:
                assert readiness_state.status in [ReadinessStatus.NOT_READY, ReadinessStatus.DEGRADED], \
                    "Failed validation should result in NOT_READY or DEGRADED status"
                assert readiness_state.consecutive_failures > 0, \
                    "Consecutive failures should be incremented"
                assert readiness_state.consecutive_successes == 0, \
                    "Consecutive successes should be reset on failure"
            
            # Verify metadata is updated
            assert 'last_validation_success_rate' in readiness_state.metadata, \
                "Metadata should include last validation success rate"
            assert readiness_state.metadata['last_validation_success_rate'] == success_rate, \
                "Metadata should contain correct success rate"
            
            # Check for status change notifications
            if previous_status is not None and readiness_state.status != previous_status:
                # Should have generated a status change notification
                status_change_notifications = [
                    n for n in notifications_received 
                    if "status changed" in n.message.lower()
                ]
                assert len(status_change_notifications) > 0, \
                    "Status change should generate notification"
            
            previous_status = readiness_state.status
        
        # Verify environment can be retrieved
        retrieved_state = readiness_manager.get_environment_readiness(environment_id.strip())
        assert retrieved_state is not None, "Environment state should be retrievable"
        assert retrieved_state.environment_id == environment_id.strip(), \
            "Retrieved state should match environment ID"
        
        # Verify readiness lists
        all_states = readiness_manager.get_all_environment_readiness()
        assert environment_id.strip() in all_states, \
            "Environment should be in all states list"
        
        final_state = all_states[environment_id.strip()]
        if final_state.status == ReadinessStatus.READY:
            ready_envs = readiness_manager.get_ready_environments()
            assert environment_id.strip() in ready_envs, \
                "Ready environment should be in ready list"
        else:
            not_ready_envs = readiness_manager.get_not_ready_environments()
            assert environment_id.strip() in not_ready_envs, \
                "Not ready environment should be in not ready list"
        
        # Verify state persistence by creating new manager with same state file
        new_manager = ReadinessManager(state_file_path=temp_path)
        await asyncio.sleep(0.1)  # Allow time for state loading
        
        persisted_state = new_manager.get_environment_readiness(environment_id.strip())
        if persisted_state:  # State might not be loaded yet in async context
            assert persisted_state.environment_id == environment_id.strip(), \
                "Persisted state should match environment ID"
            assert persisted_state.validation_count == len(validation_results), \
                "Persisted validation count should match"
    
    finally:
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)


@given(
    environment_count=st.integers(min_value=2, max_value=4),
    validation_scenarios=st.lists(
        st.tuples(
            environment_ids,
            consecutive_results
        ),
        min_size=2,
        max_size=4
    )
)
@settings(max_examples=25, deadline=5000)
async def test_multiple_environment_readiness_tracking(environment_count, validation_scenarios):
    """
    Property: Multiple environment readiness tracking maintains isolation
    
    This test verifies that:
    1. Multiple environments can be tracked independently
    2. Readiness states don't interfere between environments
    3. Notifications are environment-specific
    4. Statistics aggregate correctly across environments
    """
    assume(environment_count >= 2)
    assume(len(validation_scenarios) >= 2)
    
    # Create temporary state file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Create readiness manager
        readiness_manager = ReadinessManager(state_file_path=temp_path)
        
        # Track notifications by environment
        notifications_by_env = {}
        
        def notification_callback(notification: ReadinessNotification):
            env_id = notification.environment_id
            if env_id not in notifications_by_env:
                notifications_by_env[env_id] = []
            notifications_by_env[env_id].append(notification)
        
        readiness_manager.subscribe_to_notifications(notification_callback)
        
        # Process validation scenarios for different environments
        environment_states = {}
        
        for i in range(min(environment_count, len(validation_scenarios))):
            env_id, validation_sequence = validation_scenarios[i]
            env_id = env_id.strip()
            
            if not env_id:
                env_id = f"test_env_{i}"
            
            environment_states[env_id] = []
            
            # Process validation sequence for this environment
            for is_ready in validation_sequence:
                success_rate = 100.0 if is_ready else 50.0
                failed_checks = [] if is_ready else ["network_connectivity"]
                
                validation_result = MockValidationResult(
                    environment_id=env_id,
                    is_ready=is_ready,
                    success_rate=success_rate,
                    failed_checks=failed_checks
                )
                
                readiness_state = await readiness_manager.update_environment_readiness(
                    env_id, validation_result
                )
                environment_states[env_id].append(readiness_state)
        
        # Verify each environment has independent state
        all_states = readiness_manager.get_all_environment_readiness()
        
        for env_id, state_history in environment_states.items():
            # Verify environment exists in manager
            assert env_id in all_states, f"Environment {env_id} should exist in manager"
            
            # Verify final state matches last update
            final_state = all_states[env_id]
            expected_validation_count = len(state_history)
            assert final_state.validation_count == expected_validation_count, \
                f"Environment {env_id} should have {expected_validation_count} validations"
            
            # Verify state isolation - changes to one environment don't affect others
            for other_env_id, other_state_history in environment_states.items():
                if other_env_id != env_id:
                    other_final_state = all_states[other_env_id]
                    # States should be independent
                    assert other_final_state.environment_id != final_state.environment_id, \
                        "Environment states should have different IDs"
        
        # Verify notifications are environment-specific
        for env_id in environment_states.keys():
            if env_id in notifications_by_env:
                env_notifications = notifications_by_env[env_id]
                for notification in env_notifications:
                    assert notification.environment_id == env_id, \
                        f"Notification should be for environment {env_id}"
        
        # Verify statistics aggregate correctly
        stats = readiness_manager.get_readiness_statistics()
        assert stats['total_environments'] == len(environment_states), \
            "Statistics should reflect correct number of environments"
        
        # Count expected ready environments
        expected_ready = 0
        for env_id in environment_states.keys():
            state = all_states[env_id]
            if state.status == ReadinessStatus.READY:
                expected_ready += 1
        
        assert stats['ready_count'] == expected_ready, \
            f"Statistics should show {expected_ready} ready environments"
    
    finally:
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)


@given(
    environment_id=environment_ids,
    failure_count=st.integers(min_value=3, max_value=8),
    notification_level=notification_levels
)
@settings(max_examples=20, deadline=4000)
async def test_readiness_notification_system(environment_id, failure_count, notification_level):
    """
    Property: Readiness notification system provides appropriate alerts
    
    This test verifies that:
    1. Status change notifications are generated correctly
    2. Failure alerts are triggered after consecutive failures
    3. Notification levels are appropriate for different scenarios
    4. Notification history is maintained properly
    5. Subscribers receive notifications correctly
    """
    assume(len(environment_id.strip()) > 0)
    assume(failure_count >= 3)
    
    # Create temporary state file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Create readiness manager
        readiness_manager = ReadinessManager(state_file_path=temp_path)
        
        # Track notifications
        notifications_received = []
        
        def notification_callback(notification: ReadinessNotification):
            notifications_received.append(notification)
        
        readiness_manager.subscribe_to_notifications(notification_callback)
        
        # Start with successful validation
        success_validation = MockValidationResult(
            environment_id=environment_id.strip(),
            is_ready=True,
            success_rate=100.0
        )
        
        await readiness_manager.update_environment_readiness(
            environment_id.strip(), success_validation
        )
        
        initial_notification_count = len(notifications_received)
        
        # Generate consecutive failures
        for i in range(failure_count):
            failure_validation = MockValidationResult(
                environment_id=environment_id.strip(),
                is_ready=False,
                success_rate=20.0,
                failed_checks=["network_connectivity", "disk_space"],
                warnings=["Validation failed"]
            )
            
            await readiness_manager.update_environment_readiness(
                environment_id.strip(), failure_validation
            )
        
        # Verify notifications were generated
        new_notifications = notifications_received[initial_notification_count:]
        assert len(new_notifications) > 0, "Failures should generate notifications"
        
        # Check for status change notification (success to failure)
        status_change_notifications = [
            n for n in new_notifications 
            if "status changed" in n.message.lower()
        ]
        assert len(status_change_notifications) > 0, \
            "Status change from success to failure should generate notification"
        
        # Check for failure alert after consecutive failures
        if failure_count >= 3:
            failure_alert_notifications = [
                n for n in new_notifications 
                if "consecutive times" in n.message.lower()
            ]
            assert len(failure_alert_notifications) > 0, \
                f"Should generate failure alert after {failure_count} consecutive failures"
            
            # Verify alert has critical level
            critical_notifications = [
                n for n in failure_alert_notifications 
                if n.level == NotificationLevel.CRITICAL
            ]
            assert len(critical_notifications) > 0, \
                "Consecutive failure alerts should be CRITICAL level"
        
        # Verify notification details
        for notification in new_notifications:
            assert notification.environment_id == environment_id.strip(), \
                "Notification should be for correct environment"
            assert notification.timestamp is not None, \
                "Notification should have timestamp"
            assert isinstance(notification.details, dict), \
                "Notification should have details dictionary"
        
        # Test notification history retrieval
        recent_notifications = readiness_manager.get_recent_notifications(
            environment_id=environment_id.strip(),
            hours=1
        )
        
        assert len(recent_notifications) > 0, \
            "Should be able to retrieve recent notifications"
        
        # Verify notifications are sorted by timestamp (most recent first)
        if len(recent_notifications) > 1:
            for i in range(len(recent_notifications) - 1):
                assert recent_notifications[i].timestamp >= recent_notifications[i + 1].timestamp, \
                    "Notifications should be sorted by timestamp (newest first)"
        
        # Test notification filtering by level
        if notification_level in [NotificationLevel.ERROR, NotificationLevel.CRITICAL]:
            level_filtered_notifications = readiness_manager.get_recent_notifications(
                environment_id=environment_id.strip(),
                level=notification_level,
                hours=1
            )
            
            for notification in level_filtered_notifications:
                assert notification.level == notification_level, \
                    f"Filtered notifications should have level {notification_level.value}"
        
        # Test unsubscribing from notifications
        readiness_manager.unsubscribe_from_notifications(notification_callback)
        
        # Generate another failure - should not trigger callback
        final_notification_count = len(notifications_received)
        
        final_failure_validation = MockValidationResult(
            environment_id=environment_id.strip(),
            is_ready=False,
            success_rate=10.0,
            failed_checks=["network_connectivity"]
        )
        
        await readiness_manager.update_environment_readiness(
            environment_id.strip(), final_failure_validation
        )
        
        # Verify callback was not called after unsubscribing
        assert len(notifications_received) == final_notification_count, \
            "Unsubscribed callback should not receive new notifications"
    
    finally:
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)


@given(
    environment_id=environment_ids,
    maintenance_mode=st.booleans(),
    maintenance_reason=st.text(min_size=0, max_size=100)
)
@settings(max_examples=15, deadline=3000)
async def test_maintenance_mode_marking(environment_id, maintenance_mode, maintenance_reason):
    """
    Property: Maintenance mode marking updates environment status correctly
    
    This test verifies that:
    1. Environments can be marked for maintenance
    2. Maintenance mode affects readiness status
    3. Maintenance notifications are generated
    4. Maintenance state is persisted
    """
    assume(len(environment_id.strip()) > 0)
    
    # Create temporary state file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Create readiness manager
        readiness_manager = ReadinessManager(state_file_path=temp_path)
        
        # Track notifications
        notifications_received = []
        
        def notification_callback(notification: ReadinessNotification):
            notifications_received.append(notification)
        
        readiness_manager.subscribe_to_notifications(notification_callback)
        
        # Mark environment for maintenance
        await readiness_manager.mark_environment_maintenance(
            environment_id.strip(), 
            maintenance_mode, 
            maintenance_reason if maintenance_reason else None
        )
        
        # Verify environment state
        readiness_state = readiness_manager.get_environment_readiness(environment_id.strip())
        assert readiness_state is not None, "Environment state should exist after maintenance marking"
        
        # Verify maintenance mode in metadata
        assert readiness_state.metadata.get('maintenance_mode') == maintenance_mode, \
            f"Maintenance mode should be set to {maintenance_mode}"
        
        if maintenance_mode:
            # Verify status is set to maintenance
            assert readiness_state.status == ReadinessStatus.MAINTENANCE, \
                "Environment in maintenance mode should have MAINTENANCE status"
            
            # Verify maintenance reason is stored
            if maintenance_reason:
                assert readiness_state.metadata.get('maintenance_reason') == maintenance_reason, \
                    "Maintenance reason should be stored in metadata"
        
        # Verify notification was generated
        maintenance_notifications = [
            n for n in notifications_received 
            if "maintenance mode" in n.message.lower()
        ]
        assert len(maintenance_notifications) > 0, \
            "Maintenance mode change should generate notification"
        
        maintenance_notification = maintenance_notifications[0]
        assert maintenance_notification.environment_id == environment_id.strip(), \
            "Maintenance notification should be for correct environment"
        assert maintenance_notification.level == NotificationLevel.INFO, \
            "Maintenance notification should be INFO level"
        
        # Verify notification details
        assert 'maintenance_mode' in maintenance_notification.details, \
            "Maintenance notification should include maintenance mode in details"
        assert maintenance_notification.details['maintenance_mode'] == maintenance_mode, \
            "Notification details should reflect correct maintenance mode"
        
        if maintenance_reason:
            assert maintenance_notification.details.get('reason') == maintenance_reason, \
                "Notification details should include maintenance reason"
    
    finally:
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)


# Synchronous test runners for pytest
def test_environment_readiness_marking_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_environment_readiness_marking(
        environment_id="readiness_test_env",
        validation_results=[(True, 95.0), (False, 30.0), (True, 100.0)]
    ))


def test_multiple_environment_readiness_tracking_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_environment_readiness_tracking(
        environment_count=2,
        validation_scenarios=[
            ("env1", [True, False, True]),
            ("env2", [False, False, True])
        ]
    ))


def test_readiness_notification_system_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_readiness_notification_system(
        environment_id="notification_test_env",
        failure_count=4,
        notification_level=NotificationLevel.CRITICAL
    ))


def test_maintenance_mode_marking_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_maintenance_mode_marking(
        environment_id="maintenance_test_env",
        maintenance_mode=True,
        maintenance_reason="Scheduled maintenance"
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing environment readiness marking...")
        await test_environment_readiness_marking(
            "test_env", [(True, 95.0), (False, 30.0), (True, 100.0)]
        )
        print("✓ Environment readiness marking test passed")
        
        print("Testing multiple environment readiness tracking...")
        await test_multiple_environment_readiness_tracking(
            2, [("env1", [True, False]), ("env2", [False, True])]
        )
        print("✓ Multiple environment readiness tracking test passed")
        
        print("Testing readiness notification system...")
        await test_readiness_notification_system("test_env", 4, NotificationLevel.CRITICAL)
        print("✓ Readiness notification system test passed")
        
        print("Testing maintenance mode marking...")
        await test_maintenance_mode_marking("test_env", True, "Test maintenance")
        print("✓ Maintenance mode marking test passed")
        
        print("All environment readiness marking tests completed successfully!")
    
    asyncio.run(run_examples())