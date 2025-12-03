"""Code analysis and diff parsing for detecting changes and impact."""

import re
import ast
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from ai_generator.models import CodeAnalysis, Function, RiskLevel, TestType


@dataclass
class FileDiff:
    """Represents changes to a single file."""
    file_path: str
    added_lines: List[Tuple[int, str]]  # (line_number, content)
    removed_lines: List[Tuple[int, str]]
    is_new_file: bool = False
    is_deleted_file: bool = False


class DiffParser:
    """Parser for Git diff output."""
    
    def parse_diff(self, diff_text: str) -> List[FileDiff]:
        """Parse a Git diff into structured file changes.
        
        Args:
            diff_text: Raw Git diff output
            
        Returns:
            List of FileDiff objects representing changes
        """
        if not diff_text or not diff_text.strip():
            return []
        
        file_diffs = []
        current_file = None
        current_added = []
        current_removed = []
        current_line_num = 0
        is_new_file = False
        is_deleted_file = False
        
        lines = diff_text.split('\n')
        
        for line in lines:
            # New file marker
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file:
                    file_diffs.append(FileDiff(
                        file_path=current_file,
                        added_lines=current_added.copy(),
                        removed_lines=current_removed.copy(),
                        is_new_file=is_new_file,
                        is_deleted_file=is_deleted_file
                    ))
                
                # Extract file path
                match = re.search(r'b/(.+)$', line)
                current_file = match.group(1) if match else None
                current_added = []
                current_removed = []
                is_new_file = False
                is_deleted_file = False
                
            elif line.startswith('new file mode'):
                is_new_file = True
                
            elif line.startswith('deleted file mode'):
                is_deleted_file = True
                
            elif line.startswith('@@'):
                # Extract line number from hunk header
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line_num = int(match.group(1))
                    
            elif line.startswith('+') and not line.startswith('+++'):
                # Added line
                content = line[1:]  # Remove '+' prefix
                current_added.append((current_line_num, content))
                current_line_num += 1
                
            elif line.startswith('-') and not line.startswith('---'):
                # Removed line
                content = line[1:]  # Remove '-' prefix
                current_removed.append((current_line_num, content))
                
            elif not line.startswith('\\'):
                # Context line (unchanged)
                current_line_num += 1
        
        # Save last file
        if current_file:
            file_diffs.append(FileDiff(
                file_path=current_file,
                added_lines=current_added,
                removed_lines=current_removed,
                is_new_file=is_new_file,
                is_deleted_file=is_deleted_file
            ))
        
        return file_diffs
    
    def extract_changed_functions(self, file_diff: FileDiff, source_code: Optional[str] = None) -> List[Function]:
        """Extract functions that were modified in a file.
        
        Args:
            file_diff: FileDiff object with changes
            source_code: Optional source code content for AST analysis
            
        Returns:
            List of Function objects that were changed
        """
        functions = []
        
        # If we have source code, use AST analysis
        if source_code and file_diff.file_path.endswith('.py'):
            try:
                tree = ast.parse(source_code)
                changed_lines = {line_num for line_num, _ in file_diff.added_lines + file_diff.removed_lines}
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function overlaps with changed lines
                        func_start = node.lineno
                        func_end = getattr(node, 'end_lineno', func_start)
                        
                        if any(func_start <= line <= func_end for line in changed_lines):
                            # Extract function signature
                            args = [arg.arg for arg in node.args.args]
                            signature = f"{node.name}({', '.join(args)})"
                            
                            functions.append(Function(
                                name=node.name,
                                file_path=file_diff.file_path,
                                line_number=func_start,
                                signature=signature
                            ))
            except SyntaxError:
                # If parsing fails, fall back to heuristic approach
                pass
        
        # Heuristic approach for C files or when AST fails
        if not functions and file_diff.file_path.endswith(('.c', '.h')):
            # Look for function definitions in added/removed lines
            func_pattern = re.compile(r'^[\w\s\*]+\s+(\w+)\s*\([^)]*\)\s*\{?')
            
            for line_num, content in file_diff.added_lines + file_diff.removed_lines:
                match = func_pattern.match(content.strip())
                if match:
                    func_name = match.group(1)
                    # Avoid common false positives
                    if func_name not in ['if', 'while', 'for', 'switch', 'return']:
                        functions.append(Function(
                            name=func_name,
                            file_path=file_diff.file_path,
                            line_number=line_num,
                            signature=content.strip()
                        ))
        
        return functions


