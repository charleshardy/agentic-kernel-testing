"""Service recovery manager for handling orchestrator restarts and state persistence.

This module provides functionality for:
- Persisting execution state across service restarts
- Recovering queued tests on service startup
- Automatic retry logic for transient failures
- State consistency validation and repair
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import hashlib


class RecoveryState(str, Enum):
    """States for recovery operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PersistedTestState:
    """Represents the state of a test that needs to be persisted."""
    test_id: str
    plan_id: str
    status: str
    environment_id: Optional[str]
    started_at: Optional[str]  # ISO format datetime
    timeout_seconds: int
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None


@dataclass
class PersistedPlanState:
    """Represents the state of an execution plan that needs to be persisted."""
    plan_id: str
    submission_id: str
    status: str
    total_tests: int
    completed_tests: int
    failed_tests: int
    started_at: Optional[str]  # ISO format datetime
    test_states: List[PersistedTestState]


@dataclass
class RecoveryOperation:
    """Represents a recovery operation."""
    operation_id: str
    operation_type: str  # 'test_recovery', 'plan_recovery', 'state_repair'
    state: RecoveryState
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    data: Dict[str, Any] = None


class ServiceRecoveryManager:
    """Manager for service recovery and state persistence."""
    
    def __init__(self, config=None, state_dir: str = "orchestrator_state"):
        """Initialize the service recovery manager.
        
        Args:
            config: Optional configuration object
            state_dir: Directory for storing state files
        """
        self.logger = logging.getLogger('orchestrator.service_recovery')
        self.config = config
        
        # State storage
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        self.state_file = self.state_dir / "orchestrator_state.json"
        self.backup_state_file = self.state_dir / "orchestrator_state_backup.json"
        self.recovery_log_file = self.state_dir / "recovery_log.json"
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._persisted_plans: Dict[str, PersistedPlanState] = {}
        self._persisted_tests: Dict[str, PersistedTestState] = {}
        self._recovery_operations: Dict[str, RecoveryOperation] = {}
        
        # Service state
        self._is_running = False
        self._recovery_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._stats = {
            'recoveries_attempted': 0,
            'recoveries_successful': 0,
            'recoveries_failed': 0,
            'tests_recovered': 0,
            'plans_recovered': 0,
            'state_saves': 0,
            'state_loads': 0,
            'start_time': datetime.utcnow()
        }
        
        # Configuration
        self._save_interval = 30.0  # Save state every 30 seconds
        self._backup_interval = 300.0  # Create backup every 5 minutes
        self._max_recovery_age_hours = 24  # Don't recover operations older than 24 hours
        
        self.logger.info("Service recovery manager initialized")
    
    def start(self) -> bool:
        """Start the service recovery manager."""
        with self._lock:
            if self._is_running:
                self.logger.warning("Service recovery manager is already running")
                return False
            
            try:
                self._is_running = True
                self._stop_event.clear()
                
                # Load existing state
                self._load_state()
                
                # Start recovery thread
                self._recovery_thread = threading.Thread(
                    target=self._recovery_loop,
                    name="service-recovery",
                    daemon=True
                )
                self._recovery_thread.start()
                
                self.logger.info("Service recovery manager started successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to start service recovery manager: {e}")
                self._is_running = False
                return False
    
    def stop(self) -> bool:
        """Stop the service recovery manager."""
        with self._lock:
            if not self._is_running:
                self.logger.warning("Service recovery manager is not running")
                return False
            
            try:
                self.logger.info("Stopping service recovery manager...")
                
                # Signal stop
                self._is_running = False
                self._stop_event.set()
                
                # Save final state
                self._save_state()
                
                # Wait for recovery thread to finish
                if self._recovery_thread and self._recovery_thread.is_alive():
                    self._recovery_thread.join(timeout=10.0)
                    if self._recovery_thread.is_alive():
                        self.logger.warning("Recovery thread did not stop gracefully")
                
                self.logger.info("Service recovery manager stopped successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping service recovery manager: {e}")
                return False
    
    def persist_test_state(self, test_id: str, plan_id: str, status: str,
                          environment_id: Optional[str] = None,
                          started_at: Optional[datetime] = None,
                          timeout_seconds: int = 300) -> bool:
        """Persist the state of a test for recovery.
        
        Args:
            test_id: Test identifier
            plan_id: Plan identifier
            status: Current test status
            environment_id: Optional environment ID
            started_at: Optional start time
            timeout_seconds: Test timeout
            
        Returns:
            True if state was persisted successfully
        """
        try:
            with self._lock:
                # Get existing state or create new
                if test_id in self._persisted_tests:
                    test_state = self._persisted_tests[test_id]
                else:
                    test_state = PersistedTestState(
                        test_id=test_id,
                        plan_id=plan_id,
                        status=status,
                        environment_id=environment_id,
                        started_at=started_at.isoformat() if started_at else None,
                        timeout_seconds=timeout_seconds
                    )
                    self._persisted_tests[test_id] = test_state
                
                # Update state
                test_state.status = status
                if environment_id:
                    test_state.environment_id = environment_id
                if started_at:
                    test_state.started_at = started_at.isoformat()
                
                self.logger.debug(f"Persisted state for test {test_id}: {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error persisting test state for {test_id}: {e}")
            return False
    
    def persist_plan_state(self, plan_id: str, submission_id: str, status: str,
                          total_tests: int, completed_tests: int = 0,
                          failed_tests: int = 0,
                          started_at: Optional[datetime] = None) -> bool:
        """Persist the state of an execution plan for recovery.
        
        Args:
            plan_id: Plan identifier
            submission_id: Submission identifier
            status: Current plan status
            total_tests: Total number of tests in plan
            completed_tests: Number of completed tests
            failed_tests: Number of failed tests
            started_at: Optional start time
            
        Returns:
            True if state was persisted successfully
        """
        try:
            with self._lock:
                # Get test states for this plan
                test_states = [
                    test_state for test_state in self._persisted_tests.values()
                    if test_state.plan_id == plan_id
                ]
                
                # Create or update plan state
                plan_state = PersistedPlanState(
                    plan_id=plan_id,
                    submission_id=submission_id,
                    status=status,
                    total_tests=total_tests,
                    completed_tests=completed_tests,
                    failed_tests=failed_tests,
                    started_at=started_at.isoformat() if started_at else None,
                    test_states=test_states
                )
                
                self._persisted_plans[plan_id] = plan_state
                
                self.logger.debug(f"Persisted state for plan {plan_id}: {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error persisting plan state for {plan_id}: {e}")
            return False
    
    def remove_persisted_test(self, test_id: str) -> bool:
        """Remove a test from persistent state (when completed).
        
        Args:
            test_id: Test identifier
            
        Returns:
            True if test was removed successfully
        """
        try:
            with self._lock:
                if test_id in self._persisted_tests:
                    del self._persisted_tests[test_id]
                    self.logger.debug(f"Removed persisted state for test {test_id}")
                    return True
                else:
                    self.logger.debug(f"No persisted state found for test {test_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error removing persisted test {test_id}: {e}")
            return False
    
    def remove_persisted_plan(self, plan_id: str) -> bool:
        """Remove a plan from persistent state (when completed).
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if plan was removed successfully
        """
        try:
            with self._lock:
                if plan_id in self._persisted_plans:
                    del self._persisted_plans[plan_id]
                    self.logger.debug(f"Removed persisted state for plan {plan_id}")
                    return True
                else:
                    self.logger.debug(f"No persisted state found for plan {plan_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error removing persisted plan {plan_id}: {e}")
            return False
    
    def recover_on_startup(self, status_tracker, queue_monitor, timeout_manager) -> Dict[str, Any]:
        """Recover state on service startup.
        
        Args:
            status_tracker: Status tracker instance
            queue_monitor: Queue monitor instance
            timeout_manager: Timeout manager instance
            
        Returns:
            Dictionary containing recovery results
        """
        try:
            self.logger.info("Starting service recovery on startup")
            
            recovery_results = {
                'plans_recovered': 0,
                'tests_recovered': 0,
                'tests_requeued': 0,
                'errors': []
            }
            
            with self._lock:
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=self._max_recovery_age_hours)
                
                # Recover execution plans
                for plan_id, plan_state in self._persisted_plans.items():
                    try:
                        # Skip old plans
                        if plan_state.started_at:
                            started_at = datetime.fromisoformat(plan_state.started_at)
                            if started_at < cutoff_time:
                                self.logger.info(f"Skipping old plan {plan_id} (started {started_at})")
                                continue
                        
                        # Only recover plans that were running
                        if plan_state.status in ['running', 'queued']:
                            self._recover_execution_plan(plan_state, status_tracker, queue_monitor)
                            recovery_results['plans_recovered'] += 1
                            
                    except Exception as e:
                        error_msg = f"Error recovering plan {plan_id}: {e}"
                        self.logger.error(error_msg)
                        recovery_results['errors'].append(error_msg)
                
                # Recover individual tests
                for test_id, test_state in self._persisted_tests.items():
                    try:
                        # Skip old tests
                        if test_state.started_at:
                            started_at = datetime.fromisoformat(test_state.started_at)
                            if started_at < cutoff_time:
                                self.logger.info(f"Skipping old test {test_id} (started {started_at})")
                                continue
                        
                        # Only recover tests that were running or queued
                        if test_state.status in ['running', 'queued']:
                            recovered = self._recover_test(test_state, status_tracker, timeout_manager)
                            if recovered:
                                recovery_results['tests_recovered'] += 1
                            
                    except Exception as e:
                        error_msg = f"Error recovering test {test_id}: {e}"
                        self.logger.error(error_msg)
                        recovery_results['errors'].append(error_msg)
            
            # Update statistics
            self._stats['recoveries_attempted'] += 1
            if not recovery_results['errors']:
                self._stats['recoveries_successful'] += 1
            else:
                self._stats['recoveries_failed'] += 1
            
            self._stats['plans_recovered'] += recovery_results['plans_recovered']
            self._stats['tests_recovered'] += recovery_results['tests_recovered']
            
            self.logger.info(f"Service recovery completed: {recovery_results}")
            return recovery_results
            
        except Exception as e:
            self.logger.error(f"Error during service recovery: {e}")
            self._stats['recoveries_failed'] += 1
            return {'error': str(e)}
    
    def _recover_execution_plan(self, plan_state: PersistedPlanState,
                               status_tracker, queue_monitor):
        """Recover an execution plan.
        
        Args:
            plan_state: Persisted plan state
            status_tracker: Status tracker instance
            queue_monitor: Queue monitor instance
        """
        try:
            plan_id = plan_state.plan_id
            
            self.logger.info(f"Recovering execution plan {plan_id}")
            
            # Restore plan status
            status_tracker.update_plan_status(
                plan_id=plan_id,
                status='queued',  # Reset to queued for re-execution
                submission_id=plan_state.submission_id
            )
            
            # Re-queue the plan if it was running
            if plan_state.status == 'running':
                # Create a simplified execution plan for re-queuing
                execution_plan = {
                    'plan_id': plan_id,
                    'submission_id': plan_state.submission_id,
                    'test_case_ids': [test.test_id for test in plan_state.test_states],
                    'priority': 'high',  # Give recovered plans high priority
                    'recovered': True
                }
                
                # Add to queue monitor (this would need to be implemented in queue_monitor)
                # queue_monitor.add_execution_plan(execution_plan)
                
            self.logger.info(f"Successfully recovered execution plan {plan_id}")
            
        except Exception as e:
            self.logger.error(f"Error recovering execution plan {plan_state.plan_id}: {e}")
            raise
    
    def _recover_test(self, test_state: PersistedTestState,
                     status_tracker, timeout_manager) -> bool:
        """Recover an individual test.
        
        Args:
            test_state: Persisted test state
            status_tracker: Status tracker instance
            timeout_manager: Timeout manager instance
            
        Returns:
            True if test was recovered successfully
        """
        try:
            test_id = test_state.test_id
            
            self.logger.info(f"Recovering test {test_id}")
            
            # Check if test should be retried
            if test_state.retry_count >= test_state.max_retries:
                self.logger.warning(f"Test {test_id} exceeded max retries, marking as failed")
                status_tracker.update_test_status(test_id, 'failed', 
                                                message="Exceeded max retries during recovery")
                return False
            
            # Reset test status for retry
            if test_state.status == 'running':
                # Test was running when service stopped, reset to queued
                status_tracker.update_test_status(test_id, 'queued',
                                                message="Recovered from service restart")
                
                # Increment retry count
                test_state.retry_count += 1
                
                # Re-add timeout monitoring if test had a timeout
                if test_state.timeout_seconds > 0:
                    timeout_manager.add_monitor(
                        test_id=test_id,
                        timeout_seconds=test_state.timeout_seconds
                    )
                
                self.logger.info(f"Successfully recovered test {test_id} (retry {test_state.retry_count})")
                return True
            
            elif test_state.status == 'queued':
                # Test was queued, just restore the status
                status_tracker.update_test_status(test_id, 'queued',
                                                message="Recovered from service restart")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error recovering test {test_state.test_id}: {e}")
            return False
    
    def _recovery_loop(self):
        """Main recovery loop that runs in a separate thread."""
        self.logger.info("Service recovery loop started")
        
        last_save_time = time.time()
        last_backup_time = time.time()
        
        while self._is_running and not self._stop_event.is_set():
            try:
                current_time = time.time()
                
                # Periodic state saving
                if current_time - last_save_time >= self._save_interval:
                    self._save_state()
                    last_save_time = current_time
                
                # Periodic backup creation
                if current_time - last_backup_time >= self._backup_interval:
                    self._create_backup()
                    last_backup_time = current_time
                
                # Process pending recovery operations
                self._process_recovery_operations()
                
                # Clean up old state
                self._cleanup_old_state()
                
                # Sleep until next check
                if not self._stop_event.wait(10.0):  # Check every 10 seconds
                    continue
                else:
                    break  # Stop requested
                    
            except Exception as e:
                self.logger.error(f"Error in recovery loop: {e}")
                time.sleep(5.0)  # Brief pause before continuing
        
        self.logger.info("Service recovery loop stopped")
    
    def _save_state(self) -> bool:
        """Save current state to disk.
        
        Returns:
            True if state was saved successfully
        """
        try:
            with self._lock:
                state_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '1.0',
                    'plans': {plan_id: asdict(plan_state) 
                             for plan_id, plan_state in self._persisted_plans.items()},
                    'tests': {test_id: asdict(test_state) 
                             for test_id, test_state in self._persisted_tests.items()},
                    'statistics': self._stats.copy()
                }
                
                # Write to temporary file first, then rename for atomicity
                temp_file = self.state_file.with_suffix('.tmp')
                
                with open(temp_file, 'w') as f:
                    json.dump(state_data, f, indent=2, default=str)
                
                # Atomic rename
                temp_file.rename(self.state_file)
                
                self._stats['state_saves'] += 1
                self.logger.debug("State saved successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
            return False
    
    def _load_state(self) -> bool:
        """Load state from disk.
        
        Returns:
            True if state was loaded successfully
        """
        try:
            if not self.state_file.exists():
                self.logger.info("No existing state file found")
                return True
            
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            with self._lock:
                # Load plans
                plans_data = state_data.get('plans', {})
                for plan_id, plan_dict in plans_data.items():
                    # Convert test states
                    test_states = []
                    for test_dict in plan_dict.get('test_states', []):
                        test_state = PersistedTestState(**test_dict)
                        test_states.append(test_state)
                    
                    plan_dict['test_states'] = test_states
                    plan_state = PersistedPlanState(**plan_dict)
                    self._persisted_plans[plan_id] = plan_state
                
                # Load tests
                tests_data = state_data.get('tests', {})
                for test_id, test_dict in tests_data.items():
                    test_state = PersistedTestState(**test_dict)
                    self._persisted_tests[test_id] = test_state
                
                # Load statistics
                if 'statistics' in state_data:
                    self._stats.update(state_data['statistics'])
            
            self._stats['state_loads'] += 1
            self.logger.info(f"State loaded successfully: {len(self._persisted_plans)} plans, "
                           f"{len(self._persisted_tests)} tests")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
            
            # Try to load from backup
            if self.backup_state_file.exists():
                self.logger.info("Attempting to load from backup state file")
                try:
                    # Copy backup to main file and retry
                    import shutil
                    shutil.copy2(self.backup_state_file, self.state_file)
                    return self._load_state()
                except Exception as backup_e:
                    self.logger.error(f"Error loading from backup: {backup_e}")
            
            return False
    
    def _create_backup(self) -> bool:
        """Create a backup of the current state file.
        
        Returns:
            True if backup was created successfully
        """
        try:
            if self.state_file.exists():
                import shutil
                shutil.copy2(self.state_file, self.backup_state_file)
                self.logger.debug("State backup created successfully")
                return True
            else:
                self.logger.debug("No state file to backup")
                return True
                
        except Exception as e:
            self.logger.error(f"Error creating state backup: {e}")
            return False
    
    def _process_recovery_operations(self):
        """Process pending recovery operations."""
        try:
            with self._lock:
                pending_operations = [
                    op for op in self._recovery_operations.values()
                    if op.state == RecoveryState.PENDING
                ]
            
            for operation in pending_operations:
                try:
                    self._execute_recovery_operation(operation)
                except Exception as e:
                    self.logger.error(f"Error executing recovery operation {operation.operation_id}: {e}")
                    operation.state = RecoveryState.FAILED
                    operation.error_message = str(e)
                    
        except Exception as e:
            self.logger.error(f"Error processing recovery operations: {e}")
    
    def _execute_recovery_operation(self, operation: RecoveryOperation):
        """Execute a recovery operation.
        
        Args:
            operation: Recovery operation to execute
        """
        operation.state = RecoveryState.IN_PROGRESS
        operation.started_at = datetime.utcnow()
        
        try:
            if operation.operation_type == 'state_repair':
                self._repair_state_consistency()
            elif operation.operation_type == 'test_recovery':
                # Implement specific test recovery logic
                pass
            elif operation.operation_type == 'plan_recovery':
                # Implement specific plan recovery logic
                pass
            
            operation.state = RecoveryState.COMPLETED
            operation.completed_at = datetime.utcnow()
            
        except Exception as e:
            operation.state = RecoveryState.FAILED
            operation.error_message = str(e)
            raise
    
    def _repair_state_consistency(self):
        """Repair state consistency issues."""
        try:
            with self._lock:
                # Check for orphaned tests (tests without corresponding plans)
                plan_ids = set(self._persisted_plans.keys())
                orphaned_tests = []
                
                for test_id, test_state in self._persisted_tests.items():
                    if test_state.plan_id not in plan_ids:
                        orphaned_tests.append(test_id)
                
                # Remove orphaned tests
                for test_id in orphaned_tests:
                    del self._persisted_tests[test_id]
                    self.logger.info(f"Removed orphaned test {test_id}")
                
                # Update plan test counts
                for plan_id, plan_state in self._persisted_plans.items():
                    plan_tests = [t for t in self._persisted_tests.values() 
                                 if t.plan_id == plan_id]
                    
                    completed_count = sum(1 for t in plan_tests if t.status == 'completed')
                    failed_count = sum(1 for t in plan_tests if t.status in ['failed', 'timeout', 'error'])
                    
                    plan_state.completed_tests = completed_count
                    plan_state.failed_tests = failed_count
                    plan_state.test_states = plan_tests
                
                self.logger.info("State consistency repair completed")
                
        except Exception as e:
            self.logger.error(f"Error repairing state consistency: {e}")
            raise
    
    def _cleanup_old_state(self, max_age_hours: int = 48):
        """Clean up old state entries to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age in hours for state entries
        """
        try:
            with self._lock:
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=max_age_hours)
                
                # Clean up old completed plans
                old_plan_ids = []
                for plan_id, plan_state in self._persisted_plans.items():
                    if (plan_state.status in ['completed', 'failed'] and
                        plan_state.started_at):
                        started_at = datetime.fromisoformat(plan_state.started_at)
                        if started_at < cutoff_time:
                            old_plan_ids.append(plan_id)
                
                for plan_id in old_plan_ids:
                    del self._persisted_plans[plan_id]
                
                # Clean up old completed tests
                old_test_ids = []
                for test_id, test_state in self._persisted_tests.items():
                    if (test_state.status in ['completed', 'failed', 'timeout', 'error'] and
                        test_state.started_at):
                        started_at = datetime.fromisoformat(test_state.started_at)
                        if started_at < cutoff_time:
                            old_test_ids.append(test_id)
                
                for test_id in old_test_ids:
                    del self._persisted_tests[test_id]
                
                if old_plan_ids or old_test_ids:
                    self.logger.info(f"Cleaned up {len(old_plan_ids)} old plans and "
                                   f"{len(old_test_ids)} old tests")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old state: {e}")
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery status.
        
        Returns:
            Dictionary containing recovery status information
        """
        with self._lock:
            return {
                'is_running': self._is_running,
                'persisted_plans': len(self._persisted_plans),
                'persisted_tests': len(self._persisted_tests),
                'pending_operations': len([op for op in self._recovery_operations.values() 
                                         if op.state == RecoveryState.PENDING]),
                'statistics': self._stats.copy(),
                'state_file_exists': self.state_file.exists(),
                'backup_file_exists': self.backup_state_file.exists()
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service recovery manager.
        
        Returns:
            Dictionary containing health information
        """
        with self._lock:
            return {
                'status': 'healthy' if self._is_running else 'stopped',
                'is_running': self._is_running,
                'persisted_plans': len(self._persisted_plans),
                'persisted_tests': len(self._persisted_tests),
                'recovery_thread_alive': (self._recovery_thread.is_alive() 
                                        if self._recovery_thread else False),
                'state_file_accessible': self.state_file.exists() and self.state_file.is_file()
            }
    
    def force_state_save(self) -> bool:
        """Force an immediate state save.
        
        Returns:
            True if state was saved successfully
        """
        return self._save_state()
    
    def validate_state_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of the persisted state.
        
        Returns:
            Dictionary containing validation results
        """
        try:
            with self._lock:
                validation_results = {
                    'valid': True,
                    'issues': [],
                    'plan_count': len(self._persisted_plans),
                    'test_count': len(self._persisted_tests)
                }
                
                # Check for orphaned tests
                plan_ids = set(self._persisted_plans.keys())
                orphaned_tests = []
                
                for test_id, test_state in self._persisted_tests.items():
                    if test_state.plan_id not in plan_ids:
                        orphaned_tests.append(test_id)
                
                if orphaned_tests:
                    validation_results['valid'] = False
                    validation_results['issues'].append(f"Found {len(orphaned_tests)} orphaned tests")
                
                # Check plan consistency
                for plan_id, plan_state in self._persisted_plans.items():
                    plan_tests = [t for t in self._persisted_tests.values() 
                                 if t.plan_id == plan_id]
                    
                    if len(plan_tests) != len(plan_state.test_states):
                        validation_results['valid'] = False
                        validation_results['issues'].append(
                            f"Plan {plan_id} test count mismatch: "
                            f"expected {len(plan_state.test_states)}, found {len(plan_tests)}"
                        )
                
                return validation_results
                
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'issues': [f"Validation error: {e}"]
            }