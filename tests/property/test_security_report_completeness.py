"""Property-based tests for security report completeness.

**Feature: agentic-kernel-testing, Property 35: Security report completeness**

This test validates Requirements 7.5:
WHEN security testing completes, THE Testing System SHALL generate a security 
report with all findings, proof-of-concept exploits where applicable, and 
remediation recommendations.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from pathlib import Path
import tempfile
import json

from analysis.security_scanner import (
    SecurityIssue,
    SecurityScanner,
    VulnerabilityType,
    Severity,
    Exploitability,
    SecurityIssueClassifier
)
from analysis.security_report_generator import (
    SecurityReportGenerator,
    ReportFormat,
    ProofOfConceptGenerator,
    RemediationRecommendationGenerator
)


# Strategies for generating security issues

@st.composite
def security_issue_strategy(draw):
    """Generate random security issues."""
    vuln_type = draw(st.sampled_from(list(VulnerabilityType)))
    severity = draw(st.sampled_from(list(Severity)))
    file_path = draw(st.text(min_size=5, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.'
    )))
    line_number = draw(st.integers(min_value=1, max_value=10000))
    description = draw(st.text(min_size=10, max_size=200))
    confidence = draw(st.floats(min_value=0.1, max_value=1.0))
    
    issue = SecurityIssue(
        vulnerability_type=vuln_type,
        severity=severity,
        file_path=file_path,
        line_number=line_number,
        description=description,
        confidence=confidence
    )
    
    # Classify the issue to add classification metadata
    classifier = SecurityIssueClassifier()
    return classifier.classify_issue(issue)


@st.composite
def scan_results_strategy(draw):
    """Generate random scan results (dict of file paths to issues)."""
    num_files = draw(st.integers(min_value=1, max_value=5))
    scan_results = {}
    
    for _ in range(num_files):
        file_path = draw(st.text(min_size=5, max_size=30, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='/_.'
        )))
        num_issues = draw(st.integers(min_value=1, max_value=3))
        issues = [draw(security_issue_strategy()) for _ in range(num_issues)]
        scan_results[file_path] = issues
    
    return scan_results


# Property 35: Security report completeness
# For any completed security testing, the report should include all findings,
# POCs where applicable, and remediation recommendations.

@given(scan_results=scan_results_strategy())
@settings(max_examples=100, deadline=None)
def test_report_contains_all_findings(scan_results):
    """Property: Security report should contain all findings from scan.
    
    **Validates: Requirements 7.5**
    
    For any scan results, the generated report should include every
    security issue that was found.
    """
    generator = SecurityReportGenerator()
    
    # Generate report
    report = generator.generate_report(scan_results)
    
    # Count total issues in scan results
    total_issues = sum(len(issues) for issues in scan_results.values())
    
    # Property: Report should contain all findings
    assert len(report.findings) == total_issues, \
        f"Report should contain all {total_issues} findings, but has {len(report.findings)}"
    
    # Property: All issues should be in the report
    all_scan_issues = []
    for issues in scan_results.values():
        all_scan_issues.extend(issues)
    
    for scan_issue in all_scan_issues:
        # Check if this issue is in the report
        found = any(
            f.vulnerability_type == scan_issue.vulnerability_type and
            f.file_path == scan_issue.file_path and
            f.line_number == scan_issue.line_number
            for f in report.findings
        )
        assert found, f"Issue {scan_issue.vulnerability_type} at {scan_issue.file_path}:{scan_issue.line_number} not in report"


@given(scan_results=scan_results_strategy())
@settings(max_examples=100, deadline=None)
def test_report_contains_pocs_for_high_severity(scan_results):
    """Property: Report should contain POCs for high/critical severity issues.
    
    **Validates: Requirements 7.5**
    
    For any high or critical severity issue, the report should include
    a proof-of-concept exploit where applicable.
    """
    generator = SecurityReportGenerator()
    
    # Generate report
    report = generator.generate_report(scan_results)
    
    # Count high/critical issues
    all_issues = []
    for issues in scan_results.values():
        all_issues.extend(issues)
    
    high_severity_issues = [
        i for i in all_issues
        if i.severity in [Severity.HIGH, Severity.CRITICAL]
    ]
    
    # Property: POCs should be generated for high/critical issues
    # (at least for vulnerability types that have POC templates)
    poc_applicable_types = {
        VulnerabilityType.BUFFER_OVERFLOW,
        VulnerabilityType.USE_AFTER_FREE,
        VulnerabilityType.INTEGER_OVERFLOW,
        VulnerabilityType.NULL_POINTER_DEREFERENCE,
        VulnerabilityType.FORMAT_STRING,
        VulnerabilityType.RACE_CONDITION
    }
    
    expected_pocs = [
        i for i in high_severity_issues
        if i.vulnerability_type in poc_applicable_types
    ]
    
    # Property: Number of POCs should match expected
    assert len(report.proof_of_concepts) == len(expected_pocs), \
        f"Expected {len(expected_pocs)} POCs for high/critical issues, got {len(report.proof_of_concepts)}"


@given(scan_results=scan_results_strategy())
@settings(max_examples=100, deadline=None)
def test_report_contains_remediation_for_all_issues(scan_results):
    """Property: Report should contain remediation recommendations for all issues.
    
    **Validates: Requirements 7.5**
    
    For any security issue, the report should include remediation
    recommendations.
    """
    generator = SecurityReportGenerator()
    
    # Generate report
    report = generator.generate_report(scan_results)
    
    # Count total issues
    total_issues = sum(len(issues) for issues in scan_results.values())
    
    # Property: Remediation recommendations should exist for all issues
    assert len(report.remediation_recommendations) == total_issues, \
        f"Expected {total_issues} remediation recommendations, got {len(report.remediation_recommendations)}"
    
    # Property: Each recommendation should have required fields
    for rec in report.remediation_recommendations:
        assert rec.vulnerability_id, "Remediation should have vulnerability_id"
        assert rec.priority, "Remediation should have priority"
        assert rec.short_term_fix, "Remediation should have short_term_fix"
        assert rec.long_term_fix, "Remediation should have long_term_fix"
        assert rec.estimated_effort, "Remediation should have estimated_effort"


@given(scan_results=scan_results_strategy())
@settings(max_examples=100, deadline=None)
def test_report_has_complete_structure(scan_results):
    """Property: Report should have all required structural components.
    
    **Validates: Requirements 7.5**
    
    For any security testing completion, the report should have:
    - Report ID
    - Timestamp
    - Scan summary
    - Findings
    - Executive summary
    - Risk assessment
    """
    generator = SecurityReportGenerator()
    
    # Generate report
    report = generator.generate_report(scan_results)
    
    # Property: Report should have report_id
    assert report.report_id, "Report must have report_id"
    
    # Property: Report should have timestamp
    assert report.timestamp, "Report must have timestamp"
    assert isinstance(report.timestamp, datetime), "Timestamp must be datetime"
    
    # Property: Report should have scan_summary
    assert report.scan_summary, "Report must have scan_summary"
    assert "total_files_scanned" in report.scan_summary
    assert "total_issues" in report.scan_summary
    assert "severity_breakdown" in report.scan_summary
    
    # Property: Report should have findings
    assert report.findings is not None, "Report must have findings list"
    
    # Property: Report should have executive_summary
    assert report.executive_summary, "Report must have executive_summary"
    assert len(report.executive_summary) > 0, "Executive summary should not be empty"
    
    # Property: Report should have risk_assessment
    assert report.risk_assessment, "Report must have risk_assessment"
    assert "overall_risk_score" in report.risk_assessment
    assert "risk_level" in report.risk_assessment
    assert "recommendation" in report.risk_assessment


@given(scan_results=scan_results_strategy())
@settings(max_examples=50, deadline=None)
def test_report_exports_to_all_formats(scan_results):
    """Property: Report should be exportable to all supported formats.
    
    **Validates: Requirements 7.5**
    
    For any security report, it should be exportable to JSON, HTML,
    Markdown, and text formats without errors.
    """
    generator = SecurityReportGenerator()
    
    # Generate report
    report = generator.generate_report(scan_results)
    
    # Test export to each format
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Property: Should export to JSON
        json_path = tmpdir_path / "report.json"
        generator.export_report(report, str(json_path), ReportFormat.JSON)
        assert json_path.exists(), "JSON export should create file"
        assert json_path.stat().st_size > 0, "JSON file should not be empty"
        
        # Verify JSON is valid
        with open(json_path) as f:
            json_data = json.load(f)
            assert "report_id" in json_data
            assert "findings" in json_data
        
        # Property: Should export to HTML
        html_path = tmpdir_path / "report.html"
        generator.export_report(report, str(html_path), ReportFormat.HTML)
        assert html_path.exists(), "HTML export should create file"
        assert html_path.stat().st_size > 0, "HTML file should not be empty"
        
        # Verify HTML contains expected elements
        with open(html_path) as f:
            html_content = f.read()
            assert "<html>" in html_content
            assert report.report_id in html_content
        
        # Property: Should export to Markdown
        md_path = tmpdir_path / "report.md"
        generator.export_report(report, str(md_path), ReportFormat.MARKDOWN)
        assert md_path.exists(), "Markdown export should create file"
        assert md_path.stat().st_size > 0, "Markdown file should not be empty"
        
        # Verify Markdown contains expected elements
        with open(md_path) as f:
            md_content = f.read()
            assert "# Security Report" in md_content
            assert report.report_id in md_content
        
        # Property: Should export to text
        txt_path = tmpdir_path / "report.txt"
        generator.export_report(report, str(txt_path), ReportFormat.TEXT)
        assert txt_path.exists(), "Text export should create file"
        assert txt_path.stat().st_size > 0, "Text file should not be empty"
        
        # Verify text contains expected elements
        with open(txt_path) as f:
            txt_content = f.read()
            assert "SECURITY REPORT" in txt_content
            assert report.report_id in txt_content


@given(scan_results=scan_results_strategy())
@settings(max_examples=100, deadline=None)
def test_poc_contains_required_elements(scan_results):
    """Property: POCs should contain all required elements.
    
    **Validates: Requirements 7.5**
    
    For any generated POC, it should include:
    - Exploit code
    - Description
    - Prerequisites
    - Impact demonstration
    """
    generator = SecurityReportGenerator()
    
    # Generate report
    report = generator.generate_report(scan_results)
    
    # Property: Each POC should have required elements
    for poc in report.proof_of_concepts:
        assert poc.vulnerability_id, "POC must have vulnerability_id"
        assert poc.exploit_code, "POC must have exploit_code"
        assert len(poc.exploit_code) > 0, "Exploit code should not be empty"
        assert poc.description, "POC must have description"
        assert poc.prerequisites is not None, "POC must have prerequisites list"
        assert poc.impact_demonstration, "POC must have impact_demonstration"


@given(scan_results=scan_results_strategy())
@settings(max_examples=30, deadline=5000)
def test_remediation_priority_matches_severity(scan_results):
    """Property: Remediation priority should match issue severity.
    
    **Validates: Requirements 7.5**
    
    For any security issue, the remediation priority should be
    consistent with the issue severity.
    """
    generator = SecurityReportGenerator()
    
    # Generate report
    report = generator.generate_report(scan_results)
    
    # Get all issues
    all_issues = []
    for issues in scan_results.values():
        all_issues.extend(issues)
    
    # Property: Number of remediations should match number of issues
    assert len(report.remediation_recommendations) == len(all_issues), \
        "Should have one remediation per issue"
    
    # Property: Critical severity issues should have high priority remediation
    critical_issues = [i for i in all_issues if i.severity == Severity.CRITICAL]
    if critical_issues:
        # At least one remediation should have Critical or High priority
        high_priority_recs = [r for r in report.remediation_recommendations 
                              if r.priority in ["Critical", "High"]]
        assert len(high_priority_recs) >= len(critical_issues), \
            "Critical issues should have high-priority remediations"


@given(scan_results=scan_results_strategy())
@settings(max_examples=20, deadline=2000)
def test_risk_assessment_reflects_findings(scan_results):
    """Property: Risk assessment should reflect the severity of findings.
    
    **Validates: Requirements 7.5**
    
    For any security report, the risk assessment should accurately
    reflect the severity and exploitability of findings.
    """
    generator = SecurityReportGenerator()
    
    # Generate report
    report = generator.generate_report(scan_results)
    
    # Get all issues
    all_issues = []
    for issues in scan_results.values():
        all_issues.extend(issues)
    
    # Property: Risk level should be consistent with CVSS scores
    # (Not just severity enum, as CVSS provides more accurate assessment)
    if all_issues:
        # Check that risk level is reasonable given the CVSS scores
        cvss_scores = [
            i.classification.cvss_score.base_score
            for i in all_issues
            if i.classification
        ]
        if cvss_scores:
            max_cvss = max(cvss_scores)
            # If max CVSS is critical (9+), risk should be Critical or High
            if max_cvss >= 9.0:
                assert report.risk_assessment["risk_level"] in ["Critical", "High"], \
                    f"Report with max CVSS {max_cvss} should have Critical or High risk level"
    
    # Property: Risk score should be between 0 and 100
    assert 0 <= report.risk_assessment["overall_risk_score"] <= 100, \
        "Risk score should be between 0 and 100"
    
    # Property: Risk assessment should have recommendation
    assert report.risk_assessment["recommendation"], \
        "Risk assessment should have recommendation"
    
    # Property: Exploitable vulnerabilities count should be accurate
    exploitable_count = sum(
        1 for i in all_issues
        if i.classification and i.classification.exploitability in [
            Exploitability.HIGH, Exploitability.CRITICAL
        ]
    )
    assert report.risk_assessment["exploitable_vulnerabilities"] == exploitable_count, \
        f"Expected {exploitable_count} exploitable vulnerabilities, got {report.risk_assessment['exploitable_vulnerabilities']}"
