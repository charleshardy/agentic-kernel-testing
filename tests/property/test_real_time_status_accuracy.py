"""Property-based tests for real-time status accuracy.

**Feature: test-execution-orchestrator, Property 4: Real-time status accuracy**
**Validates: Requirements 2.1, 2.2**

Property 4: Real-time status accuracy
For any system status query, the returned active test count should match the actual number 
of tests currently in "running" status.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List, Dict, Any
import threading
import time
import json

from orchestrator.status_tracker import StatusTracker, TestExecutionStatus
from api.routers.health import get_orchestrator_metrics, set_orchestrator_service


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
def gen_test_status_mix(draw):
    """Generate a mix of test statuses with some running tests."""
    num_tests = draw(st.integers(min_value=1, max_value=20))
    test_ids = draw(st.lists(gen_test_id(), min_size=num_tests, max_size=num_tests, unique=True))
    
    # Ensure at least some tests are running
    num_running = draw(st.integers(min_value=0, max_value=max(1, num_tests // 2)))
    
    statuses = []
    for i in range(num_tests):
        if i < num_running:
            statuses.append('running')
        else:
            statuses.append(draw(st.sampled_from(['queued', 'completed', 'failed', 'timeout', 'error'])))
    
    return list(zip(test_ids, statuses))


class MockOrchestratorService:
    """Mock orchestrator service for testing API integration."""
    
    def __init__(self, status_tracker: StatusTracker):
        self.status_tracker = status_tracker
        self.is_running = True
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics from the status tracker."""
        return self.status_tracker.get_system_metrics()


@given(gen_test_status_mix())
@settings(max_examples=100, deadline=None)
def test_api_status_matches_actual_running_tests(test_status_pairs):
    """
    Property: For any system status query, the returned active test count should match 
    the actual number of tests currently in "running" status.
    
    **Feature: test-execution-orchestrator, Property 4: Real-time status accuracy**
    **Validates: Requirements 2.1, 2.2**
    """
    tracker = StatusTracker()
    tracker.start()
    
    # Set up mock orchestrator service
    mock_orchestrator = MockOrchestratorService(tracker)
    set_orchestrator_service(mock_orchestrator)
    
    try:
        # Set up tests with various statuses
        expected_running_count = 0
        
        for test_id, status in test_status_pairs:
            # First set to queued if we're going to running
            if status == 'running':
                tracker.update_test_status(test_id, 'queued')
            
            tracker.update_test_status(test_id, status)
            
            if status == 'running':
                expected_running_count += 1
        
        # Get API metrics
        api_metrics = get_orchestrator_metrics()
        
        # Verify API returns correct active test count
        api_active_count = api_metrics.get('active_tests', 0)
        assert api_active_count == expected_running_count, \
            f"API should return {expected_running_count} active tests, got {api_active_count}"
        
        # Verify consistency with direct status tracker query
        tracker_active_count = tracker.get_active_test_count()
        assert api_active_count == tracker_active_count, \
            f"API active count {api_active_count} should match tracker count {tracker_active_count}"
        
        # Verify by counting actual running tests
        all_active_tests = tracker.get_all_active_tests()
        actual_running_count = len(all_active_tests)
        assert api_active_count == actual_running_count, \
            f"API active count {api_active_count} should match actual running tests {actual_running_count}"
        
        # Verify all reported active tests are actually running
        for test_id, status in all_active_tests.items():
            assert status.status == 'running', \
                f"Test {test_id} reported as active should have running status, got {status.status}"
    
    finally:
        tracker.stop()
        set_orchestrator_service(None)


