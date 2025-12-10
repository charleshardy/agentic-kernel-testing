"""Example demonstrating the performance monitoring system.

This example shows how to:
- Run performance benchmarks (LMBench, FIO, Netperf)
- Collect benchmark results
- Compare results with baselines
- Detect performance regressions
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.performance_monitor import (
    PerformanceMonitor, BenchmarkResults, BenchmarkMetric,
    BenchmarkType, BenchmarkCollector
)
from datetime import datetime


def demonstrate_performance_monitoring():
    """Demonstrate the performance monitoring system."""
    
    print("=" * 80)
    print("Performance Monitoring System Demo")
    print("=" * 80)
    print()
    
    # Initialize performance monitor
    monitor = PerformanceMonitor(storage_dir="./demo_benchmark_data")
    
    print("1. Creating mock benchmark results for baseline kernel...")
    print("-" * 80)
    
    # Create baseline results (simulating kernel 5.10.0)
    baseline_metrics = [
        BenchmarkMetric(
            name="syscall_read_latency",
            value=1.2,
            unit="microseconds",
            benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY,
            metadata={'syscall': 'read'}
        ),
        BenchmarkMetric(
            name="sequential_read_throughput",
            value=500.0,
            unit="MB/s",
            benchmark_type=BenchmarkType.IO_THROUGHPUT,
            metadata={'operation': 'sequential_read'}
        ),
        BenchmarkMetric(
            name="tcp_stream_throughput",
            value=950.0,
            unit="Mbits/s",
            benchmark_type=BenchmarkType.NETWORK_THROUGHPUT,
            metadata={'protocol': 'TCP'}
        ),
        BenchmarkMetric(
            name="memory_bandwidth",
            value=5000.0,
            unit="MB/s",
            benchmark_type=BenchmarkType.CUSTOM,
            metadata={'test': 'memory_copy'}
        )
    ]
    
    baseline_results = BenchmarkResults(
        benchmark_id="baseline_5_10_0",
        kernel_version="5.10.0",
        timestamp=datetime.now(),
        metrics=baseline_metrics,
        environment={'suite': 'full'},
        metadata={'description': 'Baseline benchmark'}
    )
    
    # Store baseline
    monitor.collector.store_results(baseline_results)
    
    print(f"Baseline kernel: {baseline_results.kernel_version}")
    print(f"Metrics collected: {len(baseline_results.metrics)}")
    for metric in baseline_results.metrics:
        print(f"  - {metric.name}: {metric.value} {metric.unit}")
    print()
    
    print("2. Creating mock benchmark results for current kernel...")
    print("-" * 80)
    
    # Create current results (simulating kernel 5.11.0 with some regressions)
    current_metrics = [
        BenchmarkMetric(
            name="syscall_read_latency",
            value=1.5,  # 25% slower (regression)
            unit="microseconds",
            benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY,
            metadata={'syscall': 'read'}
        ),
        BenchmarkMetric(
            name="sequential_read_throughput",
            value=350.0,  # 30% slower (regression)
            unit="MB/s",
            benchmark_type=BenchmarkType.IO_THROUGHPUT,
            metadata={'operation': 'sequential_read'}
        ),
        BenchmarkMetric(
            name="tcp_stream_throughput",
            value=980.0,  # 3% faster (improvement)
            unit="Mbits/s",
            benchmark_type=BenchmarkType.NETWORK_THROUGHPUT,
            metadata={'protocol': 'TCP'}
        ),
        BenchmarkMetric(
            name="memory_bandwidth",
            value=5100.0,  # 2% faster (improvement)
            unit="MB/s",
            benchmark_type=BenchmarkType.CUSTOM,
            metadata={'test': 'memory_copy'}
        )
    ]
    
    current_results = BenchmarkResults(
        benchmark_id="current_5_11_0",
        kernel_version="5.11.0",
        timestamp=datetime.now(),
        metrics=current_metrics,
        environment={'suite': 'full'},
        metadata={'description': 'Current kernel benchmark'}
    )
    
    # Store current
    monitor.collector.store_results(current_results)
    
    print(f"Current kernel: {current_results.kernel_version}")
    print(f"Metrics collected: {len(current_results.metrics)}")
    for metric in current_results.metrics:
        print(f"  - {metric.name}: {metric.value} {metric.unit}")
    print()
    
    print("3. Comparing current results with baseline...")
    print("-" * 80)
    
    # Compare results
    comparison = monitor.compare_with_baseline(
        current_id="current_5_11_0",
        baseline_id="baseline_5_10_0"
    )
    
    print(f"Baseline: {comparison['baseline_kernel']}")
    print(f"Current:  {comparison['current_kernel']}")
    print()
    print("Metric Comparisons:")
    print()
    
    for comp in comparison['comparisons']:
        change = comp['change_percent']
        direction = "↑" if change > 0 else "↓"
        color = "worse" if (
            ('latency' in comp['metric_name'].lower() and change > 0) or
            ('throughput' in comp['metric_name'].lower() and change < 0) or
            ('bandwidth' in comp['metric_name'].lower() and change < 0)
        ) else "better"
        
        print(f"  {comp['metric_name']}:")
        print(f"    Baseline: {comp['baseline_value']:.2f} {comp['unit']}")
        print(f"    Current:  {comp['current_value']:.2f} {comp['unit']}")
        print(f"    Change:   {direction} {abs(change):.1f}% ({color})")
        print()
    
    print("4. Detecting performance regressions (threshold: 10%)...")
    print("-" * 80)
    
    # Detect regressions
    regressions = monitor.detect_regressions(comparison, threshold=0.10)
    
    if regressions:
        print(f"Found {len(regressions)} performance regression(s):")
        print()
        for reg in regressions:
            print(f"  ⚠️  {reg['metric_name']} [{reg['severity'].upper()}]")
            print(f"      Baseline: {reg['baseline_value']:.2f} {reg['unit']}")
            print(f"      Current:  {reg['current_value']:.2f} {reg['unit']}")
            print(f"      Change:   {reg['change_percent']:.1f}%")
            print()
    else:
        print("No performance regressions detected.")
        print()
    
    print("5. Listing all stored benchmark results...")
    print("-" * 80)
    
    # List all results
    all_results = monitor.collector.list_results()
    print(f"Total benchmark results stored: {len(all_results)}")
    for result_id in all_results:
        result = monitor.collector.retrieve_results(result_id)
        if result:
            print(f"  - {result_id}: {result.kernel_version} ({len(result.metrics)} metrics)")
    print()
    
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✓ Integrated LMBench for system call latency")
    print("  ✓ Integrated FIO for I/O performance benchmarks")
    print("  ✓ Integrated Netperf for network throughput")
    print("  ✓ Created custom microbenchmark runner")
    print("  ✓ Built benchmark result collector")
    print("  ✓ Implemented baseline comparison")
    print("  ✓ Implemented regression detection")
    print()


if __name__ == "__main__":
    demonstrate_performance_monitoring()
