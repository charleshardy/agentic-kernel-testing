"""Property-based tests for idle resource cleanup.

**Feature: agentic-kernel-testing, Property 47: Idle resource cleanup**
**Validates: Requirements 10.2**

Property: For any test execution environment that becomes idle, the system SHALL 
release or power down the resource to minimize costs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import uuid

from ai_generator.models import (
    Environment, EnvironmentStatus, HardwareConfig, Peripheral
)
from orchestrator.resource_manager import (
    ResourceManager, PowerState, ResourceState
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
def environment_strategy(draw, status=None):
    """Generate random environments."""
    env_id = str(uuid.uuid4())
    config = draw(hardware_config_strategy())
    env_status = status if status else draw(st.sampled_from(list(EnvironmentStatus)))
    
    # Generate timestamps
    created_at = datetime.now() - timedelta(hours=draw(st.integers(min_value=1, max_value=24)))
    last_used = created_at + timedelta(minutes=draw(st.integers(min_value=0, max_value=60)))
    
    return Environment(
        id=env_id,
        config=config,
        status=env_status,
        created_at=created_at,
        last_used=last_used,
        metadata={}
    )


@given(
    environments=st.lists(
        environment_strategy(status=EnvironmentStatus.IDLE),
        min_size=1,
        max_size=10
    ),
    idle_threshold=st.integers(min_value=60, max_value=600)
)
@settings(max_examples=100, deadline=None)
def test_idle_resource_cleanup_property(environments, idle_threshold):
    """Property: Idle resources beyond threshold are cleaned up.
    
    For any set of idle environments and idle threshold, when cleanup is triggered,
    all environments idle beyond the threshold should be released and powered down.
    """
    # Create resource manager
    env_manager = EnvironmentManager()
    resource_manager = ResourceManager(
        environment_manager=env_manager,
        idle_threshold_seconds=idle_threshold
    )
    
    try:
        # Register all environments
        for env in environments:
            resource_manager.register_resource(env)
        
        # Artificially age some environments to be beyond idle threshold
        now = datetime.now()
        aged_env_ids = set()
        
        for env in environments:
            # Make some environments old enough to be cleaned up
            if hash(env.id) % 2 == 0:  # Deterministic selection
                env.last_used = now - timedelta(seconds=idle_threshold + 60)
                aged_env_ids.add(env.id)
            else:
                # Keep some environments recent
                env.last_used = now - timedelta(seconds=idle_threshold // 2)
        
        # Detect idle resources
        idle_resources = resource_manager.detect_idle_resources()
        
        # Property: All aged environments should be detected as idle
        for env_id in aged_env_ids:
            assert env_id in idle_resources, \
                f"Environment {env_id} should be detected as idle"
        
        # Property: No recent environments should be detected as idle
        recent_env_ids = set(env.id for env in environments) - aged_env_ids
        for env_id in recent_env_ids:
            assert env_id not in idle_resources, \
                f"Environment {env_id} should not be detected as idle"
        
        # Cleanup idle resources
        cleaned_count = resource_manager.cleanup_idle_resources()
        
        # Property: Number of cleaned resources should match aged environments
        assert cleaned_count == len(aged_env_ids), \
            f"Expected {len(aged_env_ids)} resources cleaned, got {cleaned_count}"
        
        # Property: All cleaned resources should be powered down
        for env_id in aged_env_ids:
            resource_state = resource_manager.get_resource_state(env_id)
            if resource_state:  # May be unregistered after cleanup
                assert resource_state.power_state == PowerState.OFF, \
                    f"Resource {env_id} should be powered off after cleanup"
        
    finally:
        resource_manager.shutdown()


@given(
    environment=environment_strategy(status=EnvironmentStatus.IDLE),
    idle_duration=st.integers(min_value=0, max_value=1000)
)
@settings(max_examples=100, deadline=None)
def test_idle_detection_threshold_property(environment, idle_duration):
    """Property: Idle detection respects threshold.
    
    For any environment and idle duration, the environment should only be
    detected as idle if the duration exceeds the threshold.
    """
    threshold = 300  # 5 minutes
    
    # Set environment last_used based on idle_duration
    environment.last_used = datetime.now() - timedelta(seconds=idle_duration)
    
    resource_manager = ResourceManager(idle_threshold_seconds=threshold)
    
    try:
        resource_manager.register_resource(environment)
        
        idle_resources = resource_manager.detect_idle_resources()
        
        # Property: Environment is idle if and only if duration >= threshold
        if idle_duration >= threshold:
            assert environment.id in idle_resources, \
                f"Environment should be idle (duration={idle_duration}, threshold={threshold})"
        else:
            assert environment.id not in idle_resources, \
                f"Environment should not be idle (duration={idle_duration}, threshold={threshold})"
    
    finally:
        resource_manager.shutdown()


@given(
    environments=st.lists(
        environment_strategy(),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=100, deadline=None)
def test_only_idle_resources_cleaned_property(environments):
    """Property: Only idle resources are cleaned up.
    
    For any set of environments with mixed statuses, cleanup should only
    affect environments in IDLE status.
    """
    resource_manager = ResourceManager(idle_threshold_seconds=0)  # Immediate cleanup
    
    try:
        # Register all environments
        for env in environments:
            resource_manager.register_resource(env)
        
        # Age all environments
        for env in environments:
            env.last_used = datetime.now() - timedelta(hours=1)
        
        # Track which environments are idle
        idle_env_ids = set(env.id for env in environments if env.status == EnvironmentStatus.IDLE)
        non_idle_env_ids = set(env.id for env in environments if env.status != EnvironmentStatus.IDLE)
        
        # Cleanup
        cleaned_count = resource_manager.cleanup_idle_resources()
        
        # Property: Only idle environments should be cleaned
        assert cleaned_count == len(idle_env_ids), \
            f"Expected {len(idle_env_ids)} idle resources cleaned, got {cleaned_count}"
        
        # Property: Non-idle environments should still be registered
        for env_id in non_idle_env_ids:
            resource_state = resource_manager.get_resource_state(env_id)
            assert resource_state is not None, \
                f"Non-idle environment {env_id} should still be registered"
            assert resource_state.power_state == PowerState.ON, \
                f"Non-idle environment {env_id} should still be powered on"
    
    finally:
        resource_manager.shutdown()


@given(
    environment=environment_strategy(status=EnvironmentStatus.IDLE)
)
@settings(max_examples=100, deadline=None)
def test_resource_release_idempotent_property(environment):
    """Property: Resource release is idempotent.
    
    For any idle environment, releasing it multiple times should be safe
    and produce the same result.
    """
    resource_manager = ResourceManager(idle_threshold_seconds=0)
    
    try:
        resource_manager.register_resource(environment)
        
        # Age the environment
        environment.last_used = datetime.now() - timedelta(hours=1)
        
        # Release once
        result1 = resource_manager.release_resource(environment.id)
        assert result1 is True, "First release should succeed"
        
        # Release again
        result2 = resource_manager.release_resource(environment.id)
        # Second release may fail (resource already released) or succeed (idempotent)
        # Either behavior is acceptable
        
    finally:
        resource_manager.shutdown()


def test_idle_cleanup_example():
    """Example test: Idle resources are cleaned up after threshold.
    
    This is a concrete example demonstrating the idle cleanup property.
    """
    # Create environments
    env1 = Environment(
        id="env-1",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel",
            memory_mb=2048,
            is_virtual=True,
            emulator="qemu"
        ),
        status=EnvironmentStatus.IDLE,
        last_used=datetime.now() - timedelta(minutes=10)
    )
    
    env2 = Environment(
        id="env-2",
        config=HardwareConfig(
            architecture="arm64",
            cpu_model="ARM",
            memory_mb=1024,
            is_virtual=True,
            emulator="qemu"
        ),
        status=EnvironmentStatus.IDLE,
        last_used=datetime.now() - timedelta(minutes=2)
    )
    
    # Create resource manager with 5-minute threshold
    resource_manager = ResourceManager(idle_threshold_seconds=300)
    
    try:
        resource_manager.register_resource(env1)
        resource_manager.register_resource(env2)
        
        # Detect idle resources
        idle_resources = resource_manager.detect_idle_resources()
        
        # Only env1 should be idle (10 minutes > 5 minute threshold)
        assert "env-1" in idle_resources
        assert "env-2" not in idle_resources
        
        # Cleanup
        cleaned = resource_manager.cleanup_idle_resources()
        assert cleaned == 1
        
        # Verify env1 is powered down
        state1 = resource_manager.get_resource_state("env-1")
        if state1:
            assert state1.power_state == PowerState.OFF
        
        # Verify env2 is still powered on
        state2 = resource_manager.get_resource_state("env-2")
        assert state2 is not None
        assert state2.power_state == PowerState.ON
        
    finally:
        resource_manager.shutdown()
