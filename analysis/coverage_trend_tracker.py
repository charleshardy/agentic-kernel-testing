"""Coverage trend tracking for monitoring coverage changes over time.

This module provides functionality for:
- Storing coverage history with timestamps and metadata
- Analyzing coverage trends over time
- Detecting coverage regressions
- Visualizing coverage trends
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

from ai_generator.models import CoverageData


class TrendDirection(str, Enum):
    """Direction of coverage trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class CoverageSnapshot:
    """A snapshot of coverage data at a specific point in time."""
    timestamp: str  # ISO format datetime
    coverage_data: CoverageData
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    build_id: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'coverage_data': self.coverage_data.to_dict(),
            'commit_hash': self.commit_hash,
            'branch': self.branch,
            'build_id': self.build_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CoverageSnapshot':
        """Create from dictionary."""
        return cls(
            timestamp=data['timestamp'],
            coverage_data=CoverageData.from_dict(data['coverage_data']),
            commit_hash=data.get('commit_hash'),
            branch=data.get('branch'),
            build_id=data.get('build_id'),
            metadata=data.get('metadata', {})
        )


@dataclass
class CoverageRegression:
    """Represents a detected coverage regression."""
    regression_type: str  # 'line', 'branch', or 'function'
    previous_coverage: float
    current_coverage: float
    coverage_drop: float
    timestamp: str
    commit_hash: Optional[str] = None
    severity: str = "medium"  # 'low', 'medium', 'high', 'critical'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CoverageRegression':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TrendAnalysis:
    """Analysis of coverage trends over time."""
    trend_direction: TrendDirection
    average_line_coverage: float
    average_branch_coverage: float
    average_function_coverage: float
    line_coverage_change: float  # Change from first to last snapshot
    branch_coverage_change: float
    function_coverage_change: float
    num_snapshots: int
    time_span_days: float
    regressions: List[CoverageRegression] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'trend_direction': self.trend_direction.value,
            'average_line_coverage': self.average_line_coverage,
            'average_branch_coverage': self.average_branch_coverage,
            'average_function_coverage': self.average_function_coverage,
            'line_coverage_change': self.line_coverage_change,
            'branch_coverage_change': self.branch_coverage_change,
            'function_coverage_change': self.function_coverage_change,
            'num_snapshots': self.num_snapshots,
            'time_span_days': self.time_span_days,
            'regressions': [r.to_dict() for r in self.regressions]
        }


