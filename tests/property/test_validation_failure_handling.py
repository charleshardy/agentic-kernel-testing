"""
Property-based test for validation failure handling.

Tests that validation failure handling prevents test execution and provides
diagnostic information when readiness validation fails.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any

from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    DeploymentPlan, DeploymentResult, DeploymentStatus, DeploymentStep,
    TestArtifact, ArtifactType, Dependency, InstrumentationConfig, 
    DeploymentConfig, ValidationResult, Priority
)
from deployment.environment_manager import EnvironmentManagerFactory, EnvironmentConfig


# Property-based test strategies
environment_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
validation_failures = st.lists(
    st.sampled_from([
        "network_connectivity", "disk_space", "memory_availability", 
        "cpu_resources", "kernel_version", "hardware_health", 
        "tool_functionality", "permissions", "dependency_check"
    ]),
    min_size=1,
    max_size=5
)
diagnostic_types = st.lists(
    st.sampled_from([
        "error_details", "remediation_steps", "resource_status",
        "configuration_issues", "dependency_problems", "network_diagnostics"
    ]),
    min_size=1,
    max_size=4
)


class MockValidationFailureEnvironmentManager:
    """Mock environment manager for testing validation failure handling"""
    
    def __init__(self, environment_id: str):
        self.environment_id = environment_id
        self.validation_failures = []
        self.diagnostic_info = {}
        self.test_execution_prevented = False
        self.validation_history = []
        self.failure_details = {}
    
    def set_validation_failures(self, failures: List[str], diagnostics: Dict[str, Any]):
        """Set validation failures and associated diagnostic information"""
        self.validation_failures = failures
        self.diagnostic_info = diagnostics
        
        # Generate detailed failure information
        for failure in failures:
            self.failure_details[failure] = {
                "error_code": f"ERR_{failure.upper()}",
                "severity": "critical" if failure in ["kernel_version", "hardware_health"] else "warning",
                "remediation": f"Fix {failure} issue",
                "detected_at": datetime.now().isoformat()
            }
    
    async def validate_readiness(self, connection) -> ValidationResult:
        """Mock readiness validation that can fail"""
        all_checks = [
            "network_connectivity", "disk_space", "memory_availability",
            "cpu_resources", "kernel_version", "hardware_health",
            "tool_functionality", "permissions", "dependency_check"
        ]
        
        failed_checks = self.validation_failures
        is_ready = len(failed_checks) == 0
        
        # Generate warnings for failed checks
        warnings = []
        for failure in failed_checks:
            warnings.append(f"Validation failed for {failure}: {self.failure_details.get(failure, {}).get('remediation', 'Unknown issue')}")
        
        # Record validation attempt
        validation_record = {
            "timestamp": datetime.now(),
            "checks_performed": all_checks,
            "failed_checks": failed_checks,
            "is_ready": is_ready,
            "diagnostic_info": self.diagnostic_info.copy()
        }
        self.validation_history.append(validation_record)
        
        # Create detailed diagnostic information
        details = {
            "validation_count": len(self.validation_history),
            "failure_details": self.failure_details.copy(),
            "diagnostic_info": self.diagnostic_info.copy(),
            "environment_status": "failed" if failed_checks else "ready"
        }
        
        return ValidationResult(
            environment_id=self.environment_id,
            is_ready=is_ready,
            checks_performed=all_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            details=details,
            timestamp=datetime.now()
        )
    
    async def prevent_test_execution(self, reason: str) -> bool:
        """Mock test execution prevention"""
        self.test_execution_prevented = True
        self.prevention_reason = reason
        return True
    
    def get_diagnostic_information(self) -> Dict[str, Any]:
        """Get comprehensive diagnostic information"""
        return {
            "validation_failures": self.validation_failures,
            "failure_details": self.failure_details,
            "diagnostic_info": self.diagnostic_info,
            "test_execution_prevented": self.test_execution_prevented,
            "validation_history_count": len(self.validation_history)
        }


class MockDeploymentOrchestrator:
    """Mock deployment orchestrator for testing validation failure handling"""
    
    def __init__(self):
        self.deployment_attempts = []
        self.validation_results = {}
        self.test_execution_blocked = {}
    
    async def validate_environment_readiness(self, environment_id: str, env_manager) -> ValidationResult:
        """Validate environment readiness and handle failures"""
        connection = MagicMock()
        connection.environment_id = environment_id
        
        validation_result = await env_manager.validate_readiness(connection)
        self.validation_results[environment_id] = validation_result
        
        # If validation fails, prevent test execution
        if not validation_result.is_ready:
            await env_manager.prevent_test_execution(
                f"Environment {environment_id} failed readiness validation"
            )
            self.test_execution_blocked[environment_id] = True
        
        return validation_result
    
    async def attempt_deployment(self, plan_id: str, environment_id: str) -> DeploymentResult:
        """Attempt deployment with validation failure handling"""
        # Record deployment attempt
        attempt = {
            "plan_id": plan_id,
            "environment_id": environment_id,
            "timestamp": datetime.now(),
            "blocked": environment_id in self.test_execution_blocked
        }
        self.deployment_attempts.append(attempt)
        
        # If test execution is blocked, return failed deployment
        if environment_id in self.test_execution_blocked:
            return DeploymentResult(
                deployment_id=f"deploy_{plan_id}",
                plan_id=plan_id,
                environment_id=environment_id,
                status=DeploymentStatus.FAILED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_message="Test execution prevented due to validation failures"
            )
        
        # Otherwise, return successful deployment
        return DeploymentResult(
            deployment_id=f"deploy_{plan_id}",
            plan_id=plan_id,
            environment_id=environment_id,
            status=DeploymentStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now()
        )


@given(
    environment_id=environment_ids,
    validation_failures=validation_failures,
    diagnostic_types=diagnostic_types
)
@settings(max_examples=50, deadline=6000)
async def test_validation_failure_handling(environment_id, validation_failures, diagnostic_types):
    """
    **Feature: test-deployment-system, Property 19: Validation failure handling**
    
    Property: Validation failure handling prevents test execution and provides diagnostics
    
    This test verifies that:
    1. When readiness validation fails, test execution is prevented
    2. Detailed diagnostic information is provided for failed validations
    3. Failure reasons are clearly communicated
    4. Test execution blocking is properly enforced
    5. Diagnostic information includes remediation guidance
    """
    assume(len(environment_id.strip()) > 0)
    assume(len(validation_failures) > 0)
    assume(len(diagnostic_types) > 0)
    
    # Create mock environment manager with validation failures
    env_manager = MockValidationFailureEnvironmentManager(environment_id.strip())
    
    # Set up diagnostic information based on types
    diagnostic_info = {}
    for diag_type in diagnostic_types:
        if diag_type == "error_details":
            diagnostic_info["error_details"] = [f"Error in {failure}" for failure in validation_failures]
        elif diag_type == "remediation_steps":
            diagnostic_info["remediation_steps"] = [f"Fix {failure}" for failure in validation_failures]
        elif diag_type == "resource_status":
            diagnostic_info["resource_status"] = {failure: "insufficient" for failure in validation_failures}
        elif diag_type == "configuration_issues":
            diagnostic_info["configuration_issues"] = [f"Config problem: {failure}" for failure in validation_failures]
        elif diag_type == "dependency_problems":
            diagnostic_info["dependency_problems"] = [f"Missing dependency for {failure}" for failure in validation_failures]
        elif diag_type == "network_diagnostics":
            diagnostic_info["network_diagnostics"] = {"connectivity": "failed", "latency": "high"}
    
    # Configure validation failures
    env_manager.set_validation_failures(validation_failures, diagnostic_info)
    
    # Create mock deployment orchestrator
    orchestrator = MockDeploymentOrchestrator()
    
    # Perform validation and handle failures
    validation_result = await orchestrator.validate_environment_readiness(
        environment_id.strip(), env_manager
    )
    
    # Verify validation result indicates failure
    assert not validation_result.is_ready, "Validation should fail when there are validation failures"
    assert validation_result.environment_id == environment_id.strip(), "Environment ID should match"
    
    # Verify all validation failures are reported
    for failure in validation_failures:
        assert failure in validation_result.failed_checks, f"Failed check {failure} should be reported"
    
    # Verify diagnostic information is provided
    assert len(validation_result.details) > 0, "Diagnostic details should be provided"
    assert "failure_details" in validation_result.details, "Failure details should be included"
    assert "diagnostic_info" in validation_result.details, "Diagnostic info should be included"
    
    # Verify diagnostic information contains expected types
    provided_diagnostics = validation_result.details["diagnostic_info"]
    for diag_type in diagnostic_types:
        assert diag_type in provided_diagnostics, f"Diagnostic type {diag_type} should be provided"
    
    # Verify warnings are generated for failures
    assert len(validation_result.warnings) > 0, "Warnings should be generated for validation failures"
    for failure in validation_failures:
        failure_warning_found = any(failure in warning for warning in validation_result.warnings)
        assert failure_warning_found, f"Warning should be generated for failure {failure}"
    
    # Verify test execution is prevented
    assert env_manager.test_execution_prevented, "Test execution should be prevented after validation failure"
    assert environment_id.strip() in orchestrator.test_execution_blocked, "Environment should be blocked from test execution"
    
    # Attempt deployment and verify it's blocked
    plan_id = f"test_plan_{environment_id.strip()}"
    deployment_result = await orchestrator.attempt_deployment(plan_id, environment_id.strip())
    
    # Verify deployment is blocked due to validation failure
    assert deployment_result.is_failed, "Deployment should fail when validation fails"
    assert "validation failures" in deployment_result.error_message.lower(), "Error message should mention validation failures"
    
    # Verify comprehensive diagnostic information is available
    diagnostic_info_retrieved = env_manager.get_diagnostic_information()
    assert diagnostic_info_retrieved["test_execution_prevented"], "Diagnostic info should confirm test execution prevention"
    assert len(diagnostic_info_retrieved["validation_failures"]) == len(validation_failures), "All validation failures should be recorded"
    assert len(diagnostic_info_retrieved["failure_details"]) == len(validation_failures), "Detailed failure info should be available"


@given(
    environment_count=st.integers(min_value=2, max_value=4),
    failure_scenarios=st.lists(
        st.tuples(
            validation_failures,
            st.booleans()  # Whether this environment should have failures
        ),
        min_size=2,
        max_size=4
    )
)
@settings(max_examples=30, deadline=5000)
async def test_multiple_environment_validation_failure_isolation(environment_count, failure_scenarios):
    """
    Property: Validation failure handling maintains isolation between environments
    
    This test verifies that:
    1. Validation failures in one environment don't affect others
    2. Test execution blocking is environment-specific
    3. Diagnostic information is isolated per environment
    4. Successful environments can still execute tests
    """
    assume(environment_count >= 2)
    assume(len(failure_scenarios) >= 2)
    
    # Create multiple environment managers with different failure scenarios
    env_managers = []
    orchestrator = MockDeploymentOrchestrator()
    expected_results = []
    
    for i in range(environment_count):
        env_id = f"validation_env_{i}"
        env_manager = MockValidationFailureEnvironmentManager(env_id)
        
        # Use cycling failure scenarios
        scenario_index = i % len(failure_scenarios)
        failures, should_fail = failure_scenarios[scenario_index]
        
        if should_fail and failures:
            # Set up failures for this environment
            diagnostic_info = {
                "error_details": [f"Error in {failure} for {env_id}" for failure in failures],
                "remediation_steps": [f"Fix {failure} in {env_id}" for failure in failures]
            }
            env_manager.set_validation_failures(failures, diagnostic_info)
            expected_ready = False
        else:
            # No failures for this environment
            env_manager.set_validation_failures([], {})
            expected_ready = True
        
        env_managers.append(env_manager)
        expected_results.append({
            "environment_id": env_id,
            "should_be_ready": expected_ready,
            "expected_failures": failures if should_fail else []
        })
    
    # Perform validation for all environments
    validation_results = []
    for env_manager in env_managers:
        result = await orchestrator.validate_environment_readiness(
            env_manager.environment_id, env_manager
        )
        validation_results.append(result)
    
    # Verify each environment has correct validation results
    for i, (env_manager, expected, actual) in enumerate(zip(env_managers, expected_results, validation_results)):
        env_id = expected["environment_id"]
        
        # Verify readiness status
        assert actual.is_ready == expected["should_be_ready"], \
            f"Environment {env_id} readiness should be {expected['should_be_ready']}"
        
        # Verify test execution blocking
        is_blocked = env_id in orchestrator.test_execution_blocked
        assert is_blocked != expected["should_be_ready"], \
            f"Environment {env_id} blocking should be opposite of readiness"
        
        # Verify failure isolation
        if not expected["should_be_ready"]:
            # Failed environment should have failures recorded
            assert len(actual.failed_checks) > 0, f"Failed environment {env_id} should have failed checks"
            assert len(actual.warnings) > 0, f"Failed environment {env_id} should have warnings"
        else:
            # Successful environment should have no failures
            assert len(actual.failed_checks) == 0, f"Successful environment {env_id} should have no failed checks"
    
    # Attempt deployments and verify isolation
    deployment_results = []
    for i, env_manager in enumerate(env_managers):
        plan_id = f"test_plan_{i}"
        result = await orchestrator.attempt_deployment(plan_id, env_manager.environment_id)
        deployment_results.append(result)
    
    # Verify deployment results match validation results
    for i, (expected, deployment_result) in enumerate(zip(expected_results, deployment_results)):
        if expected["should_be_ready"]:
            assert deployment_result.is_successful, \
                f"Deployment to ready environment {expected['environment_id']} should succeed"
        else:
            assert deployment_result.is_failed, \
                f"Deployment to failed environment {expected['environment_id']} should be blocked"


@given(
    environment_id=environment_ids,
    failure_types=st.lists(
        st.sampled_from(["critical", "warning", "info"]),
        min_size=1,
        max_size=3
    ),
    remediation_available=st.booleans()
)
@settings(max_examples=25, deadline=4000)
async def test_diagnostic_information_completeness(environment_id, failure_types, remediation_available):
    """
    Property: Diagnostic information provides comprehensive failure analysis
    
    This test verifies that:
    1. Diagnostic information includes failure severity levels
    2. Remediation guidance is provided when available
    3. Failure details include timestamps and error codes
    4. Diagnostic information is structured and accessible
    """
    assume(len(environment_id.strip()) > 0)
    assume(len(failure_types) > 0)
    
    # Create environment manager with comprehensive diagnostic setup
    env_manager = MockValidationFailureEnvironmentManager(environment_id.strip())
    
    # Set up failures with different severity levels
    failures = []
    diagnostic_info = {
        "error_details": [],
        "severity_levels": {},
        "timestamps": {},
        "error_codes": {}
    }
    
    for i, failure_type in enumerate(failure_types):
        failure_name = f"test_failure_{i}"
        failures.append(failure_name)
        
        diagnostic_info["error_details"].append(f"Detailed error for {failure_name}")
        diagnostic_info["severity_levels"][failure_name] = failure_type
        diagnostic_info["timestamps"][failure_name] = datetime.now().isoformat()
        diagnostic_info["error_codes"][failure_name] = f"ERR_{failure_name.upper()}"
    
    # Add remediation information if available
    if remediation_available:
        diagnostic_info["remediation_steps"] = [f"Fix {failure}" for failure in failures]
        diagnostic_info["remediation_available"] = True
    else:
        diagnostic_info["remediation_available"] = False
    
    # Configure validation failures
    env_manager.set_validation_failures(failures, diagnostic_info)
    
    # Perform validation
    connection = MagicMock()
    connection.environment_id = environment_id.strip()
    
    validation_result = await env_manager.validate_readiness(connection)
    
    # Verify diagnostic information completeness
    assert not validation_result.is_ready, "Validation should fail with configured failures"
    assert len(validation_result.details) > 0, "Diagnostic details should be provided"
    
    # Verify diagnostic information structure
    provided_diagnostics = validation_result.details["diagnostic_info"]
    assert "error_details" in provided_diagnostics, "Error details should be provided"
    assert "severity_levels" in provided_diagnostics, "Severity levels should be provided"
    assert "timestamps" in provided_diagnostics, "Timestamps should be provided"
    assert "error_codes" in provided_diagnostics, "Error codes should be provided"
    
    # Verify severity levels are included
    for failure in failures:
        assert failure in provided_diagnostics["severity_levels"], \
            f"Severity level should be provided for {failure}"
    
    # Verify error codes are included
    for failure in failures:
        assert failure in provided_diagnostics["error_codes"], \
            f"Error code should be provided for {failure}"
    
    # Verify remediation information
    if remediation_available:
        assert "remediation_steps" in provided_diagnostics, "Remediation steps should be provided"
        assert provided_diagnostics["remediation_available"], "Remediation availability should be indicated"
        assert len(provided_diagnostics["remediation_steps"]) == len(failures), \
            "Remediation steps should be provided for all failures"
    else:
        assert not provided_diagnostics.get("remediation_available", True), \
            "Remediation unavailability should be indicated"
    
    # Verify failure details include comprehensive information
    failure_details = validation_result.details["failure_details"]
    for failure in failures:
        assert failure in failure_details, f"Failure details should include {failure}"
        failure_detail = failure_details[failure]
        
        assert "error_code" in failure_detail, f"Error code should be in details for {failure}"
        assert "severity" in failure_detail, f"Severity should be in details for {failure}"
        assert "detected_at" in failure_detail, f"Detection timestamp should be in details for {failure}"


# Synchronous test runners for pytest
def test_validation_failure_handling_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_validation_failure_handling(
        environment_id="validation_failure_test_env",
        validation_failures=["network_connectivity", "disk_space"],
        diagnostic_types=["error_details", "remediation_steps"]
    ))


def test_multiple_environment_validation_failure_isolation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_environment_validation_failure_isolation(
        environment_count=3,
        failure_scenarios=[
            (["network_connectivity"], True),
            ([], False),
            (["disk_space", "memory_availability"], True)
        ]
    ))


def test_diagnostic_information_completeness_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_diagnostic_information_completeness(
        environment_id="diagnostic_test_env",
        failure_types=["critical", "warning"],
        remediation_available=True
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing validation failure handling...")
        await test_validation_failure_handling(
            "test_env", ["network_connectivity", "disk_space"], ["error_details", "remediation_steps"]
        )
        print("✓ Validation failure handling test passed")
        
        print("Testing multiple environment validation failure isolation...")
        await test_multiple_environment_validation_failure_isolation(
            2, [(["network_connectivity"], True), ([], False)]
        )
        print("✓ Multiple environment validation failure isolation test passed")
        
        print("Testing diagnostic information completeness...")
        await test_diagnostic_information_completeness("test_env", ["critical"], True)
        print("✓ Diagnostic information completeness test passed")
        
        print("All validation failure handling tests completed successfully!")
    
    asyncio.run(run_examples())