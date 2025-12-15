#!/usr/bin/env python3
"""Direct API test to bypass CLI issues."""

import requests
import json

# Test the API directly
base_url = "http://localhost:8000"

print("🔍 Testing API directly...")

# 1. Test health endpoint (no auth required)
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{base_url}/api/v1/health")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check successful")
        print(f"   Active tests: {data['data']['components']['test_orchestrator']['active_tests']}")
    else:
        print(f"❌ Health check failed: {response.text}")
except Exception as e:
    print(f"❌ Health check error: {e}")

# 2. Test login
print("\n2. Testing login...")
try:
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data['data']['access_token']
        print(f"✅ Login successful")
        print(f"   Token: {token[:50]}...")
        
        # 3. Test authenticated endpoint
        print("\n3. Testing authenticated endpoint...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Authentication working")
        else:
            print(f"❌ Auth test failed: {response.text}")
            
        # 4. Test submitting a test
        print("\n4. Testing test submission...")
        test_data = {
            "test_cases": [{
                "name": "Direct API Test",
                "description": "Test submitted directly via API",
                "test_type": "unit",
                "target_subsystem": "kernel",
                "test_script": "echo 'Direct test'; sleep 10; echo 'Done'",
                "execution_time_estimate": 15,
                "code_paths": [],
                "metadata": {"source": "direct_api"}
            }],
            "priority": 5
        }
        
        response = requests.post(f"{base_url}/api/v1/tests/submit", json=test_data, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test submission successful")
            print(f"   Submission ID: {data['data']['submission_id']}")
            print(f"   Test ID: {data['data']['test_case_ids'][0]}")
        else:
            print(f"❌ Test submission failed: {response.text}")
            
        # 5. Test listing tests
        print("\n5. Testing test listing...")
        response = requests.get(f"{base_url}/api/v1/tests", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            tests = data['data']['tests']
            print(f"✅ Test listing successful")
            print(f"   Found {len(tests)} tests")
            for test in tests[:3]:  # Show first 3
                print(f"   - {test['name']} ({test['test_type']})")
        else:
            print(f"❌ Test listing failed: {response.text}")
            
    else:
        print(f"❌ Login failed: {response.text}")
except Exception as e:
    print(f"❌ Login error: {e}")

print("\n🎯 Summary:")
print("If all tests pass, the API is working and the issue is with the CLI client.")
print("If tests fail, there are server-side issues that need to be fixed.")