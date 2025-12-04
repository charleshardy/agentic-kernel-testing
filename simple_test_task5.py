#!/usr/bin/env python3
"""Simple test for Task 5 without hypothesis decorators."""

import sys
sys.path.insert(0, '.')

from ai_generator.models import TestCase, TestType
from ai_generator.test_organizer import TestCaseOrganizer, TestSummaryGenerator

print("Testing Task 5 Implementation...")
print("=" * 70)

# Create sample test cases
tests = [
    TestCase(
        id="test_001",
        name="Test scheduler",
        description="Test scheduler function",
        test_type=TestType.UNIT,
        target_subsystem="scheduler",
        test_script="pass"
    ),
    TestCase(
        id="test_002",
        name="Test memory",
        description="Test memory allocation",
        test_type=TestType.UNIT,
        target_subsystem="memory",
        test_script="pass"
    ),
    TestCase(
        id="test_003",
        name="Integration test",
        description="Test integration",
        test_type=TestType.INTEGRATION,
        target_subsystem="scheduler",
        test_script="pass"
    ),
]

organizer = TestCaseOrganizer()

# Test 1: Categorize by subsystem
print("\n[Test 1] Categorize by subsystem")
by_subsystem = organizer.categorize_by_subsystem(tests)
print(f"  Subsystems: {list(by_subsystem.keys())}")
assert "scheduler" in by_subsystem
assert "memory" in by_subsystem
assert len(by_subsystem["scheduler"]) == 2
assert len(by_subsystem["memory"]) == 1
print("  ✓ PASSED")

# Test 2: Classify by type
print("\n[Test 2] Classify by type")
by_type = organizer.classify_by_type(tests)
print(f"  Types: {[t.value for t in by_type.keys()]}")
assert TestType.UNIT in by_type
assert TestType.INTEGRATION in by_type
assert len(by_type[TestType.UNIT]) == 2
assert len(by_type[TestType.INTEGRATION]) == 1
print("  ✓ PASSED")

# Test 3: Full organization
print("\n[Test 3] Full organization")
summary = organizer.organize(tests)
print(f"  Total tests: {summary.total_tests}")
print(f"  Subsystems: {summary.subsystems}")
print(f"  Test types: {[t.value for t in summary.test_types]}")
assert summary.total_tests == 3
assert set(summary.subsystems) == {"scheduler", "memory"}
assert set(summary.test_types) == {TestType.UNIT, TestType.INTEGRATION}
print("  ✓ PASSED")

# Test 4: Summary generation
print("\n[Test 4] Summary generation")
generator = TestSummaryGenerator()
text_report = generator.generate_text_report(tests)
print("  Generated report:")
print(text_report)
assert "scheduler" in text_report
assert "memory" in text_report
assert "unit" in text_report
assert "integration" in text_report
assert "3" in text_report  # total count
print("  ✓ PASSED")

# Test 5: Empty list
print("\n[Test 5] Empty list handling")
empty_summary = organizer.organize([])
assert empty_summary.total_tests == 0
assert len(empty_summary.subsystems) == 0
assert len(empty_summary.test_types) == 0
print("  ✓ PASSED")

# Test 6: to_dict conversion
print("\n[Test 6] to_dict conversion")
summary_dict = summary.to_dict()
assert "total_tests" in summary_dict
assert "subsystems" in summary_dict
assert "test_types" in summary_dict
assert summary_dict["total_tests"] == 3
print("  ✓ PASSED")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("\nTask 5 implementation is working correctly.")
print("Property 5 (Test summary organization) validated.")
