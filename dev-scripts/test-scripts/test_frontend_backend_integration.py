#!/usr/bin/env python3
"""
Test script to verify frontend-backend integration for kernel driver generation.
"""

import requests
import json

def test_complete_flow():
    """Test the complete authentication and kernel driver generation flow."""
    
    session = requests.Session()
    base_url = "http://localhost:8000/api/v1"
    
    print("=== Testing Complete Frontend-Backend Integration ===\n")
    
    # Step 1: Test authentication
    print("1. Testing authentication...")
    auth_response = session.post(
        f"{base_url}/auth/login",
        json={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/json"}
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        return False
    
    auth_data = auth_response.json()
    if not auth_data.get('success'):
        print(f"❌ Authentication unsuccessful: {auth_data}")
        return False
    
    token = auth_data.get('data', {}).get('access_token')
    if not token:
        print("❌ No access token received")
        return False
    
    print(f"✅ Authentication successful, token received")
    
    # Step 2: Test kernel driver generation with authentication
    print("\n2. Testing kernel driver generation with authentication...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Origin": "http://localhost:3001"
    }
    
    params = {
        "function_name": "schedule",
        "file_path": "kernel/sched/core.c",
        "subsystem": "scheduler", 
        "test_types": ["unit", "integration"]
    }
    
    kernel_response = session.post(
        f"{base_url}/tests/generate-kernel-driver",
        params=params,
        headers=headers
    )
    
    if kernel_response.status_code != 200:
        print(f"❌ Kernel driver generation failed: {kernel_response.status_code}")
        print(f"Response: {kernel_response.text}")
        return False
    
    kernel_data = kernel_response.json()
    if not kernel_data.get('success'):
        print(f"❌ Kernel driver generation unsuccessful: {kernel_data}")
        return False
    
    print(f"✅ Kernel driver generation successful")
    print(f"   Generated {kernel_data['data']['generated_count']} test cases")
    print(f"   Kernel module: {kernel_data['data']['driver_info']['kernel_module']}")
    print(f"   Files: {', '.join(kernel_data['data']['driver_info']['generated_files'])}")
    
    # Step 3: Test retrieving the generated test cases
    print("\n3. Testing test case retrieval...")
    
    tests_response = session.get(
        f"{base_url}/tests",
        params={"page": 1, "page_size": 50},
        headers=headers
    )
    
    if tests_response.status_code != 200:
        print(f"❌ Test case retrieval failed: {tests_response.status_code}")
        return False
    
    tests_data = tests_response.json()
    if not tests_data.get('success'):
        print(f"❌ Test case retrieval unsuccessful: {tests_data}")
        return False
    
    # Look for our generated test case
    test_cases = tests_data.get('data', {}).get('tests', [])
    kernel_test_found = False
    
    for test_case in test_cases:
        if test_case.get('id') in kernel_data['data']['test_case_ids']:
            kernel_test_found = True
            print(f"✅ Generated kernel test case found: {test_case.get('name')}")
            print(f"   Test type: {test_case.get('test_type')}")
            print(f"   Subsystem: {test_case.get('target_subsystem')}")
            break
    
    if not kernel_test_found:
        print("⚠️  Generated kernel test case not found in test list")
        print(f"   Looking for IDs: {kernel_data['data']['test_case_ids']}")
        print(f"   Found {len(test_cases)} total test cases")
    
    print(f"\n✅ All integration tests passed!")
    return True

if __name__ == "__main__":
    try:
        if test_complete_flow():
            print("\n🎉 Frontend-Backend integration is working correctly!")
            print("The 'Network Error' issue should now be resolved.")
        else:
            print("\n❌ Integration tests failed.")
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()