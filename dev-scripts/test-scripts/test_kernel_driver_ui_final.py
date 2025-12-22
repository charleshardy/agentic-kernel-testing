#!/usr/bin/env python3
"""
Final comprehensive test for Kernel Driver UI Enhancement
Handles authentication and tests the complete workflow
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"
FRONTEND_URL = "http://localhost:3001"

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
    
    def authenticate(self):
        """Get authentication token"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("access_token"):
                    self.token = data["data"]["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}"
                    })
                    print("✅ Authentication successful")
                    return True
            print(f"❌ Authentication failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def generate_kernel_driver(self):
        """Generate kernel driver test case"""
        params = {
            "function_name": "kmalloc",
            "file_path": "mm/slab.c",
            "subsystem": "memory",
            "test_types": "unit,integration"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE_URL}/tests/generate-kernel-driver",
                params=params,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data['data']['test_case_ids'][0]
            
            print(f"❌ Generation failed: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return None
    
    def get_test_case(self, test_id):
        """Get test case details"""
        try:
            response = self.session.get(f"{API_BASE_URL}/tests/{test_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data["data"]
            
            print(f"❌ Failed to get test case: {response.status_code}")
            return None
        except Exception as e:
            print(f"❌ Error getting test case: {e}")
            return None
    
    def get_all_tests(self):
        """Get all test cases"""
        try:
            response = self.session.get(f"{API_BASE_URL}/tests", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data["data"]["tests"]
            
            print(f"❌ Failed to get tests: {response.status_code}")
            return []
        except Exception as e:
            print(f"❌ Error getting tests: {e}")
            return []

def test_kernel_driver_ui_enhancement():
    """Test the complete kernel driver UI enhancement"""
    print("🧪 Testing Kernel Driver UI Enhancement")
    print("=" * 60)
    
    client = APIClient()
    
    # Step 1: Authenticate
    print("1. Authenticating with API...")
    if not client.authenticate():
        print("❌ Cannot proceed without authentication")
        return False
    
    # Step 2: Generate kernel driver test case
    print("\n2. Generating kernel driver test case...")
    test_id = client.generate_kernel_driver()
    if not test_id:
        print("❌ Failed to generate test case")
        return False
    
    print(f"✅ Generated test case: {test_id}")
    
    # Step 3: Wait for processing
    print("\n3. Waiting for test case processing...")
    time.sleep(3)
    
    # Step 4: Get test case details
    print("4. Fetching test case details...")
    test_case = client.get_test_case(test_id)
    if not test_case:
        print("❌ Failed to get test case details")
        return False
    
    print(f"✅ Retrieved test case: {test_case.get('name', 'N/A')}")
    
    # Step 5: Verify UI data structure
    print("\n5. Verifying UI data structure...")
    
    # Check generation method
    generation_method = test_case.get('metadata', {}).get('generation_method')
    print(f"   Generation method: {generation_method}")
    
    # Check for driver files
    driver_files = test_case.get('metadata', {}).get('driver_files', {})
    if driver_files:
        print(f"✅ Driver files found: {list(driver_files.keys())}")
        
        # Verify file contents for syntax highlighting
        for filename, content in driver_files.items():
            if content and len(content) > 0:
                print(f"   📄 {filename}: {len(content)} characters")
                
                # Check file type for syntax highlighting
                ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
                syntax_lang = {
                    'c': 'C/C++',
                    'h': 'C/C++ Header', 
                    'sh': 'Bash Script',
                    'py': 'Python',
                    'md': 'Markdown',
                    'json': 'JSON',
                    'yaml': 'YAML',
                    'yml': 'YAML'
                }.get(ext, 'Makefile' if 'Makefile' in filename else 'Text')
                
                print(f"      → Syntax highlighting: {syntax_lang}")
            else:
                print(f"   ⚠️  {filename}: Empty content")
    else:
        print("❌ No driver files found")
    
    # Check kernel module metadata
    kernel_module = test_case.get('metadata', {}).get('kernel_module')
    requires_root = test_case.get('metadata', {}).get('requires_root')
    requires_headers = test_case.get('metadata', {}).get('requires_kernel_headers')
    test_types = test_case.get('metadata', {}).get('test_types', [])
    
    print(f"   Kernel module: {kernel_module}")
    print(f"   Requires root: {requires_root}")
    print(f"   Requires headers: {requires_headers}")
    print(f"   Test types: {test_types}")
    
    # Step 6: Verify UI detection logic
    print("\n6. Verifying UI detection logic...")
    
    is_kernel_driver = (
        generation_method == 'ai_kernel_driver' or
        test_case.get('metadata', {}).get('kernel_module') == True or
        test_case.get('metadata', {}).get('requires_root') == True or
        (driver_files and len(driver_files) > 0)
    )
    
    if is_kernel_driver:
        print("✅ Test case WILL be detected as kernel driver in UI")
    else:
        print("❌ Test case will NOT be detected as kernel driver in UI")
    
    # Step 7: Verify all tests endpoint
    print("\n7. Verifying test case appears in list...")
    all_tests = client.get_all_tests()
    
    found_test = None
    for test in all_tests:
        if test.get('id') == test_id:
            found_test = test
            break
    
    if found_test:
        print(f"✅ Test case found in list: {found_test.get('name')}")
    else:
        print(f"❌ Test case not found in list (total tests: {len(all_tests)})")
    
    # Step 8: Summary and UI verification guide
    print("\n" + "=" * 60)
    print("📋 KERNEL DRIVER UI ENHANCEMENT VERIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"Test Case ID: {test_id}")
    print(f"Generation Method: {generation_method}")
    print(f"Driver Files: {len(driver_files)} files")
    print(f"UI Detection: {'✅ PASS' if is_kernel_driver else '❌ FAIL'}")
    
    if is_kernel_driver and driver_files:
        print("\n🎨 EXPECTED UI FEATURES:")
        print("   ✓ 'Kernel Driver Files' tab appears in modal")
        print("   ✓ Syntax highlighting for code files:")
        for filename in driver_files.keys():
            ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
            lang = {
                'c': 'C syntax',
                'h': 'C syntax', 
                'sh': 'Bash syntax',
                'md': 'Markdown syntax'
            }.get(ext, 'Makefile syntax' if 'Makefile' in filename else 'Plain text')
            print(f"      - {filename}: {lang}")
        
        print("   ✓ Copy to clipboard buttons")
        print("   ✓ Download file buttons")
        print("   ✓ Build & execution instructions")
        print("   ✓ Safety information panel")
        print("   ✓ Driver information (module name, root required, etc.)")
        
        print(f"\n🌐 MANUAL UI VERIFICATION:")
        print(f"   1. Open: {FRONTEND_URL}/test-cases")
        print(f"   2. Find test case: {test_case.get('name', test_id)}")
        print(f"   3. Click 'View Details'")
        print(f"   4. Look for 'Kernel Driver Files' tab")
        print(f"   5. Verify syntax highlighting and file display")
        
        return True
    else:
        print("\n❌ UI enhancement verification FAILED")
        print("   - Check if driver files are properly generated")
        print("   - Verify metadata structure")
        print("   - Check UI detection logic")
        
        return False

if __name__ == "__main__":
    success = test_kernel_driver_ui_enhancement()
    
    if success:
        print("\n🎉 KERNEL DRIVER UI ENHANCEMENT VERIFICATION PASSED!")
    else:
        print("\n💥 VERIFICATION FAILED - Check the issues above")
    
    print("\nFor complete verification, manually test the UI in your browser.")