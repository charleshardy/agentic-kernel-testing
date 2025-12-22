#!/usr/bin/env python3
"""
Test the API endpoints to see what's happening with execution flow
"""

import requests
import json

def test_api_endpoints():
    """Test the API endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("=== Testing API Endpoints ===")
    print()
    
    # Get demo token
    print("1. Getting Demo Token...")
    try:
        response = requests.post(f"{base_url}/api/v1/auth/demo-login")
        if response.status_code == 200:
            token_data = response.json()
            token = token_data['data']['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            print(f"   ✅ Got demo token")
        else:
            print(f"   ❌ Failed to get demo token: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        return False
    
    print()
    
    # Test execution endpoints
    endpoints_to_test = [
        ("/api/v1/execution/active", "GET", "Active Executions"),
        ("/api/v1/execution/metrics", "GET", "Execution Metrics"),
        ("/api/v1/tests", "GET", "Test Cases"),
        ("/api/v1/health", "GET", "Health Check")
    ]
    
    for endpoint, method, name in endpoints_to_test:
        print(f"Testing {name} ({method} {endpoint})...")
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", headers=headers)
            else:
                response = requests.post(f"{base_url}{endpoint}", headers=headers)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    if isinstance(data['data'], list):
                        print(f"   Data: {len(data['data'])} items")
                        if data['data']:
                            print(f"   Sample: {list(data['data'][0].keys()) if isinstance(data['data'][0], dict) else data['data'][0]}")
                    elif isinstance(data['data'], dict):
                        print(f"   Data keys: {list(data['data'].keys())}")
                    else:
                        print(f"   Data: {data['data']}")
                else:
                    print(f"   Response: {data}")
            else:
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Test creating an AI test and see if it appears
    print("Creating AI Test...")
    try:
        test_data = {
            "function_name": "test_api_function",
            "file_path": "test/api_test.c",
            "subsystem": "test",
            "max_tests": 1
        }
        
        response = requests.post(
            f"{base_url}/api/v1/tests/generate-from-function",
            params=test_data,
            headers=headers
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Generated test IDs: {result['data']['test_case_ids']}")
            print(f"   Execution plan ID: {result['data']['execution_plan_id']}")
            
            # Now check if it appears in active executions
            print("\nChecking if test appears in active executions...")
            response = requests.get(f"{base_url}/api/v1/execution/active", headers=headers)
            if response.status_code == 200:
                executions = response.json()
                print(f"   Active executions: {len(executions['data'])}")
                for execution in executions['data']:
                    print(f"     - Plan {execution['plan_id']}: {execution['overall_status']}")
            else:
                print(f"   ❌ Failed to get active executions: {response.status_code}")
                
        else:
            print(f"   ❌ Failed to generate test: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error creating test: {e}")
    
    print()
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_api_endpoints()