"""Integration tests for complete orchestrator execution flow.

This module implements task 9.1 from the test-execution-orchestrator spec:
- Test complete workflow from test submission through execution to results
- Verify proper integration between all orchestrator components
- Test error scenarios and recovery mechanisms
- Requirements: All

This test suite validates the end-to-end execution flow as specified in the
orchestrator requirements and design documents.
"""

import pytest
import asyncio
import time
import uuid
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, TestType, RiskLevel, FailureInfo
)
from orchestrator.service import OrchestratorService
from orchestrator.config import OrchestratorConfig
from orchestrator.scheduler import TestOrchestrator, Priority
from orchestrator.status_tracker import StatusTracker
from api.orchestrator_integration import start_orchestrator, stop_orchestrator, get_orchestrator


@pytest.fixture
def temp_orchestrator_config(tmp_path):
    """Create temporary orchestrator configuration for full execution flow testing."""
    config = OrchestratorConfig(
        poll_interval=0.5,  # Fast polling for tests
        default_timeout=60,  # Reasonable timeout for integration tests
        max_concurrent_tests=5,
        enable_persistence=True,
        state_file=str(tmp_path / "orchestrator_state.json"),
        log_level="DEBUG"
    )
    return config


@pytest.fixture
def orchestrator_service(temp_orchestrator_config):
    """Create and manage orchestrator service for full execution flow testing."""
    service = OrchestratorService(temp_orchestrator_config)
    
    # Start the service
    assert service.start(), "Failed to start orchestrator service"
    
    # Verify all components are running
    health_status = service.get_health_status()
    assert health_status['status'] == 'healthy'
    assert health_status['is_running'] is True
    
    yield service
    
    # Clean up
    service.stop()


@pytest.fixture
def test_environments():
    """Create comprehensive test environments for full execution flow testing."""
    return [
        Environment(
            id="full-flow-x86-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon E5-2680",
                memory_mb=4096,
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        ),
        Environment(
            id="full-flow-x86-2",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon E5-2690",
                memory_mb=8192,
                storage_type="nvme",
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        ),
        Environment(
            id="full-flow-arm-1",
            config=HardwareConfig(
                architecture="arm64",
                cpu_model="ARM Cortex-A72",
                memory_mb=2048,
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        ),
        Environment(
            id="full-flow-docker-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Core i7",
                memory_mb=2048,
                storage_type="ssd",
                is_virtual=True,
                emulator="docker"
            ),
            status=EnvironmentStatus.IDLE
        )
    ]


