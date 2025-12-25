#!/usr/bin/env python3
"""Verify that the AI generation fix is working."""

import requests
import json
import time

def test_api_endpoint():
    """Test the API endpoint directly."""
    print("🧪 Testing API endpoint...")
    
    url = "http://localhost:8000/api/v1/tests/generate-kernel-driver"
    params = {
        "function_name": "kmalloc",
        "file_path": "mm/slab.c",
        "subsystem": "kernel/mm",
        "test_types": ["unit", "integration"]
    }
    
    try:
        response = requests.post(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API endpoint working correctly")
                print(f"   Generated {data['data']['generated_count']} test cases")
                return True
            else:
                print(f"❌ API returned error: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def check_services():
    """Check if required services are running."""
    print("🔍 Checking services...")
    
    # Check backend
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running")
        else:
            print(f"⚠️ Backend API returned {response.status_code}")
    except:
        print("❌ Backend API is not accessible")
        return False
    
    # Check frontend
    try:
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running")
        else:
            print(f"⚠️ Frontend returned {response.status_code}")
    except:
        print("❌ Frontend is not accessible")
        return False
    
    return True

def main():
    print("🔧 Verifying AI Generation Fix")
    print("=" * 40)
    
    if not check_services():
        print("\n❌ Services not running properly")
        return False
    
    if test_api_endpoint():
        print("\n🎉 Fix verification successful!")
        print("\nThe backend API is working correctly.")
        print("The 'Generation failed: undefined' error should now be fixed.")
        print("\nTo test in the browser:")
        print("1. Open http://localhost:3001")
        print("2. Go to Test Cases page")
        print("3. Click 'AI Generate Tests' -> 'Kernel Test Driver'")
        print("4. Fill in the form and submit")
        print("5. You should now see proper error messages instead of 'undefined'")
        return True
    else:
        print("\n❌ Fix verification failed")
        print("There may still be issues with the API")
        return False

if __name__ == "__main__":
    main()