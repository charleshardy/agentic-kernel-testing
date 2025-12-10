"""Performance dashboard for visualizing performance trends and metrics.

This module provides functionality for:
- Creating HTML performance dashboards
- Generating interactive performance charts
- Displaying performance trends and regressions
- Providing real-time performance monitoring views
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import html

from analysis.performance_trend_tracker import (
    PerformanceTrendTracker, PerformanceSnapshot, TrendAnalysis, 
    PerformanceRegression, TrendDirection, RegressionSeverity
)
from analysis.performance_monitor import BenchmarkResults, BenchmarkMetric, BenchmarkType


@dataclass
class DashboardConfig:
    """Configuration for performance dashboard."""
    title: str = "Performance Dashboard"
    refresh_interval: int = 300  # seconds
    max_data_points: int = 100
    show_forecast: bool = True
    show_regressions: bool = True
    metric_filters: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'title': self.title,
            'refresh_interval': self.refresh_interval,
            'max_data_points': self.max_data_points,
            'show_forecast': self.show_forecast,
            'show_regressions': self.show_regressions,
            'metric_filters': self.metric_filters
        }


class PerformanceDashboard:
    """Performance dashboard generator for HTML reports and interactive monitoring."""
    
    def __init__(self, trend_tracker: PerformanceTrendTracker, 
                 output_dir: Optional[str] = None):
        """Initialize performance dashboard.
        
        Args:
            trend_tracker: PerformanceTrendTracker instance
            output_dir: Directory for output files (default: ./performance_dashboard)
        """
        self.trend_tracker = trend_tracker
        self.output_dir = Path(output_dir) if output_dir else Path("./performance_dashboard")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_dashboard(self, config: Optional[DashboardConfig] = None,
                          days: Optional[int] = 30,
                          branch: Optional[str] = None) -> str:
        """Generate complete performance dashboard.
        
        Args:
            config: Dashboard configuration
            days: Number of days of history to include
            branch: Optional branch filter
            
        Returns:
            Path to main dashboard HTML file
        """
        if config is None:
            config = DashboardConfig()
        
        # Get performance data
        if days:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            snapshots = self.trend_tracker.get_history(
                start_date=start_date, 
                branch=branch,
                limit=config.max_data_points
            )
        else:
            snapshots = self.trend_tracker.get_history(
                limit=config.max_data_points,
                branch=branch
            )
        
        if not snapshots:
            return self._generate_empty_dashboard(config)
        
        # Analyze trends
        analysis = self.trend_tracker.analyze_trend(snapshots)
        
        # Generate dashboard files
        self._generate_css()
        self._generate_javascript(config)
        dashboard_path = self._generate_main_dashboard(config, snapshots, analysis)
        
        return str(dashboard_path)
    
    def _generate_empty_dashboard(self, config: DashboardConfig) -> str:
        """Generate dashboard for when no data is available.
        
        Args:
            config: Dashboard configuration
            
        Returns:
            Path to dashboard HTML file
        """
        dashboard_path = self.output_dir / "index.html"
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(config.title)}</title>
    <link rel="stylesheet" href="dashboard.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{html.escape(config.title)}</h1>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="no-data">
            <h2>No Performance Data Available</h2>
            <p>No performance snapshots found. Run some benchmarks to populate the dashboard.</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(dashboard_path)
    
    def _generate_main_dashboard(self, config: DashboardConfig, 
                                snapshots: List[PerformanceSnapshot],
                                analysis: TrendAnalysis) -> Path:
        """Generate main dashboard HTML.
        
        Args:
            config: Dashboard configuration
            snapshots: Performance snapshots
            analysis: Trend analysis
            
        Returns:
            Path to dashboard file
        """
        dashboard_path = self.output_dir / "index.html"
        
        # Prepare data for JavaScript
        chart_data = self._prepare_chart_data(snapshots, config.metric_filters)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(config.title)}</title>
    <link rel="stylesheet" href="dashboard.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="dashboard.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>{html.escape(config.title)}</h1>
            <div class="header-info">
                <span class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                <span class="trend-indicator trend-{analysis.trend_direction.value}">
                    {analysis.trend_direction.value.upper()}
                </span>
            </div>
        </header>
        
        <div class="dashboard-grid">
            <section class="summary-section">
                <h2>Performance Summary</h2>
                <div class="summary-cards">
                    {self._generate_summary_cards(analysis)}
                </div>
            </section>
            
            <section class="charts-section">
                <h2>Performance Trends</h2>
                <div class="chart-controls">
                    <select id="metric-selector" onchange="updateChart()">
                        <option value="all">All Metrics</option>
                        {self._generate_metric_options(chart_data)}
                    </select>
                    <select id="time-range" onchange="updateChart()">
                        <option value="7">Last 7 days</option>
                        <option value="30" selected>Last 30 days</option>
                        <option value="90">Last 90 days</option>
                    </select>
                </div>
                <div class="chart-container">
                    <canvas id="performance-chart"></canvas>
                </div>
            </section>
            
            {self._generate_regressions_section(analysis) if config.show_regressions else ''}
            
            {self._generate_forecast_section(analysis) if config.show_forecast and analysis.forecast else ''}
            
            <section class="metrics-table-section">
                <h2>Latest Metrics</h2>
                <div class="table-container">
                    {self._generate_metrics_table(snapshots)}
                </div>
            </section>
        </div>
    </div>
    
    <script>
        // Initialize dashboard with data
        const chartData = {json.dumps(chart_data, indent=2)};
        const config = {json.dumps(config.to_dict(), indent=2)};
        
        document.addEventListener('DOMContentLoaded', function() {{
            initializeDashboard(chartData, config);
        }});
    </script>
</body>
</html>
"""
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return dashboard_path
    
    def _prepare_chart_data(self, snapshots: List[PerformanceSnapshot], 
                           metric_filters: Optional[List[str]] = None) -> Dict[str, Any]:
        """Prepare data for JavaScript charts.
        
        Args:
            snapshots: Performance snapshots
            metric_filters: Optional list of metrics to include
            
        Returns:
            Chart data dictionary
        """
        # Sort snapshots by timestamp
        snapshots.sort(key=lambda s: s.timestamp)
        
        # Collect all unique metrics
        all_metrics = set()
        for snapshot in snapshots:
            for metric in snapshot.benchmark_results.metrics:
                if not metric_filters or metric.name in metric_filters:
                    all_metrics.add(metric.name)
        
        # Prepare datasets for each metric
        datasets = {}
        labels = []
        
        for snapshot in snapshots:
            # Format timestamp for display
            dt = datetime.fromisoformat(snapshot.timestamp)
            labels.append(dt.strftime('%Y-%m-%d %H:%M'))
        
        for metric_name in sorted(all_metrics):
            values = []
            for snapshot in snapshots:
                metric = snapshot.benchmark_results.get_metric(metric_name)
                if metric:
                    values.append(metric.value)
                else:
                    values.append(None)
            
            # Determine chart color based on metric type
            color = self._get_metric_color(metric_name)
            
            datasets[metric_name] = {
                'label': metric_name,
                'data': values,
                'borderColor': color,
                'backgroundColor': color + '20',  # Add transparency
                'fill': False,
                'tension': 0.1
            }
        
        return {
            'labels': labels,
            'datasets': datasets,
            'metrics': list(all_metrics)
        }
    
    def _get_metric_color(self, metric_name: str) -> str:
        """Get color for a metric based on its type.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            CSS color string
        """
        # Color scheme based on metric type
        if 'latency' in metric_name.lower() or 'time' in metric_name.lower():
            return '#e74c3c'  # Red for latency (lower is better)
        elif 'throughput' in metric_name.lower() or 'bandwidth' in metric_name.lower():
            return '#2ecc71'  # Green for throughput (higher is better)
        elif 'iops' in metric_name.lower():
            return '#3498db'  # Blue for IOPS
        elif 'cpu' in metric_name.lower():
            return '#f39c12'  # Orange for CPU metrics
        elif 'memory' in metric_name.lower():
            return '#9b59b6'  # Purple for memory metrics
        else:
            return '#34495e'  # Dark gray for other metrics
    
    def _generate_summary_cards(self, analysis: TrendAnalysis) -> str:
        """Generate summary cards HTML.
        
        Args:
            analysis: Trend analysis
            
        Returns:
            HTML string for summary cards
        """
        cards = []
        
        # Overall trend card
        trend_icon = {
            TrendDirection.IMPROVING: "↗️",
            TrendDirection.STABLE: "➡️",
            TrendDirection.DECLINING: "↘️"
        }
        
        cards.append(f"""
            <div class="summary-card trend-{analysis.trend_direction.value}">
                <div class="card-icon">{trend_icon[analysis.trend_direction]}</div>
                <div class="card-content">
                    <h3>Overall Trend</h3>
                    <p class="card-value">{analysis.trend_direction.value.title()}</p>
                    <p class="card-detail">{analysis.num_snapshots} snapshots over {analysis.time_span_days:.1f} days</p>
                </div>
            </div>
        """)
        
        # Regressions card
        regression_count = len(analysis.regressions)
        critical_regressions = len([r for r in analysis.regressions if r.severity == RegressionSeverity.CRITICAL])
        
        cards.append(f"""
            <div class="summary-card {'regressions-critical' if critical_regressions > 0 else 'regressions-normal'}">
                <div class="card-icon">⚠️</div>
                <div class="card-content">
                    <h3>Regressions</h3>
                    <p class="card-value">{regression_count}</p>
                    <p class="card-detail">{critical_regressions} critical, {regression_count - critical_regressions} others</p>
                </div>
            </div>
        """)
        
        # Metrics tracked card
        metrics_count = len(analysis.metric_trends)
        improving_metrics = len([t for t in analysis.metric_trends.values() 
                               if t['direction'] == TrendDirection.IMPROVING.value])
        
        cards.append(f"""
            <div class="summary-card metrics-normal">
                <div class="card-icon">📊</div>
                <div class="card-content">
                    <h3>Metrics Tracked</h3>
                    <p class="card-value">{metrics_count}</p>
                    <p class="card-detail">{improving_metrics} improving</p>
                </div>
            </div>
        """)
        
        return '\n'.join(cards)
    
    def _generate_metric_options(self, chart_data: Dict[str, Any]) -> str:
        """Generate metric selector options.
        
        Args:
            chart_data: Chart data dictionary
            
        Returns:
            HTML options string
        """
        options = []
        for metric in chart_data.get('metrics', []):
            options.append(f'<option value="{html.escape(metric)}">{html.escape(metric)}</option>')
        
        return '\n'.join(options)
    
    def _generate_regressions_section(self, analysis: TrendAnalysis) -> str:
        """Generate regressions section HTML.
        
        Args:
            analysis: Trend analysis
            
        Returns:
            HTML string for regressions section
        """
        if not analysis.regressions:
            return """
            <section class="regressions-section">
                <h2>Performance Regressions</h2>
                <div class="no-regressions">
                    <p>✅ No performance regressions detected</p>
                </div>
            </section>
            """
        
        # Sort regressions by severity
        severity_order = {
            RegressionSeverity.CRITICAL: 0,
            RegressionSeverity.HIGH: 1,
            RegressionSeverity.MEDIUM: 2,
            RegressionSeverity.LOW: 3
        }
        sorted_regressions = sorted(analysis.regressions, 
                                  key=lambda r: severity_order[r.severity])
        
        regression_rows = []
        for reg in sorted_regressions:
            severity_class = f"severity-{reg.severity.value}"
            
            regression_rows.append(f"""
                <tr class="{severity_class}">
                    <td>{html.escape(reg.metric_name)}</td>
                    <td>{reg.previous_value:.2f} {html.escape(reg.unit)}</td>
                    <td>{reg.current_value:.2f} {html.escape(reg.unit)}</td>
                    <td class="change-percent">{reg.change_percent:+.1f}%</td>
                    <td><span class="severity-badge {severity_class}">{reg.severity.value.upper()}</span></td>
                    <td>{datetime.fromisoformat(reg.timestamp).strftime('%Y-%m-%d %H:%M')}</td>
                </tr>
            """)
        
        return f"""
        <section class="regressions-section">
            <h2>Performance Regressions ({len(analysis.regressions)})</h2>
            <div class="table-container">
                <table class="regressions-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Previous</th>
                            <th>Current</th>
                            <th>Change</th>
                            <th>Severity</th>
                            <th>Detected</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(regression_rows)}
                    </tbody>
                </table>
            </div>
        </section>
        """
    
    def _generate_forecast_section(self, analysis: TrendAnalysis) -> str:
        """Generate forecast section HTML.
        
        Args:
            analysis: Trend analysis
            
        Returns:
            HTML string for forecast section
        """
        if not analysis.forecast or not analysis.forecast.get('forecasts'):
            return ""
        
        forecast_data = analysis.forecast
        forecast_rows = []
        
        for metric_name, forecast in forecast_data['forecasts'].items():
            confidence_class = f"confidence-{forecast['confidence']}"
            change_class = "positive" if forecast['forecast_change_percent'] >= 0 else "negative"
            
            forecast_rows.append(f"""
                <tr>
                    <td>{html.escape(metric_name)}</td>
                    <td>{forecast['current_value']:.2f}</td>
                    <td>{forecast['forecast_value']:.2f}</td>
                    <td class="change-percent {change_class}">{forecast['forecast_change_percent']:+.1f}%</td>
                    <td><span class="confidence-badge {confidence_class}">{forecast['confidence'].upper()}</span></td>
                </tr>
            """)
        
        return f"""
        <section class="forecast-section">
            <h2>Performance Forecast ({forecast_data['forecast_horizon_days']} days)</h2>
            <div class="table-container">
                <table class="forecast-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Current</th>
                            <th>Forecast</th>
                            <th>Change</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(forecast_rows)}
                    </tbody>
                </table>
            </div>
            <p class="forecast-note">
                Forecast generated using {forecast_data['methodology']} at {datetime.fromisoformat(forecast_data['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </section>
        """
    
    def _generate_metrics_table(self, snapshots: List[PerformanceSnapshot]) -> str:
        """Generate latest metrics table HTML.
        
        Args:
            snapshots: Performance snapshots
            
        Returns:
            HTML string for metrics table
        """
        if not snapshots:
            return "<p>No metrics available</p>"
        
        # Get latest snapshot
        latest_snapshot = max(snapshots, key=lambda s: s.timestamp)
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in latest_snapshot.benchmark_results.metrics:
            metric_type = metric.benchmark_type.value
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(metric)
        
        table_sections = []
        
        for metric_type, metrics in metrics_by_type.items():
            rows = []
            for metric in sorted(metrics, key=lambda m: m.name):
                rows.append(f"""
                    <tr>
                        <td>{html.escape(metric.name)}</td>
                        <td class="metric-value">{metric.value:.2f}</td>
                        <td>{html.escape(metric.unit)}</td>
                    </tr>
                """)
            
            table_sections.append(f"""
                <div class="metric-type-section">
                    <h4>{metric_type.replace('_', ' ').title()}</h4>
                    <table class="metrics-table">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Value</th>
                                <th>Unit</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows)}
                        </tbody>
                    </table>
                </div>
            """)
        
        return f"""
        <div class="latest-metrics">
            <p class="metrics-timestamp">
                Latest data from: {datetime.fromisoformat(latest_snapshot.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
            </p>
            {''.join(table_sections)}
        </div>
        """
    
    def _generate_css(self) -> None:
        """Generate CSS stylesheet for dashboard."""
        css_path = self.output_dir / "dashboard.css"
        
        css_content = """/* Performance Dashboard Styles */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f8f9fa;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

header h1 {
    font-size: 2em;
    color: #2c3e50;
}

.header-info {
    display: flex;
    align-items: center;
    gap: 20px;
}

.timestamp {
    color: #7f8c8d;
    font-size: 0.9em;
}

.trend-indicator {
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9em;
}

.trend-improving {
    background: #d5f4e6;
    color: #27ae60;
}

.trend-stable {
    background: #fef9e7;
    color: #f39c12;
}

.trend-declining {
    background: #fadbd8;
    color: #e74c3c;
}

.dashboard-grid {
    display: grid;
    gap: 20px;
}

section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h2 {
    font-size: 1.5em;
    color: #2c3e50;
    margin-bottom: 20px;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 10px;
}

.summary-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.summary-card {
    display: flex;
    align-items: center;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #3498db;
}

.summary-card.trend-improving {
    border-left-color: #27ae60;
    background: #d5f4e6;
}

.summary-card.trend-stable {
    border-left-color: #f39c12;
    background: #fef9e7;
}

.summary-card.trend-declining {
    border-left-color: #e74c3c;
    background: #fadbd8;
}

.summary-card.regressions-critical {
    border-left-color: #e74c3c;
    background: #fadbd8;
}

.summary-card.regressions-normal {
    border-left-color: #27ae60;
    background: #d5f4e6;
}

.summary-card.metrics-normal {
    border-left-color: #3498db;
    background: #ebf3fd;
}

.card-icon {
    font-size: 2em;
    margin-right: 15px;
}

.card-content h3 {
    font-size: 1em;
    color: #7f8c8d;
    margin-bottom: 5px;
}

.card-value {
    font-size: 1.8em;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 5px;
}

.card-detail {
    font-size: 0.85em;
    color: #95a5a6;
}

.chart-controls {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.chart-controls select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1em;
    background: white;
}

.chart-container {
    position: relative;
    height: 400px;
    margin-bottom: 20px;
}

.table-container {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
}

thead {
    background: #34495e;
    color: white;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ecf0f1;
}

tbody tr:hover {
    background: #f8f9fa;
}

.severity-badge, .confidence-badge {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    font-weight: bold;
}

.severity-critical {
    background: #e74c3c;
    color: white;
}

.severity-high {
    background: #f39c12;
    color: white;
}

.severity-medium {
    background: #3498db;
    color: white;
}

.severity-low {
    background: #95a5a6;
    color: white;
}

.confidence-high {
    background: #27ae60;
    color: white;
}

.confidence-medium {
    background: #f39c12;
    color: white;
}

.confidence-low {
    background: #e74c3c;
    color: white;
}

.change-percent.positive {
    color: #27ae60;
    font-weight: bold;
}

.change-percent.negative {
    color: #e74c3c;
    font-weight: bold;
}

.metric-value {
    font-weight: bold;
    text-align: right;
}

.no-data, .no-regressions {
    text-align: center;
    padding: 40px;
    color: #7f8c8d;
}

.no-regressions {
    background: #d5f4e6;
    border-radius: 8px;
}

.forecast-note {
    font-size: 0.85em;
    color: #7f8c8d;
    margin-top: 10px;
    font-style: italic;
}

.metrics-timestamp {
    font-size: 0.9em;
    color: #7f8c8d;
    margin-bottom: 15px;
}

.metric-type-section {
    margin-bottom: 30px;
}

.metric-type-section h4 {
    color: #34495e;
    margin-bottom: 10px;
    font-size: 1.1em;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
    
    .summary-cards {
        grid-template-columns: 1fr;
    }
    
    .chart-controls {
        flex-direction: column;
    }
    
    table {
        font-size: 0.9em;
    }
    
    .chart-container {
        height: 300px;
    }
}
"""
        
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    def _generate_javascript(self, config: DashboardConfig) -> None:
        """Generate JavaScript for dashboard interactivity.
        
        Args:
            config: Dashboard configuration
        """
        js_path = self.output_dir / "dashboard.js"
        
        js_content = f"""// Performance Dashboard JavaScript

let performanceChart = null;
let chartData = null;
let dashboardConfig = null;

function initializeDashboard(data, config) {{
    chartData = data;
    dashboardConfig = config;
    
    // Initialize the main chart
    initializeChart();
    
    // Set up auto-refresh if configured
    if (config.refresh_interval > 0) {{
        setInterval(refreshDashboard, config.refresh_interval * 1000);
    }}
}}

function initializeChart() {{
    const ctx = document.getElementById('performance-chart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (performanceChart) {{
        performanceChart.destroy();
    }}
    
    // Get selected metric
    const metricSelector = document.getElementById('metric-selector');
    const selectedMetric = metricSelector ? metricSelector.value : 'all';
    
    // Prepare datasets
    let datasets = [];
    
    if (selectedMetric === 'all') {{
        // Show all metrics
        Object.values(chartData.datasets).forEach(dataset => {{
            datasets.push(dataset);
        }});
    }} else {{
        // Show only selected metric
        if (chartData.datasets[selectedMetric]) {{
            datasets.push(chartData.datasets[selectedMetric]);
        }}
    }}
    
    performanceChart = new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: chartData.labels,
            datasets: datasets
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            interaction: {{
                intersect: false,
                mode: 'index'
            }},
            plugins: {{
                title: {{
                    display: true,
                    text: selectedMetric === 'all' ? 'All Performance Metrics' : selectedMetric
                }},
                legend: {{
                    display: datasets.length > 1
                }},
                tooltip: {{
                    callbacks: {{
                        title: function(context) {{
                            return 'Time: ' + context[0].label;
                        }},
                        label: function(context) {{
                            return context.dataset.label + ': ' + 
                                   (context.parsed.y !== null ? context.parsed.y.toFixed(2) : 'N/A');
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    display: true,
                    title: {{
                        display: true,
                        text: 'Time'
                    }}
                }},
                y: {{
                    display: true,
                    title: {{
                        display: true,
                        text: 'Value'
                    }}
                }}
            }}
        }}
    }});
}}

function updateChart() {{
    initializeChart();
}}

function refreshDashboard() {{
    // In a real implementation, this would fetch new data from the server
    console.log('Refreshing dashboard...');
    
    // For now, just reload the page
    window.location.reload();
}}

// Utility functions
function formatValue(value, decimals = 2) {{
    if (value === null || value === undefined) return 'N/A';
    return parseFloat(value).toFixed(decimals);
}}

function formatPercent(value, decimals = 1) {{
    if (value === null || value === undefined) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return sign + parseFloat(value).toFixed(decimals) + '%';
}}

function getMetricColor(metricName) {{
    // Color scheme based on metric type
    if (metricName.toLowerCase().includes('latency') || 
        metricName.toLowerCase().includes('time')) {{
        return '#e74c3c';  // Red for latency
    }} else if (metricName.toLowerCase().includes('throughput') || 
               metricName.toLowerCase().includes('bandwidth')) {{
        return '#2ecc71';  // Green for throughput
    }} else if (metricName.toLowerCase().includes('iops')) {{
        return '#3498db';  // Blue for IOPS
    }} else if (metricName.toLowerCase().includes('cpu')) {{
        return '#f39c12';  // Orange for CPU
    }} else if (metricName.toLowerCase().includes('memory')) {{
        return '#9b59b6';  // Purple for memory
    }} else {{
        return '#34495e';  // Dark gray for others
    }}
}}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {{
    console.log('Performance Dashboard loaded');
}});
"""
        
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
    
    def generate_json_export(self, days: Optional[int] = 30,
                            branch: Optional[str] = None,
                            output_file: Optional[str] = None) -> str:
        """Generate JSON export of performance data.
        
        Args:
            days: Number of days of history to include
            branch: Optional branch filter
            output_file: Optional output file path
            
        Returns:
            Path to JSON file
        """
        if days:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            snapshots = self.trend_tracker.get_history(start_date=start_date, branch=branch)
        else:
            snapshots = self.trend_tracker.get_history(branch=branch)
        
        # Analyze trends
        analysis = self.trend_tracker.analyze_trend(snapshots) if snapshots else None
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'branch': branch,
            'days': days,
            'snapshots_count': len(snapshots),
            'snapshots': [s.to_dict() for s in snapshots],
            'analysis': analysis.to_dict() if analysis else None
        }
        
        if output_file is None:
            output_file = self.output_dir / f"performance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        return str(output_file)