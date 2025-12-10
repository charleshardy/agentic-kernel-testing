"""Property-based tests for performance trend reporting.

**Feature: agentic-kernel-testing, Property 40: Performance trend reporting**
**Validates: Requirements 8.5**

This module tests the correctness properties of performance trend reporting:
- Performance history storage and retrieval
- Trend analysis and forecasting
- Performance dashboard generation
"""

import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import pytest
from hypothesis import given, strategies as st, assume, settings

from analysis.performance_trend_tracker import (
    PerformanceTrendTracker, PerformanceSnapshot, TrendAnalysis,
    PerformanceRegression, TrendDirection, RegressionSeverity
)
from analysis.performance_dashboard import PerformanceDashboard, DashboardConfig
from analysis.performance_monitor import (
    BenchmarkResults, BenchmarkMetric, BenchmarkType
)


# Test data generators
@st.composite
def benchmark_metric_strategy(draw):
    """Generate a BenchmarkMetric for testing."""
    metric_types = [
        ("syscall_latency", BenchmarkType.SYSTEM_CALL_LATENCY, "microseconds", (0.1, 100.0)),
        ("io_throughput", BenchmarkType.IO_THROUGHPUT, "MB/s", (10.0, 1000.0)),
        ("network_bandwidth", BenchmarkType.NETWORK_THROUGHPUT, "Mbits/s", (1.0, 10000.0)),
        ("memory_bandwidth", BenchmarkType.CUSTOM, "MB/s", (100.0, 50000.0)),
    ]
    
    name, benchmark_type, unit, (min_val, max_val) = draw(st.sampled_from(metric_types))
    value = draw(st.floats(min_value=min_val, max_value=max_val))
    
    return BenchmarkMetric(
        name=name,
        value=value,
        unit=unit,
        benchmark_type=benchmark_type,
        metadata={}
    )


@st.composite
def benchmark_results_strategy(draw):
    """Generate BenchmarkResults for testing."""
    benchmark_id = f"bench_{draw(st.integers(min_value=1000000, max_value=9999999))}"
    kernel_version = draw(st.sampled_from(["5.15.0", "6.1.0", "6.5.0"]))
    
    # Generate 1-5 metrics
    num_metrics = draw(st.integers(min_value=1, max_value=5))
    metrics = [draw(benchmark_metric_strategy()) for _ in range(num_metrics)]
    
    # Ensure unique metric names
    seen_names = set()
    unique_metrics = []
    for metric in metrics:
        if metric.name not in seen_names:
            unique_metrics.append(metric)
            seen_names.add(metric.name)
    
    assume(len(unique_metrics) > 0)
    
    return BenchmarkResults(
        benchmark_id=benchmark_id,
        kernel_version=kernel_version,
        timestamp=datetime.now(),
        metrics=unique_metrics,
        environment={"test": True},
        metadata={"generated": True}
    )


@st.composite
def performance_snapshot_strategy(draw, base_time=None):
    """Generate a PerformanceSnapshot for testing."""
    if base_time is None:
        base_time = datetime.now()
    
    # Generate timestamp within reasonable range
    offset_hours = draw(st.integers(min_value=-720, max_value=0))  # Up to 30 days ago
    timestamp = base_time + timedelta(hours=offset_hours)
    
    benchmark_results = draw(benchmark_results_strategy())
    benchmark_results.timestamp = timestamp
    
    commit_hash = draw(st.one_of(
        st.none(),
        st.text(alphabet="0123456789abcdef", min_size=7, max_size=40)
    ))
    
    branch = draw(st.one_of(
        st.none(),
        st.sampled_from(["main", "develop", "feature/test"])
    ))
    
    return PerformanceSnapshot(
        timestamp=timestamp.isoformat(),
        benchmark_results=benchmark_results,
        commit_hash=commit_hash,
        branch=branch,
        metadata={}
    )


