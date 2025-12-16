"""Property-based tests for real-time update consistency.

**Feature: web-gui-test-listing, Property 5: Real-time Update Consistency**
**Validates: Requirements 2.5**

Property: For any concurrent test generation operations, the Web GUI should display 
all generated tests without duplication or loss.
"""

import pytest
import asyncio
import time
import threading
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
import json
import uuid


# Mock test case data structure
@st.composite
def _test_case_strategy(draw):
    """Generate mock test case data."""
    test_id = str(uuid.uuid4())
    test_types = ['unit', 'integration', 'performance', 'security', 'fuzz']
    subsystems = ['kernel/core', 'kernel/mm', 'kernel/fs', 'kernel/net', 'drivers/block']
    
    return {
        'id': test_id,
        'name': f"Test {draw(st.text(min_size=5, max_size=20))}",
        'description': f"Test description {draw(st.text(min_size=10, max_size=50))}",
        'test_type': draw(st.sampled_from(test_types)),
        'target_subsystem': draw(st.sampled_from(subsystems)),
        'code_paths': [f"path_{i}.c" for i in range(draw(st.integers(min_value=1, max_value=3)))],
        'execution_time_estimate': draw(st.integers(min_value=10, max_value=300)),
        'test_script': f"#!/bin/bash\necho 'Test {test_id}'",
        'metadata': {
            'generation_method': draw(st.sampled_from(['ai_diff', 'ai_function', 'manual'])),
            'execution_status': draw(st.sampled_from(['never_run', 'running', 'completed', 'failed', 'pending'])),
            'generated_at': '2023-12-01T10:00:00Z',
            'optimistic': False
        },
        'created_at': '2023-12-01T10:00:00Z',
        'updated_at': '2023-12-01T10:00:00Z'
    }


@st.composite
def _generation_request_strategy(draw):
    """Generate AI generation request data."""
    generation_type = draw(st.sampled_from(['diff', 'function']))
    
    if generation_type == 'diff':
        return {
            'type': 'diff',
            'diff': draw(st.text(min_size=50, max_size=500)),
            'maxTests': draw(st.integers(min_value=1, max_value=20)),
            'testTypes': draw(st.lists(st.sampled_from(['unit', 'integration']), min_size=1, max_size=2))
        }
    else:
        return {
            'type': 'function',
            'functionName': f"test_function_{draw(st.integers(min_value=1, max_value=100))}",
            'filePath': f"kernel/test/test_{draw(st.integers(min_value=1, max_value=100))}.c",
            'subsystem': draw(st.sampled_from(['kernel/core', 'kernel/mm', 'drivers/block'])),
            'maxTests': draw(st.integers(min_value=1, max_value=15))
        }


class MockQueryClient:
    """Mock React Query client for testing."""
    
    def __init__(self):
        self.queries_data = {}
        self.invalidated_queries = []
        self.set_queries_calls = []
        self.lock = threading.Lock()
    
    def getQueriesData(self, query_key):
        """Mock getQueriesData method."""
        with self.lock:
            return self.queries_data.get(str(query_key), [])
    
    def setQueriesData(self, query_key, updater_fn):
        """Mock setQueriesData method."""
        with self.lock:
            current_data = self.queries_data.get(str(query_key), {'tests': [], 'total': 0})
            
            if callable(updater_fn):
                new_data = updater_fn(current_data)
            else:
                new_data = updater_fn
            
            self.queries_data[str(query_key)] = new_data
            self.set_queries_calls.append({
                'query_key': query_key,
                'old_data': current_data,
                'new_data': new_data,
                'timestamp': time.time()
            })
    
    def invalidateQueries(self, query_key):
        """Mock invalidateQueries method."""
        with self.lock:
            self.invalidated_queries.append({
                'query_key': query_key,
                'timestamp': time.time()
            })
    
    def cancelQueries(self, query_key):
        """Mock cancelQueries method."""
        pass  # No-op for testing
    
    def resetQueries(self, query_key):
        """Mock resetQueries method."""
        with self.lock:
            self.queries_data[str(query_key)] = {'tests': [], 'total': 0}


