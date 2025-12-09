"""Security scanner with static analysis for vulnerability detection.

This module integrates Coccinelle for pattern-based static analysis to detect
common vulnerability patterns in kernel code including buffer overflows,
use-after-free, and integer overflows.
"""

import subprocess
import tempfile
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class VulnerabilityType(str, Enum):
    """Types of vulnerabilities that can be detected."""
    BUFFER_OVERFLOW = "buffer_overflow"
    USE_AFTER_FREE = "use_after_free"
    INTEGER_OVERFLOW = "integer_overflow"
    NULL_POINTER_DEREFERENCE = "null_pointer_dereference"
    MEMORY_LEAK = "memory_leak"
    RACE_CONDITION = "race_condition"
    FORMAT_STRING = "format_string"
    UNINITIALIZED_VARIABLE = "uninitialized_variable"


class Severity(str, Enum):
    """Severity levels for vulnerabilities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityIssue:
    """Represents a detected security vulnerability."""
    vulnerability_type: VulnerabilityType
    severity: Severity
    file_path: str
    line_number: int
    description: str
    code_snippet: Optional[str] = None
    recommendation: str = ""
    cwe_id: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate security issue."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if isinstance(self.vulnerability_type, str):
            self.vulnerability_type = VulnerabilityType(self.vulnerability_type)
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vulnerability_type": self.vulnerability_type.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
            "cwe_id": self.cwe_id,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class VulnerabilityPatternLibrary:
    """Library of vulnerability patterns for detection."""
    
    # Coccinelle patterns for common vulnerabilities
    PATTERNS = {
        VulnerabilityType.BUFFER_OVERFLOW: {
            "name": "Buffer Overflow",
            "cocci_pattern": """
@@
expression E1, E2, E3;
@@
(
- strcpy(E1, E2)
+ strncpy(E1, E2, E3)
|
- strcat(E1, E2)
+ strncat(E1, E2, E3)
|
- sprintf(E1, E2, ...)
+ snprintf(E1, E3, E2, ...)
|
- gets(E1)
+ fgets(E1, E2, E3)
)
""",
            "severity": Severity.CRITICAL,
            "cwe_id": "CWE-120",
            "description": "Unsafe string operation that may cause buffer overflow",
            "recommendation": "Use bounded string functions (strncpy, snprintf, etc.)"
        },
        
        VulnerabilityType.USE_AFTER_FREE: {
            "name": "Use After Free",
            "cocci_pattern": """
@@
expression E;
@@
(
  kfree(E);
  ...
  * E->...
|
  kfree(E);
  ...
  * *E
)
""",
            "severity": Severity.CRITICAL,
            "cwe_id": "CWE-416",
            "description": "Memory accessed after being freed",
            "recommendation": "Set pointer to NULL after freeing and check before use"
        },
        
        VulnerabilityType.INTEGER_OVERFLOW: {
            "name": "Integer Overflow",
            "cocci_pattern": """
@@
expression E1, E2, E3;
@@
(
  * E1 = E2 + E3;
|
  * E1 = E2 * E3;
)
""",
            "severity": Severity.HIGH,
            "cwe_id": "CWE-190",
            "description": "Potential integer overflow in arithmetic operation",
            "recommendation": "Use overflow-safe functions like check_add_overflow()"
        },
        
        VulnerabilityType.NULL_POINTER_DEREFERENCE: {
            "name": "Null Pointer Dereference",
            "cocci_pattern": """
@@
expression E;
@@
(
  E = kmalloc(...);
  ...
  * E->...
|
  E = kzalloc(...);
  ...
  * E->...
)
""",
            "severity": Severity.HIGH,
            "cwe_id": "CWE-476",
            "description": "Pointer dereferenced without null check",
            "recommendation": "Check pointer for NULL before dereferencing"
        },
        
        VulnerabilityType.MEMORY_LEAK: {
            "name": "Memory Leak",
            "cocci_pattern": """
