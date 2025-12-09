#!/usr/bin/env python3
"""Debug script to test coverage visualization."""

import tempfile
from pathlib import Path

from analysis.coverage_visualizer import CoverageVisualizer
from analysis.coverage_analyzer import FileCoverage

# Create a simple test case
file_cov = FileCoverage(
    file_path='test.c',
    lines_found=10,
    lines_hit=5,
    line_details={
        1: 10,  # covered
        2: 5,   # covered
        3: 0,   # uncovered
        4: 1,   # covered
        5: 0,   # uncovered
        6: 3,   # covered
        7: 0,   # uncovered
        8: 2,   # covered
        9: 0,   # uncovered
        10: 0   # uncovered
    }
)

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    
    # Create source file
    source_dir = temp_path / "source"
    source_dir.mkdir()
    source_file = source_dir / "test.c"
    
    with open(source_file, 'w') as f:
        for i in range(1, 11):
            f.write(f"int x{i} = {i};\n")
    
    # Create lcov file
    lcov_file = temp_path / "coverage.info"
    with open(lcov_file, 'w') as f:
        f.write("SF:test.c\n")
        for line_num, hit_count in file_cov.line_details.items():
            f.write(f"DA:{line_num},{hit_count}\n")
        f.write("end_of_record\n")
    
    # Create visualizer
    visualizer = CoverageVisualizer(output_dir=str(temp_path / "reports"))
    
    # Generate report
    report = visualizer.generate_report(
        str(lcov_file),
        str(source_dir),
        "Debug Report"
    )
    
    # Generate HTML
    html_path = visualizer.generate_html_report(report, "debug_report")
    
    print(f"HTML generated at: {html_path}")
    
    # Check file HTML
    file_html_path = Path(html_path).parent / "test_c.html"
    print(f"\nLooking for file HTML at: {file_html_path}")
    print(f"  Exists: {file_html_path.exists()}")
    
    # List all files in the directory
    report_dir = Path(html_path).parent
    print(f"\nFiles in report directory:")
    for f in report_dir.iterdir():
        print(f"  {f.name}")
    
    if file_html_path.exists():
        with open(file_html_path, 'r') as f:
            content = f.read()
        
        print("\nChecking for coverage indicators:")
        print(f"  Has 'class=\"covered\"': {'class=\"covered\"' in content}")
        print(f"  Has 'class=\"uncovered\"': {'class=\"uncovered\"' in content}")
        print(f"  Has 'class=\"line': {'class=\"line' in content}")
        
        # Show first few lines with class="line"
        lines = content.split('\n')
        count = 0
        for i, line in enumerate(lines):
            if 'class="line' in line and count < 15:
                print(f"  Line {i}: {line[:150]}")
                count += 1
    else:
        print(f"File HTML not found at: {file_html_path}")
