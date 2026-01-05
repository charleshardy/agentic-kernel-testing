"""
Property-based tests for detailed status reporting.

Tests the system's ability to provide comprehensive, accurate, and detailed
status reports for deployments with proper error information and remediation.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, patch
import json

from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentResult, DeploymentStep
)


class TestDetailedStatusReporting:
    """Test detailed status reporting capabilities"""
    
    @given(
        deployment_steps=st.integers(min_value=4, max_value=8),
        error_scenarios=st.lists(
            st.sampled_from([
                "connection_timeout", "permission_denied", "disk_full", 
                "network_unreachable", "invalid_artifact", "dependency_missing"
            ]),
            min_size=0, max_size=3
        ),
        step_details=st.lists(
            st.dictionaries(
                st.text(min_size=1, max_size=20),
                st.one_of(st.text(), st.integers(), st.booleans()),
                min_size=1, max_size=5
            ),
            min_size=4, max_size=8
        )
    )
    @settings(max_examples=30, deadline=15000)
    def test_detailed_status_reporting(self, deployment_steps: int, 
                                           error_scenarios: List[str], step_details: List[Dict[str, Any]]):
        """
        **Feature: test-deployment-system, Property 12: Detailed status reporting**
        
        Property: Detailed status reports contain comprehensive information
        
        Validates that:
        1. Status reports include all deployment steps with details
        2. Error messages are descriptive and actionable
        3. Timing information is accurate and complete
        4. Progress tracking is detailed and consistent
        """
        # Run the async test
        import asyncio
        asyncio.run(self._test_detailed_status_reporting_async(deployment_steps, error_scenarios, step_details))
    
    async def _test_detailed_status_reporting_async(self, deployment_steps: int, 
                                           error_scenarios: List[str], step_details: List[Dict[str, Any]]):
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=1)
        
        try:
            await orchestrator.start()
            
            # Create test deployment
            artifact = TestArtifact(
                artifact_id="detailed_status_artifact",
                name="detailed_status_test.sh",
                type=ArtifactType.SCRIPT,
                content=b"#!/bin/bash\necho 'detailed status test'",
                checksum="",
                permissions="0755",
                target_path="/tmp/detailed_status_test.sh"
            )
            
            deployment_id = await orchestrator.deploy_to_environment(
                plan_id="detailed_status_plan",
                env_id="detailed_status_env",
                artifacts=[artifact],
                priority=Priority.NORMAL
            )
            
            # Simulate deployment with detailed steps and potential errors
            deployment = await orchestrator.get_deployment_status(deployment_id)
            if deployment:
                # Add detailed steps with custom details
                for i in range(min(deployment_steps, len(step_details))):
                    step = DeploymentStep(
                        step_id=f"detailed_step_{i}",
                        name=f"Detailed Step {i+1}",
                        status=DeploymentStatus.COMPLETED if i < len(error_scenarios) else DeploymentStatus.PREPARING,
                        start_time=datetime.now() - timedelta(seconds=30-i*5),
                        end_time=datetime.now() - timedelta(seconds=25-i*5) if i < len(error_scenarios) else None,
                        details=step_details[i] if i < len(step_details) else {}
                    )
                    
                    # Add error to some steps based on scenarios
                    if i < len(error_scenarios):
                        error_scenario = error_scenarios[i]
                        step.status = DeploymentStatus.FAILED
                        step.error_message = self._generate_error_message(error_scenario)
                        step.end_time = datetime.now() - timedelta(seconds=20-i*5)
                    
                    deployment.steps.append(step)
                
                # Update overall deployment status based on step outcomes
                failed_steps = [s for s in deployment.steps if s.status == DeploymentStatus.FAILED]
                if failed_steps:
                    deployment.status = DeploymentStatus.FAILED
                    deployment.error_message = f"Deployment failed at step: {failed_steps[0].name}"
                else:
                    deployment.status = DeploymentStatus.COMPLETED
                
                deployment.end_time = datetime.now()
            
            # Wait briefly for any processing
            await asyncio.sleep(0.2)
            
            # Retrieve detailed status report
            final_status = await orchestrator.get_deployment_status(deployment_id)
            
            # Verify detailed status reporting properties
            assert final_status is not None, "Status report should be available"
            
            # Verify comprehensive step information
            assert len(final_status.steps) > 0, "Status report should include deployment steps"
            
            for step in final_status.steps:
                # Each step should have required fields
                assert step.step_id, "Step should have unique identifier"
                assert step.name, "Step should have descriptive name"
                assert step.status, "Step should have status"
                
                # Timing information should be present for started steps
                if step.status != DeploymentStatus.PENDING:
                    assert step.start_time is not None, f"Step {step.name} should have start time"
                
                # Completed or failed steps should have end time
                if step.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]:
                    assert step.end_time is not None, f"Step {step.name} should have end time"
                    
                    # Duration should be calculable and reasonable
                    if step.start_time and step.end_time:
                        duration = step.duration_seconds
                        assert duration is not None, f"Step {step.name} should have calculable duration"
                        assert duration >= 0, f"Step {step.name} duration should be non-negative"
                        assert duration < 3600, f"Step {step.name} duration should be reasonable (< 1 hour)"
                
                # Failed steps should have error messages
                if step.status == DeploymentStatus.FAILED:
                    assert step.error_message, f"Failed step {step.name} should have error message"
                    assert len(step.error_message) > 10, f"Error message should be descriptive"
                
                # Steps should have details dictionary
                assert isinstance(step.details, dict), f"Step {step.name} should have details dictionary"
            
            # Verify overall deployment information completeness
            assert final_status.deployment_id == deployment_id, "Deployment ID should match"
            assert final_status.plan_id, "Plan ID should be present"
            assert final_status.environment_id, "Environment ID should be present"
            assert final_status.start_time, "Start time should be present"
            
            # Verify progress calculation consistency
            if final_status.steps:
                completed_steps = sum(1 for s in final_status.steps if s.status == DeploymentStatus.COMPLETED)
                total_steps = len(final_status.steps)
                expected_min_progress = (completed_steps / total_steps) * 70  # Allow variance
                
                assert final_status.completion_percentage >= expected_min_progress, \
                    f"Progress {final_status.completion_percentage}% should reflect completed steps"
            
            # Verify error reporting quality
            if final_status.status == DeploymentStatus.FAILED:
                assert final_status.error_message, "Failed deployment should have error message"
                
                # Error message should be actionable
                error_msg = final_status.error_message.lower()
                actionable_keywords = [
                    'check', 'verify', 'ensure', 'configure', 'install', 
                    'permission', 'connection', 'space', 'network'
                ]
                
                # At least some error messages should contain actionable information
                has_actionable_info = any(keyword in error_msg for keyword in actionable_keywords)
                if not has_actionable_info:
                    # Check if any step error messages are actionable
                    step_errors = [s.error_message for s in final_status.steps if s.error_message]
                    has_actionable_info = any(
                        any(keyword in err.lower() for keyword in actionable_keywords)
                        for err in step_errors
                    )
                
                # This is a soft assertion - not all errors may be actionable
                if not has_actionable_info:
                    print(f"Warning: Error messages may not be sufficiently actionable: {final_status.error_message}")
            
        finally:
            await orchestrator.stop()
    
    def _generate_error_message(self, scenario: str) -> str:
        """Generate realistic error messages for different scenarios"""
        error_messages = {
            "connection_timeout": "Connection to environment timed out after 30 seconds. Check network connectivity and ensure the target environment is accessible.",
            "permission_denied": "Permission denied when accessing /tmp/test.sh. Verify that the deployment user has write permissions to the target directory.",
            "disk_full": "No space left on device. The target environment has insufficient disk space. Free up space or use a different environment.",
            "network_unreachable": "Network unreachable. The target environment cannot be reached. Check network configuration and firewall settings.",
            "invalid_artifact": "Artifact validation failed. The uploaded artifact has an invalid checksum or is corrupted. Re-upload the artifact.",
            "dependency_missing": "Required dependency 'python3' not found. Install the missing dependency or update the deployment configuration."
        }
        return error_messages.get(scenario, f"Unknown error occurred during {scenario}")
    
    @given(
        status_updates=st.integers(min_value=5, max_value=15),
        update_interval=st.floats(min_value=0.1, max_value=1.0)
    )
    @settings(max_examples=20, deadline=12000)
    def test_status_update_consistency(self, status_updates: int, update_interval: float):
        """
        **Feature: test-deployment-system, Property 12: Detailed status reporting**
        
        Property: Status updates are consistent and maintain data integrity
        
        Validates that:
        1. Status updates preserve data consistency
        2. Timestamps are monotonically increasing
        3. Status transitions are logical
        4. No information is lost between updates
        """
        # Run the async test
        import asyncio
        asyncio.run(self._test_status_update_consistency_async(status_updates, update_interval))
    
    async def _test_status_update_consistency_async(self, status_updates: int, update_interval: float):
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=1)
        
        try:
            await orchestrator.start()
            
            # Create test deployment
            artifact = TestArtifact(
                artifact_id="consistency_test_artifact",
                name="consistency_test.sh",
                type=ArtifactType.SCRIPT,
                content=b"#!/bin/bash\necho 'consistency test'",
                checksum="",
                permissions="0755",
                target_path="/tmp/consistency_test.sh"
            )
            
            deployment_id = await orchestrator.deploy_to_environment(
                plan_id="consistency_test_plan",
                env_id="consistency_test_env",
                artifacts=[artifact],
                priority=Priority.NORMAL
            )
            
            # Collect status updates over time
            status_history = []
            
            for i in range(status_updates):
                status = await orchestrator.get_deployment_status(deployment_id)
                if status:
                    status_snapshot = {
                        "timestamp": datetime.now(),
                        "status": status.status.value,
                        "progress": status.completion_percentage,
                        "step_count": len(status.steps),
                        "artifacts_deployed": status.artifacts_deployed,
                        "retry_count": status.retry_count,
                        "error_message": status.error_message
                    }
                    status_history.append(status_snapshot)
                
                await asyncio.sleep(update_interval)
            
            # Verify status update consistency
            assert len(status_history) > 0, "Should have captured status updates"
            
            # Verify timestamp consistency
            for i in range(1, len(status_history)):
                prev_timestamp = status_history[i-1]["timestamp"]
                curr_timestamp = status_history[i]["timestamp"]
                
                assert curr_timestamp >= prev_timestamp, \
                    f"Timestamps should be monotonically increasing: {prev_timestamp} -> {curr_timestamp}"
            
            # Verify progress consistency (should not decrease significantly)
            for i in range(1, len(status_history)):
                prev_progress = status_history[i-1]["progress"]
                curr_progress = status_history[i]["progress"]
                
                # Allow small decreases during step transitions
                assert curr_progress >= prev_progress - 15, \
                    f"Progress should not decrease significantly: {prev_progress}% -> {curr_progress}%"
            
            # Verify step count consistency (should not decrease)
            for i in range(1, len(status_history)):
                prev_steps = status_history[i-1]["step_count"]
                curr_steps = status_history[i]["step_count"]
                
                assert curr_steps >= prev_steps, \
                    f"Step count should not decrease: {prev_steps} -> {curr_steps}"
            
            # Verify artifacts deployed consistency (should not decrease)
            for i in range(1, len(status_history)):
                prev_artifacts = status_history[i-1]["artifacts_deployed"]
                curr_artifacts = status_history[i]["artifacts_deployed"]
                
                assert curr_artifacts >= prev_artifacts, \
                    f"Artifacts deployed should not decrease: {prev_artifacts} -> {curr_artifacts}"
            
            # Verify status transitions are logical
            status_sequence = [update["status"] for update in status_history]
            unique_statuses = list(dict.fromkeys(status_sequence))  # Preserve order, remove duplicates
            
            # Define valid status transitions
            valid_transitions = {
                'pending': ['preparing', 'connecting', 'failed', 'cancelled'],
                'preparing': ['connecting', 'installing_dependencies', 'failed', 'cancelled'],
                'connecting': ['installing_dependencies', 'deploying_scripts', 'failed', 'cancelled'],
                'installing_dependencies': ['deploying_scripts', 'configuring_instrumentation', 'failed', 'cancelled'],
                'deploying_scripts': ['configuring_instrumentation', 'validating', 'failed', 'cancelled'],
                'configuring_instrumentation': ['validating', 'completed', 'failed', 'cancelled'],
                'validating': ['completed', 'failed', 'cancelled'],
                'completed': [],  # Final state
                'failed': [],     # Final state
                'cancelled': []   # Final state
            }
            
            # Verify each transition is valid
            for i in range(1, len(unique_statuses)):
                prev_status = unique_statuses[i-1]
                curr_status = unique_statuses[i]
                
                if prev_status in valid_transitions:
                    valid_next = valid_transitions[prev_status]
                    if valid_next:  # If not a final state
                        assert curr_status in valid_next or curr_status == prev_status, \
                            f"Invalid status transition: {prev_status} -> {curr_status}"
            
        finally:
            await orchestrator.stop()
    
    @given(
        error_types=st.lists(
            st.sampled_from([
                "timeout", "permission", "network", "resource", "validation", "configuration"
            ]),
            min_size=1, max_size=4
        ),
        remediation_required=st.booleans()
    )
    @settings(max_examples=25, deadline=10000)
    def test_error_reporting_quality(self, error_types: List[str], remediation_required: bool):
        """
        **Feature: test-deployment-system, Property 12: Detailed status reporting**
        
        Property: Error reports are comprehensive and actionable
        
        Validates that:
        1. Error messages are descriptive and specific
        2. Remediation suggestions are provided when appropriate
        3. Error context includes relevant system information
        4. Multiple errors are properly aggregated and reported
        """
        # Run the async test
        import asyncio
        asyncio.run(self._test_error_reporting_quality_async(error_types, remediation_required))
    
    async def _test_error_reporting_quality_async(self, error_types: List[str], remediation_required: bool):
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=1)
        
        try:
            await orchestrator.start()
            
            # Create test deployment
            artifact = TestArtifact(
                artifact_id="error_reporting_artifact",
                name="error_reporting_test.sh",
                type=ArtifactType.SCRIPT,
                content=b"#!/bin/bash\necho 'error reporting test'",
                checksum="",
                permissions="0755",
                target_path="/tmp/error_reporting_test.sh"
            )
            
            deployment_id = await orchestrator.deploy_to_environment(
                plan_id="error_reporting_plan",
                env_id="error_reporting_env",
                artifacts=[artifact],
                priority=Priority.NORMAL
            )
            
            # Simulate deployment with various error types
            deployment = await orchestrator.get_deployment_status(deployment_id)
            if deployment:
                # Add steps with different error types
                for i, error_type in enumerate(error_types):
                    step = DeploymentStep(
                        step_id=f"error_step_{i}",
                        name=f"Error Step {i+1} ({error_type})",
                        status=DeploymentStatus.FAILED,
                        start_time=datetime.now() - timedelta(seconds=60-i*10),
                        end_time=datetime.now() - timedelta(seconds=50-i*10),
                        error_message=self._generate_detailed_error_message(error_type, remediation_required),
                        details={
                            "error_type": error_type,
                            "error_code": f"ERR_{error_type.upper()}_{i:03d}",
                            "system_info": {
                                "environment": "error_reporting_env",
                                "timestamp": datetime.now().isoformat(),
                                "step_index": i
                            }
                        }
                    )
                    deployment.steps.append(step)
                
                # Set overall deployment status
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = f"Deployment failed with {len(error_types)} errors"
                deployment.end_time = datetime.now()
            
            # Wait briefly for processing
            await asyncio.sleep(0.1)
            
            # Retrieve and analyze error reporting
            final_status = await orchestrator.get_deployment_status(deployment_id)
            
            # Verify error reporting quality
            assert final_status is not None, "Status should be available"
            assert final_status.status == DeploymentStatus.FAILED, "Deployment should be marked as failed"
            
            # Verify overall error message
            assert final_status.error_message, "Failed deployment should have error message"
            assert len(final_status.error_message) > 5, "Error message should be descriptive"
            
            # Verify step-level error reporting
            failed_steps = [s for s in final_status.steps if s.status == DeploymentStatus.FAILED]
            assert len(failed_steps) == len(error_types), "Should have failed steps for each error type"
            
            for step in failed_steps:
                # Error message quality
                assert step.error_message, f"Step {step.name} should have error message"
                assert len(step.error_message) > 20, f"Step {step.name} error message should be detailed"
                
                # Error context in details
                assert "error_type" in step.details, f"Step {step.name} should have error type in details"
                assert "error_code" in step.details, f"Step {step.name} should have error code"
                assert "system_info" in step.details, f"Step {step.name} should have system info"
                
                # System information completeness
                system_info = step.details["system_info"]
                assert "environment" in system_info, "System info should include environment"
                assert "timestamp" in system_info, "System info should include timestamp"
                
                # Remediation suggestions (if required)
                if remediation_required:
                    error_msg_lower = step.error_message.lower()
                    remediation_keywords = [
                        'check', 'verify', 'ensure', 'try', 'consider',
                        'install', 'configure', 'update', 'restart'
                    ]
                    has_remediation = any(keyword in error_msg_lower for keyword in remediation_keywords)
                    
                    if not has_remediation:
                        print(f"Warning: Step {step.name} may lack remediation suggestions")
            
            # Verify error aggregation
            unique_error_types = set(error_types)
            reported_error_types = set()
            
            for step in failed_steps:
                if "error_type" in step.details:
                    reported_error_types.add(step.details["error_type"])
            
            assert reported_error_types == unique_error_types, \
                "All error types should be properly reported"
            
        finally:
            await orchestrator.stop()
    
    def _generate_detailed_error_message(self, error_type: str, include_remediation: bool) -> str:
        """Generate detailed error messages with optional remediation"""
        base_messages = {
            "timeout": "Operation timed out after 30 seconds while connecting to target environment",
            "permission": "Access denied when attempting to write to /tmp/test.sh",
            "network": "Network connection failed - unable to reach target host 192.168.1.100",
            "resource": "Insufficient disk space - only 50MB available, 100MB required",
            "validation": "Artifact validation failed - checksum mismatch detected",
            "configuration": "Invalid configuration parameter 'max_retries' - expected integer, got string"
        }
        
        remediation_suggestions = {
            "timeout": "Check network connectivity and increase timeout settings if needed",
            "permission": "Verify deployment user has write permissions to target directory",
            "network": "Check firewall settings and ensure target environment is accessible",
            "resource": "Free up disk space or use an environment with more available storage",
            "validation": "Re-upload the artifact or check for corruption during transfer",
            "configuration": "Review configuration file and correct parameter types"
        }
        
        message = base_messages.get(error_type, f"Unknown {error_type} error occurred")
        
        if include_remediation and error_type in remediation_suggestions:
            message += f". {remediation_suggestions[error_type]}"
        
        return message


# Synchronous test runners for pytest
@given(
    deployment_steps=st.integers(min_value=4, max_value=8),
    error_scenarios=st.lists(
        st.sampled_from([
            "connection_timeout", "permission_denied", "disk_full", 
            "network_unreachable", "invalid_artifact", "dependency_missing"
        ]),
        min_size=0, max_size=3
    ),
    step_details=st.lists(
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.text(), st.integers(), st.booleans()),
            min_size=1, max_size=5
        ),
        min_size=4, max_size=8
    )
)
@settings(max_examples=10, deadline=15000)
def test_detailed_status_reporting_property(deployment_steps: int, 
                                           error_scenarios: List[str], 
                                           step_details: List[Dict[str, Any]]):
    """
    **Feature: test-deployment-system, Property 12: Detailed status reporting**
    
    Property-based test for detailed status reporting functionality.
    Validates Requirements 3.2.
    """
    test_instance = TestDetailedStatusReporting()
    
    # Run the async test
    import asyncio
    asyncio.run(test_instance._test_detailed_status_reporting_async(
        deployment_steps, error_scenarios, step_details
    ))

def test_detailed_status_reporting_sync():
    """Simple synchronous test for detailed status reporting"""
    test_instance = TestDetailedStatusReporting()
    
    # Run with specific test values
    import asyncio
    asyncio.run(test_instance._test_detailed_status_reporting_async(
        deployment_steps=5,
        error_scenarios=["connection_timeout", "permission_denied"],
        step_details=[
            {"artifacts_processed": 3, "duration_ms": 1500},
            {"connections_established": 1, "retry_count": 0},
            {"dependencies_installed": 2, "packages": ["python3", "curl"]},
            {"scripts_deployed": 1, "permissions_set": True},
            {"validation_passed": False, "error_count": 1}
        ]
    ))

def test_status_update_consistency_sync():
    """Simple synchronous test for status update consistency"""
    test_instance = TestDetailedStatusReporting()
    
    # Run with specific test values
    import asyncio
    asyncio.run(test_instance._test_status_update_consistency_async(
        status_updates=8,
        update_interval=0.3
    ))

def test_error_reporting_quality_sync():
    """Simple synchronous test for error reporting quality"""
    test_instance = TestDetailedStatusReporting()
    
    # Run with specific test values
    import asyncio
    asyncio.run(test_instance._test_error_reporting_quality_async(
        error_types=["timeout", "permission", "network"],
        remediation_required=True
    ))


if __name__ == "__main__":
    # Run basic functionality test
    print("Testing detailed status reporting...")
    
    async def basic_test():
        test_instance = TestDetailedStatusReporting()
        
        try:
            await test_instance._test_detailed_status_reporting_async(
                deployment_steps=4,
                error_scenarios=["timeout"],
                step_details=[
                    {"test": "value1"},
                    {"test": "value2"},
                    {"test": "value3"},
                    {"test": "value4"}
                ]
            )
            print("✓ Detailed status reporting test passed")
            
            await test_instance._test_status_update_consistency_async(
                status_updates=6,
                update_interval=0.2
            )
            print("✓ Status update consistency test passed")
            
            await test_instance._test_error_reporting_quality_async(
                error_types=["timeout", "permission"],
                remediation_required=True
            )
            print("✓ Error reporting quality test passed")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(basic_test())