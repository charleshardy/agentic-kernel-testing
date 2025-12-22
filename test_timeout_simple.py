#!/usr/bin/env python3
"""Simple test to verify timeout enforcement works."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_basic_timeout():
    """Basic timeout test."""
    print("Starting basic timeout test...")
    
    try:
        from orchestrator.timeout_manager import TimeoutManager, TimeoutPolicy, TimeoutAction
        import time
        import subprocess
        import signal
        
        # Create timeout manager
        manager = TimeoutManager()
        print("Created timeout manager")
        
        start_result = manager.start()
        print(f"Manager started: {start_result}")
        
        if not start_result:
            print("Failed to start timeout manager")
            return False
        
        try:
            # Create a long-running process
            process = subprocess.Popen([
                'python3', '-c', 
                'import time; time.sleep(60)'
            ])
            
            print(f"Created process with PID: {process.pid}")
            
            # Add timeout monitor
            policy = TimeoutPolicy(
                timeout_seconds=3,
                action=TimeoutAction.TERMINATE,
                grace_period=2
            )
            
            timeout_events = []
            def callback(test_id, reason):
                timeout_events.append((test_id, reason))
                print(f"Timeout event: {test_id} - {reason}")
            
            success = manager.add_monitor(
                test_id="test_basic",
                timeout_seconds=3,
                process_id=process.pid,
                policy=policy,
                callback=callback
            )
            
            print(f"Monitor added: {success}")
            
            if not success:
                print("Failed to add monitor")
                return False
            
            # Wait for timeout
            print("Waiting for timeout...")
            start_time = time.time()
            max_wait = 8  # 3s timeout + 2s grace + 3s buffer
            
            while time.time() - start_time < max_wait:
                try:
                    os.kill(process.pid, 0)
                    print(f"Process still running after {time.time() - start_time:.1f}s")
                    time.sleep(0.5)
                except ProcessLookupError:
                    elapsed = time.time() - start_time
                    print(f"SUCCESS: Process was terminated after {elapsed:.1f}s!")
                    break
            else:
                print("ERROR: Process still running after timeout!")
                return False
                
            print(f"Timeout events: {timeout_events}")
            
            # Verify we got timeout events
            if len(timeout_events) == 0:
                print("ERROR: No timeout events received")
                return False
            
            # Check for timeout exceeded event
            timeout_exceeded = any("timeout_exceeded" in event[1] for event in timeout_events)
            if not timeout_exceeded:
                print("ERROR: No timeout_exceeded event received")
                return False
            
            print("SUCCESS: All timeout enforcement checks passed!")
            return True
            
        finally:
            # Cleanup
            try:
                if process.poll() is None:  # Process still running
                    process.terminate()
                    process.wait(timeout=2)
            except:
                pass
            manager.stop()
            
    except Exception as e:
        print(f"ERROR: Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_timeout()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
    exit(0 if success else 1)