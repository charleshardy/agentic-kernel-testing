#!/usr/bin/env python3
"""
Deep debug of execution state to find persistent test-123 entries.
"""

import sys
import os
sys.path.insert(0, '.')

def debug_execution_state():
    try:
        # Import the actual data structures
        from api.routers.tests import execution_plans, submitted_tests
        from datetime import datetime
        
        print("=== DEEP DEBUG: Execution State Analysis ===")
        print(f"Execution plans count: {len(execution_plans)}")
        print(f"Submitted tests count: {len(submitted_tests)}")
        
        # Examine each execution plan in detail
        if execution_plans:
            print("\n=== EXECUTION PLANS ANALYSIS ===")
            for plan_id, plan_data in execution_plans.items():
                print(f"\nPlan ID: {plan_id}")
                print(f"  Status: {plan_data.get('status')}")
                print(f"  Created by: {plan_data.get('created_by')}")
                print(f"  Created at: {plan_data.get('created_at')}")
                print(f"  Test case IDs: {plan_data.get('test_case_ids')}")
                
                # Check filtering criteria
                created_by = plan_data.get("created_by", "")
                test_case_ids = plan_data.get("test_case_ids", [])
                status = plan_data.get("status")
                
                print(f"  Filtering analysis:")
                print(f"    - created_by == 'debug_script': {created_by == 'debug_script'}")
                print(f"    - Any test ID starts with 'test-123': {any(test_id.startswith('test-123') for test_id in test_case_ids)}")
                print(f"    - Any test ID matches 'test_*123': {any(test_id.startswith('test_') and test_id.endswith('123') for test_id in test_case_ids)}")
                print(f"    - Status in final states: {status in ['completed', 'failed', 'cancelled']}")
                
                # Check if this would be included in active executions
                is_debug_test = (
                    created_by == "debug_script" or 
                    any(test_id.startswith("test-123") for test_id in test_case_ids) or
                    any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
                )
                
                should_be_filtered = is_debug_test or status in ["completed", "failed", "cancelled"]
                print(f"    - Should be filtered: {should_be_filtered}")
                print(f"    - Would appear in active executions: {not should_be_filtered}")
        
        # Examine submitted tests
        if submitted_tests:
            print(f"\n=== SUBMITTED TESTS ANALYSIS ===")
            debug_tests = []
            for test_id, test_data in submitted_tests.items():
                test_case = test_data.get("test_case")
                if test_case and ("test-123" in test_case.name or "test-123" in test_id):
                    debug_tests.append((test_id, test_case.name))
            
            if debug_tests:
                print(f"Found {len(debug_tests)} debug tests:")
                for test_id, name in debug_tests:
                    print(f"  - {test_id}: {name}")
            else:
                print("No debug tests found in submitted_tests")
        
        # Force cleanup of any remaining problematic entries
        print(f"\n=== FORCE CLEANUP ===")
        plans_removed = 0
        tests_removed = 0
        
        # Remove any execution plans that should be filtered
        plans_to_remove = []
        for plan_id, plan_data in execution_plans.items():
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            status = plan_data.get("status")
            
            # More aggressive filtering
            should_remove = (
                created_by == "debug_script" or
                any("test-123" in str(test_id) for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids) or
                status in ["completed", "failed", "cancelled"] or
                # Remove any plan older than 2 hours that's still queued
                (status == "queued" and plan_data.get("created_at") and 
                 hasattr(plan_data.get("created_at"), 'timestamp') and
                 (datetime.utcnow() - plan_data.get("created_at")).total_seconds() > 7200)
            )
            
            if should_remove:
                plans_to_remove.append(plan_id)
        
        for plan_id in plans_to_remove:
            if plan_id in execution_plans:
                print(f"Removing execution plan: {plan_id}")
                del execution_plans[plan_id]
                plans_removed += 1
        
        # Remove any debug test cases
        tests_to_remove = []
        for test_id, test_data in submitted_tests.items():
            test_case = test_data.get("test_case")
            created_by = test_data.get("submitted_by", "")
            
            should_remove = (
                created_by == "debug_script" or
                "test-123" in test_id or
                (test_case and "test-123" in test_case.name) or
                test_id.startswith("test_") and test_id.endswith("123")
            )
            
            if should_remove:
                tests_to_remove.append(test_id)
        
        for test_id in tests_to_remove:
            if test_id in submitted_tests:
                print(f"Removing submitted test: {test_id}")
                del submitted_tests[test_id]
                tests_removed += 1
        
        print(f"\nCleanup complete:")
        print(f"  - Removed {plans_removed} execution plans")
        print(f"  - Removed {tests_removed} submitted tests")
        print(f"  - Remaining execution plans: {len(execution_plans)}")
        print(f"  - Remaining submitted tests: {len(submitted_tests)}")
        
        return len(execution_plans), len(submitted_tests)
        
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()
        return -1, -1

if __name__ == "__main__":
    debug_execution_state()