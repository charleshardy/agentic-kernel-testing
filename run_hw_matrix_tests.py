#!/usr/bin/env python3
"""Run property-based tests for hardware matrix coverage (task 6.1)."""

import sys
import os

# Set up path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to run with pytest
try:
    import pytest
    
    print("Running hardware matrix coverage property-based tests...")
    print("=" * 70)
    
    exit_code = pytest.main([
        'tests/property/test_hardware_matrix_coverage.py',
        '-v',
        '--tb=short',
        '--hypothesis-show-statistics'
    ])
    
    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ ALL HARDWARE MATRIX COVERAGE TESTS PASSED!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
    
    sys.exit(exit_code)
    
except Exception as e:
    print(f"Error running pytest: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
