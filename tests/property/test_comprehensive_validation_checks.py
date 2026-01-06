"""Property-based tests for comprehensive validation checks.

**Feature: test-deployment-system, Property 17: Comprehensive validation checks**
**Validates: Requirements 4.2**

Property 17: Comprehensive validation checks
For any readiness check execution, network connectivity, resource availability, 
and tool functionality should be verified.
"""

import asyncio
import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List

from deployment.validation_manager import ValidationManager, ValidationCheck, ValidationSeverity
from deployment.models import ValidationResult


@st.composite
def validation_config_strategy(draw):
    """Generate validation configurations for property testing"""
    return {
        "test_hosts": draw(st.lists(
            st.fixed_dictionaries({
                "host": st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-')),
                "port": st.integers(min_value=1, max_value=65535),
                "protocol": st.sampled_from(["tcp", "udp"]),
                "description": st.text(min_size=5, max_size=50)
            }),
            min_size=0,
            max_size=3
        )),
        "disk_paths": draw(st.lists(
            st.sampled_from(["/tmp", "/var", "/home", "/opt"]),
            min_size=0,
            max_size=4
        )),
        "additional_tools": draw(st.lists(
            st.fixed_dictionaries({
                "name": st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
                "command": st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3),
                "required": st.booleans(),
                "category": st.sampled_from(["custom", "testing", "development", "system"])
            }),
            min_size=0,
            max_size=2
        ))
    }


@st.composite
def environment_id_strategy(draw):
    """Generate environment IDs for property testing"""
    return draw(st.text(
        min_size=5, 
        max_size=30, 
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    ))


