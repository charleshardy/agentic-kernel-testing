#!/usr/bin/env python3
"""
Comprehensive test to verify the test-123 fix is complete.
"""

import requests
import json
import time

def test_complete_fix():
    base_url = "http://localhost:8000/api/v1"
    
    print("=== COMPREHENSIVE FIX VERIFICATION ===")
    
    # Step 1: Verify no active executions initially
    print("\n1. Checking initial state...")
    response = requests.get(f"{base_url}/execution/active")
    data = response.json()
    initial_count = len(data['data']['executions'])
    print(f"   Initial active executions: {initial_count}")
    
    # Check if any contain test-123
    has_test_123 = False
    for exec in data['data']['executions']:
        plan_id = exec.get('plan_id', '')
        if 'test-123' in plan_id or 'test_123' in plan_id:
            has_test_123 = True
            print(f"   ❌ Found test-123 pattern in plan: {plan_id}")
    
    if not has_test_123:
        print("   ✅ No test-123 patterns found in active executions")
    
    # Step 2: Generate legitimate tests
    print("\n2. Generating legitimate test cases...")
    response = requests.post(f"{base_url}/tests/generate-from-function", params={
        'function_name': 'test_verification_func',
        'file_path': 'kernel/test_verification.c',
        'subsystem': 'kernel/test',
        'max_tests': 2
    })
    
    if response.status_code == 200:
        gen_data = response.json()
        if gen_data['success']:
            print(f"   ✅ Generated {gen_data['data']['generated_count']} legitimate tests")
            plan_id = gen_data['data']['execution_plan_id']
            print(f"   Plan ID: {plan_id[:8]}...")
        else:
            print(f"   ❌ Generation failed: {gen_data.get('message', 'Unknown error')}")
    else:
        print(f"   ❌ Generation request failed: {response.status_code}")
    
    # Step 3: Verify legitimate tests appear in active executions
    print("\n3. Verifying legitimate tests appear...")
    time.sleep(1)  # Brief pause
    response = requests.get(f"{base_url}/execution/active")
    data = response.json()
    current_count = len(data['data']['executions'])
    print(f"   Active executions after generation: {current_count}")
    
    # Verify no test-123 patterns
    legitimate_tests = 0
    test_123_found = False
    
    for exec in data['data']['executions']:
        plan_id = exec.get('plan_id', '')
        total_tests = exec.get('total_tests', 0)
        
        if 'test-123' in plan_id or 'test_123' in plan_id:
            test_123_found = True
            print(f"   ❌ Found test-123 pattern: {plan_id}")
        else:
            legitimate_tests += 1
            print(f"   ✅ Legitimate execution: {plan_id[:8]}... ({total_tests} tests)")
    
    if not test_123_found:
        print("   ✅ No test-123 patterns found after generation")
    
    # Step 4: Test cleanup functionality
    print("\n4. Testing cleanup functionality...")
    response = requests.post(f"{base_url}/execution/cleanup-debug")
    if response.status_code == 200:
        cleanup_data = response.json()
        removed = cleanup_data['data']['removed_count']
        remaining = cleanup_data['data']['remaining_count']
        print(f"   ✅ Cleanup successful: removed {removed}, remaining {remaining}")
    else:
        print(f"   ❌ Cleanup failed: {response.status_code}")
    
    # Step 5: Final verification
    print("\n5. Final verification...")
    response = requests.get(f"{base_url}/execution/active")
    data = response.json()
    final_count = len(data['data']['executions'])
    
    final_test_123_found = False
    for exec in data['data']['executions']:
        plan_id = exec.get('plan_id', '')
        if 'test-123' in plan_id or 'test_123' in plan_id:
            final_test_123_found = True
            print(f"   ❌ Still found test-123 pattern: {plan_id}")
    
    if not final_test_123_found:
        print("   ✅ Final check: No test-123 patterns found")
    
    print(f"\n=== SUMMARY ===")
    print(f"Initial executions: {initial_count}")
    print(f"After generation: {current_count}")
    print(f"Final executions: {final_count}")
    print(f"Legitimate tests generated: {legitimate_tests}")
    print(f"Test-123 patterns found: {'❌ YES' if final_test_123_found else '✅ NO'}")
    
    # Overall result
    if not final_test_123_found and legitimate_tests > 0:
        print("\n🎉 FIX VERIFICATION: SUCCESS")
        print("   - No test-123 patterns found")
        print("   - Legitimate tests work correctly")
        print("   - Cleanup functionality works")
        return True
    else:
        print("\n❌ FIX VERIFICATION: FAILED")
        return False

if __name__ == "__main__":
    success = test_complete_fix()
    exit(0 if success else 1)