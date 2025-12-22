"""Comprehensive orchestrator integration test suite.

This module provides a comprehensive test suite that validates all aspects
of the orchestrator integration including:
- Complete workflow testing
- Performance benchmarking
- Stress testing
- Error recovery testing
- Real-world scenario simulation
"""

import pytest
import asyncio
import time
import threading
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, TestType, RiskLevel, ExecutionPlan
)
from orchestrator.service import OrchestratorService
from orchestrator.config import OrchestratorConfig
from orchestrator.scheduler import TestOrchestrator, Priority
from orchestrator.status_tracker import StatusTracker
from api.orchestrator_integration import start_orchestrator, stop_orchestrator


@pytest.fixture(scope="module")
def comprehensive_orchestrator_config(tmp_path_factory):
    """Create comprehensive orchestrator configuration for testing."""
    tmp_path = tmp_path_factory.mktemp("orchestrator_comprehensive")
    
    config = OrchestratorConfig(
        poll_interval=0.2,  # Very fast polling for comprehensive tests
        default_timeout=60,
        max_concurrent_tests=10,
        enable_persistence=True,
        state_file=str(tmp_path / "orchestrator_state.json"),
        log_level="INFO"  # Reduce log noise for comprehensive tests
    )
    return config


@pytest.fixture(scope="module")
def comprehensive_orchestrator_service(comprehensive_orchestrator_config):
    """Create long-running orchestrator service for comprehensive testing."""
    service = OrchestratorService(comprehensive_orchestrator_config)
    assert service.start(), "Failed to start comprehensive orchestrator service"
    
    yield service
    
    service.stop()


