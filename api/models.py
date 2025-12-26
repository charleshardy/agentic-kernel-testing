"""API request and response models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from ai_generator.models import (
    TestType, TestStatus, TestCase, TestResult, CodeAnalysis,
    CoverageData, HardwareConfig, RiskLevel, EnvironmentStatus
)


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
    required_hardware: Optional[Dict[str, Any]] = Field(None, description="Required hardware configuration")
    test_script: str = Field("", description="Test script content")
    expected_outcome: Optional[Dict[str, Any]] = Field(None, description="Expected test outcome")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Test metadata")


class GenerationInfo(BaseModel):
    """Model for AI generation metadata."""
    method: str = Field(..., description="Generation method: manual, ai_diff, ai_function")
    source_data: Dict[str, Any] = Field(..., description="Source data used for generation")
    generated_at: datetime = Field(..., description="Generation timestamp")
    ai_model: Optional[str] = Field(None, description="AI model used for generation")
    generation_params: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters")


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
    required_hardware: Optional[Dict[str, Any]] = Field(None, description="Required hardware configuration")
    test_script: str = Field(..., description="Test script content")
    expected_outcome: Optional[Dict[str, Any]] = Field(None, description="Expected test outcome")
    test_metadata: Dict[str, Any] = Field(..., description="Test metadata")
    
    # New fields for enhanced test case management
    generation_info: Optional[GenerationInfo] = Field(None, description="AI generation metadata")
    execution_status: str = Field("never_run", description="Current execution status")
    last_execution_at: Optional[datetime] = Field(None, description="Last execution timestamp")
    tags: List[str] = Field(default_factory=list, description="Test case tags")
    is_favorite: bool = Field(False, description="Whether test is marked as favorite")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TestSubmissionRequest(BaseModel):
    """Request model for test submission."""
    test_cases: List[TestCaseRequest] = Field(..., min_length=1, description="List of test cases to submit")
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
    status: TestStatusEnum = Field(..., description="Current test status")
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


class WebhookEvent(BaseModel):
    """Model for webhook events."""
    event_type: str = Field(..., description="Type of event")
    submission_id: str = Field(..., description="Submission ID")
    test_id: Optional[str] = Field(None, description="Test ID (for test-specific events)")
    status: str = Field(..., description="Current status")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event-specific data")


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


# Environment Allocation Models
class EnvironmentTypeEnum(str, Enum):
    """Environment type enumeration."""
    QEMU_X86 = "qemu-x86"
    QEMU_ARM = "qemu-arm"
    DOCKER = "docker"
    PHYSICAL = "physical"
    CONTAINER = "container"


class EnvironmentStatusEnum(str, Enum):
    """Environment status enumeration."""
    ALLOCATING = "allocating"
    READY = "ready"
    RUNNING = "running"
    CLEANUP = "cleanup"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    OFFLINE = "offline"


class EnvironmentHealthEnum(str, Enum):
    """Environment health enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AllocationStatusEnum(str, Enum):
    """Allocation status enumeration."""
    QUEUED = "queued"
    ALLOCATING = "allocating"
    ALLOCATED = "allocated"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NetworkMetrics(BaseModel):
    """Network metrics model."""
    bytes_in: int = Field(..., description="Bytes received")
    bytes_out: int = Field(..., description="Bytes sent")
    packets_in: int = Field(..., description="Packets received")
    packets_out: int = Field(..., description="Packets sent")


class ResourceUsage(BaseModel):
    """Resource usage model."""
    cpu: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    memory: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage")
    disk: float = Field(..., ge=0.0, le=100.0, description="Disk usage percentage")
    network: NetworkMetrics = Field(..., description="Network metrics")


