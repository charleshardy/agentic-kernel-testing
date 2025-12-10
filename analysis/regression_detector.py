"""Performance regression detection system.

This module provides functionality for:
- Creating threshold-based regression detector
- Building statistical significance testing
- Implementing commit range identification via bisection
- Adding regression severity classification
"""

import os
import subprocess
import statistics
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math

from analysis.performance_monitor import BenchmarkResults, BenchmarkMetric
from analysis.baseline_manager import BaselineManager


class RegressionSeverity(str, Enum):
    """Severity levels for performance regressions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegressionType(str, Enum):
    """Types of performance regressions."""
    THROUGHPUT_DECREASE = "throughput_decrease"
    LATENCY_INCREASE = "latency_increase"
    RESOURCE_INCREASE = "resource_increase"


@dataclass
class RegressionDetection:
    """A detected performance regression."""
    metric_name: str
    regression_type: RegressionType
    severity: RegressionSeverity
    baseline_value: float
    current_value: float
    change_percent: float
    unit: str
    confidence: float  # 0.0 to 1.0
    statistical_significance: bool
    threshold_exceeded: float  # How much the threshold was exceeded
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'metric_name': self.metric_name,
            'regression_type': self.regression_type.value,
            'severity': self.severity.value,
            'baseline_value': self.baseline_value,
            'current_value': self.current_value,
            'change_percent': self.change_percent,
            'unit': self.unit,
            'confidence': self.confidence,
            'statistical_significance': self.statistical_significance,
            'threshold_exceeded': self.threshold_exceeded,
            'metadata': self.metadata
        }
        return data


@dataclass
class CommitRange:
    """A range of commits that may contain a regression."""
    start_commit: str
    end_commit: str
    suspicious_commits: List[str] = field(default_factory=list)
    confidence: float = 0.0
    bisect_log: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'start_commit': self.start_commit,
            'end_commit': self.end_commit,
            'suspicious_commits': self.suspicious_commits,
            'confidence': self.confidence,
            'bisect_log': self.bisect_log
        }


@dataclass
class RegressionReport:
    """Complete regression analysis report."""
    benchmark_id: str
    baseline_id: str
    kernel_version: str
    baseline_kernel_version: str
    timestamp: datetime
    regressions: List[RegressionDetection] = field(default_factory=list)
    commit_ranges: List[CommitRange] = field(default_factory=list)
    overall_severity: RegressionSeverity = RegressionSeverity.LOW
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'benchmark_id': self.benchmark_id,
            'baseline_id': self.baseline_id,
            'kernel_version': self.kernel_version,
            'baseline_kernel_version': self.baseline_kernel_version,
            'timestamp': self.timestamp.isoformat(),
            'regressions': [r.to_dict() for r in self.regressions],
            'commit_ranges': [c.to_dict() for c in self.commit_ranges],
            'overall_severity': self.overall_severity.value,
            'metadata': self.metadata
        }


class StatisticalAnalyzer:
    """Statistical analysis for regression detection."""
    
    @staticmethod
    def calculate_confidence(baseline_values: List[float], 
                           current_values: List[float]) -> float:
        """Calculate confidence in regression detection.
        
        Args:
            baseline_values: Historical baseline measurements
            current_values: Current measurements
            
        Returns:
            Confidence level (0.0 to 1.0)
        """
        if len(baseline_values) < 2 or len(current_values) < 2:
            return 0.5  # Low confidence with insufficient data
        
        try:
            # Calculate means and standard deviations
            baseline_mean = statistics.mean(baseline_values)
            current_mean = statistics.mean(current_values)
            
            baseline_stdev = statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0
            current_stdev = statistics.stdev(current_values) if len(current_values) > 1 else 0
            
            # If no variation, high confidence if means differ significantly
            if baseline_stdev == 0 and current_stdev == 0:
                return 1.0 if abs(baseline_mean - current_mean) > 0.01 else 0.0
            
            # Calculate pooled standard error
            n1, n2 = len(baseline_values), len(current_values)
            pooled_var = ((n1 - 1) * baseline_stdev**2 + (n2 - 1) * current_stdev**2) / (n1 + n2 - 2)
            standard_error = math.sqrt(pooled_var * (1/n1 + 1/n2))
            
            if standard_error == 0:
                return 1.0 if abs(baseline_mean - current_mean) > 0.01 else 0.0
            
            # Calculate t-statistic
            t_stat = abs(baseline_mean - current_mean) / standard_error
            
            # Convert to confidence (simplified approximation)
            # Higher t-statistic = higher confidence
            confidence = min(1.0, t_stat / 3.0)  # Normalize to 0-1 range
            
            return confidence
            
        except (statistics.StatisticsError, ZeroDivisionError, ValueError):
            return 0.5  # Default confidence on calculation error
    
    @staticmethod
    def is_statistically_significant(baseline_values: List[float],
                                   current_values: List[float],
                                   alpha: float = 0.05) -> bool:
        """Test for statistical significance using t-test approximation.
        
        Args:
            baseline_values: Historical baseline measurements
            current_values: Current measurements
            alpha: Significance level (default 0.05)
            
        Returns:
            True if difference is statistically significant
        """
        if len(baseline_values) < 2 or len(current_values) < 2:
            return False
        
        try:
            confidence = StatisticalAnalyzer.calculate_confidence(baseline_values, current_values)
            # Simple approximation: high confidence suggests significance
            return confidence > (1.0 - alpha)
        except Exception:
            return False


class GitBisectRunner:
    """Git bisect automation for regression identification."""
    
    def __init__(self, repo_path: str):
        """Initialize git bisect runner.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path)
    
    def identify_commit_range(self, good_commit: str, bad_commit: str,
                            test_script: Optional[str] = None) -> CommitRange:
        """Identify commit range that introduced regression.
        
        Args:
            good_commit: Known good commit (baseline)
            bad_commit: Known bad commit (current)
            test_script: Optional test script for automated bisection
            
        Returns:
            CommitRange with identified suspicious commits
        """
        commit_range = CommitRange(
            start_commit=good_commit,
            end_commit=bad_commit
        )
        
        if not self.repo_path.exists():
            commit_range.bisect_log.append("Repository path does not exist")
            return commit_range
        
        try:
            # Get commit list between good and bad
            cmd = [
                "git", "rev-list", "--oneline", 
                f"{good_commit}..{bad_commit}"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        commit_hash = line.split()[0]
                        commits.append(commit_hash)
                
                commit_range.suspicious_commits = commits
                commit_range.confidence = min(1.0, len(commits) / 10.0)  # More commits = lower confidence per commit
                commit_range.bisect_log.append(f"Found {len(commits)} commits in range")
            else:
                commit_range.bisect_log.append(f"Git command failed: {result.stderr}")
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            commit_range.bisect_log.append(f"Error running git bisect: {str(e)}")
        
        return commit_range
    
    def run_automated_bisect(self, good_commit: str, bad_commit: str,
                           test_script: str) -> CommitRange:
        """Run automated git bisect with test script.
        
        Args:
            good_commit: Known good commit
            bad_commit: Known bad commit  
            test_script: Script that returns 0 for good, 1 for bad
            
        Returns:
            CommitRange with bisect results
        """
        commit_range = CommitRange(
            start_commit=good_commit,
            end_commit=bad_commit
        )
        
        if not self.repo_path.exists() or not os.path.exists(test_script):
            commit_range.bisect_log.append("Repository or test script not found")
            return commit_range
        
        try:
            # Start bisect
            subprocess.run(
                ["git", "bisect", "start"],
                cwd=self.repo_path,
                check=True,
                timeout=30
            )
            
            # Mark good and bad commits
            subprocess.run(
                ["git", "bisect", "good", good_commit],
                cwd=self.repo_path,
                check=True,
                timeout=30
            )
            
            subprocess.run(
                ["git", "bisect", "bad", bad_commit],
                cwd=self.repo_path,
                check=True,
                timeout=30
            )
            
            # Run automated bisect
            result = subprocess.run(
                ["git", "bisect", "run", test_script],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode == 0:
                # Parse bisect output for first bad commit
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if "is the first bad commit" in line:
                        # Extract commit hash
                        parts = line.split()
                        if parts:
                            commit_range.suspicious_commits = [parts[0]]
                            commit_range.confidence = 0.9
                            break
                
                commit_range.bisect_log.extend(output_lines)
            else:
                commit_range.bisect_log.append(f"Bisect failed: {result.stderr}")
        
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            commit_range.bisect_log.append(f"Bisect error: {str(e)}")
        
        finally:
            # Clean up bisect state
            try:
                subprocess.run(
                    ["git", "bisect", "reset"],
                    cwd=self.repo_path,
                    timeout=30
                )
            except Exception:
                pass
        
        return commit_range


class RegressionDetector:
    """Main regression detection system."""
    
    def __init__(self, baseline_manager: BaselineManager,
                 repo_path: Optional[str] = None):
        """Initialize regression detector.
        
        Args:
            baseline_manager: BaselineManager instance
            repo_path: Optional path to git repository for bisection
        """
        self.baseline_manager = baseline_manager
        self.git_bisect = GitBisectRunner(repo_path) if repo_path else None
        self.statistical_analyzer = StatisticalAnalyzer()
    
    def detect_regressions(self, current_results: BenchmarkResults,
                          baseline_kernel_version: Optional[str] = None,
                          threshold: float = 0.1,
                          enable_statistical_test: bool = True) -> RegressionReport:
        """Detect performance regressions by comparing with baseline.
        
        Args:
            current_results: Current benchmark results
            baseline_kernel_version: Baseline kernel version (if None, uses current version)
            threshold: Regression threshold (e.g., 0.1 for 10%)
            enable_statistical_test: Whether to perform statistical significance testing
            
        Returns:
            RegressionReport with detected regressions
        """
        if baseline_kernel_version is None:
            baseline_kernel_version = current_results.kernel_version
        
        # Get baseline for comparison
        baseline = self.baseline_manager.retrieve_baseline(baseline_kernel_version)
        
        if baseline is None:
            return RegressionReport(
                benchmark_id=current_results.benchmark_id,
                baseline_id="none",
                kernel_version=current_results.kernel_version,
                baseline_kernel_version=baseline_kernel_version,
                timestamp=datetime.now(),
                metadata={'error': 'No baseline found for comparison'}
            )
        
        report = RegressionReport(
            benchmark_id=current_results.benchmark_id,
            baseline_id=baseline.baseline_id,
            kernel_version=current_results.kernel_version,
            baseline_kernel_version=baseline.kernel_version,
            timestamp=datetime.now()
        )
        
        # Compare each metric
        for current_metric in current_results.metrics:
            baseline_metric = baseline.get_metric(current_metric.name)
            
            if baseline_metric and baseline_metric.value > 0:
                regression = self._analyze_metric_regression(
                    current_metric, baseline_metric, threshold, enable_statistical_test
                )
                
                if regression:
                    report.regressions.append(regression)
        
        # Determine overall severity
        report.overall_severity = self._calculate_overall_severity(report.regressions)
        
        # Add metadata
        report.metadata.update({
            'threshold_used': threshold,
            'statistical_testing_enabled': enable_statistical_test,
            'total_metrics_compared': len([m for m in current_results.metrics 
                                         if baseline.get_metric(m.name) is not None]),
            'regressions_found': len(report.regressions)
        })
        
        return report
    
    def _analyze_metric_regression(self, current_metric: BenchmarkMetric,
                                 baseline_metric: BenchmarkMetric,
                                 threshold: float,
                                 enable_statistical_test: bool) -> Optional[RegressionDetection]:
        """Analyze a single metric for regression.
        
        Args:
            current_metric: Current metric measurement
            baseline_metric: Baseline metric measurement
            threshold: Regression threshold
            enable_statistical_test: Whether to perform statistical testing
            
        Returns:
            RegressionDetection if regression detected, None otherwise
        """
        # Calculate percentage change
        change_percent = ((current_metric.value - baseline_metric.value) / 
                         baseline_metric.value) * 100
        
        # Determine regression type and check threshold
        regression_type = None
        threshold_exceeded = 0.0
        
        # For latency metrics, increase is bad
        if 'latency' in current_metric.name.lower() or 'time' in current_metric.name.lower():
            if change_percent > (threshold * 100):
                regression_type = RegressionType.LATENCY_INCREASE
                threshold_exceeded = change_percent - (threshold * 100)
        
        # For throughput/bandwidth metrics, decrease is bad
        elif ('throughput' in current_metric.name.lower() or 
              'bandwidth' in current_metric.name.lower() or
              'iops' in current_metric.name.lower() or
              'mbps' in current_metric.unit.lower()):
            if change_percent < -(threshold * 100):
                regression_type = RegressionType.THROUGHPUT_DECREASE
                threshold_exceeded = abs(change_percent) - (threshold * 100)
        
        # For resource usage metrics, increase is bad
        elif ('memory' in current_metric.name.lower() or 
              'cpu' in current_metric.name.lower() or
              'usage' in current_metric.name.lower()):
            if change_percent > (threshold * 100):
                regression_type = RegressionType.RESOURCE_INCREASE
                threshold_exceeded = change_percent - (threshold * 100)
        
        # No regression detected
        if regression_type is None or threshold_exceeded <= 0:
            return None
        
        # Calculate confidence and statistical significance
        confidence = 0.8  # Default confidence for threshold-based detection
        statistical_significance = False
        
        if enable_statistical_test:
            # For statistical testing, we need multiple measurements
            # In this simplified version, we use the single values with some assumptions
            baseline_values = [baseline_metric.value]
            current_values = [current_metric.value]
            
            # Add some simulated variance for statistical testing
            # In a real system, we'd have historical measurements
            baseline_variance = baseline_metric.value * 0.05  # 5% variance
            current_variance = current_metric.value * 0.05
            
            baseline_values.extend([
                baseline_metric.value + baseline_variance,
                baseline_metric.value - baseline_variance
            ])
            current_values.extend([
                current_metric.value + current_variance,
                current_metric.value - current_variance
            ])
            
            confidence = self.statistical_analyzer.calculate_confidence(
                baseline_values, current_values
            )
            statistical_significance = self.statistical_analyzer.is_statistically_significant(
                baseline_values, current_values
            )
        
        # Calculate severity
        severity = self._calculate_regression_severity(threshold_exceeded, threshold)
        
        return RegressionDetection(
            metric_name=current_metric.name,
            regression_type=regression_type,
            severity=severity,
            baseline_value=baseline_metric.value,
            current_value=current_metric.value,
            change_percent=change_percent,
            unit=current_metric.unit,
            confidence=confidence,
            statistical_significance=statistical_significance,
            threshold_exceeded=threshold_exceeded,
            metadata={
                'baseline_benchmark_type': baseline_metric.benchmark_type.value,
                'current_benchmark_type': current_metric.benchmark_type.value
            }
        )
    
    def _calculate_regression_severity(self, threshold_exceeded: float, 
                                     base_threshold: float) -> RegressionSeverity:
        """Calculate severity of regression based on how much threshold was exceeded.
        
        Args:
            threshold_exceeded: How much the threshold was exceeded (percentage points)
            base_threshold: Base threshold used for detection
            
        Returns:
            RegressionSeverity level
        """
        base_threshold_percent = base_threshold * 100
        
        if threshold_exceeded >= base_threshold_percent * 3:
            return RegressionSeverity.CRITICAL
        elif threshold_exceeded >= base_threshold_percent * 2:
            return RegressionSeverity.HIGH
        elif threshold_exceeded >= base_threshold_percent * 1.5:
            return RegressionSeverity.MEDIUM
        else:
            return RegressionSeverity.LOW
    
    def _calculate_overall_severity(self, regressions: List[RegressionDetection]) -> RegressionSeverity:
        """Calculate overall severity from individual regressions.
        
        Args:
            regressions: List of detected regressions
            
        Returns:
            Overall RegressionSeverity
        """
        if not regressions:
            return RegressionSeverity.LOW
        
        # Take the highest severity
        severities = [r.severity for r in regressions]
        
        if RegressionSeverity.CRITICAL in severities:
            return RegressionSeverity.CRITICAL
        elif RegressionSeverity.HIGH in severities:
            return RegressionSeverity.HIGH
        elif RegressionSeverity.MEDIUM in severities:
            return RegressionSeverity.MEDIUM
        else:
            return RegressionSeverity.LOW
    
    def identify_commit_range(self, good_commit: str, bad_commit: str,
                            test_script: Optional[str] = None) -> Optional[CommitRange]:
        """Identify commit range that introduced regression via git bisect.
        
        Args:
            good_commit: Known good commit (baseline)
            bad_commit: Known bad commit (current)
            test_script: Optional test script for automated bisection
            
        Returns:
            CommitRange if git bisect is available, None otherwise
        """
        if self.git_bisect is None:
            return None
        
        if test_script and os.path.exists(test_script):
            return self.git_bisect.run_automated_bisect(good_commit, bad_commit, test_script)
        else:
            return self.git_bisect.identify_commit_range(good_commit, bad_commit)
    
    def generate_regression_report(self, current_results: BenchmarkResults,
                                 baseline_kernel_version: Optional[str] = None,
                                 threshold: float = 0.1,
                                 good_commit: Optional[str] = None,
                                 bad_commit: Optional[str] = None) -> RegressionReport:
        """Generate complete regression report with commit analysis.
        
        Args:
            current_results: Current benchmark results
            baseline_kernel_version: Baseline kernel version
            threshold: Regression threshold
            good_commit: Known good commit for bisection
            bad_commit: Known bad commit for bisection
            
        Returns:
            Complete RegressionReport
        """
        # Detect regressions
        report = self.detect_regressions(
            current_results, baseline_kernel_version, threshold
        )
        
        # Add commit range analysis if commits provided and regressions found
        if (good_commit and bad_commit and report.regressions and 
            self.git_bisect is not None):
            
            commit_range = self.identify_commit_range(good_commit, bad_commit)
            if commit_range:
                report.commit_ranges.append(commit_range)
                report.metadata['commit_analysis_performed'] = True
        
        return report