@given(
    st.lists(gen_test_id(), min_size=1, max_size=15, unique=True),
    st.integers(min_value=2, max_value=5)
)
@settings(max_examples=50, deadline=None)
def test_concurrent_status_queries_return_consistent_counts(
    test_ids,
    num_query_threads
):
    """
    Property: For any concurrent system status queries while tests are transitioning,
    all queries should return consistent active test counts that reflect the actual
    number of running tests at query time.
    
    **Feature: test-execution-orchestrator, Property 4: Real-time status accuracy**
    **Validates: Requirements 2.1, 2.2**
    """
    tracker = StatusTracker()
    tracker.start()
    
    # Set up mock orchestrator service
    mock_orchestrator = MockOrchestratorService(tracker)
    set_orchestrator_service(mock_orchestrator)
    
    try:
        # Shared state for collecting query results
        query_results = []
        query_lock = threading.Lock()
        errors = []
        
        def status_query_worker(worker_id: int):
            """Worker thread that performs status queries."""
            try:
                for _ in range(5):  # Each thread makes 5 queries
                    # Get API metrics
                    api_metrics = get_orchestrator_metrics()
                    api_active_count = api_metrics.get('active_tests', 0)
                    
                    # Get direct tracker count
                    tracker_active_count = tracker.get_active_test_count()
                    
                    # Get actual running tests count
                    actual_running_count = len(tracker.get_all_active_tests())
                    
                    with query_lock:
                        query_results.append({
                            'worker_id': worker_id,
                            'api_count': api_active_count,
                            'tracker_count': tracker_active_count,
                            'actual_count': actual_running_count,
                            'timestamp': time.time()
                        })
                    
                    time.sleep(0.001)  # Small delay between queries
                    
            except Exception as e:
                errors.append(f"Query worker {worker_id}: {e}")
        
        def status_update_worker():
            """Worker thread that updates test statuses."""
            try:
                for test_id in test_ids:
                    # Start test
                    tracker.update_test_status(test_id, 'queued')
                    time.sleep(0.002)
                    tracker.update_test_status(test_id, 'running')
                    time.sleep(0.005)
                    
                    # Complete test
                    completion_status = ['completed', 'failed'][hash(test_id) % 2]
                    tracker.update_test_status(test_id, completion_status)
                    time.sleep(0.002)
                    
            except Exception as e:
                errors.append(f"Update worker: {e}")
        
        # Start query threads
        query_threads = []
        for i in range(num_query_threads):
            thread = threading.Thread(target=status_query_worker, args=(i,))
            query_threads.append(thread)
            thread.start()
        
        # Start update thread
        update_thread = threading.Thread(target=status_update_worker)
        update_thread.start()
        
        # Wait for all threads to complete
        for thread in query_threads:
            thread.join()
        update_thread.join()
        
        # Check for errors
        assert not errors, f"Errors occurred during concurrent execution: {errors}"
        
        # Verify all query results are internally consistent
        for result in query_results:
            api_count = result['api_count']
            tracker_count = result['tracker_count']
            actual_count = result['actual_count']
            
            assert api_count == tracker_count, \
                f"Worker {result['worker_id']}: API count {api_count} should match tracker count {tracker_count}"
            
            assert api_count == actual_count, \
                f"Worker {result['worker_id']}: API count {api_count} should match actual count {actual_count}"
            
            # Counts should be non-negative
            assert api_count >= 0, f"Active test count should be non-negative, got {api_count}"
    
    finally:
        tracker.stop()
        set_orchestrator_service(None)


