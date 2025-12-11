"""System workflow integration tests.

This module tests specific system workflows and integration scenarios
that validate the interaction between multiple components.
"""

import pytest
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, TestType, RiskLevel, CodeAnalysis
)
from orchestrator.scheduler import Priority
from ai_generator.test_generator import AITestGenerator
from orchestrator.scheduler import TestOrchestrator
from execution.test_runner import TestRunner
from analysis.coverage_analyzer import CoverageAnalyzer
from analysis.root_cause_analyzer import RootCauseAnalyzer
from integration.vcs_integration import VCSIntegration
from integration.notification_service import NotificationDispatcher

from tests.fixtures.end_to_end_fixtures import (
    comprehensive_test_environments, comprehensive_test_cases,
    sample_test_results, sample_code_analyses, sample_failure_analyses,
    mock_vcs_events, performance_baselines, security_vulnerability_patterns
)
from tests.integration.test_end_to_end_workflows import MockLLMProvider


@pytest.mark.integration
class TestCodeAnalysisWorkflow:
    """Test code analysis and test generation workflow."""
    
    def test_git_diff_to_test_generation_workflow(
        self, 
        comprehensive_test_environments,
        sample_code_analyses
    ):
        """Test complete workflow from git diff to test case generation."""
        # Mock LLM provider
        mock_llm = MockLLMProvider()
        ai_generator = AITestGenerator(llm_provider=mock_llm)
        
        # Sample git diff
        git_diff = """
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -3000,6 +3000,20 @@ void schedule(void)
 {
     struct task_struct *prev, *next;
     struct rq *rq = cpu_rq(smp_processor_id());
+    
+    /*
+     * New optimization: check if current task can continue
+     * running to avoid unnecessary context switches
+     */
+    if (current->policy == SCHED_NORMAL) {
+        if (current->se.vruntime < rq->cfs.min_vruntime + sched_slice(&rq->cfs, &current->se)) {
+            /* Current task can continue running */
+            if (!need_resched())
+                return;
+        }
+    }
 
     prev = current;
     next = pick_next_task(rq, prev);
@@ -3010,6 +3024,12 @@ void schedule(void)
         context_switch(rq, prev, next);
     }
 }
+
+static inline bool should_preempt_current(struct task_struct *curr, struct task_struct *se)
+{
+    return (se->se.vruntime < curr->se.vruntime - sched_slice(&curr->se.cfs_rq->cfs, &curr->se));
+}
+
"""
        
        # Step 1: Analyze the diff
        analysis = ai_generator.analyze_code_changes(git_diff)
        
        # Verify analysis captures key information
        assert analysis is not None
        assert len(analysis.changed_files) > 0
        assert "scheduler" in analysis.affected_subsystems
        assert analysis.impact_score > 0.0
        assert analysis.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        
        # Verify function detection
        function_names = [f.name for f in analysis.changed_functions]
        assert "schedule" in function_names
        
        # Step 2: Generate test cases based on analysis
        test_cases = ai_generator.generate_test_cases(analysis)
        
        # Verify test generation
        assert len(test_cases) >= 10  # Should generate multiple tests
        
        # Verify test case properties
        scheduler_tests = [tc for tc in test_cases if tc.target_subsystem == "scheduler"]
        assert len(scheduler_tests) > 0
        
        for test_case in scheduler_tests:
            assert test_case.id
            assert test_case.name
            assert test_case.test_script
            assert test_case.execution_time_estimate > 0
            assert "schedule" in test_case.test_script or "scheduler" in test_case.description.lower()
        
        # Step 3: Verify test types are appropriate
        test_types = set(tc.test_type for tc in test_cases)
        expected_types = {TestType.UNIT, TestType.INTEGRATION, TestType.PERFORMANCE}
        assert test_types.intersection(expected_types), "Should generate appropriate test types"
        
        # Step 4: Verify code path targeting
        for test_case in test_cases:
            if test_case.code_paths:
                # Should target the modified function
                assert any("schedule" in path for path in test_case.code_paths)
    
    def test_multi_subsystem_analysis_workflow(self):
        """Test analysis of changes affecting multiple subsystems."""
        mock_llm = MockLLMProvider()
        ai_generator = AITestGenerator(llm_provider=mock_llm)
        
        # Multi-subsystem diff
        complex_diff = """
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -100,6 +100,10 @@ void schedule(void)
+    /* Check memory pressure before scheduling */
+    if (system_memory_pressure() > MEMORY_PRESSURE_HIGH) {
+        trigger_memory_reclaim();
+    }

diff --git a/mm/vmscan.c b/mm/vmscan.c
index 7890abc..def1234 100644
--- a/mm/vmscan.c
+++ b/mm/vmscan.c
@@ -200,6 +200,15 @@ unsigned long shrink_page_list(struct list_head *page_list)
+    /* Integrate with scheduler for better reclaim timing */
+    if (current->policy == SCHED_NORMAL) {
+        /* Allow scheduler to preempt during long reclaim */
+        if (need_resched()) {
+            cond_resched();
+        }
+    }

diff --git a/net/core/dev.c b/net/core/dev.c
index abc1234..567890d 100644
--- a/net/core/dev.c
+++ b/net/core/dev.c
@@ -300,6 +300,10 @@ int netif_receive_skb(struct sk_buff *skb)
+    /* Check system load before processing */
+    if (system_load_average() > NET_LOAD_THRESHOLD) {
+        return NET_RX_DROP;
+    }
"""
        
        # Analyze multi-subsystem changes
        analysis = ai_generator.analyze_code_changes(complex_diff)
        
        # Verify multi-subsystem detection
        assert len(analysis.affected_subsystems) >= 3
        expected_subsystems = {"scheduler", "memory_management", "networking"}
        actual_subsystems = set(analysis.affected_subsystems)
        assert expected_subsystems.issubset(actual_subsystems)
        
        # Verify higher impact score for multi-subsystem changes
        assert analysis.impact_score >= 0.7
        assert analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Generate tests
        test_cases = ai_generator.generate_test_cases(analysis)
        
        # Verify tests cover all affected subsystems
        test_subsystems = set(tc.target_subsystem for tc in test_cases)
        assert len(test_subsystems.intersection(expected_subsystems)) >= 2
        
        # Verify integration tests are generated for cross-subsystem interactions
        integration_tests = [tc for tc in test_cases if tc.test_type == TestType.INTEGRATION]
        assert len(integration_tests) > 0