class MockValidationManager(ValidationManager):
    """Mock validation manager for testing"""
    
    def __init__(self, network_success=True, disk_success=True, memory_success=True, 
                 cpu_success=True, tool_success=True, permission_success=True, 
                 kernel_success=True):
        super().__init__()
        self.network_success = network_success
        self.disk_success = disk_success
        self.memory_success = memory_success
        self.cpu_success = cpu_success
        self.tool_success = tool_success
        self.permission_success = permission_success
        self.kernel_success = kernel_success
        
        # Track which checks were called
        self.checks_called = []
    
    async def _check_network_connectivity(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        self.checks_called.append("network_connectivity")
        if self.network_success:
            return {
                "success": True,
                "details": {
                    "connectivity_results": [
                        {"host": "8.8.8.8", "port": 53, "protocol": "tcp", "connected": True}
                    ],
                    "dns_resolution_results": [
                        {"domain": "google.com", "resolved": True}
                    ],
                    "connectivity_success_rate": 1.0,
                    "dns_success_rate": 1.0
                }
            }
        else:
            return {
                "success": False,
                "error": "Network connectivity failed",
                "diagnostic_info": {"connectivity_success_rate": 0.0},
                "remediation_suggestions": ["Check network configuration"],
                "is_recoverable": True
            }
    
    async def _check_disk_space(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        self.checks_called.append("disk_space")
        if self.disk_success:
            return {
                "success": True,
                "details": {
                    "disk_usage_results": [
                        {"path": "/", "used_percent": 50.0, "free_gb": 10.0, "status": "ok"}
                    ]
                }
            }
        else:
            return {
                "success": False,
                "error": "Insufficient disk space",
                "diagnostic_info": {"disk_usage_results": []},
                "remediation_suggestions": ["Clean up temporary files"],
                "is_recoverable": True
            }
    
    async def _check_memory_availability(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        self.checks_called.append("memory_availability")
        if self.memory_success:
            return {
                "success": True,
                "details": {"used_percent": 60.0, "available_gb": 2.0}
            }
        else:
            return {
                "success": False,
                "error": "Insufficient memory",
                "diagnostic_info": {"used_percent": 98.0},
                "remediation_suggestions": ["Close unnecessary applications"],
                "is_recoverable": True
            }
    
    async def _check_cpu_availability(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        self.checks_called.append("cpu_availability")
        if self.cpu_success:
            return {
                "success": True,
                "details": {"cpu_percent": 30.0, "cpu_count": 4}
            }
        else:
            return {
                "success": False,
                "error": "High CPU usage",
                "diagnostic_info": {"cpu_percent": 98.0},
                "remediation_suggestions": ["Check for high CPU processes"],
                "is_recoverable": True
            }
    
    async def _check_tool_functionality(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        self.checks_called.append("tool_functionality")
        if self.tool_success:
            return {
                "success": True,
                "details": {
                    "tool_results": [
                        {"name": "python3", "available": True, "required": True}
                    ],
                    "statistics": {"required_availability_rate": 100.0}
                }
            }
        else:
            return {
                "success": False,
                "error": "Required tools not available",
                "diagnostic_info": {"failed_required_tools": ["python3"]},
                "remediation_suggestions": ["Install missing required tools"],
                "is_recoverable": True
            }
    
    async def _check_environment_permissions(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        self.checks_called.append("environment_permissions")
        if self.permission_success:
            return {
                "success": True,
                "details": {"permission_checks": [{"check": "temp_directory_write", "success": True}]}
            }
        else:
            return {
                "success": False,
                "error": "Permission checks failed",
                "diagnostic_info": {"permission_checks": []},
                "remediation_suggestions": ["Check file system permissions"],
                "is_recoverable": True
            }
    
    async def _check_kernel_compatibility(self, environment_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        self.checks_called.append("kernel_compatibility")
        if self.kernel_success:
            return {
                "success": True,
                "details": {
                    "system_info": {
                        "system": "Linux",
                        "release": "5.15.0-91-generic",
                        "machine": "x86_64",
                        "processor": "x86_64"
                    },
                    "version_info": {
                        "raw_version": "5.15.0-91-generic",
                        "major": 5,
                        "minor": 15,
                        "patch": 0,
                        "version_tuple": (5, 15, 0),
                        "parsed_successfully": True
                    },
                    "kernel_config": {
                        "config_available": True,
                        "config_source": "/proc/config.gz",
                        "config_options": {
                            "CONFIG_MODULES": "y",
                            "CONFIG_SYSFS": "y",
                            "CONFIG_PROC_FS": "y",
                            "CONFIG_DEBUG_INFO": "y"
                        }
                    },
                    "arch_compatibility": {
                        "compatible": True,
                        "current_architecture": "x86_64",
                        "machine": "x86_64",
                        "processor": "x86_64"
                    },
                    "version_compatibility": {
                        "compatible": True,
                        "current_version": (5, 15, 0),
                        "min_version": (3, 10, 0)
                    },
                    "config_compatibility": {
                        "compatible": True,
                        "missing_required": [],
                        "missing_recommended": [],
                        "available_testing": ["CONFIG_DEBUG_INFO"],
                        "available_security": []
                    }
                }
            }
        else:
            return {
                "success": False,
                "error": "Kernel compatibility validation failed",
                "diagnostic_info": {
                    "system_info": {
                        "system": "Linux",
                        "release": "2.6.32",
                        "machine": "i386",
                        "processor": "i386"
                    },
                    "version_info": {
                        "raw_version": "2.6.32",
                        "version_tuple": (2, 6, 32),
                        "parsed_successfully": True
                    },
                    "version_compatibility": {
                        "compatible": False,
                        "current_version": (2, 6, 32),
                        "min_version": (3, 10, 0)
                    },
                    "arch_compatibility": {
                        "compatible": False,
                        "current_architecture": None,
                        "machine": "i386"
                    }
                },
                "remediation_suggestions": [
                    "Update kernel to supported version",
                    "Enable required kernel configuration options",
                    "Verify architecture compatibility"
                ],
                "is_recoverable": False
            }


@given(
    environment_id=environment_id_strategy(),
    config=validation_config_strategy(),
    network_success=st.booleans(),
    disk_success=st.booleans(),
    memory_success=st.booleans(),
    cpu_success=st.booleans(),
    tool_success=st.booleans(),
    permission_success=st.booleans(),
    kernel_success=st.booleans()
)
@settings(max_examples=100, deadline=5000)
def test_comprehensive_validation_checks(
    environment_id, config, network_success, disk_success, memory_success,
    cpu_success, tool_success, permission_success, kernel_success
):
    """
    **Feature: test-deployment-system, Property 17: Comprehensive validation checks**
    **Validates: Requirements 4.2**
    
    Property 17: Comprehensive validation checks
    For any readiness check execution, network connectivity, resource availability, 
    and tool functionality should be verified.
    
    This test verifies that:
    1. All required validation checks are executed during readiness validation
    2. Network connectivity validation is performed and results are captured
    3. Resource availability (disk, memory, CPU) is checked comprehensively
    4. Tool functionality validation covers required and optional tools
    5. Environment permissions are validated properly
    6. Kernel compatibility is checked when required
    7. Overall readiness status reflects the results of all individual checks
    8. Failed checks are properly reported with diagnostic information
    """
    # Run the async test in a synchronous wrapper
    asyncio.run(test_comprehensive_validation_checks_manual(
        environment_id, config, network_success, disk_success, memory_success,
        cpu_success, tool_success, permission_success, kernel_success
    ))


@given(environment_id=environment_id_strategy())
@settings(max_examples=30, deadline=3000)
def test_validation_check_timeout_handling(environment_id):
    """
    Test that validation properly handles timeouts for individual checks.
    
    This verifies that when validation checks take too long, they are properly
    timed out and marked as failed with appropriate error information.
    """
    async def run_timeout_test():
        # Create validation manager with custom timeout check
        validation_manager = ValidationManager()
        
        # Add a custom check that will timeout
        timeout_check = ValidationCheck(
            name="timeout_test_check",
            description="Test check that times out",
            severity=ValidationSeverity.ERROR,
            required=True,
            timeout_seconds=1  # Very short timeout
        )
        validation_manager.add_custom_validation_check(timeout_check)
        
        # Mock the check to take longer than timeout
        async def slow_check(check, env_id, config):
            await asyncio.sleep(2)  # Sleep longer than timeout
            return {"success": True}
        
        validation_manager._execute_validation_check = slow_check
        
        # Perform validation
        result = await validation_manager.validate_environment_readiness(environment_id)
        
        # Verify timeout was handled properly
        assert "timeout_test_check" in result.failed_checks, \
            "Timed out check should be in failed checks"
        
        assert not result.is_ready, \
            "Environment should not be ready when required check times out"
        
        failure_info = result.details.get("timeout_test_check_failure")
        assert failure_info is not None, \
            "Timeout failure should have detailed information"
        
        assert "timed out" in failure_info.error_message.lower(), \
            "Failure message should indicate timeout"
    
    asyncio.run(run_timeout_test())


@given(
    environment_id=environment_id_strategy(),
    num_custom_checks=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=30, deadline=3000)
def test_custom_validation_checks_integration(environment_id, num_custom_checks):
    """
    Test that custom validation checks are properly integrated into comprehensive validation.
    
    This verifies that when custom checks are added, they are executed alongside
    the default checks and their results are properly incorporated.
    """
    async def run_custom_checks_test():
        validation_manager = MockValidationManager()
        
        # Add custom validation checks
        custom_checks = []
        for i in range(num_custom_checks):
            custom_check = ValidationCheck(
                name=f"custom_check_{i}",
                description=f"Custom validation check {i}",
                severity=ValidationSeverity.WARNING,
                required=False,
                timeout_seconds=10
            )
            custom_checks.append(custom_check)
            validation_manager.add_custom_validation_check(custom_check)
        
        # Mock custom check execution
        original_execute = validation_manager._execute_validation_check
        
        async def mock_execute_with_custom(check, env_id, config):
            if check.name.startswith("custom_check_"):
                return {
                    "success": True,
                    "details": {"custom_check": True, "check_name": check.name}
                }
            else:
                return await original_execute(check, env_id, config)
        
        validation_manager._execute_validation_check = mock_execute_with_custom
        
        # Perform validation
        result = await validation_manager.validate_environment_readiness(environment_id)
        
        # Verify custom checks were executed
        for custom_check in custom_checks:
            assert custom_check.name in result.checks_performed, \
                f"Custom check '{custom_check.name}' should have been performed"
            
            # Since these are warning-level checks, they shouldn't affect readiness
            assert custom_check.name not in result.failed_checks, \
                f"Custom check '{custom_check.name}' should have succeeded"
        
        # Verify total number of checks includes custom checks
        expected_total_checks = 7 + num_custom_checks  # 7 default + custom
        assert len(result.checks_performed) == expected_total_checks, \
            f"Should have performed {expected_total_checks} checks, got {len(result.checks_performed)}"
    
    asyncio.run(run_custom_checks_test())


async def test_comprehensive_validation_checks_manual(
    environment_id, config, network_success, disk_success, memory_success,
    cpu_success, tool_success, permission_success, kernel_success
):
    """
    Manual test function for comprehensive validation checks without Hypothesis decorator.
    
    This is the same test logic as the property-based test but can be called directly.
    """
    # Arrange - Create mock validation manager with specified success states
    validation_manager = MockValidationManager(
        network_success=network_success,
        disk_success=disk_success,
        memory_success=memory_success,
        cpu_success=cpu_success,
        tool_success=tool_success,
        permission_success=permission_success,
        kernel_success=kernel_success
    )
    
    # Act - Perform comprehensive validation
    validation_result = await validation_manager.validate_environment_readiness(
        environment_id, config
    )
    
    # Assert - Verify comprehensive validation was performed
    
    # Property: All core validation checks should be executed
    expected_checks = [
        "network_connectivity",
        "disk_space", 
        "memory_availability",
        "cpu_availability",
        "tool_functionality",
        "environment_permissions",
        "kernel_compatibility"
    ]
    
    for check in expected_checks:
        assert check in validation_manager.checks_called, \
            f"Validation check '{check}' should have been executed"
    
    # Property: Validation result should have proper structure
    assert isinstance(validation_result, ValidationResult), \
        "Validation should return a ValidationResult object"
    
    assert validation_result.environment_id == environment_id, \
        "Validation result should contain the correct environment ID"
    
    assert isinstance(validation_result.checks_performed, list), \
        "Validation result should contain list of performed checks"
    
    assert isinstance(validation_result.failed_checks, list), \
        "Validation result should contain list of failed checks"
    
    assert isinstance(validation_result.is_ready, bool), \
        "Validation result should contain boolean readiness status"
    
    # Property: All expected checks should be recorded as performed
    for check in expected_checks:
        assert check in validation_result.checks_performed, \
            f"Check '{check}' should be recorded as performed"
    
    # Property: Failed checks should be subset of performed checks
    for failed_check in validation_result.failed_checks:
        assert failed_check in validation_result.checks_performed, \
            f"Failed check '{failed_check}' should be in performed checks list"
    
    # Property: Overall readiness should reflect individual check results
    all_checks_successful = all([
        network_success, disk_success, memory_success, cpu_success,
        tool_success, permission_success, kernel_success
    ])
    
    # Required checks that affect readiness (memory and CPU are warnings, not errors)
    required_checks_successful = all([
        network_success, disk_success, tool_success, 
        permission_success, kernel_success
    ])
    
    if required_checks_successful:
        assert validation_result.is_ready, \
            "Environment should be ready when all required checks pass"
    else:
        # If any required check failed, environment should not be ready
        failed_required_checks = []
        if not network_success:
            failed_required_checks.append("network_connectivity")
        if not disk_success:
            failed_required_checks.append("disk_space")
        if not tool_success:
            failed_required_checks.append("tool_functionality")
        if not permission_success:
            failed_required_checks.append("environment_permissions")
        if not kernel_success:
            failed_required_checks.append("kernel_compatibility")
        
        if failed_required_checks:
            assert not validation_result.is_ready, \
                f"Environment should not be ready when required checks fail: {failed_required_checks}"
    
    # Property: Failed checks should have corresponding failure details
    for failed_check in validation_result.failed_checks:
        failure_key = f"{failed_check}_failure"
        assert failure_key in validation_result.details, \
            f"Failed check '{failed_check}' should have failure details in result"
        
        failure_info = validation_result.details[failure_key]
        assert hasattr(failure_info, 'error_message'), \
            f"Failure info for '{failed_check}' should contain error message"
        assert hasattr(failure_info, 'remediation_suggestions'), \
            f"Failure info for '{failed_check}' should contain remediation suggestions"
    
    # Property: Success rate should be valid percentage
    success_rate = validation_result.success_rate
    assert 0.0 <= success_rate <= 100.0, \
        f"Success rate should be between 0 and 100, got {success_rate}"
    
    # Property: Success rate should match actual success/failure ratio
    total_checks = len(validation_result.checks_performed)
    failed_checks = len(validation_result.failed_checks)
    expected_success_rate = ((total_checks - failed_checks) / total_checks) * 100.0 if total_checks > 0 else 100.0
    
    assert abs(success_rate - expected_success_rate) < 0.1, \
        f"Success rate {success_rate} should match calculated rate {expected_success_rate}"
    
    # Property: Validation timestamp should be recent
    time_diff = datetime.now() - validation_result.timestamp
    assert time_diff.total_seconds() < 60, \
        "Validation timestamp should be recent (within 60 seconds)"


def test_comprehensive_validation_checks_sync():
    """Synchronous wrapper for the async property test"""
    
    async def run_single_test():
        await test_comprehensive_validation_checks_manual(
            environment_id="test_env_001",
            config={},
            network_success=True,
            disk_success=True,
            memory_success=True,
            cpu_success=True,
            tool_success=True,
            permission_success=True,
            kernel_success=True
        )
    
    asyncio.run(run_single_test())


@st.composite
def kernel_config_strategy(draw):
    """Generate kernel configuration for property testing"""
    return {
        "min_kernel_version": draw(st.sampled_from(["3.10.0", "4.0.0", "5.0.0", "6.0.0"])),
        "max_kernel_version": draw(st.one_of(
            st.none(),
            st.sampled_from(["5.15.0", "6.1.0", "6.5.0"])
        )),
        "supported_architectures": draw(st.fixed_dictionaries({
            "x86_64": st.just(["x86_64", "amd64"]),
            "aarch64": st.just(["aarch64", "arm64"]),
            "armv7l": st.just(["armv7l", "armhf"])
        })),
        "required_config_options": draw(st.lists(
            st.sampled_from([
                "CONFIG_MODULES", "CONFIG_SYSFS", "CONFIG_PROC_FS",
                "CONFIG_DEBUG_FS", "CONFIG_TRACING"
            ]),
            min_size=1,
            max_size=3
        )),
        "testing_config_options": draw(st.lists(
            st.sampled_from([
                "CONFIG_DEBUG_INFO", "CONFIG_GCOV_KERNEL", "CONFIG_PERF_EVENTS",
                "CONFIG_FTRACE", "CONFIG_KASAN", "CONFIG_KTSAN"
            ]),
            min_size=0,
            max_size=4
        ))
    }


@st.composite
def kernel_version_strategy(draw):
    """Generate kernel version strings for property testing"""
    major = draw(st.integers(min_value=3, max_value=6))
    minor = draw(st.integers(min_value=0, max_value=20))
    patch = draw(st.integers(min_value=0, max_value=50))
    
    # Generate different version formats
    format_type = draw(st.sampled_from([
        "simple",      # 5.15.0
        "with_build",  # 5.15.0-91
        "with_suffix", # 5.15.0-91-generic
        "rc_version"   # 6.2.0-rc1
    ]))
    
    if format_type == "simple":
        return f"{major}.{minor}.{patch}"
    elif format_type == "with_build":
        build = draw(st.integers(min_value=1, max_value=100))
        return f"{major}.{minor}.{patch}-{build}"
    elif format_type == "with_suffix":
        build = draw(st.integers(min_value=1, max_value=100))
        suffix = draw(st.sampled_from(["generic", "amd64", "server", "desktop"]))
        return f"{major}.{minor}.{patch}-{build}-{suffix}"
    else:  # rc_version
        rc_num = draw(st.integers(min_value=1, max_value=8))
        return f"{major}.{minor}.{patch}-rc{rc_num}"


@given(
    environment_id=environment_id_strategy(),
    kernel_config=kernel_config_strategy(),
    kernel_version=kernel_version_strategy()
)
@settings(max_examples=100, deadline=5000)
def test_kernel_compatibility_validation(environment_id, kernel_config, kernel_version):
    """
    **Feature: test-deployment-system, Property 18: Kernel compatibility validation**
    **Validates: Requirements 4.3**
    
    Property 18: Kernel compatibility validation
    For any kernel testing deployment, kernel version and configuration compatibility 
    should be validated.
    
    This test verifies that:
    1. Kernel version parsing handles various version formats correctly
    2. Version compatibility checks work with different minimum/maximum requirements
    3. Architecture compatibility validation covers supported architectures
    4. Kernel configuration validation checks required and optional config options
    5. Overall compatibility determination considers all validation aspects
    6. Detailed diagnostic information is provided for compatibility issues
    7. Remediation suggestions are appropriate for different failure types
    """
    asyncio.run(test_kernel_compatibility_validation_manual(
        environment_id, kernel_config, kernel_version
    ))


async def test_kernel_compatibility_validation_manual(environment_id, kernel_config, kernel_version):
    """
    Manual test function for kernel compatibility validation.
    """
    # Import the actual ValidationManager for testing
    from deployment.validation_manager import ValidationManager
    
    # Create validation manager
    validation_manager = ValidationManager()
    
    # Mock platform.release to return our test kernel version
    with patch('platform.release', return_value=kernel_version):
        with patch('platform.system', return_value='Linux'):
            with patch('platform.machine', return_value='x86_64'):
                with patch('platform.processor', return_value='x86_64'):
                    
                    # Act - Perform kernel compatibility validation
                    result = await validation_manager._check_kernel_compatibility(
                        environment_id, kernel_config
                    )
    
    # Assert - Verify kernel compatibility validation properties
    
    # Property: Result should have proper structure
    assert isinstance(result, dict), \
        "Kernel compatibility result should be a dictionary"
    
    assert "success" in result, \
        "Result should contain success status"
    
    assert isinstance(result["success"], bool), \
        "Success status should be boolean"
    
    # Property: Successful validation should contain detailed information
    if result["success"]:
        assert "details" in result, \
            "Successful validation should contain details"
        
        details = result["details"]
        
        # Verify system information is present
        assert "system_info" in details, \
            "Details should contain system information"
        
        system_info = details["system_info"]
        assert system_info["system"] == "Linux", \
            "System should be Linux"
        assert system_info["release"] == kernel_version, \
            f"Release should match test kernel version {kernel_version}"
        
        # Verify version parsing information
        assert "version_info" in details, \
            "Details should contain version parsing information"
        
        version_info = details["version_info"]
        assert "raw_version" in version_info, \
            "Version info should contain raw version"
        assert version_info["raw_version"] == kernel_version, \
            "Raw version should match input"
        
        # If version was parsed successfully, verify structure
        if version_info.get("parsed_successfully", False):
            assert "version_tuple" in version_info, \
                "Parsed version should contain version tuple"
            assert isinstance(version_info["version_tuple"], tuple), \
                "Version tuple should be a tuple"
            assert len(version_info["version_tuple"]) == 3, \
                "Version tuple should have 3 elements (major, minor, patch)"
            
            # Verify version numbers are reasonable
            major, minor, patch = version_info["version_tuple"]
            assert 0 <= major <= 10, \
                f"Major version should be reasonable, got {major}"
            assert 0 <= minor <= 50, \
                f"Minor version should be reasonable, got {minor}"
            assert 0 <= patch <= 100, \
                f"Patch version should be reasonable, got {patch}"
        
        # Verify architecture compatibility information
        assert "arch_compatibility" in details, \
            "Details should contain architecture compatibility"
        
        arch_compat = details["arch_compatibility"]
        assert "compatible" in arch_compat, \
            "Architecture compatibility should have compatible status"
        assert isinstance(arch_compat["compatible"], bool), \
            "Architecture compatible status should be boolean"
        
        # Verify version compatibility information
        assert "version_compatibility" in details, \
            "Details should contain version compatibility"
        
        version_compat = details["version_compatibility"]
        assert "compatible" in version_compat, \
            "Version compatibility should have compatible status"
        assert isinstance(version_compat["compatible"], bool), \
            "Version compatible status should be boolean"
        
        # Verify configuration compatibility information
        assert "config_compatibility" in details, \
            "Details should contain configuration compatibility"
        
        config_compat = details["config_compatibility"]
        assert "compatible" in config_compat, \
            "Config compatibility should have compatible status"
        assert isinstance(config_compat["compatible"], bool), \
            "Config compatible status should be boolean"
        
        # Property: All compatibility aspects should be true for overall success
        assert arch_compat["compatible"], \
            "Architecture should be compatible for successful validation"
        assert version_compat["compatible"], \
            "Version should be compatible for successful validation"
        assert config_compat["compatible"], \
            "Configuration should be compatible for successful validation"
    
    # Property: Failed validation should contain error information
    else:
        assert "error" in result, \
            "Failed validation should contain error message"
        
        assert isinstance(result["error"], str), \
            "Error message should be a string"
        
        assert len(result["error"]) > 0, \
            "Error message should not be empty"
        
        # Should contain diagnostic information
        assert "diagnostic_info" in result, \
            "Failed validation should contain diagnostic information"
        
        # Should contain remediation suggestions
        assert "remediation_suggestions" in result, \
            "Failed validation should contain remediation suggestions"
        
        remediation = result["remediation_suggestions"]
        assert isinstance(remediation, list), \
            "Remediation suggestions should be a list"
        assert len(remediation) > 0, \
            "Should provide at least one remediation suggestion"
        
        # Should indicate if recoverable
        assert "is_recoverable" in result, \
            "Failed validation should indicate if recoverable"
        assert isinstance(result["is_recoverable"], bool), \
            "Recoverable status should be boolean"
    
    # Property: Version parsing should handle various formats
    # Test the version parsing separately to ensure it works correctly
    parsed_version = await validation_manager._parse_kernel_version(kernel_version)
    
    assert isinstance(parsed_version, dict), \
        "Version parsing should return a dictionary"
    
    assert "raw_version" in parsed_version, \
        "Parsed version should contain raw version"
    
    assert parsed_version["raw_version"] == kernel_version, \
        "Raw version should match input"
    
    # If parsing was successful, verify the parsed components
    if parsed_version.get("parsed_successfully", False):
        assert "major" in parsed_version, \
            "Successfully parsed version should contain major version"
        assert "minor" in parsed_version, \
            "Successfully parsed version should contain minor version"
        assert "patch" in parsed_version, \
            "Successfully parsed version should contain patch version"
        
        # Verify version components are integers
        assert isinstance(parsed_version["major"], int), \
            "Major version should be integer"
        assert isinstance(parsed_version["minor"], int), \
            "Minor version should be integer"
        assert isinstance(parsed_version["patch"], int), \
            "Patch version should be integer"


def test_kernel_compatibility_validation_sync():
    """Synchronous wrapper for kernel compatibility validation test"""
    
    async def run_single_test():
        # Test with a known good configuration
        kernel_config = {
            "min_kernel_version": "4.0.0",
            "supported_architectures": {
                "x86_64": ["x86_64", "amd64"]
            },
            "required_config_options": ["CONFIG_MODULES", "CONFIG_SYSFS"],
            "testing_config_options": ["CONFIG_DEBUG_INFO"]
        }
        
        await test_kernel_compatibility_validation_manual(
            "test_env_kernel", kernel_config, "5.15.0-91-generic"
        )
    
    asyncio.run(run_single_test())


if __name__ == "__main__":
    # Run a few test cases manually for verification
    print("Testing comprehensive validation checks...")
    
    async def run_tests():
        print("Testing successful validation...")
        await test_comprehensive_validation_checks_manual(
            "test_env_success", {}, True, True, True, True, True, True, True
        )
        print("✓ Successful validation test passed")
        
        print("Testing failed validation...")
        await test_comprehensive_validation_checks_manual(
            "test_env_failed", {}, False, False, True, True, False, True, True
        )
        print("✓ Failed validation test passed")
        
        print("Testing timeout handling...")
        await test_validation_check_timeout_handling("test_env_timeout")
        print("✓ Timeout handling test passed")
        
        print("Testing custom checks integration...")
        await test_custom_validation_checks_integration("test_env_custom", 3)
        print("✓ Custom checks integration test passed")
        
        print("Testing kernel compatibility validation...")
        await test_kernel_compatibility_validation_manual(
            "test_env_kernel", 
            {
                "min_kernel_version": "4.0.0",
                "required_config_options": ["CONFIG_MODULES"]
            },
            "5.15.0-91-generic"
        )
        print("✓ Kernel compatibility validation test passed")
        
        print("All comprehensive validation tests completed successfully!")
    
    asyncio.run(run_tests())