@@
expression E;
@@
(
  E = kmalloc(...);
  ...
  return ...;
|
  E = kzalloc(...);
  ...
  return ...;
)
""",
            "severity": Severity.MEDIUM,
            "cwe_id": "CWE-401",
            "description": "Allocated memory not freed on all paths",
            "recommendation": "Ensure kfree() is called on all exit paths"
        },
        
        VulnerabilityType.FORMAT_STRING: {
            "name": "Format String Vulnerability",
            "cocci_pattern": """
@@
expression E;
@@
(
  * printk(E);
|
  * sprintf(..., E);
|
  * snprintf(..., E);
)
""",
            "severity": Severity.HIGH,
            "cwe_id": "CWE-134",
            "description": "User-controlled format string",
            "recommendation": "Use constant format strings or sanitize input"
        }
    }
    
    @classmethod
    def get_pattern(cls, vuln_type: VulnerabilityType) -> Dict[str, Any]:
        """Get pattern definition for a vulnerability type."""
        return cls.PATTERNS.get(vuln_type, {})
    
    @classmethod
    def get_all_patterns(cls) -> Dict[VulnerabilityType, Dict[str, Any]]:
        """Get all vulnerability patterns."""
        return cls.PATTERNS.copy()


class CoccinelleRunner:
    """Runner for Coccinelle static analysis tool."""
    
    def __init__(self, coccinelle_path: Optional[str] = None):
        """Initialize Coccinelle runner.
        
        Args:
            coccinelle_path: Path to spatch binary (Coccinelle)
        """
        self.coccinelle_path = coccinelle_path or self._find_coccinelle()
    
    def _find_coccinelle(self) -> str:
        """Find Coccinelle binary in system PATH."""
        # Try common locations
        common_paths = [
            "/usr/bin/spatch",
            "/usr/local/bin/spatch",
            "spatch"
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        # Default to spatch in PATH
        return "spatch"
    
    def run_pattern(
        self,
        source_file: str,
        pattern: str,
        timeout: int = 60
    ) -> List[Dict[str, Any]]:
        """Run a Coccinelle pattern on a source file.
        
        Args:
            source_file: Path to source file to analyze
            pattern: Coccinelle pattern (semantic patch)
            timeout: Timeout in seconds
            
        Returns:
            List of matches with file, line, and context
        """
        # Create temporary file for pattern
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.cocci',
            delete=False
        ) as pattern_file:
            pattern_file.write(pattern)
            pattern_path = pattern_file.name
        
        try:
            # Run Coccinelle
            cmd = [
                self.coccinelle_path,
                "--sp-file", pattern_path,
                source_file,
                "--very-quiet"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Parse output
            matches = self._parse_coccinelle_output(result.stdout, source_file)
            return matches
            
        except subprocess.TimeoutExpired:
            return []
        except Exception as e:
            # If Coccinelle fails, fall back to regex-based detection
            return []
        finally:
            # Clean up temporary pattern file
            try:
                Path(pattern_path).unlink()
            except:
                pass
    
    def _parse_coccinelle_output(
        self,
        output: str,
        source_file: str
    ) -> List[Dict[str, Any]]:
        """Parse Coccinelle output to extract matches.
        
        Args:
            output: Coccinelle stdout
            source_file: Source file that was analyzed
            
        Returns:
            List of match dictionaries
        """
        matches = []
        
        # Coccinelle output format: file:line:column: message
        pattern = re.compile(r'([^:]+):(\d+):(\d+):\s*(.+)')
        
        for line in output.split('\n'):
            match = pattern.match(line.strip())
            if match:
                file_path, line_num, column, message = match.groups()
                matches.append({
                    "file": file_path,
                    "line": int(line_num),
                    "column": int(column),
                    "message": message
                })
        
        return matches


class RegexPatternDetector:
    """Fallback regex-based pattern detector when Coccinelle is unavailable."""
    
    # Regex patterns for common vulnerabilities
    REGEX_PATTERNS = {
        VulnerabilityType.BUFFER_OVERFLOW: [
            (r'\bstrcpy\s*\(', "Buffer overflow: unsafe strcpy function"),
            (r'\bstrcat\s*\(', "Buffer overflow: unsafe strcat function"),
            (r'\bsprintf\s*\(', "Buffer overflow: unsafe sprintf function"),
            (r'\bgets\s*\(', "Buffer overflow: unsafe gets function"),
        ],
        VulnerabilityType.FORMAT_STRING: [
            (r'\bprintk\s*\(\s*[a-zA-Z_]', "Format string vulnerability in printk"),
            (r'\bsprintf\s*\([^,]+,\s*[a-zA-Z_]', "Format string vulnerability in sprintf"),
        ],
        VulnerabilityType.NULL_POINTER_DEREFERENCE: [
            (r'(kmalloc|kzalloc)\s*\([^)]+\)\s*;\s*\n?\s*\w+\s*->', "Null pointer dereference without check"),
        ],
        VulnerabilityType.USE_AFTER_FREE: [
            (r'kfree\s*\([^)]+\)\s*;\s*\n?\s*[^}]*\w+\s*->', "Use-after-free: pointer accessed after kfree"),
        ],
        VulnerabilityType.INTEGER_OVERFLOW: [
            (r'\b\w+\s*=\s*\w+\s*\+\s*\w+\s*;', "Integer overflow in addition"),
            (r'\b\w+\s*=\s*\w+\s*\*\s*\w+\s*;', "Integer overflow in multiplication"),
        ]
    }
    
    def detect_patterns(
        self,
        source_code: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Detect vulnerability patterns using regex.
        
        Args:
            source_code: Source code content
            file_path: Path to source file
            
        Returns:
            List of detected issues
        """
        issues = []
        lines = source_code.split('\n')
        
        # First, try line-by-line detection
        for vuln_type, patterns in self.REGEX_PATTERNS.items():
            for pattern, description in patterns:
                regex = re.compile(pattern)
                
                for line_num, line in enumerate(lines, start=1):
                    if regex.search(line):
                        issues.append({
                            "vulnerability_type": vuln_type,
                            "file": file_path,
                            "line": line_num,
                            "description": description,
                            "code_snippet": line.strip()
                        })
        
        # Also try multi-line detection for patterns that span lines
        # Normalize whitespace for multi-line patterns
        normalized_code = re.sub(r'\s+', ' ', source_code)
        
        # Use-after-free detection (kfree followed by pointer access)
        # Pattern 1: kfree(ptr); ... ptr->...
        uaf_pattern1 = r'kfree\s*\(([^)]+)\)\s*;[^}]*?\1\s*->'
        for match in re.finditer(uaf_pattern1, normalized_code):
            # Find line number
            pos = match.start()
            line_num = source_code[:pos].count('\n') + 1
            issues.append({
                "vulnerability_type": VulnerabilityType.USE_AFTER_FREE,
                "file": file_path,
                "line": line_num,
                "description": "Use-after-free: pointer accessed after kfree",
                "code_snippet": match.group(0)[:50]
            })
        
        # Pattern 2: kfree(ptr); ... function(ptr, ...)
        uaf_pattern2 = r'kfree\s*\(([^)]+)\)\s*;[^}]*?\w+\s*\(\s*\1\s*,'
        for match in re.finditer(uaf_pattern2, normalized_code):
            # Find line number
            pos = match.start()
            line_num = source_code[:pos].count('\n') + 1
            issues.append({
                "vulnerability_type": VulnerabilityType.USE_AFTER_FREE,
                "file": file_path,
                "line": line_num,
                "description": "Use-after-free: pointer accessed after kfree",
                "code_snippet": match.group(0)[:50]
            })
        
        # Null pointer dereference (kmalloc/kzalloc followed by dereference)
        # Pattern 1: ptr = kmalloc(...); ... ptr->...
        null_deref_pattern1 = r'(\w+)\s*=\s*(kmalloc|kzalloc)[^;]*;[^}]*\1\s*->'
        for match in re.finditer(null_deref_pattern1, normalized_code):
            # Find line number
            pos = match.start()
            line_num = source_code[:pos].count('\n') + 1
            issues.append({
                "vulnerability_type": VulnerabilityType.NULL_POINTER_DEREFERENCE,
                "file": file_path,
                "line": line_num,
                "description": "Null pointer dereference without check",
                "code_snippet": match.group(0)[:50]
            })
        
        # Pattern 2: ptr = kmalloc(...); ... *ptr
        null_deref_pattern2 = r'(\w+)\s*=\s*(kmalloc|kzalloc)[^;]*;[^}]*\*\s*\1'
        for match in re.finditer(null_deref_pattern2, normalized_code):
            # Find line number
            pos = match.start()
            line_num = source_code[:pos].count('\n') + 1
            issues.append({
                "vulnerability_type": VulnerabilityType.NULL_POINTER_DEREFERENCE,
                "file": file_path,
                "line": line_num,
                "description": "Null pointer dereference without check",
                "code_snippet": match.group(0)[:50]
            })
        
        return issues


