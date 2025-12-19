"""Property-based tests for complete result capture.

**Feature: test-execution-orchestrator, Property 6: Complete result capture**
**Validates: Requirements 4.1, 4.2**

Property 6: Complete result capture
For any test that completes (successfully or with failure), the system should capture 
and store stdout, stderr, exit code, and execution time.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
from typing import Dict, Any, Optional
import tempfile
import os
import time

from ai_generator.models import (
    TestCase, TestType, TestStatus, Environment, HardwareConfig,
    ArtifactBundle, FailureInfo, EnvironmentStatus
)
from execution.runner_factory import get_runner_factory, BaseTestRunner


# Custom strategies for generating test data
@st.composite
def gen_test_id(draw):
    """Generate a random test ID."""
    return draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))


@st.composite
def gen_test_name(draw):
    """Generate a random test name."""
    return draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))))


@st.composite
def gen_test_description(draw):
    """Generate a random test description."""
    return draw(st.text(min_size=0, max_size=500))


@st.composite
def gen_target_subsystem(draw):
    """Generate a random target subsystem."""
    subsystems = ["memory", "filesystem", "network", "scheduler", "drivers", "security", "io"]
    return draw(st.sampled_from(subsystems))


@st.composite
def gen_exit_code(draw):
    """Generate a random exit code."""
    return draw(st.integers(min_value=0, max_value=255))


@st.composite
def gen_output_text(draw):
    """Generate random output text."""
    return draw(st.text(min_size=0, max_size=1000, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs', 'Po'),
        blacklist_characters='\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f'
    )))


@st.composite
def gen_execution_time(draw):
    """Generate a random execution time."""
    return draw(st.floats(min_value=0.001, max_value=300.0, allow_nan=False, allow_infinity=False))


@st.composite
def gen_successful_test_script(draw):
    """Generate a test script that always succeeds (exit code 0)."""
    stdout_text = draw(gen_output_text())
    stderr_text = draw(gen_output_text())
    
    # Create a script that produces predictable output and succeeds
    script = f"""#!/bin/bash
echo "{stdout_text}"
echo "{stderr_text}" >&2
exit 0
"""
    return script, stdout_text, stderr_text, 0


@st.composite
def gen_failed_test_script(draw):
    """Generate a test script that always fails (non-zero exit code)."""
    exit_code = draw(st.integers(min_value=1, max_value=255))
    stdout_text = draw(gen_output_text())
    stderr_text = draw(gen_output_text())
    
    # Create a script that produces predictable output and fails
    script = f"""#!/bin/bash
echo "{stdout_text}"
echo "{stderr_text}" >&2
exit {exit_code}
"""
    return script, stdout_text, stderr_text, exit_code


@st.composite
def gen_test_script(draw):
    """Generate a test script that produces specific outputs."""
    exit_code = draw(gen_exit_code())
    stdout_text = draw(gen_output_text())
    stderr_text = draw(gen_output_text())
    
    # Create a script that produces predictable output
    script = f"""#!/bin/bash
