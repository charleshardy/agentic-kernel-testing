"""Example demonstrating gap-targeted test generation.

This example shows how to:
1. Identify coverage gaps from coverage data
2. Generate tests targeting those gaps
3. Verify that tests cover the intended gaps
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_generator.gap_targeted_generator import GapTargetedTestGenerator
from ai_generator.models import CoverageData
from analysis.coverage_analyzer import CoverageAnalyzer, CoverageGap, GapType, GapPriority


def example_gap_targeted_generation():
    """Demonstrate gap-targeted test generation."""
    
    print("=" * 80)
    print("GAP-TARGETED TEST GENERATION EXAMPLE")
    print("=" * 80)
    
    # Step 1: Create sample coverage data with gaps
    print("\n1. Creating sample coverage data with gaps...")
    coverage_data = CoverageData(
        line_coverage=0.75,
        branch_coverage=0.60,
        function_coverage=0.80,
        covered_lines=[
            "kernel/sched/core.c:100",
            "kernel/sched/core.c:101",
            "kernel/sched/core.c:102"
        ],
        uncovered_lines=[
            "kernel/sched/core.c:150",
            "kernel/sched/core.c:151",
            "fs/ext4/inode.c:200"
        ],
        covered_branches=[
            "kernel/sched/core.c:100:0",
            "kernel/sched/core.c:100:1"
        ],
        uncovered_branches=[
            "kernel/sched/core.c:150:0",
            "fs/ext4/inode.c:200:1"
        ]
    )
    
    print(f"   Line coverage: {coverage_data.line_coverage:.1%}")
    print(f"   Branch coverage: {coverage_data.branch_coverage:.1%}")
    print(f"   Uncovered lines: {len(coverage_data.uncovered_lines)}")
    print(f"   Uncovered branches: {len(coverage_data.uncovered_branches)}")
    
    # Step 2: Identify coverage gaps
    print("\n2. Identifying coverage gaps...")
    analyzer = CoverageAnalyzer()
    gaps = analyzer.identify_coverage_gaps(coverage_data)
    
    print(f"   Found {len(gaps)} coverage gaps")
    for i, gap in enumerate(gaps[:5], 1):
        print(f"   {i}. {gap}")
    
    # Step 3: Prioritize gaps
    print("\n3. Prioritizing gaps by importance...")
    prioritized_gaps = analyzer.prioritize_gaps(gaps)
    
    print(f"   Prioritized {len(prioritized_gaps)} gaps")
    for priority in [GapPriority.CRITICAL, GapPriority.HIGH, GapPriority.MEDIUM, GapPriority.LOW]:
        count = sum(1 for g in prioritized_gaps if g.priority == priority)
        if count > 0:
            print(f"   {priority.value.upper()}: {count} gaps")
    
    # Step 4: Generate tests for high-priority gaps
    print("\n4. Generating tests for high-priority gaps...")
    generator = GapTargetedTestGenerator()
    
    # Take top 3 gaps for demonstration
    target_gaps = prioritized_gaps[:3]
    test_cases = generator.generate_tests_for_gaps(target_gaps)
    
    print(f"   Generated {len(test_cases)} test cases")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_case.name}")
        print(f"   - ID: {test_case.id}")
        print(f"   - Subsystem: {test_case.target_subsystem}")
        print(f"   - Code paths: {test_case.code_paths}")
        print(f"   - Gap targeted: {test_case.metadata.get('gap_targeted')}")
        
        target_gap = test_case.metadata.get('target_gap', {})
        print(f"   - Target: {target_gap.get('file_path')}:{target_gap.get('line_number')}")
        print(f"   - Gap type: {target_gap.get('gap_type')}")
    
    # Step 5: Verify gap coverage
    print("\n5. Verifying that tests cover intended gaps...")
    for test_case, gap in zip(test_cases, target_gaps):
        covers_gap = generator.verify_gap_coverage(test_case, gap)
        status = "✓" if covers_gap else "✗"
        print(f"   {status} Test '{test_case.name}' covers gap at {gap}")
    
    # Step 6: Demonstrate path-to-test conversion
    print("\n6. Converting code paths to test cases...")
    sample_paths = [
        "kernel/sched/core.c:150",
        "fs/ext4/inode.c:200:1"
    ]
    
    for path in sample_paths:
        test_case = generator.path_to_test_case(path)
        if test_case:
            print(f"   ✓ Converted '{path}' to test: {test_case.name}")
        else:
            print(f"   ✗ Failed to convert '{path}'")
    
    # Step 7: Generate gap report
    print("\n7. Generating gap analysis report...")
    report = analyzer.generate_gap_report(prioritized_gaps)
    print("\n" + report)
    
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("- Coverage gaps are automatically identified from coverage data")
    print("- Gaps are prioritized by importance (critical subsystems, error handling, etc.)")
    print("- Tests are generated specifically targeting each gap")
    print("- Generated tests include metadata linking them to their target gaps")
    print("- Verification ensures tests actually cover the intended gaps")
    print("- System provides fallback generation when LLM is unavailable")


def example_manual_gap_creation():
    """Demonstrate creating and targeting specific gaps manually."""
    
    print("\n" + "=" * 80)
    print("MANUAL GAP TARGETING EXAMPLE")
    print("=" * 80)
    
    # Create specific gaps manually
    print("\n1. Creating specific coverage gaps...")
    
    gaps = [
        CoverageGap(
            gap_type=GapType.LINE,
            file_path="kernel/sched/core.c",
            line_number=1234,
            function_name="schedule",
            context="if (unlikely(prev->state == TASK_DEAD)) {\n    prev->sched_class->task_dead(prev);\n}",
            subsystem="scheduler",
            priority=GapPriority.CRITICAL
        ),
        CoverageGap(
            gap_type=GapType.BRANCH,
            file_path="fs/ext4/inode.c",
            line_number=567,
            branch_id=2,
            function_name="ext4_write_begin",
            context="if (flags & AOP_FLAG_NOFS) {\n    return -ENOMEM;\n}",
            subsystem="ext4",
            priority=GapPriority.HIGH
        )
    ]
    
    for gap in gaps:
        print(f"   - {gap}")
    
    # Generate tests for these specific gaps
    print("\n2. Generating targeted tests...")
    generator = GapTargetedTestGenerator()
    
    for gap in gaps:
        test_case = generator.generate_test_for_gap(gap)
        if test_case:
            print(f"\n   Generated test for {gap.gap_type.value} gap:")
            print(f"   - Name: {test_case.name}")
            print(f"   - Description: {test_case.description}")
            print(f"   - Targets: {gap.file_path}:{gap.line_number}")
            
            # Show test script preview
            script_lines = test_case.test_script.split('\n')
            print(f"   - Script preview:")
            for line in script_lines[:5]:
                print(f"     {line}")
            if len(script_lines) > 5:
                print(f"     ... ({len(script_lines) - 5} more lines)")


if __name__ == "__main__":
    # Run examples
    example_gap_targeted_generation()
    print("\n")
    example_manual_gap_creation()
