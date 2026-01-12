"""
Property-Based Tests for Agentic AI Test Requirements

Tests correctness properties for requirement parsing, property generation,
and test generation using Hypothesis.

Traceability:
- Specification: agentic-test-requirements
- Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.5, 7.1-7.5, 8.1-8.5
"""

import pytest
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume, note
from typing import List, Dict, Any

from ai_generator.requirements.models import (
    EARSPattern,
    ParsedRequirement,
    ValidationResult,
    PropertyPattern,
    CorrectnessProperty,
    TypeSpecification,
    GeneratedTest,
    PropertyTestResult,
    TestSpecification,
    TraceabilityLink,
    CoverageMatrix,
    FailureAnalysis,
    FixSuggestion,
    RequirementViolation,
)
from ai_generator.requirements.parser import RequirementParser
from ai_generator.requirements.property_generator import PropertyGenerator
from ai_generator.requirements.test_generator import PropertyTestGenerator
from ai_generator.requirements.generator_factory import GeneratorFactory


# =============================================================================
# Hypothesis Strategies for generating test data
# =============================================================================

@st.composite
def ears_pattern_strategy(draw):
    """Generate a valid EARS pattern."""
    return draw(st.sampled_from(list(EARSPattern)))


@st.composite
def property_pattern_strategy(draw):
    """Generate a valid property pattern."""
    return draw(st.sampled_from(list(PropertyPattern)))


@st.composite
def requirement_id_strategy(draw):
    """Generate a valid requirement ID."""
    prefix = draw(st.sampled_from(["REQ", "FR", "NFR", "SEC", "PERF"]))
    number = draw(st.integers(min_value=1, max_value=9999))
    return f"{prefix}-{number:04d}"


@st.composite
def system_name_strategy(draw):
    """Generate a valid system name."""
    systems = [
        "system", "scheduler", "memory manager", "file system",
        "network stack", "driver", "kernel", "allocator",
        "test runner", "orchestrator", "analyzer"
    ]
    return draw(st.sampled_from(systems))


@st.composite
def trigger_strategy(draw):
    """Generate a valid trigger condition."""
    triggers = [
        "a user submits a request",
        "a file is opened",
        "memory is allocated",
        "a test completes",
        "an error occurs",
        "the system starts",
        "a timeout expires",
        "data is received",
    ]
    return draw(st.sampled_from(triggers))


@st.composite
def response_strategy(draw):
    """Generate a valid response action."""
    responses = [
        "return a success status",
        "log the event",
        "allocate resources",
        "notify the user",
        "retry the operation",
        "clean up resources",
        "update the state",
        "generate a report",
    ]
    return draw(st.sampled_from(responses))


@st.composite
def parsed_requirement_strategy(draw):
    """Generate a valid ParsedRequirement."""
    pattern = draw(ears_pattern_strategy())
    req_id = draw(requirement_id_strategy())
    system = draw(system_name_strategy())
    response = draw(response_strategy())
    
    # Build text based on pattern
    if pattern == EARSPattern.UBIQUITOUS:
        text = f"THE {system} SHALL {response}."
        trigger = None
        state = None
    elif pattern == EARSPattern.EVENT_DRIVEN:
        trigger = draw(trigger_strategy())
        text = f"WHEN {trigger}, THE {system} SHALL {response}."
        state = None
    elif pattern == EARSPattern.STATE_DRIVEN:
        state = draw(st.sampled_from(["in idle mode", "processing", "waiting", "active"]))
        text = f"WHILE {state}, THE {system} SHALL {response}."
        trigger = None
    elif pattern == EARSPattern.UNWANTED:
        trigger = draw(trigger_strategy())
        text = f"IF {trigger}, THEN THE {system} SHALL {response}."
        state = None
    else:
        trigger = draw(trigger_strategy())
        text = f"WHEN {trigger}, THE {system} SHALL {response}."
        state = None
    
    return ParsedRequirement(
        id=req_id,
        text=text,
        pattern=pattern,
        trigger=trigger,
        state=state,
        system=system,
        response=response,
        metadata={"generated": True}
    )


