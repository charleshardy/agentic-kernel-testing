#!/usr/bin/env python3
"""Simple runner for property-based tests."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pytest
    
    # Run the specific property test
    exit_code = pytest.main([
        'tests/property/test_test_summary_organization.py',
        '-v',
        '--hypothesis-show-statistics',
        '--tb=short'
    ])
    
    sys.exit(exit_code)
    
except ImportError as e:
    print(f"Error: {e}")
    print("\nTrying to run tests without pytest...")
    
    # Import the test module directly
    from tests.property.test_test_summary_organization import TestTestSummaryOrganization
    from hypothesis import given, settings
    
    test_class = TestTestSummaryOrganization()
    
    print("Running property-based tests manually...")
    print("=" * 70)
    
    # Run a few key tests
    tests_to_run = [
        ('test_empty_test_list_produces_empty_summary', test_class.test_empty_test_list_produces_empty_summary),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_method in tests_to_run:
        try:
            print(f"\nRunning {test_name}...")
            test_method()
            print(f"  ✓ PASSED")
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    sys.exit(0 if failed == 0 else 1)
