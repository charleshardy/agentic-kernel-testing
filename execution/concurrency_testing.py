"""Concurrency testing support for race condition detection.

This module provides functionality for:
- Thread scheduling variation system
- Timing variation injector for race condition detection
- Multiple execution runs with different schedules
"""

import random
import time
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import uuid


class SchedulingStrategy(str, Enum):
    """Thread scheduling strategies for concurrency testing."""
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    PRIORITY_BASED = "priority_based"
    STRESS = "stress"  # Maximum contention


@dataclass
class ThreadScheduleConfig:
    """Configuration for thread scheduling variation."""
    strategy: SchedulingStrategy = SchedulingStrategy.RANDOM
    num_threads: int = 4
    execution_runs: int = 10
    timing_variation_ms: tuple = (0, 50)
    seed: Optional[int] = None
    thread_priorities: Optional[List[int]] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if self.num_threads <= 0:
            raise ValueError("num_threads must be positive")
        if self.execution_runs <= 0:
            raise ValueError("execution_runs must be positive")
        if len(self.timing_variation_ms) != 2:
            raise ValueError("timing_variation_ms must be a tuple of (min, max)")
        if self.timing_variation_ms[0] < 0:
            raise ValueError("timing_variation_ms min must be non-negative")
        if self.timing_variation_ms[1] < self.timing_variation_ms[0]:
            raise ValueError("timing_variation_ms max must be >= min")


@dataclass
class ConcurrencyTestRun:
    """Record of a single concurrency test run."""
    run_id: str
    strategy: SchedulingStrategy
    num_threads: int
    timing_variations: List[float] = field(default_factory=list)
    execution_order: List[int] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    execution_time: float = 0.0
    detected_issues: List[str] = field(default_factory=list)


@dataclass
class ConcurrencyTestResult:
    """Aggregated results from multiple concurrency test runs."""
    total_runs: int
    successful_runs: int
    failed_runs: int
    detected_race_conditions: List[str] = field(default_factory=list)
    detected_deadlocks: List[str] = field(default_factory=list)
    detected_data_races: List[str] = field(default_factory=list)
    runs: List[ConcurrencyTestRun] = field(default_factory=list)
    unique_schedules_tested: int = 0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_runs == 0:
            return 0.0
        return self.failed_runs / self.total_runs
    
    @property
    def has_issues(self) -> bool:
        """Check if any issues were detected."""
        return bool(
            self.detected_race_conditions or 
            self.detected_deadlocks or 
            self.detected_data_races
        )


