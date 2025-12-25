#!/usr/bin/env python3
"""
Test script to verify the AI generation error fix.
This script tests the error handling improvements in the frontend.
"""

import requests
import json
import time

def test_ai_generation_endpoints():
    """Test AI generation endpoints to see error responses"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/tests/generate-from-diff",
        "/tests/generate-from-function", 
        "/tests/generate-kernel-driver"
    ]
    
    print("Testing AI generation endpoints for error handling...")
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}...")
        
        try:
            # Test with invalid parameters to trigger errors
            response = requests.post(
                f"{base_url}{endpoint}",
                params={
                    "function_name": "test_function",
                    "file_path": "test.c",
                    "subsystem": "test",
                    "max_tests": 5
                },
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    print(f"Error structure: {json.dumps(error_data, indent=2)}")
                except:
                    print("Response is not valid JSON")
                    
        except requests.exceptions.ConnectionError:
            print(f"Connection error - server may not be running")
        except requests.exceptions.Timeout:
            print(f"Request timeout")
        except Exception as e:
            print(f"Error: {e}")

def test_frontend_error_handling():
    """Test that frontend can handle various error scenarios"""
    print("\n" + "="*50)
    print("FRONTEND ERROR HANDLING TEST")
    print("="*50)
    
    print("""
The following error scenarios should now be handled properly:

1. Network errors -> "Network error: Unable to connect to server"
2. HTTP 500 errors -> "Server error: HTTP 500"  
3. API errors with message -> Display the actual error message
4. Undefined errors -> "Network or server error occurred"
5. Authentication errors -> Retry with demo token

To test:
1. Start the frontend: cd dashboard && npm run dev
2. Go to Test Cases page
3. Click "AI Generate Tests"
4. Try different scenarios (server down, invalid input, etc.)
5. Verify error messages are clear and not "undefined"
""")

if __name__ == "__main__":
    test_ai_generation_endpoints()
    test_frontend_error_handling()