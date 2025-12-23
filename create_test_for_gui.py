#!/usr/bin/env python3
"""
Create a test specifically for the Web GUI to see
"""

import requests
import json
import time

def create_test_for_gui():
    base_url = "http://localhost:8000/api/v1"
    
    print("🎯 Creating test for Web GUI verification...")
    
    # Login
    print("1. Logging in...")
    login_response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login successful")
    
    # Generate AI test
    print("2. Generating AI test for Web GUI...")
    gen_response = requests.post(
        f"{base_url}/tests/generate-from-function",
        params={
            "function_name": "web_gui_verification_test",
            "file_path": "gui_test.c",
            "subsystem": "web_gui_test",
            "max_tests": 1
        },
        headers=headers
    )
    
    if gen_response.status_code != 200:
        print(f"❌ Generation failed: {gen_response.status_code}")
        return False
    
    gen_data = gen_response.json()
    plan_id = gen_data['data']['execution_plan_id']
    test_ids = gen_data['data']['test_case_ids']
    
    print(f"✅ AI test generated successfully!")
    print(f"   Plan ID: {plan_id}")
    print(f"   Test IDs: {test_ids}")
    
    # Verify it appears in active executions
    print("3. Verifying test appears in active executions...")
    time.sleep(1)  # Give it a moment
    
    exec_response = requests.get(f"{base_url}/execution/active", headers=headers)
    if exec_response.status_code != 200:
        print(f"❌ Failed to get executions: {exec_response.status_code}")
        return False
    
    exec_data = exec_response.json()
    executions = exec_data['data']['executions']
    
    print(f"✅ Found {len(executions)} active execution(s)")
    
    # Check if our plan is there
    found = False
    for ex in executions:
        if ex['plan_id'] == plan_id:
            found = True
            print(f"✅ Our test is in active executions!")
            print(f"   Status: {ex['overall_status']}")
            print(f"   Tests: {ex['total_tests']}")
            break
    
    if not found:
        print(f"❌ Our test {plan_id} is NOT in active executions!")
        print("Available executions:")
        for ex in executions:
            print(f"   - {ex['plan_id']}: {ex['overall_status']}")
        return False
    
    print("\n🎉 SUCCESS! Test created and verified in API.")
    print("\n📋 Next steps:")
    print("1. Open Web GUI: http://localhost:3000")
    print("2. Go to Test Execution page")
    print("3. Look for the 'Direct API Test' section")
    print("4. Click 'Run Complete Test' to test from browser")
    print("5. Check if the execution appears in the table below")
    print(f"\n🔍 Look for Plan ID: {plan_id}")
    
    return True

if __name__ == "__main__":
    create_test_for_gui()