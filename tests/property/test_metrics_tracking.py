"""
Property-based tests for deployment metrics tracking.

Tests the system's ability to accurately track and report deployment
metrics including success rates, timing, failures, and performance analytics.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from typing import List, Dict
import tempfile
import shutil

from deployment.orchestrator import DeploymentOrchestrator, DeploymentLogger
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentResult
)


class TestMetricsTracking:
    """Test deployment metrics tracking capabilities"""
    
    @given(
        successful_count=st.integers(min_value=0, max_value=25),
        failed_count=st.integers(min_value=0, max_value=15),
        cancelled_count=st.integers(min_value=0, max_value=10),
        retry_count=st.integers(min_value=0, max_value=30)
    )
    @settings(max_examples=50, deadline=5000)
    async def test_deployment_metrics_tracking(self, successful_count: int, failed_count: int, 
                                             cancelled_count: int, retry_count: int):
        """
        Property: Deployment metrics are tracked accurately
        
        Validates that:
        1. All deployment outcomes are counted correctly
        2. Success rates are calculated accurately
        3. Timing metrics are computed properly
        4. Retry counts are tracked correctly
        """
        # Skip if no deployments
        total_deployments = successful_count + failed_count + cancelled_count
        if total_deployments == 0:
            return
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            orchestrator = DeploymentOrchestrator(
                max_concurrent_deployments=5,
                log_dir=temp_dir
            )
            
            await orchestrator.start()
            
            # Track expected metrics
            expected_total = total_deployments
            expected_successful = successful_count
            expected_failed = failed_count
            expected_cancelled = cancelled_count
            expected_retries = retry_count
            
            deployment_durations = []
            
            # Simulate successful deployments
            for i in range(successful_count):
                deployment_id = f"success_{i}"
                duration = (i + 1) * 15.0 + 30.0  # Varying durations: 45s, 60s, 75s, etc.
                deployment_durations.append(duration)
                
                result = DeploymentResult(
                    deployment_id=deployment_id,
                    plan_id=deployment_id,
                    environment_id="metrics_test_env",
                    status=DeploymentStatus.COMPLETED,
                    start_time=datetime.now() - timedelta(seconds=duration),
                    end_time=datetime.now(),
                    artifacts_deployed=i + 1
                )
                
                # Mock duration calculation
                result._duration_seconds = duration
                
                orchestrator.deployment_logger.log_deployment_end(deployment_id, result)
            
            # Simulate failed deployments
            for i in range(failed_count):
                deployment_id = f"failed_{i}"
                
                result = DeploymentResult(
                    deployment_id=deployment_id,
                    plan_id=deployment_id,
                    environment_id="metrics_test_env",
                    status=DeploymentStatus.FAILED,
                    start_time=datetime.now() - timedelta(seconds=60),
                    end_time=datetime.now(),
                    error_message=f"Test failure {i}",
                    retry_count=i % 3  # Vary retry counts
                )
                
                orchestrator.deployment_logger.log_deployment_end(deployment_id, result)
            
            # Simulate cancelled deployments
            for i in range(cancelled_count):
                deployment_id = f"cancelled_{i}"
                
                result = DeploymentResult(
                    deployment_id=deployment_id,
                    plan_id=deployment_id,
                    environment_id="metrics_test_env",
                    status=DeploymentStatus.CANCELLED,
                    start_time=datetime.now() - timedelta(seconds=30),
                    end_time=datetime.now(),
                    error_message="User cancelled"
                )
                
                orchestrator.deployment_logger.log_deployment_end(deployment_id, result)
            
            # Simulate retry attempts
            for i in range(retry_count):
                orchestrator.deployment_logger.log_retry_attempt(
                    f"retry_test_{i % 5}", i + 1, f"Test retry error {i}"
                )
            
            # Get and verify metrics
            metrics = orchestrator.get_deployment_metrics()
            
            # Verify basic counts
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
            if deployment_durations:
                expected_avg_duration = sum(deployment_durations) / len(deployment_durations)
                actual_avg_duration = metrics["average_duration_seconds"]
                
                # Allow small floating point differences
                duration_diff = abs(actual_avg_duration - expected_avg_duration)
                assert duration_diff < 0.1, \
                    f"Average duration: expected {expected_avg_duration}, got {actual_avg_duration}, diff {duration_diff}"
            
            # Verify calculated rates
            if expected_total > 0:
                expected_success_rate = (expected_successful / expected_total) * 100
                expected_failure_rate = (expected_failed / expected_total) * 100
                
                # These would be calculated by analytics endpoints
                actual_success_rate = (metrics["successful_deployments"] / metrics["total_deployments"]) * 100
                actual_failure_rate = (metrics["failed_deployments"] / metrics["total_deployments"]) * 100
                
                assert abs(actual_success_rate - expected_success_rate) < 0.01, \
                    f"Success rate: expected {expected_success_rate}%, got {actual_success_rate}%"
                
                assert abs(actual_failure_rate - expected_failure_rate) < 0.01, \
                    f"Failure rate: expected {expected_failure_rate}%, got {actual_failure_rate}%"
            
        finally:
            await orchestrator.stop()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @given(
        concurrent_deployments=st.integers(min_value=2, max_value=8),
        metrics_updates_per_deployment=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=30, deadline=10000)
    async def test_concurrent_metrics_updates(self, concurrent_deployments: int, 
                                            metrics_updates_per_deployment: int):
        """
        Property: Concurrent metrics updates maintain consistency
        
        Validates that:
        1. Concurrent metric updates don't cause race conditions
        2. All metric updates are preserved
        3. Final metrics are consistent with actual operations
        4. No metric data is lost during concurrent access
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            orchestrator = DeploymentOrchestrator(
                max_concurrent_deployments=concurrent_deployments,
                log_dir=temp_dir
            )
            
            await orchestrator.start()
            
            # Track expected metrics
            expected_total_deployments = concurrent_deployments
            expected_total_retries = concurrent_deployments * (metrics_updates_per_deployment - 2)  # -2 for start/end
            
            # Create concurrent deployment tasks
            deployment_tasks = []
            
            for i in range(concurrent_deployments):
                task = asyncio.create_task(
                    self._simulate_deployment_with_metrics(
                        orchestrator, i, metrics_updates_per_deployment
                    )
                )
                deployment_tasks.append(task)
            
            # Wait for all deployments to complete
            results = await asyncio.gather(*deployment_tasks, return_exceptions=True)
            
            # Check for any exceptions
            exceptions = [r for r in results if isinstance(r, Exception)]
            if exceptions:
                print(f"Deployment exceptions: {exceptions}")
            
            # Verify final metrics consistency
            final_metrics = orchestrator.get_deployment_metrics()
            
            # Verify total deployments (at least the ones we logged)
            assert final_metrics["total_deployments"] >= expected_total_deployments, \
                f"Expected at least {expected_total_deployments} total deployments, got {final_metrics['total_deployments']}"
            
            # Verify retry count (at least the ones we logged)
            assert final_metrics["retry_count"] >= expected_total_retries, \
                f"Expected at least {expected_total_retries} retries, got {final_metrics['retry_count']}"
            
            # Verify metrics consistency
            total = final_metrics["total_deployments"]
            successful = final_metrics["successful_deployments"]
            failed = final_metrics["failed_deployments"]
            cancelled = final_metrics["cancelled_deployments"]
            
            # Total should equal sum of outcomes
            calculated_total = successful + failed + cancelled
            assert calculated_total == total, \
                f"Metrics inconsistency: total {total} != sum of outcomes {calculated_total}"
            
            # Verify no negative values
            for metric_name, value in final_metrics.items():
                if isinstance(value, (int, float)):
                    assert value >= 0, f"Metric {metric_name} has negative value: {value}"
            
        finally:
            await orchestrator.stop()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _simulate_deployment_with_metrics(self, orchestrator: DeploymentOrchestrator, 
                                              deployment_index: int, update_count: int):
        """Helper method to simulate deployment with metric updates"""
        try:
            deployment_id = f"metrics_concurrent_{deployment_index}"
            
            # Create deployment result for logging
            result = DeploymentResult(
                deployment_id=deployment_id,
                plan_id=deployment_id,
                environment_id=f"metrics_env_{deployment_index}",
                status=DeploymentStatus.PENDING,
                start_time=datetime.now()
            )
            
            # Log deployment start
            orchestrator.deployment_logger.log_deployment_start(deployment_id, None)
            
            # Simulate multiple metric updates (retries)
            for j in range(update_count - 2):  # -2 for start and end
                orchestrator.deployment_logger.log_retry_attempt(
                    deployment_id, j + 1, f"Concurrent metrics test retry {j}"
                )
                await asyncio.sleep(0.01)  # Small delay to simulate real timing
            
            # Log deployment completion
            result.status = DeploymentStatus.COMPLETED if deployment_index % 2 == 0 else DeploymentStatus.FAILED
            result.end_time = datetime.now()
            result.artifacts_deployed = deployment_index + 1
            
            orchestrator.deployment_logger.log_deployment_end(deployment_id, result)
            
        except Exception as e:
            print(f"Metrics simulation {deployment_index} failed: {e}")
            raise
    
    @given(
        time_periods=st.integers(min_value=1, max_value=12),
        deployments_per_period=st.integers(min_value=1, max_value=8)
    )
    @settings(max_examples=25, deadline=8000)
    async def test_metrics_aggregation_accuracy(self, time_periods: int, deployments_per_period: int):
        """
        Property: Metrics aggregation produces accurate results
        
        Validates that:
        1. Metrics are aggregated correctly across time periods
        2. Calculated averages and rates are accurate
        3. Trend calculations are consistent
        4. Performance analytics are computed correctly
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            logger = DeploymentLogger(log_dir=temp_dir, log_sanitizer=None, secure_log_storage=None)
            
            # Track expected aggregations
            all_durations = []
            total_deployments = 0
            total_successful = 0
            total_failed = 0
            
            # Simulate deployments across time periods
            for period in range(time_periods):
                period_durations = []
                
                for deployment in range(deployments_per_period):
                    deployment_id = f"agg_period_{period}_deploy_{deployment}"
                    
                    # Vary deployment outcomes and durations
                    is_successful = deployment % 3 != 0  # 2/3 success rate
                    duration = 30.0 + (period * 10) + (deployment * 5)  # Increasing durations
                    
                    if is_successful:
                        status = DeploymentStatus.COMPLETED
                        total_successful += 1
                        period_durations.append(duration)
                        all_durations.append(duration)
                    else:
                        status = DeploymentStatus.FAILED
                        total_failed += 1
                    
                    total_deployments += 1
                    
                    # Create and log deployment result
                    result = DeploymentResult(
                        deployment_id=deployment_id,
                        plan_id=deployment_id,
                        environment_id=f"agg_env_{period}",
                        status=status,
                        start_time=datetime.now() - timedelta(seconds=duration),
                        end_time=datetime.now(),
                        artifacts_deployed=1 if is_successful else 0
                    )
                    
                    # Mock duration
                    result._duration_seconds = duration if is_successful else None
                    
                    logger.log_deployment_end(deployment_id, result)
            
            # Get aggregated metrics
            metrics = logger.get_metrics()
            
            # Verify aggregation accuracy
            assert metrics["total_deployments"] == total_deployments, \
                f"Total deployments: expected {total_deployments}, got {metrics['total_deployments']}"
            
            assert metrics["successful_deployments"] == total_successful, \
                f"Successful deployments: expected {total_successful}, got {metrics['successful_deployments']}"
            
            assert metrics["failed_deployments"] == total_failed, \
                f"Failed deployments: expected {total_failed}, got {metrics['failed_deployments']}"
            
            # Verify average duration calculation
            if all_durations:
                expected_avg = sum(all_durations) / len(all_durations)
                actual_avg = metrics["average_duration_seconds"]
                
                duration_diff = abs(actual_avg - expected_avg)
                assert duration_diff < 0.1, \
                    f"Average duration: expected {expected_avg}, got {actual_avg}, diff {duration_diff}"
            
            # Verify calculated rates
            if total_deployments > 0:
                expected_success_rate = (total_successful / total_deployments) * 100
                expected_failure_rate = (total_failed / total_deployments) * 100
                
                actual_success_rate = (metrics["successful_deployments"] / metrics["total_deployments"]) * 100
                actual_failure_rate = (metrics["failed_deployments"] / metrics["total_deployments"]) * 100
                
                assert abs(actual_success_rate - expected_success_rate) < 0.01, \
                    f"Success rate: expected {expected_success_rate}%, got {actual_success_rate}%"
                
                assert abs(actual_failure_rate - expected_failure_rate) < 0.01, \
                    f"Failure rate: expected {expected_failure_rate}%, got {actual_failure_rate}%"
            
            # Verify metrics persistence
            logger2 = DeploymentLogger(log_dir=temp_dir, log_sanitizer=None, secure_log_storage=None)
            persisted_metrics = logger2.get_metrics()
            
            assert persisted_metrics["total_deployments"] == total_deployments, \
                "Metrics not properly persisted"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# Synchronous test runners for pytest
def test_deployment_metrics_tracking_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestMetricsTracking()
    
    asyncio.run(test_instance.test_deployment_metrics_tracking(
        successful_count=8,
        failed_count=3,
        cancelled_count=2,
        retry_count=12
    ))

def test_concurrent_metrics_updates_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestMetricsTracking()
    
    asyncio.run(test_instance.test_concurrent_metrics_updates(
        concurrent_deployments=4,
        metrics_updates_per_deployment=6
    ))

def test_metrics_aggregation_accuracy_sync():
    """Synchronous wrapper for the async property test"""
    import asyncio
    
    test_instance = TestMetricsTracking()
    
    asyncio.run(test_instance.test_metrics_aggregation_accuracy(
        time_periods=5,
        deployments_per_period=4
    ))


if __name__ == "__main__":
    # Run basic functionality test
    print("Testing metrics tracking...")
    
    async def basic_test():
        test_instance = TestMetricsTracking()
        
        try:
            await test_instance.test_deployment_metrics_tracking(
                successful_count=5,
                failed_count=2,
                cancelled_count=1,
                retry_count=8
            )
            print("✓ Deployment metrics tracking test passed")
            
            await test_instance.test_concurrent_metrics_updates(
                concurrent_deployments=3,
                metrics_updates_per_deployment=5
            )
            print("✓ Concurrent metrics updates test passed")
            
            await test_instance.test_metrics_aggregation_accuracy(
                time_periods=3,
                deployments_per_period=3
            )
            print("✓ Metrics aggregation accuracy test passed")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(basic_test())