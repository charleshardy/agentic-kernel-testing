# Test Execution Orchestrator Design

## Overview

The Test Execution Orchestrator is the core execution engine that transforms the current test submission system into a fully functional testing platform. It consists of several interconnected components that work together to pick up submitted tests, execute them in appropriate environments, and provide real-time status updates.

The orchestrator operates as a background service that continuously monitors for new execution plans, manages test environments, executes tests, and tracks results. It bridges the gap between the existing test submission API (which works perfectly) and actual test execution.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Server    │    │   Orchestrator   │    │  Test Runners   │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │Test Submit  │ │───▶│ │Queue Monitor │ │───▶│ │Docker Runner│ │
│ │   API       │ │    │ │              │ │    │ │             │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │Status API   │ │◀───│ │Status Tracker│ │    │ │QEMU Runner  │ │
│ │             │ │    │ │              │ │    │ │             │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │Resource Manager  │
                       │                  │
                       │ ┌──────────────┐ │
                       │ │Environment   │ │
                       │ │Pool          │ │
                       │ └──────────────┘ │
                       └──────────────────┘
```

### Component Interaction Flow

1. **Test Submission**: API receives test submission (already working)
2. **Queue Monitoring**: Orchestrator detects new execution plans
3. **Resource Allocation**: Resource manager assigns appropriate environments
4. **Test Execution**: Test runners execute tests in isolated environments
5. **Status Updates**: Status tracker maintains real-time execution state
6. **Result Collection**: Completed tests have results stored and made available

## Components and Interfaces

### 1. Test Orchestrator Service (`orchestrator/service.py`)

**Purpose**: Main orchestration service that coordinates all execution activities.

**Key Methods**:
- `start()`: Initialize and start the orchestrator service
- `stop()`: Gracefully shutdown the orchestrator
- `process_execution_plans()`: Main loop that processes queued execution plans
- `handle_test_completion()`: Process completed test results

**Interfaces**:
- Monitors `execution_plans` dictionary for new plans
- Updates test status through Status Tracker
- Coordinates with Resource Manager for environment allocation

### 2. Queue Monitor (`orchestrator/queue_monitor.py`)

**Purpose**: Continuously monitors for new execution plans and manages the execution queue.

**Key Methods**:
- `poll_for_new_plans()`: Check for newly submitted execution plans
- `prioritize_queue()`: Sort execution queue by priority
- `get_next_execution_plan()`: Get the next plan to execute

**Interfaces**:
- Reads from `execution_plans` global dictionary
- Maintains internal priority queue
- Provides plans to orchestrator service

### 3. Resource Manager (`orchestrator/resource_manager.py`)

**Purpose**: Manages test execution environments and resource allocation.

**Key Methods**:
- `allocate_environment(hardware_requirements)`: Allocate suitable environment
- `release_environment(env_id)`: Clean and release environment
- `get_available_environments()`: Get list of available environments
- `provision_environment(config)`: Create new environment if needed

**Interfaces**:
- Manages pool of Docker containers and QEMU instances
- Tracks resource utilization and availability
- Provides environment isolation guarantees

### 4. Test Runner Factory (`execution/runner_factory.py`)

**Purpose**: Creates appropriate test runners based on test type and requirements.

**Key Methods**:
- `create_runner(test_case, environment)`: Create appropriate runner
- `get_runner_for_test_type(test_type)`: Get runner class for test type

**Supported Runners**:
- `DockerTestRunner`: For unit and integration tests
- `QEMUTestRunner`: For kernel and hardware-specific tests
- `ContainerTestRunner`: For lightweight isolated execution

### 5. Status Tracker (`orchestrator/status_tracker.py`)

**Purpose**: Maintains real-time status of all test executions and system metrics.

**Key Methods**:
- `update_test_status(test_id, status)`: Update individual test status
- `get_active_test_count()`: Get number of currently running tests
- `get_system_metrics()`: Get comprehensive system status
- `increment_active_tests()`: Increment active test counter
- `decrement_active_tests()`: Decrement active test counter

**Status States**:
- `queued`: Test is waiting for execution
- `running`: Test is currently executing
- `completed`: Test finished successfully
- `failed`: Test finished with failure
- `timeout`: Test exceeded time limit
- `error`: Test encountered system error

### 6. Test Runners (`execution/runners/`)

#### Docker Test Runner (`execution/runners/docker_runner.py`)
**Purpose**: Execute tests in Docker containers for isolation and consistency.

**Key Methods**:
- `execute(test_case)`: Run test in Docker container
- `capture_results()`: Collect stdout, stderr, exit code
- `cleanup()`: Remove container and temporary files

#### QEMU Test Runner (`execution/runners/qemu_runner.py`)
**Purpose**: Execute tests in QEMU virtual machines for kernel testing.

**Key Methods**:
- `boot_vm(kernel_image)`: Boot QEMU VM with test kernel
- `execute_test_in_vm(test_script)`: Run test inside VM
- `capture_vm_output()`: Collect VM console output and results

## Data Models

### Execution Plan Status
```python
@dataclass
class ExecutionPlanStatus:
    plan_id: str
    submission_id: str
    status: str  # queued, running, completed, failed
    total_tests: int
    completed_tests: int
    failed_tests: int
    active_tests: int
    started_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    test_statuses: List[TestExecutionStatus]
```

### Test Execution Status
```python
@dataclass
class TestExecutionStatus:
    test_id: str
    status: str  # queued, running, completed, failed, timeout, error
    environment_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float  # 0.0 to 1.0
    message: str