class StaticAnalysisRunner:
    """Main static analysis runner that coordinates pattern detection."""
    
    def __init__(self, coccinelle_path: Optional[str] = None):
        """Initialize static analysis runner.
        
        Args:
            coccinelle_path: Path to Coccinelle binary
        """
        self.coccinelle_runner = CoccinelleRunner(coccinelle_path)
        self.regex_detector = RegexPatternDetector()
        self.pattern_library = VulnerabilityPatternLibrary()
    
    def analyze_file(
        self,
        file_path: str,
        use_coccinelle: bool = True
    ) -> List[SecurityIssue]:
        """Analyze a source file for vulnerabilities.
        
        Args:
            file_path: Path to source file
            use_coccinelle: Whether to use Coccinelle (falls back to regex if False)
            
        Returns:
            List of detected security issues
        """
        issues = []
        
        # Read source file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
        except Exception:
            return issues
        
        if use_coccinelle:
            # Try Coccinelle-based detection
            issues.extend(self._analyze_with_coccinelle(file_path, source_code))
        
        # Always run regex-based detection as supplement
        issues.extend(self._analyze_with_regex(file_path, source_code))
        
        return issues
    
    def _analyze_with_coccinelle(
        self,
        file_path: str,
        source_code: str
    ) -> List[SecurityIssue]:
        """Analyze using Coccinelle patterns.
        
        Args:
            file_path: Path to source file
            source_code: Source code content
            
        Returns:
            List of security issues
        """
        issues = []
        
        for vuln_type, pattern_def in self.pattern_library.get_all_patterns().items():
            try:
                matches = self.coccinelle_runner.run_pattern(
                    file_path,
                    pattern_def["cocci_pattern"]
                )
                
                for match in matches:
                    issue = SecurityIssue(
                        vulnerability_type=vuln_type,
                        severity=pattern_def["severity"],
                        file_path=match["file"],
                        line_number=match["line"],
                        description=pattern_def["description"],
                        code_snippet=self._extract_code_snippet(
                            source_code,
                            match["line"]
                        ),
                        recommendation=pattern_def["recommendation"],
                        cwe_id=pattern_def["cwe_id"],
                        confidence=0.9,  # High confidence for Coccinelle matches
                        metadata={"tool": "coccinelle"}
                    )
                    issues.append(issue)
            except Exception:
                # Continue with other patterns if one fails
                continue
        
        return issues
    
    def _analyze_with_regex(
        self,
        file_path: str,
        source_code: str
    ) -> List[SecurityIssue]:
        """Analyze using regex patterns.
        
        Args:
            file_path: Path to source file
            source_code: Source code content
            
        Returns:
            List of security issues
        """
        issues = []
        
        detected = self.regex_detector.detect_patterns(source_code, file_path)
        
        for detection in detected:
            pattern_def = self.pattern_library.get_pattern(
                detection["vulnerability_type"]
            )
            
            issue = SecurityIssue(
                vulnerability_type=detection["vulnerability_type"],
                severity=pattern_def.get("severity", Severity.MEDIUM),
                file_path=detection["file"],
                line_number=detection["line"],
                description=detection["description"],
                code_snippet=detection.get("code_snippet"),
                recommendation=pattern_def.get("recommendation", "Review code for security issues"),
                cwe_id=pattern_def.get("cwe_id"),
                confidence=0.6,  # Lower confidence for regex matches
                metadata={"tool": "regex"}
            )
            issues.append(issue)
        
        return issues
    
    def _extract_code_snippet(
        self,
        source_code: str,
        line_number: int,
        context_lines: int = 2
    ) -> str:
        """Extract code snippet around a line.
        
        Args:
            source_code: Full source code
            line_number: Line number to extract
            context_lines: Number of context lines before/after
            
        Returns:
            Code snippet with context
        """
        lines = source_code.split('\n')
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            snippet_lines.append(f"{prefix}{lines[i]}")
        
        return '\n'.join(snippet_lines)


