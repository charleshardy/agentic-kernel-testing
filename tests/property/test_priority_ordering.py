"""Property-based tests for priority ordering in queue monitor.

**Feature: test-execution-orchestrator, Property 8: Priority ordering**
**Validates: Requirements 6.1, 6.2**

Property 8: Priority ordering
For any set of queued execution plans with different priorities, the orchestrator 
should process higher-priority plans before lower-priority ones.
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
    num_tests = draw(st.integers(min_value=1, max_value=5))
    test_case_ids = [str(uuid.uuid4()) for _ in range(num_tests)]
    
    priority = draw(st.integers(min_value=1, max_value=10))  # 1=highest, 10=lowest
    
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
def gen_execution_plans_with_priorities(draw):
    """Generate a list of execution plans with different priorities."""
    plans = draw(st.lists(gen_execution_plan(), min_size=2, max_size=8))
    
    # Ensure we have at least two different priorities
    priorities = [plan['priority'] for plan in plans]
    assume(len(set(priorities)) >= 2)
    
    return plans


def test_priority_ordering_basic():
    """
    Property: For any set of execution plans with different priorities, 
    higher-priority plans (lower numbers) should be retrieved before 
    lower-priority plans (higher numbers).
    
    **Feature: test-execution-orchestrator, Property 8: Priority ordering**
    **Validates: Requirements 6.1, 6.2**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans_dict = {}
    
    # Create test plans with different priorities
    execution_plans = [
        {
            'plan_id': str(uuid.uuid4()),
            'submission_id': str(uuid.uuid4()),
            'test_case_ids': [str(uuid.uuid4())],
            'priority': 5,  # Lower priority
            'status': 'queued',
            'created_at': datetime.now(),
        },
        {
            'plan_id': str(uuid.uuid4()),
            'submission_id': str(uuid.uuid4()),
            'test_case_ids': [str(uuid.uuid4())],
            'priority': 1,  # Higher priority
            'status': 'queued',
            'created_at': datetime.now(),
        },
        {
            'plan_id': str(uuid.uuid4()),
            'submission_id': str(uuid.uuid4()),
            'test_case_ids': [str(uuid.uuid4())],
            'priority': 3,  # Medium priority
            'status': 'queued',
            'created_at': datetime.now(),
        }
    ]
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans_dict
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Add all execution plans to the global dictionary
        for plan_data in execution_plans:
            plan_id = plan_data['plan_id']
            plan_without_id = {k: v for k, v in plan_data.items() if k != 'plan_id'}
            execution_plans_dict[plan_id] = plan_without_id
        
        # Poll should detect all new plans
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == len(execution_plans)
        
        # Retrieve plans in order
        retrieved_plans = []
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None
            retrieved_plans.append(plan)
        
        # Verify priority ordering (lower number = higher priority)
        # Should be: priority 1, then 3, then 5
        assert retrieved_plans[0]['priority'] == 1, f"First plan should have priority 1, got {retrieved_plans[0]['priority']}"
        assert retrieved_plans[1]['priority'] == 3, f"Second plan should have priority 3, got {retrieved_plans[1]['priority']}"
        assert retrieved_plans[2]['priority'] == 5, f"Third plan should have priority 5, got {retrieved_plans[2]['priority']}"
        
        # General ordering check
        for i in range(len(retrieved_plans) - 1):
            current_priority = retrieved_plans[i]['priority']
            next_priority = retrieved_plans[i + 1]['priority']
            
            # Current should have higher or equal priority (lower or equal number)
            assert current_priority <= next_priority, \
                f"Priority ordering violation: plan with priority {current_priority} " \
                f"retrieved before plan with priority {next_priority}"


