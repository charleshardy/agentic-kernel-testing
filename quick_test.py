#!/usr/bin/env python3
import requests
import json

print("Testing API...")

# 1. Health check
r = requests.get('http://localhost:8000/api/v1/health')
print(f"Health: {r.status_code}")

# 2. Login
login_data = {"username": "admin", "password": "admin123"}
r = requests.post('http://localhost:8000/api/v1/auth/login', json=login_data)
print(f"Login: {r.status_code}")

if r.status_code == 200:
    token = r.json()['data']['access_token']
    print(f"Got token: {token[:20]}...")
    
    # 3. Submit test
    headers = {"Authorization": f"Bearer {token}"}
    test_data = {
        "test_cases": [{
            "name": "Quick API Test",
            "description": "Test via direct API",
            "test_type": "unit", 
            "target_subsystem": "kernel",
            "test_script": "echo 'API test running'; sleep 20; echo 'Done'",
            "execution_time_estimate": 25,
            "code_paths": [],
            "required_hardware": {
                "architecture": "x86_64",
                "cpu_model": "generic",
                "memory_mb": 2048,
                "storage_type": "ssd",
                "peripherals": [],
                "is_virtual": True,
                "emulator": "qemu"
            },
            "metadata": {}
        }],
        "priority": 5
    }
    
    r = requests.post('http://localhost:8000/api/v1/tests/submit', json=test_data, headers=headers)
    print(f"Submit: {r.status_code}")
    if r.status_code == 200:
        data = r.json()['data']
        print(f"Success! Test ID: {data['test_case_ids'][0]}")
    else:
        print(f"Error: {r.text}")
        
    # 4. List tests
    r = requests.get('http://localhost:8000/api/v1/tests', headers=headers)
    print(f"List: {r.status_code}")
    if r.status_code == 200:
        tests = r.json()['data']['tests']
        print(f"Found {len(tests)} tests")
    else:
        print(f"List error: {r.text}")
else:
    print(f"Login failed: {r.text}")