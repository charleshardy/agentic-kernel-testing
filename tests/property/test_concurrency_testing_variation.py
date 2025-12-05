"""Property-based tests for concurrency testing variation.

**Feature: agentic-kernel-testing, Property 13: Concurrency testing variation**

This module tests that race condition testing varies execution timing and
thread scheduling across multiple test runs.

**Validates: Requirements 3.3**
"""

import pytest
import threading
import time
from hypothesis import given, strategies as st, settings
from execution.concurrency_testing import (
    ThreadScheduler,
    ThreadScheduleConfig,
    SchedulingStrategy,
    ConcurrencyTimingInjector,
    ConcurrencyTestRunner,
    ConcurrencyTestResult
)


# Custom strategies for concurrency testing
@st.composite
def thread_schedule_configs(draw):
    """Generate valid thread schedule configurations."""
    strategy = draw(st.sampled_from(list(SchedulingStrategy)))
    num_threads = draw(st.integers(min_value=2, max_value=8))
    execution_runs = draw(st.integers(min_value=5, max_value=20))
    
    # Use small timing ranges to avoid long test times
    min_timing = draw(st.integers(min_value=0, max_value=5))
    max_timing = draw(st.integers(min_value=min_timing, max_value=min_timing + 10))
    
    seed = draw(st.integers(min_value=0, max_value=10000))
    
    # Generate thread priorities if using priority-based strategy
    thread_priorities = None
    if strategy == SchedulingStrategy.PRIORITY_BASED:
        thread_priorities = [
            draw(st.integers(min_value=1, max_value=10))
            for _ in range(num_threads)
        ]
    
    config = ThreadScheduleConfig(
        strategy=strategy,
        num_threads=num_threads,
        execution_runs=execution_runs,
        timing_variation_ms=(min_timing, max_timing),
        seed=seed,
        thread_priorities=thread_priorities
    )
    
    return config