class CoverageTrendTracker:
    """Tracks coverage trends over time and detects regressions."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize coverage trend tracker.
        
        Args:
            storage_dir: Directory for storing coverage history (default: ./coverage_data/history)
        """
        self.storage_dir = Path(storage_dir) if storage_dir else Path("./coverage_data/history")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.storage_dir / "coverage_history.json"
    
    def store_snapshot(self, coverage_data: CoverageData, 
                      commit_hash: Optional[str] = None,
                      branch: Optional[str] = None,
                      build_id: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> CoverageSnapshot:
        """Store a coverage snapshot in the history.
        
        Args:
            coverage_data: CoverageData object to store
            commit_hash: Optional git commit hash
            branch: Optional git branch name
            build_id: Optional build identifier
            metadata: Optional additional metadata
            
        Returns:
            CoverageSnapshot object
        """
        timestamp = datetime.now().isoformat()
        
        snapshot = CoverageSnapshot(
            timestamp=timestamp,
            coverage_data=coverage_data,
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
                   end_date: Optional[str] = None) -> List[CoverageSnapshot]:
        """Retrieve coverage history with optional filtering.
        
        Args:
            limit: Maximum number of snapshots to return (most recent first)
            branch: Filter by branch name
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            
        Returns:
            List of CoverageSnapshot objects
        """
        history = self._load_history()
        
        # Convert to CoverageSnapshot objects
        snapshots = [CoverageSnapshot.from_dict(data) for data in history]
        
        # Apply filters
        if branch:
            snapshots = [s for s in snapshots if s.branch == branch]
        
        if start_date:
            snapshots = [s for s in snapshots if s.timestamp >= start_date]
        
        if end_date:
            snapshots = [s for s in snapshots if s.timestamp <= end_date]
        
        # Sort by timestamp (most recent first)
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            snapshots = snapshots[:limit]
        
        return snapshots
    
    def analyze_trend(self, snapshots: Optional[List[CoverageSnapshot]] = None,
                     days: Optional[int] = None,
                     branch: Optional[str] = None) -> TrendAnalysis:
        """Analyze coverage trends over time.
        
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
            raise ValueError("No coverage snapshots available for analysis")
        
        # Sort by timestamp (oldest first for trend analysis)
        snapshots.sort(key=lambda s: s.timestamp)
        
        # Calculate averages
        line_coverages = [s.coverage_data.line_coverage for s in snapshots]
        branch_coverages = [s.coverage_data.branch_coverage for s in snapshots]
        function_coverages = [s.coverage_data.function_coverage for s in snapshots]
        
        avg_line = sum(line_coverages) / len(line_coverages)
        avg_branch = sum(branch_coverages) / len(branch_coverages)
        avg_function = sum(function_coverages) / len(function_coverages)
        
        # Calculate changes
        line_change = line_coverages[-1] - line_coverages[0]
        branch_change = branch_coverages[-1] - branch_coverages[0]
        function_change = function_coverages[-1] - function_coverages[0]
        
        # Determine trend direction
        overall_change = (line_change + branch_change + function_change) / 3
        if overall_change > 0.01:  # More than 1% improvement
            trend_direction = TrendDirection.IMPROVING
        elif overall_change < -0.01:  # More than 1% decline
            trend_direction = TrendDirection.DECLINING
        else:
            trend_direction = TrendDirection.STABLE
        
        # Calculate time span
        first_time = datetime.fromisoformat(snapshots[0].timestamp)
        last_time = datetime.fromisoformat(snapshots[-1].timestamp)
        time_span_days = (last_time - first_time).total_seconds() / 86400
        
        # Detect regressions
        regressions = self._detect_regressions_in_snapshots(snapshots)
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            average_line_coverage=avg_line,
            average_branch_coverage=avg_branch,
            average_function_coverage=avg_function,
            line_coverage_change=line_change,
            branch_coverage_change=branch_change,
            function_coverage_change=function_change,
            num_snapshots=len(snapshots),
            time_span_days=time_span_days,
            regressions=regressions
        )
    
    def detect_regression(self, current_coverage: CoverageData,
                         baseline_coverage: Optional[CoverageData] = None,
                         threshold: float = 0.01) -> List[CoverageRegression]:
        """Detect coverage regressions by comparing current coverage to baseline.
        
        Args:
            current_coverage: Current coverage data
            baseline_coverage: Baseline coverage data (if None, uses most recent snapshot)
            threshold: Minimum coverage drop to consider a regression (default: 1%)
            
        Returns:
            List of CoverageRegression objects
        """
        if baseline_coverage is None:
            # Get most recent snapshot as baseline
            history = self.get_history(limit=1)
            if not history:
                return []  # No baseline available
            baseline_coverage = history[0].coverage_data
        
        regressions = []
        timestamp = datetime.now().isoformat()
        
        # Check line coverage regression
        line_drop = baseline_coverage.line_coverage - current_coverage.line_coverage
        if line_drop > threshold:
            severity = self._calculate_severity(line_drop)
            regressions.append(CoverageRegression(
                regression_type='line',
                previous_coverage=baseline_coverage.line_coverage,
                current_coverage=current_coverage.line_coverage,
                coverage_drop=line_drop,
                timestamp=timestamp,
                severity=severity
            ))
        
        # Check branch coverage regression
        branch_drop = baseline_coverage.branch_coverage - current_coverage.branch_coverage
        if branch_drop > threshold:
            severity = self._calculate_severity(branch_drop)
            regressions.append(CoverageRegression(
                regression_type='branch',
                previous_coverage=baseline_coverage.branch_coverage,
                current_coverage=current_coverage.branch_coverage,
                coverage_drop=branch_drop,
                timestamp=timestamp,
                severity=severity
            ))
        
        # Check function coverage regression
        function_drop = baseline_coverage.function_coverage - current_coverage.function_coverage
        if function_drop > threshold:
            severity = self._calculate_severity(function_drop)
            regressions.append(CoverageRegression(
                regression_type='function',
                previous_coverage=baseline_coverage.function_coverage,
                current_coverage=current_coverage.function_coverage,
                coverage_drop=function_drop,
                timestamp=timestamp,
                severity=severity
            ))
        
        return regressions
    
    def _detect_regressions_in_snapshots(self, snapshots: List[CoverageSnapshot],
                                        threshold: float = 0.01) -> List[CoverageRegression]:
        """Detect regressions within a list of snapshots.
        
        Args:
            snapshots: List of coverage snapshots (sorted by time)
            threshold: Minimum coverage drop to consider a regression
            
        Returns:
            List of CoverageRegression objects
        """
        regressions = []
        
        for i in range(1, len(snapshots)):
            prev_snapshot = snapshots[i - 1]
            curr_snapshot = snapshots[i]
            
            # Check line coverage
            line_drop = prev_snapshot.coverage_data.line_coverage - curr_snapshot.coverage_data.line_coverage
            if line_drop > threshold:
                severity = self._calculate_severity(line_drop)
                regressions.append(CoverageRegression(
                    regression_type='line',
                    previous_coverage=prev_snapshot.coverage_data.line_coverage,
                    current_coverage=curr_snapshot.coverage_data.line_coverage,
                    coverage_drop=line_drop,
                    timestamp=curr_snapshot.timestamp,
                    commit_hash=curr_snapshot.commit_hash,
                    severity=severity
                ))
            
            # Check branch coverage
            branch_drop = prev_snapshot.coverage_data.branch_coverage - curr_snapshot.coverage_data.branch_coverage
            if branch_drop > threshold:
                severity = self._calculate_severity(branch_drop)
                regressions.append(CoverageRegression(
                    regression_type='branch',
                    previous_coverage=prev_snapshot.coverage_data.branch_coverage,
                    current_coverage=curr_snapshot.coverage_data.branch_coverage,
                    coverage_drop=branch_drop,
                    timestamp=curr_snapshot.timestamp,
                    commit_hash=curr_snapshot.commit_hash,
                    severity=severity
                ))
            
            # Check function coverage
            function_drop = prev_snapshot.coverage_data.function_coverage - curr_snapshot.coverage_data.function_coverage
            if function_drop > threshold:
                severity = self._calculate_severity(function_drop)
                regressions.append(CoverageRegression(
                    regression_type='function',
                    previous_coverage=prev_snapshot.coverage_data.function_coverage,
                    current_coverage=curr_snapshot.coverage_data.function_coverage,
                    coverage_drop=function_drop,
                    timestamp=curr_snapshot.timestamp,
                    commit_hash=curr_snapshot.commit_hash,
                    severity=severity
                ))
        
        return regressions
    
    def _calculate_severity(self, coverage_drop: float) -> str:
        """Calculate severity of a coverage regression.
        
        Args:
            coverage_drop: Amount of coverage decrease (0.0 to 1.0)
            
        Returns:
            Severity level: 'low', 'medium', 'high', or 'critical'
        """
        if coverage_drop >= 0.10:  # 10% or more drop
            return "critical"
        elif coverage_drop >= 0.05:  # 5-10% drop
            return "high"
        elif coverage_drop >= 0.02:  # 2-5% drop
            return "medium"
        else:  # Less than 2% drop
            return "low"
    
    def generate_trend_visualization(self, snapshots: Optional[List[CoverageSnapshot]] = None,
                                    output_file: Optional[str] = None) -> str:
        """Generate a text-based visualization of coverage trends.
        
        Args:
            snapshots: Optional list of snapshots to visualize (if None, uses recent history)
            output_file: Optional file path to write visualization
            
        Returns:
            Visualization as string
        """
        if snapshots is None:
            snapshots = self.get_history(limit=50)
        
        if not snapshots:
            return "No coverage history available"
        
        # Sort by timestamp (oldest first)
        snapshots.sort(key=lambda s: s.timestamp)
        
        lines = []
        lines.append("=" * 80)
        lines.append("COVERAGE TREND VISUALIZATION")
        lines.append("=" * 80)
        lines.append(f"\nTime Period: {snapshots[0].timestamp} to {snapshots[-1].timestamp}")
        lines.append(f"Number of Snapshots: {len(snapshots)}\n")
        
        # Create simple ASCII chart
        lines.append("Line Coverage Trend:")
        lines.append(self._create_ascii_chart(
            [s.coverage_data.line_coverage for s in snapshots],
            "Line Coverage"
        ))
        
        lines.append("\nBranch Coverage Trend:")
        lines.append(self._create_ascii_chart(
            [s.coverage_data.branch_coverage for s in snapshots],
            "Branch Coverage"
        ))
        
        lines.append("\nFunction Coverage Trend:")
        lines.append(self._create_ascii_chart(
            [s.coverage_data.function_coverage for s in snapshots],
            "Function Coverage"
        ))
        
        # Add summary statistics
        analysis = self.analyze_trend(snapshots)
        lines.append("\n" + "=" * 80)
        lines.append("TREND SUMMARY")
        lines.append("=" * 80)
        lines.append(f"Trend Direction: {analysis.trend_direction.value.upper()}")
        lines.append(f"Average Line Coverage: {analysis.average_line_coverage:.2%}")
        lines.append(f"Average Branch Coverage: {analysis.average_branch_coverage:.2%}")
        lines.append(f"Average Function Coverage: {analysis.average_function_coverage:.2%}")
        lines.append(f"Line Coverage Change: {analysis.line_coverage_change:+.2%}")
        lines.append(f"Branch Coverage Change: {analysis.branch_coverage_change:+.2%}")
        lines.append(f"Function Coverage Change: {analysis.function_coverage_change:+.2%}")
        
        if analysis.regressions:
            lines.append(f"\nRegressions Detected: {len(analysis.regressions)}")
            for reg in analysis.regressions[:5]:  # Show first 5
                lines.append(f"  - {reg.regression_type.capitalize()}: "
                           f"{reg.previous_coverage:.2%} → {reg.current_coverage:.2%} "
                           f"({reg.severity})")
        
        lines.append("\n" + "=" * 80)
        
        visualization = '\n'.join(lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(visualization)
        
        return visualization
    
    def _create_ascii_chart(self, values: List[float], label: str, width: int = 60) -> str:
        """Create a simple ASCII chart.
        
        Args:
            values: List of values to chart (0.0 to 1.0)
            label: Label for the chart
            width: Width of the chart in characters
            
        Returns:
            ASCII chart as string
        """
        if not values:
            return "No data"
        
        lines = []
        
        # Scale values to chart height (10 rows)
        height = 10
        scaled_values = [int(v * height) for v in values]
        
        # Draw chart from top to bottom
        for row in range(height, -1, -1):
            line_parts = []
            
            # Y-axis label
            if row == height:
                line_parts.append("100% |")
            elif row == height // 2:
                line_parts.append(" 50% |")
            elif row == 0:
                line_parts.append("  0% |")
            else:
                line_parts.append("     |")
            
            # Data points
            for val in scaled_values:
                if val >= row:
                    line_parts.append("█")
                else:
                    line_parts.append(" ")
            
            lines.append(''.join(line_parts))
        
        # X-axis
        lines.append("     +" + "-" * len(values))
        lines.append(f"     {label}")
        
        return '\n'.join(lines)
    
    def _load_history(self) -> List[Dict]:
        """Load coverage history from disk.
        
        Returns:
            List of coverage snapshot dictionaries
        """
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self, history: List[Dict]) -> None:
        """Save coverage history to disk.
        
        Args:
            history: List of coverage snapshot dictionaries
        """
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def clear_history(self, branch: Optional[str] = None) -> int:
        """Clear coverage history.
        
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


# Import timedelta for date calculations
from datetime import timedelta
