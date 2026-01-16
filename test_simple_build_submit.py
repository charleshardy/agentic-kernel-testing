#!/usr/bin/env python3
"""
Simple test to submit a build job without advanced config
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1/infrastructure"

# Test 1: Submit without build_config
print("Test 1: Submit without build_config")
payload1 = {
    "source_repository": "https://github.com/torvalds/linux.git",
    "branch": "master",
    "target_architecture": "x86_64"
}

try:
    response = requests.post(f"{API_BASE}/build-jobs", json=payload1)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ SUCCESS: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ FAILED: {response.text}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "="*60 + "\n")

# Test 2: Submit with empty build_config
print("Test 2: Submit with empty build_config")
payload2 = {
    "source_repository": "https://github.com/torvalds/linux.git",
    "branch": "master",
    "target_architecture": "x86_64",
    "build_config": {}
}

try:
    response = requests.post(f"{API_BASE}/build-jobs", json=payload2)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ SUCCESS: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ FAILED: {response.text}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "="*60 + "\n")

# Test 3: Submit with one build_config field
print("Test 3: Submit with one build_config field")
payload3 = {
    "source_repository": "https://github.com/torvalds/linux.git",
    "branch": "master",
    "target_architecture": "x86_64",
    "build_config": {
        "workspace_root": "/tmp/test-builds"
    }
}

try:
    response = requests.post(f"{API_BASE}/build-jobs", json=payload3)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ SUCCESS: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ FAILED: {response.text}")
except Exception as e:
    print(f"❌ ERROR: {e}")
