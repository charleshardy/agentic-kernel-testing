"""Security report generator with comprehensive reporting and remediation recommendations.

This module generates comprehensive security reports from scan results, including
proof-of-concept exploit generation and remediation recommendations.
"""

import json
import html
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from analysis.security_scanner import (
    SecurityIssue,
    VulnerabilityType,
    Severity,
    Exploitability,
    SecurityClassification
)


class ReportFormat(str, Enum):
    """Supported report formats."""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    TEXT = "text"


@dataclass
class ProofOfConcept:
    """Proof-of-concept exploit for a vulnerability."""
    vulnerability_id: str
    exploit_code: str
    description: str
    prerequisites: List[str] = field(default_factory=list)
    impact_demonstration: str = ""
    mitigation_bypassed: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vulnerability_id": self.vulnerability_id,
            "exploit_code": self.exploit_code,
            "description": self.description,
            "prerequisites": self.prerequisites,
            "impact_demonstration": self.impact_demonstration,
            "mitigation_bypassed": self.mitigation_bypassed
        }


@dataclass
class RemediationRecommendation:
    """Remediation recommendation for a vulnerability."""
    vulnerability_id: str
    priority: str  # Critical, High, Medium, Low
    short_term_fix: str
    long_term_fix: str
    code_example: Optional[str] = None
    references: List[str] = field(default_factory=list)
    estimated_effort: str = ""  # Hours, Days, Weeks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vulnerability_id": self.vulnerability_id,
            "priority": self.priority,
            "short_term_fix": self.short_term_fix,
            "long_term_fix": self.long_term_fix,
            "code_example": self.code_example,
            "references": self.references,
            "estimated_effort": self.estimated_effort
        }


@dataclass
class SecurityReport:
    """Comprehensive security report."""
    report_id: str
    timestamp: datetime
    scan_summary: Dict[str, Any]
    findings: List[SecurityIssue]
    proof_of_concepts: List[ProofOfConcept] = field(default_factory=list)
    remediation_recommendations: List[RemediationRecommendation] = field(default_factory=list)
    executive_summary: str = ""
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "scan_summary": self.scan_summary,
            "findings": [f.to_dict() for f in self.findings],
            "proof_of_concepts": [poc.to_dict() for poc in self.proof_of_concepts],
            "remediation_recommendations": [r.to_dict() for r in self.remediation_recommendations],
            "executive_summary": self.executive_summary,
            "risk_assessment": self.risk_assessment,
            "metadata": self.metadata
        }


