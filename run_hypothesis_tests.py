#!/usr/bin/env python3
"""Run hypothesis property-based tests directly."""

import sys
sys.path.insert(0, '.')

print("Importing test module...")
try:
    # Import the test module
    from tests.property import test_compatibility_matrix_completeness
    
    print("Running property-based tests...")
    print("=" * 70)
    
    # Run each test function
    test_functions = [
        ('test_compatibility_matrix_completeness', test_compatibility_matrix_completeness.test_compatibility_matrix_completeness),
        ('test_matrix_cell_status_accuracy', test_compatibility_matrix_completeness.test_matrix_cell_status_accuracy),
        ('test_matrix_pass_rate_calculation', test_compatibility_matrix_completeness.test_matrix_pass_rate_calculation),
        ('test_matrix_population_preserves_completeness', test_compatibility_matrix_completeness.test_matrix_population_preserves_completeness),
        ('test_matrix_merge_completeness', test_compatibility_matrix_completeness.test_matrix_merge_completeness),
        ('test_matrix_summary_consistency', test_compatibility_matrix_completeness.test_matrix_summary_consistency),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in test_functions:
        try:
            print(f"\nRunning {test_name}...")
            test_func()
            print(f"  ✅ {test_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    if failed == 0:
        print(f"✅ ALL {passed} PROPERTY-BASED TESTS PASSED!")
    else:
        print(f"❌ {failed} tests failed, {passed} tests passed")
    print("=" * 70)
    
    sys.exit(0 if failed == 0 else 1)
    
except ImportError as e:
    print(f"Error importing test module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"Error running tests: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
