"""Integration tests for AI test generator."""

import pytest
from ai_generator.test_generator import AITestGenerator
from ai_generator.models import Function, CodeAnalysis, TestType, RiskLevel
from ai_generator.llm_providers import BaseLLMProvider, LLMResponse
import json


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for integration testing."""
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate mock response based on prompt type."""
        # Check if this is an analysis request
        if "analyze" in prompt.lower() or "diff" in prompt.lower():
            # Return code analysis
            analysis_data = {
                "changed_files": ["kernel/sched/core.c"],
                "changed_functions": [
                    {
                        "name": "schedule",
                        "file_path": "kernel/sched/core.c",
                        "line_number": 100,
                        "subsystem": "scheduler"
                    }
                ],
                "affected_subsystems": ["scheduler"],
                "impact_score": 0.7,
                "risk_level": "medium",
                "suggested_test_types": ["unit", "integration"]
            }
            return LLMResponse(
                content=json.dumps(analysis_data),
                model="mock-model",
                tokens_used=100,
                finish_reason="stop",
                metadata={}
            )
        else:
            # Generate comprehensive test cases
            test_cases = []
            for i in range(12):
                test_cases.append({
                    "name": f"Integration test {i + 1}",
                    "description": f"Test description {i + 1}",
                    "test_script": f"def test_{i}():\n    assert True",
                    "expected_outcome": {"should_pass": True},
                    "execution_time": 30
                })
            
            return LLMResponse(
                content=json.dumps(test_cases),
                model="mock-model",
                tokens_used=100,
                finish_reason="stop",
                metadata={}
            )


@pytest.mark.integration
class TestAIGeneratorIntegration:
    """Integration tests for the AI test generator."""
    
    def test_end_to_end_test_generation(self):
        """Test complete workflow from code analysis to test generation."""
        # Setup
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        # Sample diff
        diff = """
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -100,6 +100,10 @@ void schedule(void)
     struct task_struct *prev, *next;
     
     prev = current;
+    
+    /* New scheduling logic */
+    if (prev->policy == SCHED_FIFO)
+        return;
     
     next = pick_next_task(rq);
     context_switch(prev, next);
"""
        
        # Step 1: Analyze code changes
        analysis = generator.analyze_code_changes(diff)
        
        # Verify analysis
        assert analysis is not None
        assert len(analysis.changed_files) > 0
        assert analysis.impact_score >= 0.0
        assert analysis.impact_score <= 1.0
        
        # Step 2: Generate test cases
        test_cases = generator.generate_test_cases(analysis)
        
        # Verify test generation
        assert len(test_cases) > 0
        
        # Verify all tests are valid
        for tc in test_cases:
            assert tc.id
            assert tc.name
            assert tc.description
            assert tc.test_script
            assert tc.test_type in TestType
            assert tc.execution_time_estimate > 0
    
    def test_multiple_function_test_generation(self):
        """Test generating tests for multiple functions."""
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        # Create analysis with multiple functions
        functions = [
            Function(
                name="schedule",
                file_path="kernel/sched/core.c",
                line_number=100,
                subsystem="scheduler"
            ),
            Function(
                name="pick_next_task",
                file_path="kernel/sched/core.c",
                line_number=200,
                subsystem="scheduler"
            )
        ]
        
        analysis = CodeAnalysis(
            changed_files=["kernel/sched/core.c"],
            changed_functions=functions,
            affected_subsystems=["scheduler"],
            impact_score=0.7,
            risk_level=RiskLevel.MEDIUM,
            suggested_test_types=[TestType.UNIT]
        )
        
        # Generate tests
        test_cases = generator.generate_test_cases(analysis)
        
        # Should generate at least 10 tests per function
        assert len(test_cases) >= 20
        
        # Verify tests target the functions
        function_names = {f.name for f in functions}
        for tc in test_cases:
            # At least one code path should reference a function
            assert len(tc.code_paths) > 0
    
    def test_property_test_generation(self):
        """Test property-based test generation."""
        # Create a mock that returns property test format
        class PropertyMockLLM(BaseLLMProvider):
            def generate(self, prompt: str, **kwargs) -> LLMResponse:
                property_test = {
                    "name": "Property test for hash_function",
                    "description": "Test that hash is deterministic",
                    "test_script": "def test_hash_property():\n    assert hash(x) == hash(x)"
                }
                return LLMResponse(
                    content=json.dumps(property_test),
                    model="mock",
                    tokens_used=50,
                    finish_reason="stop",
                    metadata={}
                )
        
        mock_llm = PropertyMockLLM()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        functions = [
            Function(
                name="hash_function",
                file_path="lib/hash.c",
                line_number=50,
                subsystem="library"
            )
        ]
        
        # Generate property tests
        property_tests = generator.generate_property_tests(functions)
        
        # Should generate property tests
        assert len(property_tests) > 0
        
        # Verify property test characteristics
        for tc in property_tests:
            assert tc.test_type == TestType.UNIT
            assert "property" in tc.metadata or "property_based" in tc.metadata
    
    def test_test_validation(self):
        """Test that generated tests pass validation."""
        mock_llm = MockLLMProvider()
        generator = AITestGenerator(llm_provider=mock_llm)
        
        function = Function(
            name="test_func",
            file_path="test.c",
            line_number=10,
            subsystem="test"
        )
        
        analysis = CodeAnalysis(
            changed_files=["test.c"],
            changed_functions=[function],
            affected_subsystems=["test"],
            impact_score=0.5,
            risk_level=RiskLevel.LOW,
            suggested_test_types=[TestType.UNIT]
        )
        
        test_cases = generator.generate_test_cases(analysis)
        
        # All generated tests should pass validation
        for tc in test_cases:
            assert generator.validator.validate(tc), \
                f"Test case {tc.name} failed validation"
    
    def test_fallback_when_llm_fails(self):
        """Test that system falls back gracefully when LLM fails."""
        # Create a failing LLM provider
        class FailingLLMProvider(BaseLLMProvider):
            def generate(self, prompt: str, **kwargs) -> LLMResponse:
                raise Exception("LLM failed")
        
        failing_llm = FailingLLMProvider()
        generator = AITestGenerator(llm_provider=failing_llm)
        
        function = Function(
            name="test_func",
            file_path="test.c",
            line_number=10,
            subsystem="test"
        )
        
        # Should still generate fallback tests
        tests = generator._generate_function_tests(function, min_tests=10)
        
        # Should have fallback tests
        assert len(tests) >= 10
        
        # Fallback tests should be valid
        for tc in tests:
            assert generator.validator.validate(tc)