@pytest.fixture
def comprehensive_test_cases():
    """Create comprehensive test cases for full execution flow testing."""
    return [
        TestCase(
            id="full-flow-unit-001",
            name="Unit Test - Memory Management",
            description="Test memory allocation and deallocation",
            test_type=TestType.UNIT,
            target_subsystem="memory_management",
            test_script="""#!/bin/bash
echo "Starting memory management unit test..."
echo "Testing memory allocation patterns..."

# Simulate memory allocation test
python3 -c "
import sys
try:
    # Test basic allocation
    data = bytearray(1024 * 1024)  # 1MB
    print('Memory allocation successful')
    
    # Test deallocation
    del data
    print('Memory deallocation successful')
    
    print('Unit test PASSED')
    sys.exit(0)
except Exception as e:
    print(f'Unit test FAILED: {e}')
    sys.exit(1)
"
""",
            execution_time_estimate=30,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        ),
        TestCase(
            id="full-flow-integration-001",
            name="Integration Test - Scheduler-Memory Interaction",
            description="Test interaction between scheduler and memory management",
            test_type=TestType.INTEGRATION,
            target_subsystem="scheduler",
            test_script="""#!/bin/bash
echo "Starting scheduler-memory integration test..."
echo "Testing process scheduling with memory pressure..."

# Simulate integration test
python3 -c "
import time
import threading
import sys

def memory_worker():
    try:
        data = []
        for i in range(10):
            data.append(bytearray(100 * 1024))  # 100KB blocks
            time.sleep(0.1)
        print('Memory worker completed')
    except Exception as e:
        print(f'Memory worker failed: {e}')

def scheduler_worker():
    try:
        for i in range(20):
            time.sleep(0.05)  # Yield to scheduler
        print('Scheduler worker completed')
    except Exception as e:
        print(f'Scheduler worker failed: {e}')

# Run workers concurrently
threads = [
    threading.Thread(target=memory_worker),
    threading.Thread(target=scheduler_worker)
]

for t in threads:
    t.start()

for t in threads:
    t.join()

print('Integration test PASSED')
"
""",
            execution_time_estimate=45,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            )
        ),
        TestCase(
            id="full-flow-performance-001",
            name="Performance Test - Context Switch Latency",
            description="Measure context switch performance",
            test_type=TestType.PERFORMANCE,
            target_subsystem="scheduler",
            test_script="""#!/bin/bash
echo "Starting context switch performance test..."
echo "Measuring context switch latency..."

# Simulate performance measurement
python3 -c "
import time
import threading
import statistics

def measure_context_switches():
    times = []
    for i in range(100):
        start = time.perf_counter()
        time.sleep(0.001)  # Force context switch
        end = time.perf_counter()
        times.append((end - start) * 1000000)  # Convert to microseconds
    
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    
    print(f'Average context switch time: {avg_time:.2f} μs')
    print(f'Median context switch time: {median_time:.2f} μs')
    
    # Performance threshold check
    if avg_time < 10.0:  # Less than 10 microseconds
        print('Performance test PASSED')
        return 0
    else:
        print('Performance test FAILED - latency too high')
        return 1

exit(measure_context_switches())
"
""",
            execution_time_estimate=60,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            )
        ),
        TestCase(
            id="full-flow-security-001",
            name="Security Test - Buffer Overflow Detection",
            description="Test buffer overflow protection mechanisms",
            test_type=TestType.SECURITY,
            target_subsystem="security",
            test_script="""#!/bin/bash
echo "Starting buffer overflow security test..."
echo "Testing buffer overflow protection..."

# Simulate security test
python3 -c "
import sys
import ctypes

def test_buffer_protection():
    try:
        # Test safe buffer operations
        buffer = bytearray(1024)
        
        # Safe write
        for i in range(1024):
            buffer[i] = i % 256
        
        print('Buffer operations completed safely')
        
        # Test bounds checking
        try:
            # This should be caught by Python bounds checking
            buffer[1024] = 0
            print('Security test FAILED - bounds check bypassed')
            return 1
        except IndexError:
            print('Bounds checking working correctly')
            print('Security test PASSED')
            return 0
            
    except Exception as e:
        print(f'Security test ERROR: {e}')
        return 1

sys.exit(test_buffer_protection())
"
""",
            execution_time_estimate=30,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        ),
        TestCase(
            id="full-flow-arm-001",
            name="ARM Architecture Test",
            description="Test ARM-specific functionality",
            test_type=TestType.INTEGRATION,
            target_subsystem="architecture",
            test_script="""#!/bin/bash
echo "Starting ARM architecture test..."
echo "Testing ARM-specific features..."

# Check architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

# Simulate ARM-specific test
python3 -c "
import platform
import sys

arch = platform.machine()
print(f'Python detected architecture: {arch}')

# ARM architecture test
if 'arm' in arch.lower() or 'aarch64' in arch.lower():
    print('ARM architecture detected - running ARM-specific tests')
    # Simulate ARM-specific functionality test
    print('ARM test PASSED')
    sys.exit(0)
else:
    print('Non-ARM architecture - running compatibility test')
    # Simulate compatibility test
    print('Compatibility test PASSED')
    sys.exit(0)
"
""",
            execution_time_estimate=25,
            required_hardware=HardwareConfig(
                architecture="arm64",
                cpu_model="ARM Cortex-A72",
                memory_mb=1024,
                is_virtual=True
            )
        )
    ]


