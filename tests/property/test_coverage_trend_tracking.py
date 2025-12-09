"""Property-based tests for coverage trend tracking.

**Feature: agentic-kernel-testing, Property 29: Coverage regression detection**
**Validates: Requirements 6.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path

from analysis.coverage_trend_tracker import (
    CoverageTrendTracker,
    CoverageSnapshot,
    CoverageRegression,
    TrendDirection
)
from ai_generator.models import CoverageData


# Custom strategies for generating test data
@st.composite
def coverage_data_strategy(draw, min_coverage=0.0, max_coverage=1.0):
    """Generate valid CoverageData objects."""
    line_cov = draw(st.floats(min_value=min_coverage, max_value=max_coverage))
    branch_cov = draw(st.floats(min_value=min_coverage, max_value=max_coverage))
    function_cov = draw(st.floats(min_value=min_coverage, max_value=max_coverage))
    
    # Generate some covered/uncovered lines
    num_covered_lines = draw(st.integers(min_value=0, max_value=100))
    num_uncovered_lines = draw(st.integers(min_value=0, max_value=100))
    
    covered_lines = [f"file{i % 5}.c:{i}" for i in range(num_covered_lines)]
    uncovered_lines = [f"file{i % 5}.c:{i + 1000}" for i in range(num_uncovered_lines)]
    
    return CoverageData(
        line_coverage=line_cov,
        branch_coverage=branch_cov,
        function_coverage=function_cov,
        covered_lines=covered_lines,
        uncovered_lines=uncovered_lines,
        covered_branches=[],
        uncovered_branches=[]
    )


@st.composite
def coverage_snapshot_strategy(draw, base_time=None):
    """Generate valid CoverageSnapshot objects."""
    if base_time is None:
        base_time = datetime.now()
    
    # Generate timestamp within a reasonable range
    offset_seconds = draw(st.integers(min_value=0, max_value=86400 * 30))  # Up to 30 days
    timestamp = (base_time + timedelta(seconds=offset_seconds)).isoformat()
    
    coverage_data = draw(coverage_data_strategy())
    commit_hash = draw(st.one_of(st.none(), st.text(min_size=40, max_size=40, alphabet='0123456789abcdef')))
    branch = draw(st.one_of(st.none(), st.sampled_from(['main', 'develop', 'feature/test'])))
    build_id = draw(st.one_of(st.none(), st.text(min_size=5, max_size=20)))
    
    return CoverageSnapshot(
        timestamp=timestamp,
        coverage_data=coverage_data,
        commit_hash=commit_hash,
        branch=branch,
        build_id=build_id
    )


@st.composite
def decreasing_coverage_pair_strategy(draw):
    """Generate a pair of coverage data where the second has lower coverage."""
    # Generate baseline with reasonable coverage
    baseline_line = draw(st.floats(min_value=0.3, max_value=1.0))
    baseline_branch = draw(st.floats(min_value=0.3, max_value=1.0))
    baseline_function = draw(st.floats(min_value=0.3, max_value=1.0))
    
    baseline = CoverageData(
        line_coverage=baseline_line,
        branch_coverage=baseline_branch,
        function_coverage=baseline_function,
        covered_lines=[f"file.c:{i}" for i in range(100)],
        uncovered_lines=[f"file.c:{i}" for i in range(100, 110)],
        covered_branches=[],
        uncovered_branches=[]
    )
    
    # Generate current with lower coverage (at least 2% drop to ensure regression)
    drop_amount = draw(st.floats(min_value=0.02, max_value=0.3))
    
    current = CoverageData(
        line_coverage=max(0.0, baseline_line - drop_amount),
        branch_coverage=max(0.0, baseline_branch - drop_amount),
        function_coverage=max(0.0, baseline_function - drop_amount),
        covered_lines=[f"file.c:{i}" for i in range(90)],  # Fewer covered lines
        uncovered_lines=[f"file.c:{i}" for i in range(90, 110)],
        covered_branches=[],
        uncovered_branches=[]
    )
    
    return baseline, current


class TestCoverageRegressionDetection:
    """Property-based tests for coverage regression detection."""
    
    @given(baseline=coverage_data_strategy(), current=coverage_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_regression_detection_consistency(self, baseline, current):
        """Property 29: Coverage regression detection.
        
        For any two coverage measurements, if the current coverage is lower than
        the baseline by more than the threshold, a regression should be detected.
        
        **Validates: Requirements 6.4**
        """
        # Create temporary directory for tracker
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Detect regressions with 1% threshold
            threshold = 0.01
            regressions = tracker.detect_regression(current, baseline, threshold)
            
            # Calculate actual drops
            line_drop = baseline.line_coverage - current.line_coverage
            branch_drop = baseline.branch_coverage - current.branch_coverage
            function_drop = baseline.function_coverage - current.function_coverage
            
            # Verify line coverage regression detection
            line_regression_found = any(r.regression_type == 'line' for r in regressions)
            if line_drop > threshold:
                assert line_regression_found, \
                    f"Line coverage dropped by {line_drop:.4f} but no regression detected"
                
                # Find the line regression
                line_reg = next(r for r in regressions if r.regression_type == 'line')
                assert abs(line_reg.coverage_drop - line_drop) < 0.0001, \
                    "Regression coverage drop doesn't match actual drop"
                assert line_reg.previous_coverage == baseline.line_coverage
                assert line_reg.current_coverage == current.line_coverage
            else:
                assert not line_regression_found, \
                    f"Line coverage dropped by {line_drop:.4f} (below threshold) but regression detected"
            
            # Verify branch coverage regression detection
            branch_regression_found = any(r.regression_type == 'branch' for r in regressions)
            if branch_drop > threshold:
                assert branch_regression_found, \
                    f"Branch coverage dropped by {branch_drop:.4f} but no regression detected"
                
                branch_reg = next(r for r in regressions if r.regression_type == 'branch')
                assert abs(branch_reg.coverage_drop - branch_drop) < 0.0001
                assert branch_reg.previous_coverage == baseline.branch_coverage
                assert branch_reg.current_coverage == current.branch_coverage
            else:
                assert not branch_regression_found, \
                    f"Branch coverage dropped by {branch_drop:.4f} (below threshold) but regression detected"
            
            # Verify function coverage regression detection
            function_regression_found = any(r.regression_type == 'function' for r in regressions)
            if function_drop > threshold:
                assert function_regression_found, \
                    f"Function coverage dropped by {function_drop:.4f} but no regression detected"
                
                function_reg = next(r for r in regressions if r.regression_type == 'function')
                assert abs(function_reg.coverage_drop - function_drop) < 0.0001
                assert function_reg.previous_coverage == baseline.function_coverage
                assert function_reg.current_coverage == current.function_coverage
            else:
                assert not function_regression_found, \
                    f"Function coverage dropped by {function_drop:.4f} (below threshold) but regression detected"
    
    @given(baseline=coverage_data_strategy(), current=coverage_data_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_no_false_positives_for_improvements(self, baseline, current):
        """Verify that coverage improvements are not flagged as regressions.
        
        For any two coverage measurements where current >= baseline,
        no regressions should be detected.
        """
        # Only test cases where coverage improved or stayed the same
        assume(current.line_coverage >= baseline.line_coverage)
        assume(current.branch_coverage >= baseline.branch_coverage)
        assume(current.function_coverage >= baseline.function_coverage)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            regressions = tracker.detect_regression(current, baseline, threshold=0.01)
            
            # No regressions should be detected when coverage improves
            assert len(regressions) == 0, \
                f"Coverage improved but {len(regressions)} regressions detected"
    
    @given(data=decreasing_coverage_pair_strategy())
    @settings(max_examples=100, deadline=None)
    def test_regression_severity_classification(self, data):
        """Verify that regression severity is correctly classified based on drop amount.
        
        For any coverage regression, the severity should match the magnitude of the drop.
        """
        baseline, current = data
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            regressions = tracker.detect_regression(current, baseline, threshold=0.01)
            
            # Should have detected regressions since we forced a drop
            assert len(regressions) > 0, "No regressions detected despite coverage drop"
            
            for regression in regressions:
                drop = regression.coverage_drop
                severity = regression.severity
                
                # Verify severity matches drop amount
                if drop >= 0.10:
                    assert severity == "critical", \
                        f"Drop of {drop:.2%} should be critical, got {severity}"
                elif drop >= 0.05:
                    assert severity == "high", \
                        f"Drop of {drop:.2%} should be high, got {severity}"
                elif drop >= 0.02:
                    assert severity == "medium", \
                        f"Drop of {drop:.2%} should be medium, got {severity}"
                else:
                    assert severity == "low", \
                        f"Drop of {drop:.2%} should be low, got {severity}"
    
    @given(snapshots=st.lists(coverage_snapshot_strategy(), min_size=2, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_snapshot_storage_and_retrieval(self, snapshots):
        """Verify that coverage snapshots can be stored and retrieved correctly.
        
        For any list of coverage snapshots, storing and retrieving them
        should preserve all data.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Store all snapshots
            for snapshot in snapshots:
                tracker.store_snapshot(
                    snapshot.coverage_data,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch,
                    build_id=snapshot.build_id,
                    metadata=snapshot.metadata
                )
            
            # Retrieve history
            retrieved = tracker.get_history()
            
            # Should have at least as many snapshots as we stored
            assert len(retrieved) >= len(snapshots), \
                f"Stored {len(snapshots)} snapshots but retrieved {len(retrieved)}"
            
            # Verify the most recent snapshots match what we stored
            for i, original in enumerate(reversed(snapshots)):
                if i >= len(retrieved):
                    break
                
                retrieved_snapshot = retrieved[i]
                
                # Verify coverage data matches
                assert abs(retrieved_snapshot.coverage_data.line_coverage - 
                          original.coverage_data.line_coverage) < 0.0001
                assert abs(retrieved_snapshot.coverage_data.branch_coverage - 
                          original.coverage_data.branch_coverage) < 0.0001
                assert abs(retrieved_snapshot.coverage_data.function_coverage - 
                          original.coverage_data.function_coverage) < 0.0001
    
    @given(snapshots=st.lists(coverage_snapshot_strategy(), min_size=3, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_trend_analysis_completeness(self, snapshots):
        """Verify that trend analysis includes all required metrics.
        
        For any list of coverage snapshots, the trend analysis should include
        averages, changes, and trend direction.
        """
        # Ensure snapshots have increasing timestamps
        base_time = datetime.now()
        for i, snapshot in enumerate(snapshots):
            snapshot.timestamp = (base_time + timedelta(hours=i)).isoformat()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Analyze trend
            analysis = tracker.analyze_trend(snapshots)
            
            # Verify all required fields are present
            assert analysis.num_snapshots == len(snapshots)
            assert 0.0 <= analysis.average_line_coverage <= 1.0
            assert 0.0 <= analysis.average_branch_coverage <= 1.0
            assert 0.0 <= analysis.average_function_coverage <= 1.0
            assert -1.0 <= analysis.line_coverage_change <= 1.0
            assert -1.0 <= analysis.branch_coverage_change <= 1.0
            assert -1.0 <= analysis.function_coverage_change <= 1.0
            assert analysis.time_span_days >= 0
            assert analysis.trend_direction in [TrendDirection.IMPROVING, 
                                               TrendDirection.STABLE, 
                                               TrendDirection.DECLINING]
            
            # Verify averages are actually averages
            expected_avg_line = sum(s.coverage_data.line_coverage for s in snapshots) / len(snapshots)
            assert abs(analysis.average_line_coverage - expected_avg_line) < 0.0001
            
            # Verify changes match first to last
            expected_line_change = (snapshots[-1].coverage_data.line_coverage - 
                                   snapshots[0].coverage_data.line_coverage)
            assert abs(analysis.line_coverage_change - expected_line_change) < 0.0001
    
    @given(
        snapshots=st.lists(coverage_snapshot_strategy(), min_size=2, max_size=10),
        branch_name=st.sampled_from(['main', 'develop', 'feature/test'])
    )
    @settings(max_examples=100, deadline=None)
    def test_branch_filtering(self, snapshots, branch_name):
        """Verify that history can be filtered by branch.
        
        For any list of snapshots with different branches, filtering by a specific
        branch should return only snapshots from that branch.
        """
        # Assign branches to snapshots
        for snapshot in snapshots:
            snapshot.branch = branch_name if hash(snapshot.timestamp) % 2 == 0 else 'other-branch'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Store all snapshots
            for snapshot in snapshots:
                tracker.store_snapshot(
                    snapshot.coverage_data,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch,
                    build_id=snapshot.build_id
                )
            
            # Retrieve with branch filter
            filtered = tracker.get_history(branch=branch_name)
            
            # All retrieved snapshots should be from the specified branch
            for snapshot in filtered:
                assert snapshot.branch == branch_name, \
                    f"Expected branch {branch_name}, got {snapshot.branch}"
    
    @given(coverage=coverage_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_regression_detection_with_no_baseline(self, coverage):
        """Verify that regression detection handles missing baseline gracefully.
        
        For any coverage data, if no baseline exists, no regressions should be detected.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Detect regressions without storing any baseline
            regressions = tracker.detect_regression(coverage, baseline_coverage=None)
            
            # Should return empty list when no baseline available
            assert len(regressions) == 0, \
                "Regressions detected without baseline"
    
    @given(
        snapshots=st.lists(coverage_snapshot_strategy(), min_size=5, max_size=15),
        limit=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_history_limit(self, snapshots, limit):
        """Verify that history retrieval respects the limit parameter.
        
        For any list of snapshots and a limit value, retrieving history with that
        limit should return at most that many snapshots.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = CoverageTrendTracker(storage_dir=tmpdir)
            
            # Store all snapshots
            for snapshot in snapshots:
                tracker.store_snapshot(
                    snapshot.coverage_data,
                    commit_hash=snapshot.commit_hash,
                    branch=snapshot.branch,
                    build_id=snapshot.build_id
                )
            
            # Retrieve with limit
            retrieved = tracker.get_history(limit=limit)
            
            # Should not exceed limit
            assert len(retrieved) <= limit, \
                f"Retrieved {len(retrieved)} snapshots but limit was {limit}"
            
            # Should return exactly limit if we have enough snapshots
            if len(snapshots) >= limit:
                assert len(retrieved) == limit, \
                    f"Expected {limit} snapshots but got {len(retrieved)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