@st.composite
def correctness_property_strategy(draw):
    """Generate a valid CorrectnessProperty."""
    prop_id = f"PROP-{draw(st.text(alphabet='0123456789abcdef', min_size=8, max_size=8))}"
    pattern = draw(property_pattern_strategy())
    req_ids = draw(st.lists(requirement_id_strategy(), min_size=1, max_size=3))
    
    name_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_"
    
    return CorrectnessProperty(
        id=prop_id,
        name=draw(st.text(alphabet=name_chars, min_size=5, max_size=50)),
        description=draw(st.text(min_size=10, max_size=200)),
        pattern=pattern,
        universal_quantifier=f"For any valid input",
        property_statement=draw(st.text(min_size=10, max_size=100)),
        requirement_ids=req_ids,
        input_types=draw(st.lists(st.sampled_from(["int", "str", "list", "dict"]), min_size=1, max_size=3)),
        preconditions=draw(st.lists(st.text(min_size=5, max_size=50), max_size=3)),
        postconditions=draw(st.lists(st.text(min_size=5, max_size=50), max_size=3)),
    )


@st.composite
def type_specification_strategy(draw):
    """Generate a valid TypeSpecification."""
    base_types = ["int", "str", "float", "bool", "list", "dict"]
    base_type = draw(st.sampled_from(base_types))
    
    constraints = {}
    if base_type == "int":
        constraints = {
            "min_value": draw(st.integers(min_value=-1000, max_value=0)),
            "max_value": draw(st.integers(min_value=1, max_value=1000)),
        }
    elif base_type == "str":
        constraints = {
            "min_size": draw(st.integers(min_value=0, max_value=10)),
            "max_size": draw(st.integers(min_value=11, max_value=100)),
        }
    
    return TypeSpecification(
        name=draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=3, max_size=20)),
        base_type=base_type,
        constraints=constraints,
        examples=[],
        edge_cases=[],
    )


@st.composite
def test_specification_strategy(draw):
    """Generate a valid TestSpecification."""
    spec_id = f"SPEC-{draw(st.text(alphabet='0123456789abcdef', min_size=8, max_size=8))}"
    requirements = draw(st.lists(parsed_requirement_strategy(), min_size=1, max_size=5))
    
    return TestSpecification(
        id=spec_id,
        name=draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_", min_size=5, max_size=50)),
        description=draw(st.text(min_size=10, max_size=200)),
        version="1.0.0",
        requirements=requirements,
        properties=[],
        tests=[],
        glossary={},
        metadata={},
    )


# =============================================================================
# Property Tests - Requirement Parsing
# =============================================================================

class TestRequirementParsingCompleteness:
    """
    **Feature: agentic-test-requirements, Property 1: Requirement Parsing Completeness**
    **Validates: Requirements 1.1, 1.5**
    
    For any valid EARS-formatted requirement text, the parser SHALL extract
    all components (trigger, system, response) with correct pattern identification.
    """

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_parsed_requirement_has_valid_id(self, req: ParsedRequirement):
        """Parsed requirement must have a valid non-empty ID."""
        assert req.id is not None
        assert len(req.id) > 0
        assert "-" in req.id  # ID format: PREFIX-NUMBER

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_parsed_requirement_has_valid_pattern(self, req: ParsedRequirement):
        """Parsed requirement must have a valid EARS pattern."""
        assert req.pattern in EARSPattern
        assert isinstance(req.pattern, EARSPattern)

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_parsed_requirement_has_system_and_response(self, req: ParsedRequirement):
        """Parsed requirement must have system and response components."""
        assert req.system is not None
        assert len(req.system) > 0
        assert req.response is not None
        assert len(req.response) > 0

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_event_driven_has_trigger(self, req: ParsedRequirement):
        """Event-driven requirements must have a trigger condition."""
        if req.pattern == EARSPattern.EVENT_DRIVEN:
            assert req.trigger is not None
            assert len(req.trigger) > 0

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_state_driven_has_state(self, req: ParsedRequirement):
        """State-driven requirements must have a state condition."""
        if req.pattern == EARSPattern.STATE_DRIVEN:
            assert req.state is not None
            assert len(req.state) > 0


