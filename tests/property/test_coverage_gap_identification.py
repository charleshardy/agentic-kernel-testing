"""Property-based tests for coverage gap identification accuracy.

**Feature: agentic-kernel-testing, Property 27: Coverage gap identification accuracy**
**Validates: Requirements 6.2**

Property: For any coverage analysis, all code paths not exercised by any test 
should be identified and reported as coverage gaps.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import os

from analysis.coverage_analyzer import (
    CoverageAnalyzer, CoverageGap, GapType, GapPriority
)
from ai_generator.models import CoverageData


# Strategy for generating CoverageData with known gaps
@st.composite
def coverage_data_with_gaps_strategy(draw):
    """Generate CoverageData with known uncovered lines and branches."""
    # Generate some covered and uncovered lines
    num_files = draw(st.integers(min_value=1, max_value=5))
    
    covered_lines = []
    uncovered_lines = []
    covered_branches = []
    uncovered_branches = []
    
    for file_idx in range(num_files):
        file_path = f"test_file_{file_idx}.c"
        
        # Generate line coverage
        num_lines = draw(st.integers(min_value=10, max_value=50))
        num_covered = draw(st.integers(min_value=0, max_value=num_lines))
        
        for line_num in range(1, num_lines + 1):
            line_ref = f"{file_path}:{line_num}"
            if line_num <= num_covered:
                covered_lines.append(line_ref)
            else:
                uncovered_lines.append(line_ref)
        
        # Generate branch coverage
        num_branches = draw(st.integers(min_value=0, max_value=20))
        num_covered_branches = draw(st.integers(min_value=0, max_value=num_branches))
        
        for branch_idx in range(num_branches):
            line_num = draw(st.integers(min_value=1, max_value=num_lines))
            branch_ref = f"{file_path}:{line_num}:{branch_idx}"
            if branch_idx < num_covered_branches:
                covered_branches.append(branch_ref)
            else:
                uncovered_branches.append(branch_ref)
    
    # Calculate coverage percentages
    total_lines = len(covered_lines) + len(uncovered_lines)
    total_branches = len(covered_branches) + len(uncovered_branches)
    
    line_coverage = len(covered_lines) / total_lines if total_lines > 0 else 0.0
    branch_coverage = len(covered_branches) / total_branches if total_branches > 0 else 0.0
    
    return CoverageData(
        line_coverage=line_coverage,
        branch_coverage=branch_coverage,
        function_coverage=0.5,  # Not relevant for this test
        covered_lines=covered_lines,
        uncovered_lines=uncovered_lines,
        covered_branches=covered_branches,
        uncovered_branches=uncovered_branches
    )


@given(coverage_data=coverage_data_with_gaps_strategy())
@settings(max_examples=100, deadline=None)
def test_all_uncovered_paths_identified(coverage_data):
    """
    Property 27: Coverage gap identification accuracy
    
    For any coverage data, all uncovered lines and branches should be 
    identified as coverage gaps.
    
    This test verifies that the gap identification process finds all
    uncovered code paths.
    """
    # Create analyzer
    analyzer = CoverageAnalyzer()
    
    # Identify gaps
    gaps = analyzer.identify_coverage_gaps(coverage_data)
    
    # Extract gap references
    gap_line_refs = set()
    gap_branch_refs = set()
    
    for gap in gaps:
        if gap.gap_type == GapType.LINE:
            gap_line_refs.add(f"{gap.file_path}:{gap.line_number}")
        elif gap.gap_type == GapType.BRANCH:
            gap_branch_refs.add(f"{gap.file_path}:{gap.line_number}:{gap.branch_id}")
    
    # Property: All uncovered lines must be identified as gaps
    uncovered_line_set = set(coverage_data.uncovered_lines)
    assert gap_line_refs == uncovered_line_set, \
        f"Gap identification missed some uncovered lines. " \
        f"Expected: {uncovered_line_set}, Got: {gap_line_refs}"
    
    # Property: All uncovered branches must be identified as gaps
    uncovered_branch_set = set(coverage_data.uncovered_branches)
    assert gap_branch_refs == uncovered_branch_set, \
        f"Gap identification missed some uncovered branches. " \
        f"Expected: {uncovered_branch_set}, Got: {gap_branch_refs}"
    
    # Property: Total number of gaps should equal uncovered lines + uncovered branches
    expected_gap_count = len(coverage_data.uncovered_lines) + len(coverage_data.uncovered_branches)
    assert len(gaps) == expected_gap_count, \
        f"Expected {expected_gap_count} gaps, but found {len(gaps)}"


@given(coverage_data=coverage_data_with_gaps_strategy())
@settings(max_examples=100, deadline=None)
def test_no_covered_paths_in_gaps(coverage_data):
    """
    Property 27: Coverage gap identification accuracy (negative test)
    
    For any coverage data, no covered lines or branches should appear
    in the identified gaps.
    """
    # Create analyzer
    analyzer = CoverageAnalyzer()
    
    # Identify gaps
    gaps = analyzer.identify_coverage_gaps(coverage_data)
    
    # Extract gap references
    gap_refs = set()
    for gap in gaps:
        if gap.gap_type == GapType.LINE:
            gap_refs.add(f"{gap.file_path}:{gap.line_number}")
        elif gap.gap_type == GapType.BRANCH:
            gap_refs.add(f"{gap.file_path}:{gap.line_number}:{gap.branch_id}")
    
    # Property: No covered lines should appear in gaps
    covered_line_set = set(coverage_data.covered_lines)
    overlap_lines = gap_refs & covered_line_set
    assert len(overlap_lines) == 0, \
        f"Covered lines incorrectly identified as gaps: {overlap_lines}"
    
    # Property: No covered branches should appear in gaps
    covered_branch_set = set(coverage_data.covered_branches)
    overlap_branches = gap_refs & covered_branch_set
    assert len(overlap_branches) == 0, \
        f"Covered branches incorrectly identified as gaps: {overlap_branches}"


@given(coverage_data=coverage_data_with_gaps_strategy())
@settings(max_examples=100, deadline=None)
def test_gap_prioritization_produces_ordered_list(coverage_data):
    """
    Property 27: Coverage gap identification accuracy (prioritization)
    
    For any set of coverage gaps, prioritization should produce an ordered
    list with critical gaps first.
    """
    # Create analyzer
    analyzer = CoverageAnalyzer()
    
    # Identify gaps
    gaps = analyzer.identify_coverage_gaps(coverage_data)
    
    # Skip if no gaps
    assume(len(gaps) > 0)
    
    # Prioritize gaps
    prioritized_gaps = analyzer.prioritize_gaps(gaps)
    
    # Property: Prioritization should return same number of gaps
    assert len(prioritized_gaps) == len(gaps), \
        "Prioritization should not add or remove gaps"
    
    # Property: All gaps should have a priority assigned
    for gap in prioritized_gaps:
        assert gap.priority is not None, "All gaps must have a priority"
        assert isinstance(gap.priority, GapPriority), "Priority must be a GapPriority enum"
    
    # Property: Gaps should be ordered by priority (critical first)
    priority_order = {
        GapPriority.CRITICAL: 0,
        GapPriority.HIGH: 1,
        GapPriority.MEDIUM: 2,
        GapPriority.LOW: 3
    }
    
    for i in range(len(prioritized_gaps) - 1):
        current_priority = priority_order[prioritized_gaps[i].priority]
        next_priority = priority_order[prioritized_gaps[i + 1].priority]
        
        # Current gap should have equal or higher priority than next
        assert current_priority <= next_priority, \
            f"Gaps not properly ordered: {prioritized_gaps[i].priority} before {prioritized_gaps[i + 1].priority}"


@given(
    num_uncovered_lines=st.integers(min_value=0, max_value=50),
    num_uncovered_branches=st.integers(min_value=0, max_value=30)
)
@settings(max_examples=100, deadline=None)
def test_gap_count_matches_uncovered_count(num_uncovered_lines, num_uncovered_branches):
    """
    Property 27: Coverage gap identification accuracy (count invariant)
    
    For any coverage data, the number of identified gaps should exactly
    equal the number of uncovered lines plus uncovered branches.
    """
    # Create coverage data with specific number of uncovered items
    uncovered_lines = [f"file.c:{i}" for i in range(1, num_uncovered_lines + 1)]
    uncovered_branches = [f"file.c:{i}:{j}" for i in range(1, 11) 
                         for j in range(num_uncovered_branches // 10 + (1 if i <= num_uncovered_branches % 10 else 0))]
    uncovered_branches = uncovered_branches[:num_uncovered_branches]
    
    coverage_data = CoverageData(
        line_coverage=0.5,
        branch_coverage=0.5,
        function_coverage=0.5,
        covered_lines=[],
        uncovered_lines=uncovered_lines,
        covered_branches=[],
        uncovered_branches=uncovered_branches
    )
    
    # Create analyzer
    analyzer = CoverageAnalyzer()
    
    # Identify gaps
    gaps = analyzer.identify_coverage_gaps(coverage_data)
    
    # Property: Number of gaps must equal uncovered lines + uncovered branches
    expected_count = num_uncovered_lines + num_uncovered_branches
    assert len(gaps) == expected_count, \
        f"Expected {expected_count} gaps, but found {len(gaps)}"


@given(coverage_data=coverage_data_with_gaps_strategy())
@settings(max_examples=100, deadline=None)
def test_gap_types_are_correct(coverage_data):
    """
    Property 27: Coverage gap identification accuracy (type correctness)
    
    For any coverage data, gaps derived from uncovered lines should have
    LINE type, and gaps from uncovered branches should have BRANCH type.
    """
    # Create analyzer
    analyzer = CoverageAnalyzer()
    
    # Identify gaps
    gaps = analyzer.identify_coverage_gaps(coverage_data)
    
    # Count gaps by type
    line_gaps = [g for g in gaps if g.gap_type == GapType.LINE]
    branch_gaps = [g for g in gaps if g.gap_type == GapType.BRANCH]
    
    # Property: Number of line gaps should equal uncovered lines
    assert len(line_gaps) == len(coverage_data.uncovered_lines), \
        f"Expected {len(coverage_data.uncovered_lines)} line gaps, got {len(line_gaps)}"
    
    # Property: Number of branch gaps should equal uncovered branches
    assert len(branch_gaps) == len(coverage_data.uncovered_branches), \
        f"Expected {len(coverage_data.uncovered_branches)} branch gaps, got {len(branch_gaps)}"
    
    # Property: Line gaps should have line_number but no branch_id
    for gap in line_gaps:
        assert gap.line_number > 0, "Line gaps must have valid line number"
        assert gap.branch_id is None, "Line gaps should not have branch_id"
    
    # Property: Branch gaps should have both line_number and branch_id
    for gap in branch_gaps:
        assert gap.line_number > 0, "Branch gaps must have valid line number"
        assert gap.branch_id is not None, "Branch gaps must have branch_id"


@given(coverage_data=coverage_data_with_gaps_strategy())
@settings(max_examples=100, deadline=None)
def test_gap_report_includes_all_gaps(coverage_data):
    """
    Property 27: Coverage gap identification accuracy (reporting)
    
    For any set of coverage gaps, the generated report should reference
    all identified gaps (at least in summary counts).
    """
    # Create analyzer
    analyzer = CoverageAnalyzer()
    
    # Identify gaps
    gaps = analyzer.identify_coverage_gaps(coverage_data)
    
    # Skip if no gaps
    assume(len(gaps) > 0)
    
    # Prioritize gaps
    prioritized_gaps = analyzer.prioritize_gaps(gaps)
    
    # Generate report
    report = analyzer.generate_gap_report(prioritized_gaps)
    
    # Property: Report should mention total gap count
    assert f"Total Gaps: {len(gaps)}" in report, \
        "Report must include total gap count"
    
    # Property: Report should include priority sections
    priority_counts = {}
    for gap in prioritized_gaps:
        priority_counts[gap.priority] = priority_counts.get(gap.priority, 0) + 1
    
    for priority, count in priority_counts.items():
        assert f"{priority.value.upper()} Priority: {count} gaps" in report, \
            f"Report must include {priority.value} priority section with count"


@given(
    file_path=st.text(min_size=1, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.'
    )),
    line_number=st.integers(min_value=1, max_value=1000)
)
@settings(max_examples=100, deadline=None)
def test_gap_parsing_is_reversible(file_path, line_number):
    """
    Property 27: Coverage gap identification accuracy (parsing invariant)
    
    For any file path and line number, converting to a reference string
    and parsing back should preserve the information.
    """
    # Create a line reference
    line_ref = f"{file_path}:{line_number}"
    
    # Create coverage data with this reference
    coverage_data = CoverageData(
        line_coverage=0.0,
        branch_coverage=0.0,
        function_coverage=0.0,
        covered_lines=[],
        uncovered_lines=[line_ref],
        covered_branches=[],
        uncovered_branches=[]
    )
    
    # Create analyzer
    analyzer = CoverageAnalyzer()
    
    # Identify gaps
    gaps = analyzer.identify_coverage_gaps(coverage_data)
    
    # Property: Should have exactly one gap
    assert len(gaps) == 1, f"Expected 1 gap, got {len(gaps)}"
    
    gap = gaps[0]
    
    # Property: Gap should preserve file path and line number
    assert gap.file_path == file_path, \
        f"File path not preserved: expected {file_path}, got {gap.file_path}"
    assert gap.line_number == line_number, \
        f"Line number not preserved: expected {line_number}, got {gap.line_number}"
    
    # Property: Gap type should be LINE
    assert gap.gap_type == GapType.LINE, \
        f"Expected LINE gap type, got {gap.gap_type}"


@given(coverage_data=coverage_data_with_gaps_strategy())
@settings(max_examples=100, deadline=None)
def test_identify_gaps_is_idempotent(coverage_data):
    """
    Property 27: Coverage gap identification accuracy (idempotence)
    
    For any coverage data, identifying gaps multiple times should produce
    the same results.
    """
    # Create analyzer
    analyzer = CoverageAnalyzer()
    
    # Identify gaps twice
    gaps1 = analyzer.identify_coverage_gaps(coverage_data)
    gaps2 = analyzer.identify_coverage_gaps(coverage_data)
    
    # Property: Should produce same number of gaps
    assert len(gaps1) == len(gaps2), \
        "Gap identification should be deterministic"
    
    # Property: Gaps should be equivalent (same file paths and line numbers)
    gaps1_refs = {(g.file_path, g.line_number, g.gap_type, g.branch_id) for g in gaps1}
    gaps2_refs = {(g.file_path, g.line_number, g.gap_type, g.branch_id) for g in gaps2}
    
    assert gaps1_refs == gaps2_refs, \
        "Gap identification should produce identical results on repeated calls"
