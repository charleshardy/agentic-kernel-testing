#!/usr/bin/env python3
"""Final comprehensive verification for Task 5 with simulated property testing."""

import sys
import random
sys.path.insert(0, '.')

from ai_generator.models import TestCase, TestType
from ai_generator.test_organizer import TestCaseOrganizer, TestSummaryGenerator
import uuid

def generate_random_test_case():
    """Generate a random test case."""
    test_types = list(TestType)
    subsystems = ["scheduler", "memory", "filesystem", "networking", "drivers", "core_kernel", "security"]
    
    return TestCase(
        id=f"test_{uuid.uuid4().hex[:8]}",
        name=f"Test {random.choice(['function', 'module', 'component'])} {random.randint(1, 1000)}",
        description=f"Test description {random.randint(1, 1000)}",
        test_type=random.choice(test_types),
        target_subsystem=random.choice(subsystems),
        code_paths=[f"path/to/file{i}.c" for i in range(random.randint(0, 3))],
        execution_time_estimate=random.randint(10, 300),
        test_script=f"# Test script {random.randint(1, 1000)}\npass"
    )

def run_property_test(test_name, test_func, num_examples=20):
    """Run a property test with multiple random examples."""
    print(f"\n[Property Test] {test_name}")
    print(f"  Running {num_examples} random examples...")
    
    failures = []
    for i in range(num_examples):
        try:
            # Generate random test cases
            num_tests = random.randint(1, 30)
            test_cases = [generate_random_test_case() for _ in range(num_tests)]
            
            # Run the test
            test_func(test_cases)
            
        except AssertionError as e:
            failures.append((i, e))
    
    if failures:
        print(f"  ✗ FAILED on {len(failures)}/{num_examples} examples")
        for idx, error in failures[:3]:  # Show first 3 failures
            print(f"    Example {idx}: {error}")
        return False
    else:
        print(f"  ✓ PASSED all {num_examples} examples")
        return True

print("=" * 70)
print("COMPREHENSIVE PROPERTY-BASED VERIFICATION FOR TASK 5")
print("=" * 70)
print("\nValidating Property 5: Test summary organization")
print("Requirements 1.5: Tests organized by subsystem and test type")

organizer = TestCaseOrganizer()
generator = TestSummaryGenerator()

# Property 1: All tests appear in summary
def prop_all_tests_appear(test_cases):
    summary = organizer.organize(test_cases)
    assert summary.total_tests == len(test_cases), \
        f"Total mismatch: {summary.total_tests} != {len(test_cases)}"
    
    total_in_subsystems = sum(len(tests) for tests in summary.tests_by_subsystem.values())
    assert total_in_subsystems == len(test_cases), \
        f"Subsystem total mismatch: {total_in_subsystems} != {len(test_cases)}"
    
    total_in_types = sum(len(tests) for tests in summary.tests_by_type.values())
    assert total_in_types == len(test_cases), \
        f"Type total mismatch: {total_in_types} != {len(test_cases)}"

passed1 = run_property_test(
    "All generated tests appear in the summary",
    prop_all_tests_appear,
    num_examples=50
)

# Property 2: Tests categorized by subsystem
def prop_categorized_by_subsystem(test_cases):
    by_subsystem = organizer.categorize_by_subsystem(test_cases)
    
    all_categorized = []
    for subsystem, tests in by_subsystem.items():
        all_categorized.extend(tests)
        for test in tests:
            assert test.target_subsystem == subsystem or (
                test.target_subsystem is None and subsystem == "unknown"
            ), f"Test {test.id} in wrong subsystem category"
    
    assert len(all_categorized) == len(test_cases), \
        f"Not all tests categorized: {len(all_categorized)} != {len(test_cases)}"
    
    # No duplicates
    test_ids = [t.id for t in all_categorized]
    assert len(test_ids) == len(set(test_ids)), "Duplicate tests found"

