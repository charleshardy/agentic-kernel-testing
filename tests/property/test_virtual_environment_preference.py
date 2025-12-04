"""Property-based tests for virtual environment preference.

Feature: agentic-kernel-testing, Property 10: Virtual environment preference
Validates: Requirements 2.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List

from ai_generator.models import HardwareConfig, Peripheral
from execution.hardware_config import (
    HardwareClassifier,
    TestMatrixGenerator,
    TestMatrix
)


# Strategies for generating hardware configurations
@st.composite
def hardware_config_strategy(draw):
    """Generate a valid HardwareConfig object."""
    architectures = ['x86_64', 'arm64', 'riscv64', 'arm']
    storage_types = ['ssd', 'hdd', 'nvme', 'emmc', 'sd']
    
    architecture = draw(st.sampled_from(architectures))
    is_virtual = draw(st.booleans())
    
    # CPU models based on architecture
    cpu_models = {
        'x86_64': ['Intel Core i7', 'AMD Ryzen 9', 'Intel Xeon'],
        'arm64': ['ARM Cortex-A72', 'ARM Cortex-A53', 'Apple M1'],
        'arm': ['ARM Cortex-A53', 'ARM Cortex-A7'],
        'riscv64': ['SiFive U74', 'SiFive U54']
    }
    
    cpu_model = draw(st.sampled_from(cpu_models[architecture]))
    memory_mb = draw(st.integers(min_value=512, max_value=32768))
    storage_type = draw(st.sampled_from(storage_types))
    
    # Emulator only for virtual configs
    emulator = None
    if is_virtual:
        emulator = draw(st.sampled_from(['qemu', 'kvm']))
    
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
def mixed_config_list_strategy(draw):
    """Generate a list of configs with both virtual and physical."""
    num_configs = draw(st.integers(min_value=2, max_value=20))
    
    configs = []
    architectures = draw(st.lists(
        st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']),
        min_size=1,
        max_size=3,
        unique=True
    ))
    
    memory_sizes = draw(st.lists(
        st.integers(min_value=1024, max_value=8192),
        min_size=1,
        max_size=3,
        unique=True
    ))
    
    # Create both virtual and physical configs for each arch/memory combo
    for arch in architectures:
        for memory in memory_sizes:
            # Virtual config
            configs.append(HardwareConfig(
                architecture=arch,
                cpu_model=f'CPU-{arch}',
                memory_mb=memory,
                is_virtual=True,
                emulator='qemu'
            ))
            
            # Physical config
            configs.append(HardwareConfig(
                architecture=arch,
                cpu_model=f'CPU-{arch}',
                memory_mb=memory,
                is_virtual=False,
                emulator=None
            ))
    
    # Shuffle to mix virtual and physical
    import random
    random.shuffle(configs)
    
    return configs


@pytest.mark.property
class TestVirtualEnvironmentPreferenceProperties:
    """Property-based tests for virtual environment preference."""
    
    @given(configs=mixed_config_list_strategy())
    @settings(max_examples=100)
    def test_virtual_environment_preference_ordering(self, configs):
        """
        Property 10: Virtual environment preference
        
        For any test that can run on both virtual and physical hardware, 
        the system should execute on virtual hardware first when both are available.
        
        This property verifies that:
        1. When sorting configs, virtual configs come before physical
        2. The ordering is stable and deterministic
        3. Virtual configs are prioritized regardless of other attributes
        """
        # Assume we have both virtual and physical configs
        has_virtual = any(c.is_virtual for c in configs)
        has_physical = any(not c.is_virtual for c in configs)
        assume(has_virtual and has_physical)
        
        # Sort configs to prefer virtual
        sorted_configs = HardwareClassifier.prefer_virtual(configs)
        
        # Property 1: All virtual configs should come before all physical configs
        first_physical_index = None
        last_virtual_index = None
        
        for i, config in enumerate(sorted_configs):
            if config.is_virtual:
                last_virtual_index = i
            else:
                if first_physical_index is None:
                    first_physical_index = i
        
        if last_virtual_index is not None and first_physical_index is not None:
            assert last_virtual_index < first_physical_index, \
                f"All virtual configs should come before physical configs. " \
                f"Last virtual at index {last_virtual_index}, " \
                f"first physical at index {first_physical_index}"
        
        # Property 2: The number of configs should be preserved
        assert len(sorted_configs) == len(configs), \
            "Sorting should preserve all configurations"
        
        # Property 3: Virtual configs should be at the beginning
        virtual_count = sum(1 for c in configs if c.is_virtual)
        for i in range(virtual_count):
            assert sorted_configs[i].is_virtual, \
                f"Config at index {i} should be virtual, but is physical"
        
        # Property 4: Physical configs should be at the end
        for i in range(virtual_count, len(sorted_configs)):
            assert not sorted_configs[i].is_virtual, \
                f"Config at index {i} should be physical, but is virtual"
    
    @given(
        architecture=st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']),
        memory_mb=st.integers(min_value=1024, max_value=8192)
    )
    @settings(max_examples=100)
    def test_virtual_preferred_for_equivalent_configs(self, architecture, memory_mb):
        """
        Property: When equivalent virtual and physical configs exist, virtual is preferred.
        
        This tests that for the same architecture and memory, virtual configs
        are selected first.
        """
        # Create equivalent virtual and physical configs
        virtual_config = HardwareConfig(
            architecture=architecture,
            cpu_model=f'CPU-{architecture}',
            memory_mb=memory_mb,
            is_virtual=True,
            emulator='qemu'
        )
        
        physical_config = HardwareConfig(
            architecture=architecture,
            cpu_model=f'CPU-{architecture}',
            memory_mb=memory_mb,
            is_virtual=False,
            emulator=None
        )
        
        configs = [physical_config, virtual_config]  # Physical first intentionally
        
        # Sort to prefer virtual
        sorted_configs = HardwareClassifier.prefer_virtual(configs)
        
        # Property: Virtual config should be first
        assert sorted_configs[0].is_virtual, \
            "Virtual config should be preferred over physical"
        assert not sorted_configs[1].is_virtual, \
            "Physical config should come after virtual"
    
    @given(configs=mixed_config_list_strategy())
    @settings(max_examples=100)
    def test_preference_with_architecture_filter(self, configs):
        """
        Property: Virtual preference should work with architecture filtering.
        
        When filtering by architecture, virtual configs of that architecture
        should still be preferred over physical.
        """
        # Get unique architectures in the config list
        architectures = list(set(c.architecture for c in configs))
        assume(len(architectures) > 0)
        
        for arch in architectures:
            # Filter and sort by architecture
            sorted_configs = HardwareClassifier.prefer_virtual(configs, architecture=arch)
            
            # Skip if no configs for this architecture
            if len(sorted_configs) == 0:
                continue
            
            # Property 1: All configs should have the requested architecture
            assert all(c.architecture == arch for c in sorted_configs), \
                f"All configs should have architecture '{arch}'"
            
            # Property 2: Virtual configs should come first
            has_virtual = any(c.is_virtual for c in sorted_configs)
            has_physical = any(not c.is_virtual for c in sorted_configs)
            
            if has_virtual and has_physical:
                # Find the transition point
                first_physical_idx = next(
                    i for i, c in enumerate(sorted_configs) if not c.is_virtual
                )
                
                # All configs before transition should be virtual
                for i in range(first_physical_idx):
                    assert sorted_configs[i].is_virtual, \
                        f"Config at index {i} should be virtual"
                
                # All configs after transition should be physical
                for i in range(first_physical_idx, len(sorted_configs)):
                    assert not sorted_configs[i].is_virtual, \
                        f"Config at index {i} should be physical"
    
    @given(configs=st.lists(hardware_config_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_preference_is_stable(self, configs):
        """
        Property: Virtual preference sorting should be stable and deterministic.
        
        Sorting the same list multiple times should produce the same result.
        """
        # Sort twice
        sorted_1 = HardwareClassifier.prefer_virtual(configs)
        sorted_2 = HardwareClassifier.prefer_virtual(configs)
        
        # Property: Results should be identical
        assert len(sorted_1) == len(sorted_2), \
            "Sorting should produce same number of configs"
        
        for i, (c1, c2) in enumerate(zip(sorted_1, sorted_2)):
            assert c1.architecture == c2.architecture, \
                f"Config {i}: architectures should match"
            assert c1.memory_mb == c2.memory_mb, \
                f"Config {i}: memory should match"
            assert c1.is_virtual == c2.is_virtual, \
                f"Config {i}: virtual status should match"
    
    @given(
        architectures=st.lists(
            st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']),
            min_size=1,
            max_size=3,
            unique=True
        ),
        memory_sizes=st.lists(
            st.integers(min_value=1024, max_value=8192),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_matrix_generation_prefers_virtual(self, architectures, memory_sizes):
        """
        Property: Test matrix should list virtual configs before physical.
        
        When generating a matrix with both virtual and physical configs,
        the virtual configs should be accessible first.
        """
        # Generate matrix with both virtual and physical
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=architectures,
            memory_sizes=memory_sizes,
            virtual_only=False
        )
        
        # Get virtual and physical configs
        virtual_configs = matrix.get_virtual_configs()
        physical_configs = matrix.get_physical_configs()
        
        # Property 1: Both types should exist
        assert len(virtual_configs) > 0, "Should have virtual configs"
        assert len(physical_configs) > 0, "Should have physical configs"
        
        # Property 2: Virtual configs should be retrievable separately
        assert all(c.is_virtual for c in virtual_configs), \
            "get_virtual_configs() should only return virtual configs"
        
        # Property 3: Physical configs should be retrievable separately
        assert all(not c.is_virtual for c in physical_configs), \
            "get_physical_configs() should only return physical configs"
        
        # Property 4: When sorted, virtual should come first
        sorted_configs = HardwareClassifier.prefer_virtual(matrix.configurations)
        
        virtual_count = len(virtual_configs)
        for i in range(virtual_count):
            assert sorted_configs[i].is_virtual, \
                f"First {virtual_count} configs should be virtual"
    
    @given(configs=mixed_config_list_strategy())
    @settings(max_examples=100)
    def test_equivalent_configs_identification(self, configs):
        """
        Property: System should correctly identify equivalent virtual/physical configs.
        
        For any config, the system should find its equivalent counterpart
        (same arch/memory, different virtual/physical status).
        """
        # Pick a random config
        assume(len(configs) > 0)
        ref_config = configs[0]
        
        # Find equivalent configs
        equivalents = HardwareClassifier.get_equivalent_configs(ref_config, configs)
        
        # Property 1: Equivalent configs should have same architecture and memory
        for equiv in equivalents:
            assert equiv.architecture == ref_config.architecture, \
                "Equivalent config should have same architecture"
            assert equiv.memory_mb == ref_config.memory_mb, \
                "Equivalent config should have same memory"
        
        # Property 2: Equivalent configs should not include the reference config itself
        assert ref_config not in equivalents, \
            "Equivalent configs should not include the reference config"
        
        # Property 3: If an equivalent exists with opposite virtual status, it should be found
        opposite_virtual = not ref_config.is_virtual
        has_opposite = any(
            c.architecture == ref_config.architecture and
            c.memory_mb == ref_config.memory_mb and
            c.is_virtual == opposite_virtual
            for c in configs
        )
        
        if has_opposite:
            found_opposite = any(c.is_virtual == opposite_virtual for c in equivalents)
            assert found_opposite, \
                "Should find equivalent config with opposite virtual status"
    
    @given(
        num_virtual=st.integers(min_value=1, max_value=10),
        num_physical=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_preference_ratio_preservation(self, num_virtual, num_physical):
        """
        Property: Sorting should preserve the ratio of virtual to physical configs.
        
        The number of virtual and physical configs should remain the same after sorting.
        """
        # Create configs with specific ratio
        configs = []
        
        for i in range(num_virtual):
            configs.append(HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel',
                memory_mb=2048 + i * 1024,
                is_virtual=True,
                emulator='qemu'
            ))
        
        for i in range(num_physical):
            configs.append(HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel',
                memory_mb=2048 + i * 1024,
                is_virtual=False,
                emulator=None
            ))
        
        # Shuffle
        import random
        random.shuffle(configs)
        
        # Sort to prefer virtual
        sorted_configs = HardwareClassifier.prefer_virtual(configs)
        
        # Property: Counts should be preserved
        sorted_virtual_count = sum(1 for c in sorted_configs if c.is_virtual)
        sorted_physical_count = sum(1 for c in sorted_configs if not c.is_virtual)
        
        assert sorted_virtual_count == num_virtual, \
            f"Virtual count should be preserved: expected {num_virtual}, got {sorted_virtual_count}"
        assert sorted_physical_count == num_physical, \
            f"Physical count should be preserved: expected {num_physical}, got {sorted_physical_count}"
    
    @given(configs=mixed_config_list_strategy())
    @settings(max_examples=100)
    def test_virtual_preference_does_not_lose_configs(self, configs):
        """
        Property: Virtual preference sorting should not lose any configurations.
        
        All original configs should be present in the sorted result.
        """
        sorted_configs = HardwareClassifier.prefer_virtual(configs)
        
        # Property 1: Same number of configs
        assert len(sorted_configs) == len(configs), \
            "Sorting should not lose any configurations"
        
        # Property 2: All original configs should be findable in sorted list
        for original in configs:
            found = False
            for sorted_config in sorted_configs:
                if (sorted_config.architecture == original.architecture and
                    sorted_config.cpu_model == original.cpu_model and
                    sorted_config.memory_mb == original.memory_mb and
                    sorted_config.is_virtual == original.is_virtual):
                    found = True
                    break
            
            assert found, \
                f"Original config not found in sorted list: {original.architecture}, " \
                f"{original.memory_mb}MB, virtual={original.is_virtual}"