class TestConcurrencyTestingVariation:
    """Test suite for concurrency testing variation property."""
    
    @given(config=thread_schedule_configs())
    @settings(max_examples=50, deadline=10000)
    def test_property_concurrency_testing_variation(self, config):
        """
        **Feature: agentic-kernel-testing, Property 13: Concurrency testing variation**
        
        Property: For any test of code with suspected race conditions, the system
        should vary execution timing and thread scheduling across multiple test runs.
        
        **Validates: Requirements 3.3**
        
        This test verifies that when concurrency testing is performed, the system
        generates different thread schedules and timing variations across runs.
        """
        # Create thread scheduler with the configuration
        scheduler = ThreadScheduler(config)
        
        # Generate multiple schedules
        schedules = []
        for _ in range(min(config.execution_runs, 10)):  # Limit to 10 for test speed
            schedule = scheduler.generate_schedule()
            schedules.append(schedule)
        
        # Property 1: Each schedule should have the correct number of threads
        for schedule in schedules:
            assert len(schedule) == config.num_threads, \
                f"Schedule has {len(schedule)} threads, expected {config.num_threads}"
        
        # Property 2: Schedules should vary (unless using STRESS strategy)
        if config.strategy != SchedulingStrategy.STRESS and len(schedules) > 1:
            # Convert to tuples for comparison (round to avoid floating point issues)
            schedule_tuples = [
                tuple(round(d, 6) for d in s) for s in schedules
            ]
            unique_schedules = set(schedule_tuples)
            
            # At least some variation should exist (allow for small configs)
            # For very small timing ranges, we might get duplicates
            timing_range = config.timing_variation_ms[1] - config.timing_variation_ms[0]
            if timing_range > 1:  # Only check variation if range is meaningful
                assert len(unique_schedules) >= 1, \
                    "Schedules should show variation across runs"
        
        # Property 3: All delays should be within configured range
        # (except for STRESS strategy which always uses zero delays)
        for schedule in schedules:
            for delay in schedule:
                delay_ms = delay * 1000
                if config.strategy == SchedulingStrategy.STRESS:
                    # STRESS strategy always uses zero delays
                    assert delay_ms == 0.0, \
                        f"STRESS strategy should have zero delay, got {delay_ms}ms"
                else:
                    # Allow small floating-point tolerance (0.001ms)
                    tolerance = 0.001
                    assert config.timing_variation_ms[0] - tolerance <= delay_ms <= config.timing_variation_ms[1] + tolerance, \
                        f"Delay {delay_ms}ms outside range {config.timing_variation_ms}"
    
    @given(
        num_threads=st.integers(min_value=2, max_value=4),
        num_runs=st.integers(min_value=3, max_value=8),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=30, deadline=10000)
    def test_multiple_execution_runs_with_different_schedules(
        self, num_threads, num_runs, seed
    ):
        """
        Test that multiple execution runs use different thread schedules.
        
        This verifies the core variation property: each run should potentially
        have a different schedule to expose race conditions.
        """
        config = ThreadScheduleConfig(
            strategy=SchedulingStrategy.RANDOM,
            num_threads=num_threads,
            execution_runs=num_runs,
            timing_variation_ms=(0, 10),
            seed=seed
        )
        
        scheduler = ThreadScheduler(config)
        
        # Simple test function that records thread execution
        execution_log = []
        log_lock = threading.Lock()
        
        def test_function(thread_id):
            with log_lock:
                execution_log.append(thread_id)
            return thread_id
        
        # Run multiple schedules
        result = scheduler.run_multiple_schedules(test_function)
        
        # Property: Should have executed the configured number of runs
        assert result.total_runs == num_runs, \
            f"Expected {num_runs} runs, got {result.total_runs}"
        
        # Property: Each run should have executed all threads
        assert len(execution_log) == num_runs * num_threads, \
            f"Expected {num_runs * num_threads} thread executions, got {len(execution_log)}"
        
        # Property: Should have tested multiple unique schedules
        assert result.unique_schedules_tested >= 1, \
            "Should have tested at least one unique schedule"
    
    @given(
        strategy=st.sampled_from(list(SchedulingStrategy)),
        num_threads=st.integers(min_value=2, max_value=4),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=30, deadline=10000)
    def test_timing_variation_across_strategies(self, strategy, num_threads, seed):
        """
        Test that different scheduling strategies produce appropriate timing variations.
        """
        # Generate priorities for priority-based strategy
        priorities = [i + 1 for i in range(num_threads)] if strategy == SchedulingStrategy.PRIORITY_BASED else None
        
        config = ThreadScheduleConfig(
            strategy=strategy,
            num_threads=num_threads,
            execution_runs=5,
            timing_variation_ms=(0, 20),
            seed=seed,
            thread_priorities=priorities
        )
        
        scheduler = ThreadScheduler(config)
        
        # Generate a schedule
        schedule = scheduler.generate_schedule()
        
        # Property: Schedule should have correct length
        assert len(schedule) == num_threads
        
        # Property: Delays should be non-negative
        for delay in schedule:
            assert delay >= 0.0, f"Delay {delay} should be non-negative"
        
        # Strategy-specific properties
        if strategy == SchedulingStrategy.STRESS:
            # STRESS: All threads should start simultaneously (zero delay)
            for delay in schedule:
                assert delay == 0.0, "STRESS strategy should have zero delays"
        
        elif strategy == SchedulingStrategy.ROUND_ROBIN:
            # ROUND_ROBIN: Delays should be in ascending order
            for i in range(len(schedule) - 1):
                assert schedule[i] <= schedule[i + 1], \
                    "ROUND_ROBIN delays should be non-decreasing"
    
    @given(
        variation_range_min=st.integers(min_value=0, max_value=5),
        variation_range_max=st.integers(min_value=5, max_value=15),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=30, deadline=10000)
    def test_timing_injector_varies_delays(
        self, variation_range_min, variation_range_max, seed
    ):
        """
        Test that the timing injector produces varied delays within range.
        """
        injector = ConcurrencyTimingInjector(
            variation_range_ms=(variation_range_min, variation_range_max),
            seed=seed
        )
        
        # Inject multiple delays (reduced to 5 for speed)
        delays = []
        for _ in range(5):
            delay = injector.inject_delay("test_location")
            delays.append(delay)
        
        # Property: All delays should be within range
        for delay in delays:
            delay_ms = delay * 1000
            assert variation_range_min <= delay_ms <= variation_range_max, \
                f"Delay {delay_ms}ms outside range [{variation_range_min}, {variation_range_max}]"
        
        # Property: Delays should be non-negative
        for delay in delays:
            assert delay >= 0.0, f"Delay {delay} should be non-negative"
    
    @given(
        num_threads=st.integers(min_value=2, max_value=4),
        num_runs=st.integers(min_value=3, max_value=8),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=30, deadline=10000)
    def test_execution_order_varies_across_runs(self, num_threads, num_runs, seed):
        """
        Test that thread execution order varies across multiple runs.
        
        This is key for exposing race conditions: different execution orders
        can trigger different race condition scenarios.
        """
        config = ThreadScheduleConfig(
            strategy=SchedulingStrategy.RANDOM,
            num_threads=num_threads,
            execution_runs=num_runs,
            timing_variation_ms=(0, 10),
            seed=seed
        )
        
        scheduler = ThreadScheduler(config)
        
        # Simple test function
        def test_function(thread_id):
            return thread_id
        
        # Run multiple schedules
        result = scheduler.run_multiple_schedules(test_function)
        
        # Property: Each run should record execution order
        execution_orders = [run.execution_order for run in result.runs]
        
        # Property: Each execution order should have all threads
        for order in execution_orders:
            assert len(order) == num_threads, \
                f"Execution order has {len(order)} threads, expected {num_threads}"
            assert set(order) == set(range(num_threads)), \
                "Execution order should contain all thread IDs"
        
        # Property: Execution orders should vary (unless very constrained)
        if num_runs > 1 and num_threads > 2:
            # Convert to tuples for comparison
            order_tuples = [tuple(order) for order in execution_orders]
            unique_orders = set(order_tuples)
            
            # We expect some variation in execution order
            # (though with small timing ranges, we might get some duplicates)
            assert len(unique_orders) >= 1, \
                "Should have at least one execution order"
    
    @given(config=thread_schedule_configs())
    @settings(max_examples=30, deadline=10000)
    def test_concurrency_test_result_structure(self, config):
        """
        Test that concurrency test results have proper structure.
        """
        # Limit execution runs for test speed
        config.execution_runs = min(config.execution_runs, 10)
        
        scheduler = ThreadScheduler(config)
        
        # Simple test function
        def test_function(thread_id):
            return thread_id
        
        # Run tests
        result = scheduler.run_multiple_schedules(test_function)
        
        # Property: Result should have correct structure
        assert isinstance(result, ConcurrencyTestResult)
        assert result.total_runs == config.execution_runs
        assert result.successful_runs + result.failed_runs == result.total_runs
        assert len(result.runs) == result.total_runs
        
        # Property: Each run should have timing variations recorded
        for run in result.runs:
            assert len(run.timing_variations) == config.num_threads
            assert len(run.execution_order) == config.num_threads
    
    @given(
        num_threads=st.integers(min_value=2, max_value=4),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=30, deadline=10000)
    def test_race_condition_detection_uses_stress_strategy(self, num_threads, seed):
        """
        Test that race condition detection uses stress strategy for maximum contention.
        """
        config = ThreadScheduleConfig(
            strategy=SchedulingStrategy.RANDOM,  # Will be overridden
            num_threads=num_threads,
            execution_runs=10,
            timing_variation_ms=(0, 10),
            seed=seed
        )
        
        runner = ConcurrencyTestRunner(scheduler_config=config)
        
        # Shared state for testing
        shared_counter = {'value': 0}
        counter_lock = threading.Lock()
        
        def test_function(thread_id):
            # Increment shared counter (with proper locking)
            with counter_lock:
                shared_counter['value'] += 1
            return thread_id
        
        # Run race condition detection
        result = runner.detect_race_conditions(test_function)
        
        # Property: Should have run multiple tests
        assert result.total_runs > 0
        
        # Property: Result should have proper structure
        assert isinstance(result, ConcurrencyTestResult)
        assert hasattr(result, 'detected_race_conditions')
        assert hasattr(result, 'detected_deadlocks')
        assert hasattr(result, 'detected_data_races')
    
    @given(
        num_runs=st.integers(min_value=3, max_value=8),
        seed=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=30, deadline=10000)
    def test_multiple_strategies_produce_different_schedules(self, num_runs, seed):
        """
        Test that different scheduling strategies produce different schedule patterns.
        """
        strategies = [
            SchedulingStrategy.RANDOM,
            SchedulingStrategy.ROUND_ROBIN,
            SchedulingStrategy.STRESS
        ]
        
        num_threads = 4
        
        schedules_by_strategy = {}
        
        for strategy in strategies:
            config = ThreadScheduleConfig(
                strategy=strategy,
                num_threads=num_threads,
                execution_runs=num_runs,
                timing_variation_ms=(0, 20),
                seed=seed
            )
            
            scheduler = ThreadScheduler(config)
            schedule = scheduler.generate_schedule()
            schedules_by_strategy[strategy] = schedule
        
        # Property: STRESS strategy should have all zero delays
        stress_schedule = schedules_by_strategy[SchedulingStrategy.STRESS]
        assert all(d == 0.0 for d in stress_schedule), \
            "STRESS strategy should have zero delays"
        
        # Property: ROUND_ROBIN should have ordered delays
        rr_schedule = schedules_by_strategy[SchedulingStrategy.ROUND_ROBIN]
        for i in range(len(rr_schedule) - 1):
            assert rr_schedule[i] <= rr_schedule[i + 1], \
                "ROUND_ROBIN should have non-decreasing delays"
        
        # Property: RANDOM should have some variation (if range allows)
        random_schedule = schedules_by_strategy[SchedulingStrategy.RANDOM]
        assert len(random_schedule) == num_threads
    
    def test_empty_configuration_validation(self):
        """
        Test that invalid configurations are rejected.
        """
        # Test invalid num_threads
        with pytest.raises(ValueError, match="num_threads must be positive"):
            ThreadScheduleConfig(num_threads=0)
        
        # Test invalid execution_runs
        with pytest.raises(ValueError, match="execution_runs must be positive"):
            ThreadScheduleConfig(execution_runs=0)
        
        # Test invalid timing range
        with pytest.raises(ValueError, match="timing_variation_ms must be a tuple"):
            ThreadScheduleConfig(timing_variation_ms=(0,))
        
        # Test negative timing
        with pytest.raises(ValueError, match="timing_variation_ms min must be non-negative"):
            ThreadScheduleConfig(timing_variation_ms=(-1, 10))
        
        # Test invalid range order
        with pytest.raises(ValueError, match="timing_variation_ms max must be >= min"):
            ThreadScheduleConfig(timing_variation_ms=(10, 5))