class ASTAnalyzer:
    """Analyzer for identifying affected subsystems using AST and heuristics."""
    
    # Kernel subsystem patterns based on file paths
    SUBSYSTEM_PATTERNS = {
        'fs/': 'filesystem',
        'net/': 'networking',
        'drivers/': 'drivers',
        'mm/': 'memory_management',
        'kernel/': 'core_kernel',
        'arch/': 'architecture',
        'security/': 'security',
        'crypto/': 'cryptography',
        'block/': 'block_layer',
        'sound/': 'sound',
        'ipc/': 'ipc',
        'init/': 'initialization',
        'lib/': 'library',
        'scripts/': 'build_scripts',
        'Documentation/': 'documentation',
        'tools/': 'tools',
    }
    
    def identify_subsystems(self, file_diffs: List[FileDiff]) -> List[str]:
        """Identify affected kernel subsystems from file changes.
        
        Args:
            file_diffs: List of FileDiff objects
            
        Returns:
            List of affected subsystem names
        """
        subsystems = set()
        
        for file_diff in file_diffs:
            file_path = file_diff.file_path
            
            # Match against known subsystem patterns
            for pattern, subsystem in self.SUBSYSTEM_PATTERNS.items():
                if file_path.startswith(pattern):
                    subsystems.add(subsystem)
                    break
            else:
                # If no pattern matches, use top-level directory
                parts = file_path.split('/')
                if len(parts) > 1:
                    subsystems.add(parts[0])
                else:
                    subsystems.add('unknown')
        
        return sorted(list(subsystems))
    
    def calculate_impact_score(self, file_diffs: List[FileDiff], functions: List[Function]) -> float:
        """Calculate impact score for code changes.
        
        Impact is based on:
        - Number of files changed
        - Number of lines changed
        - Number of functions changed
        - Whether changes are in critical subsystems
        
        Args:
            file_diffs: List of FileDiff objects
            functions: List of changed Function objects
            
        Returns:
            Impact score between 0.0 and 1.0
        """
        if not file_diffs:
            return 0.0
        
        # Count changes
        num_files = len(file_diffs)
        total_lines_changed = sum(
            len(fd.added_lines) + len(fd.removed_lines) 
            for fd in file_diffs
        )
        num_functions = len(functions)
        
        # Check for critical subsystems
        subsystems = self.identify_subsystems(file_diffs)
        critical_subsystems = {'core_kernel', 'memory_management', 'security', 'networking'}
        has_critical = any(s in critical_subsystems for s in subsystems)
        
        # Calculate base score (0-0.6)
        file_score = min(num_files / 20.0, 0.2)  # Max 0.2 for files
        line_score = min(total_lines_changed / 500.0, 0.2)  # Max 0.2 for lines
        func_score = min(num_functions / 10.0, 0.2)  # Max 0.2 for functions
        
        base_score = file_score + line_score + func_score
        
        # Add critical subsystem bonus (up to 0.4)
        if has_critical:
            base_score += 0.4
        
        return min(base_score, 1.0)
    
    def determine_risk_level(self, impact_score: float, subsystems: List[str]) -> RiskLevel:
        """Determine risk level based on impact score and subsystems.
        
        Args:
            impact_score: Impact score from calculate_impact_score
            subsystems: List of affected subsystems
            
        Returns:
            RiskLevel enum value
        """
        critical_subsystems = {'core_kernel', 'memory_management', 'security'}
        has_critical = any(s in critical_subsystems for s in subsystems)
        
        if impact_score >= 0.8 or (impact_score >= 0.5 and has_critical):
            return RiskLevel.CRITICAL
        elif impact_score >= 0.5 or has_critical:
            return RiskLevel.HIGH
        elif impact_score >= 0.2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def suggest_test_types(self, subsystems: List[str], functions: List[Function]) -> List[TestType]:
        """Suggest appropriate test types based on changes.
        
        Args:
            subsystems: List of affected subsystems
            functions: List of changed functions
            
        Returns:
            List of suggested TestType values
        """
        test_types = set()
        
        # Always include unit tests
        test_types.add(TestType.UNIT)
        
        # Security-sensitive subsystems need security tests
        security_subsystems = {'security', 'cryptography', 'networking'}
        if any(s in security_subsystems for s in subsystems):
            test_types.add(TestType.SECURITY)
            test_types.add(TestType.FUZZ)
        
        # Performance-critical subsystems need performance tests
        perf_subsystems = {'memory_management', 'networking', 'block_layer', 'filesystem'}
        if any(s in perf_subsystems for s in subsystems):
            test_types.add(TestType.PERFORMANCE)
        
        # Multiple subsystems or many functions suggest integration tests
        if len(subsystems) > 1 or len(functions) > 5:
            test_types.add(TestType.INTEGRATION)
        
        return sorted(list(test_types), key=lambda t: t.value)


