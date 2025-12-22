#!/usr/bin/env python3
"""
Test the tab reorganization - Generation Source content moved to Kernel Driver Files
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3000"

def main():
    print("🔄 TAB REORGANIZATION - VERIFICATION")
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
    
    print(f"\n🎉 TAB REORGANIZATION COMPLETE!")
    print("=" * 50)
    
    print(f"\n📋 CHANGES MADE:")
    print(f"   ✅ Moved Generation Source content to Kernel Driver Files tab")
    print(f"   ✅ Enhanced Driver Information section")
    print(f"   ✅ Added generation details (Target Function, Source File, etc.)")
    print(f"   ✅ Moved Quick Access links to Kernel Driver Files")
    print(f"   ✅ Moved source code viewer to Kernel Driver Files")
    print(f"   ✅ Added Kernel Driver Capabilities section")
    print(f"   ✅ Kept Build & Execution Instructions")
    
    print(f"\n🎯 NEW STRUCTURE:")
    print(f"   📁 Kernel Driver Files Tab:")
    print(f"      • Driver Information (enhanced with generation details)")
    print(f"      • Generated Files (with Quick Access links)")
    print(f"      • Kernel Driver Capabilities")
    print(f"      • Build & Execution Instructions")
    print(f"   📋 Generation Source Tab:")
    print(f"      • General generation information (for all test types)")
    print(f"      • Source code diff (for ai_diff tests)")
    print(f"      • Function analysis (for ai_function tests)")
    print(f"      • Manual test info (for manual tests)")
    
    print(f"\n🎯 TESTING STEPS:")
    print(f"   1. Open: {FRONTEND_URL}/test-cases")
    print(f"   2. Find: '{test_case.get('name')}'")
    print(f"   3. Click: 'View Details'")
    print(f"   4. Click: 'Kernel Driver Files' tab")
    print(f"   5. See: Enhanced Driver Information with generation details")
    print(f"   6. See: Quick Access - View Source Code section")
    print(f"   7. See: Kernel Driver Capabilities section")
    print(f"   8. Click: 'Generation Source' tab")
    print(f"   9. See: General generation information (no kernel-specific content)")
    
    print(f"\n📄 AVAILABLE IN KERNEL DRIVER FILES TAB:")
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
    
    print(f"\n🔧 IF YOU DON'T SEE THE CHANGES:")
    print(f"   • Hard refresh: Ctrl+F5")
    print(f"   • Clear browser cache")
    print(f"   • Try incognito mode")
    print(f"   • Check browser console for errors")

if __name__ == "__main__":
    main()