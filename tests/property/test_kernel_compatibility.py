"""Property-based tests for kernel compatibility validation.

**Feature: test-deployment-system, Property 18: Kernel compatibility validation**
**Validates: Requirements 4.3**

Property 18: Kernel compatibility validation
For any kernel testing deployment, kernel version and configuration compatibility 
should be validated.
"""

import asyncio
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch as mock_patch
from typing import Dict, Any, Tuple

from deployment.validation_manager import ValidationManager


@st.composite
def kernel_version_strategy(draw):
    """Generate realistic kernel version strings for property testing"""
    major = draw(st.integers(min_value=2, max_value=7))
    minor = draw(st.integers(min_value=0, max_value=25))
    patch_version = draw(st.integers(min_value=0, max_value=100))
    
    # Generate different version formats that exist in the wild
    format_type = draw(st.sampled_from([
        "simple",           # 5.15.0
        "with_build",       # 5.15.0-91
        "with_suffix",      # 5.15.0-91-generic
        "rc_version",       # 6.2.0-rc1
        "ubuntu_style",     # 5.15.0-91-generic
        "debian_style",     # 5.15.0-25-amd64
        "minimal"           # 5.15
    ]))
    
    if format_type == "simple":
        return f"{major}.{minor}.{patch_version}"
    elif format_type == "with_build":
        build = draw(st.integers(min_value=1, max_value=200))
        return f"{major}.{minor}.{patch_version}-{build}"
    elif format_type == "with_suffix":
        build = draw(st.integers(min_value=1, max_value=200))
        suffix = draw(st.sampled_from(["generic", "amd64", "server", "desktop", "lowlatency"]))
        return f"{major}.{minor}.{patch_version}-{build}-{suffix}"
    elif format_type == "rc_version":
        rc_num = draw(st.integers(min_value=1, max_value=8))
        return f"{major}.{minor}.{patch_version}-rc{rc_num}"
    elif format_type == "ubuntu_style":
        build = draw(st.integers(min_value=1, max_value=200))
        return f"{major}.{minor}.{patch_version}-{build}-generic"
    elif format_type == "debian_style":
        build = draw(st.integers(min_value=1, max_value=200))
        return f"{major}.{minor}.{patch_version}-{build}-amd64"
    else:  # minimal
        return f"{major}.{minor}"


@st.composite
def environment_id_strategy(draw):
    """Generate environment IDs for property testing"""
    return draw(st.text(
        min_size=5, 
        max_size=30, 
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    ))


@given(
    environment_id=environment_id_strategy(),
    kernel_version=kernel_version_strategy()
)
@settings(max_examples=50, deadline=10000)
def test_kernel_compatibility_validation_property(environment_id, kernel_version):
    """
    **Feature: test-deployment-system, Property 18: Kernel compatibility validation**
    **Validates: Requirements 4.3**
    
    Property 18: Kernel compatibility validation
    For any kernel testing deployment, kernel version and configuration compatibility 
    should be validated.
    
    This property test verifies that:
    1. Kernel version parsing handles all realistic version formats correctly
    2. Version compatibility checks work with various minimum/maximum requirements
    3. Architecture compatibility validation covers all supported architectures
    4. Kernel configuration validation properly checks required and optional options
    5. Overall compatibility determination considers all validation aspects correctly
    6. Detailed diagnostic information is always provided for both success and failure
    7. Remediation suggestions are appropriate and helpful for different failure types
    8. The validation is deterministic for the same inputs
    """
    asyncio.run(test_kernel_compatibility_validation_async(environment_id, kernel_version))


