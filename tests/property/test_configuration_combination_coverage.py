"""Property-based tests for configuration combination coverage.

**Feature: agentic-kernel-testing, Property 41: Configuration combination coverage**
**Validates: Requirements 9.1**

Tests that the system tests minimal, default, and maximal kernel configurations
for any configuration testing execution.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from pathlib import Path
import tempfile
import shutil
from typing import List
from contextlib import contextmanager

from execution.kernel_config_testing import (
    KernelConfigGenerator,
    KernelConfigTestOrchestrator,
    ConfigType,
    KernelConfig
)


# Strategy for generating valid architectures
architecture_strategy = st.sampled_from(['x86_64', 'arm64', 'arm', 'riscv64'])

# Strategy for generating lists of architectures
architectures_list_strategy = st.lists(
    architecture_strategy,
    min_size=1,
    max_size=3,
    unique=True
)


@contextmanager
def mock_kernel_source():
    """Create a mock kernel source directory for testing."""
    temp_dir = Path(tempfile.mkdtemp(prefix="mock_kernel_"))
    
    try:
        # Create basic kernel source structure
        (temp_dir / "Makefile").touch()
        (temp_dir / "Kconfig").touch()
        (temp_dir / "arch").mkdir()
        
        # Create architecture directories
        for arch in ['x86', 'arm', 'arm64', 'riscv']:
            arch_dir = temp_dir / "arch" / arch
            arch_dir.mkdir(parents=True)
            (arch_dir / "Kconfig").touch()
        
        yield temp_dir
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestConfigurationCombinationCoverage:
    """Property-based tests for configuration combination coverage."""
    
    @given(architectures=architectures_list_strategy)
    def test_standard_config_generation_covers_all_types(self, architectures):
        """
        **Property 41: Configuration combination coverage**
        
        For any configuration testing execution, the system should test minimal, 
        default, and maximal kernel configurations.
        
        **Validates: Requirements 9.1**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            generator = KernelConfigGenerator(kernel_source)
            
            # Act - Generate standard configurations for each architecture
            all_configs = []
            for arch in architectures:
                configs = generator.generate_all_standard_configs(arch)
                all_configs.extend(configs)
            
            # Assert - Check that all configuration types are covered for each architecture
            for arch in architectures:
                arch_configs = [c for c in all_configs if c.architecture == arch]
                
                # Extract config types for this architecture
                config_types = {c.config_type for c in arch_configs}
                
                # Verify all three standard types are present
                expected_types = {ConfigType.MINIMAL, ConfigType.DEFAULT, ConfigType.MAXIMAL}
                assert config_types == expected_types, (
                    f"Architecture {arch} missing config types. "
                    f"Expected: {expected_types}, Got: {config_types}"
                )
                
                # Verify exactly one config of each type
                for config_type in expected_types:
                    type_configs = [c for c in arch_configs if c.config_type == config_type]
                    assert len(type_configs) == 1, (
                        f"Architecture {arch} should have exactly one {config_type.value} config, "
                        f"got {len(type_configs)}"
                    )
    
    @given(architectures=architectures_list_strategy)
    def test_orchestrator_tests_all_standard_configurations(self, architectures):
        """
        **Property 41: Configuration combination coverage**
        
        For any orchestrated configuration testing, all standard configuration 
        combinations (minimal, default, maximal) should be tested.
        
        **Validates: Requirements 9.1**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            orchestrator = KernelConfigTestOrchestrator(
                kernel_source_path=kernel_source,
                max_parallel_builds=1  # Use single thread for testing
            )
            
            # Generate the configs that would be tested to verify coverage
            all_configs = []
            for arch in architectures:
                configs = orchestrator.generator.generate_all_standard_configs(arch)
                all_configs.extend(configs)
            
            # Assert - Verify configuration combination coverage
            for arch in architectures:
                arch_configs = [c for c in all_configs if c.architecture == arch]
                
                # Check that all three types are represented
                config_types = {c.config_type for c in arch_configs}
                expected_types = {ConfigType.MINIMAL, ConfigType.DEFAULT, ConfigType.MAXIMAL}
                
                assert config_types == expected_types, (
                    f"Standard configuration testing for {arch} should cover all types. "
                    f"Expected: {expected_types}, Got: {config_types}"
                )
    
    @given(
        architectures=architectures_list_strategy,
        config_type=st.sampled_from([ConfigType.MINIMAL, ConfigType.DEFAULT, ConfigType.MAXIMAL])
    )
    def test_individual_config_type_generation(self, architectures, config_type):
        """
        **Property 41: Configuration combination coverage**
        
        For any architecture and configuration type combination, the generator 
        should produce a valid configuration of the specified type.
        
        **Validates: Requirements 9.1**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            generator = KernelConfigGenerator(kernel_source)
            
            # Act & Assert
            for arch in architectures:
                if config_type == ConfigType.MINIMAL:
                    config = generator.generate_minimal_config(arch)
                elif config_type == ConfigType.DEFAULT:
                    config = generator.generate_default_config(arch)
                elif config_type == ConfigType.MAXIMAL:
                    config = generator.generate_maximal_config(arch)
                
                # Verify the generated config has correct properties
                assert config.config_type == config_type, (
                    f"Generated config should have type {config_type.value}, "
                    f"got {config.config_type.value}"
                )
                assert config.architecture == arch, (
                    f"Generated config should have architecture {arch}, "
                    f"got {config.architecture}"
                )
                assert config.name.startswith(config_type.value), (
                    f"Config name should start with type {config_type.value}, "
                    f"got {config.name}"
                )
                assert arch in config.name, (
                    f"Config name should contain architecture {arch}, "
                    f"got {config.name}"
                )
    
    @given(architectures=architectures_list_strategy)
    def test_config_type_distinctness(self, architectures):
        """
        **Property 41: Configuration combination coverage**
        
        For any architecture, the minimal, default, and maximal configurations 
        should be distinct from each other.
        
        **Validates: Requirements 9.1**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            generator = KernelConfigGenerator(kernel_source)
            
            # Act & Assert
            for arch in architectures:
                minimal = generator.generate_minimal_config(arch)
                default = generator.generate_default_config(arch)
                maximal = generator.generate_maximal_config(arch)
                
                configs = [minimal, default, maximal]
                
                # Verify all configs are for the same architecture
                for config in configs:
                    assert config.architecture == arch
                
                # Verify configs have different types
                config_types = {c.config_type for c in configs}
                assert len(config_types) == 3, (
                    f"Should have 3 distinct config types, got {len(config_types)}: {config_types}"
                )
                
                # Verify configs have different names
                config_names = {c.name for c in configs}
                assert len(config_names) == 3, (
                    f"Should have 3 distinct config names, got {len(config_names)}: {config_names}"
                )
                
                # Verify configs have different option sets (at least some differences)
                # Minimal should have fewer options enabled than default/maximal
                minimal_enabled = sum(1 for v in minimal.options.values() if v == 'y')
                default_enabled = sum(1 for v in default.options.values() if v == 'y')
                maximal_enabled = sum(1 for v in maximal.options.values() if v == 'y')
                
                # Minimal should have fewer enabled options than default
                assert minimal_enabled <= default_enabled, (
                    f"Minimal config should have <= enabled options than default. "
                    f"Minimal: {minimal_enabled}, Default: {default_enabled}"
                )
                
                # Maximal should have more or equal enabled options than default
                assert maximal_enabled >= default_enabled, (
                    f"Maximal config should have >= enabled options than default. "
                    f"Maximal: {maximal_enabled}, Default: {default_enabled}"
                )
    
    @given(architectures=architectures_list_strategy)
    def test_configuration_completeness_across_architectures(self, architectures):
        """
        **Property 41: Configuration combination coverage**
        
        For any set of architectures, configuration testing should provide 
        complete coverage across all architecture and type combinations.
        
        **Validates: Requirements 9.1**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            generator = KernelConfigGenerator(kernel_source)
            
            # Act
            all_configs = []
            for arch in architectures:
                configs = generator.generate_all_standard_configs(arch)
                all_configs.extend(configs)
            
            # Assert - Check complete coverage matrix
            expected_combinations = len(architectures) * 3  # 3 config types per architecture
            assert len(all_configs) == expected_combinations, (
                f"Should have {expected_combinations} configurations "
                f"({len(architectures)} architectures × 3 types), got {len(all_configs)}"
            )
            
            # Verify each architecture-type combination exists exactly once
            combinations = set()
            for config in all_configs:
                combination = (config.architecture, config.config_type)
                assert combination not in combinations, (
                    f"Duplicate combination found: {combination}"
                )
                combinations.add(combination)
            
            # Verify all expected combinations are present
            for arch in architectures:
                for config_type in [ConfigType.MINIMAL, ConfigType.DEFAULT, ConfigType.MAXIMAL]:
                    combination = (arch, config_type)
                    assert combination in combinations, (
                        f"Missing combination: architecture={arch}, type={config_type.value}"
                    )