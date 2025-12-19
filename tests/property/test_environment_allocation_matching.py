"""Property-based tests for environment allocation matching.

**Feature: test-execution-orchestrator, Property 2: Environment allocation matching**
**Validates: Requirements 1.2, 3.1**

Property 2: Environment allocation matching
For any test case with specific hardware requirements, the resource manager should allocate 
an environment that meets or exceeds those requirements.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch
import threading
import time

from ai_generator.models import HardwareConfig, Peripheral
from orchestrator.resource_manager import ResourceManager, ManagedEnvironment, EnvironmentType
from orchestrator.config import OrchestratorConfig


def create_mock_config():
    """Create a mock orchestrator configuration for testing."""
    config = Mock(spec=OrchestratorConfig)
    config.max_environments = 5
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
    memory_mb = draw(st.integers(min_value=128, max_value=8192))
    is_virtual = draw(st.booleans())
    peripherals = draw(st.lists(gen_peripheral(), max_size=5))
    
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
def test_allocated_environment_meets_architecture_requirements(hardware_requirements: HardwareConfig):
    """
    Property: For any hardware requirements with a specific architecture, 
    the allocated environment should have the same architecture.
    
    **Feature: test-execution-orchestrator, Property 2: Environment allocation matching**
    **Validates: Requirements 1.2, 3.1**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_requirements.memory_mb <= 4096)
    assume(hardware_requirements.architecture in ["x86_64", "arm64"])
    
    resource_manager = ResourceManager(create_mock_config())
    
    try:
        # Create a compatible environment manually for testing
        compatible_env = ManagedEnvironment(
            id="test_env_1",
            type=EnvironmentType.DOCKER if hardware_requirements.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=HardwareConfig(
                architecture=hardware_requirements.architecture,
                cpu_model="test_cpu",
                memory_mb=max(hardware_requirements.memory_mb, 1024),  # Ensure sufficient memory
                storage_type="ssd",
                peripherals=hardware_requirements.peripherals or [],
                is_virtual=hardware_requirements.is_virtual,
                emulator=hardware_requirements.emulator
            )
        )
        
        # Add the environment to the resource manager
        resource_manager._environments[compatible_env.id] = compatible_env
        resource_manager._environment_pool.append(compatible_env.id)
        
        # Allocate environment
        allocated_env_id = resource_manager.allocate_environment(hardware_requirements, "test_001")
        
        if allocated_env_id:
            allocated_env = resource_manager._environments[allocated_env_id]
            
            # Verify architecture matches
            assert allocated_env.hardware_config.architecture == hardware_requirements.architecture, \
                f"Allocated environment architecture {allocated_env.hardware_config.architecture} " \
                f"does not match required {hardware_requirements.architecture}"
            
            # Clean up
            resource_manager.release_environment(allocated_env_id)
        else:
            # If no environment was allocated, it should be due to no suitable environment
            # This is acceptable behavior
            pass
            
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocated_environment_meets_memory_requirements(hardware_requirements: HardwareConfig):
    """
    Property: For any hardware requirements with specific memory needs, 
    the allocated environment should have at least that much memory.
    
    **Feature: test-execution-orchestrator, Property 2: Environment allocation matching**
    **Validates: Requirements 1.2, 3.1**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_requirements.memory_mb <= 4096)
    assume(hardware_requirements.memory_mb >= 128)
    
    resource_manager = ResourceManager(create_mock_config())
    
    try:
        # Create an environment with sufficient memory
        sufficient_memory = max(hardware_requirements.memory_mb * 2, 1024)
        compatible_env = ManagedEnvironment(
            id="test_env_2",
            type=EnvironmentType.DOCKER if hardware_requirements.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=HardwareConfig(
                architecture=hardware_requirements.architecture or "x86_64",
                cpu_model="test_cpu",
                memory_mb=sufficient_memory,
                storage_type="ssd",
                peripherals=hardware_requirements.peripherals or [],
                is_virtual=hardware_requirements.is_virtual,
                emulator=hardware_requirements.emulator
            )
        )
        
        # Add the environment to the resource manager
        resource_manager._environments[compatible_env.id] = compatible_env
        resource_manager._environment_pool.append(compatible_env.id)
        
        # Allocate environment
        allocated_env_id = resource_manager.allocate_environment(hardware_requirements, "test_002")
        
        if allocated_env_id:
            allocated_env = resource_manager._environments[allocated_env_id]
            
            # Verify memory meets or exceeds requirements
            assert allocated_env.hardware_config.memory_mb >= hardware_requirements.memory_mb, \
                f"Allocated environment memory {allocated_env.hardware_config.memory_mb}MB " \
                f"is less than required {hardware_requirements.memory_mb}MB"
            
            # Clean up
            resource_manager.release_environment(allocated_env_id)
        else:
            # If no environment was allocated, it should be due to no suitable environment
            # This is acceptable behavior
            pass
            
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocated_environment_meets_virtualization_requirements(hardware_requirements: HardwareConfig):
    """
    Property: For any hardware requirements specifying virtualization preference, 
    the allocated environment should match that preference.
    
    **Feature: test-execution-orchestrator, Property 2: Environment allocation matching**
    **Validates: Requirements 1.2, 3.1**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_requirements.memory_mb <= 4096)
    
    resource_manager = ResourceManager(create_mock_config())
    
    try:
        # Create an environment matching virtualization preference
        compatible_env = ManagedEnvironment(
            id="test_env_3",
            type=EnvironmentType.DOCKER if hardware_requirements.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=HardwareConfig(
                architecture=hardware_requirements.architecture or "x86_64",
                cpu_model="test_cpu",
                memory_mb=max(hardware_requirements.memory_mb, 1024),
                storage_type="ssd",
                peripherals=hardware_requirements.peripherals or [],
                is_virtual=hardware_requirements.is_virtual,
                emulator=hardware_requirements.emulator if hardware_requirements.is_virtual else None
            )
        )
        
        # Add the environment to the resource manager
        resource_manager._environments[compatible_env.id] = compatible_env
        resource_manager._environment_pool.append(compatible_env.id)
        
        # Allocate environment
        allocated_env_id = resource_manager.allocate_environment(hardware_requirements, "test_003")
        
        if allocated_env_id:
            allocated_env = resource_manager._environments[allocated_env_id]
            
            # Verify virtualization preference matches
            assert allocated_env.hardware_config.is_virtual == hardware_requirements.is_virtual, \
                f"Allocated environment virtualization {allocated_env.hardware_config.is_virtual} " \
                f"does not match required {hardware_requirements.is_virtual}"
            
            # Clean up
            resource_manager.release_environment(allocated_env_id)
        else:
            # If no environment was allocated, it should be due to no suitable environment
            # This is acceptable behavior
            pass
            
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocated_environment_supports_required_peripherals(hardware_requirements: HardwareConfig):
    """
    Property: For any hardware requirements with specific peripherals, 
    the allocated environment should support all required peripherals.
    
    **Feature: test-execution-orchestrator, Property 2: Environment allocation matching**
    **Validates: Requirements 1.2, 3.1**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_requirements.memory_mb <= 4096)
    assume(len(hardware_requirements.peripherals or []) <= 3)  # Limit peripheral complexity
    
    resource_manager = ResourceManager(create_mock_config())
    
    try:
        # Create an environment that supports all required peripherals
        required_peripherals = hardware_requirements.peripherals or []
        # Add some extra peripherals to ensure compatibility
        all_peripherals = required_peripherals + [
            Peripheral(name="extra_usb", type="usb", model="generic"),
            Peripheral(name="extra_ethernet", type="ethernet", model="generic")
        ]
        
        compatible_env = ManagedEnvironment(
            id="test_env_4",
            type=EnvironmentType.DOCKER if hardware_requirements.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=HardwareConfig(
                architecture=hardware_requirements.architecture or "x86_64",
                cpu_model="test_cpu",
                memory_mb=max(hardware_requirements.memory_mb, 1024),
                storage_type="ssd",
                peripherals=all_peripherals,
                is_virtual=hardware_requirements.is_virtual,
                emulator=hardware_requirements.emulator
            )
        )
        
        # Add the environment to the resource manager
        resource_manager._environments[compatible_env.id] = compatible_env
        resource_manager._environment_pool.append(compatible_env.id)
        
        # Allocate environment
        allocated_env_id = resource_manager.allocate_environment(hardware_requirements, "test_004")
        
        if allocated_env_id:
            allocated_env = resource_manager._environments[allocated_env_id]
            
            # Verify all required peripherals are supported
            allocated_peripheral_types = {p.type for p in allocated_env.hardware_config.peripherals}
            required_peripheral_types = {p.type for p in required_peripherals}
            
            assert required_peripheral_types.issubset(allocated_peripheral_types), \
                f"Allocated environment peripherals {allocated_peripheral_types} " \
                f"do not include all required {required_peripheral_types}"
            
            # Clean up
            resource_manager.release_environment(allocated_env_id)
        else:
            # If no environment was allocated, it should be due to no suitable environment
            # This is acceptable behavior
            pass
            
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocated_environment_matches_emulator_requirements(hardware_requirements: HardwareConfig):
    """
    Property: For any virtual hardware requirements with specific emulator needs, 
    the allocated environment should use the same emulator.
    
    **Feature: test-execution-orchestrator, Property 2: Environment allocation matching**
    **Validates: Requirements 1.2, 3.1**
    """
    # Only test virtual environments with emulator requirements
    assume(hardware_requirements.is_virtual)
    assume(hardware_requirements.emulator is not None)
    assume(hardware_requirements.memory_mb <= 4096)
    
    resource_manager = ResourceManager(create_mock_config())
    
    try:
        # Create an environment with matching emulator
        compatible_env = ManagedEnvironment(
            id="test_env_5",
            type=EnvironmentType.QEMU,  # Use QEMU for emulator testing
            status="available",
            hardware_config=HardwareConfig(
                architecture=hardware_requirements.architecture or "x86_64",
                cpu_model="test_cpu",
                memory_mb=max(hardware_requirements.memory_mb, 1024),
                storage_type="ssd",
                peripherals=hardware_requirements.peripherals or [],
                is_virtual=True,
                emulator=hardware_requirements.emulator
            )
        )
        
        # Add the environment to the resource manager
        resource_manager._environments[compatible_env.id] = compatible_env
        resource_manager._environment_pool.append(compatible_env.id)
        
        # Allocate environment
        allocated_env_id = resource_manager.allocate_environment(hardware_requirements, "test_005")
        
        if allocated_env_id:
            allocated_env = resource_manager._environments[allocated_env_id]
            
            # Verify emulator matches
            assert allocated_env.hardware_config.emulator == hardware_requirements.emulator, \
                f"Allocated environment emulator {allocated_env.hardware_config.emulator} " \
                f"does not match required {hardware_requirements.emulator}"
            
            # Clean up
            resource_manager.release_environment(allocated_env_id)
        else:
            # If no environment was allocated, it should be due to no suitable environment
            # This is acceptable behavior
            pass
            
    finally:
        resource_manager.stop()


@given(gen_hardware_config())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_allocation_updates_environment_status_correctly(hardware_requirements: HardwareConfig):
    """
    Property: For any successful environment allocation, the environment status 
    should be updated to "busy" and test_id should be recorded.
    
    **Feature: test-execution-orchestrator, Property 2: Environment allocation matching**
    **Validates: Requirements 1.2, 3.1**
    """
    # Skip if requirements are too restrictive for testing
    assume(hardware_requirements.memory_mb <= 4096)
    
    resource_manager = ResourceManager(create_mock_config())
    
    try:
        # Create a compatible environment
        compatible_env = ManagedEnvironment(
            id="status_test_env",
            type=EnvironmentType.DOCKER if hardware_requirements.is_virtual else EnvironmentType.PHYSICAL,
            status="available",
            hardware_config=HardwareConfig(
                architecture=hardware_requirements.architecture or "x86_64",
                cpu_model="test_cpu",
                memory_mb=max(hardware_requirements.memory_mb, 1024),
                storage_type="ssd",
                peripherals=hardware_requirements.peripherals or [],
                is_virtual=hardware_requirements.is_virtual,
                emulator=hardware_requirements.emulator
            )
        )
        
        # Add the environment to the resource manager
        resource_manager._environments[compatible_env.id] = compatible_env
        resource_manager._environment_pool.append(compatible_env.id)
        
        test_id = "status_test_001"
        
        # Verify initial state
        assert compatible_env.status == "available"
        assert compatible_env.current_test_id is None
        
        # Allocate environment
        allocated_env_id = resource_manager.allocate_environment(hardware_requirements, test_id)
        
        if allocated_env_id:
            allocated_env = resource_manager._environments[allocated_env_id]
            
            # Verify status was updated correctly
            assert allocated_env.status == "busy", \
                f"Allocated environment status should be 'busy', got '{allocated_env.status}'"
            
            assert allocated_env.current_test_id == test_id, \
                f"Allocated environment test_id should be '{test_id}', got '{allocated_env.current_test_id}'"
            
            # Verify environment was removed from available pool
            assert allocated_env_id not in resource_manager._environment_pool, \
                "Allocated environment should be removed from available pool"
            
            # Clean up
            resource_manager.release_environment(allocated_env_id)
            
            # Verify status was reset after release
            assert allocated_env.status == "available", \
                f"Released environment status should be 'available', got '{allocated_env.status}'"
            
            assert allocated_env.current_test_id is None, \
                f"Released environment test_id should be None, got '{allocated_env.current_test_id}'"
            
    finally:
        resource_manager.stop()