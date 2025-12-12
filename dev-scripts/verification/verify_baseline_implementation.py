#!/usr/bin/env python3
"""Verify baseline management implementation."""

import tempfile
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '.')

from analysis.performance_monitor import BenchmarkResults, BenchmarkMetric, BenchmarkType
from analysis.baseline_manager import BaselineManager, PerformanceBaseline

def test_basic_functionality():
    """Test basic baseline management functionality."""
    print("Testing baseline management implementation...")
    
    # Create test data
    metrics = [
        BenchmarkMetric(
            name="test_metric_1",
            value=100.0,
            unit="MB/s",
            benchmark_type=BenchmarkType.IO_THROUGHPUT
        ),
        BenchmarkMetric(
            name="test_metric_2",
            value=50.0,
            unit="microseconds",
            benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY
        )
    ]
    
    benchmark_results = BenchmarkResults(
        benchmark_id="test_bench_001",
        kernel_version="5.10.0",
        timestamp=datetime.now(),
        metrics=metrics
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = BaselineManager(storage_dir=tmpdir)
        
        # Test 1: Create baseline
        print("✓ Test 1: Creating baseline...")
        baseline = manager.create_baseline(benchmark_results)
        assert baseline.kernel_version == "5.10.0"
        assert len(baseline.metrics) == 2
        print("  ✓ Baseline created successfully")
        
        # Test 2: Store baseline
        print("✓ Test 2: Storing baseline...")
        stored_path = manager.store_baseline(baseline)
        assert stored_path is not None
        print(f"  ✓ Baseline stored at: {stored_path}")
        
        # Test 3: Retrieve baseline
        print("✓ Test 3: Retrieving baseline...")
        retrieved = manager.retrieve_baseline("5.10.0", baseline.baseline_id)
        assert retrieved is not None
        assert retrieved.kernel_version == "5.10.0"
        assert len(retrieved.metrics) == 2
        print("  ✓ Baseline retrieved successfully")
        
        # Test 4: Compare with baseline
        print("✓ Test 4: Comparing with baseline...")
        new_metrics = [
            BenchmarkMetric(
                name="test_metric_1",
                value=110.0,  # 10% increase
                unit="MB/s",
                benchmark_type=BenchmarkType.IO_THROUGHPUT
            ),
            BenchmarkMetric(
                name="test_metric_2",
                value=55.0,  # 10% increase
                unit="microseconds",
                benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY
            )
        ]
        
        new_results = BenchmarkResults(
            benchmark_id="test_bench_002",
            kernel_version="5.10.0",
            timestamp=datetime.now(),
            metrics=new_metrics
        )
        
        comparison = manager.compare_with_baseline(new_results)
        assert 'comparisons' in comparison
        assert len(comparison['comparisons']) == 2
        print("  ✓ Comparison executed successfully")
        
        # Verify change percentages
        for comp in comparison['comparisons']:
            if comp['metric_name'] == 'test_metric_1':
                # Should be ~10% increase
                assert abs(comp['change_percent'] - 10.0) < 0.1
                print(f"  ✓ Metric 1 change: {comp['change_percent']:.2f}%")
            elif comp['metric_name'] == 'test_metric_2':
                # Should be ~10% increase
                assert abs(comp['change_percent'] - 10.0) < 0.1
                print(f"  ✓ Metric 2 change: {comp['change_percent']:.2f}%")
        
        # Test 5: Update baseline
        print("✓ Test 5: Updating baseline...")
        updated = manager.update_baseline("5.10.0", new_results, merge_strategy="replace")
        assert updated is not None
        assert len(updated.metrics) == 2
        print("  ✓ Baseline updated successfully")
        
        # Test 6: List baselines
        print("✓ Test 6: Listing baselines...")
        baselines = manager.list_baselines("5.10.0")
        assert len(baselines) >= 1
        print(f"  ✓ Found {len(baselines)} baseline(s)")
        
        # Test 7: Get baseline versions
        print("✓ Test 7: Getting baseline versions...")
        versions = manager.get_baseline_versions()
        assert "5.10.0" in versions
        print(f"  ✓ Found versions: {versions}")
        
        # Test 8: Delete baseline
        print("✓ Test 8: Deleting baseline...")
        deleted = manager.delete_baseline("5.10.0", baseline.baseline_id)
        assert deleted is True
        print("  ✓ Baseline deleted successfully")
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_basic_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
