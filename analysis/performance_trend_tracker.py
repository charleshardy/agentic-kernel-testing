"""Performance trend tracking for monitoring performance changes over time.

This module provides functionality for:
- Storing performance history with timestamps and metadata
- Analyzing performance trends over time
- Detecting performance regressions
- Visualizing performance trends
- Generating performance forecasts
"""

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from analysis.performance_monitor import BenchmarkResults, BenchmarkMetric, BenchmarkType


class TrendDirection(str, Enum):
    """Direction of performance trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class RegressionSeverity(str, Enum):
    """Severity of performance regression."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PerformanceSnapshot:
    """A snapshot of performance data at a specific point in time."""
    timestamp: str  # ISO format datetime
    benchmark_results: BenchmarkResults
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    build_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'benchmark_results': self.benchmark_results.to_dict(),
            'commit_hash': self.commit_hash,
            'branch': self.branch,
            'build_id': self.build_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceSnapshot':
        """Create from dictionary."""
        return cls(
            timestamp=data['timestamp'],
            benchmark_results=BenchmarkResults.from_dict(data['benchmark_results']),
            commit_hash=data.get('commit_hash'),
            branch=data.get('branch'),
            build_id=data.get('build_id'),
            metadata=data.get('metadata', {})
        )


@dataclass
class PerformanceRegression:
    """Represents a detected performance regression."""
    metric_name: str
    benchmark_type: BenchmarkType
    previous_value: float
    current_value: float
    change_percent: float
    timestamp: str
    commit_hash: Optional[str] = None
    severity: RegressionSeverity = RegressionSeverity.MEDIUM
    unit: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['benchmark_type'] = self.benchmark_type.value
        data['severity'] = self.severity.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceRegression':
        """Create from dictionary."""
        data['benchmark_type'] = BenchmarkType(data['benchmark_type'])
        data['severity'] = RegressionSeverity(data['severity'])
        return cls(**data)


@dataclass
class TrendAnalysis:
    """Analysis of performance trends over time."""
    trend_direction: TrendDirection
    metric_trends: Dict[str, Dict[str, Any]]  # metric_name -> trend data
    num_snapshots: int
    time_span_days: float
    regressions: List[PerformanceRegression] = field(default_factory=list)
    forecast: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trend_direction': self.trend_direction.value,
            'metric_trends': self.metric_trends,
            'num_snapshots': self.num_snapshots,
            'time_span_days': self.time_span_days,
            'regressions': [r.to_dict() for r in self.regressions],
            'forecast': self.forecast
        }


