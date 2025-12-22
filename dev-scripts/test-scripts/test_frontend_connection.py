#!/usr/bin/env python3
"""
Test frontend connection and data flow
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    print("🔍 TESTING FRONTEND CONNECTION")
    print("=" * 40)
    
    # Step 1: Generate a test case
    print("1. Generating test case...")
    response = requests.post(
        f"{API_BASE_URL}/tests/generate-kernel-driver",
        params={
            "function_name": "kmalloc",
            "file_path": "mm/slab.c", 
            "subsystem": "memory",
            "test_types": ["unit"]
        }
    )
    
    if response.status_code == 200:
        test_id = response.json()['data']['test_case_ids'][0]
        print(f"   ✅ Generated: {test_id}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
        return
    
    # Step 2: Get auth token
    print("\n2. Getting auth token...")
    auth_response = requests.post(f"{API_BASE_URL}/auth/demo-login")
    token = auth_response.json()['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Got token")
    
    # Step 3: List all tests (what frontend would do)
    print("\n3. Listing tests (frontend API call)...")
    list_response = requests.get(f"{API_BASE_URL}/tests", headers=headers)
    
    if list_response.status_code == 200:
        data = list_response.json()
        tests = data['data']['tests']
        print(f"   ✅ Found {len(tests)} tests")
        
        # Find kernel driver tests
        kernel_tests = []
        for test in tests:
            metadata = test.get('test_metadata', {})
            if metadata.get('generation_method') == 'ai_kernel_driver':
                kernel_tests.append(test)
        
        print(f"   📁 Kernel driver tests: {len(kernel_tests)}")
        
        if kernel_tests:
            # Show details of first kernel test
            test = kernel_tests[0]
            print(f"\n📋 SAMPLE TEST CASE:")
            print(f"   ID: {test['id']}")
            print(f"   Name: {test['name']}")
            print(f"   Generation Method: {test['test_metadata'].get('generation_method')}")
            
            # Check driver files
            driver_files = test['test_metadata'].get('driver_files', {})
            print(f"   Driver Files: {len(driver_files)} files")
            
            if driver_files:
                print(f"\n📄 FILES AVAILABLE FOR FRONTEND:")
                for filename in driver_files.keys():
                    print(f"      {filename}")
                
                print(f"\n🌐 FRONTEND SHOULD SHOW:")
                print(f"   • Test case '{test['name']}' in the list")
                print(f"   • 'View Details' button")
                print(f"   • Generation Source tab with Generated Files section")
                print(f"   • {len(driver_files)} collapsible file panels")
                
                print(f"\n🎯 MANUAL CHECK:")
                print(f"   1. Open: http://localhost:3000/test-cases")
                print(f"   2. Look for: '{test['name']}'")
                print(f"   3. If you don't see it, try:")
                print(f"      - Hard refresh (Ctrl+F5)")
                print(f"      - Clear browser cache")
                print(f"      - Check browser console for errors")
            else:
                print("   ❌ No driver files in metadata!")
        else:
            print("   ⚠️  No kernel driver tests found")
    else:
        print(f"   ❌ Failed to list tests: {list_response.status_code}")

if __name__ == "__main__":
    main()