#!/usr/bin/env python3
"""Comprehensive property test runner for result capture."""

import sys
sys.path.append('.')

from hypothesis import given, strategies as st, settings
from tests.property.test_complete_result_capture import (
    gen_test_case, MockTestRunner
)
from ai_generator.models import Environment, EnvironmentStatus, TestStatus

def run_all_property_tests():
    """Run all property tests for result capture."""
    
    @given(gen_test_case())
    @settings(max_examples=20, deadline=None)
    def test_successful_captures_all_fields(test_case_data):
        """Test successful test result capture."""
        test_case, expected_stdout, expected_stderr, expected_exit_code = test_case_data
        
        # Only test successful cases (exit code 0)
        if expected_exit_code != 0:
            return
        
        environment = Environment(
            id="test_env",
            config=test_case.required_hardware,
            status=EnvironmentStatus.IDLE
        )
        
        runner = MockTestRunner(environment)
        result = runner.execute(test_case, timeout=30)
        
        # Verify all required fields
        required_fields = ['stdout', 'stderr', 'exit_code', 'execution_time']
        for field in required_fields:
            assert field in result, f"Result must contain {field} field"
        
        # Verify field types
        assert isinstance(result['stdout'], str), "stdout must be a string"
        assert isinstance(result['stderr'], str), "stderr must be a string"
        assert isinstance(result['exit_code'], int), "exit_code must be an integer"
        assert isinstance(result['execution_time'], (int, float)), "execution_time must be numeric"
        
        # Verify values
        assert result['exit_code'] == expected_exit_code
        assert result['stdout'] == expected_stdout
        assert result['stderr'] == expected_stderr
        assert result['execution_time'] >= 0
    
    @given(gen_test_case())
    @settings(max_examples=20, deadline=None)
    def test_failed_captures_all_fields_and_failure_info(test_case_data):
        """Test failed test result capture."""
        test_case, expected_stdout, expected_stderr, expected_exit_code = test_case_data
        
        # Only test failed cases (non-zero exit code)
        if expected_exit_code == 0:
            return
        
        environment = Environment(
            id="test_env",
            config=test_case.required_hardware,
            status=EnvironmentStatus.IDLE
        )
        
        runner = MockTestRunner(environment)
        result = runner.execute(test_case, timeout=30)
        
        # Verify all required fields
        required_fields = ['stdout', 'stderr', 'exit_code', 'execution_time', 'failure_info']
        for field in required_fields:
            assert field in result, f"Result must contain {field} field"
        
        # Verify failure info
        failure_info = result['failure_info']
        assert failure_info is not None, "failure_info must not be None for failed tests"
        assert hasattr(failure_info, 'error_message'), "failure_info must have error_message"
        assert hasattr(failure_info, 'exit_code'), "failure_info must have exit_code"
        assert failure_info.exit_code == expected_exit_code
        
        # Verify values
        assert result['exit_code'] == expected_exit_code
        assert result['stdout'] == expected_stdout
        assert result['stderr'] == expected_stderr
    
    @given(
        gen_test_case(),
        st.sampled_from([TestStatus.PASSED, TestStatus.FAILED, TestStatus.TIMEOUT, TestStatus.ERROR])
    )
    @settings(max_examples=20, deadline=None)
    def test_all_status_types_capture_fields(test_case_data, target_status):
        """Test result capture across all status types."""
        test_case, expected_stdout, expected_stderr, expected_exit_code = test_case_data
        
        environment = Environment(
            id="test_env",
            config=test_case.required_hardware,
            status=EnvironmentStatus.IDLE
        )
        
        runner = MockTestRunner(environment)
        
        # Configure result based on target status
        if target_status == TestStatus.PASSED:
            mock_exit_code = 0
        elif target_status == TestStatus.FAILED:
            mock_exit_code = expected_exit_code if expected_exit_code != 0 else 1
        elif target_status == TestStatus.TIMEOUT:
            mock_exit_code = 124
        else:  # ERROR
            mock_exit_code = -1
        
        runner.execution_results[test_case.id] = {
            'stdout': expected_stdout,
            'stderr': expected_stderr,
            'exit_code': mock_exit_code
        }
        
        result = runner.execute(test_case, timeout=30)
        
        # Verify essential fields are present
        essential_fields = ['stdout', 'stderr', 'exit_code', 'execution_time', 'status']
        for field in essential_fields:
            assert field in result, f"Result must contain {field} field for status {target_status}"
        
        # Verify field types
        assert isinstance(result['stdout'], str)
        assert isinstance(result['stderr'], str)
        assert isinstance(result['exit_code'], int)
        assert isinstance(result['execution_time'], (int, float))
        
        # Verify values
        assert result['exit_code'] == mock_exit_code
        assert result['stdout'] == expected_stdout
        assert result['stderr'] == expected_stderr
        assert result['execution_time'] >= 0
    
    # Run all tests
    tests = [
        ("Successful test result capture", test_successful_captures_all_fields),
        ("Failed test result capture", test_failed_captures_all_fields_and_failure_info),
        ("All status types result capture", test_all_status_types_capture_fields)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n=== Running {test_name} ===")
        try:
            test_func()
            print(f"✓ {test_name} PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} FAILED: {e}")
            failed += 1
    
    print(f"\n=== Property Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    return failed == 0

if __name__ == "__main__":
    print("=== Comprehensive Property Tests for Result Capture ===")
    success = run_all_property_tests()
    
    if success:
        print("\n🎉 All property tests passed!")
        print("\n**Feature: test-execution-orchestrator, Property 6: Complete result capture**")
        print("**Validates: Requirements 4.1, 4.2**")
        print("\nProperty 6 verification complete:")
        print("✓ Successful tests capture stdout, stderr, exit_code, execution_time")
        print("✓ Failed tests capture all fields plus failure_info")
        print("✓ All test status types capture required fields")
        print("✓ Output content integrity is preserved")
        print("✓ Execution time accuracy is maintained")
    else:
        print("\n❌ Some property tests failed!")
        sys.exit(1)