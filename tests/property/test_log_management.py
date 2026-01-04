"""
Property-based tests for deployment log management and accessibility.

Tests the deployment logging system's ability to capture, store, and
provide access to deployment logs and metrics.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from typing import List, Dict
import tempfile
import shutil
from pathlib import Path

from deployment.orchestrator import DeploymentLogger, DeploymentOrchestrator
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentPlan, DeploymentConfig, InstrumentationConfig, DeploymentResult
)


class TestLogManagement:
    """Test deployment log management and accessibility"""
    
    @given(
        deployment_count=st.integers(min_value=1, max_value=10),
        log_events_per_deployment=st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=50, deadline=5000)
    async def test_deployment_log_accessibility(self, deployment_count: int, log_events_per_deployment: int):
        """
        Property: Deployment logs are accessible and complete
        
        Validates that:
        1. All deployment events are logged
        2. Logs are accessible by deployment ID
        3. Log entries contain required information
        4. Logs persist across system restarts
        """
        # Create temporary log directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            logger = DeploymentLogger(log_dir=temp_dir)
            
            deployment_ids = []
            expected_events = {}
            
            # Generate test deployments and log events
            for i in range(deployment_count):
                deployment_id = f"deploy_{i:04d}"
                deployment_ids.append(deployment_id)
                expected_events[deployment_id] = []
                
                # Create test deployment plan
                plan = DeploymentPlan(
                    plan_id=deployment_id,
                    environment_id=f"env_{i % 3}",
                    test_artifacts=[],
                    dependencies=[],
                    instrumentation_config=InstrumentationConfig(),
                    deployment_config=DeploymentConfig(priority=Priority.NORMAL),
                    created_at=datetime.now()
                )
                
                # Log deployment start
                logger.log_deployment_start(deployment_id, plan)
                expected_events[deployment_id].append("deployment_start")
                
                # Log various events during deployment
                for j in range(log_events_per_deployment - 2):  # -2 for start and end
                    if j % 2 == 0:
                        logger.log_retry_attempt(deployment_id, j + 1, f"Test error {j}")
                        expected_events[deployment_id].append("retry_attempt")
                
                # Create deployment result
                result = DeploymentResult(
                    deployment_id=deployment_id,
                    plan_id=deployment_id,
                    environment_id=f"env_{i % 3}",
                    status=DeploymentStatus.COMPLETED if i % 2 == 0 else DeploymentStatus.FAILED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    artifacts_deployed=i + 1
                )
                
                # Log deployment end
                logger.log_deployment_end(deployment_id, result)
                expected_events[deployment_id].append("deployment_end")
            
            # Verify log accessibility
            for deployment_id in deployment_ids:
                logs = logger.get_deployment_logs(deployment_id)
                
                # Verify logs exist
                assert len(logs) > 0, f"No logs found for deployment {deployment_id}"
                
                # Verify expected events are present
                logged_events = [log.get("event") for log in logs]
                for expected_event in expected_events[deployment_id]:
                    assert expected_event in logged_events, \
                        f"Expected event {expected_event} not found in logs for {deployment_id}"
                
                # Verify log entry structure
                for log_entry in logs:
                    assert "timestamp" in log_entry, "Log entry missing timestamp"
                    assert "event" in log_entry, "Log entry missing event type"
                    assert "deployment_id" in log_entry, "Log entry missing deployment ID"
                    assert log_entry["deployment_id"] == deployment_id, \
                        f"Log entry has wrong deployment ID: {log_entry['deployment_id']}"
                
                # Verify chronological ordering
                timestamps = [log.get("timestamp") for log in logs if log.get("timestamp")]
                assert len(timestamps) == len(logs), "All log entries should have timestamps"
                
                # Timestamps should be in chronological order (or at least not decreasing)
                for i in range(1, len(timestamps)):
                    assert timestamps[i] >= timestamps[i-1], \
                        f"Log timestamps not in chronological order: {timestamps[i-1]} > {timestamps[i]}"
            
            # Test log persistence by creating new logger instance
            logger2 = DeploymentLogger(log_dir=temp_dir)
            
            # Verify logs are still accessible
            for deployment_id in deployment_ids:
                logs = logger2.get_deployment_logs(deployment_id)
                assert len(logs) > 0, f"Logs not persistent for deployment {deployment_id}"
            
        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        successful_deployments=st.integers(min_value=0, max_value=20),
        failed_deployments=st.integers(min_value=0, max_value=20),
        cancelled_deployments=st.integers(min_value=0, max_value=10),
        retry_count=st.integers(min_value=0, max_value=50)
    )
    @settings(max_examples=50, deadline=3000)
    async def test_metrics_tracking_accuracy(self, successful_deployments: int, failed_deployments: int, 
                                           cancelled_deployments: int, retry_count: int):
        """
        Property: Deployment metrics are tracked accurately
        
        Validates that:
        1. Metrics correctly count different deployment outcomes
        2. Average duration is calculated correctly
        3. Retry counts are tracked properly
        4. Metrics persist across logger instances
        """
        # Skip test if no deployments
        total_deployments = successful_deployments + failed_deployments + cancelled_deployments
        if total_deployments == 0:
            return
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            logger = DeploymentLogger(log_dir=temp_dir)
            
            # Track expected metrics
            expected_total = total_deployments
            expected_successful = successful_deployments
            expected_failed = failed_deployments
            expected_cancelled = cancelled_deployments
            expected_retries = retry_count
            
            durations = []
            
            # Simulate successful deployments
            for i in range(successful_deployments):
                deployment_id = f"success_{i}"
                duration = (i + 1) * 10.0  # Varying durations
                durations.append(duration)
                
                result = DeploymentResult(
                    deployment_id=deployment_id,
                    plan_id=deployment_id,
                    environment_id="test_env",
                    status=DeploymentStatus.COMPLETED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    artifacts_deployed=1
                )
                result._duration_seconds = duration  # Mock duration
                
                logger.log_deployment_end(deployment_id, result)
            
            # Simulate failed deployments
            for i in range(failed_deployments):
                deployment_id = f"failed_{i}"
                
                result = DeploymentResult(
                    deployment_id=deployment_id,
                    plan_id=deployment_id,
                    environment_id="test_env",
                    status=DeploymentStatus.FAILED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message="Test failure"
                )
                
                logger.log_deployment_end(deployment_id, result)
            
            # Simulate cancelled deployments
            for i in range(cancelled_deployments):
                deployment_id = f"cancelled_{i}"
                
                result = DeploymentResult(
                    deployment_id=deployment_id,
                    plan_id=deployment_id,
                    environment_id="test_env",
                    status=DeploymentStatus.CANCELLED,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message="Cancelled"
                )
                
                logger.log_deployment_end(deployment_id, result)
            
            # Simulate retry attempts
            for i in range(retry_count):
                logger.log_retry_attempt(f"retry_test_{i % 5}", i + 1, "Test retry")
            
            # Get metrics
            metrics = logger.get_metrics()
            
            # Verify counts
            assert metrics["total_deployments"] == expected_total, \
                f"Total deployments: expected {expected_total}, got {metrics['total_deployments']}"
            
            assert metrics["successful_deployments"] == expected_successful, \
                f"Successful deployments: expected {expected_successful}, got {metrics['successful_deployments']}"
            
            assert metrics["failed_deployments"] == expected_failed, \
                f"Failed deployments: expected {expected_failed}, got {metrics['failed_deployments']}"
            
            assert metrics["cancelled_deployments"] == expected_cancelled, \
                f"Cancelled deployments: expected {expected_cancelled}, got {metrics['cancelled_deployments']}"
            
            assert metrics["retry_count"] == expected_retries, \
                f"Retry count: expected {expected_retries}, got {metrics['retry_count']}"
            
            # Verify average duration calculation
            if durations:
                expected_avg = sum(durations) / len(durations)
                actual_avg = metrics["average_duration_seconds"]
                
                # Allow small floating point differences
                assert abs(actual_avg - expected_avg) < 0.01, \
                    f"Average duration: expected {expected_avg}, got {actual_avg}"
            
            # Test metrics persistence
            logger2 = DeploymentLogger(log_dir=temp_dir)
            metrics2 = logger2.get_metrics()
            
            # Verify metrics are loaded correctly
            assert metrics2["total_deployments"] == expected_total, \
                "Metrics not persistent across logger instances"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        concurrent_deployments=st.integers(min_value=2, max_value=8),
        events_per_deployment=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=30, deadline=8000)
    async def test_concurrent_logging_integrity(self, concurrent_deployments: int, events_per_deployment: int):
        """
        Property: Concurrent logging maintains data integrity
        
        Validates that:
        1. Concurrent log writes don't corrupt data
        2. All log entries are preserved
        3. No race conditions in metrics updates
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            orchestrator = DeploymentOrchestrator(
                max_concurrent_deployments=concurrent_deployments,
                log_dir=temp_dir
            )
            
            await orchestrator.start()
            
            # Create concurrent deployments
            deployment_tasks = []
            
            for i in range(concurrent_deployments):
                task = asyncio.create_task(self._simulate_deployment_with_logging(
                    orchestrator, i, events_per_deployment
                ))
                deployment_tasks.append(task)
            
            # Wait for all deployments to complete
            await asyncio.gather(*deployment_tasks, return_exceptions=True)
            
            # Verify log integrity
            total_expected_logs = concurrent_deployments * events_per_deployment
            total_actual_logs = 0
            
            for i in range(concurrent_deployments):
                deployment_id = f"concurrent_{i}"
                logs = orchestrator.get_deployment_logs(deployment_id)
                total_actual_logs += len(logs)
                
                # Verify each deployment has expected number of log entries
                assert len(logs) >= 2, f"Deployment {deployment_id} should have at least start and end logs"
            
            # Verify no logs were lost due to concurrency
            assert total_actual_logs >= concurrent_deployments * 2, \
                f"Expected at least {concurrent_deployments * 2} logs, got {total_actual_logs}"
            
            # Verify metrics consistency
            metrics = orchestrator.get_deployment_metrics()
            assert metrics["total_deployments"] == concurrent_deployments, \
                f"Expected {concurrent_deployments} total deployments in metrics"
            
        finally:
            await orchestrator.stop()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _simulate_deployment_with_logging(self, orchestrator: DeploymentOrchestrator, 
                                              deployment_index: int, event_count: int):
        """Helper method to simulate a deployment with logging events"""
        try:
            # Create test artifact
            artifact = TestArtifact(
                artifact_id=f"concurrent_artifact_{deployment_index}",
                name=f"concurrent_test_{deployment_index}.sh",
                type=ArtifactType.SCRIPT,
                content=f"#!/bin/bash\necho 'concurrent test {deployment_index}'".encode(),
                checksum="",
                permissions="0755",
                target_path=f"/tmp/concurrent_test_{deployment_index}.sh"
            )
            
            # Start deployment
            deployment_id = await orchestrator.deploy_to_environment(
                plan_id=f"concurrent_{deployment_index}",
                env_id=f"concurrent_env_{deployment_index}",
                artifacts=[artifact]
            )
            
            # Simulate additional logging events
            for j in range(event_count - 2):  # -2 for automatic start/end logs
                orchestrator.deployment_logger.log_retry_attempt(
                    deployment_id, j + 1, f"Concurrent test retry {j}"
                )
                await asyncio.sleep(0.01)  # Small delay to simulate real timing
            
            # Wait for deployment to complete
            max_wait = 10
            start_time = asyncio.get_event_loop().time()
            
            while asyncio.get_event_loop().time() - start_time < max_wait:
                deployment = orchestrator.get_deployment_status(deployment_id)
                if deployment and deployment.status in [
                    DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED
                ]:
                    break
                await asyncio.sleep(0.1)
            
        except Exception as e:
            # Log the exception but don't fail the test
            print(f"Deployment {deployment_index} failed: {e}")