class SecurityScanner:
    """Main security scanner interface."""
    
    def __init__(self, coccinelle_path: Optional[str] = None):
        """Initialize security scanner.
        
        Args:
            coccinelle_path: Path to Coccinelle binary
        """
        self.static_analyzer = StaticAnalysisRunner(coccinelle_path)
        self.scan_history: List[Dict[str, Any]] = []
    
    def scan_file(self, file_path: str) -> List[SecurityIssue]:
        """Scan a single file for vulnerabilities.
        
        Args:
            file_path: Path to source file
            
        Returns:
            List of detected security issues
        """
        issues = self.static_analyzer.analyze_file(file_path)
        
        # Record scan
        self.scan_history.append({
            "file": file_path,
            "timestamp": datetime.now(),
            "issues_found": len(issues)
        })
        
        return issues
    
    def scan_directory(
        self,
        directory: str,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, List[SecurityIssue]]:
        """Scan all files in a directory.
        
        Args:
            directory: Directory path to scan
            extensions: File extensions to scan (default: ['.c', '.h'])
            
        Returns:
            Dictionary mapping file paths to lists of issues
        """
        if extensions is None:
            extensions = ['.c', '.h']
        
        results = {}
        dir_path = Path(directory)
        
        for ext in extensions:
            for file_path in dir_path.rglob(f'*{ext}'):
                if file_path.is_file():
                    issues = self.scan_file(str(file_path))
                    if issues:
                        results[str(file_path)] = issues
        
        return results
    
    def generate_report(
        self,
        scan_results: Dict[str, List[SecurityIssue]]
    ) -> Dict[str, Any]:
        """Generate a security scan report.
        
        Args:
            scan_results: Dictionary of file paths to issues
            
        Returns:
            Report dictionary with statistics and findings
        """
        total_issues = sum(len(issues) for issues in scan_results.values())
        
        # Count by severity
        severity_counts = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 0,
            Severity.MEDIUM: 0,
            Severity.LOW: 0
        }
        
        # Count by vulnerability type
        vuln_type_counts = {}
        
        for issues in scan_results.values():
            for issue in issues:
                severity_counts[issue.severity] += 1
                vuln_type = issue.vulnerability_type.value
                vuln_type_counts[vuln_type] = vuln_type_counts.get(vuln_type, 0) + 1
        
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_files_scanned": len(scan_results),
            "total_issues": total_issues,
            "severity_breakdown": {
                "critical": severity_counts[Severity.CRITICAL],
                "high": severity_counts[Severity.HIGH],
                "medium": severity_counts[Severity.MEDIUM],
                "low": severity_counts[Severity.LOW]
            },
            "vulnerability_types": vuln_type_counts,
            "files_with_issues": {
                file_path: [issue.to_dict() for issue in issues]
                for file_path, issues in scan_results.items()
            }
        }
        
        return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scanner statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_scans": len(self.scan_history),
            "total_files_scanned": len(set(scan["file"] for scan in self.scan_history)),
            "total_issues_found": sum(scan["issues_found"] for scan in self.scan_history),
            "scan_history": self.scan_history[-10:]  # Last 10 scans
        }
