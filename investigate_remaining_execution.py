#!/usr/bin/env python3
"""
Investigate and clean up the remaining execution plan that's not being filtered.
"""

import sys
import os
sys.path.insert(0, '.')

try:
    from api.routers.tests import execution_plans, submitted_tests
    from datetime import datetime
    
    print("=== Investigating Remaining Execution Plan ===")
    print(f"Total execution plans: {len(execution_plans)}")
    print(f"Total submitted tests: {len(submitted_tests)}")
    
    if execution_plans:
        print("\n=== Execution Plan Details ===")
        for plan_id, plan_data in execution_plans.items():
            print(f"Plan ID: {plan_id}")
            print(f"  Status: {plan_data.get('status', 'unknown')}")
            print(f"  Created by: {plan_data.get('created_by', 'unknown')}")
            print(f"  Created at: {plan_data.get('created_at', 'unknown')}")
            print(f"  Test case IDs: {plan_data.get('test_case_ids', [])}")
            
            # Check if this should be filtered
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            
            is_debug_test = (
                created_by == "debug_script" or 
                any(test_id.startswith("test-123") for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
            )
            
            print(f"  Should be filtered (debug): {is_debug_test}")
            print(f"  Debug criteria:")
            print(f"    - created_by == 'debug_script': {created_by == 'debug_script'}")
            print(f"    - test IDs start with 'test-123': {any(test_id.startswith('test-123') for test_id in test_case_ids)}")
            print(f"    - test IDs pattern 'test_*123': {any(test_id.startswith('test_') and test_id.endswith('123') for test_id in test_case_ids)}")
            
            # Check the actual test cases
            print(f"  Test case details:")
            for test_id in test_case_ids:
                if test_id in submitted_tests:
                    test_data = submitted_tests[test_id]
                    test_case = test_data.get("test_case")
                    print(f"    Test {test_id}: {test_case.name if test_case else 'No test case'}")
                else:
                    print(f"    Test {test_id}: NOT FOUND in submitted_tests")
            
            print()
    
    # Clean up any remaining plans that should be filtered
    plans_to_remove = []
    for plan_id, plan_data in execution_plans.items():
        created_by = plan_data.get("created_by", "")
        test_case_ids = plan_data.get("test_case_ids", [])
        status = plan_data.get("status", "")
        
        # More aggressive cleanup - remove any old queued plans or plans with missing tests
        should_remove = False
        
        # Check if it's a debug test
        is_debug_test = (
            created_by == "debug_script" or 
            any(test_id.startswith("test-123") for test_id in test_case_ids) or
            any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
        )
        
        if is_debug_test:
            should_remove = True
            print(f"Marking {plan_id} for removal: debug test")
        
        # Check if all test cases are missing
        missing_tests = [test_id for test_id in test_case_ids if test_id not in submitted_tests]
        if len(missing_tests) == len(test_case_ids) and test_case_ids:
            should_remove = True
            print(f"Marking {plan_id} for removal: all test cases missing")
        
        # Check if it's an old queued plan (more than 1 hour old)
        created_at = plan_data.get("created_at")
        if created_at and hasattr(created_at, 'timestamp'):
            age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
            if age_hours > 1 and status == "queued":
                should_remove = True
                print(f"Marking {plan_id} for removal: old queued plan ({age_hours:.1f} hours)")
        
        if should_remove:
            plans_to_remove.append(plan_id)
    
    # Remove the plans
    removed_count = 0
    for plan_id in plans_to_remove:
        if plan_id in execution_plans:
            print(f"Removing execution plan: {plan_id}")
            del execution_plans[plan_id]
            removed_count += 1
    
    print(f"\n=== Cleanup Complete ===")
    print(f"Removed {removed_count} execution plans")
    print(f"Remaining execution plans: {len(execution_plans)}")
    print(f"Remaining submitted tests: {len(submitted_tests)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()