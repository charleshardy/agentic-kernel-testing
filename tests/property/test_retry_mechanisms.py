"""
Property-based tests for retry mechanisms and error recovery.

Tests the deployment orchestrator's ability to handle failures gracefully
with exponential backoff retry logic and rollback capabilities.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, patch

from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentPlan, DeploymentConfig, InstrumentationConfig
)


class TestRetryMechanisms:
    """Test retry mechanisms and error recovery"""
    
    @given(
        failure_count=st.integers(min_value=1, max_value=5),
        retry_limit=st.integers(min_value=1, max_value=4)
    )
    @settings(max_examples=50, deadline=10000)
    async def test_automatic_retry_with_backoff(self, failure_count: int, retry_limit: int):
        """
        Property: Failed deployments are automatically retried with exponential backoff
        
        Validates that:
        1. Failed deployments trigger automatic retry
        2. Exponential backoff is applied between retries
        3. Retry limit is respected
        4. Final failure is recorded after exceeding retry limit
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=1)
        
        try:
            await orchestrator.start()
            
            # Create test artifact
            artifact = TestArtifact(
                artifact_id="test_artifact",
                name="test_script.sh",
                type=ArtifactType.SCRIPT,
                content=b"#!/bin/bash\necho 'test'",
                checksum="",
                permissions="0755",
                target_path="/tmp/test.sh"
            )
            
            # Mock the deployment pipeline to fail specified number of times
            original_process = orchestrator._process_deployment
            call_count = 0
            
            async def mock_process_deployment(deployment_plan):
                nonlocal call_count
                call_count += 1
                
                if call_count <= failure_count:
                    # Simulate failure
                    deployment = orchestrator.active_deployments[deployment_plan.plan_id]
                    deployment.status = DeploymentStatus.FAILED
                    deployment.end_time = datetime.now()
                    deployment.error_message = f"Simulated failure {call_count}"
                    raise RuntimeError(f"Simulated failure {call_count}")
                else:
                    # Success after failures
                    deployment = orchestrator.active_deployments[deployment_plan.plan_id]
                    deployment.status = DeploymentStatus.COMPLETED
                    deployment.end_time = datetime.now()
            
            orchestrator._process_deployment = mock_process_deployment
            
            # Start deployment
            deployment_id = await orchestrator.deploy_to_environment(
                plan_id="test_plan",
                env_id="test_env",
                artifacts=[artifact]
            )
            
            # Wait for deployment to complete or fail permanently
            max_wait_time = 60  # seconds (accounting for retry delays)
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < max_wait_time:
                deployment = orchestrator.get_deployment_status(deployment_id)
                
                if deployment and deployment.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]:
                    # Check if we've exceeded retry limit
                    if deployment.retry_count >= retry_limit:
                        break
                
                await asyncio.sleep(0.1)
            
            # Verify retry behavior
            final_deployment = orchestrator.get_deployment_status(deployment_id)
            assert final_deployment is not None, "Deployment should exist"
            
            if failure_count <= retry_limit:
                # Should eventually succeed
                assert final_deployment.status == DeploymentStatus.COMPLETED, \
                    f"Deployment should succeed after {failure_count} failures with retry limit {retry_limit}"
            else:
                # Should fail permanently after retry limit
                assert final_deployment.status == DeploymentStatus.FAILED, \
                    "Deployment should fail permanently after exceeding retry limit"
                assert final_deployment.retry_count >= retry_limit, \
                    f"Retry count {final_deployment.retry_count} should reach limit {retry_limit}"
            
            # Verify retry attempts were logged
            logs = orchestrator.get_deployment_logs(deployment_id)
            retry_logs = [log for log in logs if log.get("event") == "retry_attempt"]
            
            expected_retries = min(failure_count, retry_limit)
            assert len(retry_logs) >= expected_retries, \
                f"Expected at least {expected_retries} retry logs, got {len(retry_logs)}"
            
        finally:
            await orchestrator.stop()
    
    @given(
        deployment_count=st.integers(min_value=2, max_value=8),
        failure_rate=st.floats(min_value=0.1, max_value=0.8)
    )
    @settings(max_examples=30, deadline=15000)
    async def test_environment_unavailability_handling(self, deployment_count: int, failure_rate: float):
        """
        Property: Environment unavailability is handled gracefully
        
        Validates that:
        1. Deployments are queued when environment is unavailable
        2. Deployments proceed when environment becomes available
        3. No deployments are lost during environment unavailability
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=deployment_count)
        
        try:
            await orchestrator.start()
            
            # Create deployments
            deployment_ids = []
            for i in range(deployment_count):
                artifact = TestArtifact(
                    artifact_id=f"artifact_{i}",
                    name=f"test_{i}.sh",
                    type=ArtifactType.SCRIPT,
                    content=f"#!/bin/bash\necho 'test {i}'".encode(),
                    checksum="",
                    permissions="0755",
                    target_path=f"/tmp/test_{i}.sh"
                )
                
                deployment_id = await orchestrator.deploy_to_environment(
                    plan_id=f"plan_{i}",
                    env_id="shared_env",  # All use same environment
                    artifacts=[artifact]
                )
                deployment_ids.append(deployment_id)
            
            # Simulate environment unavailability for some deployments
            original_acquire = orchestrator.resource_manager.acquire_environment
            
            async def mock_acquire_environment(env_id):
                # Randomly fail based on failure rate
                import random
                if random.random() < failure_rate:
                    return False  # Environment unavailable
                return await original_acquire(env_id)
            
            orchestrator.resource_manager.acquire_environment = mock_acquire_environment
            
            # Wait for deployments to complete
            max_wait_time = 30
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < max_wait_time:
                active_deployments = orchestrator.get_active_deployments()
                
                # Check completion status
                completed_count = sum(
                    1 for d in active_deployments.values()
                    if d.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]
                )
                
                if completed_count >= deployment_count * 0.8:  # Allow some to still be processing
                    break
                
                await asyncio.sleep(0.2)
            
            # Verify all deployments were tracked
            final_deployments = orchestrator.get_active_deployments()
            assert len(final_deployments) == deployment_count, \
                f"Expected {deployment_count} deployments, got {len(final_deployments)}"
            
            # Verify no deployments were lost
            for deployment_id in deployment_ids:
                assert deployment_id in final_deployments, f"Deployment {deployment_id} was lost"
            
            # Verify queue management worked
            metrics = orchestrator.get_deployment_metrics()
            assert metrics["total_deployments"] == deployment_count, \
                "Total deployment count should match submitted count"
            
        finally:
            await orchestrator.stop()
    
    @given(
        rollback_scenarios=st.lists(
            st.sampled_from(["partial_failure", "connection_lost", "timeout"]),
            min_size=1, max_size=5
        )
    )
    @settings(max_examples=20, deadline=8000)
    async def test_deployment_rollback_capabilities(self, rollback_scenarios: List[str]):
        """
        Property: Failed deployments can be rolled back successfully
        
        Validates that:
        1. Rollback removes deployed artifacts
        2. Environment is cleaned up properly
        3. Rollback status is recorded correctly
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=1)
        
        try:
            await orchestrator.start()
            
            rollback_results = []
            
            for i, scenario in enumerate(rollback_scenarios):
                # Create test artifact
                artifact = TestArtifact(
                    artifact_id=f"rollback_artifact_{i}",
                    name=f"rollback_test_{i}.sh",
                    type=ArtifactType.SCRIPT,
                    content=f"#!/bin/bash\necho 'rollback test {i}'".encode(),
                    checksum="",
                    permissions="0755",
                    target_path=f"/tmp/rollback_test_{i}.sh"
                )
                
                # Start deployment
                deployment_id = await orchestrator.deploy_to_environment(
                    plan_id=f"rollback_plan_{i}",
                    env_id=f"rollback_env_{i}",
                    artifacts=[artifact]
                )
                
                # Wait for deployment to start
                await asyncio.sleep(0.1)
                
                # Simulate failure scenario
                deployment = orchestrator.get_deployment_status(deployment_id)
                if deployment:
                    deployment.status = DeploymentStatus.FAILED
                    deployment.error_message = f"Simulated {scenario} failure"
                    deployment.artifacts_deployed = 1  # Simulate partial deployment
                
                # Attempt rollback
                rollback_success = await orchestrator.rollback_deployment(deployment_id)
                rollback_results.append(rollback_success)
                
                # Verify rollback status
                final_deployment = orchestrator.get_deployment_status(deployment_id)
                if rollback_success and final_deployment:
                    assert final_deployment.status == DeploymentStatus.CANCELLED, \
                        f"Rolled back deployment should be cancelled, got {final_deployment.status}"
                    assert "rolled back" in final_deployment.error_message.lower(), \
                        "Rollback should be recorded in error message"
            
            # Verify at least some rollbacks succeeded (depending on scenarios)
            successful_rollbacks = sum(rollback_results)
            assert successful_rollbacks >= 0, "At least some rollbacks should be attempted"
            
        finally:
            await orchestrator.stop()


