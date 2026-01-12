"""Data models for Agentic AI Test Requirements.

This module defines all data models used in the requirement-to-test workflow:
- Requirement parsing models (EARS patterns)
- Property generation models
- Test generation and execution models
- Traceability and analysis models
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import json


class EARSPattern(str, Enum):
    """EARS (Easy Approach to Requirements Syntax) patterns.
    
    These patterns provide structured templates for writing
    unambiguous, testable requirements.
    """
    UBIQUITOUS = "ubiquitous"      # THE system SHALL <response>
    EVENT_DRIVEN = "event_driven"  # WHEN <trigger>, THE system SHALL <response>
    STATE_DRIVEN = "state_driven"  # WHILE <state>, THE system SHALL <response>
    UNWANTED = "unwanted"          # IF <condition>, THEN THE system SHALL <response>
    OPTIONAL = "optional"          # WHERE <option>, THE system SHALL <response>
    COMPLEX = "complex"            # Combination of patterns


class PropertyPattern(str, Enum):
    """Common property-based testing patterns.
    
    These patterns represent different types of correctness properties
    that can be verified through property-based testing.
    """
    INVARIANT = "invariant"           # Property preserved after operation
    ROUND_TRIP = "round_trip"         # encode(decode(x)) == x
    IDEMPOTENCE = "idempotence"       # f(f(x)) == f(x)
    METAMORPHIC = "metamorphic"       # Relationship between inputs/outputs
    MODEL_BASED = "model_based"       # Compare with reference implementation
    CONFLUENCE = "confluence"         # Order independence
    ERROR_CONDITION = "error"         # Error handling verification


@dataclass
class ParsedRequirement:
    """A parsed EARS requirement.
    
    Represents a requirement that has been parsed from EARS format
    into its constituent components.
    """
    id: str
    text: str
    pattern: EARSPattern
    trigger: Optional[str] = None      # WHEN/IF condition
    state: Optional[str] = None        # WHILE condition
    system: str = ""                   # System name
    response: str = ""                 # SHALL response
    options: Optional[str] = None      # WHERE option
    user_story: Optional[str] = None   # Associated user story
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['pattern'] = self.pattern.value
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedRequirement':
        """Create from dictionary."""
        data['pattern'] = EARSPattern(data['pattern'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ParsedRequirement':
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class ValidationResult:
    """Result of requirement validation.
    
    Contains information about validation issues, suggestions,
    and identified problems with a requirement.
    """
    is_valid: bool
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)
    undefined_terms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DependencyGraph:
    """Graph of requirement dependencies.
    
    Represents relationships between requirements.
    """
    nodes: List[str] = field(default_factory=list)  # Requirement IDs
    edges: List[tuple] = field(default_factory=list)  # (from_id, to_id, relationship)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypeSpecification:
    """Specification for a type used in property tests.
    
    Defines how to generate test data for a specific type,
    including constraints and edge cases.
    """
    name: str
    base_type: str  # int, str, list, dict, custom
    constraints: Dict[str, Any] = field(default_factory=dict)
    examples: List[Any] = field(default_factory=list)
    edge_cases: List[Any] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypeSpecification':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CorrectnessProperty:
    """A correctness property derived from a requirement.
    
    Represents a universally quantified property that should
    hold for all valid inputs to the system.
    """
    id: str
    name: str
    description: str
    pattern: PropertyPattern
    universal_quantifier: str  # "For all X..."
    property_statement: str    # The actual property
    requirement_ids: List[str] = field(default_factory=list)
    input_types: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['pattern'] = self.pattern.value
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CorrectnessProperty':
        """Create from dictionary."""
        data['pattern'] = PropertyPattern(data['pattern'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CorrectnessProperty':
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class GeneratedTest:
    """A generated property-based test.
    
    Contains the test code, metadata, and traceability information
    for a property-based test generated from a correctness property.
    """
    id: str
    name: str
    property_id: str
    requirement_ids: List[str]
    test_code: str
    generators: List[str] = field(default_factory=list)  # Generator strategy names
    iterations: int = 100
    timeout_seconds: int = 300
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeneratedTest':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GeneratedTest':
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class PropertyTestResult:
    """Result of a property test execution.
    
    Contains pass/fail status, counter-examples, and execution metadata.
    """
    test_id: str
    property_id: str
    requirement_ids: List[str]
    passed: bool
    iterations_run: int
    counter_example: Optional[Any] = None
    shrunk_example: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    environment_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PropertyTestResult':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ExecutionConfig:
    """Configuration for test execution.
    
    Specifies how property tests should be executed.
    """
    iterations: int = 100
    timeout_seconds: int = 300
    parallel: bool = True
    max_workers: int = 4
    environments: List[str] = field(default_factory=list)
    shrink_on_failure: bool = True
    verbose: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TestSpecification:
    """A complete test specification.
    
    Contains all requirements, properties, and tests for a feature,
    along with glossary and metadata.
    """
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    requirements: List[ParsedRequirement] = field(default_factory=list)
    properties: List[CorrectnessProperty] = field(default_factory=list)
    tests: List[GeneratedTest] = field(default_factory=list)
    glossary: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'requirements': [r.to_dict() for r in self.requirements],
            'properties': [p.to_dict() for p in self.properties],
            'tests': [t.to_dict() for t in self.tests],
            'glossary': self.glossary,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestSpecification':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            version=data.get('version', '1.0.0'),
            requirements=[ParsedRequirement.from_dict(r) for r in data.get('requirements', [])],
            properties=[CorrectnessProperty.from_dict(p) for p in data.get('properties', [])],
            tests=[GeneratedTest.from_dict(t) for t in data.get('tests', [])],
            glossary=data.get('glossary', {}),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestSpecification':
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class TraceabilityLink:
    """Link between test and requirement.
    
    Establishes traceability from tests back to requirements.
    """
    test_id: str
    requirement_id: str
    property_id: Optional[str] = None
    link_type: str = "validates"  # validates, partially_validates, related
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceabilityLink':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class CoverageMatrix:
    """Requirement coverage matrix.
    
    Shows which tests cover which requirements.
    """
    spec_id: str
    requirements: List[str]
    tests: List[str]
    coverage: Dict[str, List[str]]  # req_id -> [test_ids]
    untested: List[str]
    orphaned_tests: List[str]
    coverage_percentage: float
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoverageMatrix':
        """Create from dictionary."""
        data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)


@dataclass
class RequirementViolation:
    """A requirement violation from a test failure.
    
    Describes how a test failure relates to a specific requirement.
    """
    requirement_id: str
    requirement_text: str
    property_id: str
    property_statement: str
    counter_example: Any
    violation_description: str
    severity: str = "high"  # low, medium, high, critical
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequirementViolation':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class FixSuggestion:
    """Suggested fix for a failure.
    
    Contains a description and optional code/requirement changes.
    """
    description: str
    code_change: Optional[str] = None
    requirement_change: Optional[str] = None
    confidence: float = 0.0
    rationale: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FixSuggestion':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class FailureAnalysis:
    """Analysis of a property test failure.
    
    Contains root cause analysis, counter-examples, and suggestions.
    """
    test_id: str
    property_id: str
    requirement_ids: List[str]
    root_cause: str
    counter_example: Any
    shrunk_example: Optional[Any] = None
    violation: Optional[RequirementViolation] = None
    related_failures: List[str] = field(default_factory=list)
    suggested_fixes: List[FixSuggestion] = field(default_factory=list)
    confidence: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'test_id': self.test_id,
            'property_id': self.property_id,
            'requirement_ids': self.requirement_ids,
            'root_cause': self.root_cause,
            'counter_example': self.counter_example,
            'shrunk_example': self.shrunk_example,
            'violation': self.violation.to_dict() if self.violation else None,
            'related_failures': self.related_failures,
            'suggested_fixes': [f.to_dict() for f in self.suggested_fixes],
            'confidence': self.confidence,
            'analyzed_at': self.analyzed_at.isoformat(),
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailureAnalysis':
        """Create from dictionary."""
        violation_data = data.pop('violation', None)
        fixes_data = data.pop('suggested_fixes', [])
        data['analyzed_at'] = datetime.fromisoformat(data['analyzed_at'])
        
        return cls(
            **data,
            violation=RequirementViolation.from_dict(violation_data) if violation_data else None,
            suggested_fixes=[FixSuggestion.from_dict(f) for f in fixes_data],
        )
