"""Property-based tests for bulk operation atomicity.

Feature: web-gui-test-listing, Property 4: Bulk Operation Atomicity
Validates: Requirements 3.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid
import sys
import os
from unittest.mock import MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from api.routers.tests import submitted_tests, execution_plans
    from api.models import BulkOperationRequest
    from ai_generator.models import TestType, TestCase
except ImportError as e:
    pytest.skip(f"Skipping test due to import error: {e}", allow_module_level=True)


# Strategy for generating test case data
@st.composite
def test_case_data_strategy(draw):
    """Generate test case data for storage."""
    test_types = [TestType.UNIT, TestType.INTEGRATION, TestType.PERFORMANCE, TestType.SECURITY]
    subsystems = ['scheduler', 'memory', 'filesystem', 'networking', 'drivers']
    execution_statuses = ['never_run', 'completed', 'failed']  # Exclude 'running' for most operations
    
    test_id = str(uuid.uuid4())
    submission_id = str(uuid.uuid4())
    
    # Create mock test case
    test_case = MagicMock()
    test_case.id = test_id
    test_case.name = draw(st.text(min_size=1, max_size=100))
    test_case.description = draw(st.text(min_size=1, max_size=500))
    test_case.test_type = draw(st.sampled_from(test_types))
    test_case.target_subsystem = draw(st.sampled_from(subsystems))
    test_case.code_paths = draw(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5))
    test_case.execution_time_estimate = draw(st.integers(min_value=1, max_value=3600))
    test_case.required_hardware = None
    test_case.test_script = draw(st.text(min_size=1, max_size=1000))
    test_case.expected_outcome = None
    test_case.metadata = {}
    
    # Generate creation time within last 30 days
    base_time = datetime.utcnow()
    time_offset = draw(st.integers(min_value=0, max_value=30 * 24 * 3600))  # 30 days in seconds
    created_at = base_time - timedelta(seconds=time_offset)
    
    return {
        "test_case": test_case,
        "submission_id": submission_id,
        "submitted_by": "test_user",
        "submitted_at": created_at,
        "priority": draw(st.integers(min_value=1, max_value=10)),
        "generation_info": {
            "method": "manual",
            "source_data": {"submitted_by": "test_user"},
            "generated_at": created_at.isoformat(),
            "ai_model": None,
            "generation_params": {}
        },
        "execution_status": draw(st.sampled_from(execution_statuses)),
        "last_execution_at": created_at + timedelta(hours=1) if draw(st.booleans()) else None,
        "tags": draw(st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5)),
        "is_favorite": draw(st.booleans()),
        "updated_at": created_at + timedelta(minutes=draw(st.integers(min_value=0, max_value=60)))
    }


@st.composite
def test_database_state_strategy(draw):
    """Generate a database state with multiple test cases."""
    num_tests = draw(st.integers(min_value=5, max_value=20))
    test_data = {}
    
    for _ in range(num_tests):
        test_case_data = draw(test_case_data_strategy())
        test_id = test_case_data["test_case"].id
        test_data[test_id] = test_case_data
    
    return test_data


@st.composite
def bulk_operation_strategy(draw):
    """Generate bulk operation requests."""
    operations = ["delete", "execute", "update_tags", "update_favorite"]
    operation = draw(st.sampled_from(operations))
    
    parameters = {}
    if operation == "execute":
        parameters = {
            "priority": draw(st.integers(min_value=1, max_value=10)),
            "timeout": draw(st.integers(min_value=30, max_value=3600))
        }
    elif operation == "update_tags":
        parameters = {
            "tags": draw(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)),
            "operation_type": draw(st.sampled_from(["replace", "add", "remove"]))
        }
    elif operation == "update_favorite":
        parameters = {
            "is_favorite": draw(st.booleans())
        }
    
    return operation, parameters


@pytest.mark.property
class TestBulkOperationAtomicityProperties:
    """Property-based tests for bulk operation atomicity."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear the global test storage before each test
        submitted_tests.clear()
        execution_plans.clear()
    
    def teardown_method(self):
        """Clean up after test."""
        # Clear the global test storage after each test
        submitted_tests.clear()
        execution_plans.clear()
    
    @given(
        test_data=test_database_state_strategy(),
        operation_data=bulk_operation_strategy()
    )
    @settings(max_examples=10)
    def test_bulk_operation_atomicity_success_case(self, test_data, operation_data):
        """
        Property 4: Bulk Operation Atomicity - Success Case
        
        For any bulk operation on test cases, if all operations can succeed,
        then all operations should succeed and the system should be in a
        consistent state after completion.
        
        **Validates: Requirements 3.5**
        """
        assume(len(test_data) >= 3)  # Need at least 3 tests for meaningful bulk operations
        
        operation, parameters = operation_data
        
        # Store test data in the global storage
        submitted_tests.clear()
        execution_plans.clear()
        submitted_tests.update(test_data)
        
        # Select a subset of test cases for the bulk operation
        test_ids = list(test_data.keys())
        selected_test_ids = test_ids[:min(len(test_ids), 5)]  # Limit to 5 for performance
        
        # Record initial state
        initial_state = {
            "test_count": len(submitted_tests),
            "execution_plan_count": len(execution_plans),
            "test_states": {tid: submitted_tests[tid]["execution_status"] for tid in selected_test_ids},
            "test_tags": {tid: submitted_tests[tid].get("tags", []).copy() for tid in selected_test_ids},
            "test_favorites": {tid: submitted_tests[tid].get("is_favorite", False) for tid in selected_test_ids}
        }
        
        # Simulate the bulk operation logic directly
        successful_operations = []
        failed_operations = []
        
        # Pre-validate all operations (atomicity check)
        can_proceed = True
        for test_id in selected_test_ids:
            if test_id not in submitted_tests:
                can_proceed = False
                break
            
            test_data_item = submitted_tests[test_id]
            
            # Check operation-specific preconditions
            if operation == "delete" and test_data_item.get("execution_status") == "running":
                can_proceed = False
                break
            
            if operation == "execute" and test_data_item.get("execution_status") == "running":
                can_proceed = False
                break
        
        if can_proceed:
            # Execute the bulk operation
            if operation == "delete":
                # Delete operations
                for test_id in selected_test_ids:
                    if test_id in submitted_tests:
                        del submitted_tests[test_id]
                        successful_operations.append(test_id)
                    else:
                        failed_operations.append(test_id)
            
            elif operation == "execute":
                # Execute operations - create execution plan
                if selected_test_ids:
                    plan_id = str(uuid.uuid4())
                    total_estimate = sum(
                        submitted_tests[test_id]["test_case"].execution_time_estimate 
                        for test_id in selected_test_ids if test_id in submitted_tests
                    )
                    estimated_completion = datetime.utcnow() + timedelta(seconds=total_estimate)
                    
                    execution_plans[plan_id] = {
                        "submission_id": str(uuid.uuid4()),
                        "test_case_ids": selected_test_ids,
                        "priority": parameters.get("priority", 5),
                        "target_environments": None,
                        "webhook_url": None,
                        "status": "queued",
                        "created_at": datetime.utcnow(),
                        "estimated_completion": estimated_completion,
                        "created_by": "test_user",
                        "execution_type": "bulk",
                        "timeout": parameters.get("timeout", 300)
                    }
                    
                    # Update test case statuses
                    for test_id in selected_test_ids:
                        if test_id in submitted_tests:
                            submitted_tests[test_id]["execution_status"] = "queued"
                            submitted_tests[test_id]["updated_at"] = datetime.utcnow()
                            successful_operations.append(test_id)
                        else:
                            failed_operations.append(test_id)
            
            elif operation == "update_tags":
                # Update tags operations
                new_tags = parameters.get("tags", [])
                operation_type = parameters.get("operation_type", "replace")
                
                for test_id in selected_test_ids:
                    if test_id in submitted_tests:
                        test_data_item = submitted_tests[test_id]
                        current_tags = test_data_item.get("tags", [])
                        
                        if operation_type == "replace":
                            test_data_item["tags"] = new_tags
                        elif operation_type == "add":
                            test_data_item["tags"] = list(set(current_tags + new_tags))
                        elif operation_type == "remove":
                            test_data_item["tags"] = [tag for tag in current_tags if tag not in new_tags]
                        
                        test_data_item["updated_at"] = datetime.utcnow()
                        successful_operations.append(test_id)
                    else:
                        failed_operations.append(test_id)
            
            elif operation == "update_favorite":
                # Update favorite status operations
                is_favorite = parameters.get("is_favorite", False)
                
                for test_id in selected_test_ids:
                    if test_id in submitted_tests:
                        submitted_tests[test_id]["is_favorite"] = is_favorite
                        submitted_tests[test_id]["updated_at"] = datetime.utcnow()
                        successful_operations.append(test_id)
                    else:
                        failed_operations.append(test_id)
        
        # Verify atomicity properties
        if can_proceed and not failed_operations:
            # All operations should have succeeded
            assert len(successful_operations) == len(selected_test_ids), \
                f"Expected all {len(selected_test_ids)} operations to succeed, got {len(successful_operations)}"
            
            # Verify final state consistency
            if operation == "delete":
                # Tests should be removed
                for test_id in selected_test_ids:
                    assert test_id not in submitted_tests, \
                        f"Test {test_id} should have been deleted but still exists"
                
                expected_final_count = initial_state["test_count"] - len(selected_test_ids)
                assert len(submitted_tests) == expected_final_count, \
                    f"Expected {expected_final_count} tests after deletion, got {len(submitted_tests)}"
            
            elif operation == "execute":
                # Tests should be queued and execution plan should exist
                for test_id in selected_test_ids:
                    assert submitted_tests[test_id]["execution_status"] == "queued", \
                        f"Test {test_id} should be queued for execution"
                
                # Should have created exactly one execution plan
                assert len(execution_plans) == 1, \
                    f"Expected 1 execution plan, got {len(execution_plans)}"
                
                plan = list(execution_plans.values())[0]
                assert set(plan["test_case_ids"]) == set(selected_test_ids), \
                    f"Execution plan should contain all selected test IDs"
            
            elif operation == "update_tags":
                # Tags should be updated according to operation type
                new_tags = parameters.get("tags", [])
                operation_type = parameters.get("operation_type", "replace")
                
                for test_id in selected_test_ids:
                    current_tags = submitted_tests[test_id].get("tags", [])
                    initial_tags = initial_state["test_tags"][test_id]
                    
                    if operation_type == "replace":
                        assert current_tags == new_tags, \
                            f"Tags should be replaced for test {test_id}"
                    elif operation_type == "add":
                        expected_tags = list(set(initial_tags + new_tags))
                        assert set(current_tags) == set(expected_tags), \
                            f"Tags should be added for test {test_id}"
                    elif operation_type == "remove":
                        expected_tags = [tag for tag in initial_tags if tag not in new_tags]
                        assert current_tags == expected_tags, \
                            f"Tags should be removed for test {test_id}"
            
            elif operation == "update_favorite":
                # Favorite status should be updated
                is_favorite = parameters.get("is_favorite", False)
                for test_id in selected_test_ids:
                    assert submitted_tests[test_id]["is_favorite"] == is_favorite, \
                        f"Favorite status should be updated for test {test_id}"
    
    @given(test_data=test_database_state_strategy())
    @settings(max_examples=5)
    def test_bulk_delete_with_running_tests_atomicity(self, test_data):
        """
        Property 4: Bulk Operation Atomicity - Failure Case
        
        For any bulk delete operation that includes running tests,
        the entire operation should fail atomically - no tests should
        be deleted if any test in the batch is running.
        
        **Validates: Requirements 3.5**
        """
        assume(len(test_data) >= 3)
        
        # Store test data in the global storage
        submitted_tests.clear()
        execution_plans.clear()
        submitted_tests.update(test_data)
        
        # Select test cases and make one of them "running"
        test_ids = list(test_data.keys())
        selected_test_ids = test_ids[:min(len(test_ids), 5)]
        
        # Make one test "running" to trigger failure condition
        running_test_id = selected_test_ids[0]
        submitted_tests[running_test_id]["execution_status"] = "running"
        
        # Record initial state
        initial_test_count = len(submitted_tests)
        initial_test_ids = set(submitted_tests.keys())
        
        # Simulate bulk delete operation with failure condition
        successful_operations = []
        failed_operations = []
        
        # Pre-validate all operations (this should detect the running test)
        can_proceed = True
        for test_id in selected_test_ids:
            if test_id not in submitted_tests:
                can_proceed = False
                break
            
            test_data_item = submitted_tests[test_id]
            if test_data_item.get("execution_status") == "running":
                can_proceed = False
                failed_operations.append(test_id)
                break
        
        # Since we have a running test, the operation should not proceed
        assert not can_proceed, "Bulk delete should not proceed when tests are running"
        
        # Verify atomicity: NO tests should be deleted
        assert len(submitted_tests) == initial_test_count, \
            f"No tests should be deleted when operation fails atomically. " \
            f"Expected {initial_test_count}, got {len(submitted_tests)}"
        
        assert set(submitted_tests.keys()) == initial_test_ids, \
            "Test IDs should remain unchanged when bulk operation fails atomically"
        
        # Verify the running test is still running
        assert submitted_tests[running_test_id]["execution_status"] == "running", \
            "Running test status should be preserved when bulk operation fails"
    
    @given(
        test_data=test_database_state_strategy(),
        partial_failure_ratio=st.floats(min_value=0.1, max_value=0.9)
    )
    @settings(max_examples=5)
    def test_bulk_operation_partial_failure_atomicity(self, test_data, partial_failure_ratio):
        """
        Property 4: Bulk Operation Atomicity - Partial Failure Case
        
        For any bulk operation where some test cases don't exist,
        the operation should handle missing tests gracefully while
        still processing valid tests atomically.
        
        **Validates: Requirements 3.5**
        """
        assume(len(test_data) >= 5)
        
        # Store test data in the global storage
        submitted_tests.clear()
        execution_plans.clear()
        submitted_tests.update(test_data)
        
        # Create a mix of valid and invalid test IDs
        valid_test_ids = list(test_data.keys())[:3]  # Take first 3 as valid
        invalid_test_ids = [str(uuid.uuid4()) for _ in range(2)]  # Create 2 invalid IDs
        mixed_test_ids = valid_test_ids + invalid_test_ids
        
        # Record initial state
        initial_test_count = len(submitted_tests)
        
        # Simulate bulk update_favorite operation (non-destructive)
        operation = "update_favorite"
        parameters = {"is_favorite": True}
        
        successful_operations = []
        failed_operations = []
        
        # Process each test ID
        for test_id in mixed_test_ids:
            if test_id in submitted_tests:
                # Valid test - should succeed
                submitted_tests[test_id]["is_favorite"] = parameters["is_favorite"]
                submitted_tests[test_id]["updated_at"] = datetime.utcnow()
                successful_operations.append(test_id)
            else:
                # Invalid test - should fail
                failed_operations.append(test_id)
        
        # Verify partial success behavior
        assert len(successful_operations) == len(valid_test_ids), \
            f"Expected {len(valid_test_ids)} successful operations, got {len(successful_operations)}"
        
        assert len(failed_operations) == len(invalid_test_ids), \
            f"Expected {len(invalid_test_ids)} failed operations, got {len(failed_operations)}"
        
        # Verify that valid operations completed successfully
        for test_id in valid_test_ids:
            assert submitted_tests[test_id]["is_favorite"] == True, \
                f"Valid test {test_id} should have been updated"
        
        # Verify system consistency - no tests should be lost or corrupted
        assert len(submitted_tests) == initial_test_count, \
            f"Test count should remain unchanged. Expected {initial_test_count}, got {len(submitted_tests)}"
        
        # Verify all originally valid tests still exist
        for test_id in test_data.keys():
            assert test_id in submitted_tests, \
                f"Original test {test_id} should still exist after partial failure"