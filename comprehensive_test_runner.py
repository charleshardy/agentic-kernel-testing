#!/usr/bin/env python3
"""
Comprehensive test runner for checkpoint 47.
This runs all tests without relying on pytest to avoid execution issues.
"""

import sys
import os
import traceback
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Tuple
import time

# Add current directory to Python path
sys.path.insert(0, '.')

class TestResult:
    def __init__(self, name: str, passed: bool, error: str = None, duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.error = error
        self.duration = duration

class TestRunner:
    def __init__(self):
        self.results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def run_test_method(self, test_class, method_name: str) -> TestResult:
        """Run a single test method."""
        start_time = time.time()
        try:
            # Create instance of test class
            instance = test_class()
            
            # Run setup if it exists
            if hasattr(instance, 'setup_method'):
                instance.setup_method()
            
            # Run the test method
            method = getattr(instance, method_name)
            method()
            
            # Run teardown if it exists
            if hasattr(instance, 'teardown_method'):
                instance.teardown_method()
            
            duration = time.time() - start_time
            return TestResult(f"{test_class.__name__}::{method_name}", True, duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            return TestResult(f"{test_class.__name__}::{method_name}", False, error_msg, duration)

    def discover_and_run_unit_tests(self) -> List[TestResult]:
        """Discover and run all unit tests."""
        print("=" * 60)
        print("RUNNING UNIT TESTS")
        print("=" * 60)
        
        results = []
        unit_test_dir = Path("tests/unit")
        
        if not unit_test_dir.exists():
            print("Unit test directory not found")
            return results
        
        # Import all test modules
        for test_file in unit_test_dir.glob("test_*.py"):
            try:
                # Import the module
                module_name = test_file.stem
                spec = importlib.util.spec_from_file_location(module_name, test_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find test classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        attr_name.startswith('Test') and 
                        attr_name != 'TestType'):  # Exclude enum
                        
                        # Find test methods
                        for method_name in dir(attr):
                            if method_name.startswith('test_'):
                                print(f"Running {attr_name}::{method_name}")
                                result = self.run_test_method(attr, method_name)
                                results.append(result)
                                
                                if result.passed:
                                    print(f"  ✅ PASSED ({result.duration:.3f}s)")
                                else:
                                    print(f"  ❌ FAILED ({result.duration:.3f}s)")
                                    print(f"     Error: {result.error}")
                                
            except Exception as e:
                print(f"Error importing {test_file}: {e}")
                traceback.print_exc()
        
        return results

    def run_property_test_simulation(self) -> List[TestResult]:
        """Simulate property-based tests by running them with hypothesis."""
        print("=" * 60)
        print("RUNNING PROPERTY-BASED TESTS SIMULATION")
        print("=" * 60)
        
        results = []
        
        # Import hypothesis for property testing
        try:
            from hypothesis import given, strategies as st
            from hypothesis import settings, Verbosity
            
            # Test property: Test generation quantity
            @given(st.integers(min_value=1, max_value=10))
            @settings(max_examples=100, verbosity=Verbosity.quiet)
            def test_property_test_generation_quantity(num_functions):
                """Property test: For any number of functions, we should generate at least 10 tests per function."""
                from ai_generator.test_generator import AITestGenerator
                from ai_generator.models import CodeAnalysis, Function, RiskLevel
                
                # Create mock functions
                functions = [
                    Function(name=f"func_{i}", file_path=f"file_{i}.c", line_number=i*10)
                    for i in range(num_functions)
                ]
                
                analysis = CodeAnalysis(
                    changed_functions=functions,
                    impact_score=0.5,
                    risk_level=RiskLevel.MEDIUM
                )
                
                generator = AITestGenerator()
                test_cases = generator.generate_test_cases(analysis)
                
                # Property: Should generate at least 10 tests per function
                expected_min_tests = num_functions * 10
                assert len(test_cases) >= expected_min_tests, f"Expected at least {expected_min_tests} tests, got {len(test_cases)}"
            
            # Run the property test
            start_time = time.time()
            try:
                test_property_test_generation_quantity()
                duration = time.time() - start_time
                results.append(TestResult("Property: Test generation quantity", True, duration=duration))
                print(f"✅ Property: Test generation quantity PASSED ({duration:.3f}s)")
            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"{type(e).__name__}: {str(e)}"
                results.append(TestResult("Property: Test generation quantity", False, error_msg, duration))
                print(f"❌ Property: Test generation quantity FAILED ({duration:.3f}s)")
                print(f"   Error: {error_msg}")
            
        except ImportError as e:
            print(f"Hypothesis not available for property testing: {e}")
            # Create a placeholder result
            results.append(TestResult("Property tests", False, "Hypothesis not available"))
        
        return results

    def run_integration_test_simulation(self) -> List[TestResult]:
        """Run integration tests simulation."""
        print("=" * 60)
        print("RUNNING INTEGRATION TESTS SIMULATION")
        print("=" * 60)
        
        results = []
        
        try:
            # Test end-to-end workflow
            from ai_generator.test_generator import AITestGenerator
            from ai_generator.models import CodeAnalysis, Function, RiskLevel
            
            start_time = time.time()
            
            # Create a simple integration test
            generator = AITestGenerator()
            
            # Test that we can create a code analysis
            func = Function(name="test_func", file_path="test.c", line_number=10)
            analysis = CodeAnalysis(
                changed_functions=[func],
                impact_score=0.5,
                risk_level=RiskLevel.MEDIUM
            )
            
            # Test that we can generate test cases
            test_cases = generator.generate_test_cases(analysis)
            
            # Verify we got some test cases
            assert len(test_cases) > 0, "Should generate at least one test case"
            
            duration = time.time() - start_time
            results.append(TestResult("Integration: End-to-end test generation", True, duration=duration))
            print(f"✅ Integration: End-to-end test generation PASSED ({duration:.3f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            results.append(TestResult("Integration: End-to-end test generation", False, error_msg, duration))
            print(f"❌ Integration: End-to-end test generation FAILED ({duration:.3f}s)")
            print(f"   Error: {error_msg}")
        
        return results

    def run_all_tests(self) -> bool:
        """Run all tests and return True if all pass."""
        print("Starting Comprehensive Test Suite")
        print(f"Working directory: {os.getcwd()}")
        print(f"Python version: {sys.version}")
        print()
        
        all_results = []
        
        # Run unit tests
        unit_results = self.discover_and_run_unit_tests()
        all_results.extend(unit_results)
        
        # Run property tests
        property_results = self.run_property_test_simulation()
        all_results.extend(property_results)
        
        # Run integration tests
        integration_results = self.run_integration_test_simulation()
        all_results.extend(integration_results)
        
        # Calculate statistics
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r.passed)
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in all_results)
        
        # Print summary
        print("=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Total duration: {total_duration:.3f}s")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            for result in all_results:
                if not result.passed:
                    print(f"  ❌ {result.name}")
                    if result.error:
                        print(f"     {result.error}")
        
        print("=" * 60)
        if failed_tests == 0:
            print("✅ ALL TESTS PASSED!")
            return True
        else:
            print(f"❌ {failed_tests} TESTS FAILED!")
            return False

def main():
    """Main function."""
    runner = TestRunner()
    success = runner.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)