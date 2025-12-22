#!/usr/bin/env python3
"""
Quick test to verify the Generation Source enhancement
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3000"

def main():
    print("🎯 GENERATION SOURCE TAB - QUICK VERIFICATION")
    print("=" * 50)
    
    # Step 1: Get auth token
    print("1. Getting authentication token...")
    try:
        auth_response = requests.post(f"{API_BASE_URL}/auth/demo-login", timeout=10)
        if auth_response.status_code == 200:
            token = auth_response.json()['data']['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ Authentication successful")
        else:
            print("   ❌ Authentication failed")
            return
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
        return
    
    # Step 2: Generate new test case
    print("\n2. Generating new kernel driver test case...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/tests/generate-kernel-driver",
            params={
                "function_name": "kmalloc",
                "file_path": "mm/slab.c",
                "subsystem": "memory",
                "test_types": ["unit", "integration"]
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            test_id = data['data']['test_case_ids'][0]
            print(f"   ✅ Generated test case: {test_id}")
        else:
            print(f"   ❌ Generation failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Generation error: {e}")
        return
    
    # Step 3: Verify test case has driver files
    print(f"\n3. Verifying test case has driver files...")
    try:
        response = requests.get(f"{API_BASE_URL}/tests/{test_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            test_case = response.json()['data']
            metadata = test_case.get("test_metadata", {})
            driver_files = metadata.get("driver_files", {})
            
            if driver_files:
                print(f"   ✅ Found {len(driver_files)} driver files:")
                for filename in driver_files.keys():
                    print(f"      📄 {filename}")
            else:
                print("   ❌ No driver files found")
                return
        else:
            print(f"   ❌ Could not retrieve test case: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 4: Success message
    print(f"\n🎉 SUCCESS! Generation Source tab enhancement is working!")
    print(f"   Test Case ID: {test_id}")
    print(f"   Test Case Name: {test_case.get('name', 'N/A')}")
    print(f"   Driver Files: {len(driver_files)} files available")
    
    print(f"\n🌐 MANUAL TESTING:")
    print(f"   1. Open: {FRONTEND_URL}/test-cases")
    print(f"   2. Find: '{test_case.get('name', 'N/A')}'")
    print(f"   3. Click: 'View Details'")
    print(f"   4. Click: 'Generation Source' tab")
    print(f"   5. Look for: 'Generated Files' section")
    print(f"   6. Test: Syntax highlighting and copy/download buttons")

if __name__ == "__main__":
    main()