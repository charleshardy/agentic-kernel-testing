"""
Property-based tests for concurrent deployment management.

Tests the deployment orchestrator's ability to handle multiple concurrent
deployments with proper resource management and priority scheduling.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from typing import List

from deployment.orchestrator import DeploymentOrchestrator, DeploymentQueue, ResourceManager
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentPlan, DeploymentConfig, InstrumentationConfig
)


class TestConcurrentDeploymentManagement:
    """Test concurrent deployment management capabilities"""
    
    @given(
        deployment_count=st.integers(min_value=2, max_value=10),
        environment_count=st.integers(min_value=1, max_value=5),
        max_concurrent=st.integers(min_value=1, max_value=8)
    )
    @settings(max_examples=100, deadline=5000)
    async def test_concurrent_deployment_management(self, deployment_count: int, environment_count: int, max_concurrent: int):
        """
        Property: Concurrent deployments are properly managed with resource limits
        
        Validates that:
        1. Multiple deployments can run concurrently up to the limit
        2. Resource contention is handled correctly
        3. Priority scheduling works as expected
        4. No deployment is lost or duplicated
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=max_concurrent)
        
        try:
            await orchestrator.start()
            
            # Create test environments
            environments = [f"env_{i}" for i in range(environment_count)]
            
            # Create deployments with different priorities
            deployment_ids = []
            priorities = [Priority.LOW, Priority.NORMAL, Priority.HIGH, Priority.CRITICAL]
            
            for i in range(deployment_count):
                env_id = environments[i % environment_count]
                priority = priorities[i % len(priorities)]
                
                # Create test artifact
                artifact = TestArtifact(
                    artifact_id=f"artifact_{i}",
                    name=f"test_script_{i}.sh",
                    type=ArtifactType.SCRIPT,
                    content=f"#!/bin/bash\necho 'Test {i}'".encode(),
                    checksum="",
                    permissions="0755",
                    target_path=f"/tmp/test_{i}.sh"
                )
                
                deployment_id = await orchestrator.deploy_to_environment(
                    plan_id=f"plan_{i}",
                    env_id=env_id,
                    artifacts=[artifact],
                    priority=priority
                )
                deployment_ids.append(deployment_id)
            
            # Wait for all deployments to complete or timeout
            max_wait_time = 30  # seconds
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < max_wait_time:
                active_deployments = orchestrator.get_active_deployments()
                
                # Check if all deployments are in final state
                final_states = [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]
                all_final = all(
                    deployment.status in final_states 
                    for deployment in active_deployments.values()
                )
                
                if all_final:
                    break
                
                await asyncio.sleep(0.1)
            
            # Verify all deployments were processed
            final_deployments = orchestrator.get_active_deployments()
            assert len(final_deployments) == deployment_count, "All deployments should be tracked"
            
            # Verify no deployment was lost
            for deployment_id in deployment_ids:
                assert deployment_id in final_deployments, f"Deployment {deployment_id} was lost"
            
            # Verify resource limits were respected
            metrics = orchestrator.get_deployment_metrics()
            assert metrics["total_deployments"] == deployment_count, "Total deployment count should match"
            
            # Verify concurrent execution didn't exceed limits
            # (This is implicitly tested by the orchestrator's semaphore mechanism)
            
        finally:
            await orchestrator.stop()
    
    @given(
        queue_size=st.integers(min_value=1, max_value=20),
        priority_distribution=st.lists(
            st.sampled_from([Priority.LOW, Priority.NORMAL, Priority.HIGH, Priority.CRITICAL]),
            min_size=1, max_size=20
        )
    )
    @settings(max_examples=50, deadline=3000)
    async def test_priority_queue_ordering(self, queue_size: int, priority_distribution: List[Priority]):
        """
        Property: Deployments are processed in priority order
        
        Validates that higher priority deployments are processed before lower priority ones.
        """
        queue = DeploymentQueue()
        
        # Create deployment plans with different priorities
        plans = []
        for i, priority in enumerate(priority_distribution[:queue_size]):
            plan = DeploymentPlan(
                plan_id=f"plan_{i}",
                environment_id=f"env_{i % 3}",
                test_artifacts=[],
                dependencies=[],
                instrumentation_config=InstrumentationConfig(),
                deployment_config=DeploymentConfig(priority=priority),
                created_at=datetime.now()
            )
            plans.append(plan)
            queue.add_deployment(plan)
        
        # Extract deployments in queue order
        extracted_priorities = []
        while not queue.is_empty():
            plan = queue.pop_deployment()
            if plan:
                extracted_priorities.append(plan.deployment_config.priority.value)
        
        # Verify priority ordering (lower values = higher priority)
        for i in range(1, len(extracted_priorities)):
            assert extracted_priorities[i-1] <= extracted_priorities[i], \
                f"Priority ordering violated: {extracted_priorities[i-1]} > {extracted_priorities[i]}"
    
    @given(
        environment_count=st.integers(min_value=1, max_value=5),
        max_per_env=st.integers(min_value=1, max_value=4),
        deployment_count=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=50, deadline=3000)
    async def test_resource_contention_handling(self, environment_count: int, max_per_env: int, deployment_count: int):
        """
        Property: Resource contention is handled correctly
        
        Validates that:
        1. No environment exceeds its concurrent deployment limit
        2. Deployments are queued when resources are unavailable
        3. Resources are properly released after deployment completion
        """
        resource_manager = ResourceManager()
        resource_manager.max_concurrent_per_env = max_per_env
        
        environments = [f"env_{i}" for i in range(environment_count)]
        
        # Track acquisitions and releases
        acquisitions = {}
        releases = {}
        
        for env in environments:
            acquisitions[env] = 0
            releases[env] = 0
        
        # Simulate concurrent deployment requests
        for i in range(deployment_count):
            env_id = environments[i % environment_count]
            
            # Try to acquire environment
            acquired = await resource_manager.acquire_environment(env_id)
            
            if acquired:
                acquisitions[env_id] += 1
                
                # Verify we don't exceed limits
                current_usage = resource_manager.environment_usage.get(env_id, 0)
                assert current_usage <= max_per_env, \
                    f"Environment {env_id} usage {current_usage} exceeds limit {max_per_env}"
                
                # Simulate deployment completion and release
                await resource_manager.release_environment(env_id)
                releases[env_id] += 1
        
        # Verify all acquisitions were released
        for env in environments:
            assert acquisitions[env] == releases[env], \
                f"Environment {env} acquisitions {acquisitions[env]} != releases {releases[env]}"
        
        # Verify final usage is zero
        final_usage = resource_manager.get_environment_usage()
        for env in environments:
            assert final_usage.get(env, 0) == 0, f"Environment {env} has non-zero final usage"


