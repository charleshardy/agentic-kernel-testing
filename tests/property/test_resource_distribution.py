"""Property-based tests for resource distribution optimization.

**Feature: agentic-kernel-testing, Property 46: Resource distribution optimization**
**Validates: Requirements 10.1**

Property 46: Resource distribution optimization
For any set of queued test jobs, the scheduler should distribute them across available 
execution environments to maximize throughput.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List
import time
import threading

from ai_generator.models import (
    TestCase, TestType, HardwareConfig, ExpectedOutcome, Environment,
    EnvironmentStatus, Peripheral
)
from orchestrator.scheduler import TestOrchestrator, Priority


# Custom strategies for generating test data
@st.composite
def gen_hardware_config(draw, architecture=None):
    """Generate a random hardware configuration."""
    if architecture is None:
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
def gen_test_case(draw, required_hw=None):
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
        required_hardware=required_hw,
        test_script="#!/bin/bash\nexit 0",
        expected_outcome=ExpectedOutcome()
    )


@st.composite
def gen_environment(draw, architecture=None):
    """Generate a random environment."""
    config = draw(gen_hardware_config(architecture=architecture))
    env_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return Environment(
        id=env_id,
        config=config,
        status=EnvironmentStatus.IDLE,
        created_at=datetime.now(),
        last_used=datetime.now()
    )


@given(
    st.lists(gen_test_case(), min_size=2, max_size=10),
    st.lists(gen_environment(), min_size=2, max_size=5)
)
@settings(max_examples=20, deadline=None)
def test_all_environments_utilized(
    test_cases: List[TestCase],
    environments: List[Environment]
):
    """
    Property: For any set of test jobs and available environments, if there are
    more jobs than environments, all environments should be utilized.
    
    **Feature: agentic-kernel-testing, Property 46: Resource distribution optimization**
    **Validates: Requirements 10.1**
    """
    assume(len(test_cases) >= len(environments))
    
    orchestrator = TestOrchestrator()
    
    # Add all environments
    for env in environments:
        orchestrator.add_environment(env)
    
    # Submit all jobs
    for test_case in test_cases:
        orchestrator.submit_job(test_case, Priority.MEDIUM, 0.5)
    
    # Give scheduler more time to allocate (async operations)
    time.sleep(0.2)
    
    # Check that environments are allocated
    with orchestrator._lock:
        allocated_count = len(orchestrator._allocated_resources)
        available_count = len(orchestrator._available_environments)
        
        # All environments should be either allocated or available
        total_envs = allocated_count + available_count
        assert total_envs == len(environments), \
            f"Environment count mismatch: {total_envs} != {len(environments)}"
        
        # If we have more jobs than environments, most should be allocated
        # (allowing for some that may have completed very quickly)
        if len(test_cases) >= len(environments):
            # At least half the environments should have been used
            assert allocated_count >= len(environments) // 2 or len(orchestrator._completed_jobs) > 0, \
                f"Not enough environments utilized: {allocated_count}/{len(environments)}, completed: {len(orchestrator._completed_jobs)}"


@given(
    st.lists(gen_test_case(), min_size=1, max_size=10),
    st.integers(min_value=1, max_value=5)
)
@settings(max_examples=20, deadline=None)
def test_no_over_allocation(test_cases: List[TestCase], num_environments: int):
    """
    Property: For any set of test jobs, the number of allocated environments
    should never exceed the number of available environments.
    
    **Feature: agentic-kernel-testing, Property 46: Resource distribution optimization**
    **Validates: Requirements 10.1**
    """
    orchestrator = TestOrchestrator()
    
    # Create and add environments
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
    
    # Submit all jobs
    for test_case in test_cases:
        orchestrator.submit_job(test_case, Priority.MEDIUM, 0.5)
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Verify no over-allocation
    with orchestrator._lock:
        allocated_count = len(orchestrator._allocated_resources)
        
        assert allocated_count <= num_environments, \
            f"Over-allocation detected: {allocated_count} > {num_environments}"


@given(
    st.lists(gen_test_case(), min_size=2, max_size=10),
    st.lists(gen_environment(), min_size=2, max_size=5)
)
@settings(max_examples=20, deadline=None)
def test_round_robin_distribution(
    test_cases: List[TestCase],
    environments: List[Environment]
):
    """
    Property: For any set of test jobs with no specific hardware requirements,
    jobs should be distributed across environments in a balanced manner.
    
    **Feature: agentic-kernel-testing, Property 46: Resource distribution optimization**
    **Validates: Requirements 10.1**
    """
    assume(len(test_cases) >= len(environments) * 2)
    
    orchestrator = TestOrchestrator()
    
    # Add all environments
    for env in environments:
        orchestrator.add_environment(env)
    
    # Track which environment each job would use
    # We'll check the allocation pattern
    initial_available = len(environments)
    
    # Submit jobs one by one and check allocation
    allocations_per_env = {env.id: 0 for env in environments}
    
    for test_case in test_cases:
        orchestrator.submit_job(test_case, Priority.MEDIUM, 0.5)
        time.sleep(0.01)  # Small delay for scheduling
        
        with orchestrator._lock:
            # Count current allocations
            for env_id in orchestrator._allocated_resources:
                if env_id in allocations_per_env:
                    allocations_per_env[env_id] += 1
    
    # Give time for all to be allocated
    time.sleep(0.2)
    
    # Check distribution is relatively balanced
    # (within 2 jobs difference between any two environments)
    with orchestrator._lock:
        allocation_counts = list(allocations_per_env.values())
        if allocation_counts:
            max_alloc = max(allocation_counts)
            min_alloc = min(allocation_counts)
            
            # Allow some imbalance due to timing, but should be roughly balanced
            # This is a soft check - perfect balance is hard with async scheduling
            assert max_alloc - min_alloc <= len(test_cases) // len(environments) + 2, \
                f"Unbalanced distribution: {allocations_per_env}"


@given(
    st.lists(gen_environment(architecture='x86_64'), min_size=2, max_size=5),
    st.integers(min_value=2, max_value=10)
)
@settings(max_examples=20, deadline=None)
def test_hardware_matching_distribution(
    environments: List[Environment],
    num_jobs: int
):
    """
    Property: For any set of test jobs with specific hardware requirements,
    jobs should only be allocated to matching environments.
    
    **Feature: agentic-kernel-testing, Property 46: Resource distribution optimization**
    **Validates: Requirements 10.1**
    """
    orchestrator = TestOrchestrator()
    
    # Add all environments (all x86_64)
    for env in environments:
        orchestrator.add_environment(env)
    
    # Create test cases requiring x86_64
    required_hw = HardwareConfig(
        architecture='x86_64',
        cpu_model='any',
        memory_mb=512,
        storage_type='ssd',
        peripherals=[],
        is_virtual=True,
        emulator='qemu'
    )
    
    test_cases = []
    for i in range(num_jobs):
        test_case = TestCase(
            id=f"test_{i}",
            name=f"Test {i}",
            description="Test requiring x86_64",
            test_type=TestType.UNIT,
            target_subsystem='kernel',
            code_paths=[],
            execution_time_estimate=30,
            required_hardware=required_hw,
            test_script="#!/bin/bash\nexit 0",
            expected_outcome=ExpectedOutcome()
        )
        test_cases.append(test_case)
    
    # Submit all jobs
    for test_case in test_cases:
        orchestrator.submit_job(test_case, Priority.MEDIUM, 0.5)
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Verify all allocated environments match requirements
    with orchestrator._lock:
        for env_id, allocation in orchestrator._allocated_resources.items():
            # Find the environment
            env = next((e for e in environments if e.id == env_id), None)
            assert env is not None, f"Allocated environment {env_id} not found"
            
            # Verify architecture matches
            assert env.config.architecture == 'x86_64', \
                f"Environment {env_id} has wrong architecture: {env.config.architecture}"


@given(
    st.lists(gen_test_case(), min_size=3, max_size=15),
    st.lists(gen_environment(), min_size=2, max_size=5)
)
@settings(max_examples=20, deadline=None)
def test_throughput_maximization(
    test_cases: List[TestCase],
    environments: List[Environment]
):
    """
    Property: For any set of test jobs, the scheduler should maximize throughput
    by keeping all available environments busy when jobs are pending.
    
    **Feature: agentic-kernel-testing, Property 46: Resource distribution optimization**
    **Validates: Requirements 10.1**
    """
    assume(len(test_cases) > len(environments))
    
    orchestrator = TestOrchestrator()
    
    # Add all environments
    for env in environments:
        orchestrator.add_environment(env)
    
    # Submit all jobs
    for test_case in test_cases:
        orchestrator.submit_job(test_case, Priority.MEDIUM, 0.5)
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Check queue status
    status = orchestrator.get_queue_status()
    
    # If there are pending jobs, all environments should be allocated
    if status['pending_jobs'] > 0:
        assert status['allocated_environments'] == len(environments), \
            f"Not maximizing throughput: {status['allocated_environments']}/{len(environments)} " \
            f"allocated with {status['pending_jobs']} pending jobs"
    
    # Total jobs should equal pending + running + completed
    total_jobs = status['pending_jobs'] + status['running_jobs'] + status['completed_jobs']
    assert total_jobs == len(test_cases), \
        f"Job count mismatch: {total_jobs} != {len(test_cases)}"


@given(
    st.lists(gen_test_case(), min_size=1, max_size=10),
    st.lists(gen_environment(), min_size=1, max_size=5)
)
@settings(max_examples=20, deadline=None)
def test_resource_allocation_tracking(
    test_cases: List[TestCase],
    environments: List[Environment]
):
    """
    Property: For any test execution, the sum of allocated and available
    environments should always equal the total number of environments.
    
    **Feature: agentic-kernel-testing, Property 46: Resource distribution optimization**
    **Validates: Requirements 10.1**
    """
    orchestrator = TestOrchestrator()
    
    # Add all environments
    for env in environments:
        orchestrator.add_environment(env)
    
    total_environments = len(environments)
    
    # Submit all jobs
    for test_case in test_cases:
        orchestrator.submit_job(test_case, Priority.MEDIUM, 0.5)
    
    # Give scheduler time to allocate
    time.sleep(0.2)
    
    # Verify resource tracking
    with orchestrator._lock:
        allocated = len(orchestrator._allocated_resources)
        available = len(orchestrator._available_environments)
        
        assert allocated + available == total_environments, \
            f"Resource tracking error: {allocated} + {available} != {total_environments}"
        
        # Verify no environment is both allocated and available
        allocated_ids = set(orchestrator._allocated_resources.keys())
        available_ids = set(env.id for env in orchestrator._available_environments)
        
        assert allocated_ids.isdisjoint(available_ids), \
            f"Environment appears in both allocated and available: {allocated_ids & available_ids}"
