"""Comprehensive load testing for the test execution orchestrator.

This module implements task 9.2 from the test-execution-orchestrator spec:
- Test system behavior under high concurrent test loads
- Verify resource management under stress conditions
- Test system stability and performance characteristics
- Requirements: 2.4, 5.4

This test suite validates the orchestrator's ability to handle high-scale
concurrent execution scenarios and maintain stability under stress.
"""

import pytest
import asyncio
import time
import uuid
import threading
import statistics
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
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
def load_test_orchestrator_config(tmp_path):
    """Create orchestrator configuration optimized for load testing."""
    config = OrchestratorConfig(
        poll_interval=0.1,  # Very fast polling for load tests
        default_timeout=120,  # Longer timeout for load tests
        max_concurrent_tests=50,  # High concurrency limit
        enable_persistence=True,
        state_file=str(tmp_path / "load_test_orchestrator_state.json"),
        log_level="INFO"  # Reduce log noise during load tests
    )
    return config


@pytest.fixture
def load_test_orchestrator_service(load_test_orchestrator_config):
    """Create orchestrator service optimized for load testing."""
    service = OrchestratorService(load_test_orchestrator_config)
    
    # Start the service
    assert service.start(), "Failed to start load test orchestrator service"
    
    # Verify service is healthy
    health_status = service.get_health_status()
    assert health_status['status'] == 'healthy'
    assert health_status['is_running'] is True
    
    yield service
    
    # Clean up
    service.stop()


@pytest.fixture
def load_test_environments():
    """Create large pool of test environments for load testing."""
    environments = []
    
    # Create 20 x86_64 environments with varying specs
    for i in range(20):
        env = Environment(
            id=f"load-test-x86-{i+1:02d}",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model=f"Intel Xeon E5-{2680 + (i % 5)}",
                memory_mb=1024 * (2 ** (i % 4)),  # 1GB, 2GB, 4GB, 8GB
                storage_type="ssd" if i % 2 == 0 else "nvme",
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        )
        environments.append(env)
    
    # Create 10 ARM64 environments
    for i in range(10):
        env = Environment(
            id=f"load-test-arm-{i+1:02d}",
            config=HardwareConfig(
                architecture="arm64",
                cpu_model=f"ARM Cortex-A{72 + (i % 3) * 6}",
                memory_mb=2048 * (1 + i % 3),  # 2GB, 4GB, 6GB
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        )
        environments.append(env)
    
    # Create 5 Docker environments for lightweight tests
    for i in range(5):
        env = Environment(
            id=f"load-test-docker-{i+1:02d}",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Core i7",
                memory_mb=1024 + (i * 512),  # 1GB to 3GB
                storage_type="ssd",
                is_virtual=True,
                emulator="docker"
            ),
            status=EnvironmentStatus.IDLE
        )
        environments.append(env)
    
    return environments


def create_load_test_case(
    test_id: str, 
    duration: int = 5, 
    architecture: str = "x86_64",
    test_type: TestType = TestType.UNIT,
    memory_mb: int = 1024,
    should_fail: bool = False,
    cpu_intensive: bool = False
) -> TestCase:
    """Create a test case for load testing with specified characteristics."""
    
    exit_code = 1 if should_fail else 0
    
    # Create different test scripts based on characteristics
    if cpu_intensive:
        test_script = f"""#!/bin/bash
echo "CPU intensive load test {test_id} starting..."
echo "Architecture: {architecture}"
echo "Duration: {duration}s"

# CPU intensive work
python3 -c "
import time
import math

start_time = time.time()
iterations = 0

while time.time() - start_time < {duration}:
    # CPU intensive calculation
    for i in range(10000):
        math.sqrt(i * math.pi)
    iterations += 1

print(f'Completed {{iterations}} iterations of CPU intensive work')
print('CPU intensive test {'failed' if should_fail else 'completed'}')
"

exit {exit_code}
"""
    else:
        test_script = f"""#!/bin/bash
echo "Load test {test_id} starting..."
echo "Architecture: {architecture}"
echo "Duration: {duration}s"
echo "Memory requirement: {memory_mb}MB"

# Simulate work with memory allocation
python3 -c "
import time
import sys

try:
    # Allocate some memory
    data = bytearray({memory_mb} * 1024)
    print(f'Allocated {memory_mb}MB of memory')
    
    # Simulate work
    for i in range({duration}):
        time.sleep(1)
        if i % 2 == 0:
            print(f'Working... {{i+1}}/{duration}')
    
    print('Load test {'failed' if should_fail else 'completed'}')
    sys.exit({exit_code})
except Exception as e:
    print(f'Load test failed: {{e}}')
    sys.exit(1)
"
"""
    
    return TestCase(
        id=test_id,
        name=f"Load Test {test_id}",
        description=f"Load testing test case {test_id}",
        test_type=test_type,
        target_subsystem="load_testing",
        test_script=test_script,
        execution_time_estimate=duration + 10,
        required_hardware=HardwareConfig(
            architecture=architecture,
            cpu_model="generic",
            memory_mb=memory_mb,
            is_virtual=True
        )
    )