class ProofOfConceptGenerator:
    """Generator for proof-of-concept exploits."""
    
    # POC templates for different vulnerability types
    POC_TEMPLATES = {
        VulnerabilityType.BUFFER_OVERFLOW: """
// Proof-of-Concept: Buffer Overflow in {file_path}:{line_number}
// Vulnerability: {description}

#include <stdio.h>
#include <string.h>

int main() {{
    char buffer[64];
    char overflow_data[128];
    
    // Fill overflow data with pattern
    memset(overflow_data, 'A', sizeof(overflow_data));
    overflow_data[127] = '\\0';
    
    // Trigger overflow - this will overwrite adjacent memory
    strcpy(buffer, overflow_data);  // UNSAFE!
    
    printf("Buffer overflow triggered\\n");
    printf("Buffer contents: %s\\n", buffer);
    
    return 0;
}}

// Expected Impact:
// - Memory corruption
// - Potential code execution if return address overwritten
// - Crash or undefined behavior
""",
        
        VulnerabilityType.USE_AFTER_FREE: """
// Proof-of-Concept: Use-After-Free in {file_path}:{line_number}
// Vulnerability: {description}

#include <stdio.h>
#include <stdlib.h>

struct data {{
    int value;
    void (*callback)(int);
}};

void print_value(int v) {{
    printf("Value: %d\\n", v);
}}

int main() {{
    struct data *ptr = malloc(sizeof(struct data));
    ptr->value = 42;
    ptr->callback = print_value;
    
    // Free the memory
    free(ptr);
    
    // Use after free - accessing freed memory
    ptr->callback(ptr->value);  // UNSAFE!
    
    return 0;
}}

// Expected Impact:
// - Access to freed memory
// - Potential arbitrary code execution
// - Crash or data corruption
""",
        
        VulnerabilityType.INTEGER_OVERFLOW: """
// Proof-of-Concept: Integer Overflow in {file_path}:{line_number}
// Vulnerability: {description}

#include <stdio.h>
#include <limits.h>

int main() {{
    unsigned int a = UINT_MAX;
    unsigned int b = 1;
    unsigned int result;
    
    // Integer overflow
    result = a + b;  // Wraps around to 0
    
    printf("a = %u\\n", a);
    printf("b = %u\\n", b);
    printf("result = %u (expected %u, got overflow)\\n", result, a + b);
    
    // Demonstrate allocation vulnerability
    size_t size = result * sizeof(int);  // Size becomes 0!
    int *buffer = malloc(size);
    
    if (buffer) {{
        // Writing to undersized buffer
        for (int i = 0; i < 100; i++) {{
            buffer[i] = i;  // Buffer overflow due to integer overflow
        }}
        free(buffer);
    }}
    
    return 0;
}}

// Expected Impact:
// - Incorrect calculations
// - Buffer overflows due to undersized allocations
// - Logic errors in size checks
""",
        
        VulnerabilityType.NULL_POINTER_DEREFERENCE: """
// Proof-of-Concept: Null Pointer Dereference in {file_path}:{line_number}
// Vulnerability: {description}

#include <stdio.h>
#include <stdlib.h>

struct device {{
    int id;
    char name[32];
}};

int main() {{
    struct device *dev = malloc(sizeof(struct device));
    
    // Simulate allocation failure
    free(dev);
    dev = NULL;
    
    // Dereference without null check
    printf("Device ID: %d\\n", dev->id);  // UNSAFE! Null pointer dereference
    
    return 0;
}}

// Expected Impact:
// - Kernel panic or segmentation fault
// - Denial of service
// - System crash
""",
        
        VulnerabilityType.FORMAT_STRING: """
// Proof-of-Concept: Format String Vulnerability in {file_path}:{line_number}
// Vulnerability: {description}

#include <stdio.h>

int main(int argc, char *argv[]) {{
    char buffer[100];
    
    if (argc < 2) {{
        printf("Usage: %s <input>\\n", argv[0]);
        return 1;
    }}
    
    // Vulnerable: user input used as format string
    printf(argv[1]);  // UNSAFE!
    
    // Demonstrate information leak
    printf("\\n");
    
    // Try with: ./poc "%x %x %x %x"
    // This will leak stack values
    
    return 0;
}}

// Expected Impact:
// - Information disclosure (stack/memory contents)
// - Arbitrary memory read
// - Potential arbitrary memory write with %n
// - Code execution in some cases
""",
        
        VulnerabilityType.RACE_CONDITION: """
// Proof-of-Concept: Race Condition in {file_path}:{line_number}
// Vulnerability: {description}

#include <stdio.h>
#include <pthread.h>
#include <unistd.h>

int shared_counter = 0;

void *increment_thread(void *arg) {{
    for (int i = 0; i < 100000; i++) {{
        // Race condition: non-atomic read-modify-write
        int temp = shared_counter;
        temp++;
        shared_counter = temp;
    }}
    return NULL;
}}

int main() {{
    pthread_t thread1, thread2;
    
    pthread_create(&thread1, NULL, increment_thread, NULL);
    pthread_create(&thread2, NULL, increment_thread, NULL);
    
    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);
    
    printf("Expected: 200000\\n");
    printf("Actual: %d\\n", shared_counter);
    printf("Lost updates: %d\\n", 200000 - shared_counter);
    
    return 0;
}}

// Expected Impact:
// - Data corruption
// - Inconsistent state
// - Security bypass if used in access control
""",
    }
    
    def generate_poc(self, issue: SecurityIssue) -> Optional[ProofOfConcept]:
        """Generate proof-of-concept exploit for a vulnerability.
        
        Args:
            issue: Security issue to generate POC for
            
        Returns:
            ProofOfConcept or None if not applicable
        """
        # Only generate POCs for high-severity issues
        if issue.severity not in [Severity.HIGH, Severity.CRITICAL]:
            return None
        
        template = self.POC_TEMPLATES.get(issue.vulnerability_type)
        if not template:
            return None
        
        # Format template with issue details
        exploit_code = template.format(
            file_path=issue.file_path,
            line_number=issue.line_number,
            description=issue.description
        )
        
        # Generate description
        description = f"Proof-of-concept demonstrating {issue.vulnerability_type.value} vulnerability"
        
        # Determine prerequisites
        prerequisites = self._get_prerequisites(issue.vulnerability_type)
        
        # Generate impact demonstration
        impact = self._get_impact_demonstration(issue.vulnerability_type)
        
        poc_id = f"POC-{issue.vulnerability_type.value}-{issue.line_number}"
        
        return ProofOfConcept(
            vulnerability_id=poc_id,
            exploit_code=exploit_code,
            description=description,
            prerequisites=prerequisites,
            impact_demonstration=impact
        )
    
    def _get_prerequisites(self, vuln_type: VulnerabilityType) -> List[str]:
        """Get prerequisites for exploiting a vulnerability type."""
        prerequisites_map = {
            VulnerabilityType.BUFFER_OVERFLOW: [
                "Compiler without stack protection (compile with -fno-stack-protector)",
                "ASLR disabled or bypassed",
                "Ability to provide input to vulnerable function"
            ],
            VulnerabilityType.USE_AFTER_FREE: [
                "Ability to trigger allocation and free",
                "Ability to control subsequent allocations",
                "Knowledge of memory layout"
            ],
            VulnerabilityType.INTEGER_OVERFLOW: [
                "Ability to control integer operands",
                "Vulnerable calculation used in size determination"
            ],
            VulnerabilityType.NULL_POINTER_DEREFERENCE: [
                "Ability to trigger allocation failure",
                "Code path that doesn't check for NULL"
            ],
            VulnerabilityType.FORMAT_STRING: [
                "Ability to provide format string input",
                "Vulnerable printf-family function"
            ],
            VulnerabilityType.RACE_CONDITION: [
                "Multi-threaded or multi-process environment",
                "Ability to trigger concurrent access",
                "Timing control or repeated attempts"
            ]
        }
        return prerequisites_map.get(vuln_type, [])
    
    def _get_impact_demonstration(self, vuln_type: VulnerabilityType) -> str:
        """Get impact demonstration for a vulnerability type."""
        impact_map = {
            VulnerabilityType.BUFFER_OVERFLOW: 
                "Memory corruption leading to potential arbitrary code execution",
            VulnerabilityType.USE_AFTER_FREE:
                "Access to freed memory, potential arbitrary code execution",
            VulnerabilityType.INTEGER_OVERFLOW:
                "Incorrect calculations leading to buffer overflows or logic errors",
            VulnerabilityType.NULL_POINTER_DEREFERENCE:
                "Kernel panic or system crash (denial of service)",
            VulnerabilityType.FORMAT_STRING:
                "Information disclosure and potential arbitrary memory write",
            VulnerabilityType.RACE_CONDITION:
                "Data corruption and potential security bypass"
        }
        return impact_map.get(vuln_type, "Security vulnerability impact")


