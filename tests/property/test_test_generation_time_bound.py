"""Property-based tests for test generation time bound.

Feature: agentic-kernel-testing, Property 1: Test generation time bound
Validates: Requirements 1.1
"""

import pytest
import time
from hypothesis import given, strategies as st, settings, assume
from ai_generator.test_generator import AITestGenerator
from ai_generator.models import Function, CodeAnalysis, TestType, RiskLevel
from ai_generator.llm_providers import BaseLLMProvider, LLMResponse
from typing import List
import json


class TimedMockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that simulates realistic response times."""
    
    def __init__(self, response_time: float = 0.1, **kwargs):
        super().__init__(**kwargs)
        self.response_time = response_time
        self.call_count = 0
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate mock response with simulated delay."""
        self.call_count += 1
        
        # Simulate LLM response time
        time.sleep(self.response_time)
        
        # Generate test cases
        test_cases = []
        for i in range(10):
            test_cases.append({
                "name": f"Test case {i + 1}",
                "description": f"Test description {i + 1}",
                "test_script": f"def test_{i}():\n    assert True",
                "expected_outcome": {"should_pass": True}
            })
        
        content = json.dumps(test_cases)
        
        return LLMResponse(
            content=content,
            model="mock-model",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )


@st.composite
def code_change_strategy(draw):
    """Generate code changes with varying complexity."""
    num_functions = draw(st.integers(min_value=1, max_value=10))
    
    functions = []
    for i in range(num_functions):
        name = f"func_{i}"
        subsystem = draw(st.sampled_from(['scheduler', 'memory', 'filesystem', 'networking']))
        
        functions.append(Function(
            name=name,
            file_path=f"kernel/{subsystem}/{name}.c",
            line_number=draw(st.integers(min_value=1, max_value=1000)),
            subsystem=subsystem
        ))
    
    subsystems = list(set(f.subsystem for f in functions))
    files = list(set(f.file_path for f in functions))
    
    return CodeAnalysis(
        changed_files=files,
        changed_functions=functions,
        affected_subsystems=subsystems,
        impact_score=draw(st.floats(min_value=0.0, max_value=1.0)),
        risk_level=draw(st.sampled_from(list(RiskLevel))),
        suggested_test_types=[TestType.UNIT]
    )


