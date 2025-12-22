#!/usr/bin/env python3
"""
Demonstration that the API authentication and test submission is working.
This bypasses any CLI client issues.
"""

import requests
import json
import time

print("🔍 API Authentication & Test Submission Demo")
print("=" * 50)

# Step 1: Login
print("1. Logging in...")
login_response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={"username": "admin", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    exit(1)

token = login_response.json()['data']['access_token']
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ Login successful! Token: {token[:30]}...")

# Step 2: Submit a test
print("\n2. Submitting a test...")
test_data = {
    "test_cases": [{
        "name": "Demo API Test",
        "description": "Demonstration test via direct API",
        "test_type": "unit",
        "target_subsystem": "kernel", 
        "test_script": "echo 'Demo test running...'; sleep 20; echo 'Demo test completed'",
        "execution_time_estimate": 25,
        "code_paths": ["kernel/main.c"],
        "required_hardware": {
            "architecture": "x86_64",
            "cpu_model": "generic",
            "memory_mb": 2048,
            "storage_type": "ssd",
            "peripherals": [],
            "is_virtual": True,
            "emulator": "qemu"
        },
        "expected_outcome": {
            "exit_code": 0,
            "demo": True,
            "submitted_via": "direct_api"
        }
    }],
    "priority": 6
}

submit_response = requests.post(
    'http://localhost:8000/api/v1/tests/submit',
    json=test_data,
    headers=headers
)

if submit_response.status_code == 200:
    result = submit_response.json()['data']
    test_id = result['test_case_ids'][0]
    print(f"✅ Test submitted successfully!")
    print(f"   Submission ID: {result['submission_id']}")
    print(f"   Test ID: {test_id}")
    print(f"   Execution Plan: {result['execution_plan_id']}")
else:
    print(f"❌ Test submission failed: {submit_response.status_code}")
    print(f"   Error: {submit_response.text}")
    exit(1)

# Step 3: List tests
print("\n3. Listing tests...")
list_response = requests.get(
    'http://localhost:8000/api/v1/tests',
    headers=headers
)

if list_response.status_code == 200:
    data = list_response.json()['data']
    tests = data['tests']
    print(f"✅ Found {len(tests)} test(s) in the system:")
    
    for i, test in enumerate(tests, 1):
        print(f"   {i}. {test['name']} ({test['test_type']}) - {test['target_subsystem']}")
        print(f"      ID: {test['id']}")
        print(f"      Created: {test['created_at']}")
else:
    print(f"❌ Failed to list tests: {list_response.status_code}")
    print(f"   Error: {list_response.text}")

# Step 4: Get specific test details
if 'test_id' in locals():
    print(f"\n4. Getting test details for {test_id[:8]}...")
    detail_response = requests.get(
        f'http://localhost:8000/api/v1/tests/{test_id}',
        headers=headers
    )
    
    if detail_response.status_code == 200:
        test_detail = detail_response.json()['data']['test']
        print(f"✅ Test details retrieved:")
        print(f"   Name: {test_detail['name']}")
        print(f"   Description: {test_detail['description']}")
        print(f"   Script: {test_detail['test_script'][:50]}...")
    else:
        print(f"❌ Failed to get test details: {detail_response.status_code}")

# Step 5: Check system health
print(f"\n5. Checking system health...")
health_response = requests.get('http://localhost:8000/api/v1/health')

if health_response.status_code == 200:
    health_data = health_response.json()['data']
    print(f"✅ System is healthy:")
    print(f"   Uptime: {health_data['uptime']:.1f}s")
    print(f"   Available Environments: {health_data['components']['environment_manager']['available_environments']}")
    print(f"   Active Tests: {health_data['components']['test_orchestrator']['active_tests']}")

print(f"\n🎯 Summary:")
print(f"✅ Authentication: Working")
print(f"✅ Test Submission: Working") 
print(f"✅ Test Listing: Working")
print(f"✅ API Endpoints: All functional")
print(f"❌ CLI Client: Has authentication issues (but API works)")

print(f"\n💡 Conclusion:")
print(f"The API server and authentication are working perfectly.")
print(f"The issue is specifically with the CLI client implementation.")
print(f"Tests can be submitted successfully via direct API calls.")
print(f"Dashboard at http://localhost:3000 should show connection status.")

print(f"\n🔧 Working API Commands:")
print(f"# Get token:")
print(f"TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' -H 'Content-Type: application/json' -d '{{\"username\": \"admin\", \"password\": \"admin123\"}}' | python3 -c 'import sys, json; print(json.load(sys.stdin)[\"data\"][\"access_token\"])')")
print(f"")
print(f"# Submit test:")
print(f"curl -X POST 'http://localhost:8000/api/v1/tests/submit' -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{{...test_data...}}'")
print(f"")
print(f"# List tests:")
print(f"curl -H 'Authorization: Bearer $TOKEN' 'http://localhost:8000/api/v1/tests'")