"""
Property-based tests for deployment completion summary generation.

**Feature: test-deployment-system, Property 15: Deployment completion summary**
**Validates: Requirements 3.5**

Tests that for any completed deployment, a comprehensive summary should be provided
with performance metrics, resource usage, and detailed reporting.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import the completion reporter we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from deployment.completion_reporter import (
    DeploymentCompletionReporter,
    DeploymentSummary,
    PerformanceMetrics,
    ResourceUsage,
    ValidationResults,
    StepDetail
)
from deployment.models import DeploymentResult, DeploymentStatus, DeploymentStep


# Hypothesis strategies for generating test data

@st.composite
def deployment_result_strategy(draw):
    """Generate realistic deployment result data"""
    statuses = [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]
    
    start_time = draw(st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime.now() - timedelta(hours=1)
    ))
    
    duration_minutes = draw(st.integers(min_value=1, max_value=120))
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    return DeploymentResult(
        deployment_id=draw(st.text(min_size=8, max_size=16, alphabet=st.characters(whitelist_categories=('Ll', 'Nd')))),
        plan_id=draw(st.text(min_size=8, max_size=12, alphabet=st.characters(whitelist_categories=('Ll', 'Nd')))),
        environment_id=draw(st.text(min_size=5, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        status=draw(st.sampled_from(statuses)),
        start_time=start_time,
        end_time=end_time,
        artifacts_deployed=draw(st.integers(min_value=0, max_value=50)),
        dependencies_installed=draw(st.integers(min_value=0, max_value=20)),
        retry_count=draw(st.integers(min_value=0, max_value=3)),
        error_message=draw(st.one_of(st.none(), st.text(min_size=10, max_size=100)))
    )

@st.composite
def deployment_steps_strategy(draw):
    """Generate realistic deployment steps data"""
    step_names = [
        'artifact_preparation',
        'environment_connection', 
        'dependency_installation',
        'script_deployment',
        'instrumentation_setup',
        'readiness_validation'
    ]
    
    statuses = [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.PENDING]
    
    num_steps = draw(st.integers(min_value=3, max_value=6))
    steps = []
    
    base_time = datetime.now() - timedelta(hours=1)
    
    for i in range(num_steps):
        step_start = base_time + timedelta(minutes=i * 5)
        step_duration = draw(st.integers(min_value=10, max_value=300))  # 10 seconds to 5 minutes
        step_end = step_start + timedelta(seconds=step_duration)
        
        step = DeploymentStep(
            step_id=f"step_{i}",
            name=step_names[i] if i < len(step_names) else f"custom_step_{i}",
            status=draw(st.sampled_from(statuses)),
            start_time=step_start,
            end_time=step_end,
            error_message=draw(st.one_of(st.none(), st.text(min_size=10, max_size=50))),
            progress_percentage=draw(st.integers(min_value=0, max_value=100)),
            details=draw(st.dictionaries(
                st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Ll',))),
                st.one_of(st.integers(), st.text(min_size=1, max_size=20), st.booleans()),
                min_size=0, max_size=5
            ))
        )
        steps.append(step)
    
    return steps

@st.composite
def performance_data_strategy(draw):
    """Generate performance data for testing"""
    return {
        'network_latency_ms': draw(st.floats(min_value=1.0, max_value=1000.0)),
        'disk_io_operations': draw(st.integers(min_value=0, max_value=10000)),
        'memory_peak_usage_mb': draw(st.floats(min_value=64.0, max_value=2048.0))
    }

@st.composite
def resource_data_strategy(draw):
    """Generate resource usage data for testing"""
    return {
        'cpu_usage_percent': draw(st.floats(min_value=0.0, max_value=100.0)),
        'memory_usage_mb': draw(st.floats(min_value=32.0, max_value=1024.0)),
        'disk_usage_mb': draw(st.floats(min_value=10.0, max_value=5000.0)),
        'network_bytes_sent': draw(st.integers(min_value=0, max_value=1000000000)),
        'network_bytes_received': draw(st.integers(min_value=0, max_value=1000000000)),
        'temporary_files_created': draw(st.integers(min_value=0, max_value=100)),
        'temporary_files_cleaned': draw(st.integers(min_value=0, max_value=100))
    }


class TestCompletionSummary:
    """Property-based tests for deployment completion summary functionality"""
    
    @given(deployment_result_strategy(), deployment_steps_strategy(), 
           performance_data_strategy(), resource_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_completion_summary_generation(self, deployment_result, deployment_steps, 
                                         performance_data, resource_data):
        """
        **Feature: test-deployment-system, Property 15: Deployment completion summary**
        **Validates: Requirements 3.5**
        
        Property: For any completed deployment, a comprehensive summary should be provided
        with all essential deployment information.
        """
        # Arrange
        reporter = DeploymentCompletionReporter(reports_dir="./test_reports")
        
        # Act
        summary = reporter.generate_completion_report(
            deployment_result=deployment_result,
            deployment_steps=deployment_steps,
            performance_data=performance_data,
            resource_data=resource_data
        )
        
        # Assert - Basic summary completeness
        assert summary.deployment_id == deployment_result.deployment_id, \
            "Summary must include correct deployment ID"
        
        assert summary.plan_id == deployment_result.plan_id, \
            "Summary must include correct plan ID"
        
        assert summary.environment_id == deployment_result.environment_id, \
            "Summary must include correct environment ID"
        
        assert summary.status == deployment_result.status.value, \
            "Summary must include correct deployment status"
        
        assert summary.artifacts_deployed == deployment_result.artifacts_deployed, \
            "Summary must include correct artifact count"
        
        assert summary.dependencies_installed == deployment_result.dependencies_installed, \
            "Summary must include correct dependency count"
        
        assert summary.retry_count == deployment_result.retry_count, \
            "Summary must include correct retry count"
    
    @given(deployment_result_strategy(), deployment_steps_strategy(), 
           performance_data_strategy(), resource_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_performance_metrics_calculation(self, deployment_result, deployment_steps, 
                                           performance_data, resource_data):
        """
        **Feature: test-deployment-system, Property 15: Deployment completion summary**
        **Validates: Requirements 3.5**
        
        Property: For any completed deployment, performance metrics should be calculated
        and included in the summary.
        """
        # Arrange
        reporter = DeploymentCompletionReporter(reports_dir="./test_reports")
        
        # Act
        summary = reporter.generate_completion_report(
            deployment_result=deployment_result,
            deployment_steps=deployment_steps,
            performance_data=performance_data,
            resource_data=resource_data
        )
        
        # Assert - Performance metrics presence
        assert summary.performance_metrics is not None, \
            "Summary must include performance metrics"
        
        perf_metrics = summary.performance_metrics
        
        # Validate performance metric types and ranges
        assert isinstance(perf_metrics.artifact_transfer_time_seconds, (int, float)), \
            "Artifact transfer time must be numeric"
        assert perf_metrics.artifact_transfer_time_seconds >= 0, \
            "Artifact transfer time must be non-negative"
        
        assert isinstance(perf_metrics.dependency_installation_time_seconds, (int, float)), \
            "Dependency installation time must be numeric"
        assert perf_metrics.dependency_installation_time_seconds >= 0, \
            "Dependency installation time must be non-negative"
        
        assert isinstance(perf_metrics.validation_time_seconds, (int, float)), \
            "Validation time must be numeric"
        assert perf_metrics.validation_time_seconds >= 0, \
            "Validation time must be non-negative"
        
        assert isinstance(perf_metrics.average_step_duration_seconds, (int, float)), \
            "Average step duration must be numeric"
        assert perf_metrics.average_step_duration_seconds >= 0, \
            "Average step duration must be non-negative"
        
        # Validate throughput calculation
        if summary.total_duration_seconds > 0 and deployment_result.artifacts_deployed > 0:
            expected_throughput = (deployment_result.artifacts_deployed / summary.total_duration_seconds) * 60
            assert abs(perf_metrics.throughput_artifacts_per_minute - expected_throughput) < 0.1, \
                "Throughput calculation must be accurate"
        
        # Validate external performance data integration
        assert perf_metrics.network_latency_ms == performance_data['network_latency_ms'], \
            "Network latency must match provided performance data"
        
        assert perf_metrics.disk_io_operations == performance_data['disk_io_operations'], \
            "Disk I/O operations must match provided performance data"
        
        assert perf_metrics.memory_peak_usage_mb == performance_data['memory_peak_usage_mb'], \
            "Memory peak usage must match provided performance data"
    
    @given(deployment_result_strategy(), deployment_steps_strategy(), 
           performance_data_strategy(), resource_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_step_details_extraction(self, deployment_result, deployment_steps, 
                                   performance_data, resource_data):
        """
        **Feature: test-deployment-system, Property 15: Deployment completion summary**
        **Validates: Requirements 3.5**
        
        Property: For any completed deployment, detailed step information should be
        extracted and included in the summary.
        """
        # Arrange
        reporter = DeploymentCompletionReporter(reports_dir="./test_reports")
        
        # Act
        summary = reporter.generate_completion_report(
            deployment_result=deployment_result,
            deployment_steps=deployment_steps,
            performance_data=performance_data,
            resource_data=resource_data
        )
        
        # Assert - Step details completeness
        assert summary.step_details is not None, \
            "Summary must include step details"
        
        assert len(summary.step_details) == len(deployment_steps), \
            "Summary must include details for all deployment steps"
        
        # Validate each step detail
        for i, (original_step, detail) in enumerate(zip(deployment_steps, summary.step_details)):
            assert detail.step_name == original_step.name, \
                f"Step {i} name must match original step"
            
            assert detail.status == original_step.status.value, \
                f"Step {i} status must match original step"
            
            assert detail.start_time == original_step.start_time.isoformat(), \
                f"Step {i} start time must match original step"
            
            if original_step.end_time:
                assert detail.end_time == original_step.end_time.isoformat(), \
                    f"Step {i} end time must match original step"
            
            if original_step.duration_seconds:
                assert detail.duration_seconds == original_step.duration_seconds, \
                    f"Step {i} duration must match original step"
            
            if original_step.error_message:
                assert detail.error_message == original_step.error_message, \
                    f"Step {i} error message must match original step"
    
    @given(deployment_result_strategy(), deployment_steps_strategy(), 
           performance_data_strategy(), resource_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_resource_usage_analysis(self, deployment_result, deployment_steps, 
                                   performance_data, resource_data):
        """
        **Feature: test-deployment-system, Property 15: Deployment completion summary**
        **Validates: Requirements 3.5**
        
        Property: For any completed deployment, resource usage analysis should be
        performed and included in the summary.
        """
        # Arrange
        reporter = DeploymentCompletionReporter(reports_dir="./test_reports")
        
        # Act
        summary = reporter.generate_completion_report(
            deployment_result=deployment_result,
            deployment_steps=deployment_steps,
            performance_data=performance_data,
            resource_data=resource_data
        )
        
        # Assert - Resource usage presence
        assert summary.resource_usage is not None, \
            "Summary must include resource usage analysis"
        
        resource_usage = summary.resource_usage
        
        # Validate resource usage data integration
        assert resource_usage.cpu_usage_percent == resource_data['cpu_usage_percent'], \
            "CPU usage must match provided resource data"
        
        assert resource_usage.memory_usage_mb == resource_data['memory_usage_mb'], \
            "Memory usage must match provided resource data"
        
        assert resource_usage.disk_usage_mb == resource_data['disk_usage_mb'], \
            "Disk usage must match provided resource data"
        
        assert resource_usage.network_bytes_sent == resource_data['network_bytes_sent'], \
            "Network bytes sent must match provided resource data"
        
        assert resource_usage.network_bytes_received == resource_data['network_bytes_received'], \
            "Network bytes received must match provided resource data"
        
        # Validate resource usage ranges
        assert 0 <= resource_usage.cpu_usage_percent <= 100, \
            "CPU usage must be within valid percentage range"
        
        assert resource_usage.memory_usage_mb >= 0, \
            "Memory usage must be non-negative"
        
        assert resource_usage.disk_usage_mb >= 0, \
            "Disk usage must be non-negative"
        
        assert resource_usage.network_bytes_sent >= 0, \
            "Network bytes sent must be non-negative"
        
        assert resource_usage.network_bytes_received >= 0, \
            "Network bytes received must be non-negative"
    
    @given(deployment_result_strategy(), deployment_steps_strategy(), 
           performance_data_strategy(), resource_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_timing_calculations(self, deployment_result, deployment_steps, 
                               performance_data, resource_data):
        """
        **Feature: test-deployment-system, Property 15: Deployment completion summary**
        **Validates: Requirements 3.5**
        
        Property: For any completed deployment, timing calculations should be accurate
        and consistent across the summary.
        """
        # Arrange
        reporter = DeploymentCompletionReporter(reports_dir="./test_reports")
        
        # Act
        summary = reporter.generate_completion_report(
            deployment_result=deployment_result,
            deployment_steps=deployment_steps,
            performance_data=performance_data,
            resource_data=resource_data
        )
        
        # Assert - Timing consistency
        if deployment_result.end_time and deployment_result.start_time:
            expected_duration = (deployment_result.end_time - deployment_result.start_time).total_seconds()
            assert abs(summary.total_duration_seconds - expected_duration) < 1.0, \
                "Total duration calculation must be accurate"
        
        # Validate step completion counting
        completed_steps = len([step for step in deployment_steps if step.status == DeploymentStatus.COMPLETED])
        assert summary.steps_completed == completed_steps, \
            "Completed steps count must be accurate"
        
        assert summary.steps_total == len(deployment_steps), \
            "Total steps count must match provided steps"
        
        # Validate timing relationships
        if summary.performance_metrics:
            perf_metrics = summary.performance_metrics
            
            # Sum of categorized times should not exceed total duration significantly
            categorized_time = (
                perf_metrics.artifact_transfer_time_seconds +
                perf_metrics.dependency_installation_time_seconds +
                perf_metrics.validation_time_seconds
            )
            
            # Allow some tolerance for overlapping operations and uncategorized time
            assert categorized_time <= summary.total_duration_seconds * 1.5, \
                "Categorized timing should not significantly exceed total duration"
    
    @given(deployment_result_strategy(), deployment_steps_strategy())
    @settings(max_examples=50, deadline=None)
    def test_validation_results_extraction(self, deployment_result, deployment_steps):
        """
        **Feature: test-deployment-system, Property 15: Deployment completion summary**
        **Validates: Requirements 3.5**
        
        Property: For any completed deployment with validation steps, validation results
        should be extracted and included in the summary.
        """
        # Arrange
        reporter = DeploymentCompletionReporter(reports_dir="./test_reports")
        
        # Add validation details to a validation step if one exists
        validation_step = None
        for step in deployment_steps:
            if 'validation' in step.name.lower() or 'readiness' in step.name.lower():
                validation_step = step
                break
        
        if validation_step:
            # Add validation details
            validation_step.details = {
                'checks_passed': 8,
                'checks_failed': 2,
                'critical_issues': 1,
                'warnings': 3
            }
        
        # Act
        summary = reporter.generate_completion_report(
            deployment_result=deployment_result,
            deployment_steps=deployment_steps,
            performance_data={},
            resource_data={}
        )
        
        # Assert - Validation results
        if validation_step and validation_step.details:
            assert summary.validation_results is not None, \
                "Summary must include validation results when validation step exists"
            
            val_results = summary.validation_results
            
            assert val_results.checks_passed == 8, \
                "Validation results must include correct passed checks count"
            
            assert val_results.checks_failed == 2, \
                "Validation results must include correct failed checks count"
            
            assert val_results.checks_total == 10, \
                "Validation results must calculate correct total checks"
            
            assert val_results.success_rate_percent == 80.0, \
                "Validation results must calculate correct success rate"
            
            assert val_results.critical_issues == 1, \
                "Validation results must include correct critical issues count"
            
            assert val_results.warnings == 3, \
                "Validation results must include correct warnings count"
        else:
            # If no validation step with details, validation results should be None
            assert summary.validation_results is None, \
                "Summary should not include validation results when no validation data exists"
    
    @given(deployment_result_strategy(), deployment_steps_strategy(), 
           performance_data_strategy(), resource_data_strategy())
    @settings(max_examples=50, deadline=None)
    def test_report_persistence_and_retrieval(self, deployment_result, deployment_steps, 
                                            performance_data, resource_data):
        """
        **Feature: test-deployment-system, Property 15: Deployment completion summary**
        **Validates: Requirements 3.5**
        
        Property: For any completed deployment, the summary should be persistable
        and retrievable for future reference.
        """
        # Arrange
        reporter = DeploymentCompletionReporter(reports_dir="./test_reports")
        
        # Act - Generate and save report
        original_summary = reporter.generate_completion_report(
            deployment_result=deployment_result,
            deployment_steps=deployment_steps,
            performance_data=performance_data,
            resource_data=resource_data
        )
        
        # Act - Retrieve report
        retrieved_summary = reporter.get_deployment_report(deployment_result.deployment_id)
        
        # Assert - Persistence and retrieval
        assert retrieved_summary is not None, \
            "Generated report must be retrievable"
        
        assert retrieved_summary.deployment_id == original_summary.deployment_id, \
            "Retrieved report must have correct deployment ID"
        
        assert retrieved_summary.status == original_summary.status, \
            "Retrieved report must preserve deployment status"
        
        assert retrieved_summary.total_duration_seconds == original_summary.total_duration_seconds, \
            "Retrieved report must preserve timing information"
        
        assert retrieved_summary.artifacts_deployed == original_summary.artifacts_deployed, \
            "Retrieved report must preserve artifact information"
        
        # Validate complex nested data preservation
        if original_summary.performance_metrics and retrieved_summary.performance_metrics:
            assert retrieved_summary.performance_metrics.throughput_artifacts_per_minute == \
                   original_summary.performance_metrics.throughput_artifacts_per_minute, \
                "Retrieved report must preserve performance metrics"
        
        if original_summary.resource_usage and retrieved_summary.resource_usage:
            assert retrieved_summary.resource_usage.cpu_usage_percent == \
                   original_summary.resource_usage.cpu_usage_percent, \
                "Retrieved report must preserve resource usage data"


def test_completion_summary_sync():
    """Synchronous test runner for the completion summary property tests"""
    # Test with a simple deployment case
    from datetime import datetime, timedelta
    
    start_time = datetime.now() - timedelta(minutes=30)
    end_time = datetime.now()
    
    deployment_result = DeploymentResult(
        deployment_id='test123',
        plan_id='plan123',
        environment_id='env001',
        status=DeploymentStatus.COMPLETED,
        start_time=start_time,
        end_time=end_time,
        artifacts_deployed=5,
        dependencies_installed=3,
        retry_count=0
    )
    
    deployment_steps = [
        DeploymentStep(
            step_id='step1',
            name='artifact_preparation',
            status=DeploymentStatus.COMPLETED,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=5),
            progress_percentage=100,
            details={'artifacts_processed': 5}
        ),
        DeploymentStep(
            step_id='step2',
            name='environment_connection',
            status=DeploymentStatus.COMPLETED,
            start_time=start_time + timedelta(minutes=5),
            end_time=start_time + timedelta(minutes=10),
            progress_percentage=100,
            details={}
        )
    ]
    
    performance_data = {
        'network_latency_ms': 50.0,
        'disk_io_operations': 100,
        'memory_peak_usage_mb': 256.0
    }
    
    resource_data = {
        'cpu_usage_percent': 45.0,
        'memory_usage_mb': 128.0,
        'disk_usage_mb': 500.0,
        'network_bytes_sent': 1024000,
        'network_bytes_received': 512000,
        'temporary_files_created': 10,
        'temporary_files_cleaned': 10
    }
    
    # Test the core functionality
    reporter = DeploymentCompletionReporter(reports_dir="./test_reports")
    
    # Test summary generation
    summary = reporter.generate_completion_report(
        deployment_result=deployment_result,
        deployment_steps=deployment_steps,
        performance_data=performance_data,
        resource_data=resource_data
    )
    
    # Basic assertions
    assert summary.deployment_id == deployment_result.deployment_id
    assert summary.status == deployment_result.status.value
    assert summary.artifacts_deployed == deployment_result.artifacts_deployed
    assert summary.performance_metrics is not None
    assert summary.resource_usage is not None
    assert summary.step_details is not None
    assert len(summary.step_details) == len(deployment_steps)
    
    # Test persistence and retrieval
    retrieved_summary = reporter.get_deployment_report(deployment_result.deployment_id)
    assert retrieved_summary is not None
    assert retrieved_summary.deployment_id == summary.deployment_id


if __name__ == "__main__":
    test_completion_summary_sync()
    print("Completion summary property tests completed successfully!")