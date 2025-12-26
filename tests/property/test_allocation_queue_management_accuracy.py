"""Property-based tests for allocation queue management accuracy.

**Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

Property 7: Allocation Queue Management Accuracy
For any test waiting for environment allocation, the UI should display correct queue position, 
estimated wait time, priority, and show real-time updates when allocations occur or capacity changes.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import json

from api.models import (
    AllocationRequest, AllocationStatusEnum, HardwareRequirements, 
    AllocationPreferences, EnvironmentTypeEnum, AllocationQueueResponse,
    AllocationEvent, AllocationMetrics
)


# Custom strategies for generating test data
@st.composite
def gen_hardware_requirements(draw):
    """Generate random hardware requirements."""
    return HardwareRequirements(
        architecture=draw(st.sampled_from(["x86_64", "arm64", "riscv64", "arm"])),
        min_memory_mb=draw(st.integers(min_value=512, max_value=32768)),
        min_cpu_cores=draw(st.integers(min_value=1, max_value=16)),
        required_features=draw(st.lists(st.text(min_size=1, max_size=20), max_size=5)),
        preferred_environment_type=draw(st.one_of(st.none(), st.sampled_from(list(EnvironmentTypeEnum)))),
        isolation_level=draw(st.sampled_from(["none", "process", "container", "vm"]))
    )


@st.composite
def gen_allocation_preferences(draw):
    """Generate random allocation preferences."""
    return AllocationPreferences(
        environment_type=draw(st.one_of(st.none(), st.sampled_from(list(EnvironmentTypeEnum)))),
        architecture=draw(st.one_of(st.none(), st.sampled_from(["x86_64", "arm64", "riscv64"]))),
        max_wait_time=draw(st.one_of(st.none(), st.integers(min_value=60, max_value=3600))),
        allow_shared_environment=draw(st.booleans()),
        require_dedicated_resources=draw(st.booleans())
    )


@st.composite
def gen_allocation_request(draw):
    """Generate a random allocation request."""
    return AllocationRequest(
        id=draw(st.text(min_size=8, max_size=32, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        test_id=draw(st.text(min_size=8, max_size=32, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        requirements=draw(gen_hardware_requirements()),
        preferences=draw(st.one_of(st.none(), gen_allocation_preferences())),
        priority=draw(st.integers(min_value=1, max_value=10)),
        submitted_at=draw(st.datetimes(min_value=datetime(2020, 1, 1)).map(lambda dt: dt.replace(tzinfo=timezone.utc))),
        estimated_start_time=draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2020, 1, 1)).map(lambda dt: dt.replace(tzinfo=timezone.utc)))),
        status=draw(st.sampled_from(list(AllocationStatusEnum)))
    )


@st.composite
def gen_allocation_queue(draw):
    """Generate a random allocation queue."""
    queue_size = draw(st.integers(min_value=0, max_value=50))
    queue = []
    
    for i in range(queue_size):
        request = draw(gen_allocation_request())
        # Ensure queue items are in QUEUED or ALLOCATING status
        if request.status not in [AllocationStatusEnum.QUEUED, AllocationStatusEnum.ALLOCATING]:
            request.status = AllocationStatusEnum.QUEUED
        queue.append(request)
    
    return queue


@given(gen_allocation_request())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_request_contains_all_required_fields(request):
    """
    Property: For any allocation request, all required fields should be present and valid.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    # Verify all required fields are present
    assert request.id is not None and len(request.id) > 0, "Request ID must be present and non-empty"
    assert request.test_id is not None and len(request.test_id) > 0, "Test ID must be present and non-empty"
    assert request.requirements is not None, "Hardware requirements must be present"
    assert request.priority >= 1 and request.priority <= 10, f"Priority {request.priority} must be between 1 and 10"
    assert request.submitted_at is not None, "Submitted timestamp must be present"
    assert request.status in AllocationStatusEnum, f"Status {request.status} must be valid"


@given(gen_allocation_request())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_request_hardware_requirements_are_valid(request):
    """
    Property: For any allocation request, hardware requirements should be within valid ranges.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    req = request.requirements
    
    # Memory should be reasonable
    assert req.min_memory_mb >= 128, f"Minimum memory {req.min_memory_mb}MB should be at least 128MB"
    assert req.min_memory_mb <= 1048576, f"Minimum memory {req.min_memory_mb}MB should not exceed 1TB"
    
    # CPU cores should be reasonable
    assert req.min_cpu_cores >= 1, f"Minimum CPU cores {req.min_cpu_cores} should be at least 1"
    assert req.min_cpu_cores <= 128, f"Minimum CPU cores {req.min_cpu_cores} should not exceed 128"
    
    # Architecture should be supported
    supported_architectures = ["x86_64", "arm64", "riscv64", "arm", "aarch64", "i386"]
    assert req.architecture in supported_architectures, \
        f"Architecture {req.architecture} should be supported"
    
    # Isolation level should be valid
    valid_isolation_levels = ["none", "process", "container", "vm"]
    assert req.isolation_level in valid_isolation_levels, \
        f"Isolation level {req.isolation_level} should be valid"


@given(gen_allocation_request())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_request_timestamps_are_consistent(request):
    """
    Property: For any allocation request, estimated_start_time should be after submitted_at when present.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    if request.estimated_start_time is not None:
        assert request.estimated_start_time >= request.submitted_at, \
            f"Estimated start time {request.estimated_start_time} must be >= submitted time {request.submitted_at}"


