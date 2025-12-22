"""Comprehensive integration tests for the test execution orchestrator.

This module provides integration tests that validate the complete orchestrator
functionality including:
- Full execution flow from submission to completion
- API integration with orchestrator service
- Load testing for concurrent execution scenarios
- Error handling and recovery workflows
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

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, TestType, RiskLevel, FailureInfo
)
from orchestrator.service import OrchestratorService
from orchestrator.config import OrchestratorConfig
from orchestrator.scheduler import TestOrchestrator, Priority
from orchestrator.status_tracker import StatusTracker
from api.orchestrator_integration import start_orchestrator, stop_orchestrator, get_orchestrator
from api.client import AgenticTestingClient


@pytest.fixture
def temp_orchestrator_config(tmp_path):
    """Create temporary orchestrator configuration for testing."""
    config = OrchestratorConfig(
        poll_interval=0.5,  # Fast polling for tests
        default_timeout=30,  # Short timeout for tests
        max_concurrent_tests=5,
        enable_persistence=True,
        state_file=str(tmp_path / "orchestrator_state.json"),
        log_level="DEBUG"
    )
    return config


@pytest.fixture
def orchestrator_service(temp_orchestrator_config):
    """Create and manage orchestrator service for testing."""
    service = OrchestratorService(temp_orchestrator_config)
    
    # Start the service
    assert service.start(), "Failed to start orchestrator service"
    
    yield service
    
    # Clean up
    service.stop()


@pytest.fixture
def test_environments():
    """Create test environments for orchestrator testing."""
    return [
        Environment(
            id="test-env-x86-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        ),
        Environment(
            id="test-env-x86-2",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=4096,
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        ),
        Environment(
            id="test-env-arm-1",
            config=HardwareConfig(
                architecture="arm64",
                cpu_model="ARM Cortex-A72",
                memory_mb=2048,
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        )
    ]


@pytest.fixture
def sample_test_cases():
    """Create sample test cases for orchestrator testing."""
    return [
        TestCase(
            id="integration-test-001",
            name="Quick Integration Test",
            description="Fast test for integration testing",
            test_type=TestType.INTEGRATION,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Integration test starting..."
sleep 2
echo "Integration test completed successfully"
exit 0
""",
            execution_time_estimate=10,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        ),
        TestCase(
            id="integration-test-002",
            name="Medium Integration Test",
            description="Medium duration test for integration testing",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Medium test starting..."
sleep 5
echo "Medium test completed successfully"
exit 0
""",
            execution_time_estimate=15,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            )
        ),
        TestCase(
            id="integration-test-003",
            name="ARM Integration Test",
            description="Test for ARM architecture",
            test_type=TestType.INTEGRATION,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "ARM test starting..."
uname -m
sleep 3
echo "ARM test completed successfully"
exit 0
""",
            execution_time_estimate=12,
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
    """Test complete execution flow from submission to completion."""
    
    def test_single_test_execution_flow(self, orchestrator_service, test_environments, sample_test_cases):
        """Test complete flow for a single test execution.
        
        This test validates:
        1. Test submission to orchestrator
        2. Environment allocation
        3. Test execution
        4. Result collection
        5. Resource cleanup
        """
        # Add test environment to orchestrator
        orchestrator = TestOrchestrator()
        orchestrator.add_environment(test_environments[0])
        
        # Submit test case
        test_case = sample_test_cases[0]
        job_id = orchestrator.submit_job(
            test_case=test_case,
            priority=Priority.HIGH,
            impact_score=0.8
        )
        
        assert job_id is not None
        assert isinstance(job_id, str)
        
        # Monitor execution
        max_wait_time = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(job_id)
            assert job_status is not None
            
            if job_status['status'] == 'completed':
                break
            elif job_status['status'] == 'running':
                # Verify active test tracking
                queue_status = orchestrator.get_queue_status()
                assert queue_status['running_jobs'] > 0
            
            time.sleep(1)
        
        # Verify final status
        final_status = orchestrator.get_job_status(job_id)
        assert final_status is not None
        assert final_status['status'] == 'completed'
        assert final_status['result'] is not None
        
        # Verify result details
        result = TestResult.from_dict(final_status['result'])
        assert result.test_id == test_case.id
        assert result.status in [TestStatus.PASSED, TestStatus.FAILED]
        assert result.execution_time > 0
        assert result.environment is not None
        
        # Verify resource cleanup
        final_queue_status = orchestrator.get_queue_status()
        assert final_queue_status['running_jobs'] == 0
        assert final_queue_status['available_environments'] == 1
    
    def test_multiple_test_execution_flow(self, orchestrator_service, test_environments, sample_test_cases):
        """Test execution flow for multiple tests."""
        orchestrator = TestOrchestrator()
        
        # Add multiple environments
        for env in test_environments[:2]:
            orchestrator.add_environment(env)
        
        # Submit multiple test cases
        job_ids = []
        for test_case in sample_test_cases[:2]:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.6
            )
            job_ids.append(job_id)
        
        # Monitor execution
        max_wait_time = 45
        start_time = time.time()
        completed_jobs = set()
        
        while time.time() - start_time < max_wait_time:
            all_completed = True
            
            for job_id in job_ids:
                if job_id not in completed_jobs:
                    job_status = orchestrator.get_job_status(job_id)
                    if job_status['status'] == 'completed':
                        completed_jobs.add(job_id)
                    else:
                        all_completed = False
            
            if all_completed:
                break
            
            time.sleep(1)
        
        # Verify all jobs completed
        assert len(completed_jobs) == len(job_ids)
        
        # Verify results
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            assert job_status['status'] == 'completed'
            assert job_status['result'] is not None
        
        # Verify final cleanup
        final_queue_status = orchestrator.get_queue_status()
        assert final_queue_status['running_jobs'] == 0
        assert final_queue_status['pending_jobs'] == 0
    
    def test_priority_based_execution_flow(self, orchestrator_service, test_environments, sample_test_cases):
        """Test that high priority tests execute before low priority tests."""
        orchestrator = TestOrchestrator()
        
        # Add single environment to force queuing
        orchestrator.add_environment(test_environments[0])
        
        # Submit tests with different priorities
        low_priority_job = orchestrator.submit_job(
            test_case=sample_test_cases[0],
            priority=Priority.LOW,
            impact_score=0.3
        )
        
        high_priority_job = orchestrator.submit_job(
            test_case=sample_test_cases[1],
            priority=Priority.HIGH,
            impact_score=0.9
        )
        
        # Monitor execution order
        execution_order = []
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            for job_id in [low_priority_job, high_priority_job]:
                job_status = orchestrator.get_job_status(job_id)
                if (job_status['status'] == 'running' and 
                    job_id not in execution_order):
                    execution_order.append(job_id)
            
            # Check if both completed
            queue_status = orchestrator.get_queue_status()
            if (queue_status['running_jobs'] == 0 and 
                queue_status['pending_jobs'] == 0):
                break
            
            time.sleep(0.5)
        
        # Verify high priority executed first
        assert len(execution_order) >= 1
        assert execution_order[0] == high_priority_job
    
    def test_architecture_specific_execution_flow(self, orchestrator_service, test_environments, sample_test_cases):
        """Test execution flow with architecture-specific requirements."""
        orchestrator = TestOrchestrator()
        
        # Add environments with different architectures
        for env in test_environments:
            orchestrator.add_environment(env)
        
        # Submit ARM-specific test
        arm_test = sample_test_cases[2]  # ARM test
        job_id = orchestrator.submit_job(
            test_case=arm_test,
            priority=Priority.MEDIUM,
            impact_score=0.7
        )
        
        # Monitor execution
        max_wait_time = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(job_id)
            if job_status['status'] == 'completed':
                break
            time.sleep(1)
        
        # Verify execution completed
        final_status = orchestrator.get_job_status(job_id)
        assert final_status['status'] == 'completed'
        
        # Verify correct architecture was used
        result = TestResult.from_dict(final_status['result'])
        assert result.environment.config.architecture == "arm64"


