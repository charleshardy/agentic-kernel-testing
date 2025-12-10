"""Property-based tests for configuration build verification.

**Feature: agentic-kernel-testing, Property 42: Configuration build verification**
**Validates: Requirements 9.2**

Tests that the system verifies successful build completion without errors or warnings
for any tested kernel configuration.
"""

import pytest
from hypothesis import given, strategies as st, assume
from pathlib import Path
import tempfile
import shutil
from typing import List, Dict, Any
from unittest.mock import Mock, patch
from contextlib import contextmanager

from execution.kernel_config_testing import (
    KernelConfigBuilder,
    KernelConfigValidator,
    KernelConfig,
    ConfigType,
    ConfigBuildResult
)


# Strategy for generating valid kernel configurations
def kernel_config_strategy():
    """Generate valid kernel configurations for testing."""
    return st.builds(
        KernelConfig,
        name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')),
        config_type=st.sampled_from([ConfigType.MINIMAL, ConfigType.DEFAULT, ConfigType.MAXIMAL]),
        options=st.dictionaries(
            keys=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')).map(lambda x: f"CONFIG_{x}"),
            values=st.sampled_from(['y', 'n', 'm']),
            min_size=1,
            max_size=20
        ),
        architecture=st.sampled_from(['x86_64', 'arm64', 'arm', 'riscv64']),
        description=st.text(max_size=100),
        metadata=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.booleans()),
            max_size=5
        )
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
            (arch_dir / "boot").mkdir()
        
        yield temp_dir
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestConfigurationBuildVerification:
    """Property-based tests for configuration build verification."""
    
    @given(config=kernel_config_strategy())
    def test_build_result_contains_verification_data(self, config):
        """
        **Property 42: Configuration build verification**
        
        For any tested kernel configuration, the system should verify successful 
        build completion and provide verification data including success status,
        errors, and warnings.
        
        **Validates: Requirements 9.2**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            builder = KernelConfigBuilder(kernel_source)
            
            # Mock the build process since we can't actually build kernels in tests
            with patch.object(builder, '_run_make_command') as mock_make:
                # Create a mock successful build result
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "Build successful"
                mock_result.stderr = ""
                mock_make.return_value = mock_result
                
                with patch.object(builder, '_find_kernel_image') as mock_find:
                    mock_image_path = kernel_source / "vmlinux"
                    mock_image_path.touch()
                    mock_find.return_value = mock_image_path
                    
                    # Act
                    result = builder.build_config(config, timeout=60)
            
            # Assert - Verify build verification data is present
            assert isinstance(result, ConfigBuildResult), (
                "Build should return ConfigBuildResult instance"
            )
            
            # Verify required verification fields are present
            assert hasattr(result, 'success'), "Build result should have success field"
            assert hasattr(result, 'build_time'), "Build result should have build_time field"
            assert hasattr(result, 'errors'), "Build result should have errors field"
            assert hasattr(result, 'warnings'), "Build result should have warnings field"
            assert hasattr(result, 'build_log'), "Build result should have build_log field"
            
            # Verify field types
            assert isinstance(result.success, bool), "success should be boolean"
            assert isinstance(result.build_time, (int, float)), "build_time should be numeric"
            assert isinstance(result.errors, list), "errors should be list"
            assert isinstance(result.warnings, list), "warnings should be list"
            assert isinstance(result.build_log, str), "build_log should be string"
            
            # Verify configuration is preserved
            assert result.config == config, "Original configuration should be preserved in result"
    
    @given(config=kernel_config_strategy())
    def test_successful_build_verification_properties(self, config):
        """
        **Property 42: Configuration build verification**
        
        For any successfully built kernel configuration, the verification should 
        confirm success without errors and provide build artifacts.
        
        **Validates: Requirements 9.2**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            builder = KernelConfigBuilder(kernel_source)
            
            # Mock successful build
            with patch.object(builder, '_run_make_command') as mock_make:
                mock_result = Mock()
                mock_result.returncode = 0  # Success
                mock_result.stdout = "CC kernel/main.o\nLD vmlinux\nBuild successful"
                mock_result.stderr = ""
                mock_make.return_value = mock_result
                
                with patch.object(builder, '_find_kernel_image') as mock_find:
                    mock_image_path = kernel_source / "vmlinux"
                    mock_image_path.touch()
                    mock_find.return_value = mock_image_path
                    
                    # Act
                    result = builder.build_config(config, timeout=60)
            
            # Assert - Verify successful build verification properties
            assert result.success is True, (
                "Successful build should have success=True"
            )
            
            assert len(result.errors) == 0, (
                f"Successful build should have no errors, got: {result.errors}"
            )
            
            assert result.build_time >= 0, (
                f"Build time should be non-negative, got: {result.build_time}"
            )
            
            assert result.kernel_image_path is not None, (
                "Successful build should have kernel image path"
            )
            
            assert result.size_bytes is not None and result.size_bytes >= 0, (
                f"Successful build should have non-negative size, got: {result.size_bytes}"
            )
            
            assert len(result.build_log) > 0, (
                "Successful build should have non-empty build log"
            )
    
    @given(config=kernel_config_strategy())
    def test_failed_build_verification_properties(self, config):
        """
        **Property 42: Configuration build verification**
        
        For any failed kernel configuration build, the verification should 
        properly identify failure and capture error information.
        
        **Validates: Requirements 9.2**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            builder = KernelConfigBuilder(kernel_source)
            
            # Mock failed build
            with patch.object(builder, '_run_make_command') as mock_make:
                mock_result = Mock()
                mock_result.returncode = 1  # Failure
                mock_result.stdout = "CC kernel/main.o"
                mock_result.stderr = "error: undefined reference to 'missing_function'"
                mock_make.return_value = mock_result
                
                with patch.object(builder, '_find_kernel_image') as mock_find:
                    mock_find.return_value = None  # No image for failed build
                    
                    # Act
                    result = builder.build_config(config, timeout=60)
            
            # Assert - Verify failed build verification properties
            assert result.success is False, (
                "Failed build should have success=False"
            )
            
            assert result.build_time >= 0, (
                f"Build time should be non-negative even for failures, got: {result.build_time}"
            )
            
            assert result.kernel_image_path is None, (
                "Failed build should not have kernel image path"
            )
            
            assert result.size_bytes is None, (
                "Failed build should not have size information"
            )
            
            assert len(result.build_log) > 0, (
                "Failed build should have non-empty build log for debugging"
            )
    
    @given(config=kernel_config_strategy())
    def test_build_with_warnings_verification(self, config):
        """
        **Property 42: Configuration build verification**
        
        For any kernel configuration build that succeeds with warnings, 
        the verification should capture and report the warnings.
        
        **Validates: Requirements 9.2**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            builder = KernelConfigBuilder(kernel_source)
            
            # Mock build with warnings
            with patch.object(builder, '_run_make_command') as mock_make:
                mock_result = Mock()
                mock_result.returncode = 0  # Success but with warnings
                mock_result.stdout = "CC kernel/main.o\nLD vmlinux"
                mock_result.stderr = (
                    "warning: unused variable 'x'\n"
                    "warning: deprecated function call\n"
                    "Build completed with warnings"
                )
                mock_make.return_value = mock_result
                
                with patch.object(builder, '_find_kernel_image') as mock_find:
                    mock_image_path = kernel_source / "vmlinux"
                    mock_image_path.touch()
                    mock_find.return_value = mock_image_path
                    
                    # Act
                    result = builder.build_config(config, timeout=60)
            
            # Assert - Verify warning capture in successful build
            assert result.success is True, (
                "Build with warnings should still be successful"
            )
            
            assert len(result.warnings) > 0, (
                "Build with warnings should capture warning messages"
            )
            
            # Verify warnings contain expected content
            warning_text = ' '.join(result.warnings).lower()
            assert 'warning' in warning_text, (
                f"Warning messages should contain 'warning', got: {result.warnings}"
            )
            
            assert len(result.errors) == 0, (
                f"Successful build with warnings should have no errors, got: {result.errors}"
            )
    
    @given(config=kernel_config_strategy())
    def test_configuration_validation_before_build(self, config):
        """
        **Property 42: Configuration build verification**
        
        For any kernel configuration, the system should validate the configuration 
        before attempting to build and report validation issues.
        
        **Validates: Requirements 9.2**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            validator = KernelConfigValidator(kernel_source)
            
            # Act
            is_valid, errors, warnings = validator.validate_config(config)
            
            # Assert - Verify validation provides verification data
            assert isinstance(is_valid, bool), (
                "Validation should return boolean validity status"
            )
            
            assert isinstance(errors, list), (
                "Validation should return list of errors"
            )
            
            assert isinstance(warnings, list), (
                "Validation should return list of warnings"
            )
            
            # Verify consistency between validity and errors
            if is_valid:
                assert len(errors) == 0, (
                    f"Valid configuration should have no errors, got: {errors}"
                )
            else:
                assert len(errors) > 0, (
                    "Invalid configuration should have at least one error"
                )
            
            # Verify error messages are informative
            for error in errors:
                assert isinstance(error, str), "Error messages should be strings"
                assert len(error) > 0, "Error messages should not be empty"
            
            for warning in warnings:
                assert isinstance(warning, str), "Warning messages should be strings"
                assert len(warning) > 0, "Warning messages should not be empty"
    
    @given(
        configs=st.lists(kernel_config_strategy(), min_size=1, max_size=5)
    )
    def test_build_verification_consistency_across_configs(self, configs):
        """
        **Property 42: Configuration build verification**
        
        For any set of kernel configurations, the build verification should 
        provide consistent verification data structure and behavior.
        
        **Validates: Requirements 9.2**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            builder = KernelConfigBuilder(kernel_source)
            results = []
            
            # Mock builds with varying success/failure
            with patch.object(builder, '_run_make_command') as mock_make:
                with patch.object(builder, '_find_kernel_image') as mock_find:
                    
                    for i, config in enumerate(configs):
                        # Alternate between success and failure for variety
                        success = i % 2 == 0
                        
                        mock_result = Mock()
                        mock_result.returncode = 0 if success else 1
                        mock_result.stdout = "Build output"
                        mock_result.stderr = "" if success else "Build error"
                        mock_make.return_value = mock_result
                        
                        if success:
                            mock_image_path = kernel_source / f"vmlinux_{i}"
                            mock_image_path.touch()
                            mock_find.return_value = mock_image_path
                        else:
                            mock_find.return_value = None
                        
                        # Act
                        result = builder.build_config(config, timeout=60)
                        results.append(result)
            
            # Assert - Verify consistency across all results
            assert len(results) == len(configs), (
                "Should have one result per configuration"
            )
            
            for i, result in enumerate(results):
                # Verify all results have consistent structure
                assert isinstance(result, ConfigBuildResult), (
                    f"Result {i} should be ConfigBuildResult instance"
                )
                
                # Verify required fields are present and correctly typed
                assert isinstance(result.success, bool), (
                    f"Result {i} success should be boolean"
                )
                assert isinstance(result.build_time, (int, float)), (
                    f"Result {i} build_time should be numeric"
                )
                assert isinstance(result.errors, list), (
                    f"Result {i} errors should be list"
                )
                assert isinstance(result.warnings, list), (
                    f"Result {i} warnings should be list"
                )
                assert isinstance(result.build_log, str), (
                    f"Result {i} build_log should be string"
                )
                
                # Verify configuration preservation
                assert result.config == configs[i], (
                    f"Result {i} should preserve original configuration"
                )
                
                # Verify success/failure consistency
                expected_success = i % 2 == 0
                assert result.success == expected_success, (
                    f"Result {i} success should match expected: {expected_success}"
                )
    
    @given(config=kernel_config_strategy())
    def test_build_verification_serialization(self, config):
        """
        **Property 42: Configuration build verification**
        
        For any build verification result, the system should be able to 
        serialize and preserve all verification data.
        
        **Validates: Requirements 9.2**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            builder = KernelConfigBuilder(kernel_source)
            
            # Mock successful build
            with patch.object(builder, '_run_make_command') as mock_make:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "Build output"
                mock_result.stderr = "warning: test warning"
                mock_make.return_value = mock_result
                
                with patch.object(builder, '_find_kernel_image') as mock_find:
                    mock_image_path = kernel_source / "vmlinux"
                    mock_image_path.touch()
                    mock_find.return_value = mock_image_path
                    
                    # Act
                    result = builder.build_config(config, timeout=60)
            
            # Act - Serialize result
            result_dict = result.to_dict()
            
            # Assert - Verify serialization preserves verification data
            assert isinstance(result_dict, dict), (
                "Build result should serialize to dictionary"
            )
            
            # Verify all verification fields are preserved
            required_fields = [
                'config', 'success', 'build_time', 'kernel_image_path',
                'build_log', 'errors', 'warnings', 'size_bytes'
            ]
            
            for field in required_fields:
                assert field in result_dict, (
                    f"Serialized result should contain field: {field}"
                )
            
            # Verify field types in serialized form
            assert isinstance(result_dict['success'], bool)
            assert isinstance(result_dict['build_time'], (int, float))
            assert isinstance(result_dict['errors'], list)
            assert isinstance(result_dict['warnings'], list)
            assert isinstance(result_dict['build_log'], str)
            assert isinstance(result_dict['config'], dict)
            
            # Verify configuration is properly serialized
            config_dict = result_dict['config']
            assert config_dict['name'] == config.name
            assert config_dict['architecture'] == config.architecture
            assert config_dict['config_type'] == config.config_type.value