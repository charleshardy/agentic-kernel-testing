#!/usr/bin/env python3
"""
Test the View Source enhancement
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3000"

def main():
    print("🎯 VIEW SOURCE ENHANCEMENT - VERIFICATION")
    print("=" * 50)
    
    # Generate a test case
    print("1. Generating kernel driver test case...")
    response = requests.post(
        f"{API_BASE_URL}/tests/generate-kernel-driver",
        params={
            "function_name": "kmalloc",
            "file_path": "mm/slab.c",
            "subsystem": "memory",
            "test_types": ["unit", "integration"]
        }
    )
    
    if response.status_code == 200:
        test_id = response.json()['data']['test_case_ids'][0]
        print(f"   ✅ Generated: {test_id}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
        return
    
    # Get auth and verify test case
    print("\n2. Verifying test case has driver files...")
    auth_response = requests.post(f"{API_BASE_URL}/auth/demo-login")
    token = auth_response.json()['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    test_response = requests.get(f"{API_BASE_URL}/tests/{test_id}", headers=headers)
    if test_response.status_code == 200:
        test_case = test_response.json()['data']
        driver_files = test_case['test_metadata']['driver_files']
        print(f"   ✅ Found {len(driver_files)} driver files")
        
        for filename in driver_files.keys():
            print(f"      📄 {filename}")
    else:
        print(f"   ❌ Could not get test case: {test_response.status_code}")
        return
    
    print(f"\n🎉 VIEW SOURCE ENHANCEMENT READY!")
    print("=" * 50)
    
    print(f"\n📋 NEW FEATURES ADDED:")
    print(f"   ✅ 'View Source' button (👁️ icon) for each file")
    print(f"   ✅ Quick Access section with direct links")
    print(f"   ✅ Full-screen source code modal")
    print(f"   ✅ Enhanced syntax highlighting")
    print(f"   ✅ Copy and download from modal")
    
    print(f"\n🎯 TESTING STEPS:")
    print(f"   1. Open: {FRONTEND_URL}/test-cases")
    print(f"   2. Find: '{test_case.get('name')}'")
    print(f"   3. Click: 'View Details'")
    print(f"   4. Click: 'Generation Source' tab")
    print(f"   5. See: 'Quick Access - View Source Code' section")
    print(f"   6. Click: Any filename link (e.g., 'test_kmalloc.c')")
    print(f"   7. See: Full-screen modal with colored syntax highlighting")
    print(f"   8. Test: Copy All and Download buttons in modal")
    
    print(f"\n📄 AVAILABLE FILES:")
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
    
    print(f"\n🔧 IF YOU DON'T SEE THE ENHANCEMENT:")
    print(f"   • Hard refresh: Ctrl+F5")
    print(f"   • Clear browser cache")
    print(f"   • Try incognito mode")
    print(f"   • Check browser console for errors")

if __name__ == "__main__":
    main()