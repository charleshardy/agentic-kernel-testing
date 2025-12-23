#!/usr/bin/env python3
"""
Debug script to check current execution plans and identify debug test cases
"""

import sys
import os
sys.path.append('.')

def debug_current_state():
    """Debug current execution plans state"""
    
    print("=== Current Execution Plans Debug ===")
    print()
    
    try:
        from api.routers.tests import execution_plans
        
        print(f"Total execution plans: {len(execution_plans)}")
        print()
        
        for plan_id, plan_data in execution_plans.items():
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            status = plan_data.get("status", "unknown")
            created_at = plan_data.get("created_at", "unknown")
            
            # Check if it's a debug test
            is_debug_test = (
                created_by == "debug_script" or 
                any(test_id.startswith("test-123") for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
            )
            
            print(f"Plan ID: {plan_id}")
            print(f"  Status: {status}")
            print(f"  Created by: '{created_by}'")
            print(f"  Test case IDs: {test_case_ids}")
            print(f"  Created at: {created_at}")
            print(f"  Is debug test: {is_debug_test}")
            print(f"  Should be filtered: {is_debug_test or status in ['completed', 'failed', 'cancelled']}")
            print()
        
        # Also check submitted_tests
        from api.routers.tests import submitted_tests
        print(f"Total submitted tests: {len(submitted_tests)}")
        
        debug_test_count = 0
        for test_id, test_data in submitted_tests.items():
            if (test_id.startswith("test-123") or 
                test_id.startswith("test_") and test_id.endswith("123") or
                test_data.get("submitted_by") == "debug_script"):
                debug_test_count += 1
                print(f"Debug test found in submitted_tests: {test_id}")
                print(f"  Name: {test_data['test_case'].name}")
                print(f"  Submitted by: {test_data.get('submitted_by', 'unknown')}")
        
        print(f"Debug tests in submitted_tests: {debug_test_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_current_state()