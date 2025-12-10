#!/usr/bin/env python3
"""
Performance Profiling Example

This example demonstrates how to use the performance profiling system
to profile kernel workloads and analyze performance regressions.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.performance_monitor import (
    PerformanceMonitor, 
    PerformanceProfiler,
    ProfilingData,
    BenchmarkResults
)


def create_sample_workload():
    """Create a sample workload script for profiling."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write("""#!/bin/bash
# Sample I/O intensive workload
echo "Starting I/O workload..."
dd if=/dev/zero of=/tmp/test_file bs=1M count=50 2>/dev/null
sync
dd if=/tmp/test_file of=/dev/null bs=1M 2>/dev/null
rm -f /tmp/test_file
echo "Workload completed"
""")
        script_path = f.name
    
    os.chmod(script_path, 0o755)
    return script_path


def demonstrate_performance_profiling():
    """Demonstrate performance profiling capabilities."""
    print("=" * 70)
    print("Performance Profiling Example")
    print("=" * 70)
    
    # Initialize performance monitor
    monitor = PerformanceMonitor()
    profiler = PerformanceProfiler()
    
    print("\n1. Running benchmarks with profiling enabled...")
    
    # Run benchmarks with profiling
    results = monitor.run_benchmarks(
        kernel_image="/boot/vmlinuz-5.15.0",
        benchmark_suite="io",
        enable_profiling=True
    )
    
    print(f"   Benchmark ID: {results.benchmark_id}")
    print(f"   Kernel Version: {results.kernel_version}")
    print(f"   Metrics Collected: {len(results.metrics)}")
    
    if results.profiling_data:
        print(f"   Profiling Data Available: Yes")
        print(f"   Profile ID: {results.profiling_data.profile_id}")
        print(f"   Duration: {results.profiling_data.duration_seconds:.2f}s")
        print(f"   Samples: {results.profiling_data.samples}")
        print(f"   Hotspots: {len(results.profiling_data.hotspots)}")
    else:
        print("   Profiling Data Available: No")
    
    print("\n2. Demonstrating direct kernel profiling...")
    
    # Create a sample workload
    workload_script = create_sample_workload()
    
    try:
        # Profile the workload directly
        profiling_data = profiler.profile_command([workload_script], duration=10)
        
        print(f"   Profile ID: {profiling_data.profile_id}")
        print(f"   Command: {profiling_data.command}")
        print(f"   Duration: {profiling_data.duration_seconds:.2f}s")
        print(f"   Samples: {profiling_data.samples}")
        print(f"   Events: {', '.join(profiling_data.events)}")
        
        # Identify hotspots
        hotspots = profiler.identify_hotspots(profiling_data, threshold_percent=5.0)
        
        print(f"\n   Hotspots Identified: {len(hotspots)}")
        for i, hotspot in enumerate(hotspots[:3], 1):  # Show top 3
            print(f"     {i}. {hotspot['symbol']}: {hotspot['overhead_percent']:.1f}% ({hotspot['severity']})")
            print(f"        Recommendation: {hotspot['recommendation']}")
        
        # Generate profiling report
        report = monitor.generate_profiling_report(profiling_data)
        
        print(f"\n   Profiling Report Summary:")
        print(f"     Total Hotspots: {report['hotspots_count']}")
        print(f"     Critical Hotspots: {len(report['critical_hotspots'])}")
        print(f"     High Priority Hotspots: {len(report['high_hotspots'])}")
        print(f"     Analysis: {report['analysis_summary']}")
        
        if report['flamegraph_path']:
            print(f"     Flamegraph: {report['flamegraph_path']}")
        
        print(f"\n   Top Recommendations:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"     {i}. {rec}")
    
    finally:
        # Cleanup
        try:
            os.unlink(workload_script)
        except OSError:
            pass
    
    print("\n3. Demonstrating regression analysis with profiling...")
    
    # Simulate regression detection with profiling data
    comparison_data = {
        'current_id': 'bench_current',
        'baseline_id': 'bench_baseline',
        'current_kernel': '5.15.0',
        'baseline_kernel': '5.14.0',
        'comparisons': [
            {
                'metric_name': 'sequential_write_throughput',
                'baseline_value': 500.0,
                'current_value': 350.0,
                'change_percent': -30.0,
                'unit': 'MB/s',
                'benchmark_type': 'throughput'
            },
            {
                'metric_name': 'syscall_read_latency',
                'baseline_value': 10.0,
                'current_value': 15.0,
                'change_percent': 50.0,
                'unit': 'microseconds',
                'benchmark_type': 'latency'
            }
        ]
    }
    
    regressions = monitor.detect_regressions(comparison_data, threshold=0.1)
    
    print(f"   Regressions Detected: {len(regressions)}")
    
    for regression in regressions:
        print(f"\n   Regression: {regression['metric_name']}")
        print(f"     Baseline: {regression['baseline_value']} {regression['unit']}")
        print(f"     Current: {regression['current_value']} {regression['unit']}")
        print(f"     Change: {regression['change_percent']:.1f}%")
        print(f"     Severity: {regression['severity']}")
        
        if 'profiling_analysis' in regression:
            analysis = regression['profiling_analysis']
            print(f"     Profiling Analysis Available: {analysis['hotspots_identified']}")
            if analysis['hotspots_identified']:
                print(f"       Top Hotspot: {analysis['top_hotspot']} ({analysis['hotspot_overhead']:.1f}%)")
                print(f"       Recommendation: {analysis['recommendation']}")
    
    print("\n4. Performance profiling capabilities summary:")
    print("   ✓ Integrated perf tool for kernel profiling")
    print("   ✓ Flamegraph generation (when tools available)")
    print("   ✓ Hotspot identification and analysis")
    print("   ✓ Profiling data analysis and recommendations")
    print("   ✓ Regression correlation with profiling data")
    print("   ✓ Comprehensive profiling reports")
    
    print("\n" + "=" * 70)
    print("Performance profiling implementation complete!")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_performance_profiling()