class ThreadScheduler:
    """System for varying thread scheduling to expose race conditions."""
    
    def __init__(self, config: Optional[ThreadScheduleConfig] = None):
        """Initialize thread scheduler.
        
        Args:
            config: Thread scheduling configuration
        """
        self.config = config or ThreadScheduleConfig()
        self.rng = random.Random(self.config.seed)
        self._lock = threading.Lock()
        self.execution_count = 0
    
    def generate_schedule(self) -> List[float]:
        """Generate timing delays for thread scheduling.
        
        Returns:
            List of delays (in seconds) for each thread
        """
        delays = []
        
        if self.config.strategy == SchedulingStrategy.RANDOM:
            # Random delays for each thread
            for _ in range(self.config.num_threads):
                delay_ms = self.rng.uniform(
                    self.config.timing_variation_ms[0],
                    self.config.timing_variation_ms[1]
                )
                delays.append(delay_ms / 1000.0)
        
        elif self.config.strategy == SchedulingStrategy.ROUND_ROBIN:
            # Sequential delays with small increments
            base_delay = self.config.timing_variation_ms[0] / 1000.0
            increment = (
                (self.config.timing_variation_ms[1] - self.config.timing_variation_ms[0]) 
                / max(1, self.config.num_threads - 1)
            ) / 1000.0
            
            for i in range(self.config.num_threads):
                delays.append(base_delay + i * increment)
        
        elif self.config.strategy == SchedulingStrategy.PRIORITY_BASED:
            # Use thread priorities if provided
            if self.config.thread_priorities:
                # Higher priority = less delay
                max_priority = max(self.config.thread_priorities)
                for priority in self.config.thread_priorities[:self.config.num_threads]:
                    # Invert priority to delay
                    normalized = 1.0 - (priority / max_priority)
                    delay_ms = (
                        self.config.timing_variation_ms[0] + 
                        normalized * (
                            self.config.timing_variation_ms[1] - 
                            self.config.timing_variation_ms[0]
                        )
                    )
                    delays.append(delay_ms / 1000.0)
            else:
                # Fall back to random delays if no priorities provided
                for _ in range(self.config.num_threads):
                    delay_ms = self.rng.uniform(
                        self.config.timing_variation_ms[0],
                        self.config.timing_variation_ms[1]
                    )
                    delays.append(delay_ms / 1000.0)
        
        elif self.config.strategy == SchedulingStrategy.STRESS:
            # All threads start simultaneously (zero delay)
            delays = [0.0] * self.config.num_threads
        
        return delays
    
    def execute_with_schedule(
        self,
        test_function: Callable,
        schedule: List[float],
        thread_args: Optional[List[tuple]] = None
    ) -> ConcurrencyTestRun:
        """Execute test function with specified thread schedule.
        
        Args:
            test_function: Function to execute in each thread
            schedule: List of delays for each thread
            thread_args: Optional arguments for each thread
            
        Returns:
            Concurrency test run result
        """
        run_id = str(uuid.uuid4())
        start_time = time.time()
        
        threads = []
        results = []
        errors = []
        execution_order = []
        order_lock = threading.Lock()
        
        def thread_wrapper(thread_id: int, delay: float, args: tuple):
            """Wrapper for thread execution with delay."""
            try:
                # Apply scheduling delay
                time.sleep(delay)
                
                # Record execution order
                with order_lock:
                    execution_order.append(thread_id)
                
                # Execute test function
                if args:
                    result = test_function(*args)
                else:
                    result = test_function(thread_id)
                
                results.append((thread_id, result))
                
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create and start threads
        for i, delay in enumerate(schedule):
            args = thread_args[i] if thread_args and i < len(thread_args) else ()
            thread = threading.Thread(
                target=thread_wrapper,
                args=(i, delay, args)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        execution_time = time.time() - start_time
        
        # Analyze results for issues
        detected_issues = []
        if errors:
            detected_issues.extend([f"Thread {tid}: {err}" for tid, err in errors])
        
        # Create run record
        run = ConcurrencyTestRun(
            run_id=run_id,
            strategy=self.config.strategy,
            num_threads=len(schedule),
            timing_variations=schedule,
            execution_order=execution_order,
            success=len(errors) == 0,
            error_message="; ".join([err for _, err in errors]) if errors else None,
            execution_time=execution_time,
            detected_issues=detected_issues
        )
        
        with self._lock:
            self.execution_count += 1
        
        return run
    
    def run_multiple_schedules(
        self,
        test_function: Callable,
        thread_args: Optional[List[tuple]] = None
    ) -> ConcurrencyTestResult:
        """Run test with multiple different schedules.
        
        Args:
            test_function: Function to execute in each thread
            thread_args: Optional arguments for each thread
            
        Returns:
            Aggregated concurrency test results
        """
        runs = []
        unique_schedules = set()
        
        for _ in range(self.config.execution_runs):
            schedule = self.generate_schedule()
            
            # Track unique schedules (rounded to avoid floating point issues)
            schedule_key = tuple(round(d, 6) for d in schedule)
            unique_schedules.add(schedule_key)
            
            run = self.execute_with_schedule(test_function, schedule, thread_args)
            runs.append(run)
        
        # Aggregate results
        successful = sum(1 for r in runs if r.success)
        failed = sum(1 for r in runs if not r.success)
        
        # Categorize detected issues
        race_conditions = []
        deadlocks = []
        data_races = []
        
        for run in runs:
            for issue in run.detected_issues:
                issue_lower = issue.lower()
                if "race" in issue_lower and "data" in issue_lower:
                    data_races.append(issue)
                elif "race" in issue_lower:
                    race_conditions.append(issue)
                elif "deadlock" in issue_lower or "lock" in issue_lower:
                    deadlocks.append(issue)
        
        result = ConcurrencyTestResult(
            total_runs=len(runs),
            successful_runs=successful,
            failed_runs=failed,
            detected_race_conditions=race_conditions,
            detected_deadlocks=deadlocks,
            detected_data_races=data_races,
            runs=runs,
            unique_schedules_tested=len(unique_schedules)
        )
        
        return result


class ConcurrencyTimingInjector:
    """Injector for timing variations to expose race conditions."""
    
    def __init__(
        self,
        variation_range_ms: tuple = (0, 100),
        seed: Optional[int] = None
    ):
        """Initialize timing injector for concurrency testing.
        
        Args:
            variation_range_ms: Tuple of (min_ms, max_ms) for delay range
            seed: Random seed for reproducibility
        """
        if len(variation_range_ms) != 2:
            raise ValueError("variation_range_ms must be a tuple of (min, max)")
        if variation_range_ms[0] < 0:
            raise ValueError("variation_range_ms min must be non-negative")
        if variation_range_ms[1] < variation_range_ms[0]:
            raise ValueError("variation_range_ms max must be >= min")
        
        self.variation_range_ms = variation_range_ms
        self.rng = random.Random(seed)
        self.injection_count = 0
        self._lock = threading.Lock()
    
    def inject_delay(self, location: str = "unknown") -> float:
        """Inject a random timing delay.
        
        Args:
            location: Location identifier for the injection
            
        Returns:
            Delay in seconds that was injected
        """
        delay_ms = self.rng.uniform(
            self.variation_range_ms[0],
            self.variation_range_ms[1]
        )
        delay_seconds = delay_ms / 1000.0
        
        with self._lock:
            self.injection_count += 1
        
        # Actually inject the delay
        time.sleep(delay_seconds)
        
        return delay_seconds
    
    def inject_at_critical_section(
        self,
        before: bool = True,
        after: bool = False
    ) -> float:
        """Inject delay before/after critical section.
        
        Args:
            before: Inject delay before critical section
            after: Inject delay after critical section
            
        Returns:
            Total delay injected in seconds
        """
        total_delay = 0.0
        
        if before:
            total_delay += self.inject_delay("before_critical_section")
        
        # Critical section would execute here
        
        if after:
            total_delay += self.inject_delay("after_critical_section")
        
        return total_delay
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get injection statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "injection_count": self.injection_count,
                "variation_range_ms": self.variation_range_ms
            }


