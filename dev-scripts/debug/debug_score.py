#!/usr/bin/env python3
"""Debug CVSS score calculation."""

from analysis.security_scanner import (
    SecurityIssue,
    SecurityIssueClassifier,
    VulnerabilityType,
    Severity
)

# Recreate the failing case
issue = SecurityIssue(
    vulnerability_type=VulnerabilityType.NULL_POINTER_DEREFERENCE,
    severity=Severity.LOW,
    file_path='00000',
    line_number=1,
    description='0000000000',
    confidence=0.234375
)

classifier = SecurityIssueClassifier()
classified = classifier.classify_issue(issue)

cvss = classified.classification.cvss_score

print(f"Base Score: {cvss.base_score}")
print(f"Impact Score: {cvss.impact_score}")
print(f"Exploitability Score: {cvss.exploitability_score}")
print(f"Severity Rating: {cvss.severity_rating}")
print()

# Check the calculation
metrics = classifier.VULNERABILITY_METRICS[VulnerabilityType.NULL_POINTER_DEREFERENCE]
print(f"Base Impact: {metrics['base_impact']}")
print(f"Base Exploitability: {metrics['base_exploitability']}")
print()

# Manual calculation
impact = metrics['base_impact']
exploit = metrics['base_exploitability'] * issue.confidence
base = impact * 0.6 + exploit * 0.4
print(f"Manual calculation:")
print(f"  Impact: {impact}")
print(f"  Exploitability (adjusted): {exploit}")
print(f"  Base: {base}")
print(f"  Rounded: {round(base, 1)}")
print()

# Check rating logic
if base < 4.0:
    expected = "Low"
elif base < 7.0:
    expected = "Medium"
elif base < 9.0:
    expected = "High"
else:
    expected = "Critical"

print(f"Expected rating: {expected}")
print(f"Actual rating: {cvss.severity_rating}")
print(f"Match: {expected == cvss.severity_rating}")