@pytest.mark.integration
@pytest.mark.slow
class TestOrchestratorHighConcurrencyLoad:
    """Test orchestrator behavior under high concurrent test loads."""
    
    def test_high_volume_concurrent_execution(
        self, 
        load_test_orchestrator_service, 
        load_test_environments
    ):
        """Test system behavior with high volume of concurrent tests.
        
        Validates Requirements:
        - 2.4: Resource utilization tracking during multiple concurrent tests
        - 5.4: Proper queuing when resource limits are exceeded
        """
        orchestrator = TestOrchestrator()
        
        # Add all environments for maximum concurrency
        for env in load_test_environments:
            orchestrator.add_environment(env)
        
        total_environments = len(load_test_environments)
        
        # Create large number of test cases (3x environment capacity)
        test_cases = []
        total_tests = total_environments * 3  # 105 tests for 35 environments
        
        for i in range(total_tests):
            # Vary test characteristics
            duration = random.randint(3, 15)  # 3-15 second tests
            architecture = random.choice(["x86_64", "arm64"])
            test_type = random.choice([TestType.UNIT, TestType.INTEGRATION, TestType.PERFORMANCE])
            memory_mb = random.choice([512, 1024, 2048, 4096])
            should_fail = (i % 50) == 0  # 2% failure rate
            cpu_intensive = (i % 20) == 0  # 5% CPU intensive tests
            
            test_case = create_load_test_case(
                test_id=f"high-volume-{i:03d}",
                duration=duration,
                architecture=architecture,
                test_type=test_type,
                memory_mb=memory_mb,
                should_fail=should_fail,
                cpu_intensive=cpu_intensive
            )
            test_cases.append(test_case)
        
        # Submit all tests rapidly
        job_ids = []
        submission_start = time.time()
        
        for test_case in test_cases:
            # Vary priorities
            priority = random.choice([Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL])
            impact_score = random.uniform(0.1, 1.0)
            
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=priority,
                impact_score=impact_score
            )
            job_ids.append(job_id)
        
        submission_time = time.time() - submission_start
        
        # Monitor execution metrics
        execution_metrics = []
        max_concurrent = 0
        max_queued = 0
        max_wait_time = 600  # 10 minutes for high volume test
        execution_start = time.time()
        
        while time.time() - execution_start < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            
            current_running = queue_status['running_jobs']
            current_queued = queue_status['pending_jobs']
            
            max_concurrent = max(max_concurrent, current_running)
            max_queued = max(max_queued, current_queued)
            
            # Collect detailed metrics (Requirements 2.4)
            metrics = {
                'timestamp': time.time() - execution_start,
                'running_jobs': current_running,
                'pending_jobs': current_queued,
                'available_environments': queue_status['available_environments'],
                'allocated_environments': queue_status['allocated_environments'],
                'utilization_rate': queue_status['allocated_environments'] / total_environments
            }
            execution_metrics.append(metrics)
            
            # Check completion
            if current_running == 0 and current_queued == 0:
                break
            
            time.sleep(2)  # Sample every 2 seconds
        
        total_execution_time = time.time() - execution_start
        
        # Collect final results
        completed_count = 0
        passed_count = 0
        failed_count = 0
        timeout_count = 0
        
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] == 'completed':
                completed_count += 1
                if job_status['result']:
                    result = TestResult.from_dict(job_status['result'])
                    if result.status == TestStatus.PASSED:
                        passed_count += 1
                    elif result.status == TestStatus.FAILED:
                        failed_count += 1
                    elif result.status == TestStatus.TIMEOUT:
                        timeout_count += 1
        
        # Performance assertions
        assert completed_count >= total_tests * 0.95, f"Should complete at least 95% of tests, got {completed_count}/{total_tests}"
        assert max_concurrent > total_environments * 0.8, f"Should achieve high concurrency, got {max_concurrent}"
        assert max_concurrent <= total_environments, f"Should not exceed environment limit, got {max_concurrent}/{total_environments}"
        assert max_queued > 0, "Should have queued tests when at capacity (Requirement 5.4)"
        assert submission_time < 30.0, f"Submission took too long: {submission_time:.2f}s"
        
        # Resource utilization analysis (Requirements 2.4)
        if execution_metrics:
            peak_utilization = max(m['utilization_rate'] for m in execution_metrics)
            avg_utilization = statistics.mean(m['utilization_rate'] for m in execution_metrics)
            
            assert peak_utilization >= 0.9, f"Should achieve high peak utilization: {peak_utilization:.2%}"
            assert avg_utilization >= 0.6, f"Should maintain good average utilization: {avg_utilization:.2%}"
        
        print(f"\nHigh Volume Concurrent Execution Results:")
        print(f"  Total tests: {total_tests}")
        print(f"  Completed: {completed_count}")
        print(f"  Passed: {passed_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Timeouts: {timeout_count}")
        print(f"  Max concurrent: {max_concurrent}")
        print(f"  Max queued: {max_queued}")
        print(f"  Peak utilization: {peak_utilization:.2%}")
        print(f"  Avg utilization: {avg_utilization:.2%}")
        print(f"  Submission time: {submission_time:.2f}s")
        print(f"  Total execution time: {total_execution_time:.2f}s")
    
    def test_burst_load_handling(
        self, 
        load_test_orchestrator_service, 
        load_test_environments
    ):
        """Test system behavior under burst load scenarios."""
        orchestrator = TestOrchestrator()
        
        # Add subset of environments to create resource pressure
        for env in load_test_environments[:10]:  # Use only 10 environments
            orchestrator.add_environment(env)
        
        # Create burst scenarios
        burst_scenarios = [
            {"name": "Initial Burst", "count": 25, "delay": 0},
            {"name": "Secondary Burst", "count": 20, "delay": 30},
            {"name": "Final Burst", "count": 15, "delay": 60}
        ]
        
        all_job_ids = []
        burst_metrics = []
        
        test_start = time.time()
        
        for scenario in burst_scenarios:
            # Wait for scenario timing
            while time.time() - test_start < scenario["delay"]:
                time.sleep(1)
            
            # Submit burst of tests
            burst_start = time.time()
            burst_job_ids = []
            
            for i in range(scenario["count"]):
                test_case = create_load_test_case(
                    test_id=f"burst-{scenario['name'].lower().replace(' ', '-')}-{i:02d}",
                    duration=random.randint(5, 20),
                    architecture=random.choice(["x86_64", "arm64"]),
                    test_type=TestType.UNIT
                )
                
                job_id = orchestrator.submit_job(
                    test_case=test_case,
                    priority=Priority.HIGH,
                    impact_score=0.8
                )
                burst_job_ids.append(job_id)
                all_job_ids.append(job_id)
            
            burst_submission_time = time.time() - burst_start
            
            # Monitor immediate response to burst
            queue_status = orchestrator.get_queue_status()
            burst_metrics.append({
                'scenario': scenario['name'],
                'count': scenario['count'],
                'submission_time': burst_submission_time,
                'immediate_running': queue_status['running_jobs'],
                'immediate_queued': queue_status['pending_jobs'],
                'immediate_utilization': queue_status['allocated_environments'] / 10
            })
            
            print(f"Submitted {scenario['name']}: {scenario['count']} tests in {burst_submission_time:.2f}s")
        
        # Monitor overall execution
        max_wait_time = 300  # 5 minutes
        execution_start = time.time()
        
        while time.time() - execution_start < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(2)
        
        total_execution_time = time.time() - execution_start
        
        # Verify burst handling
        total_submitted = sum(s['count'] for s in burst_scenarios)
        completed_count = sum(1 for job_id in all_job_ids 
                            if orchestrator.get_job_status(job_id)['status'] == 'completed')
        
        assert completed_count >= total_submitted * 0.95, f"Should complete most burst tests: {completed_count}/{total_submitted}"
        
        # Verify burst response times
        for metrics in burst_metrics:
            assert metrics['submission_time'] < 10.0, f"{metrics['scenario']} submission too slow: {metrics['submission_time']:.2f}s"
            assert metrics['immediate_running'] > 0, f"{metrics['scenario']} should start tests immediately"
        
        print(f"\nBurst Load Handling Results:")
        for metrics in burst_metrics:
            print(f"  {metrics['scenario']}: {metrics['count']} tests, {metrics['submission_time']:.2f}s submission")
        print(f"  Total completed: {completed_count}/{total_submitted}")
        print(f"  Total execution time: {total_execution_time:.2f}s")
    
    def test_sustained_load_stability(
        self, 
        load_test_orchestrator_service, 
        load_test_environments
    ):
        """Test system stability under sustained high load."""
        orchestrator = TestOrchestrator()
        
        # Add all environments
        for env in load_test_environments:
            orchestrator.add_environment(env)
        
        # Run sustained load for extended period
        test_duration = 180  # 3 minutes of sustained load
        submission_rate = 2  # 2 tests per second
        total_expected_tests = test_duration * submission_rate
        
        submitted_jobs = []
        stability_metrics = []
        
        start_time = time.time()
        last_submission = start_time
        test_counter = 0
        
        # Submit tests at steady rate
        submission_thread_active = True
        
        def submit_tests():
            nonlocal test_counter, last_submission, submission_thread_active
            
            while submission_thread_active and time.time() - start_time < test_duration:
                current_time = time.time()
                
                # Maintain submission rate
                if current_time - last_submission >= (1.0 / submission_rate):
                    test_case = create_load_test_case(
                        test_id=f"sustained-{test_counter:04d}",
                        duration=random.randint(10, 30),  # Longer tests for sustained load
                        architecture=random.choice(["x86_64", "arm64"]),
                        test_type=random.choice([TestType.UNIT, TestType.INTEGRATION])
                    )
                    
                    job_id = orchestrator.submit_job(
                        test_case=test_case,
                        priority=Priority.MEDIUM,
                        impact_score=0.6
                    )
                    
                    submitted_jobs.append({
                        'job_id': job_id,
                        'submission_time': current_time - start_time
                    })
                    
                    test_counter += 1
                    last_submission = current_time
                
                time.sleep(0.1)  # Small sleep to prevent busy waiting
        
        # Start submission thread
        submission_thread = threading.Thread(target=submit_tests)
        submission_thread.start()
        
        # Monitor system stability
        while time.time() - start_time < test_duration + 60:  # Extra time for completion
            queue_status = orchestrator.get_queue_status()
            
            stability_metrics.append({
                'timestamp': time.time() - start_time,
                'running_jobs': queue_status['running_jobs'],
                'pending_jobs': queue_status['pending_jobs'],
                'available_environments': queue_status['available_environments'],
                'allocated_environments': queue_status['allocated_environments']
            })
            
            # Check if submission phase is complete and all tests are done
            if (time.time() - start_time > test_duration and 
                queue_status['running_jobs'] == 0 and 
                queue_status['pending_jobs'] == 0):
                break
            
            time.sleep(5)  # Sample every 5 seconds
        
        # Stop submission thread
        submission_thread_active = False
        submission_thread.join()
        
        total_test_time = time.time() - start_time
        
        # Analyze stability
        completed_count = 0
        for job_info in submitted_jobs:
            job_status = orchestrator.get_job_status(job_info['job_id'])
            if job_status and job_status['status'] == 'completed':
                completed_count += 1
        
        # Calculate stability metrics
        if stability_metrics:
            running_jobs_over_time = [m['running_jobs'] for m in stability_metrics]
            pending_jobs_over_time = [m['pending_jobs'] for m in stability_metrics]
            
            avg_running = statistics.mean(running_jobs_over_time)
            max_running = max(running_jobs_over_time)
            avg_pending = statistics.mean(pending_jobs_over_time)
            max_pending = max(pending_jobs_over_time)
            
            # Check for stability (no wild fluctuations)
            running_stddev = statistics.stdev(running_jobs_over_time) if len(running_jobs_over_time) > 1 else 0
            
            # Stability assertions
            assert completed_count >= len(submitted_jobs) * 0.95, f"Should complete most sustained tests: {completed_count}/{len(submitted_jobs)}"
            assert max_running <= len(load_test_environments), f"Should not exceed environment capacity: {max_running}"
            assert running_stddev < avg_running * 0.5, f"Running jobs should be stable, stddev: {running_stddev:.2f}, avg: {avg_running:.2f}"
            
            print(f"\nSustained Load Stability Results:")
            print(f"  Test duration: {test_duration}s")
            print(f"  Tests submitted: {len(submitted_jobs)}")
            print(f"  Tests completed: {completed_count}")
            print(f"  Avg running jobs: {avg_running:.2f}")
            print(f"  Max running jobs: {max_running}")
            print(f"  Avg pending jobs: {avg_pending:.2f}")
            print(f"  Max pending jobs: {max_pending}")
            print(f"  Running jobs stability (stddev): {running_stddev:.2f}")
            print(f"  Total test time: {total_test_time:.2f}s")


