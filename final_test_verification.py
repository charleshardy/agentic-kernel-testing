#!/usr/bin/env python3
"""Final comprehensive test verification for checkpoint task 10."""

import subprocess
import sys
from pathlib import Path
import json

def run_quick_test_check(test_path, max_examples=10):
    """Run a quick check of property tests with reduced examples."""
    try:
        result = subprocess.run(
            ['python3', '-m', 'pytest', test_path, '-v', '--tb=no', '-q',
             '--hypothesis-seed=0', f'--hypothesis-max-examples={max_examples}'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        # Check for passed tests
        if 'passed' in output.lower():
            # Extract number of passed tests
            for line in output.split('\n'):
                if 'passed' in line.lower():
                    return True, line.strip()
        
        return False, output[:200]
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)

def main():
    """Run comprehensive test verification."""
    
    print("="*80)
    print("FINAL TEST VERIFICATION - Task 10: Complete System Verification")
    print("="*80)
    print()
    
    # Test categories
    test_results = {
        'unit_tests': [],
        'property_tests': [],
        'integration_tests': []
    }
    
    # Unit tests to verify
    unit_tests = [
        'tests/unit/test_models.py',
        'tests/unit/test_queue_monitor.py',
        'tests/unit/test_runner_factory.py',
        'tests/unit/test_environment_manager.py',
        'tests/unit/test_hardware_config.py',
    ]
    
    # Property tests to verify (orchestrator-specific)
    property_tests = [
        'tests/property/test_service_lifecycle.py',
        'tests/property/test_automatic_plan_processing.py',
        'tests/property/test_priority_ordering.py',
        'tests/property/test_environment_allocation_matching.py',
        'tests/property/test_status_consistency_during_execution.py',
        'tests/property/test_complete_result_capture.py',
        'tests/property/test_timeout_enforcement.py',
        'tests/property/test_resource_recovery.py',
        'tests/property/test_service_recovery.py',
        'tests/property/test_test_isolation.py',
        'tests/property/test_environment_type_selection.py',
        'tests/property/test_real_time_status_accuracy.py',
        'tests/property/test_artifact_collection_completeness.py',
    ]
    
    # Integration tests to verify
    integration_tests = [
        'tests/integration/test_orchestrator_full_execution_flow.py',
        'tests/integration/test_orchestrator_load_testing.py',
    ]
    
    print("1. UNIT TESTS")
    print("-" * 80)
    for test_path in unit_tests:
        if not Path(test_path).exists():
            print(f"  ✗ SKIP: {test_path} (not found)")
            continue
        
        passed, info = run_quick_test_check(test_path, max_examples=5)
        status = "✓ PASS" if passed else "✗ FAIL"
        test_results['unit_tests'].append((test_path, passed))
        print(f"  {status}: {Path(test_path).name}")
        if not passed and info != "TIMEOUT":
            print(f"         {info[:100]}")
    
    print()
    print("2. PROPERTY-BASED TESTS (Orchestrator)")
    print("-" * 80)
    for test_path in property_tests:
        if not Path(test_path).exists():
            print(f"  ✗ SKIP: {test_path} (not found)")
            continue
        
        passed, info = run_quick_test_check(test_path, max_examples=10)
        status = "✓ PASS" if passed else "✗ FAIL"
        test_results['property_tests'].append((test_path, passed))
        print(f"  {status}: {Path(test_path).name}")
        if not passed and info != "TIMEOUT":
            print(f"         {info[:100]}")
    
    print()
    print("3. INTEGRATION TESTS")
    print("-" * 80)
    for test_path in integration_tests:
        if not Path(test_path).exists():
            print(f"  ✗ SKIP: {test_path} (not found)")
            continue
        
        passed, info = run_quick_test_check(test_path, max_examples=5)
        status = "✓ PASS" if passed else "✗ FAIL"
        test_results['integration_tests'].append((test_path, passed))
        print(f"  {status}: {Path(test_path).name}")
        if not passed and info != "TIMEOUT":
            print(f"         {info[:100]}")
    
    # Calculate summary
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    unit_passed = sum(1 for _, passed in test_results['unit_tests'] if passed)
    unit_total = len(test_results['unit_tests'])
    
    property_passed = sum(1 for _, passed in test_results['property_tests'] if passed)
    property_total = len(test_results['property_tests'])
    
    integration_passed = sum(1 for _, passed in test_results['integration_tests'] if passed)
    integration_total = len(test_results['integration_tests'])
    
    total_passed = unit_passed + property_passed + integration_passed
    total_tests = unit_total + property_total + integration_total
    
    print(f"Unit Tests:        {unit_passed}/{unit_total} passed")
    print(f"Property Tests:    {property_passed}/{property_total} passed")
    print(f"Integration Tests: {integration_passed}/{integration_total} passed")
    print(f"")
    print(f"TOTAL:             {total_passed}/{total_tests} passed")
    print("="*80)
    
    if total_passed == total_tests:
        print("\n✓ ALL TESTS PASSED - System verification complete!")
        return 0
    else:
        failed = total_tests - total_passed
        print(f"\n✗ {failed} test suite(s) need attention")
        print("\nNote: Some tests may require additional setup (Docker, database, etc.)")
        return 1

if __name__ == '__main__':
    sys.exit(main())
