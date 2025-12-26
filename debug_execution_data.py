#!/usr/bin/env python3
"""Debug script to check execution data and test plan names."""

import sys
import os
import requests
import json

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def debug_execution_data():
    """Debug the execution data to see what's missing."""
    
    print("🔍 Debugging Execution Data and Test Plan Names")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Step 1: Authenticate
    print("\n1. Authenticating...")
    try:
        auth_response = requests.post(f"{base_url}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=5)
        
        if auth_response.status_code == 200:
            token = auth_response.json().get('data', {}).get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Authentication successful")
        else:
            headers = {}
            print("⚠️ Authentication failed, proceeding without token")
    except Exception as e:
        headers = {}
        print(f"⚠️ Authentication error: {e}")
    
    # Step 2: Get current active executions
    print("\n2. Getting current active executions...")
    try:
        response = requests.get(f"{base_url}/execution/active", 
                              headers=headers, 
                              timeout=5)
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            executions = data.get('executions', [])
            print(f"✅ Found {len(executions)} active executions")
            
            for i, execution in enumerate(executions):
                print(f"\n   Execution {i+1}:")
                print(f"   - Plan ID: {execution.get('plan_id', 'N/A')[:20]}...")
                print(f"   - Test Plan Name: {execution.get('test_plan_name', 'MISSING')}")
                print(f"   - Test Plan ID: {execution.get('test_plan_id', 'N/A')}")
                print(f"   - Status: {execution.get('overall_status', 'N/A')}")
                print(f"   - Created By: {execution.get('created_by', 'N/A')}")
                print(f"   - Total Tests: {execution.get('total_tests', 'N/A')}")
                
        else:
            print(f"❌ Failed to get active executions: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting active executions: {e}")
        return False
    
    # Step 3: Get current test plans
    print("\n3. Getting current test plans...")
    try:
        response = requests.get(f"{base_url}/test-plans", 
                              headers=headers, 
                              timeout=5)
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            plans = data.get('plans', [])
            print(f"✅ Found {len(plans)} test plans")
            
            for i, plan in enumerate(plans):
                print(f"\n   Test Plan {i+1}:")
                print(f"   - Plan ID: {plan.get('id', 'N/A')[:20]}...")
                print(f"   - Name: {plan.get('name', 'N/A')}")
                print(f"   - Status: {plan.get('status', 'N/A')}")
                print(f"   - Test IDs: {len(plan.get('test_ids', []))} tests")
                
        else:
            print(f"❌ Failed to get test plans: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting test plans: {e}")
    
    # Step 4: Clean up old executions
    print("\n4. Cleaning up old/debug executions...")
    try:
        response = requests.post(f"{base_url}/execution/cleanup-debug", 
                               headers=headers, 
                               timeout=5)
        
        if response.status_code == 200:
            cleanup_data = response.json().get('data', {})
            removed_count = cleanup_data.get('removed_count', 0)
            remaining_count = cleanup_data.get('remaining_count', 0)
            print(f"✅ Cleaned up {removed_count} debug executions")
            print(f"   Remaining executions: {remaining_count}")
        else:
            print(f"⚠️ Failed to cleanup executions: {response.text}")
            
    except Exception as e:
        print(f"⚠️ Error cleaning up executions: {e}")
    
    # Step 5: Create a new test plan and execute it
    print("\n5. Creating and executing a new test plan...")
    try:
        test_plan_data = {
            "name": "🔧 Debug Test Plan",
            "description": "Test plan for debugging test plan name display",
            "test_ids": ["debug_test_001", "debug_test_002"],
            "tags": ["debug", "test-plan-name"],
            "execution_config": {
                "environment_preference": "qemu-x86",
                "priority": 5,
                "timeout_minutes": 30,
                "retry_failed": False,
                "parallel_execution": True
            },
            "status": "active"
        }
        
        # Create test plan
        response = requests.post(f"{base_url}/test-plans", 
                               json=test_plan_data, 
                               headers=headers, 
                               timeout=5)
        
        if response.status_code == 200:
            test_plan = response.json().get('data', {})
            plan_id = test_plan.get('id')
            plan_name = test_plan.get('name')
            print(f"✅ Created test plan: '{plan_name}'")
            
            # Execute test plan
            response = requests.post(f"{base_url}/test-plans/{plan_id}/execute", 
                                   headers=headers, 
                                   timeout=5)
            
            if response.status_code == 200:
                execution_data = response.json().get('data', {})
                execution_plan_id = execution_data.get('execution_plan_id')
                print(f"✅ Executed test plan: {execution_plan_id[:20]}...")
                
                # Check if it appears in active executions with the name
                import time
                time.sleep(1)  # Wait a moment for the data to be available
                
                response = requests.get(f"{base_url}/execution/active", 
                                      headers=headers, 
                                      timeout=5)
                
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    executions = data.get('executions', [])
                    
                    # Look for our new execution
                    found_execution = None
                    for execution in executions:
                        if execution.get('plan_id') == execution_plan_id:
                            found_execution = execution
                            break
                    
                    if found_execution:
                        test_plan_name_in_execution = found_execution.get('test_plan_name')
                        print(f"✅ Found new execution in active list:")
                        print(f"   Test Plan Name: '{test_plan_name_in_execution}'")
                        
                        if test_plan_name_in_execution == plan_name:
                            print("🎉 SUCCESS: Test plan name is correctly displayed!")
                        else:
                            print(f"❌ ISSUE: Name mismatch")
                            print(f"   Expected: '{plan_name}'")
                            print(f"   Got: '{test_plan_name_in_execution}'")
                    else:
                        print("❌ New execution not found in active list")
                
                # Clean up
                requests.delete(f"{base_url}/test-plans/{plan_id}", headers=headers, timeout=5)
                print("✅ Cleaned up test plan")
                
            else:
                print(f"❌ Failed to execute test plan: {response.text}")
        else:
            print(f"❌ Failed to create test plan: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in test plan creation/execution: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Debug Summary:")
    print("1. Check if existing executions have test_plan_name field")
    print("2. Clean up old executions without proper data")
    print("3. Test new execution creation with test plan names")
    print("4. Verify the UI will now display test plan names correctly")
    print("\nNext steps:")
    print("- Refresh the Test Execution page")
    print("- Create a new test plan and execute it")
    print("- Check that the Test Plan Name column shows the correct name")
    
    return True

if __name__ == "__main__":
    try:
        debug_execution_data()
    except Exception as e:
        print(f"\n❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()