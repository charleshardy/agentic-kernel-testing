"""Agentic AI Test Requirements Module.

This module provides functionality for:
- Parsing EARS-formatted requirements
- Generating correctness properties
- Creating property-based tests with Hypothesis
- Orchestrating test execution
- Analyzing test failures
- Managing requirement-to-test traceability
- Managing test specifications
"""

from .models import (
    EARSPattern,
    ParsedRequirement,
    ValidationResult,
    DependencyGraph,
    PropertyPattern,
    CorrectnessProperty,
    TypeSpecification,
    GeneratedTest,
    PropertyTestResult,
    ExecutionConfig,
    TestSpecification,
    TraceabilityLink,
    CoverageMatrix,
    RequirementViolation,
    FailureAnalysis,
    FixSuggestion,
)

from .parser import RequirementParser
from .property_generator import PropertyGenerator
from .test_generator import PropertyTestGenerator
from .generator_factory import GeneratorFactory
from .orchestrator import (
    PropertyTestOrchestrator,
    ExecutionPlan,
    ExecutionResult,
    TestExecutionSummary,
    run_tests,
    run_single_test,
)
from .failure_analyzer import (
    PropertyFailureAnalyzer,
    analyze_test_failure,
    group_test_failures,
)
from .traceability_manager import (
    TraceabilityManager,
    create_traceability_link,
    generate_coverage_report,
)
from .specification_manager import (
    SpecificationManager,
    SpecificationUpdate,
    create_specification,
    load_specification,
)
from .ai_assistant import (
    AIAssistant,
    AISuggestion,
    SuggestionType,
    SuggestionPriority,
    CoverageAnalysis,
    TestHistoryAnalysis,
)

__all__ = [
    # Models
    "EARSPattern",
    "ParsedRequirement",
    "ValidationResult",
    "DependencyGraph",
    "PropertyPattern",
    "CorrectnessProperty",
    "TypeSpecification",
    "GeneratedTest",
    "PropertyTestResult",
    "ExecutionConfig",
    "TestSpecification",
    "TraceabilityLink",
    "CoverageMatrix",
    "RequirementViolation",
    "FailureAnalysis",
    "FixSuggestion",
    # Parser
    "RequirementParser",
    # Property Generator
    "PropertyGenerator",
    # Test Generator
    "PropertyTestGenerator",
    # Generator Factory
    "GeneratorFactory",
    # Orchestrator
    "PropertyTestOrchestrator",
    "ExecutionPlan",
    "ExecutionResult",
    "TestExecutionSummary",
    "run_tests",
    "run_single_test",
    # Failure Analyzer
    "PropertyFailureAnalyzer",
    "analyze_test_failure",
    "group_test_failures",
    # Traceability Manager
    "TraceabilityManager",
    "create_traceability_link",
    "generate_coverage_report",
    # Specification Manager
    "SpecificationManager",
    "SpecificationUpdate",
    "create_specification",
    "load_specification",
    # AI Assistant
    "AIAssistant",
    "AISuggestion",
    "SuggestionType",
    "SuggestionPriority",
    "CoverageAnalysis",
    "TestHistoryAnalysis",
]
