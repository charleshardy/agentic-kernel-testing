"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

from ai_generator.models import TestType, TestStatus, RiskLevel, EnvironmentStatus


class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    errors: Optional[List[str]] = Field(None, description="List of error messages")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response format."""
    success: bool = Field(False, description="Always false for errors")
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Number of items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="Sort order")


class HardwareConfigRequest(BaseModel):
    """Request model for hardware configuration."""
    architecture: str = Field(..., description="CPU architecture (x86_64, arm64, riscv64)")
    cpu_model: str = Field(..., description="CPU model name")
    memory_mb: int = Field(..., gt=0, description="Memory in MB")
    storage_type: str = Field("ssd", description="Storage type")
    peripherals: List[Dict[str, Any]] = Field(default_factory=list, description="Peripheral devices")
    is_virtual: bool = Field(True, description="Whether this is a virtual environment")
    emulator: Optional[str] = Field(None, description="Emulator type (qemu, kvm)")
    
    @validator('architecture')
    def validate_architecture(cls, v):
        valid_archs = ["x86_64", "arm64", "riscv64", "arm"]
        if v not in valid_archs:
            raise ValueError(f"Architecture must be one of: {valid_archs}")
        return v


class TestCaseRequest(BaseModel):
    """Request model for test case submission."""
    name: str = Field(..., min_length=1, max_length=500, description="Test case name")
    description: str = Field(..., min_length=1, description="Test case description")
    test_type: TestType = Field(..., description="Type of test")
    target_subsystem: str = Field(..., description="Target kernel subsystem")
    code_paths: List[str] = Field(default_factory=list, description="Code paths to test")
    execution_time_estimate: int = Field(60, gt=0, description="Estimated execution time in seconds")
    required_hardware: Optional[HardwareConfigRequest] = Field(None, description="Required hardware configuration")
    test_script: str = Field("", description="Test script content")
    expected_outcome: Optional[Dict[str, Any]] = Field(None, description="Expected test outcome")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    priority: int = Field(0, ge=0, le=10, description="Test priority (0=lowest, 10=highest)")


class TestCaseResponse(BaseModel):
    """Response model for test case."""
    id: str = Field(..., description="Unique test case ID")
    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="Test case description")
    test_type: TestType = Field(..., description="Type of test")
    target_subsystem: str = Field(..., description="Target kernel subsystem")
    code_paths: List[str] = Field(..., description="Code paths to test")
    execution_time_estimate: int = Field(..., description="Estimated execution time in seconds")
    required_hardware: Optional[Dict[str, Any]] = Field(None, description="Required hardware configuration")
    test_script: str = Field(..., description="Test script content")
    expected_outcome: Optional[Dict[str, Any]] = Field(None, description="Expected test outcome")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TestSubmissionRequest(BaseModel):
    """Request model for test submission."""
    test_cases: List[TestCaseRequest] = Field(..., min_items=1, description="List of test cases to submit")
    priority: int = Field(0, ge=0, le=10, description="Overall submission priority")
    target_environments: Optional[List[str]] = Field(None, description="Specific environment IDs to target")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for status updates")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Submission metadata")


class TestSubmissionResponse(BaseModel):
    """Response model for test submission."""
    submission_id: str = Field(..., description="Unique submission ID")
    test_case_ids: List[str] = Field(..., description="List of created test case IDs")
    execution_plan_id: str = Field(..., description="Execution plan ID")
    estimated_completion_time: datetime = Field(..., description="Estimated completion time")
    status: str = Field(..., description="Initial submission status")
    webhook_url: Optional[str] = Field(None, description="Configured webhook URL")


class TestExecutionStatus(BaseModel):
    """Model for test execution status."""
    test_id: str = Field(..., description="Test case ID")
    status: TestStatus = Field(..., description="Current test status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Execution progress (0.0-1.0)")
    environment_id: Optional[str] = Field(None, description="Assigned environment ID")
    started_at: Optional[datetime] = Field(None, description="Execution start time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    message: str = Field("", description="Status message")


class ExecutionPlanStatus(BaseModel):
    """Model for execution plan status."""
    plan_id: str = Field(..., description="Execution plan ID")
    submission_id: str = Field(..., description="Original submission ID")
    overall_status: str = Field(..., description="Overall plan status")
    total_tests: int = Field(..., description="Total number of tests")
    completed_tests: int = Field(..., description="Number of completed tests")
    failed_tests: int = Field(..., description="Number of failed tests")
    progress: float = Field(..., ge=0.0, le=1.0, description="Overall progress")
    test_statuses: List[TestExecutionStatus] = Field(..., description="Individual test statuses")
    started_at: Optional[datetime] = Field(None, description="Plan start time")
    completed_at: Optional[datetime] = Field(None, description="Plan completion time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class TestResultResponse(BaseModel):
    """Response model for test results."""
    test_id: str = Field(..., description="Test case ID")
    status: TestStatus = Field(..., description="Test execution status")
    execution_time: float = Field(..., description="Actual execution time in seconds")
    environment: Dict[str, Any] = Field(..., description="Environment details")
    artifacts: Dict[str, Any] = Field(..., description="Execution artifacts")
    coverage_data: Optional[Dict[str, Any]] = Field(None, description="Code coverage data")
    failure_info: Optional[Dict[str, Any]] = Field(None, description="Failure information")
    timestamp: datetime = Field(..., description="Result timestamp")


class CoverageReport(BaseModel):
    """Model for coverage report."""
    line_coverage: float = Field(..., ge=0.0, le=1.0, description="Line coverage percentage")
    branch_coverage: float = Field(..., ge=0.0, le=1.0, description="Branch coverage percentage")
    function_coverage: float = Field(..., ge=0.0, le=1.0, description="Function coverage percentage")
    covered_lines: List[str] = Field(..., description="List of covered code lines")
    uncovered_lines: List[str] = Field(..., description="List of uncovered code lines")
    coverage_gaps: List[Dict[str, Any]] = Field(..., description="Identified coverage gaps")
    report_url: Optional[str] = Field(None, description="URL to detailed coverage report")


class FailureAnalysisResponse(BaseModel):
    """Response model for failure analysis."""
    failure_id: str = Field(..., description="Unique failure ID")
    root_cause: str = Field(..., description="Identified root cause")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
    suspicious_commits: List[Dict[str, Any]] = Field(..., description="Suspicious commits")
    error_pattern: str = Field(..., description="Error pattern")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    suggested_fixes: List[Dict[str, Any]] = Field(..., description="Suggested fixes")
    related_failures: List[str] = Field(..., description="Related failure IDs")
    reproducibility: float = Field(..., ge=0.0, le=1.0, description="Reproducibility score")


class WebhookEvent(BaseModel):
    """Model for webhook events."""
    event_type: str = Field(..., description="Type of event")
    submission_id: str = Field(..., description="Submission ID")
    test_id: Optional[str] = Field(None, description="Test ID (for test-specific events)")
    status: str = Field(..., description="Current status")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event-specific data")


class HealthStatus(BaseModel):
    """Model for system health status."""
    status: str = Field(..., description="Overall system status")
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="System uptime in seconds")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component health status")
    metrics: Dict[str, Any] = Field(..., description="System metrics")
    timestamp: datetime = Field(..., description="Health check timestamp")


class SystemMetrics(BaseModel):
    """Model for system metrics."""
    active_tests: int = Field(..., description="Number of currently active tests")
    queued_tests: int = Field(..., description="Number of queued tests")
    available_environments: int = Field(..., description="Number of available environments")
    total_environments: int = Field(..., description="Total number of environments")
    cpu_usage: float = Field(..., ge=0.0, le=1.0, description="CPU usage percentage")
    memory_usage: float = Field(..., ge=0.0, le=1.0, description="Memory usage percentage")
    disk_usage: float = Field(..., ge=0.0, le=1.0, description="Disk usage percentage")
    network_io: Dict[str, float] = Field(..., description="Network I/O statistics")


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""
    repository_url: str = Field(..., description="Git repository URL")
    commit_sha: Optional[str] = Field(None, description="Specific commit SHA to analyze")
    branch: str = Field("main", description="Branch to analyze")
    diff_content: Optional[str] = Field(None, description="Raw diff content")
    webhook_url: Optional[str] = Field(None, description="Webhook for analysis completion")


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis."""
    analysis_id: str = Field(..., description="Unique analysis ID")
    commit_sha: str = Field(..., description="Analyzed commit SHA")
    changed_files: List[str] = Field(..., description="List of changed files")
    changed_functions: List[Dict[str, Any]] = Field(..., description="List of changed functions")
    affected_subsystems: List[str] = Field(..., description="Affected kernel subsystems")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Change impact score")
    risk_level: RiskLevel = Field(..., description="Risk level assessment")
    suggested_test_types: List[TestType] = Field(..., description="Suggested test types")
    generated_tests: List[str] = Field(..., description="Generated test case IDs")
    analysis_timestamp: datetime = Field(..., description="Analysis completion time")