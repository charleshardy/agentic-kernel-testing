"""Core data models for the Agentic AI Testing System."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import json


class TestType(str, Enum):
    """Types of tests that can be generated and executed."""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUZZ = "fuzz"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestStatus(str, Enum):
    """Status of a test execution."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    ERROR = "error"


class RiskLevel(str, Enum):
    """Risk level for code changes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EnvironmentStatus(str, Enum):
    """Status of a test execution environment."""
    IDLE = "idle"
    BUSY = "busy"
    PROVISIONING = "provisioning"
    ERROR = "error"


@dataclass
class Peripheral:
    """Hardware peripheral configuration."""
    name: str
    type: str
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Peripheral':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class HardwareConfig:
    """Hardware configuration for test execution."""
    architecture: str
    cpu_model: str
    memory_mb: int
    storage_type: str = "ssd"
    peripherals: List[Peripheral] = field(default_factory=list)
    is_virtual: bool = True
    emulator: Optional[str] = None
    
    def __post_init__(self):
        """Validate hardware configuration."""
        if self.memory_mb <= 0:
            raise ValueError("memory_mb must be positive")
        if self.architecture not in ["x86_64", "arm64", "riscv64", "arm"]:
            raise ValueError(f"Unsupported architecture: {self.architecture}")
        if self.is_virtual and not self.emulator:
            self.emulator = "qemu"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['peripherals'] = [p.to_dict() if hasattr(p, 'to_dict') else p for p in self.peripherals]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HardwareConfig':
        """Create from dictionary."""
        peripherals_data = data.pop('peripherals', [])
        peripherals = [Peripheral.from_dict(p) if isinstance(p, dict) else p for p in peripherals_data]
        return cls(**data, peripherals=peripherals)


@dataclass
class ExpectedOutcome:
    """Expected outcome of a test case."""
    should_pass: bool = True
    expected_return_code: Optional[int] = None
    expected_output_pattern: Optional[str] = None
    should_not_crash: bool = True
    max_execution_time: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpectedOutcome':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TestCase:
    """A test case to be executed."""
    id: str
    name: str
    description: str
    test_type: TestType
    target_subsystem: str
    code_paths: List[str] = field(default_factory=list)
    execution_time_estimate: int = 60
    required_hardware: Optional[HardwareConfig] = None
    test_script: str = ""
    expected_outcome: Optional[ExpectedOutcome] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate test case."""
        if not self.id:
            raise ValueError("Test case id cannot be empty")
        if not self.name:
            raise ValueError("Test case name cannot be empty")
        if self.execution_time_estimate <= 0:
            raise ValueError("execution_time_estimate must be positive")
        if isinstance(self.test_type, str):
            self.test_type = TestType(self.test_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['test_type'] = self.test_type.value
        if self.required_hardware:
            data['required_hardware'] = self.required_hardware.to_dict()
        if self.expected_outcome:
            data['expected_outcome'] = self.expected_outcome.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """Create from dictionary."""
        hw_data = data.pop('required_hardware', None)
        outcome_data = data.pop('expected_outcome', None)
        
        hardware = HardwareConfig.from_dict(hw_data) if hw_data else None
        outcome = ExpectedOutcome.from_dict(outcome_data) if outcome_data else None
        
        return cls(**data, required_hardware=hardware, expected_outcome=outcome)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestCase':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class ArtifactBundle:
    """Collection of artifacts from test execution."""
    logs: List[str] = field(default_factory=list)
    core_dumps: List[str] = field(default_factory=list)
    traces: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArtifactBundle':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CoverageData:
    """Code coverage data from test execution."""
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    function_coverage: float = 0.0
    covered_lines: List[str] = field(default_factory=list)
    uncovered_lines: List[str] = field(default_factory=list)
    covered_branches: List[str] = field(default_factory=list)
    uncovered_branches: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate coverage data."""
        for coverage in [self.line_coverage, self.branch_coverage, self.function_coverage]:
            if not 0.0 <= coverage <= 1.0:
                raise ValueError("Coverage values must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoverageData':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class FailureInfo:
    """Information about a test failure."""
    error_message: str
    stack_trace: Optional[str] = None
    exit_code: Optional[int] = None
    kernel_panic: bool = False
    timeout_occurred: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailureInfo':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Credentials:
    """SSH or other credentials for environment access."""
    username: str
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Credentials':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Environment:
    """Test execution environment."""
    id: str
    config: HardwareConfig
    status: EnvironmentStatus = EnvironmentStatus.IDLE
    kernel_version: Optional[str] = None
    ip_address: Optional[str] = None
    ssh_credentials: Optional[Credentials] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate environment."""
        if not self.id:
            raise ValueError("Environment id cannot be empty")
        if isinstance(self.status, str):
            self.status = EnvironmentStatus(self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['config'] = self.config.to_dict()
        data['created_at'] = self.created_at.isoformat()
        data['last_used'] = self.last_used.isoformat()
        if self.ssh_credentials:
            data['ssh_credentials'] = self.ssh_credentials.to_dict()
        data['metadata'] = self.metadata
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Environment':
        """Create from dictionary."""
        config_data = data.pop('config')
        creds_data = data.pop('ssh_credentials', None)
        created_at = datetime.fromisoformat(data.pop('created_at'))
        last_used = datetime.fromisoformat(data.pop('last_used'))
        metadata = data.pop('metadata', {})
        
        config = HardwareConfig.from_dict(config_data)
        creds = Credentials.from_dict(creds_data) if creds_data else None
        
        return cls(**data, config=config, ssh_credentials=creds, 
                   created_at=created_at, last_used=last_used, metadata=metadata)


@dataclass
class TestResult:
    """Result of a test execution."""
    test_id: str
    status: TestStatus
    execution_time: float
    environment: Environment
    artifacts: ArtifactBundle = field(default_factory=ArtifactBundle)
    coverage_data: Optional[CoverageData] = None
    failure_info: Optional[FailureInfo] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate test result."""
        if not self.test_id:
            raise ValueError("test_id cannot be empty")
        if self.execution_time < 0:
            raise ValueError("execution_time cannot be negative")
        if isinstance(self.status, str):
            self.status = TestStatus(self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['environment'] = self.environment.to_dict()
        data['artifacts'] = self.artifacts.to_dict()
        data['timestamp'] = self.timestamp.isoformat()
        if self.coverage_data:
            data['coverage_data'] = self.coverage_data.to_dict()
        if self.failure_info:
            data['failure_info'] = self.failure_info.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """Create from dictionary."""
        env_data = data.pop('environment')
        artifacts_data = data.pop('artifacts', {})
        coverage_data = data.pop('coverage_data', None)
        failure_data = data.pop('failure_info', None)
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        
        environment = Environment.from_dict(env_data)
        artifacts = ArtifactBundle.from_dict(artifacts_data)
        coverage = CoverageData.from_dict(coverage_data) if coverage_data else None
        failure = FailureInfo.from_dict(failure_data) if failure_data else None
        
        return cls(**data, environment=environment, artifacts=artifacts,
                   coverage_data=coverage, failure_info=failure, timestamp=timestamp)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestResult':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Function:
    """Representation of a function in code."""
    name: str
    file_path: str
    line_number: int
    signature: str = ""
    subsystem: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Function':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CodeAnalysis:
    """Analysis of code changes."""
    changed_files: List[str] = field(default_factory=list)
    changed_functions: List[Function] = field(default_factory=list)
    affected_subsystems: List[str] = field(default_factory=list)
    impact_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    suggested_test_types: List[TestType] = field(default_factory=list)
    related_tests: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate code analysis."""
        if not 0.0 <= self.impact_score <= 1.0:
            raise ValueError("impact_score must be between 0.0 and 1.0")
        if isinstance(self.risk_level, str):
            self.risk_level = RiskLevel(self.risk_level)
        self.suggested_test_types = [
            TestType(t) if isinstance(t, str) else t 
            for t in self.suggested_test_types
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['risk_level'] = self.risk_level.value
        data['suggested_test_types'] = [t.value for t in self.suggested_test_types]
        data['changed_functions'] = [f.to_dict() for f in self.changed_functions]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeAnalysis':
        """Create from dictionary."""
        functions_data = data.pop('changed_functions', [])
        functions = [Function.from_dict(f) for f in functions_data]
        return cls(**data, changed_functions=functions)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'CodeAnalysis':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))



@dataclass
class Commit:
    """Git commit information."""
    sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Commit':
        """Create from dictionary."""
        timestamp = datetime.fromisoformat(data.pop('timestamp'))
        return cls(**data, timestamp=timestamp)


@dataclass
class FixSuggestion:
    """Suggested fix for a failure."""
    description: str
    code_patch: Optional[str] = None
    confidence: float = 0.0
    rationale: str = ""
    
    def __post_init__(self):
        """Validate fix suggestion."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FixSuggestion':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class FailureAnalysis:
    """Analysis of a test failure."""
    failure_id: str
    root_cause: str
    confidence: float
    suspicious_commits: List[Commit] = field(default_factory=list)
    error_pattern: str = ""
    stack_trace: Optional[str] = None
    suggested_fixes: List[FixSuggestion] = field(default_factory=list)
    related_failures: List[str] = field(default_factory=list)
    reproducibility: float = 0.0
    
    def __post_init__(self):
        """Validate failure analysis."""
        if not self.failure_id:
            raise ValueError("failure_id cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not 0.0 <= self.reproducibility <= 1.0:
            raise ValueError("reproducibility must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['suspicious_commits'] = [c.to_dict() for c in self.suspicious_commits]
        data['suggested_fixes'] = [f.to_dict() for f in self.suggested_fixes]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailureAnalysis':
        """Create from dictionary."""
        commits_data = data.pop('suspicious_commits', [])
        fixes_data = data.pop('suggested_fixes', [])
        
        commits = [Commit.from_dict(c) for c in commits_data]
        fixes = [FixSuggestion.from_dict(f) for f in fixes_data]
        
        return cls(**data, suspicious_commits=commits, suggested_fixes=fixes)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FailureAnalysis':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
