#!/usr/bin/env python3
"""
Final verification script for Generation Source tab enhancement
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3000"

def main():
    print("🎯 FINAL VERIFICATION - Generation Source Tab Enhancement")
    print("=" * 60)
    
    try:
        # Step 1: Generate a fresh test case
        print("1. Generating fresh kernel driver test case...")
        response = requests.post(
            f"{API_BASE_URL}/tests/generate-kernel-driver",
            params={
                "function_name": "schedule",
                "file_path": "kernel/sched/core.c",
                "subsystem": "scheduler",
                "test_types": ["unit", "integration"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            test_id = data['data']['test_case_ids'][0]
            print(f"   ✅ Generated: {test_id}")
        else:
            print(f"   ❌ Generation failed: {response.status_code}")
            return
        
        # Step 2: Get auth token
        print("\n2. Getting authentication token...")
        auth_response = requests.post(f"{API_BASE_URL}/auth/demo-login", timeout=5)
        if auth_response.status_code == 200:
            token = auth_response.json()['data']['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ Authentication successful")
        else:
            print(f"   ❌ Auth failed: {auth_response.status_code}")
            return
        
        # Step 3: Verify test case has driver files
        print(f"\n3. Verifying test case has driver files...")
        test_response = requests.get(f"{API_BASE_URL}/tests/{test_id}", headers=headers, timeout=5)
        
        if test_response.status_code == 200:
            test_case = test_response.json()['data']
            metadata = test_case.get('test_metadata', {})
            driver_files = metadata.get('driver_files', {})
            
            print(f"   ✅ Test case retrieved: {test_case.get('name')}")
            print(f"   📁 Driver files: {len(driver_files)} files")
            
            if driver_files:
                for filename in driver_files.keys():
                    print(f"      📄 {filename}")
            else:
                print("   ❌ No driver files found!")
                return
        else:
            print(f"   ❌ Could not retrieve test case: {test_response.status_code}")
            return
        
        # Step 4: Success - provide manual instructions
        print(f"\n" + "=" * 60)
        print("🎉 SUCCESS! Enhancement is ready for testing")
        print("=" * 60)
        
        print(f"\n📋 MANUAL TESTING STEPS:")
        print(f"   1. Open browser to: {FRONTEND_URL}/test-cases")
        print(f"   2. Look for test case: '{test_case.get('name')}'")
        print(f"   3. Click 'View Details' button")
        print(f"   4. Click 'Generation Source' tab")
        print(f"   5. Scroll down to 'Generated Files' section")
        print(f"   6. You should see {len(driver_files)} collapsible file panels")
        
        print(f"\n🔧 IF YOU DON'T SEE THE ENHANCEMENT:")
        print(f"   • Press Ctrl+F5 to hard refresh the page")
        print(f"   • Try incognito/private browsing mode")
        print(f"   • Clear browser cache and cookies")
        print(f"   • Check browser console (F12) for errors")
        
        print(f"\n📄 EXPECTED FILES:")
        for filename in driver_files.keys():
            ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
            if ext in ['c', 'h']:
                syntax = 'C/C++'
            elif ext == 'sh':
                syntax = 'Bash'
            elif ext == 'md':
                syntax = 'Markdown'
            elif 'Makefile' in filename:
                syntax = 'Makefile'
            else:
                syntax = 'Text'
            print(f"   📄 {filename} → {syntax} syntax highlighting")
        
        print(f"\n🎯 DIRECT LINK:")
        print(f"   {FRONTEND_URL}/test-cases")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()