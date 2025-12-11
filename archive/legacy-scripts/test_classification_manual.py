#!/usr/bin/env python3
"""Manual test for security issue classification."""

from analysis.security_scanner import (
    SecurityIssue,
    SecurityIssueClassifier,
    VulnerabilityType,
    Severity,
    Exploitability
)

def test_basic_classification():
    """Test basic classification functionality."""
    classifier = SecurityIssueClassifier()
    
    # Create a test issue
    issue = SecurityIssue(
        vulnerability_type=VulnerabilityType.BUFFER_OVERFLOW,
        severity=Severity.HIGH,
        file_path="test.c",
        line_number=42,
        description="Buffer overflow vulnerability",
        confidence=0.9
    )
    
    # Classify the issue
    classified = classifier.classify_issue(issue)
    
    # Check classification exists
    assert classified.classification is not None, "Classification should exist"
    
    # Check CVSS score
    cvss = classified.classification.cvss_score
    assert cvss is not None, "CVSS score should exist"
    assert 0.0 <= cvss.base_score <= 10.0, f"Base score {cvss.base_score} out of range"
    assert 0.0 <= cvss.impact_score <= 10.0, f"Impact score {cvss.impact_score} out of range"
    assert 0.0 <= cvss.exploitability_score <= 10.0, f"Exploitability score {cvss.exploitability_score} out of range"
    
    # Check exploitability
    assert classified.classification.exploitability is not None, "Exploitability should exist"
    assert isinstance(classified.classification.exploitability, Exploitability), "Should be Exploitability enum"
    
    # Check all required fields
    assert classified.classification.attack_vector in ["Local", "Adjacent", "Network"]
    assert classified.classification.attack_complexity in ["Low", "High", "Medium"]
    assert classified.classification.privileges_required in ["None", "Low", "High"]
    assert classified.classification.user_interaction in ["None", "Required"]
    assert classified.classification.scope in ["Unchanged", "Changed"]
    assert classified.classification.confidentiality_impact in ["None", "Low", "High"]
    assert classified.classification.integrity_impact in ["None", "Low", "High"]
    assert classified.classification.availability_impact in ["None", "Low", "High"]
    
    print("✓ Basic classification test passed")
    print(f"  CVSS Base Score: {cvss.base_score}")
    print(f"  Exploitability: {classified.classification.exploitability.value}")
    print(f"  Severity Rating: {cvss.severity_rating}")

def test_multiple_vulnerability_types():
    """Test classification for different vulnerability types."""
    classifier = SecurityIssueClassifier()
    
    vuln_types = [
        VulnerabilityType.BUFFER_OVERFLOW,
        VulnerabilityType.USE_AFTER_FREE,
        VulnerabilityType.INTEGER_OVERFLOW,
        VulnerabilityType.NULL_POINTER_DEREFERENCE,
        VulnerabilityType.MEMORY_LEAK,
        VulnerabilityType.FORMAT_STRING
    ]
    
    for vuln_type in vuln_types:
        issue = SecurityIssue(
            vulnerability_type=vuln_type,
            severity=Severity.MEDIUM,
            file_path="test.c",
            line_number=10,
            description=f"Test {vuln_type.value}",
            confidence=0.8
        )
        
        classified = classifier.classify_issue(issue)
        
        assert classified.classification is not None
        assert classified.classification.cvss_score is not None
        assert 0.0 <= classified.classification.cvss_score.base_score <= 10.0
        
        print(f"✓ {vuln_type.value}: CVSS={classified.classification.cvss_score.base_score}, "
              f"Exploitability={classified.classification.exploitability.value}")

def test_batch_classification():
    """Test batch classification."""
    classifier = SecurityIssueClassifier()
    
    issues = [
        SecurityIssue(
            vulnerability_type=VulnerabilityType.BUFFER_OVERFLOW,
            severity=Severity.HIGH,
            file_path="test1.c",
            line_number=10,
            description="Buffer overflow",
            confidence=0.9
        ),
        SecurityIssue(
            vulnerability_type=VulnerabilityType.USE_AFTER_FREE,
            severity=Severity.CRITICAL,
            file_path="test2.c",
            line_number=20,
            description="Use after free",
            confidence=0.85
        ),
        SecurityIssue(
            vulnerability_type=VulnerabilityType.MEMORY_LEAK,
            severity=Severity.LOW,
            file_path="test3.c",
            line_number=30,
            description="Memory leak",
            confidence=0.7
        )
    ]
    
    classified_issues = classifier.classify_issues(issues)
    
    assert len(classified_issues) == len(issues), "Should classify all issues"
    
    for classified in classified_issues:
        assert classified.classification is not None
        assert classified.classification.cvss_score is not None
    
    print(f"✓ Batch classification test passed ({len(classified_issues)} issues)")

def test_serialization():
    """Test that classification can be serialized."""
    classifier = SecurityIssueClassifier()
    
    issue = SecurityIssue(
        vulnerability_type=VulnerabilityType.BUFFER_OVERFLOW,
        severity=Severity.HIGH,
        file_path="test.c",
        line_number=42,
        description="Test",
        confidence=0.9
    )
    
    classified = classifier.classify_issue(issue)
    
    # Convert to dictionary
    issue_dict = classified.to_dict()
    
    assert "classification" in issue_dict
    assert "cvss_score" in issue_dict["classification"]
    assert "exploitability" in issue_dict["classification"]
    assert "attack_vector" in issue_dict["classification"]
    
    print("✓ Serialization test passed")
    print(f"  Classification keys: {list(issue_dict['classification'].keys())}")

if __name__ == "__main__":
    print("Running security issue classification tests...\n")
    
    try:
        test_basic_classification()
        print()
        test_multiple_vulnerability_types()
        print()
        test_batch_classification()
        print()
        test_serialization()
        print()
        print("=" * 60)
        print("All manual tests passed! ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
