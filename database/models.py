"""SQLAlchemy ORM models for the database layer."""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from ai_generator.models import (
    TestType, TestStatus, RiskLevel, EnvironmentStatus,
    TestCase, TestResult, Environment, CoverageData, 
    FailureAnalysis, CodeAnalysis, HardwareConfig
)
from .connection import Base


class HardwareConfigModel(Base):
    """Database model for hardware configurations."""
    
    __tablename__ = "hardware_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    architecture = Column(String(50), nullable=False)
    cpu_model = Column(String(200), nullable=False)
    memory_mb = Column(Integer, nullable=False)
    storage_type = Column(String(50), default="ssd")
    peripherals = Column(JSON, default=list)
    is_virtual = Column(Boolean, default=True)
    emulator = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_cases = relationship("TestCaseModel", back_populates="hardware_config")
    environments = relationship("EnvironmentModel", back_populates="hardware_config")
    
    def to_domain_model(self) -> HardwareConfig:
        """Convert to domain model."""
        return HardwareConfig.from_dict({
            'architecture': self.architecture,
            'cpu_model': self.cpu_model,
            'memory_mb': self.memory_mb,
            'storage_type': self.storage_type,
            'peripherals': self.peripherals or [],
            'is_virtual': self.is_virtual,
            'emulator': self.emulator
        })
    
    @classmethod
    def from_domain_model(cls, config: HardwareConfig) -> 'HardwareConfigModel':
        """Create from domain model."""
        return cls(
            architecture=config.architecture,
            cpu_model=config.cpu_model,
            memory_mb=config.memory_mb,
            storage_type=config.storage_type,
            peripherals=[p.to_dict() for p in config.peripherals],
            is_virtual=config.is_virtual,
            emulator=config.emulator
        )


