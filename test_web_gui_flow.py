#!/usr/bin/env python3
"""
Test script to simulate Web GUI flow
"""

import requests
import json
import time

base_url = "http://localhost:8000/api/v1"

print("=== Simulating Web GUI Flow ===\n")

# Step 1: Login (like Web GUI does)
print("1. Logging in with admin credentials...")
login_response = requests.post(
    f"{base_url}/auth/login",
    json={"username": "admin", "password": "admin123"}
)
if login_response.status_code == 200:
    token = login_response.json()['data']['access_token']
    print(f"   ✅ Login successful, got token: {token[:20]}...")
else:
    print(f"   ❌ Login failed: {login_response.status_code}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Step 2: Generate AI test (like Web GUI does)
print("\n2. Generating AI test...")
gen_response = requests.post(
    f"{base_url}/tests/generate-from-function",
    params={
        "function_name": "web_gui_simulation",
        "file_path": "test.c",
        "subsystem": "test",
        "max_tests": 1
    },
    headers=headers
)
if gen_response.status_code == 200:
    gen_data = gen_response.json()
    plan_id = gen_data['data']['execution_plan_id']
    test_ids = gen_data['data']['test_case_ids']
    print(f"   ✅ AI test generated")
    print(f"   - Plan ID: {plan_id}")
    print(f"   - Test IDs: {test_ids}")
else:
    print(f"   ❌ Generation failed: {gen_response.status_code}")
    print(f"   Response: {gen_response.text}")
    exit(1)

# Step 3: Check active executions (like Web GUI does)
print("\n3. Checking active executions...")
time.sleep(1)  # Give it a moment
exec_response = requests.get(
    f"{base_url}/execution/active",
    headers=headers
)
if exec_response.status_code == 200:
    exec_data = exec_response.json()
    executions = exec_data['data']['executions']
    print(f"   ✅ Got response")
    print(f"   - Found {len(executions)} active execution(s)")
    for ex in executions:
        print(f"   - Plan: {ex['plan_id']}")
        print(f"     Status: {ex['overall_status']}")
        print(f"     Tests: {ex['total_tests']}")
else:
    print(f"   ❌ Failed to get executions: {exec_response.status_code}")
    print(f"   Response: {exec_response.text}")
    exit(1)

# Step 4: Check if our plan is in the list
print("\n4. Verifying our plan is in active executions...")
found = False
for ex in executions:
    if ex['plan_id'] == plan_id:
        found = True
        print(f"   ✅ Found our plan in active executions!")
        print(f"   - Status: {ex['overall_status']}")
        print(f"   - Tests: {ex['total_tests']}")
        break

if not found:
    print(f"   ❌ Our plan {plan_id} is NOT in active executions!")
    print(f"   Available plans: {[ex['plan_id'] for ex in executions]}")
else:
    print("\n✅ Web GUI flow simulation successful!")
    print("The execution flow is working correctly.")
    print("\nIf the Web GUI is still not showing executions, the issue is likely:")
    print("1. Web GUI not polling the /execution/active endpoint")
    print("2. Web GUI authentication issue")
    print("3. Web GUI not refreshing the data")
    print("4. Browser console errors")