class EnvironmentMetadata(BaseModel):
    """Environment metadata model."""
    kernel_version: Optional[str] = Field(None, description="Kernel version")
    ip_address: Optional[str] = Field(None, description="IP address")
    ssh_credentials: Optional[Dict[str, Any]] = Field(None, description="SSH credentials")
    provisioned_at: Optional[datetime] = Field(None, description="Provisioning timestamp")
    last_health_check: Optional[datetime] = Field(None, description="Last health check timestamp")
    additional_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class EnvironmentResponse(BaseModel):
    """Response model for environment information."""
    id: str = Field(..., description="Environment ID")
    type: EnvironmentTypeEnum = Field(..., description="Environment type")
    status: EnvironmentStatusEnum = Field(..., description="Environment status")
    architecture: str = Field(..., description="CPU architecture")
    assigned_tests: List[str] = Field(default_factory=list, description="Assigned test IDs")
    resources: ResourceUsage = Field(..., description="Resource usage")
    health: EnvironmentHealthEnum = Field(..., description="Environment health")
    metadata: EnvironmentMetadata = Field(..., description="Environment metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class HardwareRequirements(BaseModel):
    """Hardware requirements model."""
    architecture: str = Field(..., description="Required CPU architecture")
    min_memory_mb: int = Field(..., ge=1, description="Minimum memory in MB")
    min_cpu_cores: int = Field(..., ge=1, description="Minimum CPU cores")
    required_features: List[str] = Field(default_factory=list, description="Required hardware features")
    preferred_environment_type: Optional[EnvironmentTypeEnum] = Field(None, description="Preferred environment type")
    isolation_level: str = Field(..., pattern="^(none|process|container|vm)$", description="Required isolation level")


class AllocationPreferences(BaseModel):
    """Allocation preferences model."""
    environment_type: Optional[EnvironmentTypeEnum] = Field(None, description="Preferred environment type")
    architecture: Optional[str] = Field(None, description="Preferred architecture")
    max_wait_time: Optional[int] = Field(None, ge=0, description="Maximum wait time in seconds")
    allow_shared_environment: bool = Field(True, description="Allow shared environments")
    require_dedicated_resources: bool = Field(False, description="Require dedicated resources")


class AllocationRequest(BaseModel):
    """Allocation request model."""
    id: str = Field(..., description="Request ID")
    test_id: str = Field(..., description="Test ID")
    requirements: HardwareRequirements = Field(..., description="Hardware requirements")
    preferences: Optional[AllocationPreferences] = Field(None, description="Allocation preferences")
    priority: int = Field(..., ge=1, le=10, description="Request priority")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    estimated_start_time: Optional[datetime] = Field(None, description="Estimated start time")
    status: AllocationStatusEnum = Field(..., description="Allocation status")


class AllocationEvent(BaseModel):
    """Allocation event model."""
    id: str = Field(..., description="Event ID")
    type: str = Field(..., pattern="^(allocated|deallocated|failed|queued)$", description="Event type")
    environment_id: str = Field(..., description="Environment ID")
    test_id: Optional[str] = Field(None, description="Test ID")
    timestamp: datetime = Field(..., description="Event timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")


class AllocationMetrics(BaseModel):
    """Allocation metrics model."""
    total_allocations: int = Field(..., description="Total allocations")
    successful_allocations: int = Field(..., description="Successful allocations")
    failed_allocations: int = Field(..., description="Failed allocations")
    average_allocation_time: float = Field(..., description="Average allocation time in seconds")
    queue_length: int = Field(..., description="Current queue length")
    utilization_rate: float = Field(..., ge=0.0, le=1.0, description="Environment utilization rate")


class ResourceMetrics(BaseModel):
    """Resource metrics model."""
    timestamp: datetime = Field(..., description="Metrics timestamp")
    environment_id: str = Field(..., description="Environment ID")
    cpu: Dict[str, float] = Field(..., description="CPU metrics")
    memory: Dict[str, int] = Field(..., description="Memory metrics")
    disk: Dict[str, int] = Field(..., description="Disk metrics")
    network: Dict[str, int] = Field(..., description="Network metrics")


class EnvironmentAllocationResponse(BaseModel):
    """Response model for environment allocation data."""
    environments: List[EnvironmentResponse] = Field(..., description="Environment list")
    queue: List[AllocationRequest] = Field(..., description="Allocation queue")
    metrics: AllocationMetrics = Field(..., description="Allocation metrics")
    history: List[AllocationEvent] = Field(..., description="Allocation history")


class AllocationQueueResponse(BaseModel):
    """Response model for allocation queue."""
    queue: List[AllocationRequest] = Field(..., description="Allocation queue")
    estimated_wait_times: Dict[str, int] = Field(..., description="Estimated wait times by request ID")
    total_wait_time: int = Field(..., description="Total estimated wait time")


class AllocationHistoryResponse(BaseModel):
    """Response model for allocation history."""
    events: List[AllocationEvent] = Field(..., description="Allocation events")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")


class TestExecutionRequest(BaseModel):
    """Request model for test execution."""
    test_case_ids: List[str] = Field(..., min_length=1, description="List of test case IDs to execute")
    hardware_config_id: Optional[int] = Field(None, description="Override hardware configuration")
    priority: int = Field(5, ge=1, le=10, description="Execution priority (1=highest, 10=lowest)")
    timeout: int = Field(300, ge=30, le=3600, description="Execution timeout in seconds")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    tags: List[str] = Field(default_factory=list, description="Execution tags")


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations on test cases."""
    test_case_ids: List[str] = Field(..., min_length=1, description="List of test case IDs to operate on")
    operation: str = Field(..., description="Operation to perform: delete, execute, update_tags, update_favorite")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")


class BulkOperationResult(BaseModel):
    """Result model for individual bulk operation."""
    test_case_id: str = Field(..., description="Test case ID")
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Result message")
    error: Optional[str] = Field(None, description="Error message if failed")


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    operation: str = Field(..., description="Operation that was performed")
    total_requested: int = Field(..., description="Total number of operations requested")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: List[BulkOperationResult] = Field(..., description="Individual operation results")
    execution_plan_id: Optional[str] = Field(None, description="Execution plan ID for bulk execute operations")


class TestResultResponse(BaseModel):
    """Response model for test results."""
    id: str = Field(..., description="Test result ID")
    test_id: str = Field(..., description="Test ID")
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
    test_types: List[TestTypeEnum] = Field(..., min_length=1, description="Types of tests to generate")
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


class TestCaseFilters(BaseModel):
    """Model for test case filtering parameters."""
    test_type: Optional[str] = Field(None, description="Filter by test type")
    subsystem: Optional[str] = Field(None, description="Filter by subsystem")
    status: Optional[str] = Field(None, description="Filter by execution status")
    generation_method: Optional[str] = Field(None, description="Filter by generation method")
    date_range: Optional[List[str]] = Field(None, description="Filter by date range [start, end]")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


class TestListResponse(BaseModel):
    """Response model for test case listing."""
    tests: List[TestCaseResponse] = Field(..., description="List of test cases")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    filters_applied: TestCaseFilters = Field(..., description="Applied filters")
    total_count: int = Field(..., description="Total number of test cases")


class PaginatedResponse(BaseModel):
    """Generic paginated response model."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
