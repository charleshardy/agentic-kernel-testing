"""Property-based tests for test generation quantity.

Feature: agentic-kernel-testing, Property 4: Test generation quantity
Validates: Requirements 1.4
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from ai_generator.test_generator import AITestGenerator
from ai_generator.models import Function, CodeAnalysis, TestType, RiskLevel
from ai_generator.llm_providers import BaseLLMProvider, LLMResponse
from typing import List


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.call_count = 0
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate mock response with test cases."""
        self.call_count += 1
        
        # Generate 10+ test cases in response with unique names per call
        test_cases = []
        call_id = self.call_count
        for i in range(12):  # Generate 12 tests to ensure we meet minimum
            test_cases.append({
                "name": f"Test case {call_id}_{i + 1}",
                "description": f"Test description {call_id}_{i + 1}",
                "test_script": f"def test_{call_id}_{i}():\n    assert True",
                "expected_outcome": {"should_pass": True},
                "execution_time": 30
            })
        
        import json
        content = json.dumps(test_cases)
        
        return LLMResponse(
            content=content,
            model="mock-model",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )


# Strategy for generating valid function objects
@st.composite
def function_strategy(draw):
    """Generate Function objects."""
    name = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), whitelist_characters='_'),
        min_size=1,
        max_size=30
    ))
    
    subsystems = ['scheduler', 'memory', 'filesystem', 'networking', 'drivers']
    subsystem = draw(st.sampled_from(subsystems))
    
    file_path = f"kernel/{subsystem}/{name}.c"
    line_number = draw(st.integers(min_value=1, max_value=10000))
    
    return Function(
        name=name,
        file_path=file_path,
        line_number=line_number,
        subsystem=subsystem
    )


