#!/usr/bin/env python3
"""
Simple test to isolate hanging issue.
"""

import sys
import time

def test_step_by_step():
    """Test imports step by step."""
    
    print("Step 1: Basic imports...")
    from datetime import datetime
    print("✅ datetime OK")
    
    print("Step 2: AI generator models...")
    from ai_generator.models import TestType, TestStatus
    print("✅ TestType, TestStatus OK")
    
    print("Step 3: HardwareConfig...")
    from ai_generator.models import HardwareConfig
    print("✅ HardwareConfig OK")
    
    print("Step 4: Environment...")
    from ai_generator.models import Environment
    print("✅ Environment import OK")
    
    print("Step 5: Creating HardwareConfig...")
    hardware_config = HardwareConfig(
        architecture="x86_64",
        cpu_model="test",
        memory_mb=1024,
        is_virtual=True
    )
    print("✅ HardwareConfig created OK")
    
    print("Step 6: Creating Environment...")
    env = Environment(
        id="test-env",
        config=hardware_config
    )
    print("✅ Environment created OK")
    
    print("Step 7: Testing Environment methods...")
    env_dict = env.to_dict()
    print(f"✅ Environment.to_dict() OK: {type(env_dict)}")
    
    return True

if __name__ == "__main__":
    try:
        print("=== Simple Import Test ===")
        start_time = time.time()
        result = test_step_by_step()
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