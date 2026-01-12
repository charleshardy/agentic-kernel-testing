"""
AI Assistant for Test Requirements

Provides intelligent suggestions for improving test coverage,
property generation, and requirement clarification.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import (
    CorrectnessProperty,
    GeneratedTest,
    ParsedRequirement,
    PropertyTestResult,
    TestSpecification,
)

logger = logging.getLogger(__name__)


class SuggestionType(Enum):
    """Types of AI suggestions."""
    PROPERTY_SUGGESTION = "property_suggestion"
    GENERATOR_IMPROVEMENT = "generator_improvement"
    REQUIREMENT_CLARIFICATION = "requirement_clarification"
    COVERAGE_GAP = "coverage_gap"
    TEST_OPTIMIZATION = "test_optimization"
    EDGE_CASE = "edge_case"


class SuggestionPriority(Enum):
    """Priority levels for suggestions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AISuggestion:
    """An AI-generated suggestion."""
    id: str
    type: SuggestionType
    priority: SuggestionPriority
    title: str
    description: str
    rationale: str
    action_items: List[str] = field(default_factory=list)
    related_requirements: List[str] = field(default_factory=list)
    related_properties: List[str] = field(default_factory=list)
    related_tests: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CoverageAnalysis:
    """Analysis of test coverage."""
    spec_id: str
    total_requirements: int
    covered_requirements: int
    coverage_percentage: float
    untested_requirements: List[str]
    low_coverage_areas: List[Dict[str, Any]]
    suggestions: List[AISuggestion]
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class TestHistoryAnalysis:
    """Analysis of test execution history."""
    spec_id: str
    total_executions: int
    pass_rate: float
    common_failures: List[Dict[str, Any]]
    flaky_tests: List[str]
    slow_tests: List[str]
    optimization_opportunities: List[AISuggestion]
    analyzed_at: datetime = field(default_factory=datetime.now)


