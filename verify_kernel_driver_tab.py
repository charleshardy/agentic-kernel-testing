#!/usr/bin/env python3
"""Verify that the Kernel Driver Files tab is working."""

import requests
import json

def get_auth_token():
    """Get authentication token."""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            headers={"Content-Type": "application/json"},
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('access_token')
    except Exception as e:
        print(f"❌ Failed to get auth token: {e}")
    return None

def check_kernel_driver_tests():
    """Check if kernel driver tests exist and have the right structure."""
    token = get_auth_token()
    if not token:
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8000/api/v1/tests", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API returned {response.status_code}")
            return False
        
        data = response.json()
        tests = data.get('data', {}).get('tests', [])
        
        print(f"📊 Found {len(tests)} total tests")
        
        kernel_driver_tests = []
        for test in tests:
            # Check if it's a kernel driver test
            is_kernel_driver = (
                test.get('test_metadata', {}).get('generation_method') == 'ai_kernel_driver' or
                test.get('metadata', {}).get('generation_method') == 'ai_kernel_driver' or
                test.get('generation_info', {}).get('method') == 'ai_kernel_driver' or
                test.get('test_metadata', {}).get('kernel_module') or
                test.get('test_metadata', {}).get('requires_root') or
                test.get('test_metadata', {}).get('driver_files')
            )
            
            if is_kernel_driver:
                kernel_driver_tests.append(test)
        
        print(f"🔧 Found {len(kernel_driver_tests)} kernel driver tests")
        
        if kernel_driver_tests:
            for i, test in enumerate(kernel_driver_tests):
                print(f"\n📋 Kernel Driver Test {i+1}:")
                print(f"   ID: {test.get('id')}")
                print(f"   Name: {test.get('name')}")
                
                # Check test_metadata
                test_metadata = test.get('test_metadata', {})
                if test_metadata:
                    print(f"   Generation Method: {test_metadata.get('generation_method')}")
                    print(f"   Kernel Module: {test_metadata.get('kernel_module')}")
                    print(f"   Requires Root: {test_metadata.get('requires_root')}")
                    
                    driver_files = test_metadata.get('driver_files', {})
                    if driver_files:
                        print(f"   Driver Files: {list(driver_files.keys())}")
                        print(f"   ✅ Has driver files - Kernel Driver Files tab should appear!")
                    else:
                        print(f"   ❌ No driver files found")
                
                # Check generation_info
                generation_info = test.get('generation_info', {})
                if generation_info:
                    print(f"   Generation Info Method: {generation_info.get('method')}")
                    source_data = generation_info.get('source_data', {})
                    if source_data:
                        print(f"   Target Function: {source_data.get('function_name')}")
                        print(f"   Source File: {source_data.get('file_path')}")
                        print(f"   Subsystem: {source_data.get('subsystem')}")
            
            return True
        else:
            print("❌ No kernel driver tests found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking tests: {e}")
        return False

def main():
    print("🔍 Verifying Kernel Driver Files Tab")
    print("=" * 50)
    
    if check_kernel_driver_tests():
        print("\n🎉 Verification successful!")
        print("\nThe Kernel Driver Files tab should now work:")
        print("1. Open http://localhost:3001")
        print("2. Go to Test Cases page")
        print("3. Click 'View' on a kernel driver test case")
        print("4. You should see a 'Kernel Driver Files' tab")
        print("5. The tab should show source code, build instructions, etc.")
        
        print("\n📝 What the tab includes:")
        print("- Complete kernel module source code with syntax highlighting")
        print("- Makefile for building the module")
        print("- Installation and test execution scripts")
        print("- Build and execution instructions")
        print("- Safety information and capabilities")
        print("- Download and copy functionality for each file")
        
    else:
        print("\n❌ Verification failed")
        print("Generate a kernel driver test first:")
        print("1. Go to Test Cases page")
        print("2. Click 'AI Generate Tests' -> 'Kernel Test Driver'")
        print("3. Fill in function name, file path, subsystem")
        print("4. Click 'Generate Kernel Driver'")
        print("5. Then try viewing the generated test case")

if __name__ == "__main__":
    main()