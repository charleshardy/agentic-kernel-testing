"""Test orchestrator and scheduler for managing test execution.

This module provides functionality for:
- Priority queue for test jobs
- Scheduling algorithm (bin packing with priorities)
- Resource allocation and tracking
- Dynamic rescheduling based on results
- Test dependencies and ordering
"""

import heapq
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Set, Callable, Any
from collections import defaultdict

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, RiskLevel
)
from execution.test_runner import TestRunner, ExecutionHandle
from config.settings import get_settings


class Priority(int, Enum):
    """Test priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TestJob:
    """A test job to be scheduled."""
    id: str
    test_case: TestCase
    priority: Priority
    impact_score: float  # 0.0 to 1.0
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TestResult] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other: 'TestJob') -> bool:
        """Compare jobs for priority queue ordering.
        
        Higher priority and higher impact score come first.
        """
        # Primary: priority (higher is better)
        if self.priority != other.priority:
            return self.priority > other.priority
        
        # Secondary: impact score (higher is better)
        if abs(self.impact_score - other.impact_score) > 0.001:
            return self.impact_score > other.impact_score
        
        # Tertiary: creation time (earlier is better)
        return self.created_at < other.created_at
    
    def can_schedule(self, completed_jobs: Set[str]) -> bool:
        """Check if all dependencies are satisfied.
        
        Args:
            completed_jobs: Set of completed job IDs
            
        Returns:
            True if job can be scheduled
        """
        return all(dep_id in completed_jobs for dep_id in self.dependencies)


@dataclass
class ResourceAllocation:
    """Tracks resource allocation for test execution."""
    environment_id: str
    job_id: str
    allocated_at: datetime
    estimated_duration: int  # seconds
    
    def is_expired(self, current_time: datetime) -> bool:
        """Check if allocation has exceeded estimated duration.
        
        Args:
            current_time: Current time
            
        Returns:
            True if allocation is expired
        """
        elapsed = (current_time - self.allocated_at).total_seconds()
        return elapsed > self.estimated_duration * 1.5  # 50% buffer


class TestOrchestrator:
    """Orchestrates test scheduling and execution across resources."""
    
    def __init__(self, test_runner: Optional[TestRunner] = None):
        """Initialize test orchestrator.
        
        Args:
            test_runner: Test runner for executing tests
        """
        self.settings = get_settings()
        self.test_runner = test_runner or TestRunner()
        
        # Priority queue for pending jobs (min-heap, but we use __lt__ for max behavior)
        self._job_queue: List[TestJob] = []
        self._job_map: Dict[str, TestJob] = {}
        
        # Resource tracking
        self._available_environments: List[Environment] = []
        self._allocated_resources: Dict[str, ResourceAllocation] = {}
        
        # Execution tracking
        self._completed_jobs: Set[str] = set()
        self._running_jobs: Dict[str, str] = {}  # job_id -> environment_id
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Callbacks for events
        self._on_job_complete: Optional[Callable[[TestJob], None]] = None
        self._on_job_failed: Optional[Callable[[TestJob], None]] = None
    
    def add_environment(self, environment: Environment) -> None:
        """Add an environment to the available pool.
        
        Args:
            environment: Environment to add
        """
        with self._lock:
            if environment.status == EnvironmentStatus.IDLE:
                self._available_environments.append(environment)
    
    def remove_environment(self, environment_id: str) -> bool:
        """Remove an environment from the pool.
        
        Args:
            environment_id: ID of environment to remove
            
        Returns:
            True if removed successfully
        """
        with self._lock:
            # Remove from available list
            self._available_environments = [
                env for env in self._available_environments 
                if env.id != environment_id
            ]
            
            # Check if it's allocated
            if environment_id in self._allocated_resources:
                return False
            
            return True
    
    def submit_job(
        self,
        test_case: TestCase,
        priority: Priority = Priority.MEDIUM,
        impact_score: float = 0.5,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Submit a test job to the scheduler.
        
        Args:
            test_case: Test case to execute
            priority: Job priority
            impact_score: Code change impact score (0.0 to 1.0)
            dependencies: List of job IDs that must complete first
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        job = TestJob(
            id=job_id,
            test_case=test_case,
            priority=priority,
            impact_score=impact_score,
            dependencies=dependencies or []
        )
        
        with self._lock:
            self._job_map[job_id] = job
            heapq.heappush(self._job_queue, job)
        
        # Try to schedule immediately
        self._schedule_next_jobs()
        
        return job_id
    
    def submit_jobs(
        self,
        test_cases: List[TestCase],
        priority: Priority = Priority.MEDIUM,
        impact_scores: Optional[List[float]] = None
    ) -> List[str]:
        """Submit multiple test jobs.
        
        Args:
            test_cases: List of test cases
            priority: Default priority for all jobs
            impact_scores: Optional list of impact scores (same length as test_cases)
            
        Returns:
            List of job IDs
        """
        if impact_scores is None:
            impact_scores = [0.5] * len(test_cases)
        
        if len(impact_scores) != len(test_cases):
            raise ValueError("impact_scores must have same length as test_cases")
        
        job_ids = []
        for test_case, impact_score in zip(test_cases, impact_scores):
            job_id = self.submit_job(test_case, priority, impact_score)
            job_ids.append(job_id)
        
        return job_ids
    
    def _schedule_next_jobs(self) -> None:
        """Schedule next available jobs to idle environments."""
        with self._lock:
            while self._available_environments and self._job_queue:
                # Get highest priority job that can be scheduled
                schedulable_job = self._find_schedulable_job()
                
                if not schedulable_job:
                    break
                
                # Find best environment for this job
                environment = self._find_best_environment(schedulable_job)
                
                if not environment:
                    break
                
                # Allocate and execute
                self._allocate_and_execute(schedulable_job, environment)
    
    def _find_schedulable_job(self) -> Optional[TestJob]:
        """Find the highest priority job that can be scheduled.
        
        Returns:
            Schedulable job or None
        """
        # Create a temporary list to check jobs
        temp_queue = []
        schedulable_job = None
        
        while self._job_queue:
            job = heapq.heappop(self._job_queue)
            
            if job.can_schedule(self._completed_jobs):
                schedulable_job = job
                # Put remaining jobs back
                for remaining_job in temp_queue:
                    heapq.heappush(self._job_queue, remaining_job)
                break
            else:
                temp_queue.append(job)
        
        # Put all jobs back if none were schedulable
        if not schedulable_job:
            for job in temp_queue:
                heapq.heappush(self._job_queue, job)
        
        return schedulable_job
    
    def _find_best_environment(self, job: TestJob) -> Optional[Environment]:
        """Find the best environment for a job using bin packing.
        
        Args:
            job: Job to schedule
            
        Returns:
            Best environment or None
        """
        if not self._available_environments:
            return None
        
        required_hw = job.test_case.required_hardware
        
        if not required_hw:
            # No specific requirements, use any available environment
            return self._available_environments[0]
        
        # Find matching environments
        matching_envs = []
        for env in self._available_environments:
            if self._hardware_matches(env.config, required_hw):
                matching_envs.append(env)
        
        if not matching_envs:
            return None
        
        # Prefer virtual environments for faster execution
        virtual_envs = [e for e in matching_envs if e.config.is_virtual]
        if virtual_envs:
            return virtual_envs[0]
        
        return matching_envs[0]
    
    def _hardware_matches(
        self,
        env_config: HardwareConfig,
        required_config: HardwareConfig
    ) -> bool:
        """Check if environment hardware matches requirements.
        
        Args:
            env_config: Environment hardware configuration
            required_config: Required hardware configuration
            
        Returns:
            True if hardware matches
        """
        # Check architecture
        if env_config.architecture != required_config.architecture:
            return False
        
        # Check memory (environment must have at least required memory)
        if env_config.memory_mb < required_config.memory_mb:
            return False
        
        # Check peripherals (environment must have all required peripherals)
        required_peripheral_types = set(p.type for p in required_config.peripherals)
        env_peripheral_types = set(p.type for p in env_config.peripherals)
        
        if not required_peripheral_types.issubset(env_peripheral_types):
            return False
        
        return True
    
    def _allocate_and_execute(self, job: TestJob, environment: Environment) -> None:
        """Allocate environment and execute job.
        
        Args:
            job: Job to execute
            environment: Environment to use
        """
        # Remove environment from available pool
        self._available_environments.remove(environment)
        
        # Create allocation
        allocation = ResourceAllocation(
            environment_id=environment.id,
            job_id=job.id,
            allocated_at=datetime.now(),
            estimated_duration=job.test_case.execution_time_estimate
        )
        self._allocated_resources[environment.id] = allocation
        self._running_jobs[job.id] = environment.id
        
        # Mark job as scheduled
        job.scheduled_at = datetime.now()
        
        # Execute in background thread
        def execute_job():
            try:
                result = self.test_runner.execute_test(
                    job.test_case,
                    environment,
                    timeout=job.test_case.execution_time_estimate
                )
                
                with self._lock:
                    job.result = result
                    job.completed_at = datetime.now()
                    
                    # Handle result
                    if result.status == TestStatus.PASSED:
                        self._handle_job_success(job, environment)
                    else:
                        self._handle_job_failure(job, environment)
                        
            except Exception as e:
                with self._lock:
                    self._handle_job_error(job, environment, str(e))
        
        threading.Thread(target=execute_job, daemon=True).start()
    
    def _handle_job_success(self, job: TestJob, environment: Environment) -> None:
        """Handle successful job completion.
        
        Args:
            job: Completed job
            environment: Environment used
        """
        # Mark as completed
        self._completed_jobs.add(job.id)
        
        # Release resources
        self._release_resources(job.id, environment)
        
        # Trigger callback
        if self._on_job_complete:
            self._on_job_complete(job)
        
        # Schedule next jobs
        self._schedule_next_jobs()
    
    def _handle_job_failure(self, job: TestJob, environment: Environment) -> None:
        """Handle job failure with retry logic.
        
        Args:
            job: Failed job
            environment: Environment used
        """
        # Check if we should retry
        if job.retry_count < job.max_retries:
            job.retry_count += 1
            job.scheduled_at = None
            
            # Re-queue the job
            heapq.heappush(self._job_queue, job)
            
            # Release resources
            self._release_resources(job.id, environment)
            
            # Schedule next jobs
            self._schedule_next_jobs()
        else:
            # Max retries exceeded, mark as completed (failed)
            self._completed_jobs.add(job.id)
            
            # Release resources
            self._release_resources(job.id, environment)
            
            # Trigger callback
            if self._on_job_failed:
                self._on_job_failed(job)
            
            # Schedule next jobs
            self._schedule_next_jobs()
    
    def _handle_job_error(
        self,
        job: TestJob,
        environment: Environment,
        error: str
    ) -> None:
        """Handle job execution error.
        
        Args:
            job: Job that errored
            environment: Environment used
            error: Error message
        """
        # Treat as failure
        self._handle_job_failure(job, environment)
    
    def _release_resources(self, job_id: str, environment: Environment) -> None:
        """Release allocated resources.
        
        Args:
            job_id: Job ID
            environment: Environment to release
        """
        # Remove allocation
        if environment.id in self._allocated_resources:
            del self._allocated_resources[environment.id]
        
        # Remove from running jobs
        if job_id in self._running_jobs:
            del self._running_jobs[job_id]
        
        # Return environment to available pool
        environment.status = EnvironmentStatus.IDLE
        self._available_environments.append(environment)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status dictionary or None
        """
        with self._lock:
            job = self._job_map.get(job_id)
            if not job:
                return None
            
            status = "pending"
            if job.id in self._completed_jobs:
                status = "completed"
            elif job.id in self._running_jobs:
                status = "running"
            
            return {
                'id': job.id,
                'status': status,
                'priority': job.priority.value,
                'impact_score': job.impact_score,
                'created_at': job.created_at.isoformat(),
                'scheduled_at': job.scheduled_at.isoformat() if job.scheduled_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'retry_count': job.retry_count,
                'result': job.result.to_dict() if job.result else None
            }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status.
        
        Returns:
            Queue status dictionary
        """
        with self._lock:
            return {
                'pending_jobs': len(self._job_queue),
                'running_jobs': len(self._running_jobs),
                'completed_jobs': len(self._completed_jobs),
                'available_environments': len(self._available_environments),
                'allocated_environments': len(self._allocated_resources)
            }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        with self._lock:
            job = self._job_map.get(job_id)
            if not job:
                return False
            
            # If running, we can't easily cancel (would need test runner support)
            if job_id in self._running_jobs:
                return False
            
            # If pending, remove from queue
            if job in self._job_queue:
                self._job_queue.remove(job)
                heapq.heapify(self._job_queue)
                self._completed_jobs.add(job_id)
                return True
            
            return False
    
    def set_on_job_complete(self, callback: Callable[[TestJob], None]) -> None:
        """Set callback for job completion.
        
        Args:
            callback: Function to call when job completes
        """
        self._on_job_complete = callback
    
    def set_on_job_failed(self, callback: Callable[[TestJob], None]) -> None:
        """Set callback for job failure.
        
        Args:
            callback: Function to call when job fails
        """
        self._on_job_failed = callback
    
    def reschedule_based_on_results(self, results: List[TestResult]) -> None:
        """Dynamically reschedule based on test results.
        
        If critical failures are detected, increase priority of related tests.
        
        Args:
            results: Recent test results
        """
        with self._lock:
            # Find critical failures
            critical_failures = [
                r for r in results 
                if r.status == TestStatus.FAILED and 
                r.failure_info and 
                r.failure_info.kernel_panic
            ]
            
            if not critical_failures:
                return
            
            # Extract affected subsystems from failures
            affected_subsystems = set()
            for result in critical_failures:
                job = self._job_map.get(result.test_id)
                if job:
                    affected_subsystems.add(job.test_case.target_subsystem)
            
            # Increase priority of pending jobs in affected subsystems
            for job in self._job_queue:
                if job.test_case.target_subsystem in affected_subsystems:
                    if job.priority < Priority.HIGH:
                        job.priority = Priority.HIGH
            
            # Re-heapify to reflect new priorities
            heapq.heapify(self._job_queue)
    
    def shutdown(self) -> None:
        """Shutdown the orchestrator and cleanup resources."""
        with self._lock:
            # Cancel all pending jobs
            self._job_queue.clear()
            
            # Wait for running jobs (in a real implementation)
            # For now, just clear the tracking
            self._running_jobs.clear()
            self._allocated_resources.clear()
        
        # Shutdown test runner
        self.test_runner.shutdown()
