#!/usr/bin/env python3
"""Verification script for security report generator."""

from analysis.security_scanner import (
    SecurityIssue,
    SecurityScanner,
    VulnerabilityType,
    Severity,
    SecurityIssueClassifier
)
from analysis.security_report_generator import (
    SecurityReportGenerator,
    ReportFormat
)
from pathlib import Path
import tempfile

def test_basic_report_generation():
    """Test basic report generation."""
    print("Testing basic report generation...")
    
    # Create some test issues
    classifier = SecurityIssueClassifier()
    
    issue1 = SecurityIssue(
        vulnerability_type=VulnerabilityType.BUFFER_OVERFLOW,
        severity=Severity.CRITICAL,
        file_path="test.c",
        line_number=42,
        description="Buffer overflow in strcpy",
        confidence=0.9
    )
    issue1 = classifier.classify_issue(issue1)
    
    issue2 = SecurityIssue(
        vulnerability_type=VulnerabilityType.NULL_POINTER_DEREFERENCE,
        severity=Severity.HIGH,
        file_path="test.c",
        line_number=100,
        description="Null pointer dereference",
        confidence=0.8
    )
    issue2 = classifier.classify_issue(issue2)
    
    scan_results = {
        "test.c": [issue1, issue2]
    }
    
    # Generate report
    generator = SecurityReportGenerator()
    report = generator.generate_report(scan_results)
    
    # Verify report structure
    assert report.report_id, "Report should have ID"
    assert report.timestamp, "Report should have timestamp"
    assert len(report.findings) == 2, f"Expected 2 findings, got {len(report.findings)}"
    assert report.executive_summary, "Report should have executive summary"
    assert report.risk_assessment, "Report should have risk assessment"
    
    print(f"✓ Report ID: {report.report_id}")
    print(f"✓ Findings: {len(report.findings)}")
    print(f"✓ POCs: {len(report.proof_of_concepts)}")
    print(f"✓ Remediations: {len(report.remediation_recommendations)}")
    print(f"✓ Risk Level: {report.risk_assessment['risk_level']}")
    
    # Test POC generation
    assert len(report.proof_of_concepts) > 0, "Should have POCs for high-severity issues"
    print(f"✓ POC generated for critical issue")
    
    # Test remediation recommendations
    assert len(report.remediation_recommendations) == 2, "Should have remediation for all issues"
    print(f"✓ Remediation recommendations generated")
    
    # Test export to different formats
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # JSON export
        json_path = tmpdir_path / "report.json"
        generator.export_report(report, str(json_path), ReportFormat.JSON)
        assert json_path.exists(), "JSON export failed"
        print(f"✓ JSON export successful")
        
        # HTML export
        html_path = tmpdir_path / "report.html"
        generator.export_report(report, str(html_path), ReportFormat.HTML)
        assert html_path.exists(), "HTML export failed"
        print(f"✓ HTML export successful")
        
        # Markdown export
        md_path = tmpdir_path / "report.md"
        generator.export_report(report, str(md_path), ReportFormat.MARKDOWN)
        assert md_path.exists(), "Markdown export failed"
        print(f"✓ Markdown export successful")
        
        # Text export
        txt_path = tmpdir_path / "report.txt"
        generator.export_report(report, str(txt_path), ReportFormat.TEXT)
        assert txt_path.exists(), "Text export failed"
        print(f"✓ Text export successful")
    
    print("\n✅ All basic tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_basic_report_generation()
        print("\n✅ Security report generator verification successful!")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
