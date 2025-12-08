"""Root cause analyzer for test failures using AI-powered analysis.

This module implements the IRootCauseAnalyzer interface to analyze test failures,
correlate them with code changes, group related failures, and suggest fixes.
"""

import re
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime

from ai_generator.interfaces import IRootCauseAnalyzer
from ai_generator.models import (
    TestResult, FailureAnalysis, Commit, FixSuggestion,
    TestStatus, FailureInfo
)
from ai_generator.llm_providers import BaseLLMProvider, LLMProviderFactory, LLMProvider
from ai_generator.llm_providers_extended import (
    ExtendedLLMProviderFactory, ExtendedLLMProvider,
    AmazonQDeveloperProvider, KiroProvider
)


class StackTraceParser:
    """Parser for kernel stack traces and error messages."""
    
    @staticmethod
    def parse_stack_trace(stack_trace: str) -> Dict[str, Any]:
        """Parse a kernel stack trace into structured data.
        
        Args:
            stack_trace: Raw stack trace string
            
        Returns:
            Dictionary with parsed stack trace information
        """
        if not stack_trace:
            return {
                "frames": [],
                "error_type": "unknown",
                "error_location": None
            }
        
        frames = []
        error_type = "unknown"
        error_location = None
        
        # Extract error type from common patterns
        error_patterns = [
            r"(BUG|WARNING|OOPS|panic|kernel BUG)",
            r"(segmentation fault|general protection fault)",
            r"(use-after-free|double-free|buffer overflow)",
            r"(deadlock|race condition|NULL pointer dereference)"
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, stack_trace, re.IGNORECASE)
            if match:
                error_type = match.group(1).lower()
                break
        
        # Parse stack frames
        # Common format: function+offset/size [module]
        frame_pattern = r"(?:\[<[0-9a-f]+>\])?\s*([a-zA-Z_][a-zA-Z0-9_]*)\+0x([0-9a-f]+)/0x([0-9a-f]+)(?:\s+\[([^\]]+)\])?"
        
        for match in re.finditer(frame_pattern, stack_trace):
            function_name = match.group(1)
            offset = match.group(2)
            size = match.group(3)
            module = match.group(4) if match.group(4) else "kernel"
            
            frames.append({
                "function": function_name,
                "offset": f"0x{offset}",
                "size": f"0x{size}",
                "module": module
            })
            
            # First frame is usually the error location
            if not error_location:
                error_location = {
                    "function": function_name,
                    "module": module
                }
        
        # Alternative format: file:line function
        alt_frame_pattern = r"([a-zA-Z0-9_/\.]+):(\d+)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        
        for match in re.finditer(alt_frame_pattern, stack_trace):
            file_path = match.group(1)
            line_number = match.group(2)
            function_name = match.group(3)
            
            frames.append({
                "function": function_name,
                "file": file_path,
                "line": int(line_number),
                "module": "kernel"
            })
            
            if not error_location:
                error_location = {
                    "function": function_name,
                    "file": file_path,
                    "line": int(line_number)
                }
        
        return {
            "frames": frames,
            "error_type": error_type,
            "error_location": error_location
        }
    
    @staticmethod
    def symbolicate_address(address: str, symbol_map: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Convert a memory address to a symbol name.
        
        Args:
            address: Memory address as hex string
            symbol_map: Optional mapping of addresses to symbols
            
        Returns:
            Symbol name if found, None otherwise
        """
        if not symbol_map:
            return None
        
        # Normalize address format
        addr = address.lower().replace("0x", "")
        return symbol_map.get(addr)


class ErrorPatternRecognizer:
    """Recognizes common error patterns in kernel failures."""
    
    # Common kernel error patterns
    PATTERNS = {
        "null_pointer": {
            "regex": r"NULL pointer dereference|unable to handle kernel NULL pointer",
            "description": "NULL pointer dereference",
            "severity": "high"
        },
        "use_after_free": {
            "regex": r"use-after-free|KASAN.*use after free",
            "description": "Use-after-free memory error",
            "severity": "critical"
        },
        "buffer_overflow": {
            "regex": r"buffer overflow|stack overflow|KASAN.*out-of-bounds",
            "description": "Buffer overflow",
            "severity": "critical"
        },
        "deadlock": {
            "regex": r"deadlock|circular locking dependency|possible recursive locking",
            "description": "Deadlock or locking issue",
            "severity": "high"
        },
        "race_condition": {
            "regex": r"race condition|data race|KTSAN",
            "description": "Race condition",
            "severity": "high"
        },
        "memory_leak": {
            "regex": r"memory leak|unreferenced object|kmemleak",
            "description": "Memory leak",
            "severity": "medium"
        },
        "assertion_failure": {
            "regex": r"BUG_ON|WARN_ON|assertion.*failed",
            "description": "Assertion failure",
            "severity": "high"
        },
        "timeout": {
            "regex": r"timeout|hung task|soft lockup|hard lockup",
            "description": "Timeout or hang",
            "severity": "medium"
        }
    }
    
    @classmethod
    def recognize_pattern(cls, error_message: str, stack_trace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recognize error patterns in failure information.
        
        Args:
            error_message: Error message from failure
            stack_trace: Optional stack trace
            
        Returns:
            List of recognized patterns with metadata
        """
        recognized = []
        text = error_message + (" " + stack_trace if stack_trace else "")
        
        for pattern_name, pattern_info in cls.PATTERNS.items():
            if re.search(pattern_info["regex"], text, re.IGNORECASE):
                recognized.append({
                    "name": pattern_name,
                    "description": pattern_info["description"],
                    "severity": pattern_info["severity"]
                })
        
        return recognized


class FailureSignatureGenerator:
    """Generates unique signatures for failures to enable grouping."""
    
    @staticmethod
    def generate_signature(failure_info: FailureInfo, parsed_stack: Dict[str, Any]) -> str:
        """Generate a unique signature for a failure.
        
        The signature is based on:
        - Error type
        - Top stack frames (function names)
        - Error message (normalized)
        
        Args:
            failure_info: FailureInfo object
            parsed_stack: Parsed stack trace from StackTraceParser
            
        Returns:
            Hex string signature
        """
        components = []
        
        # Add error type
        components.append(parsed_stack.get("error_type", "unknown"))
        
        # Add top 3 stack frames (most relevant)
        frames = parsed_stack.get("frames", [])
        for frame in frames[:3]:
            components.append(frame.get("function", ""))
        
        # Add normalized error message (remove addresses, numbers)
        normalized_msg = re.sub(r'0x[0-9a-f]+', 'ADDR', failure_info.error_message)
        normalized_msg = re.sub(r'\d+', 'NUM', normalized_msg)
        components.append(normalized_msg[:100])  # First 100 chars
        
        # Generate hash
        signature_str = "|".join(components)
        return hashlib.sha256(signature_str.encode()).hexdigest()[:16]


class RootCauseAnalyzer(IRootCauseAnalyzer):
    """AI-powered root cause analyzer for test failures.
    
    Supports multiple LLM providers for log analysis:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Amazon Bedrock (Claude via Bedrock)
    - Amazon Q Developer Pro (AWS's AI coding assistant)
    - Kiro AI (AI-powered IDE)
    """
    
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **provider_kwargs
    ):
        """Initialize root cause analyzer.
        
        Args:
            llm_provider: Pre-configured LLM provider (optional)
            provider_type: Type of LLM provider ("openai", "anthropic", "bedrock", "amazon_q", "kiro")
            api_key: API key for LLM provider
            model: Model name to use
            **provider_kwargs: Additional provider-specific parameters:
                - For Amazon Q: region, profile, use_sso, sso_start_url, sso_region
                - For Kiro: api_url, use_sso, client_id, client_secret
                - For Bedrock: region
        
        Examples:
            # Using Amazon Q Developer Pro
            analyzer = RootCauseAnalyzer(
                provider_type="amazon_q",
                region="us-east-1",
                use_sso=True,
                sso_start_url="https://my-sso.awsapps.com/start"
            )
            
            # Using Kiro AI
            analyzer = RootCauseAnalyzer(
                provider_type="kiro",
                api_key="your-kiro-key"
            )
            
            # Using OpenAI (default)
            analyzer = RootCauseAnalyzer(
                provider_type="openai",
                api_key="your-openai-key"
            )
        """
        if llm_provider:
            self.llm_provider = llm_provider
        elif provider_type:
            # Try to create LLM provider with extended support
            try:
                # Use extended factory for Amazon Q and Kiro support
                if provider_type in ["amazon_q", "kiro"]:
                    self.llm_provider = ExtendedLLMProviderFactory.create(
                        provider=ExtendedLLMProvider(provider_type),
                        api_key=api_key,
                        model=model,
                        **provider_kwargs
                    )
                else:
                    # Use standard factory for OpenAI, Anthropic, Bedrock
                    self.llm_provider = ExtendedLLMProviderFactory.create(
                        provider=ExtendedLLMProvider(provider_type),
                        api_key=api_key,
                        model=model,
                        **provider_kwargs
                    )
            except (ImportError, Exception) as e:
                # Fall back to pattern-based analysis if LLM unavailable
                print(f"Warning: Could not initialize LLM provider: {e}")
                print("Falling back to pattern-based analysis")
                self.llm_provider = None
        else:
            # No LLM provider - use pattern-based analysis only
            self.llm_provider = None
        
        self.stack_parser = StackTraceParser()
        self.pattern_recognizer = ErrorPatternRecognizer()
        self.signature_generator = FailureSignatureGenerator()
        
        # Cache for failure signatures to enable grouping
        self._failure_signatures: Dict[str, List[str]] = {}
    
    def analyze_failure(self, failure: TestResult) -> FailureAnalysis:
        """Analyze a test failure to determine root cause.
        
        Args:
            failure: TestResult with failure information
            
        Returns:
            FailureAnalysis with root cause and suggestions
        """
        if failure.status == TestStatus.PASSED:
            raise ValueError("Cannot analyze a passing test")
        
        if not failure.failure_info:
            # Create minimal failure analysis for tests without detailed failure info
            return FailureAnalysis(
                failure_id=failure.test_id,
                root_cause="Test failed without detailed failure information",
                confidence=0.3,
                error_pattern="unknown",
                reproducibility=0.5
            )
        
        # Parse stack trace
        parsed_stack = self.stack_parser.parse_stack_trace(
            failure.failure_info.stack_trace or ""
        )
        
        # Recognize error patterns
        patterns = self.pattern_recognizer.recognize_pattern(
            failure.failure_info.error_message,
            failure.failure_info.stack_trace
        )
        
        # Generate failure signature
        signature = self.signature_generator.generate_signature(
            failure.failure_info,
            parsed_stack
        )
        
        # Use LLM to analyze the failure
        root_cause, confidence, suggested_fixes = self._llm_analyze_failure(
            failure.failure_info,
            parsed_stack,
            patterns
        )
        
        # Store signature for grouping
        if signature not in self._failure_signatures:
            self._failure_signatures[signature] = []
        self._failure_signatures[signature].append(failure.test_id)
        
        # Find related failures with same signature
        related_failures = [
            fid for fid in self._failure_signatures[signature]
            if fid != failure.test_id
        ]
        
        # Determine reproducibility based on related failures
        reproducibility = min(1.0, len(self._failure_signatures[signature]) / 10.0)
        
        return FailureAnalysis(
            failure_id=failure.test_id,
            root_cause=root_cause,
            confidence=confidence,
            error_pattern=patterns[0]["name"] if patterns else "unknown",
            stack_trace=failure.failure_info.stack_trace,
            suggested_fixes=suggested_fixes,
            related_failures=related_failures,
            reproducibility=reproducibility
        )
    
    def _llm_analyze_failure(
        self,
        failure_info: FailureInfo,
        parsed_stack: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> tuple[str, float, List[FixSuggestion]]:
        """Use LLM to analyze failure and suggest fixes.
        
        Args:
            failure_info: FailureInfo object
            parsed_stack: Parsed stack trace
            patterns: Recognized error patterns
            
        Returns:
            Tuple of (root_cause, confidence, suggested_fixes)
        """
        # If no LLM provider, use fallback immediately
        if not self.llm_provider:
            return self._fallback_analysis(failure_info, patterns)
        
        # Build prompt for LLM
        prompt = self._build_analysis_prompt(failure_info, parsed_stack, patterns)
        
        try:
            # Call LLM with retry logic
            response = self.llm_provider.generate_with_retry(prompt)
            
            # Parse LLM response
            return self._parse_llm_response(response.content)
            
        except Exception as e:
            # Fallback to pattern-based analysis if LLM fails
            return self._fallback_analysis(failure_info, patterns)
    
    def _build_analysis_prompt(
        self,
        failure_info: FailureInfo,
        parsed_stack: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for LLM analysis.
        
        Args:
            failure_info: FailureInfo object
            parsed_stack: Parsed stack trace
            patterns: Recognized error patterns
            
        Returns:
            Prompt string
        """
        prompt = f"""Analyze this kernel test failure and provide root cause analysis.

Error Message: {failure_info.error_message}

Error Type: {parsed_stack.get('error_type', 'unknown')}

Recognized Patterns: {', '.join(p['description'] for p in patterns) if patterns else 'None'}

Stack Trace:
{failure_info.stack_trace or 'Not available'}

Error Location: {parsed_stack.get('error_location', 'Unknown')}

Please provide:
1. Root cause (1-2 sentences)
2. Confidence level (0.0-1.0)
3. Up to 3 suggested fixes with descriptions

Format your response as:
ROOT_CAUSE: <description>
CONFIDENCE: <0.0-1.0>
FIX_1: <description>
FIX_2: <description>
FIX_3: <description>
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> tuple[str, float, List[FixSuggestion]]:
        """Parse LLM response into structured data.
        
        Args:
            response: LLM response text
            
        Returns:
            Tuple of (root_cause, confidence, suggested_fixes)
        """
        root_cause = "Unknown failure"
        confidence = 0.5
        suggested_fixes = []
        
        # Extract root cause
        root_match = re.search(r'ROOT_CAUSE:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
        if root_match:
            root_cause = root_match.group(1).strip()
        
        # Extract confidence
        conf_match = re.search(r'CONFIDENCE:\s*(0?\.\d+|1\.0)', response, re.IGNORECASE)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
            except ValueError:
                pass
        
        # Extract fixes
        for i in range(1, 4):
            fix_match = re.search(rf'FIX_{i}:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if fix_match:
                fix_desc = fix_match.group(1).strip()
                if fix_desc and fix_desc.lower() not in ['none', 'n/a', 'not applicable']:
                    suggested_fixes.append(FixSuggestion(
                        description=fix_desc,
                        confidence=confidence * 0.8,  # Slightly lower confidence for fixes
                        rationale="Generated by AI analysis"
                    ))
        
        return root_cause, confidence, suggested_fixes
    
    def _fallback_analysis(
        self,
        failure_info: FailureInfo,
        patterns: List[Dict[str, Any]]
    ) -> tuple[str, float, List[FixSuggestion]]:
        """Fallback analysis when LLM is unavailable.
        
        Args:
            failure_info: FailureInfo object
            patterns: Recognized error patterns
            
        Returns:
            Tuple of (root_cause, confidence, suggested_fixes)
        """
        if patterns:
            pattern = patterns[0]
            root_cause = f"{pattern['description']}: {failure_info.error_message[:100]}"
            confidence = 0.6
            
            # Pattern-based fix suggestions
            fix_suggestions = self._get_pattern_based_fixes(pattern['name'])
        else:
            root_cause = f"Test failure: {failure_info.error_message[:100]}"
            confidence = 0.3
            fix_suggestions = []
        
        return root_cause, confidence, fix_suggestions
    
    def _get_pattern_based_fixes(self, pattern_name: str) -> List[FixSuggestion]:
        """Get fix suggestions based on error pattern.
        
        Args:
            pattern_name: Name of recognized pattern
            
        Returns:
            List of FixSuggestion objects
        """
        pattern_fixes = {
            "null_pointer": [
                "Add NULL pointer check before dereferencing",
                "Ensure proper initialization of pointer variables"
            ],
            "use_after_free": [
                "Review object lifetime management",
                "Add reference counting or use-after-free detection"
            ],
            "buffer_overflow": [
                "Check buffer bounds before write operations",
                "Use safe string functions (strncpy, snprintf)"
            ],
            "deadlock": [
                "Review lock ordering and acquisition patterns",
                "Consider using lock-free data structures"
            ],
            "race_condition": [
                "Add proper synchronization primitives",
                "Review critical sections and shared data access"
            ],
            "memory_leak": [
                "Ensure all allocated memory is freed",
                "Review error paths for missing cleanup"
            ]
        }
        
        fixes = pattern_fixes.get(pattern_name, [])
        return [
            FixSuggestion(
                description=fix,
                confidence=0.5,
                rationale=f"Common fix for {pattern_name} errors"
            )
            for fix in fixes
        ]
    
    def correlate_with_changes(self, failure: TestResult, commits: List[Commit]) -> List[Commit]:
        """Correlate failure with recent code changes.
        
        Args:
            failure: TestResult with failure information
            commits: List of recent Commit objects
            
        Returns:
            List of suspicious Commit objects, sorted by suspicion score
        """
        if not commits:
            return []
        
        # Parse stack trace to get affected files/functions
        if failure.failure_info and failure.failure_info.stack_trace:
            parsed_stack = self.stack_parser.parse_stack_trace(
                failure.failure_info.stack_trace
            )
        else:
            parsed_stack = {"frames": [], "error_location": None}
        
        # Extract affected files from stack trace
        affected_files = set()
        for frame in parsed_stack.get("frames", []):
            if "file" in frame:
                affected_files.add(frame["file"])
        
        # Score commits based on relevance
        scored_commits = []
        for commit in commits:
            score = self._calculate_suspicion_score(
                commit,
                affected_files,
                failure
            )
            scored_commits.append((score, commit))
        
        # Sort by score (highest first) and return commits
        scored_commits.sort(reverse=True, key=lambda x: x[0])
        return [commit for score, commit in scored_commits if score > 0]
    
    def _calculate_suspicion_score(
        self,
        commit: Commit,
        affected_files: set,
        failure: TestResult
    ) -> float:
        """Calculate suspicion score for a commit.
        
        Args:
            commit: Commit to score
            affected_files: Set of files involved in failure
            failure: TestResult object
            
        Returns:
            Suspicion score (0.0-1.0)
        """
        score = 0.0
        
        # Check if commit modified files in stack trace
        for changed_file in commit.files_changed:
            for affected_file in affected_files:
                if affected_file in changed_file or changed_file in affected_file:
                    score += 0.5
        
        # Check if commit is recent (more suspicious)
        if failure.timestamp:
            time_diff = (failure.timestamp - commit.timestamp).total_seconds()
            if time_diff < 86400:  # Within 24 hours
                score += 0.3
            elif time_diff < 604800:  # Within 1 week
                score += 0.1
        
        # Check commit message for relevant keywords
        keywords = ["fix", "bug", "crash", "error", "issue", "problem"]
        if any(keyword in commit.message.lower() for keyword in keywords):
            score += 0.2
        
        return min(1.0, score)
    
    def group_failures(self, failures: List[TestResult]) -> Dict[str, List[TestResult]]:
        """Group related failures by root cause.
        
        Args:
            failures: List of TestResult objects with failures
            
        Returns:
            Dictionary mapping failure signature to list of TestResult objects
        """
        groups: Dict[str, List[TestResult]] = {}
        
        for failure in failures:
            if failure.status == TestStatus.PASSED:
                continue
            
            if not failure.failure_info:
                # Group failures without detailed info separately
                signature = "unknown"
            else:
                # Parse and generate signature
                parsed_stack = self.stack_parser.parse_stack_trace(
                    failure.failure_info.stack_trace or ""
                )
                signature = self.signature_generator.generate_signature(
                    failure.failure_info,
                    parsed_stack
                )
            
            if signature not in groups:
                groups[signature] = []
            groups[signature].append(failure)
        
        return groups