@given(gen_execution_plans_with_priorities())
@settings(max_examples=50, deadline=None)
def test_priority_ordering_property(execution_plans: List[Dict[str, Any]]):
    """
    Property-based test: For any set of execution plans with different priorities, 
    higher-priority plans (lower numbers) should be retrieved before 
    lower-priority plans (higher numbers).
    
    **Feature: test-execution-orchestrator, Property 8: Priority ordering**
    **Validates: Requirements 6.1, 6.2**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans_dict = {}
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans_dict
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Add all execution plans to the global dictionary
        for plan_data in execution_plans:
            plan_id = plan_data['plan_id']
            plan_without_id = {k: v for k, v in plan_data.items() if k != 'plan_id'}
            execution_plans_dict[plan_id] = plan_without_id
        
        # Poll should detect all new plans
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == len(execution_plans)
        
        # Retrieve plans in order
        retrieved_plans = []
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None
            retrieved_plans.append(plan)
        
        # Verify priority ordering (lower number = higher priority)
        for i in range(len(retrieved_plans) - 1):
            current_priority = retrieved_plans[i]['priority']
            next_priority = retrieved_plans[i + 1]['priority']
            
            # Current should have higher or equal priority (lower or equal number)
            assert current_priority <= next_priority, \
                f"Priority ordering violation: plan with priority {current_priority} " \
                f"retrieved before plan with priority {next_priority}"


@given(
    st.lists(gen_execution_plan(), min_size=1, max_size=3),  # High priority plans
    st.lists(gen_execution_plan(), min_size=1, max_size=3)   # Low priority plans
)
@settings(max_examples=50, deadline=None)
def test_high_priority_before_low_priority(
    high_priority_plans: List[Dict[str, Any]], 
    low_priority_plans: List[Dict[str, Any]]
):
    """
    Property: For any set of high-priority and low-priority execution plans,
    all high-priority plans should be processed before any low-priority plans.
    
    **Feature: test-execution-orchestrator, Property 8: Priority ordering**
    **Validates: Requirements 6.1, 6.2**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans_dict = {}
    
    # Set priorities explicitly
    for plan in high_priority_plans:
        plan['priority'] = 1  # High priority
    for plan in low_priority_plans:
        plan['priority'] = 10  # Low priority
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans_dict
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Add all plans to execution_plans_dict
        all_plans = high_priority_plans + low_priority_plans
        for plan_data in all_plans:
            plan_id = plan_data['plan_id']
            plan_without_id = {k: v for k, v in plan_data.items() if k != 'plan_id'}
            execution_plans_dict[plan_id] = plan_without_id
        
        # Poll should detect all plans
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == len(all_plans)
        
        # Retrieve all plans
        retrieved_plans = []
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None
            retrieved_plans.append(plan)
        
        # Find the last high priority plan and first low priority plan
        last_high_priority_index = -1
        first_low_priority_index = len(retrieved_plans)
        
        for i, plan in enumerate(retrieved_plans):
            if plan['priority'] == 1:  # High priority
                last_high_priority_index = i
            elif plan['priority'] == 10:  # Low priority
                if first_low_priority_index == len(retrieved_plans):
                    first_low_priority_index = i
        
        # Verify all high priority plans come before all low priority plans
        if last_high_priority_index >= 0 and first_low_priority_index < len(retrieved_plans):
            assert last_high_priority_index < first_low_priority_index, \
                f"High priority plan at index {last_high_priority_index} " \
                f"came after low priority plan at index {first_low_priority_index}"


@given(
    st.lists(gen_execution_plan(), min_size=3, max_size=6),
    st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50, deadline=None)
def test_same_priority_fifo_ordering(execution_plans: List[Dict[str, Any]], priority: int):
    """
    Property: For any set of execution plans with the same priority,
    they should be processed in FIFO (first-in-first-out) order.
    
    **Feature: test-execution-orchestrator, Property 8: Priority ordering**
    **Validates: Requirements 6.1, 6.2**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans_dict = {}
    
    # Set same priority for all plans
    for plan in execution_plans:
        plan['priority'] = priority
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans_dict
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Add plans one by one with small delays to ensure different timestamps
        submission_order = []
        for plan in execution_plans:
            plan_id = plan['plan_id']
            plan_without_id = {k: v for k, v in plan.items() if k != 'plan_id'}
            execution_plans_dict[plan_id] = plan_without_id
            submission_order.append(plan_id)
            time.sleep(0.001)  # Small delay to ensure different timestamps
        
        # Poll for new plans
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == len(execution_plans)
        
        # Retrieve all plans
        retrieved_order = []
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None
            retrieved_order.append(plan['plan_id'])
        
        # Verify FIFO ordering for same priority
        assert retrieved_order == submission_order, \
            f"FIFO violation for same priority: submitted {submission_order}, " \
            f"retrieved {retrieved_order}"


@given(gen_execution_plans_with_priorities())
@settings(max_examples=50, deadline=None)
def test_queue_status_reflects_priority_distribution(execution_plans: List[Dict[str, Any]]):
    """
    Property: For any set of queued execution plans, the queue status should
    accurately reflect the distribution of plans across priority levels.
    
    **Feature: test-execution-orchestrator, Property 8: Priority ordering**
    **Validates: Requirements 6.1, 6.2**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans_dict = {}
    
    # Count plans by priority
    priority_counts = {}
    for plan in execution_plans:
        priority = plan['priority']
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans_dict
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Add all plans to execution_plans_dict
        for plan_data in execution_plans:
            plan_id = plan_data['plan_id']
            plan_without_id = {k: v for k, v in plan_data.items() if k != 'plan_id'}
            execution_plans_dict[plan_id] = plan_without_id
        
        # Get queue status
        status = monitor.get_queue_status()
        
        # Verify total plan count
        assert status['total_plans'] == len(execution_plans), \
            f"Expected {len(execution_plans)} total plans, got {status['total_plans']}"
        
        # Verify priority distribution in queue details
        queue_priorities = [detail['priority'] for detail in status['queue_details']]
        actual_priority_counts = {}
        for priority in queue_priorities:
            actual_priority_counts[priority] = actual_priority_counts.get(priority, 0) + 1
        
        assert actual_priority_counts == priority_counts, \
            f"Priority distribution mismatch: expected {priority_counts}, " \
            f"got {actual_priority_counts}"
        
        # Verify queue details are sorted by priority (highest first = lowest number first)
        queue_details = status['queue_details']
        for i in range(len(queue_details) - 1):
            current_priority = queue_details[i]['priority']
            next_priority = queue_details[i + 1]['priority']
            assert current_priority <= next_priority, \
                f"Queue details not sorted by priority: {current_priority} before {next_priority}"