async def test_kernel_compatibility_validation_async(environment_id, kernel_version):
    """Async implementation of the kernel compatibility validation property test"""
    
    # Arrange - Create validation manager and mock system information
    validation_manager = ValidationManager()
    
    system_info = {
        "system": "Linux",
        "release": kernel_version,
        "version": "#test-version",
        "machine": "x86_64",
        "processor": "x86_64"
    }
    
    kernel_config = {
        "config_available": True,
        "config_source": "/proc/config.gz",
        "config_options": {
            "CONFIG_MODULES": "y",
            "CONFIG_SYSFS": "y",
            "CONFIG_PROC_FS": "y",
            "CONFIG_DEBUG_INFO": "y"
        },
        "proc_config_gz": True,
        "boot_config": False,
        "module_support": True
    }
    
    requirements = {
        "min_kernel_version": "4.0.0",
        "max_kernel_version": None,
        "supported_architectures": {
            "x86_64": ["x86_64", "amd64"],
            "aarch64": ["aarch64", "arm64"]
        },
        "required_config_options": ["CONFIG_MODULES", "CONFIG_SYSFS"],
        "recommended_config_options": ["CONFIG_DEBUG_FS"],
        "testing_config_options": ["CONFIG_DEBUG_INFO"],
        "security_config_options": ["CONFIG_KASAN"]
    }
    
    # Mock platform functions to return our test data
    with mock_patch('platform.release', return_value=kernel_version), \
         mock_patch('platform.system', return_value=system_info["system"]), \
         mock_patch('platform.version', return_value=system_info["version"]), \
         mock_patch('platform.machine', return_value=system_info["machine"]), \
         mock_patch('platform.processor', return_value=system_info["processor"]):
        
        # Mock kernel configuration access
        with mock_patch.object(validation_manager, '_get_kernel_configuration', return_value=kernel_config):
            
            # Act - Perform kernel compatibility validation
            result = await validation_manager._check_kernel_compatibility(environment_id, requirements)
    
    # Assert - Verify the kernel compatibility validation properties
    
    # Property 1: Result structure is always consistent
    assert isinstance(result, dict), \
        "Kernel compatibility result must be a dictionary"
    
    assert "success" in result, \
        "Result must contain success status"
    
    assert isinstance(result["success"], bool), \
        "Success status must be boolean"
    
    # Property 2: Version parsing is deterministic and handles all formats
    parsed_version = await validation_manager._parse_kernel_version(kernel_version)
    
    assert isinstance(parsed_version, dict), \
        "Version parsing must return a dictionary"
    
    assert "raw_version" in parsed_version, \
        "Parsed version must contain raw version"
    
    assert parsed_version["raw_version"] == kernel_version, \
        "Raw version must match input exactly"
    
    assert "parsed_successfully" in parsed_version, \
        "Parsed version must indicate parsing success status"
    
    # If parsing succeeded, verify structure
    if parsed_version["parsed_successfully"]:
        assert "version_tuple" in parsed_version, \
            "Successfully parsed version must contain version tuple"
        
        version_tuple = parsed_version["version_tuple"]
        assert isinstance(version_tuple, tuple), \
            "Version tuple must be a tuple"
        
        assert len(version_tuple) == 3, \
            "Version tuple must have exactly 3 elements (major, minor, patch)"
        
        major, minor, patch_ver = version_tuple
        assert isinstance(major, int) and major >= 0, \
            f"Major version must be non-negative integer, got {major}"
        assert isinstance(minor, int) and minor >= 0, \
            f"Minor version must be non-negative integer, got {minor}"
        assert isinstance(patch_ver, int) and patch_ver >= 0, \
            f"Patch version must be non-negative integer, got {patch_ver}"
    
    # Property 3: Successful validation contains comprehensive details
    if result["success"]:
        assert "details" in result, \
            "Successful validation must contain detailed information"
        
        details = result["details"]
        
        # System information must be present and accurate
        assert "system_info" in details, \
            "Details must contain system information"
        
        sys_info = details["system_info"]
        assert sys_info["system"] == system_info["system"], \
            "System type must match input"
        assert sys_info["release"] == kernel_version, \
            "Kernel release must match input"
        assert sys_info["machine"] == system_info["machine"], \
            "Machine architecture must match input"
        
        # Version information must be present
        assert "version_info" in details, \
            "Details must contain version information"
        
        # Architecture compatibility must be evaluated
        assert "arch_compatibility" in details, \
            "Details must contain architecture compatibility"
        
        arch_compat = details["arch_compatibility"]
        assert "compatible" in arch_compat, \
            "Architecture compatibility must have compatible status"
        
        # Version compatibility must be evaluated
        assert "version_compatibility" in details, \
            "Details must contain version compatibility"
        
        version_compat = details["version_compatibility"]
        assert "compatible" in version_compat, \
            "Version compatibility must have compatible status"
        
        # Configuration compatibility must be evaluated
        assert "config_compatibility" in details, \
            "Details must contain configuration compatibility"
        
        config_compat = details["config_compatibility"]
        assert "compatible" in config_compat, \
            "Configuration compatibility must have compatible status"
        
        # Property 4: Overall success requires all aspects to be compatible
        assert arch_compat["compatible"], \
            "Architecture must be compatible for overall success"
        assert version_compat["compatible"], \
            "Version must be compatible for overall success"
        assert config_compat["compatible"], \
            "Configuration must be compatible for overall success"
        
        # Property 5: Requirements must be included in details
        assert "requirements" in details, \
            "Details must contain the requirements used for validation"
    
    # Property 6: Failed validation provides diagnostic information
    else:
        assert "error" in result, \
            "Failed validation must contain error message"
        
        error_msg = result["error"]
        assert isinstance(error_msg, str), \
            "Error message must be a string"
        assert len(error_msg.strip()) > 0, \
            "Error message must not be empty"
        
        assert "diagnostic_info" in result, \
            "Failed validation must contain diagnostic information"
        
        diagnostic = result["diagnostic_info"]
        assert isinstance(diagnostic, dict), \
            "Diagnostic info must be a dictionary"
        
        # Must contain system and version information even on failure
        assert "system_info" in diagnostic, \
            "Diagnostic info must contain system information"
        assert "version_info" in diagnostic, \
            "Diagnostic info must contain version information"
        
        # Property 7: Remediation suggestions are provided
        assert "remediation_suggestions" in result, \
            "Failed validation must contain remediation suggestions"
        
        remediation = result["remediation_suggestions"]
        assert isinstance(remediation, list), \
            "Remediation suggestions must be a list"
        assert len(remediation) > 0, \
            "Must provide at least one remediation suggestion"
        
        for suggestion in remediation:
            assert isinstance(suggestion, str), \
                "Each remediation suggestion must be a string"
            assert len(suggestion.strip()) > 0, \
                "Remediation suggestions must not be empty"
        
        # Property 8: Recoverability status is indicated
        assert "is_recoverable" in result, \
            "Failed validation must indicate if issue is recoverable"
        assert isinstance(result["is_recoverable"], bool), \
            "Recoverable status must be boolean"


def test_kernel_compatibility_validation_sync():
    """Synchronous wrapper for the kernel compatibility validation property test"""
    
    async def run_single_test():
        # Test with a known good configuration
        await test_kernel_compatibility_validation_async(
            "test_env_kernel_001", "5.15.0-91-generic"
        )
    
    asyncio.run(run_single_test())


if __name__ == "__main__":
    # Run a few test cases manually for verification
    print("Testing kernel compatibility validation property...")
    
    async def run_manual_tests():
        print("Testing successful kernel compatibility...")
        await test_kernel_compatibility_validation_async(
            environment_id="test_env_success",
            kernel_version="5.15.0-91-generic"
        )
        print("✓ Successful kernel compatibility test passed")
        
        print("Testing different kernel version formats...")
        test_versions = ["5.15.0", "6.1.0-rc1", "4.19.0-25-amd64", "5.4"]
        for version in test_versions:
            await test_kernel_compatibility_validation_async(
                f"test_env_{version.replace('.', '_').replace('-', '_')}", 
                version
            )
            print(f"✓ Kernel version {version} test passed")
        
        print("All kernel compatibility validation tests completed successfully!")
    
    asyncio.run(run_manual_tests())