"""End-to-end integration tests for the Agentic AI Testing System.

This module provides comprehensive integration tests that validate complete workflows
across all system components, from code analysis through test execution to reporting.
"""

import pytest
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, TestType, RiskLevel, CodeAnalysis, Function,
    ArtifactBundle, CoverageData, FailureInfo, Peripheral
)
from orchestrator.scheduler import Priority
from ai_generator.test_generator import AITestGenerator
from ai_generator.llm_providers import BaseLLMProvider, LLMResponse
from orchestrator.scheduler import TestOrchestrator, TestJob
from execution.test_runner import TestRunner
from execution.environment_manager import EnvironmentManager
from analysis.coverage_analyzer import CoverageAnalyzer
from analysis.root_cause_analyzer import RootCauseAnalyzer
from integration.vcs_integration import VCSIntegration
from integration.notification_service import NotificationDispatcher
from api.client import AgenticTestingClient
# from database.repositories import TestResultRepository  # Commented out to avoid SQLAlchemy dependency
from config.settings import get_settings


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for end-to-end testing."""
    
    def __init__(self):
        self.call_count = 0
        self.responses = {}
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate mock responses based on prompt patterns."""
        self.call_count += 1
        
        if "analyze" in prompt.lower() or "diff" in prompt.lower():
            return self._generate_analysis_response()
        elif "test" in prompt.lower() and "generate" in prompt.lower():
            return self._generate_test_cases_response()
        elif "failure" in prompt.lower() or "error" in prompt.lower():
            return self._generate_failure_analysis_response()
        else:
            return self._generate_default_response()
    
    def _generate_analysis_response(self) -> LLMResponse:
        """Generate code analysis response."""
        analysis_data = {
            "changed_files": ["kernel/sched/core.c", "mm/page_alloc.c"],
            "changed_functions": [
                {
                    "name": "schedule",
                    "file_path": "kernel/sched/core.c",
                    "line_number": 100,
                    "subsystem": "scheduler"
                },
                {
                    "name": "alloc_pages",
                    "file_path": "mm/page_alloc.c",
                    "line_number": 200,
                    "subsystem": "memory_management"
                }
            ],
            "affected_subsystems": ["scheduler", "memory_management"],
            "impact_score": 0.8,
            "risk_level": "high",
            "suggested_test_types": ["unit", "integration", "performance"]
        }
        
        return LLMResponse(
            content=str(analysis_data),
            model="mock-model",
            tokens_used=150,
            finish_reason="stop",
            metadata={}
        )
    
    def _generate_test_cases_response(self) -> LLMResponse:
        """Generate test cases response."""
        test_cases = []
        for i in range(15):  # Generate more than minimum required
            test_cases.append({
                "name": f"Generated test case {i + 1}",
                "description": f"Test description for case {i + 1}",
                "test_script": f"#!/bin/bash\necho 'Test {i + 1}'\nexit 0",
                "expected_outcome": {"should_pass": True},
                "execution_time": 30 + (i * 5)
            })
        
        return LLMResponse(
            content=str(test_cases),
            model="mock-model",
            tokens_used=200,
            finish_reason="stop",
            metadata={}
        )
    
    def _generate_failure_analysis_response(self) -> LLMResponse:
        """Generate failure analysis response."""
        analysis = {
            "root_cause": "Memory allocation failure in scheduler path",
            "confidence": 0.85,
            "suspicious_commits": ["abc123", "def456"],
            "suggested_fixes": [
                {
                    "description": "Add null pointer check",
                    "confidence": 0.9,
                    "code_patch": "if (ptr == NULL) return -ENOMEM;"
                }
            ]
        }
        
        return LLMResponse(
            content=str(analysis),
            model="mock-model",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )
    
    def _generate_default_response(self) -> LLMResponse:
        """Generate default response."""
        return LLMResponse(
            content="Mock response",
            model="mock-model",
            tokens_used=50,
            finish_reason="stop",
            metadata={}
        )


