"""Status tracking component for real-time test execution monitoring."""

import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging


@dataclass
class TestExecutionStatus:
    """Status information for a single test execution."""
    test_id: str
    status: str  # queued, running, completed, failed, timeout, error
    plan_id: Optional[str] = None
    environment_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    execution_time: Optional[float] = None


@dataclass
class ExecutionPlanStatus:
    """Status information for an execution plan."""
    plan_id: str
    submission_id: str
    status: str  # queued, running, completed, failed
    total_tests: int = 0
    completed_tests: int = 0
    failed_tests: int = 0
    active_tests: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    test_statuses: Dict[str, TestExecutionStatus] = field(default_factory=dict)


class StatusTracker:
    """Thread-safe status tracker for test execution monitoring."""
    
    def __init__(self):
        """Initialize the status tracker."""
        self.logger = logging.getLogger('orchestrator.status_tracker')
        
        # Thread-safe counters
        self._lock = threading.RLock()
        self._active_test_count = 0
        self._queued_test_count = 0
        self._completed_test_count = 0
        self._failed_test_count = 0
        
        # Status storage
        self._test_statuses: Dict[str, TestExecutionStatus] = {}
        self._plan_statuses: Dict[str, ExecutionPlanStatus] = {}
        
        # Metrics
        self._metrics = {
            'status_updates': 0,
            'last_update': None,
            'start_time': datetime.utcnow()
        }
        
        self._is_running = False
        self.logger.info("Status tracker initialized")
    
    def start(self):
        """Start the status tracker."""
        with self._lock:
            if self._is_running:
                self.logger.warning("Status tracker is already running")
                return
            
            self._is_running = True
            self._metrics['start_time'] = datetime.utcnow()
            self.logger.info("Status tracker started")
    
    def stop(self):
        """Stop the status tracker."""
        with self._lock:
            if not self._is_running:
                self.logger.warning("Status tracker is not running")
                return
            
            self._is_running = False
            self.logger.info("Status tracker stopped")
    
    def update_test_status(self, test_id: str, status: str, 
                          message: str = "", progress: float = None,
                          environment_id: str = None) -> bool:
        """Update the status of a specific test."""
        try:
            with self._lock:
                current_time = datetime.utcnow()
                
                # Get or create test status
                if test_id not in self._test_statuses:
                    self._test_statuses[test_id] = TestExecutionStatus(
                        test_id=test_id,
                        status='queued'
                    )
                
                test_status = self._test_statuses[test_id]
                old_status = test_status.status
                
                # Update status fields
                test_status.status = status
                test_status.message = message
                if progress is not None:
                    test_status.progress = max(0.0, min(1.0, progress))
                if environment_id:
                    test_status.environment_id = environment_id
                
                # Update timestamps
                if status == 'running' and old_status != 'running':
                    test_status.started_at = current_time
                elif status in ['completed', 'failed', 'timeout', 'error']:
                    if test_status.started_at:
                        test_status.execution_time = (current_time - test_status.started_at).total_seconds()
                    test_status.completed_at = current_time
                    test_status.progress = 1.0
                
                # Update counters based on status transitions
                self._update_counters_for_transition(old_status, status)
                
                # Update metrics
                self._metrics['status_updates'] += 1
                self._metrics['last_update'] = current_time
                
                self.logger.debug(f"Updated test {test_id}: {old_status} -> {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating test status for {test_id}: {e}")
            return False
    
    def update_plan_status(self, plan_id: str, status: str, 
                          submission_id: str = None) -> bool:
        """Update the status of an execution plan."""
        try:
            with self._lock:
                current_time = datetime.utcnow()
                
                # Get or create plan status
                if plan_id not in self._plan_statuses:
                    self._plan_statuses[plan_id] = ExecutionPlanStatus(
                        plan_id=plan_id,
                        submission_id=submission_id or f"sub-{plan_id[:8]}",
                        status='queued'
                    )
                
                plan_status = self._plan_statuses[plan_id]
                old_status = plan_status.status
                
                # Update status
                plan_status.status = status
                
                # Update timestamps
                if status == 'running' and old_status != 'running':
                    plan_status.started_at = current_time
                elif status in ['completed', 'failed']:
                    plan_status.completed_at = current_time
                
                self.logger.debug(f"Updated plan {plan_id}: {old_status} -> {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating plan status for {plan_id}: {e}")
            return False
    
    def _update_counters_for_transition(self, old_status: str, new_status: str):
        """Update internal counters based on status transition."""
        # Decrement old status counter
        if old_status == 'running':
            self._active_test_count = max(0, self._active_test_count - 1)
        elif old_status == 'queued':
            self._queued_test_count = max(0, self._queued_test_count - 1)
        
        # Increment new status counter
        if new_status == 'running':
            self._active_test_count += 1
        elif new_status == 'queued':
            self._queued_test_count += 1
        elif new_status == 'completed':
            self._completed_test_count += 1
        elif new_status in ['failed', 'timeout', 'error']:
            self._failed_test_count += 1
    
    def increment_active_tests(self) -> int:
        """Increment the active test counter."""
        with self._lock:
            self._active_test_count += 1
            return self._active_test_count
    
    def decrement_active_tests(self) -> int:
        """Decrement the active test counter."""
        with self._lock:
            self._active_test_count = max(0, self._active_test_count - 1)
            return self._active_test_count
    
    def get_active_test_count(self) -> int:
        """Get the current number of active (running) tests."""
        with self._lock:
            return self._active_test_count
    
    def get_queued_test_count(self) -> int:
        """Get the current number of queued tests."""
        with self._lock:
            return self._queued_test_count
    
    def get_completed_test_count(self) -> int:
        """Get the total number of completed tests."""
        with self._lock:
            return self._completed_test_count
    
    def get_failed_test_count(self) -> int:
        """Get the total number of failed tests."""
        with self._lock:
            return self._failed_test_count
    
    def get_test_status(self, test_id: str) -> Optional[TestExecutionStatus]:
        """Get the status of a specific test."""
        with self._lock:
            return self._test_statuses.get(test_id)
    
    def get_plan_status(self, plan_id: str) -> Optional[ExecutionPlanStatus]:
        """Get the status of a specific execution plan."""
        with self._lock:
            return self._plan_statuses.get(plan_id)
    
    def get_all_active_tests(self) -> Dict[str, TestExecutionStatus]:
        """Get all currently active (running) tests."""
        with self._lock:
            return {
                test_id: status 
                for test_id, status in self._test_statuses.items()
                if status.status == 'running'
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        with self._lock:
            uptime = (datetime.utcnow() - self._metrics['start_time']).total_seconds()
            
            return {
                'active_tests': self._active_test_count,
                'queued_tests': self._queued_test_count,
                'completed_tests': self._completed_test_count,
                'failed_tests': self._failed_test_count,
                'total_tests': len(self._test_statuses),
                'total_plans': len(self._plan_statuses),
                'uptime_seconds': uptime,
                'status_updates': self._metrics['status_updates'],
                'last_update': self._metrics['last_update'].isoformat() if self._metrics['last_update'] else None
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the status tracker."""
        with self._lock:
            return {
                'status': 'healthy' if self._is_running else 'stopped',
                'is_running': self._is_running,
                'active_tests': self._active_test_count,
                'total_tracked_tests': len(self._test_statuses),
                'total_tracked_plans': len(self._plan_statuses),
                'last_update': self._metrics['last_update'].isoformat() if self._metrics['last_update'] else None
            }
    
    def update_metrics(self):
        """Update internal metrics (called periodically)."""
        try:
            with self._lock:
                # Recalculate counters from actual status data for accuracy
                active_count = sum(1 for status in self._test_statuses.values() if status.status == 'running')
                queued_count = sum(1 for status in self._test_statuses.values() if status.status == 'queued')
                completed_count = sum(1 for status in self._test_statuses.values() if status.status == 'completed')
                failed_count = sum(1 for status in self._test_statuses.values() 
                                 if status.status in ['failed', 'timeout', 'error'])
                
                # Update counters if they're out of sync
                if active_count != self._active_test_count:
                    self.logger.warning(f"Active test count mismatch: {self._active_test_count} -> {active_count}")
                    self._active_test_count = active_count
                
                if queued_count != self._queued_test_count:
                    self.logger.warning(f"Queued test count mismatch: {self._queued_test_count} -> {queued_count}")
                    self._queued_test_count = queued_count
                
                self._completed_test_count = completed_count
                self._failed_test_count = failed_count
                
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def cleanup_old_statuses(self, max_age_hours: int = 24):
        """Clean up old test and plan statuses to prevent memory leaks."""
        try:
            with self._lock:
                current_time = datetime.utcnow()
                cutoff_time = current_time.timestamp() - (max_age_hours * 3600)
                
                # Clean up old test statuses
                old_test_ids = []
                for test_id, status in self._test_statuses.items():
                    if (status.completed_at and 
                        status.completed_at.timestamp() < cutoff_time and
                        status.status in ['completed', 'failed', 'timeout', 'error']):
                        old_test_ids.append(test_id)
                
                for test_id in old_test_ids:
                    del self._test_statuses[test_id]
                
                # Clean up old plan statuses
                old_plan_ids = []
                for plan_id, status in self._plan_statuses.items():
                    if (status.completed_at and 
                        status.completed_at.timestamp() < cutoff_time and
                        status.status in ['completed', 'failed']):
                        old_plan_ids.append(plan_id)
                
                for plan_id in old_plan_ids:
                    del self._plan_statuses[plan_id]
                
                if old_test_ids or old_plan_ids:
                    self.logger.info(f"Cleaned up {len(old_test_ids)} old test statuses and {len(old_plan_ids)} old plan statuses")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old statuses: {e}")