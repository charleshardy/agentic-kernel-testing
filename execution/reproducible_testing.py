"""Reproducible test case generation and minimization.

This module provides functionality for:
- Test case minimization for failures
- Reproducibility verification
- Seed-based test execution for determinism
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from ai_generator.models import TestCase, TestResult, TestStatus, FailureInfo


class MinimizationStrategy(str, Enum):
    """Strategies for test case minimization."""
    BINARY_SEARCH = "binary_search"
    DELTA_DEBUGGING = "delta_debugging"
    GREEDY = "greedy"


@dataclass
class ReproducibilityResult:
    """Result of reproducibility verification."""
    test_case_id: str
    original_failure: FailureInfo
    reproduction_attempts: int
    successful_reproductions: int
    reproducibility_rate: float
    is_reproducible: bool  # True if rate >= threshold
    seed: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate reproducibility result."""
        if self.reproduction_attempts <= 0:
            raise ValueError("reproduction_attempts must be positive")
        if not 0.0 <= self.reproducibility_rate <= 1.0:
            raise ValueError("reproducibility_rate must be between 0.0 and 1.0")


@dataclass
class MinimizedTestCase:
    """Result of test case minimization."""
    original_test: TestCase
    minimized_test: TestCase
    reduction_ratio: float  # How much was reduced (0.0 to 1.0)
    minimization_steps: int
    still_reproduces: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate minimized test case."""
        if not 0.0 <= self.reduction_ratio <= 1.0:
            raise ValueError("reduction_ratio must be between 0.0 and 1.0")
        if self.minimization_steps < 0:
            raise ValueError("minimization_steps cannot be negative")


class TestCaseMinimizer:
    """Minimizes test cases that trigger failures."""
    
    def __init__(
        self,
        strategy: MinimizationStrategy = MinimizationStrategy.DELTA_DEBUGGING,
        max_iterations: int = 100
    ):
        """Initialize test case minimizer.
        
        Args:
            strategy: Minimization strategy to use
            max_iterations: Maximum minimization iterations
        """
        self.strategy = strategy
        self.max_iterations = max_iterations
    
    def minimize(
        self,
        test_case: TestCase,
        failure_checker: Callable[[TestCase], bool]
    ) -> MinimizedTestCase:
        """Minimize a test case while preserving failure reproduction.
        
        Args:
            test_case: Original test case that triggers failure
            failure_checker: Function that returns True if test still fails
            
        Returns:
            Minimized test case result
        """
        if self.strategy == MinimizationStrategy.DELTA_DEBUGGING:
            return self._delta_debugging(test_case, failure_checker)
        elif self.strategy == MinimizationStrategy.BINARY_SEARCH:
            return self._binary_search(test_case, failure_checker)
        else:  # GREEDY
            return self._greedy_minimize(test_case, failure_checker)
    
    def _delta_debugging(
        self,
        test_case: TestCase,
        failure_checker: Callable[[TestCase], bool]
    ) -> MinimizedTestCase:
        """Delta debugging minimization algorithm.
        
        Args:
            test_case: Original test case
            failure_checker: Failure checking function
            
        Returns:
            Minimized test case
        """
        # Split test script into lines
        lines = test_case.test_script.split('\n')
        current_lines = lines.copy()
        steps = 0
        
        # Delta debugging: try removing chunks of lines
        chunk_size = len(current_lines) // 2
        
        while chunk_size > 0 and steps < self.max_iterations:
            i = 0
            made_progress = False
            
            while i < len(current_lines):
                # Try removing a chunk
                test_lines = (
                    current_lines[:i] + 
                    current_lines[min(i + chunk_size, len(current_lines)):]
                )
                
                if len(test_lines) == 0:
                    i += chunk_size
                    continue
                
                # Create test case with reduced script
                reduced_test = TestCase(
                    id=test_case.id,
                    name=test_case.name,
                    description=test_case.description,
                    test_type=test_case.test_type,
                    target_subsystem=test_case.target_subsystem,
                    code_paths=test_case.code_paths,
                    execution_time_estimate=test_case.execution_time_estimate,
                    required_hardware=test_case.required_hardware,
                    test_script='\n'.join(test_lines),
                    expected_outcome=test_case.expected_outcome,
                    metadata=test_case.metadata
                )
                
                steps += 1
                
                # Check if reduced test still fails
                if failure_checker(reduced_test):
                    current_lines = test_lines
                    made_progress = True
                else:
                    i += chunk_size
            
            # Reduce chunk size if no progress
            if not made_progress:
                chunk_size = chunk_size // 2
        
        # Create final minimized test case
        minimized_script = '\n'.join(current_lines)
        minimized_test = TestCase(
            id=test_case.id,
            name=f"{test_case.name} (minimized)",
            description=f"Minimized version: {test_case.description}",
            test_type=test_case.test_type,
            target_subsystem=test_case.target_subsystem,
            code_paths=test_case.code_paths,
            execution_time_estimate=test_case.execution_time_estimate,
            required_hardware=test_case.required_hardware,
            test_script=minimized_script,
            expected_outcome=test_case.expected_outcome,
            metadata={**test_case.metadata, "minimized": True}
        )
        
        # Calculate reduction ratio
        original_size = len(test_case.test_script)
        minimized_size = len(minimized_script)
        reduction_ratio = 1.0 - (minimized_size / original_size) if original_size > 0 else 0.0
        
        # Verify minimized test still reproduces
        still_reproduces = failure_checker(minimized_test)
        
        return MinimizedTestCase(
            original_test=test_case,
            minimized_test=minimized_test,
            reduction_ratio=reduction_ratio,
            minimization_steps=steps,
            still_reproduces=still_reproduces
        )
    
    def _binary_search(
        self,
        test_case: TestCase,
        failure_checker: Callable[[TestCase], bool]
    ) -> MinimizedTestCase:
        """Binary search minimization (simpler, faster).
        
        Args:
            test_case: Original test case
            failure_checker: Failure checking function
            
        Returns:
            Minimized test case
        """
        lines = test_case.test_script.split('\n')
        left, right = 0, len(lines)
        best_lines = lines.copy()
        steps = 0
        
        while left < right and steps < self.max_iterations:
            mid = (left + right) // 2
            test_lines = lines[:mid]
            
            if len(test_lines) == 0:
                break
            
            reduced_test = TestCase(
                id=test_case.id,
                name=test_case.name,
                description=test_case.description,
                test_type=test_case.test_type,
                target_subsystem=test_case.target_subsystem,
                test_script='\n'.join(test_lines),
                required_hardware=test_case.required_hardware
            )
            
            steps += 1
            
            if failure_checker(reduced_test):
                best_lines = test_lines
                right = mid
            else:
                left = mid + 1
        
        minimized_script = '\n'.join(best_lines)
        minimized_test = TestCase(
            id=test_case.id,
            name=f"{test_case.name} (minimized)",
            description=f"Minimized: {test_case.description}",
            test_type=test_case.test_type,
            target_subsystem=test_case.target_subsystem,
            test_script=minimized_script,
            required_hardware=test_case.required_hardware
        )
        
        original_size = len(test_case.test_script)
        minimized_size = len(minimized_script)
        reduction_ratio = 1.0 - (minimized_size / original_size) if original_size > 0 else 0.0
        
        return MinimizedTestCase(
            original_test=test_case,
            minimized_test=minimized_test,
            reduction_ratio=reduction_ratio,
            minimization_steps=steps,
            still_reproduces=failure_checker(minimized_test)
        )
    
    def _greedy_minimize(
        self,
        test_case: TestCase,
        failure_checker: Callable[[TestCase], bool]
    ) -> MinimizedTestCase:
        """Greedy minimization: remove one line at a time.
        
        Args:
            test_case: Original test case
            failure_checker: Failure checking function
            
        Returns:
            Minimized test case
        """
        lines = test_case.test_script.split('\n')
        current_lines = lines.copy()
        steps = 0
        
        i = 0
        while i < len(current_lines) and steps < self.max_iterations:
            # Try removing line i
            test_lines = current_lines[:i] + current_lines[i+1:]
            
            if len(test_lines) == 0:
                i += 1
                continue
            
            reduced_test = TestCase(
                id=test_case.id,
                name=test_case.name,
                description=test_case.description,
                test_type=test_case.test_type,
                target_subsystem=test_case.target_subsystem,
                test_script='\n'.join(test_lines),
                required_hardware=test_case.required_hardware
            )
            
            steps += 1
            
            if failure_checker(reduced_test):
                current_lines = test_lines
                # Don't increment i, check same position again
            else:
                i += 1
        
        minimized_script = '\n'.join(current_lines)
        minimized_test = TestCase(
            id=test_case.id,
            name=f"{test_case.name} (minimized)",
            description=f"Minimized: {test_case.description}",
            test_type=test_case.test_type,
            target_subsystem=test_case.target_subsystem,
            test_script=minimized_script,
            required_hardware=test_case.required_hardware
        )
        
        original_size = len(test_case.test_script)
        minimized_size = len(minimized_script)
        reduction_ratio = 1.0 - (minimized_size / original_size) if original_size > 0 else 0.0
        
        return MinimizedTestCase(
            original_test=test_case,
            minimized_test=minimized_test,
            reduction_ratio=reduction_ratio,
            minimization_steps=steps,
            still_reproduces=failure_checker(minimized_test)
        )



class ReproducibilityVerifier:
    """Verifies that test cases reliably reproduce failures."""
    
    def __init__(
        self,
        reproducibility_threshold: float = 0.8,
        verification_attempts: int = 10
    ):
        """Initialize reproducibility verifier.
        
        Args:
            reproducibility_threshold: Minimum rate to consider reproducible
            verification_attempts: Number of times to attempt reproduction
        """
        if not 0.0 <= reproducibility_threshold <= 1.0:
            raise ValueError("reproducibility_threshold must be between 0.0 and 1.0")
        if verification_attempts <= 0:
            raise ValueError("verification_attempts must be positive")
        
        self.reproducibility_threshold = reproducibility_threshold
        self.verification_attempts = verification_attempts
    
    def verify(
        self,
        test_case: TestCase,
        original_failure: FailureInfo,
        test_executor: Callable[[TestCase], TestResult]
    ) -> ReproducibilityResult:
        """Verify that a test case reliably reproduces a failure.
        
        Args:
            test_case: Test case to verify
            original_failure: Original failure information
            test_executor: Function to execute test and return result
            
        Returns:
            Reproducibility result
        """
        successful_reproductions = 0
        
        for _ in range(self.verification_attempts):
            result = test_executor(test_case)
            
            # Check if test failed with similar error
            if result.status == TestStatus.FAILED and result.failure_info:
                if self._is_similar_failure(original_failure, result.failure_info):
                    successful_reproductions += 1
        
        reproducibility_rate = successful_reproductions / self.verification_attempts
        is_reproducible = reproducibility_rate >= self.reproducibility_threshold
        
        return ReproducibilityResult(
            test_case_id=test_case.id,
            original_failure=original_failure,
            reproduction_attempts=self.verification_attempts,
            successful_reproductions=successful_reproductions,
            reproducibility_rate=reproducibility_rate,
            is_reproducible=is_reproducible
        )
    
    def _is_similar_failure(
        self,
        failure1: FailureInfo,
        failure2: FailureInfo
    ) -> bool:
        """Check if two failures are similar.
        
        Args:
            failure1: First failure
            failure2: Second failure
            
        Returns:
            True if failures are similar
        """
        # Check kernel panic match
        if failure1.kernel_panic != failure2.kernel_panic:
            return False
        
        # Check timeout match
        if failure1.timeout_occurred != failure2.timeout_occurred:
            return False
        
        # Check exit code match (if both present)
        if failure1.exit_code is not None and failure2.exit_code is not None:
            if failure1.exit_code != failure2.exit_code:
                return False
        
        # Check error message similarity (simple substring check)
        if failure1.error_message and failure2.error_message:
            # Extract key error terms
            error1_lower = failure1.error_message.lower()
            error2_lower = failure2.error_message.lower()
            
            # Check for common error keywords
            common_keywords = [
                "segfault", "panic", "oops", "bug", "null pointer",
                "memory", "timeout", "assertion", "failed"
            ]
            
            error1_keywords = [kw for kw in common_keywords if kw in error1_lower]
            error2_keywords = [kw for kw in common_keywords if kw in error2_lower]
            
            # If both have keywords, they should overlap
            if error1_keywords and error2_keywords:
                return bool(set(error1_keywords) & set(error2_keywords))
        
        # Default to similar if basic checks pass
        return True



class DeterministicTestExecutor:
    """Executes tests with deterministic seeding for reproducibility."""
    
    def __init__(self, base_seed: Optional[int] = None):
        """Initialize deterministic test executor.
        
        Args:
            base_seed: Base seed for deterministic execution
        """
        self.base_seed = base_seed or self._generate_seed()
    
    def _generate_seed(self) -> int:
        """Generate a seed based on current time.
        
        Returns:
            Integer seed
        """
        return int(time.time() * 1000) % (2**31)
    
    def get_test_seed(self, test_case: TestCase) -> int:
        """Get deterministic seed for a test case.
        
        Args:
            test_case: Test case
            
        Returns:
            Deterministic seed for this test
        """
        # Combine base seed with test case ID for determinism
        test_hash = hashlib.sha256(test_case.id.encode()).hexdigest()
        test_seed = int(test_hash[:8], 16)
        
        # XOR with base seed for uniqueness
        return self.base_seed ^ test_seed
    
    def prepare_test_environment(
        self,
        test_case: TestCase,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Prepare environment variables for deterministic execution.
        
        Args:
            test_case: Test case to execute
            environment_vars: Additional environment variables
            
        Returns:
            Dictionary of environment variables with seed set
        """
        env_vars = environment_vars.copy() if environment_vars else {}
        
        # Set deterministic seed
        test_seed = self.get_test_seed(test_case)
        env_vars['RANDOM_SEED'] = str(test_seed)
        env_vars['PYTHONHASHSEED'] = str(test_seed)
        
        # Set other determinism flags
        env_vars['DETERMINISTIC_MODE'] = '1'
        
        return env_vars
    
    def set_random_seed(self, test_case: TestCase):
        """Set random seed for deterministic execution.
        
        Args:
            test_case: Test case
        """
        seed = self.get_test_seed(test_case)
        random.seed(seed)
    
    def get_reproducible_test_case(
        self,
        test_case: TestCase
    ) -> TestCase:
        """Create a test case with embedded seed for reproducibility.
        
        Args:
            test_case: Original test case
            
        Returns:
            Test case with seed metadata
        """
        seed = self.get_test_seed(test_case)
        
        # Add seed to metadata
        metadata = test_case.metadata.copy()
        metadata['seed'] = seed
        metadata['deterministic'] = True
        
        return TestCase(
            id=test_case.id,
            name=test_case.name,
            description=test_case.description,
            test_type=test_case.test_type,
            target_subsystem=test_case.target_subsystem,
            code_paths=test_case.code_paths,
            execution_time_estimate=test_case.execution_time_estimate,
            required_hardware=test_case.required_hardware,
            test_script=test_case.test_script,
            expected_outcome=test_case.expected_outcome,
            metadata=metadata
        )