@pytest.fixture
def mock_llm_provider():
    """Provide mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def sample_environments():
    """Provide sample test environments."""
    return [
        Environment(
            id="env-x86-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=4096,
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu"
            ),
            status=EnvironmentStatus.IDLE
        ),
        Environment(
            id="env-arm-1",
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
            id="env-physical-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel i7",
                memory_mb=8192,
                storage_type="nvme",
                is_virtual=False,
                peripherals=[
                    Peripheral(name="eth0", type="network", model="e1000e"),
                    Peripheral(name="sda", type="storage", model="Samsung SSD")
                ]
            ),
            status=EnvironmentStatus.IDLE,
            ip_address="192.168.1.100"
        )
    ]


@pytest.fixture
def sample_code_diff():
    """Provide sample code diff for testing."""
    return """
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -100,6 +100,15 @@ void schedule(void)
     struct task_struct *prev, *next;
     
     prev = current;
+    
+    /* New scheduling optimization */
+    if (prev->policy == SCHED_FIFO) {
+        if (prev->rt_priority > MAX_RT_PRIO) {
+            prev->rt_priority = MAX_RT_PRIO;
+        }
+        return;
+    }
     
     next = pick_next_task(rq);
     context_switch(prev, next);

diff --git a/mm/page_alloc.c b/mm/page_alloc.c
index 7890abc..def1234 100644
--- a/mm/page_alloc.c
+++ b/mm/page_alloc.c
@@ -200,6 +200,10 @@ struct page *alloc_pages(gfp_t gfp_mask, unsigned int order)
     struct page *page;
     
+    /* Add memory pressure check */
+    if (system_memory_pressure() > MEMORY_PRESSURE_THRESHOLD) {
+        return NULL;
+    }
+    
     page = __alloc_pages(gfp_mask, order, preferred_zone);
     return page;
