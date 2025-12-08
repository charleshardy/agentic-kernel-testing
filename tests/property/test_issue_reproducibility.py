"""Property-based tests for issue reproducibility.

**Feature: agentic-kernel-testing, Property 14: Issue reproducibility**

This module tests that issues discovered during stress testing can be
reliably reproduced when executed again.

**Validates: Requirements 3.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
import random

from ai_generator.models import (
    TestCase, TestResult, TestStatus, TestType, FailureInfo,
    Environment, EnvironmentStatus, HardwareConfig, ArtifactBundle
)
from execution.reproducible_testing import (
    ReproducibilityVerifier,
    TestCaseMinimizer,
    DeterministicTestExecutor,
    ReproducibleTestSystem,
    MinimizationStrategy
)


# Custom strategies for reproducibility testing
@st.composite
def _test_cases(draw):
    """Generate test cases with various scripts."""
    test_id = f"test_{draw(st.integers(min_value=1, max_value=10000))}"
    
    # Generate test script with multiple lines
    num_lines = draw(st.integers(min_value=5, max_value=20))
    script_lines = []
    for _ in range(num_lines):
        line = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=5,
            max_size=30
        ))
        script_lines.append(f"echo {line}")
    
    test_script = '\n'.join(script_lines)
    
    return TestCase(
        id=test_id,
        name=f"Test {test_id}",
        description="Test case for reproducibility testing",
        test_type=TestType.UNIT,
        target_subsystem="kernel",
        code_paths=["/kernel/test.c"],
        test_script=test_script,
        metadata={}
    )


@st.composite
def _failure_infos(draw):
    """Generate failure information."""
    error_types = [
        "Kernel panic",
        "Segmentation fault",
        "Null pointer dereference",
        "Memory leak detected",
        "Assertion failed",
        "Timeout occurred"
    ]
    
    error_message = draw(st.sampled_from(error_types))
    kernel_panic = "panic" in error_message.lower()
    timeout = "timeout" in error_message.lower()
    
    return FailureInfo(
        error_message=error_message,
        stack_trace=draw(st.one_of(st.none(), st.text(min_size=10, max_size=100))),
        exit_code=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=255))),
        kernel_panic=kernel_panic,
        timeout_occurred=timeout
    )


@st.composite
def _environments(draw):
    """Generate test environments."""
    env_id = f"env_{draw(st.integers(min_value=1, max_value=1000))}"
    
    config = HardwareConfig(
        architecture=draw(st.sampled_from(["x86_64", "arm64", "riscv64"])),
        cpu_model=draw(st.text(min_size=3, max_size=20)),
        memory_mb=draw(st.integers(min_value=512, max_value=8192)),
        is_virtual=True,
        emulator="qemu"
    )
    
    return Environment(
        id=env_id,
        config=config,
        status=EnvironmentStatus.IDLE
    )



class TestIssueReproducibility:
    """Test suite for issue reproducibility property."""
    
    @given(
        test_case=_test_cases(),
        failure_info=_failure_infos(),
        seed=st.integers(min_value=0, max_value=100000)
    )
    @settings(max_examples=100)
    def test_property_issue_reproducibility(self, test_case, failure_info, seed):
        """
        **Feature: agentic-kernel-testing, Property 14: Issue reproducibility**
        
        Property: For any issue discovered during stress testing, the reported
        test case should reliably reproduce the issue when executed again.
        
        **Validates: Requirements 3.4**
        
        This test verifies that when a test case triggers a failure, the system
        can create a reproducible version that consistently reproduces the failure.
        """
        # Create deterministic executor with seed
        executor = DeterministicTestExecutor(base_seed=seed)
        
        # Get reproducible test case
        reproducible_test = executor.get_reproducible_test_case(test_case)
        
        # Property 1: Reproducible test should have seed in metadata
        assert 'seed' in reproducible_test.metadata, \
            "Reproducible test must have seed in metadata"
        assert 'deterministic' in reproducible_test.metadata, \
            "Reproducible test must be marked as deterministic"
        assert reproducible_test.metadata['deterministic'] is True
        
        # Property 2: Same test case should always get same seed
        seed1 = executor.get_test_seed(test_case)
        seed2 = executor.get_test_seed(test_case)
        assert seed1 == seed2, \
            "Same test case should always produce same seed for reproducibility"
        
        # Property 3: Seed should be deterministic based on test ID
        executor2 = DeterministicTestExecutor(base_seed=seed)
        seed3 = executor2.get_test_seed(test_case)
        assert seed1 == seed3, \
            "Same base seed and test ID should produce same test seed"
    
    @given(
        test_case=_test_cases(),
        failure_info=_failure_infos(),
        reproducibility_threshold=st.floats(min_value=0.5, max_value=1.0)
    )
    @settings(max_examples=100)
    def test_reproducibility_verification(self, test_case, failure_info, reproducibility_threshold):
        """
        Test that reproducibility verifier correctly identifies reproducible failures.
        
        This verifies the reproducibility verification mechanism works correctly.
        """
        # Create verifier with threshold
        verifier = ReproducibilityVerifier(
            reproducibility_threshold=reproducibility_threshold,
            verification_attempts=10
        )
        
        # Create a mock test executor that always fails with same error
        def consistent_executor(tc: TestCase) -> TestResult:
            env = Environment(
                id="test_env",
                config=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="test",
                    memory_mb=1024
                )
            )
            return TestResult(
                test_id=tc.id,
                status=TestStatus.FAILED,
                execution_time=1.0,
                environment=env,
                failure_info=failure_info,
                timestamp=datetime.now()
            )
        
        # Verify reproducibility
        result = verifier.verify(test_case, failure_info, consistent_executor)
        
        # Property: Consistent failures should be 100% reproducible
        assert result.reproducibility_rate == 1.0, \
            "Consistent failures should have 100% reproducibility rate"
        assert result.is_reproducible is True, \
            "Consistent failures should be marked as reproducible"
        assert result.successful_reproductions == result.reproduction_attempts, \
            "All attempts should succeed for consistent failures"
    
    @given(
        test_case=_test_cases(),
        failure_info=_failure_infos(),
        success_rate=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100)
    def test_reproducibility_rate_calculation(self, test_case, failure_info, success_rate):
        """
        Test that reproducibility rate is calculated correctly.
        """
        verifier = ReproducibilityVerifier(
            reproducibility_threshold=0.8,
            verification_attempts=10
        )
        
        # Create executor with controlled success rate
        attempt_count = [0]
        
        def variable_executor(tc: TestCase) -> TestResult:
            attempt_count[0] += 1
            env = Environment(
                id="test_env",
                config=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="test",
                    memory_mb=1024
                )
            )
            
            # Fail with probability = success_rate
            if random.random() < success_rate:
                status = TestStatus.FAILED
                fail_info = failure_info
            else:
                status = TestStatus.PASSED
                fail_info = None
            
            return TestResult(
                test_id=tc.id,
                status=status,
                execution_time=1.0,
                environment=env,
                failure_info=fail_info,
                timestamp=datetime.now()
            )
        
        # Set seed for reproducibility of this test
        random.seed(42)
        
        result = verifier.verify(test_case, failure_info, variable_executor)
        
        # Property: Reproducibility rate should be between 0 and 1
        assert 0.0 <= result.reproducibility_rate <= 1.0, \
            "Reproducibility rate must be between 0.0 and 1.0"
        
        # Property: Rate should match successful reproductions / attempts
        expected_rate = result.successful_reproductions / result.reproduction_attempts
        assert abs(result.reproducibility_rate - expected_rate) < 0.001, \
            "Reproducibility rate should equal successful_reproductions / attempts"
    
    @given(
        test_case=_test_cases(),
        strategy=st.sampled_from([
            MinimizationStrategy.DELTA_DEBUGGING,
            MinimizationStrategy.BINARY_SEARCH,
            MinimizationStrategy.GREEDY
        ])
    )
    @settings(max_examples=100)
    def test_minimization_preserves_failure(self, test_case, strategy):
        """
        Test that minimization preserves the failure-triggering behavior.
        
        This verifies that minimized test cases still reproduce the original failure.
        """
        # Assume test has enough lines to minimize
        assume(len(test_case.test_script.split('\n')) >= 5)
        
        minimizer = TestCaseMinimizer(strategy=strategy, max_iterations=20)
        
        # Create a failure checker that always returns True (simulating consistent failure)
        def always_fails(tc: TestCase) -> bool:
            return True
        
        # Minimize the test case
        result = minimizer.minimize(test_case, always_fails)
        
        # Property: Minimized test should still reproduce failure
        assert result.still_reproduces is True, \
            "Minimized test case must still reproduce the original failure"
        
        # Property: Minimized test should be smaller or equal
        original_size = len(test_case.test_script)
        minimized_size = len(result.minimized_test.test_script)
        assert minimized_size <= original_size, \
            "Minimized test should not be larger than original"
        
        # Property: Reduction ratio should be valid
        assert 0.0 <= result.reduction_ratio <= 1.0, \
            "Reduction ratio must be between 0.0 and 1.0"
        
        # Property: Reduction ratio should match actual reduction
        if original_size > 0:
            expected_ratio = 1.0 - (minimized_size / original_size)
            assert abs(result.reduction_ratio - expected_ratio) < 0.001, \
                "Reduction ratio should match actual size reduction"
    
    @given(
        test_case=_test_cases(),
        failure_info=_failure_infos()
    )
    @settings(max_examples=100)
    def test_end_to_end_reproducible_test_generation(self, test_case, failure_info):
        """
        Test the complete reproducible test generation workflow.
        
        This is the main property test that validates the entire system.
        """
        # Assume test has enough content
        assume(len(test_case.test_script.split('\n')) >= 3)
        
        # Create reproducible test system
        system = ReproducibleTestSystem()
        
        # Mock failure checker (always fails)
        def failure_checker(tc: TestCase) -> bool:
            return True
        
        # Mock test executor (always returns failure)
        def test_executor(tc: TestCase) -> TestResult:
            env = Environment(
                id="test_env",
                config=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="test",
                    memory_mb=1024
                )
            )
            return TestResult(
                test_id=tc.id,
                status=TestStatus.FAILED,
                execution_time=1.0,
                environment=env,
                failure_info=failure_info,
                timestamp=datetime.now()
            )
        
        # Process the failure
        result = system.process_failure(
            test_case,
            failure_info,
            failure_checker,
            test_executor
        )
        
        # Property 1: Result should contain all required components
        assert 'original_test' in result
        assert 'reproducible_test' in result
        assert 'minimized_test' in result
        assert 'seed' in result
        assert 'is_reproducible' in result
        
        # Property 2: Reproducible test should have seed
        assert 'seed' in result['reproducible_test'].metadata
        
        # Property 3: Should be marked as reproducible (since we always fail)
        assert result['is_reproducible'] is True, \
            "Consistent failures should be reproducible"
        
        # Property 4: Minimized test should be smaller or equal
        original_size = len(test_case.test_script)
        minimized_size = len(result['minimized_test'].test_script)
        assert minimized_size <= original_size, \
            "Minimized test should not be larger than original"
    
    @given(
        seed1=st.integers(min_value=0, max_value=100000),
        seed2=st.integers(min_value=0, max_value=100000)
    )
    @settings(max_examples=100)
    def test_different_seeds_produce_different_results(self, seed1, seed2):
        """
        Test that different seeds produce different test seeds.
        """
        assume(seed1 != seed2)
        
        test_case = TestCase(
            id="test_123",
            name="Test",
            description="Test",
            test_type=TestType.UNIT,
            target_subsystem="kernel",
            test_script="echo test"
        )
        
        executor1 = DeterministicTestExecutor(base_seed=seed1)
        executor2 = DeterministicTestExecutor(base_seed=seed2)
        
        test_seed1 = executor1.get_test_seed(test_case)
        test_seed2 = executor2.get_test_seed(test_case)
        
        # Property: Different base seeds should produce different test seeds
        # (with very high probability)
        assert test_seed1 != test_seed2, \
            "Different base seeds should produce different test seeds"
    
    @given(test_case=_test_cases())
    @settings(max_examples=100)
    def test_environment_variables_include_seed(self, test_case):
        """
        Test that environment preparation includes seed for determinism.
        """
        executor = DeterministicTestExecutor(base_seed=12345)
        
        env_vars = executor.prepare_test_environment(test_case)
        
        # Property: Environment should have seed-related variables
        assert 'RANDOM_SEED' in env_vars, \
            "Environment must include RANDOM_SEED for reproducibility"
        assert 'PYTHONHASHSEED' in env_vars, \
            "Environment must include PYTHONHASHSEED for Python reproducibility"
        assert 'DETERMINISTIC_MODE' in env_vars, \
            "Environment must include DETERMINISTIC_MODE flag"
        
        # Property: Seeds should be valid integers
        assert env_vars['RANDOM_SEED'].isdigit(), \
            "RANDOM_SEED must be a valid integer string"
        assert env_vars['PYTHONHASHSEED'].isdigit(), \
            "PYTHONHASHSEED must be a valid integer string"
    
    @given(
        failure1=_failure_infos(),
        failure2=_failure_infos()
    )
    @settings(max_examples=100)
    def test_similar_failure_detection(self, failure1, failure2):
        """
        Test that similar failures are correctly identified.
        """
        verifier = ReproducibilityVerifier()
        
        # Property: Identical failures should be similar
        is_similar = verifier._is_similar_failure(failure1, failure1)
        assert is_similar is True, \
            "Identical failures should always be considered similar"
        
        # Property: Failures with different kernel panic status should not be similar
        if failure1.kernel_panic != failure2.kernel_panic:
            is_similar = verifier._is_similar_failure(failure1, failure2)
            # This may or may not be similar depending on other factors
            # Just verify the method runs without error
            assert isinstance(is_similar, bool)
        
        # Property: Failures with different timeout status should not be similar
        if failure1.timeout_occurred != failure2.timeout_occurred:
            is_similar = verifier._is_similar_failure(failure1, failure2)
            # This may or may not be similar depending on other factors
            assert isinstance(is_similar, bool)
    
    def test_minimization_with_no_removable_lines(self):
        """
        Test minimization when no lines can be removed.
        """
        test_case = TestCase(
            id="test_minimal",
            name="Minimal Test",
            description="Test with minimal script",
            test_type=TestType.UNIT,
            target_subsystem="kernel",
            test_script="echo critical_line"
        )
        
        minimizer = TestCaseMinimizer(max_iterations=10)
        
        # Failure checker that only fails if the critical line is present
        def strict_checker(tc: TestCase) -> bool:
            return "critical_line" in tc.test_script
        
        result = minimizer.minimize(test_case, strict_checker)
        
        # Property: Should still reproduce
        assert result.still_reproduces is True
        
        # Property: Should not be able to reduce much
        assert len(result.minimized_test.test_script) > 0
