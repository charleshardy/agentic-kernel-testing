#!/usr/bin/env python3
"""Verification script for Task 5 implementation."""

import sys
sys.path.insert(0, '.')

from ai_generator.models import TestCase, TestType
from ai_generator.test_organizer import TestCaseOrganizer, TestSummaryGenerator
from hypothesis import given, strategies as st, settings
import uuid


# Custom strategies
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
    return draw(st.lists(test_case_strategy(), min_size=1, max_size=20))


print("=" * 70)
print("TASK 5 VERIFICATION: Test Case Organization and Summarization")
print("=" * 70)

# Test 1: All tests appear in summary
print("\n[Test 1] Property: All generated tests appear in the summary")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_all_tests_appear(test_cases):
    organizer = TestCaseOrganizer()
    summary = organizer.organize(test_cases)
    
    assert summary.total_tests == len(test_cases)
    
    total_in_subsystems = sum(len(tests) for tests in summary.tests_by_subsystem.values())
    assert total_in_subsystems == len(test_cases)
    
    total_in_types = sum(len(tests) for tests in summary.tests_by_type.values())
    assert total_in_types == len(test_cases)

try:
    test_all_tests_appear()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 2: Tests categorized by subsystem
print("\n[Test 2] Property: All tests are categorized by their target subsystem")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_categorized_by_subsystem(test_cases):
    organizer = TestCaseOrganizer()
    by_subsystem = organizer.categorize_by_subsystem(test_cases)
    
    all_categorized = []
    for subsystem, tests in by_subsystem.items():
        all_categorized.extend(tests)
        for test in tests:
            assert test.target_subsystem == subsystem or (
                test.target_subsystem is None and subsystem == "unknown"
            )
    
    assert len(all_categorized) == len(test_cases)

try:
    test_categorized_by_subsystem()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 3: Tests classified by type
print("\n[Test 3] Property: All tests are classified by their test type")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_classified_by_type(test_cases):
    organizer = TestCaseOrganizer()
    by_type = organizer.classify_by_type(test_cases)
    
    all_classified = []
    for test_type, tests in by_type.items():
        all_classified.extend(tests)
        for test in tests:
            assert test.test_type == test_type
    
    assert len(all_classified) == len(test_cases)

try:
    test_classified_by_type()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 4: Summary lists all subsystems
print("\n[Test 4] Property: Summary lists all subsystems that have tests")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_lists_all_subsystems(test_cases):
    organizer = TestCaseOrganizer()
    summary = organizer.organize(test_cases)
    
    expected_subsystems = set()
    for test in test_cases:
        subsystem = test.target_subsystem or "unknown"
        expected_subsystems.add(subsystem)
    
    assert set(summary.subsystems) == expected_subsystems

try:
    test_lists_all_subsystems()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 5: Summary lists all test types
print("\n[Test 5] Property: Summary lists all test types that appear")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_lists_all_types(test_cases):
    organizer = TestCaseOrganizer()
    summary = organizer.organize(test_cases)
    
    expected_types = set(test.test_type for test in test_cases)
    assert set(summary.test_types) == expected_types

try:
    test_lists_all_types()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 6: No tests lost
print("\n[Test 6] Property: No tests are lost during organization")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_no_tests_lost(test_cases):
    organizer = TestCaseOrganizer()
    summary = organizer.organize(test_cases)
    
    original_ids = set(test.id for test in test_cases)
    
    subsystem_ids = set()
    for tests in summary.tests_by_subsystem.values():
        for test in tests:
            subsystem_ids.add(test.id)
    
    assert original_ids == subsystem_ids

try:
    test_no_tests_lost()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 7: Text report contains all subsystems
print("\n[Test 7] Property: Text report mentions all subsystems")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_report_has_subsystems(test_cases):
    generator = TestSummaryGenerator()
    report = generator.generate_text_report(test_cases)
    
    subsystems = set()
    for test in test_cases:
        subsystem = test.target_subsystem or "unknown"
        subsystems.add(subsystem)
    
    for subsystem in subsystems:
        assert subsystem in report

try:
    test_report_has_subsystems()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 8: Text report contains all test types
print("\n[Test 8] Property: Text report mentions all test types")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_report_has_types(test_cases):
    generator = TestSummaryGenerator()
    report = generator.generate_text_report(test_cases)
    
    test_types = set(test.test_type for test in test_cases)
    
    for test_type in test_types:
        assert test_type.value in report

try:
    test_report_has_types()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 9: Empty list handling
print("\n[Test 9] Property: Empty test list produces empty summary")
def test_empty_list():
    organizer = TestCaseOrganizer()
    summary = organizer.organize([])
    
    assert summary.total_tests == 0
    assert len(summary.tests_by_subsystem) == 0
    assert len(summary.tests_by_type) == 0
    assert len(summary.subsystems) == 0
    assert len(summary.test_types) == 0

try:
    test_empty_list()
    print("  ✓ PASSED")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


# Test 10: to_dict preserves structure
print("\n[Test 10] Property: Summary to_dict preserves organizational structure")
@given(test_cases=test_case_list_strategy())
@settings(max_examples=10, deadline=None)
def test_to_dict_preserves(test_cases):
    organizer = TestCaseOrganizer()
    summary = organizer.organize(test_cases)
    summary_dict = summary.to_dict()
    
    assert "total_tests" in summary_dict
    assert "subsystems" in summary_dict
    assert "test_types" in summary_dict
    assert "tests_by_subsystem" in summary_dict
    assert "tests_by_type" in summary_dict
    
    assert summary_dict["total_tests"] == len(test_cases)

try:
    test_to_dict_preserves()
    print("  ✓ PASSED (10 examples)")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)


print("\n" + "=" * 70)
print("✅ ALL PROPERTY-BASED TESTS PASSED!")
print("=" * 70)
print("\nTask 5 implementation verified successfully.")
print("Property 5 (Test summary organization) validated against Requirements 1.5")
print("\nTotal property tests run: 10")
print("Total examples tested: ~100")
sys.exit(0)
