"""Property-based tests for hardware matrix coverage.

Feature: agentic-kernel-testing, Property 6: Hardware matrix coverage
Validates: Requirements 2.1
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List

from ai_generator.models import HardwareConfig, Peripheral
from execution.hardware_config import (
    TestMatrixGenerator,
    TestMatrix,
    HardwareConfigParser
)


# Strategies for generating hardware configurations
@st.composite
def peripheral_strategy(draw):
    """Generate a Peripheral object."""
    peripheral_types = ['network', 'storage', 'serial', 'usb', 'pci', 'gpio']
    models = ['virtio-net', 'virtio-blk', 'pl011', 'ehci', 'generic', None]
    
    return Peripheral(
        name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Nd')))),
        type=draw(st.sampled_from(peripheral_types)),
        model=draw(st.sampled_from(models))
    )


@st.composite
def hardware_config_strategy(draw):
    """Generate a valid HardwareConfig object."""
    architectures = ['x86_64', 'arm64', 'riscv64', 'arm']
    storage_types = ['ssd', 'hdd', 'nvme', 'emmc', 'sd']
    emulators = ['qemu', 'kvm', 'bochs', None]
    
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
    
    # Generate peripherals
    num_peripherals = draw(st.integers(min_value=0, max_value=5))
    peripherals = [draw(peripheral_strategy()) for _ in range(num_peripherals)]
    
    # Emulator only for virtual configs
    emulator = None
    if is_virtual:
        emulator = draw(st.sampled_from(['qemu', 'kvm']))
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=cpu_model,
        memory_mb=memory_mb,
        storage_type=storage_type,
        peripherals=peripherals,
        is_virtual=is_virtual,
        emulator=emulator
    )


@st.composite
def test_matrix_params_strategy(draw):
    """Generate parameters for test matrix generation."""
    architectures = draw(st.lists(
        st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']),
        min_size=1,
        max_size=4,
        unique=True
    ))
    
    memory_sizes = draw(st.lists(
        st.integers(min_value=512, max_value=16384),
        min_size=1,
        max_size=5,
        unique=True
    ))
    
    virtual_only = draw(st.booleans())
    include_peripherals = draw(st.booleans())
    
    return {
        'architectures': architectures,
        'memory_sizes': memory_sizes,
        'virtual_only': virtual_only,
        'include_peripherals': include_peripherals
    }


@pytest.mark.property
class TestHardwareMatrixCoverageProperties:
    """Property-based tests for hardware matrix coverage."""
    
    @given(params=test_matrix_params_strategy())
    @settings(max_examples=100)
    def test_hardware_matrix_coverage_completeness(self, params):
        """
        Property 6: Hardware matrix coverage
        
        For any BSP test execution, tests should run on all hardware targets 
        configured in the test matrix, with no configured target being skipped.
        
        This property verifies that:
        1. All requested architectures appear in the generated matrix
        2. All requested memory sizes appear in the generated matrix
        3. Virtual/physical configurations are generated as requested
        4. No configurations are duplicated
        """
        matrix = TestMatrixGenerator.generate_matrix(**params)
        
        # Property 1: All requested architectures must be present
        matrix_architectures = {config.architecture for config in matrix.configurations}
        expected_architectures = set(params['architectures'])
        
        assert matrix_architectures == expected_architectures, \
            f"Matrix should contain all requested architectures. " \
            f"Expected: {expected_architectures}, Got: {matrix_architectures}"
        
        # Property 2: All requested memory sizes must be present
        matrix_memory_sizes = {config.memory_mb for config in matrix.configurations}
        expected_memory_sizes = set(params['memory_sizes'])
        
        assert matrix_memory_sizes == expected_memory_sizes, \
            f"Matrix should contain all requested memory sizes. " \
            f"Expected: {expected_memory_sizes}, Got: {matrix_memory_sizes}"
        
        # Property 3: Each architecture-memory combination should be present
        expected_combinations = len(params['architectures']) * len(params['memory_sizes'])
        if not params['virtual_only']:
            expected_combinations *= 2  # Both virtual and physical
        
        assert len(matrix.configurations) == expected_combinations, \
            f"Matrix should contain all architecture-memory combinations. " \
            f"Expected: {expected_combinations}, Got: {len(matrix.configurations)}"
        
        # Property 4: Virtual/physical configurations should match request
        virtual_configs = [c for c in matrix.configurations if c.is_virtual]
        physical_configs = [c for c in matrix.configurations if not c.is_virtual]
        
        if params['virtual_only']:
            assert len(physical_configs) == 0, \
                "virtual_only=True should produce no physical configurations"
            assert len(virtual_configs) == len(matrix.configurations), \
                "virtual_only=True should produce only virtual configurations"
        else:
            assert len(virtual_configs) > 0, \
                "virtual_only=False should produce some virtual configurations"
            assert len(physical_configs) > 0, \
                "virtual_only=False should produce some physical configurations"
        
        # Property 5: No duplicate configurations
        config_tuples = [
            (c.architecture, c.memory_mb, c.is_virtual)
            for c in matrix.configurations
        ]
        assert len(config_tuples) == len(set(config_tuples)), \
            "Matrix should not contain duplicate configurations"
    
    @given(configs=st.lists(hardware_config_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_matrix_from_configs_preserves_all_configs(self, configs):
        """
        Property: Generating a matrix from a list of configs should preserve all configs.
        
        This ensures that when we create a matrix from existing configurations,
        no configurations are lost or modified.
        """
        matrix = TestMatrixGenerator.generate_from_configs(configs)
        
        # Property 1: Matrix should contain exactly the same number of configs
        assert len(matrix.configurations) == len(configs), \
            f"Matrix should preserve all configurations. " \
            f"Expected: {len(configs)}, Got: {len(matrix.configurations)}"
        
        # Property 2: All original configs should be in the matrix
        for original_config in configs:
            found = False
            for matrix_config in matrix.configurations:
                if (matrix_config.architecture == original_config.architecture and
                    matrix_config.cpu_model == original_config.cpu_model and
                    matrix_config.memory_mb == original_config.memory_mb and
                    matrix_config.is_virtual == original_config.is_virtual):
                    found = True
                    break
            
            assert found, \
                f"Original config not found in matrix: {original_config.architecture}, " \
                f"{original_config.memory_mb}MB, virtual={original_config.is_virtual}"
    
    @given(params=test_matrix_params_strategy())
    @settings(max_examples=100)
    def test_matrix_filtering_by_architecture(self, params):
        """
        Property: Filtering matrix by architecture should return only matching configs.
        
        This ensures that matrix filtering operations work correctly and don't
        skip any configurations.
        """
        matrix = TestMatrixGenerator.generate_matrix(**params)
        
        for arch in params['architectures']:
            filtered_configs = matrix.get_by_architecture(arch)
            
            # Property 1: All filtered configs should have the requested architecture
            assert all(c.architecture == arch for c in filtered_configs), \
                f"All filtered configs should have architecture '{arch}'"
            
            # Property 2: Number of filtered configs should match expected count
            expected_count = len(params['memory_sizes'])
            if not params['virtual_only']:
                expected_count *= 2  # Both virtual and physical
            
            assert len(filtered_configs) == expected_count, \
                f"Should have {expected_count} configs for architecture '{arch}', " \
                f"got {len(filtered_configs)}"
            
            # Property 3: All memory sizes should be represented
            filtered_memory_sizes = {c.memory_mb for c in filtered_configs}
            expected_memory_sizes = set(params['memory_sizes'])
            
            assert filtered_memory_sizes == expected_memory_sizes, \
                f"Filtered configs should contain all memory sizes for '{arch}'"
    
    @given(params=test_matrix_params_strategy())
    @settings(max_examples=100)
    def test_matrix_virtual_physical_separation(self, params):
        """
        Property: Matrix should correctly separate virtual and physical configurations.
        
        This ensures that the matrix can be filtered by virtual/physical status
        without losing any configurations.
        """
        matrix = TestMatrixGenerator.generate_matrix(**params)
        
        virtual_configs = matrix.get_virtual_configs()
        physical_configs = matrix.get_physical_configs()
        
        # Property 1: Virtual and physical configs should be disjoint
        virtual_set = set(id(c) for c in virtual_configs)
        physical_set = set(id(c) for c in physical_configs)
        
        assert len(virtual_set.intersection(physical_set)) == 0, \
            "Virtual and physical config sets should be disjoint"
        
        # Property 2: Union of virtual and physical should equal total
        assert len(virtual_configs) + len(physical_configs) == len(matrix.configurations), \
            "Virtual + physical configs should equal total configs"
        
        # Property 3: All virtual configs should have is_virtual=True
        assert all(c.is_virtual for c in virtual_configs), \
            "All configs from get_virtual_configs() should have is_virtual=True"
        
        # Property 4: All physical configs should have is_virtual=False
        assert all(not c.is_virtual for c in physical_configs), \
            "All configs from get_physical_configs() should have is_virtual=False"
        
        # Property 5: Virtual configs should have emulators
        assert all(c.emulator is not None for c in virtual_configs), \
            "All virtual configs should have an emulator specified"
    
    @given(
        architectures=st.lists(
            st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']),
            min_size=1,
            max_size=3,
            unique=True
        ),
        memory_size=st.integers(min_value=1024, max_value=8192)
    )
    @settings(max_examples=100)
    def test_matrix_coverage_across_architectures(self, architectures, memory_size):
        """
        Property: For a given memory size, all architectures should be represented.
        
        This ensures that test coverage is uniform across architectures.
        """
        matrix = TestMatrixGenerator.generate_matrix(
            architectures=architectures,
            memory_sizes=[memory_size],
            virtual_only=True
        )
        
        # Property 1: Each architecture should have at least one config
        matrix_archs = {c.architecture for c in matrix.configurations}
        assert matrix_archs == set(architectures), \
            f"All architectures should be represented. " \
            f"Expected: {set(architectures)}, Got: {matrix_archs}"
        
        # Property 2: Each architecture should have exactly one config (virtual only)
        for arch in architectures:
            arch_configs = [c for c in matrix.configurations if c.architecture == arch]
            assert len(arch_configs) == 1, \
                f"Architecture '{arch}' should have exactly 1 config, got {len(arch_configs)}"
            assert arch_configs[0].memory_mb == memory_size, \
                f"Config for '{arch}' should have memory size {memory_size}"
    
    @given(params=test_matrix_params_strategy())
    @settings(max_examples=100)
    def test_matrix_serialization_preserves_coverage(self, params):
        """
        Property: Serializing and deserializing a matrix should preserve all configurations.
        
        This ensures that matrix data can be persisted and restored without loss.
        """
        original_matrix = TestMatrixGenerator.generate_matrix(**params)
        
        # Serialize to dict
        matrix_dict = original_matrix.to_dict()
        
        # Deserialize from dict
        restored_matrix = TestMatrix.from_dict(matrix_dict)
        
        # Property 1: Same number of configurations
        assert len(restored_matrix.configurations) == len(original_matrix.configurations), \
            "Restored matrix should have same number of configurations"
        
        # Property 2: All architectures preserved
        original_archs = {c.architecture for c in original_matrix.configurations}
        restored_archs = {c.architecture for c in restored_matrix.configurations}
        assert original_archs == restored_archs, \
            "Restored matrix should preserve all architectures"
        
        # Property 3: All memory sizes preserved
        original_memory = {c.memory_mb for c in original_matrix.configurations}
        restored_memory = {c.memory_mb for c in restored_matrix.configurations}
        assert original_memory == restored_memory, \
            "Restored matrix should preserve all memory sizes"
        
        # Property 4: Virtual/physical distribution preserved
        original_virtual_count = sum(1 for c in original_matrix.configurations if c.is_virtual)
        restored_virtual_count = sum(1 for c in restored_matrix.configurations if c.is_virtual)
        assert original_virtual_count == restored_virtual_count, \
            "Restored matrix should preserve virtual/physical distribution"
    
    @given(
        configs=st.lists(hardware_config_strategy(), min_size=2, max_size=10),
        architecture_filter=st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm', None])
    )
    @settings(max_examples=100)
    def test_no_configurations_skipped_in_filtering(self, configs, architecture_filter):
        """
        Property: Filtering operations should not skip any matching configurations.
        
        This ensures that all configurations matching the filter criteria are returned.
        """
        matrix = TestMatrixGenerator.generate_from_configs(configs)
        
        if architecture_filter:
            filtered = matrix.get_by_architecture(architecture_filter)
            
            # Count expected matches
            expected_matches = [c for c in configs if c.architecture == architecture_filter]
            
            # Property: All matching configs should be in filtered result
            assert len(filtered) == len(expected_matches), \
                f"Filter should return all matching configs. " \
                f"Expected: {len(expected_matches)}, Got: {len(filtered)}"
            
            # Property: No non-matching configs should be in filtered result
            assert all(c.architecture == architecture_filter for c in filtered), \
                f"Filtered result should only contain configs with architecture '{architecture_filter}'"
        else:
            # No filter - should return all configs
            all_configs = matrix.configurations
            assert len(all_configs) == len(configs), \
                "No filter should return all configurations"
    
    @given(params=test_matrix_params_strategy())
    @settings(max_examples=100)
    def test_matrix_metadata_consistency(self, params):
        """
        Property: Matrix metadata should accurately reflect the generation parameters.
        
        This ensures that matrix metadata can be used to understand how the matrix
        was generated.
        """
        matrix = TestMatrixGenerator.generate_matrix(**params)
        
        # Property 1: Metadata should contain generation parameters
        assert 'architectures' in matrix.metadata, \
            "Matrix metadata should contain architectures"
        assert 'memory_sizes' in matrix.metadata, \
            "Matrix metadata should contain memory_sizes"
        assert 'virtual_only' in matrix.metadata, \
            "Matrix metadata should contain virtual_only flag"
        
        # Property 2: Metadata should match actual configurations
        metadata_archs = set(matrix.metadata['architectures'])
        actual_archs = {c.architecture for c in matrix.configurations}
        assert metadata_archs == actual_archs, \
            "Metadata architectures should match actual configurations"
        
        metadata_memory = set(matrix.metadata['memory_sizes'])
        actual_memory = {c.memory_mb for c in matrix.configurations}
        assert metadata_memory == actual_memory, \
            "Metadata memory sizes should match actual configurations"