class RemediationRecommendationGenerator:
    """Generator for remediation recommendations."""
    
    # Remediation templates for different vulnerability types
    REMEDIATION_TEMPLATES = {
        VulnerabilityType.BUFFER_OVERFLOW: {
            "short_term": "Replace unsafe string functions with bounded alternatives",
            "long_term": "Implement comprehensive input validation and use safe string libraries",
            "code_example": """
// Before (unsafe):
strcpy(dest, src);

// After (safe):
strncpy(dest, src, sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\\0';

// Or better, use strlcpy if available:
strlcpy(dest, src, sizeof(dest));
""",
            "references": [
                "CWE-120: Buffer Copy without Checking Size of Input",
                "CERT C Coding Standard: STR31-C",
                "https://cwe.mitre.org/data/definitions/120.html"
            ],
            "effort": "2-4 hours per instance"
        },
        
        VulnerabilityType.USE_AFTER_FREE: {
            "short_term": "Set pointers to NULL after freeing and add NULL checks",
            "long_term": "Implement reference counting or use smart pointers",
            "code_example": """
// Before (unsafe):
kfree(ptr);
ptr->field = value;  // Use after free!

// After (safe):
kfree(ptr);
ptr = NULL;

// Later, before use:
if (ptr != NULL) {
    ptr->field = value;
}
""",
            "references": [
                "CWE-416: Use After Free",
                "CERT C Coding Standard: MEM30-C",
                "https://cwe.mitre.org/data/definitions/416.html"
            ],
            "effort": "4-8 hours per instance"
        },
        
        VulnerabilityType.INTEGER_OVERFLOW: {
            "short_term": "Add overflow checks before arithmetic operations",
            "long_term": "Use overflow-safe functions and compiler built-ins",
            "code_example": """
// Before (unsafe):
size_t size = count * element_size;
buffer = kmalloc(size, GFP_KERNEL);

// After (safe):
size_t size;
if (check_mul_overflow(count, element_size, &size)) {
    return -EINVAL;  // Overflow detected
}
buffer = kmalloc(size, GFP_KERNEL);

// Or use kernel helpers:
buffer = kmalloc_array(count, element_size, GFP_KERNEL);
""",
            "references": [
                "CWE-190: Integer Overflow or Wraparound",
                "CERT C Coding Standard: INT32-C",
                "https://cwe.mitre.org/data/definitions/190.html"
            ],
            "effort": "2-4 hours per instance"
        },
        
        VulnerabilityType.NULL_POINTER_DEREFERENCE: {
            "short_term": "Add NULL checks after all allocations",
            "long_term": "Implement consistent error handling patterns",
            "code_example": """
// Before (unsafe):
ptr = kmalloc(size, GFP_KERNEL);
ptr->field = value;  // No NULL check!

// After (safe):
ptr = kmalloc(size, GFP_KERNEL);
if (!ptr) {
    return -ENOMEM;
}
ptr->field = value;
""",
            "references": [
                "CWE-476: NULL Pointer Dereference",
                "CERT C Coding Standard: EXP34-C",
                "https://cwe.mitre.org/data/definitions/476.html"
            ],
            "effort": "1-2 hours per instance"
        },
        
        VulnerabilityType.FORMAT_STRING: {
            "short_term": "Use constant format strings, never user input",
            "long_term": "Enable format string protection compiler flags",
            "code_example": """
// Before (unsafe):
printk(user_input);

// After (safe):
printk("%s", user_input);

// Or for logging:
printk(KERN_INFO "User message: %s\\n", user_input);
""",
            "references": [
                "CWE-134: Use of Externally-Controlled Format String",
                "CERT C Coding Standard: FIO30-C",
                "https://cwe.mitre.org/data/definitions/134.html"
            ],
            "effort": "1-2 hours per instance"
        },
        
        VulnerabilityType.RACE_CONDITION: {
            "short_term": "Add proper locking around shared data access",
            "long_term": "Design lock-free algorithms or use atomic operations",
            "code_example": """
// Before (unsafe):
shared_counter++;

// After (safe with locking):
spin_lock(&counter_lock);
shared_counter++;
spin_unlock(&counter_lock);

// Or use atomic operations:
atomic_inc(&shared_counter);
""",
            "references": [
                "CWE-362: Concurrent Execution using Shared Resource",
                "CERT C Coding Standard: CON43-C",
                "https://cwe.mitre.org/data/definitions/362.html"
            ],
            "effort": "8-16 hours per instance"
        },
        
        VulnerabilityType.MEMORY_LEAK: {
            "short_term": "Ensure kfree() is called on all exit paths",
            "long_term": "Use RAII patterns or automated resource management",
            "code_example": """
// Before (unsafe):
ptr = kmalloc(size, GFP_KERNEL);
if (error_condition) {
    return -EINVAL;  // Memory leak!
}
kfree(ptr);

// After (safe):
ptr = kmalloc(size, GFP_KERNEL);
if (error_condition) {
    kfree(ptr);
    return -EINVAL;
}
kfree(ptr);
""",
            "references": [
                "CWE-401: Missing Release of Memory after Effective Lifetime",
                "https://cwe.mitre.org/data/definitions/401.html"
            ],
            "effort": "2-4 hours per instance"
        }
    }
    
    def generate_recommendation(self, issue: SecurityIssue) -> RemediationRecommendation:
        """Generate remediation recommendation for a vulnerability.
        
        Args:
            issue: Security issue to generate recommendation for
            
        Returns:
            RemediationRecommendation
        """
        template = self.REMEDIATION_TEMPLATES.get(
            issue.vulnerability_type,
            self._get_default_template()
        )
        
        # Determine priority based on severity and exploitability
        priority = self._determine_priority(issue)
        
        rec_id = f"REC-{issue.vulnerability_type.value}-{issue.line_number}"
        
        return RemediationRecommendation(
            vulnerability_id=rec_id,
            priority=priority,
            short_term_fix=template["short_term"],
            long_term_fix=template["long_term"],
            code_example=template.get("code_example"),
            references=template.get("references", []),
            estimated_effort=template.get("effort", "Unknown")
        )
    
    def _get_default_template(self) -> Dict[str, Any]:
        """Get default remediation template."""
        return {
            "short_term": "Review and fix the identified security issue",
            "long_term": "Implement secure coding practices and code review",
            "code_example": None,
            "references": [],
            "effort": "Unknown"
        }
    
    def _determine_priority(self, issue: SecurityIssue) -> str:
        """Determine remediation priority based on issue severity and exploitability."""
        if issue.severity == Severity.CRITICAL:
            return "Critical"
        elif issue.severity == Severity.HIGH:
            if issue.classification and issue.classification.exploitability in [
                Exploitability.CRITICAL, Exploitability.HIGH
            ]:
                return "Critical"
            return "High"
        elif issue.severity == Severity.MEDIUM:
            return "Medium"
        else:
            return "Low"