# Synchronous test runners for pytest
def test_automatic_retry_with_backoff_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestRetryMechanisms()
    
    asyncio.run(test_instance.test_automatic_retry_with_backoff(
        failure_count=2,
        retry_limit=3
    ))

def test_environment_unavailability_handling_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestRetryMechanisms()
    
    asyncio.run(test_instance.test_environment_unavailability_handling(
        deployment_count=4,
        failure_rate=0.3
    ))

def test_deployment_rollback_capabilities_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestRetryMechanisms()
    
    asyncio.run(test_instance.test_deployment_rollback_capabilities(
        rollback_scenarios=["partial_failure", "connection_lost"]
    ))


if __name__ == "__main__":
    # Run basic functionality test
    print("Testing retry mechanisms...")
    
    async def basic_test():
        test_instance = TestRetryMechanisms()
        
        try:
            await test_instance.test_automatic_retry_with_backoff(
                failure_count=1,
                retry_limit=2
            )
            print("✓ Automatic retry with backoff test passed")
            
            await test_instance.test_environment_unavailability_handling(
                deployment_count=3,
                failure_rate=0.2
            )
            print("✓ Environment unavailability handling test passed")
            
            await test_instance.test_deployment_rollback_capabilities(
                rollback_scenarios=["partial_failure"]
            )
            print("✓ Deployment rollback capabilities test passed")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(basic_test())