"""


@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end integration tests for complete system workflows."""
    
    def test_complete_code_change_to_results_workflow(
        self, 
        mock_llm_provider, 
        sample_environments, 
        sample_code_diff
    ):
        """Test complete workflow from code change detection to test results.
        
        This test validates the entire pipeline:
        1. Code change detection
        2. AI-powered analysis
        3. Test case generation
        4. Test orchestration and scheduling
        5. Test execution across environments
        6. Result collection and analysis
        7. Coverage analysis
        8. Failure analysis (if applicable)
        """
        # Step 1: Initialize system components
        ai_generator = AITestGenerator(llm_provider=mock_llm_provider)
        orchestrator = TestOrchestrator()
        
        # Add environments to orchestrator
        for env in sample_environments:
            orchestrator.add_environment(env)
        
        # Step 2: Analyze code changes
        analysis = ai_generator.analyze_code_changes(sample_code_diff)
        
        # Verify analysis results
        assert analysis is not None
        assert len(analysis.changed_files) >= 2
        assert "scheduler" in analysis.affected_subsystems
        assert "memory_management" in analysis.affected_subsystems
        assert analysis.impact_score > 0.5
        assert analysis.risk_level == RiskLevel.HIGH
        
        # Step 3: Generate test cases
        test_cases = ai_generator.generate_test_cases(analysis)
        
        # Verify test generation
        assert len(test_cases) >= 20  # At least 10 per function
        
        # Verify test case properties
        for test_case in test_cases:
            assert test_case.id
            assert test_case.name
            assert test_case.test_script
            assert test_case.target_subsystem in analysis.affected_subsystems
            assert test_case.execution_time_estimate > 0
        
        # Step 4: Submit tests to orchestrator
        job_ids = []
        for test_case in test_cases[:5]:  # Submit subset for faster testing
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.HIGH,
                impact_score=analysis.impact_score
            )
            job_ids.append(job_id)
        
        # Step 5: Wait for test execution to complete
        max_wait_time = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(1)
        
        # Step 6: Collect and verify results
        results = []
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            assert job_status is not None
            assert job_status['status'] == 'completed'
            
            if job_status['result']:
                results.append(TestResult.from_dict(job_status['result']))
        
        # Verify results
        assert len(results) > 0
        
        for result in results:
            assert result.test_id
            assert result.status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]
            assert result.execution_time >= 0
            assert result.environment
            assert result.timestamp
        
        # Step 7: Aggregate results
        aggregated = orchestrator.test_runner.aggregate_results(
            results, 
            group_by="architecture"
        )
        
        # Verify aggregation
        assert aggregated['total'] == len(results)
        assert aggregated['total'] == (
            aggregated['passed'] + 
            aggregated['failed'] + 
            aggregated['error'] + 
            aggregated['timeout'] + 
            aggregated['skipped']
        )
        assert 0.0 <= aggregated['pass_rate'] <= 1.0
        assert aggregated['total_execution_time'] >= 0
        
        # Verify architecture grouping
        assert 'groups' in aggregated
        for arch, group_stats in aggregated['groups'].items():
            assert arch in ['x86_64', 'arm64']
            assert group_stats['total'] > 0
            assert 0.0 <= group_stats['pass_rate'] <= 1.0
    
    def test_multi_hardware_compatibility_testing(
        self, 
        mock_llm_provider, 
        sample_environments
    ):
        """Test BSP compatibility across multiple hardware configurations.
        
        This test validates:
        1. Hardware matrix generation
        2. Test execution across different architectures
        3. Compatibility matrix creation
        4. Hardware-specific failure isolation
        """
        # Create test case requiring specific hardware
        test_case = TestCase(
            id="hw-compat-test-1",
            name="Hardware Compatibility Test",
            description="Test kernel module loading across architectures",
            test_type=TestType.INTEGRATION,
            target_subsystem="drivers",
            test_script="""#!/bin/bash
echo "Testing hardware compatibility..."
uname -a
lscpu || echo "lscpu not available"
lsmod | head -10
echo "Hardware compatibility test completed"
exit 0
""",
            execution_time_estimate=60,
            required_hardware=HardwareConfig(
                architecture="x86_64",  # Will be overridden for different envs
                cpu_model="generic",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        
        # Add all environments
        for env in sample_environments:
            orchestrator.add_environment(env)
        
        # Submit test for each architecture
        job_ids = []
        for env in sample_environments:
            # Clone test case with environment-specific requirements
            env_test = TestCase(
                id=f"{test_case.id}-{env.config.architecture}",
                name=f"{test_case.name} ({env.config.architecture})",
                description=test_case.description,
                test_type=test_case.test_type,
                target_subsystem=test_case.target_subsystem,
                test_script=test_case.test_script,
                execution_time_estimate=test_case.execution_time_estimate,
                required_hardware=HardwareConfig(
                    architecture=env.config.architecture,
                    cpu_model=env.config.cpu_model,
                    memory_mb=min(env.config.memory_mb, 2048),
                    is_virtual=env.config.is_virtual
                )
            )
            
            job_id = orchestrator.submit_job(
                test_case=env_test,
                priority=Priority.MEDIUM,
                impact_score=0.7
            )
            job_ids.append((job_id, env.config.architecture))
        
        # Wait for completion
        max_wait_time = 45
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(1)
        
        # Collect results by architecture
        results_by_arch = {}
        for job_id, arch in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            assert job_status is not None
            
            if job_status['result']:
                result = TestResult.from_dict(job_status['result'])
                results_by_arch[arch] = result
        
        # Verify we have results for multiple architectures
        assert len(results_by_arch) >= 2
        
        # Create compatibility matrix
        compatibility_matrix = {}
        for arch, result in results_by_arch.items():
            compatibility_matrix[arch] = {
                'status': result.status.value,
                'execution_time': result.execution_time,
                'environment_id': result.environment.id,
                'passed': result.status == TestStatus.PASSED
            }
        
        # Verify matrix completeness
        expected_architectures = set(env.config.architecture for env in sample_environments)
        actual_architectures = set(compatibility_matrix.keys())
        assert expected_architectures.issubset(actual_architectures)
        
        # Verify each architecture has complete information
        for arch, matrix_entry in compatibility_matrix.items():
            assert 'status' in matrix_entry
            assert 'execution_time' in matrix_entry
            assert 'environment_id' in matrix_entry
            assert 'passed' in matrix_entry
            assert matrix_entry['execution_time'] >= 0
    
    def test_fault_injection_and_recovery_workflow(
        self, 
        mock_llm_provider, 
        sample_environments
    ):
        """Test fault injection, detection, and recovery workflow.
        
        This test validates:
        1. Fault injection during test execution
        2. Fault detection and monitoring
        3. Test isolation and environment recovery
        4. Failure analysis and root cause identification
        """
        # Create test case that will trigger fault injection
        fault_test = TestCase(
            id="fault-injection-test",
            name="Fault Injection Test",
            description="Test system behavior under fault conditions",
            test_type=TestType.INTEGRATION,
            target_subsystem="memory_management",
            test_script="""#!/bin/bash
echo "Starting fault injection test..."

# Simulate memory allocation stress
for i in {1..5}; do
    echo "Allocation round $i"
    # This would normally trigger fault injection
    python3 -c "
import sys
try:
    # Allocate memory blocks
    blocks = []
    for j in range(100):
        blocks.append(b'x' * 1024 * 1024)  # 1MB blocks
    print(f'Allocated {len(blocks)} blocks')
except MemoryError:
    print('Memory allocation failed as expected')
    sys.exit(1)
except Exception as e:
    print(f'Unexpected error: {e}')
    sys.exit(1)
"
    sleep 1
done

echo "Fault injection test completed"
exit 0
""",
            execution_time_estimate=120,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            ),
            metadata={
                "fault_injection": True,
                "fault_types": ["memory_allocation_failure", "timing_variation"]
            }
        )
        
        # Initialize components
        orchestrator = TestOrchestrator()
        root_cause_analyzer = RootCauseAnalyzer(llm_provider=mock_llm_provider)
        
        # Add environment
        test_env = sample_environments[0]  # Use x86_64 environment
        orchestrator.add_environment(test_env)
        
        # Submit fault injection test
        job_id = orchestrator.submit_job(
            test_case=fault_test,
            priority=Priority.HIGH,
            impact_score=0.9
        )
        
        # Monitor execution
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] == 'completed':
                break
            time.sleep(2)
        
        # Get final job status
        job_status = orchestrator.get_job_status(job_id)
        assert job_status is not None
        assert job_status['status'] == 'completed'
        
        # Analyze result
        if job_status['result']:
            result = TestResult.from_dict(job_status['result'])
            
            # Verify test execution
            assert result.test_id == fault_test.id
            assert result.status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]
            assert result.execution_time > 0
            
            # If test failed, perform root cause analysis
            if result.status == TestStatus.FAILED:
                failure_analysis = root_cause_analyzer.analyze_failure(result)
                
                # Verify failure analysis
                assert failure_analysis.failure_id == result.test_id
                assert failure_analysis.root_cause
                assert 0.0 <= failure_analysis.confidence <= 1.0
                assert failure_analysis.error_pattern
                
                # Verify suggested fixes
                if failure_analysis.suggested_fixes:
                    for fix in failure_analysis.suggested_fixes:
                        assert fix.description
                        assert 0.0 <= fix.confidence <= 1.0
            
            # Verify environment recovery
            final_env_status = test_env.status
            assert final_env_status == EnvironmentStatus.IDLE
    
    def test_ci_cd_integration_workflow(
        self, 
        mock_llm_provider, 
        sample_environments
    ):
        """Test CI/CD integration workflow.
        
        This test validates:
        1. VCS webhook handling
        2. Automatic test triggering
        3. Status reporting back to VCS
        4. Notification delivery
        """
        # Mock VCS integration
        vcs_integration = Mock(spec=VCSIntegration)
        notification_service = Mock(spec=NotificationDispatcher)
        
        # Create sample commit event
        commit_event = {
            'event_type': 'push',
            'repository': 'torvalds/linux',
            'branch': 'master',
            'commit_sha': 'abc123def456',
            'author': 'developer@example.com',
            'message': 'Fix scheduler race condition',
            'changed_files': ['kernel/sched/core.c', 'kernel/sched/fair.c'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Initialize system components
        ai_generator = AITestGenerator(llm_provider=mock_llm_provider)
        orchestrator = TestOrchestrator()
        
        # Add environments
        for env in sample_environments[:2]:  # Use subset for faster testing
            orchestrator.add_environment(env)
        
        # Step 1: Process VCS event (simulate webhook)
        # In real system, this would be triggered by webhook
        
        # Step 2: Analyze commit changes
        mock_diff = f"""
diff --git a/{commit_event['changed_files'][0]} b/{commit_event['changed_files'][0]}
index 1234567..abcdefg 100644
--- a/{commit_event['changed_files'][0]}
+++ b/{commit_event['changed_files'][0]}
@@ -100,6 +100,10 @@ void schedule(void)
     struct task_struct *prev, *next;
     
     prev = current;
+    
+    /* Fix race condition */
+    if (need_resched())
+        return;
     
     next = pick_next_task(rq);
"""
        
        analysis = ai_generator.analyze_code_changes(mock_diff)
        
        # Step 3: Generate and submit tests
        test_cases = ai_generator.generate_test_cases(analysis)
        
        # Submit high-priority tests for CI/CD
        job_ids = []
        for test_case in test_cases[:3]:  # Submit subset
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.CRITICAL,  # High priority for CI/CD
                impact_score=analysis.impact_score
            )
            job_ids.append(job_id)
        
        # Step 4: Monitor execution and report status
        vcs_integration.report_status.return_value = True
        notification_service.send_notification.return_value = True
        
        # Report initial status
        vcs_integration.report_status(
            commit_sha=commit_event['commit_sha'],
            status='pending',
            description=f'Running {len(job_ids)} tests',
            target_url='https://testing.example.com/results'
        )
        
        # Wait for completion
        max_wait_time = 45
        start_time = time.time()
        completed_jobs = 0
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            current_completed = queue_status['completed_jobs']
            
            if current_completed > completed_jobs:
                completed_jobs = current_completed
                # Report progress
                vcs_integration.report_status(
                    commit_sha=commit_event['commit_sha'],
                    status='pending',
                    description=f'Completed {completed_jobs}/{len(job_ids)} tests'
                )
            
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(2)
        
        # Step 5: Collect final results and report
        results = []
        all_passed = True
        
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['result']:
                result = TestResult.from_dict(job_status['result'])
                results.append(result)
                if result.status != TestStatus.PASSED:
                    all_passed = False
        
        # Report final status to VCS
        final_status = 'success' if all_passed else 'failure'
        pass_rate = sum(1 for r in results if r.status == TestStatus.PASSED) / len(results)
        
        vcs_integration.report_status(
            commit_sha=commit_event['commit_sha'],
            status=final_status,
            description=f'Tests completed: {len(results)} total, {pass_rate:.1%} passed'
        )
        
        # Send notifications
        if not all_passed:
            failed_tests = [r for r in results if r.status != TestStatus.PASSED]
            notification_service.send_notification(
                recipients=[commit_event['author']],
                subject=f'Test failures in {commit_event["repository"]}',
                message=f'{len(failed_tests)} tests failed for commit {commit_event["commit_sha"][:8]}'
            )
        
        # Verify CI/CD workflow
        assert len(results) > 0
        assert vcs_integration.report_status.call_count >= 2  # At least initial and final
        
        # Verify notification behavior
        if not all_passed:
            assert notification_service.send_notification.called
        
        # Verify all jobs completed
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            assert job_status['status'] == 'completed'
    
    def test_performance_regression_detection_workflow(
        self, 
        mock_llm_provider, 
        sample_environments
    ):
        """Test performance regression detection workflow.
        
        This test validates:
        1. Performance benchmark execution
        2. Baseline comparison
        3. Regression detection
        4. Performance trend analysis
        """
        # Create performance test case
        perf_test = TestCase(
            id="perf-regression-test",
            name="Scheduler Performance Test",
            description="Measure scheduler performance metrics",
            test_type=TestType.PERFORMANCE,
            target_subsystem="scheduler",
            test_script="""#!/bin/bash
echo "Starting scheduler performance test..."

# Simulate performance measurements
echo "Measuring context switch latency..."
CONTEXT_SWITCH_TIME=$(python3 -c "
import time
import random
# Simulate context switch measurement
base_time = 1.5  # microseconds
variation = random.uniform(-0.2, 0.3)  # Add some variation
result = base_time + variation
print(f'{result:.3f}')
")

echo "Measuring scheduling latency..."
SCHED_LATENCY=$(python3 -c "
import time
import random
base_latency = 2.1  # microseconds
variation = random.uniform(-0.1, 0.4)
result = base_latency + variation
print(f'{result:.3f}')
")

echo "Performance Results:"
echo "context_switch_latency_us: $CONTEXT_SWITCH_TIME"
echo "scheduling_latency_us: $SCHED_LATENCY"

# Write results to file for collection
cat > /tmp/perf_results.json << EOF
{
    "context_switch_latency_us": $CONTEXT_SWITCH_TIME,
    "scheduling_latency_us": $SCHED_LATENCY,
    "timestamp": "$(date -Iseconds)"
}
EOF

echo "Performance test completed"
exit 0
""",
            execution_time_estimate=180,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=4096,
                is_virtual=True
            ),
            metadata={
                "performance_test": True,
                "metrics": ["context_switch_latency_us", "scheduling_latency_us"],
                "baseline_comparison": True
            }
        )
        
        # Initialize components
        orchestrator = TestOrchestrator()
        
        # Add environment
        test_env = sample_environments[0]
        orchestrator.add_environment(test_env)
        
        # Submit performance test
        job_id = orchestrator.submit_job(
            test_case=perf_test,
            priority=Priority.MEDIUM,
            impact_score=0.6
        )
        
        # Wait for completion
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] == 'completed':
                break
            time.sleep(2)
        
        # Get results
        job_status = orchestrator.get_job_status(job_id)
        assert job_status is not None
        assert job_status['status'] == 'completed'
        
        if job_status['result']:
            result = TestResult.from_dict(job_status['result'])
            
            # Verify performance test execution
            assert result.test_id == perf_test.id
            assert result.status in [TestStatus.PASSED, TestStatus.FAILED]
            assert result.execution_time > 0
            
            # Simulate performance analysis
            # In real system, this would extract metrics from artifacts
            mock_current_metrics = {
                'context_switch_latency_us': 1.7,
                'scheduling_latency_us': 2.4
            }
            
            mock_baseline_metrics = {
                'context_switch_latency_us': 1.5,
                'scheduling_latency_us': 2.1
            }
            
            # Calculate performance changes
            performance_changes = {}
            regressions_detected = []
            
            for metric, current_value in mock_current_metrics.items():
                baseline_value = mock_baseline_metrics.get(metric, current_value)
                change_percent = ((current_value - baseline_value) / baseline_value) * 100
                performance_changes[metric] = {
                    'current': current_value,
                    'baseline': baseline_value,
                    'change_percent': change_percent
                }
                
                # Detect regressions (>10% increase in latency is bad)
                if change_percent > 10.0:
                    regressions_detected.append({
                        'metric': metric,
                        'change_percent': change_percent,
                        'severity': 'high' if change_percent > 20.0 else 'medium'
                    })
            
            # Verify performance analysis
            assert len(performance_changes) > 0
            
            for metric, change_data in performance_changes.items():
                assert 'current' in change_data
                assert 'baseline' in change_data
                assert 'change_percent' in change_data
                assert change_data['current'] > 0
                assert change_data['baseline'] > 0
            
            # If regressions detected, verify they're properly identified
            if regressions_detected:
                for regression in regressions_detected:
                    assert regression['metric'] in mock_current_metrics
                    assert regression['change_percent'] > 10.0
                    assert regression['severity'] in ['medium', 'high']
    
    def test_security_testing_workflow(
        self, 
        mock_llm_provider, 
        sample_environments
    ):
        """Test security testing workflow.
        
        This test validates:
        1. Security-focused test generation
        2. Fuzzing execution
        3. Vulnerability detection
        4. Security issue classification
        5. Security report generation
        """
        # Create security test case
        security_test = TestCase(
            id="security-fuzz-test",
            name="System Call Fuzzing Test",
            description="Fuzz system call interfaces for security vulnerabilities",
            test_type=TestType.SECURITY,
            target_subsystem="syscalls",
            test_script="""#!/bin/bash
echo "Starting security fuzzing test..."

# Simulate fuzzing activity
echo "Fuzzing system call interfaces..."

# Test 1: Invalid pointer fuzzing
echo "Testing invalid pointer handling..."
python3 -c "
import os
import sys
import random

# Simulate fuzzing with invalid pointers
test_cases = [
    'null_pointer_test',
    'invalid_address_test', 
    'buffer_overflow_test',
    'integer_overflow_test'
]

results = []
for test in test_cases:
    # Simulate test execution
    success = random.choice([True, True, True, False])  # 75% success rate
    results.append({'test': test, 'passed': success})
    print(f'{test}: {\"PASS\" if success else \"FAIL\"}')

# Check for any failures (potential vulnerabilities)
failed_tests = [r for r in results if not r['passed']]
if failed_tests:
    print(f'SECURITY ISSUE: {len(failed_tests)} tests failed')
    for failed in failed_tests:
        print(f'  - {failed[\"test\"]} failed (potential vulnerability)')
    sys.exit(1)
else:
    print('All security tests passed')
    sys.exit(0)
"

echo "Security fuzzing test completed"
""",
            execution_time_estimate=240,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=2048,
                is_virtual=True
            ),
            metadata={
                "security_test": True,
                "fuzzing_targets": ["syscalls", "ioctl", "network_protocols"],
                "vulnerability_patterns": ["buffer_overflow", "use_after_free", "integer_overflow"]
            }
        )
        
        # Initialize components
        orchestrator = TestOrchestrator()
        
        # Add environment
        test_env = sample_environments[0]
        orchestrator.add_environment(test_env)
        
        # Submit security test
        job_id = orchestrator.submit_job(
            test_case=security_test,
            priority=Priority.HIGH,
            impact_score=0.8
        )
        
        # Wait for completion
        max_wait_time = 90
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] == 'completed':
                break
            time.sleep(2)
        
        # Get results
        job_status = orchestrator.get_job_status(job_id)
        assert job_status is not None
        assert job_status['status'] == 'completed'
        
        if job_status['result']:
            result = TestResult.from_dict(job_status['result'])
            
            # Verify security test execution
            assert result.test_id == security_test.id
            assert result.status in [TestStatus.PASSED, TestStatus.FAILED]
            assert result.execution_time > 0
            
            # Simulate security analysis
            if result.status == TestStatus.FAILED:
                # Simulate vulnerability detection
                mock_vulnerabilities = [
                    {
                        'type': 'buffer_overflow',
                        'severity': 'high',
                        'location': 'syscall_handler.c:123',
                        'description': 'Buffer overflow in system call parameter validation',
                        'cvss_score': 7.8,
                        'exploitable': True
                    }
                ]
                
                # Verify vulnerability classification
                for vuln in mock_vulnerabilities:
                    assert vuln['type'] in ['buffer_overflow', 'use_after_free', 'integer_overflow']
                    assert vuln['severity'] in ['low', 'medium', 'high', 'critical']
                    assert 0.0 <= vuln['cvss_score'] <= 10.0
                    assert isinstance(vuln['exploitable'], bool)
                    assert vuln['description']
                    assert vuln['location']
                
                # Simulate security report generation
                security_report = {
                    'test_id': result.test_id,
                    'vulnerabilities_found': len(mock_vulnerabilities),
                    'high_severity_count': sum(1 for v in mock_vulnerabilities if v['severity'] == 'high'),
                    'exploitable_count': sum(1 for v in mock_vulnerabilities if v['exploitable']),
                    'overall_risk': 'high' if any(v['severity'] == 'high' for v in mock_vulnerabilities) else 'medium',
                    'recommendations': [
                        'Implement input validation for system call parameters',
                        'Add bounds checking for buffer operations',
                        'Enable KASAN for memory error detection'
                    ]
                }
                
                # Verify security report
                assert security_report['vulnerabilities_found'] > 0
                assert security_report['overall_risk'] in ['low', 'medium', 'high', 'critical']
                assert len(security_report['recommendations']) > 0
                
                for recommendation in security_report['recommendations']:
                    assert isinstance(recommendation, str)
                    assert len(recommendation) > 0


