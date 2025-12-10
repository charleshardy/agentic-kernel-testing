#!/usr/bin/env python3
"""Example demonstrating performance trend reporting functionality.

This example shows how to:
1. Store performance snapshots over time
2. Analyze performance trends and detect regressions
3. Generate performance forecasts
4. Create interactive performance dashboards
5. Export performance data for analysis
"""

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.performance_trend_tracker import PerformanceTrendTracker, TrendDirection
from analysis.performance_dashboard import PerformanceDashboard, DashboardConfig
from analysis.performance_monitor import (
    BenchmarkResults, BenchmarkMetric, BenchmarkType
)


def create_sample_benchmark_results(benchmark_id: str, kernel_version: str, 
                                   base_latency: float = 10.0, 
                                   base_throughput: float = 1000.0) -> BenchmarkResults:
    """Create sample benchmark results for demonstration."""
    metrics = [
        BenchmarkMetric(
            name="syscall_read_latency",
            value=base_latency,
            unit="microseconds",
            benchmark_type=BenchmarkType.SYSTEM_CALL_LATENCY,
            metadata={"syscall": "read"}
        ),
        BenchmarkMetric(
            name="io_sequential_throughput",
            value=base_throughput,
            unit="MB/s",
            benchmark_type=BenchmarkType.IO_THROUGHPUT,
            metadata={"operation": "sequential_read"}
        ),
        BenchmarkMetric(
            name="network_tcp_bandwidth",
            value=base_throughput * 8,  # Convert to Mbits/s
            unit="Mbits/s",
            benchmark_type=BenchmarkType.NETWORK_THROUGHPUT,
            metadata={"protocol": "TCP"}
        ),
        BenchmarkMetric(
            name="memory_copy_bandwidth",
            value=base_throughput * 5,
            unit="MB/s",
            benchmark_type=BenchmarkType.CUSTOM,
            metadata={"test": "memory_copy"}
        )
    ]
    
    return BenchmarkResults(
        benchmark_id=benchmark_id,
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=metrics,
        environment={"arch": "x86_64", "cpu": "Intel i7"},
        metadata={"example": True}
    )