passed2 = run_property_test(
    "All tests categorized by their target subsystem",
    prop_categorized_by_subsystem,
    num_examples=50
)

# Property 3: Tests classified by type
def prop_classified_by_type(test_cases):
    by_type = organizer.classify_by_type(test_cases)
    
    all_classified = []
    for test_type, tests in by_type.items():
        all_classified.extend(tests)
        for test in tests:
            assert test.test_type == test_type, \
                f"Test {test.id} has wrong type"
    
    assert len(all_classified) == len(test_cases), \
        f"Not all tests classified: {len(all_classified)} != {len(test_cases)}"

passed3 = run_property_test(
    "All tests classified by their test type",
    prop_classified_by_type,
    num_examples=50
)

# Property 4: Summary lists all subsystems
def prop_lists_all_subsystems(test_cases):
    summary = organizer.organize(test_cases)
    
    expected_subsystems = set()
    for test in test_cases:
        subsystem = test.target_subsystem or "unknown"
        expected_subsystems.add(subsystem)
    
    assert set(summary.subsystems) == expected_subsystems, \
        f"Subsystem mismatch: {set(summary.subsystems)} != {expected_subsystems}"

passed4 = run_property_test(
    "Summary lists all subsystems that have tests",
    prop_lists_all_subsystems,
    num_examples=50
)

# Property 5: Summary lists all test types
def prop_lists_all_types(test_cases):
    summary = organizer.organize(test_cases)
    
    expected_types = set(test.test_type for test in test_cases)
    assert set(summary.test_types) == expected_types, \
        f"Type mismatch: {set(summary.test_types)} != {expected_types}"

passed5 = run_property_test(
    "Summary lists all test types that appear",
    prop_lists_all_types,
    num_examples=50
)

# Property 6: No tests lost
def prop_no_tests_lost(test_cases):
    summary = organizer.organize(test_cases)
    
    original_ids = set(test.id for test in test_cases)
    
    subsystem_ids = set()
    for tests in summary.tests_by_subsystem.values():
        for test in tests:
            subsystem_ids.add(test.id)
    
    assert original_ids == subsystem_ids, "Tests lost in subsystem organization"

passed6 = run_property_test(
    "No tests are lost during organization",
    prop_no_tests_lost,
    num_examples=50
)

# Property 7: Text report contains all subsystems
def prop_report_has_subsystems(test_cases):
    report = generator.generate_text_report(test_cases)
    
    subsystems = set()
    for test in test_cases:
        subsystem = test.target_subsystem or "unknown"
        subsystems.add(subsystem)
    
    for subsystem in subsystems:
        assert subsystem in report, f"Subsystem {subsystem} not in report"

passed7 = run_property_test(
    "Text report mentions all subsystems",
    prop_report_has_subsystems,
    num_examples=50
)

# Property 8: Text report contains all test types
def prop_report_has_types(test_cases):
    report = generator.generate_text_report(test_cases)
    
    test_types = set(test.test_type for test in test_cases)
    
    for test_type in test_types:
        assert test_type.value in report, f"Test type {test_type.value} not in report"

passed8 = run_property_test(
    "Text report mentions all test types",
    prop_report_has_types,
    num_examples=50
)

# Summary
print("\n" + "=" * 70)
print("PROPERTY TEST RESULTS")
print("=" * 70)

all_passed = all([passed1, passed2, passed3, passed4, passed5, passed6, passed7, passed8])

if all_passed:
    print("\n✅ ALL PROPERTY-BASED TESTS PASSED!")
    print(f"\nTotal properties tested: 8")
    print(f"Total examples per property: 50")
    print(f"Total test executions: 400")
    print("\nProperty 5 (Test summary organization) VALIDATED")
    print("Requirements 1.5: SATISFIED")
    sys.exit(0)
else:
    print("\n❌ SOME PROPERTY TESTS FAILED")
    sys.exit(1)
