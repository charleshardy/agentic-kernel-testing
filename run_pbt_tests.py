#!/usr/bin/env python3
"""Run property-based tests for task 5."""

import sys
import os

# Set up path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to run with pytest
try:
    import pytest
    
    print("Running property-based tests with pytest...")
    print("=" * 70)
    
    exit_code = pytest.main([
        'tests/property/test_test_summary_organization.py',
        '-v',
        '--tb=short',
        '-x'  # Stop on first failure
    ])
    
    if exit_code == 0:
        print("\n" + "=" * 70)
        print("✅ ALL PROPERTY-BASED TESTS PASSED!")
        print("=" * 70)
    
    sys.exit(exit_code)
    
except Exception as e:
    print(f"Error running pytest: {e}")
    print("\nFalling back to manual test execution...")
    sys.exit(1)