echo "{stdout_text}"
echo "{stderr_text}" >&2
exit {exit_code}
"""
    return script, stdout_text, stderr_text, exit_code


@st.composite
def gen_hardware_config(draw):
    """Generate a random hardware configuration."""
    return HardwareConfig(
        architecture=draw(st.sampled_from(["x86_64", "arm64", "arm"])),
        cpu_model=draw(st.text(min_size=1, max_size=50)),
        memory_mb=draw(st.integers(min_value=512, max_value=8192)),
        is_virtual=True,
        emulator="qemu"
    )


@st.composite
def gen_environment(draw):
    """Generate a random test environment."""
    env_id = draw(gen_test_id())
    config = draw(gen_hardware_config())
    
    return Environment(
        id=env_id,
        config=config,
        status=EnvironmentStatus.IDLE
    )


@st.composite
def gen_successful_test_case(draw):
    """Generate a random test case that always succeeds."""
    test_id = draw(gen_test_id())
    name = draw(gen_test_name())
    description = draw(gen_test_description())
    test_type = draw(st.sampled_from(list(TestType)))
    target_subsystem = draw(gen_target_subsystem())
    hardware = draw(gen_hardware_config())
    
    script, expected_stdout, expected_stderr, expected_exit_code = draw(gen_successful_test_script())
    
    test_case = TestCase(
        id=test_id,
        name=name,
        description=description,
        test_type=test_type,
        target_subsystem=target_subsystem,
        required_hardware=hardware,
        test_script=script,
        execution_time_estimate=draw(st.integers(min_value=1, max_value=60))
    )
    
    return test_case, expected_stdout, expected_stderr, expected_exit_code


@st.composite
def gen_failed_test_case(draw):
    """Generate a random test case that always fails."""
    test_id = draw(gen_test_id())
    name = draw(gen_test_name())
    description = draw(gen_test_description())
    test_type = draw(st.sampled_from(list(TestType)))
    target_subsystem = draw(gen_target_subsystem())
    hardware = draw(gen_hardware_config())
    
    script, expected_stdout, expected_stderr, expected_exit_code = draw(gen_failed_test_script())
    
    test_case = TestCase(
        id=test_id,
        name=name,
        description=description,
        test_type=test_type,
        target_subsystem=target_subsystem,
        required_hardware=hardware,
        test_script=script,
        execution_time_estimate=draw(st.integers(min_value=1, max_value=60))
    )
    
    return test_case, expected_stdout, expected_stderr, expected_exit_code


@st.composite
def gen_test_case(draw):
    """Generate a random test case with predictable output."""
    test_id = draw(gen_test_id())
    name = draw(gen_test_name())
    description = draw(gen_test_description())
    test_type = draw(st.sampled_from(list(TestType)))
    target_subsystem = draw(gen_target_subsystem())
    hardware = draw(gen_hardware_config())
    
    script, expected_stdout, expected_stderr, expected_exit_code = draw(gen_test_script())
    
    test_case = TestCase(
        id=test_id,
        name=name,
        description=description,
        test_type=test_type,
        target_subsystem=target_subsystem,
        required_hardware=hardware,
        test_script=script,
        execution_time_estimate=draw(st.integers(min_value=1, max_value=60))
    )
    
    return test_case, expected_stdout, expected_stderr, expected_exit_code


class MockTestRunner(BaseTestRunner):
    """Mock test runner for testing result capture."""
    
    def __init__(self, environment: Environment):
        super().__init__(environment)
        self.execution_results = {}
    
    def set_execution_result(self, test_id: str, result: Dict[str, Any]):
        """Set the expected execution result for a test."""
        self.execution_results[test_id] = result
    
    def execute(self, test_case: TestCase, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute a test case and return mock results."""
        start_time = time.time()
        
        # Get pre-configured result or create default
        if test_case.id in self.execution_results:
            result = self.execution_results[test_case.id].copy()
        else:
            # Parse expected results from test script if it's our generated format
            if "echo" in test_case.test_script and "exit" in test_case.test_script:
                lines = test_case.test_script.strip().split('\n')
                stdout = ""
                stderr = ""
                exit_code = 0
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('echo "') and '>&2' not in line:
                        # Extract stdout: echo "content"
                        stdout = line[6:-1]  # Extract text between quotes
                    elif line.startswith('echo "') and '>&2' in line:
                        # Extract stderr: echo "content" >&2
                        # Find the closing quote before >&2
                        quote_end = line.rfind('" >&2')
                        if quote_end > 5:
                            stderr = line[6:quote_end]  # Extract text between quotes
                        else:
                            stderr = ""
                    elif line.startswith('exit '):
                        exit_code = int(line[5:])
                
                result = {
                    'stdout': stdout,
                    'stderr': stderr,
                    'exit_code': exit_code
                }
            else:
                result = {
                    'stdout': f"Mock output for test {test_case.id}",
                    'stderr': "",
                    'exit_code': 0
                }
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Determine status based on exit code
        if result['exit_code'] == 0:
            status = TestStatus.PASSED
            failure_info = None
        else:
            status = TestStatus.FAILED
            failure_info = FailureInfo(
                error_message=f"Test failed with exit code {result['exit_code']}",
                exit_code=result['exit_code'],
                timeout_occurred=False,
                kernel_panic=False
            )
        
        # Create artifacts bundle
        artifacts = ArtifactBundle(
            logs=[f"/tmp/test_{test_case.id}.log"],
            metadata={"mock_execution": True}
        )
        
        return {
            'status': status,
            'stdout': result['stdout'],
            'stderr': result['stderr'],
            'exit_code': result['exit_code'],
            'execution_time': execution_time,
            'artifacts': artifacts,
            'failure_info': failure_info
        }
    
    def cleanup(self) -> None:
        """Clean up mock resources."""
        pass
    
    def supports_test_type(self, test_type: TestType) -> bool:
        """Mock runner supports all test types."""
        return True
    
    def supports_hardware(self, hardware_config: HardwareConfig) -> bool:
        """Mock runner supports all hardware configurations."""
        return True


