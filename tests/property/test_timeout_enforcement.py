"""Property-based tests for timeout enforcement.

This module tests the timeout enforcement property:
Property 7: For any test that exceeds its specified timeout limit, 
the orchestrator should terminate the test and record a timeout status 
within a reasonable grace period.

**Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
**Validates: Requirements 4.3, 5.2**
"""

import pytest
import time
import threading
import subprocess
import os
import signal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Optional, Dict, Any

from orchestrator.timeout_manager import TimeoutManager, TimeoutPolicy, TimeoutAction


class MockProcess:
    """Mock process for testing timeout enforcement."""
    
    def __init__(self, process_id: int, should_terminate: bool = True):
        self.process_id = process_id
        self.should_terminate = should_terminate
        self.terminated = False
        self.killed = False
        self.start_time = time.time()
        
    def terminate(self):
        """Simulate process termination."""
        if self.should_terminate:
            self.terminated = True
            return True
        return False
    
    def kill(self):
        """Simulate process kill."""
        self.killed = True
        return True
    
    def is_running(self) -> bool:
        """Check if process is still running."""
        return not (self.terminated or self.killed)


class MockContainer:
    """Mock container for testing timeout enforcement."""
    
    def __init__(self, container_id: str, should_stop: bool = True):
        self.container_id = container_id
        self.should_stop = should_stop
        self.stopped = False
        self.killed = False
        self.start_time = time.time()
    
    def stop(self):
        """Simulate container stop."""
        if self.should_stop:
            self.stopped = True
            return True
        return False
    
    def kill(self):
        """Simulate container kill."""
        self.killed = True
        return True
    
    def is_running(self) -> bool:
        """Check if container is still running."""
        return not (self.stopped or self.killed)


@pytest.fixture
def timeout_manager():
    """Create a timeout manager for testing."""
    manager = TimeoutManager()
    manager.start()
    yield manager
    manager.stop()


@pytest.fixture
def mock_processes():
    """Dictionary to track mock processes."""
    return {}


@pytest.fixture
def mock_containers():
    """Dictionary to track mock containers."""
    return {}


def create_long_running_process() -> int:
    """Create a real long-running process for testing."""
    # Create a simple Python process that sleeps
    process = subprocess.Popen([
        'python3', '-c', 
        'import time; time.sleep(300)'  # Sleep for 5 minutes
    ])
    return process.pid


def terminate_process_if_exists(pid: int):
    """Terminate a process if it exists."""
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.1)  # Brief wait
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Already terminated
    except ProcessLookupError:
        pass  # Process doesn't exist


