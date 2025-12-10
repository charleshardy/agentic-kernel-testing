"""Property-based tests for configuration boot verification.

**Feature: agentic-kernel-testing, Property 43: Configuration boot verification**
**Validates: Requirements 9.3**

Tests that the system boots each successfully built kernel configuration 
and verifies basic functionality.
"""

import pytest
from hypothesis import given, strategies as st, assume
from pathlib import Path
import tempfile
import shutil
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

from execution.kernel_config_testing import (
    KernelConfigBootTester,
    KernelConfigTestOrchestrator,
    KernelConfig,
    ConfigType,
    ConfigBuildResult,
    ConfigBootResult,
    ConfigTestResult
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


def successful_build_result_strategy():
    """Generate successful build results for testing."""
    return st.builds(
        ConfigBuildResult,
        config=kernel_config_strategy(),
        success=st.just(True),
        build_time=st.floats(min_value=1.0, max_value=3600.0),
        kernel_image_path=st.just(Path("/tmp/test_kernel")),
        build_log=st.text(min_size=10, max_size=1000),
        errors=st.just([]),
        warnings=st.lists(st.text(min_size=1, max_size=100), max_size=5),
        size_bytes=st.integers(min_value=1024, max_value=100*1024*1024)
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


@contextmanager
def mock_boot_environment():
    """Create a mock boot test environment."""
    temp_dir = Path(tempfile.mkdtemp(prefix="mock_boot_"))
    
    try:
        # Create mock kernel image
        kernel_image = temp_dir / "vmlinux"
        kernel_image.write_bytes(b"mock kernel image data" * 1000)  # Make it reasonably sized
        
        yield temp_dir, kernel_image
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestConfigurationBootVerification:
    """Property-based tests for configuration boot verification."""
    
    @given(config=kernel_config_strategy(), build_result=successful_build_result_strategy())
    def test_boot_verification_attempts_for_successful_builds(self, config, build_result):
        """
        **Property 43: Configuration boot verification**
        
        For any successfully built kernel configuration, the system should 
        attempt to boot it and verify basic functionality.
        
        **Validates: Requirements 9.3**
        """
        # Arrange
        with mock_boot_environment() as (boot_dir, kernel_image):
            # Update build result to use our mock kernel image
            build_result.kernel_image_path = kernel_image
            build_result.config = config
            
            boot_tester = KernelConfigBootTester(boot_dir)
            
            # Mock QEMU availability check to avoid actual QEMU dependency
            with patch.object(boot_tester, '_is_qemu_available', return_value=False):
                # This will use validation-only boot testing
                
                # Act
                boot_result = boot_tester.boot_test_config(config, build_result)
        
        # Assert - Verify boot verification was attempted
        assert isinstance(boot_result, ConfigBootResult), (
            "Boot test should return ConfigBootResult instance"
        )
        
        # Verify required boot verification fields are present
        assert hasattr(boot_result, 'success'), "Boot result should have success field"
        assert hasattr(boot_result, 'boot_time'), "Boot result should have boot_time field"
        assert hasattr(boot_result, 'log'), "Boot result should have log field"
        assert hasattr(boot_result, 'errors'), "Boot result should have errors field"
        assert hasattr(boot_result, 'boot_stages'), "Boot result should have boot_stages field"
        
        # Verify field types
        assert isinstance(boot_result.success, bool), "success should be boolean"
        assert isinstance(boot_result.boot_time, (int, float)), "boot_time should be numeric"
        assert isinstance(boot_result.log, str), "log should be string"
        assert isinstance(boot_result.errors, list), "errors should be list"
        assert isinstance(boot_result.boot_stages, dict), "boot_stages should be dict"
        
        # Verify configuration is preserved
        assert boot_result.config == config, "Original configuration should be preserved in boot result"
        
        # Verify boot time is reasonable (non-negative)
        assert boot_result.boot_time >= 0, f"Boot time should be non-negative, got: {boot_result.boot_time}"
    
    @given(config=kernel_config_strategy(), build_result=successful_build_result_strategy())
    def test_successful_boot_verification_properties(self, config, build_result):
        """
        **Property 43: Configuration boot verification**
        
        For any successfully booted kernel configuration, the verification should 
        confirm boot success and provide boot diagnostics.
        
        **Validates: Requirements 9.3**
        """
        # Arrange
        with mock_boot_environment() as (boot_dir, kernel_image):
            build_result.kernel_image_path = kernel_image
            build_result.config = config
            
            boot_tester = KernelConfigBootTester(boot_dir)
            
            # Mock successful boot scenario
            with patch.object(boot_tester, '_is_qemu_available', return_value=False):
                # Mock validation to always succeed for this test
                with patch.object(boot_tester, '_validate_architecture_requirements') as mock_validate:
                    mock_validate.return_value = {'errors': [], 'log': ['Validation passed']}
                    
                    # Act
                    boot_result = boot_tester.boot_test_config(config, build_result)
        
        # Assert - Verify successful boot properties
        assert boot_result.success is True, (
            "Successful boot should have success=True"
        )
        
        assert len(boot_result.errors) == 0, (
            f"Successful boot should have no errors, got: {boot_result.errors}"
        )
        
        assert boot_result.boot_time >= 0, (
            f"Boot time should be non-negative, got: {boot_result.boot_time}"
        )
        
        assert len(boot_result.log) > 0, (
            "Successful boot should have non-empty log for diagnostics"
        )
        
        assert 'validation' in boot_result.boot_stages, (
            "Boot stages should include validation stage"
        )
        
        assert boot_result.boot_stages['validation'] is True, (
            "Validation stage should be successful"
        )
    
    @given(config=kernel_config_strategy())
    def test_failed_build_boot_verification_handling(self, config):
        """
        **Property 43: Configuration boot verification**
        
        For any failed kernel configuration build, the boot verification should 
        properly handle the failure and not attempt to boot.
        
        **Validates: Requirements 9.3**
        """
        # Arrange
        with mock_boot_environment() as (boot_dir, kernel_image):
            # Create failed build result
            failed_build_result = ConfigBuildResult(
                config=config,
                success=False,
                build_time=10.0,
                kernel_image_path=None,
                build_log="Build failed",
                errors=["Compilation error"],
                warnings=[],
                size_bytes=None
            )
            
            boot_tester = KernelConfigBootTester(boot_dir)
            
            # Act
            boot_result = boot_tester.boot_test_config(config, failed_build_result)
        
        # Assert - Verify failed build handling
        assert boot_result.success is False, (
            "Boot test of failed build should have success=False"
        )
        
        assert len(boot_result.errors) > 0, (
            "Boot test of failed build should have error messages"
        )
        
        assert boot_result.boot_time >= 0, (
            f"Boot time should be non-negative even for failures, got: {boot_result.boot_time}"
        )
        
        assert len(boot_result.log) > 0, (
            "Boot test should have log explaining why boot was not attempted"
        )
        
        # Verify error message indicates build failure
        error_text = ' '.join(boot_result.errors).lower()
        assert any(term in error_text for term in ['build', 'failed', 'image']), (
            f"Error should mention build failure or missing image, got: {boot_result.errors}"
        )
    
    @given(config=kernel_config_strategy(), build_result=successful_build_result_strategy())
    def test_boot_failure_diagnostics_capture(self, config, build_result):
        """
        **Property 43: Configuration boot verification**
        
        For any kernel configuration that fails to boot, the system should 
        capture diagnostic information about the failure.
        
        **Validates: Requirements 9.3**
        """
        # Arrange
        with mock_boot_environment() as (boot_dir, kernel_image):
            build_result.kernel_image_path = kernel_image
            build_result.config = config
            
            boot_tester = KernelConfigBootTester(boot_dir)
            
            # Mock boot failure scenario
            with patch.object(boot_tester, '_is_qemu_available', return_value=False):
                # Mock validation to fail for this test
                with patch.object(boot_tester, '_validate_architecture_requirements') as mock_validate:
                    mock_validate.return_value = {
                        'errors': ['Missing required CONFIG_ARCH option'],
                        'log': ['Architecture validation failed']
                    }
                    
                    # Act
                    boot_result = boot_tester.boot_test_config(config, build_result)
        
        # Assert - Verify failure diagnostics are captured
        assert boot_result.success is False, (
            "Failed boot should have success=False"
        )
        
        assert len(boot_result.errors) > 0, (
            "Failed boot should capture error diagnostics"
        )
        
        assert len(boot_result.log) > 0, (
            "Failed boot should capture diagnostic log information"
        )
        
        # Verify diagnostic information is informative
        for error in boot_result.errors:
            assert isinstance(error, str), "Error diagnostics should be strings"
            assert len(error) > 0, "Error diagnostics should not be empty"
        
        assert isinstance(boot_result.log, str), "Log should be string"
        assert len(boot_result.log) > 0, "Log should contain diagnostic information"
    
    @given(config=kernel_config_strategy(), build_result=successful_build_result_strategy())
    def test_boot_stages_tracking(self, config, build_result):
        """
        **Property 43: Configuration boot verification**
        
        For any boot verification attempt, the system should track boot stages 
        to provide detailed diagnostics.
        
        **Validates: Requirements 9.3**
        """
        # Arrange
        with mock_boot_environment() as (boot_dir, kernel_image):
            build_result.kernel_image_path = kernel_image
            build_result.config = config
            
            boot_tester = KernelConfigBootTester(boot_dir)
            
            # Mock boot with stage tracking
            with patch.object(boot_tester, '_is_qemu_available', return_value=False):
                # Act
                boot_result = boot_tester.boot_test_config(config, build_result)
        
        # Assert - Verify boot stages are tracked
        assert isinstance(boot_result.boot_stages, dict), (
            "Boot stages should be tracked in dictionary"
        )
        
        # Verify at least one stage is tracked
        assert len(boot_result.boot_stages) > 0, (
            "At least one boot stage should be tracked"
        )
        
        # Verify stage values are boolean
        for stage_name, stage_status in boot_result.boot_stages.items():
            assert isinstance(stage_name, str), (
                f"Stage name should be string, got: {type(stage_name)}"
            )
            assert isinstance(stage_status, bool), (
                f"Stage status should be boolean, got: {type(stage_status)} for stage {stage_name}"
            )
    
    @given(config=kernel_config_strategy(), build_result=successful_build_result_strategy())
    def test_orchestrator_integrates_boot_verification(self, config, build_result):
        """
        **Property 43: Configuration boot verification**
        
        For any configuration testing orchestration, boot verification should 
        be integrated into the overall testing process.
        
        **Validates: Requirements 9.3**
        """
        # Arrange
        with mock_kernel_source() as kernel_source:
            with mock_boot_environment() as (boot_dir, kernel_image):
                orchestrator = KernelConfigTestOrchestrator(
                    kernel_source_path=kernel_source,
                    build_dir=boot_dir,
                    max_parallel_builds=1
                )
                
                # Mock the build process to return our successful build result
                build_result.config = config
                build_result.kernel_image_path = kernel_image
                
                with patch.object(orchestrator.builder, 'build_config', return_value=build_result):
                    with patch.object(orchestrator.validator, 'validate_config', return_value=(True, [], [])):
                        # Act
                        test_result = orchestrator._test_single_config(config, timeout=60)
        
        # Assert - Verify boot verification is integrated
        assert isinstance(test_result, ConfigTestResult), (
            "Orchestrator should return ConfigTestResult"
        )
        
        # Verify boot verification fields are populated
        assert hasattr(test_result, 'boot_success'), (
            "Test result should include boot_success field"
        )
        assert hasattr(test_result, 'boot_time'), (
            "Test result should include boot_time field"
        )
        
        # Verify boot verification was attempted for successful build
        assert isinstance(test_result.boot_success, bool), (
            "boot_success should be boolean"
        )
        
        if test_result.boot_time is not None:
            assert isinstance(test_result.boot_time, (int, float)), (
                "boot_time should be numeric when present"
            )
            assert test_result.boot_time >= 0, (
                f"boot_time should be non-negative, got: {test_result.boot_time}"
            )
    
    @given(
        configs=st.lists(kernel_config_strategy(), min_size=1, max_size=3),
        build_results=st.lists(successful_build_result_strategy(), min_size=1, max_size=3)
    )
    def test_boot_verification_consistency_across_configs(self, configs, build_results):
        """
        **Property 43: Configuration boot verification**
        
        For any set of kernel configurations, boot verification should provide 
        consistent verification behavior and data structure.
        
        **Validates: Requirements 9.3**
        """
        # Ensure we have matching configs and build results
        assume(len(configs) == len(build_results))
        
        # Arrange
        with mock_boot_environment() as (boot_dir, kernel_image):
            boot_tester = KernelConfigBootTester(boot_dir)
            boot_results = []
            
            # Mock QEMU availability to use validation-only testing
            with patch.object(boot_tester, '_is_qemu_available', return_value=False):
                for config, build_result in zip(configs, build_results):
                    # Update build result to match config and use mock kernel image
                    build_result.config = config
                    build_result.kernel_image_path = kernel_image
                    
                    # Act
                    boot_result = boot_tester.boot_test_config(config, build_result)
                    boot_results.append(boot_result)
        
        # Assert - Verify consistency across all boot results
        assert len(boot_results) == len(configs), (
            "Should have one boot result per configuration"
        )
        
        for i, boot_result in enumerate(boot_results):
            # Verify all results have consistent structure
            assert isinstance(boot_result, ConfigBootResult), (
                f"Boot result {i} should be ConfigBootResult instance"
            )
            
            # Verify required fields are present and correctly typed
            assert isinstance(boot_result.success, bool), (
                f"Boot result {i} success should be boolean"
            )
            assert isinstance(boot_result.boot_time, (int, float)), (
                f"Boot result {i} boot_time should be numeric"
            )
            assert isinstance(boot_result.log, str), (
                f"Boot result {i} log should be string"
            )
            assert isinstance(boot_result.errors, list), (
                f"Boot result {i} errors should be list"
            )
            assert isinstance(boot_result.boot_stages, dict), (
                f"Boot result {i} boot_stages should be dict"
            )
            
            # Verify configuration preservation
            assert boot_result.config == configs[i], (
                f"Boot result {i} should preserve original configuration"
            )
            
            # Verify boot time is reasonable
            assert boot_result.boot_time >= 0, (
                f"Boot result {i} boot_time should be non-negative"
            )
    
    @given(config=kernel_config_strategy(), build_result=successful_build_result_strategy())
    def test_boot_verification_serialization(self, config, build_result):
        """
        **Property 43: Configuration boot verification**
        
        For any boot verification result, the system should be able to 
        serialize and preserve all boot verification data.
        
        **Validates: Requirements 9.3**
        """
        # Arrange
        with mock_boot_environment() as (boot_dir, kernel_image):
            build_result.kernel_image_path = kernel_image
            build_result.config = config
            
            boot_tester = KernelConfigBootTester(boot_dir)
            
            # Mock boot test
            with patch.object(boot_tester, '_is_qemu_available', return_value=False):
                # Act
                boot_result = boot_tester.boot_test_config(config, build_result)
        
        # Act - Serialize boot result
        result_dict = boot_result.to_dict()
        
        # Assert - Verify serialization preserves boot verification data
        assert isinstance(result_dict, dict), (
            "Boot result should serialize to dictionary"
        )
        
        # Verify all boot verification fields are preserved
        required_fields = [
            'config', 'success', 'boot_time', 'log', 'errors', 
            'boot_stages', 'kernel_version'
        ]
        
        for field in required_fields:
            assert field in result_dict, (
                f"Serialized boot result should contain field: {field}"
            )
        
        # Verify field types in serialized form
        assert isinstance(result_dict['success'], bool)
        assert isinstance(result_dict['boot_time'], (int, float))
        assert isinstance(result_dict['log'], str)
        assert isinstance(result_dict['errors'], list)
        assert isinstance(result_dict['boot_stages'], dict)
        assert isinstance(result_dict['config'], dict)
        
        # Verify configuration is properly serialized
        config_dict = result_dict['config']
        assert config_dict['name'] == config.name
        assert config_dict['architecture'] == config.architecture
        assert config_dict['config_type'] == config.config_type.value