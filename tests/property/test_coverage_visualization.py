"""Property-based tests for coverage visualization completeness.

**Feature: agentic-kernel-testing, Property 30: Coverage visualization completeness**
**Validates: Requirements 6.5**

Property: For any coverage results display, the visualization should clearly show 
both covered and uncovered code regions.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import shutil
import os
from typing import Dict, List, Tuple

from analysis.coverage_visualizer import CoverageVisualizer, CoverageReport
from analysis.coverage_analyzer import FileCoverage, LcovParser
from ai_generator.models import CoverageData


# Strategies for generating test data

@st.composite
def file_coverage_strategy(draw):
    """Generate a FileCoverage object with random coverage data."""
    file_path = draw(st.text(min_size=5, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.'
    )))
    
    # Ensure valid file path
    if not file_path.endswith('.c') and not file_path.endswith('.py'):
        file_path += '.c'
    
    lines_found = draw(st.integers(min_value=10, max_value=100))
    lines_hit = draw(st.integers(min_value=0, max_value=lines_found))
    
    branches_found = draw(st.integers(min_value=0, max_value=50))
    branches_hit = draw(st.integers(min_value=0, max_value=branches_found))
    
    functions_found = draw(st.integers(min_value=1, max_value=20))
    functions_hit = draw(st.integers(min_value=0, max_value=functions_found))
    
    # Generate line details
    line_details = {}
    covered_count = 0
    for i in range(1, lines_found + 1):
        if covered_count < lines_hit:
            hit_count = draw(st.integers(min_value=1, max_value=100))
            covered_count += 1
        else:
            hit_count = 0
        line_details[i] = hit_count
    
    # Generate branch details
    branch_details = {}
    if branches_found > 0:
        lines_with_branches = draw(st.integers(min_value=1, max_value=min(10, lines_found)))
        branch_lines = draw(st.lists(
            st.integers(min_value=1, max_value=lines_found),
            min_size=lines_with_branches,
            max_size=lines_with_branches,
            unique=True
        ))
        
        branches_allocated = 0
        for line_num in branch_lines:
            if branches_allocated >= branches_found:
                break
            num_branches = min(2, branches_found - branches_allocated)
            branches = []
            for branch_id in range(num_branches):
                if branches_allocated < branches_hit:
                    hit_count = draw(st.integers(min_value=1, max_value=50))
                else:
                    hit_count = 0
                branches.append((branch_id, hit_count))
                branches_allocated += 1
            branch_details[line_num] = branches
    
    # Generate function details
    function_details = {}
    for i in range(functions_found):
        func_name = f"function_{i}"
        if i < functions_hit:
            hit_count = draw(st.integers(min_value=1, max_value=100))
        else:
            hit_count = 0
        function_details[func_name] = hit_count
    
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


@st.composite
def coverage_data_strategy(draw):
    """Generate a CoverageData object."""
    line_coverage = draw(st.floats(min_value=0.0, max_value=1.0))
    branch_coverage = draw(st.floats(min_value=0.0, max_value=1.0))
    function_coverage = draw(st.floats(min_value=0.0, max_value=1.0))
    
    num_covered_lines = draw(st.integers(min_value=0, max_value=100))
    num_uncovered_lines = draw(st.integers(min_value=0, max_value=100))
    
    covered_lines = [f"file.c:{i}" for i in range(1, num_covered_lines + 1)]
    uncovered_lines = [f"file.c:{i}" for i in range(num_covered_lines + 1, num_covered_lines + num_uncovered_lines + 1)]
    
    num_covered_branches = draw(st.integers(min_value=0, max_value=50))
    num_uncovered_branches = draw(st.integers(min_value=0, max_value=50))
    
    covered_branches = [f"file.c:{i}:0" for i in range(1, num_covered_branches + 1)]
    uncovered_branches = [f"file.c:{i}:1" for i in range(1, num_uncovered_branches + 1)]
    
    total_lines = num_covered_lines + num_uncovered_lines
    total_branches = num_covered_branches + num_uncovered_branches
    
    return CoverageData(
        line_coverage=line_coverage,
        branch_coverage=branch_coverage,
        function_coverage=function_coverage,
        covered_lines=covered_lines,
        uncovered_lines=uncovered_lines,
        covered_branches=covered_branches,
        uncovered_branches=uncovered_branches,
        metadata={
            'total_lines_found': total_lines,
            'total_lines_hit': num_covered_lines,
            'total_branches_found': total_branches,
            'total_branches_hit': num_covered_branches,
            'total_functions_found': 10,
            'total_functions_hit': 5,
            'num_files': 1
        }
    )


def create_test_source_file(temp_dir: Path, file_path: str, num_lines: int) -> Path:
    """Create a test source file with the specified number of lines."""
    full_path = temp_dir / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(full_path, 'w') as f:
        for i in range(1, num_lines + 1):
            f.write(f"int x{i} = {i};\n")
    
    return full_path


def create_test_lcov_file(temp_dir: Path, file_coverage: FileCoverage) -> Path:
    """Create a test lcov file from FileCoverage data."""
    lcov_path = temp_dir / "coverage.info"
    
    with open(lcov_path, 'w') as f:
        f.write(f"SF:{file_coverage.file_path}\n")
        
        # Write function data
        for func_name, hit_count in file_coverage.function_details.items():
            f.write(f"FN:1,{func_name}\n")
        for func_name, hit_count in file_coverage.function_details.items():
            f.write(f"FNDA:{hit_count},{func_name}\n")
        
        # Write line data
        for line_num, hit_count in file_coverage.line_details.items():
            f.write(f"DA:{line_num},{hit_count}\n")
        
        # Write branch data
        for line_num, branches in file_coverage.branch_details.items():
            for branch_id, hit_count in branches:
                f.write(f"BRDA:{line_num},0,{branch_id},{hit_count}\n")
        
        f.write("end_of_record\n")
    
    return lcov_path


# Property-based tests

@given(coverage_data=coverage_data_strategy())
@settings(max_examples=100, deadline=None)
def test_visualization_includes_covered_regions(coverage_data):
    """
    Property: For any coverage data with covered lines, the HTML visualization 
    should include visual indicators for all covered regions.
    
    **Feature: agentic-kernel-testing, Property 30: Coverage visualization completeness**
    **Validates: Requirements 6.5**
    """
    # Skip if no covered lines
    assume(len(coverage_data.covered_lines) > 0)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create visualizer
        visualizer = CoverageVisualizer(output_dir=str(temp_path / "reports"))
        
        # Create a simple test file with exact number of lines
        source_dir = temp_path / "source"
        source_dir.mkdir()
        num_lines = len(coverage_data.covered_lines) + len(coverage_data.uncovered_lines)
        test_file = create_test_source_file(source_dir, "file.c", max(num_lines, 1))
        
        # Create file coverage
        file_cov = FileCoverage(
            file_path="file.c",
            lines_found=len(coverage_data.covered_lines) + len(coverage_data.uncovered_lines),
            lines_hit=len(coverage_data.covered_lines),
            line_details={i: 1 for i in range(1, len(coverage_data.covered_lines) + 1)}
        )
        
        # Create lcov file
        lcov_file = create_test_lcov_file(temp_path, file_cov)
        
        # Generate report
        report = visualizer.generate_report(
            str(lcov_file),
            str(source_dir),
            "Test Report"
        )
        
        # Generate HTML
        html_path = visualizer.generate_html_report(report, "test_report")
        
        # Verify HTML was created
        assert os.path.exists(html_path)
        
        # Read HTML content from index
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Property: HTML should contain coverage metrics
        assert 'Line Coverage' in html_content
        assert 'Branch Coverage' in html_content
        assert 'Function Coverage' in html_content
        
        # Property: HTML should show covered regions with visual indicators
        # Check the file-specific HTML page for coverage indicators
        safe_path = "file.c".replace('/', '_').replace('.', '_')
        file_html_path = Path(html_path).parent / f"{safe_path}.html"
        
        if file_html_path.exists():
            with open(file_html_path, 'r') as f:
                file_html_content = f.read()
            
            # Check for CSS classes that indicate covered code
            assert 'line covered' in file_html_content, "File HTML should show covered regions"


@given(coverage_data=coverage_data_strategy())
@settings(max_examples=100, deadline=None)
def test_visualization_includes_uncovered_regions(coverage_data):
    """
    Property: For any coverage data with uncovered lines, the HTML visualization 
    should include visual indicators for all uncovered regions.
    
    **Feature: agentic-kernel-testing, Property 30: Coverage visualization completeness**
    **Validates: Requirements 6.5**
    """
    # Skip if no uncovered lines
    assume(len(coverage_data.uncovered_lines) > 0)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create visualizer
        visualizer = CoverageVisualizer(output_dir=str(temp_path / "reports"))
        
        # Create a simple test file with exact number of lines
        source_dir = temp_path / "source"
        source_dir.mkdir()
        num_lines = len(coverage_data.covered_lines) + len(coverage_data.uncovered_lines)
        test_file = create_test_source_file(source_dir, "file.c", max(num_lines, 1))
        
        # Create file coverage with uncovered lines
        total_lines = len(coverage_data.covered_lines) + len(coverage_data.uncovered_lines)
        covered_count = len(coverage_data.covered_lines)
        
        line_details = {}
        for i in range(1, total_lines + 1):
            if i <= covered_count:
                line_details[i] = 1
            else:
                line_details[i] = 0
        
        file_cov = FileCoverage(
            file_path="file.c",
            lines_found=total_lines,
            lines_hit=covered_count,
            line_details=line_details
        )
        
        # Create lcov file
        lcov_file = create_test_lcov_file(temp_path, file_cov)
        
        # Generate report
        report = visualizer.generate_report(
            str(lcov_file),
            str(source_dir),
            "Test Report"
        )
        
        # Generate HTML
        html_path = visualizer.generate_html_report(report, "test_report")
        
        # Verify HTML was created
        assert os.path.exists(html_path)
        
        # Read HTML content from index
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Property: HTML should show uncovered regions with visual indicators
        # Check the file-specific HTML page for coverage indicators
        safe_path = "file.c".replace('/', '_').replace('.', '_')
        file_html_path = Path(html_path).parent / f"{safe_path}.html"
        
        if file_html_path.exists():
            with open(file_html_path, 'r') as f:
                file_html_content = f.read()
            
            # Check for CSS classes that indicate uncovered code
            assert 'line uncovered' in file_html_content, "File HTML should show uncovered regions"


@given(file_cov=file_coverage_strategy())
@settings(max_examples=100, deadline=None)
def test_visualization_shows_both_covered_and_uncovered(file_cov):
    """
    Property: For any file with both covered and uncovered lines, the visualization 
    should clearly distinguish between covered and uncovered regions.
    
    **Feature: agentic-kernel-testing, Property 30: Coverage visualization completeness**
    **Validates: Requirements 6.5**
    """
    # Skip if all lines are covered or all uncovered
    assume(file_cov.lines_hit > 0)
    assume(file_cov.lines_hit < file_cov.lines_found)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create visualizer
        visualizer = CoverageVisualizer(output_dir=str(temp_path / "reports"))
        
        # Create source file with exact number of lines
        source_dir = temp_path / "source"
        source_dir.mkdir()
        test_file = create_test_source_file(source_dir, file_cov.file_path, file_cov.lines_found)
        
        # Create lcov file
        lcov_file = create_test_lcov_file(temp_path, file_cov)
        
        # Generate report
        report = visualizer.generate_report(
            str(lcov_file),
            str(source_dir),
            "Test Report"
        )
        
        # Generate HTML
        html_path = visualizer.generate_html_report(report, "test_report")
        
        # Verify HTML was created
        assert os.path.exists(html_path)
        
        # Read the file-specific HTML
        safe_path = file_cov.file_path.replace('/', '_').replace('.', '_')
        file_html_path = Path(html_path).parent / f"{safe_path}.html"
        
        if file_html_path.exists():
            with open(file_html_path, 'r') as f:
                html_content = f.read()
            
            # Property: Both covered and uncovered indicators should be present
            has_covered = 'line covered' in html_content
            has_uncovered = 'line uncovered' in html_content
            
            assert has_covered, "Visualization should show covered regions"
            assert has_uncovered, "Visualization should show uncovered regions"


@given(file_cov=file_coverage_strategy())
@settings(max_examples=100, deadline=None)
def test_visualization_includes_all_coverage_metrics(file_cov):
    """
    Property: For any coverage data, the visualization should display all three 
    coverage metrics: line, branch, and function coverage.
    
    **Feature: agentic-kernel-testing, Property 30: Coverage visualization completeness**
    **Validates: Requirements 6.5**
    """
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create visualizer
        visualizer = CoverageVisualizer(output_dir=str(temp_path / "reports"))
        
        # Create source file
        source_dir = temp_path / "source"
        source_dir.mkdir()
        test_file = create_test_source_file(source_dir, file_cov.file_path, file_cov.lines_found)
        
        # Create lcov file
        lcov_file = create_test_lcov_file(temp_path, file_cov)
        
        # Generate report
        report = visualizer.generate_report(
            str(lcov_file),
            str(source_dir),
            "Test Report"
        )
        
        # Generate HTML
        html_path = visualizer.generate_html_report(report, "test_report")
        
        # Verify HTML was created
        assert os.path.exists(html_path)
        
        # Read HTML content
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Property: All three coverage metrics should be displayed
        assert 'Line Coverage' in html_content, "Should display line coverage"
        assert 'Branch Coverage' in html_content, "Should display branch coverage"
        assert 'Function Coverage' in html_content, "Should display function coverage"
        
        # Property: Metrics should have percentage values
        assert '%' in html_content, "Should display coverage percentages"


@given(file_cov=file_coverage_strategy())
@settings(max_examples=100, deadline=None)
def test_visualization_creates_interactive_browser(file_cov):
    """
    Property: For any coverage data, the visualization should create an interactive 
    browser with CSS and JavaScript files.
    
    **Feature: agentic-kernel-testing, Property 30: Coverage visualization completeness**
    **Validates: Requirements 6.5**
    """
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create visualizer
        visualizer = CoverageVisualizer(output_dir=str(temp_path / "reports"))
        
        # Create source file
        source_dir = temp_path / "source"
        source_dir.mkdir()
        test_file = create_test_source_file(source_dir, file_cov.file_path, file_cov.lines_found)
        
        # Create lcov file
        lcov_file = create_test_lcov_file(temp_path, file_cov)
        
        # Generate report
        report = visualizer.generate_report(
            str(lcov_file),
            str(source_dir),
            "Test Report"
        )
        
        # Generate HTML
        html_path = visualizer.generate_html_report(report, "test_report")
        
        # Verify HTML was created
        assert os.path.exists(html_path)
        
        # Property: CSS file should be created
        css_path = Path(html_path).parent / "coverage.css"
        assert css_path.exists(), "Should create CSS file for styling"
        
        # Property: JavaScript file should be created
        js_path = Path(html_path).parent / "coverage.js"
        assert js_path.exists(), "Should create JavaScript file for interactivity"
        
        # Property: HTML should reference CSS and JS files
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        assert 'coverage.css' in html_content, "HTML should reference CSS file"
        assert 'coverage.js' in html_content, "HTML should reference JavaScript file"


@given(
    file_covs=st.lists(file_coverage_strategy(), min_size=2, max_size=5)
)
@settings(max_examples=50, deadline=None)
def test_visualization_lists_all_files(file_covs):
    """
    Property: For any set of files with coverage data, the visualization should 
    list all files in the index page.
    
    **Feature: agentic-kernel-testing, Property 30: Coverage visualization completeness**
    **Validates: Requirements 6.5**
    """
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create visualizer
        visualizer = CoverageVisualizer(output_dir=str(temp_path / "reports"))
        
        # Create source files
        source_dir = temp_path / "source"
        source_dir.mkdir()
        
        # Create lcov file with all files
        lcov_path = temp_path / "coverage.info"
        with open(lcov_path, 'w') as f:
            for file_cov in file_covs:
                # Create source file
                create_test_source_file(source_dir, file_cov.file_path, file_cov.lines_found)
                
                # Write lcov data
                f.write(f"SF:{file_cov.file_path}\n")
                for line_num, hit_count in file_cov.line_details.items():
                    f.write(f"DA:{line_num},{hit_count}\n")
                f.write("end_of_record\n")
        
        # Generate report
        report = visualizer.generate_report(
            str(lcov_path),
            str(source_dir),
            "Test Report"
        )
        
        # Generate HTML
        html_path = visualizer.generate_html_report(report, "test_report")
        
        # Verify HTML was created
        assert os.path.exists(html_path)
        
        # Read HTML content
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Property: All files should be listed in the index
        for file_cov in file_covs:
            assert file_cov.file_path in html_content, \
                f"File {file_cov.file_path} should be listed in index"
