#!/usr/bin/env python3
"""Manual test script for test organizer functionality."""

import sys
sys.path.insert(0, '.')

from ai_generator.models import TestCase, TestType
from ai_generator.test_organizer import TestCaseOrganizer, TestSummaryGenerator


def create_sample_tests():
    """Create sample test cases for testing."""
    tests = []
    
    # Create tests for different subsystems and types
    tests.append(TestCase(
        id="test_001",
        name="Test scheduler function",
        description="Test the scheduler's task allocation",
        test_type=TestType.UNIT,
        target_subsystem="scheduler",
        test_script="# Test code here\npass"
    ))
    
    tests.append(TestCase(
        id="test_002",
        name="Test memory allocation",
        description="Test memory allocation under load",
        test_type=TestType.UNIT,
        target_subsystem="memory",
        test_script="# Test code here\npass"
    ))
    
    tests.append(TestCase(
        id="test_003",
        name="Integration test scheduler-memory",
        description="Test interaction between scheduler and memory",
        test_type=TestType.INTEGRATION,
        target_subsystem="scheduler",
        test_script="# Test code here\npass"
    ))
    
    tests.append(TestCase(
        id="test_004",
        name="Fuzz filesystem API",
        description="Fuzz test for filesystem operations",
        test_type=TestType.FUZZ,
        target_subsystem="filesystem",
        test_script="# Test code here\npass"
    ))
    
    tests.append(TestCase(
        id="test_005",
        name="Performance test network throughput",
        description="Measure network throughput",
        test_type=TestType.PERFORMANCE,
        target_subsystem="networking",
        test_script="# Test code here\npass"
    ))
    
    tests.append(TestCase(
        id="test_006",
        name="Security test buffer overflow",
        description="Test for buffer overflow vulnerabilities",
        test_type=TestType.SECURITY,
        target_subsystem="drivers",
        test_script="# Test code here\npass"
    ))
    
    tests.append(TestCase(
        id="test_007",
        name="Test scheduler priority",
        description="Test scheduler priority handling",
        test_type=TestType.UNIT,
        target_subsystem="scheduler",
        test_script="# Test code here\npass"
    ))
    
    return tests


def test_categorization():
    """Test categorization by subsystem."""
    print("Testing categorization by subsystem...")
    tests = create_sample_tests()
    organizer = TestCaseOrganizer()
    
    by_subsystem = organizer.categorize_by_subsystem(tests)
    
    print(f"  Total tests: {len(tests)}")
    print(f"  Subsystems found: {sorted(by_subsystem.keys())}")
    
    for subsystem, subsystem_tests in sorted(by_subsystem.items()):
        print(f"    {subsystem}: {len(subsystem_tests)} tests")
        for test in subsystem_tests:
            assert test.target_subsystem == subsystem
    
    # Verify all tests are categorized
    total_categorized = sum(len(t) for t in by_subsystem.values())
    assert total_categorized == len(tests), "Not all tests were categorized!"
    
    print("  ✓ Categorization test passed")


def test_classification():
    """Test classification by type."""
    print("\nTesting classification by type...")
    tests = create_sample_tests()
    organizer = TestCaseOrganizer()
    
    by_type = organizer.classify_by_type(tests)
    
    print(f"  Total tests: {len(tests)}")
    print(f"  Test types found: {sorted([t.value for t in by_type.keys()])}")
    
    for test_type, type_tests in sorted(by_type.items(), key=lambda x: x[0].value):
        print(f"    {test_type.value}: {len(type_tests)} tests")
        for test in type_tests:
            assert test.test_type == test_type
    
    # Verify all tests are classified
    total_classified = sum(len(t) for t in by_type.values())
    assert total_classified == len(tests), "Not all tests were classified!"
    
    print("  ✓ Classification test passed")


def test_organization():
    """Test full organization."""
    print("\nTesting full organization...")
    tests = create_sample_tests()
    organizer = TestCaseOrganizer()
    
    summary = organizer.organize(tests)
    
    print(f"  Total tests: {summary.total_tests}")
    print(f"  Subsystems: {summary.subsystems}")
    print(f"  Test types: {[t.value for t in summary.test_types]}")
    
    assert summary.total_tests == len(tests)
    assert len(summary.subsystems) > 0
    assert len(summary.test_types) > 0
    
    # Verify all tests appear in both categorizations
    total_in_subsystems = sum(len(t) for t in summary.tests_by_subsystem.values())
    total_in_types = sum(len(t) for t in summary.tests_by_type.values())
    
    assert total_in_subsystems == len(tests)
    assert total_in_types == len(tests)
    
    print("  ✓ Organization test passed")


def test_summary_generation():
    """Test summary generation."""
    print("\nTesting summary generation...")
    tests = create_sample_tests()
    generator = TestSummaryGenerator()
    
    summary = generator.generate_summary(tests)
    
    print(f"  Generated summary with {summary.total_tests} tests")
    
    # Generate text report
    text_report = generator.generate_text_report(tests)
    print("\n" + "="*70)
    print("Generated Text Report:")
    print("="*70)
    print(text_report)
    
    # Verify all subsystems appear in report
    for subsystem in summary.subsystems:
        assert subsystem in text_report, f"Subsystem {subsystem} not in report!"
    
    # Verify all test types appear in report
    for test_type in summary.test_types:
        assert test_type.value in text_report, f"Test type {test_type.value} not in report!"
    
    print("\n  ✓ Summary generation test passed")


def test_detailed_report():
    """Test detailed report generation."""
    print("\nTesting detailed report generation...")
    tests = create_sample_tests()
    generator = TestSummaryGenerator()
    
    detailed_report = generator.generate_detailed_report(tests)
    
    print("\n" + "="*70)
    print("Generated Detailed Report:")
    print("="*70)
    print(detailed_report)
    
    # Verify test names appear in detailed report
    for test in tests:
        assert test.name in detailed_report, f"Test {test.name} not in detailed report!"
    
    print("\n  ✓ Detailed report generation test passed")


def test_empty_list():
    """Test with empty test list."""
    print("\nTesting with empty test list...")
    organizer = TestCaseOrganizer()
    
    summary = organizer.organize([])
    
    assert summary.total_tests == 0
    assert len(summary.tests_by_subsystem) == 0
    assert len(summary.tests_by_type) == 0
    assert len(summary.subsystems) == 0
    assert len(summary.test_types) == 0
    
    print("  ✓ Empty list test passed")


def test_summary_to_dict():
    """Test summary to_dict conversion."""
    print("\nTesting summary to_dict conversion...")
    tests = create_sample_tests()
    organizer = TestCaseOrganizer()
    
    summary = organizer.organize(tests)
    summary_dict = summary.to_dict()
    
    print(f"  Dictionary keys: {sorted(summary_dict.keys())}")
    
    assert "total_tests" in summary_dict
    assert "subsystems" in summary_dict
    assert "test_types" in summary_dict
    assert "tests_by_subsystem" in summary_dict
    assert "tests_by_type" in summary_dict
    
    assert summary_dict["total_tests"] == len(tests)
    
    print("  ✓ to_dict conversion test passed")


def main():
    """Run all tests."""
    print("="*70)
    print("MANUAL TEST SUITE FOR TEST ORGANIZER")
    print("="*70)
    
    try:
        test_categorization()
        test_classification()
        test_organization()
        test_summary_generation()
        test_detailed_report()
        test_empty_list()
        test_summary_to_dict()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
