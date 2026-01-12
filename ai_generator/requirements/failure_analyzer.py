"""Property Failure Analyzer for Agentic AI Test Requirements.

Analyzes property test failures and provides:
- Root cause analysis
- Requirement correlation
- Failure grouping
- Fix suggestions
"""

import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import json

from .models import (
    PropertyTestResult,
    FailureAnalysis,
    RequirementViolation,
    FixSuggestion,
    ParsedRequirement,
    CorrectnessProperty,
    PropertyPattern,
)


class PropertyFailureAnalyzer:
    """Analyzes property test failures.
    
    Provides:
    - Root cause identification
    - Requirement violation correlation
    - Failure grouping by pattern
    - AI-assisted fix suggestions
    """
    
    # Common failure patterns and their descriptions
    FAILURE_PATTERNS = {
        'assertion_error': {
            'pattern': r'AssertionError',
            'description': 'Property assertion failed',
            'severity': 'high',
        },
        'type_error': {
            'pattern': r'TypeError',
            'description': 'Type mismatch in property test',
            'severity': 'high',
        },
        'value_error': {
            'pattern': r'ValueError',
            'description': 'Invalid value encountered',
            'severity': 'medium',
        },
        'attribute_error': {
            'pattern': r'AttributeError',
            'description': 'Missing attribute or method',
            'severity': 'high',
        },
        'key_error': {
            'pattern': r'KeyError',
            'description': 'Missing dictionary key',
            'severity': 'medium',
        },
        'index_error': {
            'pattern': r'IndexError',
            'description': 'Index out of bounds',
            'severity': 'medium',
        },
        'timeout': {
            'pattern': r'timed out|timeout',
            'description': 'Test execution timed out',
            'severity': 'low',
        },
        'overflow': {
            'pattern': r'OverflowError|overflow',
            'description': 'Numeric overflow occurred',
            'severity': 'high',
        },
        'memory': {
            'pattern': r'MemoryError|out of memory',
            'description': 'Memory allocation failed',
            'severity': 'critical',
        },
    }
    
    def __init__(self, llm_provider: Optional[Any] = None):
        """Initialize the failure analyzer.
        
        Args:
            llm_provider: Optional LLM provider for intelligent analysis
        """
        self.llm_provider = llm_provider
        self._requirements_cache: Dict[str, ParsedRequirement] = {}
        self._properties_cache: Dict[str, CorrectnessProperty] = {}
    
    def register_requirement(self, req: ParsedRequirement) -> None:
        """Register a requirement for correlation.
        
        Args:
            req: ParsedRequirement to register
        """
        self._requirements_cache[req.id] = req
    
    def register_property(self, prop: CorrectnessProperty) -> None:
        """Register a property for correlation.
        
        Args:
            prop: CorrectnessProperty to register
        """
        self._properties_cache[prop.id] = prop
    
    async def analyze_failure(self, result: PropertyTestResult) -> FailureAnalysis:
        """Analyze a property test failure.
        
        Args:
            result: PropertyTestResult with failure
            
        Returns:
            FailureAnalysis with root cause and suggestions
        """
        if result.passed:
            raise ValueError("Cannot analyze a passing test result")
        
        # Identify failure pattern
        failure_type, severity = self._identify_failure_pattern(result.error_message)
        
        # Determine root cause
        root_cause = self._determine_root_cause(result, failure_type)
        
        # Correlate with requirement
        violation = await self.correlate_with_requirement(result)
        
        # Generate fix suggestions
        suggestions = await self.suggest_fixes_for_result(result, failure_type)
        
        # Calculate confidence based on available information
        confidence = self._calculate_confidence(result, violation, suggestions)
        
        return FailureAnalysis(
            test_id=result.test_id,
            property_id=result.property_id,
            requirement_ids=result.requirement_ids,
            root_cause=root_cause,
            counter_example=result.counter_example,
            shrunk_example=result.shrunk_example,
            violation=violation,
            related_failures=[],  # Will be populated by group_failures
            suggested_fixes=suggestions,
            confidence=confidence,
        )
    
    async def correlate_with_requirement(
        self,
        result: PropertyTestResult
    ) -> Optional[RequirementViolation]:
        """Correlate failure with violated requirement.
        
        Args:
            result: PropertyTestResult with failure
            
        Returns:
            RequirementViolation with requirement details
        """
        if not result.requirement_ids:
            return None
        
        # Get the primary requirement
        req_id = result.requirement_ids[0]
        req = self._requirements_cache.get(req_id)
        
        # Get the property
        prop = self._properties_cache.get(result.property_id)
        
        # Generate violation description
        violation_desc = self._generate_violation_description(result, req, prop)
        
        # Determine severity based on failure type
        severity = self._determine_severity(result.error_message)
        
        return RequirementViolation(
            requirement_id=req_id,
            requirement_text=req.text if req else f"Requirement {req_id}",
            property_id=result.property_id,
            property_statement=prop.property_statement if prop else "Unknown property",
            counter_example=result.counter_example or result.shrunk_example,
            violation_description=violation_desc,
            severity=severity,
        )
    
    def group_failures(
        self,
        results: List[PropertyTestResult]
    ) -> Dict[str, List[PropertyTestResult]]:
        """Group related failures by root cause.
        
        Args:
            results: List of failed test results
            
        Returns:
            Dictionary mapping root cause to failures
        """
        groups: Dict[str, List[PropertyTestResult]] = defaultdict(list)
        
        for result in results:
            if not result.passed:
                # Identify failure pattern
                failure_type, _ = self._identify_failure_pattern(result.error_message)
                
                # Create group key based on failure type and property pattern
                prop = self._properties_cache.get(result.property_id)
                pattern = prop.pattern.value if prop else 'unknown'
                
                group_key = f"{failure_type}:{pattern}"
                groups[group_key].append(result)
        
        return dict(groups)
    
    async def suggest_fixes(self, analysis: FailureAnalysis) -> List[FixSuggestion]:
        """Suggest fixes based on failure analysis.
        
        Args:
            analysis: FailureAnalysis to generate fixes for
            
        Returns:
            List of suggested fixes
        """
        suggestions = []
        
        # Get property pattern for context
        prop = self._properties_cache.get(analysis.property_id)
        pattern = prop.pattern if prop else None
        
        # Generate pattern-specific suggestions
        if pattern == PropertyPattern.ROUND_TRIP:
            suggestions.extend(self._suggest_round_trip_fixes(analysis))
        elif pattern == PropertyPattern.IDEMPOTENCE:
            suggestions.extend(self._suggest_idempotence_fixes(analysis))
        elif pattern == PropertyPattern.INVARIANT:
            suggestions.extend(self._suggest_invariant_fixes(analysis))
        elif pattern == PropertyPattern.METAMORPHIC:
            suggestions.extend(self._suggest_metamorphic_fixes(analysis))
        elif pattern == PropertyPattern.ERROR_CONDITION:
            suggestions.extend(self._suggest_error_handling_fixes(analysis))
        
        # Add generic suggestions based on error type
        suggestions.extend(self._suggest_generic_fixes(analysis))
        
        # Use LLM for additional suggestions if available
        if self.llm_provider:
            llm_suggestions = await self._get_llm_suggestions(analysis)
            suggestions.extend(llm_suggestions)
        
        # Sort by confidence
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    async def suggest_fixes_for_result(
        self,
        result: PropertyTestResult,
        failure_type: str
    ) -> List[FixSuggestion]:
        """Generate fix suggestions for a test result.
        
        Args:
            result: PropertyTestResult with failure
            failure_type: Identified failure type
            
        Returns:
            List of FixSuggestion objects
        """
        suggestions = []
        
        # Add suggestions based on failure type
        if failure_type == 'assertion_error':
            suggestions.append(FixSuggestion(
                description="Review the property assertion logic",
                code_change="Check that the assertion correctly captures the property",
                confidence=0.7,
                rationale="Assertion errors often indicate incorrect property specification",
            ))
        
        elif failure_type == 'type_error':
            suggestions.append(FixSuggestion(
                description="Add type validation or conversion",
                code_change="Add isinstance() checks or type conversion before operations",
                confidence=0.8,
                rationale="Type errors suggest missing input validation",
            ))
        
        elif failure_type == 'value_error':
            suggestions.append(FixSuggestion(
                description="Add value range validation",
                code_change="Add assume() preconditions to filter invalid values",
                confidence=0.75,
                rationale="Value errors indicate edge cases not handled",
            ))
        
        elif failure_type == 'timeout':
            suggestions.append(FixSuggestion(
                description="Optimize test or increase timeout",
                code_change="Consider reducing input size or complexity",
                confidence=0.6,
                rationale="Timeouts may indicate performance issues or infinite loops",
            ))
        
        # Add counter-example specific suggestion
        if result.counter_example:
            suggestions.append(FixSuggestion(
                description=f"Handle edge case: {str(result.counter_example)[:50]}",
                code_change="Add specific handling for this input pattern",
                confidence=0.65,
                rationale="Counter-example reveals unhandled edge case",
            ))
        
        return suggestions
    
    def _identify_failure_pattern(
        self,
        error_message: Optional[str]
    ) -> Tuple[str, str]:
        """Identify the failure pattern from error message.
        
        Args:
            error_message: Error message string
            
        Returns:
            Tuple of (failure_type, severity)
        """
        if not error_message:
            return ('unknown', 'medium')
        
        for pattern_name, pattern_info in self.FAILURE_PATTERNS.items():
            if re.search(pattern_info['pattern'], error_message, re.IGNORECASE):
                return (pattern_name, pattern_info['severity'])
        
        return ('unknown', 'medium')
    
    def _determine_root_cause(
        self,
        result: PropertyTestResult,
        failure_type: str
    ) -> str:
        """Determine the root cause of a failure.
        
        Args:
            result: PropertyTestResult with failure
            failure_type: Identified failure type
            
        Returns:
            Root cause description
        """
        prop = self._properties_cache.get(result.property_id)
        
        if failure_type == 'assertion_error':
            if prop:
                return f"Property '{prop.name}' violated: {prop.property_statement}"
            return "Property assertion failed with counter-example"
        
        elif failure_type == 'type_error':
            return "Type mismatch between expected and actual values"
        
        elif failure_type == 'value_error':
            return "Invalid value encountered during property verification"
        
        elif failure_type == 'timeout':
            return "Test execution exceeded time limit"
        
        elif failure_type == 'memory':
            return "Memory exhaustion during test execution"
        
        else:
            return f"Test failed with {failure_type}: {result.error_message or 'Unknown error'}"
    
    def _determine_severity(self, error_message: Optional[str]) -> str:
        """Determine severity from error message.
        
        Args:
            error_message: Error message string
            
        Returns:
            Severity level (low, medium, high, critical)
        """
        _, severity = self._identify_failure_pattern(error_message)
        return severity
    
    def _generate_violation_description(
        self,
        result: PropertyTestResult,
        req: Optional[ParsedRequirement],
        prop: Optional[CorrectnessProperty]
    ) -> str:
        """Generate a description of the requirement violation.
        
        Args:
            result: PropertyTestResult with failure
            req: Associated requirement
            prop: Associated property
            
        Returns:
            Violation description
        """
        parts = []
        
        if prop:
            parts.append(f"Property '{prop.name}' failed to hold.")
            parts.append(f"Universal quantifier: {prop.universal_quantifier}")
        
        if req:
            parts.append(f"This violates requirement: {req.text[:100]}...")
        
        if result.counter_example:
            parts.append(f"Counter-example found: {result.counter_example}")
        
        if result.error_message:
            parts.append(f"Error: {result.error_message[:200]}")
        
        return ' '.join(parts) if parts else "Property test failed"
    
    def _calculate_confidence(
        self,
        result: PropertyTestResult,
        violation: Optional[RequirementViolation],
        suggestions: List[FixSuggestion]
    ) -> float:
        """Calculate confidence score for the analysis.
        
        Args:
            result: PropertyTestResult
            violation: RequirementViolation if found
            suggestions: List of suggestions
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have a counter-example
        if result.counter_example:
            confidence += 0.15
        
        # Increase confidence if we have a shrunk example
        if result.shrunk_example:
            confidence += 0.1
        
        # Increase confidence if we correlated with requirement
        if violation:
            confidence += 0.15
        
        # Increase confidence based on suggestion quality
        if suggestions:
            avg_suggestion_confidence = sum(s.confidence for s in suggestions) / len(suggestions)
            confidence += avg_suggestion_confidence * 0.1
        
        return min(confidence, 1.0)
    
    def _suggest_round_trip_fixes(self, analysis: FailureAnalysis) -> List[FixSuggestion]:
        """Generate fixes for round-trip property failures."""
        return [
            FixSuggestion(
                description="Ensure encode/decode functions are inverses",
                code_change="Verify that decode(encode(x)) == x for all valid inputs",
                confidence=0.8,
                rationale="Round-trip failures indicate asymmetric transformations",
            ),
            FixSuggestion(
                description="Check for data loss during transformation",
                code_change="Ensure no information is lost during encoding",
                confidence=0.7,
                rationale="Some data types may lose precision during conversion",
            ),
        ]
    
    def _suggest_idempotence_fixes(self, analysis: FailureAnalysis) -> List[FixSuggestion]:
        """Generate fixes for idempotence property failures."""
        return [
            FixSuggestion(
                description="Ensure operation produces same result when applied twice",
                code_change="Verify that f(f(x)) == f(x) for the operation",
                confidence=0.8,
                rationale="Idempotence failures indicate state mutation",
            ),
            FixSuggestion(
                description="Check for side effects in the operation",
                code_change="Remove or isolate side effects that affect repeated calls",
                confidence=0.7,
                rationale="Side effects can cause different results on repeated calls",
            ),
        ]
    
    def _suggest_invariant_fixes(self, analysis: FailureAnalysis) -> List[FixSuggestion]:
        """Generate fixes for invariant property failures."""
        return [
            FixSuggestion(
                description="Verify invariant is maintained throughout operation",
                code_change="Add invariant checks before and after state changes",
                confidence=0.8,
                rationale="Invariant failures indicate state corruption",
            ),
            FixSuggestion(
                description="Review state transition logic",
                code_change="Ensure all state transitions preserve the invariant",
                confidence=0.7,
                rationale="Some transitions may inadvertently break invariants",
            ),
        ]
    
    def _suggest_metamorphic_fixes(self, analysis: FailureAnalysis) -> List[FixSuggestion]:
        """Generate fixes for metamorphic property failures."""
        return [
            FixSuggestion(
                description="Verify metamorphic relation is correctly specified",
                code_change="Review the relationship between source and follow-up outputs",
                confidence=0.75,
                rationale="Metamorphic failures may indicate incorrect relation specification",
            ),
            FixSuggestion(
                description="Check input transformation preserves expected relationship",
                code_change="Ensure follow-up input correctly relates to source input",
                confidence=0.7,
                rationale="Input transformation may not preserve the expected relationship",
            ),
        ]
    
    def _suggest_error_handling_fixes(self, analysis: FailureAnalysis) -> List[FixSuggestion]:
        """Generate fixes for error handling property failures."""
        return [
            FixSuggestion(
                description="Add proper error handling for edge cases",
                code_change="Add try/except blocks or validation for invalid inputs",
                confidence=0.8,
                rationale="Error handling failures indicate missing validation",
            ),
            FixSuggestion(
                description="Define clear error conditions and responses",
                code_change="Document and implement consistent error responses",
                confidence=0.7,
                rationale="Inconsistent error handling causes unpredictable behavior",
            ),
        ]
    
    def _suggest_generic_fixes(self, analysis: FailureAnalysis) -> List[FixSuggestion]:
        """Generate generic fix suggestions."""
        suggestions = []
        
        if analysis.counter_example:
            suggestions.append(FixSuggestion(
                description="Add unit test for the counter-example",
                code_change=f"Create a specific test case for: {str(analysis.counter_example)[:50]}",
                confidence=0.6,
                rationale="Counter-examples should be captured as regression tests",
            ))
        
        suggestions.append(FixSuggestion(
            description="Review requirement for ambiguity",
            requirement_change="Clarify the requirement to remove ambiguous interpretations",
            confidence=0.5,
            rationale="Failures may indicate ambiguous requirements",
        ))
        
        return suggestions
    
    async def _get_llm_suggestions(self, analysis: FailureAnalysis) -> List[FixSuggestion]:
        """Get fix suggestions from LLM.
        
        Args:
            analysis: FailureAnalysis to analyze
            
        Returns:
            List of LLM-generated suggestions
        """
        # Placeholder for LLM integration
        # In production, this would call the LLM provider
        return []


# Convenience functions

async def analyze_test_failure(result: PropertyTestResult) -> FailureAnalysis:
    """Convenience function to analyze a test failure.
    
    Args:
        result: PropertyTestResult with failure
        
    Returns:
        FailureAnalysis
    """
    analyzer = PropertyFailureAnalyzer()
    return await analyzer.analyze_failure(result)


def group_test_failures(
    results: List[PropertyTestResult]
) -> Dict[str, List[PropertyTestResult]]:
    """Convenience function to group test failures.
    
    Args:
        results: List of test results
        
    Returns:
        Grouped failures
    """
    analyzer = PropertyFailureAnalyzer()
    return analyzer.group_failures(results)
