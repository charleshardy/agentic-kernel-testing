#!/usr/bin/env python3
"""Run property-based tests for task 9 manually."""

import sys
sys.path.insert(0, '.')

# Import hypothesis and run tests manually
from hypothesis import given, strategies as st, settings
from tests.property.test_result_aggregation import (
    test_aggregation_by_architecture,
    test_aggregation_by_board_type,
    test_aggregation_by_peripheral_config,
    test_aggregation_overall_statistics,
    test_aggregation_all_dimensions_represented
)
from tests.property.test_diagnostic_capture import (
    test_diagnostic_capture_on_failure,
    test_diagnostic_capture_for_multiple_failures,
    test_diagnostic_capture_includes_kernel_logs,
    test_diagnostic_capture_includes_stack_trace_on_failure,
    test_diagnostic_capture_completeness_structure
)

def run_test(test_func, test_name):
    """Run a single test function."""
    print(f"\nRunning: {test_name}")
    print("-" * 70)
    try:
        test_func()
        print(f"✅ PASSED: {test_name}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all property-based tests."""
    print("=" * 70)
    print("RUNNING PROPERTY-BASED TESTS FOR TASK 9")
    print("=" * 70)
    
    tests = [
        # Result aggregation tests (Property 7)
        (test_aggregation_overall_statistics, "Property 7: Aggregation overall statistics"),
        (test_aggregation_by_architecture, "Property 7: Aggregation by architecture"),
        (test_aggregation_by_board_type, "Property 7: Aggregation by board type"),
        (test_aggregation_by_peripheral_config, "Property 7: Aggregation by peripheral config"),
        (test_aggregation_all_dimensions_represented, "Property 7: All dimensions represented"),
        
        # Diagnostic capture tests (Property 16)
        (test_diagnostic_capture_on_failure, "Property 16: Diagnostic capture on failure"),
        (test_diagnostic_capture_includes_kernel_logs, "Property 16: Includes kernel logs"),
        (test_diagnostic_capture_includes_stack_trace_on_failure, "Property 16: Includes stack trace"),
        (test_diagnostic_capture_completeness_structure, "Property 16: Completeness structure"),
        (test_diagnostic_capture_for_multiple_failures, "Property 16: Multiple failures"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("✅ ALL PROPERTY-BASED TESTS PASSED!")
        return 0
    else:
        print(f"❌ {failed} TEST(S) FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
