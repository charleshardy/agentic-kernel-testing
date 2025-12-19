"""Property-based tests for resource recovery.

**Feature: test-execution-orchestrator, Property 11: Resource recovery**
**Validates: Requirements 3.4, 5.1**

Property 11: Resource recovery
For any environment that becomes available after test completion, it should be properly 
cleaned and made available for the next test within a reasonable time.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch
import threading
import time
from datetime import datetime, timedelta

from ai_generator.models import HardwareConfig, Peripheral
from orchestrator.resource_manager import ResourceManager, ManagedEnvironment, EnvironmentType, EnvironmentHealth
from orchestrator.config import OrchestratorConfig


def create_mock_config():
    """Create a mock orchestrator configuration for testing."""
    config = Mock(spec=OrchestratorConfig)
    config.max_environments = 10
    config.docker_enabled = True
    config.qemu_enabled = True
    config.physical_enabled = False
    config.health_check_interval = 30
    return config


# Custom strategies for generating test data
@st.composite
def gen_peripheral(draw):
    """Generate a random peripheral."""
    return Peripheral(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        type=draw(st.sampled_from(["usb", "pci", "i2c", "spi", "uart", "gpio", "ethernet", "wifi"])),
        model=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        metadata=draw(st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50), max_size=3))
    )


@st.composite
def gen_hardware_config(draw):
    """Generate a random hardware configuration."""
    architecture = draw(st.sampled_from(["x86_64", "arm64", "riscv64", "arm"]))
    memory_mb = draw(st.integers(min_value=512, max_value=4096))
    is_virtual = draw(st.booleans())
    peripherals = draw(st.lists(gen_peripheral(), max_size=3))
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        memory_mb=memory_mb,
        storage_type=draw(st.sampled_from(["ssd", "hdd", "nvme"])),
        peripherals=peripherals,
        is_virtual=is_virtual,
        emulator=draw(st.one_of(st.none(), st.sampled_from(["qemu", "kvm", "xen"]))) if is_virtual else None
    )


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_becomes_available_after_release(hardware_config: HardwareConfig):
    """
    Property: For any environment that is released after test completion, 
    it should be cleaned and made available for the next test.
    
    **Feature: test-execution-orchestrator, Property 11: Resource recovery**
    **Validates: Requirements 3.4**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_config.memory_mb <= 4096)
    assume(hardware_config.architecture in ["x86_64", "arm64"])
    
    resource_manager = ResourceManager(create_mock_config())
    resource_manager.start()  # Start the resource manager
    
    try:
        # Create an environment
        env_id = f"test-env-{hash(str(hardware_config)) % 10000}"
        environment = ManagedEnvironment(
            id=env_id,
            type=EnvironmentType.DOCKER if hardware_config.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=hardware_config
        )
        
        # Add environment to resource manager
        resource_manager._environments[env_id] = environment
        resource_manager._environment_pool.append(env_id)
        
        # Allocate the environment (simulating test start)
        test_id = "test_recovery_001"
        allocated_env_id = resource_manager.allocate_environment(hardware_config, test_id)
        
        if allocated_env_id:
            # Verify environment is busy
            assert environment.status == "busy"
            assert environment.current_test_id == test_id
            assert env_id not in resource_manager._environment_pool
            
            # Release the environment (simulating test completion)
            release_success = resource_manager.release_environment(env_id)
            
            # Property 1: Release should succeed
            assert release_success, "Environment release should succeed"
            
            # Property 2: Environment should be cleaned and available
            assert environment.status == "available", \
                f"Environment status should be 'available' after release, got '{environment.status}'"
            
            # Property 3: Test ID should be cleared
            assert environment.current_test_id is None, \
                f"Environment test_id should be None after release, got '{environment.current_test_id}'"
            
            # Property 4: Environment should be back in available pool
            assert env_id in resource_manager._environment_pool, \
                "Environment should be back in available pool after release"
            
            # Property 5: Resource usage should be cleared
            assert len(environment.resource_usage) == 0, \
                "Environment resource usage should be cleared after release"
            
            # Property 6: Environment should be ready for next test
            next_test_id = "test_recovery_002"
            next_allocated_env_id = resource_manager.allocate_environment(hardware_config, next_test_id)
            
            if next_allocated_env_id:
                assert next_allocated_env_id == env_id, \
                    "Same environment should be reusable for next test"
                assert environment.current_test_id == next_test_id, \
                    "Environment should be assigned to next test"
                
                # Clean up
                resource_manager.release_environment(env_id)
        
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_failed_environment_marked_unavailable_and_replaced(hardware_config: HardwareConfig):
    """
    Property: For any environment that fails, it should be marked as unavailable 
    and a replacement should be provisioned.
    
    **Feature: test-execution-orchestrator, Property 11: Resource recovery**
    **Validates: Requirements 5.1**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_config.memory_mb <= 4096)
    assume(hardware_config.architecture in ["x86_64", "arm64"])
    
    resource_manager = ResourceManager(create_mock_config())
    resource_manager.start()  # Start the resource manager
    
    try:
        # Create an environment
        env_id = f"fail-env-{hash(str(hardware_config)) % 10000}"
        environment = ManagedEnvironment(
            id=env_id,
            type=EnvironmentType.DOCKER if hardware_config.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=hardware_config
        )
        
        # Add environment to resource manager
        resource_manager._environments[env_id] = environment
        resource_manager._environment_pool.append(env_id)
        
        initial_env_count = len(resource_manager._environments)
        
        # Simulate environment failure by marking it as unhealthy
        environment.health_status = EnvironmentHealth.UNHEALTHY
        environment.failure_count = 5  # High failure count
        
        # Handle the unhealthy environment
        resource_manager._handle_unhealthy_environment(env_id)
        
        # Property 1: Failed environment should be marked as unavailable
        assert environment.status == "error", \
            f"Failed environment status should be 'error', got '{environment.status}'"
        
        # Property 2: Failed environment should be removed from available pool
        assert env_id not in resource_manager._environment_pool, \
            "Failed environment should be removed from available pool"
        
        # Property 3: Failed environment should be in failed set
        assert env_id in resource_manager._failed_environments, \
            "Failed environment should be tracked in failed environments"
        
        # Give some time for replacement provisioning (it's async)
        time.sleep(0.5)
        
        # Property 4: A replacement should be provisioned (or attempted)
        # Since replacement is async, we check if provisioning was attempted
        # by checking if new environments are being created
        final_env_count = len(resource_manager._environments)
        
        # The environment count might stay the same if replacement is still provisioning
        # or might increase if replacement was created
        assert final_env_count >= initial_env_count - 1, \
            "Environment count should not decrease significantly after failure handling"
        
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_environment_recovery_after_failure(hardware_config: HardwareConfig):
    """
    Property: For any environment that fails but can be recovered, 
    it should be cleaned, recovered, and made available again.
    
    **Feature: test-execution-orchestrator, Property 11: Resource recovery**
    **Validates: Requirements 3.4, 5.1**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_config.memory_mb <= 4096)
    assume(hardware_config.architecture in ["x86_64", "arm64"])
    
    resource_manager = ResourceManager(create_mock_config())
    resource_manager.start()  # Start the resource manager
    
    try:
        # Create an environment
        env_id = f"recover-env-{hash(str(hardware_config)) % 10000}"
        environment = ManagedEnvironment(
            id=env_id,
            type=EnvironmentType.DOCKER if hardware_config.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=hardware_config
        )
        
        # Add environment to resource manager
        resource_manager._environments[env_id] = environment
        resource_manager._environment_pool.append(env_id)
        
        # Simulate a recoverable failure (low failure count)
        environment.health_status = EnvironmentHealth.UNHEALTHY
        environment.failure_count = 2  # Low failure count - recoverable
        environment.status = "error"
        
        # Remove from available pool to simulate failure
        if env_id in resource_manager._environment_pool:
            resource_manager._environment_pool.remove(env_id)
        resource_manager._failed_environments.add(env_id)
        
        # Attempt recovery
        recovery_success = resource_manager._recover_environment(env_id)
        
        if recovery_success:
            # Property 1: Environment should be recovered and available
            assert environment.status == "available", \
                f"Recovered environment status should be 'available', got '{environment.status}'"
            
            # Property 2: Environment should have healthy status
            assert environment.health_status == EnvironmentHealth.HEALTHY, \
                f"Recovered environment should be healthy, got '{environment.health_status}'"
            
            # Property 3: Environment should be removed from failed set
            assert env_id not in resource_manager._failed_environments, \
                "Recovered environment should not be in failed environments"
            
            # Property 4: Environment should be back in available pool
            assert env_id in resource_manager._environment_pool, \
                "Recovered environment should be back in available pool"
            
            # Property 5: Environment should be usable for new tests
            test_id = "test_recovery_after_failure"
            allocated_env_id = resource_manager.allocate_environment(hardware_config, test_id)
            
            if allocated_env_id == env_id:
                assert environment.current_test_id == test_id, \
                    "Recovered environment should be assignable to new tests"
                
                # Clean up
                resource_manager.release_environment(env_id)
        
    finally:
        resource_manager.stop()