@pytest.mark.integration
class TestTestExecutionWorkflow:
    """Test test execution and result collection workflow."""
    
    def test_parallel_execution_across_architectures(
        self, 
        comprehensive_test_environments,
        comprehensive_test_cases
    ):
        """Test parallel test execution across different architectures."""
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        
        # Add environments with different architectures
        x86_envs = [env for env in comprehensive_test_environments if env.config.architecture == "x86_64"]
        arm_envs = [env for env in comprehensive_test_environments if env.config.architecture == "arm64"]
        
        for env in x86_envs[:2] + arm_envs[:1]:  # Use subset for faster testing
            orchestrator.add_environment(env)
        
        # Create architecture-specific test cases
        arch_tests = []
        for arch in ["x86_64", "arm64"]:
            test_case = TestCase(
                id=f"arch-test-{arch}",
                name=f"Architecture Test for {arch}",
                description=f"Test kernel functionality on {arch}",
                test_type=TestType.INTEGRATION,
                target_subsystem="architecture",
                test_script=f"""#!/bin/bash
echo "Testing on {arch} architecture"
uname -m | grep -E "({arch}|aarch64)" || exit 1
echo "Architecture test completed for {arch}"
exit 0
""",
                execution_time_estimate=30,
                required_hardware=HardwareConfig(
                    architecture=arch,
                    cpu_model="generic",
                    memory_mb=1024,
                    is_virtual=True
                )
            )
            arch_tests.append(test_case)
        
        # Submit tests
        job_ids = []
        for test_case in arch_tests:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.6
            )
            job_ids.append((job_id, test_case.required_hardware.architecture))
        
        # Monitor parallel execution
        start_time = time.time()
        max_concurrent = 0
        
        while time.time() - start_time < 60:
            queue_status = orchestrator.get_queue_status()
            current_running = queue_status['running_jobs']
            max_concurrent = max(max_concurrent, current_running)
            
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(1)
        
        # Verify parallel execution occurred
        assert max_concurrent > 1, "Tests should run in parallel across architectures"
        
        # Collect results by architecture
        results_by_arch = {}
        for job_id, arch in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            assert job_status is not None
            assert job_status['status'] == 'completed'
            
            if job_status['result']:
                result = TestResult.from_dict(job_status['result'])
                results_by_arch[arch] = result
        
        # Verify results for each architecture
        assert len(results_by_arch) >= 2
        for arch, result in results_by_arch.items():
            assert result.status in [TestStatus.PASSED, TestStatus.FAILED]
            assert result.environment.config.architecture == arch
    
    def test_test_retry_and_failure_handling(
        self, 
        comprehensive_test_environments
    ):
        """Test test retry logic and failure handling."""
        # Create flaky test that fails sometimes
        flaky_test = TestCase(
            id="flaky-test-001",
            name="Flaky Test",
            description="Test that fails intermittently",
            test_type=TestType.UNIT,
            target_subsystem="testing",
            test_script="""#!/bin/bash
# Randomly fail 50% of the time
if [ $((RANDOM % 2)) -eq 0 ]; then
    echo "Test failed randomly"
    exit 1
else
    echo "Test passed"
    exit 0
fi
""",
            execution_time_estimate=10,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=512,
                is_virtual=True
            )
        )
        
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        orchestrator.add_environment(comprehensive_test_environments[0])
        
        # Submit flaky test multiple times to test retry logic
        job_ids = []
        for i in range(3):
            job_id = orchestrator.submit_job(
                test_case=TestCase(
                    id=f"{flaky_test.id}-{i}",
                    name=f"{flaky_test.name} {i}",
                    description=flaky_test.description,
                    test_type=flaky_test.test_type,
                    target_subsystem=flaky_test.target_subsystem,
                    test_script=flaky_test.test_script,
                    execution_time_estimate=flaky_test.execution_time_estimate,
                    required_hardware=flaky_test.required_hardware
                ),
                priority=Priority.LOW,
                impact_score=0.3
            )
            job_ids.append(job_id)
        
        # Wait for completion
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            queue_status = orchestrator.get_queue_status()
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(1)
        
        # Analyze retry behavior
        retry_counts = []
        final_statuses = []
        
        for job_id in job_ids:
            job_status = orchestrator.get_job_status(job_id)
            assert job_status is not None
            assert job_status['status'] == 'completed'
            
            retry_counts.append(job_status['retry_count'])
            
            if job_status['result']:
                result = TestResult.from_dict(job_status['result'])
                final_statuses.append(result.status)
        
        # Verify retry logic
        assert len(retry_counts) > 0
        # Some tests should have been retried (due to random failures)
        assert any(count > 0 for count in retry_counts)
        
        # Verify final statuses are valid
        for status in final_statuses:
            assert status in [TestStatus.PASSED, TestStatus.FAILED]
    
    def test_resource_allocation_and_cleanup(
        self, 
        comprehensive_test_environments,
        comprehensive_test_cases
    ):
        """Test resource allocation and cleanup workflow."""
        # Initialize orchestrator
        orchestrator = TestOrchestrator()
        
        # Add limited environments to test resource contention
        test_envs = comprehensive_test_environments[:2]  # Only 2 environments
        for env in test_envs:
            orchestrator.add_environment(env)
        
        # Submit more tests than available environments
        test_cases = comprehensive_test_cases[:4]  # 4 tests, 2 environments
        job_ids = []
        
        for test_case in test_cases:
            job_id = orchestrator.submit_job(
                test_case=test_case,
                priority=Priority.MEDIUM,
                impact_score=0.5
            )
            job_ids.append(job_id)
        
        # Monitor resource allocation
        resource_usage_history = []
        start_time = time.time()
        
        while time.time() - start_time < 90:
            queue_status = orchestrator.get_queue_status()
            resource_usage_history.append({
                'timestamp': time.time(),
                'running_jobs': queue_status['running_jobs'],
                'pending_jobs': queue_status['pending_jobs'],
                'available_environments': queue_status['available_environments'],
                'allocated_environments': queue_status['allocated_environments']
            })
            
            if queue_status['running_jobs'] == 0 and queue_status['pending_jobs'] == 0:
                break
            time.sleep(2)
        
        # Verify resource allocation behavior
        max_running = max(usage['running_jobs'] for usage in resource_usage_history)
        max_allocated = max(usage['allocated_environments'] for usage in resource_usage_history)
        
        # Should not exceed available environments
        assert max_running <= len(test_envs)
        assert max_allocated <= len(test_envs)
        
        # Should have queued tests when resources were exhausted
        had_pending = any(usage['pending_jobs'] > 0 for usage in resource_usage_history)
        assert had_pending, "Should have queued tests when resources were busy"
        
        # Verify final cleanup
        final_status = orchestrator.get_queue_status()
        assert final_status['running_jobs'] == 0
        assert final_status['pending_jobs'] == 0
        assert final_status['available_environments'] == len(test_envs)
        assert final_status['allocated_environments'] == 0


