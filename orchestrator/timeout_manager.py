"""Timeout management for test execution.

This module provides functionality for:
- Monitoring test execution timeouts
- Enforcing timeout limits and terminating stuck processes
- Recording timeout status and reporting
- Managing timeout policies for different test types
"""

import threading
import time
import signal
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class TimeoutAction(str, Enum):
    """Actions to take when a timeout occurs."""
    TERMINATE = "terminate"  # Terminate the process
    KILL = "kill"  # Force kill the process
    NOTIFY = "notify"  # Just notify, don't terminate


@dataclass
class TimeoutPolicy:
    """Policy for handling timeouts."""
    timeout_seconds: int
    warning_threshold: float = 0.8  # Warn at 80% of timeout
    action: TimeoutAction = TimeoutAction.TERMINATE
    grace_period: int = 5  # Seconds to wait before force kill
    max_retries: int = 0  # Number of retries after timeout


@dataclass
class TimeoutMonitor:
    """Monitor for tracking a single test timeout."""
    test_id: str
    process_id: Optional[int]
    container_id: Optional[str]
    start_time: datetime
    timeout_seconds: int
    policy: TimeoutPolicy
    callback: Optional[Callable[[str, str], None]] = None  # callback(test_id, reason)
    warning_sent: bool = False
    terminated: bool = False