@pytest.mark.integration
class TestOrchestratorAPIIntegration:
    """Test orchestrator integration with the API server."""
    
    @patch('api.orchestrator_integration._orchestrator')
    def test_orchestrator_startup_integration(self, mock_orchestrator):
        """Test orchestrator startup integration with API server."""
        # Mock orchestrator service
        mock_service = Mock()
        mock_service.start.return_value = True
        mock_service.is_running = True
        mock_orchestrator.return_value = mock_service
        
        # Test startup
        result = start_orchestrator()
        assert result is True
        mock_service.start.assert_called_once()
    
    @patch('api.orchestrator_integration._orchestrator')
    def test_orchestrator_shutdown_integration(self, mock_orchestrator):
        """Test orchestrator shutdown integration with API server."""
        # Mock orchestrator service
        mock_service = Mock()
        mock_service.stop.return_value = True
        mock_service.is_running = False
        mock_orchestrator.return_value = mock_service
        
        # Test shutdown
        result = stop_orchestrator()
        assert result is True
        mock_service.stop.assert_called_once()
    
    def test_orchestrator_health_status_integration(self, orchestrator_service):
        """Test health status reporting integration."""
        health_status = orchestrator_service.get_health_status()
        
        # Verify health status structure
        assert 'status' in health_status
        assert 'is_running' in health_status
        assert 'uptime_seconds' in health_status
        assert 'components' in health_status
        
        # Verify component health
        components = health_status['components']
        expected_components = [
            'status_tracker', 'resource_manager', 'queue_monitor',
            'timeout_manager', 'error_recovery_manager', 'service_recovery_manager'
        ]
        
        for component in expected_components:
            assert component in components
            assert 'status' in components[component]
    
    def test_orchestrator_metrics_integration(self, orchestrator_service):
        """Test system metrics reporting integration."""
        metrics = orchestrator_service.get_system_metrics()
        
        # Verify metrics structure
        expected_metrics = [
            'active_tests', 'queued_tests', 'completed_tests',
            'failed_tests', 'total_processed', 'available_environments',
            'uptime_seconds'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
            assert metrics[metric] >= 0
    
    def test_status_tracker_integration(self, orchestrator_service):
        """Test status tracker integration with orchestrator."""
        status_tracker = orchestrator_service.status_tracker
        
        # Test status updates
        test_id = "integration-test-status-001"
        
        # Update test status
        assert status_tracker.update_test_status(test_id, 'queued')
        assert status_tracker.update_test_status(test_id, 'running')
        assert status_tracker.update_test_status(test_id, 'completed')
        
        # Verify status retrieval
        test_status = status_tracker.get_test_status(test_id)
        assert test_status is not None
        assert test_status.test_id == test_id
        assert test_status.status == 'completed'
        
        # Verify metrics
        metrics = status_tracker.get_system_metrics()
        assert 'active_tests' in metrics
        assert 'completed_tests' in metrics


@pytest.mark.integration
class TestOrchestratorLoadTesting:
    """Test orchestrator under concurrent execution scenarios."""
    
    def test_concurrent_test_execution_load(self, orchestrator_service, test_environments):
        """Test orchestrator performance under concurrent test load."""
        orchestrator = TestOrchestrator()
        
        # Add all test environments
        for env in test_environments:
            orchestrator.add_environment(env)
        
        # Create multiple test cases
        test_cases = []
        for i in range(10):  # 10 concurrent tests
            test_case = TestCase(
                id=f"load-test-{i:03d}",
                name=f"Load Test {i}",
                description=f"Load testing test case {i}",
                test_type=TestType.UNIT,
                target_subsystem="testing",
                test_script=f"""#!/bin/bash
echo "Load test {i} starting..."
sleep $((RANDOM % 5 + 1))  # Random 1-5 second execution
echo "Load test {i} completed"
exit 0
""",
                execution_time_estimate=10,
                required_hardware=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="Intel Xeon",
                    memory_mb=1024,
                    is_virtual=True
                )
            )
            test_cases.append(test_case)
        
        # Submit all tests
        job_ids = []
        start_time = time.time()
        
        for test_case in test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_ids.append(job_id)
        
        submission_time = time.time() - start_time
        
        # Monitor concurrent execution
        max_concurrent = 0
        max_wait_time = 120  # 2 minutes for load test
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            current_running = queue_status['running_jobs']
            max_concurrent = max(max_concurrent, current_running)
            
            # Check if all completed
            if (queue_status['running_jobs'] == 0 and 
                queue_status['pending_jobs'] == 0):
                break
            
            time.sleep(0.5)
        
        execution_time = time.time() - start_time
        
        # Verify all jobs completed
        completed_count = 0
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status['status'] == 'completed':
                completed_count += 1
        
        # Performance assertions
        assert completed_count == len(job_ids), f"Only {completed_count}/{len(job_ids)} tests completed"
        assert max_concurrent > 1, "Tests should run concurrently"
        assert max_concurrent <= len(test_environments), "Should not exceed available environments"
        assert submission_time < 5.0, f"Submission took too long: {submission_time:.2f}s"
        assert execution_time < 60.0, f"Execution took too long: {execution_time:.2f}s"
        
        print(f"Load test results:")
        print(f"  Tests submitted: {len(job_ids)}")
        print(f"  Tests completed: {completed_count}")
        print(f"  Max concurrent: {max_concurrent}")
        print(f"  Submission time: {submission_time:.2f}s")
        print(f"  Total execution time: {execution_time:.2f}s")
    
    def test_priority_contention_load(self, orchestrator_service, test_environments):
        """Test orchestrator under priority contention scenarios."""
        orchestrator = TestOrchestrator()
        
        # Add limited environments to create contention
        for env in test_environments[:2]:  # Only 2 environments
            orchestrator.add_environment(env)
        
        # Create tests with different priorities
        high_priority_tests = []
        low_priority_tests = []
        
        for i in range(3):
            # High priority tests
            high_test = TestCase(
                id=f"high-priority-{i}",
                name=f"High Priority Test {i}",
                description=f"High priority test {i}",
                test_type=TestType.INTEGRATION,
                target_subsystem="testing",
                test_script=f"""#!/bin/bash
echo "High priority test {i} executing..."
sleep 3
echo "High priority test {i} completed"
exit 0
""",
                execution_time_estimate=8,
                required_hardware=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="Intel Xeon",
                    memory_mb=1024,
                    is_virtual=True
                )
            )
            high_priority_tests.append(high_test)
            
            # Low priority tests
            low_test = TestCase(
                id=f"low-priority-{i}",
                name=f"Low Priority Test {i}",
                description=f"Low priority test {i}",
                test_type=TestType.UNIT,
                target_subsystem="testing",
                test_script=f"""#!/bin/bash
echo "Low priority test {i} executing..."
sleep 2
echo "Low priority test {i} completed"
exit 0
""",
                execution_time_estimate=5,
                required_hardware=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="Intel Xeon",
                    memory_mb=1024,
                    is_virtual=True
                )
            )
            low_priority_tests.append(low_test)
        
        # Submit low priority tests first
        low_job_ids = []
        for test_case in low_priority_tests:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.LOW,
                impact_score=0.3
            )
            low_job_ids.append(job_id)
        
        # Brief delay, then submit high priority tests
        time.sleep(1)
        
        high_job_ids = []
        for test_case in high_priority_tests:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.HIGH,
                impact_score=0.9
            )
            high_job_ids.append(job_id)
        
        # Monitor execution order
        execution_order = []
        max_wait_time = 90
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check for newly running jobs
            for job_id in high_job_ids + low_job_ids:
                if job_id not in execution_order:
                    job_status = orchestrator.get_job_status(job_id)
                    if job_status['status'] == 'running':
                        execution_order.append(job_id)
            
            # Check if all completed
            queue_status = orchestrator.get_queue_status()
            if (queue_status['running_jobs'] == 0 and 
                queue_status['pending_jobs'] == 0):
                break
            
            time.sleep(0.5)
        
        # Verify priority ordering
        high_priority_positions = [execution_order.index(job_id) 
                                 for job_id in high_job_ids 
                                 if job_id in execution_order]
        low_priority_positions = [execution_order.index(job_id) 
                                for job_id in low_job_ids 
                                if job_id in execution_order]
        
        if high_priority_positions and low_priority_positions:
            avg_high_position = sum(high_priority_positions) / len(high_priority_positions)
            avg_low_position = sum(low_priority_positions) / len(low_priority_positions)
            
            # High priority tests should generally execute earlier
            assert avg_high_position < avg_low_position, \
                f"High priority avg position ({avg_high_position}) should be less than low priority ({avg_low_position})"
    
    def test_resource_exhaustion_handling(self, orchestrator_service, test_environments):
        """Test orchestrator behavior when resources are exhausted."""
        orchestrator = TestOrchestrator()
        
        # Add single environment to force resource exhaustion
        orchestrator.add_environment(test_environments[0])
        
        # Create long-running test cases
        long_running_tests = []
        for i in range(5):  # 5 tests, 1 environment
            test_case = TestCase(
                id=f"long-running-{i}",
                name=f"Long Running Test {i}",
                description=f"Long running test {i}",
                test_type=TestType.INTEGRATION,
                target_subsystem="testing",
                test_script=f"""#!/bin/bash
echo "Long running test {i} starting..."
sleep 10  # 10 second execution
echo "Long running test {i} completed"
exit 0
""",
                execution_time_estimate=15,
                required_hardware=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="Intel Xeon",
                    memory_mb=1024,
                    is_virtual=True
                )
            )
            long_running_tests.append(test_case)
        
        # Submit all tests
        job_ids = []
        for test_case in long_running_tests:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_ids.append(job_id)
        
        # Monitor resource utilization
        max_running = 0
        max_pending = 0
        max_wait_time = 120
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            max_running = max(max_running, queue_status['running_jobs'])
            max_pending = max(max_pending, queue_status['pending_jobs'])
            
            if (queue_status['running_jobs'] == 0 and 
                queue_status['pending_jobs'] == 0):
                break
            
            time.sleep(1)
        
        # Verify resource constraints were respected
        assert max_running <= 1, f"Should not exceed 1 concurrent test, got {max_running}"
        assert max_pending > 0, "Should have queued tests when resource exhausted"
        
        # Verify all tests eventually completed
        completed_count = 0
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status['status'] == 'completed':
                completed_count += 1
        
        assert completed_count == len(job_ids), f"Only {completed_count}/{len(job_ids)} tests completed"


