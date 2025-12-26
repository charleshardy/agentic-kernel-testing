#!/usr/bin/env python3
"""Test the API response to see if test_plan_name is included."""

import sys
import os
import requests
import json

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_api_response():
    """Test the API response for test plan names."""
    
    print("🔍 Testing API Response for Test Plan Names")
    print("=" * 50)
    
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
    
    # Step 2: Get active executions and examine the response
    print("\n2. Getting active executions...")
    try:
        response = requests.get(f"{base_url}/execution/active", 
                              headers=headers, 
                              timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response Status: {response.status_code}")
            print(f"✅ Response Success: {data.get('success')}")
            print(f"✅ Response Message: {data.get('message')}")
            
            executions = data.get('data', {}).get('executions', [])
            print(f"✅ Found {len(executions)} executions")
            
            if executions:
                print("\n📋 Detailed Execution Data:")
                for i, execution in enumerate(executions):
                    print(f"\n   Execution {i+1}:")
                    print(f"   ├─ plan_id: {execution.get('plan_id', 'N/A')}")
                    print(f"   ├─ test_plan_name: {repr(execution.get('test_plan_name'))}")
                    print(f"   ├─ test_plan_id: {execution.get('test_plan_id', 'N/A')}")
                    print(f"   ├─ overall_status: {execution.get('overall_status', 'N/A')}")
                    print(f"   ├─ total_tests: {execution.get('total_tests', 'N/A')}")
                    print(f"   ├─ created_by: {execution.get('created_by', 'N/A')}")
                    print(f"   └─ started_at: {execution.get('started_at', 'N/A')}")
                    
                    # Check if this execution has test_plan_name
                    has_test_plan_name = 'test_plan_name' in execution
                    test_plan_name_value = execution.get('test_plan_name')
                    
                    if has_test_plan_name:
                        if test_plan_name_value:
                            print(f"      ✅ HAS test_plan_name: '{test_plan_name_value}'")
                        else:
                            print(f"      ⚠️ HAS test_plan_name field but value is: {repr(test_plan_name_value)}")
                    else:
                        print(f"      ❌ MISSING test_plan_name field")
            else:
                print("\n⚠️ No executions found")
                
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting active executions: {e}")
    
    # Step 3: Create a new test plan and execute it to test
    print("\n3. Creating a test plan to verify the fix...")
    try:
        test_plan_data = {
            "name": "🧪 API Test Plan",
            "description": "Test plan to verify API response includes test_plan_name",
            "test_ids": ["api_test_001", "api_test_002"],
            "tags": ["api-test"],
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
            
            # Execute it
            response = requests.post(f"{base_url}/test-plans/{plan_id}/execute", 
                                   headers=headers, 
                                   timeout=5)
            
            if response.status_code == 200:
                execution_data = response.json().get('data', {})
                execution_plan_id = execution_data.get('execution_plan_id')
                print(f"✅ Executed test plan, execution ID: {execution_plan_id}")
                
                # Wait and check if it appears with test_plan_name
                import time
                time.sleep(2)
                
                response = requests.get(f"{base_url}/execution/active", 
                                      headers=headers, 
                                      timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    executions = data.get('data', {}).get('executions', [])
                    
                    # Find our new execution
                    our_execution = None
                    for execution in executions:
                        if execution.get('plan_id') == execution_plan_id:
                            our_execution = execution
                            break
                    
                    if our_execution:
                        print(f"\n🎯 NEW EXECUTION FOUND:")
                        print(f"   plan_id: {our_execution.get('plan_id')}")
                        print(f"   test_plan_name: {repr(our_execution.get('test_plan_name'))}")
                        
                        if our_execution.get('test_plan_name') == plan_name:
                            print(f"   ✅ SUCCESS: test_plan_name matches!")
                        else:
                            print(f"   ❌ MISMATCH: Expected '{plan_name}', got {repr(our_execution.get('test_plan_name'))}")
                    else:
                        print(f"   ❌ New execution not found in active list")
                
                # Clean up
                requests.delete(f"{base_url}/test-plans/{plan_id}", headers=headers, timeout=5)
                print(f"✅ Cleaned up test plan")
            else:
                print(f"❌ Failed to execute test plan: {response.text}")
        else:
            print(f"❌ Failed to create test plan: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in test plan test: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 API Response Analysis Complete!")
    print("\nIf test_plan_name is missing from the API response:")
    print("1. The backend fix may not be working")
    print("2. The execution data structure needs updating")
    print("3. Check the server logs for errors")
    print("\nIf test_plan_name is present in API but not in UI:")
    print("1. Frontend component may not be updated")
    print("2. Check browser console for errors")
    print("3. Clear browser cache and refresh")
    
    return True

if __name__ == "__main__":
    try:
        test_api_response()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()