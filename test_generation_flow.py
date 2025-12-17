#!/usr/bin/env python3
"""
Test the complete generation flow
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    print("🧪 TESTING COMPLETE GENERATION FLOW")
    print("=" * 40)
    
    # Step 1: Get auth token
    print("1. Getting auth token...")
    auth_response = requests.post(f"{API_BASE_URL}/auth/demo-login")
    token = auth_response.json()['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Got auth token")
    
    # Step 2: Generate test case
    print("\n2. Generating kernel driver test case...")
    gen_response = requests.post(
        f"{API_BASE_URL}/tests/generate-kernel-driver",
        params={
            "function_name": "kmalloc",
            "file_path": "mm/slab.c",
            "subsystem": "memory",
            "test_types": ["unit", "integration"]
        }
    )
    
    print(f"   Generation status: {gen_response.status_code}")
    if gen_response.status_code == 200:
        gen_data = gen_response.json()
        test_id = gen_data['data']['test_case_ids'][0]
        print(f"   ✅ Generated test case: {test_id}")
    else:
        print(f"   ❌ Generation failed: {gen_response.text}")
        return
    
    # Step 3: Wait a moment and try to retrieve it
    print(f"\n3. Retrieving test case {test_id}...")
    time.sleep(1)  # Wait a moment
    
    get_response = requests.get(f"{API_BASE_URL}/tests/{test_id}", headers=headers)
    print(f"   Retrieval status: {get_response.status_code}")
    
    if get_response.status_code == 200:
        test_data = get_response.json()['data']
        print(f"   ✅ Retrieved test case: {test_data.get('name')}")
        
        # Check for driver files
        metadata = test_data.get('test_metadata', {})
        driver_files = metadata.get('driver_files', {})
        
        if driver_files:
            print(f"   📁 Found {len(driver_files)} driver files:")
            for filename in driver_files.keys():
                print(f"      📄 {filename}")
            
            print(f"\n🎉 SUCCESS! Frontend should now show:")
            print(f"   - Test case: '{test_data.get('name')}'")
            print(f"   - Generation Source tab with Generated Files")
            print(f"   - {len(driver_files)} files with syntax highlighting")
            print(f"\n🌐 Check: http://localhost:3000/test-cases")
        else:
            print("   ❌ No driver files found in metadata")
    else:
        print(f"   ❌ Could not retrieve: {get_response.text}")
    
    # Step 4: List all tests to verify
    print(f"\n4. Listing all tests...")
    list_response = requests.get(f"{API_BASE_URL}/tests", headers=headers)
    if list_response.status_code == 200:
        tests = list_response.json()['data']['tests']
        print(f"   ✅ Total tests in system: {len(tests)}")
        
        kernel_tests = [t for t in tests if t.get('test_metadata', {}).get('generation_method') == 'ai_kernel_driver']
        print(f"   📁 Kernel driver tests: {len(kernel_tests)}")
    else:
        print(f"   ❌ Could not list tests: {list_response.status_code}")

if __name__ == "__main__":
    main()