def main():
    """Demonstrate performance trend reporting."""
    print("=" * 80)
    print("PERFORMANCE TREND REPORTING EXAMPLE")
    print("=" * 80)
    
    # Create a temporary directory for this example
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nUsing temporary directory: {tmpdir}")
        
        # Initialize performance trend tracker
        tracker = PerformanceTrendTracker(storage_dir=tmpdir)
        
        print("\n1. Storing Performance Snapshots")
        print("-" * 80)
        
        # Simulate a series of builds with varying performance
        base_time = datetime.now() - timedelta(days=30)
        snapshots_data = [
            # Week 1: Good performance
            ("build_001", "6.1.0", 8.5, 1200.0, "main", "abc123"),
            ("build_002", "6.1.1", 8.3, 1250.0, "main", "def456"),
            ("build_003", "6.1.2", 8.1, 1300.0, "main", "ghi789"),
            
            # Week 2: Performance regression introduced
            ("build_004", "6.2.0", 12.5, 950.0, "main", "jkl012"),  # Regression!
            ("build_005", "6.2.1", 13.2, 920.0, "main", "mno345"),  # Worse
            
            # Week 3: Performance partially recovered
            ("build_006", "6.2.2", 10.8, 1100.0, "main", "pqr678"),
            ("build_007", "6.2.3", 9.9, 1180.0, "main", "stu901"),
            
            # Week 4: Performance improving
            ("build_008", "6.3.0", 8.8, 1320.0, "main", "vwx234"),
            ("build_009", "6.3.1", 8.2, 1380.0, "main", "yza567"),
            ("build_010", "6.3.2", 7.9, 1420.0, "main", "bcd890"),  # Best yet
        ]
        
        stored_snapshots = []
        for i, (build_id, kernel_ver, latency, throughput, branch, commit) in enumerate(snapshots_data):
            # Create timestamp for each build (spread over 30 days)
            timestamp = base_time + timedelta(days=i * 3)
            
            # Create benchmark results
            results = create_sample_benchmark_results(build_id, kernel_ver, latency, throughput)
            results.timestamp = timestamp
            
            # Store snapshot
            snapshot = tracker.store_snapshot(
                results,
                commit_hash=commit,
                branch=branch,
                build_id=build_id,
                metadata={"week": i // 3 + 1}
            )
            stored_snapshots.append(snapshot)
            
            print(f"  Stored {build_id} ({kernel_ver}): "
                  f"latency={latency:.1f}μs, throughput={throughput:.0f}MB/s")
        
        print(f"\n  ✓ Stored {len(stored_snapshots)} performance snapshots")
        
        # Analyze trends
        print("\n2. Analyzing Performance Trends")
        print("-" * 80)
        
        analysis = tracker.analyze_trend()
        
        print(f"  Overall Trend Direction: {analysis.trend_direction.value.upper()}")
        print(f"  Number of Snapshots: {analysis.num_snapshots}")
        print(f"  Time Span: {analysis.time_span_days:.1f} days")
        print(f"  Metrics Analyzed: {len(analysis.metric_trends)}")
        
        # Show individual metric trends
        print("\n  Metric Trends:")
        for metric_name, trend_data in analysis.metric_trends.items():
            direction = trend_data['direction']
            change = trend_data['percent_change']
            print(f"    - {metric_name}: {direction} ({change:+.1f}%)")
        
        # Detect regressions
        print("\n3. Performance Regressions Detected")
        print("-" * 80)
        
        if analysis.regressions:
            print(f"  Found {len(analysis.regressions)} regressions:")
            for reg in analysis.regressions:
                print(f"    - {reg.metric_name}: "
                      f"{reg.previous_value:.2f} → {reg.current_value:.2f} "
                      f"({reg.change_percent:+.1f}%, {reg.severity.value})")
                if reg.commit_hash:
                    print(f"      at commit {reg.commit_hash[:7]}")
        else:
            print("  ✓ No regressions detected")
        
        # Show forecast
        print("\n4. Performance Forecast")
        print("-" * 80)
        
        if analysis.forecast:
            forecast_data = analysis.forecast
            print(f"  Forecast Horizon: {forecast_data['forecast_horizon_days']} days")
            print(f"  Methodology: {forecast_data['methodology']}")
            print("\n  Predictions:")
            
            for metric_name, forecast in forecast_data['forecasts'].items():
                current = forecast['current_value']
                predicted = forecast['forecast_value']
                change = forecast['forecast_change_percent']
                confidence = forecast['confidence']
                
                print(f"    - {metric_name}: "
                      f"{current:.2f} → {predicted:.2f} "
                      f"({change:+.1f}%, confidence: {confidence})")
        else:
            print("  No forecast available (insufficient data)")
        
        # Generate visualization
        print("\n5. Generating Trend Visualization")
        print("-" * 80)
        
        viz = tracker.generate_trend_visualization()
        print("  Text-based visualization:")
        print(viz)
        
        # Create performance dashboard
        print("\n6. Creating Performance Dashboard")
        print("-" * 80)
        
        dashboard_dir = Path(tmpdir) / "dashboard"
        dashboard = PerformanceDashboard(tracker, output_dir=str(dashboard_dir))
        
        config = DashboardConfig(
            title="Kernel Performance Dashboard",
            show_forecast=True,
            show_regressions=True,
            refresh_interval=300
        )
        
        dashboard_path = dashboard.generate_dashboard(config=config, days=30)
        print(f"  ✓ Generated dashboard: {dashboard_path}")
        
        # List generated files
        dashboard_files = list(dashboard_dir.glob("*"))
        print(f"  Dashboard files created:")
        for file_path in sorted(dashboard_files):
            size = file_path.stat().st_size
            print(f"    - {file_path.name} ({size:,} bytes)")
        
        # Export data
        print("\n7. Exporting Performance Data")
        print("-" * 80)
        
        export_path = dashboard.generate_json_export(days=30)
        export_size = Path(export_path).stat().st_size
        print(f"  ✓ Exported data to: {Path(export_path).name}")
        print(f"  Export size: {export_size:,} bytes")
        
        # Show some export statistics
        import json
        with open(export_path, 'r') as f:
            export_data = json.load(f)
        
        print(f"  Snapshots exported: {export_data['snapshots_count']}")
        print(f"  Analysis included: {'Yes' if export_data['analysis'] else 'No'}")
        
        # Demonstrate filtering
        print("\n8. Filtering and Querying")
        print("-" * 80)
        
        # Get history for specific branch
        main_snapshots = tracker.get_history(branch="main")
        print(f"  Snapshots on 'main' branch: {len(main_snapshots)}")
        
        # Get recent history
        recent_snapshots = tracker.get_history(limit=5)
        print(f"  Most recent 5 snapshots: {len(recent_snapshots)}")
        
        # Get history for specific metric
        latency_history = tracker.get_metric_history("syscall_read_latency")
        print(f"  Syscall latency history points: {len(latency_history)}")
        
        if latency_history:
            first_time, first_val = latency_history[0]
            last_time, last_val = latency_history[-1]
            print(f"    First: {first_val:.2f}μs at {first_time[:19]}")
            print(f"    Last:  {last_val:.2f}μs at {last_time[:19]}")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("Performance trend reporting provides:")
        print("  • Automated storage and tracking of performance metrics over time")
        print("  • Intelligent trend analysis with regression detection")
        print("  • Performance forecasting using statistical models")
        print("  • Interactive HTML dashboards for visualization")
        print("  • Flexible filtering and querying capabilities")
        print("  • JSON export for integration with other tools")
        print("\nThis enables continuous performance monitoring and early")
        print("detection of performance regressions in kernel development.")


if __name__ == "__main__":
    main()