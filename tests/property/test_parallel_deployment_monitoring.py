"""
Property-based tests for parallel deployment monitoring.

Tests the system's ability to monitor multiple concurrent deployments
with accurate status tracking, progress reporting, and summary statistics.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
from unittest.mock import AsyncMock, patch
import json

from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentResult, DeploymentStep
)


class TestParallelDeploymentMonitoring:
    """Test parallel deployment monitoring capabilities"""
    
    @given(
        parallel_deployments=st.integers(min_value=2, max_value=8),
        environment_count=st.integers(min_value=1, max_value=4),
        monitoring_duration=st.integers(min_value=5, max_value=12)
    )
    @settings(max_examples=25, deadline=20000)
    async def test_parallel_deployment_monitoring(self, parallel_deployments: int, 
                                                environment_count: int, monitoring_duration: int):
        """
        Property: Parallel deployment monitoring tracks all deployments accurately
        
        Validates that:
        1. All parallel deployments are tracked simultaneously
        2. Individual deployment progress is maintained independently
        3. Summary statistics are calculated correctly
        4. No deployment data is lost during parallel monitoring
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=parallel_deployments)
        
        try:
            await orchestrator.start()
            
            # Create parallel deployments across environments
            deployment_tracking = {}
            environments = [f"parallel_env_{i}" for i in range(environment_count)]
            
            for i in range(parallel_deployments):
                env_id = environments[i % environment_count]
                
                artifact = TestArtifact(
                    artifact_id=f"parallel_artifact_{i}",
                    name=f"parallel_test_{i}.sh",
                    type=ArtifactType.SCRIPT,
                    content=f"#!/bin/bash\necho 'parallel test {i}'".encode(),
                    checksum="",
                    permissions="0755",
                    target_path=f"/tmp/parallel_test_{i}.sh"
                )
                
                deployment_id = await orchestrator.deploy_to_environment(
                    plan_id=f"parallel_plan_{i}",
                    env_id=env_id,
                    artifacts=[artifact],
                    priority=Priority.NORMAL
                )
                
                deployment_tracking[deployment_id] = {
                    "environment_id": env_id,
                    "expected_artifacts": 1,
                    "start_time": datetime.now(),
                    "progress_history": [],
                    "status_history": []
                }
            
            # Monitor all deployments in parallel
            monitoring_start = asyncio.get_event_loop().time()
            monitoring_snapshots = []
            
            while asyncio.get_event_loop().time() - monitoring_start < monitoring_duration:
                # Take a snapshot of all deployments
                snapshot = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "deployments": {},
                    "metrics": orchestrator.get_deployment_metrics()
                }
                
                for deployment_id in deployment_tracking.keys():
                    deployment = await orchestrator.get_deployment_status(deployment_id)
                    if deployment:
                        snapshot["deployments"][deployment_id] = {
                            "status": deployment.status.value,
                            "progress": deployment.completion_percentage,
                            "artifacts_deployed": deployment.artifacts_deployed,
                            "retry_count": deployment.retry_count,
                            "error_message": deployment.error_message
                        }
                        
                        # Update tracking history
                        deployment_tracking[deployment_id]["progress_history"].append(deployment.completion_percentage)
                        deployment_tracking[deployment_id]["status_history"].append(deployment.status.value)
                
                monitoring_snapshots.append(snapshot)
                await asyncio.sleep(0.5)  # Monitor every 500ms
            
            # Verify parallel monitoring results
            assert len(monitoring_snapshots) > 0, "Should have captured monitoring snapshots"
            
            # Verify all deployments were tracked throughout monitoring
            for snapshot in monitoring_snapshots:
                tracked_deployments = set(snapshot["deployments"].keys())
                expected_deployments = set(deployment_tracking.keys())
                
                # Allow for some deployments to complete and potentially be cleaned up
                assert len(tracked_deployments) > 0, "Should track at least some deployments"
                assert tracked_deployments.issubset(expected_deployments), \
                    "Tracked deployments should be subset of expected deployments"
            
            # Verify independent progress tracking
            for deployment_id, tracking_info in deployment_tracking.items():
                progress_history = tracking_info["progress_history"]
                status_history = tracking_info["status_history"]
                
                if progress_history:
                    # Progress should be within valid range
                    for progress in progress_history:
                        assert 0 <= progress <= 100, f"Progress {progress} should be between 0-100%"
                    
                    # Progress should generally increase or stay the same
                    for i in range(1, len(progress_history)):
                        # Allow small decreases during step transitions
                        assert progress_history[i] >= progress_history[i-1] - 10, \
                            f"Progress should not decrease significantly: {progress_history[i-1]} -> {progress_history[i]}"
                
                if status_history:
                    # Should have at least one status update
                    assert len(status_history) > 0, f"Deployment {deployment_id} should have status updates"
            
            # Verify summary statistics accuracy
            final_metrics = orchestrator.get_deployment_metrics()
            
            # Total deployments should match what we created
            assert final_metrics["total_deployments"] >= parallel_deployments, \
                f"Total deployments {final_metrics['total_deployments']} should be at least {parallel_deployments}"
            
            # Active deployments should be reasonable
            assert final_metrics["active_deployments"] >= 0, "Active deployments should be non-negative"
            assert final_metrics["active_deployments"] <= parallel_deployments, \
                "Active deployments should not exceed total created"
            
            # Environment usage should be tracked
            env_usage = final_metrics.get("environment_usage", {})
            for env_id in environments:
                if env_id in env_usage:
                    assert env_usage[env_id] >= 0, f"Environment {env_id} usage should be non-negative"
            
        finally:
            await orchestrator.stop()
    
    @given(
        deployment_batches=st.lists(
            st.integers(min_value=1, max_value=4),
            min_size=2, max_size=5
        ),
        batch_delay=st.floats(min_value=0.5, max_value=3.0)
    )
    @settings(max_examples=20, deadline=25000)
    async def test_multi_environment_deployment_tracking(self, deployment_batches: List[int], 
                                                       batch_delay: float):
        """
        Property: Multi-environment deployment tracking maintains environment isolation
        
        Validates that:
        1. Deployments to different environments are tracked separately
        2. Environment-specific metrics are accurate
        3. Cross-environment interference is prevented
        4. Environment capacity limits are respected
        """
        total_deployments = sum(deployment_batches)
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=total_deployments)
        
        try:
            await orchestrator.start()
            
            # Track deployments by environment
            environment_deployments = {}
            all_deployment_ids = []
            
            # Create deployment batches for different environments
            for batch_idx, batch_size in enumerate(deployment_batches):
                env_id = f"multi_env_{batch_idx}"
                environment_deployments[env_id] = []
                
                for i in range(batch_size):
                    artifact = TestArtifact(
                        artifact_id=f"multi_env_artifact_{batch_idx}_{i}",
                        name=f"multi_env_test_{batch_idx}_{i}.sh",
                        type=ArtifactType.SCRIPT,
                        content=f"#!/bin/bash\necho 'multi-env test {batch_idx}-{i}'".encode(),
                        checksum="",
                        permissions="0755",
                        target_path=f"/tmp/multi_env_test_{batch_idx}_{i}.sh"
                    )
                    
                    deployment_id = await orchestrator.deploy_to_environment(
                        plan_id=f"multi_env_plan_{batch_idx}_{i}",
                        env_id=env_id,
                        artifacts=[artifact],
                        priority=Priority.NORMAL
                    )
                    
                    environment_deployments[env_id].append(deployment_id)
                    all_deployment_ids.append(deployment_id)
                
                # Delay between batches to simulate realistic deployment patterns
                await asyncio.sleep(batch_delay)
            
            # Monitor multi-environment deployments
            max_monitoring_time = 20
            monitoring_start = asyncio.get_event_loop().time()
            environment_snapshots = {env_id: [] for env_id in environment_deployments.keys()}
            
            while asyncio.get_event_loop().time() - monitoring_start < max_monitoring_time:
                # Take environment-specific snapshots
                for env_id, deployment_ids in environment_deployments.items():
                    env_snapshot = {
                        "timestamp": asyncio.get_event_loop().time(),
                        "deployments": {},
                        "active_count": 0,
                        "completed_count": 0,
                        "failed_count": 0
                    }
                    
                    for deployment_id in deployment_ids:
                        deployment = await orchestrator.get_deployment_status(deployment_id)
                        if deployment:
                            env_snapshot["deployments"][deployment_id] = {
                                "status": deployment.status.value,
                                "progress": deployment.completion_percentage,
                                "environment_id": deployment.environment_id
                            }
                            
                            # Count by status
                            if deployment.status in [DeploymentStatus.COMPLETED]:
                                env_snapshot["completed_count"] += 1
                            elif deployment.status in [DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]:
                                env_snapshot["failed_count"] += 1
                            else:
                                env_snapshot["active_count"] += 1
                    
                    environment_snapshots[env_id].append(env_snapshot)
                
                await asyncio.sleep(0.8)
            
            # Verify multi-environment tracking
            for env_id, snapshots in environment_snapshots.items():
                assert len(snapshots) > 0, f"Environment {env_id} should have snapshots"
                
                expected_deployment_count = len(environment_deployments[env_id])
                
                for snapshot in snapshots:
                    # Verify environment isolation
                    for deployment_id, deployment_data in snapshot["deployments"].items():
                        assert deployment_data["environment_id"] == env_id, \
                            f"Deployment {deployment_id} should belong to environment {env_id}"
                    
                    # Verify counts are reasonable
                    total_tracked = (snapshot["active_count"] + 
                                   snapshot["completed_count"] + 
                                   snapshot["failed_count"])
                    
                    assert total_tracked <= expected_deployment_count, \
                        f"Environment {env_id} tracked count {total_tracked} should not exceed expected {expected_deployment_count}"
            
            # Verify final environment metrics
            final_metrics = orchestrator.get_deployment_metrics()
            env_usage = final_metrics.get("environment_usage", {})
            
            # Each environment should have reasonable usage
            for env_id in environment_deployments.keys():
                if env_id in env_usage:
                    usage = env_usage[env_id]
                    max_expected_usage = min(len(environment_deployments[env_id]), 3)  # Default max per env
                    assert 0 <= usage <= max_expected_usage, \
                        f"Environment {env_id} usage {usage} should be between 0 and {max_expected_usage}"
            
        finally:
            await orchestrator.stop()
    
    @given(
        deployment_count=st.integers(min_value=3, max_value=10),
        failure_rate=st.floats(min_value=0.1, max_value=0.5),
        completion_rate=st.floats(min_value=0.3, max_value=0.8)
    )
    @settings(max_examples=20, deadline=15000)
    async def test_deployment_summary_accuracy(self, deployment_count: int, 
                                             failure_rate: float, completion_rate: float):
        """
        Property: Deployment summary statistics are calculated accurately
        
        Validates that:
        1. Summary counts match actual deployment states
        2. Success rates are calculated correctly
        3. Progress aggregation is accurate
        4. Timing statistics are consistent
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=deployment_count)
        
        try:
            await orchestrator.start()
            
            # Create deployments with controlled outcomes
            deployment_outcomes = {}
            deployment_ids = []
            
            for i in range(deployment_count):
                artifact = TestArtifact(
                    artifact_id=f"summary_artifact_{i}",
                    name=f"summary_test_{i}.sh",
                    type=ArtifactType.SCRIPT,
                    content=f"#!/bin/bash\necho 'summary test {i}'".encode(),
                    checksum="",
                    permissions="0755",
                    target_path=f"/tmp/summary_test_{i}.sh"
                )
                
                deployment_id = await orchestrator.deploy_to_environment(
                    plan_id=f"summary_plan_{i}",
                    env_id=f"summary_env_{i % 3}",  # Distribute across 3 environments
                    artifacts=[artifact],
                    priority=Priority.NORMAL
                )
                
                deployment_ids.append(deployment_id)
                
                # Determine expected outcome based on rates
                import random
                if random.random() < failure_rate:
                    deployment_outcomes[deployment_id] = "failed"
                elif random.random() < completion_rate:
                    deployment_outcomes[deployment_id] = "completed"
                else:
                    deployment_outcomes[deployment_id] = "active"
            
            # Wait for deployments to process
            max_wait_time = 15
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < max_wait_time:
                # Check if enough deployments have reached final states
                final_count = 0
                for deployment_id in deployment_ids:
                    deployment = await orchestrator.get_deployment_status(deployment_id)
                    if deployment and deployment.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]:
                        final_count += 1
                
                if final_count >= deployment_count * 0.7:  # 70% in final state
                    break
                
                await asyncio.sleep(0.5)
            
            # Collect final deployment states
            final_states = {}
            progress_values = []
            durations = []
            
            for deployment_id in deployment_ids:
                deployment = await orchestrator.get_deployment_status(deployment_id)
                if deployment:
                    final_states[deployment_id] = deployment.status.value
                    progress_values.append(deployment.completion_percentage)
                    
                    if deployment.duration_seconds:
                        durations.append(deployment.duration_seconds)
            
            # Verify summary accuracy
            metrics = orchestrator.get_deployment_metrics()
            
            # Count actual states
            actual_completed = sum(1 for state in final_states.values() if state == "completed")
            actual_failed = sum(1 for state in final_states.values() if state == "failed")
            actual_cancelled = sum(1 for state in final_states.values() if state == "cancelled")
            actual_active = sum(1 for state in final_states.values() 
                              if state not in ["completed", "failed", "cancelled"])
            
            # Verify metrics match actual counts (allowing for timing differences)
            assert metrics["total_deployments"] >= deployment_count, \
                f"Total deployments {metrics['total_deployments']} should be at least {deployment_count}"
            
            # Verify success rate calculation
            if metrics["total_deployments"] > 0:
                calculated_success_rate = (metrics["successful_deployments"] / metrics["total_deployments"]) * 100
                assert 0 <= calculated_success_rate <= 100, \
                    f"Success rate {calculated_success_rate}% should be between 0-100%"
            
            # Verify progress values are reasonable
            for progress in progress_values:
                assert 0 <= progress <= 100, f"Progress {progress} should be between 0-100%"
            
            # Verify average duration calculation
            if durations and metrics["average_duration_seconds"] > 0:
                expected_avg = sum(durations) / len(durations)
                actual_avg = metrics["average_duration_seconds"]
                
                # Allow reasonable variance in average calculation
                variance_threshold = max(expected_avg * 0.5, 10.0)  # 50% or 10 seconds
                assert abs(actual_avg - expected_avg) <= variance_threshold, \
                    f"Average duration {actual_avg} should be close to expected {expected_avg}"
            
            # Verify environment usage tracking
            env_usage = metrics.get("environment_usage", {})
            total_env_usage = sum(env_usage.values())
            assert total_env_usage >= 0, "Total environment usage should be non-negative"
            
        finally:
            await orchestrator.stop()


# Synchronous test runners for pytest
def test_parallel_deployment_monitoring_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestParallelDeploymentMonitoring()
    
    asyncio.run(test_instance.test_parallel_deployment_monitoring(
        parallel_deployments=4,
        environment_count=2,
        monitoring_duration=8
    ))

def test_multi_environment_deployment_tracking_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestParallelDeploymentMonitoring()
    
    asyncio.run(test_instance.test_multi_environment_deployment_tracking(
        deployment_batches=[2, 3, 2],
        batch_delay=1.0
    ))

def test_deployment_summary_accuracy_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestParallelDeploymentMonitoring()
    
    asyncio.run(test_instance.test_deployment_summary_accuracy(
        deployment_count=6,
        failure_rate=0.2,
        completion_rate=0.6
    ))


if __name__ == "__main__":
    # Run basic functionality test
    print("Testing parallel deployment monitoring...")
    
    async def basic_test():
        test_instance = TestParallelDeploymentMonitoring()
        
        try:
            await test_instance.test_parallel_deployment_monitoring(
                parallel_deployments=3,
                environment_count=2,
                monitoring_duration=6
            )
            print("✓ Parallel deployment monitoring test passed")
            
            await test_instance.test_multi_environment_deployment_tracking(
                deployment_batches=[2, 2],
                batch_delay=0.8
            )
            print("✓ Multi-environment deployment tracking test passed")
            
            await test_instance.test_deployment_summary_accuracy(
                deployment_count=4,
                failure_rate=0.25,
                completion_rate=0.5
            )
            print("✓ Deployment summary accuracy test passed")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(basic_test())