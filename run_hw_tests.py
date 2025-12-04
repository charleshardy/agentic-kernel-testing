#!/usr/bin/env python3
"""Simple test runner for hardware config tests."""

import sys
sys.path.insert(0, '.')

from tests.unit.test_hardware_config import (
    TestHardwareConfigParser,
    TestTestMatrixGenerator,
    TestHardwareCapabilityDetector,
    TestHardwareClassifier
)

def run_tests():
    """Run all hardware config tests."""
    test_classes = [
        TestHardwareConfigParser,
        TestTestMatrixGenerator,
        TestHardwareCapabilityDetector,
        TestHardwareClassifier
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print('='*60)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"✓ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"✗ {method_name}: {e}")
                failed_tests += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed_tests}/{total_tests} passed, {failed_tests} failed")
    print('='*60)
    
    return failed_tests == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