@pytest.mark.integration
class TestOrchestratorErrorHandling:
    """Test orchestrator error handling and recovery scenarios."""
    
    def test_test_timeout_handling(self, orchestrator_service, test_environments):
        """Test orchestrator handling of test timeouts."""
        orchestrator = TestOrchestrator()
        orchestrator.add_environment(test_environments[0])
        
        # Create test that will timeout
        timeout_test = TestCase(
            id="timeout-test-001",
            name="Timeout Test",
            description="Test that will timeout",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Starting long running test..."
sleep 60  # Sleep longer than timeout
echo "This should not be reached"
exit 0
""",
            execution_time_estimate=5,  # Short timeout
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        # Submit test
        job_id = orchestrator.submit_job(
            test_case=timeout_test,
            priority=Priority.MEDIUM,
            impact_score=0.5
        )
        
        # Monitor for timeout
        max_wait_time = 30  # Wait for timeout to occur
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(job_id)
            if job_status['status'] in ['completed', 'timeout', 'failed']:
                break
            time.sleep(1)
        
        # Verify timeout was handled
        final_status = orchestrator.get_job_status(job_id)
        assert final_status['status'] in ['timeout', 'failed']
        
        # Verify resource cleanup
        queue_status = orchestrator.get_queue_status()
        assert queue_status['running_jobs'] == 0
        assert queue_status['available_environments'] == 1
    
    def test_environment_failure_recovery(self, orchestrator_service, test_environments):
        """Test orchestrator recovery from environment failures."""
        orchestrator = TestOrchestrator()
        
        # Add environments
        for env in test_environments[:2]:
            orchestrator.add_environment(env)
        
        # Create test case
        test_case = TestCase(
            id="env-failure-test-001",
            name="Environment Failure Test",
            description="Test environment failure handling",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Test executing..."
sleep 2
echo "Test completed"
exit 0
""",
            execution_time_estimate=10,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        # Submit test
        job_id = orchestrator.submit_job(
            test_case=test_case,
            priority=Priority.MEDIUM,
            impact_score=0.5
        )
        
        # Simulate environment failure by removing environment
        # (In real scenario, this would be detected by health checks)
        time.sleep(2)  # Let test start
        
        # Remove one environment to simulate failure
        orchestrator.remove_environment(test_environments[0].id)
        
        # Monitor execution
        max_wait_time = 30
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(job_id)
            if job_status['status'] == 'completed':
                break
            time.sleep(1)
        
        # Verify test still completed (using remaining environment)
        final_status = orchestrator.get_job_status(job_id)
        assert final_status['status'] == 'completed'
    
    def test_service_recovery_after_restart(self, temp_orchestrator_config, test_environments):
        """Test orchestrator service recovery after restart."""
        # Create first service instance
        service1 = OrchestratorService(temp_orchestrator_config)
        assert service1.start()
        
        # Submit some work
        orchestrator = TestOrchestrator()
        orchestrator.add_environment(test_environments[0])
        
        test_case = TestCase(
            id="recovery-test-001",
            name="Recovery Test",
            description="Test for service recovery",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
echo "Recovery test executing..."
sleep 5
echo "Recovery test completed"
exit 0
""",
            execution_time_estimate=10,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        job_id = orchestrator.submit_job(
            test_case=test_case,
            priority=Priority.MEDIUM,
            impact_score=0.5
        )
        
        # Stop first service
        service1.stop()
        
        # Create second service instance (simulating restart)
        service2 = OrchestratorService(temp_orchestrator_config)
        assert service2.start()
        
        # Verify service recovered
        health_status = service2.get_health_status()
        assert health_status['status'] == 'healthy'
        assert health_status['is_running'] is True
        
        # Clean up
        service2.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])