class TestCaseModel(Base):
    """Database model for test cases."""
    
    __tablename__ = "test_cases"
    
    id = Column(String(255), primary_key=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    test_type = Column(SQLEnum(TestType), nullable=False)
    target_subsystem = Column(String(200), nullable=False)
    code_paths = Column(JSON, default=list)
    execution_time_estimate = Column(Integer, default=60)
    hardware_config_id = Column(Integer, ForeignKey("hardware_configs.id"), nullable=True)
    test_script = Column(Text, default="")
    expected_outcome = Column(JSON, nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hardware_config = relationship("HardwareConfigModel", back_populates="test_cases")
    test_results = relationship("TestResultModel", back_populates="test_case")
    
    def to_domain_model(self) -> TestCase:
        """Convert to domain model."""
        hardware = self.hardware_config.to_domain_model() if self.hardware_config else None
        
        return TestCase.from_dict({
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'test_type': self.test_type.value,
            'target_subsystem': self.target_subsystem,
            'code_paths': self.code_paths or [],
            'execution_time_estimate': self.execution_time_estimate,
            'required_hardware': hardware.to_dict() if hardware else None,
            'test_script': self.test_script,
            'expected_outcome': self.expected_outcome,
            'metadata': self.metadata or {}
        })
    
    @classmethod
    def from_domain_model(cls, test_case: TestCase, hardware_config_id: Optional[int] = None) -> 'TestCaseModel':
        """Create from domain model."""
        return cls(
            id=test_case.id,
            name=test_case.name,
            description=test_case.description,
            test_type=test_case.test_type,
            target_subsystem=test_case.target_subsystem,
            code_paths=test_case.code_paths,
            execution_time_estimate=test_case.execution_time_estimate,
            hardware_config_id=hardware_config_id,
            test_script=test_case.test_script,
            expected_outcome=test_case.expected_outcome.to_dict() if test_case.expected_outcome else None,
            metadata=test_case.metadata
        )


class EnvironmentModel(Base):
    """Database model for test environments."""
    
    __tablename__ = "environments"
    
    id = Column(String(255), primary_key=True)
    hardware_config_id = Column(Integer, ForeignKey("hardware_configs.id"), nullable=False)
    status = Column(SQLEnum(EnvironmentStatus), default=EnvironmentStatus.IDLE)
    kernel_version = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    ssh_credentials = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    hardware_config = relationship("HardwareConfigModel", back_populates="environments")
    test_results = relationship("TestResultModel", back_populates="environment")
    
    def to_domain_model(self) -> Environment:
        """Convert to domain model."""
        return Environment.from_dict({
            'id': self.id,
            'config': self.hardware_config.to_domain_model().to_dict(),
            'status': self.status.value,
            'kernel_version': self.kernel_version,
            'ip_address': self.ip_address,
            'ssh_credentials': self.ssh_credentials,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat(),
            'metadata': self.metadata or {}
        })
    
    @classmethod
    def from_domain_model(cls, environment: Environment, hardware_config_id: int) -> 'EnvironmentModel':
        """Create from domain model."""
        return cls(
            id=environment.id,
            hardware_config_id=hardware_config_id,
            status=environment.status,
            kernel_version=environment.kernel_version,
            ip_address=environment.ip_address,
            ssh_credentials=environment.ssh_credentials.to_dict() if environment.ssh_credentials else None,
            created_at=environment.created_at,
            last_used=environment.last_used,
            metadata=environment.metadata
        )


class CoverageDataModel(Base):
    """Database model for coverage data."""
    
    __tablename__ = "coverage_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)
    line_coverage = Column(Float, default=0.0)
    branch_coverage = Column(Float, default=0.0)
    function_coverage = Column(Float, default=0.0)
    covered_lines = Column(JSON, default=list)
    uncovered_lines = Column(JSON, default=list)
    covered_branches = Column(JSON, default=list)
    uncovered_branches = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_result = relationship("TestResultModel", back_populates="coverage_data")
    
    def to_domain_model(self) -> CoverageData:
        """Convert to domain model."""
        return CoverageData.from_dict({
            'line_coverage': self.line_coverage,
            'branch_coverage': self.branch_coverage,
            'function_coverage': self.function_coverage,
            'covered_lines': self.covered_lines or [],
            'uncovered_lines': self.uncovered_lines or [],
            'covered_branches': self.covered_branches or [],
            'uncovered_branches': self.uncovered_branches or [],
            'metadata': self.metadata or {}
        })
    
    @classmethod
    def from_domain_model(cls, coverage: CoverageData, test_result_id: int) -> 'CoverageDataModel':
        """Create from domain model."""
        return cls(
            test_result_id=test_result_id,
            line_coverage=coverage.line_coverage,
            branch_coverage=coverage.branch_coverage,
            function_coverage=coverage.function_coverage,
            covered_lines=coverage.covered_lines,
            uncovered_lines=coverage.uncovered_lines,
            covered_branches=coverage.covered_branches,
            uncovered_branches=coverage.uncovered_branches,
            metadata=coverage.metadata
        )


class TestResultModel(Base):
    """Database model for test results."""
    
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_case_id = Column(String(255), ForeignKey("test_cases.id"), nullable=False)
    environment_id = Column(String(255), ForeignKey("environments.id"), nullable=False)
    status = Column(SQLEnum(TestStatus), nullable=False)
    execution_time = Column(Float, nullable=False)
    artifacts = Column(JSON, default=dict)
    failure_info = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_case = relationship("TestCaseModel", back_populates="test_results")
    environment = relationship("EnvironmentModel", back_populates="test_results")
    coverage_data = relationship("CoverageDataModel", back_populates="test_result", uselist=False)
    
    def to_domain_model(self) -> TestResult:
        """Convert to domain model."""
        coverage = self.coverage_data.to_domain_model() if self.coverage_data else None
        
        return TestResult.from_dict({
            'test_id': self.test_case_id,
            'status': self.status.value,
            'execution_time': self.execution_time,
            'environment': self.environment.to_domain_model().to_dict(),
            'artifacts': self.artifacts or {},
            'coverage_data': coverage.to_dict() if coverage else None,
            'failure_info': self.failure_info,
            'timestamp': self.timestamp.isoformat()
        })
    
    @classmethod
    def from_domain_model(cls, result: TestResult) -> 'TestResultModel':
        """Create from domain model."""
        return cls(
            test_case_id=result.test_id,
            environment_id=result.environment.id,
            status=result.status,
            execution_time=result.execution_time,
            artifacts=result.artifacts.to_dict(),
            failure_info=result.failure_info.to_dict() if result.failure_info else None,
            timestamp=result.timestamp
        )


class CodeAnalysisModel(Base):
    """Database model for code analysis results."""
    
    __tablename__ = "code_analyses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    commit_sha = Column(String(40), nullable=False, index=True)
    changed_files = Column(JSON, default=list)
    changed_functions = Column(JSON, default=list)
    affected_subsystems = Column(JSON, default=list)
    impact_score = Column(Float, default=0.0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    suggested_test_types = Column(JSON, default=list)
    related_tests = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_domain_model(self) -> CodeAnalysis:
        """Convert to domain model."""
        return CodeAnalysis.from_dict({
            'changed_files': self.changed_files or [],
            'changed_functions': self.changed_functions or [],
            'affected_subsystems': self.affected_subsystems or [],
            'impact_score': self.impact_score,
            'risk_level': self.risk_level.value,
            'suggested_test_types': self.suggested_test_types or [],
            'related_tests': self.related_tests or []
        })
    
    @classmethod
    def from_domain_model(cls, analysis: CodeAnalysis, commit_sha: str) -> 'CodeAnalysisModel':
        """Create from domain model."""
        return cls(
            commit_sha=commit_sha,
            changed_files=analysis.changed_files,
            changed_functions=[f.to_dict() for f in analysis.changed_functions],
            affected_subsystems=analysis.affected_subsystems,
            impact_score=analysis.impact_score,
            risk_level=analysis.risk_level,
            suggested_test_types=[t.value for t in analysis.suggested_test_types],
            related_tests=analysis.related_tests
        )


class FailureAnalysisModel(Base):
    """Database model for failure analysis results."""
    
    __tablename__ = "failure_analyses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    failure_id = Column(String(255), nullable=False, unique=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)
    root_cause = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    suspicious_commits = Column(JSON, default=list)
    error_pattern = Column(Text, default="")
    stack_trace = Column(Text, nullable=True)
    suggested_fixes = Column(JSON, default=list)
    related_failures = Column(JSON, default=list)
    reproducibility = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_result = relationship("TestResultModel")
    
    def to_domain_model(self) -> FailureAnalysis:
        """Convert to domain model."""
        return FailureAnalysis.from_dict({
            'failure_id': self.failure_id,
            'root_cause': self.root_cause,
            'confidence': self.confidence,
            'suspicious_commits': self.suspicious_commits or [],
            'error_pattern': self.error_pattern,
            'stack_trace': self.stack_trace,
            'suggested_fixes': self.suggested_fixes or [],
            'related_failures': self.related_failures or [],
            'reproducibility': self.reproducibility
        })
    
    @classmethod
    def from_domain_model(cls, analysis: FailureAnalysis, test_result_id: int) -> 'FailureAnalysisModel':
        """Create from domain model."""
        return cls(
            failure_id=analysis.failure_id,
            test_result_id=test_result_id,
            root_cause=analysis.root_cause,
            confidence=analysis.confidence,
            suspicious_commits=[c.to_dict() for c in analysis.suspicious_commits],
            error_pattern=analysis.error_pattern,
            stack_trace=analysis.stack_trace,
            suggested_fixes=[f.to_dict() for f in analysis.suggested_fixes],
            related_failures=analysis.related_failures,
            reproducibility=analysis.reproducibility
        )


class PerformanceBaselineModel(Base):
    """Database model for performance baselines."""
    
    __tablename__ = "performance_baselines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    kernel_version = Column(String(100), nullable=False)
    hardware_config_id = Column(Integer, ForeignKey("hardware_configs.id"), nullable=False)
    benchmark_name = Column(String(200), nullable=False)
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    hardware_config = relationship("HardwareConfigModel")
    
    # Composite index for efficient lookups
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )


class SecurityIssueModel(Base):
    """Database model for security issues."""
    
    __tablename__ = "security_issues"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(String(255), nullable=False, unique=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=True)
    issue_type = Column(String(100), nullable=False)  # buffer_overflow, use_after_free, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    exploitability = Column(String(20), nullable=False)  # none, low, medium, high
    cvss_score = Column(Float, nullable=True)
    description = Column(Text, nullable=False)
    location = Column(JSON, nullable=False)  # file, line, function
    proof_of_concept = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_result = relationship("TestResultModel")