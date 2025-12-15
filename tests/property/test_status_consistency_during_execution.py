"""Property-based tests for status consistency during execution.

**Feature: test-execution-orchestrator, Property 3: Status consistency during execution**
**Validates: Requirements 1.4, 1.5**

Property 3: Status consistency during execution
For any test that transitions to "running" status, the active test count should increase by exactly one, 
and when it completes, the count should decrease by exactly one.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List, Set
import threading
import time

from orchestrator.status_tracker import StatusTracker, TestExecutionStatus


# Custom strategies for generating test data
@st.composite
def gen_test_id(draw):
    """Generate a random test ID."""
    return draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))


@st.composite
def gen_valid_status(draw):
    """Generate a valid test status."""
    return draw(st.sampled_from(['queued', 'running', 'completed', 'failed', 'timeout', 'error']))


@st.composite
def gen_completion_status(draw):
    """Generate a completion status (non-running, non-queued)."""
    return draw(st.sampled_from(['completed', 'failed', 'timeout', 'error']))


@given(st.lists(gen_test_id(), min_size=1, max_size=20, unique=True))
@settings(max_examples=100, deadline=None)
def test_running_status_increments_active_count(test_ids: List[str]):
    """
    Property: For any test that transitions to "running" status, the active test count 
    should increase by exactly one.
    
    **Feature: test-execution-orchestrator, Property 3: Status consistency during execution**
    **Validates: Requirements 1.4**
    """
    tracker = StatusTracker()
    tracker.start()
    
    try:
        initial_count = tracker.get_active_test_count()
        
        # Transition each test to running status
        for i, test_id in enumerate(test_ids):
            # First set to queued (if not already)
            tracker.update_test_status(test_id, 'queued')
            
            # Get count before transition
            count_before = tracker.get_active_test_count()
            
            # Transition to running
            success = tracker.update_test_status(test_id, 'running')
            assert success, f"Failed to update status for test {test_id}"
            
            # Get count after transition
            count_after = tracker.get_active_test_count()
            
            # Verify count increased by exactly one
            assert count_after == count_before + 1, \
                f"Active count should increase by 1 when test {test_id} transitions to running. " \
                f"Before: {count_before}, After: {count_after}"
            
            # Verify total active count is correct
            expected_total = initial_count + i + 1
            assert count_after == expected_total, \
                f"Total active count should be {expected_total}, got {count_after}"
    
    finally:
        tracker.stop()


@given(st.lists(gen_test_id(), min_size=1, max_size=20, unique=True))
@settings(max_examples=100, deadline=None)
def test_completion_status_decrements_active_count(test_ids: List[str]):
    """
    Property: For any test that completes (transitions from running to any completion status), 
    the active test count should decrease by exactly one.
    
    **Feature: test-execution-orchestrator, Property 3: Status consistency during execution**
    **Validates: Requirements 1.5**
    """
    tracker = StatusTracker()
    tracker.start()
    
    try:
        # First, set all tests to running status
        for test_id in test_ids:
            tracker.update_test_status(test_id, 'queued')
            tracker.update_test_status(test_id, 'running')
        
        initial_active_count = tracker.get_active_test_count()
        assert initial_active_count == len(test_ids), \
            f"Expected {len(test_ids)} active tests, got {initial_active_count}"
        
        # Complete each test with different completion statuses
        completion_statuses = ['completed', 'failed', 'timeout', 'error']
        
        for i, test_id in enumerate(test_ids):
            # Get count before completion
            count_before = tracker.get_active_test_count()
            
            # Complete the test
            completion_status = completion_statuses[i % len(completion_statuses)]
            success = tracker.update_test_status(test_id, completion_status)
            assert success, f"Failed to complete test {test_id} with status {completion_status}"
            
            # Get count after completion
            count_after = tracker.get_active_test_count()
            
            # Verify count decreased by exactly one
            assert count_after == count_before - 1, \
                f"Active count should decrease by 1 when test {test_id} completes with {completion_status}. " \
                f"Before: {count_before}, After: {count_after}"
            
            # Verify total active count is correct
            expected_total = initial_active_count - i - 1
            assert count_after == expected_total, \
                f"Total active count should be {expected_total}, got {count_after}"
    
    finally:
        tracker.stop()


@given(
    st.lists(gen_test_id(), min_size=2, max_size=15, unique=True),
    st.lists(gen_completion_status(), min_size=2, max_size=15)
)
@settings(max_examples=100, deadline=None)
def test_mixed_status_transitions_maintain_consistency(
    test_ids: List[str], 
    completion_statuses: List[str]
):
    """
    Property: For any sequence of mixed status transitions (some tests starting, some completing),
    the active test count should remain consistent with the actual number of running tests.
    
    **Feature: test-execution-orchestrator, Property 3: Status consistency during execution**
    **Validates: Requirements 1.4, 1.5**
    """
    # Ensure we have enough completion statuses
    min_len = min(len(test_ids), len(completion_statuses))
    assume(min_len >= 2)
    
    test_ids = test_ids[:min_len]
    completion_statuses = completion_statuses[:min_len]
    
    tracker = StatusTracker()
    tracker.start()
    
    try:
        running_tests: Set[str] = set()
        
        # Mix of starting and completing tests
        for i, test_id in enumerate(test_ids):
            # Start some tests
            if i < len(test_ids) // 2:
                tracker.update_test_status(test_id, 'queued')
                tracker.update_test_status(test_id, 'running')
                running_tests.add(test_id)
                
                # Verify count matches our tracking
                expected_count = len(running_tests)
                actual_count = tracker.get_active_test_count()
                assert actual_count == expected_count, \
                    f"After starting test {test_id}: expected {expected_count} active, got {actual_count}"
        
        # Complete some tests while starting others
        for i in range(len(test_ids) // 2, len(test_ids)):
            test_id = test_ids[i]
            
            # Complete a previously running test if any exist
            if running_tests and i % 2 == 0:
                completed_test = running_tests.pop()
                completion_status = completion_statuses[i % len(completion_statuses)]
                tracker.update_test_status(completed_test, completion_status)
            
            # Start a new test
            tracker.update_test_status(test_id, 'queued')
            tracker.update_test_status(test_id, 'running')
            running_tests.add(test_id)
            
            # Verify count matches our tracking
            expected_count = len(running_tests)
            actual_count = tracker.get_active_test_count()
            assert actual_count == expected_count, \
                f"After mixed operations at step {i}: expected {expected_count} active, got {actual_count}"
        
        # Complete all remaining tests
        for test_id in list(running_tests):
            completion_status = completion_statuses[len(running_tests) % len(completion_statuses)]
            tracker.update_test_status(test_id, completion_status)
            running_tests.remove(test_id)
            
            # Verify count matches our tracking
            expected_count = len(running_tests)
            actual_count = tracker.get_active_test_count()
            assert actual_count == expected_count, \
                f"After completing test {test_id}: expected {expected_count} active, got {actual_count}"
        
        # Final verification - should be zero active tests
        assert tracker.get_active_test_count() == 0, \
            f"Expected 0 active tests at end, got {tracker.get_active_test_count()}"
    
    finally:
        tracker.stop()


@given(
    st.lists(gen_test_id(), min_size=3, max_size=10, unique=True),
    st.integers(min_value=2, max_value=5)
)
@settings(max_examples=50, deadline=None)
def test_concurrent_status_updates_maintain_consistency(
    test_ids: List[str],
    num_threads: int
):
    """
    Property: For any concurrent status updates from multiple threads, the active test count
    should remain consistent and reflect the actual number of running tests.
    
    **Feature: test-execution-orchestrator, Property 3: Status consistency during execution**
    **Validates: Requirements 1.4, 1.5**
    """
    tracker = StatusTracker()
    tracker.start()
    
    try:
        # Shared state for tracking expected results
        expected_running = set()
        lock = threading.Lock()
        errors = []
        
        def worker_thread(thread_id: int, assigned_tests: List[str]):
            """Worker thread that performs status updates."""
            try:
                for test_id in assigned_tests:
                    # Start the test
                    tracker.update_test_status(test_id, 'queued')
                    tracker.update_test_status(test_id, 'running')
                    
                    with lock:
                        expected_running.add(test_id)
                    
                    # Small delay to allow interleaving
                    time.sleep(0.001)
                    
                    # Complete the test
                    completion_status = ['completed', 'failed'][thread_id % 2]
                    tracker.update_test_status(test_id, completion_status)
                    
                    with lock:
                        expected_running.discard(test_id)
                        
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Distribute tests among threads
        tests_per_thread = len(test_ids) // num_threads
        threads = []
        
        for i in range(num_threads):
            start_idx = i * tests_per_thread
            end_idx = start_idx + tests_per_thread if i < num_threads - 1 else len(test_ids)
            assigned_tests = test_ids[start_idx:end_idx]
            
            if assigned_tests:  # Only create thread if there are tests to process
                thread = threading.Thread(
                    target=worker_thread,
                    args=(i, assigned_tests)
                )
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check for errors
        assert not errors, f"Errors occurred during concurrent execution: {errors}"
        
        # Final verification - all tests should be completed
        final_active_count = tracker.get_active_test_count()
        assert final_active_count == 0, \
            f"Expected 0 active tests after all threads complete, got {final_active_count}"
        
        # Verify all tests have completion status
        for test_id in test_ids:
            status = tracker.get_test_status(test_id)
            assert status is not None, f"Test {test_id} should have status recorded"
            assert status.status in ['completed', 'failed'], \
                f"Test {test_id} should be completed, got status {status.status}"
    
    finally:
        tracker.stop()


@given(st.lists(gen_test_id(), min_size=1, max_size=10, unique=True))
@settings(max_examples=100, deadline=None)
def test_status_count_matches_actual_running_tests(test_ids: List[str]):
    """
    Property: For any set of tests with various statuses, the active test count should
    exactly match the number of tests with "running" status.
    
    **Feature: test-execution-orchestrator, Property 3: Status consistency during execution**
    **Validates: Requirements 1.4, 1.5**
    """
    tracker = StatusTracker()
    tracker.start()
    
    try:
        # Set tests to various statuses
        running_tests = set()
        all_statuses = ['queued', 'running', 'completed', 'failed', 'timeout', 'error']
        
        for i, test_id in enumerate(test_ids):
            status = all_statuses[i % len(all_statuses)]
            
            # First set to queued if we're going to running
            if status == 'running':
                tracker.update_test_status(test_id, 'queued')
            
            tracker.update_test_status(test_id, status)
            
            if status == 'running':
                running_tests.add(test_id)
        
        # Verify active count matches running tests
        active_count = tracker.get_active_test_count()
        expected_count = len(running_tests)
        
        assert active_count == expected_count, \
            f"Active count {active_count} should match number of running tests {expected_count}"
        
        # Verify by getting all active tests
        active_tests = tracker.get_all_active_tests()
        assert len(active_tests) == expected_count, \
            f"Number of active tests {len(active_tests)} should match expected {expected_count}"
        
        # Verify all active tests are actually running
        for test_id, status in active_tests.items():
            assert status.status == 'running', \
                f"Active test {test_id} should have running status, got {status.status}"
            assert test_id in running_tests, \
                f"Active test {test_id} should be in our running tests set"
    
    finally:
        tracker.stop()


@given(
    st.lists(gen_test_id(), min_size=1, max_size=10, unique=True),
    st.lists(gen_valid_status(), min_size=1, max_size=10)
)
@settings(max_examples=100, deadline=None)
def test_invalid_transitions_dont_affect_count(
    test_ids: List[str],
    status_sequence: List[str]
):
    """
    Property: For any sequence of status updates, only valid transitions to/from "running"
    should affect the active test count.
    
    **Feature: test-execution-orchestrator, Property 3: Status consistency during execution**
    **Validates: Requirements 1.4, 1.5**
    """
    # Ensure we have enough statuses
    min_len = min(len(test_ids), len(status_sequence))
    assume(min_len >= 1)
    
    test_ids = test_ids[:min_len]
    status_sequence = status_sequence[:min_len]
    
    tracker = StatusTracker()
    tracker.start()
    
    try:
        expected_running_count = 0
        
        for test_id, target_status in zip(test_ids, status_sequence):
            # Get current status
            current_status_obj = tracker.get_test_status(test_id)
            current_status = current_status_obj.status if current_status_obj else None
            
            # Update status
            tracker.update_test_status(test_id, target_status)
            
            # Calculate expected change in running count
            if current_status != 'running' and target_status == 'running':
                expected_running_count += 1
            elif current_status == 'running' and target_status != 'running':
                expected_running_count -= 1
            
            # Verify count matches expectation
            actual_count = tracker.get_active_test_count()
            assert actual_count == expected_running_count, \
                f"After setting test {test_id} to {target_status}: " \
                f"expected {expected_running_count} active, got {actual_count}"
    
    finally:
        tracker.stop()