#!/usr/bin/env python3
"""
Simple test to verify the function generation endpoint is working.
"""

import requests
import json

def test_function_generation():
    """Test the function generation endpoint directly."""
    
    # First, get an auth token
    print("🔑 Getting auth token...")
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return False
    
    token = login_response.json()["data"]["access_token"]
    print(f"✅ Got token: {token[:20]}...")
    
    # Test the function generation endpoint
    print("\n🧪 Testing function generation endpoint...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "function_name": "test_function",
        "file_path": "kernel/test.c",
        "subsystem": "kernel/core",
        "max_tests": 3
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/tests/generate-from-function",
        headers=headers,
        params=params
    )
    
    print(f"📡 Response status: {response.status_code}")
    print(f"📡 Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Function generation successful!")
        print(f"📊 Generated {data['data']['generated_count']} test cases")
        print(f"🆔 Test IDs: {data['data']['test_case_ids']}")
        return True
    else:
        print(f"❌ Function generation failed: {response.status_code}")
        print(f"📄 Response: {response.text}")
        return False

def test_without_auth():
    """Test without authentication to see what happens."""
    print("\n🧪 Testing without authentication...")
    
    params = {
        "function_name": "test_function",
        "file_path": "kernel/test.c", 
        "subsystem": "kernel/core",
        "max_tests": 3
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/tests/generate-from-function",
        params=params
    )
    
    print(f"📡 No-auth response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"📄 No-auth response: {response.text}")
    else:
        data = response.json()
        print("✅ No-auth worked!")
        print(f"📊 Generated {data['data']['generated_count']} test cases")

if __name__ == "__main__":
    print("=== Function Generation API Test ===")
    
    # Test with auth
    success = test_function_generation()
    
    # Test without auth
    test_without_auth()
    
    if success:
        print("\n✅ All tests passed! The API endpoint is working correctly.")
    else:
        print("\n❌ Tests failed! There may be an issue with the API endpoint.")