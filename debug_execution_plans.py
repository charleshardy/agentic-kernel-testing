#!/usr/bin/env python3
"""
Debug what's in the execution_plans dictionary
"""

import sys
sys.path.append('.')

def debug_execution_plans():
    """Debug execution plans"""
    
    print("=== Debugging Execution Plans ===")
    print()
    
    try:
        from api.routers.tests import execution_plans, submitted_tests
        
        print(f"1. Execution Plans Dictionary:")
        print(f"   Total plans: {len(execution_plans)}")
        
        if execution_plans:
            for plan_id, plan_data in execution_plans.items():
                print(f"\n   Plan ID: {plan_id}")
                print(f"   Status: {plan_data.get('status', 'unknown')}")
                print(f"   Test IDs: {plan_data.get('test_case_ids', [])}")
                print(f"   Created at: {plan_data.get('created_at', 'unknown')}")
                print(f"   Created by: {plan_data.get('created_by', 'unknown')}")
                
                # Check if this plan should be included in active executions
                status = plan_data.get("status")
                should_include = status not in ["completed", "failed", "cancelled"]
                print(f"   Should include in active: {should_include} (status: {status})")
        else:
            print("   No execution plans found")
        
        print(f"\n2. Submitted Tests Dictionary:")
        print(f"   Total tests: {len(submitted_tests)}")
        
        if submitted_tests:
            for test_id, test_data in list(submitted_tests.items())[-3:]:  # Show last 3
                print(f"\n   Test ID: {test_id}")
                print(f"   Name: {test_data['test_case'].name}")
                print(f"   Status: {test_data.get('execution_status', 'unknown')}")
                print(f"   Submitted by: {test_data.get('submitted_by', 'unknown')}")
        
        # Test the filtering logic directly
        print(f"\n3. Testing Active Execution Logic:")
        active_executions = []
        for plan_id, plan_data in execution_plans.items():
            status = plan_data.get("status")
            print(f"   Plan {plan_id}: status='{status}', excluded={status in ['completed', 'failed', 'cancelled']}")
            
            if status not in ["completed", "failed", "cancelled"]:
                active_executions.append({
                    "plan_id": plan_id,
                    "status": status,
                    "test_count": len(plan_data.get("test_case_ids", []))
                })
        
        print(f"   Result: {len(active_executions)} active executions")
        for execution in active_executions:
            print(f"     - {execution['plan_id']}: {execution['status']} ({execution['test_count']} tests)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_execution_plans()