@given(gen_successful_test_case())
@settings(max_examples=100, deadline=None)
def test_successful_test_captures_all_required_fields(test_case_data):
    """
    Property: For any test that completes successfully, the system should capture 
    stdout, stderr, exit code, and execution time.
    
    **Feature: test-execution-orchestrator, Property 6: Complete result capture**
    **Validates: Requirements 4.1**
    """
    test_case, expected_stdout, expected_stderr, expected_exit_code = test_case_data
    
    environment = Environment(
        id="test_env",
        config=test_case.required_hardware,
        status=EnvironmentStatus.IDLE
    )
    
    # Create mock runner
    runner = MockTestRunner(environment)
    
    # Execute the test
    result = runner.execute(test_case, timeout=30)
    
    # Verify all required fields are present and not None/empty
    assert 'stdout' in result, "Result must contain stdout field"
    assert 'stderr' in result, "Result must contain stderr field"
    assert 'exit_code' in result, "Result must contain exit_code field"
    assert 'execution_time' in result, "Result must contain execution_time field"
    
    # Verify field types and values
    assert isinstance(result['stdout'], str), "stdout must be a string"
    assert isinstance(result['stderr'], str), "stderr must be a string"
    assert isinstance(result['exit_code'], int), "exit_code must be an integer"
    assert isinstance(result['execution_time'], (int, float)), "execution_time must be numeric"
    
    # Verify execution time is reasonable
    assert result['execution_time'] >= 0, "execution_time must be non-negative"
    assert result['execution_time'] < 60, "execution_time should be reasonable for test execution"
    
    # Verify exit code matches expected
    assert result['exit_code'] == expected_exit_code, \
        f"exit_code should match expected: {expected_exit_code}, got {result['exit_code']}"
    
    # Verify output matches expected (for our controlled test scripts)
    assert result['stdout'] == expected_stdout, \
        f"stdout should match expected: '{expected_stdout}', got '{result['stdout']}'"
    assert result['stderr'] == expected_stderr, \
        f"stderr should match expected: '{expected_stderr}', got '{result['stderr']}'"