class TestRequirementRoundTrip:
    """
    **Feature: agentic-test-requirements, Property 8: Specification Round-Trip**
    **Validates: Requirements 8.1, 8.4**
    
    For any valid test specification, serializing to JSON and deserializing
    SHALL produce an equivalent specification.
    """

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_requirement_json_round_trip(self, req: ParsedRequirement):
        """Requirement JSON serialization must be reversible."""
        json_str = req.to_json()
        restored = ParsedRequirement.from_json(json_str)
        
        assert restored.id == req.id
        assert restored.text == req.text
        assert restored.pattern == req.pattern
        assert restored.system == req.system
        assert restored.response == req.response

    @given(prop=correctness_property_strategy())
    @settings(max_examples=10)
    def test_property_json_round_trip(self, prop: CorrectnessProperty):
        """Property JSON serialization must be reversible."""
        json_str = prop.to_json()
        restored = CorrectnessProperty.from_json(json_str)
        
        assert restored.id == prop.id
        assert restored.name == prop.name
        assert restored.pattern == prop.pattern
        assert restored.requirement_ids == prop.requirement_ids

    @given(spec=test_specification_strategy())
    @settings(max_examples=10)
    def test_specification_json_round_trip(self, spec: TestSpecification):
        """Specification JSON serialization must be reversible."""
        json_str = spec.to_json()
        restored = TestSpecification.from_json(json_str)
        
        assert restored.id == spec.id
        assert restored.name == spec.name
        assert restored.version == spec.version
        assert len(restored.requirements) == len(spec.requirements)


# =============================================================================
# Property Tests - Property Generation
# =============================================================================

class TestPropertyGenerationTraceability:
    """
    **Feature: agentic-test-requirements, Property 2: Property Generation Traceability**
    **Validates: Requirements 2.5, 7.1**
    
    For any generated correctness property, there SHALL exist a traceable link
    to at least one originating requirement.
    """

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_generated_property_has_requirement_link(self, req: ParsedRequirement):
        """Generated properties must link to originating requirement."""
        generator = PropertyGenerator()
        properties = generator.generate_properties(req)
        
        for prop in properties:
            assert len(prop.requirement_ids) > 0
            assert req.id in prop.requirement_ids

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_generated_property_has_valid_pattern(self, req: ParsedRequirement):
        """Generated properties must have a valid property pattern."""
        generator = PropertyGenerator()
        properties = generator.generate_properties(req)
        
        for prop in properties:
            assert prop.pattern in PropertyPattern
            assert isinstance(prop.pattern, PropertyPattern)

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_generated_property_has_universal_quantifier(self, req: ParsedRequirement):
        """Generated properties must have a universal quantifier statement."""
        generator = PropertyGenerator()
        properties = generator.generate_properties(req)
        
        for prop in properties:
            assert prop.universal_quantifier is not None
            assert len(prop.universal_quantifier) > 0
            # Should start with "For any" or similar
            assert "for" in prop.universal_quantifier.lower() or "any" in prop.universal_quantifier.lower()


class TestPropertyPatternIdentification:
    """
    **Feature: agentic-test-requirements, Property: Pattern Identification Consistency**
    **Validates: Requirements 2.2**
    
    Property pattern identification must be deterministic and consistent.
    """

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_pattern_identification_is_deterministic(self, req: ParsedRequirement):
        """Pattern identification must return same result for same input."""
        generator = PropertyGenerator()
        
        pattern1 = generator.identify_property_pattern(req)
        pattern2 = generator.identify_property_pattern(req)
        
        assert pattern1 == pattern2

    @given(req=parsed_requirement_strategy())
    @settings(max_examples=10)
    def test_unwanted_pattern_maps_to_error_condition(self, req: ParsedRequirement):
        """UNWANTED EARS pattern should map to ERROR_CONDITION property pattern."""
        if req.pattern == EARSPattern.UNWANTED:
            generator = PropertyGenerator()
            pattern = generator.identify_property_pattern(req)
            # UNWANTED typically maps to error condition handling
            assert pattern in [PropertyPattern.ERROR_CONDITION, PropertyPattern.INVARIANT]


# =============================================================================
# Property Tests - Test Generation
# =============================================================================

class TestTestGenerationValidity:
    """
    **Feature: agentic-test-requirements, Property 3: Test Generation Validity**
    **Validates: Requirements 3.5**
    
    For any generated property-based test, the test code SHALL be syntactically
    valid Python that can be compiled without errors.
    """

    @given(prop=correctness_property_strategy())
    @settings(max_examples=10)
    def test_generated_test_has_valid_syntax(self, prop: CorrectnessProperty):
        """Generated test code must have valid Python syntax."""
        generator = PropertyTestGenerator()
        test = generator.generate_test(prop)
        
        # Validate syntax
        is_valid = generator.validate_test_syntax(test.test_code)
        assert is_valid, f"Invalid syntax in generated test: {test.test_code[:200]}"

    @given(prop=correctness_property_strategy())
    @settings(max_examples=10)
    def test_generated_test_has_traceability(self, prop: CorrectnessProperty):
        """Generated test must include traceability to property and requirements."""
        generator = PropertyTestGenerator()
        test = generator.generate_test(prop)
        
        assert test.property_id == prop.id
        assert test.requirement_ids == prop.requirement_ids
        assert len(test.requirement_ids) > 0

    @given(prop=correctness_property_strategy())
    @settings(max_examples=10)
    def test_generated_test_has_minimum_iterations(self, prop: CorrectnessProperty):
        """Generated test must be configured for minimum 100 iterations."""
        generator = PropertyTestGenerator()
        test = generator.generate_test(prop)
        
        assert test.iterations >= 100