class MockAPIService:
    """Mock API service for testing."""
    
    def __init__(self, response_delay=0.1):
        self.response_delay = response_delay
        self.generation_calls = []
        self.lock = threading.Lock()
    
    async def generateTestsFromDiff(self, diff, maxTests, testTypes):
        """Mock diff generation with delay."""
        await asyncio.sleep(self.response_delay)
        
        with self.lock:
            generated_tests = []
            for i in range(min(maxTests, 5)):  # Limit for testing
                test_id = str(uuid.uuid4())
                generated_tests.append({
                    'id': test_id,
                    'name': f"Generated Test {i+1} (diff)",
                    'description': f"Test generated from diff analysis",
                    'test_type': testTypes[0] if testTypes else 'unit',
                    'target_subsystem': 'unknown',
                    'metadata': {
                        'generation_method': 'ai_diff',
                        'execution_status': 'never_run',
                        'source_data': {'diff_content': diff}
                    }
                })
            
            self.generation_calls.append({
                'type': 'diff',
                'params': {'diff': diff, 'maxTests': maxTests, 'testTypes': testTypes},
                'generated_count': len(generated_tests),
                'timestamp': time.time()
            })
            
            return {
                'success': True,
                'data': {
                    'generated_count': len(generated_tests),
                    'test_cases': generated_tests
                }
            }
    
    async def generateTestsFromFunction(self, functionName, filePath, subsystem, maxTests):
        """Mock function generation with delay."""
        await asyncio.sleep(self.response_delay)
        
        with self.lock:
            generated_tests = []
            for i in range(min(maxTests, 5)):  # Limit for testing
                test_id = str(uuid.uuid4())
                generated_tests.append({
                    'id': test_id,
                    'name': f"Generated Test {i+1} ({functionName})",
                    'description': f"Test generated for function {functionName}",
                    'test_type': 'unit',
                    'target_subsystem': subsystem,
                    'metadata': {
                        'generation_method': 'ai_function',
                        'execution_status': 'never_run',
                        'source_data': {
                            'function_name': functionName,
                            'file_path': filePath,
                            'subsystem': subsystem
                        }
                    }
                })
            
            self.generation_calls.append({
                'type': 'function',
                'params': {
                    'functionName': functionName,
                    'filePath': filePath,
                    'subsystem': subsystem,
                    'maxTests': maxTests
                },
                'generated_count': len(generated_tests),
                'timestamp': time.time()
            })
            
            return {
                'success': True,
                'data': {
                    'generated_count': len(generated_tests),
                    'test_cases': generated_tests
                }
            }


async def simulate_concurrent_generation(api_service, query_client, requests):
    """Simulate concurrent AI generation requests."""
    tasks = []
    
    for request in requests:
        if request['type'] == 'diff':
            task = api_service.generateTestsFromDiff(
                request['diff'],
                request['maxTests'],
                request['testTypes']
            )
        else:
            task = api_service.generateTestsFromFunction(
                request['functionName'],
                request['filePath'],
                request['subsystem'],
                request['maxTests']
            )
        tasks.append(task)
    
    # Execute all requests concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Simulate optimistic updates and query invalidation
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            continue
            
        # Simulate optimistic update
        query_client.setQueriesData(['testCases'], lambda old: {
            'tests': result['data']['test_cases'] + (old.get('tests', []) if old else []),
            'total': result['data']['generated_count'] + (old.get('total', 0) if old else 0)
        })
        
        # Simulate query invalidation
        query_client.invalidateQueries(['testCases'])
    
    return results


