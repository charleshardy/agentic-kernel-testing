"""Property-based tests for regression profiling data.

**Feature: agentic-kernel-testing, Property 39: Regression profiling data**

This module tests that for any detected performance regression, the system 
provides profiling data showing where additional time or resources are consumed.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile
import os

from analysis.performance_monitor import (
    PerformanceMonitor, 
    BenchmarkResults, 
    BenchmarkMetric, 
    BenchmarkType,
    ProfilingData,
    PerformanceProfiler
)


# Test data generators
@st.composite
def benchmark_metric_strategy(draw):
    """Generate a BenchmarkMetric for testing."""
    metric_types = [
        ("latency", "microseconds", st.floats(min_value=0.1, max_value=1000.0)),
        ("throughput", "MB/s", st.floats(min_value=1.0, max_value=10000.0)),
        ("iops", "IOPS", st.floats(min_value=100.0, max_value=100000.0))
    ]
    
    metric_type, unit, value_strategy = draw(st.sampled_from(metric_types))
    name = draw(st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'))
    value = draw(value_strategy)
    
    return BenchmarkMetric(
        name=f"{metric_type}_{name}",
        value=value,
        unit=unit,
        benchmark_type=BenchmarkType.CUSTOM,
        metadata={'test_metric': True}
    )


@st.composite
def profiling_data_strategy(draw):
    """Generate ProfilingData for testing."""
    profile_id = draw(st.text(min_size=5, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'))
    command = draw(st.text(min_size=5, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./'))
    duration = draw(st.floats(min_value=1.0, max_value=300.0))
    samples = draw(st.integers(min_value=100, max_value=10000))
    
    # Generate hotspots
    num_hotspots = draw(st.integers(min_value=1, max_value=10))
    hotspots = []
    
    for _ in range(num_hotspots):
        symbol = draw(st.text(min_size=5, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'))
        overhead = draw(st.floats(min_value=1.0, max_value=50.0))
        hotspots.append({
            'symbol': symbol,
            'overhead_percent': overhead,
            'type': 'function'
        })
    
    return ProfilingData(
        profile_id=profile_id,
        command=command,
        duration_seconds=duration,
        samples=samples,
        events=['cycles', 'instructions'],
        hotspots=hotspots,
        metadata={'test_data': True}
    )


@st.composite
def benchmark_results_strategy(draw):
    """Generate BenchmarkResults with optional profiling data."""
    benchmark_id = draw(st.text(min_size=5, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'))
    kernel_version = draw(st.text(min_size=5, max_size=10, alphabet='0123456789.'))
    
    # Generate metrics
    num_metrics = draw(st.integers(min_value=1, max_value=5))
    metrics = [draw(benchmark_metric_strategy()) for _ in range(num_metrics)]
    
    # Optionally include profiling data
    include_profiling = draw(st.booleans())
    profiling_data = draw(profiling_data_strategy()) if include_profiling else None
    
    return BenchmarkResults(
        benchmark_id=benchmark_id,
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=metrics,
        profiling_data=profiling_data,
        environment={'test': True},
        metadata={'test_results': True}
    )


@st.composite
def regression_comparison_strategy(draw):
    """Generate comparison data with regressions."""
    current_id = draw(st.text(min_size=5, max_size=15))
    baseline_id = draw(st.text(min_size=5, max_size=15))
    
    # Generate comparisons with some regressions
    num_comparisons = draw(st.integers(min_value=3, max_value=8))
    comparisons = []
    
    for i in range(num_comparisons):
        metric_name = draw(st.sampled_from([
            'syscall_read_latency', 'sequential_write_throughput', 
            'tcp_stream_throughput', 'random_read_iops'
        ]))
        
        baseline_value = draw(st.floats(min_value=10.0, max_value=1000.0))
        
        # Create some regressions (>10% change)
        is_regression = draw(st.booleans())
        if is_regression:
            if 'latency' in metric_name:
                # Latency regression: increase by 15-50%
                change_percent = draw(st.floats(min_value=15.0, max_value=50.0))
                current_value = baseline_value * (1 + change_percent / 100)
            else:
                # Throughput regression: decrease by 15-50%
                change_percent = draw(st.floats(min_value=-50.0, max_value=-15.0))
                current_value = baseline_value * (1 + change_percent / 100)
        else:
            # No regression: small change
            change_percent = draw(st.floats(min_value=-5.0, max_value=5.0))
            current_value = baseline_value * (1 + change_percent / 100)
        
        comparisons.append({
            'metric_name': metric_name,
            'baseline_value': baseline_value,
            'current_value': current_value,
            'change_percent': change_percent,
            'unit': 'microseconds' if 'latency' in metric_name else 'MB/s',
            'benchmark_type': 'latency' if 'latency' in metric_name else 'throughput'
        })
    
    return {
        'current_id': current_id,
        'baseline_id': baseline_id,
        'current_kernel': '5.15.0',
        'baseline_kernel': '5.14.0',
        'comparisons': comparisons,
        'timestamp': datetime.now().isoformat()
    }


class TestRegressionProfilingData:
    """Test regression profiling data property."""
    
    @given(regression_comparison_strategy())
    @settings(max_examples=100, deadline=None)
    def test_regression_detection_provides_profiling_data(self, comparison_data):
        """
        **Feature: agentic-kernel-testing, Property 39: Regression profiling data**
        
        Property: For any detected performance regression, the system should provide 
        profiling data showing where additional time or resources are consumed.
        
        **Validates: Requirements 8.4**
        """
        # Arrange
        monitor = PerformanceMonitor()
        
        # Act - detect regressions
        regressions = monitor.detect_regressions(comparison_data, threshold=0.1)
        
        # Assert - check that regressions have profiling analysis
        for regression in regressions:
            # Each regression should have the basic regression data
            assert 'metric_name' in regression
            assert 'baseline_value' in regression
            assert 'current_value' in regression
            assert 'change_percent' in regression
            assert 'severity' in regression
            
            # Verify change is actually a regression (>10%)
            change_percent = abs(regression['change_percent'])
            assert change_percent > 10.0, f"Detected regression should exceed 10% threshold, got {change_percent}%"
            
            # Property: Regression should include profiling analysis
            assert 'profiling_analysis' in regression, f"Regression for {regression['metric_name']} missing profiling analysis"
            
            profiling_analysis = regression['profiling_analysis']
            
            # Profiling analysis should contain key information
            assert 'hotspots_identified' in profiling_analysis
            assert 'recommendation' in profiling_analysis
            assert isinstance(profiling_analysis['recommendation'], str)
            assert len(profiling_analysis['recommendation']) > 0
            
            # If hotspots are identified, should have details
            if profiling_analysis['hotspots_identified']:
                assert 'top_hotspot' in profiling_analysis
                assert 'hotspot_overhead' in profiling_analysis
                assert isinstance(profiling_analysis['hotspot_overhead'], (int, float))
                assert profiling_analysis['hotspot_overhead'] > 0
    
    @given(profiling_data_strategy())
    @settings(max_examples=50, deadline=None)
    def test_profiling_data_contains_performance_information(self, profiling_data):
        """
        Property: Profiling data should contain information about where time/resources are consumed.
        """
        # Arrange
        profiler = PerformanceProfiler()
        
        # Act - analyze profiling data
        hotspots = profiler.identify_hotspots(profiling_data, threshold_percent=5.0)
        
        # Assert - profiling data contains performance information
        assert profiling_data.profile_id is not None
        assert profiling_data.command is not None
        assert profiling_data.duration_seconds > 0
        assert profiling_data.samples >= 0
        
        # Hotspots should be identified from profiling data
        for hotspot in hotspots:
            assert 'symbol' in hotspot
            assert 'overhead_percent' in hotspot
            assert 'severity' in hotspot
            assert 'recommendation' in hotspot
            
            # Overhead should be above threshold
            assert hotspot['overhead_percent'] >= 5.0
            
            # Severity should be valid
            assert hotspot['severity'] in ['low', 'medium', 'high', 'critical']
            
            # Recommendation should be meaningful
            assert isinstance(hotspot['recommendation'], str)
            assert len(hotspot['recommendation']) > 10
    
    @given(benchmark_results_strategy())
    @settings(max_examples=50, deadline=None)
    def test_benchmark_results_with_profiling_data_structure(self, benchmark_results):
        """
        Property: Benchmark results with profiling data should maintain proper structure.
        """
        # Act & Assert - verify structure
        assert benchmark_results.benchmark_id is not None
        assert benchmark_results.kernel_version is not None
        assert benchmark_results.timestamp is not None
        assert isinstance(benchmark_results.metrics, list)
        
        # If profiling data is present, verify its structure
        if benchmark_results.profiling_data is not None:
            profiling = benchmark_results.profiling_data
            
            assert profiling.profile_id is not None
            assert profiling.command is not None
            assert profiling.duration_seconds > 0
            assert profiling.samples >= 0
            assert isinstance(profiling.events, list)
            assert isinstance(profiling.hotspots, list)
            
            # Hotspots should have required fields
            for hotspot in profiling.hotspots:
                assert 'symbol' in hotspot
                assert 'overhead_percent' in hotspot
                assert isinstance(hotspot['overhead_percent'], (int, float))
                assert hotspot['overhead_percent'] > 0
    
    @given(st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./'), 
           st.text(min_size=5, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./'))
    @settings(max_examples=30, deadline=None)
    def test_profiling_report_generation_completeness(self, kernel_image, workload):
        """
        Property: Profiling reports should be complete and contain analysis.
        """
        # Arrange
        monitor = PerformanceMonitor()
        
        # Create mock profiling data
        profiling_data = ProfilingData(
            profile_id="test_profile",
            command=workload,
            duration_seconds=30.0,
            samples=1000,
            events=['cycles', 'instructions'],
            hotspots=[
                {'symbol': 'test_function', 'overhead_percent': 15.5, 'type': 'function'},
                {'symbol': 'malloc', 'overhead_percent': 8.2, 'type': 'function'}
            ],
            metadata={'test': True}
        )
        
        # Act - generate profiling report
        report = monitor.generate_profiling_report(profiling_data)
        
        # Assert - report completeness
        required_fields = [
            'profile_id', 'command', 'duration_seconds', 'total_samples',
            'events_monitored', 'hotspots_count', 'analysis_summary', 'recommendations'
        ]
        
        for field in required_fields:
            assert field in report, f"Profiling report missing required field: {field}"
        
        # Verify report content quality
        assert report['profile_id'] == profiling_data.profile_id
        assert report['command'] == profiling_data.command
        assert report['duration_seconds'] == profiling_data.duration_seconds
        assert report['total_samples'] == profiling_data.samples
        assert report['hotspots_count'] >= 0
        
        # Analysis summary should be meaningful
        assert isinstance(report['analysis_summary'], str)
        assert len(report['analysis_summary']) > 20
        
        # Recommendations should be provided
        assert isinstance(report['recommendations'], list)
        for recommendation in report['recommendations']:
            assert isinstance(recommendation, str)
            assert len(recommendation) > 10
    
    def test_profiling_data_serialization_roundtrip(self):
        """
        Property: Profiling data should serialize and deserialize correctly.
        """
        # Arrange
        original_data = ProfilingData(
            profile_id="test_123",
            command="test_workload.sh",
            duration_seconds=45.5,
            samples=2500,
            events=['cycles', 'instructions', 'cache-misses'],
            hotspots=[
                {'symbol': 'kernel_function', 'overhead_percent': 25.3, 'type': 'function'},
                {'symbol': 'user_function', 'overhead_percent': 12.1, 'type': 'function'}
            ],
            flamegraph_path="/tmp/flamegraph.svg",
            raw_data_path="/tmp/perf.data",
            metadata={'version': '1.0', 'test': True}
        )
        
        # Act - serialize and deserialize
        serialized = original_data.to_dict()
        deserialized = ProfilingData.from_dict(serialized)
        
        # Assert - data integrity
        assert deserialized.profile_id == original_data.profile_id
        assert deserialized.command == original_data.command
        assert deserialized.duration_seconds == original_data.duration_seconds
        assert deserialized.samples == original_data.samples
        assert deserialized.events == original_data.events
        assert deserialized.hotspots == original_data.hotspots
        assert deserialized.flamegraph_path == original_data.flamegraph_path
        assert deserialized.raw_data_path == original_data.raw_data_path
        assert deserialized.metadata == original_data.metadata


if __name__ == "__main__":
    pytest.main([__file__])