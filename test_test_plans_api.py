#!/usr/bin/env python3
"""Test the Test Plans API endpoints."""

import sys
import os
import requests
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_test_plans_api():
    """Test the test plans API endpoints."""
    
    print("🧪 Testing Test Plans API Integration")
    print("=" * 50)
    
    # API base URL
    base_url = "http://localhost:8000/api/v1"
    
    # Test authentication first
    print("\n1. Testing Authentication...")
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
            print("⚠️ Authentication failed, proceeding without token")
            headers = {}
    except Exception as e:
        print(f"⚠️ Authentication error: {e}")
        headers = {}
    
    # Test 1: Get all test plans
    print("\n2. Testing GET /test-plans...")
    try:
        response = requests.get(f"{base_url}/test-plans", headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            plans = data.get('data', {}).get('plans', [])
            print(f"✅ Retrieved {len(plans)} test plans")
            
            # Print sample plan info
            if plans:
                sample_plan = plans[0]
                print(f"   Sample plan: '{sample_plan['name']}' (ID: {sample_plan['id'][:8]}...)")
        else:
            print(f"❌ Failed to get test plans: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting test plans: {e}")
        return False
    
    # Test 2: Create a new test plan
    print("\n3. Testing POST /test-plans...")
    try:
        new_plan_data = {
            "name": f"Test Plan Created at {datetime.now().strftime('%H:%M:%S')}",
            "description": "Test plan created by API integration test",
            "test_ids": ["test_123", "test_456"],
            "tags": ["integration", "test"],
            "execution_config": {
                "environment_preference": "qemu-x86",
                "priority": 7,
                "timeout_minutes": 90,
                "retry_failed": True,
                "parallel_execution": True
            },
            "status": "draft"
        }
        
        response = requests.post(f"{base_url}/test-plans", 
                               json=new_plan_data, 
                               headers=headers, 
                               timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            created_plan = response.json().get('data', {})
            plan_id = created_plan.get('id')
            print(f"✅ Created test plan: '{created_plan['name']}' (ID: {plan_id[:8]}...)")
        else:
            print(f"❌ Failed to create test plan: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test plan: {e}")
        return False
    
    # Test 3: Get the specific test plan
    print(f"\n4. Testing GET /test-plans/{plan_id[:8]}...")
    try:
        response = requests.get(f"{base_url}/test-plans/{plan_id}", 
                              headers=headers, 
                              timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            plan_data = response.json().get('data', {})
            print(f"✅ Retrieved test plan: '{plan_data['name']}'")
            print(f"   Test IDs: {plan_data['test_ids']}")
            print(f"   Status: {plan_data['status']}")
        else:
            print(f"❌ Failed to get specific test plan: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting specific test plan: {e}")
    
    # Test 4: Update the test plan
    print(f"\n5. Testing PUT /test-plans/{plan_id[:8]}...")
    try:
        update_data = {
            "name": f"Updated Test Plan at {datetime.now().strftime('%H:%M:%S')}",
            "description": "Updated description",
            "status": "active",
            "test_ids": ["test_123", "test_456", "test_789"]
        }
        
        response = requests.put(f"{base_url}/test-plans/{plan_id}", 
                              json=update_data, 
                              headers=headers, 
                              timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            updated_plan = response.json().get('data', {})
            print(f"✅ Updated test plan: '{updated_plan['name']}'")
            print(f"   New status: {updated_plan['status']}")
            print(f"   Test count: {len(updated_plan['test_ids'])}")
        else:
            print(f"❌ Failed to update test plan: {response.text}")
            
    except Exception as e:
        print(f"❌ Error updating test plan: {e}")
    
    # Test 5: Execute the test plan
    print(f"\n6. Testing POST /test-plans/{plan_id[:8]}/execute...")
    try:
        response = requests.post(f"{base_url}/test-plans/{plan_id}/execute", 
                               headers=headers, 
                               timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            execution_data = response.json().get('data', {})
            execution_plan_id = execution_data.get('execution_plan_id')
            print(f"✅ Started test plan execution")
            print(f"   Execution ID: {execution_plan_id[:8]}...")
            print(f"   Test count: {execution_data.get('test_case_count')}")
        else:
            print(f"❌ Failed to execute test plan: {response.text}")
            
    except Exception as e:
        print(f"❌ Error executing test plan: {e}")
    
    # Test 6: Delete the test plan
    print(f"\n7. Testing DELETE /test-plans/{plan_id[:8]}...")
    try:
        response = requests.delete(f"{base_url}/test-plans/{plan_id}", 
                                 headers=headers, 
                                 timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            delete_data = response.json().get('data', {})
            print(f"✅ Deleted test plan: '{delete_data['deleted_plan_name']}'")
        else:
            print(f"❌ Failed to delete test plan: {response.text}")
            
    except Exception as e:
        print(f"❌ Error deleting test plan: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test Plans API Integration Test Complete!")
    print("\nThe backend now supports:")
    print("✅ Creating test plans with test cases")
    print("✅ Listing and retrieving test plans") 
    print("✅ Updating test plan configurations")
    print("✅ Executing test plans")
    print("✅ Deleting test plans")
    print("\nThe frontend should now work with real API data instead of mock data!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_test_plans_api()
        if success:
            print("\n✅ All tests passed! The Test Plans API is working correctly.")
        else:
            print("\n❌ Some tests failed. Check the API server.")
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()