@given(
    timeout_seconds=st.integers(min_value=1, max_value=10),
    grace_period=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=3, deadline=60000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_timeout_enforcement_with_real_process(timeout_manager, timeout_seconds, grace_period):
    """
    **Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
    
    Property: For any test that exceeds its specified timeout limit, 
    the orchestrator should terminate the test and record a timeout status 
    within a reasonable grace period.
    
    **Validates: Requirements 4.3, 5.2**
    """
    # Create a real long-running process
    process_pid = create_long_running_process()
    
    try:
        # Verify process exists
        assert timeout_manager._process_exists(process_pid), "Test process should exist"
        
        # Create timeout policy
        policy = TimeoutPolicy(
            timeout_seconds=timeout_seconds,
            action=TimeoutAction.TERMINATE,
            grace_period=grace_period
        )
        
        # Track timeout events
        timeout_events = []
        
        def timeout_callback(test_id: str, reason: str):
            timeout_events.append((test_id, reason, time.time()))
        
        # Add monitor for the process
        test_id = f"test_timeout_{process_pid}"
        success = timeout_manager.add_monitor(
            test_id=test_id,
            timeout_seconds=timeout_seconds,
            process_id=process_pid,
            policy=policy,
            callback=timeout_callback
        )
        
        assert success, "Should successfully add timeout monitor"
        
        # Wait for timeout to occur (with some buffer)
        max_wait_time = timeout_seconds + grace_period + 5  # Extra buffer for processing
        start_time = time.time()
        
        # Wait for timeout enforcement
        while time.time() - start_time < max_wait_time:
            if not timeout_manager._process_exists(process_pid):
                break
            time.sleep(0.1)
        
        # Property: Process should be terminated within reasonable grace period
        elapsed_time = time.time() - start_time
        assert not timeout_manager._process_exists(process_pid), \
            f"Process should be terminated after timeout ({elapsed_time:.1f}s elapsed)"
        
        # Property: Timeout should be detected within reasonable time
        assert elapsed_time <= timeout_seconds + grace_period + 3, \
            f"Timeout enforcement took too long: {elapsed_time:.1f}s > {timeout_seconds + grace_period + 3}s"
        
        # Property: Timeout callback should be called
        assert len(timeout_events) > 0, "Timeout callback should be called"
        
        # Property: Timeout event should indicate timeout exceeded
        timeout_event = next((event for event in timeout_events if "timeout_exceeded" in event[1]), None)
        assert timeout_event is not None, "Should receive timeout_exceeded event"
        
        # Property: Monitor should be marked as terminated
        assert timeout_manager.is_timeout_exceeded(test_id), "Test should be marked as timed out"
        
    finally:
        # Cleanup: ensure process is terminated
        terminate_process_if_exists(process_pid)
        timeout_manager.remove_monitor(test_id)


@given(
    timeout_seconds=st.integers(min_value=1, max_value=5),
    num_tests=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=10, deadline=20000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_timeout_enforcement_multiple_tests(timeout_manager, timeout_seconds, num_tests):
    """
    **Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
    
    Property: For any set of tests that exceed their timeout limits,
    each should be terminated independently within their grace periods.
    
    **Validates: Requirements 4.3, 5.2**
    """
    processes = []
    test_ids = []
    timeout_events = []
    
    def timeout_callback(test_id: str, reason: str):
        timeout_events.append((test_id, reason, time.time()))
    
    try:
        # Create multiple long-running processes
        for i in range(num_tests):
            process_pid = create_long_running_process()
            processes.append(process_pid)
            
            test_id = f"test_multi_timeout_{i}_{process_pid}"
            test_ids.append(test_id)
            
            # Add monitor for each process
            policy = TimeoutPolicy(
                timeout_seconds=timeout_seconds,
                action=TimeoutAction.TERMINATE,
                grace_period=2
            )
            
            success = timeout_manager.add_monitor(
                test_id=test_id,
                timeout_seconds=timeout_seconds,
                process_id=process_pid,
                policy=policy,
                callback=timeout_callback
            )
            
            assert success, f"Should successfully add timeout monitor for test {i}"
        
        # Wait for all timeouts to occur
        max_wait_time = timeout_seconds + 5  # Buffer for processing
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check if all processes are terminated
            running_processes = [pid for pid in processes if timeout_manager._process_exists(pid)]
            if not running_processes:
                break
            time.sleep(0.1)
        
        # Property: All processes should be terminated
        for i, process_pid in enumerate(processes):
            assert not timeout_manager._process_exists(process_pid), \
                f"Process {i} (PID {process_pid}) should be terminated after timeout"
        
        # Property: All tests should be marked as timed out
        for test_id in test_ids:
            assert timeout_manager.is_timeout_exceeded(test_id), \
                f"Test {test_id} should be marked as timed out"
        
        # Property: Should receive timeout events for all tests
        timeout_exceeded_events = [event for event in timeout_events if "timeout_exceeded" in event[1]]
        assert len(timeout_exceeded_events) >= num_tests, \
            f"Should receive timeout events for all {num_tests} tests, got {len(timeout_exceeded_events)}"
        
    finally:
        # Cleanup: ensure all processes are terminated
        for process_pid in processes:
            terminate_process_if_exists(process_pid)
        for test_id in test_ids:
            timeout_manager.remove_monitor(test_id)


@given(
    timeout_seconds=st.integers(min_value=2, max_value=8),
    action_type=st.sampled_from([TimeoutAction.TERMINATE, TimeoutAction.KILL, TimeoutAction.NOTIFY])
)
@settings(max_examples=15, deadline=25000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_timeout_enforcement_different_actions(timeout_manager, timeout_seconds, action_type):
    """
    **Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
    
    Property: For any timeout action type (terminate, kill, notify),
    the orchestrator should handle timeout enforcement according to the policy.
    
    **Validates: Requirements 4.3, 5.2**
    """
    process_pid = create_long_running_process()
    timeout_events = []
    
    def timeout_callback(test_id: str, reason: str):
        timeout_events.append((test_id, reason, time.time()))
    
    try:
        # Create timeout policy with specified action
        policy = TimeoutPolicy(
            timeout_seconds=timeout_seconds,
            action=action_type,
            grace_period=2
        )
        
        test_id = f"test_action_{action_type.value}_{process_pid}"
        
        # Add monitor
        success = timeout_manager.add_monitor(
            test_id=test_id,
            timeout_seconds=timeout_seconds,
            process_id=process_pid,
            policy=policy,
            callback=timeout_callback
        )
        
        assert success, "Should successfully add timeout monitor"
        
        # Wait for timeout to occur
        max_wait_time = timeout_seconds + 5
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if action_type == TimeoutAction.NOTIFY:
                # For notify action, process should still be running
                if len(timeout_events) > 0:
                    break
            else:
                # For terminate/kill actions, process should be stopped
                if not timeout_manager._process_exists(process_pid):
                    break
            time.sleep(0.1)
        
        # Property: Timeout callback should be called
        assert len(timeout_events) > 0, "Timeout callback should be called"
        
        # Property: Behavior should match action type
        if action_type == TimeoutAction.NOTIFY:
            # Process should still be running for notify action
            assert timeout_manager._process_exists(process_pid), \
                "Process should still be running for NOTIFY action"
        else:
            # Process should be terminated for TERMINATE/KILL actions
            assert not timeout_manager._process_exists(process_pid), \
                f"Process should be terminated for {action_type.value} action"
        
        # Property: Test should be marked as timed out regardless of action
        assert timeout_manager.is_timeout_exceeded(test_id), \
            "Test should be marked as timed out regardless of action type"
        
    finally:
        # Cleanup
        terminate_process_if_exists(process_pid)
        timeout_manager.remove_monitor(test_id)


@given(
    timeout_seconds=st.integers(min_value=1, max_value=5),
    warning_threshold=st.floats(min_value=0.1, max_value=0.9)
)
@settings(max_examples=10, deadline=20000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_timeout_warning_before_enforcement(timeout_manager, timeout_seconds, warning_threshold):
    """
    **Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
    
    Property: For any test approaching timeout, a warning should be sent
    before the actual timeout enforcement occurs.
    
    **Validates: Requirements 4.3, 5.2**
    """
    process_pid = create_long_running_process()
    timeout_events = []
    
    def timeout_callback(test_id: str, reason: str):
        timeout_events.append((test_id, reason, time.time()))
    
    try:
        # Create timeout policy with warning threshold
        policy = TimeoutPolicy(
            timeout_seconds=timeout_seconds,
            warning_threshold=warning_threshold,
            action=TimeoutAction.TERMINATE,
            grace_period=1
        )
        
        test_id = f"test_warning_{process_pid}"
        
        # Add monitor
        success = timeout_manager.add_monitor(
            test_id=test_id,
            timeout_seconds=timeout_seconds,
            process_id=process_pid,
            policy=policy,
            callback=timeout_callback
        )
        
        assert success, "Should successfully add timeout monitor"
        
        # Wait for both warning and timeout
        max_wait_time = timeout_seconds + 3
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if not timeout_manager._process_exists(process_pid):
                break
            time.sleep(0.1)
        
        # Property: Process should be terminated
        assert not timeout_manager._process_exists(process_pid), \
            "Process should be terminated after timeout"
        
        # Property: Should receive both warning and timeout events
        warning_events = [event for event in timeout_events if "timeout_warning" in event[1]]
        timeout_events_exceeded = [event for event in timeout_events if "timeout_exceeded" in event[1]]
        
        assert len(warning_events) > 0, "Should receive timeout warning event"
        assert len(timeout_events_exceeded) > 0, "Should receive timeout exceeded event"
        
        # Property: Warning should come before timeout exceeded
        if warning_events and timeout_events_exceeded:
            warning_time = warning_events[0][2]
            timeout_time = timeout_events_exceeded[0][2]
            assert warning_time < timeout_time, "Warning should come before timeout exceeded"
        
    finally:
        # Cleanup
        terminate_process_if_exists(process_pid)
        timeout_manager.remove_monitor(test_id)


@given(
    timeout_seconds=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=5, deadline=15000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_timeout_enforcement_with_container_mock(timeout_manager, timeout_seconds):
    """
    **Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
    
    Property: For any test running in a container that exceeds timeout,
    the container should be terminated within the grace period.
    
    **Validates: Requirements 4.3, 5.2**
    """
    container_id = f"test_container_{int(time.time())}"
    timeout_events = []
    
    def timeout_callback(test_id: str, reason: str):
        timeout_events.append((test_id, reason, time.time()))
    
    # Mock container operations
    with patch('subprocess.run') as mock_run:
        # Mock successful container stop
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        policy = TimeoutPolicy(
            timeout_seconds=timeout_seconds,
            action=TimeoutAction.TERMINATE,
            grace_period=1
        )
        
        test_id = f"test_container_timeout_{container_id}"
        
        # Add monitor for container
        success = timeout_manager.add_monitor(
            test_id=test_id,
            timeout_seconds=timeout_seconds,
            container_id=container_id,
            policy=policy,
            callback=timeout_callback
        )
        
        assert success, "Should successfully add timeout monitor for container"
        
        # Wait for timeout to occur
        max_wait_time = timeout_seconds + 3
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            if len(timeout_events) > 0:
                # Check if timeout exceeded event received
                timeout_exceeded = any("timeout_exceeded" in event[1] for event in timeout_events)
                if timeout_exceeded:
                    break
            time.sleep(0.1)
        
        # Property: Timeout callback should be called
        assert len(timeout_events) > 0, "Timeout callback should be called"
        
        # Property: Should receive timeout exceeded event
        timeout_exceeded_events = [event for event in timeout_events if "timeout_exceeded" in event[1]]
        assert len(timeout_exceeded_events) > 0, "Should receive timeout exceeded event"
        
        # Property: Docker stop should be called
        mock_run.assert_called()
        
        # Verify docker stop was called with correct container ID
        docker_stop_calls = [call for call in mock_run.call_args_list 
                           if call[0][0][:2] == ['docker', 'stop']]
        assert len(docker_stop_calls) > 0, "Docker stop should be called"
        assert container_id in docker_stop_calls[0][0][0], "Should call docker stop with correct container ID"
        
        # Property: Test should be marked as timed out
        assert timeout_manager.is_timeout_exceeded(test_id), "Test should be marked as timed out"
        
        # Cleanup
        timeout_manager.remove_monitor(test_id)


def test_timeout_enforcement_edge_cases(timeout_manager):
    """
    **Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
    
    Property: Timeout enforcement should handle edge cases gracefully
    (non-existent processes, permission errors, etc.).
    
    **Validates: Requirements 4.3, 5.2**
    """
    timeout_events = []
    
    def timeout_callback(test_id: str, reason: str):
        timeout_events.append((test_id, reason, time.time()))
    
    # Test with non-existent process ID
    fake_pid = 999999  # Very unlikely to exist
    
    policy = TimeoutPolicy(
        timeout_seconds=1,
        action=TimeoutAction.TERMINATE,
        grace_period=1
    )
    
    test_id = f"test_fake_pid_{fake_pid}"
    
    # Add monitor for non-existent process
    success = timeout_manager.add_monitor(
        test_id=test_id,
        timeout_seconds=1,
        process_id=fake_pid,
        policy=policy,
        callback=timeout_callback
    )
    
    assert success, "Should successfully add timeout monitor even for non-existent process"
    
    # Wait for timeout
    time.sleep(2.5)
    
    # Property: Should handle non-existent process gracefully
    assert len(timeout_events) > 0, "Should receive timeout event even for non-existent process"
    
    # Property: Test should be marked as timed out
    assert timeout_manager.is_timeout_exceeded(test_id), "Test should be marked as timed out"
    
    # Cleanup
    timeout_manager.remove_monitor(test_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])