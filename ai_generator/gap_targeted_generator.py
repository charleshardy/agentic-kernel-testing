"""Gap-targeted test generator for covering untested code paths.

This module provides functionality for:
- Generating test cases specifically targeting coverage gaps
- Converting code paths to test cases
- Verifying that generated tests cover the intended gaps
"""

import uuid
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import TestCase, TestType, ExpectedOutcome, Function
from .interfaces import ITestGenerator
from .llm_providers import BaseLLMProvider, LLMProviderFactory, LLMProvider
from analysis.coverage_analyzer import CoverageGap, GapType

try:
    from config import get_settings
except ImportError:
    # Fallback for testing
    def get_settings():
        from types import SimpleNamespace
        return SimpleNamespace(
            llm=SimpleNamespace(
                provider="openai",
                api_key=None,
                model="gpt-4",
                temperature=0.7,
                max_tokens=2000,
                timeout=60,
                max_retries=3
            )
        )


class GapTargetedTestGenerator:
    """Generator for creating tests that target specific coverage gaps."""
    
    GAP_TEST_TEMPLATE = """
Generate a test case to cover the following untested code path:

File: {file_path}
Line: {line_number}
Function: {function_name}
Subsystem: {subsystem}
Gap Type: {gap_type}

Code Context:
{context}

Generate a test case that will execute this specific code path.
The test should:
1. Set up the necessary preconditions to reach this code
2. Execute the code path
3. Verify the expected behavior

Return the test in JSON format with these fields:
- name: Test name describing what gap it covers
- description: Detailed description of the test
- test_script: Complete test code that will execute this path
- expected_outcome: What should happen when the test runs
- setup_requirements: Any special setup needed
"""
    
    BRANCH_TEST_TEMPLATE = """
Generate a test case to cover an untested branch:

File: {file_path}
Line: {line_number}
Branch ID: {branch_id}
Function: {function_name}

Code Context:
{context}

This is a conditional branch that has not been executed.
Generate a test case that will take this specific branch.

Consider:
1. What condition must be true/false to take this branch?
2. How to set up inputs to satisfy that condition?
3. What is the expected behavior when this branch executes?

Return the test in JSON format.
"""
    
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        settings: Optional[Any] = None
    ):
        """Initialize gap-targeted test generator.
        
        Args:
            llm_provider: LLM provider instance (creates default if None)
            settings: Settings instance (uses global if None)
        """
        self.settings = settings or get_settings()
        
        if llm_provider is None:
            # Create provider from settings
            provider_type = LLMProvider(self.settings.llm.provider)
            self.llm_provider = LLMProviderFactory.create(
                provider=provider_type,
                api_key=self.settings.llm.api_key,
                model=self.settings.llm.model,
                temperature=self.settings.llm.temperature,
                max_tokens=self.settings.llm.max_tokens,
                timeout=self.settings.llm.timeout,
                max_retries=self.settings.llm.max_retries
            )
        else:
            self.llm_provider = llm_provider
    
    def generate_tests_for_gaps(
        self,
        gaps: List[CoverageGap],
        source_dir: Optional[str] = None
    ) -> List[TestCase]:
        """Generate test cases targeting specific coverage gaps.
        
        Args:
            gaps: List of CoverageGap objects to target
            source_dir: Optional source directory for reading code
            
        Returns:
            List of TestCase objects targeting the gaps
        """
        test_cases = []
        
        for gap in gaps:
            try:
                test_case = self.generate_test_for_gap(gap, source_dir)
                if test_case:
                    test_cases.append(test_case)
            except Exception as e:
                # Log error but continue with other gaps
                print(f"Failed to generate test for gap {gap}: {e}")
                continue
        
        return test_cases
    
    def generate_test_for_gap(
        self,
        gap: CoverageGap,
        source_dir: Optional[str] = None
    ) -> Optional[TestCase]:
        """Generate a test case for a specific coverage gap.
        
        Args:
            gap: CoverageGap to target
            source_dir: Optional source directory for reading code
            
        Returns:
            TestCase object or None if generation fails
        """
        # Enhance context if source directory provided
        context = gap.context
        if source_dir and not context:
            context = self._read_code_context(source_dir, gap.file_path, gap.line_number)
        
        # Choose template based on gap type
        if gap.gap_type == GapType.BRANCH:
            template = self.BRANCH_TEST_TEMPLATE
            template_vars = {
                'file_path': gap.file_path,
                'line_number': gap.line_number,
                'branch_id': gap.branch_id or 0,
                'function_name': gap.function_name or 'unknown',
                'context': context or 'No context available'
            }
        else:
            template = self.GAP_TEST_TEMPLATE
            template_vars = {
                'file_path': gap.file_path,
                'line_number': gap.line_number,
                'function_name': gap.function_name or 'unknown',
                'subsystem': gap.subsystem or 'unknown',
                'gap_type': gap.gap_type.value,
                'context': context or 'No context available'
            }
        
        prompt = template.format(**template_vars)
        
        try:
            response = self.llm_provider.generate_with_retry(prompt)
            test_data = self._extract_json(response.content)
            
            # Create test case from LLM response
            test_case = self._create_test_case_from_gap(test_data, gap)
            
            return test_case
        except Exception as e:
            # Fallback to template-based generation
            return self._create_fallback_test_for_gap(gap)
    
    def path_to_test_case(
        self,
        code_path: str,
        source_dir: Optional[str] = None
    ) -> Optional[TestCase]:
        """Convert a code path reference to a test case.
        
        Args:
            code_path: Code path in format "file:line" or "file:line:branch"
            source_dir: Optional source directory for reading code
            
        Returns:
            TestCase object or None if conversion fails
        """
        # Parse code path
        parts = code_path.split(':')
        if len(parts) < 2:
            return None
        
        file_path = parts[0]
        line_number = int(parts[1])
        branch_id = int(parts[2]) if len(parts) > 2 else None
        
        # Create a CoverageGap from the code path
        gap_type = GapType.BRANCH if branch_id is not None else GapType.LINE
        
        # Read context from source
        context = ""
        function_name = None
        if source_dir:
            context = self._read_code_context(source_dir, file_path, line_number)
            function_name = self._extract_function_name(source_dir, file_path, line_number)
        
        # Determine subsystem
        subsystem = self._determine_subsystem(file_path)
        
        # Create gap object
        gap = CoverageGap(
            gap_type=gap_type,
            file_path=file_path,
            line_number=line_number,
            branch_id=branch_id,
            function_name=function_name,
            context=context,
            subsystem=subsystem
        )
        
        # Generate test for this gap
        return self.generate_test_for_gap(gap, source_dir)
    
    def verify_gap_coverage(
        self,
        test_case: TestCase,
        gap: CoverageGap
    ) -> bool:
        """Verify that a test case targets a specific gap.
        
        Args:
            test_case: TestCase to verify
            gap: CoverageGap that should be covered
            
        Returns:
            True if test targets the gap, False otherwise
        """
        # Check if test metadata references the gap
        if 'target_gap' in test_case.metadata:
            target_gap = test_case.metadata['target_gap']
            if (target_gap.get('file_path') == gap.file_path and
                target_gap.get('line_number') == gap.line_number):
                return True
        
        # Check if test code paths include the gap location
        gap_path = f"{gap.file_path}:{gap.line_number}"
        for code_path in test_case.code_paths:
            if gap_path in code_path:
                return True
        
        # Check if test script mentions the file and line
        if gap.file_path in test_case.test_script:
            # Look for line number references
            if str(gap.line_number) in test_case.test_script:
                return True
        
        # Check if test targets the same function
        if gap.function_name and gap.function_name in test_case.test_script:
            return True
        
        return False
    
    def _create_test_case_from_gap(
        self,
        test_data: Dict[str, Any],
        gap: CoverageGap
    ) -> TestCase:
        """Create a TestCase from LLM-generated data and gap info.
        
        Args:
            test_data: Dictionary with test data from LLM
            gap: CoverageGap being targeted
            
        Returns:
            TestCase object
        """
        # Parse expected outcome
        outcome_data = test_data.get('expected_outcome', {})
        if isinstance(outcome_data, str):
            outcome = ExpectedOutcome(should_pass=True)
        elif isinstance(outcome_data, dict):
            outcome = ExpectedOutcome(**outcome_data)
        else:
            outcome = ExpectedOutcome(should_pass=True)
        
        # Create test case
        test_case = TestCase(
            id=f"gap_{uuid.uuid4().hex[:8]}",
            name=test_data.get('name', f"Cover {gap.file_path}:{gap.line_number}"),
            description=test_data.get('description', f"Test to cover gap at {gap}"),
            test_type=TestType.UNIT,
            target_subsystem=gap.subsystem or "unknown",
            code_paths=[f"{gap.file_path}:{gap.line_number}"],
            test_script=test_data.get('test_script', ''),
            expected_outcome=outcome,
            execution_time_estimate=test_data.get('execution_time', 60),
            metadata={
                'gap_targeted': True,
                'target_gap': {
                    'file_path': gap.file_path,
                    'line_number': gap.line_number,
                    'gap_type': gap.gap_type.value,
                    'branch_id': gap.branch_id,
                    'function_name': gap.function_name,
                    'priority': gap.priority.value
                },
                'setup_requirements': test_data.get('setup_requirements', [])
            }
        )
        
        return test_case
    
    def _create_fallback_test_for_gap(self, gap: CoverageGap) -> TestCase:
        """Create a fallback test case when LLM generation fails.
        
        Args:
            gap: CoverageGap to target
            
        Returns:
            Basic TestCase object
        """
        test_script = f"""# Gap-targeted test for {gap.file_path}:{gap.line_number}
# Function: {gap.function_name or 'unknown'}
# Subsystem: {gap.subsystem or 'unknown'}
# Gap type: {gap.gap_type.value}

def test_gap_{gap.line_number}():
    \"\"\"Test to cover untested code at line {gap.line_number}.\"\"\"
    # TODO: Implement test to reach {gap.file_path}:{gap.line_number}
    pass
"""
        
        return TestCase(
            id=f"gap_{uuid.uuid4().hex[:8]}",
            name=f"Cover gap at {gap.file_path}:{gap.line_number}",
            description=f"Fallback test to cover {gap.gap_type.value} gap",
            test_type=TestType.UNIT,
            target_subsystem=gap.subsystem or "unknown",
            code_paths=[f"{gap.file_path}:{gap.line_number}"],
            test_script=test_script,
            execution_time_estimate=30,
            metadata={
                'gap_targeted': True,
                'fallback': True,
                'target_gap': {
                    'file_path': gap.file_path,
                    'line_number': gap.line_number,
                    'gap_type': gap.gap_type.value
                }
            }
        )
    
    def _read_code_context(
        self,
        source_dir: str,
        file_path: str,
        line_number: int,
        context_lines: int = 5
    ) -> str:
        """Read code context around a line.
        
        Args:
            source_dir: Source directory
            file_path: Relative file path
            line_number: Line number
            context_lines: Number of lines before/after to include
            
        Returns:
            Code context as string
        """
        full_path = Path(source_dir) / file_path
        
        if not full_path.exists():
            return ""
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if line_number < 1 or line_number > len(lines):
                return ""
            
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            context = ''.join(lines[start:end])
            return context.strip()
        except (IOError, UnicodeDecodeError):
            return ""
    
    def _extract_function_name(
        self,
        source_dir: str,
        file_path: str,
        line_number: int
    ) -> Optional[str]:
        """Extract function name containing a line.
        
        Args:
            source_dir: Source directory
            file_path: Relative file path
            line_number: Line number
            
        Returns:
            Function name or None
        """
        full_path = Path(source_dir) / file_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if line_number < 1 or line_number > len(lines):
                return None
            
            # Look backwards for function definition
            for i in range(line_number - 1, max(0, line_number - 100), -1):
                line = lines[i]
                # Simple heuristic for function definitions
                if re.match(r'^\s*(static\s+)?\w+\s+\w+\s*\(', line):
                    match = re.search(r'\b(\w+)\s*\(', line)
                    if match:
                        return match.group(1)
            
            return None
        except (IOError, UnicodeDecodeError):
            return None
    
    def _determine_subsystem(self, file_path: str) -> str:
        """Determine subsystem from file path.
        
        Args:
            file_path: File path
            
        Returns:
            Subsystem name
        """
        parts = file_path.split('/')
        
        if len(parts) >= 2:
            if parts[0] in ['drivers', 'fs', 'net', 'kernel', 'mm', 'arch']:
                return parts[1] if len(parts) > 1 else parts[0]
            return parts[0]
        
        return "unknown"
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON object from LLM response.
        
        Args:
            text: Response text that may contain JSON
            
        Returns:
            Parsed JSON dictionary
        """
        import json
        
        # Try to find JSON in code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # Try to find JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        # Try parsing the whole text
        return json.loads(text)