@st.composite
def code_analysis_strategy(draw):
    """Generate CodeAnalysis objects with functions."""
    num_functions = draw(st.integers(min_value=1, max_value=5))
    functions = [draw(function_strategy()) for _ in range(num_functions)]
    
    # Extract subsystems from functions
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
class TestTestGenerationQuantityProperties:
    """Property-based tests for test generation quantity."""
    
    @given(analysis=code_analysis_strategy())
    @settings(max_examples=100)
    def test_minimum_tests_per_function(self, analysis):
        """
        Property 4: Test generation quantity
        
        For any modified function in a code change, the system should generate 
        at least 10 distinct test cases targeting that function.
        
        This property verifies that:
        1. Each function gets at least 10 test cases
        2. Test cases are distinct (different names/descriptions)
        3. All test cases target the correct function
        """
        # Skip if no functions (edge case)
        assume(len(analysis.changed_functions) > 0)
        
        # Create generator with mock LLM
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        # Generate test cases
        test_cases = generator.generate_test_cases(analysis)
        
        # Property 1: Should generate at least 10 tests per unique function
        unique_functions = list({f.name: f for f in analysis.changed_functions}.values())
        min_expected_tests = len(unique_functions) * 10
        assert len(test_cases) >= min_expected_tests, \
            f"Expected at least {min_expected_tests} tests for {len(unique_functions)} unique functions, " \
            f"but got {len(test_cases)}"
        
        # Property 2: Test cases should be distinct (allowing for duplicate functions)
        # If we have duplicate functions, we may have duplicate test names
        # What matters is that each unique function gets its tests
        unique_functions = list({f.name: f for f in analysis.changed_functions}.values())
        test_names = [tc.name for tc in test_cases]
        
        # For unique functions, we should have unique test sets
        # But duplicate functions can generate duplicate tests
        if len(unique_functions) == len(analysis.changed_functions):
            # No duplicates, test names should be unique
            assert len(test_names) == len(set(test_names)), \
                "Test cases should have unique names when functions are unique"
        
        # Property 3: Each unique function should have at least 10 tests targeting it
        unique_functions = list({f.name: f for f in analysis.changed_functions}.values())
        for function in unique_functions:
            function_tests = [
                tc for tc in test_cases
                if tc.code_paths and function.name in tc.code_paths[0]
            ]
            assert len(function_tests) >= 10, \
                f"Function {function.name} should have at least 10 tests, got {len(function_tests)}"
        
        # Property 4: All test cases should have valid test scripts
        for tc in test_cases:
            assert tc.test_script, "Test case should have non-empty test script"
            assert len(tc.test_script.strip()) > 0, "Test script should not be just whitespace"
    
    @given(function=function_strategy())
    @settings(max_examples=100)
    def test_single_function_test_generation(self, function):
        """
        Property: Single function should generate exactly 10+ tests.
        
        When generating tests for a single function, the system should produce
        at least 10 distinct test cases.
        """
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        # Generate tests for single function
        test_cases = generator._generate_function_tests(function, min_tests=10)
        
        # Should have at least 10 tests
        assert len(test_cases) >= 10, \
            f"Should generate at least 10 tests for function {function.name}, got {len(test_cases)}"
        
        # All tests should target this function
        for tc in test_cases:
            assert tc.target_subsystem == function.subsystem, \
                f"Test should target subsystem {function.subsystem}"
            assert any(function.name in path for path in tc.code_paths), \
                f"Test should reference function {function.name} in code paths"
    
    @given(
        functions=st.lists(function_strategy(), min_size=1, max_size=10)
    )
    @settings(max_examples=100)
    def test_test_quantity_scales_with_functions(self, functions):
        """
        Property: Test quantity should scale linearly with number of functions.
        
        If we have N functions, we should get at least N * 10 tests.
        """
        # Create analysis with these functions
        subsystems = list(set(f.subsystem for f in functions))
        files = list(set(f.file_path for f in functions))
        
        analysis = CodeAnalysis(
            changed_files=files,
            changed_functions=functions,
            affected_subsystems=subsystems,
            impact_score=0.5,
            risk_level=RiskLevel.MEDIUM,
            suggested_test_types=[TestType.UNIT]
        )
        
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        test_cases = generator.generate_test_cases(analysis)
        
        # Should have at least 10 tests per function
        min_expected = len(functions) * 10
        assert len(test_cases) >= min_expected, \
            f"Expected at least {min_expected} tests for {len(functions)} functions, " \
            f"got {len(test_cases)}"
    
    @given(analysis=code_analysis_strategy())
    @settings(max_examples=100)
    def test_test_case_validity(self, analysis):
        """
        Property: All generated test cases should be valid.
        
        Every test case generated should pass validation checks.
        """
        assume(len(analysis.changed_functions) > 0)
        
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        test_cases = generator.generate_test_cases(analysis)
        
        # All test cases should be valid
        for tc in test_cases:
            assert generator.validator.validate(tc), \
                f"Test case {tc.name} should be valid"
            
            # Check required fields
            assert tc.id, "Test case should have ID"
            assert tc.name, "Test case should have name"
            assert tc.description, "Test case should have description"
            assert tc.test_script, "Test case should have test script"
            assert tc.target_subsystem, "Test case should have target subsystem"
            assert tc.execution_time_estimate > 0, "Execution time should be positive"
    
    @given(
        function=function_strategy(),
        min_tests=st.integers(min_value=10, max_value=20)
    )
    @settings(max_examples=50)
    def test_respects_minimum_test_count(self, function, min_tests):
        """
        Property: Generator should respect the minimum test count parameter.
        
        When asked to generate N tests, should generate at least N tests.
        """
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        test_cases = generator._generate_function_tests(function, min_tests=min_tests)
        
        assert len(test_cases) >= min_tests, \
            f"Should generate at least {min_tests} tests, got {len(test_cases)}"
    
    @given(analysis=code_analysis_strategy())
    @settings(max_examples=100)
    def test_test_distribution_across_functions(self, analysis):
        """
        Property: Tests should be distributed across all functions.
        
        No function should be left without tests.
        """
        assume(len(analysis.changed_functions) > 0)
        
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        test_cases = generator.generate_test_cases(analysis)
        
        # Every function should have at least one test
        for function in analysis.changed_functions:
            function_tests = [
                tc for tc in test_cases
                if any(function.name in path for path in tc.code_paths)
            ]
            assert len(function_tests) > 0, \
                f"Function {function.name} should have at least one test"
