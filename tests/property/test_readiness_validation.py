"""
Property-based test for readiness validation.

Tests that readiness check execution properly validates environment readiness,
network connectivity, resource availability, and kernel compatibility.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock

from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    DeploymentPlan, DeploymentResult, DeploymentStatus, DeploymentStep,
    TestArtifact, ArtifactType, Dependency, InstrumentationConfig, 
    DeploymentConfig, ValidationResult
)
from deployment.environment_manager import EnvironmentManagerFactory, EnvironmentConfig
from datetime import datetime


# Property-based test strategies
environment_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
readiness_checks = st.lists(
    st.sampled_from([
        "network_connectivity", "disk_space", "memory_availability", 
        "cpu_resources", "kernel_version", "hardware_health", 
        "tool_functionality", "permissions"
    ]),
    min_size=1,
    max_size=8
)
failure_scenarios = st.lists(
    st.sampled_from([
        "network_connectivity", "disk_space", "memory_availability",
        "kernel_version", "hardware_health"
    ]),
    min_size=0,
    max_size=3
)


class MockReadinessEnvironmentManager:
    """Mock environment manager for testing readiness validation"""
    
    def __init__(self, environment_id: str):
        self.environment_id = environment_id
        self.readiness_state = {
            "network_connectivity": True,
            "disk_space": True,
            "memory_availability": True,
            "cpu_resources": True,
            "kernel_version": True,
            "hardware_health": True,
            "tool_functionality": True,
            "permissions": True
        }
        self.validation_history = []
        self.warnings = []
    
    def set_check_result(self, check: str, result: bool, warning: str = None):
        """Set the result of a specific readiness check"""
        self.readiness_state[check] = result
        if warning and not result:
            self.warnings.append(warning)
    
    async def test_connection(self) -> bool:
        """Mock connection test"""
        return self.readiness_state.get("network_connectivity", True)
    
    async def validate_readiness(self, connection) -> ValidationResult:
        """Mock readiness validation"""
        checks_performed = list(self.readiness_state.keys())
        failed_checks = [check for check, result in self.readiness_state.items() if not result]
        is_ready = len(failed_checks) == 0
        
        # Record validation attempt
        self.validation_history.append({
            "timestamp": asyncio.get_event_loop().time(),
            "checks_performed": checks_performed,
            "failed_checks": failed_checks,
            "is_ready": is_ready
        })
        
        return ValidationResult(
            environment_id=self.environment_id,
            is_ready=is_ready,
            checks_performed=checks_performed,
            failed_checks=failed_checks,
            warnings=self.warnings.copy(),
            details={
                "validation_count": len(self.validation_history),
                "last_validation": asyncio.get_event_loop().time()
            }
        )


@given(
    environment_id=environment_ids,
    checks_to_perform=readiness_checks,
    failed_checks=failure_scenarios
)
@settings(max_examples=40, deadline=5000)
async def test_readiness_check_execution(environment_id, checks_to_perform, failed_checks):
    """
    Property: Readiness check execution validates environment properly
    
    This test verifies that:
    1. All specified readiness checks are performed
    2. Failed checks are properly identified and reported
    3. Readiness status reflects the state of all checks
    4. Validation results include comprehensive details
    5. Multiple validation attempts are tracked
    """
    assume(len(environment_id.strip()) > 0)
    assume(len(checks_to_perform) > 0)
    
    # Create mock environment manager
    env_manager = MockReadinessEnvironmentManager(environment_id.strip())
    
    # Set up check results based on failure scenarios
    for check in checks_to_perform:
        is_failed = check in failed_checks
        env_manager.set_check_result(
            check, 
            not is_failed, 
            f"Warning: {check} failed" if is_failed else None
        )
    
    # Create mock connection
    connection = MagicMock()
    connection.environment_id = environment_id.strip()
    
    # Perform readiness validation
    validation_result = await env_manager.validate_readiness(connection)
    
    # Verify validation result structure
    assert isinstance(validation_result, ValidationResult), "Should return ValidationResult"
    assert validation_result.environment_id == environment_id.strip(), "Environment ID should match"
    
    # Verify all checks were performed
    assert len(validation_result.checks_performed) >= len(checks_to_perform), "All checks should be performed"
    for check in checks_to_perform:
        if check in env_manager.readiness_state:
            assert check in validation_result.checks_performed, f"Check {check} should be performed"
    
    # Verify failed checks are correctly identified
    expected_failed_checks = [check for check in checks_to_perform if check in failed_checks]
    for failed_check in expected_failed_checks:
        if failed_check in env_manager.readiness_state:
            assert failed_check in validation_result.failed_checks, f"Failed check {failed_check} should be reported"
    
    # Verify readiness status
    expected_ready = len(expected_failed_checks) == 0
    assert validation_result.is_ready == expected_ready, f"Readiness should be {expected_ready}"
    
    # Verify warnings for failed checks
    if expected_failed_checks:
        assert len(validation_result.warnings) > 0, "Warnings should be present for failed checks"
    
    # Verify validation history
    assert len(env_manager.validation_history) == 1, "Validation should be recorded in history"
    history_entry = env_manager.validation_history[0]
    assert history_entry["is_ready"] == expected_ready, "History should record correct readiness status"
    assert history_entry["failed_checks"] == validation_result.failed_checks, "History should record failed checks"
    
    # Verify validation details
    assert "validation_count" in validation_result.details, "Details should include validation count"
    assert validation_result.details["validation_count"] == 1, "First validation should have count 1"


@given(
    environment_count=st.integers(min_value=1, max_value=4),
    validation_scenarios=st.lists(
        st.tuples(
            readiness_checks,
            failure_scenarios
        ),
        min_size=1,
        max_size=4
    )
)
@settings(max_examples=25, deadline=4000)
async def test_multiple_environment_readiness_validation(environment_count, validation_scenarios):
    """
    Property: Multiple environment readiness validation maintains isolation
    
    This test verifies that:
    1. Each environment gets independent readiness validation
    2. Validation results don't interfere between environments
    3. Different failure scenarios are handled per environment
    4. Validation history is environment-specific
    """
    assume(environment_count >= 1)
    assume(len(validation_scenarios) >= 1)
    
    # Create multiple environment managers with different scenarios
    env_managers = []
    expected_results = []
    
    for i in range(environment_count):
        env_id = f"readiness_env_{i}"
        env_manager = MockReadinessEnvironmentManager(env_id)
        
        # Use cycling validation scenarios
        scenario_index = i % len(validation_scenarios)
        checks_to_perform, failed_checks = validation_scenarios[scenario_index]
        
        # Set up check results for this environment
        for check in checks_to_perform:
            is_failed = check in failed_checks
            env_manager.set_check_result(
                check,
                not is_failed,
                f"Warning: {check} failed in {env_id}" if is_failed else None
            )
        
        expected_ready = len([c for c in checks_to_perform if c in failed_checks]) == 0
        
        env_managers.append(env_manager)
        expected_results.append({
            "environment_id": env_id,
            "is_ready": expected_ready,
            "checks_performed": checks_to_perform,
            "failed_checks": [c for c in checks_to_perform if c in failed_checks]
        })
    
    # Perform validation for all environments
    validation_results = []
    for env_manager in env_managers:
        connection = MagicMock()
        connection.environment_id = env_manager.environment_id
        
        result = await env_manager.validate_readiness(connection)
        validation_results.append(result)
    
    # Verify each environment got correct validation results
    for i, (env_manager, expected, actual) in enumerate(zip(env_managers, expected_results, validation_results)):
        env_id = expected["environment_id"]
        
        # Verify basic result properties
        assert actual.environment_id == env_id, f"Environment ID should match for {env_id}"
        assert actual.is_ready == expected["is_ready"], f"Readiness should match for {env_id}"
        
        # Verify checks were performed
        for check in expected["checks_performed"]:
            if check in env_manager.readiness_state:
                assert check in actual.checks_performed, f"Check {check} should be performed for {env_id}"
        
        # Verify failed checks
        for failed_check in expected["failed_checks"]:
            if failed_check in env_manager.readiness_state:
                assert failed_check in actual.failed_checks, f"Failed check {failed_check} should be reported for {env_id}"
        
        # Verify validation history is environment-specific
        assert len(env_manager.validation_history) == 1, f"Validation history should exist for {env_id}"
        assert env_manager.validation_history[0]["is_ready"] == expected["is_ready"], \
            f"History should record correct readiness for {env_id}"
    
    # Verify isolation - different environments should have different results if scenarios differ
    for i in range(len(env_managers)):
        for j in range(i + 1, len(env_managers)):
            scenario_i = i % len(validation_scenarios)
            scenario_j = j % len(validation_scenarios)
            
            if scenario_i != scenario_j:
                # Different scenarios should likely produce different results
                result_i = validation_results[i]
                result_j = validation_results[j]
                
                # At least environment IDs should be different
                assert result_i.environment_id != result_j.environment_id, \
                    "Different environments should have different IDs"
                
                # Validation histories should be independent
                history_i = env_managers[i].validation_history
                history_j = env_managers[j].validation_history
                
                assert len(history_i) == 1 and len(history_j) == 1, \
                    "Each environment should have its own validation history"


@given(
    environment_id=environment_ids,
    validation_iterations=st.integers(min_value=2, max_value=5),
    intermittent_failures=st.booleans()
)
@settings(max_examples=20, deadline=3000)
async def test_repeated_readiness_validation(environment_id, validation_iterations, intermittent_failures):
    """
    Property: Repeated readiness validation tracks state changes
    
    This test verifies that:
    1. Multiple validation attempts are properly tracked
    2. Validation history accumulates correctly
    3. State changes between validations are detected
    4. Validation count increases with each attempt
    """
    assume(len(environment_id.strip()) > 0)
    assume(validation_iterations >= 2)
    
    # Create mock environment manager
    env_manager = MockReadinessEnvironmentManager(environment_id.strip())
    
    # Create mock connection
    connection = MagicMock()
    connection.environment_id = environment_id.strip()
    
    # Perform multiple validations
    validation_results = []
    
    for iteration in range(validation_iterations):
        # Optionally introduce intermittent failures
        if intermittent_failures and iteration % 2 == 1:
            # Introduce a failure on odd iterations
            env_manager.set_check_result("network_connectivity", False, "Intermittent network issue")
        else:
            # Ensure success on even iterations
            env_manager.set_check_result("network_connectivity", True)
        
        result = await env_manager.validate_readiness(connection)
        validation_results.append(result)
        
        # Small delay between validations
        await asyncio.sleep(0.01)
    
    # Verify validation count increases
    for i, result in enumerate(validation_results):
        expected_count = i + 1
        assert result.details["validation_count"] == expected_count, \
            f"Validation {i+1} should have count {expected_count}"
    
    # Verify validation history accumulates
    assert len(env_manager.validation_history) == validation_iterations, \
        f"Should have {validation_iterations} validation history entries"
    
    # Verify state changes are reflected if intermittent failures were introduced
    if intermittent_failures and validation_iterations > 1:
        # Should have different readiness states between iterations
        readiness_states = [result.is_ready for result in validation_results]
        
        # With intermittent failures, we should see both True and False states
        if validation_iterations >= 2:
            # At least one should be different due to intermittent failures
            assert not all(state == readiness_states[0] for state in readiness_states), \
                "Intermittent failures should cause different readiness states"
    
    # Verify timestamps are different (validations happened at different times)
    timestamps = [entry["timestamp"] for entry in env_manager.validation_history]
    for i in range(1, len(timestamps)):
        assert timestamps[i] > timestamps[i-1], \
            f"Validation {i+1} should have later timestamp than validation {i}"


# Synchronous test runners for pytest
def test_readiness_check_execution_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_readiness_check_execution(
        environment_id="readiness_test_env",
        checks_to_perform=["network_connectivity", "disk_space", "memory_availability"],
        failed_checks=["disk_space"]
    ))


def test_multiple_environment_readiness_validation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_environment_readiness_validation(
        environment_count=2,
        validation_scenarios=[
            (["network_connectivity", "disk_space"], ["disk_space"]),
            (["memory_availability", "kernel_version"], [])
        ]
    ))


def test_repeated_readiness_validation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_repeated_readiness_validation(
        environment_id="repeated_test_env",
        validation_iterations=3,
        intermittent_failures=True
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing readiness check execution...")
        await test_readiness_check_execution(
            "test_env", ["network_connectivity", "disk_space"], ["disk_space"]
        )
        print("✓ Readiness check execution test passed")
        
        print("Testing multiple environment readiness validation...")
        await test_multiple_environment_readiness_validation(
            2, [(["network_connectivity"], []), (["disk_space"], ["disk_space"])]
        )
        print("✓ Multiple environment readiness validation test passed")
        
        print("Testing repeated readiness validation...")
        await test_repeated_readiness_validation("test_env", 3, True)
        print("✓ Repeated readiness validation test passed")
        
        print("All readiness validation tests completed successfully!")
    
    asyncio.run(run_examples())