@given(st.lists(gen_test_id(), min_size=1, max_size=10, unique=True))
@settings(max_examples=100, deadline=None)
def test_status_api_reflects_immediate_changes(test_ids):
    """
    Property: For any test status change, the API should immediately reflect the new
    active test count without delay.
    
    **Feature: test-execution-orchestrator, Property 4: Real-time status accuracy**
    **Validates: Requirements 2.1, 2.2**
    """
    tracker = StatusTracker()
    tracker.start()
    
    # Set up mock orchestrator service
    mock_orchestrator = MockOrchestratorService(tracker)
    set_orchestrator_service(mock_orchestrator)
    
    try:
        expected_active_count = 0
        
        for test_id in test_ids:
            # Start test
            tracker.update_test_status(test_id, 'queued')
            
            # Check API immediately after queuing (should not change active count)
            api_metrics = get_orchestrator_metrics()
            api_active_count = api_metrics.get('active_tests', 0)
            assert api_active_count == expected_active_count, \
                f"After queuing {test_id}: expected {expected_active_count} active, got {api_active_count}"
            
            # Transition to running
            tracker.update_test_status(test_id, 'running')
            expected_active_count += 1
            
            # Check API immediately after running transition
            api_metrics = get_orchestrator_metrics()
            api_active_count = api_metrics.get('active_tests', 0)
            assert api_active_count == expected_active_count, \
                f"After starting {test_id}: expected {expected_active_count} active, got {api_active_count}"
        
        # Complete all tests
        for test_id in test_ids:
            # Complete test
            tracker.update_test_status(test_id, 'completed')
            expected_active_count -= 1
            
            # Check API immediately after completion
            api_metrics = get_orchestrator_metrics()
            api_active_count = api_metrics.get('active_tests', 0)
            assert api_active_count == expected_active_count, \
                f"After completing {test_id}: expected {expected_active_count} active, got {api_active_count}"
        
        # Final verification - should be zero
        assert expected_active_count == 0, "All tests should be completed"
        api_metrics = get_orchestrator_metrics()
        api_active_count = api_metrics.get('active_tests', 0)
        assert api_active_count == 0, f"Final API count should be 0, got {api_active_count}"
    
    finally:
        tracker.stop()
        set_orchestrator_service(None)


@given(
    st.lists(gen_test_id(), min_size=5, max_size=15, unique=True),
    st.lists(gen_valid_status(), min_size=5, max_size=15)
)
@settings(max_examples=100, deadline=None)
def test_api_metrics_include_all_required_fields(
    test_ids,
    statuses
):
    """
    Property: For any system status query, the API should return all required metrics
    fields with accurate values that match the actual system state.
    
    **Feature: test-execution-orchestrator, Property 4: Real-time status accuracy**
    **Validates: Requirements 2.1, 2.2**
    """
    # Ensure we have enough data
    min_len = min(len(test_ids), len(statuses))
    assume(min_len >= 5)
    
    test_ids = test_ids[:min_len]
    statuses = statuses[:min_len]
    
    tracker = StatusTracker()
    tracker.start()
    
    # Set up mock orchestrator service
    mock_orchestrator = MockOrchestratorService(tracker)
    set_orchestrator_service(mock_orchestrator)
    
    try:
        # Set up tests with various statuses
        expected_counts = {
            'active_tests': 0,
            'queued_tests': 0,
            'completed_tests': 0,
            'failed_tests': 0
        }
        
        for test_id, status in zip(test_ids, statuses):
            # First set to queued if we're going to running
            if status == 'running':
                tracker.update_test_status(test_id, 'queued')
            
            tracker.update_test_status(test_id, status)
            
            # Update expected counts
            if status == 'running':
                expected_counts['active_tests'] += 1
            elif status == 'queued':
                expected_counts['queued_tests'] += 1
            elif status == 'completed':
                expected_counts['completed_tests'] += 1
            elif status in ['failed', 'timeout', 'error']:
                expected_counts['failed_tests'] += 1
        
        # Get API metrics
        api_metrics = get_orchestrator_metrics()
        
        # Verify all required fields are present
        required_fields = ['active_tests', 'queued_tests']
        for field in required_fields:
            assert field in api_metrics, f"API metrics should include '{field}' field"
        
        # Verify active tests count is accurate
        assert api_metrics['active_tests'] == expected_counts['active_tests'], \
            f"API active_tests should be {expected_counts['active_tests']}, got {api_metrics['active_tests']}"
        
        # Verify queued tests count is accurate
        assert api_metrics['queued_tests'] == expected_counts['queued_tests'], \
            f"API queued_tests should be {expected_counts['queued_tests']}, got {api_metrics['queued_tests']}"
        
        # Verify counts are non-negative
        for field in required_fields:
            assert api_metrics[field] >= 0, f"API {field} should be non-negative, got {api_metrics[field]}"
        
        # Verify consistency with direct tracker queries
        tracker_metrics = tracker.get_system_metrics()
        assert api_metrics['active_tests'] == tracker_metrics['active_tests'], \
            "API active_tests should match tracker active_tests"
        assert api_metrics['queued_tests'] == tracker_metrics['queued_tests'], \
            "API queued_tests should match tracker queued_tests"
    
    finally:
        tracker.stop()
        set_orchestrator_service(None)