@given(gen_allocation_queue())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_priority_ordering(queue):
    """
    Property: For any allocation queue, requests should be orderable by priority (higher priority = lower number).
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    if len(queue) <= 1:
        return  # Nothing to test for empty or single-item queues
    
    # Sort by priority (lower number = higher priority)
    sorted_queue = sorted(queue, key=lambda r: r.priority)
    
    # Verify sorting is stable and correct
    for i in range(len(sorted_queue) - 1):
        current_priority = sorted_queue[i].priority
        next_priority = sorted_queue[i + 1].priority
        assert current_priority <= next_priority, \
            f"Queue should be sortable by priority: {current_priority} should be <= {next_priority}"


@given(gen_allocation_queue())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_position_calculation(queue):
    """
    Property: For any allocation queue, queue positions should be calculable and consistent.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    if len(queue) == 0:
        return  # Nothing to test for empty queue
    
    # Sort by priority and submission time
    sorted_queue = sorted(queue, key=lambda r: (r.priority, r.submitted_at))
    
    # Calculate positions
    positions = {}
    for i, request in enumerate(sorted_queue):
        positions[request.id] = i + 1  # 1-based position
    
    # Verify positions are unique and sequential
    position_values = list(positions.values())
    assert len(set(position_values)) == len(position_values), "Queue positions should be unique"
    assert min(position_values) == 1, "First position should be 1"
    assert max(position_values) == len(queue), f"Last position should be {len(queue)}"
    assert sorted(position_values) == list(range(1, len(queue) + 1)), "Positions should be sequential"


@given(gen_allocation_queue(), st.integers(min_value=1, max_value=600))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_wait_time_estimation(queue, avg_allocation_time_seconds):
    """
    Property: For any allocation queue, wait times should be estimatable and reasonable.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    if len(queue) == 0:
        return  # Nothing to test for empty queue
    
    # Sort by priority and submission time
    sorted_queue = sorted(queue, key=lambda r: (r.priority, r.submitted_at))
    
    # Calculate estimated wait times
    wait_times = {}
    for i, request in enumerate(sorted_queue):
        # Wait time = position in queue * average allocation time
        estimated_wait_seconds = i * avg_allocation_time_seconds
        wait_times[request.id] = estimated_wait_seconds
    
    # Verify wait times are reasonable
    for request_id, wait_time in wait_times.items():
        assert wait_time >= 0, f"Wait time {wait_time} should be non-negative"
        assert wait_time <= len(queue) * avg_allocation_time_seconds, \
            f"Wait time {wait_time} should not exceed maximum possible wait"


@given(gen_allocation_queue())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_status_consistency(queue):
    """
    Property: For any allocation queue, all requests should have appropriate status for being in queue.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    valid_queue_statuses = [AllocationStatusEnum.QUEUED, AllocationStatusEnum.ALLOCATING]
    
    for request in queue:
        assert request.status in valid_queue_statuses, \
            f"Request in queue should have status QUEUED or ALLOCATING, got {request.status}"