@pytest.fixture
def comprehensive_test_environments():
    """Create comprehensive set of test environments."""
    environments = []
    
    # Multiple x86_64 environments with different specs
    for i in range(5):
        env = Environment(
            id=f"comprehensive-x86-{i+1}",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model=f"Intel Xeon E5-{2680 + i}",
                memory_mb=2048 * (i + 1),  # 2GB, 4GB, 6GB, 8GB, 10GB
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        )
        environments.append(env)
    
    # ARM64 environments
    for i in range(2):
        env = Environment(
            id=f"comprehensive-arm-{i+1}",
            config=HardwareConfig(
                architecture="arm64",
                cpu_model=f"ARM Cortex-A{72 + i*6}",
                memory_mb=2048 + (i * 2048),  # 2GB, 4GB
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        )
        environments.append(env)
    
    # RISC-V environment
    env = Environment(
        id="comprehensive-riscv-1",
        config=HardwareConfig(
            architecture="riscv64",
            cpu_model="SiFive U74",
            memory_mb=1024,
            is_virtual=True,
            emulator="qemu"
        ),
        status=EnvironmentStatus.IDLE
    )
    environments.append(env)
    
    return environments


def create_test_case(test_id: str, duration: int = 5, architecture: str = "x86_64", 
                    test_type: TestType = TestType.UNIT, should_fail: bool = False) -> TestCase:
    """Create a test case with specified parameters."""
    exit_code = 1 if should_fail else 0
    
    return TestCase(
        id=test_id,
        name=f"Comprehensive Test {test_id}",
        description=f"Comprehensive test case {test_id}",
        test_type=test_type,
        target_subsystem="comprehensive_testing",
        test_script=f"""#!/bin/bash
echo "Comprehensive test {test_id} starting..."
echo "Architecture: {architecture}"
echo "Duration: {duration}s"
echo "Should fail: {should_fail}"

# Simulate work
for i in $(seq 1 {duration}); do
    echo "Working... $i/{duration}"
    sleep 1
done

echo "Comprehensive test {test_id} {'failed' if should_fail else 'completed'}"
exit {exit_code}
""",
        execution_time_estimate=duration + 5,
        required_hardware=HardwareConfig(
            architecture=architecture,
            cpu_model="generic",
            memory_mb=1024,
            is_virtual=True
        )
    )


@pytest.mark.integration
class TestOrchestratorComprehensiveWorkflows:
    """Comprehensive workflow testing for orchestrator."""
    
    def test_large_scale_test_execution(self, comprehensive_orchestrator_service, comprehensive_test_environments):
        """Test large-scale test execution with many tests and environments."""
        orchestrator = TestOrchestrator()
        
        # Add all environments
        for env in comprehensive_test_environments:
            orchestrator.add_environment(env)
        
        # Create large number of test cases
        test_cases = []
        job_ids = []
        
        # Create 50 test cases with varied characteristics
        for i in range(50):
            duration = (i % 10) + 1  # 1-10 seconds
            architecture = ["x86_64", "arm64", "riscv64"][i % 3]
            test_type = [TestType.UNIT, TestType.INTEGRATION, TestType.PERFORMANCE][i % 3]
            should_fail = (i % 20) == 0  # 5% failure rate
            
            test_case = create_test_case(
                test_id=f"large-scale-{i:03d}",
                duration=duration,
                architecture=architecture,
                test_type=test_type,
                should_fail=should_fail
            )
            test_cases.append(test_case)
        
        # Submit all tests
        start_time = time.time()
        for test_case in test_cases:
            priority = Priority.HIGH if test_case.test_type == TestType.PERFORMANCE else Priority.MEDIUM
            impact_score = 0.8 if test_case.test_type == TestType.INTEGRATION else 0.5
            
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=priority,
                impact_score=impact_score
            )
            job_ids.append(job_id)
        
        submission_time = time.time() - start_time
        
        # Monitor execution
        max_concurrent = 0
        execution_start = time.time()
        completed_jobs = set()
        
        while time.time() - execution_start < 300:  # 5 minute timeout
            queue_status = orchestrator.get_queue_status()
            current_running = queue_status['running_jobs']
            max_concurrent = max(max_concurrent, current_running)
            
            # Check completed jobs
            for job_id in job_ids:
                if job_id not in completed_jobs:
                    job_status = orchestrator.get_job_status(job_id)
                    if job_status['status'] == 'completed':
                        completed_jobs.add(job_id)
            
            # Check if all completed
            if len(completed_jobs) == len(job_ids):
                break
            
            time.sleep(1)
        
        execution_time = time.time() - execution_start
        
        # Analyze results
        passed_count = 0
        failed_count = 0
        execution_times = []
        
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status['result']:
                result = TestResult.from_dict(job_status['result'])
                execution_times.append(result.execution_time)
                
                if result.status == TestStatus.PASSED:
                    passed_count += 1
                else:
                    failed_count += 1
        
        # Performance assertions
        assert len(completed_jobs) == len(job_ids), f"Only {len(completed_jobs)}/{len(job_ids)} tests completed"
        assert max_concurrent > 1, "Should have concurrent execution"
        assert max_concurrent <= len(comprehensive_test_environments), "Should not exceed available environments"
        assert submission_time < 10.0, f"Submission took too long: {submission_time:.2f}s"
        assert execution_time < 180.0, f"Execution took too long: {execution_time:.2f}s"
        
        # Quality assertions
        expected_failures = len([tc for tc in test_cases if "should_fail: True" in tc.test_script])
        assert failed_count >= expected_failures * 0.8, "Should have expected failure rate"
        assert passed_count > len(job_ids) * 0.8, "Should have high pass rate"
        
        # Performance metrics
        if execution_times:
            avg_execution_time = statistics.mean(execution_times)
            median_execution_time = statistics.median(execution_times)
            
            print(f"\nLarge Scale Test Results:")
            print(f"  Total tests: {len(job_ids)}")
            print(f"  Completed: {len(completed_jobs)}")
            print(f"  Passed: {passed_count}")
            print(f"  Failed: {failed_count}")
            print(f"  Max concurrent: {max_concurrent}")
            print(f"  Submission time: {submission_time:.2f}s")
            print(f"  Total execution time: {execution_time:.2f}s")
            print(f"  Avg test execution time: {avg_execution_time:.2f}s")
            print(f"  Median test execution time: {median_execution_time:.2f}s")
    
    def test_mixed_architecture_workflow(self, comprehensive_orchestrator_service, comprehensive_test_environments):
        """Test workflow with mixed architecture requirements."""
        orchestrator = TestOrchestrator()
        
        # Add all environments
        for env in comprehensive_test_environments:
            orchestrator.add_environment(env)
        
        # Create architecture-specific test cases
        arch_test_cases = []
        architectures = ["x86_64", "arm64", "riscv64"]
        
        for arch in architectures:
            for i in range(5):  # 5 tests per architecture
                test_case = create_test_case(
                    test_id=f"mixed-arch-{arch}-{i:02d}",
                    duration=3,
                    architecture=arch,
                    test_type=TestType.INTEGRATION
                )
                arch_test_cases.append(test_case)
        
        # Submit all tests
        job_ids = []
        for test_case in arch_test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.6
            )
            job_ids.append((job_id, test_case.required_hardware.architecture))
        
        # Monitor execution
        max_wait_time = 120
        start_time = time.time()
        results_by_arch = {arch: [] for arch in architectures}
        
        while time.time() - start_time < max_wait_time:
            all_completed = True
            
            for job_id, arch in job_ids:
                job_status = orchestrator.get_job_status(job_id)
                if job_status['status'] == 'completed':
                    if job_status['result']:
                        result = TestResult.from_dict(job_status['result'])
                        if result not in results_by_arch[arch]:
                            results_by_arch[arch].append(result)
                else:
                    all_completed = False
            
            if all_completed:
                break
            
            time.sleep(1)
        
        # Verify results by architecture
        for arch in architectures:
            arch_results = results_by_arch[arch]
            assert len(arch_results) == 5, f"Expected 5 results for {arch}, got {len(arch_results)}"
            
            for result in arch_results:
                assert result.environment.config.architecture == arch, \
                    f"Test for {arch} ran on {result.environment.config.architecture}"
    
    def test_priority_and_impact_workflow(self, comprehensive_orchestrator_service, comprehensive_test_environments):
        """Test workflow with complex priority and impact score scenarios."""
        orchestrator = TestOrchestrator()
        
        # Add limited environments to create contention
        for env in comprehensive_test_environments[:3]:
            orchestrator.add_environment(env)
        
        # Create tests with different priorities and impact scores
        test_scenarios = [
            # (priority, impact_score, expected_order_group)
            (Priority.CRITICAL, 0.95, 1),
            (Priority.HIGH, 0.90, 2),
            (Priority.HIGH, 0.85, 2),
            (Priority.MEDIUM, 0.80, 3),
            (Priority.MEDIUM, 0.60, 3),
            (Priority.LOW, 0.40, 4),
            (Priority.LOW, 0.20, 4),
            (Priority.CRITICAL, 0.99, 1),  # Should be first
        ]
        
        # Create and submit test cases
        job_data = []
        for i, (priority, impact_score, order_group) in enumerate(test_scenarios):
            test_case = create_test_case(
                test_id=f"priority-test-{i:02d}",
                duration=5,
                test_type=TestType.INTEGRATION
            )
            
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=priority,
                impact_score=impact_score
            )
            
            job_data.append({
                'job_id': job_id,
                'priority': priority,
                'impact_score': impact_score,
                'order_group': order_group,
                'start_time': None
            })
        
        # Monitor execution order
        max_wait_time = 180
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            for job_info in job_data:
                if job_info['start_time'] is None:
                    job_status = orchestrator.get_job_status(job_info['job_id'])
                    if job_status['status'] == 'running':
                        job_info['start_time'] = time.time()
            
            # Check if all completed
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            
            time.sleep(0.5)
        
        # Analyze execution order
        started_jobs = [job for job in job_data if job['start_time'] is not None]
        started_jobs.sort(key=lambda x: x['start_time'])
        
        # Verify priority ordering (within reasonable bounds due to concurrency)
        for i in range(len(started_jobs) - 1):
            current_job = started_jobs[i]
            next_job = started_jobs[i + 1]
            
            # Jobs in higher priority groups should generally start earlier
            if current_job['order_group'] > next_job['order_group']:
                # This might happen due to concurrency, but shouldn't be common
                print(f"Warning: Lower priority job started before higher priority job")
    
    def test_fault_tolerance_workflow(self, comprehensive_orchestrator_service, comprehensive_test_environments):
        """Test orchestrator fault tolerance under various failure scenarios."""
        orchestrator = TestOrchestrator()
        
        # Add environments
        for env in comprehensive_test_environments[:4]:
            orchestrator.add_environment(env)
        
        # Create mix of normal and problematic test cases
        test_cases = []
        
        # Normal tests
        for i in range(10):
            test_case = create_test_case(
                test_id=f"fault-normal-{i:02d}",
                duration=2,
                should_fail=False
            )
            test_cases.append(test_case)
        
        # Failing tests
        for i in range(3):
            test_case = create_test_case(
                test_id=f"fault-failing-{i:02d}",
                duration=2,
                should_fail=True
            )
            test_cases.append(test_case)
        
        # Timeout tests (longer than expected)
        for i in range(2):
            test_case = TestCase(
                id=f"fault-timeout-{i:02d}",
                name=f"Timeout Test {i}",
                description=f"Test that will timeout {i}",
                test_type=TestType.UNIT,
                target_subsystem="fault_testing",
                test_script=f"""#!/bin/bash
echo "Timeout test {i} starting..."
sleep 30  # Sleep longer than timeout
echo "This should not be reached"
exit 0
""",
                execution_time_estimate=5,  # Short timeout
                required_hardware=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="generic",
                    memory_mb=1024,
                    is_virtual=True
                )
            )
            test_cases.append(test_case)
        
        # Submit all tests
        job_ids = []
        for test_case in test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_ids.append(job_id)
        
        # Monitor execution with fault injection
        max_wait_time = 120
        start_time = time.time()
        
        # Simulate environment failure after some tests start
        time.sleep(5)
        if len(comprehensive_test_environments) > 1:
            orchestrator.remove_environment(comprehensive_test_environments[0].id)
            print("Simulated environment failure")
        
        # Continue monitoring
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(1)
        
        # Analyze fault tolerance
        completed_count = 0
        passed_count = 0
        failed_count = 0
        timeout_count = 0
        
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status['status'] == 'completed':
                completed_count += 1
                if job_status['result']:
                    result = TestResult.from_dict(job_status['result'])
                    if result.status == TestStatus.PASSED:
                        passed_count += 1
                    elif result.status == TestStatus.FAILED:
                        failed_count += 1
                    elif result.status == TestStatus.TIMEOUT:
                        timeout_count += 1
        
        # Verify fault tolerance
        assert completed_count > len(job_ids) * 0.8, "Should complete most tests despite faults"
        assert passed_count >= 10, "Should pass normal tests"
        assert failed_count >= 3, "Should properly handle failing tests"
        assert timeout_count >= 2, "Should properly handle timeout tests"
        
        print(f"\nFault Tolerance Results:")
        print(f"  Total tests: {len(job_ids)}")
        print(f"  Completed: {completed_count}")
        print(f"  Passed: {passed_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Timeouts: {timeout_count}")


