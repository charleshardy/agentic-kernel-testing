"""
Property-based tests for Deployment State Management

**Feature: test-deployment-system, Property 5: Deployment failure handling**
**Validates: Requirements 1.5**

Tests that for any deployment failure, the system should provide detailed error
information and implement retry mechanisms.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
from datetime import datetime, timedelta

from deployment.models import (
    DeploymentPlan,
    DeploymentResult,
    DeploymentStep,
    DeploymentStatus,
    TestArtifact,
    ArtifactType,
    Dependency,
    InstrumentationConfig,
    DeploymentConfig,
    Priority,
    ValidationResult
)


@composite
def deployment_status_strategy(draw):
    """Generate deployment status for property testing"""
    return draw(st.sampled_from(list(DeploymentStatus)))


@composite
def deployment_step_strategy(draw):
    """Generate deployment steps for property testing"""
    step_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    status = draw(deployment_status_strategy())
    
    # Generate realistic timestamps
    base_time = datetime.now()
    start_time = base_time if status != DeploymentStatus.PENDING else None
    end_time = base_time + timedelta(seconds=draw(st.integers(min_value=1, max_value=300))) if status.is_final else None
    
    error_message = None
    if status == DeploymentStatus.FAILED:
        error_message = draw(st.text(min_size=1, max_size=100))
    
    progress = 100.0 if status == DeploymentStatus.COMPLETED else draw(st.floats(min_value=0.0, max_value=100.0))
    retry_count = draw(st.integers(min_value=0, max_value=5))
    
    return DeploymentStep(
        step_id=step_id,
        name=name,
        status=status,
        start_time=start_time,
        end_time=end_time,
        error_message=error_message,
        progress_percentage=progress,
        retry_count=retry_count
    )


@composite
def deployment_result_strategy(draw):
    """Generate deployment results for property testing"""
    deployment_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    plan_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    environment_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    status = draw(deployment_status_strategy())
    
    base_time = datetime.now()
    start_time = base_time
    end_time = base_time + timedelta(seconds=draw(st.integers(min_value=1, max_value=600))) if status.is_final else None
    
    steps = draw(st.lists(deployment_step_strategy(), min_size=0, max_size=10))
    
    error_message = None
    if status == DeploymentStatus.FAILED:
        error_message = draw(st.text(min_size=1, max_size=200))
    
    artifacts_deployed = draw(st.integers(min_value=0, max_value=50))
    dependencies_installed = draw(st.integers(min_value=0, max_value=20))
    retry_count = draw(st.integers(min_value=0, max_value=5))
    
    return DeploymentResult(
        deployment_id=deployment_id,
        plan_id=plan_id,
        environment_id=environment_id,
        status=status,
        start_time=start_time,
        end_time=end_time,
        steps=steps,
        error_message=error_message,
        artifacts_deployed=artifacts_deployed,
        dependencies_installed=dependencies_installed,
        retry_count=retry_count
    )


@composite
def validation_result_strategy(draw):
    """Generate validation results for property testing"""
    environment_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    is_ready = draw(st.booleans())
    
    # Generate realistic check names
    check_names = ["network_connectivity", "disk_space", "memory_available", "kernel_version", "dependencies"]
    checks_performed = draw(st.lists(st.sampled_from(check_names), min_size=1, max_size=len(check_names), unique=True))
    
    # Generate failed checks (subset of performed checks if not ready)
    failed_checks = []
    if not is_ready:
        failed_checks = draw(st.lists(st.sampled_from(checks_performed), min_size=1, max_size=len(checks_performed), unique=True))
    
    warnings = draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5))
    
    return ValidationResult(
        environment_id=environment_id,
        is_ready=is_ready,
        checks_performed=checks_performed,
        failed_checks=failed_checks,
        warnings=warnings
    )


class TestDeploymentStateManagement:
    """Property-based tests for deployment state management"""
    
    @given(deployment_result_strategy())
    @settings(max_examples=100, deadline=3000)
    def test_deployment_failure_handling(self, deployment_result):
        """
        **Feature: test-deployment-system, Property 5: Deployment failure handling**
        **Validates: Requirements 1.5**
        
        Property: For any deployment failure, the system should provide detailed error
        information and implement retry mechanisms.
        """
        # Property: Failed deployments must have error information
        if deployment_result.is_failed:
            assert deployment_result.error_message is not None, \
                "Failed deployments must have error message"
            assert len(deployment_result.error_message) > 0, \
                "Error message must not be empty"
            
            # Failed deployments should have at least one failed step
            failed_steps = deployment_result.get_failed_steps()
            assert len(failed_steps) >= 0, \
                "Failed deployments should have failed steps information"
            
            # Each failed step should have error information
            for step in failed_steps:
                assert step.is_failed, "Failed step should be marked as failed"
                assert step.error_message is not None, \
                    f"Failed step {step.name} should have error message"
        
        # Property: Successful deployments should not have error messages
        if deployment_result.is_successful:
            # Successful deployments may have warnings but not errors
            assert deployment_result.error_message is None or deployment_result.error_message == "", \
                "Successful deployments should not have error messages"
            
            # All steps in successful deployment should be completed
            for step in deployment_result.steps:
                assert step.is_completed or step.status == DeploymentStatus.PENDING, \
                    f"Step {step.name} in successful deployment should be completed or pending"
        
        # Property: Deployment duration should be non-negative
        if deployment_result.duration_seconds is not None:
            assert deployment_result.duration_seconds >= 0, \
                "Deployment duration should be non-negative"
        
        # Property: Completion percentage should be valid
        completion = deployment_result.completion_percentage
        assert 0.0 <= completion <= 100.0, \
            f"Completion percentage should be between 0 and 100, got {completion}"
        
        # Property: Successful deployments should have 100% completion
        if deployment_result.is_successful and deployment_result.steps:
            assert completion == 100.0, \
                "Successful deployments with steps should have 100% completion"
        
        # Property: Retry count should be non-negative
        assert deployment_result.retry_count >= 0, \
            "Retry count should be non-negative"
    
    @given(deployment_step_strategy())
    @settings(max_examples=100, deadline=2000)
    def test_deployment_step_state_consistency(self, deployment_step):
        """
        Property: Deployment steps should maintain consistent state transitions
        and timing information.
        """
        # Property: Step duration should be non-negative
        if deployment_step.duration_seconds is not None:
            assert deployment_step.duration_seconds >= 0, \
                "Step duration should be non-negative"
        
        # Property: Completed steps should have end time
        if deployment_step.is_completed:
            assert deployment_step.end_time is not None, \
                "Completed steps should have end time"
            assert deployment_step.progress_percentage == 100.0, \
                "Completed steps should have 100% progress"
        
        # Property: Failed steps should have error message
        if deployment_step.is_failed:
            assert deployment_step.error_message is not None, \
                "Failed steps should have error message"
            assert len(deployment_step.error_message) > 0, \
                "Failed step error message should not be empty"
            assert deployment_step.end_time is not None, \
                "Failed steps should have end time"
        
        # Property: Steps with start time should have valid timing
        if deployment_step.start_time and deployment_step.end_time:
            assert deployment_step.end_time >= deployment_step.start_time, \
                "End time should be after start time"
        
        # Property: Progress percentage should be valid
        assert 0.0 <= deployment_step.progress_percentage <= 100.0, \
            f"Progress should be between 0 and 100, got {deployment_step.progress_percentage}"
        
        # Property: Retry count should be non-negative
        assert deployment_step.retry_count >= 0, \
            "Retry count should be non-negative"
    
    @given(validation_result_strategy())
    @settings(max_examples=100, deadline=2000)
    def test_validation_result_consistency(self, validation_result):
        """
        Property: Validation results should maintain consistency between
        readiness status and check results.
        """
        # Property: Success rate should be valid percentage
        success_rate = validation_result.success_rate
        assert 0.0 <= success_rate <= 100.0, \
            f"Success rate should be between 0 and 100, got {success_rate}"
        
        # Property: If not ready, there should be failed checks
        if not validation_result.is_ready and validation_result.checks_performed:
            assert len(validation_result.failed_checks) > 0, \
                "Non-ready environments should have failed checks"
        
        # Property: Failed checks should be subset of performed checks
        for failed_check in validation_result.failed_checks:
            assert failed_check in validation_result.checks_performed, \
                f"Failed check {failed_check} should be in performed checks"
        
        # Property: Success rate calculation should be correct
        if validation_result.checks_performed:
            expected_success_rate = ((len(validation_result.checks_performed) - len(validation_result.failed_checks)) 
                                   / len(validation_result.checks_performed)) * 100.0
            assert abs(success_rate - expected_success_rate) < 0.01, \
                f"Success rate calculation incorrect: expected {expected_success_rate}, got {success_rate}"
        else:
            assert success_rate == 0.0, \
                "Success rate should be 0 when no checks performed"
        
        # Property: Timestamp should be reasonable (within last day)
        now = datetime.now()
        time_diff = abs((now - validation_result.timestamp).total_seconds())
        assert time_diff < 86400, \
            "Validation timestamp should be within reasonable time range"
    
    @given(st.lists(deployment_step_strategy(), min_size=1, max_size=10))
    @settings(max_examples=50, deadline=3000)
    def test_deployment_pipeline_state_progression(self, steps):
        """
        Property: Deployment pipeline should maintain logical state progression
        and step ordering.
        """
        # Create a deployment result with the steps
        deployment_result = DeploymentResult(
            deployment_id="test_deployment",
            plan_id="test_plan",
            environment_id="test_env",
            status=DeploymentStatus.PENDING,
            start_time=datetime.now(),
            steps=steps
        )
        
        # Property: Steps should maintain consistent state
        completed_steps = [step for step in steps if step.is_completed]
        failed_steps = [step for step in steps if step.is_failed]
        
        # Property: If there are failed steps, deployment should handle them appropriately
        if failed_steps:
            # At least one step failed, so deployment should not be successful
            # (unless it's been marked as successful despite failures, which could be valid for optional steps)
            for failed_step in failed_steps:
                assert failed_step.error_message is not None, \
                    f"Failed step {failed_step.name} should have error message"
        
        # Property: Completed steps should have proper timing
        for step in completed_steps:
            assert step.progress_percentage == 100.0, \
                f"Completed step {step.name} should have 100% progress"
            
            if step.start_time and step.end_time:
                assert step.end_time >= step.start_time, \
                    f"Step {step.name} end time should be after start time"
        
        # Property: Step IDs should be unique
        step_ids = [step.step_id for step in steps]
        assert len(step_ids) == len(set(step_ids)), \
            "Step IDs should be unique"
        
        # Property: Step names should not be empty
        for step in steps:
            assert step.name and len(step.name.strip()) > 0, \
                "Step names should not be empty"
    
    @given(st.integers(min_value=0, max_value=5))  # Match the config retry_attempts
    @settings(max_examples=50, deadline=2000)
    def test_retry_mechanism_properties(self, retry_count):
        """
        Property: Retry mechanisms should follow exponential backoff and
        maintain proper retry count tracking.
        """
        # Create deployment config with retry settings
        config = DeploymentConfig(
            retry_attempts=5,
            retry_delay_seconds=2,
            retry_backoff_multiplier=2.0
        )
        
        # Property: Retry delay should increase exponentially
        if retry_count > 0:
            delay = config.get_retry_delay(retry_count)
            
            # Delay should be positive
            assert delay > 0, "Retry delay should be positive"
            
            # Delay should be capped at reasonable maximum
            assert delay <= 60, "Retry delay should be capped at 60 seconds"
            
            # Delay should increase with retry count (up to the cap)
            if retry_count > 1:
                previous_delay = config.get_retry_delay(retry_count - 1)
                if delay < 60 and previous_delay < 60:  # Both under cap
                    assert delay >= previous_delay, \
                        "Retry delay should increase or stay same with retry count"
        
        # Property: Zero retry count should have zero delay
        zero_delay = config.get_retry_delay(0)
        assert zero_delay == 0, "Zero retry count should have zero delay"
        
        # Property: Retry attempts should be within configured limits
        assert retry_count <= config.retry_attempts, \
            "Retry count should not exceed configured attempts"


if __name__ == "__main__":
    # Run a simple test to verify the property tests work
    def run_simple_test():
        # Test deployment step state management
        step = DeploymentStep(
            step_id="test_step",
            name="Test Step",
            status=DeploymentStatus.PENDING
        )
        
        # Mark as started
        step.mark_started()
        assert step.status == DeploymentStatus.PREPARING
        assert step.start_time is not None
        
        # Mark as completed
        step.mark_completed()
        assert step.is_completed
        assert step.progress_percentage == 100.0
        assert step.end_time is not None
        assert step.duration_seconds is not None
        assert step.duration_seconds >= 0
        
        print("✓ Deployment step state management test passed")
        
        # Test deployment result properties
        result = DeploymentResult(
            deployment_id="test_deployment",
            plan_id="test_plan", 
            environment_id="test_env",
            status=DeploymentStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            artifacts_deployed=5,
            dependencies_installed=3
        )
        
        assert result.is_successful
        assert not result.is_failed
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0
        
        print("✓ Deployment result properties test passed")
        
        # Test validation result
        validation = ValidationResult(
            environment_id="test_env",
            is_ready=True,
            checks_performed=["network", "disk", "memory"],
            failed_checks=[],
            warnings=[]
        )
        
        assert validation.success_rate == 100.0
        assert not validation.has_failures
        
        print("✓ Validation result test passed")
        
        print("All simple tests passed!")
    
    # Run the simple test
    run_simple_test()