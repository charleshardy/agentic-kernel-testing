#!/usr/bin/env python3
"""
Test script to generate a kernel driver test and verify the UI displays it correctly.
"""

import requests
import json

def generate_kernel_driver_test():
    """Generate a kernel driver test for UI testing."""
    
    url = "http://localhost:8000/api/v1/tests/generate-kernel-driver"
    
    params = {
        "function_name": "schedule",
        "file_path": "kernel/sched/core.c",
        "subsystem": "scheduler",
        "test_types": ["unit", "integration", "performance"]
    }
    
    print("Generating kernel driver test for UI testing...")
    print(f"Function: {params['function_name']}")
    print(f"File: {params['file_path']}")
    print(f"Subsystem: {params['subsystem']}")
    print(f"Test types: {params['test_types']}")
    
    try:
        response = requests.post(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Kernel driver test generated successfully!")
            print(f"Test case ID: {data['data']['test_case_ids'][0]}")
            print(f"Kernel module: {data['data']['driver_info']['kernel_module']}")
            print(f"Generated files: {', '.join(data['data']['driver_info']['generated_files'])}")
            
            # Get the test case details
            test_id = data['data']['test_case_ids'][0]
            test_url = f"http://localhost:8000/api/v1/tests/{test_id}"
            
            test_response = requests.get(test_url)
            if test_response.status_code == 200:
                test_data = test_response.json()
                print(f"\n📋 Test case details:")
                print(f"Name: {test_data['data']['name']}")
                print(f"Description: {test_data['data']['description']}")
                print(f"Generation method: {test_data['data'].get('generation_info', {}).get('method', 'unknown')}")
                
                # Check if driver files are included
                if 'driver_files' in test_data['data']:
                    print(f"Driver files included: {len(test_data['data']['driver_files'])} files")
                    for filename in test_data['data']['driver_files'].keys():
                        print(f"  - {filename}")
                
                print(f"\n🎯 To test the UI:")
                print(f"1. Open http://localhost:3001/test-cases")
                print(f"2. Find the test case: {test_data['data']['name']}")
                print(f"3. Click 'View Details' to see the enhanced modal")
                print(f"4. Check the 'Kernel Driver Files' tab for syntax-highlighted code")
                
                return True
            else:
                print(f"❌ Failed to get test case details: {test_response.status_code}")
                return False
        else:
            print(f"❌ Failed to generate kernel driver test: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=== Kernel Driver UI Test ===\n")
    
    if generate_kernel_driver_test():
        print(f"\n✅ Test completed successfully!")
        print(f"The enhanced TestCaseModal should now display kernel driver files with syntax highlighting.")
    else:
        print(f"\n❌ Test failed.")