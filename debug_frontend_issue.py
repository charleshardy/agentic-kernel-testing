#!/usr/bin/env python3
"""
Debug frontend issue - check if API is returning proper data
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    print("🔍 DEBUGGING FRONTEND ISSUE")
    print("=" * 40)
    
    # Step 1: Check API health
    print("1. Checking API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"   API Health: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API is healthy")
        else:
            print("   ❌ API health issue")
            return
    except Exception as e:
        print(f"   ❌ API not accessible: {e}")
        return
    
    # Step 2: Get auth token
    print("\n2. Getting authentication...")
    try:
        auth_response = requests.post(f"{API_BASE_URL}/auth/demo-login", timeout=10)
        if auth_response.status_code == 200:
            token = auth_response.json()['data']['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ Authentication successful")
        else:
            print(f"   ❌ Auth failed: {auth_response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
        return
    
    # Step 3: List all test cases
    print("\n3. Listing test cases...")
    try:
        response = requests.get(f"{API_BASE_URL}/tests", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            tests = data.get('data', {}).get('tests', [])
            print(f"   ✅ Found {len(tests)} test cases")
            
            # Find kernel driver tests
            kernel_tests = []
            for test in tests:
                metadata = test.get('test_metadata', {})
                generation_info = test.get('generation_info', {})
                
                is_kernel = (
                    metadata.get('generation_method') == 'ai_kernel_driver' or
                    generation_info.get('method') == 'ai_kernel_driver' or
                    bool(metadata.get('driver_files'))
                )
                
                if is_kernel:
                    kernel_tests.append({
                        'id': test.get('id'),
                        'name': test.get('name'),
                        'has_driver_files': bool(metadata.get('driver_files')),
                        'file_count': len(metadata.get('driver_files', {}))
                    })
            
            print(f"   📁 Found {len(kernel_tests)} kernel driver tests:")
            for test in kernel_tests[:3]:  # Show first 3
                print(f"      🧪 {test['name']} (ID: {test['id']})")
                print(f"         Files: {test['file_count']} files available")
            
            if kernel_tests:
                # Test one specific case
                test_case = kernel_tests[0]
                print(f"\n4. Testing specific case: {test_case['id']}")
                
                response = requests.get(f"{API_BASE_URL}/tests/{test_case['id']}", headers=headers, timeout=10)
                if response.status_code == 200:
                    test_data = response.json()['data']
                    metadata = test_data.get('test_metadata', {})
                    driver_files = metadata.get('driver_files', {})
                    
                    print(f"   ✅ Test case details retrieved")
                    print(f"   📁 Driver files: {len(driver_files)} files")
                    for filename in list(driver_files.keys())[:3]:
                        content_length = len(driver_files[filename]) if driver_files[filename] else 0
                        print(f"      📄 {filename}: {content_length} chars")
                    
                    print(f"\n🎯 FRONTEND SHOULD SHOW:")
                    print(f"   - Test case: '{test_case['name']}'")
                    print(f"   - Generation Source tab with 'Generated Files' section")
                    print(f"   - {len(driver_files)} collapsible file panels")
                    print(f"   - Syntax highlighting and copy/download buttons")
                else:
                    print(f"   ❌ Could not get test details: {response.status_code}")
            else:
                print("   ⚠️  No kernel driver tests found")
                print("   💡 Try generating a new one:")
                print(f"      curl -X POST '{API_BASE_URL}/tests/generate-kernel-driver?function_name=kmalloc&file_path=mm/slab.c&subsystem=memory'")
        else:
            print(f"   ❌ Could not list tests: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error listing tests: {e}")
    
    print(f"\n🌐 FRONTEND ACCESS:")
    print(f"   URL: http://localhost:3000/test-cases")
    print(f"   Expected: Test cases should be visible with 'View Details' buttons")

if __name__ == "__main__":
    main()