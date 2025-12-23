#!/usr/bin/env python3
"""
Test script to identify and fix API hanging issues.
"""

import sys
import traceback
import time

def test_imports():
    """Test all imports that might cause hanging."""
    print("Testing imports...")
    
    try:
        print("1. Testing basic imports...")
        from datetime import datetime
        from typing import Dict, List, Optional, Any
        print("✅ Basic imports OK")
        
        print("2. Testing AI generator models...")
        from ai_generator.models import TestCase, TestResult, TestStatus, Environment
        print("✅ AI generator models OK")
        
        print("3. Testing execution service...")
        from execution.execution_service import ExecutionService, get_execution_service
        print("✅ Execution service import OK")
        
        print("4. Testing execution service initialization...")
        service = ExecutionService()
        print("✅ Execution service initialization OK")
        
        print("5. Testing basic service methods...")
        active = service.get_active_executions()
        print(f"✅ get_active_executions returned {len(active)} executions")
        
        print("6. Testing API router imports...")
        from api.routers.execution import get_execution_service as api_get_service
        print("✅ API router imports OK")
        
        print("7. Testing API service call...")
        api_service = api_get_service()
        api_active = api_service.get_active_executions()
        print(f"✅ API service call returned {len(api_active)} executions")
        
        return True
        
    except Exception as e:
        print(f"❌ Import/initialization failed: {e}")
        traceback.print_exc()
        return False

def test_execution_status_endpoint():
    """Test the specific endpoint that's hanging."""
    print("\nTesting execution status endpoint logic...")
    
    try:
        from execution.execution_service import get_execution_service
        from api.routers.tests import execution_plans, submitted_tests
        
        service = get_execution_service()
        
        # Test with a fake plan ID
        fake_plan_id = "test-plan-123"
        
        print(f"Testing get_execution_status with fake ID: {fake_plan_id}")
        status = service.get_execution_status(fake_plan_id)
        print(f"✅ get_execution_status returned: {status}")
        
        print(f"Current execution_plans count: {len(execution_plans)}")
        print(f"Current submitted_tests count: {len(submitted_tests)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Execution status test failed: {e}")
        traceback.print_exc()
        return False

def test_mock_execution():
    """Test mock execution to see if it hangs."""
    print("\nTesting mock execution...")
    
    try:
        from ai_generator.models import TestCase, TestType, Environment, HardwareConfig
        from execution.runners.mock_runner import MockTestRunner
        
        # Create a test environment
        hardware_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024,
            is_virtual=True
        )
        
        env = Environment(
            id="test-env",
            config=hardware_config,
            status="idle"
        )
        
        # Create a test case
        test_case = TestCase(
            id="test-001",
            name="Test mock execution",
            description="Test to verify mock execution works",
            test_type=TestType.UNIT,
            target_subsystem="test",
            execution_time_estimate=5
        )
        
        # Create mock runner and execute
        runner = MockTestRunner(env)
        print("Starting mock execution...")
        start_time = time.time()
        
        result = runner.execute(test_case, timeout=10)
        
        end_time = time.time()
        print(f"✅ Mock execution completed in {end_time - start_time:.2f}s")
        print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock execution test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=== API Hang Fix Test ===")
    
    tests = [
        ("Import Tests", test_imports),
        ("Execution Status Endpoint", test_execution_status_endpoint),
        ("Mock Execution", test_mock_execution)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n=== Test Results ===")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! API should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)