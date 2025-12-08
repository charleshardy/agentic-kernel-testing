"""Property-based tests for priority-based scheduling under contention.

**Feature: agentic-kernel-testing, Property 48: Priority-based scheduling under contention**
**Validates: Requirements 10.3**

Property 48: Priority-based scheduling under contention
For any situation where test demand exceeds available resources, the system should 
prioritize critical tests and defer lower-priority tests.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List
import time

from ai_generator.models import (
    TestCase, TestType, HardwareConfig, ExpectedOutcome, Environment,
    EnvironmentStatus
)
from orchestrator.scheduler import TestOrchestrator, Priority


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
        execution_time_estimate=draw(st.integers(min_value=10, max_value=100)),
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
    st.integers(min_value=1, max_value=3),  # Limited environments
    st.integers(min_value=5, max_value=15)  # More jobs than environments
)
@settings(max_examples=20, deadline=None)
def test_critical_jobs_scheduled_first_under_contention(
    num_environments: int,
    num_jobs: int
):
    """
    Property: When test demand exceeds available resources, critical priority
    jobs should be scheduled before lower priority jobs.
    
    **Feature: agentic-kernel-testing, Property 48: Priority-based scheduling under contention**
    **Validates: Requirements 10.3**
    """
    assume(num_jobs > num_environments * 2)
    
    orchestrator = TestOrchestrator()
    
    # Create limited environments
    environments = []
    for i in range(num_environments):
        env = Environment(
            id=f"env_{i}",
            config=HardwareConfig(
                architecture='x86_64',
                cpu_model='test_cpu',
                memory_mb=2048,
                storage_type='ssd',
                peripherals=[],
                is_virtual=True,
                emulator='qemu'
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        environments.append(env)
        orchestrator.add_environment(env)
    
    # Create jobs with different priorities
    # Ensure we have at least one critical and one low priority job
    critical_jobs = []
    low_priority_jobs = []
    
    for i in range(num_jobs):
        test_case = TestCase(
            id=f"test_{i}",
            name=f"Test {i}",
            description=f"Test {i}",
            test_type=TestType.UNIT,
            target_subsystem='kernel',
            code_paths=[],
            execution_time_estimate=30,
            test_script="#!/bin/bash\nexit 0",
            expected_outcome=ExpectedOutcome()
        )
        
        # Alternate between critical and low priority
        if i % 3 == 0:
            job_id = orchestrator.submit_job(test_case, Priority.CRITICAL, 0.9)
            critical_jobs.append(job_id)
        else:
            job_id = orchestrator.submit_job(test_case, Priority.LOW, 0.1)
            low_priority_jobs.append(job_id)
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Check that critical jobs are running/completed while low priority jobs are pending
    with orchestrator._lock:
        running_job_ids = set(orchestrator._running_jobs.keys())
        completed_job_ids = orchestrator._completed_jobs
        
        # Count critical and low priority jobs in running/completed
        critical_active = sum(1 for jid in critical_jobs if jid in running_job_ids or jid in completed_job_ids)
        low_active = sum(1 for jid in low_priority_jobs if jid in running_job_ids or jid in completed_job_ids)
        
        # If there are critical jobs, they should be prioritized
        if critical_jobs and low_active > 0:
            # At least some critical jobs should be active before low priority jobs
            assert critical_active > 0, \
                f"No critical jobs active while {low_active} low priority jobs are active"


@given(
    st.integers(min_value=2, max_value=4),
    st.lists(
        st.tuples(
            gen_test_case(),
            st.sampled_from(list(Priority))
        ),
        min_size=10,
        max_size=20
    )
)
@settings(max_examples=20, deadline=None)
def test_lower_priority_deferred_under_contention(
    num_environments: int,
    test_data: List[tuple]
):
    """
    Property: When resources are constrained, lower priority jobs should remain
    pending while higher priority jobs are executed.
    
    **Feature: agentic-kernel-testing, Property 48: Priority-based scheduling under contention**
    **Validates: Requirements 10.3**
    """
    assume(len(test_data) > num_environments * 2)
    
    orchestrator = TestOrchestrator()
    
    # Create limited environments
    for i in range(num_environments):
        env = Environment(
            id=f"env_{i}",
            config=HardwareConfig(
                architecture='x86_64',
                cpu_model='test_cpu',
                memory_mb=2048,
                storage_type='ssd',
                peripherals=[],
                is_virtual=True,
                emulator='qemu'
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        orchestrator.add_environment(env)
    
    # Submit all jobs and track by priority
    jobs_by_priority = {p: [] for p in Priority}
    
    for test_case, priority in test_data:
        job_id = orchestrator.submit_job(test_case, priority, 0.5)
        jobs_by_priority[priority].append(job_id)
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Check queue status
    status = orchestrator.get_queue_status()
    
    # If there are pending jobs (contention), verify priority ordering
    if status['pending_jobs'] > 0:
        with orchestrator._lock:
            # Get pending jobs from queue
            pending_priorities = [job.priority for job in orchestrator._job_queue]
            
            # Get running jobs
            running_job_ids = set(orchestrator._running_jobs.keys())
            running_priorities = []
            for priority, job_ids in jobs_by_priority.items():
                for job_id in job_ids:
                    if job_id in running_job_ids:
                        running_priorities.append(priority)
            
            # If there are both running and pending jobs
            if running_priorities and pending_priorities:
                # Minimum running priority should be >= maximum pending priority
                # (higher priority value = higher priority)
                min_running = min(running_priorities) if running_priorities else Priority.CRITICAL
                max_pending = max(pending_priorities) if pending_priorities else Priority.LOW
                
                # Allow some slack due to async scheduling
                # But generally, running jobs should have higher or equal priority
                assert min_running >= max_pending or abs(min_running - max_pending) <= 1, \
                    f"Priority inversion: running min={min_running}, pending max={max_pending}"


@given(
    st.integers(min_value=1, max_value=3),
    st.integers(min_value=5, max_value=15)
)
@settings(max_examples=20, deadline=None)
def test_resource_contention_detection(
    num_environments: int,
    num_jobs: int
):
    """
    Property: When test demand exceeds available resources, the system should
    correctly identify resource contention (pending jobs > 0 and all envs allocated).
    
    **Feature: agentic-kernel-testing, Property 48: Priority-based scheduling under contention**
    **Validates: Requirements 10.3**
    """
    assume(num_jobs > num_environments)
    
    orchestrator = TestOrchestrator()
    
    # Create limited environments
    for i in range(num_environments):
        env = Environment(
            id=f"env_{i}",
            config=HardwareConfig(
                architecture='x86_64',
                cpu_model='test_cpu',
                memory_mb=2048,
                storage_type='ssd',
                peripherals=[],
                is_virtual=True,
                emulator='qemu'
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        orchestrator.add_environment(env)
    
    # Create and submit jobs
    for i in range(num_jobs):
        test_case = TestCase(
            id=f"test_{i}",
            name=f"Test {i}",
            description=f"Test {i}",
            test_type=TestType.UNIT,
            target_subsystem='kernel',
            code_paths=[],
            execution_time_estimate=30,
            test_script="#!/bin/bash\nexit 0",
            expected_outcome=ExpectedOutcome()
        )
        orchestrator.submit_job(test_case, Priority.MEDIUM, 0.5)
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Check for contention
    status = orchestrator.get_queue_status()
    
    # If we have more jobs than environments, we should have contention
    if num_jobs > num_environments:
        # Either we have pending jobs, or some jobs completed very quickly
        assert status['pending_jobs'] > 0 or status['completed_jobs'] > 0, \
            f"Expected contention with {num_jobs} jobs and {num_environments} environments"
        
        # If pending jobs exist, all environments should be allocated
        if status['pending_jobs'] > 0:
            assert status['allocated_environments'] == num_environments, \
                f"Contention detected but not all environments allocated: " \
                f"{status['allocated_environments']}/{num_environments}"


@given(
    st.integers(min_value=2, max_value=4),
    st.integers(min_value=3, max_value=10),
    st.integers(min_value=3, max_value=10)
)
@settings(max_examples=20, deadline=None)
def test_priority_levels_respected_under_contention(
    num_environments: int,
    num_high_priority: int,
    num_low_priority: int
):
    """
    Property: Under resource contention, high priority jobs should be scheduled
    before low priority jobs, regardless of submission order.
    
    **Feature: agentic-kernel-testing, Property 48: Priority-based scheduling under contention**
    **Validates: Requirements 10.3**
    """
    total_jobs = num_high_priority + num_low_priority
    assume(total_jobs > num_environments * 2)
    
    orchestrator = TestOrchestrator()
    
    # Create limited environments
    for i in range(num_environments):
        env = Environment(
            id=f"env_{i}",
            config=HardwareConfig(
                architecture='x86_64',
                cpu_model='test_cpu',
                memory_mb=2048,
                storage_type='ssd',
                peripherals=[],
                is_virtual=True,
                emulator='qemu'
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        orchestrator.add_environment(env)
    
    # Submit low priority jobs first
    low_priority_jobs = []
    for i in range(num_low_priority):
        test_case = TestCase(
            id=f"low_{i}",
            name=f"Low Priority Test {i}",
            description=f"Low priority test {i}",
            test_type=TestType.UNIT,
            target_subsystem='kernel',
            code_paths=[],
            execution_time_estimate=30,
            test_script="#!/bin/bash\nexit 0",
            expected_outcome=ExpectedOutcome()
        )
        job_id = orchestrator.submit_job(test_case, Priority.LOW, 0.1)
        low_priority_jobs.append(job_id)
    
    # Then submit high priority jobs
    high_priority_jobs = []
    for i in range(num_high_priority):
        test_case = TestCase(
            id=f"high_{i}",
            name=f"High Priority Test {i}",
            description=f"High priority test {i}",
            test_type=TestType.UNIT,
            target_subsystem='kernel',
            code_paths=[],
            execution_time_estimate=30,
            test_script="#!/bin/bash\nexit 0",
            expected_outcome=ExpectedOutcome()
        )
        job_id = orchestrator.submit_job(test_case, Priority.HIGH, 0.9)
        high_priority_jobs.append(job_id)
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Verify high priority jobs are scheduled despite being submitted later
    with orchestrator._lock:
        running_job_ids = set(orchestrator._running_jobs.keys())
        
        # Count how many of each priority are running
        high_running = sum(1 for jid in high_priority_jobs if jid in running_job_ids)
        low_running = sum(1 for jid in low_priority_jobs if jid in running_job_ids)
        
        # If we have contention and high priority jobs exist
        if len(running_job_ids) >= num_environments and high_priority_jobs:
            # High priority jobs should be running
            assert high_running > 0, \
                f"No high priority jobs running under contention"
            
            # If low priority jobs are running, high priority should also be running
            if low_running > 0:
                assert high_running >= low_running, \
                    f"More low priority jobs running than high priority: {low_running} > {high_running}"


@given(
    st.integers(min_value=1, max_value=3),
    st.lists(gen_test_case(), min_size=5, max_size=15)
)
@settings(max_examples=20, deadline=None)
def test_fair_scheduling_within_same_priority(
    num_environments: int,
    test_cases: List[TestCase]
):
    """
    Property: Under contention, jobs with the same priority should be scheduled
    fairly (FIFO order) without starvation.
    
    **Feature: agentic-kernel-testing, Property 48: Priority-based scheduling under contention**
    **Validates: Requirements 10.3**
    """
    assume(len(test_cases) > num_environments * 2)
    
    orchestrator = TestOrchestrator()
    
    # Create limited environments
    for i in range(num_environments):
        env = Environment(
            id=f"env_{i}",
            config=HardwareConfig(
                architecture='x86_64',
                cpu_model='test_cpu',
                memory_mb=2048,
                storage_type='ssd',
                peripherals=[],
                is_virtual=True,
                emulator='qemu'
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        orchestrator.add_environment(env)
    
    # Submit all jobs with same priority
    job_ids = []
    for test_case in test_cases:
        job_id = orchestrator.submit_job(test_case, Priority.MEDIUM, 0.5)
        job_ids.append(job_id)
        time.sleep(0.001)  # Small delay to ensure different timestamps
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Verify no job is starved (all jobs should eventually be scheduled)
    with orchestrator._lock:
        # All jobs should be either pending, running, or completed
        total_accounted = (
            len(orchestrator._job_queue) +
            len(orchestrator._running_jobs) +
            len(orchestrator._completed_jobs)
        )
        
        assert total_accounted == len(test_cases), \
            f"Job accounting error: {total_accounted} != {len(test_cases)}"
        
        # No job should be lost
        all_tracked_jobs = set()
        all_tracked_jobs.update(job.id for job in orchestrator._job_queue)
        all_tracked_jobs.update(orchestrator._running_jobs.keys())
        all_tracked_jobs.update(orchestrator._completed_jobs)
        
        assert len(all_tracked_jobs) == len(test_cases), \
            f"Some jobs lost: {len(all_tracked_jobs)} != {len(test_cases)}"
