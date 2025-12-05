"""Test execution engine for running tests in environments.

This module provides functionality for:
- Test execution in virtual and physical environments
- Test timeout and cancellation logic
- Result collection and aggregation
- Parallel test execution support
- Kernel panic and crash handling
"""

import asyncio
import subprocess
import signal
import time
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    ArtifactBundle, FailureInfo, CoverageData
)
from execution.environment_manager import EnvironmentManager
from config.settings import get_settings


@dataclass
class ExecutionHandle:
    """Handle for tracking test execution."""
    execution_id: str
    test_ids: List[str]
    status: str  # running, completed, cancelled, failed
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[TestResult] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []


class TestExecutionError(Exception):
    """Exception raised when test execution fails."""
    pass


class TestRunner:
    """Engine for executing tests in environments."""
    
    def __init__(self, environment_manager: Optional[EnvironmentManager] = None):
        """Initialize test runner.
        
        Args:
            environment_manager: Manager for test environments
        """
        self.settings = get_settings()
        self.env_manager = environment_manager or EnvironmentManager()
        self.active_executions: Dict[str, ExecutionHandle] = {}
        self.executor = ThreadPoolExecutor(
            max_workers=self.settings.execution.max_parallel_tests
        )
        self._lock = threading.Lock()
    
    def execute_test(
        self, 
        test: TestCase, 
        environment: Environment,
        timeout: Optional[int] = None
    ) -> TestResult:
        """Execute a single test in an environment.
        
        Args:
            test: Test case to execute
            environment: Environment to execute in
            timeout: Optional timeout in seconds (overrides default)
            
        Returns:
            Test result
            
        Raises:
            TestExecutionError: If execution fails
        """
        if environment.status != EnvironmentStatus.IDLE:
            raise TestExecutionError(
                f"Environment {environment.id} is not idle (status: {environment.status})"
            )
        
        # Mark environment as busy
        environment.status = EnvironmentStatus.BUSY
        environment.last_used = datetime.now()
        
        timeout = timeout or self.settings.execution.test_timeout
        start_time = time.time()
        
        try:
            # Execute the test script
            result = self._run_test_script(test, environment, timeout)
            
            # Capture artifacts
            artifacts = self.env_manager.capture_artifacts(environment)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create test result
            test_result = TestResult(
                test_id=test.id,
                status=result['status'],
                execution_time=execution_time,
                environment=environment,
                artifacts=artifacts,
                coverage_data=result.get('coverage'),
                failure_info=result.get('failure_info'),
                timestamp=datetime.now()
            )
            
            return test_result
            
        except Exception as e:
            # Handle execution errors
            execution_time = time.time() - start_time
            
            failure_info = FailureInfo(
                error_message=str(e),
                stack_trace=None,
                exit_code=None,
                kernel_panic=False,
                timeout_occurred=False
            )
            
            test_result = TestResult(
                test_id=test.id,
                status=TestStatus.ERROR,
                execution_time=execution_time,
                environment=environment,
                artifacts=ArtifactBundle(),
                failure_info=failure_info,
                timestamp=datetime.now()
            )
            
            return test_result
            
        finally:
            # Mark environment as idle
            environment.status = EnvironmentStatus.IDLE
    
    def _run_test_script(
        self, 
        test: TestCase, 
        environment: Environment,
        timeout: int
    ) -> Dict[str, Any]:
        """Run the test script and collect results.
        
        Args:
            test: Test case to run
            environment: Environment to run in
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with status, coverage, and failure_info
        """
        # Create a temporary script file
        env_dir = Path(environment.metadata.get("env_dir", f"/tmp/{environment.id}"))
        script_path = env_dir / f"test_{test.id}.sh"
        script_path.write_text(test.test_script)
        script_path.chmod(0o755)
        
        try:
            # Execute the test script with timeout
            process = subprocess.Popen(
                [str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=env_dir,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
                
                # Check for kernel panic indicators
                kernel_panic = self._detect_kernel_panic(stdout, stderr)
                
                # Determine test status
                if kernel_panic:
                    status = TestStatus.FAILED
                    failure_info = FailureInfo(
                        error_message="Kernel panic detected",
                        stack_trace=stderr.decode('utf-8', errors='ignore'),
                        exit_code=exit_code,
                        kernel_panic=True,
                        timeout_occurred=False
                    )
                elif exit_code == 0:
                    status = TestStatus.PASSED
                    failure_info = None
                else:
                    status = TestStatus.FAILED
                    failure_info = FailureInfo(
                        error_message=f"Test failed with exit code {exit_code}",
                        stack_trace=stderr.decode('utf-8', errors='ignore'),
                        exit_code=exit_code,
                        kernel_panic=False,
                        timeout_occurred=False
                    )
                
                return {
                    'status': status,
                    'failure_info': failure_info,
                    'coverage': None  # Coverage collection would be implemented here
                }
                
            except subprocess.TimeoutExpired:
                # Kill the process group
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                
                process.wait()
                
                failure_info = FailureInfo(
                    error_message=f"Test timed out after {timeout} seconds",
                    stack_trace=None,
                    exit_code=None,
                    kernel_panic=False,
                    timeout_occurred=True
                )
                
                return {
                    'status': TestStatus.TIMEOUT,
                    'failure_info': failure_info,
                    'coverage': None
                }
                
        finally:
            # Clean up script file
            if script_path.exists():
                script_path.unlink()
    
    def _detect_kernel_panic(self, stdout: bytes, stderr: bytes) -> bool:
        """Detect kernel panic from output.
        
        Args:
            stdout: Standard output
            stderr: Standard error
            
        Returns:
            True if kernel panic detected
        """
        panic_indicators = [
            b"Kernel panic",
            b"kernel BUG at",
            b"Oops:",
            b"general protection fault",
            b"unable to handle kernel",
        ]
        
        output = stdout + stderr
        return any(indicator in output for indicator in panic_indicators)
    
    def execute_tests_parallel(
        self,
        tests: List[TestCase],
        environments: List[Environment],
        timeout: Optional[int] = None
    ) -> ExecutionHandle:
        """Execute multiple tests in parallel across environments.
        
        Args:
            tests: List of test cases to execute
            environments: List of available environments
            timeout: Optional timeout per test
            
        Returns:
            Execution handle for tracking progress
        """
        execution_id = str(uuid.uuid4())
        handle = ExecutionHandle(
            execution_id=execution_id,
            test_ids=[t.id for t in tests],
            status="running",
            start_time=datetime.now()
        )
        
        with self._lock:
            self.active_executions[execution_id] = handle
        
        # Submit tests to thread pool
        futures: List[Future] = []
        env_index = 0
        
        for test in tests:
            # Round-robin environment assignment
            env = environments[env_index % len(environments)]
            env_index += 1
            
            future = self.executor.submit(
                self._execute_with_error_handling,
                test,
                env,
                timeout
            )
            futures.append(future)
        
        # Collect results in a separate thread
        def collect_results():
            results = []
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Create error result
                    pass
            
            with self._lock:
                handle.results = results
                handle.status = "completed"
                handle.end_time = datetime.now()
        
        threading.Thread(target=collect_results, daemon=True).start()
        
        return handle
    
    def _execute_with_error_handling(
        self,
        test: TestCase,
        environment: Environment,
        timeout: Optional[int]
    ) -> TestResult:
        """Execute test with error handling wrapper.
        
        Args:
            test: Test case
            environment: Environment
            timeout: Timeout
            
        Returns:
            Test result
        """
        try:
            return self.execute_test(test, environment, timeout)
        except Exception as e:
            # Return error result
            return TestResult(
                test_id=test.id,
                status=TestStatus.ERROR,
                execution_time=0.0,
                environment=environment,
                failure_info=FailureInfo(
                    error_message=f"Execution error: {str(e)}",
                    stack_trace=None
                ),
                timestamp=datetime.now()
            )
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an ongoing execution.
        
        Args:
            execution_id: ID of execution to cancel
            
        Returns:
            True if cancelled successfully
        """
        with self._lock:
            handle = self.active_executions.get(execution_id)
            if not handle:
                return False
            
            if handle.status != "running":
                return False
            
            handle.status = "cancelled"
            handle.end_time = datetime.now()
            
        return True
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionHandle]:
        """Get status of an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution handle if found
        """
        with self._lock:
            return self.active_executions.get(execution_id)
    
    def aggregate_results(
        self,
        results: List[TestResult],
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Aggregate test results.
        
        Args:
            results: List of test results
            group_by: Optional grouping key (architecture, board_type, peripheral_config)
            
        Returns:
            Aggregated results dictionary
        """
        if not results:
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'timeout': 0,
                'error': 0,
                'skipped': 0,
                'pass_rate': 0.0,
                'total_execution_time': 0.0,
                'groups': {}
            }
        
        # Calculate overall statistics
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        timeout = sum(1 for r in results if r.status == TestStatus.TIMEOUT)
        error = sum(1 for r in results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        
        pass_rate = passed / total if total > 0 else 0.0
        total_time = sum(r.execution_time for r in results)
        
        aggregated = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'timeout': timeout,
            'error': error,
            'skipped': skipped,
            'pass_rate': pass_rate,
            'total_execution_time': total_time,
            'groups': {}
        }
        
        # Group results if requested
        if group_by:
            groups = {}
            
            for result in results:
                # Extract grouping key
                if group_by == 'architecture':
                    key = result.environment.config.architecture
                elif group_by == 'board_type':
                    key = result.environment.config.cpu_model
                elif group_by == 'peripheral_config':
                    key = f"{len(result.environment.config.peripherals)}_peripherals"
                else:
                    key = 'unknown'
                
                if key not in groups:
                    groups[key] = []
                groups[key].append(result)
            
            # Aggregate each group
            for key, group_results in groups.items():
                group_total = len(group_results)
                group_passed = sum(1 for r in group_results if r.status == TestStatus.PASSED)
                group_failed = sum(1 for r in group_results if r.status == TestStatus.FAILED)
                
                aggregated['groups'][key] = {
                    'total': group_total,
                    'passed': group_passed,
                    'failed': group_failed,
                    'pass_rate': group_passed / group_total if group_total > 0 else 0.0
                }
        
        return aggregated
    
    def shutdown(self):
        """Shutdown the test runner and cleanup resources."""
        self.executor.shutdown(wait=True)


# Import os for process group handling
import os