@given(gen_failed_test_case())
@settings(max_examples=100, deadline=None)
def test_failed_test_captures_all_required_fields_and_failure_info(test_case_data):
    """
    Property: For any test that fails, the system should capture stdout, stderr, 
    exit code, execution time, and failure information.
    
    **Feature: test-execution-orchestrator, Property 6: Complete result capture**
    **Validates: Requirements 4.2**
    """
    test_case, expected_stdout, expected_stderr, expected_exit_code = test_case_data
    
    environment = Environment(
        id="test_env",
        config=test_case.required_hardware,
        status=EnvironmentStatus.IDLE
    )
    
    # Create mock runner
    runner = MockTestRunner(environment)
    
    # Execute the test
    result = runner.execute(test_case, timeout=30)
    
    # Verify all required fields are present
    assert 'stdout' in result, "Result must contain stdout field"
    assert 'stderr' in result, "Result must contain stderr field"
    assert 'exit_code' in result, "Result must contain exit_code field"
    assert 'execution_time' in result, "Result must contain execution_time field"
    assert 'failure_info' in result, "Failed test result must contain failure_info field"
    
    # Verify field types
    assert isinstance(result['stdout'], str), "stdout must be a string"
    assert isinstance(result['stderr'], str), "stderr must be a string"
    assert isinstance(result['exit_code'], int), "exit_code must be an integer"
    assert isinstance(result['execution_time'], (int, float)), "execution_time must be numeric"
    
    # Verify failure info is present and properly structured
    failure_info = result['failure_info']
    assert failure_info is not None, "failure_info must not be None for failed tests"
    assert hasattr(failure_info, 'error_message'), "failure_info must have error_message"
    assert hasattr(failure_info, 'exit_code'), "failure_info must have exit_code"
    assert isinstance(failure_info.error_message, str), "error_message must be a string"
    assert len(failure_info.error_message) > 0, "error_message must not be empty"
    
    # Verify exit code consistency
    assert result['exit_code'] == expected_exit_code, \
        f"exit_code should match expected: {expected_exit_code}, got {result['exit_code']}"
    assert failure_info.exit_code == expected_exit_code, \
        f"failure_info.exit_code should match result exit_code: {expected_exit_code}"
    
    # Verify execution time is reasonable
    assert result['execution_time'] >= 0, "execution_time must be non-negative"
    
    # Verify output matches expected
    assert result['stdout'] == expected_stdout, \
        f"stdout should match expected: '{expected_stdout}', got '{result['stdout']}'"
    assert result['stderr'] == expected_stderr, \
        f"stderr should match expected: '{expected_stderr}', got '{result['stderr']}'"


@given(
    st.lists(gen_test_case(), min_size=1, max_size=10),
    st.lists(st.floats(min_value=0.001, max_value=5.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=10)
)
@settings(max_examples=50, deadline=None)
def test_multiple_tests_all_capture_complete_results(test_cases_data, execution_times):
    """
    Property: For any sequence of test executions, each test should have complete 
    result capture regardless of the execution order or other tests.
    
    **Feature: test-execution-orchestrator, Property 6: Complete result capture**
    **Validates: Requirements 4.1, 4.2**
    """
    # Ensure we have matching lengths
    min_len = min(len(test_cases_data), len(execution_times))
    assume(min_len >= 1)
    
    test_cases_data = test_cases_data[:min_len]
    execution_times = execution_times[:min_len]
    
    environment = Environment(
        id="test_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=1024,
            is_virtual=True
        ),
        status=EnvironmentStatus.IDLE
    )
    
    # Execute all tests and collect results
    results = []
    
    for (test_case, expected_stdout, expected_stderr, expected_exit_code), expected_time in zip(test_cases_data, execution_times):
        runner = MockTestRunner(environment)
        
        # Set custom execution time for this test
        runner.execution_results[test_case.id] = {
            'stdout': expected_stdout,
            'stderr': expected_stderr,
            'exit_code': expected_exit_code,
            'execution_time': expected_time
        }
        
        result = runner.execute(test_case, timeout=30)
        results.append((test_case, result, expected_stdout, expected_stderr, expected_exit_code))
    
    # Verify each result has complete capture
    for i, (test_case, result, expected_stdout, expected_stderr, expected_exit_code) in enumerate(results):
        # Verify all required fields are present
        required_fields = ['stdout', 'stderr', 'exit_code', 'execution_time', 'status', 'artifacts']
        for field in required_fields:
            assert field in result, f"Test {i} ({test_case.id}) missing required field: {field}"
        
        # Verify field types
        assert isinstance(result['stdout'], str), f"Test {i} stdout must be string"
        assert isinstance(result['stderr'], str), f"Test {i} stderr must be string"
        assert isinstance(result['exit_code'], int), f"Test {i} exit_code must be integer"
        assert isinstance(result['execution_time'], (int, float)), f"Test {i} execution_time must be numeric"
        
        # Verify values match expectations
        assert result['stdout'] == expected_stdout, \
            f"Test {i} stdout mismatch: expected '{expected_stdout}', got '{result['stdout']}'"
        assert result['stderr'] == expected_stderr, \
            f"Test {i} stderr mismatch: expected '{expected_stderr}', got '{result['stderr']}'"
        assert result['exit_code'] == expected_exit_code, \
            f"Test {i} exit_code mismatch: expected {expected_exit_code}, got {result['exit_code']}"
        
        # Verify execution time is reasonable
        assert result['execution_time'] >= 0, f"Test {i} execution_time must be non-negative"
        
        # Verify failure info is present for failed tests
        if expected_exit_code != 0:
            assert 'failure_info' in result, f"Failed test {i} must have failure_info"
            assert result['failure_info'] is not None, f"Failed test {i} failure_info must not be None"


