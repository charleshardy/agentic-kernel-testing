"""Error recovery manager for handling system failures and environment issues.

This module provides functionality for:
- Environment failure detection and recovery
- Logging and monitoring of critical errors
- Graceful degradation for system issues
- Automatic retry logic for transient failures
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Categories of errors."""
    ENVIRONMENT_FAILURE = "environment_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_ISSUE = "network_issue"
    TIMEOUT = "timeout"
    PERMISSION_ERROR = "permission_error"
    CONFIGURATION_ERROR = "configuration_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """Represents an error event in the system."""
    id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    component: str  # Component that reported the error
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    environment_id: Optional[str] = None
    test_id: Optional[str] = None
    retry_count: int = 0
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None


@dataclass
class RecoveryAction:
    """Defines a recovery action for an error."""
    name: str
    description: str
    action_func: Callable[[ErrorEvent], bool]  # Returns True if recovery succeeded
    max_retries: int = 3
    retry_delay: float = 5.0  # Seconds between retries
    applicable_categories: Set[ErrorCategory] = field(default_factory=set)
    applicable_severities: Set[ErrorSeverity] = field(default_factory=set)


class ErrorRecoveryManager:
    """Manager for error detection, logging, and recovery."""
    
    def __init__(self, config=None):
        """Initialize the error recovery manager.
        
        Args:
            config: Optional configuration object
        """
        self.logger = logging.getLogger('orchestrator.error_recovery')
        self.config = config
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._error_events: Dict[str, ErrorEvent] = {}
        self._recovery_actions: List[RecoveryAction] = []
        
        # Service state
        self._is_running = False
        self._recovery_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._stats = {
            'total_errors': 0,
            'resolved_errors': 0,
            'failed_recoveries': 0,
            'environment_failures': 0,
            'critical_errors': 0,
            'start_time': datetime.utcnow()
        }
        
        # Error thresholds for degradation
        self._degradation_thresholds = {
            ErrorCategory.ENVIRONMENT_FAILURE: 5,  # Max environment failures before degradation
            ErrorCategory.RESOURCE_EXHAUSTION: 3,  # Max resource exhaustion events
            'critical_severity': 1  # Any critical error triggers degradation
        }
        
        self._degraded_mode = False
        self._degradation_start_time: Optional[datetime] = None
        
        # Register default recovery actions
        self._register_default_recovery_actions()
        
        self.logger.info("Error recovery manager initialized")
    
    def start(self) -> bool:
        """Start the error recovery service."""
        with self._lock:
            if self._is_running:
                self.logger.warning("Error recovery manager is already running")
                return False
            
            try:
                self._is_running = True
                self._stop_event.clear()
                
                # Start recovery thread
                self._recovery_thread = threading.Thread(
                    target=self._recovery_loop,
                    name="error-recovery",
                    daemon=True
                )
                self._recovery_thread.start()
                
                self.logger.info("Error recovery manager started successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start error recovery manager: {e}")
                self._is_running = False
                return False
    
    def stop(self) -> bool:
        """Stop the error recovery service."""
        with self._lock:
            if not self._is_running:
                self.logger.warning("Error recovery manager is not running")
                return False
            
            try:
                self.logger.info("Stopping error recovery manager...")
                
                # Signal stop
                self._is_running = False
                self._stop_event.set()
                
                # Wait for recovery thread to finish
                if self._recovery_thread and self._recovery_thread.is_alive():
                    self._recovery_thread.join(timeout=10.0)
                    if self._recovery_thread.is_alive():
                        self.logger.warning("Recovery thread did not stop gracefully")
                
                self.logger.info("Error recovery manager stopped successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping error recovery manager: {e}")
                return False
    
    def report_error(self, category: ErrorCategory, severity: ErrorSeverity,
                    component: str, message: str, details: Optional[Dict[str, Any]] = None,
                    stack_trace: Optional[str] = None, environment_id: Optional[str] = None,
                    test_id: Optional[str] = None) -> str:
        """Report an error event.
        
        Args:
            category: Error category
            severity: Error severity
            component: Component reporting the error
            message: Error message
            details: Optional additional details
            stack_trace: Optional stack trace
            environment_id: Optional environment ID
            test_id: Optional test ID
            
        Returns:
            Error event ID
        """
        try:
            # Generate unique error ID
            error_id = f"err_{int(time.time() * 1000)}_{len(self._error_events)}"
            
            # Create error event
            error_event = ErrorEvent(
                id=error_id,
                timestamp=datetime.utcnow(),
                category=category,
                severity=severity,
                component=component,
                message=message,
                details=details or {},
                stack_trace=stack_trace,
                environment_id=environment_id,
                test_id=test_id
            )
            
            with self._lock:
                self._error_events[error_id] = error_event
                self._stats['total_errors'] += 1
                
                # Update category-specific stats
                if category == ErrorCategory.ENVIRONMENT_FAILURE:
                    self._stats['environment_failures'] += 1
                if severity == ErrorSeverity.CRITICAL:
                    self._stats['critical_errors'] += 1
            
            # Log the error
            log_level = self._get_log_level_for_severity(severity)
            self.logger.log(log_level, f"Error reported: {message} "
                          f"(category: {category}, severity: {severity}, "
                          f"component: {component}, id: {error_id})")
            
            # Check for degradation conditions
            self._check_degradation_conditions()
            
            return error_id
            
        except Exception as e:
            self.logger.error(f"Error reporting error event: {e}")
            return ""
    
    def resolve_error(self, error_id: str, resolution_message: str = "") -> bool:
        """Mark an error as resolved.
        
        Args:
            error_id: Error event ID
            resolution_message: Optional resolution message
            
        Returns:
            True if error was resolved successfully
        """
        try:
            with self._lock:
                error_event = self._error_events.get(error_id)
                if not error_event:
                    self.logger.warning(f"Error event {error_id} not found")
                    return False
                
                if error_event.resolved:
                    self.logger.debug(f"Error event {error_id} already resolved")
                    return True
                
                error_event.resolved = True
                error_event.resolution_timestamp = datetime.utcnow()
                if resolution_message:
                    error_event.details['resolution_message'] = resolution_message
                
                self._stats['resolved_errors'] += 1
            
            self.logger.info(f"Error {error_id} resolved: {resolution_message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving error event {error_id}: {e}")
            return False
    
    def register_recovery_action(self, action: RecoveryAction) -> bool:
        """Register a recovery action.
        
        Args:
            action: Recovery action to register
            
        Returns:
            True if action was registered successfully
        """
        try:
            with self._lock:
                # Check if action with same name already exists
                existing_names = {action.name for action in self._recovery_actions}
                if action.name in existing_names:
                    self.logger.warning(f"Recovery action '{action.name}' already exists")
                    return False
                
                self._recovery_actions.append(action)
            
            self.logger.info(f"Registered recovery action: {action.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering recovery action: {e}")
            return False
    
    def _register_default_recovery_actions(self):
        """Register default recovery actions."""
        # Environment restart action
        restart_env_action = RecoveryAction(
            name="restart_environment",
            description="Restart failed environment",
            action_func=self._restart_environment,
            max_retries=2,
            retry_delay=10.0,
            applicable_categories={ErrorCategory.ENVIRONMENT_FAILURE},
            applicable_severities={ErrorSeverity.HIGH, ErrorSeverity.CRITICAL}
        )
        self._recovery_actions.append(restart_env_action)
        
        # Resource cleanup action
        cleanup_action = RecoveryAction(
            name="cleanup_resources",
            description="Clean up system resources",
            action_func=self._cleanup_resources,
            max_retries=1,
            retry_delay=5.0,
            applicable_categories={ErrorCategory.RESOURCE_EXHAUSTION},
            applicable_severities={ErrorSeverity.MEDIUM, ErrorSeverity.HIGH}
        )
        self._recovery_actions.append(cleanup_action)
        
        # Network retry action
        network_retry_action = RecoveryAction(
            name="retry_network_operation",
            description="Retry network operation",
            action_func=self._retry_network_operation,
            max_retries=3,
            retry_delay=2.0,
            applicable_categories={ErrorCategory.NETWORK_ISSUE},
            applicable_severities={ErrorSeverity.LOW, ErrorSeverity.MEDIUM}
        )
        self._recovery_actions.append(network_retry_action)
    
    def _recovery_loop(self):
        """Main recovery loop that runs in a separate thread."""
        self.logger.info("Error recovery loop started")
        
        while self._is_running and not self._stop_event.is_set():
            try:
                # Find unresolved errors that need recovery
                errors_to_process = []
                
                with self._lock:
                    for error_event in self._error_events.values():
                        if (not error_event.resolved and 
                            error_event.retry_count < self._get_max_retries_for_error(error_event)):
                            errors_to_process.append(error_event)
                
                # Process errors outside the lock
                for error_event in errors_to_process:
                    self._attempt_recovery(error_event)
                
                # Clean up old resolved errors
                self._cleanup_old_errors()
                
                # Sleep until next check
                if not self._stop_event.wait(30.0):  # Check every 30 seconds
                    continue
                else:
                    break  # Stop requested
                    
            except Exception as e:
                self.logger.error(f"Error in recovery loop: {e}")
                time.sleep(5.0)  # Brief pause before continuing
        
        self.logger.info("Error recovery loop stopped")
    
    def _attempt_recovery(self, error_event: ErrorEvent):
        """Attempt to recover from an error.
        
        Args:
            error_event: Error event to recover from
        """
        try:
            # Find applicable recovery actions
            applicable_actions = []
            
            for action in self._recovery_actions:
                if (error_event.category in action.applicable_categories and
                    error_event.severity in action.applicable_severities):
                    applicable_actions.append(action)
            
            if not applicable_actions:
                self.logger.debug(f"No recovery actions available for error {error_event.id}")
                return
            
            # Try each applicable action
            for action in applicable_actions:
                if error_event.retry_count >= action.max_retries:
                    continue
                
                self.logger.info(f"Attempting recovery action '{action.name}' "
                               f"for error {error_event.id}")
                
                try:
                    # Increment retry count
                    with self._lock:
                        error_event.retry_count += 1
                    
                    # Execute recovery action
                    success = action.action_func(error_event)
                    
                    if success:
                        self.resolve_error(error_event.id, f"Recovered using {action.name}")
                        self.logger.info(f"Recovery successful for error {error_event.id}")
                        return
                    else:
                        self.logger.warning(f"Recovery action '{action.name}' failed "
                                          f"for error {error_event.id}")
                        
                        # Wait before next retry
                        time.sleep(action.retry_delay)
                        
                except Exception as e:
                    self.logger.error(f"Error executing recovery action '{action.name}': {e}")
                    with self._lock:
                        self._stats['failed_recoveries'] += 1
            
            # If all recovery attempts failed
            if error_event.retry_count >= self._get_max_retries_for_error(error_event):
                self.logger.error(f"All recovery attempts failed for error {error_event.id}")
                
        except Exception as e:
            self.logger.error(f"Error in recovery attempt for {error_event.id}: {e}")
    
    def _restart_environment(self, error_event: ErrorEvent) -> bool:
        """Restart a failed environment.
        
        Args:
            error_event: Error event containing environment information
            
        Returns:
            True if environment was restarted successfully
        """
        try:
            environment_id = error_event.environment_id
            if not environment_id:
                self.logger.warning("No environment ID provided for restart")
                return False
            
            self.logger.info(f"Attempting to restart environment {environment_id}")
            
            # This would integrate with the resource manager to restart the environment
            # For now, simulate the restart
            time.sleep(2.0)  # Simulate restart time
            
            # In a real implementation, this would:
            # 1. Stop the failed environment
            # 2. Clean up resources
            # 3. Provision a new environment
            # 4. Update environment status
            
            self.logger.info(f"Environment {environment_id} restarted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting environment: {e}")
            return False
    
    def _cleanup_resources(self, error_event: ErrorEvent) -> bool:
        """Clean up system resources.
        
        Args:
            error_event: Error event
            
        Returns:
            True if cleanup was successful
        """
        try:
            self.logger.info("Attempting resource cleanup")
            
            # This would implement actual resource cleanup:
            # 1. Clean up temporary files
            # 2. Kill orphaned processes
            # 3. Free up memory
            # 4. Clean up Docker containers/images
            
            # Simulate cleanup
            time.sleep(1.0)
            
            self.logger.info("Resource cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {e}")
            return False
    
    def _retry_network_operation(self, error_event: ErrorEvent) -> bool:
        """Retry a network operation.
        
        Args:
            error_event: Error event
            
        Returns:
            True if retry was successful
        """
        try:
            self.logger.info("Retrying network operation")
            
            # This would implement network operation retry:
            # 1. Check network connectivity
            # 2. Retry the failed operation
            # 3. Update connection pools
            
            # Simulate retry
            time.sleep(0.5)
            
            self.logger.info("Network operation retry successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error retrying network operation: {e}")
            return False
    
    def _get_max_retries_for_error(self, error_event: ErrorEvent) -> int:
        """Get maximum retries for an error based on its properties.
        
        Args:
            error_event: Error event
            
        Returns:
            Maximum number of retries
        """
        # Find the highest max_retries among applicable actions
        max_retries = 0
        
        for action in self._recovery_actions:
            if (error_event.category in action.applicable_categories and
                error_event.severity in action.applicable_severities):
                max_retries = max(max_retries, action.max_retries)
        
        return max_retries
    
    def _get_log_level_for_severity(self, severity: ErrorSeverity) -> int:
        """Get logging level for error severity.
        
        Args:
            severity: Error severity
            
        Returns:
            Logging level
        """
        severity_to_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_to_level.get(severity, logging.ERROR)
    
    def _check_degradation_conditions(self):
        """Check if system should enter degraded mode."""
        try:
            with self._lock:
                current_time = datetime.utcnow()
                recent_window = current_time - timedelta(minutes=10)  # 10-minute window
                
                # Count recent errors by category
                recent_errors = {category: 0 for category in ErrorCategory}
                critical_errors = 0
                
                for error_event in self._error_events.values():
                    if error_event.timestamp >= recent_window and not error_event.resolved:
                        recent_errors[error_event.category] += 1
                        if error_event.severity == ErrorSeverity.CRITICAL:
                            critical_errors += 1
                
                # Check degradation thresholds
                should_degrade = False
                
                for category, threshold in self._degradation_thresholds.items():
                    if category == 'critical_severity':
                        if critical_errors >= threshold:
                            should_degrade = True
                            break
                    elif recent_errors.get(category, 0) >= threshold:
                        should_degrade = True
                        break
                
                # Enter or exit degraded mode
                if should_degrade and not self._degraded_mode:
                    self._enter_degraded_mode()
                elif not should_degrade and self._degraded_mode:
                    self._exit_degraded_mode()
                    
        except Exception as e:
            self.logger.error(f"Error checking degradation conditions: {e}")
    
    def _enter_degraded_mode(self):
        """Enter degraded mode due to high error rate."""
        try:
            self._degraded_mode = True
            self._degradation_start_time = datetime.utcnow()
            
            self.logger.critical("System entering degraded mode due to high error rate")
            
            # In degraded mode, the system would:
            # 1. Reduce concurrent test execution
            # 2. Disable non-essential features
            # 3. Increase monitoring frequency
            # 4. Send alerts to administrators
            
        except Exception as e:
            self.logger.error(f"Error entering degraded mode: {e}")
    
    def _exit_degraded_mode(self):
        """Exit degraded mode when error rate decreases."""
        try:
            degraded_duration = None
            if self._degradation_start_time:
                degraded_duration = (datetime.utcnow() - self._degradation_start_time).total_seconds()
            
            self._degraded_mode = False
            self._degradation_start_time = None
            
            self.logger.info(f"System exiting degraded mode "
                           f"(was degraded for {degraded_duration:.1f}s)")
            
        except Exception as e:
            self.logger.error(f"Error exiting degraded mode: {e}")
    
    def _cleanup_old_errors(self, max_age_hours: int = 24):
        """Clean up old resolved errors to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age in hours for resolved errors
        """
        try:
            with self._lock:
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=max_age_hours)
                
                # Find old resolved errors
                old_error_ids = []
                for error_id, error_event in self._error_events.items():
                    if (error_event.resolved and 
                        error_event.resolution_timestamp and
                        error_event.resolution_timestamp < cutoff_time):
                        old_error_ids.append(error_id)
                
                # Remove old errors
                for error_id in old_error_ids:
                    del self._error_events[error_id]
                
                if old_error_ids:
                    self.logger.info(f"Cleaned up {len(old_error_ids)} old error events")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old errors: {e}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of errors in the specified time window.
        
        Args:
            hours: Time window in hours
            
        Returns:
            Dictionary containing error summary
        """
        try:
            with self._lock:
                current_time = datetime.utcnow()
                window_start = current_time - timedelta(hours=hours)
                
                # Count errors by category and severity
                category_counts = {category.value: 0 for category in ErrorCategory}
                severity_counts = {severity.value: 0 for severity in ErrorSeverity}
                
                total_errors = 0
                resolved_errors = 0
                unresolved_errors = 0
                
                for error_event in self._error_events.values():
                    if error_event.timestamp >= window_start:
                        total_errors += 1
                        category_counts[error_event.category.value] += 1
                        severity_counts[error_event.severity.value] += 1
                        
                        if error_event.resolved:
                            resolved_errors += 1
                        else:
                            unresolved_errors += 1
                
                return {
                    'time_window_hours': hours,
                    'total_errors': total_errors,
                    'resolved_errors': resolved_errors,
                    'unresolved_errors': unresolved_errors,
                    'resolution_rate': resolved_errors / total_errors if total_errors > 0 else 0.0,
                    'errors_by_category': category_counts,
                    'errors_by_severity': severity_counts,
                    'degraded_mode': self._degraded_mode,
                    'degraded_since': self._degradation_start_time.isoformat() if self._degradation_start_time else None
                }
                
        except Exception as e:
            self.logger.error(f"Error generating error summary: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error recovery manager statistics.
        
        Returns:
            Dictionary containing statistics
        """
        with self._lock:
            uptime = (datetime.utcnow() - self._stats['start_time']).total_seconds()
            
            return {
                'is_running': self._is_running,
                'uptime_seconds': uptime,
                'total_errors': self._stats['total_errors'],
                'resolved_errors': self._stats['resolved_errors'],
                'failed_recoveries': self._stats['failed_recoveries'],
                'environment_failures': self._stats['environment_failures'],
                'critical_errors': self._stats['critical_errors'],
                'active_errors': len([e for e in self._error_events.values() if not e.resolved]),
                'degraded_mode': self._degraded_mode,
                'recovery_actions_registered': len(self._recovery_actions)
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the error recovery manager.
        
        Returns:
            Dictionary containing health information
        """
        with self._lock:
            return {
                'status': 'degraded' if self._degraded_mode else ('healthy' if self._is_running else 'stopped'),
                'is_running': self._is_running,
                'degraded_mode': self._degraded_mode,
                'active_errors': len([e for e in self._error_events.values() if not e.resolved]),
                'recovery_thread_alive': (self._recovery_thread.is_alive() 
                                        if self._recovery_thread else False)
            }
    
    def export_error_log(self, filepath: str, hours: int = 24) -> bool:
        """Export error log to a file.
        
        Args:
            filepath: Path to export file
            hours: Time window in hours
            
        Returns:
            True if export was successful
        """
        try:
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(hours=hours)
            
            # Collect errors in time window
            errors_to_export = []
            
            with self._lock:
                for error_event in self._error_events.values():
                    if error_event.timestamp >= window_start:
                        errors_to_export.append({
                            'id': error_event.id,
                            'timestamp': error_event.timestamp.isoformat(),
                            'category': error_event.category.value,
                            'severity': error_event.severity.value,
                            'component': error_event.component,
                            'message': error_event.message,
                            'details': error_event.details,
                            'environment_id': error_event.environment_id,
                            'test_id': error_event.test_id,
                            'retry_count': error_event.retry_count,
                            'resolved': error_event.resolved,
                            'resolution_timestamp': (error_event.resolution_timestamp.isoformat() 
                                                    if error_event.resolution_timestamp else None)
                        })
            
            # Export to file
            export_data = {
                'export_timestamp': current_time.isoformat(),
                'time_window_hours': hours,
                'total_errors': len(errors_to_export),
                'errors': errors_to_export
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported {len(errors_to_export)} errors to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting error log: {e}")
            return False