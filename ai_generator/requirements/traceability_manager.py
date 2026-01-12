"""Traceability Manager for Agentic AI Test Requirements.

Manages requirement-to-test traceability with:
- Bidirectional linking between tests and requirements
- Coverage matrix generation
- Untested requirement identification
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import json

from .models import (
    TraceabilityLink,
    CoverageMatrix,
    ParsedRequirement,
    CorrectnessProperty,
    GeneratedTest,
    TestSpecification,
)


class TraceabilityManager:
    """Manages requirement-to-test traceability.
    
    Provides:
    - Bidirectional test-requirement linking
    - Coverage matrix generation
    - Untested requirement identification
    - Orphaned test detection
    """
    
    def __init__(self):
        """Initialize the traceability manager."""
        # Storage for links
        self._links: List[TraceabilityLink] = []
        
        # Indexes for fast lookup
        self._test_to_requirements: Dict[str, Set[str]] = defaultdict(set)
        self._requirement_to_tests: Dict[str, Set[str]] = defaultdict(set)
        self._property_to_tests: Dict[str, Set[str]] = defaultdict(set)
        self._test_to_property: Dict[str, Optional[str]] = {}
        
        # Registered entities
        self._requirements: Dict[str, ParsedRequirement] = {}
        self._properties: Dict[str, CorrectnessProperty] = {}
        self._tests: Dict[str, GeneratedTest] = {}
        self._specifications: Dict[str, TestSpecification] = {}
    
    def register_requirement(self, req: ParsedRequirement) -> None:
        """Register a requirement.
        
        Args:
            req: ParsedRequirement to register
        """
        self._requirements[req.id] = req
    
    def register_property(self, prop: CorrectnessProperty) -> None:
        """Register a property.
        
        Args:
            prop: CorrectnessProperty to register
        """
        self._properties[prop.id] = prop
        
        # Auto-link property to its requirements
        for req_id in prop.requirement_ids:
            self._requirement_to_tests[req_id]  # Ensure key exists
    
    def register_test(self, test: GeneratedTest) -> None:
        """Register a test.
        
        Args:
            test: GeneratedTest to register
        """
        self._tests[test.id] = test
        
        # Auto-create links from test metadata
        for req_id in test.requirement_ids:
            self.link_test_to_requirement(
                test.id,
                req_id,
                property_id=test.property_id
            )
    
    def register_specification(self, spec: TestSpecification) -> None:
        """Register a specification with all its entities.
        
        Args:
            spec: TestSpecification to register
        """
        self._specifications[spec.id] = spec
        
        # Register all requirements
        for req in spec.requirements:
            self.register_requirement(req)
        
        # Register all properties
        for prop in spec.properties:
            self.register_property(prop)
        
        # Register all tests
        for test in spec.tests:
            self.register_test(test)
    
    def link_test_to_requirement(
        self,
        test_id: str,
        requirement_id: str,
        property_id: Optional[str] = None,
        link_type: str = "validates"
    ) -> TraceabilityLink:
        """Create a link between test and requirement.
        
        Args:
            test_id: Test identifier
            requirement_id: Requirement identifier
            property_id: Optional property identifier
            link_type: Type of link (validates, partially_validates, related)
            
        Returns:
            TraceabilityLink object
        """
        link = TraceabilityLink(
            test_id=test_id,
            requirement_id=requirement_id,
            property_id=property_id,
            link_type=link_type,
        )
        
        self._links.append(link)
        
        # Update indexes
        self._test_to_requirements[test_id].add(requirement_id)
        self._requirement_to_tests[requirement_id].add(test_id)
        
        if property_id:
            self._property_to_tests[property_id].add(test_id)
            self._test_to_property[test_id] = property_id
        
        return link
    
    def unlink_test_from_requirement(
        self,
        test_id: str,
        requirement_id: str
    ) -> bool:
        """Remove a link between test and requirement.
        
        Args:
            test_id: Test identifier
            requirement_id: Requirement identifier
            
        Returns:
            True if link was removed, False if not found
        """
        # Find and remove the link
        for i, link in enumerate(self._links):
            if link.test_id == test_id and link.requirement_id == requirement_id:
                self._links.pop(i)
                
                # Update indexes
                self._test_to_requirements[test_id].discard(requirement_id)
                self._requirement_to_tests[requirement_id].discard(test_id)
                
                return True
        
        return False
    
    def get_tests_for_requirement(self, requirement_id: str) -> List[str]:
        """Get all tests that cover a requirement.
        
        Args:
            requirement_id: Requirement identifier
            
        Returns:
            List of test identifiers
        """
        return list(self._requirement_to_tests.get(requirement_id, set()))
    
    def get_requirements_for_test(self, test_id: str) -> List[str]:
        """Get all requirements covered by a test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            List of requirement identifiers
        """
        return list(self._test_to_requirements.get(test_id, set()))
    
    def get_requirement_for_test(self, test_id: str) -> Optional[str]:
        """Get the primary requirement a test validates.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Requirement identifier or None
        """
        reqs = self.get_requirements_for_test(test_id)
        return reqs[0] if reqs else None
    
    def get_property_for_test(self, test_id: str) -> Optional[str]:
        """Get the property a test validates.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Property identifier or None
        """
        return self._test_to_property.get(test_id)
    
    def get_tests_for_property(self, property_id: str) -> List[str]:
        """Get all tests for a property.
        
        Args:
            property_id: Property identifier
            
        Returns:
            List of test identifiers
        """
        return list(self._property_to_tests.get(property_id, set()))
    
    def generate_coverage_matrix(
        self,
        spec_id: Optional[str] = None
    ) -> CoverageMatrix:
        """Generate a requirement coverage matrix.
        
        Args:
            spec_id: Optional specification identifier to scope the matrix
            
        Returns:
            CoverageMatrix showing requirements vs tests
        """
        # Determine which requirements and tests to include
        if spec_id and spec_id in self._specifications:
            spec = self._specifications[spec_id]
            requirement_ids = [r.id for r in spec.requirements]
            test_ids = [t.id for t in spec.tests]
        else:
            requirement_ids = list(self._requirements.keys())
            test_ids = list(self._tests.keys())
        
        # Build coverage mapping
        coverage: Dict[str, List[str]] = {}
        for req_id in requirement_ids:
            tests = self.get_tests_for_requirement(req_id)
            # Filter to only include tests in scope
            coverage[req_id] = [t for t in tests if t in test_ids or not spec_id]
        
        # Find untested requirements
        untested = [req_id for req_id, tests in coverage.items() if not tests]
        
        # Find orphaned tests (tests not linked to any requirement)
        all_linked_tests = set()
        for tests in coverage.values():
            all_linked_tests.update(tests)
        
        orphaned = [t for t in test_ids if t not in all_linked_tests]
        
        # Calculate coverage percentage
        total_reqs = len(requirement_ids)
        covered_reqs = total_reqs - len(untested)
        coverage_pct = (covered_reqs / total_reqs * 100) if total_reqs > 0 else 0.0
        
        return CoverageMatrix(
            spec_id=spec_id or "all",
            requirements=requirement_ids,
            tests=test_ids,
            coverage=coverage,
            untested=untested,
            orphaned_tests=orphaned,
            coverage_percentage=coverage_pct,
        )
    
    def find_untested_requirements(
        self,
        spec: Optional[TestSpecification] = None
    ) -> List[str]:
        """Find requirements without test coverage.
        
        Args:
            spec: Optional TestSpecification to analyze
            
        Returns:
            List of untested requirement identifiers
        """
        if spec:
            self.register_specification(spec)
            matrix = self.generate_coverage_matrix(spec.id)
        else:
            matrix = self.generate_coverage_matrix()
        return matrix.untested
    
    def find_orphaned_tests(
        self,
        spec: Optional[TestSpecification] = None
    ) -> List[str]:
        """Find tests not linked to any requirement.
        
        Args:
            spec: Optional TestSpecification to analyze
            
        Returns:
            List of orphaned test identifiers
        """
        if spec:
            self.register_specification(spec)
            matrix = self.generate_coverage_matrix(spec.id)
        else:
            matrix = self.generate_coverage_matrix()
        return matrix.orphaned_tests
    
    def get_tests_for_requirement(
        self,
        requirement_id: str,
        spec_id: Optional[str] = None
    ) -> List[str]:
        """Get all tests that cover a requirement.
        
        Args:
            requirement_id: Requirement identifier
            spec_id: Optional specification ID to filter by
            
        Returns:
            List of test identifiers
        """
        tests = list(self._requirement_to_tests.get(requirement_id, set()))
        
        # Filter by spec if provided
        if spec_id and spec_id in self._specifications:
            spec = self._specifications[spec_id]
            spec_test_ids = {t.id for t in spec.tests}
            tests = [t for t in tests if t in spec_test_ids]
        
        return tests
    
    def format_report_markdown(self, report_data: Dict[str, Any]) -> str:
        """Format a report as markdown.
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            Markdown formatted report
        """
        lines = [
            "# Traceability Report",
            "",
            f"**Specification:** {report_data.get('spec_name', 'Unknown')}",
            f"**ID:** {report_data.get('spec_id', 'Unknown')}",
            "",
            "## Summary",
            "",
        ]
        
        summary = report_data.get('summary', {})
        lines.extend([
            f"- **Total Requirements:** {summary.get('total_requirements', 0)}",
            f"- **Total Properties:** {summary.get('total_properties', 0)}",
            f"- **Total Tests:** {summary.get('total_tests', 0)}",
            f"- **Coverage:** {summary.get('coverage_percentage', 0):.1f}%",
            f"- **Untested Requirements:** {summary.get('untested_count', 0)}",
            f"- **Orphaned Tests:** {summary.get('orphaned_count', 0)}",
            "",
        ])
        
        # Coverage matrix
        matrix = report_data.get('coverage_matrix', {})
        if matrix:
            lines.extend([
                "## Coverage Matrix",
                "",
                "| Requirement | Tests | Status |",
                "|-------------|-------|--------|",
            ])
            
            coverage = matrix.get('coverage', {})
            for req_id in matrix.get('requirements', []):
                tests = coverage.get(req_id, [])
                status = "✅" if tests else "❌"
                test_list = ", ".join(tests[:3])
                if len(tests) > 3:
                    test_list += f" (+{len(tests) - 3} more)"
                lines.append(f"| {req_id} | {test_list or 'None'} | {status} |")
            
            lines.append("")
        
        # Untested requirements
        untested = report_data.get('untested_requirements', [])
        if untested:
            lines.extend([
                "## Untested Requirements",
                "",
            ])
            for req_id in untested:
                lines.append(f"- {req_id}")
            lines.append("")
        
        # Orphaned tests
        orphaned = report_data.get('orphaned_tests', [])
        if orphaned:
            lines.extend([
                "## Orphaned Tests",
                "",
            ])
            for test_id in orphaned:
                lines.append(f"- {test_id}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def format_report_html(self, report_data: Dict[str, Any]) -> str:
        """Format a report as HTML.
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            HTML formatted report
        """
        summary = report_data.get('summary', {})
        matrix = report_data.get('coverage_matrix', {})
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Traceability Report - {report_data.get('spec_name', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .summary-item {{ display: inline-block; margin-right: 30px; }}
        .summary-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .summary-label {{ font-size: 12px; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        .status-pass {{ color: green; }}
        .status-fail {{ color: red; }}
        .warning {{ background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ padding: 5px 0; }}
    </style>
</head>
<body>
    <h1>Traceability Report</h1>
    <p><strong>Specification:</strong> {report_data.get('spec_name', 'Unknown')}</p>
    <p><strong>ID:</strong> {report_data.get('spec_id', 'Unknown')}</p>
    
    <div class="summary">
        <div class="summary-item">
            <div class="summary-value">{summary.get('total_requirements', 0)}</div>
            <div class="summary-label">Requirements</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">{summary.get('total_tests', 0)}</div>
            <div class="summary-label">Tests</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">{summary.get('coverage_percentage', 0):.1f}%</div>
            <div class="summary-label">Coverage</div>
        </div>
        <div class="summary-item">
            <div class="summary-value">{summary.get('untested_count', 0)}</div>
            <div class="summary-label">Untested</div>
        </div>
    </div>
    
    <h2>Coverage Matrix</h2>
    <table>
        <tr>
            <th>Requirement</th>
            <th>Tests</th>
            <th>Status</th>
        </tr>
"""
        
        coverage = matrix.get('coverage', {})
        for req_id in matrix.get('requirements', []):
            tests = coverage.get(req_id, [])
            status_class = "status-pass" if tests else "status-fail"
            status_icon = "✅" if tests else "❌"
            test_list = ", ".join(tests[:3])
            if len(tests) > 3:
                test_list += f" (+{len(tests) - 3} more)"
            
            html += f"""        <tr>
            <td>{req_id}</td>
            <td>{test_list or 'None'}</td>
            <td class="{status_class}">{status_icon}</td>
        </tr>
"""
        
        html += """    </table>
"""
        
        # Untested requirements
        untested = report_data.get('untested_requirements', [])
        if untested:
            html += """    <h2>Untested Requirements</h2>
    <div class="warning">
        <ul>
"""
            for req_id in untested:
                html += f"            <li>⚠️ {req_id}</li>\n"
            html += """        </ul>
    </div>
"""
        
        # Orphaned tests
        orphaned = report_data.get('orphaned_tests', [])
        if orphaned:
            html += """    <h2>Orphaned Tests</h2>
    <div class="warning">
        <ul>
"""
            for test_id in orphaned:
                html += f"            <li>⚠️ {test_id}</li>\n"
            html += """        </ul>
    </div>
"""
        
        html += """</body>
</html>"""
        
        return html
    
    def get_links_for_test(self, test_id: str) -> List[TraceabilityLink]:
        """Get all traceability links for a test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            List of TraceabilityLink objects
        """
        return [link for link in self._links if link.test_id == test_id]
    
    def get_links_for_requirement(self, requirement_id: str) -> List[TraceabilityLink]:
        """Get all traceability links for a requirement.
        
        Args:
            requirement_id: Requirement identifier
            
        Returns:
            List of TraceabilityLink objects
        """
        return [link for link in self._links if link.requirement_id == requirement_id]
    
    def export_links(self) -> List[Dict[str, Any]]:
        """Export all traceability links.
        
        Returns:
            List of link dictionaries
        """
        return [link.to_dict() for link in self._links]
    
    def import_links(self, links_data: List[Dict[str, Any]]) -> int:
        """Import traceability links.
        
        Args:
            links_data: List of link dictionaries
            
        Returns:
            Number of links imported
        """
        count = 0
        for data in links_data:
            link = TraceabilityLink.from_dict(data)
            self._links.append(link)
            
            # Update indexes
            self._test_to_requirements[link.test_id].add(link.requirement_id)
            self._requirement_to_tests[link.requirement_id].add(link.test_id)
            
            if link.property_id:
                self._property_to_tests[link.property_id].add(link.test_id)
                self._test_to_property[link.test_id] = link.property_id
            
            count += 1
        
        return count
    
    def get_coverage_summary(self, spec_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of coverage statistics.
        
        Args:
            spec_id: Optional specification identifier
            
        Returns:
            Dictionary with coverage statistics
        """
        matrix = self.generate_coverage_matrix(spec_id)
        
        return {
            'spec_id': matrix.spec_id,
            'total_requirements': len(matrix.requirements),
            'covered_requirements': len(matrix.requirements) - len(matrix.untested),
            'untested_requirements': len(matrix.untested),
            'total_tests': len(matrix.tests),
            'orphaned_tests': len(matrix.orphaned_tests),
            'coverage_percentage': matrix.coverage_percentage,
            'generated_at': matrix.generated_at.isoformat(),
        }
    
    def generate_traceability_report(
        self,
        spec_id: Optional[str] = None,
        format: str = 'text'
    ) -> str:
        """Generate a traceability report.
        
        Args:
            spec_id: Optional specification identifier
            format: Report format ('text', 'markdown', 'json')
            
        Returns:
            Report string
        """
        matrix = self.generate_coverage_matrix(spec_id)
        
        if format == 'json':
            return json.dumps(matrix.to_dict(), indent=2)
        
        elif format == 'markdown':
            return self._generate_markdown_report(matrix)
        
        else:  # text
            return self._generate_text_report(matrix)
    
    def _generate_text_report(self, matrix: CoverageMatrix) -> str:
        """Generate a text traceability report."""
        lines = [
            "=" * 60,
            "Traceability Report",
            "=" * 60,
            f"Specification: {matrix.spec_id}",
            f"Generated: {matrix.generated_at.isoformat()}",
            "",
            f"Coverage: {matrix.coverage_percentage:.1f}%",
            f"Requirements: {len(matrix.requirements)}",
            f"Tests: {len(matrix.tests)}",
            f"Untested: {len(matrix.untested)}",
            f"Orphaned Tests: {len(matrix.orphaned_tests)}",
            "",
            "Requirement Coverage:",
            "-" * 40,
        ]
        
        for req_id in matrix.requirements:
            tests = matrix.coverage.get(req_id, [])
            status = "✓" if tests else "✗"
            test_count = len(tests)
            lines.append(f"  {status} {req_id}: {test_count} test(s)")
        
        if matrix.untested:
            lines.extend([
                "",
                "Untested Requirements:",
                "-" * 40,
            ])
            for req_id in matrix.untested:
                lines.append(f"  - {req_id}")
        
        if matrix.orphaned_tests:
            lines.extend([
                "",
                "Orphaned Tests:",
                "-" * 40,
            ])
            for test_id in matrix.orphaned_tests:
                lines.append(f"  - {test_id}")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)
    
    def _generate_markdown_report(self, matrix: CoverageMatrix) -> str:
        """Generate a markdown traceability report."""
        lines = [
            "# Traceability Report",
            "",
            f"**Specification:** {matrix.spec_id}",
            f"**Generated:** {matrix.generated_at.isoformat()}",
            "",
            "## Summary",
            "",
            f"- **Coverage:** {matrix.coverage_percentage:.1f}%",
            f"- **Requirements:** {len(matrix.requirements)}",
            f"- **Tests:** {len(matrix.tests)}",
            f"- **Untested:** {len(matrix.untested)}",
            f"- **Orphaned Tests:** {len(matrix.orphaned_tests)}",
            "",
            "## Coverage Matrix",
            "",
            "| Requirement | Tests | Status |",
            "|-------------|-------|--------|",
        ]
        
        for req_id in matrix.requirements:
            tests = matrix.coverage.get(req_id, [])
            status = "✅" if tests else "❌"
            test_list = ", ".join(tests[:3])
            if len(tests) > 3:
                test_list += f" (+{len(tests) - 3} more)"
            lines.append(f"| {req_id} | {test_list or 'None'} | {status} |")
        
        if matrix.untested:
            lines.extend([
                "",
                "## Untested Requirements",
                "",
            ])
            for req_id in matrix.untested:
                lines.append(f"- {req_id}")
        
        if matrix.orphaned_tests:
            lines.extend([
                "",
                "## Orphaned Tests",
                "",
            ])
            for test_id in matrix.orphaned_tests:
                lines.append(f"- {test_id}")
        
        return '\n'.join(lines)


# Convenience functions

def create_traceability_link(
    test_id: str,
    requirement_id: str,
    property_id: Optional[str] = None
) -> TraceabilityLink:
    """Create a traceability link.
    
    Args:
        test_id: Test identifier
        requirement_id: Requirement identifier
        property_id: Optional property identifier
        
    Returns:
        TraceabilityLink object
    """
    return TraceabilityLink(
        test_id=test_id,
        requirement_id=requirement_id,
        property_id=property_id,
    )


def generate_coverage_report(
    specification: TestSpecification,
    format: str = 'text'
) -> str:
    """Generate a coverage report for a specification.
    
    Args:
        specification: TestSpecification to report on
        format: Report format
        
    Returns:
        Report string
    """
    manager = TraceabilityManager()
    manager.register_specification(specification)
    return manager.generate_traceability_report(specification.id, format)