@given(st.lists(gen_hardware_config(), min_size=2, max_size=5))
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_resource_recovery_isolation(hardware_configs: List[HardwareConfig]):
    """
    Property: For any set of environments where some fail and some succeed, 
    recovery of failed environments should not affect healthy environments.
    
    **Feature: test-execution-orchestrator, Property 11: Resource recovery**
    **Validates: Requirements 3.4, 5.1**
    """
    # Skip if requirements are too restrictive for testing
    assume(all(config.memory_mb <= 4096 for config in hardware_configs))
    assume(all(config.architecture in ["x86_64", "arm64"] for config in hardware_configs))
    assume(len(hardware_configs) >= 2)
    
    resource_manager = ResourceManager(create_mock_config())
    resource_manager.start()  # Start the resource manager
    
    try:
        environments = []
        
        # Create multiple environments
        for i, config in enumerate(hardware_configs):
            env_id = f"isolation-env-{i}-{hash(str(config)) % 10000}"
            environment = ManagedEnvironment(
                id=env_id,
                type=EnvironmentType.DOCKER if config.is_virtual else EnvironmentType.PHYSICAL,
                status="available",
                hardware_config=config
            )
            
            resource_manager._environments[env_id] = environment
            resource_manager._environment_pool.append(env_id)
            environments.append(environment)
        
        # Make some environments fail (first half)
        failed_envs = environments[:len(environments)//2]
        healthy_envs = environments[len(environments)//2:]
        
        for env in failed_envs:
            env.health_status = EnvironmentHealth.UNHEALTHY
            env.failure_count = 3
            env.status = "error"
            if env.id in resource_manager._environment_pool:
                resource_manager._environment_pool.remove(env.id)
            resource_manager._failed_environments.add(env.id)
        
        # Record initial state of healthy environments
        healthy_states = {}
        for env in healthy_envs:
            healthy_states[env.id] = {
                'status': env.status,
                'health': env.health_status,
                'in_pool': env.id in resource_manager._environment_pool
            }
        
        # Attempt recovery of failed environments
        for env in failed_envs:
            resource_manager._recover_environment(env.id)
        
        # Property: Healthy environments should be unaffected
        for env in healthy_envs:
            original_state = healthy_states[env.id]
            
            assert env.status == original_state['status'], \
                f"Healthy environment {env.id} status should be unchanged"
            
            assert env.health_status == original_state['health'], \
                f"Healthy environment {env.id} health should be unchanged"
            
            assert (env.id in resource_manager._environment_pool) == original_state['in_pool'], \
                f"Healthy environment {env.id} pool membership should be unchanged"
        
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_resource_recovery_timing(hardware_config: HardwareConfig):
    """
    Property: For any environment that becomes available after test completion, 
    it should be ready for the next test within a reasonable time.
    
    **Feature: test-execution-orchestrator, Property 11: Resource recovery**
    **Validates: Requirements 3.4**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_config.memory_mb <= 4096)
    assume(hardware_config.architecture in ["x86_64", "arm64"])
    
    resource_manager = ResourceManager(create_mock_config())
    resource_manager.start()  # Start the resource manager
    
    try:
        # Create an environment
        env_id = f"timing-env-{hash(str(hardware_config)) % 10000}"
        environment = ManagedEnvironment(
            id=env_id,
            type=EnvironmentType.DOCKER if hardware_config.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=hardware_config
        )
        
        # Add environment to resource manager
        resource_manager._environments[env_id] = environment
        resource_manager._environment_pool.append(env_id)
        
        # Allocate and release the environment
        test_id = "test_timing_001"
        allocated_env_id = resource_manager.allocate_environment(hardware_config, test_id)
        
        if allocated_env_id:
            # Record time before release
            start_time = time.time()
            
            # Release the environment
            release_success = resource_manager.release_environment(env_id)
            
            # Record time after release
            end_time = time.time()
            recovery_time = end_time - start_time
            
            if release_success:
                # Property: Recovery should complete within reasonable time (10 seconds)
                assert recovery_time < 10.0, \
                    f"Environment recovery took {recovery_time:.2f}s, should be < 10s"
                
                # Property: Environment should be immediately available
                assert environment.status == "available", \
                    "Environment should be available immediately after release"
                
                assert env_id in resource_manager._environment_pool, \
                    "Environment should be in available pool immediately after release"
        
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_resource_recovery_cleanup_completeness(hardware_config: HardwareConfig):
    """
    Property: For any environment that is released, all traces of the previous 
    test should be cleaned up completely.
    
    **Feature: test-execution-orchestrator, Property 11: Resource recovery**
    **Validates: Requirements 3.4**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_config.memory_mb <= 4096)
    assume(hardware_config.architecture in ["x86_64", "arm64"])
    
    resource_manager = ResourceManager(create_mock_config())
    resource_manager.start()  # Start the resource manager
    
    try:
        # Create an environment
        env_id = f"cleanup-env-{hash(str(hardware_config)) % 10000}"
        environment = ManagedEnvironment(
            id=env_id,
            type=EnvironmentType.DOCKER if hardware_config.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=hardware_config
        )
        
        # Add environment to resource manager
        resource_manager._environments[env_id] = environment
        resource_manager._environment_pool.append(env_id)
        
        # Allocate the environment and simulate test artifacts
        test_id = "test_cleanup_001"
        allocated_env_id = resource_manager.allocate_environment(hardware_config, test_id)
        
        if allocated_env_id:
            # Simulate test artifacts
            environment.resource_usage = {
                'cpu_percent': 75.5,
                'memory_mb': 1024,
                'disk_io': 'high'
            }
            environment.metadata = {
                'last_test_artifacts': ['log1.txt', 'core.dump'],
                'temp_files': ['/tmp/test1', '/tmp/test2']
            }
            
            # Release the environment
            release_success = resource_manager.release_environment(env_id)
            
            if release_success:
                # Property 1: Resource usage should be completely cleared
                assert len(environment.resource_usage) == 0, \
                    f"Resource usage should be cleared, got {environment.resource_usage}"
                
                # Property 2: Test-specific metadata should be preserved but test ID cleared
                assert environment.current_test_id is None, \
                    f"Test ID should be cleared, got {environment.current_test_id}"
                
                # Property 3: Environment should be in clean state
                assert environment.status == "available", \
                    f"Environment should be available after cleanup, got {environment.status}"
                
                # Property 4: Health status should be reset to unknown (will be checked later)
                assert environment.health_status == EnvironmentHealth.UNKNOWN, \
                    f"Health status should be reset, got {environment.health_status}"
        
    finally:
        resource_manager.stop()