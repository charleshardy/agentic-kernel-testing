"""Property-based tests for coverage metric completeness.

**Feature: agentic-kernel-testing, Property 26: Coverage metric completeness**
**Validates: Requirements 6.1**

Property: For any test execution, the collected coverage data should include 
line coverage, branch coverage, and function coverage.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import os
import json

from analysis.coverage_analyzer import (
    CoverageAnalyzer, FileCoverage, LcovParser, CoverageMerger
)
from ai_generator.models import CoverageData


# Strategy for generating valid FileCoverage objects
@st.composite
def file_coverage_strategy(draw):
    """Generate a valid FileCoverage object."""
    file_path = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.'
    )))
    
    # Ensure we have at least some coverage data
    lines_found = draw(st.integers(min_value=1, max_value=100))
    lines_hit = draw(st.integers(min_value=0, max_value=lines_found))
    
    branches_found = draw(st.integers(min_value=0, max_value=50))
    branches_hit = draw(st.integers(min_value=0, max_value=branches_found))
    
    functions_found = draw(st.integers(min_value=0, max_value=20))
    functions_hit = draw(st.integers(min_value=0, max_value=functions_found))
    
    # Generate line details
    line_details = {}
    hit_lines = draw(st.integers(min_value=0, max_value=lines_hit))
    for i in range(lines_found):
        line_num = i + 1
        hit_count = draw(st.integers(min_value=1, max_value=10)) if i < hit_lines else 0
        line_details[line_num] = hit_count
    
    # Generate function details
    function_details = {}
    for i in range(functions_found):
        func_name = f"func_{i}"
        hit_count = draw(st.integers(min_value=1, max_value=10)) if i < functions_hit else 0
        function_details[func_name] = hit_count
    
    # Generate branch details
    branch_details = {}
    if branches_found > 0:
        num_branch_lines = draw(st.integers(min_value=1, max_value=min(10, lines_found)))
        for i in range(num_branch_lines):
            line_num = draw(st.integers(min_value=1, max_value=lines_found))
            num_branches = draw(st.integers(min_value=1, max_value=4))
            branches = []
            for j in range(num_branches):
                hit_count = draw(st.integers(min_value=0, max_value=10))
                branches.append((j, hit_count))
            branch_details[line_num] = branches
    
    return FileCoverage(
        file_path=file_path,
        lines_found=lines_found,
        lines_hit=lines_hit,
        branches_found=branches_found,
        branches_hit=branches_hit,
        functions_found=functions_found,
        functions_hit=functions_hit,
        line_details=line_details,
        branch_details=branch_details,
        function_details=function_details
    )


# Strategy for generating lcov file content
@st.composite
def lcov_content_strategy(draw):
    """Generate valid lcov file content."""
    file_path = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.'
    )))
    
    lines = [f"SF:{file_path}"]
    
    # Add functions
    num_functions = draw(st.integers(min_value=0, max_value=5))
    for i in range(num_functions):
        func_name = f"func_{i}"
        line_num = draw(st.integers(min_value=1, max_value=100))
        hit_count = draw(st.integers(min_value=0, max_value=10))
        lines.append(f"FN:{line_num},{func_name}")
        lines.append(f"FNDA:{hit_count},{func_name}")
    
    # Add lines
    num_lines = draw(st.integers(min_value=1, max_value=20))
    for i in range(num_lines):
        line_num = i + 1
        hit_count = draw(st.integers(min_value=0, max_value=10))
        lines.append(f"DA:{line_num},{hit_count}")
    
    # Add branches
    num_branches = draw(st.integers(min_value=0, max_value=10))
    for i in range(num_branches):
        line_num = draw(st.integers(min_value=1, max_value=num_lines))
        block_num = 0
        branch_num = i
        hit_count = draw(st.integers(min_value=0, max_value=10))
        lines.append(f"BRDA:{line_num},{block_num},{branch_num},{hit_count}")
    
    lines.append("end_of_record")
    
    return "\n".join(lines)


@given(lcov_content=lcov_content_strategy())
@settings(max_examples=100, deadline=None)
def test_coverage_data_includes_all_metrics(lcov_content):
    """
    Property 26: Coverage metric completeness
    
    For any test execution (represented by lcov data), the collected coverage 
    data should include line coverage, branch coverage, and function coverage.
    
    This test verifies that when we parse coverage data, all three metrics
    are present and properly calculated.
    """
    # Create a temporary lcov file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.info', delete=False) as f:
        f.write(lcov_content)
        lcov_file = f.name
    
    try:
        # Parse the lcov file
        parser = LcovParser()
        file_coverages = parser.parse_lcov_file(lcov_file)
        
        # Aggregate coverage (simulating what CoverageAnalyzer does)
        total_lines_found = 0
        total_lines_hit = 0
        total_branches_found = 0
        total_branches_hit = 0
        total_functions_found = 0
        total_functions_hit = 0
        
        for file_cov in file_coverages.values():
            total_lines_found += file_cov.lines_found
            total_lines_hit += file_cov.lines_hit
            total_branches_found += file_cov.branches_found
            total_branches_hit += file_cov.branches_hit
            total_functions_found += file_cov.functions_found
            total_functions_hit += file_cov.functions_hit
        
        # Calculate coverage percentages
        line_coverage = total_lines_hit / total_lines_found if total_lines_found > 0 else 0.0
        branch_coverage = total_branches_hit / total_branches_found if total_branches_found > 0 else 0.0
        function_coverage = total_functions_hit / total_functions_found if total_functions_found > 0 else 0.0
        
        # Property: All three coverage metrics must be present
        assert line_coverage is not None, "Line coverage must be present"
        assert branch_coverage is not None, "Branch coverage must be present"
        assert function_coverage is not None, "Function coverage must be present"
        
        # Property: All coverage metrics must be valid percentages (0.0 to 1.0)
        assert 0.0 <= line_coverage <= 1.0, f"Line coverage must be between 0 and 1, got {line_coverage}"
        assert 0.0 <= branch_coverage <= 1.0, f"Branch coverage must be between 0 and 1, got {branch_coverage}"
        assert 0.0 <= function_coverage <= 1.0, f"Function coverage must be between 0 and 1, got {function_coverage}"
        
    finally:
        # Clean up
        if os.path.exists(lcov_file):
            os.unlink(lcov_file)


@given(file_cov=file_coverage_strategy())
@settings(max_examples=100, deadline=None)
def test_aggregated_coverage_has_all_metrics(file_cov):
    """
    Property 26: Coverage metric completeness (aggregation variant)
    
    For any aggregated coverage data, all three metrics (line, branch, function)
    must be present and properly calculated.
    """
    # Create a mock file_coverages dict
    file_coverages = {"test_file.c": file_cov}
    
    # Aggregate coverage
    total_lines_found = file_cov.lines_found
    total_lines_hit = file_cov.lines_hit
    total_branches_found = file_cov.branches_found
    total_branches_hit = file_cov.branches_hit
    total_functions_found = file_cov.functions_found
    total_functions_hit = file_cov.functions_hit
    
    # Calculate coverage percentages
    line_coverage = total_lines_hit / total_lines_found if total_lines_found > 0 else 0.0
    branch_coverage = total_branches_hit / total_branches_found if total_branches_found > 0 else 0.0
    function_coverage = total_functions_hit / total_functions_found if total_functions_found > 0 else 0.0
    
    # Create CoverageData object
    coverage_data = CoverageData(
        line_coverage=line_coverage,
        branch_coverage=branch_coverage,
        function_coverage=function_coverage
    )
    
    # Property: All three coverage metrics must be present in CoverageData
    assert hasattr(coverage_data, 'line_coverage'), "CoverageData must have line_coverage"
    assert hasattr(coverage_data, 'branch_coverage'), "CoverageData must have branch_coverage"
    assert hasattr(coverage_data, 'function_coverage'), "CoverageData must have function_coverage"
    
    # Property: All metrics must be accessible
    assert coverage_data.line_coverage is not None
    assert coverage_data.branch_coverage is not None
    assert coverage_data.function_coverage is not None
    
    # Property: All metrics must be valid percentages
    assert 0.0 <= coverage_data.line_coverage <= 1.0
    assert 0.0 <= coverage_data.branch_coverage <= 1.0
    assert 0.0 <= coverage_data.function_coverage <= 1.0


@given(
    file_covs=st.lists(file_coverage_strategy(), min_size=1, max_size=5)
)
@settings(max_examples=100, deadline=None)
def test_merged_coverage_has_all_metrics(file_covs):
    """
    Property 26: Coverage metric completeness (merge variant)
    
    For any merged coverage data from multiple test executions, all three 
    metrics must be present and properly calculated.
    """
    # Assume all file coverages are for the same file
    for fc in file_covs:
        fc.file_path = "merged_test.c"
    
    # Merge coverage data
    merger = CoverageMerger()
    merged = merger.merge_coverage_data(file_covs)
    
    # Property: Merged coverage must have all metrics
    assert merged.lines_found >= 0, "Merged coverage must have lines_found"
    assert merged.branches_found >= 0, "Merged coverage must have branches_found"
    assert merged.functions_found >= 0, "Merged coverage must have functions_found"
    
    # Calculate percentages
    line_coverage = merged.lines_hit / merged.lines_found if merged.lines_found > 0 else 0.0
    branch_coverage = merged.branches_hit / merged.branches_found if merged.branches_found > 0 else 0.0
    function_coverage = merged.functions_hit / merged.functions_found if merged.functions_found > 0 else 0.0
    
    # Property: All metrics must be valid percentages
    assert 0.0 <= line_coverage <= 1.0
    assert 0.0 <= branch_coverage <= 1.0
    assert 0.0 <= function_coverage <= 1.0


@given(
    lines_found=st.integers(min_value=1, max_value=100),
    lines_hit=st.integers(min_value=0, max_value=100),
    branches_found=st.integers(min_value=0, max_value=50),
    branches_hit=st.integers(min_value=0, max_value=50),
    functions_found=st.integers(min_value=0, max_value=20),
    functions_hit=st.integers(min_value=0, max_value=20)
)
@settings(max_examples=100, deadline=None)
def test_coverage_data_model_completeness(lines_found, lines_hit, branches_found, 
                                          branches_hit, functions_found, functions_hit):
    """
    Property 26: Coverage metric completeness (data model variant)
    
    For any CoverageData object created with coverage metrics, all three
    coverage types must be present and accessible.
    """
    # Ensure hit counts don't exceed found counts
    assume(lines_hit <= lines_found)
    assume(branches_hit <= branches_found)
    assume(functions_hit <= functions_found)
    
    # Calculate coverage percentages
    line_coverage = lines_hit / lines_found if lines_found > 0 else 0.0
    branch_coverage = branches_hit / branches_found if branches_found > 0 else 0.0
    function_coverage = functions_hit / functions_found if functions_found > 0 else 0.0
    
    # Create CoverageData object
    coverage_data = CoverageData(
        line_coverage=line_coverage,
        branch_coverage=branch_coverage,
        function_coverage=function_coverage
    )
    
    # Property: All three metrics must be present
    assert hasattr(coverage_data, 'line_coverage')
    assert hasattr(coverage_data, 'branch_coverage')
    assert hasattr(coverage_data, 'function_coverage')
    
    # Property: All metrics must be the values we set
    assert coverage_data.line_coverage == line_coverage
    assert coverage_data.branch_coverage == branch_coverage
    assert coverage_data.function_coverage == function_coverage
    
    # Property: Serialization must preserve all metrics
    data_dict = coverage_data.to_dict()
    assert 'line_coverage' in data_dict
    assert 'branch_coverage' in data_dict
    assert 'function_coverage' in data_dict
    
    # Property: Deserialization must restore all metrics
    restored = CoverageData.from_dict(data_dict)
    assert restored.line_coverage == coverage_data.line_coverage
    assert restored.branch_coverage == coverage_data.branch_coverage
    assert restored.function_coverage == coverage_data.function_coverage


@given(file_cov=file_coverage_strategy())
@settings(max_examples=100, deadline=None)
def test_file_coverage_percentages_completeness(file_cov):
    """
    Property 26: Coverage metric completeness (file-level variant)
    
    For any FileCoverage object, all three coverage percentage properties
    must be present and properly calculated.
    """
    # Property: All three percentage properties must exist
    assert hasattr(file_cov, 'line_coverage_percent')
    assert hasattr(file_cov, 'branch_coverage_percent')
    assert hasattr(file_cov, 'function_coverage_percent')
    
    # Property: All percentages must be accessible
    line_pct = file_cov.line_coverage_percent
    branch_pct = file_cov.branch_coverage_percent
    function_pct = file_cov.function_coverage_percent
    
    assert line_pct is not None
    assert branch_pct is not None
    assert function_pct is not None
    
    # Property: All percentages must be valid (0.0 to 1.0)
    assert 0.0 <= line_pct <= 1.0
    assert 0.0 <= branch_pct <= 1.0
    assert 0.0 <= function_pct <= 1.0
    
    # Property: Percentages must match manual calculation
    expected_line_pct = file_cov.lines_hit / file_cov.lines_found if file_cov.lines_found > 0 else 0.0
    expected_branch_pct = file_cov.branches_hit / file_cov.branches_found if file_cov.branches_found > 0 else 0.0
    expected_function_pct = file_cov.functions_hit / file_cov.functions_found if file_cov.functions_found > 0 else 0.0
    
    assert abs(line_pct - expected_line_pct) < 0.0001
    assert abs(branch_pct - expected_branch_pct) < 0.0001
    assert abs(function_pct - expected_function_pct) < 0.0001