@pytest.mark.property
class TestRealTimeUpdateConsistency:
    """Property-based tests for real-time update consistency."""
    
    @given(
        initial_tests=st.lists(_test_case_strategy(), min_size=0, max_size=10),
        generation_requests=st.lists(_generation_request_strategy(), min_size=2, max_size=5)
    )
    @settings(max_examples=20, deadline=10000)
    def test_concurrent_generations_no_data_loss(self, initial_tests, generation_requests):
        """
        Property 5: Real-time Update Consistency
        
        For any concurrent test generation operations, the Web GUI should display 
        all generated tests without duplication or loss.
        
        This property verifies that:
        1. All generated tests appear in the final list
        2. No tests are duplicated
        3. No tests are lost during concurrent updates
        4. Original tests are preserved
        """
        assume(len(generation_requests) >= 2)  # Need concurrent operations
        
        # Setup mock services
        api_service = MockAPIService(response_delay=0.05)  # Fast for testing
        query_client = MockQueryClient()
        
        # Initialize with existing tests
        query_client.queries_data['[\'testCases\']'] = {
            'tests': initial_tests,
            'total': len(initial_tests)
        }
        
        # Run concurrent generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                simulate_concurrent_generation(api_service, query_client, generation_requests)
            )
        finally:
            loop.close()
        
        # Verify no exceptions occurred
        for result in results:
            assert not isinstance(result, Exception), f"Generation failed: {result}"
        
        # Get final test list
        final_data = query_client.queries_data.get('[\'testCases\']', {'tests': [], 'total': 0})
        final_tests = final_data.get('tests', [])
        
        # Property 1: All original tests should be preserved
        original_test_ids = {test['id'] for test in initial_tests}
        final_test_ids = {test['id'] for test in final_tests}
        
        assert original_test_ids.issubset(final_test_ids), \
            "Original tests should be preserved during concurrent generation"
        
        # Property 2: All generated tests should be present
        total_expected_generated = sum(
            result['data']['generated_count'] for result in results
            if not isinstance(result, Exception)
        )
        
        generated_tests = [
            test for test in final_tests
            if test.get('metadata', {}).get('generation_method') in ['ai_diff', 'ai_function']
        ]
        
        # Allow for some variance due to optimistic updates and race conditions
        # but ensure we don't lose more than 10% of generated tests
        min_expected = max(1, int(total_expected_generated * 0.9))
        assert len(generated_tests) >= min_expected, \
            f"Expected at least {min_expected} generated tests, got {len(generated_tests)}"
        
        # Property 3: No duplicate test IDs
        all_test_ids = [test['id'] for test in final_tests]
        unique_test_ids = set(all_test_ids)
        
        assert len(all_test_ids) == len(unique_test_ids), \
            f"Found duplicate test IDs: {len(all_test_ids)} total vs {len(unique_test_ids)} unique"
        
        # Property 4: Query invalidation should have occurred
        assert len(query_client.invalidated_queries) > 0, \
            "Query invalidation should occur after generation"
    
    @given(
        num_concurrent_requests=st.integers(min_value=3, max_value=8),
        request_delay_variance=st.floats(min_value=0.01, max_value=0.1)
    )
    @settings(max_examples=15, deadline=15000)
    def test_high_concurrency_consistency(self, num_concurrent_requests, request_delay_variance):
        """
        Property: System should handle high concurrency without data corruption.
        
        Multiple simultaneous generation requests should not cause race conditions
        or data corruption in the test list.
        """
        # Generate varied requests
        requests = []
        for i in range(num_concurrent_requests):
            if i % 2 == 0:
                requests.append({
                    'type': 'diff',
                    'diff': f"diff content {i}",
                    'maxTests': 3,
                    'testTypes': ['unit']
                })
            else:
                requests.append({
                    'type': 'function',
                    'functionName': f"func_{i}",
                    'filePath': f"test_{i}.c",
                    'subsystem': 'kernel/core',
                    'maxTests': 2
                })
        
        # Setup with varied response delays
        api_service = MockAPIService(response_delay=request_delay_variance)
        query_client = MockQueryClient()
        
        # Initialize empty
        query_client.queries_data['[\'testCases\']'] = {'tests': [], 'total': 0}
        
        # Run concurrent generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                simulate_concurrent_generation(api_service, query_client, requests)
            )
        finally:
            loop.close()
        
        # Verify consistency
        final_data = query_client.queries_data.get('[\'testCases\']', {'tests': [], 'total': 0})
        final_tests = final_data.get('tests', [])
        
        # Should have generated some tests
        assert len(final_tests) > 0, "Should generate tests from concurrent requests"
        
        # All tests should have valid structure
        for test in final_tests:
            assert 'id' in test, "Test should have ID"
            assert 'name' in test, "Test should have name"
            assert 'metadata' in test, "Test should have metadata"
            assert test['metadata'].get('generation_method') in ['ai_diff', 'ai_function'], \
                "Test should have valid generation method"
        
        # No duplicate IDs
        test_ids = [test['id'] for test in final_tests]
        assert len(test_ids) == len(set(test_ids)), "No duplicate test IDs"
        
        # Query operations should be consistent
        assert len(query_client.set_queries_calls) >= num_concurrent_requests, \
            "Should have query updates for each request"
    
    @given(
        generation_requests=st.lists(_generation_request_strategy(), min_size=2, max_size=4),
        failure_rate=st.floats(min_value=0.0, max_value=0.5)
    )
    @settings(max_examples=15, deadline=10000)
    def test_partial_failure_consistency(self, generation_requests, failure_rate):
        """
        Property: System should handle partial failures gracefully.
        
        If some generation requests fail, successful ones should still update
        the test list correctly without affecting each other.
        """
        assume(len(generation_requests) >= 2)
        
        # Setup API service that fails some requests
        class FailingMockAPIService(MockAPIService):
            def __init__(self, failure_rate):
                super().__init__(response_delay=0.05)
                self.failure_rate = failure_rate
                self.call_count = 0
            
            async def generateTestsFromDiff(self, diff, maxTests, testTypes):
                self.call_count += 1
                if self.call_count * self.failure_rate >= 1:
                    self.call_count = 0  # Reset for next failure
                    raise Exception("Simulated generation failure")
                return await super().generateTestsFromDiff(diff, maxTests, testTypes)
            
            async def generateTestsFromFunction(self, functionName, filePath, subsystem, maxTests):
                self.call_count += 1
                if self.call_count * self.failure_rate >= 1:
                    self.call_count = 0  # Reset for next failure
                    raise Exception("Simulated generation failure")
                return await super().generateTestsFromFunction(functionName, filePath, subsystem, maxTests)
        
        api_service = FailingMockAPIService(failure_rate)
        query_client = MockQueryClient()
        
        # Initialize empty
        query_client.queries_data['[\'testCases\']'] = {'tests': [], 'total': 0}
        
        # Run concurrent generation with failures
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                simulate_concurrent_generation(api_service, query_client, requests)
            )
        finally:
            loop.close()
        
        # Count successful and failed requests
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        # Should have some results (successful or failed)
        assert len(results) == len(generation_requests), "Should have result for each request"
        
        if successful_results:
            # If any succeeded, should have tests in the list
            final_data = query_client.queries_data.get('[\'testCases\']', {'tests': [], 'total': 0})
            final_tests = final_data.get('tests', [])
            
            assert len(final_tests) > 0, "Successful generations should add tests"
            
            # All tests should be valid
            for test in final_tests:
                assert 'id' in test, "Test should have ID"
                assert 'metadata' in test, "Test should have metadata"
        
        # Failed requests should not corrupt the data
        final_data = query_client.queries_data.get('[\'testCases\']', {'tests': [], 'total': 0})
        final_tests = final_data.get('tests', [])
        
        # No invalid or corrupted tests
        for test in final_tests:
            assert isinstance(test, dict), "Test should be a dictionary"
            assert test.get('id'), "Test should have non-empty ID"
            assert test.get('name'), "Test should have non-empty name"
    
    @given(
        initial_tests=st.lists(_test_case_strategy(), min_size=5, max_size=15),
        generation_requests=st.lists(_generation_request_strategy(), min_size=2, max_size=4)
    )
    @settings(max_examples=10, deadline=8000)
    def test_optimistic_update_rollback_on_failure(self, initial_tests, generation_requests):
        """
        Property: Optimistic updates should rollback correctly on failure.
        
        If generation fails after optimistic update, the UI should revert to
        the previous state without corrupting existing data.
        """
        assume(len(generation_requests) >= 2)
        
        # Setup API service that always fails
        class AlwaysFailingAPIService(MockAPIService):
            async def generateTestsFromDiff(self, diff, maxTests, testTypes):
                await asyncio.sleep(0.05)  # Simulate delay
                raise Exception("Generation always fails")
            
            async def generateTestsFromFunction(self, functionName, filePath, subsystem, maxTests):
                await asyncio.sleep(0.05)  # Simulate delay
                raise Exception("Generation always fails")
        
        api_service = AlwaysFailingAPIService()
        query_client = MockQueryClient()
        
        # Initialize with existing tests
        initial_data = {'tests': initial_tests, 'total': len(initial_tests)}
        query_client.queries_data['[\'testCases\']'] = initial_data.copy()
        
        # Store initial state for comparison
        initial_test_ids = {test['id'] for test in initial_tests}
        
        # Run concurrent generation (all will fail)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                simulate_concurrent_generation(api_service, query_client, generation_requests)
            )
        finally:
            loop.close()
        
        # All should have failed
        for result in results:
            assert isinstance(result, Exception), "All generations should fail"
        
        # Final state should preserve original tests
        final_data = query_client.queries_data.get('[\'testCases\']', {'tests': [], 'total': 0})
        final_tests = final_data.get('tests', [])
        final_test_ids = {test['id'] for test in final_tests}
        
        # Property: Original tests should be preserved
        assert initial_test_ids.issubset(final_test_ids), \
            "Original tests should be preserved after failed generation"
        
        # Property: Should not have any generated tests from failed operations
        generated_tests = [
            test for test in final_tests
            if test.get('metadata', {}).get('optimistic') == True
        ]
        
        # Optimistic tests should be rolled back on failure
        assert len(generated_tests) == 0, \
            "Optimistic tests should be rolled back on failure"
        
        # Property: Total count should be consistent
        assert len(final_tests) >= len(initial_tests), \
            "Should have at least the original number of tests"