```

### Test Result
```python
@dataclass
class TestResult:
    test_id: str
    execution_id: str
    status: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    execution_time: float
    environment_info: Dict[str, Any]
    artifacts: List[str]  # Paths to generated artifacts
    metrics: Dict[str, Any]  # Performance/resource metrics
    created_at: datetime
```

### Environment
```python
@dataclass
class Environment:
    id: str
    type: str  # docker, qemu, physical
    status: str  # available, busy, provisioning, error
    hardware_config: HardwareConfig
    resource_usage: Dict[str, float]
    created_at: datetime
    last_used: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Automatic Plan Processing
*For any* execution plan that gets queued, the orchestrator should pick it up and begin processing within a reasonable time window (e.g., 30 seconds)
**Validates: Requirements 1.1**

### Property 2: Environment Allocation Matching
*For any* test case with specific hardware requirements, the resource manager should allocate an environment that meets or exceeds those requirements
**Validates: Requirements 1.2, 3.1**

### Property 3: Status Consistency During Execution
*For any* test that transitions to "running" status, the active test count should increase by exactly one, and when it completes, the count should decrease by exactly one
**Validates: Requirements 1.4, 1.5**

### Property 4: Real-time Status Accuracy
*For any* system status query, the returned active test count should match the actual number of tests currently in "running" status
**Validates: Requirements 2.1, 2.2**

### Property 5: Test Isolation
*For any* two tests running simultaneously, changes made by one test should not be visible to or affect the other test's execution environment
**Validates: Requirements 3.2, 3.5**

### Property 6: Complete Result Capture
*For any* test that completes (successfully or with failure), the system should capture and store stdout, stderr, exit code, and execution time
**Validates: Requirements 4.1, 4.2**

### Property 7: Timeout Enforcement
*For any* test that exceeds its specified timeout limit, the orchestrator should terminate the test and record a timeout status within a reasonable grace period
**Validates: Requirements 4.3, 5.2**

### Property 8: Priority Ordering
*For any* set of queued execution plans with different priorities, the orchestrator should process higher-priority plans before lower-priority ones
**Validates: Requirements 6.1, 6.2**

### Property 9: FIFO for Equal Priority
*For any* set of execution plans with equal priority, the orchestrator should process them in first-in-first-out order
**Validates: Requirements 6.3**

### Property 10: Environment Type Selection
*For any* test case, the runner factory should select an environment type appropriate for the test type (lightweight for unit tests, full VM for integration tests, etc.)
**Validates: Requirements 7.1, 7.2, 7.5**

### Property 11: Resource Recovery
*For any* environment that becomes available after test completion, it should be properly cleaned and made available for the next test within a reasonable time
**Validates: Requirements 3.4, 5.1**

### Property 12: Service Recovery
*For any* orchestrator service restart with queued tests, all previously queued tests should be recovered and resume execution
**Validates: Requirements 5.3**

## Error Handling

### Environment Failures
- **Detection**: Monitor environment health through heartbeat checks
- **Response**: Mark failed environments as unavailable, provision replacements
- **Recovery**: Attempt to restart failed environments, escalate to manual intervention if needed

### Test Execution Failures
- **Timeout Handling**: Enforce strict timeout limits, terminate hung processes
- **Resource Exhaustion**: Queue tests when resources unavailable, scale environments if possible
- **Script Errors**: Capture and report script failures without affecting other tests

### System Failures
- **Orchestrator Crashes**: Persist execution state, recover on restart
- **Network Issues**: Retry operations with exponential backoff
- **Storage Failures**: Gracefully handle artifact storage issues

## Testing Strategy

### Unit Testing
- Test individual components in isolation
- Mock external dependencies (Docker, QEMU)
- Verify error handling and edge cases
- Test resource allocation algorithms

### Property-Based Testing
The system will use **Hypothesis** for property-based testing with a minimum of 100 iterations per property.

Each property-based test will be tagged with comments referencing the design document:
- Format: `**Feature: test-execution-orchestrator, Property {number}: {property_text}**`

**Key Property Tests**:
1. **Execution Plan Processing**: Generate random execution plans and verify automatic pickup
2. **Resource Allocation**: Generate various hardware requirements and verify matching allocation
3. **Status Tracking**: Generate test state transitions and verify counter accuracy
4. **Priority Scheduling**: Generate mixed-priority queues and verify execution order
5. **Environment Isolation**: Generate concurrent tests and verify no cross-contamination
6. **Result Capture**: Generate tests with various outputs and verify complete capture
7. **Timeout Handling**: Generate tests with various timeout scenarios and verify enforcement

### Integration Testing
- Test full execution flow from submission to completion
- Verify interaction between orchestrator components
- Test with real Docker containers and QEMU instances
- Validate API integration and status updates

### Performance Testing
- Test with high volumes of concurrent tests
- Measure resource utilization and scaling behavior
- Verify system stability under load
- Test environment provisioning performance

## Implementation Notes

### Phase 1: Core Orchestrator
- Implement basic orchestrator service and queue monitor
- Add simple Docker-based test execution
- Integrate with existing API for status updates

### Phase 2: Advanced Features
- Add QEMU support for kernel testing
- Implement priority scheduling and resource management
- Add comprehensive error handling and recovery

### Phase 3: Optimization
- Add performance monitoring and metrics
- Implement auto-scaling of environments
- Add advanced scheduling algorithms

The orchestrator will integrate seamlessly with the existing API server, using the current `submitted_tests` and `execution_plans` dictionaries as the interface between submission and execution.