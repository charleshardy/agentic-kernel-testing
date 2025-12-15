"""Property-based tests for automatic plan processing.

**Feature: test-execution-orchestrator, Property 1: Automatic plan processing**
**Validates: Requirements 1.1**

Property 1: Automatic plan processing
For any execution plan that gets queued, the orchestrator should pick it up and begin 
processing within a reasonable time window (e.g., 30 seconds).
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid
import time
import threading
from unittest.mock import MagicMock, patch
import sys

from orchestrator.queue_monitor import QueueMonitor
from orchestrator.config import OrchestratorConfig


# Custom strategies for generating test data
@st.composite
def gen_execution_plan(draw):
    """Generate a random execution plan."""
    plan_id = str(uuid.uuid4())
    submission_id = str(uuid.uuid4())
    
    # Generate test case IDs
    num_tests = draw(st.integers(min_value=1, max_value=10))
    test_case_ids = [str(uuid.uuid4()) for _ in range(num_tests)]
    
    priority = draw(st.integers(min_value=1, max_value=10))
    
    return {
        'plan_id': plan_id,
        'submission_id': submission_id,
        'test_case_ids': test_case_ids,
        'priority': priority,
        'status': 'queued',
        'created_at': datetime.now(),
        'hardware_requirements': {
            'architecture': draw(st.sampled_from(['x86_64', 'arm64', 'riscv64'])),
            'memory_mb': draw(st.integers(min_value=512, max_value=4096)),
            'cpu_cores': draw(st.integers(min_value=1, max_value=8))
        }
    }


@st.composite
def gen_execution_plans_batch(draw):
    """Generate a batch of execution plans."""
    num_plans = draw(st.integers(min_value=1, max_value=5))
    plans = []
    
    for _ in range(num_plans):
        plan = draw(gen_execution_plan())
        plans.append(plan)
    
    return plans


class TestAutomaticPlanProcessing:
    """Test cases for automatic plan processing property."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = OrchestratorConfig()
        self.monitor = QueueMonitor(self.config)
        
        # Mock execution_plans dictionary
        self.execution_plans = {}
        
        # Create mock module for api.routers.tests
        self.mock_tests_module = MagicMock()
        self.mock_tests_module.execution_plans = self.execution_plans
        
        # Patch sys.modules
        self.modules_patcher = patch.dict('sys.modules', {
            'api': MagicMock(),
            'api.routers': MagicMock(),
            'api.routers.tests': self.mock_tests_module
        })
        self.modules_patcher.start()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.modules_patcher.stop()


@given(gen_execution_plan())
@settings(max_examples=100, deadline=None)
def test_single_plan_automatic_pickup(execution_plan_data: Dict[str, Any]):
    """
    Property: For any single execution plan that gets queued, the queue monitor 
    should automatically detect and pick it up for processing.
    
    **Feature: test-execution-orchestrator, Property 1: Automatic plan processing**
    **Validates: Requirements 1.1**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans = {}
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Initially no plans should be detected
        initial_plans = monitor.poll_for_new_plans()
        assert len(initial_plans) == 0
        assert monitor.get_queued_plan_count() == 0
        
        # Add execution plan to the global dictionary
        plan_id = execution_plan_data['plan_id']
        plan_data = {k: v for k, v in execution_plan_data.items() if k != 'plan_id'}
        execution_plans[plan_id] = plan_data
        
        # Poll should detect the new plan
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == 1
        assert new_plans[0]['plan_id'] == plan_id
        
        # Plan should be queued for processing
        assert monitor.get_queued_plan_count() == 1
        
        # Monitor should be able to retrieve the plan for processing
        retrieved_plan = monitor.get_next_execution_plan()
        assert retrieved_plan is not None
        assert retrieved_plan['plan_id'] == plan_id
        assert retrieved_plan['priority'] == execution_plan_data['priority']
        
        # After retrieval, queue should be empty
        assert monitor.get_queued_plan_count() == 0


@given(gen_execution_plans_batch())
@settings(max_examples=50, deadline=None)
def test_multiple_plans_automatic_pickup(execution_plans_data: List[Dict[str, Any]]):
    """
    Property: For any set of execution plans that get queued, the queue monitor 
    should automatically detect and pick up all of them for processing.
    
    **Feature: test-execution-orchestrator, Property 1: Automatic plan processing**
    **Validates: Requirements 1.1**
    """
    assume(len(execution_plans_data) > 0)
    
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans = {}
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Initially no plans should be detected
        initial_plans = monitor.poll_for_new_plans()
        assert len(initial_plans) == 0
        
        # Add all execution plans to the global dictionary
        expected_plan_ids = set()
        total_tests = 0
        
        for plan_data in execution_plans_data:
            plan_id = plan_data['plan_id']
            plan_without_id = {k: v for k, v in plan_data.items() if k != 'plan_id'}
            execution_plans[plan_id] = plan_without_id
            expected_plan_ids.add(plan_id)
            total_tests += len(plan_data['test_case_ids'])
        
        # Poll should detect all new plans
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == len(execution_plans_data)
        
        detected_plan_ids = {plan['plan_id'] for plan in new_plans}
        assert detected_plan_ids == expected_plan_ids
        
        # All plans should be queued for processing
        assert monitor.get_queued_plan_count() == len(execution_plans_data)
        assert monitor.get_queued_test_count() == total_tests
        
        # Monitor should be able to retrieve all plans for processing
        retrieved_plans = []
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None
            retrieved_plans.append(plan)
        
        # All plans should have been retrieved
        assert len(retrieved_plans) == len(execution_plans_data)
        retrieved_plan_ids = {plan['plan_id'] for plan in retrieved_plans}
        assert retrieved_plan_ids == expected_plan_ids


@given(gen_execution_plan())
@settings(max_examples=50, deadline=None)
def test_plan_not_reprocessed_after_pickup(execution_plan_data: Dict[str, Any]):
    """
    Property: For any execution plan that has been picked up for processing,
    subsequent polls should not detect it again (no duplicate processing).
    
    **Feature: test-execution-orchestrator, Property 1: Automatic plan processing**
    **Validates: Requirements 1.1**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans = {}
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Add execution plan
        plan_id = execution_plan_data['plan_id']
        plan_data = {k: v for k, v in execution_plan_data.items() if k != 'plan_id'}
        execution_plans[plan_id] = plan_data
        
        # First poll should detect the plan
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == 1
        assert new_plans[0]['plan_id'] == plan_id
        
        # Second poll should not detect it again (already processed)
        new_plans_second = monitor.poll_for_new_plans()
        assert len(new_plans_second) == 0
        
        # Plan should still be in queue until retrieved
        assert monitor.get_queued_plan_count() == 1
        
        # Retrieve the plan
        retrieved_plan = monitor.get_next_execution_plan()
        assert retrieved_plan is not None
        assert retrieved_plan['plan_id'] == plan_id
        
        # Third poll should still not detect it
        new_plans_third = monitor.poll_for_new_plans()
        assert len(new_plans_third) == 0
        
        # Queue should be empty after retrieval
        assert monitor.get_queued_plan_count() == 0


