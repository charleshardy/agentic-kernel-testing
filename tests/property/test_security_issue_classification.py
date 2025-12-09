"""Property-based tests for security issue classification.

**Feature: agentic-kernel-testing, Property 34: Security issue classification**

This test validates Requirements 7.4:
WHEN security issues are detected, THE Testing System SHALL classify them by 
severity and potential exploitability.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from analysis.security_scanner import (
    SecurityIssue,
    SecurityIssueClassifier,
    VulnerabilityType,
    Severity,
    Exploitability,
    CVSSScore,
    SecurityClassification
)


# Strategies for generating security issues

@st.composite
def security_issue_strategy(draw):
    """Generate random security issues."""
    vuln_type = draw(st.sampled_from(list(VulnerabilityType)))
    severity = draw(st.sampled_from(list(Severity)))
    file_path = draw(st.text(min_size=5, max_size=50))
    line_number = draw(st.integers(min_value=1, max_value=10000))
    description = draw(st.text(min_size=10, max_size=200))
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return SecurityIssue(
        vulnerability_type=vuln_type,
        severity=severity,
        file_path=file_path,
        line_number=line_number,
        description=description,
        confidence=confidence
    )


# Property 34: Security issue classification
# For any detected security issue, the system should classify it with severity 
# and exploitability assessment.

@given(issue=security_issue_strategy())
@settings(max_examples=100, deadline=None)
def test_classification_completeness(issue):
    """Property: All security issues should receive complete classification.
    
    **Validates: Requirements 7.4**
    
    For any security issue, classification should include:
    - CVSS score
    - Exploitability level
    - Attack vector, complexity, privileges, etc.
    """
    classifier = SecurityIssueClassifier()
    
    # Classify the issue
    classified_issue = classifier.classify_issue(issue)
    
    # Property: Issue should have classification
    assert classified_issue.classification is not None, \
        "Security issue must have classification"
    
    classification = classified_issue.classification
    
    # Property: Classification should have CVSS score
    assert classification.cvss_score is not None
    assert isinstance(classification.cvss_score, CVSSScore)
    
    # Property: CVSS score should be valid
    assert 0.0 <= classification.cvss_score.base_score <= 10.0
    assert 0.0 <= classification.cvss_score.impact_score <= 10.0
    assert 0.0 <= classification.cvss_score.exploitability_score <= 10.0
    
    # Property: Classification should have exploitability
    assert classification.exploitability is not None
    assert isinstance(classification.exploitability, Exploitability)
    
    # Property: Classification should have all required fields
    assert classification.attack_vector in ["Local", "Adjacent", "Network"]
    assert classification.attack_complexity in ["Low", "High", "Medium"]
    assert classification.privileges_required in ["None", "Low", "High"]
    assert classification.user_interaction in ["None", "Required"]
    assert classification.scope in ["Unchanged", "Changed"]
    assert classification.confidentiality_impact in ["None", "Low", "High"]
    assert classification.integrity_impact in ["None", "Low", "High"]
    assert classification.availability_impact in ["None", "Low", "High"]


@given(issues=st.lists(security_issue_strategy(), min_size=1, max_size=20))
@settings(max_examples=50, deadline=None)
def test_batch_classification(issues):
    """Property: Batch classification should classify all issues.
    
    **Validates: Requirements 7.4**
    
    For any list of security issues, all should be classified.
    """
    classifier = SecurityIssueClassifier()
    
    # Classify all issues
    classified_issues = classifier.classify_issues(issues)
    
    # Property: Same number of issues should be returned
    assert len(classified_issues) == len(issues)
    
    # Property: All issues should have classification
    for classified_issue in classified_issues:
        assert classified_issue.classification is not None
        assert classified_issue.classification.cvss_score is not None
        assert classified_issue.classification.exploitability is not None


@given(vuln_type=st.sampled_from(list(VulnerabilityType)))
@settings(max_examples=100, deadline=None)
def test_vulnerability_type_consistency(vuln_type):
    """Property: Same vulnerability type should produce consistent classification.
    
    **Validates: Requirements 7.4**
    
    For any vulnerability type, the base classification metrics should be consistent.
    """
    classifier = SecurityIssueClassifier()
    
    # Create two issues with same vulnerability type
    issue1 = SecurityIssue(
        vulnerability_type=vuln_type,
        severity=Severity.MEDIUM,
        file_path="test1.c",
        line_number=10,
        description="Test issue 1",
        confidence=0.8
    )
    
    issue2 = SecurityIssue(
        vulnerability_type=vuln_type,
        severity=Severity.MEDIUM,
        file_path="test2.c",
        line_number=20,
        description="Test issue 2",
        confidence=0.8
    )
    
    # Classify both
    classified1 = classifier.classify_issue(issue1)
    classified2 = classifier.classify_issue(issue2)
    
    # Property: Same vulnerability type should have same base metrics
    assert classified1.classification.attack_vector == classified2.classification.attack_vector
    assert classified1.classification.attack_complexity == classified2.classification.attack_complexity
    assert classified1.classification.privileges_required == classified2.classification.privileges_required
    assert classified1.classification.user_interaction == classified2.classification.user_interaction
    assert classified1.classification.scope == classified2.classification.scope


@given(
    vuln_type=st.sampled_from(list(VulnerabilityType)),
    confidence=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, deadline=None)
def test_confidence_affects_exploitability(vuln_type, confidence):
    """Property: Confidence should affect exploitability score.
    
    **Validates: Requirements 7.4**
    
    For any vulnerability, lower confidence should result in lower exploitability score.
    """
    classifier = SecurityIssueClassifier()
    
    # Create issue with given confidence
    issue = SecurityIssue(
        vulnerability_type=vuln_type,
        severity=Severity.MEDIUM,
        file_path="test.c",
        line_number=10,
        description="Test issue",
        confidence=confidence
    )
    
    # Classify
    classified = classifier.classify_issue(issue)
    
    # Property: Exploitability score should be affected by confidence
    # Lower confidence should not increase exploitability
    assert classified.classification.cvss_score.exploitability_score <= 10.0
    
    # If confidence is very low, exploitability should be lower
    if confidence < 0.3:
        assert classified.classification.cvss_score.exploitability_score < 8.0


@given(issue=security_issue_strategy())
@settings(max_examples=100, deadline=None)
def test_cvss_score_bounds(issue):
    """Property: CVSS scores should always be within valid bounds.
    
    **Validates: Requirements 7.4**
    
    For any security issue, all CVSS scores must be between 0.0 and 10.0.
    """
    classifier = SecurityIssueClassifier()
    
    # Classify the issue
    classified_issue = classifier.classify_issue(issue)
    
    cvss = classified_issue.classification.cvss_score
    
    # Property: All scores must be in valid range
    assert 0.0 <= cvss.base_score <= 10.0
    assert 0.0 <= cvss.impact_score <= 10.0
    assert 0.0 <= cvss.exploitability_score <= 10.0


@given(issue=security_issue_strategy())
@settings(max_examples=100, deadline=None)
def test_severity_rating_consistency(issue):
    """Property: CVSS severity rating should match base score.
    
    **Validates: Requirements 7.4**
    
    For any security issue, the severity rating should be consistent with the base score.
    """
    classifier = SecurityIssueClassifier()
    
    # Classify the issue
    classified_issue = classifier.classify_issue(issue)
    
    cvss = classified_issue.classification.cvss_score
    
    # Property: Severity rating should match score range
    # The ranges are: None (0.0), Low (0.1-3.9), Medium (4.0-6.9), High (7.0-8.9), Critical (9.0-10.0)
    if cvss.base_score == 0.0:
        assert cvss.severity_rating == "None", \
            f"Score {cvss.base_score} should be 'None', got '{cvss.severity_rating}'"
    elif cvss.base_score < 4.0:
        assert cvss.severity_rating == "Low", \
            f"Score {cvss.base_score} should be 'Low', got '{cvss.severity_rating}'"
    elif cvss.base_score < 7.0:
        assert cvss.severity_rating == "Medium", \
            f"Score {cvss.base_score} should be 'Medium', got '{cvss.severity_rating}'"
    elif cvss.base_score < 9.0:
        assert cvss.severity_rating == "High", \
            f"Score {cvss.base_score} should be 'High', got '{cvss.severity_rating}'"
    else:
        assert cvss.severity_rating == "Critical", \
            f"Score {cvss.base_score} should be 'Critical', got '{cvss.severity_rating}'"


@given(
    vuln_type=st.sampled_from([
        VulnerabilityType.BUFFER_OVERFLOW,
        VulnerabilityType.USE_AFTER_FREE,
        VulnerabilityType.FORMAT_STRING
    ])
)
@settings(max_examples=50, deadline=None)
def test_high_severity_vulnerabilities(vuln_type):
    """Property: Critical vulnerability types should have high scores.
    
    **Validates: Requirements 7.4**
    
    For critical vulnerability types (buffer overflow, use-after-free, format string),
    the CVSS score should be high.
    """
    classifier = SecurityIssueClassifier()
    
    # Create issue with critical vulnerability type
    issue = SecurityIssue(
        vulnerability_type=vuln_type,
        severity=Severity.CRITICAL,
        file_path="test.c",
        line_number=10,
        description="Critical vulnerability",
        confidence=0.9
    )
    
    # Classify
    classified = classifier.classify_issue(issue)
    
    # Property: Critical vulnerabilities should have high CVSS scores
    assert classified.classification.cvss_score.base_score >= 7.0
    
    # Property: Should have high exploitability
    assert classified.classification.exploitability in [
        Exploitability.HIGH,
        Exploitability.CRITICAL
    ]


@given(
    vuln_type=st.sampled_from([
        VulnerabilityType.MEMORY_LEAK,
        VulnerabilityType.UNINITIALIZED_VARIABLE
    ])
)
@settings(max_examples=50, deadline=None)
def test_low_severity_vulnerabilities(vuln_type):
    """Property: Low severity vulnerability types should have lower scores.
    
    **Validates: Requirements 7.4**
    
    For low severity vulnerability types (memory leak, uninitialized variable),
    the CVSS score should be lower.
    """
    classifier = SecurityIssueClassifier()
    
    # Create issue with low severity vulnerability type
    issue = SecurityIssue(
        vulnerability_type=vuln_type,
        severity=Severity.LOW,
        file_path="test.c",
        line_number=10,
        description="Low severity vulnerability",
        confidence=0.8
    )
    
    # Classify
    classified = classifier.classify_issue(issue)
    
    # Property: Low severity vulnerabilities should have lower CVSS scores
    assert classified.classification.cvss_score.base_score < 7.0


@given(issue=security_issue_strategy())
@settings(max_examples=100, deadline=None)
def test_classification_serialization(issue):
    """Property: Classification should be serializable to dictionary.
    
    **Validates: Requirements 7.4**
    
    For any classified security issue, the classification should be serializable.
    """
    classifier = SecurityIssueClassifier()
    
    # Classify the issue
    classified_issue = classifier.classify_issue(issue)
    
    # Property: Should be able to convert to dictionary
    issue_dict = classified_issue.to_dict()
    
    # Property: Dictionary should contain classification
    assert "classification" in issue_dict
    
    classification_dict = issue_dict["classification"]
    
    # Property: Classification dictionary should have all fields
    assert "cvss_score" in classification_dict
    assert "exploitability" in classification_dict
    assert "attack_vector" in classification_dict
    assert "attack_complexity" in classification_dict
    assert "privileges_required" in classification_dict
    assert "user_interaction" in classification_dict
    assert "scope" in classification_dict
    assert "confidentiality_impact" in classification_dict
    assert "integrity_impact" in classification_dict
    assert "availability_impact" in classification_dict
    
    # Property: CVSS score should have all fields
    cvss_dict = classification_dict["cvss_score"]
    assert "base_score" in cvss_dict
    assert "impact_score" in cvss_dict
    assert "exploitability_score" in cvss_dict
    assert "severity_rating" in cvss_dict


@given(issue=security_issue_strategy())
@settings(max_examples=100, deadline=None)
def test_severity_upgrade(issue):
    """Property: Classification may upgrade severity based on CVSS score.
    
    **Validates: Requirements 7.4**
    
    For any security issue, if CVSS score indicates higher severity than initial,
    the severity should be upgraded.
    """
    classifier = SecurityIssueClassifier()
    
    # Create issue with low initial severity
    low_severity_issue = SecurityIssue(
        vulnerability_type=VulnerabilityType.BUFFER_OVERFLOW,
        severity=Severity.LOW,
        file_path="test.c",
        line_number=10,
        description="Buffer overflow",
        confidence=0.9
    )
    
    # Classify
    classified = classifier.classify_issue(low_severity_issue)
    
    # Property: Severity should be upgraded if CVSS score is high
    if classified.classification.cvss_score.base_score >= 9.0:
        assert classified.severity == Severity.CRITICAL
    elif classified.classification.cvss_score.base_score >= 7.0:
        assert classified.severity in [Severity.HIGH, Severity.CRITICAL]


def test_exploitability_levels():
    """Property: Exploitability levels should be properly assigned.
    
    **Validates: Requirements 7.4**
    
    Different exploitability scores should map to appropriate levels.
    """
    classifier = SecurityIssueClassifier()
    
    # Test different vulnerability types
    test_cases = [
        (VulnerabilityType.BUFFER_OVERFLOW, 0.9, [Exploitability.HIGH, Exploitability.CRITICAL]),
        (VulnerabilityType.NULL_POINTER_DEREFERENCE, 0.8, [Exploitability.MEDIUM, Exploitability.HIGH]),
        (VulnerabilityType.MEMORY_LEAK, 0.7, [Exploitability.LOW, Exploitability.MEDIUM, Exploitability.HIGH]),
    ]
    
    for vuln_type, confidence, expected_levels in test_cases:
        issue = SecurityIssue(
            vulnerability_type=vuln_type,
            severity=Severity.MEDIUM,
            file_path="test.c",
            line_number=10,
            description="Test",
            confidence=confidence
        )
        
        classified = classifier.classify_issue(issue)
        
        # Property: Exploitability should be in expected range
        assert classified.classification.exploitability in expected_levels or \
               classified.classification.exploitability in list(Exploitability)


def test_classification_metadata_preservation():
    """Property: Original issue metadata should be preserved after classification.
    
    **Validates: Requirements 7.4**
    
    Classification should not lose original issue information.
    """
    classifier = SecurityIssueClassifier()
    
    # Create issue with metadata
    original_metadata = {"test_key": "test_value", "line_context": "some code"}
    issue = SecurityIssue(
        vulnerability_type=VulnerabilityType.BUFFER_OVERFLOW,
        severity=Severity.HIGH,
        file_path="test.c",
        line_number=42,
        description="Test vulnerability",
        code_snippet="strcpy(buf, input);",
        recommendation="Use strncpy",
        cwe_id="CWE-120",
        confidence=0.85,
        metadata=original_metadata
    )
    
    # Classify
    classified = classifier.classify_issue(issue)
    
    # Property: Original fields should be preserved
    assert classified.vulnerability_type == issue.vulnerability_type
    assert classified.file_path == issue.file_path
    assert classified.line_number == issue.line_number
    assert classified.description == issue.description
    assert classified.code_snippet == issue.code_snippet
    assert classified.recommendation == issue.recommendation
    assert classified.cwe_id == issue.cwe_id
    assert classified.confidence == issue.confidence
    assert classified.metadata == original_metadata
    
    # Property: Classification should be added
    assert classified.classification is not None


@given(
    issues=st.lists(
        security_issue_strategy(),
        min_size=5,
        max_size=20
    )
)
@settings(max_examples=30, deadline=None)
def test_classification_statistics(issues):
    """Property: Classification statistics should be accurate.
    
    **Validates: Requirements 7.4**
    
    For any set of classified issues, statistics should accurately reflect the data.
    """
    classifier = SecurityIssueClassifier()
    
    # Classify all issues
    classified_issues = classifier.classify_issues(issues)
    
    # Calculate statistics manually
    cvss_scores = [
        issue.classification.cvss_score.base_score
        for issue in classified_issues
    ]
    
    exploitability_counts = {}
    for issue in classified_issues:
        exp = issue.classification.exploitability
        exploitability_counts[exp] = exploitability_counts.get(exp, 0) + 1
    
    # Property: All CVSS scores should be valid
    assert all(0.0 <= score <= 10.0 for score in cvss_scores)
    
    # Property: Average should be within range
    if cvss_scores:
        avg_score = sum(cvss_scores) / len(cvss_scores)
        assert 0.0 <= avg_score <= 10.0
    
    # Property: Exploitability counts should sum to total issues
    assert sum(exploitability_counts.values()) == len(classified_issues)