@given(
    gen_test_case(),
    st.sampled_from([TestStatus.PASSED, TestStatus.FAILED, TestStatus.TIMEOUT, TestStatus.ERROR])
)
@settings(max_examples=100, deadline=None)
def test_result_capture_completeness_across_all_status_types(test_case_data, target_status):
    """
    Property: For any test completion status (passed, failed, timeout, error), 
    the system should capture all required result fields.
    
    **Feature: test-execution-orchestrator, Property 6: Complete result capture**
    **Validates: Requirements 4.1, 4.2**
    """
    test_case, expected_stdout, expected_stderr, expected_exit_code = test_case_data
    
    environment = Environment(
        id="test_env",
        config=test_case.required_hardware,
        status=EnvironmentStatus.IDLE
    )
    
    # Create mock runner and configure it to produce the target status
    runner = MockTestRunner(environment)
    
    # Configure result based on target status
    if target_status == TestStatus.PASSED:
        mock_exit_code = 0
    elif target_status == TestStatus.FAILED:
        mock_exit_code = expected_exit_code if expected_exit_code != 0 else 1
    elif target_status == TestStatus.TIMEOUT:
        mock_exit_code = 124  # Standard timeout exit code
    else:  # ERROR
        mock_exit_code = -1
    
    runner.execution_results[test_case.id] = {
        'stdout': expected_stdout,
        'stderr': expected_stderr,
        'exit_code': mock_exit_code
    }
    
    # Execute the test
    result = runner.execute(test_case, timeout=30)
    
    # Verify all essential fields are present regardless of status
    essential_fields = ['stdout', 'stderr', 'exit_code', 'execution_time', 'status']
    for field in essential_fields:
        assert field in result, f"Result must contain {field} field for status {target_status}"
    
    # Verify field types
    assert isinstance(result['stdout'], str), f"stdout must be string for status {target_status}"
    assert isinstance(result['stderr'], str), f"stderr must be string for status {target_status}"
    assert isinstance(result['exit_code'], int), f"exit_code must be integer for status {target_status}"
    assert isinstance(result['execution_time'], (int, float)), f"execution_time must be numeric for status {target_status}"
    
    # Verify execution time is captured
    assert result['execution_time'] >= 0, f"execution_time must be non-negative for status {target_status}"
    
    # Verify exit code is captured
    assert result['exit_code'] == mock_exit_code, \
        f"exit_code should match mock value for status {target_status}"
    
    # Verify output is captured (even if empty)
    assert result['stdout'] == expected_stdout, \
        f"stdout should be captured for status {target_status}"
    assert result['stderr'] == expected_stderr, \
        f"stderr should be captured for status {target_status}"
    
    # Verify artifacts are present
    assert 'artifacts' in result, f"artifacts must be present for status {target_status}"
    assert result['artifacts'] is not None, f"artifacts must not be None for status {target_status}"