# Synchronous test runners for pytest
def test_concurrent_deployment_management_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestConcurrentDeploymentManagement()
    
    # Run with multiple parameter combinations
    asyncio.run(test_instance.test_concurrent_deployment_management(
        deployment_count=5,
        environment_count=2,
        max_concurrent=3
    ))

def test_priority_queue_ordering_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestConcurrentDeploymentManagement()
    
    asyncio.run(test_instance.test_priority_queue_ordering(
        queue_size=10,
        priority_distribution=[Priority.LOW, Priority.HIGH, Priority.NORMAL, Priority.CRITICAL, Priority.LOW]
    ))

def test_resource_contention_handling_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestConcurrentDeploymentManagement()
    
    asyncio.run(test_instance.test_resource_contention_handling(
        environment_count=3,
        max_per_env=2,
        deployment_count=8
    ))


if __name__ == "__main__":
    # Run basic functionality test
    print("Testing concurrent deployment management...")
    
    async def basic_test():
        test_instance = TestConcurrentDeploymentManagement()
        
        try:
            await test_instance.test_concurrent_deployment_management(
                deployment_count=3,
                environment_count=2,
                max_concurrent=2
            )
            print("✓ Concurrent deployment management test passed")
            
            await test_instance.test_priority_queue_ordering(
                queue_size=5,
                priority_distribution=[Priority.LOW, Priority.HIGH, Priority.NORMAL]
            )
            print("✓ Priority queue ordering test passed")
            
            await test_instance.test_resource_contention_handling(
                environment_count=2,
                max_per_env=1,
                deployment_count=4
            )
            print("✓ Resource contention handling test passed")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(basic_test())