@given(st.lists(gen_execution_plan(), min_size=2, max_size=4))
@settings(max_examples=10, deadline=None)
def test_fifo_equal_priority_property(execution_plans: List[Dict[str, Any]]):
    """
    Property 9: FIFO for equal priority
    For any set of execution plans with equal priority, they should be processed 
    in first-in-first-out (FIFO) order based on submission time.
    
    **Feature: test-execution-orchestrator, Property 9: FIFO for equal priority**
    **Validates: Requirements 6.3**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans_dict = {}
    
    # Set all plans to the same priority
    equal_priority = 5  # Use middle priority
    for plan in execution_plans:
        plan['priority'] = equal_priority
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans_dict
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Add plans one by one with small delays to ensure different timestamps
        # This simulates real-world submission timing
        submission_order = []
        for i, plan in enumerate(execution_plans):
            plan_id = plan['plan_id']
            plan_without_id = {k: v for k, v in plan.items() if k != 'plan_id'}
            
            # Add timestamp to track submission order
            plan_without_id['submitted_at'] = datetime.now()
            
            execution_plans_dict[plan_id] = plan_without_id
            submission_order.append(plan_id)
            
            # Small delay to ensure different timestamps
            time.sleep(0.001)
        
        # Poll for new plans - this should detect all plans and queue them
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == len(execution_plans), \
            f"Expected {len(execution_plans)} new plans, got {len(new_plans)}"
        
        # Retrieve all plans in the order they would be processed
        retrieval_order = []
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None, "Expected to retrieve a plan but got None"
            
            # Verify this plan has the expected priority
            assert plan['priority'] == equal_priority, \
                f"Expected priority {equal_priority}, got {plan['priority']}"
            
            retrieval_order.append(plan['plan_id'])
        
        # Property: For equal priority plans, retrieval order should match submission order (FIFO)
        assert retrieval_order == submission_order, \
            f"FIFO violation for equal priority plans: " \
            f"submitted in order {submission_order}, " \
            f"but retrieved in order {retrieval_order}"


@given(
    st.integers(min_value=1, max_value=10),  # priority level
    st.integers(min_value=2, max_value=6)    # number of plans
)
@settings(max_examples=100, deadline=None)
def test_fifo_equal_priority_with_random_priority(priority_level: int, num_plans: int):
    """
    Property 9: FIFO for equal priority (with random priority levels)
    For any priority level and any number of execution plans with that same priority,
    they should be processed in FIFO order.
    
    **Feature: test-execution-orchestrator, Property 9: FIFO for equal priority**
    **Validates: Requirements 6.3**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans_dict = {}
    
    # Generate plans with the same priority
    execution_plans = []
    for i in range(num_plans):
        plan = {
            'plan_id': str(uuid.uuid4()),
            'submission_id': str(uuid.uuid4()),
            'test_case_ids': [str(uuid.uuid4())],
            'priority': priority_level,
            'status': 'queued',
            'created_at': datetime.now(),
            'hardware_requirements': {
                'architecture': 'x86_64',
                'memory_mb': 1024,
                'cpu_cores': 2
            }
        }
        execution_plans.append(plan)
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans_dict
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Submit plans sequentially with timestamps
        submission_order = []
        for plan in execution_plans:
            plan_id = plan['plan_id']
            plan_without_id = {k: v for k, v in plan.items() if k != 'plan_id'}
            
            execution_plans_dict[plan_id] = plan_without_id
            submission_order.append(plan_id)
            
            # Ensure different timestamps for FIFO ordering
            time.sleep(0.001)
        
        # Poll and retrieve all plans
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == num_plans
        
        retrieval_order = []
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None
            assert plan['priority'] == priority_level
            retrieval_order.append(plan['plan_id'])
        
        # Verify FIFO ordering
        assert retrieval_order == submission_order, \
            f"FIFO violation for priority {priority_level}: " \
            f"submitted {submission_order}, retrieved {retrieval_order}"


