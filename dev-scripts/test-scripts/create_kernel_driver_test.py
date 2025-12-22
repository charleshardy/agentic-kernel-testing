#!/usr/bin/env python3
"""
Create a kernel driver test case to verify tab reorganization
"""

import requests
import json

def create_kernel_driver_test():
    """Create a kernel driver test case for verification"""
    
    print("🔧 CREATING KERNEL DRIVER TEST CASE")
    print("=" * 50)
    
    # Get demo token
    try:
        auth_response = requests.post('http://localhost:8000/api/v1/auth/demo-login', timeout=5)
        if auth_response.status_code == 200:
            token = auth_response.json()['data']['access_token']
            print("✅ Demo authentication successful")
        else:
            print(f"❌ Demo authentication failed: {auth_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Demo authentication error: {e}")
        return False
    
    # Create kernel driver test case
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Use query parameters instead of JSON body
    params = {
        "function_name": "kmalloc",
        "file_path": "mm/slab.c",
        "subsystem": "memory_management",
        "test_types": "unit,performance,stress",
        "complexity": "medium"
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/tests/generate-kernel-driver',
            headers=headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 API Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                test_case = result['data']
                
                # Handle kernel driver generation response structure
                if 'test_case_ids' in test_case and test_case['test_case_ids']:
                    test_id = test_case['test_case_ids'][0]
                elif 'id' in test_case:
                    test_id = test_case['id']
                else:
                    print(f"❌ No test case ID found in response")
                    return None
                
                print(f"✅ Created kernel driver test case: {test_id}")
                print(f"   Function: {test_case.get('function', {}).get('name', 'Unknown')}")
                
                # Verify the test case has driver files
                if test_case.get('driver_info', {}).get('generated_files'):
                    driver_files = test_case['driver_info']['generated_files']
                    print(f"✅ Driver files created: {driver_files}")
                    return test_id
                else:
                    print("⚠️  Test case created but no driver files found")
                    return test_id
            else:
                print(f"❌ Failed to create test case: {result.get('message', 'Unknown error')}")
                return None
        else:
            print(f"❌ API request failed: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating kernel driver test: {e}")
        return None

def verify_test_case(test_id, token):
    """Verify the created test case has all required data"""
    
    print(f"\n🔍 VERIFYING TEST CASE: {test_id}")
    print("=" * 50)
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(
            f'http://localhost:8000/api/v1/tests/{test_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            test_case = response.json()['data']
            print("✅ Retrieved detailed test case")
            
            # Check generation method
            gen_method = (test_case.get('test_metadata', {}).get('generation_method') or 
                         test_case.get('generation_info', {}).get('method'))
            print(f"✅ Generation method: {gen_method}")
            
            # Check driver files
            driver_files = None
            if test_case.get('test_metadata', {}).get('driver_files'):
                driver_files = test_case['test_metadata']['driver_files']
            elif test_case.get('generation_info', {}).get('driver_files'):
                driver_files = test_case['generation_info']['driver_files']
            
            if driver_files:
                print(f"✅ Driver files found: {list(driver_files.keys())}")
                
                # Check file contents
                for filename, content in driver_files.items():
                    if content and len(str(content)) > 0:
                        print(f"   📄 {filename}: {len(str(content))} characters")
                    else:
                        print(f"   ⚠️  {filename}: Empty content")
                        
                return True
            else:
                print("❌ No driver files found")
                return False
        else:
            print(f"❌ Failed to retrieve test case: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying test case: {e}")
        return False

def main():
    """Main function"""
    
    print("🚀 CREATING KERNEL DRIVER TEST FOR TAB VERIFICATION")
    print("=" * 70)
    
    # Create test case
    test_id = create_kernel_driver_test()
    
    if test_id:
        # Get token again for verification
        auth_response = requests.post('http://localhost:8000/api/v1/auth/demo-login', timeout=5)
        token = auth_response.json()['data']['access_token']
        
        # Verify test case
        verified = verify_test_case(test_id, token)
        
        if verified:
            print("\n🎉 KERNEL DRIVER TEST CASE CREATED SUCCESSFULLY!")
            print("\n🌐 MANUAL VERIFICATION STEPS:")
            print("   1. Open: http://localhost:3000/test-cases")
            print("   2. Find the newly created kernel driver test")
            print("   3. Click 'View Details' on the test case")
            print("   4. Look for 'Kernel Driver Files' tab")
            print("   5. Check 'Driver Information' section with generation details")
            print("   6. Verify 'Generated Files' section with syntax highlighting")
            print("   7. Test 'Quick Access - View Source Code' links")
            print("\n🔧 IF YOU STILL DON'T SEE THE CHANGES:")
            print("   • Hard refresh: Ctrl+F5")
            print("   • Clear browser cache completely")
            print("   • Try incognito/private browsing mode")
            print("   • Check browser console for errors (F12)")
            return True
        else:
            print("\n❌ TEST CASE VERIFICATION FAILED")
            return False
    else:
        print("\n❌ FAILED TO CREATE TEST CASE")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)