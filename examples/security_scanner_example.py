#!/usr/bin/env python3
"""Example demonstrating the security scanner functionality."""

import tempfile
from pathlib import Path
from analysis.security_scanner import SecurityScanner, VulnerabilityType, Severity


def example_single_file_scan():
    """Example: Scan a single file for vulnerabilities."""
    print("=" * 70)
    print("Example 1: Single File Scan")
    print("=" * 70)
    
    # Sample vulnerable code
    vulnerable_code = """
#include <linux/kernel.h>
#include <linux/slab.h>

void process_user_input(char *user_data) {
    char buffer[64];
    strcpy(buffer, user_data);  // Buffer overflow vulnerability
    printk(buffer);  // Format string vulnerability
}

void handle_data(struct data *ptr) {
    kfree(ptr);
    if (ptr->next != NULL) {  // Use-after-free vulnerability
        handle_data(ptr->next);
    }
}

int calculate_total(int count, int size) {
    int total = count * size;  // Integer overflow vulnerability
    return total;
}

void init_device(void) {
    struct device *dev = kmalloc(sizeof(*dev), GFP_KERNEL);
    dev->id = 42;  // Null pointer dereference
}
"""
    
    # Create scanner
    scanner = SecurityScanner()
    
    # Write code to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(vulnerable_code)
        temp_file = f.name
    
    try:
        # Scan the file
        print(f"\nScanning file: {temp_file}")
        issues = scanner.scan_file(temp_file)
        
        print(f"\nFound {len(issues)} security issues:\n")
        
        # Display issues grouped by severity
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            severity_issues = [i for i in issues if i.severity == severity]
            if severity_issues:
                print(f"\n{severity.value.upper()} Severity ({len(severity_issues)} issues):")
                print("-" * 70)
                for issue in severity_issues:
                    print(f"  Line {issue.line_number}: {issue.vulnerability_type.value}")
                    print(f"    Description: {issue.description}")
                    print(f"    Recommendation: {issue.recommendation}")
                    if issue.cwe_id:
                        print(f"    CWE: {issue.cwe_id}")
                    print()
    
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)


def example_directory_scan():
    """Example: Scan a directory of files."""
    print("\n" + "=" * 70)
    print("Example 2: Directory Scan")
    print("=" * 70)
    
    # Create temporary directory with multiple files
    import os
    temp_dir = tempfile.mkdtemp()
    
    # File 1: Buffer overflow
    file1_code = """
void copy_string(char *dest, char *src) {
    strcpy(dest, src);
}
"""
    
    # File 2: Use-after-free
    file2_code = """
void free_and_use(void *ptr) {
    kfree(ptr);
    memset(ptr, 0, 100);
}
"""
    
    # File 3: Integer overflow
    file3_code = """
int multiply(int a, int b) {
    int result = a * b;
    return result;
}
"""
    
    try:
        # Write files
        Path(temp_dir, "file1.c").write_text(file1_code)
        Path(temp_dir, "file2.c").write_text(file2_code)
        Path(temp_dir, "file3.c").write_text(file3_code)
        
        # Create scanner
        scanner = SecurityScanner()
        
        # Scan directory
        print(f"\nScanning directory: {temp_dir}")
        results = scanner.scan_directory(temp_dir, extensions=['.c'])
        
        print(f"\nScanned {len(results)} files with issues:\n")
        
        for file_path, issues in results.items():
            print(f"File: {Path(file_path).name}")
            print(f"  Issues: {len(issues)}")
            for issue in issues:
                print(f"    - {issue.vulnerability_type.value} (Line {issue.line_number})")
            print()
    
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


def example_report_generation():
    """Example: Generate a comprehensive security report."""
    print("\n" + "=" * 70)
    print("Example 3: Security Report Generation")
    print("=" * 70)
    
    # Sample code with multiple vulnerabilities
    code = """
void vulnerable_function(char *input) {
    char buf[64];
    strcpy(buf, input);
    
    struct data *ptr = kmalloc(sizeof(*ptr), GFP_KERNEL);
    kfree(ptr);
    ptr->value = 10;
    
    int x = input[0] + input[1];
}
"""
    
    scanner = SecurityScanner()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Scan and generate report
        issues = scanner.scan_file(temp_file)
        scan_results = {temp_file: issues}
        report = scanner.generate_report(scan_results)
        
        print("\nSecurity Scan Report")
        print("-" * 70)
        print(f"Scan Timestamp: {report['scan_timestamp']}")
        print(f"Total Files Scanned: {report['total_files_scanned']}")
        print(f"Total Issues Found: {report['total_issues']}")
        
        print("\nSeverity Breakdown:")
        for severity, count in report['severity_breakdown'].items():
            print(f"  {severity.capitalize()}: {count}")
        
        print("\nVulnerability Types:")
        for vuln_type, count in report['vulnerability_types'].items():
            print(f"  {vuln_type}: {count}")
        
        # Get statistics
        stats = scanner.get_statistics()
        print("\nScanner Statistics:")
        print(f"  Total Scans: {stats['total_scans']}")
        print(f"  Total Files Scanned: {stats['total_files_scanned']}")
        print(f"  Total Issues Found: {stats['total_issues_found']}")
    
    finally:
        Path(temp_file).unlink(missing_ok=True)


def example_vulnerability_types():
    """Example: Demonstrate detection of different vulnerability types."""
    print("\n" + "=" * 70)
    print("Example 4: Vulnerability Type Detection")
    print("=" * 70)
    
    vulnerability_examples = {
        "Buffer Overflow": """
void test() {
    char buf[10];
    gets(buf);
}
""",
        "Use-After-Free": """
void test(void *p) {
    kfree(p);
    memset(p, 0, 10);
}
""",
        "Integer Overflow": """
int test(int a, int b) {
    return a + b;
}
""",
        "Null Pointer Dereference": """
void test() {
    int *p = kmalloc(sizeof(int), GFP_KERNEL);
    *p = 42;
}
""",
        "Format String": """
void test(char *msg) {
    printk(msg);
}
"""
    }
    
    scanner = SecurityScanner()
    
    for vuln_name, code in vulnerability_examples.items():
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            issues = scanner.scan_file(temp_file)
            if issues:
                print(f"\n{vuln_name}:")
                print(f"  Detected: ✓")
                print(f"  Severity: {issues[0].severity.value}")
                print(f"  Description: {issues[0].description}")
            else:
                print(f"\n{vuln_name}:")
                print(f"  Detected: ✗")
        finally:
            Path(temp_file).unlink(missing_ok=True)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Security Scanner Examples")
    print("=" * 70)
    
    # Run examples
    example_single_file_scan()
    example_directory_scan()
    example_report_generation()
    example_vulnerability_types()
    
    print("\n" + "=" * 70)
    print("Examples Complete")
    print("=" * 70)
