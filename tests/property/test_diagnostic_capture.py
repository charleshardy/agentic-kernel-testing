"""Property-based tests for diagnostic capture completeness.

**Feature: agentic-kernel-testing, Property 16: Diagnostic capture completeness**
**Validates: Requirements 4.1**

Property 16: Diagnostic capture completeness
For any test failure, the captured diagnostics should include kernel logs, 
stack traces, and system state.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from ai_generator.models import (
    TestCase, TestResult, TestStatus, TestType, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle, FailureInfo, ExpectedOutcome
)
from execution.test_runner import TestRunner
from execution.environment_manager import EnvironmentManager


@st.composite
def hardware_config_strategy(draw):
    """Generate a random hardware configuration."""
    architecture = draw(st.sampled_from(['x86_64', 'arm64', 'riscv64']))
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        memory_mb=draw(st.integers(min_value=512, max_value=4096)),
        storage_type='ssd',
        is_virtual=True,
        emulator='qemu'
    )


@st.composite
def failing_test_case_strategy(draw):
    """Generate a test case that will fail."""
    test_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    # Create a test script that will fail
    test_script = "#!/bin/bash\nexit 1"
    
    return TestCase(
        id=test_id,
        name=f"test_{test_id}",
        description="A failing test",
        test_type=TestType.UNIT,
        target_subsystem="test_subsystem",
        test_script=test_script,
        execution_time_estimate=10,
        expected_outcome=ExpectedOutcome(should_pass=False)
    )


def test_diagnostic_capture_on_failure():
    """
    Property: For any test failure, the test result should contain diagnostic information
    including artifacts (logs, core dumps, traces).
    
    **Feature: agentic-kernel-testing, Property 16: Diagnostic capture completeness**
    **Validates: Requirements 4.1**
    """
    # Create a temporary working directory
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        # Create environment manager with temp directory
        env_manager = EnvironmentManager(work_dir=work_dir)
        runner = TestRunner(environment_manager=env_manager)
        
        # Create a hardware config and environment
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='test_cpu',
            memory_mb=1024,
            is_virtual=True,
            emulator='qemu'
        )
        
        environment = env_manager.provision_environment(config)
        
        # Create a failing test
        test = TestCase(
            id='test_fail_001',
            name='failing_test',
            description='A test that fails',
            test_type=TestType.UNIT,
            target_subsystem='test',
            test_script='#!/bin/bash\necho "Test failed" >&2\nexit 1',
            execution_time_estimate=10
        )
        
        # Execute the test
        result = runner.execute_test(test, environment, timeout=5)
        
        # Verify the test failed
        assert result.status in [TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT], \
            f"Expected test to fail, but got status: {result.status}"
        
        # Verify diagnostic information is captured
        # 1. Artifacts should be present
        assert result.artifacts is not None, "Artifacts should not be None"
        assert isinstance(result.artifacts, ArtifactBundle), "Artifacts should be ArtifactBundle"
        
        # 2. For failures, failure_info should be present
        if result.status == TestStatus.FAILED:
            assert result.failure_info is not None, "FailureInfo should be present for failed tests"
            assert isinstance(result.failure_info, FailureInfo), "failure_info should be FailureInfo"
            assert result.failure_info.error_message, "Error message should not be empty"
        
        # 3. Execution time should be recorded
        assert result.execution_time >= 0, "Execution time should be non-negative"
        
        # 4. Timestamp should be present
        assert result.timestamp is not None, "Timestamp should be present"
        
        # Cleanup
        env_manager.cleanup_environment(environment)


@given(
    st.integers(min_value=1, max_value=10),
    hardware_config_strategy()
)
@settings(max_examples=50, deadline=None)
def test_diagnostic_capture_for_multiple_failures(num_tests: int, config: HardwareConfig):
    """
    Property: For any set of test failures, each failure should have complete diagnostic
    information captured independently.
    
    **Feature: agentic-kernel-testing, Property 16: Diagnostic capture completeness**
    **Validates: Requirements 4.1**
    """
    # Create a temporary working directory
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        # Create environment manager with temp directory
        env_manager = EnvironmentManager(work_dir=work_dir)
        runner = TestRunner(environment_manager=env_manager)
        
        # Provision environment
        environment = env_manager.provision_environment(config)
        
        # Create multiple failing tests
        results = []
        for i in range(num_tests):
            test = TestCase(
                id=f'test_fail_{i}',
                name=f'failing_test_{i}',
                description=f'Failing test {i}',
                test_type=TestType.UNIT,
                target_subsystem='test',
                test_script=f'#!/bin/bash\necho "Test {i} failed" >&2\nexit 1',
                execution_time_estimate=10
            )
            
            result = runner.execute_test(test, environment, timeout=5)
            results.append(result)
        
        # Verify all results have diagnostic information
        for i, result in enumerate(results):
            # Each result should have artifacts
            assert result.artifacts is not None, f"Test {i}: Artifacts should not be None"
            
            # Each result should have a timestamp
            assert result.timestamp is not None, f"Test {i}: Timestamp should be present"
            
            # Each result should have execution time
            assert result.execution_time >= 0, f"Test {i}: Execution time should be non-negative"
            
            # Failed tests should have failure_info
            if result.status == TestStatus.FAILED:
                assert result.failure_info is not None, f"Test {i}: FailureInfo should be present"
                assert result.failure_info.error_message, f"Test {i}: Error message should not be empty"
        
        # Cleanup
        env_manager.cleanup_environment(environment)


def test_diagnostic_capture_includes_kernel_logs():
    """
    Property: For any test failure, if kernel logs are available, they should be
    included in the artifacts.
    
    **Feature: agentic-kernel-testing, Property 16: Diagnostic capture completeness**
    **Validates: Requirements 4.1**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        env_manager = EnvironmentManager(work_dir=work_dir)
        runner = TestRunner(environment_manager=env_manager)
        
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='test_cpu',
            memory_mb=1024,
            is_virtual=True,
            emulator='qemu'
        )
        
        environment = env_manager.provision_environment(config)
        
        # Create log directory and add a kernel log
        env_dir = Path(environment.metadata.get("env_dir"))
        log_dir = env_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        kernel_log = log_dir / "kernel.log"
        kernel_log.write_text("Kernel log content\nSome kernel messages\n")
        
        # Create and execute a failing test
        test = TestCase(
            id='test_with_logs',
            name='test_with_kernel_logs',
            description='Test with kernel logs',
            test_type=TestType.UNIT,
            target_subsystem='test',
            test_script='#!/bin/bash\nexit 1',
            execution_time_estimate=10
        )
        
        result = runner.execute_test(test, environment, timeout=5)
        
        # Verify artifacts include logs
        assert result.artifacts is not None
        assert len(result.artifacts.logs) > 0, "Logs should be captured"
        assert any('kernel.log' in log for log in result.artifacts.logs), \
            "Kernel log should be in captured logs"
        
        env_manager.cleanup_environment(environment)


