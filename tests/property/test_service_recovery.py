"""Property-based tests for service recovery.

**Feature: test-execution-orchestrator, Property 12: Service recovery**
**Validates: Requirements 5.3**

Property 12: Service recovery
For any orchestrator service restart with queued tests, all previously queued tests 
should be recovered and resume execution.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import threading
import time
import tempfile
import os
import json
from datetime import datetime, timedelta

from orchestrator.service_recovery_manager import ServiceRecoveryManager, PersistedTestState, PersistedPlanState
from orchestrator.status_tracker import StatusTracker
from orchestrator.queue_monitor import QueueMonitor
from orchestrator.timeout_manager import TimeoutManager
from orchestrator.config import OrchestratorConfig


def create_mock_config():
    """Create a mock orchestrator configuration for testing."""
    config = Mock(spec=OrchestratorConfig)
    config.max_environments = 10
    config.docker_enabled = True
    config.qemu_enabled = True
    config.physical_enabled = False
    config.health_check_interval = 30
    config.enable_persistence = True
    return config


# Custom strategies for generating test data
@st.composite
def gen_simple_test_state(draw):
    """Generate a simple test state for testing."""
    # Use a more unique test ID to avoid collisions
    test_id = f"test_{draw(st.integers(min_value=1, max_value=100000))}"
    plan_id = f"plan_{draw(st.integers(min_value=1, max_value=10))}"
    status = draw(st.sampled_from(['queued', 'running']))
    
    return PersistedTestState(
        test_id=test_id,
        plan_id=plan_id,
        status=status,
        environment_id=None,
        started_at=None,
        timeout_seconds=300,
        retry_count=0
    )


@st.composite
def gen_plan_state(draw):
    """Generate a random persisted plan state."""
    plan_id = f"plan_{draw(st.integers(min_value=1, max_value=1000))}"
    submission_id = f"sub_{draw(st.integers(min_value=1, max_value=10000))}"
    status = draw(st.sampled_from(['queued', 'running', 'completed', 'failed']))
    total_tests = draw(st.integers(min_value=1, max_value=20))
    completed_tests = draw(st.integers(min_value=0, max_value=total_tests))
    failed_tests = draw(st.integers(min_value=0, max_value=total_tests - completed_tests))
    
    # Generate started_at timestamp for running plans
    started_at = None
    if status == 'running':
        # Recent timestamp (within last hour)
        minutes_ago = draw(st.integers(min_value=1, max_value=60))
        started_at = (datetime.utcnow() - timedelta(minutes=minutes_ago)).isoformat()
    
    # Generate test states for this plan
    test_states = []
    for i in range(total_tests):
        test_state = PersistedTestState(
            test_id=f"{plan_id}_test_{i}",
            plan_id=plan_id,
            status=draw(st.sampled_from(['queued', 'running', 'completed', 'failed'])),
            environment_id=draw(st.one_of(st.none(), st.text(min_size=5, max_size=20))),
            started_at=started_at,
            timeout_seconds=draw(st.integers(min_value=30, max_value=3600)),
            retry_count=draw(st.integers(min_value=0, max_value=3))
        )
        test_states.append(test_state)
    
    return PersistedPlanState(
        plan_id=plan_id,
        submission_id=submission_id,
        status=status,
        total_tests=total_tests,
        completed_tests=completed_tests,
        failed_tests=failed_tests,
        started_at=started_at,
        test_states=test_states
    )


@given(st.lists(gen_simple_test_state(), min_size=1, max_size=2))
@settings(max_examples=5, deadline=10000)
def test_queued_tests_recovered_on_startup(test_states: List[PersistedTestState]):
    """
    Property: For any set of queued tests when the orchestrator service restarts,
    all queued tests should be recovered and resume execution.
    
    **Feature: test-execution-orchestrator, Property 12: Service recovery**
    **Validates: Requirements 5.3**
    """
    # Filter to only queued and running tests (the ones that should be recovered)
    recoverable_tests = [t for t in test_states if t.status in ['queued', 'running']]
    assume(len(recoverable_tests) > 0)
    
    # Ensure unique test IDs to avoid overwrites
    test_ids = [t.test_id for t in recoverable_tests]
    assume(len(set(test_ids)) == len(test_ids))  # All test IDs must be unique
    
    # Create temporary state directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the threading to prevent background threads from hanging tests
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            recovery_manager = ServiceRecoveryManager(
                config=create_mock_config(),
                state_dir=temp_dir
            )
            
            try:
                # Start the recovery manager
                start_success = recovery_manager.start()
                assert start_success, "Recovery manager should start successfully"
                
                # Persist test states (simulating previous service run)
                for test_state in recoverable_tests:
                    # First persist the plan state for this test
                    recovery_manager.persist_plan_state(
                        plan_id=test_state.plan_id,
                        submission_id=f"sub_{test_state.plan_id}",
                        status="running",
                        total_tests=1,
                        completed_tests=0,
                        failed_tests=0,
                        started_at=None
                    )
                    
                    # Then persist the test state
                    recovery_manager.persist_test_state(
                        test_id=test_state.test_id,
                        plan_id=test_state.plan_id,
                        status=test_state.status,
                        environment_id=test_state.environment_id,
                        started_at=None,
                        timeout_seconds=test_state.timeout_seconds
                    )
                
                # Force save state to disk
                save_success = recovery_manager.force_state_save()
                assert save_success, "State should be saved successfully"
                
                # Stop the recovery manager (simulating service shutdown)
                stop_success = recovery_manager.stop()
                assert stop_success, "Recovery manager should stop successfully"
                
                # Create new recovery manager instance (simulating service restart)
                new_recovery_manager = ServiceRecoveryManager(
                    config=create_mock_config(),
                    state_dir=temp_dir
                )
                
                # Create mock components for recovery
                mock_status_tracker = Mock(spec=StatusTracker)
                mock_queue_monitor = Mock(spec=QueueMonitor)
                mock_timeout_manager = Mock(spec=TimeoutManager)
                
                # Start new recovery manager
                start_success = new_recovery_manager.start()
                assert start_success, "New recovery manager should start successfully"
                
                # Perform recovery on startup
                recovery_results = new_recovery_manager.recover_on_startup(
                    status_tracker=mock_status_tracker,
                    queue_monitor=mock_queue_monitor,
                    timeout_manager=mock_timeout_manager
                )
                
                # Property 1: Recovery should succeed without errors
                assert 'error' not in recovery_results, f"Recovery should not have errors: {recovery_results}"
                
                # Property 2: All recoverable tests should be recovered
                tests_recovered = recovery_results.get('tests_recovered', 0)
                assert tests_recovered == len(recoverable_tests), \
                    f"Should recover {len(recoverable_tests)} tests, got {tests_recovered}"
                
                # Property 3: Status tracker should be updated for each recovered test
                expected_calls = len(recoverable_tests)
                actual_calls = mock_status_tracker.update_test_status.call_count
                assert actual_calls >= expected_calls, \
                    f"Status tracker should be called at least {expected_calls} times, got {actual_calls}"
                
                # Property 4: Running tests should have timeout monitoring restored
                running_tests = [t for t in recoverable_tests if t.status == 'running']
                if running_tests:
                    timeout_calls = mock_timeout_manager.add_monitor.call_count
                    assert timeout_calls >= len(running_tests), \
                        f"Timeout manager should be called for {len(running_tests)} running tests, got {timeout_calls}"
                
                # Property 5: Recovery statistics should be updated
                recovery_status = new_recovery_manager.get_recovery_status()
                assert recovery_status['statistics']['tests_recovered'] >= len(recoverable_tests), \
                    "Recovery statistics should reflect recovered tests"
                
            finally:
                # Clean up
                if recovery_manager._is_running:
                    recovery_manager.stop()
                if new_recovery_manager._is_running:
                    new_recovery_manager.stop()


@given(st.lists(gen_simple_test_state(), min_size=1, max_size=2))
@settings(max_examples=5, deadline=10000)
def test_state_persistence_across_restart(test_states: List[PersistedTestState]):
    """
    Property: For any persisted state before service restart, the same state
    should be available after restart and recovery.
    
    **Feature: test-execution-orchestrator, Property 12: Service recovery**
    **Validates: Requirements 5.3**
    """
    # Filter to recoverable tests
    recoverable_tests = [t for t in test_states if t.status in ['queued', 'running']]
    assume(len(recoverable_tests) > 0)
    
    # Create temporary state directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the threading to prevent background threads from hanging tests
        with patch('threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            recovery_manager = ServiceRecoveryManager(
                config=create_mock_config(),
                state_dir=temp_dir
            )
            
            try:
                # Start the recovery manager
                start_success = recovery_manager.start()
                assert start_success, "Recovery manager should start successfully"
                
                # Persist test states (simulating previous service run)
                for test_state in recoverable_tests:
                    # First persist the plan state for this test
                    recovery_manager.persist_plan_state(
                        plan_id=test_state.plan_id,
                        submission_id=f"sub_{test_state.plan_id}",
                        status="running",
                        total_tests=1,
                        completed_tests=0,
                        failed_tests=0,
                        started_at=None
                    )
                    
                    # Then persist the test state
                    recovery_manager.persist_test_state(
                        test_id=test_state.test_id,
                        plan_id=test_state.plan_id,
                        status=test_state.status,
                        environment_id=test_state.environment_id,
                        started_at=None,
                        timeout_seconds=test_state.timeout_seconds
                    )
                
                # Get initial recovery status
                initial_status = recovery_manager.get_recovery_status()
                initial_persisted_tests = initial_status['persisted_tests']
                
                # Force save state to disk
                save_success = recovery_manager.force_state_save()
                assert save_success, "State should be saved successfully"
                
                # Stop the recovery manager (simulating service shutdown)
                stop_success = recovery_manager.stop()
                assert stop_success, "Recovery manager should stop successfully"
                
                # Create new recovery manager instance (simulating service restart)
                new_recovery_manager = ServiceRecoveryManager(
                    config=create_mock_config(),
                    state_dir=temp_dir
                )
                
                # Start new recovery manager
                start_success = new_recovery_manager.start()
                assert start_success, "New recovery manager should start successfully"
                
                # Property 1: State should be loaded from disk
                loaded_status = new_recovery_manager.get_recovery_status()
                loaded_persisted_tests = loaded_status['persisted_tests']
                
                assert loaded_persisted_tests == initial_persisted_tests, \
                    f"Should load {initial_persisted_tests} persisted tests, got {loaded_persisted_tests}"
                
                # Property 2: State file should exist and be accessible
                assert loaded_status['state_file_exists'], "State file should exist after restart"
                
                # Property 3: Statistics should be preserved
                assert 'statistics' in loaded_status, "Statistics should be preserved across restart"
                
            finally:
                # Clean up
                if recovery_manager._is_running:
                    recovery_manager.stop()
                if new_recovery_manager._is_running:
                    new_recovery_manager.stop()