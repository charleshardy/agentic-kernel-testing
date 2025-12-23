#!/usr/bin/env python3
"""
Script to clean up debug test cases from the execution_plans dictionary
"""

import sys
import os
sys.path.append('.')

def cleanup_debug_tests():
    """Clean up debug test cases from execution plans"""
    
    print("=== Debug Test Cleanup ===")
    print()
    
    try:
        from api.routers.tests import execution_plans
        
        print(f"Current execution plans: {len(execution_plans)}")
        
        # Find debug test plans
        debug_plans_to_remove = []
        regular_plans = []
        
        for plan_id, plan_data in execution_plans.items():
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            status = plan_data.get("status", "unknown")
            
            # Identify debug test cases
            is_debug_test = (
                created_by == "debug_script" or 
                any(test_id.startswith("test-123") for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
            )
            
            if is_debug_test:
                debug_plans_to_remove.append(plan_id)
                print(f"   Debug plan found: {plan_id} (created_by: {created_by}, tests: {test_case_ids}, status: {status})")
            else:
                regular_plans.append(plan_id)
                print(f"   Regular plan: {plan_id} (created_by: {created_by}, tests: {len(test_case_ids)} tests, status: {status})")
        
        print()
        print(f"Found {len(debug_plans_to_remove)} debug plans to remove")
        print(f"Found {len(regular_plans)} regular plans to keep")
        
        # Remove debug plans
        removed_count = 0
        for plan_id in debug_plans_to_remove:
            if plan_id in execution_plans:
                del execution_plans[plan_id]
                removed_count += 1
                print(f"   Removed: {plan_id}")
        
        print()
        print(f"Successfully removed {removed_count} debug test plans")
        print(f"Remaining execution plans: {len(execution_plans)}")
        
        # Show remaining plans
        if execution_plans:
            print("\nRemaining plans:")
            for plan_id, plan_data in execution_plans.items():
                created_by = plan_data.get("created_by", "")
                test_case_ids = plan_data.get("test_case_ids", [])
                status = plan_data.get("status", "unknown")
                print(f"   {plan_id}: {status} ({len(test_case_ids)} tests, by: {created_by})")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=== Cleanup Complete ===")

if __name__ == "__main__":
    cleanup_debug_tests()