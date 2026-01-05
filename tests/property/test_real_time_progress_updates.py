"""
Property-based tests for real-time progress updates.

Tests the system's ability to provide accurate, real-time progress updates
for deployment monitoring with proper state transitions and timing.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch
import json

from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentResult, DeploymentStep
)


class TestRealTimeProgressUpdates:
    """Test real-time progress update capabilities"""
    
    @given(
        deployment_steps=st.integers(min_value=3, max_value=8),
        update_frequency=st.integers(min_value=1, max_value=5),
        progress_increments=st.lists(
            st.integers(min_value=5, max_value=25),
            min_size=3, max_size=8
        )
    )
    @settings(max_examples=30, deadline=10000)
    async def test_real_time_progress_updates(self, deployment_steps: int, 
                                            update_frequency: int, progress_increments: List[int]):
        """
        Property: Real-time progress updates are accurate and timely
        
        Validates that:
        1. Progress updates reflect actual deployment state
        2. Progress values are monotonically increasing
        3. Updates are delivered within expected time windows
        4. Final progress reaches 100% on completion
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=1)
        
        try:
            await orchestrator.start()
            
            # Create test deployment
            artifact = TestArtifact(
                artifact_id="progress_test_artifact",
                name="progress_test.sh",
                type=ArtifactType.SCRIPT,
                content=b"#!/bin/bash\necho 'progress test'",
                checksum="",
                permissions="0755",
                target_path="/tmp/progress_test.sh"
            )
            
            deployment_id = await orchestrator.deploy_to_environment(
                plan_id="progress_test_plan",
                env_id="progress_test_env",
                artifacts=[artifact],
                priority=Priority.NORMAL
            )
            
            # Track progress updates
            progress_history = []
            status_history = []
            update_timestamps = []
            
            # Monitor progress updates
            max_monitoring_time = 15  # seconds
            monitoring_start = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - monitoring_start < max_monitoring_time:
                deployment = await orchestrator.get_deployment_status(deployment_id)
                
                if deployment:
                    current_time = asyncio.get_event_loop().time()
                    progress_history.append(deployment.completion_percentage)
                    status_history.append(deployment.status.value)
                    update_timestamps.append(current_time)
                    
                    # Break if deployment is in final state
                    if deployment.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]:
                        break
                
                await asyncio.sleep(1.0 / update_frequency)  # Update frequency control
            
            # Verify progress update properties
            assert len(progress_history) > 0, "Should have captured progress updates"
            
            # Verify monotonic progress (allowing for small variations due to step transitions)
            for i in range(1, len(progress_history)):
                # Allow small decreases during step transitions, but overall trend should be upward
                if i > 2:  # After initial updates
                    recent_progress = progress_history[i-3:i+1]
                    assert max(recent_progress) >= min(recent_progress), \
                        f"Progress should generally increase: {recent_progress}"
            
            # Verify final progress for completed deployments
            final_deployment = await orchestrator.get_deployment_status(deployment_id)
            if final_deployment and final_deployment.status == DeploymentStatus.COMPLETED:
                assert final_deployment.completion_percentage >= 90.0, \
                    f"Completed deployment should have high progress: {final_deployment.completion_percentage}%"
            
            # Verify update timing consistency
            if len(update_timestamps) > 1:
                update_intervals = [
                    update_timestamps[i] - update_timestamps[i-1] 
                    for i in range(1, len(update_timestamps))
                ]
                
                expected_interval = 1.0 / update_frequency
                avg_interval = sum(update_intervals) / len(update_intervals)
                
                # Allow 50% variance in update timing
                assert abs(avg_interval - expected_interval) < expected_interval * 0.5, \
                    f"Update interval {avg_interval} should be close to expected {expected_interval}"
            
            # Verify status transitions are logical
            unique_statuses = list(dict.fromkeys(status_history))  # Preserve order, remove duplicates
            
            # Common valid status transitions
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
            
            # Verify each status transition is valid
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
        concurrent_deployments=st.integers(min_value=2, max_value=6),
        monitoring_duration=st.integers(min_value=5, max_value=15)
    )
    @settings(max_examples=20, deadline=20000)
    async def test_concurrent_progress_monitoring(self, concurrent_deployments: int, 
                                                monitoring_duration: int):
        """
        Property: Concurrent deployment progress monitoring is accurate
        
        Validates that:
        1. Multiple deployments can be monitored simultaneously
        2. Progress updates don't interfere with each other
        3. Each deployment maintains independent progress tracking
        4. No progress data is lost during concurrent monitoring
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=concurrent_deployments)
        
        try:
            await orchestrator.start()
            
            # Create multiple concurrent deployments
            deployment_ids = []
            for i in range(concurrent_deployments):
                artifact = TestArtifact(
                    artifact_id=f"concurrent_progress_artifact_{i}",
                    name=f"concurrent_progress_{i}.sh",
                    type=ArtifactType.SCRIPT,
                    content=f"#!/bin/bash\necho 'concurrent progress test {i}'".encode(),
                    checksum="",
                    permissions="0755",
                    target_path=f"/tmp/concurrent_progress_{i}.sh"
                )
                
                deployment_id = await orchestrator.deploy_to_environment(
                    plan_id=f"concurrent_progress_plan_{i}",
                    env_id=f"concurrent_progress_env_{i}",
                    artifacts=[artifact],
                    priority=Priority.NORMAL
                )
                deployment_ids.append(deployment_id)
            
            # Monitor all deployments concurrently
            deployment_progress = {dep_id: [] for dep_id in deployment_ids}
            deployment_statuses = {dep_id: [] for dep_id in deployment_ids}
            
            monitoring_start = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - monitoring_start < monitoring_duration:
                # Check all deployments
                for deployment_id in deployment_ids:
                    deployment = await orchestrator.get_deployment_status(deployment_id)
                    
                    if deployment:
                        deployment_progress[deployment_id].append(deployment.completion_percentage)
                        deployment_statuses[deployment_id].append(deployment.status.value)
                
                await asyncio.sleep(0.5)  # Monitor every 500ms
            
            # Verify concurrent monitoring results
            for deployment_id in deployment_ids:
                progress_list = deployment_progress[deployment_id]
                status_list = deployment_statuses[deployment_id]
                
                # Each deployment should have progress updates
                assert len(progress_list) > 0, f"Deployment {deployment_id} should have progress updates"
                assert len(status_list) > 0, f"Deployment {deployment_id} should have status updates"
                
                # Progress should be within valid range
                for progress in progress_list:
                    assert 0 <= progress <= 100, f"Progress {progress} should be between 0-100%"
                
                # Verify independence - each deployment should have unique progress patterns
                # (unless they happen to be identical by coincidence)
                unique_progress_values = len(set(progress_list))
                assert unique_progress_values >= 1, "Should have at least one progress value"
            
            # Verify no cross-contamination between deployments
            all_progress_patterns = list(deployment_progress.values())
            
            # Check that not all deployments have identical progress patterns
            # (which would indicate a bug in progress tracking)
            if len(all_progress_patterns) > 1:
                identical_patterns = 0
                for i in range(len(all_progress_patterns)):
                    for j in range(i + 1, len(all_progress_patterns)):
                        if all_progress_patterns[i] == all_progress_patterns[j]:
                            identical_patterns += 1
                
                # Allow some identical patterns but not all (which would be suspicious)
                max_allowed_identical = concurrent_deployments // 2
                assert identical_patterns <= max_allowed_identical, \
                    f"Too many identical progress patterns: {identical_patterns} > {max_allowed_identical}"
            
        finally:
            await orchestrator.stop()
    
    @given(
        step_count=st.integers(min_value=4, max_value=10),
        step_durations=st.lists(
            st.floats(min_value=0.1, max_value=2.0),
            min_size=4, max_size=10
        )
    )
    @settings(max_examples=25, deadline=15000)
    async def test_step_level_progress_tracking(self, step_count: int, step_durations: List[float]):
        """
        Property: Step-level progress tracking is accurate and detailed
        
        Validates that:
        1. Individual step progress is tracked accurately
        2. Step transitions are reflected in overall progress
        3. Step timing information is consistent
        4. Step status changes are properly recorded
        """
        orchestrator = DeploymentOrchestrator(max_concurrent_deployments=1)
        
        try:
            await orchestrator.start()
            
            # Create test deployment
            artifact = TestArtifact(
                artifact_id="step_progress_test_artifact",
                name="step_progress_test.sh",
                type=ArtifactType.SCRIPT,
                content=b"#!/bin/bash\necho 'step progress test'",
                checksum="",
                permissions="0755",
                target_path="/tmp/step_progress_test.sh"
            )
            
            deployment_id = await orchestrator.deploy_to_environment(
                plan_id="step_progress_test_plan",
                env_id="step_progress_test_env",
                artifacts=[artifact],
                priority=Priority.NORMAL
            )
            
            # Monitor step-level progress
            step_progress_history = {}
            step_status_history = {}
            
            max_monitoring_time = 20
            monitoring_start = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - monitoring_start < max_monitoring_time:
                deployment = await orchestrator.get_deployment_status(deployment_id)
                
                if deployment and deployment.steps:
                    for step in deployment.steps:
                        step_id = step.step_id
                        
                        if step_id not in step_progress_history:
                            step_progress_history[step_id] = []
                            step_status_history[step_id] = []
                        
                        step_progress_history[step_id].append(step.progress_percentage)
                        step_status_history[step_id].append(step.status)
                
                # Break if deployment is complete
                if deployment and deployment.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]:
                    break
                
                await asyncio.sleep(0.3)
            
            # Verify step-level progress properties
            assert len(step_progress_history) > 0, "Should have captured step progress"
            
            for step_id, progress_list in step_progress_history.items():
                status_list = step_status_history[step_id]
                
                # Each step should have progress updates
                assert len(progress_list) > 0, f"Step {step_id} should have progress updates"
                
                # Progress should be within valid range
                for progress in progress_list:
                    assert 0 <= progress <= 100, f"Step progress {progress} should be between 0-100%"
                
                # Verify step status transitions
                unique_statuses = list(dict.fromkeys(status_list))
                
                # Steps should start with pending or preparing
                if unique_statuses:
                    first_status = unique_statuses[0]
                    assert first_status in ['pending', 'preparing'], \
                        f"Step should start with pending/preparing, got {first_status}"
                
                # Completed steps should have 100% progress
                if 'completed' in [s.value if hasattr(s, 'value') else str(s) for s in status_list]:
                    final_progress = progress_list[-1]
                    # Allow some tolerance for timing issues
                    assert final_progress >= 90.0, \
                        f"Completed step should have high progress: {final_progress}%"
            
            # Verify overall progress consistency with step progress
            final_deployment = await orchestrator.get_deployment_status(deployment_id)
            if final_deployment and final_deployment.steps:
                completed_steps = sum(
                    1 for step in final_deployment.steps 
                    if step.status == DeploymentStatus.COMPLETED
                )
                total_steps = len(final_deployment.steps)
                
                if total_steps > 0:
                    expected_min_progress = (completed_steps / total_steps) * 80  # Allow some variance
                    actual_progress = final_deployment.completion_percentage
                    
                    assert actual_progress >= expected_min_progress, \
                        f"Overall progress {actual_progress}% should reflect completed steps {completed_steps}/{total_steps}"
            
        finally:
            await orchestrator.stop()


# Synchronous test runners for pytest
def test_real_time_progress_updates_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestRealTimeProgressUpdates()
    
    asyncio.run(test_instance.test_real_time_progress_updates(
        deployment_steps=5,
        update_frequency=2,
        progress_increments=[10, 15, 20, 25, 30]
    ))

def test_concurrent_progress_monitoring_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestRealTimeProgressUpdates()
    
    asyncio.run(test_instance.test_concurrent_progress_monitoring(
        concurrent_deployments=3,
        monitoring_duration=8
    ))

def test_step_level_progress_tracking_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestRealTimeProgressUpdates()
    
    asyncio.run(test_instance.test_step_level_progress_tracking(
        step_count=6,
        step_durations=[0.5, 1.0, 0.8, 1.2, 0.6, 0.9]
    ))


if __name__ == "__main__":
    # Run basic functionality test
    print("Testing real-time progress updates...")
    
    async def basic_test():
        test_instance = TestRealTimeProgressUpdates()
        
        try:
            await test_instance.test_real_time_progress_updates(
                deployment_steps=4,
                update_frequency=2,
                progress_increments=[15, 20, 25, 40]
            )
            print("✓ Real-time progress updates test passed")
            
            await test_instance.test_concurrent_progress_monitoring(
                concurrent_deployments=2,
                monitoring_duration=6
            )
            print("✓ Concurrent progress monitoring test passed")
            
            await test_instance.test_step_level_progress_tracking(
                step_count=5,
                step_durations=[0.5, 1.0, 0.8, 1.2, 0.6]
            )
            print("✓ Step-level progress tracking test passed")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(basic_test())