#!/usr/bin/env python3
"""Test script to verify kernel generation fix."""

import requests
import json
import time

def test_kernel_generation():
    """Test the kernel driver generation endpoint."""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/tests/generate-kernel-driver"
    
    # Test parameters
    params = {
        "function_name": "kmalloc",
        "file_path": "mm/slab.c", 
        "subsystem": "kernel/mm",
        "test_types": ["unit", "integration"]
    }
    
    print("Testing kernel driver generation...")
    print(f"URL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(url, params=params, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Data:")
            print(json.dumps(data, indent=2))
            
            if data.get('success'):
                print("\n✅ SUCCESS: Kernel driver generation worked!")
                print(f"Generated {data['data']['generated_count']} test cases")
                print(f"Test case IDs: {data['data']['test_case_ids']}")
                return True
            else:
                print(f"\n❌ API ERROR: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ HTTP ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON ERROR: {e}")
        print(f"Response text: {response.text}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

def test_frontend_connection():
    """Test if frontend can connect to backend."""
    
    print("\nTesting frontend connection...")
    
    try:
        # Test basic API health
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is accessible")
        else:
            print(f"❌ Backend API returned {response.status_code}")
            
        # Test frontend
        response = requests.get("http://localhost:3001", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
        else:
            print(f"❌ Frontend returned {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Kernel Generation Fix")
    print("=" * 50)
    
    # Test backend API
    success = test_kernel_generation()
    
    # Test connections
    test_frontend_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The fix should work.")
        print("\nNext steps:")
        print("1. Open http://localhost:3001 in your browser")
        print("2. Go to Test Cases page")
        print("3. Click 'AI Generate Tests' -> 'Kernel Test Driver'")
        print("4. Fill in the form and click 'Generate Kernel Driver'")
        print("5. Check browser console for detailed error logs if issues persist")
    else:
        print("❌ Tests failed. Check the backend API.")