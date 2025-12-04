"""Test case organization and summarization."""

from typing import List, Dict, Any
from collections import defaultdict
from dataclasses import dataclass, field

from .models import TestCase, TestType


@dataclass
class TestSummary:
    """Summary of organized test cases."""
    total_tests: int
    tests_by_subsystem: Dict[str, List[TestCase]] = field(default_factory=dict)
    tests_by_type: Dict[TestType, List[TestCase]] = field(default_factory=dict)
    subsystems: List[str] = field(default_factory=list)
    test_types: List[TestType] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_tests": self.total_tests,
            "subsystems": self.subsystems,
            "test_types": [t.value for t in self.test_types],
            "tests_by_subsystem": {
                subsystem: [tc.id for tc in tests]
                for subsystem, tests in self.tests_by_subsystem.items()
            },
            "tests_by_type": {
                test_type.value: [tc.id for tc in tests]
                for test_type, tests in self.tests_by_type.items()
            }
        }
    
    def to_text(self) -> str:
        """Generate human-readable text summary."""
        lines = []
        lines.append("=" * 70)
        lines.append("TEST CASE SUMMARY")
        lines.append("=" * 70)
        lines.append(f"\nTotal Tests Generated: {self.total_tests}")
        
        # Summary by subsystem
        lines.append(f"\n{'Subsystems Covered:':<30} {len(self.subsystems)}")
        for subsystem in sorted(self.subsystems):
            count = len(self.tests_by_subsystem[subsystem])
            lines.append(f"  - {subsystem:<28} {count:>3} tests")
        
        # Summary by test type
        lines.append(f"\n{'Test Types:':<30}")
        for test_type in sorted(self.test_types, key=lambda t: t.value):
            count = len(self.tests_by_type[test_type])
            lines.append(f"  - {test_type.value:<28} {count:>3} tests")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


class TestCaseOrganizer:
    """Organizes and categorizes test cases."""
    
    def categorize_by_subsystem(self, test_cases: List[TestCase]) -> Dict[str, List[TestCase]]:
        """Categorize test cases by subsystem.
        
        Args:
            test_cases: List of TestCase objects to categorize
            
        Returns:
            Dictionary mapping subsystem name to list of test cases
        """
        categorized = defaultdict(list)
        
        for test_case in test_cases:
            subsystem = test_case.target_subsystem or "unknown"
            categorized[subsystem].append(test_case)
        
        return dict(categorized)
    
    def classify_by_type(self, test_cases: List[TestCase]) -> Dict[TestType, List[TestCase]]:
        """Classify test cases by test type.
        
        Args:
            test_cases: List of TestCase objects to classify
            
        Returns:
            Dictionary mapping TestType to list of test cases
        """
        classified = defaultdict(list)
        
        for test_case in test_cases:
            classified[test_case.test_type].append(test_case)
        
        return dict(classified)
    
    def organize(self, test_cases: List[TestCase]) -> TestSummary:
        """Organize test cases by subsystem and type.
        
        Args:
            test_cases: List of TestCase objects to organize
            
        Returns:
            TestSummary with organized test information
        """
        if not test_cases:
            return TestSummary(
                total_tests=0,
                tests_by_subsystem={},
                tests_by_type={},
                subsystems=[],
                test_types=[]
            )
        
        # Categorize by subsystem
        by_subsystem = self.categorize_by_subsystem(test_cases)
        
        # Classify by type
        by_type = self.classify_by_type(test_cases)
        
        # Extract unique subsystems and types
        subsystems = sorted(by_subsystem.keys())
        test_types = sorted(by_type.keys(), key=lambda t: t.value)
        
        return TestSummary(
            total_tests=len(test_cases),
            tests_by_subsystem=by_subsystem,
            tests_by_type=by_type,
            subsystems=subsystems,
            test_types=test_types
        )


class TestSummaryGenerator:
    """Generates summaries of test cases with organized output."""
    
    def __init__(self):
        """Initialize the summary generator."""
        self.organizer = TestCaseOrganizer()
    
    def generate_summary(self, test_cases: List[TestCase]) -> TestSummary:
        """Generate a comprehensive summary of test cases.
        
        Args:
            test_cases: List of TestCase objects to summarize
            
        Returns:
            TestSummary with organized information
        """
        return self.organizer.organize(test_cases)
    
    def generate_text_report(self, test_cases: List[TestCase]) -> str:
        """Generate a text report of test cases.
        
        Args:
            test_cases: List of TestCase objects to report on
            
        Returns:
            Formatted text report string
        """
        summary = self.generate_summary(test_cases)
        return summary.to_text()
    
    def generate_detailed_report(self, test_cases: List[TestCase]) -> str:
        """Generate a detailed report with test case listings.
        
        Args:
            test_cases: List of TestCase objects to report on
            
        Returns:
            Detailed formatted text report
        """
        summary = self.generate_summary(test_cases)
        lines = [summary.to_text()]
        
        # Add detailed listings by subsystem
        lines.append("\n" + "=" * 70)
        lines.append("DETAILED TEST LISTINGS BY SUBSYSTEM")
        lines.append("=" * 70)
        
        for subsystem in sorted(summary.subsystems):
            tests = summary.tests_by_subsystem[subsystem]
            lines.append(f"\n{subsystem.upper()} ({len(tests)} tests):")
            lines.append("-" * 70)
            
            # Group by type within subsystem
            by_type = defaultdict(list)
            for test in tests:
                by_type[test.test_type].append(test)
            
            for test_type in sorted(by_type.keys(), key=lambda t: t.value):
                type_tests = by_type[test_type]
                lines.append(f"\n  {test_type.value.upper()} Tests ({len(type_tests)}):")
                
                for test in type_tests:
                    lines.append(f"    • {test.name}")
                    lines.append(f"      ID: {test.id}")
                    lines.append(f"      Description: {test.description[:80]}...")
                    if test.code_paths:
                        lines.append(f"      Code Paths: {', '.join(test.code_paths[:3])}")
                    lines.append("")
        
        return "\n".join(lines)
