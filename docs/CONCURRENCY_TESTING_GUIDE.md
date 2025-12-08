# Concurrency Testing Guide

## Overview

The Agentic AI Testing System includes comprehensive concurrency testing support to detect race conditions, deadlocks, and data races in kernel and BSP code. This guide explains how to use the concurrency testing features to expose concurrency issues through varied thread scheduling and timing.

## Table of Contents

- [Introduction](#introduction)
- [Core Concepts](#core-concepts)
- [Scheduling Strategies](#scheduling-strategies)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Introduction

Concurrency bugs like race conditions and deadlocks are notoriously difficult to detect because they depend on specific timing and thread scheduling. The concurrency testing system addresses this by:

1. **Varying thread schedules** across multiple test runs
2. **Injecting timing delays** to expose race windows
3. **Tracking execution order** to identify patterns
4. **Detecting issues** through multiple execution strategies

## Core Concepts

### Thread Scheduling Variation

The system executes tests multiple times with different thread schedules to increase the probability of exposing race conditions. Each run may have threads starting at different times, creating different interleaving patterns.

### Timing Injection

Random delays are injected before thread execution to vary the timing and expose race windows that might not appear under normal execution.

### Execution Strategies

Four different scheduling strategies provide comprehensive coverage:
- **RANDOM**: Maximum variation for general race detection
- **ROUND_ROBIN**: Predictable ordering for systematic testing
- **PRIORITY_BASED**: Priority-driven for priority inversion testing
- **STRESS**: Maximum contention for stress testing

## Scheduling Strategies

### RANDOM Strategy

Generates random delays for each thread within a configured range.

**Best for:**
- General race condition detection
- Exploring different execution orderings
- Initial testing of concurrent code

**Example:**
```python
from execution.concurrency_testing import ThreadScheduleConfig, SchedulingStrategy

config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.RANDOM,
    num_threads=4,
    execution_runs=20,
    timing_variation_ms=(0, 50),
    seed=42  # For reproducibility
)
```

### ROUND_ROBIN Strategy

Creates sequential delays with predictable ordering.

**Best for:**
- Systematic testing of thread orderings
- Debugging specific race conditions
- Validating fixes

**Example:**
```python
config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.ROUND_ROBIN,
    num_threads=4,
    execution_runs=10,
    timing_variation_ms=(0, 20)
)
```

### PRIORITY_BASED Strategy

Uses thread priorities to determine delays (higher priority = less delay).

**Best for:**
- Testing priority inversion scenarios
- Real-time system testing
- Priority-sensitive code

**Example:**
```python
config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.PRIORITY_BASED,
    num_threads=4,
    execution_runs=15,
    timing_variation_ms=(0, 30),
    thread_priorities=[1, 2, 3, 4]  # Thread 4 has highest priority
)
```

### STRESS Strategy

All threads start simultaneously with zero delays.

**Best for:**
- Maximum contention testing
- Stress testing shared resources
- Finding race conditions under load

**Example:**
```python
config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.STRESS,
    num_threads=8,
    execution_runs=50,
    timing_variation_ms=(0, 0)  # Zero delays
)
```

## Basic Usage

### Simple Concurrency Test

```python
from execution.concurrency_testing import ThreadScheduler, ThreadScheduleConfig, SchedulingStrategy

# Configure the scheduler
config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.RANDOM,
    num_threads=4,
    execution_runs=10,
    timing_variation_ms=(0, 20),
    seed=42
)

scheduler = ThreadScheduler(config)

# Define your test function
def test_concurrent_access(thread_id):
    # Your concurrent code here
    # Access shared resources, perform operations, etc.
    return result

# Run the test with multiple schedules
result = scheduler.run_multiple_schedules(test_concurrent_access)

# Check results
print(f"Total runs: {result.total_runs}")
print(f"Successful: {result.successful_runs}")
print(f"Failed: {result.failed_runs}")
print(f"Unique schedules tested: {result.unique_schedules_tested}")

if result.has_issues:
    print("Issues detected:")
    for issue in result.detected_race_conditions:
        print(f"  - {issue}")
```

### Using the High-Level Runner

```python
from execution.concurrency_testing import ConcurrencyTestRunner

runner = ConcurrencyTestRunner()

def test_function(thread_id):
    # Your test code
    pass

# Test with multiple strategies
results = runner.test_with_variations(
    test_function,
    num_runs=10,
    strategies=[
        SchedulingStrategy.RANDOM,
        SchedulingStrategy.STRESS
    ]
)

for strategy, result in results.items():
    print(f"{strategy}: {result.successful_runs}/{result.total_runs} passed")
```

## Advanced Features

### Race Condition Detection

The system provides a specialized method for race condition detection:

```python
from execution.concurrency_testing import ConcurrencyTestRunner

runner = ConcurrencyTestRunner()

# Shared state for testing
shared_counter = {'value': 0}
lock = threading.Lock()

def increment_counter(thread_id):
    # Intentionally racy code for demonstration
    current = shared_counter['value']
    time.sleep(0.001)  # Simulate work
    shared_counter['value'] = current + 1
    return thread_id

# Validator to check shared state
def validate_state():
    expected = config.num_threads * config.execution_runs
    return shared_counter['value'] == expected

# Run race detection
result = runner.detect_race_conditions(
    increment_counter,
    shared_state_validator=validate_state
)

if result.has_issues:
    print("Race conditions detected!")
    for issue in result.detected_data_races:
        print(f"  - {issue}")
```

### Timing Injection

For fine-grained control over timing:

```python
from execution.concurrency_testing import ConcurrencyTimingInjector

injector = ConcurrencyTimingInjector(
    variation_range_ms=(0, 10),
    seed=42
)

def test_with_timing_injection(thread_id):
    # Inject delay before critical section
    injector.inject_delay("before_critical_section")
    
    # Critical section
    with lock:
        # Access shared resource
        pass
    
    # Inject delay after critical section
    injector.inject_delay("after_critical_section")
    
    return result
```

### Custom Thread Arguments

Pass different arguments to each thread:

```python
# Prepare arguments for each thread
thread_args = [
    (data1, config1),
    (data2, config2),
    (data3, config3),
    (data4, config4)
]

def test_function(data, config):
    # Use thread-specific data and config
    return process(data, config)

# Execute with custom arguments
schedule = scheduler.generate_schedule()
run = scheduler.execute_with_schedule(
    test_function,
    schedule,
    thread_args=thread_args
)
```

## Best Practices

### 1. Start with STRESS Strategy

Begin testing with the STRESS strategy to quickly identify obvious race conditions:

```python
config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.STRESS,
    num_threads=8,
    execution_runs=50
)
```

### 2. Use Reproducible Seeds

Always use seeds for reproducibility during debugging:

```python
config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.RANDOM,
    seed=42  # Same seed = same schedules
)
```

### 3. Increase Runs for Rare Races

For hard-to-reproduce race conditions, increase execution runs:

```python
config = ThreadScheduleConfig(
    execution_runs=100  # More runs = higher probability
)
```

### 4. Validate Shared State

Always provide a validator function to check shared state consistency:

```python
def validate_shared_state():
    # Check invariants
    assert shared_data.is_consistent()
    assert shared_data.checksum_valid()
    return True

result = runner.detect_race_conditions(
    test_function,
    shared_state_validator=validate_shared_state
)
```

### 5. Test Multiple Strategies

Different strategies expose different types of issues:

```python
strategies = [
    SchedulingStrategy.RANDOM,    # General races
    SchedulingStrategy.STRESS,    # High contention
    SchedulingStrategy.ROUND_ROBIN  # Systematic ordering
]

results = runner.test_with_variations(
    test_function,
    strategies=strategies
)
```

### 6. Keep Timing Ranges Reasonable

Use small timing ranges to keep tests fast:

```python
config = ThreadScheduleConfig(
    timing_variation_ms=(0, 20)  # 0-20ms is usually sufficient
)
```

### 7. Monitor Execution Order

Track execution order to understand race patterns:

```python
result = scheduler.run_multiple_schedules(test_function)

for run in result.runs:
    print(f"Run {run.run_id}:")
    print(f"  Execution order: {run.execution_order}")
    print(f"  Timing: {run.timing_variations}")
```

## Examples

### Example 1: Testing a Shared Counter

```python
import threading
from execution.concurrency_testing import ConcurrencyTestRunner

# Shared state
counter = {'value': 0}
lock = threading.Lock()

def increment_with_lock(thread_id):
    """Correctly synchronized increment."""
    with lock:
        counter['value'] += 1
    return thread_id

def increment_without_lock(thread_id):
    """Racy increment (for demonstration)."""
    current = counter['value']
    counter['value'] = current + 1
    return thread_id

runner = ConcurrencyTestRunner()

# Test the correct version
counter['value'] = 0
result = runner.detect_race_conditions(increment_with_lock)
print(f"With lock - Issues: {result.has_issues}")

# Test the racy version
counter['value'] = 0
result = runner.detect_race_conditions(increment_without_lock)
print(f"Without lock - Issues: {result.has_issues}")
```

### Example 2: Testing Lock Ordering

```python
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()

def acquire_a_then_b(thread_id):
    """Acquire locks in order A -> B."""
    with lock_a:
        time.sleep(0.001)
        with lock_b:
            # Critical section
            pass
    return thread_id

def acquire_b_then_a(thread_id):
    """Acquire locks in order B -> A (potential deadlock)."""
    with lock_b:
        time.sleep(0.001)
        with lock_a:
            # Critical section
            pass
    return thread_id

# Test for deadlock potential
config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.STRESS,
    num_threads=4,
    execution_runs=20
)

scheduler = ThreadScheduler(config)

# This might deadlock!
try:
    result = scheduler.run_multiple_schedules(acquire_b_then_a)
    print(f"Completed {result.successful_runs} runs")
except Exception as e:
    print(f"Deadlock or error detected: {e}")
```

### Example 3: Testing Producer-Consumer

```python
import queue
import threading

work_queue = queue.Queue()
results = []
results_lock = threading.Lock()

def producer(thread_id):
    """Produce work items."""
    for i in range(10):
        work_queue.put((thread_id, i))
    return thread_id

def consumer(thread_id):
    """Consume work items."""
    while not work_queue.empty():
        try:
            item = work_queue.get(timeout=0.1)
            with results_lock:
                results.append(item)
            work_queue.task_done()
        except queue.Empty:
            break
    return thread_id

# Test producer-consumer pattern
config = ThreadScheduleConfig(
    strategy=SchedulingStrategy.RANDOM,
    num_threads=6,  # 3 producers, 3 consumers
    execution_runs=10
)

scheduler = ThreadScheduler(config)

# Run test
result = scheduler.run_multiple_schedules(
    lambda tid: producer(tid) if tid < 3 else consumer(tid)
)

print(f"Processed {len(results)} items")
print(f"Queue empty: {work_queue.empty()}")
```

## Troubleshooting

### Tests Timing Out

If tests are timing out, reduce the timing variation range:

```python
config = ThreadScheduleConfig(
    timing_variation_ms=(0, 5)  # Reduce from (0, 50)
)
```

### Not Finding Race Conditions

If known race conditions aren't being detected:

1. Increase execution runs:
   ```python
   config.execution_runs = 100
   ```

2. Use STRESS strategy:
   ```python
   config.strategy = SchedulingStrategy.STRESS
   ```

3. Add timing injection in critical sections:
   ```python
   injector.inject_delay("before_critical_section")
   ```

### Too Many False Positives

If getting false positives:

1. Verify your test function is thread-safe
2. Check that shared state validation is correct
3. Ensure proper cleanup between runs

### Reproducibility Issues

To reproduce a specific failure:

1. Use the same seed:
   ```python
   config.seed = 42
   ```

2. Use the same strategy and parameters
3. Check the execution order from the failing run

## Integration with Test Suite

### Adding to pytest

```python
# tests/concurrency/test_my_feature.py
import pytest
from execution.concurrency_testing import ConcurrencyTestRunner

def test_concurrent_feature():
    """Test feature under concurrent access."""
    runner = ConcurrencyTestRunner()
    
    result = runner.detect_race_conditions(my_concurrent_function)
    
    assert result.successful_runs > 0, "No successful runs"
    assert not result.has_issues, f"Race conditions detected: {result.detected_race_conditions}"
```

### Property-Based Testing

```python
from hypothesis import given, strategies as st
from execution.concurrency_testing import ThreadScheduleConfig, SchedulingStrategy

@given(
    num_threads=st.integers(min_value=2, max_value=8),
    strategy=st.sampled_from(list(SchedulingStrategy))
)
def test_property_no_races(num_threads, strategy):
    """Property: No races should occur regardless of scheduling."""
    config = ThreadScheduleConfig(
        strategy=strategy,
        num_threads=num_threads,
        execution_runs=10
    )
    
    scheduler = ThreadScheduler(config)
    result = scheduler.run_multiple_schedules(my_function)
    
    assert result.successful_runs == result.total_runs
```

## Performance Considerations

### Test Duration

Concurrency tests can be time-consuming. To optimize:

1. **Reduce timing ranges**: Use smaller delays (0-10ms instead of 0-100ms)
2. **Limit execution runs**: Start with 10-20 runs, increase if needed
3. **Use appropriate strategies**: STRESS is fastest, RANDOM is slowest
4. **Parallelize tests**: Run different test cases in parallel

### Resource Usage

Monitor resource usage during testing:

```python
result = scheduler.run_multiple_schedules(test_function)

print(f"Total execution time: {sum(r.execution_time for r in result.runs):.2f}s")
print(f"Average per run: {sum(r.execution_time for r in result.runs) / len(result.runs):.2f}s")
```

## Conclusion

The concurrency testing system provides powerful tools for detecting race conditions, deadlocks, and data races. By varying thread scheduling and timing across multiple runs, it significantly increases the probability of exposing concurrency bugs that might otherwise go undetected.

For more information, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [API Reference](../execution/concurrency_testing.py)
- [Property-Based Tests](../tests/property/test_concurrency_testing_variation.py)
- [Implementation Summary](../TASK13_CONCURRENCY_TESTING_SUMMARY.md)
