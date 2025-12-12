"""API request and response models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from ai_generator.models import TestType, TestStatus, TestCase, TestResult, CodeAnalysis
from execution.hardware_config import HardwareConfig
from analysis.coverage_models import CoverageData
from analysis.performance_models import PerformanceMetric
from analysis.security_models import SecurityVulnerability


class TestStatusEnum(str, Enum):
    """Test status enumeration for API."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestTypeEnum(str, Enum):
    """Test type enumeration for API."""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class HardwareConfigRequest(BaseModel):
    """Request model for hardware configuration."""
    architecture: str = Field(..., description="CPU architecture (x86_64, arm64, riscv64)")
    cpu_model: str = Field(..., description="CPU model name")
    memory_gb: int = Field(..., ge=1, le=1024, description="Memory in GB")
    storage_gb: int = Field(..., ge=1, le=10240, description="Storage in GB")
    network_interfaces: List[str] = Field(default_factory=list, description="Network interface types")
    peripherals: List[Dict[str, Any]] = Field(default_factory=list, description="Peripheral devices")
    is_virtual: bool = Field(True, description="Whether this is a virtual environment")
    emulator: Optional[str] = Field(None, description="Emulator type (qemu, kvm, etc.)")


class HardwareConfigResponse(BaseModel):
    """Response model for hardware configuration."""
    id: int = Field(..., description="Configuration ID")
    architecture: str = Field(..., description="CPU architecture")
    cpu_model: str = Field(..., description="CPU model name")
    memory_gb: int = Field(..., description="Memory in GB")
    storage_gb: int = Field(..., description="Storage in GB")
    network_interfaces: List[str] = Field(..., description="Network interface types")
    peripherals: List[Dict[str, Any]] = Field(..., description="Peripheral devices")
    is_virtual: bool = Field(..., description="Whether this is a virtual environment")
    emulator: Optional[str] = Field(None, description="Emulator type")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TestCaseRequest(BaseModel):
    """Request model for creating test cases."""
    name: str = Field(..., min_length=1, max_length=500, description="Test case name")
    description: str = Field(..., min_length=1, description="Test case description")
    test_type: TestTypeEnum = Field(..., description="Type of test")
    target_subsystem: str = Field(..., min_length=1, max_length=200, description="Target kernel subsystem")
    code_paths: List[str] = Field(default_factory=list, description="Code paths to test")
    execution_time_estimate: int = Field(60, ge=1, le=3600, description="Estimated execution time in seconds")
    hardware_config_id: Optional[int] = Field(None, description="Required hardware configuration ID")
    test_script: str = Field("", description="Test script content")
    expected_outcome: Optional[Dict[str, Any]] = Field(None, description="Expected test outcome")