@pytest.mark.integration
@pytest.mark.slow
class TestOrchestratorResourceManagementStress:
    """Test resource management under stress conditions."""
    
    def test_resource_exhaustion_and_recovery(
        self, 
        load_test_orchestrator_service, 
        load_test_environments
    ):
        """Test system behavior when resources are completely exhausted.
        
        Validates Requirements:
        - 5.4: Proper queuing when resource limits are exceeded
        - 2.4: Resource utilization tracking during stress
        """
        orchestrator = TestOrchestrator()
        
        # Add limited environments to force exhaustion
        limited_environments = load_test_environments[:5]  # Only 5 environments
        for env in limited_environments:
            orchestrator.add_environment(env)
        
        # Create many long-running tests to exhaust resources
        long_running_tests = []
        for i in range(20):  # 20 tests, 5 environments = 4x oversubscription
            test_case = create_load_test_case(
                test_id=f"resource-exhaustion-{i:02d}",
                duration=30,  # 30 second tests
                architecture="x86_64",
                test_type=TestType.INTEGRATION,
                memory_mb=2048
            )
            long_running_tests.append(test_case)
        
        # Submit all tests rapidly
        job_ids = []
        for test_case in long_running_tests:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_ids.append(job_id)
        
        # Monitor resource exhaustion and recovery
        resource_metrics = []
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        exhaustion_detected = False
        recovery_detected = False
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            
            metrics = {
                'timestamp': time.time() - start_time,
                'running_jobs': queue_status['running_jobs'],
                'pending_jobs': queue_status['pending_jobs'],
                'available_environments': queue_status['available_environments'],
                'allocated_environments': queue_status['allocated_environments'],
                'utilization_rate': queue_status['allocated_environments'] / len(limited_environments)
            }
            resource_metrics.append(metrics)
            
            # Detect resource exhaustion (Requirements 5.4)
            if (queue_status['available_environments'] == 0 and 
                queue_status['pending_jobs'] > 0):
                exhaustion_detected = True
            
            # Detect recovery (resources becoming available again)
            if (exhaustion_detected and 
                queue_status['available_environments'] > 0 and
                queue_status['pending_jobs'] < len(job_ids)):
                recovery_detected = True
            
            # Check completion
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            
            time.sleep(2)
        
        # Verify all tests completed
        completed_count = 0
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] == 'completed':
                completed_count += 1
        
        # Analyze resource utilization patterns
        if resource_metrics:
            max_running = max(m['running_jobs'] for m in resource_metrics)
            max_pending = max(m['pending_jobs'] for m in resource_metrics)
            peak_utilization = max(m['utilization_rate'] for m in resource_metrics)
            
            # Resource management assertions
            assert exhaustion_detected, "Should detect resource exhaustion"
            assert recovery_detected, "Should detect resource recovery"
            assert completed_count == len(job_ids), f"All tests should complete: {completed_count}/{len(job_ids)}"
            assert max_running <= len(limited_environments), f"Should not exceed environment limit: {max_running}"
            assert max_pending > 0, "Should queue tests when resources exhausted"
            assert peak_utilization >= 0.95, f"Should achieve near-full utilization: {peak_utilization:.2%}"
            
            print(f"\nResource Exhaustion and Recovery Results:")
            print(f"  Total tests: {len(job_ids)}")
            print(f"  Completed: {completed_count}")
            print(f"  Available environments: {len(limited_environments)}")
            print(f"  Max running: {max_running}")
            print(f"  Max pending: {max_pending}")
            print(f"  Peak utilization: {peak_utilization:.2%}")
            print(f"  Exhaustion detected: {exhaustion_detected}")
            print(f"  Recovery detected: {recovery_detected}")
    
    def test_memory_pressure_handling(
        self, 
        load_test_orchestrator_service, 
        load_test_environments
    ):
        """Test system behavior under memory pressure conditions."""
        orchestrator = TestOrchestrator()
        
        # Add environments with varying memory capacities
        memory_environments = [env for env in load_test_environments 
                             if env.config.architecture == "x86_64"][:10]
        
        for env in memory_environments:
            orchestrator.add_environment(env)
        
        # Create tests with high memory requirements
        memory_intensive_tests = []
        for i in range(15):
            # Vary memory requirements
            memory_mb = random.choice([4096, 8192, 16384])  # 4GB, 8GB, 16GB
            
            test_case = create_load_test_case(
                test_id=f"memory-pressure-{i:02d}",
                duration=20,
                architecture="x86_64",
                test_type=TestType.PERFORMANCE,
                memory_mb=memory_mb
            )
            memory_intensive_tests.append(test_case)
        
        # Submit memory-intensive tests
        job_ids = []
        for test_case in memory_intensive_tests:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.7
            )
            job_ids.append(job_id)
        
        # Monitor memory allocation patterns
        allocation_metrics = []
        max_wait_time = 240  # 4 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            
            # Track allocation patterns
            allocation_metrics.append({
                'timestamp': time.time() - start_time,
                'running_jobs': queue_status['running_jobs'],
                'pending_jobs': queue_status['pending_jobs'],
                'allocated_environments': queue_status['allocated_environments']
            })
            
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            
            time.sleep(3)
        
        # Verify memory pressure handling
        completed_count = 0
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] == 'completed':
                completed_count += 1
        
        # Memory pressure should be handled gracefully
        assert completed_count >= len(job_ids) * 0.9, f"Should handle memory pressure gracefully: {completed_count}/{len(job_ids)}"
        
        if allocation_metrics:
            max_concurrent = max(m['running_jobs'] for m in allocation_metrics)
            # Under memory pressure, concurrency might be lower than environment count
            assert max_concurrent > 0, "Should still execute some tests under memory pressure"
            
            print(f"\nMemory Pressure Handling Results:")
            print(f"  Memory intensive tests: {len(job_ids)}")
            print(f"  Completed: {completed_count}")
            print(f"  Max concurrent under pressure: {max_concurrent}")
    
    def test_mixed_workload_resource_allocation(
        self, 
        load_test_orchestrator_service, 
        load_test_environments
    ):
        """Test resource allocation with mixed workload characteristics."""
        orchestrator = TestOrchestrator()
        
        # Add diverse environments
        for env in load_test_environments:
            orchestrator.add_environment(env)
        
        # Create mixed workload
        mixed_tests = []
        
        # Lightweight tests (should get Docker environments)
        for i in range(10):
            test_case = create_load_test_case(
                test_id=f"mixed-light-{i:02d}",
                duration=5,
                architecture="x86_64",
                test_type=TestType.UNIT,
                memory_mb=512
            )
            mixed_tests.append(('light', test_case))
        
        # Medium tests (should get QEMU environments)
        for i in range(8):
            test_case = create_load_test_case(
                test_id=f"mixed-medium-{i:02d}",
                duration=15,
                architecture=random.choice(["x86_64", "arm64"]),
                test_type=TestType.INTEGRATION,
                memory_mb=2048
            )
            mixed_tests.append(('medium', test_case))
        
        # Heavy tests (should get high-spec environments)
        for i in range(5):
            test_case = create_load_test_case(
                test_id=f"mixed-heavy-{i:02d}",
                duration=25,
                architecture="x86_64",
                test_type=TestType.PERFORMANCE,
                memory_mb=8192,
                cpu_intensive=True
            )
            mixed_tests.append(('heavy', test_case))
        
        # Shuffle to simulate realistic mixed submission
        random.shuffle(mixed_tests)
        
        # Submit mixed workload
        job_submissions = []
        for workload_type, test_case in mixed_tests:
            # Assign priorities based on workload type
            if workload_type == 'heavy':
                priority = Priority.HIGH
                impact_score = 0.9
            elif workload_type == 'medium':
                priority = Priority.MEDIUM
                impact_score = 0.6
            else:  # light
                priority = Priority.LOW
                impact_score = 0.3
            
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=priority,
                impact_score=impact_score
            )
            
            job_submissions.append({
                'job_id': job_id,
                'workload_type': workload_type,
                'test_id': test_case.id,
                'memory_mb': test_case.required_hardware.memory_mb,
                'architecture': test_case.required_hardware.architecture
            })
        
        # Monitor mixed workload execution
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(2)
        
        # Analyze resource allocation patterns
        allocation_results = {'light': [], 'medium': [], 'heavy': []}
        
        for submission in job_submissions:
            job_status = orchestrator.get_job_status(submission['job_id'])
            if job_status and job_status['status'] == 'completed' and job_status['result']:
                result = TestResult.from_dict(job_status['result'])
                allocation_results[submission['workload_type']].append({
                    'test_id': submission['test_id'],
                    'environment_id': result.environment.id,
                    'environment_type': result.environment.config.emulator,
                    'allocated_memory': result.environment.config.memory_mb
                })
        
        # Verify appropriate resource allocation
        total_completed = sum(len(results) for results in allocation_results.values())
        assert total_completed >= len(mixed_tests) * 0.95, f"Should complete mixed workload: {total_completed}/{len(mixed_tests)}"
        
        # Analyze allocation patterns
        docker_allocations = sum(1 for workload_results in allocation_results.values() 
                               for result in workload_results 
                               if result['environment_type'] == 'docker')
        
        qemu_allocations = sum(1 for workload_results in allocation_results.values() 
                             for result in workload_results 
                             if result['environment_type'] == 'qemu')
        
        # Light tests should prefer Docker, heavy tests should prefer QEMU
        light_docker_ratio = (sum(1 for result in allocation_results['light'] 
                                if result['environment_type'] == 'docker') / 
                             max(len(allocation_results['light']), 1))
        
        heavy_qemu_ratio = (sum(1 for result in allocation_results['heavy'] 
                              if result['environment_type'] == 'qemu') / 
                           max(len(allocation_results['heavy']), 1))
        
        print(f"\nMixed Workload Resource Allocation Results:")
        print(f"  Total completed: {total_completed}/{len(mixed_tests)}")
        print(f"  Light tests completed: {len(allocation_results['light'])}")
        print(f"  Medium tests completed: {len(allocation_results['medium'])}")
        print(f"  Heavy tests completed: {len(allocation_results['heavy'])}")
        print(f"  Docker allocations: {docker_allocations}")
        print(f"  QEMU allocations: {qemu_allocations}")
        print(f"  Light->Docker ratio: {light_docker_ratio:.2%}")
        print(f"  Heavy->QEMU ratio: {heavy_qemu_ratio:.2%}")


