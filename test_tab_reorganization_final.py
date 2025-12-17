#!/usr/bin/env python3
"""
Final verification of tab reorganization implementation
"""

import requests
import json
import time

def test_tab_reorganization():
    """Test that the tab reorganization is working correctly"""
    
    print("🔍 TAB REORGANIZATION FINAL VERIFICATION")
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
                if (tc.get('metadata', {}).get('generation_method') == 'ai_kernel_driver' or
                    tc.get('generation_info', {}).get('method') == 'ai_kernel_driver' or
                    tc.get('metadata', {}).get('kernel_module') or
                    tc.get('metadata', {}).get('driver_files'))
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
                    if detailed_test.get('metadata', {}).get('driver_files'):
                        driver_files = detailed_test['metadata']['driver_files']
                    elif detailed_test.get('generation_info', {}).get('driver_files'):
                        driver_files = detailed_test['generation_info']['driver_files']
                    
                    if driver_files:
                        print(f"✅ Driver files found: {list(driver_files.keys())}")
                        
                        # Check file contents
                        for filename, content in driver_files.items():
                            if content and len(str(content)) > 0:
                                print(f"   📄 {filename}: {len(str(content))} characters")
                            else:
                                print(f"   ⚠️  {filename}: Empty or missing content")
                    else:
                        print("❌ No driver files found in test case")
                    
                    # Check generation info
                    gen_method = (detailed_test.get('metadata', {}).get('generation_method') or 
                                detailed_test.get('generation_info', {}).get('method'))
                    if gen_method:
                        print(f"✅ Generation method: {gen_method}")
                    
                    return True
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

def check_frontend_file():
    """Check the current state of the TestCaseModal.tsx file"""
    
    print("\n🔍 CHECKING FRONTEND FILE")
    print("=" * 40)
    
    try:
        with open('dashboard/src/components/TestCaseModal.tsx', 'r') as f:
            content = f.read()
            
        # Check for key indicators of the reorganization
        indicators = [
            'Kernel Driver Files',
            'Driver Information',
            'Generated Files',
            'Quick Access - View Source Code',
            'Kernel Driver Capabilities'
        ]
        
        found_indicators = []
        for indicator in indicators:
            if indicator in content:
                found_indicators.append(indicator)
                print(f"✅ Found: {indicator}")
            else:
                print(f"❌ Missing: {indicator}")
        
        if len(found_indicators) >= 4:
            print("✅ Tab reorganization implementation looks correct")
            return True
        else:
            print("❌ Tab reorganization implementation incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Error reading frontend file: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 STARTING FINAL TAB REORGANIZATION VERIFICATION")
    print("=" * 70)
    
    # Check frontend file
    frontend_ok = check_frontend_file()
    
    # Check API functionality
    api_ok = test_tab_reorganization()
    
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS:")
    print(f"   Frontend Implementation: {'✅ OK' if frontend_ok else '❌ ISSUES'}")
    print(f"   API Functionality: {'✅ OK' if api_ok else '❌ ISSUES'}")
    
    if frontend_ok and api_ok:
        print("\n🎉 TAB REORGANIZATION VERIFICATION SUCCESSFUL!")
        print("\n🔧 IF YOU STILL DON'T SEE THE CHANGES:")
        print("   • Hard refresh: Ctrl+F5 or Cmd+Shift+R")
        print("   • Clear browser cache completely")
        print("   • Try incognito/private browsing mode")
        print("   • Check browser console for errors (F12)")
        print("   • Restart the frontend server: npm run dev")
        print("\n🌐 Manual verification: http://localhost:3000/test-cases")
        print("   1. Click on any kernel driver test case")
        print("   2. Look for 'Kernel Driver Files' tab")
        print("   3. Check 'Driver Information' section")
        print("   4. Verify 'Generated Files' with syntax highlighting")
    else:
        print("\n❌ ISSUES DETECTED - NEEDS INVESTIGATION")
    
    return frontend_ok and api_ok

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)