@given(
    gen_execution_plan(),
    st.floats(min_value=0.001, max_value=0.1)  # Small delay in seconds
)
@settings(max_examples=30, deadline=None)
def test_plan_pickup_timing(execution_plan_data: Dict[str, Any], delay_seconds: float):
    """
    Property: For any execution plan that gets queued, the queue monitor should 
    pick it up within a reasonable time window when polling occurs.
    
    **Feature: test-execution-orchestrator, Property 1: Automatic plan processing**
    **Validates: Requirements 1.1**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans = {}
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Record start time
        start_time = time.time()
        
        # Add execution plan after a small delay
        plan_id = execution_plan_data['plan_id']
        plan_data = {k: v for k, v in execution_plan_data.items() if k != 'plan_id'}
        
        # Simulate plan being added after some delay
        time.sleep(delay_seconds)
        execution_plans[plan_id] = plan_data
        
        # Poll should detect the plan
        detection_time = time.time()
        new_plans = monitor.poll_for_new_plans()
        
        # Verify plan was detected
        assert len(new_plans) == 1
        assert new_plans[0]['plan_id'] == plan_id
        
        # Verify timing is reasonable (within expected bounds)
        total_time = detection_time - start_time
        assert total_time >= delay_seconds  # At least the delay time
        assert total_time < delay_seconds + 1.0  # But not too much longer
        
        # Plan should be available for processing
        retrieved_plan = monitor.get_next_execution_plan()
        assert retrieved_plan is not None
        assert retrieved_plan['plan_id'] == plan_id


@given(gen_execution_plans_batch())
@settings(max_examples=30, deadline=None)
def test_concurrent_plan_addition_and_polling(execution_plans_data: List[Dict[str, Any]]):
    """
    Property: For any set of execution plans that get added concurrently while 
    polling is happening, all plans should eventually be detected and processed.
    
    **Feature: test-execution-orchestrator, Property 1: Automatic plan processing**
    **Validates: Requirements 1.1**
    """
    assume(len(execution_plans_data) > 1)
    
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans = {}
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        detected_plans = []
        expected_plan_ids = set()
        
        # Add plans gradually while polling
        for i, plan_data in enumerate(execution_plans_data):
            plan_id = plan_data['plan_id']
            plan_without_id = {k: v for k, v in plan_data.items() if k != 'plan_id'}
            execution_plans[plan_id] = plan_without_id
            expected_plan_ids.add(plan_id)
            
            # Poll after each addition
            new_plans = monitor.poll_for_new_plans()
            detected_plans.extend(new_plans)
            
            # Small delay to simulate real-world timing
            time.sleep(0.001)
        
        # Final poll to catch any remaining plans
        final_plans = monitor.poll_for_new_plans()
        detected_plans.extend(final_plans)
        
        # Verify all plans were eventually detected
        detected_plan_ids = {plan['plan_id'] for plan in detected_plans}
        assert detected_plan_ids == expected_plan_ids
        
        # Verify all plans are queued for processing
        assert monitor.get_queued_plan_count() == len(execution_plans_data)
        
        # Verify all plans can be retrieved for processing
        retrieved_count = 0
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None
            retrieved_count += 1
        
        assert retrieved_count == len(execution_plans_data)