#!/usr/bin/env python3
import requests
import json
import time

# Login and get token
login_data = {"username": "admin", "password": "admin123"}
r = requests.post('http://localhost:8000/api/v1/auth/login', json=login_data)
token = r.json()['data']['access_token']
headers = {"Authorization": f"Bearer {token}"}

# Submit multiple tests
tests = [
    {
        "name": "Memory Allocation Test",
        "description": "Test kernel memory allocation under stress",
        "test_type": "unit",
        "target_subsystem": "mm",
        "test_script": "echo 'Testing memory allocation...'; sleep 45; echo 'Memory test completed'",
        "execution_time_estimate": 50
    },
    {
        "name": "Network Performance Test", 
        "description": "Test network throughput and latency",
        "test_type": "performance",
        "target_subsystem": "net",
        "test_script": "echo 'Testing network performance...'; sleep 60; echo 'Network test completed'",
        "execution_time_estimate": 65
    },
    {
        "name": "File System Integrity Test",
        "description": "Test file system operations and integrity",
        "test_type": "integration", 
        "target_subsystem": "fs",
        "test_script": "echo 'Testing file system...'; sleep 40; echo 'FS test completed'",
        "execution_time_estimate": 45
    },
    {
        "name": "Security Fuzzing Test",
        "description": "Fuzz test system call interfaces",
        "test_type": "fuzz",
        "target_subsystem": "syscall",
        "test_script": "echo 'Running security fuzzing...'; sleep 90; echo 'Fuzzing completed'",
        "execution_time_estimate": 95
    },
    {
        "name": "Boot Sequence Test",
        "description": "Test kernel boot and initialization",
        "test_type": "integration",
        "target_subsystem": "init", 
        "test_script": "echo 'Testing boot sequence...'; sleep 35; echo 'Boot test completed'",
        "execution_time_estimate": 40
    }
]

print(f"Submitting {len(tests)} tests...")

for i, test in enumerate(tests, 1):
    # Add required hardware config
    test["code_paths"] = []
    test["required_hardware"] = {
        "architecture": "x86_64",
        "cpu_model": "generic", 
        "memory_mb": 2048,
        "storage_type": "ssd",
        "peripherals": [],
        "is_virtual": True,
        "emulator": "qemu"
    }
    test["metadata"] = {"batch": "demo_tests", "order": i}
    
    test_data = {
        "test_cases": [test],
        "priority": 5 + (i % 3)  # Vary priority 5-7
    }
    
    r = requests.post('http://localhost:8000/api/v1/tests/submit', json=test_data, headers=headers)
    if r.status_code == 200:
        data = r.json()['data']
        print(f"✅ {i}. {test['name']} - ID: {data['test_case_ids'][0][:8]}")
    else:
        print(f"❌ {i}. {test['name']} - Error: {r.status_code}")
    
    time.sleep(0.5)  # Small delay between submissions

# Check final count
r = requests.get('http://localhost:8000/api/v1/tests', headers=headers)
if r.status_code == 200:
    tests = r.json()['data']['tests']
    print(f"\n🎯 Total tests in system: {len(tests)}")
    print("\nRecent tests:")
    for test in tests[-3:]:  # Show last 3
        print(f"  - {test['name']} ({test['test_type']})")
else:
    print(f"Error checking tests: {r.status_code}")

print(f"\n🚀 Check the dashboard at http://localhost:3000 to see the tests!")
print(f"📊 The dashboard should now show real test data instead of 0s.")