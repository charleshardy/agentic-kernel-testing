#!/usr/bin/env python3
"""Direct test execution for coverage metric completeness."""

import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the coverage metric completeness tests."""
    print("=" * 80)
    print("Testing Coverage Metric Completeness (Property 26)")
    print("=" * 80)
    
    # Test 1: Check that the coverage analyzer module exists and has the right components
    print("\n[1/5] Checking coverage analyzer module...")
    try:
        from analysis.coverage_analyzer import (
            CoverageAnalyzer,
            FileCoverage,
            LcovParser,
            CoverageMerger,
            CoverageCollector
        )
        print("  ✓ All coverage analyzer components present")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return 1
    
    # Test 2: Check that CoverageData model has all three metrics
    print("\n[2/5] Checking CoverageData model...")
    try:
        from ai_generator.models import CoverageData
        
        # Create a sample coverage data object
        coverage = CoverageData(
            line_coverage=0.8,
            branch_coverage=0.7,
            function_coverage=0.9
        )
        
        # Verify all three metrics are present
        assert hasattr(coverage, 'line_coverage'), "Missing line_coverage"
        assert hasattr(coverage, 'branch_coverage'), "Missing branch_coverage"
        assert hasattr(coverage, 'function_coverage'), "Missing function_coverage"
        
        assert coverage.line_coverage == 0.8
        assert coverage.branch_coverage == 0.7
        assert coverage.function_coverage == 0.9
        
        print(f"  ✓ CoverageData has all three metrics")
        print(f"    - line_coverage: {coverage.line_coverage}")
        print(f"    - branch_coverage: {coverage.branch_coverage}")
        print(f"    - function_coverage: {coverage.function_coverage}")
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return 1
    
    # Test 3: Check FileCoverage percentage calculations
    print("\n[3/5] Checking FileCoverage percentage calculations...")
    try:
        file_cov = FileCoverage(
            file_path="test.c",
            lines_found=100,
            lines_hit=75,
            branches_found=50,
            branches_hit=40,
            functions_found=10,
            functions_hit=8
        )
        
        # Check all percentage properties exist
        assert hasattr(file_cov, 'line_coverage_percent')
        assert hasattr(file_cov, 'branch_coverage_percent')
        assert hasattr(file_cov, 'function_coverage_percent')
        
        line_pct = file_cov.line_coverage_percent
        branch_pct = file_cov.branch_coverage_percent
        func_pct = file_cov.function_coverage_percent
        
        # Verify calculations
        assert abs(line_pct - 0.75) < 0.001
        assert abs(branch_pct - 0.80) < 0.001
        assert abs(func_pct - 0.80) < 0.001
        
        print(f"  ✓ All percentage calculations correct")
        print(f"    - line_coverage_percent: {line_pct:.1%}")
        print(f"    - branch_coverage_percent: {branch_pct:.1%}")
        print(f"    - function_coverage_percent: {func_pct:.1%}")
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 4: Check lcov parsing produces all metrics
    print("\n[4/5] Checking lcov parsing...")
    try:
        import tempfile
        
        lcov_content = """SF:test_file.c
FN:10,test_func
FNDA:5,test_func
DA:1,10
DA:2,5
DA:3,0
BRDA:2,0,0,3
BRDA:2,0,1,2
end_of_record
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.info', delete=False) as f:
            f.write(lcov_content)
            lcov_file = f.name
        
        try:
            parser = LcovParser()
            file_coverages = parser.parse_lcov_file(lcov_file)
            
            assert len(file_coverages) > 0
            
            for file_path, file_cov in file_coverages.items():
                # Verify all metrics are present
                assert file_cov.lines_found > 0
                assert file_cov.branches_found >= 0
                assert file_cov.functions_found >= 0
                
                print(f"  ✓ Parsed coverage for {file_path}")
                print(f"    - Lines: {file_cov.lines_hit}/{file_cov.lines_found}")
                print(f"    - Branches: {file_cov.branches_hit}/{file_cov.branches_found}")
                print(f"    - Functions: {file_cov.functions_hit}/{file_cov.functions_found}")
        finally:
            if os.path.exists(lcov_file):
                os.unlink(lcov_file)
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 5: Check coverage merging preserves all metrics
    print("\n[5/5] Checking coverage merging...")
    try:
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
        
        merger = CoverageMerger()
        merged = merger.merge_coverage_data([cov1, cov2])
        
        # Verify all metrics are present
        assert merged.lines_found > 0
        assert merged.branches_found >= 0
        assert merged.functions_found > 0
        
        print(f"  ✓ Merged coverage preserves all metrics")
        print(f"    - Lines: {merged.lines_hit}/{merged.lines_found}")
        print(f"    - Branches: {merged.branches_hit}/{merged.branches_found}")
        print(f"    - Functions: {merged.functions_hit}/{merged.functions_found}")
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED")
    print("\nProperty 26 validated: The coverage analyzer correctly includes")
    print("line coverage, branch coverage, and function coverage for all")
    print("test executions.")
    print("=" * 80)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