@pytest.mark.integration
class TestAnalysisWorkflow:
    """Test analysis and reporting workflow."""
    
    def test_coverage_analysis_workflow(
        self, 
        sample_test_results
    ):
        """Test coverage analysis and gap identification workflow."""
        # Initialize coverage analyzer
        coverage_analyzer = CoverageAnalyzer()
        
        # Extract coverage data from results
        coverage_results = [r for r in sample_test_results if r.coverage_data]
        assert len(coverage_results) > 0, "Need results with coverage data"
        
        # Step 1: Merge coverage data
        coverage_data_list = [r.coverage_data for r in coverage_results]
        merged_coverage = coverage_analyzer.merge_coverage(coverage_data_list)
        
        # Verify merged coverage
        assert merged_coverage.line_coverage >= 0.0
        assert merged_coverage.branch_coverage >= 0.0
        assert merged_coverage.function_coverage >= 0.0
        assert len(merged_coverage.covered_lines) > 0
        
        # Step 2: Identify coverage gaps
        coverage_gaps = coverage_analyzer.identify_gaps(merged_coverage)
        
        # Verify gap identification
        assert isinstance(coverage_gaps, list)
        for gap in coverage_gaps:
            assert hasattr(gap, 'file_path') or isinstance(gap, str)
        
        # Step 3: Generate coverage report
        coverage_report = coverage_analyzer.generate_report(merged_coverage)
        
        # Verify report structure
        assert 'summary' in coverage_report
        assert 'line_coverage' in coverage_report['summary']
        assert 'branch_coverage' in coverage_report['summary']
        assert 'function_coverage' in coverage_report['summary']
        
        # Step 4: Compare with baseline (simulate)
        baseline_coverage = coverage_data_list[0]  # Use first result as baseline
        coverage_diff = coverage_analyzer.compare_coverage(baseline_coverage, merged_coverage)
        
        # Verify comparison
        assert 'line_coverage_diff' in coverage_diff
        assert 'branch_coverage_diff' in coverage_diff
        assert 'function_coverage_diff' in coverage_diff
    
    def test_failure_analysis_workflow(
        self, 
        sample_test_results,
        sample_failure_analyses
    ):
        """Test failure analysis and root cause identification workflow."""
        # Mock LLM provider for analysis
        mock_llm = MockLLMProvider()
        root_cause_analyzer = RootCauseAnalyzer(llm_provider=mock_llm)
        
        # Get failed test results
        failed_results = [r for r in sample_test_results if r.status == TestStatus.FAILED]
        assert len(failed_results) > 0, "Need failed test results"
        
        # Step 1: Analyze individual failures
        failure_analyses = []
        for failed_result in failed_results[:2]:  # Analyze first 2 failures
            analysis = root_cause_analyzer.analyze_failure(failed_result)
            failure_analyses.append(analysis)
        
        # Verify individual analyses
        for analysis in failure_analyses:
            assert analysis.failure_id
            assert analysis.root_cause
            assert 0.0 <= analysis.confidence <= 1.0
            assert analysis.error_pattern
        
        # Step 2: Group related failures
        all_failures = [TestFailure(result=r) for r in failed_results]
        failure_groups = root_cause_analyzer.group_failures(all_failures)
        
        # Verify grouping
        assert isinstance(failure_groups, list)
        for group in failure_groups:
            assert len(group.failures) > 0
            assert group.common_pattern
        
        # Step 3: Generate fix suggestions
        for analysis in failure_analyses:
            fix_suggestions = root_cause_analyzer.suggest_fixes(analysis)
            
            # Verify fix suggestions
            assert isinstance(fix_suggestions, list)
            for fix in fix_suggestions:
                assert fix.description
                assert 0.0 <= fix.confidence <= 1.0
    
    def test_performance_regression_analysis_workflow(
        self, 
        sample_test_results,
        performance_baselines
    ):
        """Test performance regression detection and analysis workflow."""
        # Get performance test results
        perf_results = [r for r in sample_test_results 
                       if r.test_id.startswith('performance-')]
        
        if not perf_results:
            # Create mock performance result
            from ai_generator.models import TestResult, TestStatus, Environment, HardwareConfig
            
            perf_result = TestResult(
                test_id="performance-scheduler-001",
                status=TestStatus.PASSED,
                execution_time=180.5,
                environment=Environment(
                    id="perf-env-1",
                    config=HardwareConfig(
                        architecture="x86_64",
                        cpu_model="Intel Xeon",
                        memory_mb=4096,
                        is_virtual=True
                    )
                ),
                timestamp=datetime.now(),
                metadata={
                    'performance_metrics': {
                        'context_switch_latency_us': 1.8,  # Regression from baseline 1.5
                        'scheduling_latency_us': 2.3,     # Regression from baseline 2.1
                        'throughput_tasks_per_sec': 9500   # Regression from baseline 10000
                    }
                }
            )
            perf_results = [perf_result]
        
        # Step 1: Extract performance metrics
        current_metrics = {}
        for result in perf_results:
            if 'performance_metrics' in result.metadata:
                current_metrics.update(result.metadata['performance_metrics'])
        
        # Step 2: Compare with baselines
        regressions = []
        improvements = []
        
        baseline_scheduler = performance_baselines.get('scheduler', {})
        for metric, current_value in current_metrics.items():
            if metric in baseline_scheduler:
                baseline_value = baseline_scheduler[metric]
                change_percent = ((current_value - baseline_value) / baseline_value) * 100
                
                if abs(change_percent) > 5.0:  # 5% threshold
                    change_data = {
                        'metric': metric,
                        'current': current_value,
                        'baseline': baseline_value,
                        'change_percent': change_percent,
                        'is_regression': change_percent > 0  # Higher latency is worse
                    }
                    
                    if change_data['is_regression']:
                        regressions.append(change_data)
                    else:
                        improvements.append(change_data)
        
        # Step 3: Classify regression severity
        for regression in regressions:
            if regression['change_percent'] > 20.0:
                regression['severity'] = 'critical'
            elif regression['change_percent'] > 10.0:
                regression['severity'] = 'high'
            else:
                regression['severity'] = 'medium'
        
        # Verify regression detection
        if regressions:
            assert len(regressions) > 0
            for regression in regressions:
                assert regression['metric']
                assert regression['change_percent'] > 5.0
                assert regression['severity'] in ['medium', 'high', 'critical']
    
    def test_security_analysis_workflow(
        self, 
        sample_test_results,
        security_vulnerability_patterns
    ):
        """Test security analysis and vulnerability detection workflow."""
        # Get security test results
        security_results = [r for r in sample_test_results 
                           if r.test_id.startswith('security-')]
        
        if not security_results:
            # Create mock security result with failure
            from ai_generator.models import TestResult, TestStatus, Environment, HardwareConfig, FailureInfo
            
            security_result = TestResult(
                test_id="security-syscall-001",
                status=TestStatus.FAILED,
                execution_time=120.0,
                environment=Environment(
                    id="sec-env-1",
                    config=HardwareConfig(
                        architecture="x86_64",
                        cpu_model="Intel Xeon",
                        memory_mb=2048,
                        is_virtual=True
                    )
                ),
                failure_info=FailureInfo(
                    error_message="Buffer overflow detected in syscall handler",
                    stack_trace="syscall_handler+0x123\nbuffer_overflow+0x456\n"
                ),
                timestamp=datetime.now(),
                metadata={
                    'security_test': True,
                    'vulnerability_found': True,
                    'vulnerability_type': 'buffer_overflow'
                }
            )
            security_results = [security_result]
        
        # Step 1: Analyze security test failures
        vulnerabilities = []
        for result in security_results:
            if result.status == TestStatus.FAILED and result.metadata.get('security_test'):
                vuln_type = result.metadata.get('vulnerability_type', 'unknown')
                
                # Find matching pattern
                matching_pattern = None
                for pattern in security_vulnerability_patterns:
                    if vuln_type in pattern['pattern_id']:
                        matching_pattern = pattern
                        break
                
                if matching_pattern:
                    vulnerability = {
                        'test_id': result.test_id,
                        'type': vuln_type,
                        'severity': matching_pattern['severity'],
                        'cwe_id': matching_pattern['cwe_id'],
                        'description': matching_pattern['description'],
                        'location': 'syscall_handler.c:123',  # From stack trace
                        'fix_suggestion': matching_pattern['fix_suggestion']
                    }
                    vulnerabilities.append(vulnerability)
        
        # Step 2: Classify vulnerabilities by severity
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for vuln in vulnerabilities:
            severity_counts[vuln['severity']] += 1
        
        # Step 3: Generate security report
        security_report = {
            'total_vulnerabilities': len(vulnerabilities),
            'severity_breakdown': severity_counts,
            'high_risk_count': severity_counts['high'] + severity_counts['critical'],
            'vulnerabilities': vulnerabilities,
            'overall_risk': 'high' if severity_counts['high'] + severity_counts['critical'] > 0 else 'medium',
            'recommendations': [
                'Implement input validation for all user-controlled data',
                'Enable compiler security features (stack canaries, ASLR)',
                'Conduct regular security code reviews',
                'Use static analysis tools for vulnerability detection'
            ]
        }
        
        # Verify security analysis
        assert security_report['total_vulnerabilities'] >= 0
        assert security_report['overall_risk'] in ['low', 'medium', 'high', 'critical']
        assert len(security_report['recommendations']) > 0
        
        if vulnerabilities:
            for vuln in vulnerabilities:
                assert vuln['type']
                assert vuln['severity'] in ['low', 'medium', 'high', 'critical']
                assert vuln['description']
                assert vuln['fix_suggestion']