class PerformanceTrendTracker:
    """Tracks performance trends over time and detects regressions."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize performance trend tracker.
        
        Args:
            storage_dir: Directory for storing performance history (default: ./performance_data/history)
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path("./performance_data/history")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_dir / "performance_history.json"
    
    def store_snapshot(self, benchmark_results: BenchmarkResults,
                      commit_hash: Optional[str] = None,
                      branch: Optional[str] = None,
                      build_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> PerformanceSnapshot:
        """Store a performance snapshot in the history.
        
        Args:
            benchmark_results: BenchmarkResults object to store
            commit_hash: Optional git commit hash
            branch: Optional git branch name
            build_id: Optional build identifier
            metadata: Optional additional metadata
            
        Returns:
            PerformanceSnapshot object
        """
        timestamp = datetime.now().isoformat()
        
        snapshot = PerformanceSnapshot(
            timestamp=timestamp,
            benchmark_results=benchmark_results,
            commit_hash=commit_hash,
            branch=branch,
            build_id=build_id,
            metadata=metadata or {}
        )
        
        # Load existing history
        history = self._load_history()
        
        # Add new snapshot
        history.append(snapshot.to_dict())
        
        # Save updated history
        self._save_history(history)
        
        return snapshot
    
    def get_history(self, limit: Optional[int] = None,
                   branch: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   metric_name: Optional[str] = None) -> List[PerformanceSnapshot]:
        """Retrieve performance history with optional filtering.
        
        Args:
            limit: Maximum number of snapshots to return (most recent first)
            branch: Filter by branch name
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            metric_name: Filter by specific metric name
            
        Returns:
            List of PerformanceSnapshot objects
        """
        history = self._load_history()
        
        # Convert to PerformanceSnapshot objects
        snapshots = [PerformanceSnapshot.from_dict(data) for data in history]
        
        # Apply filters
        if branch:
            snapshots = [s for s in snapshots if s.branch == branch]
        
        if start_date:
            snapshots = [s for s in snapshots if s.timestamp >= start_date]
        
        if end_date:
            snapshots = [s for s in snapshots if s.timestamp <= end_date]
        
        if metric_name:
            # Filter snapshots that have the specified metric
            filtered_snapshots = []
            for snapshot in snapshots:
                if any(m.name == metric_name for m in snapshot.benchmark_results.metrics):
                    filtered_snapshots.append(snapshot)
            snapshots = filtered_snapshots
        
        # Sort by timestamp (most recent first)
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            snapshots = snapshots[:limit]
        
        return snapshots
    
    def analyze_trend(self, snapshots: Optional[List[PerformanceSnapshot]] = None,
                     days: Optional[int] = None,
                     branch: Optional[str] = None) -> TrendAnalysis:
        """Analyze performance trends over time.
        
        Args:
            snapshots: Optional list of snapshots to analyze (if None, uses recent history)
            days: Optional number of days to analyze (if snapshots not provided)
            branch: Optional branch to filter by
            
        Returns:
            TrendAnalysis object
        """
        if snapshots is None:
            # Get recent history
            if days:
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                snapshots = self.get_history(start_date=start_date, branch=branch)
            else:
                snapshots = self.get_history(limit=100, branch=branch)
        
        if not snapshots:
            raise ValueError("No performance snapshots available for analysis")
        
        # Sort by timestamp (oldest first for trend analysis)
        snapshots.sort(key=lambda s: s.timestamp)
        
        # Analyze trends for each metric
        metric_trends = self._analyze_metric_trends(snapshots)
        
        # Determine overall trend direction
        trend_direction = self._determine_overall_trend(metric_trends)
        
        # Calculate time span
        first_time = datetime.fromisoformat(snapshots[0].timestamp)
        last_time = datetime.fromisoformat(snapshots[-1].timestamp)
        time_span_days = (last_time - first_time).total_seconds() / 86400
        
        # Detect regressions
        regressions = self._detect_regressions_in_snapshots(snapshots)
        
        # Generate forecast
        forecast = self._generate_forecast(metric_trends, time_span_days)
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            metric_trends=metric_trends,
            num_snapshots=len(snapshots),
            time_span_days=time_span_days,
            regressions=regressions,
            forecast=forecast
        )
    
    def _analyze_metric_trends(self, snapshots: List[PerformanceSnapshot]) -> Dict[str, Dict[str, Any]]:
        """Analyze trends for individual metrics.
        
        Args:
            snapshots: List of performance snapshots (sorted by time)
            
        Returns:
            Dictionary mapping metric names to trend data
        """
        # Collect all unique metrics
        all_metrics = set()
        for snapshot in snapshots:
            for metric in snapshot.benchmark_results.metrics:
                all_metrics.add(metric.name)
        
        metric_trends = {}
        
        for metric_name in all_metrics:
            # Extract values for this metric across snapshots
            values = []
            timestamps = []
            
            for snapshot in snapshots:
                metric = snapshot.benchmark_results.get_metric(metric_name)
                if metric:
                    values.append(metric.value)
                    timestamps.append(snapshot.timestamp)
            
            if len(values) < 2:
                continue  # Need at least 2 points for trend analysis
            
            # Calculate trend statistics
            trend_data = self._calculate_metric_trend(values, timestamps, metric_name)
            metric_trends[metric_name] = trend_data
        
        return metric_trends
    
    def _calculate_metric_trend(self, values: List[float], timestamps: List[str], 
                               metric_name: str) -> Dict[str, Any]:
        """Calculate trend statistics for a single metric.
        
        Args:
            values: List of metric values
            timestamps: List of timestamps
            metric_name: Name of the metric
            
        Returns:
            Dictionary with trend statistics
        """
        # Basic statistics
        avg_value = statistics.mean(values)
        median_value = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        min_value = min(values)
        max_value = max(values)
        
        # Calculate linear trend (simple slope)
        n = len(values)
        x_values = list(range(n))  # Use indices as x values
        
        # Linear regression slope calculation
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determine trend direction for this metric
        if abs(slope) < avg_value * 0.01:  # Less than 1% change per unit time
            direction = TrendDirection.STABLE
        elif slope > 0:
            # For latency metrics, positive slope is bad (declining performance)
            # For throughput metrics, positive slope is good (improving performance)
            if 'latency' in metric_name.lower() or 'time' in metric_name.lower():
                direction = TrendDirection.DECLINING
            else:
                direction = TrendDirection.IMPROVING
        else:
            # Negative slope
            if 'latency' in metric_name.lower() or 'time' in metric_name.lower():
                direction = TrendDirection.IMPROVING
            else:
                direction = TrendDirection.DECLINING
        
        # Calculate percentage change from first to last
        if values[0] != 0:
            percent_change = ((values[-1] - values[0]) / values[0]) * 100
        else:
            percent_change = 0.0
        
        # Calculate volatility (coefficient of variation)
        volatility = (std_dev / avg_value) * 100 if avg_value != 0 else 0.0
        
        return {
            'direction': direction.value,
            'average': avg_value,
            'median': median_value,
            'std_dev': std_dev,
            'min': min_value,
            'max': max_value,
            'slope': slope,
            'percent_change': percent_change,
            'volatility': volatility,
            'num_points': n,
            'first_value': values[0],
            'last_value': values[-1],
            'first_timestamp': timestamps[0],
            'last_timestamp': timestamps[-1]
        }
    
    def _determine_overall_trend(self, metric_trends: Dict[str, Dict[str, Any]]) -> TrendDirection:
        """Determine overall trend direction from individual metric trends.
        
        Args:
            metric_trends: Dictionary of metric trend data
            
        Returns:
            Overall TrendDirection
        """
        if not metric_trends:
            return TrendDirection.STABLE
        
        # Count trends by direction
        improving_count = 0
        declining_count = 0
        stable_count = 0
        
        for trend_data in metric_trends.values():
            direction = TrendDirection(trend_data['direction'])
            if direction == TrendDirection.IMPROVING:
                improving_count += 1
            elif direction == TrendDirection.DECLINING:
                declining_count += 1
            else:
                stable_count += 1
        
        # Determine overall direction
        total_metrics = len(metric_trends)
        
        if improving_count > declining_count and improving_count > total_metrics * 0.4:
            return TrendDirection.IMPROVING
        elif declining_count > improving_count and declining_count > total_metrics * 0.4:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    def _detect_regressions_in_snapshots(self, snapshots: List[PerformanceSnapshot],
                                        threshold: float = 0.05) -> List[PerformanceRegression]:
        """Detect regressions within a list of snapshots.
        
        Args:
            snapshots: List of performance snapshots (sorted by time)
            threshold: Minimum percentage change to consider a regression (default: 5%)
            
        Returns:
            List of PerformanceRegression objects
        """
        regressions = []
        
        for i in range(1, len(snapshots)):
            prev_snapshot = snapshots[i - 1]
            curr_snapshot = snapshots[i]
            
            # Compare metrics between consecutive snapshots
            prev_metrics = {m.name: m for m in prev_snapshot.benchmark_results.metrics}
            curr_metrics = {m.name: m for m in curr_snapshot.benchmark_results.metrics}
            
            for metric_name in prev_metrics:
                if metric_name not in curr_metrics:
                    continue
                
                prev_metric = prev_metrics[metric_name]
                curr_metric = curr_metrics[metric_name]
                
                # Calculate percentage change
                if prev_metric.value != 0:
                    change_percent = ((curr_metric.value - prev_metric.value) / 
                                    prev_metric.value) * 100
                else:
                    change_percent = 0.0
                
                # Determine if this is a regression
                is_regression = False
                
                # For latency/time metrics, increase is bad
                if ('latency' in metric_name.lower() or 'time' in metric_name.lower() or
                    'duration' in metric_name.lower()):
                    if change_percent > threshold * 100:
                        is_regression = True
                
                # For throughput/bandwidth/IOPS metrics, decrease is bad
                elif ('throughput' in metric_name.lower() or 'bandwidth' in metric_name.lower() or
                      'iops' in metric_name.lower() or 'transactions' in metric_name.lower()):
                    if change_percent < -threshold * 100:
                        is_regression = True
                
                if is_regression:
                    severity = self._calculate_regression_severity(abs(change_percent))
                    
                    regressions.append(PerformanceRegression(
                        metric_name=metric_name,
                        benchmark_type=curr_metric.benchmark_type,
                        previous_value=prev_metric.value,
                        current_value=curr_metric.value,
                        change_percent=change_percent,
                        timestamp=curr_snapshot.timestamp,
                        commit_hash=curr_snapshot.commit_hash,
                        severity=severity,
                        unit=curr_metric.unit
                    ))
        
        return regressions
    
    def _calculate_regression_severity(self, change_percent: float) -> RegressionSeverity:
        """Calculate severity of a performance regression.
        
        Args:
            change_percent: Absolute percentage change
            
        Returns:
            RegressionSeverity level
        """
        if change_percent >= 25.0:  # 25% or more change
            return RegressionSeverity.CRITICAL
        elif change_percent >= 15.0:  # 15-25% change
            return RegressionSeverity.HIGH
        elif change_percent >= 10.0:  # 10-15% change
            return RegressionSeverity.MEDIUM
        else:  # Less than 10% change
            return RegressionSeverity.LOW
    
    def _generate_forecast(self, metric_trends: Dict[str, Dict[str, Any]], 
                          time_span_days: float) -> Dict[str, Any]:
        """Generate performance forecast based on trends.
        
        Args:
            metric_trends: Dictionary of metric trend data
            time_span_days: Time span of the data in days
            
        Returns:
            Forecast data
        """
        if not metric_trends or time_span_days <= 0:
            return None
        
        forecast_days = 30  # Forecast 30 days ahead
        forecasts = {}
        
        for metric_name, trend_data in metric_trends.items():
            slope = trend_data['slope']
            last_value = trend_data['last_value']
            volatility = trend_data['volatility']
            
            # Simple linear extrapolation
            # Convert slope from per-index to per-day
            slope_per_day = slope * (trend_data['num_points'] / time_span_days) if time_span_days > 0 else 0
            
            # Forecast value
            forecast_value = last_value + (slope_per_day * forecast_days)
            
            # Calculate confidence based on volatility
            if volatility < 5:
                confidence = "high"
            elif volatility < 15:
                confidence = "medium"
            else:
                confidence = "low"
            
            forecasts[metric_name] = {
                'forecast_value': forecast_value,
                'current_value': last_value,
                'forecast_change_percent': ((forecast_value - last_value) / last_value * 100) if last_value != 0 else 0,
                'confidence': confidence,
                'volatility': volatility,
                'forecast_days': forecast_days
            }
        
        return {
            'forecasts': forecasts,
            'forecast_horizon_days': forecast_days,
            'generated_at': datetime.now().isoformat(),
            'methodology': 'linear_extrapolation'
        }
    
    def detect_regression(self, current_results: BenchmarkResults,
                         baseline_results: Optional[BenchmarkResults] = None,
                         threshold: float = 0.05) -> List[PerformanceRegression]:
        """Detect performance regressions by comparing current results to baseline.
        
        Args:
            current_results: Current benchmark results
            baseline_results: Baseline results (if None, uses most recent snapshot)
            threshold: Minimum percentage change to consider a regression (default: 5%)
            
        Returns:
            List of PerformanceRegression objects
        """
        if baseline_results is None:
            # Get most recent snapshot as baseline
            history = self.get_history(limit=1)
            if not history:
                return []  # No baseline available
            baseline_results = history[0].benchmark_results
        
        regressions = []
        timestamp = datetime.now().isoformat()
        
        # Compare metrics
        baseline_metrics = {m.name: m for m in baseline_results.metrics}
        current_metrics = {m.name: m for m in current_results.metrics}
        
        for metric_name in baseline_metrics:
            if metric_name not in current_metrics:
                continue
            
            baseline_metric = baseline_metrics[metric_name]
            current_metric = current_metrics[metric_name]
            
            # Calculate percentage change
            if baseline_metric.value != 0:
                change_percent = ((current_metric.value - baseline_metric.value) / 
                                baseline_metric.value) * 100
            else:
                change_percent = 0.0
            
            # Determine if this is a regression
            is_regression = False
            
            # For latency/time metrics, increase is bad
            if ('latency' in metric_name.lower() or 'time' in metric_name.lower() or
                'duration' in metric_name.lower()):
                if change_percent > threshold * 100:
                    is_regression = True
            
            # For throughput/bandwidth/IOPS metrics, decrease is bad
            elif ('throughput' in metric_name.lower() or 'bandwidth' in metric_name.lower() or
                  'iops' in metric_name.lower() or 'transactions' in metric_name.lower()):
                if change_percent < -threshold * 100:
                    is_regression = True
            
            if is_regression:
                severity = self._calculate_regression_severity(abs(change_percent))
                
                regressions.append(PerformanceRegression(
                    metric_name=metric_name,
                    benchmark_type=current_metric.benchmark_type,
                    previous_value=baseline_metric.value,
                    current_value=current_metric.value,
                    change_percent=change_percent,
                    timestamp=timestamp,
                    severity=severity,
                    unit=current_metric.unit
                ))
        
        return regressions
    
    def generate_trend_visualization(self, snapshots: Optional[List[PerformanceSnapshot]] = None,
                                    output_file: Optional[str] = None,
                                    metric_filter: Optional[List[str]] = None) -> str:
        """Generate a text-based visualization of performance trends.
        
        Args:
            snapshots: Optional list of snapshots to visualize (if None, uses recent history)
            output_file: Optional file path to write visualization
            metric_filter: Optional list of metric names to include
            
        Returns:
            Visualization as string
        """
        if snapshots is None:
            snapshots = self.get_history(limit=50)
        
        if not snapshots:
            return "No performance history available"
        
        # Sort by timestamp (oldest first)
        snapshots.sort(key=lambda s: s.timestamp)
        
        lines = []
        lines.append("=" * 80)
        lines.append("PERFORMANCE TREND VISUALIZATION")
        lines.append("=" * 80)
        lines.append(f"\nTime Period: {snapshots[0].timestamp} to {snapshots[-1].timestamp}")
        lines.append(f"Number of Snapshots: {len(snapshots)}\n")
        
        # Get all unique metrics
        all_metrics = set()
        for snapshot in snapshots:
            for metric in snapshot.benchmark_results.metrics:
                if not metric_filter or metric.name in metric_filter:
                    all_metrics.add(metric.name)
        
        # Create charts for each metric
        for metric_name in sorted(all_metrics):
            values = []
            timestamps = []
            
            for snapshot in snapshots:
                metric = snapshot.benchmark_results.get_metric(metric_name)
                if metric:
                    values.append(metric.value)
                    timestamps.append(snapshot.timestamp)
            
            if len(values) < 2:
                continue
            
            lines.append(f"\n{metric_name}:")
            lines.append(self._create_ascii_chart(values, metric_name))
        
        # Add trend analysis summary
        analysis = self.analyze_trend(snapshots)
        lines.append("\n" + "=" * 80)
        lines.append("TREND SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Overall Trend Direction: {analysis.trend_direction.value.upper()}")
        lines.append(f"Number of Metrics Analyzed: {len(analysis.metric_trends)}")
        lines.append(f"Time Span: {analysis.time_span_days:.1f} days")
        
        if analysis.regressions:
            lines.append(f"\nRegressions Detected: {len(analysis.regressions)}")
            for reg in analysis.regressions[:5]:  # Show first 5
                lines.append(f"  - {reg.metric_name}: "
                           f"{reg.previous_value:.2f} → {reg.current_value:.2f} "
                           f"({reg.change_percent:+.1f}%, {reg.severity.value})")
        
        # Add forecast if available
        if analysis.forecast:
            lines.append(f"\nForecast ({analysis.forecast['forecast_horizon_days']} days ahead):")
            for metric_name, forecast_data in analysis.forecast['forecasts'].items():
                if not metric_filter or metric_name in metric_filter:
                    lines.append(f"  - {metric_name}: "
                               f"{forecast_data['current_value']:.2f} → "
                               f"{forecast_data['forecast_value']:.2f} "
                               f"({forecast_data['forecast_change_percent']:+.1f}%, "
                               f"confidence: {forecast_data['confidence']})")
        
        lines.append("\n" + "=" * 80)
        
        visualization = '\n'.join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(visualization)
        
        return visualization
    
    def _create_ascii_chart(self, values: List[float], label: str, width: int = 60) -> str:
        """Create a simple ASCII chart for performance values.
        
        Args:
            values: List of values to chart
            label: Label for the chart
            width: Width of the chart in characters
            
        Returns:
            ASCII chart as string
        """
        if not values:
            return "No data"
        
        lines = []
        
        # Normalize values to chart height (10 rows)
        height = 10
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            # All values are the same
            scaled_values = [height // 2] * len(values)
        else:
            scaled_values = [int(((v - min_val) / (max_val - min_val)) * height) for v in values]
        
        # Draw chart from top to bottom
        for row in range(height, -1, -1):
            line_parts = []
            
            # Y-axis label
            if row == height:
                line_parts.append(f"{max_val:8.2f} |")
            elif row == height // 2:
                mid_val = (max_val + min_val) / 2
                line_parts.append(f"{mid_val:8.2f} |")
            elif row == 0:
                line_parts.append(f"{min_val:8.2f} |")
            else:
                line_parts.append("         |")
            
            # Data points
            for val in scaled_values:
                if val >= row:
                    line_parts.append("█")
                else:
                    line_parts.append(" ")
            
            lines.append(''.join(line_parts))
        
        # X-axis
        lines.append("         +" + "-" * len(values))
        lines.append(f"         {label}")
        
        # Add statistics
        avg_val = sum(values) / len(values)
        lines.append(f"         Avg: {avg_val:.2f}, Min: {min_val:.2f}, Max: {max_val:.2f}")
        
        return '\n'.join(lines)
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load performance history from disk.
        
        Returns:
            List of performance snapshot dictionaries
        """
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """Save performance history to disk.
        
        Args:
            history: List of performance snapshot dictionaries
        """
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def clear_history(self, branch: Optional[str] = None) -> int:
        """Clear performance history.
        
        Args:
            branch: Optional branch to clear (if None, clears all history)
            
        Returns:
            Number of snapshots removed
        """
        if branch is None:
            # Clear all history
            count = len(self._load_history())
            self._save_history([])
            return count
        else:
            # Clear only specific branch
            history = self._load_history()
            filtered = [h for h in history if h.get('branch') != branch]
            removed = len(history) - len(filtered)
            self._save_history(filtered)
            return removed
    
    def get_metric_history(self, metric_name: str, 
                          limit: Optional[int] = None,
                          branch: Optional[str] = None) -> List[Tuple[str, float]]:
        """Get history for a specific metric.
        
        Args:
            metric_name: Name of the metric
            limit: Maximum number of data points
            branch: Optional branch filter
            
        Returns:
            List of (timestamp, value) tuples
        """
        snapshots = self.get_history(limit=limit, branch=branch, metric_name=metric_name)
        
        history = []
        for snapshot in reversed(snapshots):  # Oldest first
            metric = snapshot.benchmark_results.get_metric(metric_name)
            if metric:
                history.append((snapshot.timestamp, metric.value))
        
        return history