@given(st.lists(gen_test_id(), min_size=1, max_size=8, unique=True))
@settings(max_examples=50, deadline=None)
def test_api_handles_orchestrator_service_unavailable(test_ids):
    """
    Property: For any system status query when the orchestrator service is unavailable,
    the API should return default values without errors and indicate the service status.
    
    **Feature: test-execution-orchestrator, Property 4: Real-time status accuracy**
    **Validates: Requirements 2.1, 2.2**
    """
    # Ensure no orchestrator service is set
    set_orchestrator_service(None)
    
    try:
        # Get API metrics when orchestrator is unavailable
        api_metrics = get_orchestrator_metrics()
        
        # Verify API returns default values
        assert 'active_tests' in api_metrics, "API should include active_tests field"
        assert 'queued_tests' in api_metrics, "API should include queued_tests field"
        assert 'available_environments' in api_metrics, "API should include available_environments field"
        
        # Default values should be reasonable
        assert api_metrics['active_tests'] == 0, "Default active_tests should be 0"
        assert api_metrics['queued_tests'] == 0, "Default queued_tests should be 0"
        assert api_metrics['available_environments'] >= 0, "Default available_environments should be non-negative"
        
        # Should indicate service is not running
        assert 'status' in api_metrics, "API should include status field when orchestrator unavailable"
        assert api_metrics['status'] == 'not_running', "Status should indicate orchestrator is not running"
        
    finally:
        set_orchestrator_service(None)


@given(
    st.lists(gen_test_id(), min_size=3, max_size=10, unique=True),
    st.integers(min_value=1, max_value=3)
)
@settings(max_examples=50, deadline=None)
def test_api_status_accuracy_during_rapid_changes(
    test_ids,
    change_cycles
):
    """
    Property: For any rapid sequence of test status changes, the API should maintain
    accuracy and never return inconsistent counts.
    
    **Feature: test-execution-orchestrator, Property 4: Real-time status accuracy**
    **Validates: Requirements 2.1, 2.2**
    """
    tracker = StatusTracker()
    tracker.start()
    
    # Set up mock orchestrator service
    mock_orchestrator = MockOrchestratorService(tracker)
    set_orchestrator_service(mock_orchestrator)
    
    try:
        for cycle in range(change_cycles):
            # Rapid start of all tests
            for test_id in test_ids:
                tracker.update_test_status(test_id, 'queued')
                tracker.update_test_status(test_id, 'running')
            
            # Check API after rapid starts
            api_metrics = get_orchestrator_metrics()
            expected_active = len(test_ids)
            actual_active = api_metrics.get('active_tests', 0)
            
            assert actual_active == expected_active, \
                f"Cycle {cycle}: After rapid starts, expected {expected_active} active, got {actual_active}"
            
            # Verify consistency
            tracker_active = tracker.get_active_test_count()
            assert actual_active == tracker_active, \
                f"Cycle {cycle}: API count {actual_active} should match tracker count {tracker_active}"
            
            # Rapid completion of all tests
            for i, test_id in enumerate(test_ids):
                completion_status = ['completed', 'failed'][i % 2]
                tracker.update_test_status(test_id, completion_status)
            
            # Check API after rapid completions
            api_metrics = get_orchestrator_metrics()
            actual_active = api_metrics.get('active_tests', 0)
            
            assert actual_active == 0, \
                f"Cycle {cycle}: After rapid completions, expected 0 active, got {actual_active}"
            
            # Verify consistency
            tracker_active = tracker.get_active_test_count()
            assert actual_active == tracker_active, \
                f"Cycle {cycle}: API count {actual_active} should match tracker count {tracker_active}"
    
    finally:
        tracker.stop()
        set_orchestrator_service(None)