class ConcurrencyTestRunner:
    """High-level runner for concurrency testing."""
    
    def __init__(
        self,
        scheduler_config: Optional[ThreadScheduleConfig] = None,
        timing_injector: Optional[ConcurrencyTimingInjector] = None
    ):
        """Initialize concurrency test runner.
        
        Args:
            scheduler_config: Thread scheduler configuration
            timing_injector: Optional timing injector
        """
        self.scheduler = ThreadScheduler(scheduler_config)
        self.timing_injector = timing_injector or ConcurrencyTimingInjector()
    
    def test_with_variations(
        self,
        test_function: Callable,
        num_runs: int = 10,
        strategies: Optional[List[SchedulingStrategy]] = None
    ) -> Dict[SchedulingStrategy, ConcurrencyTestResult]:
        """Test function with multiple scheduling strategies.
        
        Args:
            test_function: Function to test
            num_runs: Number of runs per strategy
            strategies: List of strategies to test (default: all)
            
        Returns:
            Dictionary mapping strategy to results
        """
        if strategies is None:
            strategies = list(SchedulingStrategy)
        
        results = {}
        
        for strategy in strategies:
            # Update scheduler config
            self.scheduler.config.strategy = strategy
            self.scheduler.config.execution_runs = num_runs
            
            # Run tests
            result = self.scheduler.run_multiple_schedules(test_function)
            results[strategy] = result
        
        return results
    
    def detect_race_conditions(
        self,
        test_function: Callable,
        shared_state_validator: Optional[Callable] = None
    ) -> ConcurrencyTestResult:
        """Run tests specifically to detect race conditions.
        
        Args:
            test_function: Function to test
            shared_state_validator: Optional function to validate shared state
            
        Returns:
            Concurrency test results
        """
        # Use stress strategy for maximum contention
        self.scheduler.config.strategy = SchedulingStrategy.STRESS
        self.scheduler.config.execution_runs = 50  # More runs for race detection
        
        result = self.scheduler.run_multiple_schedules(test_function)
        
        # If validator provided, check shared state
        if shared_state_validator:
            try:
                validation_result = shared_state_validator()
                if not validation_result:
                    result.detected_data_races.append(
                        "Shared state validation failed after concurrent execution"
                    )
            except Exception as e:
                result.detected_data_races.append(
                    f"Shared state validation error: {str(e)}"
                )
        
        return result