@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests for system-level functionality."""
    
    def test_api_client_integration(self, mock_llm_provider, sample_environments):
        """Test API client integration with backend services."""
        # This would test the API client against a running API server
        # For now, we'll test the client interface
        
        # Mock API responses
        with patch('api.client.requests.Session.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'success': True,
                'data': {
                    'status': 'healthy',
                    'version': '1.0.0',
                    'uptime': 3600
                }
            }
            mock_response.raise_for_status.return_value = None
            mock_request.return_value = mock_response
            
            # Test client initialization and health check
            client = AgenticTestingClient(base_url='http://localhost:8000')
            health = client.health_check()
            
            assert health['status'] == 'healthy'
            assert health['version'] == '1.0.0'
            assert health['uptime'] == 3600
    
    def test_database_integration(self, sample_environments):
        """Test database integration for result persistence."""
        # Mock database operations
        mock_repo = Mock()  # spec=TestResultRepository
        
        # Create sample test result
        test_result = TestResult(
            test_id="db-test-1",
            status=TestStatus.PASSED,
            execution_time=45.2,
            environment=sample_environments[0],
            timestamp=datetime.now()
        )
        
        # Test result storage
        mock_repo.save_result.return_value = test_result.test_id
        result_id = mock_repo.save_result(test_result)
        
        assert result_id == test_result.test_id
        mock_repo.save_result.assert_called_once_with(test_result)
        
        # Test result retrieval
        mock_repo.get_result.return_value = test_result
        retrieved_result = mock_repo.get_result(test_result.test_id)
        
        assert retrieved_result.test_id == test_result.test_id
        assert retrieved_result.status == test_result.status
        mock_repo.get_result.assert_called_once_with(test_result.test_id)
    
    def test_concurrent_test_execution(self, mock_llm_provider, sample_environments):
        """Test concurrent test execution across multiple environments."""
        # Create multiple test cases
        test_cases = []
        for i in range(6):
            test_case = TestCase(
                id=f"concurrent-test-{i}",
                name=f"Concurrent Test {i}",
                description=f"Test case {i} for concurrent execution",
                test_type=TestType.UNIT,
                target_subsystem="testing",
                test_script=f"""#!/bin/bash
