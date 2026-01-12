"""Property Test Orchestrator for Agentic AI Test Requirements.

Orchestrates property test execution across environments with:
- Test scheduling and execution
- Counter-example shrinking
- Result aggregation and reporting
"""

import asyncio
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import json
import traceback

from .models import (
    GeneratedTest,
    PropertyTestResult,
    ExecutionConfig,
    CorrectnessProperty,
)


@dataclass
class ExecutionPlan:
    """Plan for executing property tests."""
    id: str
    tests: List[GeneratedTest]
    config: ExecutionConfig
    environments: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'tests': [t.to_dict() for t in self.tests],
            'config': self.config.to_dict(),
            'environments': self.environments,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class ExecutionResult:
    """Result of executing a test plan."""
    plan_id: str
    results: List[PropertyTestResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_iterations: int
    execution_time_seconds: float
    completed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'plan_id': self.plan_id,
            'results': [r.to_dict() for r in self.results],
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'total_iterations': self.total_iterations,
            'execution_time_seconds': self.execution_time_seconds,
            'completed_at': self.completed_at.isoformat(),
        }
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


class PropertyTestOrchestrator:
    """Orchestrates property test execution across environments.
    
    Provides:
    - Test scheduling with parallel execution
    - Counter-example shrinking via Hypothesis
    - Result aggregation and summary generation
    """
    
    MIN_ITERATIONS = 100  # Minimum iterations per property test
    
    def __init__(
        self,
        max_workers: int = 4,
        default_timeout: int = 300,
        verbose: bool = False
    ):
        """Initialize the orchestrator.
        
        Args:
            max_workers: Maximum parallel test workers
            default_timeout: Default test timeout in seconds
            verbose: Enable verbose output
        """
        self.max_workers = max_workers
        self.default_timeout = default_timeout
        self.verbose = verbose
        self._executor: Optional[ThreadPoolExecutor] = None
    
    def schedule_tests(
        self,
        tests: List[GeneratedTest],
        config: Optional[ExecutionConfig] = None
    ) -> ExecutionPlan:
        """Schedule property tests for execution.
        
        Args:
            tests: List of tests to execute
            config: Execution configuration
            
        Returns:
            ExecutionPlan with scheduled tests
        """
        if config is None:
            config = ExecutionConfig(
                iterations=self.MIN_ITERATIONS,
                timeout_seconds=self.default_timeout,
                parallel=True,
                max_workers=self.max_workers,
                shrink_on_failure=True,
                verbose=self.verbose,
            )
        
        # Ensure minimum iterations
        if config.iterations < self.MIN_ITERATIONS:
            config.iterations = self.MIN_ITERATIONS
        
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        
        return ExecutionPlan(
            id=plan_id,
            tests=tests,
            config=config,
            environments=config.environments or ['local'],
        )
    
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """Execute a test plan.
        
        Args:
            plan: ExecutionPlan to execute
            
        Returns:
            ExecutionResult with all test results
        """
        start_time = time.time()
        results: List[PropertyTestResult] = []
        
        if plan.config.parallel and len(plan.tests) > 1:
            # Parallel execution
            results = await self._execute_parallel(plan)
        else:
            # Sequential execution
            results = await self._execute_sequential(plan)
        
        execution_time = time.time() - start_time
        
        # Aggregate results
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        total_iterations = sum(r.iterations_run for r in results)
        
        return ExecutionResult(
            plan_id=plan.id,
            results=results,
            total_tests=len(results),
            passed_tests=passed,
            failed_tests=failed,
            total_iterations=total_iterations,
            execution_time_seconds=execution_time,
        )
    
    async def run_property_test(
        self,
        test: GeneratedTest,
        iterations: int = 100,
        timeout_seconds: int = 300,
        shrink_on_failure: bool = True,
        environment_id: Optional[str] = None
    ) -> PropertyTestResult:
        """Run a single property test.
        
        Args:
            test: GeneratedTest to run
            iterations: Number of test iterations
            timeout_seconds: Test timeout
            shrink_on_failure: Whether to shrink counter-examples
            environment_id: Environment identifier
            
        Returns:
            PropertyTestResult with pass/fail and counter-examples
        """
        # Ensure minimum iterations
        iterations = max(iterations, self.MIN_ITERATIONS)
        
        start_time = time.time()
        
        try:
            # Write test to temporary file
            result = await self._execute_test_code(
                test.test_code,
                iterations=iterations,
                timeout_seconds=timeout_seconds,
            )
            
            execution_time = time.time() - start_time
            
            return PropertyTestResult(
                test_id=test.id,
                property_id=test.property_id,
                requirement_ids=test.requirement_ids,
                passed=result['passed'],
                iterations_run=result.get('iterations', iterations),
                counter_example=result.get('counter_example'),
                shrunk_example=result.get('shrunk_example'),
                error_message=result.get('error_message'),
                execution_time_seconds=execution_time,
                environment_id=environment_id or 'local',
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return PropertyTestResult(
                test_id=test.id,
                property_id=test.property_id,
                requirement_ids=test.requirement_ids,
                passed=False,
                iterations_run=0,
                error_message=f"Execution error: {str(e)}\n{traceback.format_exc()}",
                execution_time_seconds=execution_time,
                environment_id=environment_id or 'local',
            )
    
    def shrink_counter_example(
        self,
        test: GeneratedTest,
        counter_example: Any
    ) -> Any:
        """Shrink a counter-example to minimal failing case.
        
        Hypothesis handles shrinking automatically during test execution.
        This method is for manual shrinking of stored counter-examples.
        
        Args:
            test: GeneratedTest that failed
            counter_example: Original failing input
            
        Returns:
            Minimal failing input (may be same as original)
        """
        # Hypothesis shrinks automatically during execution
        # For stored counter-examples, we can re-run with the specific input
        # to verify it still fails, but shrinking requires re-execution
        return counter_example
    
    def execute_tests(
        self,
        tests: List[GeneratedTest],
        config: Optional[ExecutionConfig] = None
    ) -> List[PropertyTestResult]:
        """Execute tests synchronously.
        
        Args:
            tests: List of tests to execute
            config: Execution configuration
            
        Returns:
            List of PropertyTestResult
        """
        plan = self.schedule_tests(tests, config)
        
        # Run the async execution in a new event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.execute_plan(plan)
                    )
                    result = future.result()
            else:
                result = loop.run_until_complete(self.execute_plan(plan))
        except RuntimeError:
            # No event loop, create one
            result = asyncio.run(self.execute_plan(plan))
        
        return result.results
    
    def get_test_results(
        self,
        test_id: str,
        limit: int = 10
    ) -> List[PropertyTestResult]:
        """Get historical results for a test.
        
        Note: This is a placeholder - in production, results would be
        stored in a database and retrieved here.
        
        Args:
            test_id: Test identifier
            limit: Maximum results to return
            
        Returns:
            List of PropertyTestResult
        """
        # In a production system, this would query a database
        # For now, return empty list as results aren't persisted
        return []
    
    async def _execute_parallel(self, plan: ExecutionPlan) -> List[PropertyTestResult]:
        """Execute tests in parallel.
        
        Args:
            plan: ExecutionPlan with tests
            
        Returns:
            List of PropertyTestResult
        """
        results: List[PropertyTestResult] = []
        
        # Create tasks for all tests
        tasks = [
            self.run_property_test(
                test,
                iterations=plan.config.iterations,
                timeout_seconds=plan.config.timeout_seconds,
                shrink_on_failure=plan.config.shrink_on_failure,
            )
            for test in plan.tests
        ]
        
        # Execute with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(plan.config.max_workers)
        
        async def run_with_semaphore(task):
            async with semaphore:
                return await task
        
        # Gather results
        results = await asyncio.gather(
            *[run_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test = plan.tests[i]
                processed_results.append(PropertyTestResult(
                    test_id=test.id,
                    property_id=test.property_id,
                    requirement_ids=test.requirement_ids,
                    passed=False,
                    iterations_run=0,
                    error_message=f"Execution exception: {str(result)}",
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_sequential(self, plan: ExecutionPlan) -> List[PropertyTestResult]:
        """Execute tests sequentially.
        
        Args:
            plan: ExecutionPlan with tests
            
        Returns:
            List of PropertyTestResult
        """
        results = []
        
        for test in plan.tests:
            result = await self.run_property_test(
                test,
                iterations=plan.config.iterations,
                timeout_seconds=plan.config.timeout_seconds,
                shrink_on_failure=plan.config.shrink_on_failure,
            )
            results.append(result)
            
            if self.verbose:
                status = "PASSED" if result.passed else "FAILED"
                print(f"  {test.name}: {status} ({result.iterations_run} iterations)")
        
        return results
    
    async def _execute_test_code(
        self,
        test_code: str,
        iterations: int,
        timeout_seconds: int
    ) -> Dict[str, Any]:
        """Execute test code in a subprocess.
        
        Args:
            test_code: Python test code to execute
            iterations: Number of iterations
            timeout_seconds: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        # Create a wrapper script that runs the test
        wrapper_code = self._create_test_wrapper(test_code, iterations)
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(wrapper_code)
            temp_path = f.name
        
        try:
            # Run with pytest
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pytest', temp_path,
                '-v', '--tb=short', '-x',
                f'--hypothesis-seed=0',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'passed': False,
                    'iterations': 0,
                    'error_message': f'Test timed out after {timeout_seconds} seconds',
                }
            
            # Parse results
            output = stdout.decode() + stderr.decode()
            passed = process.returncode == 0
            
            # Extract counter-example if present
            counter_example = self._extract_counter_example(output)
            
            return {
                'passed': passed,
                'iterations': iterations if passed else self._extract_iterations(output),
                'counter_example': counter_example,
                'shrunk_example': counter_example,  # Hypothesis shrinks automatically
                'error_message': None if passed else self._extract_error(output),
            }
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
    
    def _create_test_wrapper(self, test_code: str, iterations: int) -> str:
        """Create a wrapper script for test execution.
        
        Args:
            test_code: Original test code
            iterations: Number of iterations
            
        Returns:
            Wrapper script code
        """
        # Ensure the test code has proper imports
        imports = """
import pytest
from hypothesis import given, settings, assume, note, Verbosity
from hypothesis import strategies as st
from typing import Any, Dict, List, Optional
import json

"""
        
        # Update settings in test code to use specified iterations
        modified_code = test_code.replace(
            'max_examples=100',
            f'max_examples={iterations}'
        )
        
        return imports + modified_code
    
    def _extract_counter_example(self, output: str) -> Optional[Any]:
        """Extract counter-example from test output.
        
        Args:
            output: Test output string
            
        Returns:
            Counter-example if found, None otherwise
        """
        # Look for Hypothesis falsifying example
        if 'Falsifying example:' in output:
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if 'Falsifying example:' in line:
                    # Get the next few lines as the example
                    example_lines = []
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip() and not lines[j].startswith('='):
                            example_lines.append(lines[j])
                        else:
                            break
                    return '\n'.join(example_lines)
        return None
    
    def _extract_iterations(self, output: str) -> int:
        """Extract number of iterations from test output.
        
        Args:
            output: Test output string
            
        Returns:
            Number of iterations run
        """
        # Look for iteration count in output
        import re
        match = re.search(r'(\d+) passing', output)
        if match:
            return int(match.group(1))
        
        match = re.search(r'Tried (\d+) examples', output)
        if match:
            return int(match.group(1))
        
        return 0
    
    def _extract_error(self, output: str) -> str:
        """Extract error message from test output.
        
        Args:
            output: Test output string
            
        Returns:
            Error message
        """
        # Look for assertion error or exception
        lines = output.split('\n')
        error_lines = []
        capture = False
        
        for line in lines:
            if 'AssertionError' in line or 'Error' in line or 'FAILED' in line:
                capture = True
            if capture:
                error_lines.append(line)
                if len(error_lines) > 10:
                    break
        
        return '\n'.join(error_lines) if error_lines else output[-500:]


class TestExecutionSummary:
    """Generates execution summaries and reports."""
    
    @staticmethod
    def generate_summary(result: ExecutionResult) -> str:
        """Generate a text summary of execution results.
        
        Args:
            result: ExecutionResult to summarize
            
        Returns:
            Summary text
        """
        lines = [
            "=" * 60,
            "Property Test Execution Summary",
            "=" * 60,
            f"Plan ID: {result.plan_id}",
            f"Completed: {result.completed_at.isoformat()}",
            f"Duration: {result.execution_time_seconds:.2f}s",
            "",
            f"Total Tests: {result.total_tests}",
            f"Passed: {result.passed_tests}",
            f"Failed: {result.failed_tests}",
            f"Pass Rate: {result.pass_rate:.1f}%",
            f"Total Iterations: {result.total_iterations}",
            "",
        ]
        
        if result.failed_tests > 0:
            lines.append("Failed Tests:")
            lines.append("-" * 40)
            for r in result.results:
                if not r.passed:
                    lines.append(f"  - {r.test_id}")
                    if r.error_message:
                        lines.append(f"    Error: {r.error_message[:100]}...")
                    if r.counter_example:
                        lines.append(f"    Counter-example: {r.counter_example}")
            lines.append("")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    @staticmethod
    def generate_json_report(result: ExecutionResult) -> str:
        """Generate a JSON report of execution results.
        
        Args:
            result: ExecutionResult to report
            
        Returns:
            JSON report string
        """
        return json.dumps(result.to_dict(), indent=2)


# Convenience functions

async def run_tests(
    tests: List[GeneratedTest],
    iterations: int = 100,
    parallel: bool = True
) -> ExecutionResult:
    """Convenience function to run property tests.
    
    Args:
        tests: List of tests to run
        iterations: Number of iterations per test
        parallel: Whether to run in parallel
        
    Returns:
        ExecutionResult
    """
    orchestrator = PropertyTestOrchestrator()
    config = ExecutionConfig(
        iterations=iterations,
        parallel=parallel,
    )
    plan = orchestrator.schedule_tests(tests, config)
    return await orchestrator.execute_plan(plan)


async def run_single_test(
    test: GeneratedTest,
    iterations: int = 100
) -> PropertyTestResult:
    """Convenience function to run a single property test.
    
    Args:
        test: Test to run
        iterations: Number of iterations
        
    Returns:
        PropertyTestResult
    """
    orchestrator = PropertyTestOrchestrator()
    return await orchestrator.run_property_test(test, iterations=iterations)
