#!/usr/bin/env python3
"""Example demonstrating coverage trend tracking functionality.

This example shows how to:
1. Store coverage snapshots over time
2. Detect coverage regressions
3. Analyze coverage trends
4. Generate trend visualizations
"""

import tempfile
from datetime import datetime, timedelta

from analysis.coverage_trend_tracker import CoverageTrendTracker
from ai_generator.models import CoverageData


def main():
    """Demonstrate coverage trend tracking."""
    
    print("=" * 80)
    print("COVERAGE TREND TRACKING EXAMPLE")
    print("=" * 80)
    
    # Create a temporary directory for this example
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = CoverageTrendTracker(storage_dir=tmpdir)
        
        # Simulate a series of builds with varying coverage
        print("\n1. Storing coverage snapshots over time...")
        print("-" * 80)
        
        base_time = datetime.now()
        commits = [
            ("abc123", 0.85, 0.75, 0.80, "Initial implementation"),
            ("def456", 0.87, 0.77, 0.82, "Added more tests"),
            ("ghi789", 0.89, 0.79, 0.84, "Improved test coverage"),
            ("jkl012", 0.83, 0.73, 0.78, "Refactoring - some tests removed"),
            ("mno345", 0.85, 0.75, 0.80, "Added back missing tests"),
        ]
        
        for i, (commit, line_cov, branch_cov, func_cov, message) in enumerate(commits):
            coverage = CoverageData(
                line_coverage=line_cov,
                branch_coverage=branch_cov,
                function_coverage=func_cov,
                covered_lines=[f"file{j}.c:{k}" for j in range(5) for k in range(int(line_cov * 100))],
                uncovered_lines=[f"file{j}.c:{k}" for j in range(5) for k in range(int(line_cov * 100), 100)],
                covered_branches=[],
                uncovered_branches=[]
            )
            
            snapshot = tracker.store_snapshot(
                coverage,
                commit_hash=commit,
                branch="main",
                build_id=f"build-{i+1}",
                metadata={"message": message}
            )
            
            print(f"  Commit {commit[:7]}: Line={line_cov:.1%}, Branch={branch_cov:.1%}, "
                  f"Function={func_cov:.1%} - {message}")
        
        # Retrieve and display history
        print("\n2. Retrieving coverage history...")
        print("-" * 80)
        history = tracker.get_history(limit=10)
        print(f"  Retrieved {len(history)} snapshots from history")
        
        # Detect regressions
        print("\n3. Detecting coverage regressions...")
        print("-" * 80)
        
        # Compare commit 4 (jkl012) with commit 3 (ghi789) - should detect regression
        baseline_coverage = CoverageData(
            line_coverage=0.89,
            branch_coverage=0.79,
            function_coverage=0.84,
            covered_lines=[],
            uncovered_lines=[],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        current_coverage = CoverageData(
            line_coverage=0.83,
            branch_coverage=0.73,
            function_coverage=0.78,
            covered_lines=[],
            uncovered_lines=[],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        regressions = tracker.detect_regression(current_coverage, baseline_coverage, threshold=0.01)
        
        if regressions:
            print(f"  ⚠️  Detected {len(regressions)} regression(s):")
            for reg in regressions:
                print(f"    - {reg.regression_type.capitalize()} coverage: "
                      f"{reg.previous_coverage:.2%} → {reg.current_coverage:.2%} "
                      f"(drop: {reg.coverage_drop:.2%}, severity: {reg.severity})")
        else:
            print("  ✓ No regressions detected")
        
        # Analyze trends
        print("\n4. Analyzing coverage trends...")
        print("-" * 80)
        
        analysis = tracker.analyze_trend(history)
        
        print(f"  Trend Direction: {analysis.trend_direction.value.upper()}")
        print(f"  Number of Snapshots: {analysis.num_snapshots}")
        print(f"  Time Span: {analysis.time_span_days:.2f} days")
        print(f"\n  Average Coverage:")
        print(f"    - Line: {analysis.average_line_coverage:.2%}")
        print(f"    - Branch: {analysis.average_branch_coverage:.2%}")
        print(f"    - Function: {analysis.average_function_coverage:.2%}")
        print(f"\n  Coverage Change (first to last):")
        print(f"    - Line: {analysis.line_coverage_change:+.2%}")
        print(f"    - Branch: {analysis.branch_coverage_change:+.2%}")
        print(f"    - Function: {analysis.function_coverage_change:+.2%}")
        
        if analysis.regressions:
            print(f"\n  Regressions in History: {len(analysis.regressions)}")
            for reg in analysis.regressions[:3]:  # Show first 3
                print(f"    - {reg.regression_type.capitalize()}: "
                      f"{reg.previous_coverage:.2%} → {reg.current_coverage:.2%} "
                      f"at commit {reg.commit_hash[:7] if reg.commit_hash else 'unknown'}")
        
        # Generate visualization
        print("\n5. Generating trend visualization...")
        print("-" * 80)
        
        viz = tracker.generate_trend_visualization(history)
        print(viz)
        
        # Demonstrate branch filtering
        print("\n6. Branch-specific history...")
        print("-" * 80)
        
        # Add some snapshots for a different branch
        develop_coverage = CoverageData(
            line_coverage=0.70,
            branch_coverage=0.60,
            function_coverage=0.65,
            covered_lines=[],
            uncovered_lines=[],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        tracker.store_snapshot(develop_coverage, commit_hash="xyz789", branch="develop")
        
        main_history = tracker.get_history(branch="main")
        develop_history = tracker.get_history(branch="develop")
        
        print(f"  Main branch: {len(main_history)} snapshots")
        print(f"  Develop branch: {len(develop_history)} snapshots")
        
        # Demonstrate clearing history
        print("\n7. History management...")
        print("-" * 80)
        
        total_before = len(tracker.get_history())
        print(f"  Total snapshots before clear: {total_before}")
        
        # Clear only develop branch
        removed = tracker.clear_history(branch="develop")
        print(f"  Removed {removed} snapshots from develop branch")
        
        total_after = len(tracker.get_history())
        print(f"  Total snapshots after clear: {total_after}")
        
        print("\n" + "=" * 80)
        print("EXAMPLE COMPLETE")
        print("=" * 80)
        print("\nKey Takeaways:")
        print("  • Coverage snapshots track metrics over time")
        print("  • Regressions are automatically detected with configurable thresholds")
        print("  • Trend analysis provides insights into coverage evolution")
        print("  • Visualizations help understand coverage patterns")
        print("  • Branch-specific tracking enables parallel development workflows")


if __name__ == "__main__":
    main()
