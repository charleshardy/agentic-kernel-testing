#!/usr/bin/env python3
"""
Direct test runner to diagnose issues.
"""

import sys
import traceback
sys.path.insert(0, '.')

def test_imports():
    """Test if all imports work."""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from ai_generator.models import TestCase, TestType
        print("✅ ai_generator.models imports work")
        
        from config import Settings
        print("✅ config imports work")
        
        import pytest
        print("✅ pytest imports work")
        
        import hypothesis
        print("✅ hypothesis imports work")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_model_creation():
    """Test if we can create model instances."""
    try:
        print("\nTesting model creation...")
        
        from ai_generator.models import TestCase, TestType, HardwareConfig
        
        # Test HardwareConfig
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        print("✅ HardwareConfig creation works")
        
        # Test TestCase
        test = TestCase(
            id="test_001",
            name="Test",
            description="Test",
            test_type=TestType.UNIT,
            target_subsystem="test"
        )
        print("✅ TestCase creation works")
        
        return True
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        traceback.print_exc()
        return False

def run_single_test():
    """Run a single test method directly."""
    try:
        print("\nRunning single test method...")
        
        sys.path.insert(0, 'tests')
        from tests.unit.test_models import TestPeripheral
        
        test_instance = TestPeripheral()
        test_instance.test_peripheral_creation()
        print("✅ Single test method works")
        
        return True
    except Exception as e:
        print(f"❌ Single test error: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("Direct Test Runner - Diagnosing Issues")
    print("=" * 50)
    
    success = True
    
    if not test_imports():
        success = False
    
    if not test_model_creation():
        success = False
    
    if not run_single_test():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All direct tests passed!")
    else:
        print("❌ Some direct tests failed!")
    
    return success

if __name__ == "__main__":
    main()