class CodeAnalyzer:
    """Main code analyzer that coordinates diff parsing and AST analysis."""
    
    def __init__(self):
        self.diff_parser = DiffParser()
        self.ast_analyzer = ASTAnalyzer()
    
    def analyze_diff(self, diff_text: str, source_files: Optional[Dict[str, str]] = None) -> CodeAnalysis:
        """Analyze a Git diff and produce comprehensive code analysis.
        
        Args:
            diff_text: Raw Git diff output
            source_files: Optional dict mapping file paths to source code content
            
        Returns:
            CodeAnalysis object with complete analysis
        """
        # Parse diff
        file_diffs = self.diff_parser.parse_diff(diff_text)
        
        if not file_diffs:
            return CodeAnalysis(
                changed_files=[],
                changed_functions=[],
                affected_subsystems=[],
                impact_score=0.0,
                risk_level=RiskLevel.LOW,
                suggested_test_types=[],
                related_tests=[]
            )
        
        # Extract changed files
        changed_files = [fd.file_path for fd in file_diffs]
        
        # Extract changed functions
        all_functions = []
        for file_diff in file_diffs:
            source_code = source_files.get(file_diff.file_path) if source_files else None
            functions = self.diff_parser.extract_changed_functions(file_diff, source_code)
            
            # Set subsystem for each function
            subsystems = self.ast_analyzer.identify_subsystems([file_diff])
            for func in functions:
                func.subsystem = subsystems[0] if subsystems else 'unknown'
            
            all_functions.extend(functions)
        
        # Identify affected subsystems
        affected_subsystems = self.ast_analyzer.identify_subsystems(file_diffs)
        
        # Calculate impact score
        impact_score = self.ast_analyzer.calculate_impact_score(file_diffs, all_functions)
        
        # Determine risk level
        risk_level = self.ast_analyzer.determine_risk_level(impact_score, affected_subsystems)
        
        # Suggest test types
        suggested_test_types = self.ast_analyzer.suggest_test_types(affected_subsystems, all_functions)
        
        return CodeAnalysis(
            changed_files=changed_files,
            changed_functions=all_functions,
            affected_subsystems=affected_subsystems,
            impact_score=impact_score,
            risk_level=risk_level,
            suggested_test_types=suggested_test_types,
            related_tests=[]  # Will be populated by test database lookup
        )