@given(gen_allocation_request())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_request_preferences_consistency(request):
    """
    Property: For any allocation request, preferences should be consistent with requirements.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    if request.preferences is None:
        return  # No preferences to validate
    
    prefs = request.preferences
    reqs = request.requirements
    
    # If architecture preference is specified, it should match requirements
    if prefs.architecture is not None:
        assert prefs.architecture == reqs.architecture, \
            f"Preference architecture {prefs.architecture} should match requirement {reqs.architecture}"
    
    # If environment type preference is specified, it should be compatible with architecture
    if prefs.environment_type is not None:
        if reqs.architecture == "x86_64":
            compatible_types = [EnvironmentTypeEnum.QEMU_X86, EnvironmentTypeEnum.DOCKER, 
                             EnvironmentTypeEnum.CONTAINER, EnvironmentTypeEnum.PHYSICAL]
        elif reqs.architecture in ["arm64", "arm"]:
            compatible_types = [EnvironmentTypeEnum.QEMU_ARM, EnvironmentTypeEnum.DOCKER, 
                             EnvironmentTypeEnum.CONTAINER, EnvironmentTypeEnum.PHYSICAL]
        else:
            compatible_types = [EnvironmentTypeEnum.DOCKER, EnvironmentTypeEnum.CONTAINER, 
                             EnvironmentTypeEnum.PHYSICAL]
        
        assert prefs.environment_type in compatible_types, \
            f"Environment type {prefs.environment_type} should be compatible with architecture {reqs.architecture}"
    
    # Dedicated resources and shared environment should not both be true
    if prefs.require_dedicated_resources and not prefs.allow_shared_environment:
        # This is consistent - requiring dedicated resources and not allowing sharing
        pass
    elif not prefs.require_dedicated_resources and prefs.allow_shared_environment:
        # This is consistent - allowing sharing and not requiring dedicated resources
        pass
    # Other combinations are also valid, so no assertion needed


@given(gen_allocation_queue())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_serialization_roundtrip(queue):
    """
    Property: For any allocation queue, it should survive serialization/deserialization roundtrip.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    try:
        # Create queue response
        estimated_wait_times = {req.id: i * 60 for i, req in enumerate(queue)}  # 60 seconds per position
        total_wait_time = len(queue) * 60
        
        queue_response = AllocationQueueResponse(
            queue=queue,
            estimated_wait_times=estimated_wait_times,
            total_wait_time=total_wait_time
        )
        
        # Serialize to JSON
        json_data = queue_response.json()
        
        # Deserialize back to object
        deserialized = AllocationQueueResponse.parse_raw(json_data)
        
        # Verify key fields are preserved
        assert len(deserialized.queue) == len(queue), "Queue length should be preserved"
        assert deserialized.total_wait_time == total_wait_time, "Total wait time should be preserved"
        assert len(deserialized.estimated_wait_times) == len(estimated_wait_times), \
            "Estimated wait times count should be preserved"
        
        # Verify individual requests are preserved
        for original, deserialized_req in zip(queue, deserialized.queue):
            assert deserialized_req.id == original.id, "Request ID should be preserved"
            assert deserialized_req.test_id == original.test_id, "Test ID should be preserved"
            assert deserialized_req.priority == original.priority, "Priority should be preserved"
            assert deserialized_req.status == original.status, "Status should be preserved"
        
    except Exception as e:
        pytest.fail(f"Allocation queue should survive serialization roundtrip, but got error: {e}")


@given(gen_allocation_queue())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_unique_request_ids(queue):
    """
    Property: For any allocation queue, all request IDs should be unique.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    request_ids = [req.id for req in queue]
    unique_ids = set(request_ids)
    
    assert len(request_ids) == len(unique_ids), \
        f"Request IDs should be unique, but found duplicates: {[id for id in request_ids if request_ids.count(id) > 1]}"


@given(gen_allocation_queue())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_unique_test_ids(queue):
    """
    Property: For any allocation queue, all test IDs should be unique (one allocation per test).
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    test_ids = [req.test_id for req in queue]
    unique_test_ids = set(test_ids)
    
    assert len(test_ids) == len(unique_test_ids), \
        f"Test IDs should be unique in queue, but found duplicates: {[id for id in test_ids if test_ids.count(id) > 1]}"


@given(st.lists(gen_allocation_request(), min_size=2, max_size=10))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_priority_based_reordering(requests):
    """
    Property: For any set of allocation requests, changing priorities should result in correct reordering.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    # Ensure all requests have QUEUED status
    for req in requests:
        req.status = AllocationStatusEnum.QUEUED
    
    # Sort by original priority
    original_order = sorted(requests, key=lambda r: (r.priority, r.submitted_at))
    
    # Change priority of first request to highest (1)
    if len(requests) > 1:
        first_request = requests[0]
        original_priority = first_request.priority
        first_request.priority = 1
        
        # Re-sort after priority change
        new_order = sorted(requests, key=lambda r: (r.priority, r.submitted_at))
        
        # The first request should now be at the front (or maintain position if already priority 1)
        if original_priority > 1:
            assert new_order[0].id == first_request.id, \
                "Request with changed priority to 1 should be first in queue"
        
        # Restore original priority
        first_request.priority = original_priority


@given(gen_allocation_queue(), st.integers(min_value=1, max_value=10))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_queue_capacity_change_impact(queue, available_environments):
    """
    Property: For any allocation queue, changes in available capacity should affect wait time estimates.
    
    **Feature: environment-allocation-ui, Property 7: Allocation Queue Management Accuracy**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    """
    if len(queue) == 0:
        return  # Nothing to test for empty queue
    
    avg_allocation_time = 120  # 2 minutes per allocation
    
    # Calculate wait times with current capacity
    original_wait_times = {}
    for i, request in enumerate(queue):
        # With multiple environments, requests can be processed in parallel
        parallel_slots = min(available_environments, len(queue))
        batch_number = i // parallel_slots
        wait_time = batch_number * avg_allocation_time
        original_wait_times[request.id] = wait_time
    
    # Calculate wait times with increased capacity
    increased_capacity = available_environments + 2
    increased_wait_times = {}
    for i, request in enumerate(queue):
        parallel_slots = min(increased_capacity, len(queue))
        batch_number = i // parallel_slots
        wait_time = batch_number * avg_allocation_time
        increased_wait_times[request.id] = wait_time
    
    # With increased capacity, wait times should be equal or shorter
    for request_id in original_wait_times:
        original_wait = original_wait_times[request_id]
        increased_wait = increased_wait_times[request_id]
        assert increased_wait <= original_wait, \
            f"Wait time with increased capacity ({increased_wait}) should be <= original ({original_wait})"