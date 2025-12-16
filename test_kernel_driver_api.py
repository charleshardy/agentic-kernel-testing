#!/usr/bin/env python3
"""
Test script to verify the kernel driver generation API endpoint is working.
"""

import requests
import json

def test_kernel_driver_generation():
    """Test the kernel driver generation endpoint."""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/tests/generate-kernel-driver"
    
    # Test parameters
    params = {
        "function_name": "kmalloc",
        "file_path": "mm/slab.c", 
        "subsystem": "mm",
        "test_types": ["unit", "integration"]
    }
    
    print("Testing kernel driver generation API...")
    print(f"URL: {url}")
    print(f"Parameters: {params}")
    
    try:
        # Make the request
        response = requests.post(url, params=params, timeout=30)
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            
            if data.get('data'):
                driver_info = data['data'].get('driver_info', {})
                print(f"Generated files: {driver_info.get('generated_files', [])}")
                print(f"Kernel module: {driver_info.get('kernel_module')}")
                print(f"Requires root: {driver_info.get('requires_root')}")
                print(f"Test case IDs: {data['data'].get('test_case_ids', [])}")
            
            return True
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint to verify server is running."""
    
    url = "http://localhost:8000/api/v1/health"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('message')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    print("=== Kernel Driver API Test ===\n")
    
    # Test health first
    if not test_health_endpoint():
        print("Server is not running or not accessible")
        exit(1)
    
    print()
    
    # Test kernel driver generation
    if test_kernel_driver_generation():
        print("\n✅ All tests passed! Kernel driver generation is working.")
    else:
        print("\n❌ Tests failed. Check the server logs for more details.")
        exit(1)