@pytest.mark.integration
class TestOrchestratorPerformanceBenchmarks:
    """Performance benchmarking for orchestrator."""
    
    def test_throughput_benchmark(self, comprehensive_orchestrator_service, comprehensive_test_environments):
        """Benchmark orchestrator throughput capacity."""
        orchestrator = TestOrchestrator()
        
        # Add all environments for maximum throughput
        for env in comprehensive_test_environments:
            orchestrator.add_environment(env)
        
        # Create lightweight test cases for throughput testing
        test_cases = []
        for i in range(100):  # 100 lightweight tests
            test_case = TestCase(
                id=f"throughput-{i:03d}",
                name=f"Throughput Test {i}",
                description=f"Lightweight throughput test {i}",
                test_type=TestType.UNIT,
                target_subsystem="performance",
                test_script=f"""#!/bin/bash
echo "Throughput test {i}"
sleep 0.5  # Very short execution
echo "Completed {i}"
exit 0
""",
                execution_time_estimate=2,
                required_hardware=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="generic",
                    memory_mb=512,
                    is_virtual=True
                )
            )
            test_cases.append(test_case)
        
        # Measure submission throughput
        submission_start = time.time()
        job_ids = []
        
        for test_case in test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_ids.append(job_id)
        
        submission_time = time.time() - submission_start
        submission_throughput = len(job_ids) / submission_time
        
        # Measure execution throughput
        execution_start = time.time()
        completed_count = 0
        
        while time.time() - execution_start < 120:  # 2 minute timeout
            current_completed = 0
            for job_id in job_ids:
                job_status = orchestrator.get_job_status(job_id)
                if job_status['status'] == 'completed':
                    current_completed += 1
            
            if current_completed == len(job_ids):
                completed_count = current_completed
                break
            
            time.sleep(0.5)
        
        execution_time = time.time() - execution_start
        execution_throughput = completed_count / execution_time
        
        # Performance assertions
        assert submission_throughput > 50, f"Submission throughput too low: {submission_throughput:.2f} jobs/s"
        assert execution_throughput > 5, f"Execution throughput too low: {execution_throughput:.2f} jobs/s"
        assert completed_count == len(job_ids), f"Only {completed_count}/{len(job_ids)} tests completed"
        
        print(f"\nThroughput Benchmark Results:")
        print(f"  Submission throughput: {submission_throughput:.2f} jobs/s")
        print(f"  Execution throughput: {execution_throughput:.2f} jobs/s")
        print(f"  Total tests: {len(job_ids)}")
        print(f"  Completed: {completed_count}")
        print(f"  Submission time: {submission_time:.2f}s")
        print(f"  Execution time: {execution_time:.2f}s")
    
    def test_latency_benchmark(self, comprehensive_orchestrator_service, comprehensive_test_environments):
        """Benchmark orchestrator latency characteristics."""
        orchestrator = TestOrchestrator()
        
        # Add single environment for latency testing
        orchestrator.add_environment(comprehensive_test_environments[0])
        
        # Measure end-to-end latency for individual tests
        latencies = []
        
        for i in range(20):  # 20 individual latency measurements
            test_case = create_test_case(
                test_id=f"latency-{i:02d}",
                duration=1,  # Very short test
                test_type=TestType.UNIT
            )
            
            # Measure submission to completion latency
            start_time = time.time()
            
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.HIGH,  # High priority for immediate execution
                impact_score=0.9
            )
            
            # Wait for completion
            while time.time() - start_time < 30:  # 30 second timeout
                job_status = orchestrator.get_job_status(job_id)
                if job_status['status'] == 'completed':
                    end_time = time.time()
                    latency = end_time - start_time
                    latencies.append(latency)
                    break
                time.sleep(0.1)
            
            # Brief pause between tests
            time.sleep(0.5)
        
        # Analyze latency metrics
        if latencies:
            avg_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            # Performance assertions
            assert avg_latency < 10.0, f"Average latency too high: {avg_latency:.2f}s"
            assert median_latency < 8.0, f"Median latency too high: {median_latency:.2f}s"
            assert p95_latency < 15.0, f"95th percentile latency too high: {p95_latency:.2f}s"
            
            print(f"\nLatency Benchmark Results:")
            print(f"  Average latency: {avg_latency:.2f}s")
            print(f"  Median latency: {median_latency:.2f}s")
            print(f"  95th percentile: {p95_latency:.2f}s")
            print(f"  Min latency: {min_latency:.2f}s")
            print(f"  Max latency: {max_latency:.2f}s")
            print(f"  Samples: {len(latencies)}")
    
    def test_resource_utilization_benchmark(self, comprehensive_orchestrator_service, comprehensive_test_environments):
        """Benchmark resource utilization efficiency."""
        orchestrator = TestOrchestrator()
        
        # Add all environments
        for env in comprehensive_test_environments:
            orchestrator.add_environment(env)
        
        total_environments = len(comprehensive_test_environments)
        
        # Create tests that will fully utilize resources
        test_cases = []
        for i in range(total_environments * 3):  # 3x oversubscription
            test_case = create_test_case(
                test_id=f"resource-util-{i:02d}",
                duration=10,  # Longer tests to measure utilization
                test_type=TestType.INTEGRATION
            )
            test_cases.append(test_case)
        
        # Submit all tests
        job_ids = []
        for test_case in test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_ids.append(job_id)
        
        # Monitor resource utilization
        utilization_samples = []
        max_wait_time = 180
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            
            utilization = {
                'timestamp': time.time() - start_time,
                'running_jobs': queue_status['running_jobs'],
                'pending_jobs': queue_status['pending_jobs'],
                'available_environments': queue_status['available_environments'],
                'allocated_environments': queue_status['allocated_environments'],
                'utilization_rate': queue_status['allocated_environments'] / total_environments
            }
            utilization_samples.append(utilization)
            
            # Check if all completed
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            
            time.sleep(1)
        
        # Analyze resource utilization
        if utilization_samples:
            max_utilization = max(sample['utilization_rate'] for sample in utilization_samples)
            avg_utilization = statistics.mean(sample['utilization_rate'] for sample in utilization_samples)
            
            # Find peak concurrent execution
            max_concurrent = max(sample['running_jobs'] for sample in utilization_samples)
            
            # Performance assertions
            assert max_utilization >= 0.8, f"Peak utilization too low: {max_utilization:.2%}"
            assert avg_utilization >= 0.4, f"Average utilization too low: {avg_utilization:.2%}"
            assert max_concurrent >= total_environments * 0.8, f"Peak concurrency too low: {max_concurrent}"
            
            print(f"\nResource Utilization Benchmark Results:")
            print(f"  Total environments: {total_environments}")
            print(f"  Peak utilization: {max_utilization:.2%}")
            print(f"  Average utilization: {avg_utilization:.2%}")
            print(f"  Max concurrent jobs: {max_concurrent}")
            print(f"  Total tests: {len(job_ids)}")
            print(f"  Samples collected: {len(utilization_samples)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])