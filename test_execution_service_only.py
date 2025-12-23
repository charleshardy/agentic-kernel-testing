#!/usr/bin/env python3
"""
Test execution service specifically to find hanging issue.
"""

import sys
import time

def test_execution_service():
    """Test execution service step by step."""
    
    print("Step 1: Basic imports...")
    from datetime import datetime
    from typing import Dict, List, Optional, Any
    print("✅ Basic imports OK")
    
    print("Step 2: AI generator models...")
    from ai_generator.models import TestCase, TestResult, TestStatus, Environment, HardwareConfig
    print("✅ AI generator models OK")
    
    print("Step 3: Execution service imports...")
    try:
        from execution.test_runner import TestRunner
        print("✅ TestRunner import OK")
    except Exception as e:
        print(f"⚠️  TestRunner import failed: {e}")
    
    try:
        from execution.environment_manager import EnvironmentManager
        print("✅ EnvironmentManager import OK")
    except Exception as e:
        print(f"⚠️  EnvironmentManager import failed: {e}")
    
    try:
        from execution.runner_factory import get_runner_factory
        print("✅ runner_factory import OK")
    except Exception as e:
        print(f"⚠️  runner_factory import failed: {e}")
    
    print("Step 4: ExecutionService import...")
    from execution.execution_service import ExecutionService
    print("✅ ExecutionService import OK")
    
    print("Step 5: Creating ExecutionService (this might hang)...")
    start_time = time.time()
    service = ExecutionService()
    end_time = time.time()
    print(f"✅ ExecutionService created in {end_time - start_time:.2f}s")
    
    print("Step 6: Testing basic methods...")
    active = service.get_active_executions()
    print(f"✅ get_active_executions returned {len(active)} executions")
    
    return True

if __name__ == "__main__":
    try:
        print("=== Execution Service Test ===")
        start_time = time.time()
        result = test_execution_service()
        end_time = time.time()
        
        if result:
            print(f"\n🎉 All steps completed in {end_time - start_time:.2f}s")
        else:
            print(f"\n❌ Test failed after {end_time - start_time:.2f}s")
            
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)