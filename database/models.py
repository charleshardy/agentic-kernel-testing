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

# Import enums directly to avoid circular imports
from enum import Enum

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
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'architecture': self.architecture,
            'cpu_model': self.cpu_model,
            'memory_mb': self.memory_mb,
            'storage_type': self.storage_type,
            'peripherals': self.peripherals or [],
            'is_virtual': self.is_virtual,
            'emulator': self.emulator,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


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
    test_metadata = Column(JSON, default=dict)
    
    # New fields for generation metadata and execution status
    generation_info = Column(JSON, nullable=True)  # Stores AI generation metadata
    execution_status = Column(String(50), default="never_run")  # never_run, running, completed, failed
    last_execution_at = Column(DateTime, nullable=True)
    tags = Column(JSON, default=list)  # For categorization and filtering
    is_favorite = Column(Boolean, default=False)  # User favorites
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hardware_config = relationship("HardwareConfigModel", back_populates="test_cases")
    test_results = relationship("TestResultModel", back_populates="test_case")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'test_type': self.test_type.value,
            'target_subsystem': self.target_subsystem,
            'code_paths': self.code_paths or [],
            'execution_time_estimate': self.execution_time_estimate,
            'hardware_config': self.hardware_config.to_dict() if self.hardware_config else None,
            'test_script': self.test_script,
            'expected_outcome': self.expected_outcome,
            'metadata': self.test_metadata or {},
            'generation_info': self.generation_info,
            'execution_status': self.execution_status,
            'last_execution_at': self.last_execution_at.isoformat() if self.last_execution_at else None,
            'tags': self.tags or [],
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


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
    env_metadata = Column(JSON, default=dict)
    
    # Relationships
    hardware_config = relationship("HardwareConfigModel", back_populates="environments")
    test_results = relationship("TestResultModel", back_populates="environment")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'hardware_config': self.hardware_config.to_dict() if self.hardware_config else None,
            'status': self.status.value,
            'kernel_version': self.kernel_version,
            'ip_address': self.ip_address,
            'ssh_credentials': self.ssh_credentials,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'metadata': self.env_metadata or {}
        }


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
    coverage_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_result = relationship("TestResultModel", back_populates="coverage_data")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'test_result_id': self.test_result_id,
            'line_coverage': self.line_coverage,
            'branch_coverage': self.branch_coverage,
            'function_coverage': self.function_coverage,
            'covered_lines': self.covered_lines or [],
            'uncovered_lines': self.uncovered_lines or [],
            'covered_branches': self.covered_branches or [],
            'uncovered_branches': self.uncovered_branches or [],
            'metadata': self.coverage_metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


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
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'test_case_id': self.test_case_id,
            'environment_id': self.environment_id,
            'status': self.status.value,
            'execution_time': self.execution_time,
            'environment': self.environment.to_dict() if self.environment else None,
            'test_case': self.test_case.to_dict() if self.test_case else None,
            'artifacts': self.artifacts or {},
            'coverage_data': self.coverage_data.to_dict() if self.coverage_data else None,
            'failure_info': self.failure_info,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


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
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'commit_sha': self.commit_sha,
            'changed_files': self.changed_files or [],
            'changed_functions': self.changed_functions or [],
            'affected_subsystems': self.affected_subsystems or [],
            'impact_score': self.impact_score,
            'risk_level': self.risk_level.value,
            'suggested_test_types': self.suggested_test_types or [],
            'related_tests': self.related_tests or [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


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
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'failure_id': self.failure_id,
            'test_result_id': self.test_result_id,
            'root_cause': self.root_cause,
            'confidence': self.confidence,
            'suspicious_commits': self.suspicious_commits or [],
            'error_pattern': self.error_pattern,
            'stack_trace': self.stack_trace,
            'suggested_fixes': self.suggested_fixes or [],
            'related_failures': self.related_failures or [],
            'reproducibility': self.reproducibility,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


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
    perf_metadata = Column(JSON, default=dict)
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
    vuln_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_result = relationship("TestResultModel")