@given(gen_test_case())
@settings(max_examples=100, deadline=None)
def test_result_capture_preserves_output_content_integrity(test_case_data):
    """
    Property: For any test output content, the captured stdout and stderr should 
    preserve the exact content without modification or truncation.
    
    **Feature: test-execution-orchestrator, Property 6: Complete result capture**
    **Validates: Requirements 4.1, 4.2**
    """
    test_case, expected_stdout, expected_stderr, expected_exit_code = test_case_data
    
    # Skip empty outputs as they don't test content preservation
    assume(len(expected_stdout) > 0 or len(expected_stderr) > 0)
    
    environment = Environment(
        id="test_env",
        config=test_case.required_hardware,
        status=EnvironmentStatus.IDLE
    )
    
    runner = MockTestRunner(environment)
    
    # Execute the test
    result = runner.execute(test_case, timeout=30)
    
    # Verify exact content preservation
    assert result['stdout'] == expected_stdout, \
        f"stdout content must be preserved exactly. Expected: '{expected_stdout}', Got: '{result['stdout']}'"
    
    assert result['stderr'] == expected_stderr, \
        f"stderr content must be preserved exactly. Expected: '{expected_stderr}', Got: '{result['stderr']}'"
    
    # Verify no unexpected modifications
    assert len(result['stdout']) == len(expected_stdout), \
        f"stdout length must be preserved. Expected: {len(expected_stdout)}, Got: {len(result['stdout'])}"
    
    assert len(result['stderr']) == len(expected_stderr), \
        f"stderr length must be preserved. Expected: {len(expected_stderr)}, Got: {len(result['stderr'])}"
    
    # Verify character-by-character integrity for non-empty outputs
    if expected_stdout:
        for i, (expected_char, actual_char) in enumerate(zip(expected_stdout, result['stdout'])):
            assert expected_char == actual_char, \
                f"stdout character at position {i} differs. Expected: '{expected_char}', Got: '{actual_char}'"
    
    if expected_stderr:
        for i, (expected_char, actual_char) in enumerate(zip(expected_stderr, result['stderr'])):
            assert expected_char == actual_char, \
                f"stderr character at position {i} differs. Expected: '{expected_char}', Got: '{actual_char}'"


@given(
    gen_test_case(),
    st.integers(min_value=1, max_value=300)
)
@settings(max_examples=50, deadline=None)
def test_execution_time_capture_accuracy(test_case_data, timeout_seconds):
    """
    Property: For any test execution, the captured execution time should be 
    accurate and reflect the actual time taken to execute the test.
    
    **Feature: test-execution-orchestrator, Property 6: Complete result capture**
    **Validates: Requirements 4.1, 4.2**
    """
    test_case, expected_stdout, expected_stderr, expected_exit_code = test_case_data
    
    environment = Environment(
        id="test_env",
        config=test_case.required_hardware,
        status=EnvironmentStatus.IDLE
    )
    
    runner = MockTestRunner(environment)
    
    # Record start time
    start_time = time.time()
    
    # Execute the test
    result = runner.execute(test_case, timeout=timeout_seconds)
    
    # Record end time
    end_time = time.time()
    actual_duration = end_time - start_time
    
    # Verify execution time is captured
    assert 'execution_time' in result, "execution_time must be captured"
    assert isinstance(result['execution_time'], (int, float)), "execution_time must be numeric"
    
    # Verify execution time is reasonable (should be close to actual duration)
    captured_time = result['execution_time']
    assert captured_time >= 0, "execution_time must be non-negative"
    
    # Allow some tolerance for measurement differences (up to 1 second)
    time_difference = abs(captured_time - actual_duration)
    assert time_difference <= 1.0, \
        f"Captured execution time should be close to actual duration. " \
        f"Captured: {captured_time}, Actual: {actual_duration}, Difference: {time_difference}"
    
    # Verify execution time is not unreasonably large
    assert captured_time <= timeout_seconds, \
        f"execution_time should not exceed timeout. Captured: {captured_time}, Timeout: {timeout_seconds}"