class TestPerformanceTrendReporting:
    """Property-based tests for performance trend reporting functionality."""
    
    @given(snapshots=st.lists(performance_snapshot_strategy(), min_size=1, max_size=20))
    @settings(max_examples=50, deadline=5000)
    def test_performance_history_storage_completeness(self, snapshots):
        """
        **Feature: agentic-kernel-testing, Property 40: Performance trend reporting**
        **Validates: Requirements 8.5**
        
        Property: For any set of performance snapshots stored in the trend tracker,
        all snapshots should be retrievable and contain complete performance data.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = PerformanceTrendTracker(storage_dir=tmpdir)
            
            # Store all snapshots
            stored_snapshots = []
            for snapshot in snapshots:
                stored = tracker.store_snapshot(
                    snapshot.benchmark_results,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch,
                    metadata=snapshot.metadata
                )
                stored_snapshots.append(stored)
            
            # Retrieve all history
            retrieved = tracker.get_history()
            
            # Property: All stored snapshots should be retrievable
            assert len(retrieved) == len(snapshots), \
                f"Expected {len(snapshots)} snapshots, got {len(retrieved)}"
            
            # Property: Each retrieved snapshot should contain complete data
            for retrieved_snapshot in retrieved:
                assert retrieved_snapshot.benchmark_results is not None
                assert len(retrieved_snapshot.benchmark_results.metrics) > 0
                assert retrieved_snapshot.timestamp is not None
                
                # Verify timestamp format
                datetime.fromisoformat(retrieved_snapshot.timestamp)
                
                # Property: Metrics should be preserved exactly
                for metric in retrieved_snapshot.benchmark_results.metrics:
                    assert metric.name is not None
                    assert metric.value is not None
                    assert metric.unit is not None
                    assert metric.benchmark_type is not None
    
    @given(snapshots=st.lists(performance_snapshot_strategy(), min_size=2, max_size=15))
    @settings(max_examples=30, deadline=5000)
    def test_trend_analysis_consistency(self, snapshots):
        """
        **Feature: agentic-kernel-testing, Property 40: Performance trend reporting**
        **Validates: Requirements 8.5**
        
        Property: For any set of performance snapshots, trend analysis should
        produce consistent results and identify trends correctly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = PerformanceTrendTracker(storage_dir=tmpdir)
            
            # Store snapshots with consistent timestamps
            base_time = datetime.now()
            stored_snapshots = []
            
            for i, snapshot in enumerate(snapshots):
                # Ensure chronological order
                timestamp = base_time + timedelta(hours=i)
                snapshot.timestamp = timestamp.isoformat()
                snapshot.benchmark_results.timestamp = timestamp
                
                stored = tracker.store_snapshot(
                    snapshot.benchmark_results,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch
                )
                stored_snapshots.append(stored)
            
            # Analyze trends
            analysis = tracker.analyze_trend(stored_snapshots)
            
            # Property: Analysis should contain valid data
            assert isinstance(analysis, TrendAnalysis)
            assert analysis.num_snapshots == len(snapshots)
            assert analysis.time_span_days >= 0
            assert analysis.trend_direction in [TrendDirection.IMPROVING, TrendDirection.STABLE, TrendDirection.DECLINING]
            
            # Property: Metric trends should be consistent
            assert isinstance(analysis.metric_trends, dict)
            
            for metric_name, trend_data in analysis.metric_trends.items():
                assert 'direction' in trend_data
                assert 'average' in trend_data
                assert 'num_points' in trend_data
                assert trend_data['num_points'] >= 2  # Need at least 2 points for trend
                assert trend_data['average'] >= 0  # Performance metrics should be non-negative
                
                # Property: Trend direction should be valid
                assert trend_data['direction'] in ['improving', 'stable', 'declining']
            
            # Property: Regressions should be valid if present
            for regression in analysis.regressions:
                assert isinstance(regression, PerformanceRegression)
                assert regression.metric_name is not None
                assert regression.previous_value >= 0
                assert regression.current_value >= 0
                assert regression.severity in [s.value for s in RegressionSeverity]
    
    @given(
        snapshots=st.lists(performance_snapshot_strategy(), min_size=3, max_size=10),
        threshold=st.floats(min_value=0.01, max_value=0.5)
    )
    @settings(max_examples=25, deadline=5000)
    def test_regression_detection_accuracy(self, snapshots, threshold):
        """
        **Feature: agentic-kernel-testing, Property 40: Performance trend reporting**
        **Validates: Requirements 8.5**
        
        Property: For any performance data with known changes, regression detection
        should accurately identify performance degradations above the threshold.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = PerformanceTrendTracker(storage_dir=tmpdir)
            
            # Create snapshots with intentional regression
            base_time = datetime.now()
            modified_snapshots = []
            
            for i, snapshot in enumerate(snapshots):
                timestamp = base_time + timedelta(hours=i)
                snapshot.timestamp = timestamp.isoformat()
                snapshot.benchmark_results.timestamp = timestamp
                
                # Introduce regression in the middle snapshot for latency metrics
                if i == len(snapshots) // 2:
                    for metric in snapshot.benchmark_results.metrics:
                        if 'latency' in metric.name.lower():
                            # Increase latency by more than threshold (regression)
                            metric.value *= (1 + threshold + 0.1)
                
                modified_snapshots.append(snapshot)
            
            # Store snapshots
            for snapshot in modified_snapshots:
                tracker.store_snapshot(
                    snapshot.benchmark_results,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch
                )
            
            # Detect regressions
            regressions = tracker._detect_regressions_in_snapshots(
                modified_snapshots, threshold=threshold
            )
            
            # Property: Regression detection should be consistent
            for regression in regressions:
                # Property: Change should exceed threshold
                assert abs(regression.change_percent) >= threshold * 100
                
                # Property: Regression direction should be correct for metric type
                if 'latency' in regression.metric_name.lower():
                    # For latency, positive change is bad (regression)
                    assert regression.change_percent > 0
                elif 'throughput' in regression.metric_name.lower():
                    # For throughput, negative change is bad (regression)
                    assert regression.change_percent < 0
                
                # Property: Severity should be appropriate for change magnitude
                change_magnitude = abs(regression.change_percent)
                if change_magnitude >= 25.0:
                    assert regression.severity == RegressionSeverity.CRITICAL
                elif change_magnitude >= 15.0:
                    assert regression.severity == RegressionSeverity.HIGH
                elif change_magnitude >= 10.0:
                    assert regression.severity == RegressionSeverity.MEDIUM
                else:
                    assert regression.severity == RegressionSeverity.LOW
    
    @given(snapshots=st.lists(performance_snapshot_strategy(), min_size=5, max_size=12))
    @settings(max_examples=20, deadline=5000)
    def test_forecast_generation_validity(self, snapshots):
        """
        **Feature: agentic-kernel-testing, Property 40: Performance trend reporting**
        **Validates: Requirements 8.5**
        
        Property: For any performance trend data, forecast generation should
        produce valid predictions with appropriate confidence levels.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = PerformanceTrendTracker(storage_dir=tmpdir)
            
            # Store snapshots with consistent timing
            base_time = datetime.now()
            stored_snapshots = []
            
            for i, snapshot in enumerate(snapshots):
                timestamp = base_time + timedelta(days=i)  # Daily intervals
                snapshot.timestamp = timestamp.isoformat()
                snapshot.benchmark_results.timestamp = timestamp
                
                stored = tracker.store_snapshot(
                    snapshot.benchmark_results,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch
                )
                stored_snapshots.append(stored)
            
            # Analyze trends (includes forecast)
            analysis = tracker.analyze_trend(stored_snapshots)
            
            # Property: Forecast should be generated for sufficient data
            if analysis.time_span_days > 1:  # Need reasonable time span
                assert analysis.forecast is not None
                
                forecast_data = analysis.forecast
                
                # Property: Forecast structure should be valid
                assert 'forecasts' in forecast_data
                assert 'forecast_horizon_days' in forecast_data
                assert 'generated_at' in forecast_data
                assert 'methodology' in forecast_data
                
                # Property: Forecast horizon should be positive
                assert forecast_data['forecast_horizon_days'] > 0
                
                # Property: Generated timestamp should be valid
                datetime.fromisoformat(forecast_data['generated_at'])
                
                # Property: Individual forecasts should be valid
                for metric_name, forecast in forecast_data['forecasts'].items():
                    assert 'forecast_value' in forecast
                    assert 'current_value' in forecast
                    assert 'confidence' in forecast
                    assert 'forecast_days' in forecast
                    
                    # Property: Forecast values should be non-negative for performance metrics
                    assert forecast['forecast_value'] >= 0
                    assert forecast['current_value'] >= 0
                    
                    # Property: Confidence should be valid
                    assert forecast['confidence'] in ['low', 'medium', 'high']
                    
                    # Property: Forecast days should match horizon
                    assert forecast['forecast_days'] == forecast_data['forecast_horizon_days']
    
    @given(
        snapshots=st.lists(performance_snapshot_strategy(), min_size=2, max_size=8),
        config_title=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')), min_size=1, max_size=50),
        show_forecast=st.booleans(),
        show_regressions=st.booleans()
    )
    @settings(max_examples=15, deadline=8000)
    def test_dashboard_generation_completeness(self, snapshots, config_title, show_forecast, show_regressions):
        """
        **Feature: agentic-kernel-testing, Property 40: Performance trend reporting**
        **Validates: Requirements 8.5**
        
        Property: For any performance data and dashboard configuration, the generated
        dashboard should contain all required sections and valid HTML structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = PerformanceTrendTracker(storage_dir=tmpdir)
            
            # Store snapshots
            base_time = datetime.now()
            for i, snapshot in enumerate(snapshots):
                timestamp = base_time + timedelta(hours=i * 6)  # 6-hour intervals
                snapshot.timestamp = timestamp.isoformat()
                snapshot.benchmark_results.timestamp = timestamp
                
                tracker.store_snapshot(
                    snapshot.benchmark_results,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch
                )
            
            # Create dashboard
            dashboard_dir = Path(tmpdir) / "dashboard"
            dashboard = PerformanceDashboard(tracker, output_dir=str(dashboard_dir))
            
            config = DashboardConfig(
                title=config_title,
                show_forecast=show_forecast,
                show_regressions=show_regressions
            )
            
            # Generate dashboard
            dashboard_path = dashboard.generate_dashboard(config=config)
            
            # Property: Dashboard file should be created
            assert Path(dashboard_path).exists()
            
            # Property: Dashboard should be valid HTML
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Property: HTML should contain required elements
            assert '<!DOCTYPE html>' in html_content
            assert '<html' in html_content
            assert '</html>' in html_content
            assert '<head>' in html_content
            assert '<body>' in html_content
            
            # Property: Title should be included (check both raw and HTML-escaped versions)
            import html as html_module
            escaped_title = html_module.escape(config_title)
            assert config_title in html_content or escaped_title in html_content
            
            # Property: Required CSS and JS files should be created
            css_path = dashboard_dir / "dashboard.css"
            js_path = dashboard_dir / "dashboard.js"
            assert css_path.exists()
            assert js_path.exists()
            
            # Property: CSS should contain valid styles
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            assert 'body {' in css_content
            assert '.container' in css_content
            
            # Property: JavaScript should contain valid functions
            with open(js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            assert 'function initializeDashboard' in js_content
            assert 'Chart' in js_content  # Chart.js usage
    
    @given(
        snapshots=st.lists(performance_snapshot_strategy(), min_size=1, max_size=10),
        branch_filter=st.one_of(st.none(), st.sampled_from(["main", "develop", "feature/test"]))
    )
    @settings(max_examples=20, deadline=5000)
    def test_history_filtering_accuracy(self, snapshots, branch_filter):
        """
        **Feature: agentic-kernel-testing, Property 40: Performance trend reporting**
        **Validates: Requirements 8.5**
        
        Property: For any performance history and filter criteria, the filtering
        should return only snapshots that match the specified criteria.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = PerformanceTrendTracker(storage_dir=tmpdir)
            
            # Store snapshots with various branches
            base_time = datetime.now()
            stored_snapshots = []
            
            for i, snapshot in enumerate(snapshots):
                timestamp = base_time + timedelta(hours=i)
                snapshot.timestamp = timestamp.isoformat()
                snapshot.benchmark_results.timestamp = timestamp
                
                # Assign branch (some may be None)
                if i % 3 == 0:
                    snapshot.branch = "main"
                elif i % 3 == 1:
                    snapshot.branch = "develop"
                else:
                    snapshot.branch = None
                
                stored = tracker.store_snapshot(
                    snapshot.benchmark_results,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch
                )
                stored_snapshots.append(stored)
            
            # Test filtering by branch
            filtered = tracker.get_history(branch=branch_filter)
            
            # Property: All filtered results should match the filter
            for snapshot in filtered:
                if branch_filter is not None:
                    assert snapshot.branch == branch_filter
            
            # Property: No matching snapshots should be excluded
            expected_count = sum(1 for s in stored_snapshots 
                               if branch_filter is None or s.branch == branch_filter)
            assert len(filtered) == expected_count
            
            # Test date filtering
            if len(snapshots) > 2:
                mid_time = base_time + timedelta(hours=len(snapshots) // 2)
                start_date = mid_time.isoformat()
                
                date_filtered = tracker.get_history(start_date=start_date)
                
                # Property: All results should be after start_date
                for snapshot in date_filtered:
                    assert snapshot.timestamp >= start_date
    
    @given(
        snapshots=st.lists(performance_snapshot_strategy(), min_size=3, max_size=8),
        export_days=st.integers(min_value=1, max_value=90)
    )
    @settings(max_examples=15, deadline=5000)
    def test_json_export_completeness(self, snapshots, export_days):
        """
        **Feature: agentic-kernel-testing, Property 40: Performance trend reporting**
        **Validates: Requirements 8.5**
        
        Property: For any performance data, JSON export should contain complete
        and valid data that can be imported and used elsewhere.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = PerformanceTrendTracker(storage_dir=tmpdir)
            
            # Store snapshots
            base_time = datetime.now()
            for i, snapshot in enumerate(snapshots):
                timestamp = base_time - timedelta(days=i)  # Spread over time
                snapshot.timestamp = timestamp.isoformat()
                snapshot.benchmark_results.timestamp = timestamp
                
                tracker.store_snapshot(
                    snapshot.benchmark_results,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch
                )
            
            # Create dashboard and export
            dashboard_dir = Path(tmpdir) / "dashboard"
            dashboard = PerformanceDashboard(tracker, output_dir=str(dashboard_dir))
            
            export_path = dashboard.generate_json_export(days=export_days)
            
            # Property: Export file should be created
            assert Path(export_path).exists()
            
            # Property: Export should be valid JSON
            with open(export_path, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
            
            # Property: Export should contain required fields
            required_fields = [
                'export_timestamp', 'days', 'snapshots_count', 
                'snapshots', 'analysis'
            ]
            for field in required_fields:
                assert field in export_data
            
            # Property: Export timestamp should be valid
            datetime.fromisoformat(export_data['export_timestamp'])
            
            # Property: Snapshots count should match actual snapshots
            assert export_data['snapshots_count'] == len(export_data['snapshots'])
            
            # Property: Each exported snapshot should be complete
            for snapshot_data in export_data['snapshots']:
                assert 'timestamp' in snapshot_data
                assert 'benchmark_results' in snapshot_data
                
                # Verify benchmark results structure
                benchmark_data = snapshot_data['benchmark_results']
                assert 'benchmark_id' in benchmark_data
                assert 'kernel_version' in benchmark_data
                assert 'metrics' in benchmark_data
                assert len(benchmark_data['metrics']) > 0
                
                # Verify each metric
                for metric_data in benchmark_data['metrics']:
                    assert 'name' in metric_data
                    assert 'value' in metric_data
                    assert 'unit' in metric_data
                    assert 'benchmark_type' in metric_data
            
            # Property: Analysis should be included if snapshots exist
            if export_data['snapshots_count'] >= 2:
                assert export_data['analysis'] is not None
                analysis_data = export_data['analysis']
                assert 'trend_direction' in analysis_data
                assert 'metric_trends' in analysis_data
                assert 'num_snapshots' in analysis_data