@pytest.mark.property
class TestTestGenerationTimeBoundProperties:
    """Property-based tests for test generation time bound."""
    
    @given(analysis=code_change_strategy())
    @settings(max_examples=10, deadline=5000)  # 5 second deadline per example
    def test_generation_completes_within_time_bound(self, analysis):
        """
        Property 1: Test generation time bound
        
        For any code change committed by a developer, the system should analyze 
        the code and generate relevant test cases within 5 minutes (300 seconds).
        
        This property verifies that:
        1. Test generation completes within the time limit
        2. Time scales reasonably with code complexity
        3. System doesn't hang or timeout
        """
        assume(len(analysis.changed_functions) > 0)
        assume(len(analysis.changed_functions) <= 3)  # Limit for faster testing
        
        # Use fast mock LLM (0.01s per call for speed)
        mock_llm = TimedMockLLMProvider(response_time=0.01)
        generator = AITestGenerator(llm_provider=mock_llm)
        
        # Measure generation time
        start_time = time.time()
        test_cases = generator.generate_test_cases(analysis)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Property 1: Should complete within reasonable time
        # For testing with mock LLM, should be very fast
        max_time = 5  # 5 seconds for testing with fast mock
        assert generation_time < max_time, \
            f"Test generation took {generation_time:.2f}s, should be under {max_time}s"
        
        # Property 2: Should generate valid test cases
        assert len(test_cases) > 0, "Should generate at least some test cases"
        
        # Property 3: Time should scale reasonably with complexity
        # More functions should not cause exponential time increase
        num_functions = len(analysis.changed_functions)
        time_per_function = generation_time / num_functions
        
        # Each function should take less than 2 seconds on average with fast mock
        assert time_per_function < 2.0, \
            f"Time per function ({time_per_function:.2f}s) is too high"
    
    @given(
        num_functions=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_time_scales_linearly_with_functions(self, num_functions):
        """
        Property: Generation time should scale linearly with number of functions.
        
        Doubling the number of functions should roughly double the time, not
        cause exponential growth.
        """
        # Create analysis with specified number of functions
        functions = [
            Function(
                name=f"func_{i}",
                file_path=f"kernel/test/func_{i}.c",
                line_number=100 + i,
                subsystem="test"
            )
            for i in range(num_functions)
        ]
        
        analysis = CodeAnalysis(
            changed_files=[f.file_path for f in functions],
            changed_functions=functions,
            affected_subsystems=["test"],
            impact_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            suggested_test_types=[TestType.UNIT]
        )
        
        mock_llm = TimedMockLLMProvider(response_time=0.05)
        generator = AITestGenerator(llm_provider=mock_llm)
        
        start_time = time.time()
        test_cases = generator.generate_test_cases(analysis)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Time should be roughly linear: O(n) not O(n^2) or O(2^n)
        # With 0.05s per LLM call and ~1 call per function, expect ~0.05s * num_functions
        expected_max_time = 0.1 * num_functions + 2  # 2s overhead
        
        assert generation_time < expected_max_time, \
            f"Generation time {generation_time:.2f}s exceeds linear expectation {expected_max_time:.2f}s"
        
        # Should still generate tests
        assert len(test_cases) >= num_functions * 10, \
            "Should generate at least 10 tests per function"
    
    @given(analysis=code_change_strategy())
    @settings(max_examples=20, deadline=10000)  # 10 second deadline per example
    def test_generation_does_not_hang(self, analysis):
        """
        Property: Test generation should always complete (no hangs).
        
        The system should never hang indefinitely, even with complex code changes.
        """
        assume(len(analysis.changed_functions) > 0)
        assume(len(analysis.changed_functions) <= 5)  # Limit complexity
        
        mock_llm = TimedMockLLMProvider(response_time=0.05)
        generator = AITestGenerator(llm_provider=mock_llm)
        
        # Just run generation - hypothesis will timeout if it hangs
        test_cases = generator.generate_test_cases(analysis)
        
        # Should complete successfully
        assert len(test_cases) > 0, "Should generate test cases"
    
    @given(
        analysis=code_change_strategy(),
        llm_response_time=st.floats(min_value=0.01, max_value=0.5)
    )
    @settings(max_examples=10, deadline=None)
    def test_handles_varying_llm_response_times(self, analysis, llm_response_time):
        """
        Property: System should handle varying LLM response times gracefully.
        
        Even if LLM is slow, system should still complete within reasonable time.
        """
        assume(len(analysis.changed_functions) > 0)
        assume(len(analysis.changed_functions) <= 5)  # Limit for reasonable test time
        
        mock_llm = TimedMockLLMProvider(response_time=llm_response_time)
        generator = AITestGenerator(llm_provider=mock_llm)
        
        start_time = time.time()
        test_cases = generator.generate_test_cases(analysis)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Should complete even with slow LLM
        # Max time should be roughly: num_functions * llm_response_time * calls_per_function + overhead
        num_functions = len(analysis.changed_functions)
        expected_max_time = num_functions * llm_response_time * 2 + 5  # 2 calls per function, 5s overhead
        
        assert generation_time < expected_max_time, \
            f"Generation time {generation_time:.2f}s exceeds expected {expected_max_time:.2f}s"
        
        # Should still generate valid tests
        assert len(test_cases) > 0, "Should generate test cases despite slow LLM"
    
    @given(analysis=code_change_strategy())
    @settings(max_examples=20, deadline=None)
    def test_generation_time_is_deterministic(self, analysis):
        """
        Property: Generation time should be relatively consistent for same input.
        
        Running generation twice on same input should take similar time.
        """
        assume(len(analysis.changed_functions) > 0)
        assume(len(analysis.changed_functions) <= 3)  # Keep test fast
        
        mock_llm = TimedMockLLMProvider(response_time=0.05)
        generator = AITestGenerator(llm_provider=mock_llm)
        
        # First run
        start_time_1 = time.time()
        test_cases_1 = generator.generate_test_cases(analysis)
        end_time_1 = time.time()
        time_1 = end_time_1 - start_time_1
        
        # Second run
        start_time_2 = time.time()
        test_cases_2 = generator.generate_test_cases(analysis)
        end_time_2 = time.time()
        time_2 = end_time_2 - start_time_2
        
        # Times should be within 50% of each other
        time_ratio = max(time_1, time_2) / min(time_1, time_2)
        assert time_ratio < 1.5, \
            f"Generation times should be consistent: {time_1:.2f}s vs {time_2:.2f}s"
        
        # Should generate similar number of tests
        assert abs(len(test_cases_1) - len(test_cases_2)) <= 2, \
            "Should generate similar number of tests on repeated runs"
