"""Property-based tests for test summary organization.

**Feature: agentic-kernel-testing, Property 5: Test summary organization**
**Validates: Requirements 1.5**

Property: For any completed test generation, the summary should organize tests 
by subsystem and test type, with all generated tests appearing in the 
appropriate categories.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import List
import uuid

from ai_generator.models import TestCase, TestType
from ai_generator.test_organizer import (
    TestCaseOrganizer,
    TestSummaryGenerator,
    TestSummary
)


# Custom strategies for generating test data
@st.composite
def test_case_strategy(draw):
    """Generate a valid TestCase for testing."""
    test_types = list(TestType)
    subsystems = ["scheduler", "memory", "filesystem", "networking", "drivers", "core_kernel"]
    
    test_type = draw(st.sampled_from(test_types))
    subsystem = draw(st.sampled_from(subsystems))
    
    return TestCase(
        id=f"test_{uuid.uuid4().hex[:8]}",
        name=draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', ' ')))),
        description=draw(st.text(min_size=10, max_size=200)),
        test_type=test_type,
        target_subsystem=subsystem,
        code_paths=draw(st.lists(st.text(min_size=5, max_size=30), min_size=0, max_size=5)),
        execution_time_estimate=draw(st.integers(min_value=1, max_value=600)),
        test_script=draw(st.text(min_size=10, max_size=100))
    )


@st.composite
def test_case_list_strategy(draw):
    """Generate a list of TestCase objects."""
    return draw(st.lists(test_case_strategy(), min_size=1, max_size=50))


class TestTestSummaryOrganization:
    """Property-based tests for test summary organization."""
    
    @given(test_cases=test_case_list_strategy())
    def test_all_tests_appear_in_summary(self, test_cases: List[TestCase]):
        """Property: All generated tests appear in the summary.
        
        For any list of test cases, when we generate a summary,
        the total count should equal the number of input tests.
        """
        organizer = TestCaseOrganizer()
        summary = organizer.organize(test_cases)
        
        # Total tests in summary should match input
        assert summary.total_tests == len(test_cases)
        
        # Count tests across all subsystems
        total_in_subsystems = sum(
            len(tests) for tests in summary.tests_by_subsystem.values()
        )
        assert total_in_subsystems == len(test_cases)
        
        # Count tests across all types
        total_in_types = sum(
            len(tests) for tests in summary.tests_by_type.values()
        )
        assert total_in_types == len(test_cases)
    
    @given(test_cases=test_case_list_strategy())
    def test_tests_categorized_by_subsystem(self, test_cases: List[TestCase]):
        """Property: All tests are categorized by their target subsystem.
        
        For any list of test cases, each test should appear in exactly
        one subsystem category matching its target_subsystem.
        """
        organizer = TestCaseOrganizer()
        by_subsystem = organizer.categorize_by_subsystem(test_cases)
        
        # Every test should appear in exactly one subsystem
        all_categorized_tests = []
        for subsystem, tests in by_subsystem.items():
            all_categorized_tests.extend(tests)
            
            # All tests in this category should have matching subsystem
            for test in tests:
                assert test.target_subsystem == subsystem or (
                    test.target_subsystem is None and subsystem == "unknown"
                )
        
        # All tests should be categorized
        assert len(all_categorized_tests) == len(test_cases)
        
        # No duplicates
        test_ids = [t.id for t in all_categorized_tests]
        assert len(test_ids) == len(set(test_ids))
    
    @given(test_cases=test_case_list_strategy())
    def test_tests_classified_by_type(self, test_cases: List[TestCase]):
        """Property: All tests are classified by their test type.
        
        For any list of test cases, each test should appear in exactly
        one type category matching its test_type.
        """
        organizer = TestCaseOrganizer()
        by_type = organizer.classify_by_type(test_cases)
        
        # Every test should appear in exactly one type category
        all_classified_tests = []
        for test_type, tests in by_type.items():
            all_classified_tests.extend(tests)
            
            # All tests in this category should have matching type
            for test in tests:
                assert test.test_type == test_type
        
        # All tests should be classified
        assert len(all_classified_tests) == len(test_cases)
        
        # No duplicates
        test_ids = [t.id for t in all_classified_tests]
        assert len(test_ids) == len(set(test_ids))
    
    @given(test_cases=test_case_list_strategy())
    def test_summary_lists_all_subsystems(self, test_cases: List[TestCase]):
        """Property: Summary lists all subsystems that have tests.
        
        For any list of test cases, the summary should list exactly
        the subsystems that appear in the test cases.
        """
        organizer = TestCaseOrganizer()
        summary = organizer.organize(test_cases)
        
        # Extract unique subsystems from test cases
        expected_subsystems = set()
        for test in test_cases:
            subsystem = test.target_subsystem or "unknown"
            expected_subsystems.add(subsystem)
        
        # Summary should list exactly these subsystems
        assert set(summary.subsystems) == expected_subsystems
        
        # Each listed subsystem should have tests
        for subsystem in summary.subsystems:
            assert subsystem in summary.tests_by_subsystem
            assert len(summary.tests_by_subsystem[subsystem]) > 0
    
    @given(test_cases=test_case_list_strategy())
    def test_summary_lists_all_test_types(self, test_cases: List[TestCase]):
        """Property: Summary lists all test types that appear.
        
        For any list of test cases, the summary should list exactly
        the test types that appear in the test cases.
        """
        organizer = TestCaseOrganizer()
        summary = organizer.organize(test_cases)
        
        # Extract unique test types from test cases
        expected_types = set(test.test_type for test in test_cases)
        
        # Summary should list exactly these types
        assert set(summary.test_types) == expected_types
        
        # Each listed type should have tests
        for test_type in summary.test_types:
            assert test_type in summary.tests_by_type
            assert len(summary.tests_by_type[test_type]) > 0
    
    @given(test_cases=test_case_list_strategy())
    def test_no_test_lost_in_organization(self, test_cases: List[TestCase]):
        """Property: No tests are lost during organization.
        
        For any list of test cases, every test ID should appear
        exactly once in the organized summary.
        """
        organizer = TestCaseOrganizer()
        summary = organizer.organize(test_cases)
        
        # Collect all test IDs from original list
        original_ids = set(test.id for test in test_cases)
        
        # Collect all test IDs from subsystem categorization
        subsystem_ids = set()
        for tests in summary.tests_by_subsystem.values():
            for test in tests:
                subsystem_ids.add(test.id)
        
        # Should be identical
        assert original_ids == subsystem_ids
        
        # Collect all test IDs from type classification
        type_ids = set()
        for tests in summary.tests_by_type.values():
            for test in tests:
                type_ids.add(test.id)
        
        # Should be identical
        assert original_ids == type_ids
    
    @given(test_cases=test_case_list_strategy())
    def test_summary_generator_produces_valid_summary(self, test_cases: List[TestCase]):
        """Property: Summary generator produces valid TestSummary.
        
        For any list of test cases, the summary generator should
        produce a valid TestSummary with correct counts and organization.
        """
        generator = TestSummaryGenerator()
        summary = generator.generate_summary(test_cases)
        
        # Should be a TestSummary instance
        assert isinstance(summary, TestSummary)
        
        # Total should match
        assert summary.total_tests == len(test_cases)
        
        # Should have valid organization
        assert isinstance(summary.tests_by_subsystem, dict)
        assert isinstance(summary.tests_by_type, dict)
        assert isinstance(summary.subsystems, list)
        assert isinstance(summary.test_types, list)
    
    @given(test_cases=test_case_list_strategy())
    def test_text_report_contains_all_subsystems(self, test_cases: List[TestCase]):
        """Property: Text report mentions all subsystems.
        
        For any list of test cases, the generated text report
        should mention all subsystems that have tests.
        """
        generator = TestSummaryGenerator()
        report = generator.generate_text_report(test_cases)
        
        # Extract unique subsystems
        subsystems = set()
        for test in test_cases:
            subsystem = test.target_subsystem or "unknown"
            subsystems.add(subsystem)
        
        # Each subsystem should appear in the report
        for subsystem in subsystems:
            assert subsystem in report
    
    @given(test_cases=test_case_list_strategy())
    def test_text_report_contains_all_test_types(self, test_cases: List[TestCase]):
        """Property: Text report mentions all test types.
        
        For any list of test cases, the generated text report
        should mention all test types that appear.
        """
        generator = TestSummaryGenerator()
        report = generator.generate_text_report(test_cases)
        
        # Extract unique test types
        test_types = set(test.test_type for test in test_cases)
        
        # Each test type should appear in the report
        for test_type in test_types:
            assert test_type.value in report
    
    def test_empty_test_list_produces_empty_summary(self):
        """Property: Empty test list produces empty summary.
        
        When given an empty list of tests, the summary should
        indicate zero tests with empty categorizations.
        """
        organizer = TestCaseOrganizer()
        summary = organizer.organize([])
        
        assert summary.total_tests == 0
        assert len(summary.tests_by_subsystem) == 0
        assert len(summary.tests_by_type) == 0
        assert len(summary.subsystems) == 0
        assert len(summary.test_types) == 0
    
    @given(test_cases=test_case_list_strategy())
    def test_summary_to_dict_preserves_structure(self, test_cases: List[TestCase]):
        """Property: Summary to_dict preserves organizational structure.
        
        For any list of test cases, converting the summary to a dictionary
        should preserve all organizational information.
        """
        organizer = TestCaseOrganizer()
        summary = organizer.organize(test_cases)
        summary_dict = summary.to_dict()
        
        # Should have all required keys
        assert "total_tests" in summary_dict
        assert "subsystems" in summary_dict
        assert "test_types" in summary_dict
        assert "tests_by_subsystem" in summary_dict
        assert "tests_by_type" in summary_dict
        
        # Total should match
        assert summary_dict["total_tests"] == len(test_cases)
        
        # Subsystems should match
        assert set(summary_dict["subsystems"]) == set(summary.subsystems)
        
        # Test types should match (as strings)
        assert set(summary_dict["test_types"]) == set(t.value for t in summary.test_types)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
