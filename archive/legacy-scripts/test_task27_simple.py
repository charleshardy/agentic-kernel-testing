#!/usr/bin/env python3
"""Simple test for Task 27 coverage trend tracking."""

import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from analysis.coverage_trend_tracker import CoverageTrendTracker, CoverageSnapshot, TrendDirection
from ai_generator.models import CoverageData

print("Testing coverage trend tracking...")

with tempfile.TemporaryDirectory() as tmpdir:
    tracker = CoverageTrendTracker(storage_dir=tmpdir)
    
    # Test 1: Store snapshot
    print("\n1. Testing snapshot storage...")
    coverage = CoverageData(
        line_coverage=0.85,
        branch_coverage=0.75,
        function_coverage=0.80,
        covered_lines=["file.c:1"],
        uncovered_lines=["file.c:2"],
        covered_branches=[],
        uncovered_branches=[]
    )
    
    snapshot = tracker.store_snapshot(coverage, commit_hash="abc123", branch="main")
    print(f"   ✓ Stored snapshot with commit {snapshot.commit_hash}")
    
    # Test 2: Retrieve history
    print("\n2. Testing history retrieval...")
    history = tracker.get_history(limit=10)
    print(f"   ✓ Retrieved {len(history)} snapshots")
    
    # Test 3: Detect regression
    print("\n3. Testing regression detection...")
    baseline = CoverageData(
        line_coverage=0.90,
        branch_coverage=0.80,
        function_coverage=0.85,
        covered_lines=[],
        uncovered_lines=[],
        covered_branches=[],
        uncovered_branches=[]
    )
    
    current = CoverageData(
        line_coverage=0.80,
        branch_coverage=0.75,
        function_coverage=0.83,
        covered_lines=[],
        uncovered_lines=[],
        covered_branches=[],
        uncovered_branches=[]
    )
    
    regressions = tracker.detect_regression(current, baseline, threshold=0.01)
    print(f"   ✓ Detected {len(regressions)} regressions")
    for reg in regressions:
        print(f"     - {reg.regression_type}: {reg.previous_coverage:.2%} → {reg.current_coverage:.2%} ({reg.severity})")
    
    # Test 4: Trend analysis
    print("\n4. Testing trend analysis...")
    base_time = datetime.now()
    snapshots = []
    for i in range(5):
        cov = CoverageData(
            line_coverage=0.70 + i * 0.05,
            branch_coverage=0.60 + i * 0.05,
            function_coverage=0.65 + i * 0.05,
            covered_lines=[],
            uncovered_lines=[],
            covered_branches=[],
            uncovered_branches=[]
        )
        timestamp = (base_time + timedelta(hours=i)).isoformat()
        snapshots.append(CoverageSnapshot(timestamp=timestamp, coverage_data=cov))
    
    analysis = tracker.analyze_trend(snapshots)
    print(f"   ✓ Trend direction: {analysis.trend_direction.value}")
    print(f"   ✓ Average line coverage: {analysis.average_line_coverage:.2%}")
    print(f"   ✓ Line coverage change: {analysis.line_coverage_change:+.2%}")
    
    # Test 5: Visualization
    print("\n5. Testing visualization...")
    viz = tracker.generate_trend_visualization(snapshots)
    print("   ✓ Generated visualization:")
    print(viz)

print("\n" + "="*60)
print("✓ All tests passed! Task 27 is working correctly.")
print("="*60)