class SecurityReportGenerator:
    """Main security report generator."""
    
    def __init__(self):
        """Initialize security report generator."""
        self.poc_generator = ProofOfConceptGenerator()
        self.remediation_generator = RemediationRecommendationGenerator()
    
    def generate_report(
        self,
        scan_results: Dict[str, List[SecurityIssue]],
        report_id: Optional[str] = None
    ) -> SecurityReport:
        """Generate comprehensive security report.
        
        Args:
            scan_results: Dictionary mapping file paths to security issues
            report_id: Optional report ID (generated if not provided)
            
        Returns:
            SecurityReport
        """
        if report_id is None:
            report_id = f"SEC-REPORT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Flatten all issues
        all_issues = []
        for issues in scan_results.values():
            all_issues.extend(issues)
        
        # Generate scan summary
        scan_summary = self._generate_scan_summary(scan_results, all_issues)
        
        # Generate POCs for high-severity issues
        proof_of_concepts = []
        for issue in all_issues:
            poc = self.poc_generator.generate_poc(issue)
            if poc:
                proof_of_concepts.append(poc)
        
        # Generate remediation recommendations
        remediation_recommendations = []
        for issue in all_issues:
            rec = self.remediation_generator.generate_recommendation(issue)
            remediation_recommendations.append(rec)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            all_issues, scan_summary
        )
        
        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(all_issues)
        
        return SecurityReport(
            report_id=report_id,
            timestamp=datetime.now(),
            scan_summary=scan_summary,
            findings=all_issues,
            proof_of_concepts=proof_of_concepts,
            remediation_recommendations=remediation_recommendations,
            executive_summary=executive_summary,
            risk_assessment=risk_assessment
        )
    
    def _generate_scan_summary(
        self,
        scan_results: Dict[str, List[SecurityIssue]],
        all_issues: List[SecurityIssue]
    ) -> Dict[str, Any]:
        """Generate scan summary statistics."""
        severity_counts = {
            "critical": sum(1 for i in all_issues if i.severity == Severity.CRITICAL),
            "high": sum(1 for i in all_issues if i.severity == Severity.HIGH),
            "medium": sum(1 for i in all_issues if i.severity == Severity.MEDIUM),
            "low": sum(1 for i in all_issues if i.severity == Severity.LOW)
        }
        
        vuln_type_counts = {}
        for issue in all_issues:
            vtype = issue.vulnerability_type.value
            vuln_type_counts[vtype] = vuln_type_counts.get(vtype, 0) + 1
        
        # Calculate CVSS statistics
        cvss_scores = [
            issue.classification.cvss_score.base_score
            for issue in all_issues
            if issue.classification
        ]
        
        return {
            "total_files_scanned": len(scan_results),
            "total_issues": len(all_issues),
            "severity_breakdown": severity_counts,
            "vulnerability_types": vuln_type_counts,
            "cvss_statistics": {
                "average": round(sum(cvss_scores) / len(cvss_scores), 1) if cvss_scores else 0.0,
                "max": max(cvss_scores) if cvss_scores else 0.0,
                "min": min(cvss_scores) if cvss_scores else 0.0
            }
        }
    
    def _generate_executive_summary(
        self,
        all_issues: List[SecurityIssue],
        scan_summary: Dict[str, Any]
    ) -> str:
        """Generate executive summary text."""
        critical_count = scan_summary["severity_breakdown"]["critical"]
        high_count = scan_summary["severity_breakdown"]["high"]
        total_count = scan_summary["total_issues"]
        
        summary = f"Security scan identified {total_count} potential vulnerabilities. "
        
        if critical_count > 0:
            summary += f"{critical_count} critical severity issues require immediate attention. "
        
        if high_count > 0:
            summary += f"{high_count} high severity issues should be addressed promptly. "
        
        if critical_count == 0 and high_count == 0:
            summary += "No critical or high severity issues were found. "
        
        # Add most common vulnerability type
        vuln_types = scan_summary["vulnerability_types"]
        if vuln_types:
            most_common = max(vuln_types.items(), key=lambda x: x[1])
            summary += f"The most common vulnerability type is {most_common[0]} ({most_common[1]} instances). "
        
        summary += "Detailed findings and remediation recommendations are provided in this report."
        
        return summary
    
    def _generate_risk_assessment(self, all_issues: List[SecurityIssue]) -> Dict[str, Any]:
        """Generate risk assessment."""
        # Calculate overall risk score (0-100)
        risk_scores = []
        for issue in all_issues:
            if issue.classification:
                # Use CVSS score as basis (0-10 scale)
                score = issue.classification.cvss_score.base_score * 10
                risk_scores.append(score)
        
        overall_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        # Determine risk level
        if overall_risk >= 70:
            risk_level = "Critical"
        elif overall_risk >= 50:
            risk_level = "High"
        elif overall_risk >= 30:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Count exploitable issues
        exploitable_count = sum(
            1 for issue in all_issues
            if issue.classification and issue.classification.exploitability in [
                Exploitability.HIGH, Exploitability.CRITICAL
            ]
        )
        
        return {
            "overall_risk_score": round(overall_risk, 1),
            "risk_level": risk_level,
            "exploitable_vulnerabilities": exploitable_count,
            "total_vulnerabilities": len(all_issues),
            "recommendation": self._get_risk_recommendation(risk_level)
        }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level."""
        recommendations = {
            "Critical": "Immediate action required. Halt deployment and address critical issues.",
            "High": "Urgent attention needed. Address high-priority issues before deployment.",
            "Medium": "Schedule remediation. Address issues in next development cycle.",
            "Low": "Monitor and address during regular maintenance."
        }
        return recommendations.get(risk_level, "Review findings and take appropriate action.")
    
    def export_report(
        self,
        report: SecurityReport,
        output_path: str,
        format: ReportFormat = ReportFormat.JSON
    ) -> None:
        """Export report to file in specified format.
        
        Args:
            report: Security report to export
            output_path: Output file path
            format: Report format
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format == ReportFormat.JSON:
            self._export_json(report, output_file)
        elif format == ReportFormat.HTML:
            self._export_html(report, output_file)
        elif format == ReportFormat.MARKDOWN:
            self._export_markdown(report, output_file)
        elif format == ReportFormat.TEXT:
            self._export_text(report, output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, report: SecurityReport, output_file: Path) -> None:
        """Export report as JSON."""
        with open(output_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
    
    def _export_html(self, report: SecurityReport, output_file: Path) -> None:
        """Export report as HTML."""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Security Report - {html.escape(report.report_id)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
        .critical {{ color: #d32f2f; font-weight: bold; }}
        .high {{ color: #f57c00; font-weight: bold; }}
        .medium {{ color: #fbc02d; font-weight: bold; }}
        .low {{ color: #388e3c; font-weight: bold; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .finding {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .code {{ background: #f5f5f5; padding: 10px; border-radius: 3px; font-family: monospace; white-space: pre-wrap; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>Security Report: {html.escape(report.report_id)}</h1>
    <p><strong>Generated:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <p>{html.escape(report.executive_summary)}</p>
        
        <h3>Risk Assessment</h3>
        <p><strong>Overall Risk Level:</strong> <span class="{report.risk_assessment['risk_level'].lower()}">{report.risk_assessment['risk_level']}</span></p>
        <p><strong>Risk Score:</strong> {report.risk_assessment['overall_risk_score']}/100</p>
        <p><strong>Recommendation:</strong> {html.escape(report.risk_assessment['recommendation'])}</p>
    </div>
    
    <h2>Scan Summary</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Total Files Scanned</td>
            <td>{report.scan_summary['total_files_scanned']}</td>
        </tr>
        <tr>
            <td>Total Issues</td>
            <td>{report.scan_summary['total_issues']}</td>
        </tr>
        <tr>
            <td>Critical Severity</td>
            <td class="critical">{report.scan_summary['severity_breakdown']['critical']}</td>
        </tr>
        <tr>
            <td>High Severity</td>
            <td class="high">{report.scan_summary['severity_breakdown']['high']}</td>
        </tr>
        <tr>
            <td>Medium Severity</td>
            <td class="medium">{report.scan_summary['severity_breakdown']['medium']}</td>
        </tr>
        <tr>
            <td>Low Severity</td>
            <td class="low">{report.scan_summary['severity_breakdown']['low']}</td>
        </tr>
    </table>
    
    <h2>Findings</h2>
"""
        
        for i, finding in enumerate(report.findings, 1):
            severity_class = finding.severity.value
            html_content += f"""
    <div class="finding">
        <h3>Finding #{i}: {html.escape(finding.vulnerability_type.value)}</h3>
        <p><strong>Severity:</strong> <span class="{severity_class}">{finding.severity.value.upper()}</span></p>
        <p><strong>File:</strong> {html.escape(finding.file_path)}:{finding.line_number}</p>
        <p><strong>Description:</strong> {html.escape(finding.description)}</p>
        {f'<p><strong>CWE:</strong> {html.escape(finding.cwe_id)}</p>' if finding.cwe_id else ''}
        {f'<div class="code"><strong>Code Snippet:</strong><br>{html.escape(finding.code_snippet)}</div>' if finding.code_snippet else ''}
        <p><strong>Recommendation:</strong> {html.escape(finding.recommendation)}</p>
    </div>
"""
        
        if report.remediation_recommendations:
            html_content += "<h2>Remediation Recommendations</h2>"
            for rec in report.remediation_recommendations:
                html_content += f"""
    <div class="finding">
        <h3>{html.escape(rec.vulnerability_id)}</h3>
        <p><strong>Priority:</strong> <span class="{rec.priority.lower()}">{rec.priority}</span></p>
        <p><strong>Short-term Fix:</strong> {html.escape(rec.short_term_fix)}</p>
        <p><strong>Long-term Fix:</strong> {html.escape(rec.long_term_fix)}</p>
        {f'<div class="code">{html.escape(rec.code_example)}</div>' if rec.code_example else ''}
        <p><strong>Estimated Effort:</strong> {html.escape(rec.estimated_effort)}</p>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html_content)
    
    def _export_markdown(self, report: SecurityReport, output_file: Path) -> None:
        """Export report as Markdown."""
        md_content = f"""# Security Report: {report.report_id}

**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

{report.executive_summary}

### Risk Assessment

- **Overall Risk Level:** {report.risk_assessment['risk_level']}
- **Risk Score:** {report.risk_assessment['overall_risk_score']}/100
- **Exploitable Vulnerabilities:** {report.risk_assessment['exploitable_vulnerabilities']}
- **Recommendation:** {report.risk_assessment['recommendation']}

## Scan Summary

| Metric | Value |
|--------|-------|
| Total Files Scanned | {report.scan_summary['total_files_scanned']} |
| Total Issues | {report.scan_summary['total_issues']} |
| Critical Severity | {report.scan_summary['severity_breakdown']['critical']} |
| High Severity | {report.scan_summary['severity_breakdown']['high']} |
| Medium Severity | {report.scan_summary['severity_breakdown']['medium']} |
| Low Severity | {report.scan_summary['severity_breakdown']['low']} |

## Findings

"""
        
        for i, finding in enumerate(report.findings, 1):
            md_content += f"""### Finding #{i}: {finding.vulnerability_type.value}

- **Severity:** {finding.severity.value.upper()}
- **File:** {finding.file_path}:{finding.line_number}
- **Description:** {finding.description}
"""
            if finding.cwe_id:
                md_content += f"- **CWE:** {finding.cwe_id}\n"
            
            if finding.code_snippet:
                md_content += f"\n**Code Snippet:**\n```\n{finding.code_snippet}\n```\n"
            
            md_content += f"\n**Recommendation:** {finding.recommendation}\n\n"
        
        if report.remediation_recommendations:
            md_content += "## Remediation Recommendations\n\n"
            for rec in report.remediation_recommendations:
                md_content += f"""### {rec.vulnerability_id}

- **Priority:** {rec.priority}
- **Short-term Fix:** {rec.short_term_fix}
- **Long-term Fix:** {rec.long_term_fix}
- **Estimated Effort:** {rec.estimated_effort}

"""
                if rec.code_example:
                    md_content += f"**Code Example:**\n```c\n{rec.code_example}\n```\n\n"
        
        with open(output_file, 'w') as f:
            f.write(md_content)
    
    def _export_text(self, report: SecurityReport, output_file: Path) -> None:
        """Export report as plain text."""
        text_content = f"""SECURITY REPORT: {report.report_id}
{'=' * 80}

Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
{'-' * 80}
{report.executive_summary}

RISK ASSESSMENT
{'-' * 80}
Overall Risk Level: {report.risk_assessment['risk_level']}
Risk Score: {report.risk_assessment['overall_risk_score']}/100
Exploitable Vulnerabilities: {report.risk_assessment['exploitable_vulnerabilities']}
Recommendation: {report.risk_assessment['recommendation']}

SCAN SUMMARY
{'-' * 80}
Total Files Scanned: {report.scan_summary['total_files_scanned']}
Total Issues: {report.scan_summary['total_issues']}
Critical Severity: {report.scan_summary['severity_breakdown']['critical']}
High Severity: {report.scan_summary['severity_breakdown']['high']}
Medium Severity: {report.scan_summary['severity_breakdown']['medium']}
Low Severity: {report.scan_summary['severity_breakdown']['low']}

FINDINGS
{'-' * 80}
"""
        
        for i, finding in enumerate(report.findings, 1):
            text_content += f"""
Finding #{i}: {finding.vulnerability_type.value}
Severity: {finding.severity.value.upper()}
File: {finding.file_path}:{finding.line_number}
Description: {finding.description}
"""
            if finding.cwe_id:
                text_content += f"CWE: {finding.cwe_id}\n"
            
            if finding.code_snippet:
                text_content += f"\nCode Snippet:\n{finding.code_snippet}\n"
            
            text_content += f"\nRecommendation: {finding.recommendation}\n"
            text_content += "-" * 80 + "\n"
        
        with open(output_file, 'w') as f:
            f.write(text_content)
