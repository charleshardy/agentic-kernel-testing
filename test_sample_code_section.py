#!/usr/bin/env python3
"""
Test the new Sample Generated Code section in TestCaseModal
"""

import requests
import json

def test_sample_code_section():
    """Test that the Sample Generated Code section is working"""
    
    print("🔍 TESTING SAMPLE GENERATED CODE SECTION")
    print("=" * 60)
    
    # Check API server
    try:
        response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend API server is running")
        else:
            print(f"❌ Backend API server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend API server not accessible: {e}")
        return False
    
    # Check frontend server
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print("✅ Frontend server is running")
        else:
            print(f"❌ Frontend server error: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend server not accessible: {e}")
    
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
    
    # Get test cases
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get('http://localhost:8000/api/v1/tests/', headers=headers, timeout=10)
        
        if response.status_code == 200:
            response_data = response.json()['data']
            test_cases = response_data.get('tests', [])
            print(f"✅ Retrieved {len(test_cases)} test cases")
            
            # Find kernel driver test cases
            kernel_driver_tests = [
                tc for tc in test_cases 
                if (tc.get('test_metadata', {}).get('generation_method') == 'ai_kernel_driver' or
                    tc.get('generation_info', {}).get('method') == 'ai_kernel_driver')
            ]
            
            print(f"✅ Found {len(kernel_driver_tests)} kernel driver test cases")
            
            if kernel_driver_tests:
                # Check first kernel driver test
                test_case = kernel_driver_tests[0]
                test_id = test_case['id']
                
                print(f"\n📝 Checking kernel driver test: {test_id}")
                print(f"   Name: {test_case.get('name', 'Unknown')}")
                
                # Get detailed test case
                detail_response = requests.get(
                    f'http://localhost:8000/api/v1/tests/{test_id}', 
                    headers=headers, 
                    timeout=10
                )
                
                if detail_response.status_code == 200:
                    detailed_test = detail_response.json()['data']
                    print("✅ Retrieved detailed test case")
                    
                    # Check for driver files
                    driver_files = None
                    if detailed_test.get('test_metadata', {}).get('driver_files'):
                        driver_files = detailed_test['test_metadata']['driver_files']
                    elif detailed_test.get('generation_info', {}).get('driver_files'):
                        driver_files = detailed_test['generation_info']['driver_files']
                    
                    if driver_files:
                        print(f"✅ Driver files found: {list(driver_files.keys())}")
                        
                        # Check for main C file
                        c_files = [f for f in driver_files.keys() if f.endswith('.c')]
                        if c_files:
                            main_c_file = c_files[0]
                            c_content = driver_files[main_c_file]
                            print(f"✅ Main C file: {main_c_file} ({len(str(c_content))} characters)")
                            
                            # Check for key kernel module components
                            if '#include <linux/module.h>' in str(c_content):
                                print("✅ Contains kernel module headers")
                            if 'module_init' in str(c_content):
                                print("✅ Contains module initialization")
                            if 'module_exit' in str(c_content):
                                print("✅ Contains module cleanup")
                        
                        # Check for Makefile
                        makefiles = [f for f in driver_files.keys() if 'Makefile' in f]
                        if makefiles:
                            makefile = makefiles[0]
                            print(f"✅ Makefile found: {makefile}")
                        
                        # Check for shell scripts
                        scripts = [f for f in driver_files.keys() if f.endswith('.sh')]
                        if scripts:
                            print(f"✅ Shell scripts found: {scripts}")
                        
                        return True
                    else:
                        print("❌ No driver files found in test case")
                        return False
                else:
                    print(f"❌ Failed to get detailed test case: {detail_response.status_code}")
                    return False
            else:
                print("❌ No kernel driver test cases found")
                return False
        else:
            print(f"❌ Failed to get test cases: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking test cases: {e}")
        return False

def check_frontend_implementation():
    """Check if the Sample Generated Code section is implemented in the frontend"""
    
    print("\n🔍 CHECKING FRONTEND IMPLEMENTATION")
    print("=" * 50)
    
    try:
        with open('dashboard/src/components/TestCaseModal.tsx', 'r') as f:
            content = f.read()
            
        # Check for key indicators of the Sample Generated Code section
        indicators = [
            'Sample Generated Code',
            'Kernel Test Driver Code Preview',
            'Main Test Driver:',
            'Build System:',
            'Execution Script:',
            'Production Ready Code'
        ]
        
        found_indicators = []
        for indicator in indicators:
            if indicator in content:
                found_indicators.append(indicator)
                print(f"✅ Found: {indicator}")
            else:
                print(f"❌ Missing: {indicator}")
        
        if len(found_indicators) >= 5:
            print("✅ Sample Generated Code section implementation looks correct")
            return True
        else:
            print("❌ Sample Generated Code section implementation incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Error reading frontend file: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 TESTING SAMPLE GENERATED CODE SECTION")
    print("=" * 70)
    
    # Check frontend implementation
    frontend_ok = check_frontend_implementation()
    
    # Check API functionality
    api_ok = test_sample_code_section()
    
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS:")
    print(f"   Frontend Implementation: {'✅ OK' if frontend_ok else '❌ ISSUES'}")
    print(f"   API Functionality: {'✅ OK' if api_ok else '❌ ISSUES'}")
    
    if frontend_ok and api_ok:
        print("\n🎉 SAMPLE GENERATED CODE SECTION TEST SUCCESSFUL!")
        print("\n🌐 MANUAL VERIFICATION STEPS:")
        print("   1. Open: http://localhost:3000/test-cases")
        print("   2. Click on any kernel driver test case")
        print("   3. Go to 'Kernel Driver Files' tab")
        print("   4. Look for 'Sample Generated Code' section")
        print("   5. Verify it shows:")
        print("      • Main Test Driver (C source code preview)")
        print("      • Build System (Makefile)")
        print("      • Execution Script (shell script)")
        print("   6. Test the copy buttons and code preview")
        print("\n🔧 IF YOU DON'T SEE THE CHANGES:")
        print("   • Hard refresh: Ctrl+F5")
        print("   • Clear browser cache completely")
        print("   • Try incognito/private browsing mode")
        print("   • Check browser console for errors (F12)")
    else:
        print("\n❌ ISSUES DETECTED - NEEDS INVESTIGATION")
    
    return frontend_ok and api_ok

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)