@given(
    st.lists(gen_execution_plan(), min_size=2, max_size=4),  # Equal priority group 1
    st.lists(gen_execution_plan(), min_size=2, max_size=4),  # Equal priority group 2
    st.integers(min_value=1, max_value=5),                   # Priority for group 1
    st.integers(min_value=6, max_value=10)                   # Priority for group 2
)
@settings(max_examples=50, deadline=None)
def test_fifo_within_priority_groups(
    group1_plans: List[Dict[str, Any]], 
    group2_plans: List[Dict[str, Any]],
    group1_priority: int,
    group2_priority: int
):
    """
    Property 9: FIFO for equal priority (within priority groups)
    For any two groups of execution plans with different priorities,
    plans within each group should maintain FIFO order, and higher
    priority group should be processed before lower priority group.
    
    **Feature: test-execution-orchestrator, Property 9: FIFO for equal priority**
    **Validates: Requirements 6.3**
    """
    # Setup
    config = OrchestratorConfig()
    monitor = QueueMonitor(config)
    execution_plans_dict = {}
    
    # Set priorities for each group
    for plan in group1_plans:
        plan['priority'] = group1_priority
    for plan in group2_plans:
        plan['priority'] = group2_priority
    
    # Mock the execution_plans module
    mock_tests_module = MagicMock()
    mock_tests_module.execution_plans = execution_plans_dict
    
    with patch.dict('sys.modules', {
        'api': MagicMock(),
        'api.routers': MagicMock(),
        'api.routers.tests': mock_tests_module
    }):
        # Submit all plans with interleaved timing to test priority vs FIFO
        all_plans = []
        group1_submission_order = []
        group2_submission_order = []
        
        # Interleave submissions from both groups
        max_len = max(len(group1_plans), len(group2_plans))
        for i in range(max_len):
            if i < len(group1_plans):
                plan = group1_plans[i]
                plan_id = plan['plan_id']
                plan_without_id = {k: v for k, v in plan.items() if k != 'plan_id'}
                execution_plans_dict[plan_id] = plan_without_id
                group1_submission_order.append(plan_id)
                all_plans.append((plan_id, group1_priority))
                time.sleep(0.001)
            
            if i < len(group2_plans):
                plan = group2_plans[i]
                plan_id = plan['plan_id']
                plan_without_id = {k: v for k, v in plan.items() if k != 'plan_id'}
                execution_plans_dict[plan_id] = plan_without_id
                group2_submission_order.append(plan_id)
                all_plans.append((plan_id, group2_priority))
                time.sleep(0.001)
        
        # Poll and retrieve all plans
        new_plans = monitor.poll_for_new_plans()
        assert len(new_plans) == len(group1_plans) + len(group2_plans)
        
        retrieval_order = []
        while monitor.get_queued_plan_count() > 0:
            plan = monitor.get_next_execution_plan()
            assert plan is not None
            retrieval_order.append((plan['plan_id'], plan['priority']))
        
        # Separate retrieved plans by priority
        group1_retrieved = [plan_id for plan_id, priority in retrieval_order if priority == group1_priority]
        group2_retrieved = [plan_id for plan_id, priority in retrieval_order if priority == group2_priority]
        
        # Verify FIFO within each priority group
        assert group1_retrieved == group1_submission_order, \
            f"FIFO violation in group 1 (priority {group1_priority}): " \
            f"submitted {group1_submission_order}, retrieved {group1_retrieved}"
        
        assert group2_retrieved == group2_submission_order, \
            f"FIFO violation in group 2 (priority {group2_priority}): " \
            f"submitted {group2_submission_order}, retrieved {group2_retrieved}"
        
        # Verify priority ordering between groups (lower number = higher priority)
        if group1_priority < group2_priority:
            # Group 1 should come before Group 2
            last_group1_index = max([i for i, (_, priority) in enumerate(retrieval_order) if priority == group1_priority])
            first_group2_index = min([i for i, (_, priority) in enumerate(retrieval_order) if priority == group2_priority])
            assert last_group1_index < first_group2_index, \
                f"Priority violation: group 1 (priority {group1_priority}) should come before group 2 (priority {group2_priority})"
        elif group2_priority < group1_priority:
            # Group 2 should come before Group 1
            last_group2_index = max([i for i, (_, priority) in enumerate(retrieval_order) if priority == group2_priority])
            first_group1_index = min([i for i, (_, priority) in enumerate(retrieval_order) if priority == group1_priority])
            assert last_group2_index < first_group1_index, \
                f"Priority violation: group 2 (priority {group2_priority}) should come before group 1 (priority {group1_priority})"