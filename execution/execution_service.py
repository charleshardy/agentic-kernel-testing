"""
Execution Service - Bridges API and Test Runner for actual test execution.

This service handles:
- Execution plan processing
- Test case execution coordination
- Real-time progress updates
- Result collection and storage
- Environment management
"""

import asyncio
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future
import logging

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle
)
from execution.test_runner import TestRunner, ExecutionHandle
from execution.environment_manager import EnvironmentManager
from execution.runner_factory import get_runner_factory, create_test_runner

logger = logging.getLogger(__name__)


@dataclass
class ExecutionProgress:
    """Progress information for an execution plan."""
    plan_id: str
    total_tests: int
    completed_tests: int
    failed_tests: int
    running_tests: int
    progress_percentage: float
    current_test: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "plan_id": self.plan_id,
            "total_tests": self.total_tests,
            "completed_tests": self.completed_tests,
            "failed_tests": self.failed_tests,
            "running_tests": self.running_tests,
            "progress": self.progress_percentage / 100.0,
            "current_test": self.current_test,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None
        }


@dataclass
class ExecutionPlan:
    """Execution plan with test cases and metadata."""
    plan_id: str
    test_cases: List[TestCase]
    priority: int
    status: str
    created_at: datetime
    created_by: str
    environment_preference: Optional[str] = None
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ExecutionService:
    """Service for managing test execution lifecycle."""
    
    def __init__(self):
        """Initialize the execution service."""
        self.environment_manager = EnvironmentManager()
        self.test_runner = TestRunner(self.environment_manager)
        self.runner_factory = get_runner_factory()
        
        # Execution tracking
        self.active_executions: Dict[str, ExecutionPlan] = {}
        self.execution_progress: Dict[str, ExecutionProgress] = {}
        self.execution_results: Dict[str, List[TestResult]] = {}
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="execution")
        self._lock = threading.Lock()
        
        # Progress callbacks
        self.progress_callbacks: List[Callable[[str, ExecutionProgress], None]] = []
        
        # Initialize default environments
        self._initialize_default_environments()
    
    def _initialize_default_environments(self):
        """Initialize default test environments."""
        try:
            # Create a few default virtual environments
            configs = [
                HardwareConfig(
                    architecture="x86_64",
                    cpu_model="qemu64",
                    memory_mb=2048,
                    storage_type="ssd",
                    is_virtual=True,
                    emulator="qemu"
                ),
                HardwareConfig(
                    architecture="x86_64", 
                    cpu_model="host",
                    memory_mb=4096,
                    storage_type="ssd",
                    is_virtual=True,
                    emulator="kvm"
                )
            ]
            
            for config in configs:
                try:
                    env = self.environment_manager.provision_environment(config)
                    logger.info(f"Provisioned default environment: {env.id}")
                except Exception as e:
                    logger.warning(f"Failed to provision default environment: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing default environments: {e}")
    
    def register_progress_callback(self, callback: Callable[[str, ExecutionProgress], None]):
        """Register a callback for execution progress updates."""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, plan_id: str, progress: ExecutionProgress):
        """Notify all registered callbacks of progress updates."""
        for callback in self.progress_callbacks:
            try:
                callback(plan_id, progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def start_execution(self, plan_id: str, test_cases: List[TestCase], 
                       created_by: str, priority: int = 5,
                       environment_preference: Optional[str] = None,
                       timeout: Optional[int] = None) -> bool:
        """Start execution of a test plan.
        
        Args:
            plan_id: Unique identifier for the execution plan
            test_cases: List of test cases to execute
            created_by: User who started the execution
            priority: Execution priority (1-10, higher is more important)
            environment_preference: Preferred environment type
            timeout: Optional timeout per test in seconds
            
        Returns:
            True if execution started successfully
        """
        try:
            with self._lock:
                if plan_id in self.active_executions:
                    logger.warning(f"Execution plan {plan_id} is already active")
                    return False
                
                # Create execution plan
                execution_plan = ExecutionPlan(
                    plan_id=plan_id,
                    test_cases=test_cases,
                    priority=priority,
                    status="running",
                    created_at=datetime.utcnow(),
                    created_by=created_by,
                    environment_preference=environment_preference,
                    timeout=timeout
                )
                
                self.active_executions[plan_id] = execution_plan
                
                # Initialize progress tracking
                progress = ExecutionProgress(
                    plan_id=plan_id,
                    total_tests=len(test_cases),
                    completed_tests=0,
                    failed_tests=0,
                    running_tests=0,
                    progress_percentage=0.0,
                    estimated_completion=datetime.utcnow() + timedelta(
                        seconds=len(test_cases) * (timeout or 60)
                    )
                )
                self.execution_progress[plan_id] = progress
                self.execution_results[plan_id] = []
            
            # Start execution in background thread
            future = self.executor.submit(self._execute_plan, execution_plan)
            
            logger.info(f"Started execution plan {plan_id} with {len(test_cases)} tests")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start execution plan {plan_id}: {e}")
            return False
    
    def _execute_plan(self, execution_plan: ExecutionPlan):
        """Execute a test plan in a background thread."""
        plan_id = execution_plan.plan_id
        
        try:
            logger.info(f"Executing plan {plan_id} with {len(execution_plan.test_cases)} tests")
            
            # Get available environments
            environments = self.environment_manager.get_idle_environments()
            
            if not environments:
                logger.warning(f"No idle environments available for plan {plan_id}")
                # Try to provision a new environment
                try:
                    config = HardwareConfig(
                        architecture="x86_64",
                        cpu_model="qemu64", 
                        memory_mb=2048,
                        is_virtual=True,
                        emulator="qemu"
                    )
                    env = self.environment_manager.provision_environment(config)
                    environments = [env]
                    logger.info(f"Provisioned new environment {env.id} for plan {plan_id}")
                except Exception as e:
                    logger.error(f"Failed to provision environment for plan {plan_id}: {e}")
                    self._mark_execution_failed(plan_id, f"No environments available: {e}")
                    return
            
            # Execute tests sequentially for now (can be parallelized later)
            for i, test_case in enumerate(execution_plan.test_cases):
                if self._is_execution_cancelled(plan_id):
                    logger.info(f"Execution plan {plan_id} was cancelled")
                    break
                
                # Update progress - test starting
                with self._lock:
                    progress = self.execution_progress[plan_id]
                    progress.running_tests = 1
                    progress.current_test = test_case.name
                    self._notify_progress(plan_id, progress)
                
                # Select environment (round-robin for now)
                env = environments[i % len(environments)]
                
                # Execute the test with timeout protection
                try:
                    logger.info(f"Executing test {test_case.id} ({test_case.name}) in environment {env.id}")
                    
                    # Use a timeout to prevent hanging
                    test_timeout = execution_plan.timeout or 60  # Default 60 seconds per test
                    
                    # Execute with timeout using the mock runner for now
                    from execution.runners.mock_runner import MockTestRunner
                    runner = MockTestRunner(env)
                    
                    # Simulate test execution
                    result_data = runner.execute(test_case, timeout=test_timeout)
                    
                    # Create TestResult object
                    from ai_generator.models import TestResult, FailureInfo
                    
                    failure_info = None
                    if result_data['status'] != TestStatus.PASSED:
                        failure_info = FailureInfo(
                            error_message=result_data.get('error', 'Test failed'),
                            stack_trace=None,
                            exit_code=result_data.get('exit_code'),
                            kernel_panic=False,
                            timeout_occurred=result_data['status'] == TestStatus.TIMEOUT
                        )
                    
                    result = TestResult(
                        test_id=test_case.id,
                        status=result_data['status'],
                        execution_time=result_data['execution_time'],
                        environment=env,
                        failure_info=failure_info,
                        timestamp=datetime.utcnow()
                    )
                    
                    # Store result
                    with self._lock:
                        self.execution_results[plan_id].append(result)
                        
                        # Update progress
                        progress = self.execution_progress[plan_id]
                        progress.completed_tests += 1
                        progress.running_tests = 0
                        
                        if result.status in [TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT]:
                            progress.failed_tests += 1
                        
                        progress.progress_percentage = (progress.completed_tests / progress.total_tests) * 100
                        
                        # Update estimated completion
                        if progress.completed_tests > 0:
                            avg_time_per_test = sum(r.execution_time for r in self.execution_results[plan_id]) / progress.completed_tests
                            remaining_tests = progress.total_tests - progress.completed_tests
                            progress.estimated_completion = datetime.utcnow() + timedelta(seconds=remaining_tests * avg_time_per_test)
                        
                        self._notify_progress(plan_id, progress)
                    
                    logger.info(f"Test {test_case.id} completed with status: {result.status}")
                    
                except Exception as e:
                    logger.error(f"Error executing test {test_case.id}: {e}")
                    
                    # Create error result
                    from ai_generator.models import TestResult, FailureInfo
                    
                    failure_info = FailureInfo(
                        error_message=f"Execution error: {str(e)}",
                        stack_trace=None,
                        exit_code=None,
                        kernel_panic=False,
                        timeout_occurred=False
                    )
                    
                    error_result = TestResult(
                        test_id=test_case.id,
                        status=TestStatus.ERROR,
                        execution_time=0.0,
                        environment=env,
                        failure_info=failure_info,
                        timestamp=datetime.utcnow()
                    )
                    
                    with self._lock:
                        self.execution_results[plan_id].append(error_result)
                        progress = self.execution_progress[plan_id]
                        progress.completed_tests += 1
                        progress.failed_tests += 1
                        progress.running_tests = 0
                        progress.progress_percentage = (progress.completed_tests / progress.total_tests) * 100
                        self._notify_progress(plan_id, progress)
            
            # Mark execution as completed
            with self._lock:
                if plan_id in self.active_executions:
                    self.active_executions[plan_id].status = "completed"
                    progress = self.execution_progress[plan_id]
                    progress.running_tests = 0
                    progress.current_test = None
                    self._notify_progress(plan_id, progress)
            
            logger.info(f"Execution plan {plan_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in execution plan {plan_id}: {e}")
            self._mark_execution_failed(plan_id, str(e))
    
    def _is_execution_cancelled(self, plan_id: str) -> bool:
        """Check if an execution has been cancelled."""
        with self._lock:
            plan = self.active_executions.get(plan_id)
            return plan is None or plan.status == "cancelled"
    
    def _mark_execution_failed(self, plan_id: str, error_message: str):
        """Mark an execution as failed."""
        with self._lock:
            if plan_id in self.active_executions:
                self.active_executions[plan_id].status = "failed"
                self.active_executions[plan_id].metadata["error"] = error_message
                
                progress = self.execution_progress.get(plan_id)
                if progress:
                    progress.running_tests = 0
                    progress.current_test = None
                    self._notify_progress(plan_id, progress)
        
        logger.error(f"Execution plan {plan_id} failed: {error_message}")
    
    def cancel_execution(self, plan_id: str) -> bool:
        """Cancel an active execution.
        
        Args:
            plan_id: ID of the execution to cancel
            
        Returns:
            True if cancelled successfully
        """
        try:
            with self._lock:
                plan = self.active_executions.get(plan_id)
                if not plan:
                    return False
                
                if plan.status not in ["running", "queued"]:
                    return False
                
                plan.status = "cancelled"
                
                # Update progress
                progress = self.execution_progress.get(plan_id)
                if progress:
                    progress.running_tests = 0
                    progress.current_test = None
                    self._notify_progress(plan_id, progress)
            
            logger.info(f"Cancelled execution plan {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling execution {plan_id}: {e}")
            return False
    
    def get_execution_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of an execution.
        
        Args:
            plan_id: ID of the execution
            
        Returns:
            Status dictionary or None if not found
        """
        with self._lock:
            plan = self.active_executions.get(plan_id)
            progress = self.execution_progress.get(plan_id)
            results = self.execution_results.get(plan_id, [])
            
            if not plan:
                return None
            
            # Build test case status list
            test_statuses = []
            for i, test_case in enumerate(plan.test_cases):
                # Find result for this test
                test_result = None
                for result in results:
                    if result.test_id == test_case.id:
                        test_result = result
                        break
                
                if test_result:
                    status = test_result.status.value if hasattr(test_result.status, 'value') else str(test_result.status)
                elif progress and progress.current_test == test_case.name:
                    status = "running"
                else:
                    status = "queued"
                
                test_statuses.append({
                    "test_id": test_case.id,
                    "name": test_case.name,
                    "description": test_case.description,
                    "test_type": test_case.test_type.value if hasattr(test_case.test_type, 'value') else str(test_case.test_type),
                    "target_subsystem": test_case.target_subsystem,
                    "execution_status": status,
                    "execution_time_estimate": test_case.execution_time_estimate
                })
            
            status_dict = {
                "plan_id": plan_id,
                "submission_id": plan.metadata.get("submission_id", plan_id),
                "overall_status": plan.status,
                "total_tests": len(plan.test_cases),
                "completed_tests": progress.completed_tests if progress else 0,
                "failed_tests": progress.failed_tests if progress else 0,
                "progress": (progress.progress_percentage / 100.0) if progress else 0.0,
                "started_at": plan.created_at.isoformat(),
                "estimated_completion": progress.estimated_completion.isoformat() if progress and progress.estimated_completion else None,
                "test_cases": test_statuses,
                "test_statuses": []  # Legacy field
            }
            
            return status_dict
    
    def get_active_executions(self) -> List[Dict[str, Any]]:
        """Get all active executions.
        
        Returns:
            List of execution status dictionaries
        """
        active_list = []
        
        with self._lock:
            for plan_id in list(self.active_executions.keys()):
                status = self.get_execution_status(plan_id)
                if status and status["overall_status"] in ["running", "queued"]:
                    active_list.append(status)
        
        return active_list
    
    def cleanup_completed_executions(self, max_age_hours: int = 24) -> int:
        """Clean up old completed executions.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of executions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned = 0
        
        with self._lock:
            plans_to_remove = []
            
            for plan_id, plan in self.active_executions.items():
                if (plan.status in ["completed", "failed", "cancelled"] and 
                    plan.created_at < cutoff_time):
                    plans_to_remove.append(plan_id)
            
            for plan_id in plans_to_remove:
                del self.active_executions[plan_id]
                if plan_id in self.execution_progress:
                    del self.execution_progress[plan_id]
                if plan_id in self.execution_results:
                    del self.execution_results[plan_id]
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} old executions")
        return cleaned
    
    def get_execution_results(self, plan_id: str) -> Optional[List[TestResult]]:
        """Get results for a completed execution.
        
        Args:
            plan_id: ID of the execution
            
        Returns:
            List of test results or None if not found
        """
        with self._lock:
            return self.execution_results.get(plan_id)
    
    def shutdown(self):
        """Shutdown the execution service."""
        logger.info("Shutting down execution service")
        
        # Cancel all active executions
        with self._lock:
            for plan_id in list(self.active_executions.keys()):
                self.cancel_execution(plan_id)
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        # Shutdown test runner
        self.test_runner.shutdown()


# Global execution service instance
_execution_service: Optional[ExecutionService] = None


def get_execution_service() -> ExecutionService:
    """Get the global execution service instance."""
    global _execution_service
    if _execution_service is None:
        _execution_service = ExecutionService()
    return _execution_service


def start_execution_service() -> ExecutionService:
    """Start and return the execution service."""
    service = get_execution_service()
    logger.info("Execution service started")
    return service