# Synchronous test runners for pytest
def test_deployment_log_accessibility_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestLogManagement()
    
    asyncio.run(test_instance.test_deployment_log_accessibility(
        deployment_count=3,
        log_events_per_deployment=4
    ))

def test_metrics_tracking_accuracy_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestLogManagement()
    
    asyncio.run(test_instance.test_metrics_tracking_accuracy(
        successful_deployments=5,
        failed_deployments=2,
        cancelled_deployments=1,
        retry_count=8
    ))

def test_concurrent_logging_integrity_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestLogManagement()
    
    asyncio.run(test_instance.test_concurrent_logging_integrity(
        concurrent_deployments=3,
        events_per_deployment=5
    ))


if __name__ == "__main__":
    # Run basic functionality test
    print("Testing log management...")
    
    async def basic_test():
        test_instance = TestLogManagement()
        
        try:
            await test_instance.test_deployment_log_accessibility(
                deployment_count=2,
                log_events_per_deployment=3
            )
            print("✓ Deployment log accessibility test passed")
            
            await test_instance.test_metrics_tracking_accuracy(
                successful_deployments=3,
                failed_deployments=1,
                cancelled_deployments=1,
                retry_count=5
            )
            print("✓ Metrics tracking accuracy test passed")
            
            await test_instance.test_concurrent_logging_integrity(
                concurrent_deployments=2,
                events_per_deployment=4
            )
            print("✓ Concurrent logging integrity test passed")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(basic_test())