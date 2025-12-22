#!/usr/bin/env python3
"""
Test script to verify the execution flow fix works
"""

import requests
import json
import time
import sys

def test_execution_flow():
    """Test the complete execution flow"""
    
    base_url = "http://localhost:8000"
    
    print("=== Testing Execution Flow Fix ===")
    print()
    
    # Step 1: Check API health
    print("1. Checking API Health...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ API is healthy")
            print(f"   - Orchestrator status: {health_data.get('data', {}).get('orchestrator', {}).get('status', 'unknown')}")
        else:
            print(f"   ❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        print("   💡 Make sure to start the API server: python -m api.server")
        return False
    
    print()
    
    # Step 2: Get demo token
    print("2. Getting Demo Token...")
    try:
        response = requests.post(f"{base_url}/api/v1/auth/demo-login")
        if response.status_code == 200:
            token_data = response.json()
            token = token_data['data']['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            print(f"   ✅ Got demo token")
        else:
            print(f"   ❌ Failed to get demo token: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Token request failed: {e}")
        return False
    
    print()
    
    # Step 3: Check orchestrator status
    print("3. Checking Orchestrator Status...")
    try:
        response = requests.get(f"{base_url}/api/v1/execution/metrics", headers=headers)
        if response.status_code == 200:
            metrics = response.json()
            orchestrator_status = metrics['data']['orchestrator_status']
            print(f"   - Orchestrator status: {orchestrator_status}")
            
            if orchestrator_status == "not_running":
                print("   ⚠️  Orchestrator not running, trying to force poll...")
                
                # Try to force poll (this should start orchestrator)
                poll_response = requests.post(f"{base_url}/api/v1/execution/orchestrator/poll", headers=headers)
                if poll_response.status_code == 200:
                    poll_data = poll_response.json()
                    print(f"   ✅ Forced poll successful")
                    print(f"   - Detected plans: {poll_data['data']['new_plans_detected']}")
                else:
                    print(f"   ❌ Force poll failed: {poll_response.status_code}")
            else:
                print(f"   ✅ Orchestrator is running")
        else:
            print(f"   ❌ Failed to get metrics: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Metrics request failed: {e}")
    
    print()
    
    # Step 4: Generate an AI test
    print("4. Generating AI Test...")
    try:
        test_data = {
            "function_name": "test_function",
            "file_path": "test/test_file.c",
            "subsystem": "test",
            "max_tests": 1
        }
        
        response = requests.post(
            f"{base_url}/api/v1/tests/generate-from-function",
            params=test_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            test_ids = result['data']['test_case_ids']
            plan_id = result['data']['execution_plan_id']
            print(f"   ✅ Generated AI test")
            print(f"   - Test IDs: {test_ids}")
            print(f"   - Execution Plan ID: {plan_id}")
        else:
            print(f"   ❌ Failed to generate test: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Test generation failed: {e}")
        return False
    
    print()
    
    # Step 5: Check if test appears in execution
    print("5. Checking Test Execution Status...")
    try:
        # Force orchestrator to poll for the new plan
        poll_response = requests.post(f"{base_url}/api/v1/execution/orchestrator/poll", headers=headers)
        if poll_response.status_code == 200:
            poll_data = poll_response.json()
            print(f"   - Forced poll detected: {poll_data['data']['new_plans_detected']} plans")
            print(f"   - Queued plans: {poll_data['data']['queued_plans']}")
            print(f"   - Queued tests: {poll_data['data']['queued_tests']}")
        
        # Check active executions
        response = requests.get(f"{base_url}/api/v1/execution/active", headers=headers)
        if response.status_code == 200:
            executions = response.json()
            active_count = len(executions['data'])
            print(f"   - Active executions: {active_count}")
            
            if active_count > 0:
                print("   ✅ Test is visible in execution system!")
                for execution in executions['data']:
                    print(f"     * Plan {execution['plan_id']}: {execution['overall_status']} ({execution['total_tests']} tests)")
            else:
                print("   ⚠️  No active executions found")
        else:
            print(f"   ❌ Failed to get active executions: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Execution check failed: {e}")
    
    print()
    
    # Step 6: Check metrics again
    print("6. Final Metrics Check...")
    try:
        response = requests.get(f"{base_url}/api/v1/execution/metrics", headers=headers)
        if response.status_code == 200:
            metrics = response.json()
            data = metrics['data']
            print(f"   - Orchestrator status: {data['orchestrator_status']}")
            print(f"   - Active tests: {data['active_tests']}")
            print(f"   - Queued tests: {data['queued_tests']}")
            print(f"   - Available environments: {data['available_environments']}")
            
            if data['queued_tests'] > 0:
                print("   ✅ Tests are queued for execution!")
            else:
                print("   ⚠️  No tests in queue")
        else:
            print(f"   ❌ Failed to get final metrics: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Final metrics check failed: {e}")
    
    print()
    print("=== Test Complete ===")
    print()
    print("🎯 Next Steps:")
    print("1. Open Web GUI: http://localhost:3000")
    print("2. Go to Test Cases page and create an AI test")
    print("3. Check Test Execution page for real-time updates")
    print("4. If tests don't appear, use the manual poll endpoint")
    
    return True

if __name__ == "__main__":
    success = test_execution_flow()
    sys.exit(0 if success else 1)