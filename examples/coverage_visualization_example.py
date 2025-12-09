#!/usr/bin/env python3
"""Example demonstrating coverage visualization functionality.

This example shows how to:
1. Generate HTML coverage reports from lcov files
2. Create interactive coverage browsers
3. Visualize covered and uncovered code regions
"""

import tempfile
from pathlib import Path

from analysis.coverage_visualizer import CoverageVisualizer
from analysis.coverage_analyzer import FileCoverage


def create_sample_coverage_data():
    """Create sample coverage data for demonstration."""
    # Create a sample source file
    source_code = """#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int multiply(int a, int b) {
    if (a == 0 || b == 0) {
        return 0;
    }
    return a * b;
}

int divide(int a, int b) {
    if (b == 0) {
        printf("Error: Division by zero\\n");
        return 0;
    }
    return a / b;
}

int main() {
    int x = 10;
    int y = 5;
    
    printf("Add: %d\\n", add(x, y));
    printf("Subtract: %d\\n", subtract(x, y));
    printf("Multiply: %d\\n", multiply(x, y));
    
    // Division not tested
    // printf("Divide: %d\\n", divide(x, y));
    
    return 0;
}
"""
    
    # Create lcov data (simulating coverage from test execution)
    lcov_data = """SF:calculator.c
FN:3,add
FN:7,subtract
FN:11,multiply
FN:18,divide
FN:25,main
FNDA:10,add
FNDA:5,subtract
FNDA:3,multiply
FNDA:0,divide
FNDA:1,main
DA:3,10
DA:4,10
DA:7,5
DA:8,5
DA:11,3
DA:12,3
DA:13,1
DA:15,2
DA:18,0
DA:19,0
DA:20,0
DA:21,0
DA:23,0
DA:26,1
DA:27,1
DA:29,1
DA:30,1
DA:31,1
DA:36,1
BRDA:12,0,0,1
BRDA:12,0,1,2
BRDA:19,0,0,0
BRDA:19,0,1,0
end_of_record
"""
    
    return source_code, lcov_data


def main():
    """Run the coverage visualization example."""
    print("Coverage Visualization Example")
    print("=" * 80)
    
    # Create temporary directory for demonstration
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source directory and file
        source_dir = temp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / "calculator.c"
        
        source_code, lcov_data = create_sample_coverage_data()
        
        with open(source_file, 'w') as f:
            f.write(source_code)
        
        # Create lcov file
        lcov_file = temp_path / "coverage.info"
        with open(lcov_file, 'w') as f:
            f.write(lcov_data)
        
        print(f"\n1. Created sample source file: {source_file}")
        print(f"2. Created lcov coverage file: {lcov_file}")
        
        # Create visualizer
        output_dir = temp_path / "coverage_reports"
        visualizer = CoverageVisualizer(output_dir=str(output_dir))
        
        print(f"\n3. Generating coverage report...")
        
        # Generate report
        report = visualizer.generate_report(
            str(lcov_file),
            str(source_dir),
            "Calculator Coverage Report"
        )
        
        print(f"\n4. Coverage Summary:")
        print(f"   - Line Coverage: {report.coverage_data.line_coverage * 100:.1f}%")
        print(f"   - Branch Coverage: {report.coverage_data.branch_coverage * 100:.1f}%")
        print(f"   - Function Coverage: {report.coverage_data.function_coverage * 100:.1f}%")
        print(f"   - Files Analyzed: {report.coverage_data.metadata.get('num_files', 0)}")
        
        # Generate HTML report
        html_path = visualizer.generate_html_report(report, "calculator_report")
        
        print(f"\n5. Generated HTML report at: {html_path}")
        print(f"\n6. Report includes:")
        print(f"   - Index page with coverage summary")
        print(f"   - File-specific pages with highlighted code")
        print(f"   - Interactive filtering and sorting")
        print(f"   - Visual indicators for covered/uncovered regions")
        
        # Show what files were created
        report_dir = Path(html_path).parent
        print(f"\n7. Generated files:")
        for file in sorted(report_dir.iterdir()):
            print(f"   - {file.name}")
        
        # Generate JSON report as well
        json_path = temp_path / "coverage_report.json"
        visualizer.generate_json_report(report, str(json_path))
        print(f"\n8. Also generated JSON report at: {json_path}")
        
        print(f"\n9. Coverage Gaps Identified:")
        uncovered_count = len(report.coverage_data.uncovered_lines)
        print(f"   - {uncovered_count} uncovered lines")
        
        if uncovered_count > 0:
            print(f"\n   Sample uncovered lines:")
            for line_ref in report.coverage_data.uncovered_lines[:5]:
                print(f"     - {line_ref}")
        
        print(f"\n{'=' * 80}")
        print("Example completed successfully!")
        print(f"\nTo view the report, open: {html_path}")
        print("(Note: Files are in a temporary directory and will be deleted)")


if __name__ == '__main__':
    main()
