"""Property-based tests for regression detection and attribution.

**Feature: agentic-kernel-testing, Property 38: Regression detection and attribution**
**Validates: Requirements 8.3**

Property: For any performance degradation exceeding configured thresholds, the system 
should flag it as a regression and identify the commit range that introduced it.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Tuple
from datetime import datetime
import tempfile
import math

from analysis.performance_monitor import (
    BenchmarkResults, BenchmarkMetric, BenchmarkType
)
from analysis.baseline_manager import BaselineManager
from analysis.regression_detector import (
    RegressionDetector, RegressionSeverity, RegressionType,
    RegressionDetection, CommitRange, StatisticalAnalyzer
)


# Custom strategies for generating test data
@st.composite
def kernel_version_strategy(draw):
    """Generate valid kernel version strings."""
    major = draw(st.integers(min_value=4, max_value=6))
    minor = draw(st.integers(min_value=0, max_value=20))
    patch = draw(st.integers(min_value=0, max_value=100))
    return f"{major}.{minor}.{patch}"


@st.composite
def performance_metric_strategy(draw, metric_name=None, baseline_value=None):
    """Generate a performance metric with optional baseline for comparison."""
    if metric_name is None:
        metric_types = ["latency", "throughput", "bandwidth", "iops", "memory_usage"]
        metric_type = draw(st.sampled_from(metric_types))
        suffix = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=8))
        metric_name = f"{metric_type}_{suffix}"
    
    # Determine appropriate value range based on metric type
    if "latency" in metric_name or "time" in metric_name:
        # Latency metrics (microseconds, milliseconds)
        value_range = st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False)
        unit = draw(st.sampled_from(["microseconds", "milliseconds", "seconds"]))
        benchmark_type = BenchmarkType.SYSTEM_CALL_LATENCY
    elif "throughput" in metric_name or "bandwidth" in metric_name or "iops" in metric_name:
        # Throughput metrics (MB/s, IOPS, etc.)
        value_range = st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
        unit = draw(st.sampled_from(["MB/s", "IOPS", "Mbits/s"]))
        benchmark_type = BenchmarkType.IO_THROUGHPUT
    else:
        # Resource usage metrics
        value_range = st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
        unit = draw(st.sampled_from(["MB", "percent", "count"]))
        benchmark_type = BenchmarkType.CUSTOM
    
    if baseline_value is not None:
        # Generate value relative to baseline
        variation = draw(st.floats(min_value=0.5, max_value=2.0))
        value = baseline_value * variation
    else:
        value = draw(value_range)
    
    return BenchmarkMetric(
        name=metric_name,
        value=value,
        unit=unit,
        benchmark_type=benchmark_type
    )


@st.composite
def regression_scenario_strategy(draw):
    """Generate a scenario with baseline and regressed metrics.
    
    Returns tuple of (baseline_results, current_results, expected_regressions)
    """
    kernel_version = draw(kernel_version_strategy())
    
    # Generate 3-8 metrics
    num_metrics = draw(st.integers(min_value=3, max_value=8))
    
    baseline_metrics = []
    current_metrics = []
    expected_regressions = []
    
    for i in range(num_metrics):
        # Generate metric name
        metric_types = ["latency", "throughput", "bandwidth", "iops", "memory_usage"]
        metric_type = draw(st.sampled_from(metric_types))
        metric_name = f"{metric_type}_{i}"
        
        # Generate baseline value
        baseline_metric = draw(performance_metric_strategy(metric_name=metric_name))
        baseline_metrics.append(baseline_metric)
        
        # Decide if this metric should have a regression
        has_regression = draw(st.booleans())
        
        if has_regression:
            # Generate regression based on metric type
            if "latency" in metric_name or "time" in metric_name:
                # Latency increase (bad)
                regression_factor = draw(st.floats(min_value=1.15, max_value=2.0))  # 15% to 100% increase
                current_value = baseline_metric.value * regression_factor
                expected_type = RegressionType.LATENCY_INCREASE
            elif ("throughput" in metric_name or "bandwidth" in metric_name or 
                  "iops" in metric_name):
                # Throughput decrease (bad)
                regression_factor = draw(st.floats(min_value=0.5, max_value=0.85))  # 15% to 50% decrease
                current_value = baseline_metric.value * regression_factor
                expected_type = RegressionType.THROUGHPUT_DECREASE
            else:
                # Resource usage increase (bad)
                regression_factor = draw(st.floats(min_value=1.15, max_value=2.0))  # 15% to 100% increase
                current_value = baseline_metric.value * regression_factor
                expected_type = RegressionType.RESOURCE_INCREASE
            
            current_metric = BenchmarkMetric(
                name=metric_name,
                value=current_value,
                unit=baseline_metric.unit,
                benchmark_type=baseline_metric.benchmark_type
            )
            
            # Calculate expected change percent
            change_percent = ((current_value - baseline_metric.value) / baseline_metric.value) * 100
            
            expected_regressions.append({
                'metric_name': metric_name,
                'regression_type': expected_type,
                'change_percent': change_percent
            })
        else:
            # No regression - small variation
            variation = draw(st.floats(min_value=0.95, max_value=1.05))  # ±5% variation
            current_value = baseline_metric.value * variation
            
            current_metric = BenchmarkMetric(
                name=metric_name,
                value=current_value,
                unit=baseline_metric.unit,
                benchmark_type=baseline_metric.benchmark_type
            )
        
        current_metrics.append(current_metric)
    
    baseline_results = BenchmarkResults(
        benchmark_id=f"baseline_{draw(st.integers(min_value=1000000, max_value=9999999))}",
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=baseline_metrics
    )
    
    current_results = BenchmarkResults(
        benchmark_id=f"current_{draw(st.integers(min_value=1000000, max_value=9999999))}",
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=current_metrics
    )
    
    return baseline_results, current_results, expected_regressions


@st.composite
def commit_hash_strategy(draw):
    """Generate realistic git commit hashes."""
    return draw(st.text(alphabet='0123456789abcdef', min_size=7, max_size=40))


@st.composite
def threshold_strategy(draw):
    """Generate reasonable threshold values."""
    return draw(st.floats(min_value=0.05, max_value=0.5))  # 5% to 50%


class TestRegressionDetectionAndAttribution:
    """Test regression detection and attribution functionality."""
    
    @given(scenario=regression_scenario_strategy(), threshold=threshold_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_regression_detection_flags_degradation(self, scenario, threshold):
        """Property: Performance degradation exceeding thresholds should be flagged.
        
        **Feature: agentic-kernel-testing, Property 38: Regression detection and attribution**
        **Validates: Requirements 8.3**
        
        For any performance degradation exceeding configured thresholds, the system 
        should flag it as a regression.
        """
        baseline_results, current_results, expected_regressions = scenario
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_manager = BaselineManager(storage_dir=tmpdir)
            detector = RegressionDetector(baseline_manager)
            
            # Create and store baseline
            baseline = baseline_manager.create_baseline(baseline_results)
            baseline_manager.store_baseline(baseline)
            
            # Detect regressions
            report = detector.detect_regressions(current_results, threshold=threshold)
            
            # Verify report structure
            assert report is not None
            assert report.benchmark_id == current_results.benchmark_id
            assert report.baseline_id == baseline.baseline_id
            assert isinstance(report.regressions, list)
            
            # Check that regressions exceeding threshold are detected
            threshold_percent = threshold * 100
            
            for expected in expected_regressions:
                change_percent = abs(expected['change_percent'])
                
                if change_percent > threshold_percent:
                    # Should be detected as regression
                    detected_names = [r.metric_name for r in report.regressions]
                    assert expected['metric_name'] in detected_names, \
                        f"Regression in {expected['metric_name']} ({change_percent:.1f}% change) " \
                        f"should be detected with threshold {threshold_percent:.1f}%"
                    
                    # Find the detected regression
                    detected = next(r for r in report.regressions if r.metric_name == expected['metric_name'])
                    
                    # Verify regression type
                    assert detected.regression_type == expected['regression_type'], \
                        f"Wrong regression type for {expected['metric_name']}"
                    
                    # Verify threshold was exceeded
                    assert detected.threshold_exceeded > 0, \
                        f"Threshold exceeded should be positive for {expected['metric_name']}"
    
    @given(scenario=regression_scenario_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_regression_severity_classification(self, scenario):
        """Property: Detected regressions should be classified by severity.
        
        Regressions should be classified as low, medium, high, or critical based on
        how much they exceed the threshold.
        """
        baseline_results, current_results, expected_regressions = scenario
        threshold = 0.1  # 10% threshold
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_manager = BaselineManager(storage_dir=tmpdir)
            detector = RegressionDetector(baseline_manager)
            
            # Create and store baseline
            baseline = baseline_manager.create_baseline(baseline_results)
            baseline_manager.store_baseline(baseline)
            
            # Detect regressions
            report = detector.detect_regressions(current_results, threshold=threshold)
            
            # Verify all detected regressions have valid severity
            for regression in report.regressions:
                assert regression.severity in [
                    RegressionSeverity.LOW, RegressionSeverity.MEDIUM,
                    RegressionSeverity.HIGH, RegressionSeverity.CRITICAL
                ], f"Invalid severity for regression {regression.metric_name}"
                
                # Verify severity correlates with threshold exceeded
                if regression.threshold_exceeded >= 30:  # 30% over threshold
                    assert regression.severity in [RegressionSeverity.HIGH, RegressionSeverity.CRITICAL]
                elif regression.threshold_exceeded >= 15:  # 15% over threshold
                    assert regression.severity in [RegressionSeverity.MEDIUM, RegressionSeverity.HIGH, RegressionSeverity.CRITICAL]
    
    @given(scenario=regression_scenario_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_statistical_significance_testing(self, scenario):
        """Property: Statistical significance testing should provide confidence levels.
        
        When statistical testing is enabled, regressions should have confidence
        levels and statistical significance flags.
        """
        baseline_results, current_results, expected_regressions = scenario
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_manager = BaselineManager(storage_dir=tmpdir)
            detector = RegressionDetector(baseline_manager)
            
            # Create and store baseline
            baseline = baseline_manager.create_baseline(baseline_results)
            baseline_manager.store_baseline(baseline)
            
            # Detect regressions with statistical testing enabled
            report = detector.detect_regressions(
                current_results, 
                threshold=0.1, 
                enable_statistical_test=True
            )
            
            # Verify statistical properties
            for regression in report.regressions:
                # Should have confidence level
                assert 0.0 <= regression.confidence <= 1.0, \
                    f"Invalid confidence level {regression.confidence} for {regression.metric_name}"
                
                # Should have statistical significance flag
                assert isinstance(regression.statistical_significance, bool), \
                    f"Statistical significance should be boolean for {regression.metric_name}"
    
    @given(
        good_commit=commit_hash_strategy(),
        bad_commit=commit_hash_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_commit_range_identification(self, good_commit, bad_commit):
        """Property: System should identify commit ranges for regressions.
        
        When good and bad commits are provided, the system should attempt to
        identify the commit range that introduced the regression.
        """
        # Ensure commits are different
        assume(good_commit != bad_commit)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_manager = BaselineManager(storage_dir=tmpdir)
            # Don't provide repo path - this will test the case where git bisect is unavailable
            detector = RegressionDetector(baseline_manager, repo_path=None)
            
            # Test commit range identification when git bisect is not available
            commit_range = detector.identify_commit_range(good_commit, bad_commit)
            
            # Should return None when git bisect is not available
            assert commit_range is None, \
                "Should return None when git bisect is not available"
    
    @given(scenario=regression_scenario_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_overall_severity_calculation(self, scenario):
        """Property: Overall severity should reflect the highest individual severity.
        
        The overall report severity should be the maximum of all individual regression severities.
        """
        baseline_results, current_results, expected_regressions = scenario
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_manager = BaselineManager(storage_dir=tmpdir)
            detector = RegressionDetector(baseline_manager)
            
            # Create and store baseline
            baseline = baseline_manager.create_baseline(baseline_results)
            baseline_manager.store_baseline(baseline)
            
            # Detect regressions
            report = detector.detect_regressions(current_results, threshold=0.1)
            
            if report.regressions:
                # Find highest individual severity
                individual_severities = [r.severity for r in report.regressions]
                
                severity_order = [
                    RegressionSeverity.LOW,
                    RegressionSeverity.MEDIUM,
                    RegressionSeverity.HIGH,
                    RegressionSeverity.CRITICAL
                ]
                
                max_individual = max(individual_severities, key=lambda s: severity_order.index(s))
                
                # Overall severity should match or exceed the highest individual
                overall_index = severity_order.index(report.overall_severity)
                max_individual_index = severity_order.index(max_individual)
                
                assert overall_index >= max_individual_index, \
                    f"Overall severity {report.overall_severity} should be at least {max_individual}"
            else:
                # No regressions should result in LOW overall severity
                assert report.overall_severity == RegressionSeverity.LOW
    
    @given(scenario=regression_scenario_strategy(), threshold=threshold_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_regression_report_completeness(self, scenario, threshold):
        """Property: Regression reports should contain all required information.
        
        Every regression report should have complete metadata and structure.
        """
        baseline_results, current_results, expected_regressions = scenario
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_manager = BaselineManager(storage_dir=tmpdir)
            detector = RegressionDetector(baseline_manager)
            
            # Create and store baseline
            baseline = baseline_manager.create_baseline(baseline_results)
            baseline_manager.store_baseline(baseline)
            
            # Generate complete report
            report = detector.generate_regression_report(current_results, threshold=threshold)
            
            # Verify report completeness
            assert report.benchmark_id is not None
            assert report.baseline_id is not None
            assert report.kernel_version is not None
            assert report.baseline_kernel_version is not None
            assert report.timestamp is not None
            assert isinstance(report.regressions, list)
            assert isinstance(report.commit_ranges, list)
            assert report.overall_severity in RegressionSeverity
            assert isinstance(report.metadata, dict)
            
            # Verify metadata contains expected keys
            expected_metadata_keys = [
                'threshold_used', 'statistical_testing_enabled',
                'total_metrics_compared', 'regressions_found'
            ]
            for key in expected_metadata_keys:
                assert key in report.metadata, f"Missing metadata key: {key}"
    
    @given(
        baseline_values=st.lists(
            st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=2, max_size=10
        ),
        current_values=st.lists(
            st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=2, max_size=10
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_statistical_analyzer_confidence_calculation(self, baseline_values, current_values):
        """Property: Statistical analyzer should calculate valid confidence levels.
        
        Confidence calculations should always return values between 0.0 and 1.0.
        """
        confidence = StatisticalAnalyzer.calculate_confidence(baseline_values, current_values)
        
        assert 0.0 <= confidence <= 1.0, \
            f"Confidence {confidence} should be between 0.0 and 1.0"
        
        # If values are identical, confidence should be low (no significant difference)
        if all(abs(b - baseline_values[0]) < 0.01 for b in baseline_values) and \
           all(abs(c - current_values[0]) < 0.01 for c in current_values) and \
           abs(baseline_values[0] - current_values[0]) < 0.01:
            assert confidence < 0.5, \
                "Confidence should be low when values are nearly identical"
    
    @given(scenario=regression_scenario_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_regression_detection_serialization(self, scenario):
        """Property: Regression reports should serialize to dictionaries correctly.
        
        All regression report data should be serializable for storage and transmission.
        """
        baseline_results, current_results, expected_regressions = scenario
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_manager = BaselineManager(storage_dir=tmpdir)
            detector = RegressionDetector(baseline_manager)
            
            # Create and store baseline
            baseline = baseline_manager.create_baseline(baseline_results)
            baseline_manager.store_baseline(baseline)
            
            # Detect regressions
            report = detector.detect_regressions(current_results, threshold=0.1)
            
            # Serialize to dictionary
            report_dict = report.to_dict()
            
            # Verify serialization completeness
            assert isinstance(report_dict, dict)
            assert 'benchmark_id' in report_dict
            assert 'baseline_id' in report_dict
            assert 'kernel_version' in report_dict
            assert 'baseline_kernel_version' in report_dict
            assert 'timestamp' in report_dict
            assert 'regressions' in report_dict
            assert 'commit_ranges' in report_dict
            assert 'overall_severity' in report_dict
            assert 'metadata' in report_dict
            
            # Verify regressions are serialized
            assert isinstance(report_dict['regressions'], list)
            for regression_dict in report_dict['regressions']:
                assert isinstance(regression_dict, dict)
                assert 'metric_name' in regression_dict
                assert 'regression_type' in regression_dict
                assert 'severity' in regression_dict
    
    @given(scenario=regression_scenario_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_no_false_positives_within_threshold(self, scenario):
        """Property: No regressions should be detected for changes within threshold.
        
        Performance changes that don't exceed the threshold should not be flagged as regressions.
        """
        baseline_results, current_results, expected_regressions = scenario
        
        # Use a high threshold to test this property
        high_threshold = 0.5  # 50% threshold
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_manager = BaselineManager(storage_dir=tmpdir)
            detector = RegressionDetector(baseline_manager)
            
            # Create and store baseline
            baseline = baseline_manager.create_baseline(baseline_results)
            baseline_manager.store_baseline(baseline)
            
            # Detect regressions with high threshold
            report = detector.detect_regressions(current_results, threshold=high_threshold)
            
            # Verify no false positives
            threshold_percent = high_threshold * 100
            
            for regression in report.regressions:
                # Find corresponding baseline and current metrics
                baseline_metric = baseline.get_metric(regression.metric_name)
                current_metric = next(m for m in current_results.metrics if m.name == regression.metric_name)
                
                # Calculate actual change
                change_percent = abs(regression.change_percent)
                
                # Should exceed threshold
                assert change_percent > threshold_percent, \
                    f"Regression {regression.metric_name} with {change_percent:.1f}% change " \
                    f"should not be detected with {threshold_percent:.1f}% threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])