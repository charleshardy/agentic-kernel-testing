#!/usr/bin/env python3
"""Debug the Test Plan Name column issue step by step."""

import sys
import os
import requests
import json
import time

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def debug_test_plan_column():
    """Debug why the Test Plan Name column is not showing up."""
    
    print("🔍 Debugging Test Plan Name Column Issue")
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
    
    # Step 2: Clean up old executions first
    print("\n2. Cleaning up old executions...")
    try:
        response = requests.post(f"{base_url}/execution/cleanup-debug", 
                               headers=headers, 
                               timeout=5)
        
        if response.status_code == 200:
            cleanup_data = response.json().get('data', {})
            removed_count = cleanup_data.get('removed_count', 0)
            print(f"✅ Cleaned up {removed_count} old executions")
        else:
            print(f"⚠️ Cleanup failed: {response.text}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")
    
    # Step 3: Check current active executions
    print("\n3. Checking current active executions...")
    try:
        response = requests.get(f"{base_url}/execution/active", 
                              headers=headers, 
                              timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            executions = data.get('data', {}).get('executions', [])
            print(f"✅ Current active executions: {len(executions)}")
            
            if executions:
                print("\n   Current executions:")
                for i, execution in enumerate(executions):
                    test_plan_name = execution.get('test_plan_name')
                    print(f"   {i+1}. {execution.get('plan_id', 'N/A')[:12]}... - '{test_plan_name}' ({execution.get('overall_status', 'N/A')})")
            else:
                print("   No active executions found")
        else:
            print(f"❌ Failed to get executions: {response.text}")
    except Exception as e:
        print(f"❌ Error getting executions: {e}")
    
    # Step 4: Create a new test plan with a very distinctive name
    print("\n4. Creating a new test plan with distinctive name...")
    try:
        distinctive_name = f"🚀 DEBUG TEST PLAN {int(time.time())}"
        test_plan_data = {
            "name": distinctive_name,
            "description": "Test plan specifically for debugging the Test Plan Name column",
            "test_ids": ["debug_001", "debug_002", "debug_003"],
            "tags": ["debug", "column-test"],
            "execution_config": {
                "environment_preference": "qemu-x86",
                "priority": 7,
                "timeout_minutes": 30,
                "retry_failed": False,
                "parallel_execution": True
            },
            "status": "active"
        }
        
        response = requests.post(f"{base_url}/test-plans", 
                               json=test_plan_data, 
                               headers=headers, 
                               timeout=5)
        
        if response.status_code == 200:
            test_plan = response.json().get('data', {})
            plan_id = test_plan.get('id')
            plan_name = test_plan.get('name')
            print(f"✅ Created test plan:")
            print(f"   Name: '{plan_name}'")
            print(f"   ID: {plan_id}")
            
            # Step 5: Execute the test plan
            print(f"\n5. Executing test plan...")
            response = requests.post(f"{base_url}/test-plans/{plan_id}/execute", 
                                   headers=headers, 
                                   timeout=5)
            
            if response.status_code == 200:
                execution_data = response.json().get('data', {})
                execution_plan_id = execution_data.get('execution_plan_id')
                print(f"✅ Execution started:")
                print(f"   Execution ID: {execution_plan_id}")
                print(f"   Test Count: {execution_data.get('test_case_count')}")
                
                # Step 6: Wait and check if it appears in active executions
                print(f"\n6. Waiting 3 seconds then checking active executions...")
                time.sleep(3)
                
                response = requests.get(f"{base_url}/execution/active", 
                                      headers=headers, 
                                      timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    executions = data.get('data', {}).get('executions', [])
                    print(f"✅ Found {len(executions)} active executions after creation")
                    
                    # Look for our execution
                    our_execution = None
                    for execution in executions:
                        if execution.get('plan_id') == execution_plan_id:
                            our_execution = execution
                            break
                    
                    if our_execution:
                        print(f"\n🎯 FOUND OUR EXECUTION:")
                        print(f"   Execution ID: {our_execution.get('plan_id')}")
                        print(f"   Test Plan Name: '{our_execution.get('test_plan_name')}'")
                        print(f"   Test Plan ID: {our_execution.get('test_plan_id')}")
                        print(f"   Status: {our_execution.get('overall_status')}")
                        print(f"   Created By: {our_execution.get('created_by')}")
                        print(f"   Total Tests: {our_execution.get('total_tests')}")
                        
                        # Check if test_plan_name field exists and matches
                        has_field = 'test_plan_name' in our_execution
                        field_value = our_execution.get('test_plan_name')
                        
                        print(f"\n📋 FIELD ANALYSIS:")
                        print(f"   Has 'test_plan_name' field: {has_field}")
                        print(f"   Field value: {repr(field_value)}")
                        print(f"   Expected value: '{distinctive_name}'")
                        print(f"   Values match: {field_value == distinctive_name}")
                        
                        if has_field and field_value == distinctive_name:
                            print(f"\n🎉 SUCCESS! The API is returning the correct test plan name!")
                            print(f"\n📱 FRONTEND DEBUGGING:")
                            print(f"   1. Open browser Developer Tools (F12)")
                            print(f"   2. Go to Console tab")
                            print(f"   3. Refresh the Test Execution page")
                            print(f"   4. Look for these console messages:")
                            print(f"      - '🔍 Fetching active executions...'")
                            print(f"      - '📊 Active executions result: ...'")
                            print(f"      - 'Execution 1: {{plan_id: ..., test_plan_name: \"{distinctive_name}\", ...}}'")
                            print(f"      - 'Rendering test plan name: {distinctive_name} for record: ...'")
                            print(f"\n   5. If you see the console logs but not the column:")
                            print(f"      - Clear browser cache (Ctrl+Shift+Delete)")
                            print(f"      - Hard refresh (Ctrl+Shift+R)")
                            print(f"      - Check if there are any JavaScript errors")
                            print(f"\n   6. The Test Plan Name column should show: '{distinctive_name}'")
                        else:
                            print(f"\n❌ BACKEND ISSUE: Test plan name not properly set")
                            if not has_field:
                                print(f"   - The 'test_plan_name' field is missing from the API response")
                            elif field_value != distinctive_name:
                                print(f"   - The field value doesn't match the expected test plan name")
                    else:
                        print(f"\n❌ EXECUTION NOT FOUND in active list")
                        print(f"   Looking for execution ID: {execution_plan_id}")
                        print(f"   Available executions:")
                        for i, execution in enumerate(executions):
                            print(f"   {i+1}. {execution.get('plan_id')} - '{execution.get('test_plan_name', 'No name')}'")
                else:
                    print(f"❌ Failed to get active executions: {response.text}")
                
                # Don't clean up immediately so you can test in the UI
                print(f"\n7. Test plan left active for UI testing")
                print(f"   You can now go to the Test Execution page and see if the column appears")
                print(f"   Look for execution: {execution_plan_id[:12]}...")
                print(f"   Expected Test Plan Name: '{distinctive_name}'")
                print(f"\n   To clean up later, delete the test plan from the Test Plans page")
                
            else:
                print(f"❌ Failed to execute test plan: {response.text}")
        else:
            print(f"❌ Failed to create test plan: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in test plan creation/execution: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 Debug Summary:")
    print("\nIf the API shows the correct test_plan_name but UI doesn't:")
    print("1. Check browser console for JavaScript errors")
    print("2. Clear browser cache and hard refresh")
    print("3. Verify the RealTimeExecutionMonitor component is updated")
    print("4. Check if there are any React rendering errors")
    print("\nIf the API doesn't show test_plan_name:")
    print("1. Check server logs for backend errors")
    print("2. Verify the execution.py changes were applied")
    print("3. Restart the API server")
    
    return True

if __name__ == "__main__":
    try:
        debug_test_plan_column()
    except Exception as e:
        print(f"\n❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()