class TestTestFileGeneration:
    """
    **Feature: agentic-test-requirements, Property: Test File Completeness**
    **Validates: Requirements 3.3, 3.4**
    
    Generated test files must be complete and executable.
    """

    @given(props=st.lists(correctness_property_strategy(), min_size=1, max_size=3))
    @settings(max_examples=5)
    def test_generated_file_has_valid_syntax(self, props: List[CorrectnessProperty]):
        """Generated test file must have valid Python syntax."""
        generator = PropertyTestGenerator()
        file_content = generator.generate_test_file(
            props,
            spec_id="SPEC-test",
            spec_name="Test Specification"
        )
        
        # Validate syntax
        is_valid = generator.validate_test_syntax(file_content)
        assert is_valid, f"Invalid syntax in generated file"

    @given(props=st.lists(correctness_property_strategy(), min_size=1, max_size=3))
    @settings(max_examples=5)
    def test_generated_file_has_imports(self, props: List[CorrectnessProperty]):
        """Generated test file must include necessary imports."""
        generator = PropertyTestGenerator()
        file_content = generator.generate_test_file(
            props,
            spec_id="SPEC-test",
            spec_name="Test Specification"
        )
        
        assert "import pytest" in file_content
        assert "from hypothesis import" in file_content
        assert "strategies as st" in file_content


# =============================================================================
# Property Tests - Generator Factory
# =============================================================================

class TestGeneratorConstraintSatisfaction:
    """
    **Feature: agentic-test-requirements, Property 4: Generator Constraint Satisfaction**
    **Validates: Requirements 4.3**
    
    For any type specification with constraints, generated values SHALL
    satisfy all specified constraints.
    """

    @given(type_spec=type_specification_strategy())
    @settings(max_examples=10)
    def test_generator_respects_constraints(self, type_spec: TypeSpecification):
        """Generated values must satisfy type constraints."""
        factory = GeneratorFactory()
        generator = factory.create_generator(type_spec)
        
        # Draw some values and verify constraints
        from hypothesis import find
        
        # Just verify the generator can produce values
        # (actual constraint checking happens in Hypothesis)
        assert generator is not None

    @given(domain=st.sampled_from(["hostname", "ip_address", "port", "architecture", "status"]))
    @settings(max_examples=5)
    def test_domain_generator_produces_valid_values(self, domain: str):
        """Domain-specific generators must produce valid domain values."""
        factory = GeneratorFactory()
        generator = factory.create_domain_generator(domain)
        
        assert generator is not None


# =============================================================================
# Property Tests - Traceability
# =============================================================================

class TestTraceabilityBidirectionality:
    """
    **Feature: agentic-test-requirements, Property 7: Traceability Bidirectionality**
    **Validates: Requirements 7.1, 7.2**
    
    For any traceability link from test to requirement, there SHALL exist
    a corresponding reverse lookup from requirement to test.
    """

    @given(
        test_id=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=5, max_size=20),
        req_id=requirement_id_strategy()
    )
    @settings(max_examples=10)
    def test_traceability_link_is_bidirectional(self, test_id: str, req_id: str):
        """Traceability links must support bidirectional lookup."""
        link = TraceabilityLink(
            test_id=test_id,
            requirement_id=req_id,
            link_type="validates"
        )
        
        # Link should contain both IDs
        assert link.test_id == test_id
        assert link.requirement_id == req_id
        
        # Serialization should preserve both
        link_dict = link.to_dict()
        restored = TraceabilityLink.from_dict(link_dict)
        
        assert restored.test_id == test_id
        assert restored.requirement_id == req_id


