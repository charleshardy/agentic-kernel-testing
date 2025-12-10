#!/usr/bin/env python3
"""Example demonstrating performance baseline management.

This example shows how to:
1. Create baselines from benchmark results
2. Store and retrieve baselines
3. Compare current results with baselines
4. Update baselines with new measurements
5. Manage baselines across kernel versions
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.performance_monitor import (
    PerformanceMonitor, BenchmarkResults, BenchmarkMetric, BenchmarkType
)
from analysis.baseline_manager import BaselineManager


def create_sample_benchmark_results(kernel_version: str, benchmark_id: str) -> BenchmarkResults:
    """Create sample benchmark results for demonstration."""
    metrics = [
        BenchmarkMetric(
            name="sequential_read_throughput",
            value=500.0,
            unit="MB/s",
            benchmark_type=BenchmarkType.IO_THROUGHPUT
        ),
        BenchmarkMetric(
            name="sequential_write_throughput",
            value=450.0,
            unit="MB/s",
            benchmark_type=BenchmarkType.IO_THROUGHPUT
        ),
        BenchmarkMetric(
            name="syscall_read_latency",
            value=1.5,
            unit="microseconds",
            benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY
        ),
        BenchmarkMetric(
            name="tcp_stream_throughput",
            value=1000.0,
            unit="Mbits/s",
            benchmark_type=BenchmarkType.NETWORK_THROUGHPUT
        ),
        BenchmarkMetric(
            name="memory_bandwidth",
            value=5000.0,
            unit="MB/s",
            benchmark_type=BenchmarkType.CUSTOM
        )
    ]
    
    return BenchmarkResults(
        benchmark_id=benchmark_id,
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=metrics
    )


def example_1_create_and_store_baseline():
    """Example 1: Create and store a baseline."""
    print("=" * 70)
    print("Example 1: Creating and Storing Baseline")
    print("=" * 70)
    
    # Create baseline manager
    manager = BaselineManager(storage_dir="./example_baseline_data")
    
    # Create sample benchmark results
    results = create_sample_benchmark_results("5.10.0", "bench_001")
    
    print(f"\n📊 Benchmark Results:")
    print(f"  Kernel Version: {results.kernel_version}")
    print(f"  Benchmark ID: {results.benchmark_id}")
    print(f"  Number of Metrics: {len(results.metrics)}")
    
    # Create baseline from results
    baseline = manager.create_baseline(results)
    
    print(f"\n✅ Baseline Created:")
    print(f"  Baseline ID: {baseline.baseline_id}")
    print(f"  Kernel Version: {baseline.kernel_version}")
    print(f"  Created At: {baseline.created_at}")
    
    # Store baseline
    stored_path = manager.store_baseline(baseline)
    
    print(f"\n💾 Baseline Stored:")
    print(f"  Path: {stored_path}")
    
    return baseline


def example_2_retrieve_baseline(baseline_id: str):
    """Example 2: Retrieve a stored baseline."""
    print("\n" + "=" * 70)
    print("Example 2: Retrieving Baseline")
    print("=" * 70)
    
    manager = BaselineManager(storage_dir="./example_baseline_data")
    
    # Retrieve specific baseline
    baseline = manager.retrieve_baseline("5.10.0", baseline_id)
    
    if baseline:
        print(f"\n✅ Baseline Retrieved:")
        print(f"  Baseline ID: {baseline.baseline_id}")
        print(f"  Kernel Version: {baseline.kernel_version}")
        print(f"  Number of Metrics: {len(baseline.metrics)}")
        print(f"\n  Metrics:")
        for metric in baseline.metrics:
            print(f"    - {metric.name}: {metric.value} {metric.unit}")
    else:
        print("\n❌ Baseline not found")
    
    return baseline


def example_3_compare_with_baseline():
    """Example 3: Compare current results with baseline."""
    print("\n" + "=" * 70)
    print("Example 3: Comparing with Baseline")
    print("=" * 70)
    
    manager = BaselineManager(storage_dir="./example_baseline_data")
    
    # Create new results with some performance changes
    new_results = BenchmarkResults(
        benchmark_id="bench_002",
        kernel_version="5.10.0",
        timestamp=datetime.now(),
        metrics=[
            BenchmarkMetric(
                name="sequential_read_throughput",
                value=550.0,  # 10% improvement
                unit="MB/s",
                benchmark_type=BenchmarkType.IO_THROUGHPUT
            ),
            BenchmarkMetric(
                name="sequential_write_throughput",
                value=405.0,  # 10% regression
                unit="MB/s",
                benchmark_type=BenchmarkType.IO_THROUGHPUT
            ),
            BenchmarkMetric(
                name="syscall_read_latency",
                value=1.65,  # 10% regression (higher latency is worse)
                unit="microseconds",
                benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY
            ),
            BenchmarkMetric(
                name="tcp_stream_throughput",
                value=1000.0,  # No change
                unit="Mbits/s",
                benchmark_type=BenchmarkType.NETWORK_THROUGHPUT
            ),
            BenchmarkMetric(
                name="memory_bandwidth",
                value=5500.0,  # 10% improvement
                unit="MB/s",
                benchmark_type=BenchmarkType.CUSTOM
            )
        ]
    )
    
    print(f"\n📊 New Benchmark Results:")
    print(f"  Kernel Version: {new_results.kernel_version}")
    print(f"  Benchmark ID: {new_results.benchmark_id}")
    
    # Compare with baseline
    comparison = manager.compare_with_baseline(new_results)
    
    print(f"\n📈 Comparison Results:")
    print(f"  Baseline ID: {comparison['baseline_id']}")
    print(f"  Current Benchmark: {comparison['current_benchmark_id']}")
    print(f"\n  Metric Comparisons:")
    
    for comp in comparison['comparisons']:
        metric_name = comp['metric_name']
        baseline_val = comp.get('baseline_value')
        current_val = comp['current_value']
        change_pct = comp.get('change_percent')
        
        if baseline_val is not None and change_pct is not None:
            direction = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            print(f"    {direction} {metric_name}:")
            print(f"       Baseline: {baseline_val:.2f} {comp['unit']}")
            print(f"       Current:  {current_val:.2f} {comp['unit']}")
            print(f"       Change:   {change_pct:+.2f}%")
        else:
            print(f"    ℹ️  {metric_name}: {current_val:.2f} {comp['unit']} (not in baseline)")


def example_4_update_baseline():
    """Example 4: Update baseline with new measurements."""
    print("\n" + "=" * 70)
    print("Example 4: Updating Baseline")
    print("=" * 70)
    
    manager = BaselineManager(storage_dir="./example_baseline_data")
    
    # Create new results
    new_results = create_sample_benchmark_results("5.10.0", "bench_003")
    
    # Modify some values
    new_results.metrics[0].value = 525.0  # Average between 500 and 550
    
    print(f"\n📊 New Measurements:")
    print(f"  Benchmark ID: {new_results.benchmark_id}")
    
    # Update baseline using average strategy
    updated = manager.update_baseline(
        "5.10.0",
        new_results,
        merge_strategy="average"
    )
    
    print(f"\n✅ Baseline Updated:")
    print(f"  Baseline ID: {updated.baseline_id}")
    print(f"  Updated At: {updated.updated_at}")
    print(f"  Merge Strategy: average")
    
    # Store updated baseline
    manager.store_baseline(updated)
    print(f"\n💾 Updated baseline saved")


def example_5_manage_multiple_versions():
    """Example 5: Manage baselines across kernel versions."""
    print("\n" + "=" * 70)
    print("Example 5: Managing Multiple Kernel Versions")
    print("=" * 70)
    
    manager = BaselineManager(storage_dir="./example_baseline_data")
    
    # Create baselines for different kernel versions
    versions = ["5.10.0", "5.15.0", "6.0.0"]
    
    for version in versions:
        results = create_sample_benchmark_results(version, f"bench_{version}")
        baseline = manager.create_baseline(results)
        manager.store_baseline(baseline)
        print(f"  ✅ Created baseline for kernel {version}")
    
    # List all baseline versions
    print(f"\n📋 Available Kernel Versions:")
    all_versions = manager.get_baseline_versions()
    for version in all_versions:
        baselines = manager.list_baselines(version)
        print(f"  - {version}: {len(baselines)} baseline(s)")
    
    # Retrieve latest baseline for each version
    print(f"\n📊 Latest Baselines:")
    for version in all_versions:
        baseline = manager.retrieve_baseline(version)
        if baseline:
            print(f"  - {version}: {baseline.baseline_id}")
            print(f"    Created: {baseline.created_at}")
            print(f"    Metrics: {len(baseline.metrics)}")


def example_6_detect_regressions():
    """Example 6: Detect performance regressions using baselines."""
    print("\n" + "=" * 70)
    print("Example 6: Detecting Performance Regressions")
    print("=" * 70)
    
    manager = BaselineManager(storage_dir="./example_baseline_data")
    monitor = PerformanceMonitor()
    
    # Create results with a significant regression
    regressed_results = BenchmarkResults(
        benchmark_id="bench_regressed",
        kernel_version="5.10.0",
        timestamp=datetime.now(),
        metrics=[
            BenchmarkMetric(
                name="sequential_read_throughput",
                value=400.0,  # 20% regression
                unit="MB/s",
                benchmark_type=BenchmarkType.IO_THROUGHPUT
            ),
            BenchmarkMetric(
                name="syscall_read_latency",
                value=2.0,  # 33% regression (higher is worse)
                unit="microseconds",
                benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY
            )
        ]
    )
    
    # Compare with baseline
    comparison = manager.compare_with_baseline(regressed_results)
    
    # Detect regressions (10% threshold)
    regressions = monitor.detect_regressions(comparison, threshold=0.1)
    
    print(f"\n⚠️  Performance Regressions Detected:")
    print(f"  Threshold: 10%")
    print(f"  Found: {len(regressions)} regression(s)")
    
    for regression in regressions:
        print(f"\n  🔴 {regression['metric_name']}:")
        print(f"     Baseline: {regression['baseline_value']:.2f} {regression['unit']}")
        print(f"     Current:  {regression['current_value']:.2f} {regression['unit']}")
        print(f"     Change:   {regression['change_percent']:+.2f}%")
        print(f"     Severity: {regression['severity'].upper()}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Performance Baseline Management Examples")
    print("=" * 70)
    
    # Example 1: Create and store baseline
    baseline = example_1_create_and_store_baseline()
    
    # Example 2: Retrieve baseline
    example_2_retrieve_baseline(baseline.baseline_id)
    
    # Example 3: Compare with baseline
    example_3_compare_with_baseline()
    
    # Example 4: Update baseline
    example_4_update_baseline()
    
    # Example 5: Manage multiple versions
    example_5_manage_multiple_versions()
    
    # Example 6: Detect regressions
    example_6_detect_regressions()
    
    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70)
    print("\nBaseline data stored in: ./example_baseline_data/")
    print("You can inspect the JSON files to see the stored baselines.")


if __name__ == "__main__":
    main()