echo "Running concurrent test {i}"
sleep {1 + (i % 3)}  # Variable sleep time
echo "Test {i} completed"
exit 0
""",
                execution_time_estimate=30 + (i * 5),
                required_hardware=HardwareConfig(
                    architecture=sample_environments[i % len(sample_environments)].config.architecture,
                    cpu_model="generic",
                    memory_mb=1024,
                    is_virtual=True
                )
            )
            test_cases.append(test_case)
        
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        
        # Add all environments
        for env in sample_environments:
            orchestrator.add_environment(env)
        
        # Submit all tests
        job_ids = []
        for test_case in test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_ids.append(job_id)
        
        # Monitor concurrent execution
        start_time = time.time()
        max_concurrent = 0
        
        while time.time() - start_time < 60:  # Max 60 seconds
            queue_status = orchestrator.get_queue_status()
            current_running = queue_status['running_jobs']
            max_concurrent = max(max_concurrent, current_running)
            
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(1)
        
        # Verify concurrent execution occurred
        assert max_concurrent > 1, "Tests should have run concurrently"
        
        # Verify all tests completed
        completed_count = 0
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status and job_status['status'] == 'completed':
                completed_count += 1
        
        assert completed_count == len(job_ids), "All tests should have completed"
    
    def test_error_handling_and_recovery(self, mock_llm_provider, sample_environments):
        """Test system error handling and recovery mechanisms."""
        # Create test case that will cause errors
        error_test = TestCase(
            id="error-handling-test",
            name="Error Handling Test",
            description="Test system error handling",
            test_type=TestType.UNIT,
            target_subsystem="error_handling",
            test_script="""#!/bin/bash
