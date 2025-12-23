#!/usr/bin/env python3
"""
Comprehensive cleanup script to remove all debug test cases from both execution_plans and submitted_tests
"""

import sys
import os
sys.path.append('.')

def comprehensive_cleanup():
    """Comprehensive cleanup of debug test cases"""
    
    print("=== Comprehensive Debug Test Cleanup ===")
    print()
    
    try:
        from api.routers.tests import execution_plans, submitted_tests
        
        print(f"Before cleanup:")
        print(f"  - Execution plans: {len(execution_plans)}")
        print(f"  - Submitted tests: {len(submitted_tests)}")
        print()
        
        # Clean up execution_plans
        debug_plans_to_remove = []
        for plan_id, plan_data in execution_plans.items():
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            
            # Identify debug test cases with broader patterns
            is_debug_test = (
                created_by == "debug_script" or 
                created_by == "debug" or
                any(test_id.startswith("test-123") for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids) or
                any("debug" in test_id.lower() for test_id in test_case_ids) or
                any("test" in test_id and len(test_id) < 10 for test_id in test_case_ids)  # Short test IDs are likely debug
            )
            
            if is_debug_test:
                debug_plans_to_remove.append(plan_id)
                print(f"  Debug execution plan: {plan_id} (created_by: {created_by}, tests: {test_case_ids})")
        
        # Remove debug execution plans
        removed_plans = 0
        for plan_id in debug_plans_to_remove:
            if plan_id in execution_plans:
                del execution_plans[plan_id]
                removed_plans += 1
        
        print(f"Removed {removed_plans} debug execution plans")
        print()
        
        # Clean up submitted_tests
        debug_tests_to_remove = []
        for test_id, test_data in submitted_tests.items():
            submitted_by = test_data.get("submitted_by", "")
            test_name = test_data.get("test_case", {}).name if hasattr(test_data.get("test_case", {}), 'name') else ""
            
            # Identify debug test cases
            is_debug_test = (
                submitted_by == "debug_script" or
                submitted_by == "debug" or
                test_id.startswith("test-123") or
                test_id.startswith("test_") and test_id.endswith("123") or
                "debug" in test_id.lower() or
                "debug" in test_name.lower() or
                (len(test_id) < 10 and "test" in test_id)  # Short test IDs are likely debug
            )
            
            if is_debug_test:
                debug_tests_to_remove.append(test_id)
                print(f"  Debug test case: {test_id} (submitted_by: {submitted_by}, name: {test_name})")
        
        # Remove debug test cases
        removed_tests = 0
        for test_id in debug_tests_to_remove:
            if test_id in submitted_tests:
                del submitted_tests[test_id]
                removed_tests += 1
        
        print(f"Removed {removed_tests} debug test cases")
        print()
        
        print(f"After cleanup:")
        print(f"  - Execution plans: {len(execution_plans)}")
        print(f"  - Submitted tests: {len(submitted_tests)}")
        print()
        
        # Show remaining items
        if execution_plans:
            print("Remaining execution plans:")
            for plan_id, plan_data in execution_plans.items():
                created_by = plan_data.get("created_by", "")
                test_case_ids = plan_data.get("test_case_ids", [])
                status = plan_data.get("status", "unknown")
                print(f"  - {plan_id}: {status} ({len(test_case_ids)} tests, by: {created_by})")
        
        if submitted_tests:
            print(f"\nRemaining submitted tests: {len(submitted_tests)}")
            for test_id, test_data in list(submitted_tests.items())[:5]:  # Show first 5
                submitted_by = test_data.get("submitted_by", "")
                test_name = test_data.get("test_case", {}).name if hasattr(test_data.get("test_case", {}), 'name') else ""
                print(f"  - {test_id}: {test_name} (by: {submitted_by})")
            if len(submitted_tests) > 5:
                print(f"  ... and {len(submitted_tests) - 5} more")
        
        print()
        print(f"✅ Cleanup complete! Removed {removed_plans} execution plans and {removed_tests} test cases")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    comprehensive_cleanup()