def test_diagnostic_capture_includes_stack_trace_on_failure():
    """
    Property: For any test failure with stderr output, the failure_info should
    include the stack trace (stderr content).
    
    **Feature: agentic-kernel-testing, Property 16: Diagnostic capture completeness**
    **Validates: Requirements 4.1**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        env_manager = EnvironmentManager(work_dir=work_dir)
        runner = TestRunner(environment_manager=env_manager)
        
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='test_cpu',
            memory_mb=1024,
            is_virtual=True,
            emulator='qemu'
        )
        
        environment = env_manager.provision_environment(config)
        
        # Create a test that produces stderr output
        test = TestCase(
            id='test_with_stderr',
            name='test_with_stack_trace',
            description='Test with stack trace',
            test_type=TestType.UNIT,
            target_subsystem='test',
            test_script='#!/bin/bash\necho "Error: Stack trace line 1" >&2\necho "Error: Stack trace line 2" >&2\nexit 1',
            execution_time_estimate=10
        )
        
        result = runner.execute_test(test, environment, timeout=5)
        
        # Verify failure_info includes stack trace
        if result.status == TestStatus.FAILED:
            assert result.failure_info is not None
            assert result.failure_info.stack_trace is not None, \
                "Stack trace should be captured for failed tests"
            assert "Stack trace" in result.failure_info.stack_trace, \
                "Stack trace should contain stderr output"
        
        env_manager.cleanup_environment(environment)


def test_diagnostic_capture_completeness_structure():
    """
    Property: For any test failure, the diagnostic information should have a complete
    structure with all required fields present.
    
    **Feature: agentic-kernel-testing, Property 16: Diagnostic capture completeness**
    **Validates: Requirements 4.1**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        env_manager = EnvironmentManager(work_dir=work_dir)
        runner = TestRunner(environment_manager=env_manager)
        
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='test_cpu',
            memory_mb=1024,
            is_virtual=True,
            emulator='qemu'
        )
        
        environment = env_manager.provision_environment(config)
        
        test = TestCase(
            id='test_complete_diagnostics',
            name='test_complete_diagnostics',
            description='Test for complete diagnostics',
            test_type=TestType.UNIT,
            target_subsystem='test',
            test_script='#!/bin/bash\nexit 1',
            execution_time_estimate=10
        )
        
        result = runner.execute_test(test, environment, timeout=5)
        
        # Verify TestResult has all required diagnostic fields
        assert hasattr(result, 'test_id'), "Result should have test_id"
        assert hasattr(result, 'status'), "Result should have status"
        assert hasattr(result, 'execution_time'), "Result should have execution_time"
        assert hasattr(result, 'environment'), "Result should have environment"
        assert hasattr(result, 'artifacts'), "Result should have artifacts"
        assert hasattr(result, 'timestamp'), "Result should have timestamp"
        
        # Verify artifacts structure
        assert hasattr(result.artifacts, 'logs'), "Artifacts should have logs field"
        assert hasattr(result.artifacts, 'core_dumps'), "Artifacts should have core_dumps field"
        assert hasattr(result.artifacts, 'traces'), "Artifacts should have traces field"
        assert hasattr(result.artifacts, 'metadata'), "Artifacts should have metadata field"
        
        # Verify failure_info structure if present
        if result.failure_info:
            assert hasattr(result.failure_info, 'error_message'), \
                "FailureInfo should have error_message"
            assert hasattr(result.failure_info, 'stack_trace'), \
                "FailureInfo should have stack_trace"
            assert hasattr(result.failure_info, 'exit_code'), \
                "FailureInfo should have exit_code"
            assert hasattr(result.failure_info, 'kernel_panic'), \
                "FailureInfo should have kernel_panic"
            assert hasattr(result.failure_info, 'timeout_occurred'), \
                "FailureInfo should have timeout_occurred"
        
        env_manager.cleanup_environment(environment)