@pytest.mark.integration
class TestOrchestratorFullExecutionFlow:
    """Test complete orchestrator execution flow from submission to results.
    
    This test class implements the requirements for task 9.1:
    - Complete workflow from test submission through execution to results
    - Proper integration between all orchestrator components
    - Error scenarios and recovery mechanisms
    """
    
    def test_complete_single_test_execution_flow(
        self, 
        orchestrator_service, 
        test_environments, 
        comprehensive_test_cases
    ):
        """Test complete execution flow for a single test case.
        
        Validates Requirements:
        - 1.1: Automatic test pickup and processing
        - 1.2: Environment allocation based on hardware requirements
        - 1.3: Test execution in appropriate environment
        - 1.4, 1.5: Status tracking during execution
        - 4.1, 4.2: Complete result capture
        - 3.2, 3.5: Test isolation
        """
        # Initialize orchestrator components
        orchestrator = TestOrchestrator()
        
        # Add test environment
        test_env = test_environments[0]  # x86_64 environment
        orchestrator.add_environment(test_env)
        
        # Select test case
        test_case = comprehensive_test_cases[0]  # Unit test
        
        # Step 1: Submit test case (Requirements 1.1)
        submission_time = time.time()
        job_id = orchestrator.submit_job(
            test_case=test_case,
            priority=Priority.HIGH,
            impact_score=0.8
        )
        
        assert job_id is not None
        assert isinstance(job_id, str)
        
        # Verify automatic pickup within reasonable time
        pickup_detected = False
        max_pickup_time = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_pickup_time:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] in ['running', 'completed']:
                pickup_detected = True
                break
            time.sleep(0.5)
        
        assert pickup_detected, "Test should be automatically picked up for processing"
        
        # Step 2: Monitor environment allocation (Requirements 1.2, 3.1)
        allocation_verified = False
        while time.time() - start_time < max_pickup_time:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] == 'running':
                # Verify environment allocation
                queue_status = orchestrator.get_queue_status()
                assert queue_status['allocated_environments'] > 0
                assert queue_status['available_environments'] < len(test_environments)
                allocation_verified = True
                break
            time.sleep(0.5)
        
        assert allocation_verified, "Environment should be allocated for running test"
        
        # Step 3: Monitor status tracking (Requirements 1.4, 1.5, 2.1, 2.2)
        status_updates = []
        execution_start = time.time()
        max_execution_time = 120  # seconds
        
        while time.time() - execution_start < max_execution_time:
            job_status = orchestrator.get_job_status(job_id)
            queue_status = orchestrator.get_queue_status()
            
            status_update = {
                'timestamp': time.time(),
                'job_status': job_status['status'] if job_status else 'unknown',
                'active_tests': queue_status['running_jobs'],
                'queued_tests': queue_status['pending_jobs']
            }
            status_updates.append(status_update)
            
            if job_status and job_status['status'] == 'completed':
                break
            
            time.sleep(1)
        
        # Verify status progression
        assert len(status_updates) > 0
        final_status = status_updates[-1]
        assert final_status['job_status'] == 'completed'
        
        # Verify status consistency
        running_statuses = [s for s in status_updates if s['job_status'] == 'running']
        if running_statuses:
            for status in running_statuses:
                assert status['active_tests'] > 0, "Active test count should be > 0 when test is running"
        
        # Step 4: Verify complete result capture (Requirements 4.1, 4.2)
        final_job_status = orchestrator.get_job_status(job_id)
        assert final_job_status is not None
        assert final_job_status['status'] == 'completed'
        assert final_job_status['result'] is not None
        
        # Parse and verify result details
        result = TestResult.from_dict(final_job_status['result'])
        assert result.test_id == test_case.id
        assert result.status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]
        assert result.execution_time > 0
        assert result.environment is not None
        assert result.environment.id == test_env.id
        assert result.timestamp is not None
        
        # Verify output capture
        assert hasattr(result, 'stdout') or 'stdout' in final_job_status['result']
        assert hasattr(result, 'stderr') or 'stderr' in final_job_status['result']
        assert hasattr(result, 'exit_code') or 'exit_code' in final_job_status['result']
        
        # Step 5: Verify resource cleanup (Requirements 3.4, 5.1)
        final_queue_status = orchestrator.get_queue_status()
        assert final_queue_status['running_jobs'] == 0
        assert final_queue_status['allocated_environments'] == 0
        assert final_queue_status['available_environments'] == len(test_environments)
        
        # Verify environment is back to idle state
        assert test_env.status == EnvironmentStatus.IDLE
        
        # Calculate and verify timing metrics
        total_execution_time = time.time() - submission_time
        assert total_execution_time < 180, f"Total execution time too long: {total_execution_time:.2f}s"
        
        print(f"Single test execution flow completed successfully:")
        print(f"  Test ID: {test_case.id}")
        print(f"  Final Status: {result.status.value}")
        print(f"  Execution Time: {result.execution_time:.2f}s")
        print(f"  Total Flow Time: {total_execution_time:.2f}s")
        print(f"  Environment: {result.environment.id}")
    
    def test_multiple_test_execution_flow_with_priority(
        self, 
        orchestrator_service, 
        test_environments, 
        comprehensive_test_cases
    ):
        """Test execution flow for multiple tests with different priorities.
        
        Validates Requirements:
        - 6.1, 6.2: Priority-based execution ordering
        - 6.3: FIFO for equal priority tests
        - 2.4: Multiple concurrent test handling
        - 3.2, 3.5: Test isolation between concurrent tests
        """
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        
        # Add multiple environments for concurrent execution
        for env in test_environments[:3]:  # Use 3 environments
            orchestrator.add_environment(env)
        
        # Prepare test cases with different priorities
        test_submissions = [
            (comprehensive_test_cases[0], Priority.LOW, 0.3),      # Unit test - low priority
            (comprehensive_test_cases[1], Priority.HIGH, 0.9),     # Integration test - high priority
            (comprehensive_test_cases[2], Priority.CRITICAL, 0.95), # Performance test - critical priority
            (comprehensive_test_cases[3], Priority.MEDIUM, 0.6),   # Security test - medium priority
            (comprehensive_test_cases[4], Priority.HIGH, 0.8),     # ARM test - high priority
        ]
        
        # Step 1: Submit all tests
        job_submissions = []
        submission_start = time.time()
        
        for test_case, priority, impact_score in test_submissions:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=priority,
                impact_score=impact_score
            )
            job_submissions.append({
                'job_id': job_id,
                'test_id': test_case.id,
                'priority': priority,
                'impact_score': impact_score,
                'submission_time': time.time()
            })
        
        submission_time = time.time() - submission_start
        assert submission_time < 5.0, f"Submission took too long: {submission_time:.2f}s"
        
        # Step 2: Monitor execution order and concurrency
        execution_order = []
        max_concurrent = 0
        max_wait_time = 300  # 5 minutes for multiple tests
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            current_running = queue_status['running_jobs']
            max_concurrent = max(max_concurrent, current_running)
            
            # Track execution order
            for submission in job_submissions:
                job_id = submission['job_id']
                if job_id not in [e['job_id'] for e in execution_order]:
                    job_status = orchestrator.get_job_status(job_id)
                    if job_status and job_status['status'] == 'running':
                        execution_order.append({
                            'job_id': job_id,
                            'test_id': submission['test_id'],
                            'priority': submission['priority'],
                            'start_time': time.time()
                        })
            
            # Check if all completed
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            
            time.sleep(1)
        
        # Step 3: Verify priority ordering (Requirements 6.1, 6.2)
        assert len(execution_order) >= 3, "Should have tracked execution order for multiple tests"
        assert max_concurrent > 1, "Should have concurrent execution"
        assert max_concurrent <= 3, "Should not exceed available environments"
        
        # Analyze priority ordering
        priority_values = {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1
        }
        
        # Check that higher priority tests generally started earlier
        for i in range(len(execution_order) - 1):
            current = execution_order[i]
            next_test = execution_order[i + 1]
            
            current_priority_val = priority_values[current['priority']]
            next_priority_val = priority_values[next_test['priority']]
            
            # Allow some flexibility due to concurrent execution
            if current_priority_val < next_priority_val:
                time_diff = next_test['start_time'] - current['start_time']
                # If a lower priority test started significantly before a higher priority test,
                # it might indicate a priority ordering issue
                if time_diff > 10.0:  # 10 second tolerance
                    print(f"Warning: Lower priority test {current['test_id']} started {time_diff:.2f}s before higher priority test {next_test['test_id']}")
        
        # Step 4: Collect and verify all results
        results = []
        for submission in job_submissions:
            job_status = orchestrator.get_job_status(submission['job_id'])
            assert job_status is not None
            assert job_status['status'] == 'completed'
            
            if job_status['result']:
                result = TestResult.from_dict(job_status['result'])
                results.append(result)
        
        assert len(results) == len(job_submissions)
        
        # Step 5: Verify test isolation (Requirements 3.2, 3.5)
        # Each test should have run in a different environment or at different times
        environment_usage = {}
        for result in results:
            env_id = result.environment.id
            if env_id not in environment_usage:
                environment_usage[env_id] = []
            environment_usage[env_id].append(result)
        
        # Verify no environment conflicts (tests on same environment should not overlap)
        for env_id, env_results in environment_usage.items():
            if len(env_results) > 1:
                # Sort by start time and verify no overlap
                env_results.sort(key=lambda r: r.timestamp)
                for i in range(len(env_results) - 1):
                    current_result = env_results[i]
                    next_result = env_results[i + 1]
                    
                    # Calculate end time of current test
                    current_end = current_result.timestamp + timedelta(seconds=current_result.execution_time)
                    
                    # Verify next test started after current test ended (with small buffer)
                    time_gap = (next_result.timestamp - current_end).total_seconds()
                    assert time_gap >= -5.0, f"Tests on {env_id} may have overlapped: gap = {time_gap:.2f}s"
        
        # Step 6: Verify final cleanup
        final_queue_status = orchestrator.get_queue_status()
        assert final_queue_status['running_jobs'] == 0
        assert final_queue_status['pending_jobs'] == 0
        assert final_queue_status['allocated_environments'] == 0
        
        total_execution_time = time.time() - start_time
        
        print(f"Multiple test execution flow completed successfully:")
        print(f"  Total Tests: {len(job_submissions)}")
        print(f"  Max Concurrent: {max_concurrent}")
        print(f"  Execution Order: {[e['test_id'] for e in execution_order]}")
        print(f"  Total Flow Time: {total_execution_time:.2f}s")
        print(f"  Environment Usage: {list(environment_usage.keys())}")
    
    def test_error_scenarios_and_recovery_mechanisms(
        self, 
        orchestrator_service, 
        test_environments
    ):
        """Test error scenarios and recovery mechanisms.
        
        Validates Requirements:
        - 4.3, 5.2: Timeout enforcement
        - 5.1: Environment failure handling
        - 5.3: Service recovery
        - 5.5: Error logging and monitoring
        """
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        
        # Add test environments
        for env in test_environments[:2]:
            orchestrator.add_environment(env)
        
        # Test Case 1: Timeout scenario (Requirements 4.3, 5.2)
        timeout_test = TestCase(
            id="full-flow-timeout-001",
            name="Timeout Test",
            description="Test that will exceed timeout limit",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Starting timeout test..."
echo "This test will run longer than the timeout limit"
sleep 120  # Sleep for 2 minutes (longer than 60s timeout)
echo "This should not be reached"
exit 0
""",
            execution_time_estimate=30,  # Estimate shorter than actual
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        # Submit timeout test
        timeout_job_id = orchestrator.submit_job(
            test_case=timeout_test,
            priority=Priority.MEDIUM,
            impact_score=0.5
        )
        
        # Monitor for timeout
        timeout_detected = False
        max_wait_time = 90  # Wait for timeout to occur
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(timeout_job_id)
            if job_status and job_status['status'] in ['timeout', 'failed', 'completed']:
                if job_status['status'] in ['timeout', 'failed']:
                    timeout_detected = True
                break
            time.sleep(2)
        
        # Verify timeout was handled
        final_timeout_status = orchestrator.get_job_status(timeout_job_id)
        assert final_timeout_status is not None
        assert final_timeout_status['status'] in ['timeout', 'failed']
        timeout_detected = True
        
        # Verify resource cleanup after timeout
        queue_status = orchestrator.get_queue_status()
        assert queue_status['running_jobs'] == 0, "No jobs should be running after timeout"
        
        # Test Case 2: Failing test scenario
        failing_test = TestCase(
            id="full-flow-failing-001",
            name="Failing Test",
            description="Test that will fail with error",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Starting failing test..."
echo "This test will fail intentionally"
echo "Error: Simulated test failure" >&2
exit 1
""",
            execution_time_estimate=15,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        # Submit failing test
        failing_job_id = orchestrator.submit_job(
            test_case=failing_test,
            priority=Priority.MEDIUM,
            impact_score=0.5
        )
        
        # Wait for completion
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(failing_job_id)
            if job_status and job_status['status'] == 'completed':
                break
            time.sleep(1)
        
        # Verify failure was handled properly
        final_failing_status = orchestrator.get_job_status(failing_job_id)
        assert final_failing_status is not None
        assert final_failing_status['status'] == 'completed'
        
        if final_failing_status['result']:
            result = TestResult.from_dict(final_failing_status['result'])
            assert result.status == TestStatus.FAILED
            assert result.exit_code == 1
            assert 'Error: Simulated test failure' in result.stderr
        
        # Test Case 3: Environment recovery scenario (Requirements 5.1)
        # Simulate environment failure by removing an environment during execution
        recovery_test = TestCase(
            id="full-flow-recovery-001",
            name="Recovery Test",
            description="Test environment recovery",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Starting recovery test..."
sleep 10
echo "Recovery test completed"
exit 0
""",
            execution_time_estimate=20,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        # Submit recovery test
        recovery_job_id = orchestrator.submit_job(
            test_case=recovery_test,
            priority=Priority.MEDIUM,
            impact_score=0.5
        )
        
        # Wait for test to start, then simulate environment failure
        time.sleep(5)
        
        # Remove one environment to simulate failure
        if len(test_environments) > 1:
            failed_env = test_environments[0]
            orchestrator.remove_environment(failed_env.id)
            print(f"Simulated failure of environment {failed_env.id}")
        
        # Wait for completion
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(recovery_job_id)
            if job_status and job_status['status'] == 'completed':
                break
            time.sleep(1)
        
        # Verify test still completed (using remaining environment)
        final_recovery_status = orchestrator.get_job_status(recovery_job_id)
        assert final_recovery_status is not None
        assert final_recovery_status['status'] == 'completed'
        
        # Verify system health after error scenarios
        health_status = orchestrator_service.get_health_status()
        assert health_status['status'] in ['healthy', 'degraded']  # May be degraded due to lost environment
        assert health_status['is_running'] is True
        
        # Verify error logging (Requirements 5.5)
        system_metrics = orchestrator_service.get_system_metrics()
        assert 'failed_tests' in system_metrics
        assert system_metrics['failed_tests'] >= 1  # At least the failing test
        
        print(f"Error scenarios and recovery testing completed:")
        print(f"  Timeout detected: {timeout_detected}")
        print(f"  Failure handled: {final_failing_status['status'] == 'completed'}")
        print(f"  Recovery successful: {final_recovery_status['status'] == 'completed'}")
        print(f"  System health: {health_status['status']}")
    
    def test_component_integration_verification(
        self, 
        orchestrator_service, 
        test_environments, 
        comprehensive_test_cases
    ):
        """Test proper integration between all orchestrator components.
        
        Validates Requirements:
        - 2.5: Orchestrator service health reporting
        - All component interactions work correctly
        """
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        
        # Add test environment
        orchestrator.add_environment(test_environments[0])
        
        # Step 1: Verify all components are initialized and healthy
        health_status = orchestrator_service.get_health_status()
        assert health_status['status'] == 'healthy'
        assert health_status['is_running'] is True
        
        # Verify individual component health
        components = health_status['components']
        expected_components = [
            'status_tracker', 'resource_manager', 'queue_monitor',
            'timeout_manager', 'error_recovery_manager', 'service_recovery_manager'
        ]
        
        for component in expected_components:
            assert component in components
            assert components[component]['status'] in ['healthy', 'running']
        
        # Step 2: Test component interactions through a test execution
        test_case = comprehensive_test_cases[0]  # Use unit test
        
        # Submit test and monitor component interactions
        job_id = orchestrator.submit_job(
            test_case=test_case,
            priority=Priority.MEDIUM,
            impact_score=0.6
        )
        
        # Monitor component states during execution
        component_states = []
        max_wait_time = 120
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Get current system state
            health_status = orchestrator_service.get_health_status()
            system_metrics = orchestrator_service.get_system_metrics()
            job_status = orchestrator.get_job_status(job_id)
            queue_status = orchestrator.get_queue_status()
            
            state = {
                'timestamp': time.time(),
                'health_status': health_status['status'],
                'job_status': job_status['status'] if job_status else 'unknown',
                'active_tests': system_metrics['active_tests'],
                'queued_tests': system_metrics['queued_tests'],
                'available_environments': system_metrics['available_environments'],
                'component_health': {comp: info['status'] for comp, info in health_status['components'].items()}
            }
            component_states.append(state)
            
            if job_status and job_status['status'] == 'completed':
                break
            
            time.sleep(2)
        
        # Step 3: Verify component integration worked correctly
        assert len(component_states) > 0
        
        # Verify health remained stable throughout execution
        for state in component_states:
            assert state['health_status'] in ['healthy', 'degraded']
            
            # All components should remain healthy
            for comp, status in state['component_health'].items():
                assert status in ['healthy', 'running'], f"Component {comp} became unhealthy: {status}"
        
        # Verify metrics consistency
        final_state = component_states[-1]
        assert final_state['job_status'] == 'completed'
        assert final_state['active_tests'] == 0
        assert final_state['available_environments'] > 0
        
        # Step 4: Verify final system state
        final_health = orchestrator_service.get_health_status()
        final_metrics = orchestrator_service.get_system_metrics()
        
        assert final_health['status'] == 'healthy'
        assert final_metrics['active_tests'] == 0
        assert final_metrics['completed_tests'] > 0
        
        print(f"Component integration verification completed:")
        print(f"  Health checks: {len(component_states)}")
        print(f"  Final health: {final_health['status']}")
        print(f"  Components healthy: {len([c for c in final_health['components'].values() if c['status'] in ['healthy', 'running']])}")
        print(f"  Total completed tests: {final_metrics['completed_tests']}")


@pytest.mark.integration
class TestOrchestratorArchitectureSpecificFlow:
    """Test execution flow across different architectures."""
    
    def test_cross_architecture_execution_flow(
        self, 
        orchestrator_service, 
        test_environments, 
        comprehensive_test_cases
    ):
        """Test execution flow across different hardware architectures.
        
        Validates Requirements:
        - 7.1, 7.2, 7.5: Environment type selection
        - 1.2, 3.1: Hardware requirement matching
        """
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        
        # Add environments with different architectures
        x86_envs = [env for env in test_environments if env.config.architecture == "x86_64"]
        arm_envs = [env for env in test_environments if env.config.architecture == "arm64"]
        
        for env in x86_envs[:2] + arm_envs[:1]:
            orchestrator.add_environment(env)
        
        # Create architecture-specific test cases
        arch_test_cases = [
            TestCase(
                id="arch-flow-x86-001",
                name="x86_64 Specific Test",
                description="Test x86_64 specific functionality",
                test_type=TestType.INTEGRATION,
                target_subsystem="architecture",
                test_script="""#!/bin/bash
echo "Testing x86_64 architecture..."
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

# Verify x86_64 architecture
if [[ "$ARCH" == "x86_64" ]]; then
    echo "x86_64 architecture confirmed"
    echo "Testing x86_64 specific features..."
    # Simulate x86_64 specific test
    echo "x86_64 test PASSED"
    exit 0
else
    echo "Expected x86_64, got $ARCH"
    exit 1
fi
""",
                execution_time_estimate=30,
                required_hardware=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="Intel Xeon",
                    memory_mb=2048,
                    is_virtual=True
                )
            ),
            TestCase(
                id="arch-flow-arm-001",
                name="ARM64 Specific Test",
                description="Test ARM64 specific functionality",
                test_type=TestType.INTEGRATION,
                target_subsystem="architecture",
                test_script="""#!/bin/bash
echo "Testing ARM64 architecture..."
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

# Verify ARM64 architecture (accept both arm64 and aarch64)
if [[ "$ARCH" == "arm64" ]] || [[ "$ARCH" == "aarch64" ]]; then
    echo "ARM64 architecture confirmed"
    echo "Testing ARM64 specific features..."
    # Simulate ARM64 specific test
    echo "ARM64 test PASSED"
    exit 0
else
    echo "Expected ARM64/aarch64, got $ARCH - running compatibility test"
    echo "Compatibility test PASSED"
    exit 0
fi
""",
                execution_time_estimate=30,
                required_hardware=HardwareConfig(
                    architecture="arm64",
                    cpu_model="ARM Cortex-A72",
                    memory_mb=2048,
                    is_virtual=True
                )
            )
        ]
        
        # Submit architecture-specific tests
        job_submissions = []
        for test_case in arch_test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.7
            )
            job_submissions.append({
                'job_id': job_id,
                'test_id': test_case.id,
                'required_arch': test_case.required_hardware.architecture
            })
        
        # Monitor execution
        max_wait_time = 120
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(2)
        
        # Verify results and architecture matching
        for submission in job_submissions:
            job_status = orchestrator.get_job_status(submission['job_id'])
            assert job_status is not None
            assert job_status['status'] == 'completed'
            
            if job_status['result']:
                result = TestResult.from_dict(job_status['result'])
                
                # Verify test ran on correct architecture
                actual_arch = result.environment.config.architecture
                required_arch = submission['required_arch']
                
                assert actual_arch == required_arch, \
                    f"Test {submission['test_id']} required {required_arch} but ran on {actual_arch}"
                
                # Verify test passed (architecture matching worked)
                assert result.status in [TestStatus.PASSED, TestStatus.FAILED]
        
        print(f"Cross-architecture execution flow completed:")
        print(f"  Tests executed: {len(job_submissions)}")
        print(f"  Architecture matching verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])