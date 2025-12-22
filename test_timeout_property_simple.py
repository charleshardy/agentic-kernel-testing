#!/usr/bin/env python3
"""Simple property-based test for timeout enforcement."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from hypothesis import given, strategies as st, settings
import subprocess
import time
import signal
from orchestrator.timeout_manager import TimeoutManager, TimeoutPolicy, TimeoutAction


def create_long_running_process() -> int:
    """Create a real long-running process for testing."""
    process = subprocess.Popen([
        'python3', '-c', 
        'import time; time.sleep(300)'  # Sleep for 5 minutes
    ])
    return process.pid


def terminate_process_if_exists(pid: int):
    """Terminate a process if it exists."""
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.1)
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        pass


@given(
    timeout_seconds=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=3, deadline=30000)
def test_timeout_enforcement_property(timeout_seconds):
    """
    **Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
    
    Property: For any test that exceeds its specified timeout limit, 
    the orchestrator should terminate the test and record a timeout status 
    within a reasonable grace period.
    
    **Validates: Requirements 4.3, 5.2**
    """
    # Create timeout manager
    timeout_manager = TimeoutManager()
    timeout_manager.start()
    
    try:
        # Create a real long-running process
        process_pid = create_long_running_process()
        
        try:
            # Verify process exists
            assert timeout_manager._process_exists(process_pid), "Test process should exist"
            
            # Create timeout policy
            policy = TimeoutPolicy(
                timeout_seconds=timeout_seconds,
                action=TimeoutAction.TERMINATE,
                grace_period=2
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
            max_wait_time = timeout_seconds + 5  # Extra buffer for processing
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
            assert elapsed_time <= timeout_seconds + 4, \
                f"Timeout enforcement took too long: {elapsed_time:.1f}s > {timeout_seconds + 4}s"
            
            # Property: Timeout callback should be called
            assert len(timeout_events) > 0, "Timeout callback should be called"
            
            # Property: Timeout event should indicate timeout exceeded
            timeout_event = next((event for event in timeout_events if "timeout_exceeded" in event[1]), None)
            assert timeout_event is not None, "Should receive timeout_exceeded event"
            
            # Property: Monitor should be marked as terminated
            assert timeout_manager.is_timeout_exceeded(test_id), "Test should be marked as timed out"
            
            print(f"SUCCESS: Timeout enforcement worked for {timeout_seconds}s timeout")
            
        finally:
            # Cleanup: ensure process is terminated
            terminate_process_if_exists(process_pid)
            timeout_manager.remove_monitor(test_id)
            
    finally:
        timeout_manager.stop()


if __name__ == "__main__":
    # Run the property test manually
    try:
        test_timeout_enforcement_property()
        print("All property tests passed!")
    except Exception as e:
        print(f"Property test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)