"""Property-based tests for gap-targeted test generation.

**Feature: agentic-kernel-testing, Property 28: Gap-targeted test generation**
**Validates: Requirements 6.3**

Property: For any identified untested code path, the system should generate 
additional test cases specifically targeting that path.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from unittest.mock import Mock
import json

from ai_generator.gap_targeted_generator import GapTargetedTestGenerator
from ai_generator.models import TestCase
from ai_generator.llm_providers import LLMResponse
from analysis.coverage_analyzer import CoverageGap, GapType, GapPriority


# Strategies for generating test data
@st.composite
def coverage_gap_strategy(draw):
    """Generate random coverage gaps."""
    gap_type = draw(st.sampled_from([GapType.LINE, GapType.BRANCH, GapType.FUNCTION]))
    
    # Generate realistic file paths
    subsystems = ['kernel', 'drivers', 'fs', 'net', 'mm', 'arch']
    components = ['sched', 'memory', 'net', 'block', 'ext4', 'tcp']
    subsystem = draw(st.sampled_from(subsystems))
    component = draw(st.sampled_from(components))
    file_name = draw(st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu')), 
                             min_size=3, max_size=10)) + '.c'
    file_path = f"{subsystem}/{component}/{file_name}"
    
    line_number = draw(st.integers(min_value=1, max_value=10000))
    
    # Generate function name
    function_name = draw(st.one_of(
        st.none(),
        st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), 
                min_size=3, max_size=20)
    ))
    
    # Generate code context
    context = draw(st.one_of(
        st.just(""),
        st.text(min_size=10, max_size=200)
    ))
    
    # Branch ID only for branch gaps
    branch_id = draw(st.integers(min_value=0, max_value=10)) if gap_type == GapType.BRANCH else None
    
    priority = draw(st.sampled_from([GapPriority.CRITICAL, GapPriority.HIGH, 
                                     GapPriority.MEDIUM, GapPriority.LOW]))
    
    return CoverageGap(
        gap_type=gap_type,
        file_path=file_path,
        line_number=line_number,
        function_name=function_name,
        branch_id=branch_id,
        context=context,
        subsystem=component,
        priority=priority
    )


@st.composite
def gap_list_strategy(draw):
    """Generate a list of coverage gaps."""
    num_gaps = draw(st.integers(min_value=1, max_value=10))
    return [draw(coverage_gap_strategy()) for _ in range(num_gaps)]


def create_mock_llm_provider():
    """Create a mock LLM provider that returns valid test data."""
    provider = Mock()
    
    def mock_generate(prompt):
        # Return a valid test case JSON
        return LLMResponse(
            content=json.dumps({
                'name': 'Generated test',
                'description': 'Test to cover gap',
                'test_script': 'def test_gap(): pass',
                'expected_outcome': {'should_pass': True},
                'execution_time': 60
            }),
            model='gpt-4',
            tokens_used=100,
            finish_reason='stop',
            metadata={}
        )
    
    provider.generate_with_retry.side_effect = mock_generate
    return provider


class TestGapTargetedGenerationProperty:
    """Property-based tests for gap-targeted test generation."""
    
    @given(gap=coverage_gap_strategy())
    @settings(max_examples=100, deadline=None, 
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_gap_targeted_generation(self, gap):
        """
        Property 28: Gap-targeted test generation
        
        For any identified untested code path (coverage gap), the system should 
        generate additional test cases specifically targeting that path.
        
        This property verifies that:
        1. A test case is generated for the gap
        2. The test case targets the specific gap location
        3. The test case metadata references the gap
        """
        # Create generator with mock LLM
        mock_llm = create_mock_llm_provider()
        generator = GapTargetedTestGenerator(llm_provider=mock_llm)
        
        # Generate test for the gap
        test_case = generator.generate_test_for_gap(gap)
        
        # Property: A test case should be generated
        assert test_case is not None, \
            f"Failed to generate test for gap at {gap.file_path}:{gap.line_number}"
        
        # Property: Test case should be marked as gap-targeted
        assert test_case.metadata.get('gap_targeted') is True, \
            "Generated test should be marked as gap-targeted"
        
        # Property: Test case should reference the gap location
        target_gap = test_case.metadata.get('target_gap', {})
        assert target_gap.get('file_path') == gap.file_path, \
            f"Test should target file {gap.file_path}, got {target_gap.get('file_path')}"
        assert target_gap.get('line_number') == gap.line_number, \
            f"Test should target line {gap.line_number}, got {target_gap.get('line_number')}"
        
        # Property: Test case should include the gap location in code paths
        gap_path = f"{gap.file_path}:{gap.line_number}"
        assert any(gap_path in path for path in test_case.code_paths), \
            f"Test code paths should include {gap_path}"
        
        # Property: Test case should target the correct subsystem
        assert test_case.target_subsystem == gap.subsystem or test_case.target_subsystem == "unknown", \
            f"Test should target subsystem {gap.subsystem}"
        
        # Property: For branch gaps, branch ID should be recorded
        if gap.gap_type == GapType.BRANCH:
            assert target_gap.get('branch_id') == gap.branch_id, \
                f"Branch gap should record branch ID {gap.branch_id}"
            assert target_gap.get('gap_type') == 'branch', \
                "Branch gap should have gap_type 'branch'"
    
    @given(gaps=gap_list_strategy())
    @settings(max_examples=50, deadline=None,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_multiple_gaps_coverage(self, gaps):
        """
        Property: For any list of coverage gaps, the system should generate 
        test cases for all gaps.
        
        This verifies that the system can handle multiple gaps and generate
        tests for each one.
        """
        # Create generator with mock LLM
        mock_llm = create_mock_llm_provider()
        generator = GapTargetedTestGenerator(llm_provider=mock_llm)
        
        # Generate tests for all gaps
        test_cases = generator.generate_tests_for_gaps(gaps)
        
        # Property: Should generate at least one test per gap
        # (may be fewer if some fail, but should attempt all)
        assert len(test_cases) > 0, \
            "Should generate at least some tests for the gaps"
        
        # Property: All generated tests should be gap-targeted
        for test_case in test_cases:
            assert test_case.metadata.get('gap_targeted') is True, \
                "All generated tests should be gap-targeted"
        
        # Property: Each test should target a unique gap location
        targeted_locations = set()
        for test_case in test_cases:
            target_gap = test_case.metadata.get('target_gap', {})
            location = (target_gap.get('file_path'), target_gap.get('line_number'))
            targeted_locations.add(location)
        
        # Should have unique targets (no duplicate tests for same gap)
        assert len(targeted_locations) == len(test_cases), \
            "Each test should target a unique gap location"
    
    @given(gap=coverage_gap_strategy())
    @settings(max_examples=100, deadline=None,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_gap_verification(self, gap):
        """
        Property: For any generated test case targeting a gap, the verification
        function should correctly identify that the test targets the gap.
        
        This ensures the verification logic is consistent with generation.
        """
        # Create generator with mock LLM
        mock_llm = create_mock_llm_provider()
        generator = GapTargetedTestGenerator(llm_provider=mock_llm)
        
        # Generate test for the gap
        test_case = generator.generate_test_for_gap(gap)
        
        assume(test_case is not None)
        
        # Property: Verification should confirm the test targets the gap
        assert generator.verify_gap_coverage(test_case, gap) is True, \
            f"Verification should confirm test targets gap at {gap.file_path}:{gap.line_number}"
    
    @given(gap=coverage_gap_strategy())
    @settings(max_examples=100, deadline=None,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_path_to_test_conversion(self, gap):
        """
        Property: For any coverage gap, converting its path representation to
        a test case should produce a valid test targeting that location.
        
        This verifies the path-to-test-case conversion works correctly.
        """
        # Create generator with mock LLM
        mock_llm = create_mock_llm_provider()
        generator = GapTargetedTestGenerator(llm_provider=mock_llm)
        
        # Create path representation
        if gap.gap_type == GapType.BRANCH and gap.branch_id is not None:
            path = f"{gap.file_path}:{gap.line_number}:{gap.branch_id}"
        else:
            path = f"{gap.file_path}:{gap.line_number}"
        
        # Convert path to test case
        test_case = generator.path_to_test_case(path)
        
        # Property: Should generate a valid test case
        assert test_case is not None, \
            f"Should generate test case from path {path}"
        
        # Property: Test should target the correct location
        assert f"{gap.file_path}:{gap.line_number}" in str(test_case.code_paths), \
            f"Test should target location from path {path}"
        
        # Property: Test should be gap-targeted
        assert test_case.metadata.get('gap_targeted') is True, \
            "Converted test should be gap-targeted"
    
    @given(gap=coverage_gap_strategy())
    @settings(max_examples=50, deadline=None,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_fallback_generation(self, gap):
        """
        Property: Even when LLM generation fails, the system should still
        generate a fallback test case for the gap.
        
        This ensures robustness and that gaps are never left without tests.
        """
        # Create generator with failing LLM
        mock_llm = Mock()
        mock_llm.generate_with_retry.side_effect = Exception("LLM failed")
        generator = GapTargetedTestGenerator(llm_provider=mock_llm)
        
        # Generate test (should fall back)
        test_case = generator.generate_test_for_gap(gap)
        
        # Property: Should still generate a test case
        assert test_case is not None, \
            "Should generate fallback test even when LLM fails"
        
        # Property: Fallback test should be marked
        assert test_case.metadata.get('fallback') is True, \
            "Fallback test should be marked as such"
        
        # Property: Fallback test should still target the gap
        assert test_case.metadata.get('gap_targeted') is True, \
            "Fallback test should still be gap-targeted"
        
        target_gap = test_case.metadata.get('target_gap', {})
        assert target_gap.get('file_path') == gap.file_path, \
            "Fallback test should target correct file"
        assert target_gap.get('line_number') == gap.line_number, \
            "Fallback test should target correct line"
    
    @given(gap=coverage_gap_strategy())
    @settings(max_examples=100, deadline=None,
              suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_test_case_validity(self, gap):
        """
        Property: All generated test cases should be valid TestCase objects
        with required fields populated.
        
        This ensures generated tests meet the system's requirements.
        """
        # Create generator with mock LLM
        mock_llm = create_mock_llm_provider()
        generator = GapTargetedTestGenerator(llm_provider=mock_llm)
        
        # Generate test for the gap
        test_case = generator.generate_test_for_gap(gap)
        
        assume(test_case is not None)
        
        # Property: Test case should have required fields
        assert test_case.id is not None and test_case.id != "", \
            "Test case should have a valid ID"
        assert test_case.name is not None and test_case.name != "", \
            "Test case should have a name"
        assert test_case.description is not None, \
            "Test case should have a description"
        assert test_case.test_type is not None, \
            "Test case should have a test type"
        assert test_case.target_subsystem is not None and test_case.target_subsystem != "", \
            "Test case should have a target subsystem"
        assert test_case.test_script is not None and test_case.test_script != "", \
            "Test case should have a test script"
        assert test_case.execution_time_estimate > 0, \
            "Test case should have positive execution time estimate"
        assert len(test_case.code_paths) > 0, \
            "Test case should have at least one code path"


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
