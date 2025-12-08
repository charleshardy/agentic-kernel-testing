"""Property-based tests for resource metrics collection.

**Feature: agentic-kernel-testing, Property 50: Resource metrics collection**
**Validates: Requirements 10.5**

Property: While monitoring resource utilization, the system SHALL collect metrics 
on test execution time, resource consumption, and queue wait times.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import uuid
import time

from ai_generator.models import (
    Environment, EnvironmentStatus, HardwareConfig
)
from orchestrator.resource_manager import (
    ResourceManager, ResourceMetrics, PowerState
)
from execution.environment_manager import EnvironmentManager


# Strategies for generating test data
@st.composite
def hardware_config_strategy(draw):
    """Generate random hardware configurations."""
    architecture = draw(st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']))
    cpu_model = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    memory_mb = draw(st.integers(min_value=512, max_value=16384))
    storage_type = draw(st.sampled_from(['ssd', 'hdd', 'nvme']))
    is_virtual = draw(st.booleans())
    emulator = 'qemu' if is_virtual else None
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=cpu_model,
        memory_mb=memory_mb,
        storage_type=storage_type,
        peripherals=[],
        is_virtual=is_virtual,
        emulator=emulator
    )


@st.composite
def environment_strategy(draw):
    """Generate random environments."""
    env_id = str(uuid.uuid4())
    config = draw(hardware_config_strategy())
    status = draw(st.sampled_from(list(EnvironmentStatus)))
    
    return Environment(
        id=env_id,
        config=config,
        status=status,
        created_at=datetime.now(),
        last_used=datetime.now(),
        metadata={}
    )


@given(
    environments=st.lists(
        environment_strategy(),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, deadline=None)
def test_metrics_collection_completeness_property(environments):
    """Property: Metrics are collected for all registered resources.
    
    For any set of registered environments, metrics should be collected
    for each one, including uptime, busy time, idle time, and test executions.
    """
    resource_manager = ResourceManager()
    
    try:
        # Register all environments
        for env in environments:
            resource_manager.register_resource(env)
        
        # Get all metrics
        all_metrics = resource_manager.get_all_metrics()
        
        # Property: Metrics exist for all registered environments
        assert len(all_metrics) == len(environments), \
            f"Expected metrics for {len(environments)} environments, got {len(all_metrics)}"
        
        # Property: Each metric has required fields
        for metrics in all_metrics:
            assert metrics.environment_id is not None, "Metrics must have environment_id"
            assert metrics.total_uptime_seconds >= 0, "Uptime must be non-negative"
            assert metrics.total_busy_seconds >= 0, "Busy time must be non-negative"
            assert metrics.total_idle_seconds >= 0, "Idle time must be non-negative"
            assert metrics.test_executions >= 0, "Test executions must be non-negative"
            assert metrics.created_at is not None, "Metrics must have creation timestamp"
            
            # Property: Busy + Idle should not exceed uptime
            assert metrics.total_busy_seconds + metrics.total_idle_seconds <= metrics.total_uptime_seconds + 1, \
                "Busy + Idle time should not exceed uptime"
        
    finally:
        resource_manager.shutdown()


@given(
    environment=environment_strategy(),
    test_count=st.integers(min_value=0, max_value=20)
)
@settings(max_examples=100, deadline=None)
def test_test_execution_tracking_property(environment, test_count):
    """Property: Test execution count is accurately tracked.
    
    For any environment and number of test completions, the metrics should
    accurately reflect the number of tests executed.
    """
    resource_manager = ResourceManager()
    
    try:
        resource_manager.register_resource(environment)
        
        # Simulate test executions
        for _ in range(test_count):
            resource_manager.update_resource_usage(
                environment.id,
                EnvironmentStatus.BUSY,
                test_completed=False
            )
            resource_manager.update_resource_usage(
                environment.id,
                EnvironmentStatus.IDLE,
                test_completed=True
            )
        
        # Get metrics
        metrics = resource_manager.get_resource_metrics(environment.id)
        
        # Property: Test execution count matches
        assert metrics is not None, "Metrics should exist"
        assert metrics.test_executions == test_count, \
            f"Expected {test_count} test executions, got {metrics.test_executions}"
        
        # Property: If tests were executed, last_test_execution should be set
        if test_count > 0:
            assert metrics.last_test_execution is not None, \
                "last_test_execution should be set after test execution"
        
    finally:
        resource_manager.shutdown()


@given(
    environment=environment_strategy()
)
@settings(max_examples=100, deadline=None)
def test_utilization_rate_bounds_property(environment):
    """Property: Utilization rate is always between 0 and 1.
    
    For any environment with any usage pattern, the utilization rate
    should always be a valid percentage (0.0 to 1.0).
    """
    resource_manager = ResourceManager()
    
    try:
        resource_manager.register_resource(environment)
        
        # Simulate various usage patterns
        resource_manager.update_resource_usage(environment.id, EnvironmentStatus.BUSY)
        time.sleep(0.01)  # Small delay to accumulate time
        resource_manager.update_resource_usage(environment.id, EnvironmentStatus.IDLE)
        time.sleep(0.01)
        
        # Get metrics
        metrics = resource_manager.get_resource_metrics(environment.id)
        
        # Property: Utilization rate is bounded
        assert metrics is not None, "Metrics should exist"
        assert 0.0 <= metrics.utilization_rate <= 1.0, \
            f"Utilization rate {metrics.utilization_rate} must be between 0.0 and 1.0"
        
        # Property: Idle rate is bounded
        assert 0.0 <= metrics.idle_rate <= 1.0, \
            f"Idle rate {metrics.idle_rate} must be between 0.0 and 1.0"
        
        # Property: Utilization + Idle should not exceed 1.0 (with small tolerance)
        assert metrics.utilization_rate + metrics.idle_rate <= 1.01, \
            f"Utilization ({metrics.utilization_rate}) + Idle ({metrics.idle_rate}) should not exceed 1.0"
        
    finally:
        resource_manager.shutdown()


@given(
    environments=st.lists(
        environment_strategy(),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=100, deadline=None)
def test_utilization_summary_aggregation_property(environments):
    """Property: Utilization summary correctly aggregates across resources.
    
    For any set of environments, the utilization summary should correctly
    aggregate metrics across all resources.
    """
    resource_manager = ResourceManager()
    
    try:
        # Register all environments
        for env in environments:
            resource_manager.register_resource(env)
        
        # Simulate some usage
        for env in environments:
            if hash(env.id) % 2 == 0:
                resource_manager.update_resource_usage(env.id, EnvironmentStatus.BUSY)
                time.sleep(0.01)
        
        # Get summary
        summary = resource_manager.get_utilization_summary()
        
        # Property: Summary has required fields
        assert 'total_resources' in summary, "Summary must include total_resources"
        assert 'average_utilization' in summary, "Summary must include average_utilization"
        assert 'average_idle_rate' in summary, "Summary must include average_idle_rate"
        assert 'total_test_executions' in summary, "Summary must include total_test_executions"
        
        # Property: Total resources matches registered count
        assert summary['total_resources'] == len(environments), \
            f"Expected {len(environments)} resources, got {summary['total_resources']}"
        
        # Property: Average utilization is bounded
        assert 0.0 <= summary['average_utilization'] <= 1.0, \
            f"Average utilization {summary['average_utilization']} must be between 0.0 and 1.0"
        
        # Property: Average idle rate is bounded
        assert 0.0 <= summary['average_idle_rate'] <= 1.0, \
            f"Average idle rate {summary['average_idle_rate']} must be between 0.0 and 1.0"
        
        # Property: Test executions is non-negative
        assert summary['total_test_executions'] >= 0, \
            "Total test executions must be non-negative"
        
    finally:
        resource_manager.shutdown()


@given(
    environment=environment_strategy()
)
@settings(max_examples=100, deadline=None)
def test_metrics_persistence_across_updates_property(environment):
    """Property: Metrics accumulate correctly across multiple updates.
    
    For any environment, metrics should accumulate correctly as the
    environment transitions between states.
    """
    resource_manager = ResourceManager()
    
    try:
        resource_manager.register_resource(environment)
        
        # Get initial metrics
        initial_metrics = resource_manager.get_resource_metrics(environment.id)
        initial_uptime = initial_metrics.total_uptime_seconds
        
        # Perform multiple state transitions
        resource_manager.update_resource_usage(environment.id, EnvironmentStatus.BUSY)
        time.sleep(0.01)
        resource_manager.update_resource_usage(environment.id, EnvironmentStatus.IDLE)
        time.sleep(0.01)
        resource_manager.update_resource_usage(environment.id, EnvironmentStatus.BUSY)
        time.sleep(0.01)
        
        # Get updated metrics
        updated_metrics = resource_manager.get_resource_metrics(environment.id)
        
        # Property: Uptime should increase
        assert updated_metrics.total_uptime_seconds > initial_uptime, \
            "Uptime should increase over time"
        
        # Property: Either busy or idle time should have increased
        assert (updated_metrics.total_busy_seconds > 0 or 
                updated_metrics.total_idle_seconds > 0), \
            "Either busy or idle time should increase"
        
    finally:
        resource_manager.shutdown()


@given(
    environment=environment_strategy()
)
@settings(max_examples=100, deadline=None)
def test_cost_tracking_property(environment):
    """Property: Cost is tracked for all resources.
    
    For any registered environment, cost information should be available
    and should increase over time.
    """
    resource_manager = ResourceManager()
    
    try:
        resource_manager.register_resource(environment)
        
        # Get initial cost
        initial_cost = resource_manager.get_resource_cost(environment.id)
        
        # Property: Cost information exists
        assert initial_cost is not None, "Cost information should exist"
        assert initial_cost.hourly_rate > 0, "Hourly rate should be positive"
        assert initial_cost.total_cost >= 0, "Total cost should be non-negative"
        
        # Simulate some usage
        time.sleep(0.01)
        resource_manager.update_resource_usage(environment.id, EnvironmentStatus.BUSY)
        time.sleep(0.01)
        
        # Get updated cost
        updated_cost = resource_manager.get_resource_cost(environment.id)
        
        # Property: Cost should increase or stay the same
        assert updated_cost.total_cost >= initial_cost.total_cost, \
            "Cost should not decrease over time"
        
        # Property: Runtime hours should increase
        assert updated_cost.total_runtime_hours >= initial_cost.total_runtime_hours, \
            "Runtime hours should not decrease"
        
    finally:
        resource_manager.shutdown()


def test_metrics_collection_example():
    """Example test: Metrics are collected during resource usage.
    
    This is a concrete example demonstrating the metrics collection property.
    """
    # Create environment
    env = Environment(
        id="test-env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel",
            memory_mb=2048,
            is_virtual=True,
            emulator="qemu"
        ),
        status=EnvironmentStatus.IDLE
    )
    
    resource_manager = ResourceManager()
    
    try:
        # Register environment
        resource_manager.register_resource(env)
        
        # Simulate test execution
        resource_manager.update_resource_usage(env.id, EnvironmentStatus.BUSY, test_completed=False)
        time.sleep(0.02)
        resource_manager.update_resource_usage(env.id, EnvironmentStatus.IDLE, test_completed=True)
        time.sleep(0.01)
        
        # Get metrics
        metrics = resource_manager.get_resource_metrics(env.id)
        
        # Verify metrics are collected
        assert metrics is not None
        assert metrics.environment_id == "test-env"
        assert metrics.total_uptime_seconds > 0
        assert metrics.test_executions == 1
        assert metrics.last_test_execution is not None
        assert 0.0 <= metrics.utilization_rate <= 1.0
        assert 0.0 <= metrics.idle_rate <= 1.0
        
        # Get cost information
        cost = resource_manager.get_resource_cost(env.id)
        assert cost is not None
        assert cost.total_cost >= 0
        assert cost.hourly_rate > 0
        
        # Get utilization summary
        summary = resource_manager.get_utilization_summary()
        assert summary['total_resources'] == 1
        assert summary['total_test_executions'] == 1
        assert 0.0 <= summary['average_utilization'] <= 1.0
        
    finally:
        resource_manager.shutdown()


def test_metrics_to_dict_serialization():
    """Example test: Metrics can be serialized to dictionary.
    
    This verifies that metrics can be exported for reporting.
    """
    metrics = ResourceMetrics(
        environment_id="test-env",
        total_uptime_seconds=3600.0,
        total_busy_seconds=2400.0,
        total_idle_seconds=1200.0,
        test_executions=10,
        last_test_execution=datetime.now()
    )
    
    # Convert to dictionary
    metrics_dict = metrics.to_dict()
    
    # Verify all fields are present
    assert 'environment_id' in metrics_dict
    assert 'total_uptime_seconds' in metrics_dict
    assert 'total_busy_seconds' in metrics_dict
    assert 'total_idle_seconds' in metrics_dict
    assert 'test_executions' in metrics_dict
    assert 'utilization_rate' in metrics_dict
    assert 'idle_rate' in metrics_dict
    assert 'last_test_execution' in metrics_dict
    assert 'created_at' in metrics_dict
    
    # Verify calculated fields
    assert metrics_dict['utilization_rate'] == pytest.approx(2400.0 / 3600.0)
    assert metrics_dict['idle_rate'] == pytest.approx(1200.0 / 3600.0)
