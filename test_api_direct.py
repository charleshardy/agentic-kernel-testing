#!/usr/bin/env python3
"""
Test API directly without curl to avoid hanging issues.
"""

import requests
import json
import time

def test_api():
    """Test API endpoints directly."""
    base_url = "http://localhost:8000"
    
    try:
        print("=== Testing API Endpoints ===")
        
        # Test 1: Health check
        print("1. Testing health check...")
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 2: Active executions
        print("\n2. Testing active executions...")
        response = requests.get(f"{base_url}/api/v1/execution/active", timeout=5)
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Active executions: {len(data['data']['executions'])}")
        
        # Test 3: Start execution
        print("\n3. Testing start execution...")
        plan_id = "test-plan-456"
        response = requests.post(f"{base_url}/api/v1/execution/{plan_id}/start", timeout=10)
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Success: {data['success']}")
        print(f"   Message: {data['message']}")
        
        # Test 4: Check execution status
        print("\n4. Testing execution status...")
        time.sleep(2)  # Wait a bit for execution to progress
        response = requests.get(f"{base_url}/api/v1/execution/{plan_id}/status", timeout=5)
        print(f"   Status: {response.status_code}")
        data = response.json()
        if data['success']:
            status_data = data['data']
            print(f"   Overall Status: {status_data['overall_status']}")
            print(f"   Progress: {status_data['progress']*100:.1f}%")
            print(f"   Completed: {status_data['completed_tests']}/{status_data['total_tests']}")
            print(f"   Failed: {status_data['failed_tests']}")
        
        # Test 5: Check active executions again
        print("\n5. Testing active executions after start...")
        response = requests.get(f"{base_url}/api/v1/execution/active", timeout=5)
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Active executions: {len(data['data']['executions'])}")
        
        print("\n✅ All API tests completed successfully!")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out - API might be hanging")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - API server might not be running")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    exit(0 if success else 1)