class AIAssistant:
    """
    AI Assistant for test requirements.
    
    Provides intelligent suggestions for:
    - Property generation for low coverage areas
    - Generator improvements for frequent passes
    - Requirement clarification for ambiguous text
    - Test optimization based on execution history
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize the AI Assistant.
        
        Args:
            llm_client: Optional LLM client for advanced analysis
        """
        self.llm_client = llm_client
        self._suggestion_counter = 0
    
    def _generate_suggestion_id(self) -> str:
        """Generate a unique suggestion ID."""
        self._suggestion_counter += 1
        return f"sug_{self._suggestion_counter:06d}"
    
    async def analyze_coverage(
        self,
        spec: TestSpecification,
        test_results: Optional[List[PropertyTestResult]] = None
    ) -> CoverageAnalysis:
        """
        Analyze test coverage and generate suggestions.
        
        Args:
            spec: Test specification to analyze
            test_results: Optional list of test results
            
        Returns:
            CoverageAnalysis with suggestions
        """
        # Calculate coverage metrics
        total_reqs = len(spec.requirements)
        tested_reqs = set()
        
        for test in spec.tests:
            tested_reqs.update(test.requirement_ids)
        
        covered_count = len(tested_reqs)
        coverage_pct = (covered_count / total_reqs * 100) if total_reqs > 0 else 0
        
        untested = [
            req.id for req in spec.requirements 
            if req.id not in tested_reqs
        ]
        
        # Identify low coverage areas
        low_coverage_areas = []
        for req in spec.requirements:
            if req.id not in tested_reqs:
                low_coverage_areas.append({
                    "requirement_id": req.id,
                    "requirement_text": req.text,
                    "pattern": req.pattern.value if hasattr(req.pattern, 'value') else str(req.pattern),
                    "reason": "No tests generated"
                })
        
        # Generate suggestions
        suggestions = await self._generate_coverage_suggestions(
            spec, untested, test_results
        )
        
        return CoverageAnalysis(
            spec_id=spec.id,
            total_requirements=total_reqs,
            covered_requirements=covered_count,
            coverage_percentage=coverage_pct,
            untested_requirements=untested,
            low_coverage_areas=low_coverage_areas,
            suggestions=suggestions
        )
    
    async def _generate_coverage_suggestions(
        self,
        spec: TestSpecification,
        untested: List[str],
        test_results: Optional[List[PropertyTestResult]]
    ) -> List[AISuggestion]:
        """Generate suggestions for improving coverage."""
        suggestions = []
        
        # Suggest properties for untested requirements
        for req_id in untested[:5]:  # Limit to top 5
            req = next((r for r in spec.requirements if r.id == req_id), None)
            if req:
                suggestions.append(AISuggestion(
                    id=self._generate_suggestion_id(),
                    type=SuggestionType.PROPERTY_SUGGESTION,
                    priority=SuggestionPriority.HIGH,
                    title=f"Generate property for {req_id}",
                    description=f"Requirement '{req_id}' has no test coverage. Consider generating a property-based test.",
                    rationale=f"This requirement describes: {req.text[:100]}...",
                    action_items=[
                        f"Generate correctness property from requirement {req_id}",
                        "Create Hypothesis-based test with appropriate generators",
                        "Run test with minimum 100 iterations"
                    ],
                    related_requirements=[req_id],
                    confidence=0.9
                ))
        
        # Suggest edge case testing if coverage is high but failures exist
        if test_results:
            failed_tests = [r for r in test_results if not r.passed]
            if failed_tests and len(untested) == 0:
                suggestions.append(AISuggestion(
                    id=self._generate_suggestion_id(),
                    type=SuggestionType.EDGE_CASE,
                    priority=SuggestionPriority.MEDIUM,
                    title="Add edge case generators",
                    description="All requirements have coverage but some tests are failing. Consider adding edge case generators.",
                    rationale=f"{len(failed_tests)} test(s) failed, suggesting edge cases may not be covered.",
                    action_items=[
                        "Review counter-examples from failed tests",
                        "Add edge case values to generators",
                        "Consider boundary conditions"
                    ],
                    related_tests=[r.test_id for r in failed_tests[:3]],
                    confidence=0.75
                ))
        
        return suggestions
    
    async def suggest_properties(
        self,
        requirement: ParsedRequirement,
        existing_properties: Optional[List[CorrectnessProperty]] = None
    ) -> List[AISuggestion]:
        """
        Suggest properties for a requirement.
        
        Args:
            requirement: Requirement to analyze
            existing_properties: Already generated properties
            
        Returns:
            List of property suggestions
        """
        suggestions = []
        existing_patterns = set()
        
        if existing_properties:
            existing_patterns = {p.pattern for p in existing_properties}
        
        # Suggest based on requirement pattern
        pattern = requirement.pattern.value if hasattr(requirement.pattern, 'value') else str(requirement.pattern)
        
        if pattern == "event_driven" and "round_trip" not in str(existing_patterns):
            suggestions.append(AISuggestion(
                id=self._generate_suggestion_id(),
                type=SuggestionType.PROPERTY_SUGGESTION,
                priority=SuggestionPriority.MEDIUM,
                title="Consider round-trip property",
                description="Event-driven requirements often benefit from round-trip properties.",
                rationale="If the trigger involves data transformation, verify that the transformation is reversible.",
                action_items=[
                    "Identify input/output data types",
                    "Create encode/decode property",
                    "Test with diverse input generators"
                ],
                related_requirements=[requirement.id],
                confidence=0.7
            ))
        
        if pattern == "state_driven" and "invariant" not in str(existing_patterns):
            suggestions.append(AISuggestion(
                id=self._generate_suggestion_id(),
                type=SuggestionType.PROPERTY_SUGGESTION,
                priority=SuggestionPriority.HIGH,
                title="Add state invariant property",
                description="State-driven requirements should verify state invariants.",
                rationale="The WHILE condition implies a state that must be maintained.",
                action_items=[
                    "Identify state variables",
                    "Define invariant conditions",
                    "Test state transitions"
                ],
                related_requirements=[requirement.id],
                confidence=0.85
            ))
        
        if "idempotence" not in str(existing_patterns):
            suggestions.append(AISuggestion(
                id=self._generate_suggestion_id(),
                type=SuggestionType.PROPERTY_SUGGESTION,
                priority=SuggestionPriority.LOW,
                title="Consider idempotence property",
                description="Check if the operation should be idempotent.",
                rationale="Many operations should produce the same result when applied multiple times.",
                action_items=[
                    "Determine if operation should be idempotent",
                    "Create f(f(x)) == f(x) property if applicable"
                ],
                related_requirements=[requirement.id],
                confidence=0.5
            ))
        
        return suggestions
    
    async def suggest_generator_improvements(
        self,
        test: GeneratedTest,
        results: List[PropertyTestResult]
    ) -> List[AISuggestion]:
        """
        Suggest improvements to test generators.
        
        Args:
            test: Test to analyze
            results: Historical test results
            
        Returns:
            List of generator improvement suggestions
        """
        suggestions = []
        
        # Analyze pass rate
        if results:
            pass_count = sum(1 for r in results if r.passed)
            pass_rate = pass_count / len(results)
            
            if pass_rate == 1.0 and len(results) >= 5:
                suggestions.append(AISuggestion(
                    id=self._generate_suggestion_id(),
                    type=SuggestionType.GENERATOR_IMPROVEMENT,
                    priority=SuggestionPriority.MEDIUM,
                    title="Expand generator coverage",
                    description="Test always passes - consider expanding generator to cover more edge cases.",
                    rationale=f"Test has passed {len(results)} times consecutively. Generators may be too narrow.",
                    action_items=[
                        "Add boundary values to generators",
                        "Include null/empty cases",
                        "Add larger/extreme values",
                        "Consider negative test cases"
                    ],
                    related_tests=[test.id],
                    confidence=0.7
                ))
            
            # Check for flakiness
            if 0 < pass_rate < 1.0:
                fail_count = len(results) - pass_count
                suggestions.append(AISuggestion(
                    id=self._generate_suggestion_id(),
                    type=SuggestionType.TEST_OPTIMIZATION,
                    priority=SuggestionPriority.HIGH,
                    title="Investigate test flakiness",
                    description=f"Test has {fail_count} failures out of {len(results)} runs.",
                    rationale="Intermittent failures may indicate race conditions or non-deterministic behavior.",
                    action_items=[
                        "Review counter-examples from failures",
                        "Check for timing-dependent behavior",
                        "Consider adding deterministic seeds",
                        "Increase iteration count for better coverage"
                    ],
                    related_tests=[test.id],
                    confidence=0.85
                ))
        
        return suggestions
    
    async def suggest_requirement_clarifications(
        self,
        requirement: ParsedRequirement
    ) -> List[AISuggestion]:
        """
        Suggest clarifications for ambiguous requirements.
        
        Args:
            requirement: Requirement to analyze
            
        Returns:
            List of clarification suggestions
        """
        suggestions = []
        
        # Check for ambiguous words
        ambiguous_words = [
            'appropriate', 'adequate', 'reasonable', 'sufficient', 'timely',
            'fast', 'slow', 'quick', 'efficient', 'effective',
            'user-friendly', 'intuitive', 'easy', 'simple', 'complex',
            'many', 'few', 'some', 'several', 'various'
        ]
        
        text_lower = requirement.text.lower()
        found_ambiguous = [w for w in ambiguous_words if w in text_lower]
        
        if found_ambiguous:
            suggestions.append(AISuggestion(
                id=self._generate_suggestion_id(),
                type=SuggestionType.REQUIREMENT_CLARIFICATION,
                priority=SuggestionPriority.HIGH,
                title="Clarify ambiguous terms",
                description=f"Requirement contains ambiguous terms: {', '.join(found_ambiguous)}",
                rationale="Ambiguous terms make it difficult to create precise property tests.",
                action_items=[
                    f"Replace '{w}' with specific, measurable criteria" 
                    for w in found_ambiguous
                ],
                related_requirements=[requirement.id],
                confidence=0.9
            ))
        
        # Check for missing quantification
        if not any(q in text_lower for q in ['all', 'every', 'any', 'each', 'no', 'none']):
            suggestions.append(AISuggestion(
                id=self._generate_suggestion_id(),
                type=SuggestionType.REQUIREMENT_CLARIFICATION,
                priority=SuggestionPriority.MEDIUM,
                title="Add explicit quantification",
                description="Requirement lacks explicit quantification (all, every, any, etc.)",
                rationale="Property-based tests need clear quantification to define test scope.",
                action_items=[
                    "Specify if requirement applies to 'all' or 'some' cases",
                    "Define the domain of valid inputs",
                    "Clarify boundary conditions"
                ],
                related_requirements=[requirement.id],
                confidence=0.7
            ))
        
        return suggestions
    
    async def analyze_test_history(
        self,
        spec: TestSpecification,
        results: List[PropertyTestResult]
    ) -> TestHistoryAnalysis:
        """
        Analyze test execution history for patterns.
        
        Args:
            spec: Test specification
            results: Historical test results
            
        Returns:
            TestHistoryAnalysis with optimization suggestions
        """
        if not results:
            return TestHistoryAnalysis(
                spec_id=spec.id,
                total_executions=0,
                pass_rate=0.0,
                common_failures=[],
                flaky_tests=[],
                slow_tests=[],
                optimization_opportunities=[]
            )
        
        # Calculate metrics
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        pass_rate = passed / total if total > 0 else 0
        
        # Group by test
        test_results: Dict[str, List[PropertyTestResult]] = {}
        for r in results:
            if r.test_id not in test_results:
                test_results[r.test_id] = []
            test_results[r.test_id].append(r)
        
        # Find flaky tests (sometimes pass, sometimes fail)
        flaky_tests = []
        for test_id, test_runs in test_results.items():
            if len(test_runs) >= 3:
                passes = sum(1 for r in test_runs if r.passed)
                if 0 < passes < len(test_runs):
                    flaky_tests.append(test_id)
        
        # Find slow tests
        slow_tests = []
        for test_id, test_runs in test_results.items():
            avg_time = sum(r.execution_time_seconds for r in test_runs) / len(test_runs)
            if avg_time > 60:  # More than 60 seconds
                slow_tests.append(test_id)
        
        # Find common failures
        common_failures = []
        failed_results = [r for r in results if not r.passed]
        if failed_results:
            # Group by error message
            error_groups: Dict[str, int] = {}
            for r in failed_results:
                msg = r.error_message or "Unknown error"
                error_groups[msg] = error_groups.get(msg, 0) + 1
            
            for msg, count in sorted(error_groups.items(), key=lambda x: -x[1])[:5]:
                common_failures.append({
                    "error_message": msg[:200],
                    "count": count,
                    "percentage": count / len(failed_results) * 100
                })
        
        # Generate optimization suggestions
        suggestions = []
        
        if flaky_tests:
            suggestions.append(AISuggestion(
                id=self._generate_suggestion_id(),
                type=SuggestionType.TEST_OPTIMIZATION,
                priority=SuggestionPriority.HIGH,
                title="Fix flaky tests",
                description=f"{len(flaky_tests)} test(s) show intermittent failures.",
                rationale="Flaky tests reduce confidence in the test suite.",
                action_items=[
                    "Review test isolation",
                    "Check for race conditions",
                    "Add deterministic seeds where appropriate"
                ],
                related_tests=flaky_tests[:5],
                confidence=0.9
            ))
        
        if slow_tests:
            suggestions.append(AISuggestion(
                id=self._generate_suggestion_id(),
                type=SuggestionType.TEST_OPTIMIZATION,
                priority=SuggestionPriority.MEDIUM,
                title="Optimize slow tests",
                description=f"{len(slow_tests)} test(s) take more than 60 seconds.",
                rationale="Slow tests increase feedback time and CI costs.",
                action_items=[
                    "Profile test execution",
                    "Consider reducing iteration count for slow tests",
                    "Optimize generators to avoid expensive computations"
                ],
                related_tests=slow_tests[:5],
                confidence=0.8
            ))
        
        return TestHistoryAnalysis(
            spec_id=spec.id,
            total_executions=total,
            pass_rate=pass_rate,
            common_failures=common_failures,
            flaky_tests=flaky_tests,
            slow_tests=slow_tests,
            optimization_opportunities=suggestions
        )
    
    async def get_best_practices(
        self,
        context: str = "general"
    ) -> List[AISuggestion]:
        """
        Get best practice recommendations.
        
        Args:
            context: Context for recommendations (general, kernel, bsp, etc.)
            
        Returns:
            List of best practice suggestions
        """
        suggestions = []
        
        # General best practices
        suggestions.append(AISuggestion(
            id=self._generate_suggestion_id(),
            type=SuggestionType.TEST_OPTIMIZATION,
            priority=SuggestionPriority.LOW,
            title="Use minimum 100 iterations",
            description="Property-based tests should run at least 100 iterations.",
            rationale="More iterations increase the chance of finding edge cases.",
            action_items=[
                "Set @settings(max_examples=100) or higher",
                "Consider 1000+ iterations for critical properties"
            ],
            confidence=1.0
        ))
        
        suggestions.append(AISuggestion(
            id=self._generate_suggestion_id(),
            type=SuggestionType.PROPERTY_SUGGESTION,
            priority=SuggestionPriority.LOW,
            title="Include round-trip properties",
            description="For any serialization, include encode/decode round-trip tests.",
            rationale="Round-trip properties catch data loss and corruption bugs.",
            action_items=[
                "Identify all serialization points",
                "Create decode(encode(x)) == x properties"
            ],
            confidence=1.0
        ))
        
        if context == "kernel":
            suggestions.append(AISuggestion(
                id=self._generate_suggestion_id(),
                type=SuggestionType.EDGE_CASE,
                priority=SuggestionPriority.HIGH,
                title="Test memory allocation failures",
                description="Kernel code should handle memory allocation failures gracefully.",
                rationale="Memory pressure is common in kernel environments.",
                action_items=[
                    "Add fault injection for kmalloc failures",
                    "Test error paths for ENOMEM",
                    "Verify cleanup on allocation failure"
                ],
                confidence=0.95
            ))
        
        return suggestions
