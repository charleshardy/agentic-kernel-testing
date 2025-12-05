#!/usr/bin/env python3
"""Direct execution of property-based tests."""

import sys
import os

# Set PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment to suppress warnings
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

def main():
    try:
        # Try pytest first
        import pytest
        print("Using pytest to run property-based tests...")
        exit_code = pytest.main([
            'tests/property/test_compatibility_matrix_completeness.py',
            '-v',
            '--tb=line',
            '--hypothesis-show-statistics',
            '-x'
        ])
        return exit_code
    except ImportError:
        print("pytest not available, running tests directly...")
        
        # Import and run tests directly
        from hypothesis import given, settings
        from tests.property.test_compatibility_matrix_completeness import (
            test_compatibility_matrix_completeness,
            test_matrix_cell_status_accuracy,
            test_matrix_pass_rate_calculation
        )
        
        tests = [
            test_compatibility_matrix_completeness,
            test_matrix_cell_status_accuracy,
            test_matrix_pass_rate_calculation
        ]
        
        for test in tests:
            print(f"\nRunning {test.__name__}...")
            try:
                test()
                print(f"✅ PASSED")
            except Exception as e:
                print(f"❌ FAILED: {e}")
                return 1
        
        print("\n✅ All tests passed!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
