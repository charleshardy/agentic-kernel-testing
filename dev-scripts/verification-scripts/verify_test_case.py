#!/usr/bin/env python3
"""
Verify the test case has proper structure for frontend
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"
TEST_ID = "kernel_driver_5f704763"

def main():
    print(f"🔍 VERIFYING TEST CASE: {TEST_ID}")
    print("=" * 50)
    
    # Get auth token
    auth_response = requests.post(f"{API_BASE_URL}/auth/demo-login")
    token = auth_response.json()['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get test case
    response = requests.get(f"{API_BASE_URL}/tests/{TEST_ID}", headers=headers)
    
    if response.status_code == 200:
        test_case = response.json()['data']
        
        print(f"✅ Test Case: {test_case.get('name')}")
        print(f"✅ ID: {test_case.get('id')}")
        
        # Check metadata
        metadata = test_case.get('test_metadata', {})
        generation_info = test_case.get('generation_info', {})
        
        print(f"\n📋 METADATA:")
        print(f"   Generation Method: {metadata.get('generation_method')}")
        print(f"   Kernel Module: {metadata.get('kernel_module')}")
        print(f"   Requires Root: {metadata.get('requires_root')}")
        
        # Check driver files
        driver_files = metadata.get('driver_files', {})
        print(f"\n📁 DRIVER FILES: {len(driver_files)} files")
        
        if driver_files:
            for filename, content in driver_files.items():
                content_len = len(content) if content else 0
                print(f"   📄 {filename}: {content_len} chars")
            
            print(f"\n🎯 FRONTEND SHOULD SHOW:")
            print(f"   1. Go to: http://localhost:3000/test-cases")
            print(f"   2. Find: '{test_case.get('name')}'")
            print(f"   3. Click: 'View Details'")
            print(f"   4. Click: 'Generation Source' tab")
            print(f"   5. See: 'Generated Files' section with {len(driver_files)} files")
            print(f"   6. Each file should have syntax highlighting and copy/download buttons")
            
            # Show sample content
            first_file = list(driver_files.keys())[0]
            sample_content = driver_files[first_file][:200] + "..." if len(driver_files[first_file]) > 200 else driver_files[first_file]
            print(f"\n📄 SAMPLE CONTENT ({first_file}):")
            print(f"   {sample_content}")
        else:
            print("   ❌ No driver files found!")
    else:
        print(f"❌ Could not get test case: {response.status_code}")

if __name__ == "__main__":
    main()