class TimeoutManager:
    """Manager for test execution timeouts."""
    
    def __init__(self):
        """Initialize the timeout manager."""
        self.logger = logging.getLogger('orchestrator.timeout_manager')
        
        # Thread-safe storage for active monitors
        self._lock = threading.RLock()
        self._monitors: Dict[str, TimeoutMonitor] = {}
        self._is_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._stats = {
            'timeouts_detected': 0,
            'processes_terminated': 0,
            'warnings_sent': 0,
            'start_time': datetime.utcnow()
        }
        
        self.logger.info("Timeout manager initialized")
    
    def start(self) -> bool:
        """Start the timeout monitoring service."""
        with self._lock:
            if self._is_running:
                self.logger.warning("Timeout manager is already running")
                return False
            
            try:
                self._is_running = True
                self._stop_event.clear()
                
                # Start monitoring thread
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    name="timeout-monitor",
                    daemon=True
                )
                self._monitor_thread.start()
                
                self.logger.info("Timeout manager started successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start timeout manager: {e}")
                self._is_running = False
                return False
    
    def stop(self) -> bool:
        """Stop the timeout monitoring service."""
        with self._lock:
            if not self._is_running:
                self.logger.warning("Timeout manager is not running")
                return False
            
            try:
                self.logger.info("Stopping timeout manager...")
                
                # Signal stop
                self._is_running = False
                self._stop_event.set()
                
                # Wait for monitor thread to finish
                if self._monitor_thread and self._monitor_thread.is_alive():
                    self._monitor_thread.join(timeout=10.0)
                    if self._monitor_thread.is_alive():
                        self.logger.warning("Monitor thread did not stop gracefully")
                
                # Clean up any remaining monitors
                self._monitors.clear()
                
                self.logger.info("Timeout manager stopped successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping timeout manager: {e}")
                return False
    
    def add_monitor(self, test_id: str, timeout_seconds: int,
                   process_id: Optional[int] = None,
                   container_id: Optional[str] = None,
                   policy: Optional[TimeoutPolicy] = None,
                   callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """Add a timeout monitor for a test.
        
        Args:
            test_id: Unique identifier for the test
            timeout_seconds: Timeout in seconds
            process_id: Optional process ID to terminate
            container_id: Optional container ID to terminate
            policy: Optional timeout policy (uses default if not provided)
            callback: Optional callback function for timeout events
            
        Returns:
            True if monitor was added successfully
        """
        try:
            with self._lock:
                if test_id in self._monitors:
                    self.logger.warning(f"Monitor for test {test_id} already exists")
                    return False
                
                # Create default policy if not provided
                if policy is None:
                    policy = TimeoutPolicy(
                        timeout_seconds=timeout_seconds,
                        action=TimeoutAction.TERMINATE
                    )
                
                # Create monitor
                monitor = TimeoutMonitor(
                    test_id=test_id,
                    process_id=process_id,
                    container_id=container_id,
                    start_time=datetime.utcnow(),
                    timeout_seconds=timeout_seconds,
                    policy=policy,
                    callback=callback
                )
                
                self._monitors[test_id] = monitor
                
                self.logger.debug(f"Added timeout monitor for test {test_id} "
                                f"(timeout: {timeout_seconds}s)")
                return True
                
        except Exception as e:
            self.logger.error(f"Error adding timeout monitor for {test_id}: {e}")
            return False
    
    def remove_monitor(self, test_id: str) -> bool:
        """Remove a timeout monitor for a test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            True if monitor was removed successfully
        """
        try:
            with self._lock:
                if test_id not in self._monitors:
                    self.logger.debug(f"No monitor found for test {test_id}")
                    return False
                
                del self._monitors[test_id]
                self.logger.debug(f"Removed timeout monitor for test {test_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error removing timeout monitor for {test_id}: {e}")
            return False
    
    def update_monitor(self, test_id: str, process_id: Optional[int] = None,
                      container_id: Optional[str] = None) -> bool:
        """Update an existing timeout monitor with process/container information.
        
        Args:
            test_id: Test identifier
            process_id: Optional process ID to update
            container_id: Optional container ID to update
            
        Returns:
            True if monitor was updated successfully
        """
        try:
            with self._lock:
                monitor = self._monitors.get(test_id)
                if not monitor:
                    self.logger.warning(f"No monitor found for test {test_id}")
                    return False
                
                if process_id is not None:
                    monitor.process_id = process_id
                if container_id is not None:
                    monitor.container_id = container_id
                
                self.logger.debug(f"Updated monitor for test {test_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating timeout monitor for {test_id}: {e}")
            return False
    
    def get_remaining_time(self, test_id: str) -> Optional[float]:
        """Get remaining time before timeout for a test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Remaining time in seconds, or None if no monitor exists
        """
        with self._lock:
            monitor = self._monitors.get(test_id)
            if not monitor:
                return None
            
            elapsed = (datetime.utcnow() - monitor.start_time).total_seconds()
            remaining = monitor.timeout_seconds - elapsed
            return max(0.0, remaining)
    
    def is_timeout_exceeded(self, test_id: str) -> bool:
        """Check if a test has exceeded its timeout.
        
        Args:
            test_id: Test identifier
            
        Returns:
            True if timeout has been exceeded
        """
        remaining = self.get_remaining_time(test_id)
        return remaining is not None and remaining <= 0
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        self.logger.info("Timeout monitoring loop started")
        
        while self._is_running and not self._stop_event.is_set():
            try:
                current_time = datetime.utcnow()
                monitors_to_process = []
                
                # Collect monitors that need processing
                with self._lock:
                    for monitor in self._monitors.values():
                        elapsed = (current_time - monitor.start_time).total_seconds()
                        
                        # Check for warning threshold
                        warning_threshold = monitor.timeout_seconds * monitor.policy.warning_threshold
                        if (not monitor.warning_sent and 
                            elapsed >= warning_threshold and 
                            elapsed < monitor.timeout_seconds):
                            monitors_to_process.append(('warning', monitor))
                        
                        # Check for timeout
                        elif elapsed >= monitor.timeout_seconds and not monitor.terminated:
                            monitors_to_process.append(('timeout', monitor))
                
                # Process monitors outside the lock to avoid blocking
                for action, monitor in monitors_to_process:
                    if action == 'warning':
                        self._send_warning(monitor)
                    elif action == 'timeout':
                        self._handle_timeout(monitor)
                
                # Sleep until next check (but wake up if stop is requested)
                if not self._stop_event.wait(1.0):  # Check every second
                    continue
                else:
                    break  # Stop requested
                    
            except Exception as e:
                self.logger.error(f"Error in timeout monitoring loop: {e}")
                time.sleep(1.0)  # Brief pause before continuing
        
        self.logger.info("Timeout monitoring loop stopped")
    
    def _send_warning(self, monitor: TimeoutMonitor):
        """Send a timeout warning for a monitor.
        
        Args:
            monitor: The timeout monitor
        """
        try:
            elapsed = (datetime.utcnow() - monitor.start_time).total_seconds()
            remaining = monitor.timeout_seconds - elapsed
            
            self.logger.warning(f"Test {monitor.test_id} approaching timeout "
                              f"(remaining: {remaining:.1f}s)")
            
            # Mark warning as sent
            with self._lock:
                monitor.warning_sent = True
                self._stats['warnings_sent'] += 1
            
            # Call callback if provided
            if monitor.callback:
                try:
                    monitor.callback(monitor.test_id, f"timeout_warning:{remaining:.1f}")
                except Exception as e:
                    self.logger.error(f"Error in timeout warning callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error sending timeout warning for {monitor.test_id}: {e}")
    
    def _handle_timeout(self, monitor: TimeoutMonitor):
        """Handle a timeout event for a monitor.
        
        Args:
            monitor: The timeout monitor that timed out
        """
        try:
            elapsed = (datetime.utcnow() - monitor.start_time).total_seconds()
            
            self.logger.warning(f"Test {monitor.test_id} timed out after {elapsed:.1f}s "
                              f"(limit: {monitor.timeout_seconds}s)")
            
            # Mark as terminated to prevent duplicate processing
            with self._lock:
                monitor.terminated = True
                self._stats['timeouts_detected'] += 1
            
            # Take action based on policy
            if monitor.policy.action == TimeoutAction.TERMINATE:
                self._terminate_test(monitor)
            elif monitor.policy.action == TimeoutAction.KILL:
                self._kill_test(monitor)
            elif monitor.policy.action == TimeoutAction.NOTIFY:
                self.logger.info(f"Timeout notification only for test {monitor.test_id}")
            
            # Call callback if provided
            if monitor.callback:
                try:
                    monitor.callback(monitor.test_id, "timeout_exceeded")
                except Exception as e:
                    self.logger.error(f"Error in timeout callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error handling timeout for {monitor.test_id}: {e}")
    
    def _terminate_test(self, monitor: TimeoutMonitor):
        """Terminate a test process gracefully.
        
        Args:
            monitor: The timeout monitor
        """
        try:
            terminated = False
            
            # Try to terminate Docker container first
            if monitor.container_id:
                terminated = self._terminate_container(monitor.container_id)
            
            # Try to terminate process if container termination failed or no container
            if not terminated and monitor.process_id:
                terminated = self._terminate_process(monitor.process_id, monitor.policy.grace_period)
            
            if terminated:
                with self._lock:
                    self._stats['processes_terminated'] += 1
                self.logger.info(f"Successfully terminated test {monitor.test_id}")
            else:
                self.logger.warning(f"Failed to terminate test {monitor.test_id}")
                
        except Exception as e:
            self.logger.error(f"Error terminating test {monitor.test_id}: {e}")
    
    def _kill_test(self, monitor: TimeoutMonitor):
        """Force kill a test process.
        
        Args:
            monitor: The timeout monitor
        """
        try:
            killed = False
            
            # Try to kill Docker container first
            if monitor.container_id:
                killed = self._kill_container(monitor.container_id)
            
            # Try to kill process if container kill failed or no container
            if not killed and monitor.process_id:
                killed = self._kill_process(monitor.process_id)
            
            if killed:
                with self._lock:
                    self._stats['processes_terminated'] += 1
                self.logger.info(f"Successfully killed test {monitor.test_id}")
            else:
                self.logger.warning(f"Failed to kill test {monitor.test_id}")
                
        except Exception as e:
            self.logger.error(f"Error killing test {monitor.test_id}: {e}")
    
    def _terminate_container(self, container_id: str) -> bool:
        """Terminate a Docker container gracefully.
        
        Args:
            container_id: Container ID to terminate
            
        Returns:
            True if container was terminated successfully
        """
        try:
            import subprocess
            
            # Try graceful stop first
            result = subprocess.run(
                ['docker', 'stop', container_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.debug(f"Container {container_id} stopped gracefully")
                return True
            else:
                self.logger.warning(f"Failed to stop container {container_id}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Timeout stopping container {container_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error stopping container {container_id}: {e}")
            return False
    
    def _kill_container(self, container_id: str) -> bool:
        """Force kill a Docker container.
        
        Args:
            container_id: Container ID to kill
            
        Returns:
            True if container was killed successfully
        """
        try:
            import subprocess
            
            result = subprocess.run(
                ['docker', 'kill', container_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.debug(f"Container {container_id} killed")
                return True
            else:
                self.logger.warning(f"Failed to kill container {container_id}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Timeout killing container {container_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error killing container {container_id}: {e}")
            return False
    
    def _terminate_process(self, process_id: int, grace_period: int = 5) -> bool:
        """Terminate a process gracefully with optional force kill.
        
        Args:
            process_id: Process ID to terminate
            grace_period: Seconds to wait before force kill
            
        Returns:
            True if process was terminated successfully
        """
        try:
            # Check if process exists
            if not self._process_exists(process_id):
                self.logger.debug(f"Process {process_id} does not exist")
                return True
            
            # Send SIGTERM for graceful shutdown
            os.kill(process_id, signal.SIGTERM)
            self.logger.debug(f"Sent SIGTERM to process {process_id}")
            
            # Wait for graceful shutdown
            for _ in range(grace_period):
                time.sleep(1.0)
                if not self._process_exists(process_id):
                    self.logger.debug(f"Process {process_id} terminated gracefully")
                    return True
            
            # Force kill if still running
            if self._process_exists(process_id):
                os.kill(process_id, signal.SIGKILL)
                self.logger.debug(f"Sent SIGKILL to process {process_id}")
                
                # Brief wait to confirm kill
                time.sleep(1.0)
                if not self._process_exists(process_id):
                    self.logger.debug(f"Process {process_id} killed")
                    return True
                else:
                    self.logger.warning(f"Process {process_id} still running after SIGKILL")
                    return False
            
            return True
            
        except ProcessLookupError:
            # Process already terminated
            self.logger.debug(f"Process {process_id} already terminated")
            return True
        except PermissionError:
            self.logger.error(f"Permission denied terminating process {process_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error terminating process {process_id}: {e}")
            return False
    
    def _kill_process(self, process_id: int) -> bool:
        """Force kill a process immediately.
        
        Args:
            process_id: Process ID to kill
            
        Returns:
            True if process was killed successfully
        """
        try:
            if not self._process_exists(process_id):
                self.logger.debug(f"Process {process_id} does not exist")
                return True
            
            os.kill(process_id, signal.SIGKILL)
            self.logger.debug(f"Sent SIGKILL to process {process_id}")
            
            # Brief wait to confirm kill
            time.sleep(1.0)
            return not self._process_exists(process_id)
            
        except ProcessLookupError:
            # Process already terminated
            return True
        except PermissionError:
            self.logger.error(f"Permission denied killing process {process_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error killing process {process_id}: {e}")
            return False
    
    def _process_exists(self, process_id: int) -> bool:
        """Check if a process exists.
        
        Args:
            process_id: Process ID to check
            
        Returns:
            True if process exists
        """
        try:
            os.kill(process_id, 0)  # Signal 0 just checks if process exists
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we don't have permission to signal it
            return True
        except Exception:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get timeout manager statistics.
        
        Returns:
            Dictionary containing statistics
        """
        with self._lock:
            uptime = (datetime.utcnow() - self._stats['start_time']).total_seconds()
            
            return {
                'is_running': self._is_running,
                'active_monitors': len(self._monitors),
                'timeouts_detected': self._stats['timeouts_detected'],
                'processes_terminated': self._stats['processes_terminated'],
                'warnings_sent': self._stats['warnings_sent'],
                'uptime_seconds': uptime
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the timeout manager.
        
        Returns:
            Dictionary containing health information
        """
        with self._lock:
            return {
                'status': 'healthy' if self._is_running else 'stopped',
                'is_running': self._is_running,
                'active_monitors': len(self._monitors),
                'monitor_thread_alive': (self._monitor_thread.is_alive() 
                                       if self._monitor_thread else False)
            }
    
    def cleanup_completed_monitors(self, max_age_hours: int = 1):
        """Clean up monitors for completed tests to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age in hours for completed monitors
        """
        try:
            with self._lock:
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=max_age_hours)
                
                # Find old terminated monitors
                old_monitors = []
                for test_id, monitor in self._monitors.items():
                    if monitor.terminated and monitor.start_time < cutoff_time:
                        old_monitors.append(test_id)
                
                # Remove old monitors
                for test_id in old_monitors:
                    del self._monitors[test_id]
                
                if old_monitors:
                    self.logger.info(f"Cleaned up {len(old_monitors)} old timeout monitors")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up timeout monitors: {e}")