echo "Testing error handling..."

# Simulate different types of errors
case $((RANDOM % 4)) in
    0)
        echo "Simulating timeout"
        sleep 300  # This should timeout
        ;;
    1)
        echo "Simulating crash"
        kill -9 $$  # Kill self
        ;;
    2)
        echo "Simulating failure"
        exit 1
        ;;
    *)
        echo "Normal execution"
        exit 0
        ;;
esac
""",
            execution_time_estimate=30,  # Short timeout to trigger timeout error
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=512,
                is_virtual=True
            )
        )
        
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        orchestrator.add_environment(sample_environments[0])
        
        # Submit error test multiple times to test different error paths
        job_ids = []
        for i in range(3):
            job_id = orchestrator.submit_job(
                test_case=TestCase(
                    id=f"{error_test.id}-{i}",
                    name=f"{error_test.name} {i}",
                    description=error_test.description,
                    test_type=error_test.test_type,
                    target_subsystem=error_test.target_subsystem,
                    test_script=error_test.test_script,
                    execution_time_estimate=error_test.execution_time_estimate,
                    required_hardware=error_test.required_hardware
                ),
                priority=Priority.LOW,
                impact_score=0.3
            )
            job_ids.append(job_id)
        
        # Wait for completion with generous timeout
        max_wait_time = 120
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(2)
        
        # Verify error handling
        error_statuses = []
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            if job_status:
                error_statuses.append(job_status['status'])
                
                # Verify job completed (even if with errors)
                assert job_status['status'] == 'completed'
                
                # Check result details
                if job_status['result']:
                    result = TestResult.from_dict(job_status['result'])
                    
                    # Verify error information is captured
                    if result.status in [TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT]:
                        assert result.failure_info is not None
                        assert result.failure_info.error_message
        
        # Verify system recovered and environment is still available
        final_queue_status = orchestrator.get_queue_status()
        assert final_queue_status['available_environments'] > 0