class ReproducibleTestSystem:
    """Unified system for reproducible test case generation."""
    
    def __init__(
        self,
        minimizer: Optional[TestCaseMinimizer] = None,
        verifier: Optional[ReproducibilityVerifier] = None,
        executor: Optional[DeterministicTestExecutor] = None
    ):
        """Initialize reproducible test system.
        
        Args:
            minimizer: Test case minimizer
            verifier: Reproducibility verifier
            executor: Deterministic test executor
        """
        self.minimizer = minimizer or TestCaseMinimizer()
        self.verifier = verifier or ReproducibilityVerifier()
        self.executor = executor or DeterministicTestExecutor()
    
    def process_failure(
        self,
        test_case: TestCase,
        failure_info: FailureInfo,
        failure_checker: Callable[[TestCase], bool],
        test_executor: Callable[[TestCase], TestResult]
    ) -> Dict[str, Any]:
        """Process a test failure to create reproducible, minimized test case.
        
        Args:
            test_case: Original failing test case
            failure_info: Failure information
            failure_checker: Function to check if test still fails
            test_executor: Function to execute test
            
        Returns:
            Dictionary with minimized test, reproducibility result, and seed
        """
        # Make test deterministic
        reproducible_test = self.executor.get_reproducible_test_case(test_case)
        
        # Minimize the test case
        minimized = self.minimizer.minimize(reproducible_test, failure_checker)
        
        # Verify reproducibility
        reproducibility = self.verifier.verify(
            minimized.minimized_test,
            failure_info,
            test_executor
        )
        
        return {
            'original_test': test_case,
            'reproducible_test': reproducible_test,
            'minimized_test': minimized.minimized_test,
            'minimization_result': minimized,
            'reproducibility_result': reproducibility,
            'seed': self.executor.get_test_seed(test_case),
            'is_reproducible': reproducibility.is_reproducible,
            'reduction_ratio': minimized.reduction_ratio
        }
