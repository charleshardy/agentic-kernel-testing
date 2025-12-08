"""Property-based tests for queue prioritization.

**Feature: agentic-kernel-testing, Property 25: Queue prioritization correctness**
**Validates: Requirements 5.5**

Property 25: Queue prioritization correctness
For any set of queued test runs, the execution order should respect both code change 
impact scores and developer-specified priority levels.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import List
import time

from ai_generator.models import (
    TestCase, TestType, HardwareConfig, ExpectedOutcome, Environment,
    EnvironmentStatus
)
from orchestrator.scheduler import TestOrchestrator, Priority, TestJob


# Custom strategies for generating test data
@st.composite
def gen_hardware_config(draw):
    """Generate a random hardware configuration."""
    architecture = draw(st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']))
    cpu_model = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    memory_mb = draw(st.integers(min_value=512, max_value=8192))
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=cpu_model,
        memory_mb=memory_mb,
        storage_type='ssd',
        peripherals=[],
        is_virtual=True,
        emulator='qemu'
    )


@st.composite
def gen_test_case(draw):
    """Generate a random test case."""
    test_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    subsystem = draw(st.sampled_from(['fs', 'net', 'mm', 'sched', 'drivers', 'kernel']))
    test_type = draw(st.sampled_from(list(TestType)))
    
    return TestCase(
        id=test_id,
        name=name,
        description=f"Test for {subsystem}",
        test_type=test_type,
        target_subsystem=subsystem,
        code_paths=[],
        execution_time_estimate=draw(st.integers(min_value=10, max_value=300)),
        test_script="#!/bin/bash\nexit 0",
        expected_outcome=ExpectedOutcome()
    )


@st.composite
def gen_environment(draw):
    """Generate a random environment."""
    config = draw(gen_hardware_config())
    env_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return Environment(
        id=env_id,
        config=config,
        status=EnvironmentStatus.IDLE,
        created_at=datetime.now(),
        last_used=datetime.now()
    )


@given(
    st.lists(
        st.tuples(
            gen_test_case(),
            st.sampled_from(list(Priority)),
            st.floats(min_value=0.0, max_value=1.0)
        ),
        min_size=2,
        max_size=20
    )
)
@settings(max_examples=100, deadline=None)
def test_priority_ordering(test_data: List[tuple]):
    """
    Property: For any set of test jobs with different priorities, jobs with higher
    priority should be scheduled before jobs with lower priority.
    
    **Feature: agentic-kernel-testing, Property 25: Queue prioritization correctness**
    **Validates: Requirements 5.5**
    """
    orchestrator = TestOrchestrator()
    
    # Submit all jobs
    job_ids = []
    job_priorities = {}
    
    for test_case, priority, impact_score in test_data:
        job_id = orchestrator.submit_job(test_case, priority, impact_score)
        job_ids.append(job_id)
        job_priorities[job_id] = priority
    
    # Extract jobs from queue (without executing)
    scheduled_order = []
    with orchestrator._lock:
        # Make a copy of the queue to inspect order
        import heapq
        queue_copy = orchestrator._job_queue.copy()
        
        while queue_copy:
            job = heapq.heappop(queue_copy)
            scheduled_order.append(job)
    
    # Verify priority ordering
    for i in range(len(scheduled_order) - 1):
        current_job = scheduled_order[i]
        next_job = scheduled_order[i + 1]
        
        # Current job should have >= priority than next job
        assert current_job.priority >= next_job.priority, \
            f"Priority violation: job {current_job.id} (priority {current_job.priority}) " \
            f"scheduled before job {next_job.id} (priority {next_job.priority})"


@given(
    st.lists(
        st.tuples(
            gen_test_case(),
            st.floats(min_value=0.0, max_value=1.0)
        ),
        min_size=2,
        max_size=20
    )
)
@settings(max_examples=100, deadline=None)
def test_impact_score_ordering_same_priority(test_data: List[tuple]):
    """
    Property: For any set of test jobs with the same priority, jobs with higher
    impact scores should be scheduled before jobs with lower impact scores.
    
    **Feature: agentic-kernel-testing, Property 25: Queue prioritization correctness**
    **Validates: Requirements 5.5**
    """
    orchestrator = TestOrchestrator()
    
    # Use same priority for all jobs
    priority = Priority.MEDIUM
    
    # Submit all jobs
    job_ids = []
    job_impact_scores = {}
    
    for test_case, impact_score in test_data:
        job_id = orchestrator.submit_job(test_case, priority, impact_score)
        job_ids.append(job_id)
        job_impact_scores[job_id] = impact_score
    
    # Extract jobs from queue
    scheduled_order = []
    with orchestrator._lock:
        import heapq
        queue_copy = orchestrator._job_queue.copy()
        
        while queue_copy:
            job = heapq.heappop(queue_copy)
            scheduled_order.append(job)
    
    # Verify impact score ordering (for same priority)
    for i in range(len(scheduled_order) - 1):
        current_job = scheduled_order[i]
        next_job = scheduled_order[i + 1]
        
        # Since all have same priority, impact score should be non-increasing
        assert current_job.impact_score >= next_job.impact_score - 0.001, \
            f"Impact score violation: job {current_job.id} (impact {current_job.impact_score}) " \
            f"scheduled before job {next_job.id} (impact {next_job.impact_score})"


@given(
    st.lists(gen_test_case(), min_size=3, max_size=10),
    st.lists(st.sampled_from(list(Priority)), min_size=3, max_size=10),
    st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=3, max_size=10)
)
@settings(max_examples=100, deadline=None)
def test_combined_priority_and_impact(
    test_cases: List[TestCase],
    priorities: List[Priority],
    impact_scores: List[float]
):
    """
    Property: For any set of test jobs, the execution order should respect both
    priority (primary) and impact score (secondary) ordering.
    
    **Feature: agentic-kernel-testing, Property 25: Queue prioritization correctness**
    **Validates: Requirements 5.5**
    """
    # Ensure all lists have same length
    min_len = min(len(test_cases), len(priorities), len(impact_scores))
    assume(min_len >= 3)
    
    test_cases = test_cases[:min_len]
    priorities = priorities[:min_len]
    impact_scores = impact_scores[:min_len]
    
    orchestrator = TestOrchestrator()
    
    # Submit all jobs
    for test_case, priority, impact_score in zip(test_cases, priorities, impact_scores):
        orchestrator.submit_job(test_case, priority, impact_score)
    
    # Extract jobs from queue
    scheduled_order = []
    with orchestrator._lock:
        import heapq
        queue_copy = orchestrator._job_queue.copy()
        
        while queue_copy:
            job = heapq.heappop(queue_copy)
            scheduled_order.append(job)
    
    # Verify ordering respects priority first, then impact score
    for i in range(len(scheduled_order) - 1):
        current_job = scheduled_order[i]
        next_job = scheduled_order[i + 1]
        
        # If priorities differ, current should be higher
        if current_job.priority != next_job.priority:
            assert current_job.priority > next_job.priority, \
                f"Priority violation at position {i}"
        else:
            # If priorities are same, impact score should be non-increasing
            assert current_job.impact_score >= next_job.impact_score - 0.001, \
                f"Impact score violation at position {i} with same priority"


@given(
    st.lists(gen_test_case(), min_size=2, max_size=10),
    st.sampled_from(list(Priority))
)
@settings(max_examples=100, deadline=None)
def test_fifo_ordering_same_priority_and_impact(
    test_cases: List[TestCase],
    priority: Priority
):
    """
    Property: For any set of test jobs with the same priority and impact score,
    jobs should be scheduled in FIFO order (first submitted, first scheduled).
    
    **Feature: agentic-kernel-testing, Property 25: Queue prioritization correctness**
    **Validates: Requirements 5.5**
    """
    orchestrator = TestOrchestrator()
    
    # Use same priority and impact score for all
    impact_score = 0.5
    
    # Submit jobs with small delays to ensure different timestamps
    submission_order = []
    for test_case in test_cases:
        job_id = orchestrator.submit_job(test_case, priority, impact_score)
        submission_order.append(job_id)
        time.sleep(0.001)  # Small delay to ensure different timestamps
    
    # Extract jobs from queue
    scheduled_order = []
    with orchestrator._lock:
        import heapq
        queue_copy = orchestrator._job_queue.copy()
        
        while queue_copy:
            job = heapq.heappop(queue_copy)
            scheduled_order.append(job.id)
    
    # Verify FIFO ordering
    assert scheduled_order == submission_order, \
        f"FIFO violation: submitted {submission_order}, scheduled {scheduled_order}"


@given(
    st.lists(
        st.tuples(
            gen_test_case(),
            st.sampled_from(list(Priority)),
            st.floats(min_value=0.0, max_value=1.0)
        ),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=100, deadline=None)
def test_queue_status_reflects_priorities(test_data: List[tuple]):
    """
    Property: For any set of queued jobs, the queue status should accurately
    reflect the number of pending jobs at each priority level.
    
    **Feature: agentic-kernel-testing, Property 25: Queue prioritization correctness**
    **Validates: Requirements 5.5**
    """
    orchestrator = TestOrchestrator()
    
    # Count jobs by priority
    priority_counts = {p: 0 for p in Priority}
    
    # Submit all jobs
    for test_case, priority, impact_score in test_data:
        orchestrator.submit_job(test_case, priority, impact_score)
        priority_counts[priority] += 1
    
    # Get queue status
    status = orchestrator.get_queue_status()
    
    # Verify total pending jobs
    assert status['pending_jobs'] == len(test_data), \
        f"Expected {len(test_data)} pending jobs, got {status['pending_jobs']}"
    
    # Verify jobs are in queue
    with orchestrator._lock:
        queue_priorities = [job.priority for job in orchestrator._job_queue]
        
        for priority, expected_count in priority_counts.items():
            actual_count = queue_priorities.count(priority)
            assert actual_count == expected_count, \
                f"Priority {priority}: expected {expected_count} jobs, got {actual_count}"