@pytest.mark.integration
@pytest.mark.slow
class TestOrchestratorSystemStability:
    """Test system stability and performance characteristics under stress."""
    
    def test_long_running_stability(
        self, 
        load_test_orchestrator_service, 
        load_test_environments
    ):
        """Test system stability over extended periods."""
        orchestrator = TestOrchestrator()
        
        # Add environments
        for env in load_test_environments[:15]:  # Use 15 environments
            orchestrator.add_environment(env)
        
        # Run continuous load for extended period
        test_duration = 300  # 5 minutes of continuous operation
        continuous_submission_rate = 1  # 1 test per second
        
        submitted_jobs = []
        stability_events = []
        
        start_time = time.time()
        test_counter = 0
        
        # Continuous submission thread
        def continuous_submission():
            nonlocal test_counter
            last_submission = start_time
            
            while time.time() - start_time < test_duration:
                current_time = time.time()
                
                if current_time - last_submission >= (1.0 / continuous_submission_rate):
                    # Create varied test characteristics
                    duration = random.randint(10, 60)  # 10-60 second tests
                    architecture = random.choice(["x86_64", "arm64"])
                    test_type = random.choice([TestType.UNIT, TestType.INTEGRATION, TestType.PERFORMANCE])
                    
                    test_case = create_load_test_case(
                        test_id=f"stability-{test_counter:04d}",
                        duration=duration,
                        architecture=architecture,
                        test_type=test_type,
                        should_fail=(test_counter % 100) == 0  # 1% failure rate
                    )
                    
                    job_id = orchestrator.submit_job(
                        test_case=test_case,
                        priority=random.choice([Priority.LOW, Priority.MEDIUM, Priority.HIGH]),
                        impact_score=random.uniform(0.2, 0.9)
                    )
                    
                    submitted_jobs.append({
                        'job_id': job_id,
                        'submission_time': current_time - start_time,
                        'expected_duration': duration
                    })
                    
                    test_counter += 1
                    last_submission = current_time
                
                time.sleep(0.1)
        
        # Start continuous submission
        submission_thread = threading.Thread(target=continuous_submission)
        submission_thread.start()
        
        # Monitor system stability
        last_health_check = start_time
        health_check_interval = 30  # Check health every 30 seconds
        
        while time.time() - start_time < test_duration + 120:  # Extra time for completion
            current_time = time.time()
            
            # Periodic health checks
            if current_time - last_health_check >= health_check_interval:
                try:
                    health_status = load_test_orchestrator_service.get_health_status()
                    queue_status = orchestrator.get_queue_status()
                    
                    stability_events.append({
                        'timestamp': current_time - start_time,
                        'event_type': 'health_check',
                        'health_status': health_status['status'],
                        'is_running': health_status['is_running'],
                        'running_jobs': queue_status['running_jobs'],
                        'pending_jobs': queue_status['pending_jobs']
                    })
                    
                    last_health_check = current_time
                    
                except Exception as e:
                    stability_events.append({
                        'timestamp': current_time - start_time,
                        'event_type': 'health_check_error',
                        'error': str(e)
                    })
            
            # Check if submission is done and all tests completed
            queue_status = orchestrator.get_queue_status()
            if (current_time - start_time > test_duration and 
                queue_status['running_jobs'] == 0 and 
                queue_status['pending_jobs'] == 0):
                break
            
            time.sleep(10)
        
        # Wait for submission thread to complete
        submission_thread.join()
        
        total_test_time = time.time() - start_time
        
        # Analyze stability
        completed_count = 0
        failed_count = 0
        
        for job_info in submitted_jobs:
            job_status = orchestrator.get_job_status(job_info['job_id'])
            if job_status and job_status['status'] == 'completed':
                completed_count += 1
                if job_status['result']:
                    result = TestResult.from_dict(job_status['result'])
                    if result.status == TestStatus.FAILED:
                        failed_count += 1
        
        # Analyze health check results
        health_checks = [event for event in stability_events if event['event_type'] == 'health_check']
        health_errors = [event for event in stability_events if event['event_type'] == 'health_check_error']
        
        healthy_checks = sum(1 for check in health_checks if check['health_status'] == 'healthy')
        
        # Stability assertions
        assert len(submitted_jobs) >= test_duration * continuous_submission_rate * 0.9, "Should maintain submission rate"
        assert completed_count >= len(submitted_jobs) * 0.95, f"Should complete most tests: {completed_count}/{len(submitted_jobs)}"
        assert len(health_errors) == 0, f"Should not have health check errors: {len(health_errors)}"
        assert healthy_checks >= len(health_checks) * 0.95, f"Should maintain health: {healthy_checks}/{len(health_checks)}"
        
        print(f"\nLong Running Stability Results:")
        print(f"  Test duration: {test_duration}s")
        print(f"  Total runtime: {total_test_time:.2f}s")
        print(f"  Tests submitted: {len(submitted_jobs)}")
        print(f"  Tests completed: {completed_count}")
        print(f"  Tests failed: {failed_count}")
        print(f"  Health checks: {len(health_checks)}")
        print(f"  Healthy checks: {healthy_checks}")
        print(f"  Health errors: {len(health_errors)}")
    
    def test_error_recovery_under_load(
        self, 
        load_test_orchestrator_service, 
        load_test_environments
    ):
        """Test system recovery from errors under load conditions."""
        orchestrator = TestOrchestrator()
        
        # Add environments
        for env in load_test_environments[:10]:
            orchestrator.add_environment(env)
        
        # Create mix of normal and problematic tests
        test_cases = []
        
        # Normal tests (70%)
        for i in range(35):
            test_case = create_load_test_case(
                test_id=f"error-recovery-normal-{i:02d}",
                duration=random.randint(5, 15),
                architecture=random.choice(["x86_64", "arm64"]),
                test_type=TestType.UNIT
            )
            test_cases.append(('normal', test_case))
        
        # Failing tests (20%)
        for i in range(10):
            test_case = create_load_test_case(
                test_id=f"error-recovery-failing-{i:02d}",
                duration=random.randint(3, 10),
                architecture="x86_64",
                test_type=TestType.UNIT,
                should_fail=True
            )
            test_cases.append(('failing', test_case))
        
        # Timeout tests (10%)
        for i in range(5):
            test_case = TestCase(
                id=f"error-recovery-timeout-{i:02d}",
                name=f"Timeout Test {i}",
                description=f"Test that will timeout {i}",
                test_type=TestType.UNIT,
                target_subsystem="error_recovery",
                test_script=f"""#!/bin/bash
echo "Timeout test {i} starting..."
sleep 180  # Sleep longer than timeout
echo "This should not be reached"
exit 0
""",
                execution_time_estimate=10,  # Short timeout
                required_hardware=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="generic",
                    memory_mb=1024,
                    is_virtual=True
                )
            )
            test_cases.append(('timeout', test_case))
        
        # Shuffle test order
        random.shuffle(test_cases)
        
        # Submit all tests
        job_submissions = []
        for test_type, test_case in test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_submissions.append({
                'job_id': job_id,
                'test_type': test_type,
                'test_id': test_case.id
            })
        
        # Monitor error recovery
        recovery_metrics = []
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            
            recovery_metrics.append({
                'timestamp': time.time() - start_time,
                'running_jobs': queue_status['running_jobs'],
                'pending_jobs': queue_status['pending_jobs'],
                'available_environments': queue_status['available_environments']
            })
            
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            
            time.sleep(3)
        
        # Analyze error recovery
        results_by_type = {'normal': [], 'failing': [], 'timeout': []}
        
        for submission in job_submissions:
            job_status = orchestrator.get_job_status(submission['job_id'])
            if job_status and job_status['status'] == 'completed':
                test_type = submission['test_type']
                results_by_type[test_type].append(job_status)
        
        # Verify error recovery
        normal_completed = len(results_by_type['normal'])
        failing_completed = len(results_by_type['failing'])
        timeout_completed = len(results_by_type['timeout'])
        
        total_expected = len([s for s in job_submissions if s['test_type'] == 'normal'])
        failing_expected = len([s for s in job_submissions if s['test_type'] == 'failing'])
        timeout_expected = len([s for s in job_submissions if s['test_type'] == 'timeout'])
        
        # System should recover from errors and continue processing
        assert normal_completed >= total_expected * 0.95, f"Should complete normal tests despite errors: {normal_completed}/{total_expected}"
        assert failing_completed >= failing_expected * 0.9, f"Should handle failing tests: {failing_completed}/{failing_expected}"
        assert timeout_completed >= timeout_expected * 0.8, f"Should handle timeout tests: {timeout_completed}/{timeout_expected}"
        
        # Verify system remained stable (environments available)
        final_metrics = recovery_metrics[-1] if recovery_metrics else None
        if final_metrics:
            assert final_metrics['available_environments'] > 0, "Should have available environments after error recovery"
        
        print(f"\nError Recovery Under Load Results:")
        print(f"  Normal tests completed: {normal_completed}/{total_expected}")
        print(f"  Failing tests handled: {failing_completed}/{failing_expected}")
        print(f"  Timeout tests handled: {timeout_completed}/{timeout_expected}")
        print(f"  Final available environments: {final_metrics['available_environments'] if final_metrics else 'N/A'}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])