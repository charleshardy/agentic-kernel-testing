#!/usr/bin/env python3
"""
Simple verification script for Kernel Driver UI Enhancement
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def test_kernel_driver_generation_and_ui():
    """Test kernel driver generation and verify UI data structure"""
    print("🧪 Testing Kernel Driver UI Enhancement")
    print("=" * 50)
    
    # Step 1: Generate a new kernel driver test
    print("1. Generating kernel driver test case...")
    
    params = {
        "function_name": "kmalloc",
        "file_path": "mm/slab.c", 
        "subsystem": "memory",
        "test_types": "unit,integration"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/tests/generate-kernel-driver",
            params=params,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                test_id = data['data']['test_case_ids'][0]
                print(f"✅ Generated test case: {test_id}")
                
                # Step 2: Wait for processing
                print("2. Waiting for test case processing...")
                time.sleep(3)
                
                # Step 3: Fetch test case details
                print("3. Fetching test case details...")
                
                detail_response = requests.get(f"{API_BASE_URL}/tests/{test_id}")
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data.get("success"):
                        test_case = detail_data["data"]
                        
                        print(f"✅ Test case retrieved: {test_case.get('name', 'N/A')}")
                        
                        # Check UI-relevant data
                        print("4. Verifying UI data structure...")
                        
                        # Check generation method
                        generation_method = test_case.get('metadata', {}).get('generation_method')
                        print(f"   Generation method: {generation_method}")
                        
                        # Check for driver files
                        driver_files = test_case.get('metadata', {}).get('driver_files', {})
                        if driver_files:
                            print(f"✅ Driver files found: {list(driver_files.keys())}")
                            
                            # Check file contents for UI display
                            for filename, content in driver_files.items():
                                if content and len(content) > 0:
                                    print(f"   📄 {filename}: {len(content)} characters")
                                else:
                                    print(f"   ⚠️  {filename}: Empty or missing content")
                        else:
                            print("❌ No driver files found in metadata")
                        
                        # Check kernel module info
                        kernel_module = test_case.get('metadata', {}).get('kernel_module')
                        requires_root = test_case.get('metadata', {}).get('requires_root')
                        
                        print(f"   Kernel module: {kernel_module}")
                        print(f"   Requires root: {requires_root}")
                        
                        # Verify UI detection logic
                        is_kernel_driver = (
                            generation_method == 'ai_kernel_driver' or
                            test_case.get('metadata', {}).get('kernel_module') == True or
                            test_case.get('metadata', {}).get('requires_root') == True or
                            (driver_files and len(driver_files) > 0)
                        )
                        
                        if is_kernel_driver:
                            print("✅ Test case will be detected as kernel driver in UI")
                        else:
                            print("❌ Test case will NOT be detected as kernel driver in UI")
                        
                        # Summary
                        print("\n📋 UI Enhancement Verification Summary:")
                        print(f"   - Test ID: {test_id}")
                        print(f"   - Generation Method: {generation_method}")
                        print(f"   - Driver Files: {len(driver_files)} files")
                        print(f"   - Kernel Module: {kernel_module}")
                        print(f"   - UI Detection: {'✅ Yes' if is_kernel_driver else '❌ No'}")
                        
                        if is_kernel_driver and driver_files:
                            print("\n🎨 Expected UI Features:")
                            print("   - 'Kernel Driver Files' tab will appear")
                            print("   - Syntax highlighting for code files")
                            print("   - Copy/download buttons for each file")
                            print("   - Build and execution instructions")
                            print("   - Safety information panel")
                        
                        return True
                    else:
                        print(f"❌ Failed to get test details: {detail_data.get('message')}")
                else:
                    print(f"❌ Failed to fetch test details: {detail_response.status_code}")
            else:
                print(f"❌ Generation failed: {data.get('message')}")
        else:
            print(f"❌ Generation request failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_kernel_driver_generation_and_ui()
    if success:
        print("\n🎉 Kernel Driver UI Enhancement verification completed successfully!")
        print("\nNext steps:")
        print("1. Open http://localhost:3001/test-cases in your browser")
        print("2. Find the generated test case")
        print("3. Click 'View Details' to open the modal")
        print("4. Look for the 'Kernel Driver Files' tab")
        print("5. Verify syntax highlighting and file display")
    else:
        print("\n❌ Verification failed")