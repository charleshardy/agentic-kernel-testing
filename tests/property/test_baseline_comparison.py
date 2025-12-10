"""Property-based tests for baseline comparison.

**Feature: agentic-kernel-testing, Property 37: Baseline comparison execution**
**Validates: Requirements 8.2**

Property: For any collected benchmark results, the system should compare them 
against baseline measurements from previous kernel versions.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List
from datetime import datetime
import tempfile
import shutil

from analysis.performance_monitor import (
    BenchmarkResults, BenchmarkMetric, BenchmarkType
)
from analysis.baseline_manager import BaselineManager, PerformanceBaseline


# Custom strategies for generating test data
@st.composite
def kernel_version_strategy(draw):
    """Generate valid kernel version strings."""
    major = draw(st.integers(min_value=4, max_value=6))
    minor = draw(st.integers(min_value=0, max_value=20))
    patch = draw(st.integers(min_value=0, max_value=100))
    return f"{major}.{minor}.{patch}"


@st.composite
def benchmark_metric_strategy(draw):
    """Generate a single benchmark metric."""
    metric_type = draw(st.sampled_from(list(BenchmarkType)))
    name = f"{metric_type.value}_{draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10))}"
    value = draw(st.floats(min_value=0.1, max_value=10000.0, allow_nan=False, allow_infinity=False))
    unit = draw(st.sampled_from(["MB/s", "microseconds", "Mbits/s", "IOPS", "trans/s"]))
    
    return BenchmarkMetric(
        name=name,
        value=value,
        unit=unit,
        benchmark_type=metric_type
    )


@st.composite
def benchmark_results_strategy(draw, kernel_version=None):
    """Generate BenchmarkResults."""
    if kernel_version is None:
        kernel_version = draw(kernel_version_strategy())
    
    benchmark_id = f"bench_{draw(st.integers(min_value=1000000, max_value=9999999))}"
    
    # Generate 3-10 metrics
    num_metrics = draw(st.integers(min_value=3, max_value=10))
    metrics = [draw(benchmark_metric_strategy()) for _ in range(num_metrics)]
    
    return BenchmarkResults(
        benchmark_id=benchmark_id,
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=metrics
    )


@st.composite
def related_benchmark_results_strategy(draw):
    """Generate two related benchmark results with some common metrics.
    
    This ensures we have comparable metrics between baseline and current results.
    """
    kernel_version = draw(kernel_version_strategy())
    
    # Generate common metric names
    num_common = draw(st.integers(min_value=2, max_value=5))
    common_names = [
        f"metric_{i}_{draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=8))}"
        for i in range(num_common)
    ]
    
    # Create baseline metrics
    baseline_metrics = []
    for name in common_names:
        metric_type = draw(st.sampled_from(list(BenchmarkType)))
        value = draw(st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
        unit = draw(st.sampled_from(["MB/s", "microseconds", "Mbits/s", "IOPS"]))
        
        baseline_metrics.append(BenchmarkMetric(
            name=name,
            value=value,
            unit=unit,
            benchmark_type=metric_type
        ))
    
    # Create current metrics (with some variation)
    current_metrics = []
    for name in common_names:
        # Find corresponding baseline metric
        baseline_metric = next(m for m in baseline_metrics if m.name == name)
        
        # Vary the value by -50% to +50%
        variation = draw(st.floats(min_value=0.5, max_value=1.5))
        new_value = baseline_metric.value * variation
        
        current_metrics.append(BenchmarkMetric(
            name=name,
            value=new_value,
            unit=baseline_metric.unit,
            benchmark_type=baseline_metric.benchmark_type
        ))
    
    # Add some unique metrics to current
    num_unique = draw(st.integers(min_value=0, max_value=3))
    for i in range(num_unique):
        unique_name = f"unique_{i}_{draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=8))}"
        metric_type = draw(st.sampled_from(list(BenchmarkType)))
        value = draw(st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
        unit = draw(st.sampled_from(["MB/s", "microseconds", "Mbits/s", "IOPS"]))
        
        current_metrics.append(BenchmarkMetric(
            name=unique_name,
            value=value,
            unit=unit,
            benchmark_type=metric_type
        ))
    
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
    
    return baseline_results, current_results


class TestBaselineComparison:
    """Test baseline comparison functionality."""
    
    @given(benchmark_results=benchmark_results_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_baseline_creation_and_storage(self, benchmark_results: BenchmarkResults):
        """Property: Any benchmark results can be stored as a baseline.
        
        This tests that we can create and store baselines from any valid benchmark results.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create baseline
            baseline = manager.create_baseline(benchmark_results)
            
            # Verify baseline properties
            assert baseline.kernel_version == benchmark_results.kernel_version
            assert len(baseline.metrics) == len(benchmark_results.metrics)
            assert baseline.baseline_id is not None
            
            # Store baseline
            stored_path = manager.store_baseline(baseline)
            assert stored_path is not None
            
            # Verify file exists
            import os
            assert os.path.exists(stored_path)
    
    @given(benchmark_results=benchmark_results_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_baseline_retrieval_roundtrip(self, benchmark_results: BenchmarkResults):
        """Property: Stored baselines can be retrieved with same data.
        
        Any baseline that is stored should be retrievable with identical data.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create and store baseline
            baseline = manager.create_baseline(benchmark_results)
            manager.store_baseline(baseline)
            
            # Retrieve baseline
            retrieved = manager.retrieve_baseline(
                baseline.kernel_version,
                baseline.baseline_id
            )
            
            assert retrieved is not None
            assert retrieved.kernel_version == baseline.kernel_version
            assert retrieved.baseline_id == baseline.baseline_id
            assert len(retrieved.metrics) == len(baseline.metrics)
            
            # Verify metrics match
            for orig, retr in zip(baseline.metrics, retrieved.metrics):
                assert orig.name == retr.name
                assert abs(orig.value - retr.value) < 0.01
                assert orig.unit == retr.unit
    
    @given(results_pair=related_benchmark_results_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_baseline_comparison_execution(self, results_pair):
        """Property: Baseline comparison should execute for any benchmark results.
        
        **Feature: agentic-kernel-testing, Property 37: Baseline comparison execution**
        **Validates: Requirements 8.2**
        
        For any collected benchmark results, the system should compare them against 
        baseline measurements from previous kernel versions.
        """
        baseline_results, current_results = results_pair
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create and store baseline
            baseline = manager.create_baseline(baseline_results)
            manager.store_baseline(baseline)
            
            # Compare current results with baseline
            comparison = manager.compare_with_baseline(current_results)
            
            # Verify comparison executed successfully
            assert 'comparisons' in comparison, "Comparison should contain 'comparisons' key"
            assert 'current_benchmark_id' in comparison
            assert 'baseline_id' in comparison
            assert 'current_kernel' in comparison
            assert 'baseline_kernel' in comparison
            
            # Verify comparisons list exists and is not empty
            comparisons_list = comparison['comparisons']
            assert isinstance(comparisons_list, list)
            assert len(comparisons_list) > 0, "Should have at least one comparison"
            
            # Verify each comparison has required fields
            for comp in comparisons_list:
                assert 'metric_name' in comp
                assert 'current_value' in comp
                assert 'unit' in comp
                assert 'benchmark_type' in comp
                
                # If metric exists in baseline, should have comparison data
                if comp.get('baseline_value') is not None:
                    assert 'change_percent' in comp
                    assert isinstance(comp['change_percent'], (int, float))
    
    @given(results_pair=related_benchmark_results_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_comparison_calculates_change_percent(self, results_pair):
        """Property: Comparison should calculate percentage change for common metrics.
        
        When comparing metrics that exist in both baseline and current results,
        the system should calculate the percentage change.
        """
        baseline_results, current_results = results_pair
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create and store baseline
            baseline = manager.create_baseline(baseline_results)
            manager.store_baseline(baseline)
            
            # Compare
            comparison = manager.compare_with_baseline(current_results)
            
            # Find comparisons with both baseline and current values
            for comp in comparison['comparisons']:
                if comp.get('baseline_value') is not None and comp.get('current_value') is not None:
                    baseline_val = comp['baseline_value']
                    current_val = comp['current_value']
                    change_pct = comp['change_percent']
                    
                    # Verify calculation
                    if baseline_val != 0:
                        expected_change = ((current_val - baseline_val) / baseline_val) * 100
                        assert abs(change_pct - expected_change) < 0.01, \
                            f"Change percent calculation incorrect: expected {expected_change}, got {change_pct}"
    
    @given(
        kernel_version=kernel_version_strategy(),
        results1=benchmark_results_strategy(),
        results2=benchmark_results_strategy()
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_baseline_versioning_by_kernel(self, kernel_version, results1, results2):
        """Property: Baselines should be versioned by kernel version.
        
        Different kernel versions should have separate baselines that don't interfere.
        """
        # Force different kernel versions
        results1.kernel_version = kernel_version
        results2.kernel_version = f"{kernel_version}.1"  # Different version
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create baselines for different versions
            baseline1 = manager.create_baseline(results1)
            baseline2 = manager.create_baseline(results2)
            
            manager.store_baseline(baseline1)
            manager.store_baseline(baseline2)
            
            # Retrieve each baseline
            retrieved1 = manager.retrieve_baseline(results1.kernel_version)
            retrieved2 = manager.retrieve_baseline(results2.kernel_version)
            
            # Both should exist
            assert retrieved1 is not None
            assert retrieved2 is not None
            
            # Should have correct versions
            assert retrieved1.kernel_version == results1.kernel_version
            assert retrieved2.kernel_version == results2.kernel_version
            
            # Should be different baselines
            assert retrieved1.baseline_id != retrieved2.baseline_id
    
    @given(benchmark_results=benchmark_results_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_baseline_update_mechanism(self, benchmark_results: BenchmarkResults):
        """Property: Baselines can be updated with new measurements.
        
        The system should support updating existing baselines with new data.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create initial baseline
            baseline = manager.create_baseline(benchmark_results)
            manager.store_baseline(baseline)
            
            # Create new results for same kernel version
            new_results = BenchmarkResults(
                benchmark_id=f"new_{benchmark_results.benchmark_id}",
                kernel_version=benchmark_results.kernel_version,
                timestamp=datetime.now(),
                metrics=benchmark_results.metrics.copy()
            )
            
            # Update baseline
            updated = manager.update_baseline(
                benchmark_results.kernel_version,
                new_results,
                merge_strategy="replace"
            )
            
            # Verify update occurred
            assert updated is not None
            assert updated.kernel_version == benchmark_results.kernel_version
            assert updated.updated_at > updated.created_at or updated.updated_at == updated.created_at
    
    @given(benchmark_results=benchmark_results_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_retrieve_latest_baseline(self, benchmark_results: BenchmarkResults):
        """Property: Retrieving without baseline_id returns the latest baseline.
        
        When no specific baseline ID is provided, the system should return the
        most recently updated baseline for that kernel version.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create and store baseline
            baseline = manager.create_baseline(benchmark_results)
            manager.store_baseline(baseline)
            
            # Retrieve without specifying ID
            retrieved = manager.retrieve_baseline(benchmark_results.kernel_version)
            
            # Should retrieve the baseline
            assert retrieved is not None
            assert retrieved.kernel_version == benchmark_results.kernel_version
    
    @given(benchmark_results=benchmark_results_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_list_baselines_by_version(self, benchmark_results: BenchmarkResults):
        """Property: System can list all baselines for a kernel version.
        
        The system should be able to enumerate all stored baselines.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create and store baseline
            baseline = manager.create_baseline(benchmark_results)
            manager.store_baseline(baseline)
            
            # List baselines for this version
            baselines = manager.list_baselines(benchmark_results.kernel_version)
            
            # Should find at least one
            assert len(baselines) >= 1
            
            # Should contain our baseline
            baseline_ids = [b['baseline_id'] for b in baselines]
            assert baseline.baseline_id in baseline_ids
    
    @given(benchmark_results=benchmark_results_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_baseline_deletion(self, benchmark_results: BenchmarkResults):
        """Property: Baselines can be deleted.
        
        The system should support removing baselines that are no longer needed.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Create and store baseline
            baseline = manager.create_baseline(benchmark_results)
            manager.store_baseline(baseline)
            
            # Verify it exists
            retrieved = manager.retrieve_baseline(
                baseline.kernel_version,
                baseline.baseline_id
            )
            assert retrieved is not None
            
            # Delete it
            deleted = manager.delete_baseline(
                baseline.kernel_version,
                baseline.baseline_id
            )
            assert deleted is True
            
            # Verify it's gone
            retrieved_after = manager.retrieve_baseline(
                baseline.kernel_version,
                baseline.baseline_id
            )
            assert retrieved_after is None
    
    @given(benchmark_results=benchmark_results_strategy())
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_comparison_handles_missing_baseline(self, benchmark_results: BenchmarkResults):
        """Property: Comparison gracefully handles missing baselines.
        
        When no baseline exists, the system should return an appropriate error response.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BaselineManager(storage_dir=tmpdir)
            
            # Try to compare without creating a baseline
            comparison = manager.compare_with_baseline(benchmark_results)
            
            # Should indicate error
            assert 'error' in comparison or len(comparison.get('comparisons', [])) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
