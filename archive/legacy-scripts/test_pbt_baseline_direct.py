#!/usr/bin/env python3
"""Direct test of baseline comparison property."""

import sys
sys.path.insert(0, '.')

import tempfile
from datetime import datetime
from hypothesis import given, strategies as st, settings

from analysis.performance_monitor import BenchmarkResults, BenchmarkMetric, BenchmarkType
from analysis.baseline_manager import BaselineManager

# Strategy for generating related benchmark results
@st.composite
def related_benchmark_results_strategy(draw):
    """Generate two related benchmark results with some common metrics."""
    kernel_version = "5.10.0"
    
    # Generate common metric names
    common_names = ["metric_1", "metric_2", "metric_3"]
    
    # Create baseline metrics
    baseline_metrics = []
    for name in common_names:
        value = draw(st.floats(min_value=10.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
        baseline_metrics.append(BenchmarkMetric(
            name=name,
            value=value,
            unit="MB/s",
            benchmark_type=BenchmarkType.IO_THROUGHPUT
        ))
    
    # Create current metrics (with some variation)
    current_metrics = []
    for baseline_metric in baseline_metrics:
        variation = draw(st.floats(min_value=0.5, max_value=1.5))
        new_value = baseline_metric.value * variation
        
        current_metrics.append(BenchmarkMetric(
            name=baseline_metric.name,
            value=new_value,
            unit=baseline_metric.unit,
            benchmark_type=baseline_metric.benchmark_type
        ))
    
    baseline_results = BenchmarkResults(
        benchmark_id="baseline_001",
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=baseline_metrics
    )
    
    current_results = BenchmarkResults(
        benchmark_id="current_001",
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=current_metrics
    )
    
    return baseline_results, current_results


@given(results_pair=related_benchmark_results_strategy())
@settings(max_examples=100, deadline=None)
def test_baseline_comparison_execution(results_pair):
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


if __name__ == "__main__":
    print("Running baseline comparison property test...")
    print("Testing with 100 examples...")
    
    try:
        test_baseline_comparison_execution()
        print("\n✅ Property test passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Property test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
