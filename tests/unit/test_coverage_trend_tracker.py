"""Unit tests for coverage trend tracking."""

import pytest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

from analysis.coverage_trend_tracker import (
    CoverageTrendTracker,
    CoverageSnapshot,
    CoverageRegression,
    TrendDirection
)
from ai_generator.models import CoverageData


class TestCoverageTrendTracker:
    """Unit tests for CoverageTrendTracker."""
    
    def test_store_and_retrieve_snapshot(self):
        """Test storing and retrieving a single snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            coverage = CoverageData(
                line_coverage=0.85,
                branch_coverage=0.75,
                function_coverage=0.80,
                covered_lines=["file.c:1", "file.c:2"],
                uncovered_lines=["file.c:3"],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            snapshot = tracker.store_snapshot(
                coverage,
                commit_hash="abc123",
                branch="main",
                build_id="build-001"
            )
            
            assert snapshot.coverage_data.line_coverage == 0.85
            assert snapshot.commit_hash == "abc123"
            assert snapshot.branch == "main"
            assert snapshot.build_id == "build-001"
            
            # Retrieve and verify
            history = tracker.get_history(limit=1)
            assert len(history) == 1
            assert history[0].commit_hash == "abc123"
    
    def test_detect_line_coverage_regression(self):
        """Test detection of line coverage regression."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            baseline = CoverageData(
                line_coverage=0.80,
                branch_coverage=0.70,
                function_coverage=0.75,
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            current = CoverageData(
                line_coverage=0.70,  # 10% drop
                branch_coverage=0.70,
                function_coverage=0.75,
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            regressions = tracker.detect_regression(current, baseline, threshold=0.01)
            
            assert len(regressions) == 1
            assert regressions[0].regression_type == 'line'
            assert abs(regressions[0].coverage_drop - 0.10) < 0.0001
            assert regressions[0].severity == 'critical'
    
    def test_no_regression_when_coverage_improves(self):
        """Test that no regression is detected when coverage improves."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            baseline = CoverageData(
                line_coverage=0.70,
                branch_coverage=0.60,
                function_coverage=0.65,
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            current = CoverageData(
                line_coverage=0.80,  # Improved
                branch_coverage=0.70,  # Improved
                function_coverage=0.75,  # Improved
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            regressions = tracker.detect_regression(current, baseline, threshold=0.01)
            
            assert len(regressions) == 0
    
    def test_severity_classification(self):
        """Test severity classification for different drop amounts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Test critical (>= 10%)
            assert tracker._calculate_severity(0.15) == "critical"
            assert tracker._calculate_severity(0.10) == "critical"
            
            # Test high (5-10%)
            assert tracker._calculate_severity(0.08) == "high"
            assert tracker._calculate_severity(0.05) == "high"
            
            # Test medium (2-5%)
            assert tracker._calculate_severity(0.04) == "medium"
            assert tracker._calculate_severity(0.02) == "medium"
            
            # Test low (< 2%)
            assert tracker._calculate_severity(0.015) == "low"
            assert tracker._calculate_severity(0.01) == "low"
    
    def test_trend_analysis_improving(self):
        """Test trend analysis detects improving coverage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Create snapshots with improving coverage
            base_time = datetime.now()
            snapshots = []
            for i in range(5):
                coverage = CoverageData(
                    line_coverage=0.60 + i * 0.05,  # Improving from 60% to 80%
                    branch_coverage=0.50 + i * 0.05,
                    function_coverage=0.55 + i * 0.05,
                    covered_lines=[],
                    uncovered_lines=[],
                    covered_branches=[],
                    uncovered_branches=[]
                )
                timestamp = (base_time + timedelta(hours=i)).isoformat()
                snapshots.append(CoverageSnapshot(
                    timestamp=timestamp,
                    coverage_data=coverage
                ))
            
            analysis = tracker.analyze_trend(snapshots)
            
            assert analysis.trend_direction == TrendDirection.IMPROVING
            assert analysis.line_coverage_change > 0.01
            assert analysis.num_snapshots == 5
    
    def test_trend_analysis_declining(self):
        """Test trend analysis detects declining coverage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Create snapshots with declining coverage
            base_time = datetime.now()
            snapshots = []
            for i in range(5):
                coverage = CoverageData(
                    line_coverage=0.80 - i * 0.05,  # Declining from 80% to 60%
                    branch_coverage=0.70 - i * 0.05,
                    function_coverage=0.75 - i * 0.05,
                    covered_lines=[],
                    uncovered_lines=[],
                    covered_branches=[],
                    uncovered_branches=[]
                )
                timestamp = (base_time + timedelta(hours=i)).isoformat()
                snapshots.append(CoverageSnapshot(
                    timestamp=timestamp,
                    coverage_data=coverage
                ))
            
            analysis = tracker.analyze_trend(snapshots)
            
            assert analysis.trend_direction == TrendDirection.DECLINING
            assert analysis.line_coverage_change < -0.01
    
    def test_trend_analysis_stable(self):
        """Test trend analysis detects stable coverage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Create snapshots with stable coverage
            base_time = datetime.now()
            snapshots = []
            for i in range(5):
                coverage = CoverageData(
                    line_coverage=0.75,  # Stable at 75%
                    branch_coverage=0.65,
                    function_coverage=0.70,
                    covered_lines=[],
                    uncovered_lines=[],
                    covered_branches=[],
                    uncovered_branches=[]
                )
                timestamp = (base_time + timedelta(hours=i)).isoformat()
                snapshots.append(CoverageSnapshot(
                    timestamp=timestamp,
                    coverage_data=coverage
                ))
            
            analysis = tracker.analyze_trend(snapshots)
            
            assert analysis.trend_direction == TrendDirection.STABLE
            assert abs(analysis.line_coverage_change) <= 0.01
    
    def test_branch_filtering(self):
        """Test filtering history by branch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            coverage = CoverageData(
                line_coverage=0.75,
                branch_coverage=0.65,
                function_coverage=0.70,
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            # Store snapshots for different branches
            tracker.store_snapshot(coverage, branch="main")
            tracker.store_snapshot(coverage, branch="develop")
            tracker.store_snapshot(coverage, branch="main")
            
            # Filter by main branch
            main_history = tracker.get_history(branch="main")
            assert len(main_history) == 2
            assert all(s.branch == "main" for s in main_history)
            
            # Filter by develop branch
            develop_history = tracker.get_history(branch="develop")
            assert len(develop_history) == 1
            assert develop_history[0].branch == "develop"
    
    def test_history_limit(self):
        """Test limiting the number of returned snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            coverage = CoverageData(
                line_coverage=0.75,
                branch_coverage=0.65,
                function_coverage=0.70,
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            # Store 10 snapshots
            for i in range(10):
                tracker.store_snapshot(coverage, build_id=f"build-{i}")
            
            # Retrieve with limit
            history = tracker.get_history(limit=5)
            assert len(history) == 5
    
    def test_clear_history_all(self):
        """Test clearing all history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            coverage = CoverageData(
                line_coverage=0.75,
                branch_coverage=0.65,
                function_coverage=0.70,
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            # Store some snapshots
            for i in range(5):
                tracker.store_snapshot(coverage)
            
            # Clear all
            removed = tracker.clear_history()
            assert removed == 5
            
            # Verify empty
            history = tracker.get_history()
            assert len(history) == 0
    
    def test_clear_history_by_branch(self):
        """Test clearing history for a specific branch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            coverage = CoverageData(
                line_coverage=0.75,
                branch_coverage=0.65,
                function_coverage=0.70,
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            # Store snapshots for different branches
            tracker.store_snapshot(coverage, branch="main")
            tracker.store_snapshot(coverage, branch="main")
            tracker.store_snapshot(coverage, branch="develop")
            
            # Clear only main branch
            removed = tracker.clear_history(branch="main")
            assert removed == 2
            
            # Verify develop branch still exists
            history = tracker.get_history()
            assert len(history) == 1
            assert history[0].branch == "develop"
    
    def test_visualization_generation(self):
        """Test generating trend visualization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Create some snapshots
            base_time = datetime.now()
            for i in range(5):
                coverage = CoverageData(
                    line_coverage=0.70 + i * 0.02,
                    branch_coverage=0.60 + i * 0.02,
                    function_coverage=0.65 + i * 0.02,
                    covered_lines=[],
                    uncovered_lines=[],
                    covered_branches=[],
                    uncovered_branches=[]
                )
                timestamp = (base_time + timedelta(hours=i)).isoformat()
                snapshot = CoverageSnapshot(
                    timestamp=timestamp,
                    coverage_data=coverage
                )
                tracker.store_snapshot(
                    coverage,
                    commit_hash=f"commit{i}"
                )
            
            # Generate visualization
            history = tracker.get_history()
            viz = tracker.generate_trend_visualization(history)
            
            assert "COVERAGE TREND VISUALIZATION" in viz
            assert "Line Coverage Trend:" in viz
            assert "Branch Coverage Trend:" in viz
            assert "Function Coverage Trend:" in viz
            assert "TREND SUMMARY" in viz
    
    def test_regression_detection_with_no_baseline(self):
        """Test regression detection when no baseline exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            current = CoverageData(
                line_coverage=0.70,
                branch_coverage=0.60,
                function_coverage=0.65,
                covered_lines=[],
                uncovered_lines=[],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            # No baseline stored, should return empty list
            regressions = tracker.detect_regression(current, baseline_coverage=None)
            assert len(regressions) == 0
    
    def test_snapshot_serialization(self):
        """Test snapshot to_dict and from_dict."""
        coverage = CoverageData(
            line_coverage=0.85,
            branch_coverage=0.75,
            function_coverage=0.80,
            covered_lines=["file.c:1"],
            uncovered_lines=["file.c:2"],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        snapshot = CoverageSnapshot(
            timestamp="2025-01-01T00:00:00",
            coverage_data=coverage,
            commit_hash="abc123",
            branch="main",
            build_id="build-001"
        )
        
        # Serialize
        data = snapshot.to_dict()
        assert data['timestamp'] == "2025-01-01T00:00:00"
        assert data['commit_hash'] == "abc123"
        assert data['branch'] == "main"
        
        # Deserialize
        restored = CoverageSnapshot.from_dict(data)
        assert restored.timestamp == snapshot.timestamp
        assert restored.commit_hash == snapshot.commit_hash
        assert restored.coverage_data.line_coverage == coverage.line_coverage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
