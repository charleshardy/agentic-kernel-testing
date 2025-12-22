#!/usr/bin/env python3
"""Final timeout enforcement property test."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import subprocess
import time
import signal
from orchestrator.timeout_manager import TimeoutManager, TimeoutPolicy, TimeoutAction


def test_timeout_enforcement_property():
    """
    **Feature: test-execution-orchestrator, Property 7: Timeout enforcement**
    
    Property: For any test that exceeds its specified timeout limit, 
    the orchestrator should terminate the test and record a timeout status 
    within a reasonable grace period.
    
    **Validates: Requirements 4.3, 5.2**
    """
    print("Testing timeout enforcement property...")
    
    # Test with different timeout values
    test_cases = [1, 2, 3]
    
    for timeout_seconds in test_cases:
        print(f"\nTesting with {timeout_seconds}s timeout...")
        
        # Create timeout manager
        timeout_manager = TimeoutManager()
        timeout_manager.start()
        
        try:
            # Create a long-running process
            process = subprocess.Popen([
                'python3', '-c', 
                'import time; time.sleep(60)'
            ])
            process_pid = process.pid
            print(f"Created process {process_pid}")
            
            # Verify process exists
            assert timeout_manager._process_exists(process_pid), "Test process should exist"
            
            # Create timeout policy
            policy = TimeoutPolicy(
                timeout_seconds=timeout_seconds,
                action=TimeoutAction.TERMINATE,
                grace_period=1
            )
            
            # Track timeout events
            timeout_events = []
            
            def timeout_callback(test_id: str, reason: str):
                timeout_events.append((test_id, reason))
                print(f"Timeout event: {test_id} - {reason}")
            
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
            print("Monitor added successfully")
            
            # Wait for timeout to occur
            max_wait_time = timeout_seconds + 3  # Buffer for processing
            start_time = time.time()
            
            print(f"Waiting up to {max_wait_time}s for timeout...")
            while time.time() - start_time < max_wait_time:
                if not timeout_manager._process_exists(process_pid):
                    break
                time.sleep(0.2)
            
            # Property: Process should be terminated within reasonable grace period
            elapsed_time = time.time() - start_time
            print(f"Elapsed time: {elapsed_time:.1f}s")
            
            assert not timeout_manager._process_exists(process_pid), \
                f"Process should be terminated after timeout ({elapsed_time:.1f}s elapsed)"
            
            # Property: Timeout should be detected within reasonable time
            assert elapsed_time <= timeout_seconds + 2, \
                f"Timeout enforcement took too long: {elapsed_time:.1f}s > {timeout_seconds + 2}s"
            
            # Property: Timeout callback should be called
            assert len(timeout_events) > 0, "Timeout callback should be called"
            
            # Property: Timeout event should indicate timeout exceeded
            timeout_event = next((event for event in timeout_events if "timeout_exceeded" in event[1]), None)
            assert timeout_event is not None, "Should receive timeout_exceeded event"
            
            # Property: Monitor should be marked as terminated
            assert timeout_manager.is_timeout_exceeded(test_id), "Test should be marked as timed out"
            
            print(f"✓ SUCCESS: Timeout enforcement worked for {timeout_seconds}s timeout")
            
        finally:
            # Cleanup: ensure process is terminated
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=1)
            except:
                pass
            timeout_manager.stop()
    
    print("\n✓ All timeout enforcement property tests passed!")
    return True


if __name__ == "__main__":
    try:
        success = test_timeout_enforcement_property()
        print(f"\nFinal result: {'PASS' if success else 'FAIL'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nProperty test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)