class TestCaseResponse(BaseModel):
    """Response model for test cases."""
    id: str = Field(..., description="Test case ID")
    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="Test case description")
    test_type: TestTypeEnum = Field(..., description="Type of test")
    target_subsystem: str = Field(..., description="Target kernel subsystem")
    code_paths: List[str] = Field(..., description="Code paths to test")
    execution_time_estimate: int = Field(..., description="Estimated execution time in seconds")
    hardware_config_id: Optional[int] = Field(None, description="Required hardware configuration ID")
    test_script: str = Field(..., description="Test script content")
    expected_outcome: Optional[Dict[str, Any]] = Field(None, description="Expected test outcome")
    test_metadata: Dict[str, Any] = Field(..., description="Test metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TestExecutionRequest(BaseModel):
    """Request model for test execution."""
    test_case_ids: List[str] = Field(..., min_items=1, description="List of test case IDs to execute")
    hardware_config_id: Optional[int] = Field(None, description="Override hardware configuration")
    priority: int = Field(5, ge=1, le=10, description="Execution priority (1=highest, 10=lowest)")
    timeout: int = Field(300, ge=30, le=3600, description="Execution timeout in seconds")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    tags: List[str] = Field(default_factory=list, description="Execution tags")


class TestResultResponse(BaseModel):
    """Response model for test results."""
    id: str = Field(..., description="Test result ID")
    test_case_id: str = Field(..., description="Test case ID")
    status: TestStatusEnum = Field(..., description="Test execution status")
    start_time: datetime = Field(..., description="Test start time")
    end_time: Optional[datetime] = Field(None, description="Test end time")
    duration: Optional[float] = Field(None, description="Test duration in seconds")
    exit_code: Optional[int] = Field(None, description="Test exit code")
    stdout: str = Field("", description="Standard output")
    stderr: str = Field("", description="Standard error")
    artifacts: List[str] = Field(default_factory=list, description="Generated artifacts")
    environment_id: Optional[int] = Field(None, description="Execution environment ID")
    hardware_config_id: Optional[int] = Field(None, description="Hardware configuration ID")
    coverage_data_id: Optional[str] = Field(None, description="Coverage data ID")
    performance_metrics: List[str] = Field(default_factory=list, description="Performance metric IDs")
    security_findings: List[str] = Field(default_factory=list, description="Security finding IDs")
    failure_reason: Optional[str] = Field(None, description="Failure reason if test failed")
    created_at: datetime = Field(..., description="Creation timestamp")


class CoverageDataResponse(BaseModel):
    """Response model for coverage data."""
    id: str = Field(..., description="Coverage data ID")
    test_result_id: str = Field(..., description="Associated test result ID")
    line_coverage: float = Field(..., ge=0.0, le=1.0, description="Line coverage percentage")
    branch_coverage: float = Field(..., ge=0.0, le=1.0, description="Branch coverage percentage")
    function_coverage: float = Field(..., ge=0.0, le=1.0, description="Function coverage percentage")
    covered_lines: List[int] = Field(..., description="List of covered line numbers")
    uncovered_lines: List[int] = Field(..., description="List of uncovered line numbers")
    covered_branches: List[Dict[str, Any]] = Field(..., description="Covered branch information")
    uncovered_branches: List[Dict[str, Any]] = Field(..., description="Uncovered branch information")
    coverage_metadata: Dict[str, Any] = Field(..., description="Coverage metadata")
    created_at: datetime = Field(..., description="Creation timestamp")


class PerformanceMetricResponse(BaseModel):
    """Response model for performance metrics."""
    id: str = Field(..., description="Performance metric ID")
    test_result_id: str = Field(..., description="Associated test result ID")
    hardware_config_id: int = Field(..., description="Hardware configuration ID")
    benchmark_name: str = Field(..., description="Benchmark name")
    metric_name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Metric unit")
    perf_metadata: Dict[str, Any] = Field(..., description="Performance metadata")
    created_at: datetime = Field(..., description="Creation timestamp")


class SecurityVulnerabilityResponse(BaseModel):
    """Response model for security vulnerabilities."""
    id: str = Field(..., description="Vulnerability ID")
    test_result_id: str = Field(..., description="Associated test result ID")
    vulnerability_type: str = Field(..., description="Type of vulnerability")
    severity: str = Field(..., description="Vulnerability severity")
    description: str = Field(..., description="Vulnerability description")
    affected_component: str = Field(..., description="Affected component")
    cve_id: Optional[str] = Field(None, description="CVE identifier if applicable")
    proof_of_concept: Optional[str] = Field(None, description="Proof of concept")
    remediation: Optional[str] = Field(None, description="Remediation steps")
    vuln_metadata: Dict[str, Any] = Field(..., description="Vulnerability metadata")
    created_at: datetime = Field(..., description="Creation timestamp")


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    diff_content: str = Field(..., min_length=1, description="Git diff content to analyze")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    branch_name: Optional[str] = Field(None, description="Branch name")
    commit_hash: Optional[str] = Field(None, description="Commit hash")
    analysis_options: Dict[str, Any] = Field(default_factory=dict, description="Analysis options")


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis."""
    id: str = Field(..., description="Analysis ID")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    branch_name: Optional[str] = Field(None, description="Branch name")
    commit_hash: Optional[str] = Field(None, description="Commit hash")
    changed_files: List[str] = Field(..., description="List of changed files")
    added_functions: List[str] = Field(..., description="List of added functions")
    modified_functions: List[str] = Field(..., description="List of modified functions")
    deleted_functions: List[str] = Field(..., description="List of deleted functions")
    affected_subsystems: List[str] = Field(..., description="List of affected subsystems")
    complexity_score: float = Field(..., ge=0.0, description="Code complexity score")
    risk_level: str = Field(..., description="Risk level assessment")
    suggested_tests: List[str] = Field(..., description="Suggested test types")
    created_at: datetime = Field(..., description="Creation timestamp")


class TestGenerationRequest(BaseModel):
    """Request model for test generation."""
    analysis_id: str = Field(..., description="Code analysis ID")
    test_types: List[TestTypeEnum] = Field(..., min_items=1, description="Types of tests to generate")
    target_coverage: float = Field(0.8, ge=0.0, le=1.0, description="Target coverage percentage")
    max_tests: int = Field(50, ge=1, le=1000, description="Maximum number of tests to generate")
    priority_subsystems: List[str] = Field(default_factory=list, description="Priority subsystems")
    generation_options: Dict[str, Any] = Field(default_factory=dict, description="Generation options")


class TestGenerationResponse(BaseModel):
    """Response model for test generation."""
    id: str = Field(..., description="Generation job ID")
    analysis_id: str = Field(..., description="Code analysis ID")
    generated_tests: List[TestCaseResponse] = Field(..., description="Generated test cases")
    generation_stats: Dict[str, Any] = Field(..., description="Generation statistics")
    created_at: datetime = Field(..., description="Creation timestamp")


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Check timestamp")
    components: Dict[str, str] = Field(..., description="Component status")
    uptime: float = Field(..., description="Service uptime in seconds")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class PaginatedResponse(BaseModel):
    """Generic paginated response model."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