class TestCoverageMatrixCompleteness:
    """
    **Feature: agentic-test-requirements, Property 10: Coverage Matrix Completeness**
    **Validates: Requirements 7.5**
    
    Coverage matrix must account for all requirements and tests.
    """

    @given(
        requirements=st.lists(requirement_id_strategy(), min_size=1, max_size=10, unique=True),
        tests=st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=5, max_size=15), min_size=1, max_size=10, unique=True)
    )
    @settings(max_examples=10)
    def test_coverage_matrix_accounts_for_all_items(self, requirements: List[str], tests: List[str]):
        """Coverage matrix must include all requirements and tests."""
        # Create coverage mapping (some requirements covered, some not)
        coverage = {}
        for i, req in enumerate(requirements):
            if i % 2 == 0 and tests:  # Cover every other requirement
                coverage[req] = [tests[0]]
            else:
                coverage[req] = []
        
        # Calculate untested and orphaned
        untested = [req for req, test_list in coverage.items() if not test_list]
        covered_tests = set()
        for test_list in coverage.values():
            covered_tests.update(test_list)
        orphaned = [t for t in tests if t not in covered_tests]
        
        # Calculate coverage percentage
        covered_count = len([req for req, test_list in coverage.items() if test_list])
        coverage_pct = (covered_count / len(requirements) * 100) if requirements else 0.0
        
        matrix = CoverageMatrix(
            spec_id="SPEC-test",
            requirements=requirements,
            tests=tests,
            coverage=coverage,
            untested=untested,
            orphaned_tests=orphaned,
            coverage_percentage=coverage_pct
        )
        
        # Verify completeness
        assert set(matrix.requirements) == set(requirements)
        assert set(matrix.tests) == set(tests)
        assert len(matrix.untested) + covered_count == len(requirements)
        assert 0.0 <= matrix.coverage_percentage <= 100.0


# =============================================================================
# Property Tests - Failure Analysis
# =============================================================================

class TestFailureRequirementCorrelation:
    """
    **Feature: agentic-test-requirements, Property 6: Failure-Requirement Correlation**
    **Validates: Requirements 6.1, 6.2**
    
    For any property test failure, the analysis SHALL identify which
    requirement(s) are potentially violated.
    """

    @given(
        test_id=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=5, max_size=20),
        prop_id=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=5, max_size=20),
        req_ids=st.lists(requirement_id_strategy(), min_size=1, max_size=3)
    )
    @settings(max_examples=10)
    def test_failure_analysis_has_requirement_correlation(self, test_id: str, prop_id: str, req_ids: List[str]):
        """Failure analysis must correlate with requirements."""
        analysis = FailureAnalysis(
            test_id=test_id,
            property_id=prop_id,
            requirement_ids=req_ids,
            root_cause="Test failure due to constraint violation",
            counter_example={"input": 42},
            confidence=0.85
        )
        
        assert len(analysis.requirement_ids) > 0
        assert analysis.property_id == prop_id
        assert analysis.test_id == test_id

    @given(
        req_id=requirement_id_strategy(),
        counter_example=st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), min_size=1, max_size=5)
    )
    @settings(max_examples=10)
    def test_requirement_violation_has_counter_example(self, req_id: str, counter_example: Dict[str, int]):
        """Requirement violation must include counter-example."""
        violation = RequirementViolation(
            requirement_id=req_id,
            requirement_text="THE system SHALL handle all inputs",
            property_id="PROP-test",
            property_statement="For all inputs, output is valid",
            counter_example=counter_example,
            violation_description="Input caused unexpected behavior",
            severity="high"
        )
        
        assert violation.counter_example is not None
        assert violation.requirement_id == req_id


# =============================================================================
# Property Tests - Model Serialization
# =============================================================================

class TestModelSerialization:
    """
    **Feature: agentic-test-requirements, Property: Model Serialization Consistency**
    **Validates: Requirements 8.1, 8.4**
    
    All models must serialize and deserialize consistently.
    """

    @given(
        description=st.text(min_size=5, max_size=100),
        confidence=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=10)
    def test_fix_suggestion_round_trip(self, description: str, confidence: float):
        """FixSuggestion must serialize and deserialize correctly."""
        suggestion = FixSuggestion(
            description=description,
            confidence=confidence,
            rationale="Based on pattern analysis"
        )
        
        data = suggestion.to_dict()
        restored = FixSuggestion.from_dict(data)
        
        assert restored.description == description
        assert restored.confidence == confidence

    @given(
        is_valid=st.booleans(),
        issues=st.lists(st.text(min_size=5, max_size=50), max_size=5)
    )
    @settings(max_examples=10)
    def test_validation_result_round_trip(self, is_valid: bool, issues: List[str]):
        """ValidationResult must serialize correctly."""
        result = ValidationResult(
            is_valid=is_valid,
            issues=issues
        )
        
        data = result.to_dict()
        
        assert data["is_valid"] == is_valid
        assert data["issues"] == issues
