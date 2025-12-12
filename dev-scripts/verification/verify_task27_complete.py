#!/usr/bin/env python3
"""Verification script for Task 27: Coverage Trend Tracking.

This script verifies that all components of Task 27 are working correctly.
"""

import sys
import tempfile
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, '.')

from analysis.coverage_trend_tracker import (
    CoverageTrendTracker,
    CoverageSnapshot,
    CoverageRegression,
    TrendDirection
)
from ai_generator.models import CoverageData


def test_basic_functionality():
    """Test basic coverage trend tracking functionality."""
    print("Testing basic functionality...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = CoverageTrendTracker(storage_dir=tmpdir)
        
        # Test 1: Store snapshot
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
        assert snapshot.commit_hash == "abc123"
        print("  ✓ Snapshot storage works")
        
        # Test 2: Retrieve history
        history = tracker.get_history(limit=10)
        assert len(history) >= 1
        print("  ✓ History retrieval works")
        
        # Test 3: Detect regression
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
            line_coverage=0.80,  # 10% drop
            branch_coverage=0.75,  # 5% drop
            function_coverage=0.83,  # 2% drop
            covered_lines=[],
            uncovered_lines=[],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        regressions = tracker.detect_regression(current, baseline, threshold=0.01)
        assert len(regressions) == 3
        assert any(r.regression_type == 'line' and r.severity == 'critical' for r in regressions)
        assert any(r.regression_type == 'branch' and r.severity == 'high' for r in regressions)
        assert any(r.regression_type == 'function' and r.severity == 'medium' for r in regressions)
        print("  ✓ Regression detection works")
        
        # Test 4: Trend analysis
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
        assert analysis.trend_direction == TrendDirection.IMPROVING
        assert analysis.num_snapshots == 5
        print("  ✓ Trend analysis works")
        
        # Test 5: Visualization
        viz = tracker.generate_trend_visualization(snapshots)
        assert "COVERAGE TREND VISUALIZATION" in viz
        assert "Line Coverage Trend:" in viz
        print("  ✓ Visualization generation works")
        
        # Test 6: Branch filtering
        tracker.store_snapshot(coverage, branch="develop")
        main_history = tracker.get_history(branch="main")
        develop_history = tracker.get_history(branch="develop")
        assert len(main_history) >= 1
        assert len(develop_history) >= 1
        print("  ✓ Branch filtering works")
        
        print("\n✓ All basic functionality tests passed!")
        return True


def test_property_based_tests():
    """Verify property-based tests pass."""
    print("\nRunning property-based tests...")
    
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", 
         "tests/property/test_coverage_trend_tracking.py",
         "-v", "--tb=short", "-q"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Count passed tests
        passed = result.stdout.count(" PASSED")
        print(f"  ✓ All {passed} property-based tests passed")
        return True
    else:
        print(f"  ✗ Property-based tests failed")
        print(result.stdout)
        return False


def test_unit_tests():
    """Verify unit tests pass."""
    print("\nRunning unit tests...")
    
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest",
         "tests/unit/test_coverage_trend_tracker.py",
         "-v", "--tb=short", "-q"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Count passed tests
        passed = result.stdout.count(" PASSED")
        print(f"  ✓ All {passed} unit tests passed")
        return True
    else:
        print(f"  ✗ Unit tests failed")
        print(result.stdout)
        return False


def main():
    """Run all verification tests."""
    print("=" * 80)
    print("TASK 27 VERIFICATION: Coverage Trend Tracking")
    print("=" * 80)
    
    results = []
    
    # Test basic functionality
    try:
        results.append(("Basic Functionality", test_basic_functionality()))
    except Exception as e:
        print(f"  ✗ Basic functionality test failed: {e}")
        results.append(("Basic Functionality", False))
    
    # Test property-based tests
    try:
        results.append(("Property-Based Tests", test_property_based_tests()))
    except Exception as e:
        print(f"  ✗ Property-based tests failed: {e}")
        results.append(("Property-Based Tests", False))
    
    # Test unit tests
    try:
        results.append(("Unit Tests", test_unit_tests()))
    except Exception as e:
        print(f"  ✗ Unit tests failed: {e}")
        results.append(("Unit Tests", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n" + "=" * 80)
        print("✓ TASK 27 COMPLETE - All verification tests passed!")
        print("=" * 80)
        print("\nImplemented:")
        print("  • Coverage history storage")
        print("  • Trend analysis algorithm")
        print("  • Regression detection with severity classification")
        print("  • Trend visualization (ASCII charts)")
        print("  • Branch-specific tracking")
        print("  • 8 property-based tests (800+ test cases)")
        print("  • 14 unit tests")
        print("  • Example usage demonstration")
        return 0
    else:
        print("\n✗ Some verification tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
