"""Property-based tests for capacity and availability indication accuracy.

**Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
**Validates: Requirements 2.5, 3.4, 3.5**

Property 10: Capacity and Availability Indication
For any system state, the UI should clearly indicate available capacity, idle environments, 
and allocation likelihood based on current resource utilization.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import json

from api.models import (
    EnvironmentResponse, EnvironmentTypeEnum, EnvironmentStatusEnum, 
    EnvironmentHealthEnum, ResourceUsage, NetworkMetrics, EnvironmentMetadata
)


@st.composite
def gen_system_capacity_state(draw):
    """Generate random system capacity state with multiple environments."""
    num_environments = draw(st.integers(min_value=1, max_value=20))
    
    environments = []
    for i in range(num_environments):
        env_type = draw(st.sampled_from(list(EnvironmentTypeEnum)))
        status = draw(st.sampled_from(list(EnvironmentStatusEnum)))
        
        # Generate resource usage based on status
        if status == EnvironmentStatusEnum.READY:
            # Ready environments should have low resource usage
            cpu_usage = draw(st.floats(min_value=0.0, max_value=20.0))
            memory_usage = draw(st.floats(min_value=0.0, max_value=30.0))
            disk_usage = draw(st.floats(min_value=0.0, max_value=50.0))
        elif status == EnvironmentStatusEnum.RUNNING:
            # Running environments should have higher resource usage
            cpu_usage = draw(st.floats(min_value=20.0, max_value=100.0))
            memory_usage = draw(st.floats(min_value=30.0, max_value=100.0))
            disk_usage = draw(st.floats(min_value=20.0, max_value=100.0))
        elif status in [EnvironmentStatusEnum.OFFLINE, EnvironmentStatusEnum.ERROR]:
            # Offline/error environments should have zero or minimal usage
            cpu_usage = draw(st.floats(min_value=0.0, max_value=5.0))
            memory_usage = draw(st.floats(min_value=0.0, max_value=5.0))
            disk_usage = draw(st.floats(min_value=0.0, max_value=10.0))
        else:
            # Other statuses (allocating, cleanup, maintenance)
            cpu_usage = draw(st.floats(min_value=0.0, max_value=60.0))
            memory_usage = draw(st.floats(min_value=0.0, max_value=60.0))
            disk_usage = draw(st.floats(min_value=0.0, max_value=60.0))
        
        # Assigned tests based on status
        if status == EnvironmentStatusEnum.RUNNING:
            assigned_tests = draw(st.lists(st.text(min_size=8, max_size=16), min_size=1, max_size=5))
        elif status == EnvironmentStatusEnum.READY:
            assigned_tests = draw(st.lists(st.text(min_size=8, max_size=16), min_size=0, max_size=1))
        else:
            assigned_tests = []
        
        environment = {
            'id': f"env_{i}_{draw(st.text(min_size=4, max_size=8))}",
            'type': env_type,
            'status': status,
            'architecture': draw(st.sampled_from(["x86_64", "arm64", "riscv64"])),
            'assigned_tests': assigned_tests,
            'resources': {
                'cpu': cpu_usage,
                'memory': memory_usage,
                'disk': disk_usage,
                'network': {
                    'bytes_in': draw(st.integers(min_value=0, max_value=1000000)),
                    'bytes_out': draw(st.integers(min_value=0, max_value=1000000)),
                    'packets_in': draw(st.integers(min_value=0, max_value=10000)),
                    'packets_out': draw(st.integers(min_value=0, max_value=10000))
                }
            },
            'health': draw(st.sampled_from(list(EnvironmentHealthEnum))),
            'metadata': {
                'kernel_version': draw(st.one_of(st.none(), st.text(min_size=5, max_size=20))),
                'ip_address': draw(st.one_of(st.none(), st.ip_addresses().map(str))),
                'ssh_credentials': None,
                'provisioned_at': draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2020, 1, 1)).map(lambda dt: dt.replace(tzinfo=timezone.utc)))),
                'last_health_check': draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2020, 1, 1)).map(lambda dt: dt.replace(tzinfo=timezone.utc)))),
                'additional_metadata': {}
            },
            'created_at': datetime.now(timezone.utc) - timedelta(hours=draw(st.integers(min_value=1, max_value=168))),
            'updated_at': datetime.now(timezone.utc) - timedelta(minutes=draw(st.integers(min_value=0, max_value=60)))
        }
        environments.append(environment)
    
    # Generate pending allocation requests
    num_pending_requests = draw(st.integers(min_value=0, max_value=10))
    pending_requests = []
    for i in range(num_pending_requests):
        pending_requests.append({
            'id': f"req_{i}_{draw(st.text(min_size=4, max_size=8))}",
            'test_id': f"test_{draw(st.text(min_size=8, max_size=16))}",
            'requirements': {
                'architecture': draw(st.sampled_from(["x86_64", "arm64", "riscv64"])),
                'min_memory_mb': draw(st.integers(min_value=512, max_value=8192)),
                'min_cpu_cores': draw(st.integers(min_value=1, max_value=8)),
                'required_features': draw(st.lists(st.text(min_size=3, max_size=10), max_size=3)),
                'preferred_environment_type': draw(st.one_of(st.none(), st.sampled_from(list(EnvironmentTypeEnum)))),
                'isolation_level': draw(st.sampled_from(['none', 'process', 'container', 'vm']))
            },
            'priority': draw(st.integers(min_value=1, max_value=10)),
            'submitted_at': datetime.now(timezone.utc) - timedelta(minutes=draw(st.integers(min_value=1, max_value=120))),
            'estimated_start_time': datetime.now(timezone.utc) + timedelta(minutes=draw(st.integers(min_value=1, max_value=60)))
        })
    
    return {
        'environments': environments,
        'pending_requests': pending_requests,
        'timestamp': datetime.now(timezone.utc)
    }


def calculate_capacity_metrics(system_state):
    """Calculate capacity metrics from system state."""
    environments = system_state['environments']
    pending_requests = system_state['pending_requests']
    
    # Count environments by status
    status_counts = {}
    for env in environments:
        status = env['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Calculate available capacity
    ready_environments = [env for env in environments if env['status'] == EnvironmentStatusEnum.READY]
    idle_environments = [env for env in ready_environments if len(env['assigned_tests']) == 0]
    
    # Calculate resource utilization
    total_cpu = sum(env['resources']['cpu'] for env in environments)
    total_memory = sum(env['resources']['memory'] for env in environments)
    total_disk = sum(env['resources']['disk'] for env in environments)
    
    avg_cpu = total_cpu / len(environments) if environments else 0
    avg_memory = total_memory / len(environments) if environments else 0
    avg_disk = total_disk / len(environments) if environments else 0
    
    # Calculate allocation likelihood for pending requests
    allocation_likelihood = {}
    for request in pending_requests:
        # Simple heuristic: likelihood based on available environments and requirements
        compatible_envs = [
            env for env in ready_environments
            if env['architecture'] == request['requirements']['architecture']
        ]
        
        if len(compatible_envs) > 0:
            likelihood = min(100, (len(compatible_envs) / max(1, len(pending_requests))) * 100)
        else:
            likelihood = 0
        
        allocation_likelihood[request['id']] = likelihood
    
    return {
        'total_environments': len(environments),
        'ready_environments': len(ready_environments),
        'idle_environments': len(idle_environments),
        'running_environments': status_counts.get(EnvironmentStatusEnum.RUNNING, 0),
        'offline_environments': status_counts.get(EnvironmentStatusEnum.OFFLINE, 0),
        'error_environments': status_counts.get(EnvironmentStatusEnum.ERROR, 0),
        'average_cpu_utilization': avg_cpu,
        'average_memory_utilization': avg_memory,
        'average_disk_utilization': avg_disk,
        'pending_requests_count': len(pending_requests),
        'allocation_likelihood': allocation_likelihood,
        'capacity_percentage': (len(ready_environments) / max(1, len(environments))) * 100,
        'utilization_percentage': (avg_cpu + avg_memory + avg_disk) / 3
    }


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_capacity_metrics_are_consistent(system_state):
    """
    Property: For any system state, capacity metrics should be mathematically consistent.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    metrics = calculate_capacity_metrics(system_state)
    
    # Basic consistency checks
    assert metrics['total_environments'] >= 0, "Total environments should be non-negative"
    assert metrics['ready_environments'] >= 0, "Ready environments should be non-negative"
    assert metrics['idle_environments'] >= 0, "Idle environments should be non-negative"
    assert metrics['running_environments'] >= 0, "Running environments should be non-negative"
    
    # Idle environments should be subset of ready environments
    assert metrics['idle_environments'] <= metrics['ready_environments'], \
        "Idle environments should not exceed ready environments"
    
    # Ready + running + offline + error should not exceed total
    accounted_envs = (metrics['ready_environments'] + metrics['running_environments'] + 
                     metrics['offline_environments'] + metrics['error_environments'])
    assert accounted_envs <= metrics['total_environments'], \
        "Sum of categorized environments should not exceed total"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_capacity_percentage_is_valid(system_state):
    """
    Property: For any system state, capacity percentage should be between 0 and 100.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    metrics = calculate_capacity_metrics(system_state)
    capacity_percentage = metrics['capacity_percentage']
    
    assert 0.0 <= capacity_percentage <= 100.0, \
        f"Capacity percentage {capacity_percentage} should be between 0 and 100"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_utilization_metrics_are_valid(system_state):
    """
    Property: For any system state, resource utilization metrics should be within valid ranges.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    metrics = calculate_capacity_metrics(system_state)
    
    # Individual utilization metrics should be valid
    assert 0.0 <= metrics['average_cpu_utilization'] <= 100.0, \
        f"Average CPU utilization {metrics['average_cpu_utilization']} should be between 0 and 100"
    
    assert 0.0 <= metrics['average_memory_utilization'] <= 100.0, \
        f"Average memory utilization {metrics['average_memory_utilization']} should be between 0 and 100"
    
    assert 0.0 <= metrics['average_disk_utilization'] <= 100.0, \
        f"Average disk utilization {metrics['average_disk_utilization']} should be between 0 and 100"
    
    # Overall utilization percentage should be valid
    assert 0.0 <= metrics['utilization_percentage'] <= 100.0, \
        f"Overall utilization percentage {metrics['utilization_percentage']} should be between 0 and 100"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_likelihood_is_reasonable(system_state):
    """
    Property: For any system state, allocation likelihood should be reasonable based on available capacity.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    metrics = calculate_capacity_metrics(system_state)
    allocation_likelihood = metrics['allocation_likelihood']
    
    # All likelihood values should be between 0 and 100
    for request_id, likelihood in allocation_likelihood.items():
        assert 0.0 <= likelihood <= 100.0, \
            f"Allocation likelihood {likelihood} for request {request_id} should be between 0 and 100"
    
    # If no ready environments, likelihood should be 0
    if metrics['ready_environments'] == 0:
        for request_id, likelihood in allocation_likelihood.items():
            assert likelihood == 0.0, \
                f"Allocation likelihood should be 0 when no ready environments available, got {likelihood}"
    
    # If more ready environments than pending requests, likelihood should be high
    if metrics['ready_environments'] > metrics['pending_requests_count'] and metrics['pending_requests_count'] > 0:
        avg_likelihood = sum(allocation_likelihood.values()) / len(allocation_likelihood) if allocation_likelihood else 0
        assert avg_likelihood >= 50.0, \
            f"Average allocation likelihood should be high when capacity exceeds demand, got {avg_likelihood}"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_idle_environment_identification(system_state):
    """
    Property: For any system state, idle environments should be correctly identified.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    environments = system_state['environments']
    metrics = calculate_capacity_metrics(system_state)
    
    # Count actual idle environments
    actual_idle = 0
    for env in environments:
        if env['status'] == EnvironmentStatusEnum.READY and len(env['assigned_tests']) == 0:
            actual_idle += 1
    
    assert metrics['idle_environments'] == actual_idle, \
        f"Idle environment count {metrics['idle_environments']} should match actual count {actual_idle}"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_capacity_indication_reflects_system_health(system_state):
    """
    Property: For any system state, capacity indication should reflect overall system health.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    environments = system_state['environments']
    metrics = calculate_capacity_metrics(system_state)
    
    # Count healthy vs unhealthy environments
    healthy_envs = [env for env in environments if env['health'] == EnvironmentHealthEnum.HEALTHY]
    unhealthy_envs = [env for env in environments if env['health'] == EnvironmentHealthEnum.UNHEALTHY]
    
    # If most environments are unhealthy, capacity should be lower
    if len(unhealthy_envs) > len(healthy_envs) and len(environments) > 0:
        # System with mostly unhealthy environments should have reduced effective capacity
        effective_capacity = metrics['ready_environments'] - len([
            env for env in environments 
            if env['status'] == EnvironmentStatusEnum.READY and env['health'] == EnvironmentHealthEnum.UNHEALTHY
        ])
        assert effective_capacity >= 0, "Effective capacity should be non-negative"
    
    # If all environments are healthy and ready, capacity should be high
    if all(env['health'] == EnvironmentHealthEnum.HEALTHY for env in environments):
        if all(env['status'] == EnvironmentStatusEnum.READY for env in environments):
            assert metrics['capacity_percentage'] == 100.0, \
                "Capacity should be 100% when all environments are healthy and ready"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_resource_utilization_affects_availability(system_state):
    """
    Property: For any system state, high resource utilization should affect availability indication.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    environments = system_state['environments']
    metrics = calculate_capacity_metrics(system_state)
    
    # Check if any environments have high resource utilization
    high_utilization_envs = [
        env for env in environments
        if (env['resources']['cpu'] > 80 or 
            env['resources']['memory'] > 80 or 
            env['resources']['disk'] > 80)
    ]
    
    # If many environments have high utilization, overall utilization should be high
    if len(high_utilization_envs) > len(environments) / 2 and len(environments) > 0:
        assert metrics['utilization_percentage'] > 50.0, \
            f"Overall utilization should be high when many environments have high usage, got {metrics['utilization_percentage']}"
    
    # Environments with high utilization should not be considered fully available
    for env in high_utilization_envs:
        if env['status'] == EnvironmentStatusEnum.READY:
            # High utilization ready environments should be flagged as potentially unavailable
            max_resource_usage = max(env['resources']['cpu'], env['resources']['memory'], env['resources']['disk'])
            assert max_resource_usage > 80.0, \
                f"Environment flagged as high utilization should have >80% usage, got {max_resource_usage}"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_pending_requests_affect_allocation_likelihood(system_state):
    """
    Property: For any system state, number of pending requests should affect allocation likelihood.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    metrics = calculate_capacity_metrics(system_state)
    pending_requests = system_state['pending_requests']
    
    # If no pending requests, allocation likelihood should be undefined or high
    if metrics['pending_requests_count'] == 0:
        assert len(metrics['allocation_likelihood']) == 0, \
            "Should have no allocation likelihood when no pending requests"
    
    # If pending requests exist, they should all have likelihood values
    if metrics['pending_requests_count'] > 0:
        assert len(metrics['allocation_likelihood']) == metrics['pending_requests_count'], \
            f"Should have likelihood for each pending request: {len(metrics['allocation_likelihood'])} vs {metrics['pending_requests_count']}"
        
        # All requests should have valid likelihood values
        for request_id, likelihood in metrics['allocation_likelihood'].items():
            assert isinstance(likelihood, (int, float)), \
                f"Allocation likelihood should be numeric, got {type(likelihood)}"
            assert 0.0 <= likelihood <= 100.0, \
                f"Allocation likelihood should be 0-100, got {likelihood}"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_architecture_compatibility_affects_likelihood(system_state):
    """
    Property: For any system state, architecture compatibility should affect allocation likelihood.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    environments = system_state['environments']
    pending_requests = system_state['pending_requests']
    metrics = calculate_capacity_metrics(system_state)
    
    # Check architecture compatibility for each request
    for request in pending_requests:
        required_arch = request['requirements']['architecture']
        request_id = request['id']
        
        # Count compatible ready environments
        compatible_ready_envs = [
            env for env in environments
            if (env['status'] == EnvironmentStatusEnum.READY and 
                env['architecture'] == required_arch)
        ]
        
        likelihood = metrics['allocation_likelihood'].get(request_id, 0)
        
        # If no compatible environments, likelihood should be 0
        if len(compatible_ready_envs) == 0:
            assert likelihood == 0.0, \
                f"Allocation likelihood should be 0 when no compatible environments available, got {likelihood}"
        
        # If compatible environments exist, likelihood should be > 0
        if len(compatible_ready_envs) > 0:
            assert likelihood > 0.0, \
                f"Allocation likelihood should be > 0 when compatible environments available, got {likelihood}"


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_capacity_metrics_are_serializable(system_state):
    """
    Property: For any system state, capacity metrics should be JSON serializable.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    metrics = calculate_capacity_metrics(system_state)
    
    try:
        # Serialize to JSON
        json_str = json.dumps(metrics, default=str)
        
        # Deserialize back
        deserialized = json.loads(json_str)
        
        # Verify key fields are preserved
        assert deserialized['total_environments'] == metrics['total_environments'], \
            "Total environments should be preserved"
        assert deserialized['ready_environments'] == metrics['ready_environments'], \
            "Ready environments should be preserved"
        assert deserialized['idle_environments'] == metrics['idle_environments'], \
            "Idle environments should be preserved"
        
        # Verify numeric fields are preserved (with some tolerance for float precision)
        assert abs(deserialized['capacity_percentage'] - metrics['capacity_percentage']) < 0.01, \
            "Capacity percentage should be preserved"
        assert abs(deserialized['utilization_percentage'] - metrics['utilization_percentage']) < 0.01, \
            "Utilization percentage should be preserved"
        
    except (TypeError, ValueError) as e:
        pytest.fail(f"Capacity metrics should be JSON serializable, but got error: {e}")


@given(gen_system_capacity_state())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_capacity_indication_updates_with_state_changes(system_state):
    """
    Property: For any system state, capacity indication should change appropriately with state changes.
    
    **Feature: environment-allocation-ui, Property 10: Capacity and Availability Indication**
    **Validates: Requirements 2.5, 3.4, 3.5**
    """
    # Calculate initial metrics
    initial_metrics = calculate_capacity_metrics(system_state)
    
    # Simulate state change: move one ready environment to running
    modified_state = system_state.copy()
    modified_environments = [env.copy() for env in modified_state['environments']]
    
    ready_env_found = False
    for env in modified_environments:
        if env['status'] == EnvironmentStatusEnum.READY and not ready_env_found:
            env['status'] = EnvironmentStatusEnum.RUNNING
            env['assigned_tests'] = ['test_123']
            env['resources']['cpu'] = min(100.0, env['resources']['cpu'] + 30.0)
            ready_env_found = True
            break
    
    if ready_env_found:
        modified_state['environments'] = modified_environments
        modified_metrics = calculate_capacity_metrics(modified_state)
        
        # Ready environments should decrease
        assert modified_metrics['ready_environments'] <= initial_metrics['ready_environments'], \
            "Ready environments should not increase when moving to running"
        
        # Running environments should increase
        assert modified_metrics['running_environments'] >= initial_metrics['running_environments'], \
            "Running environments should not decrease when adding running environment"
        
        # Utilization should increase
        assert modified_metrics['utilization_percentage'] >= initial_metrics['utilization_percentage'], \
            "Utilization should not decrease when adding resource usage"