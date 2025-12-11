#!/usr/bin/env python3
"""Direct test of coverage analyzer."""

import sys
import os
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.coverage_analyzer import (
    CoverageAnalyzer, FileCoverage, LcovParser, CoverageMerger
)
from ai_generator.models import CoverageData

def test_basic_coverage_parsing():
    """Test basic lcov parsing."""
    print("Testing basic lcov parsing...")
    
    # Create a simple lcov file
    lcov_content = """SF:test.c
FN:10,test_func
FNDA:5,test_func
DA:10,5
DA:11,5
DA:12,0
BRDA:11,0,0,3
BRDA:11,0,1,2
end_of_record
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.info', delete=False) as f:
        f.write(lcov_content)
        lcov_file = f.name
    
    try:
        parser = LcovParser()
        file_coverages = parser.parse_lcov_file(lcov_file)
        
        assert len(file_coverages) == 1, f"Expected 1 file, got {len(file_coverages)}"
        
        file_cov = list(file_coverages.values())[0]
        
        # Check line coverage
        assert file_cov.lines_found == 3, f"Expected 3 lines found, got {file_cov.lines_found}"
        assert file_cov.lines_hit == 2, f"Expected 2 lines hit, got {file_cov.lines_hit}"
        
        # Check branch coverage
        assert file_cov.branches_found == 2, f"Expected 2 branches found, got {file_cov.branches_found}"
        assert file_cov.branches_hit == 2, f"Expected 2 branches hit, got {file_cov.branches_hit}"
        
        # Check function coverage
        assert file_cov.functions_found == 1, f"Expected 1 function found, got {file_cov.functions_found}"
        assert file_cov.functions_hit == 1, f"Expected 1 function hit, got {file_cov.functions_hit}"
        
        # Check percentages
        line_pct = file_cov.line_coverage_percent
        branch_pct = file_cov.branch_coverage_percent
        function_pct = file_cov.function_coverage_percent
        
        assert 0.0 <= line_pct <= 1.0, f"Line coverage out of range: {line_pct}"
        assert 0.0 <= branch_pct <= 1.0, f"Branch coverage out of range: {branch_pct}"
        assert 0.0 <= function_pct <= 1.0, f"Function coverage out of range: {function_pct}"
        
        print(f"✓ Line coverage: {line_pct:.2%}")
        print(f"✓ Branch coverage: {branch_pct:.2%}")
        print(f"✓ Function coverage: {function_pct:.2%}")
        
        print("✓ Basic lcov parsing test PASSED")
        return True
        
    finally:
        if os.path.exists(lcov_file):
            os.unlink(lcov_file)

def test_coverage_data_model():
    """Test CoverageData model."""
    print("\nTesting CoverageData model...")
    
    coverage = CoverageData(
        line_coverage=0.75,
        branch_coverage=0.80,
        function_coverage=0.90
    )
    
    # Check all metrics are present
    assert hasattr(coverage, 'line_coverage'), "Missing line_coverage"
    assert hasattr(coverage, 'branch_coverage'), "Missing branch_coverage"
    assert hasattr(coverage, 'function_coverage'), "Missing function_coverage"
    
    # Check values
    assert coverage.line_coverage == 0.75
    assert coverage.branch_coverage == 0.80
    assert coverage.function_coverage == 0.90
    
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
    
    print("✓ All three coverage metrics present")
    print("✓ Serialization/deserialization works")
    print("✓ CoverageData model test PASSED")
    return True

def test_coverage_merger():
    """Test coverage merging."""
    print("\nTesting coverage merger...")
    
    # Create two FileCoverage objects for the same file
    cov1 = FileCoverage(
        file_path="test.c",
        lines_found=5,
        lines_hit=3,
        branches_found=2,
        branches_hit=1,
        functions_found=1,
        functions_hit=1,
        line_details={1: 5, 2: 3, 3: 0, 4: 2, 5: 0},
        branch_details={2: [(0, 3), (1, 0)]},
        function_details={"func1": 5}
    )
    
    cov2 = FileCoverage(
        file_path="test.c",
        lines_found=5,
        lines_hit=4,
        branches_found=2,
        branches_hit=2,
        functions_found=1,
        functions_hit=1,
        line_details={1: 2, 2: 1, 3: 4, 4: 1, 5: 0},
        branch_details={2: [(0, 1), (1, 2)]},
        function_details={"func1": 3}
    )
    
    merger = CoverageMerger()
    merged = merger.merge_coverage_data([cov1, cov2])
    
    # Check merged has all metrics
    assert merged.lines_found > 0, "Merged should have lines"
    assert merged.branches_found > 0, "Merged should have branches"
    assert merged.functions_found > 0, "Merged should have functions"
    
    # Calculate percentages
    line_pct = merged.lines_hit / merged.lines_found if merged.lines_found > 0 else 0.0
    branch_pct = merged.branches_hit / merged.branches_found if merged.branches_found > 0 else 0.0
    function_pct = merged.functions_hit / merged.functions_found if merged.functions_found > 0 else 0.0
    
    assert 0.0 <= line_pct <= 1.0
    assert 0.0 <= branch_pct <= 1.0
    assert 0.0 <= function_pct <= 1.0
    
    print(f"✓ Merged line coverage: {line_pct:.2%}")
    print(f"✓ Merged branch coverage: {branch_pct:.2%}")
    print(f"✓ Merged function coverage: {function_pct:.2%}")
    print("✓ Coverage merger test PASSED")
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Coverage Analyzer Property Tests")
    print("=" * 60)
    
    tests = [
        test_basic_coverage_parsing,
        test_coverage_data_model,
        test_coverage_merger
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