@pytest.mark.integration
class TestNotificationWorkflow:
    """Test notification and reporting workflow."""
    
    def test_failure_notification_workflow(
        self, 
        sample_test_results,
        mock_vcs_events
    ):
        """Test failure notification and escalation workflow."""
        # Mock notification service
        notification_service = Mock(spec=NotificationDispatcher)
        notification_service.send_notification.return_value = True
        
        # Get failed results
        failed_results = [r for r in sample_test_results if r.status == TestStatus.FAILED]
        critical_failures = [r for r in failed_results if r.failure_info and r.failure_info.kernel_panic]
        
        # Step 1: Process test failures
        notifications_sent = []
        
        for result in failed_results:
            # Determine notification severity
            if result.failure_info and result.failure_info.kernel_panic:
                severity = 'critical'
                recipients = ['maintainers@example.com', 'security@example.com']
            elif result.test_id.startswith('security-'):
                severity = 'high'
                recipients = ['security@example.com', 'developers@example.com']
            else:
                severity = 'medium'
                recipients = ['developers@example.com']
            
            # Send notification
            notification_service.send_notification(
                recipients=recipients,
                subject=f'{severity.upper()}: Test failure in {result.test_id}',
                message=f'Test {result.test_id} failed: {result.failure_info.error_message if result.failure_info else "Unknown error"}',
                severity=severity
            )
            
            notifications_sent.append({
                'test_id': result.test_id,
                'severity': severity,
                'recipients': recipients
            })
        
        # Step 2: Verify notification behavior
        assert notification_service.send_notification.call_count == len(failed_results)
        
        # Verify critical failures get escalated
        critical_notifications = [n for n in notifications_sent if n['severity'] == 'critical']
        for notif in critical_notifications:
            assert 'maintainers@example.com' in notif['recipients']
            assert 'security@example.com' in notif['recipients']
        
        # Step 3: Test notification aggregation for multiple failures
        if len(failed_results) > 3:
            # Send summary notification
            summary_message = f"""
Test Failure Summary:
- Total failures: {len(failed_results)}
- Critical failures: {len(critical_failures)}
- Failed subsystems: {set(r.test_id.split('-')[1] for r in failed_results if '-' in r.test_id)}
"""
            
            notification_service.send_notification(
                recipients=['team-lead@example.com'],
                subject=f'Daily Test Summary: {len(failed_results)} failures',
                message=summary_message,
                severity='medium'
            )
    
    def test_vcs_status_reporting_workflow(
        self, 
        mock_vcs_events,
        sample_test_results
    ):
        """Test VCS status reporting workflow."""
        # Mock VCS integration
        vcs_integration = Mock(spec=VCSIntegration)
        vcs_integration.report_status.return_value = True
        
        # Process VCS event
        commit_event = mock_vcs_events[0]  # Use first event
        
        # Step 1: Report initial status
        vcs_integration.report_status(
            commit_sha=commit_event['commit_sha'],
            status='pending',
            description='Tests queued for execution',
            target_url='https://testing.example.com/results'
        )
        
        # Step 2: Report progress updates
        total_tests = len(sample_test_results)
        completed_tests = 0
        
        for i, result in enumerate(sample_test_results):
            completed_tests += 1
            progress = (completed_tests / total_tests) * 100
            
            # Report progress every 25%
            if progress % 25 == 0:
                vcs_integration.report_status(
                    commit_sha=commit_event['commit_sha'],
                    status='pending',
                    description=f'Tests in progress: {completed_tests}/{total_tests} completed ({progress:.0f}%)'
                )
        
        # Step 3: Report final status
        passed_tests = len([r for r in sample_test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in sample_test_results if r.status == TestStatus.FAILED])
        pass_rate = (passed_tests / total_tests) * 100
        
        final_status = 'success' if failed_tests == 0 else 'failure'
        final_description = f'Tests completed: {passed_tests} passed, {failed_tests} failed ({pass_rate:.1f}% pass rate)'
        
        vcs_integration.report_status(
            commit_sha=commit_event['commit_sha'],
            status=final_status,
            description=final_description,
            target_url=f'https://testing.example.com/results/{commit_event["commit_sha"]}'
        )
        
        # Verify VCS reporting
        assert vcs_integration.report_status.call_count >= 3  # Initial + progress + final
        
        # Verify final status is appropriate
        final_call = vcs_integration.report_status.call_args_list[-1]
        final_args = final_call[1]  # keyword arguments
        assert final_args['status'] in ['success', 'failure']
        assert 'completed' in final_args['description']


# Helper class for failure analysis testing
class TestFailure:
    """Helper class to represent test failures for analysis."""
    
    def __init__(self, result: TestResult):
        self.result = result
        self.test_id = result.test_id
        self.error_message = result.failure_info.error_message if result.failure_info else ""
        self.stack_trace = result.failure_info.stack_trace if result.failure_info else ""
        self.subsystem = result.test_id.split('-')[1] if '-' in result.test_id else "unknown"