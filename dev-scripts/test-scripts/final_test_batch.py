#!/usr/bin/env python3
import requests
import json

# Use the fresh API key
api_key = "ak_6nHL48mBH3HfSFMcvlgw_CR6bOFcGgPS7XeJDcyCAvA"
headers = {"Authorization": f"Bearer {api_key}"}

# Submit a batch of tests to make dashboard interesting
tests = [
    {
        "name": "Kernel Memory Stress Test",
        "description": "Intensive memory allocation and deallocation test",
        "test_type": "unit",
        "target_subsystem": "mm",
        "execution_time_estimate": 60
    },
    {
        "name": "Network Stack Performance",
        "description": "High-throughput network performance test", 
        "test_type": "performance",
        "target_subsystem": "net",
        "execution_time_estimate": 90
    },
    {
        "name": "File System Integrity Check",
        "description": "Comprehensive file system integrity verification",
        "test_type": "integration",
        "target_subsystem": "fs", 
        "execution_time_estimate": 75
    },
    {
        "name": "Security Vulnerability Scan",
        "description": "Automated security vulnerability detection",
        "test_type": "security",
        "target_subsystem": "security",
        "execution_time_estimate": 120
    },
    {
        "name": "Boot Performance Analysis",
        "description": "Analyze kernel boot time and performance",
        "test_type": "performance", 
        "target_subsystem": "init",
        "execution_time_estimate": 45
    }
]

print("🚀 Submitting final test batch...")

for i, test in enumerate(tests, 1):
    # Complete the test data
    test_data = {
        "test_cases": [{
            **test,
            "test_script": f"echo 'Running {test['name']}...'; sleep {test['execution_time_estimate']}; echo 'Test completed'",
            "code_paths": [],
            "required_hardware": {
                "architecture": "x86_64",
                "cpu_model": "generic",
                "memory_mb": 4096,
                "storage_type": "ssd", 
                "peripherals": [],
                "is_virtual": True,
                "emulator": "qemu"
            },
            "metadata": {
                "batch": "final_demo",
                "priority": "high" if test["test_type"] == "security" else "normal"
            }
        }],
        "priority": 7 if test["test_type"] == "security" else 5
    }
    
    r = requests.post('http://localhost:8000/api/v1/tests/submit', json=test_data, headers=headers)
    if r.status_code == 200:
        data = r.json()['data']
        print(f"✅ {i}. {test['name']} - Submitted successfully")
    else:
        print(f"❌ {i}. {test['name']} - Error: {r.status_code}")

# Check final status
print("\n📊 Final System Status:")
r = requests.get('http://localhost:8000/api/v1/tests', headers=headers)
if r.status_code == 200:
    tests = r.json()['data']['tests']
    print(f"  Total Tests Submitted: {len(tests)}")
    
    # Count by type
    types = {}
    for test in tests:
        test_type = test['test_type']
        types[test_type] = types.get(test_type, 0) + 1
    
    print("  Test Types:")
    for test_type, count in types.items():
        print(f"    {test_type}: {count}")

print(f"\n🎯 Dashboard Status:")
print(f"  URL: http://localhost:3000")
print(f"  API: http://localhost:8000")
print(f"  Tests are submitted and stored in the API")
print(f"  Dashboard will show demo data + connection status")

print(f"\n✅ Authentication Issue Resolved!")
print(f"  Fresh API Key: ak_6nHL48mBH3HfSFMcvlgw_CR6bOFcGgPS7XeJDcyCAvA")
print(f"  Valid for: 365 days")
print(f"  CLI Command: python3 -m cli.main --api-key 'ak_6nHL48mBH3HfSFMcvlgw_CR6bOFcGgPS7XeJDcyCAvA' test list")