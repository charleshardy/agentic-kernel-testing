#!/usr/bin/env python3
"""
Simple test to verify execution service works without hanging.
"""

import sys
import time
import requests
from datetime import datetime

def test_api_simple():
    """Test basic API functionality."""
    try:
        print(f"=== SIMPLE API TEST - {datetime.now()} ===")
        
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"   Health: {response.status_code}")
        
        # Test active executions with timeout
        print("2. Testing active executions...")
        response = requests.get("http://localhost:8000/api/v1/execution/active", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   Active executions: {len(data['data']['executions'])}")
        else:
            print(f"   Error: {response.status_code}")
        
        # Generate a simple test
        print("3. Generating test...")
        response = requests.post(
            "http://localhost:8000/api/v1/tests/generate-from-function",
            params={
                'function_name': 'simple_test',
                'file_path': 'test.c',
                'subsystem': 'test',
                'max_tests': 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            plan_id = data['data']['execution_plan_id']
            print(f"   Generated plan: {plan_id[:8]}...")
            
            # Try to start execution
            print("4. Starting execution...")
            
            # Get auth token
            auth_response = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=5
            )
            
            if auth_response.status_code == 200:
                token = auth_response.json()['data']['access_token']
                
                # Start execution
                start_response = requests.post(
                    f"http://localhost:8000/api/v1/execution/{plan_id}/start",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                
                if start_response.status_code == 200:
                    print(f"   Execution started successfully")
                    
                    # Wait a bit and check status
                    print("5. Checking status after 3 seconds...")
                    time.sleep(3)
                    
                    status_response = requests.get(
                        f"http://localhost:8000/api/v1/execution/{plan_id}/status",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"   Status: {status_data['data']['overall_status']}")
                        print(f"   Progress: {status_data['data']['progress']*100:.1f}%")
                        print(f"   Tests: {status_data['data']['completed_tests']}/{status_data['data']['total_tests']}")
                    else:
                        print(f"   Status check failed: {status_response.status_code}")
                else:
                    print(f"   Start failed: {start_response.status_code}")
                    print(f"   Error: {start_response.text}")
            else:
                print(f"   Auth failed: {auth_response.status_code}")
        else:
            print(f"   Generation failed: {response.status_code}")
        
        print("=== TEST COMPLETED ===")
        
    except requests.Timeout:
        print("❌ API call timed out - server may be hanging")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_api_simple()