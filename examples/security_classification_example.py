#!/usr/bin/env python3
"""Example demonstrating security issue classification with CVSS scoring.

This example shows how to use the SecurityIssueClassifier to classify
detected vulnerabilities with severity and exploitability assessment.
"""

import tempfile
from pathlib import Path
from analysis.security_scanner import (
    SecurityScanner,
    SecurityIssueClassifier,
    VulnerabilityType,
    Severity
)


def main():
    """Demonstrate security issue classification."""
    
    print("=" * 70)
    print("Security Issue Classification Example")
    print("=" * 70)
    print()
    
    # Create a test C file with multiple vulnerabilities
    test_code = """
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// Buffer overflow vulnerability
void process_input(char *user_input) {
    char buffer[64];
    strcpy(buffer, user_input);  // Unsafe!
    printf("Processed: %s\\n", buffer);
}

// Use-after-free vulnerability
void cleanup_data(struct data *ptr) {
    kfree(ptr);
    ptr->value = 0;  // Use after free!
}

// Integer overflow vulnerability
size_t calculate_size(size_t count, size_t item_size) {
    size_t total = count * item_size;  // Potential overflow
    return total;
}

// Null pointer dereference
void init_device(void) {
    struct device *dev = kmalloc(sizeof(*dev), GFP_KERNEL);
    dev->id = 42;  // No null check!
}

// Format string vulnerability
void log_error(char *error_msg) {
    printk(error_msg);  // User-controlled format string!
}
"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        # Create scanner with classification enabled
        scanner = SecurityScanner()
        
        print("Scanning file for vulnerabilities...")
        print(f"File: {temp_file}")
        print()
        
        # Scan the file (classification is enabled by default)
        issues = scanner.scan_file(temp_file, classify=True)
        
        print(f"Found {len(issues)} security issues")
        print()
        
        # Display each issue with classification
        for i, issue in enumerate(issues, 1):
            print(f"Issue #{i}: {issue.vulnerability_type.value}")
            print(f"  Location: Line {issue.line_number}")
            print(f"  Severity: {issue.severity.value}")
            print(f"  Description: {issue.description}")
            print(f"  Confidence: {issue.confidence:.2f}")
            
            if issue.classification:
                print(f"  Classification:")
                cvss = issue.classification.cvss_score
                print(f"    CVSS Base Score: {cvss.base_score} ({cvss.severity_rating})")
                print(f"    Impact Score: {cvss.impact_score}")
                print(f"    Exploitability Score: {cvss.exploitability_score}")
                print(f"    Exploitability Level: {issue.classification.exploitability.value}")
                print(f"    Attack Vector: {issue.classification.attack_vector}")
                print(f"    Attack Complexity: {issue.classification.attack_complexity}")
                print(f"    Privileges Required: {issue.classification.privileges_required}")
                print(f"    User Interaction: {issue.classification.user_interaction}")
                print(f"    Scope: {issue.classification.scope}")
                print(f"    CIA Impact: C:{issue.classification.confidentiality_impact}, "
                      f"I:{issue.classification.integrity_impact}, "
                      f"A:{issue.classification.availability_impact}")
            
            if issue.recommendation:
                print(f"  Recommendation: {issue.recommendation}")
            
            print()
        
        # Generate comprehensive report
        print("=" * 70)
        print("Security Scan Report")
        print("=" * 70)
        print()
        
        scan_results = {temp_file: issues}
        report = scanner.generate_report(scan_results)
        
        print(f"Scan Timestamp: {report['scan_timestamp']}")
        print(f"Total Files Scanned: {report['total_files_scanned']}")
        print(f"Total Issues Found: {report['total_issues']}")
        print()
        
        print("Severity Breakdown:")
        for severity, count in report['severity_breakdown'].items():
            if count > 0:
                print(f"  {severity.capitalize()}: {count}")
        print()
        
        print("Exploitability Breakdown:")
        for exploit, count in report['exploitability_breakdown'].items():
            if count > 0:
                print(f"  {exploit.capitalize()}: {count}")
        print()
        
        print("CVSS Statistics:")
        print(f"  Average Score: {report['cvss_statistics']['average_score']}")
        print(f"  Maximum Score: {report['cvss_statistics']['max_score']}")
        print(f"  Minimum Score: {report['cvss_statistics']['min_score']}")
        print()
        
        print("Vulnerability Types:")
        for vuln_type, count in report['vulnerability_types'].items():
            print(f"  {vuln_type}: {count}")
        print()
        
        # Demonstrate manual classification
        print("=" * 70)
        print("Manual Classification Example")
        print("=" * 70)
        print()
        
        from analysis.security_scanner import SecurityIssue
        
        # Create a custom issue
        custom_issue = SecurityIssue(
            vulnerability_type=VulnerabilityType.BUFFER_OVERFLOW,
            severity=Severity.HIGH,
            file_path="custom.c",
            line_number=100,
            description="Custom buffer overflow in network packet handler",
            confidence=0.95,
            metadata={
                "in_critical_path": True,
                "user_controlled_input": True
            }
        )
        
        # Classify it
        classifier = SecurityIssueClassifier()
        classified = classifier.classify_issue(custom_issue)
        
        print("Custom Issue Classification:")
        print(f"  Vulnerability: {classified.vulnerability_type.value}")
        print(f"  CVSS Base Score: {classified.classification.cvss_score.base_score}")
        print(f"  Severity Rating: {classified.classification.cvss_score.severity_rating}")
        print(f"  Exploitability: {classified.classification.exploitability.value}")
        print()
        
        print("Note: Metadata flags (in_critical_path, user_controlled_input)")
        print("      increased the impact and exploitability scores.")
        print()
        
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)
    
    print("=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
