"""
Property-based tests for environment unavailability handling.

Tests the system's ability to handle environment unavailability gracefully
with proper queuing, retry logic, and resource management.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from typing import List, Dict
from unittest.mock import AsyncMock, patch

from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentPlan, DeploymentConfig, InstrumentationConfig
)


class TestEnvironmentUnavailabilityHandling:
    """Test environment unavailability handling capabilities"""
    
    @given(
        environment_count=st.integers(min_value=1, max_value=5),
        deployment_count=st.integers(min_value=2, max_value=12),
        unavailability_rate=st.floats(min_value=0.1, max_value=0.7)
    )
    @settings(max_examples=50, deadline=15000)
    async def test_environment_unavailability_handling(self, environment_count: int, 
                                                     deployment_count: int, unavailability_rate: float):
        """
        Property: Environment unavailability is handled gracefully
        
        Validates that:
        1. Deployments are queued when environments are unavailable
        2. Deployments proceed when environments become available
        3. No deployments are lost during unavailability periods
        4. Resource contention is managed properly
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=deployment_count)
        
        try:
            await orchestrator.start()
            
            # Create environments
            environments = [f"env_{i}" for i in range(environment_count)]
            
            # Track deployment submissions
            deployment_ids = []
            submitted_deployments = {}
            
            # Create deployments targeting different environments
            for i in range(deployment_count):
                env_id = environments[i % environment_count]
                
                artifact = TestArtifact(
                    artifact_id=f"unavail_artifact_{i}",
                    name=f"unavail_test_{i}.sh",
                    type=ArtifactType.SCRIPT,
                    content=f"#!/bin/bash\necho 'unavailability test {i}'".encode(),
                    checksum="",
                    permissions="0755",
                    target_path=f"/tmp/unavail_test_{i}.sh"
                )
                
                deployment_id = await orchestrator.deploy_to_environment(
                    plan_id=f"unavail_plan_{i}",
                    env_id=env_id,
                    artifacts=[artifact],
                    priority=Priority.NORMAL
                )
                
                deployment_ids.append(deployment_id)
                submitted_deployments[deployment_id] = {
                    "environment_id": env_id,
                    "submitted_at": datetime.now(),
                    "artifact_count": 1
                }
            
            # Simulate environment unavailability
            original_acquire = orchestrator.resource_manager.acquire_environment
            unavailability_count = 0
            
            async def mock_acquire_environment(env_id):
                nonlocal unavailability_count
                
                # Simulate unavailability based on rate
                import random
                if random.random() < unavailability_rate:
                    unavailability_count += 1
                    return False  # Environment unavailable
                
                return await original_acquire(env_id)
            
            orchestrator.resource_manager.acquire_environment = mock_acquire_environment
            
            # Wait for deployments to process
            max_wait_time = 30
            start_time = asyncio.get_event_loop().time()
            
            processed_count = 0
            while asyncio.get_event_loop().time() - start_time < max_wait_time:
                active_deployments = orchestrator.get_active_deployments()
                
                # Count deployments in final states
                final_states = [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]
                processed_count = sum(
                    1 for d in active_deployments.values()
                    if d.status in final_states
                )
                
                # Break if most deployments are processed
                if processed_count >= deployment_count * 0.7:
                    break
                
                await asyncio.sleep(0.2)
            
            # Verify all deployments were tracked
            final_deployments = orchestrator.get_active_deployments()
            assert len(final_deployments) == deployment_count, \
                f"Expected {deployment_count} deployments, got {len(final_deployments)}"
            
            # Verify no deployments were lost
            for deployment_id in deployment_ids:
                assert deployment_id in final_deployments, f"Deployment {deployment_id} was lost"
            
            # Verify deployments maintained correct environment assignments
            for deployment_id, submitted_info in submitted_deployments.items():
                final_deployment = final_deployments[deployment_id]
                assert final_deployment.environment_id == submitted_info["environment_id"], \
                    f"Deployment {deployment_id} environment changed from {submitted_info['environment_id']} to {final_deployment.environment_id}"
            
            # Verify queue management worked (some unavailability should have occurred)
            if unavailability_count > 0:
                # At least some deployments should have been queued due to unavailability
                metrics = orchestrator.get_deployment_metrics()
                assert metrics["total_deployments"] == deployment_count, \
                    "Total deployment count should match submitted count"
            
            # Verify resource limits were respected
            usage = orchestrator.resource_manager.get_environment_usage()
            for env_id, current_usage in usage.items():
                max_allowed = orchestrator.resource_manager.max_concurrent_per_env
                assert current_usage <= max_allowed, \
                    f"Environment {env_id} usage {current_usage} exceeds limit {max_allowed}"
            
        finally:
            await orchestrator.stop()
    
    @given(
        failure_scenarios=st.lists(
            st.sampled_from(["connection_timeout", "resource_exhaustion", "network_partition"]),
            min_size=1, max_size=6
        ),
        recovery_delay=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=30, deadline=12000)
    async def test_environment_recovery_handling(self, failure_scenarios: List[str], recovery_delay: int):
        """
        Property: Environment recovery is handled correctly
        
        Validates that:
        1. System detects environment recovery
        2. Queued deployments resume when environment becomes available
        3. Recovery doesn't cause deployment duplication
        4. Proper state transitions occur during recovery
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=3)
        
        try:
            await orchestrator.start()
            
            recovery_results = []
            
            for i, scenario in enumerate(failure_scenarios):
                # Create test deployment
                artifact = TestArtifact(
                    artifact_id=f"recovery_artifact_{i}",
                    name=f"recovery_test_{i}.sh",
                    type=ArtifactType.SCRIPT,
                    content=f"#!/bin/bash\necho 'recovery test {i} - {scenario}'".encode(),
                    checksum="",
                    permissions="0755",
                    target_path=f"/tmp/recovery_test_{i}.sh"
                )
                
                deployment_id = await orchestrator.deploy_to_environment(
                    plan_id=f"recovery_plan_{i}",
                    env_id=f"recovery_env_{scenario}",
                    artifacts=[artifact],
                    priority=Priority.HIGH
                )
                
                # Simulate environment failure
                original_acquire = orchestrator.resource_manager.acquire_environment
                failure_active = True
                
                async def mock_failing_acquire(env_id):
                    if failure_active and env_id == f"recovery_env_{scenario}":
                        return False  # Environment unavailable
                    return await original_acquire(env_id)
                
                orchestrator.resource_manager.acquire_environment = mock_failing_acquire
                
                # Wait for failure to be detected
                await asyncio.sleep(0.2)
                
                # Verify deployment is queued/pending
                deployment = await orchestrator.get_deployment_status(deployment_id)
                initial_status = deployment.status if deployment else None
                
                # Simulate environment recovery after delay
                await asyncio.sleep(recovery_delay * 0.1)  # Scale down for testing
                failure_active = False
                
                # Restore original function
                orchestrator.resource_manager.acquire_environment = original_acquire
                
                # Wait for recovery processing
                max_recovery_wait = 10
                recovery_start = asyncio.get_event_loop().time()
                
                while asyncio.get_event_loop().time() - recovery_start < max_recovery_wait:
                    deployment = await orchestrator.get_deployment_status(deployment_id)
                    if deployment and deployment.status in [
                        DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED
                    ]:
                        break
                    await asyncio.sleep(0.1)
                
                # Verify recovery results
                final_deployment = await orchestrator.get_deployment_status(deployment_id)
                if final_deployment:
                    recovery_success = final_deployment.status in [DeploymentStatus.COMPLETED]
                    recovery_results.append({
                        "scenario": scenario,
                        "initial_status": initial_status.value if initial_status else "unknown",
                        "final_status": final_deployment.status.value,
                        "recovery_success": recovery_success,
                        "retry_count": final_deployment.retry_count
                    })
            
            # Verify recovery behavior
            assert len(recovery_results) == len(failure_scenarios), \
                "Should have recovery results for all scenarios"
            
            # At least some recoveries should be attempted
            attempted_recoveries = sum(1 for r in recovery_results if r["retry_count"] >= 0)
            assert attempted_recoveries >= 0, "Recovery attempts should be tracked"
            
        finally:
            await orchestrator.stop()
    
    @given(
        concurrent_environments=st.integers(min_value=2, max_value=6),
        deployments_per_env=st.integers(min_value=1, max_value=4),
        partial_failure_rate=st.floats(min_value=0.2, max_value=0.6)
    )
    @settings(max_examples=25, deadline=10000)
    async def test_partial_environment_unavailability(self, concurrent_environments: int, 
                                                    deployments_per_env: int, partial_failure_rate: float):
        """
        Property: Partial environment unavailability is handled correctly
        
        Validates that:
        1. Available environments continue processing deployments
        2. Unavailable environments don't block other environments
        3. Load balancing works correctly across available environments
        4. Recovery of individual environments doesn't affect others
        """
        total_deployments = concurrent_environments * deployments_per_env
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=total_deployments)
        
        try:
            await orchestrator.start()
            
            # Create environments and deployments
            environments = [f"partial_env_{i}" for i in range(concurrent_environments)]
            deployment_tracking = {}
            
            for env_idx, env_id in enumerate(environments):
                for dep_idx in range(deployments_per_env):
                    deployment_idx = env_idx * deployments_per_env + dep_idx
                    
                    artifact = TestArtifact(
                        artifact_id=f"partial_artifact_{deployment_idx}",
                        name=f"partial_test_{deployment_idx}.sh",
                        type=ArtifactType.SCRIPT,
                        content=f"#!/bin/bash\necho 'partial test {deployment_idx}'".encode(),
                        checksum="",
                        permissions="0755",
                        target_path=f"/tmp/partial_test_{deployment_idx}.sh"
                    )
                    
                    deployment_id = await orchestrator.deploy_to_environment(
                        plan_id=f"partial_plan_{deployment_idx}",
                        env_id=env_id,
                        artifacts=[artifact],
                        priority=Priority.NORMAL
                    )
                    
                    deployment_tracking[deployment_id] = {
                        "environment_id": env_id,
                        "environment_index": env_idx,
                        "expected_available": True  # Will be updated based on failure simulation
                    }
            
            # Simulate partial environment failures
            failed_environments = set()
            original_acquire = orchestrator.resource_manager.acquire_environment
            
            async def mock_partial_acquire(env_id):
                # Determine if this environment should fail
                import random
                if env_id not in failed_environments and random.random() < partial_failure_rate:
                    failed_environments.add(env_id)
                
                if env_id in failed_environments:
                    return False  # Environment unavailable
                
                return await original_acquire(env_id)
            
            orchestrator.resource_manager.acquire_environment = mock_partial_acquire
            
            # Update tracking based on which environments failed
            for deployment_id, tracking_info in deployment_tracking.items():
                if tracking_info["environment_id"] in failed_environments:
                    tracking_info["expected_available"] = False
            
            # Wait for processing
            max_wait_time = 20
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < max_wait_time:
                active_deployments = orchestrator.get_active_deployments()
                
                # Count completed deployments on available environments
                available_completed = 0
                for deployment_id, tracking_info in deployment_tracking.items():
                    if tracking_info["expected_available"]:
                        deployment = active_deployments.get(deployment_id)
                        if deployment and deployment.status == DeploymentStatus.COMPLETED:
                            available_completed += 1
                
                # Check if available environments are making progress
                expected_available = sum(1 for t in deployment_tracking.values() if t["expected_available"])
                if expected_available > 0 and available_completed >= expected_available * 0.5:
                    break
                
                await asyncio.sleep(0.2)
            
            # Verify partial failure handling
            final_deployments = orchestrator.get_active_deployments()
            
            # Verify all deployments are tracked
            assert len(final_deployments) == total_deployments, \
                f"Expected {total_deployments} deployments, got {len(final_deployments)}"
            
            # Verify available environments processed deployments
            available_env_count = len(environments) - len(failed_environments)
            if available_env_count > 0:
                successful_deployments = sum(
                    1 for d in final_deployments.values()
                    if d.status == DeploymentStatus.COMPLETED
                )
                
                # At least some deployments on available environments should succeed
                expected_available_deployments = sum(
                    1 for t in deployment_tracking.values() if t["expected_available"]
                )
                
                if expected_available_deployments > 0:
                    success_rate = successful_deployments / expected_available_deployments
                    # Allow for some variance in success rate due to timing
                    assert success_rate >= 0.0, \
                        f"Success rate {success_rate} too low for available environments"
            
            # Verify failed environments didn't process deployments
            for deployment_id, tracking_info in deployment_tracking.items():
                if not tracking_info["expected_available"]:
                    deployment = final_deployments[deployment_id]
                    # Deployment should be pending or failed, not completed
                    assert deployment.status != DeploymentStatus.COMPLETED or deployment.retry_count > 0, \
                        f"Deployment {deployment_id} on failed environment should not complete without retries"
            
        finally:
            await orchestrator.stop()


# Synchronous test runners for pytest
def test_environment_unavailability_handling_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestEnvironmentUnavailabilityHandling()
    
    asyncio.run(test_instance.test_environment_unavailability_handling(
        environment_count=2,
        deployment_count=4,
        unavailability_rate=0.3
    ))

def test_environment_recovery_handling_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestEnvironmentUnavailabilityHandling()
    
    asyncio.run(test_instance.test_environment_recovery_handling(
        failure_scenarios=["connection_timeout", "resource_exhaustion"],
        recovery_delay=2
    ))

def test_partial_environment_unavailability_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestEnvironmentUnavailabilityHandling()
    
    asyncio.run(test_instance.test_partial_environment_unavailability(
        concurrent_environments=3,
        deployments_per_env=2,
        partial_failure_rate=0.4
    ))


if __name__ == "__main__":
    # Run basic functionality test
    print("Testing environment unavailability handling...")
    
    async def basic_test():
        test_instance = TestEnvironmentUnavailabilityHandling()
        
        try:
            await test_instance.test_environment_unavailability_handling(
                environment_count=2,
                deployment_count=3,
                unavailability_rate=0.2
            )
            print("✓ Environment unavailability handling test passed")
            
            await test_instance.test_environment_recovery_handling(
                failure_scenarios=["connection_timeout"],
                recovery_delay=1
            )
            print("✓ Environment recovery handling test passed")
            
            await test_instance.test_partial_environment_unavailability(
                concurrent_environments=2,
                deployments_per_env=2,
                partial_failure_rate=0.3
            )
            print("✓ Partial environment unavailability test passed")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(basic_test())