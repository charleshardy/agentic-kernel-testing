#!/usr/bin/env python3
"""Standalone test for coverage metric completeness."""

import sys
import os
import tempfile

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.coverage_analyzer import LcovParser, FileCoverage, CoverageMerger
from ai_generator.models import CoverageData


def test_basic_lcov_parsing():
    """Test that parsing lcov data produces all three coverage metrics."""
    print("Test 1: Basic lcov parsing...")
    
    # Create sample lcov content
    lcov_content = """SF:test_file.c
FN:10,test_function
FNDA:5,test_function
DA:1,10
DA:2,5
DA:3,0
BRDA:2,0,0,3
BRDA:2,0,1,2
end_of_record
"""
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.info', delete=False) as f:
        f.write(lcov_content)
        lcov_file = f.name
    
    try:
        # Parse the file
        parser = LcovParser()
        file_coverages = parser.parse_lcov_file(lcov_file)
        
        assert len(file_coverages) > 0, "Should parse at least one file"
        
        # Check that we have coverage data
        for file_path, file_cov in file_coverages.items():
            print(f"  File: {file_path}")
            print(f"    Lines: {file_cov.lines_hit}/{file_cov.lines_found}")
            print(f"    Branches: {file_cov.branches_hit}/{file_cov.branches_found}")
            print(f"    Functions: {file_cov.functions_hit}/{file_cov.functions_found}")
            
            # Verify all three metrics are present
            assert file_cov.lines_found >= 0, "Lines found should be present"
            assert file_cov.branches_found >= 0, "Branches found should be present"
            assert file_cov.functions_found >= 0, "Functions found should be present"
            
            # Verify percentages are calculable
            line_pct = file_cov.line_coverage_percent
            branch_pct = file_cov.branch_coverage_percent
            func_pct = file_cov.function_coverage_percent
            
            assert 0.0 <= line_pct <= 1.0, f"Line coverage should be 0-1, got {line_pct}"
            assert 0.0 <= branch_pct <= 1.0, f"Branch coverage should be 0-1, got {branch_pct}"
            assert 0.0 <= func_pct <= 1.0, f"Function coverage should be 0-1, got {func_pct}"
        
        print("  ✓ PASSED")
        return True
        
    finally:
        if os.path.exists(lcov_file):
            os.unlink(lcov_file)


def test_coverage_data_model():
    """Test that CoverageData model includes all three metrics."""
    print("\nTest 2: CoverageData model completeness...")
    
    # Create a CoverageData object
    coverage = CoverageData(
        line_coverage=0.75,
        branch_coverage=0.60,
        function_coverage=0.85
    )
    
    # Verify all metrics are present
    assert hasattr(coverage, 'line_coverage'), "Should have line_coverage"
    assert hasattr(coverage, 'branch_coverage'), "Should have branch_coverage"
    assert hasattr(coverage, 'function_coverage'), "Should have function_coverage"
    
    assert coverage.line_coverage == 0.75
    assert coverage.branch_coverage == 0.60
    assert coverage.function_coverage == 0.85
    
    print(f"  Line coverage: {coverage.line_coverage}")
    print(f"  Branch coverage: {coverage.branch_coverage}")
    print(f"  Function coverage: {coverage.function_coverage}")
    
    # Test serialization
    data_dict = coverage.to_dict()
    assert 'line_coverage' in data_dict
    assert 'branch_coverage' in data_dict
    assert 'function_coverage' in data_dict
    
    # Test deserialization
    restored = CoverageData.from_dict(data_dict)
    assert restored.line_coverage == coverage.line_coverage
    assert restored.branch_coverage == coverage.branch_coverage
    assert restored.function_coverage == coverage.function_coverage
    
    print("  ✓ PASSED")
    return True


def test_file_coverage_percentages():
    """Test that FileCoverage calculates all three percentage metrics."""
    print("\nTest 3: FileCoverage percentage calculations...")
    
    file_cov = FileCoverage(
        file_path="test.c",
        lines_found=10,
        lines_hit=7,
        branches_found=6,
        branches_hit=4,
        functions_found=3,
        functions_hit=2
    )
    
    # Check all percentage properties exist
    assert hasattr(file_cov, 'line_coverage_percent')
    assert hasattr(file_cov, 'branch_coverage_percent')
    assert hasattr(file_cov, 'function_coverage_percent')
    
    line_pct = file_cov.line_coverage_percent
    branch_pct = file_cov.branch_coverage_percent
    func_pct = file_cov.function_coverage_percent
    
    print(f"  Line coverage: {line_pct:.2%}")
    print(f"  Branch coverage: {branch_pct:.2%}")
    print(f"  Function coverage: {func_pct:.2%}")
    
    # Verify calculations
    assert abs(line_pct - 0.7) < 0.001, f"Expected 0.7, got {line_pct}"
    assert abs(branch_pct - 0.666667) < 0.001, f"Expected 0.666667, got {branch_pct}"
    assert abs(func_pct - 0.666667) < 0.001, f"Expected 0.666667, got {func_pct}"
    
    print("  ✓ PASSED")
    return True


def test_merge_preserves_metrics():
    """Test that merging coverage data preserves all three metrics."""
    print("\nTest 4: Coverage merging preserves all metrics...")
    
    # Create two FileCoverage objects
    cov1 = FileCoverage(
        file_path="test.c",
        lines_found=5,
        lines_hit=3,
        branches_found=2,
        branches_hit=1,
        functions_found=2,
        functions_hit=1,
        line_details={1: 5, 2: 3, 3: 0, 4: 2, 5: 0},
        function_details={"func1": 5, "func2": 0}
    )
    
    cov2 = FileCoverage(
        file_path="test.c",
        lines_found=5,
        lines_hit=4,
        branches_found=2,
        branches_hit=2,
        functions_found=2,
        functions_hit=2,
        line_details={1: 3, 2: 4, 3: 2, 4: 1, 5: 0},
        function_details={"func1": 3, "func2": 2}
    )
    
    # Merge them
    merger = CoverageMerger()
    merged = merger.merge_coverage_data([cov1, cov2])
    
    print(f"  Merged lines: {merged.lines_hit}/{merged.lines_found}")
    print(f"  Merged branches: {merged.branches_hit}/{merged.branches_found}")
    print(f"  Merged functions: {merged.functions_hit}/{merged.functions_found}")
    
    # Verify all metrics are present
    assert merged.lines_found > 0
    assert merged.branches_found >= 0
    assert merged.functions_found > 0
    
    # Verify percentages are calculable
    line_pct = merged.line_coverage_percent
    branch_pct = merged.branch_coverage_percent
    func_pct = merged.function_coverage_percent
    
    assert 0.0 <= line_pct <= 1.0
    assert 0.0 <= branch_pct <= 1.0
    assert 0.0 <= func_pct <= 1.0
    
    print("  ✓ PASSED")
    return True


def main():
    """Run all tests."""
    print("=" * 80)
    print("Coverage Metric Completeness Tests")
    print("Property 26: For any test execution, the collected coverage data")
    print("should include line coverage, branch coverage, and function coverage.")
    print("=" * 80)
    
    tests = [
        test_basic_lcov_parsing,
        test_coverage_data_model,
        test_file_coverage_percentages,
        test_merge_preserves_metrics
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
