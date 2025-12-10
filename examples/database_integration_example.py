#!/usr/bin/env python3
"""Example showing database integration with the testing system."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
from ai_generator.models import (
    TestCase, TestResult, Environment, CoverageData, CodeAnalysis,
    TestType, TestStatus, EnvironmentStatus, HardwareConfig, RiskLevel
)

def simulate_testing_workflow():
    """Simulate a complete testing workflow with database persistence."""
    print("🔄 Simulating Complete Testing Workflow")
    print("=" * 50)
    
    # Step 1: Code Analysis (normally from git diff)
    print("\n1️⃣  Code Analysis Phase")
    code_analysis = CodeAnalysis(
        changed_files=["mm/page_alloc.c", "mm/slab.c"],
        affected_subsystems=["memory_management"],
        impact_score=0.8,
        risk_level=RiskLevel.HIGH,
        suggested_test_types=[TestType.UNIT, TestType.PERFORMANCE, TestType.FUZZ]
    )
    
    print(f"   Changed Files: {len(code_analysis.changed_files)}")
    print(f"   Impact Score: {code_analysis.impact_score}")
    print(f"   Risk Level: {code_analysis.risk_level.value}")
    print(f"   Suggested Tests: {[t.value for t in code_analysis.suggested_test_types]}")
    
    # Step 2: Test Case Generation (normally by AI)
    print("\n2️⃣  Test Case Generation Phase")
    
    hw_configs = [
        HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel i7-9700K",
            memory_mb=16384,
            is_virtual=True,
            emulator="qemu"
        ),
        HardwareConfig(
            architecture="arm64",
            cpu_model="ARM Cortex-A78",
            memory_mb=8192,
            is_virtual=True,
            emulator="qemu"
        )
    ]
    
    test_cases = []
    for i, test_type in enumerate(code_analysis.suggested_test_types):
        test_case = TestCase(
            id=f"mm-test-{i+1:03d}",
            name=f"Memory Management {test_type.value.title()} Test",
            description=f"Test memory management subsystem with {test_type.value} approach",
            test_type=test_type,
            target_subsystem="memory_management",
            code_paths=code_analysis.changed_files,
            execution_time_estimate=120 + (i * 60),
            required_hardware=hw_configs[i % len(hw_configs)]
        )
        test_cases.append(test_case)
    
    print(f"   Generated {len(test_cases)} test cases")
    for tc in test_cases:
        print(f"     - {tc.id}: {tc.name} ({tc.test_type.value})")
    
    # Step 3: Environment Provisioning
    print("\n3️⃣  Environment Provisioning Phase")
    
    environments = []
    for i, hw_config in enumerate(hw_configs):
        env = Environment(
            id=f"env-{hw_config.architecture}-{i+1:03d}",
            config=hw_config,
            status=EnvironmentStatus.IDLE,
            kernel_version="6.5.0-rc1",
            ip_address=f"192.168.122.{100+i}"
        )
        environments.append(env)
    
    print(f"   Provisioned {len(environments)} environments")
    for env in environments:
        print(f"     - {env.id}: {env.config.architecture} ({env.status.value})")
    
    # Step 4: Test Execution
    print("\n4️⃣  Test Execution Phase")
    
    test_results = []
    for i, test_case in enumerate(test_cases):
        # Simulate test execution
        env = environments[i % len(environments)]
        env.status = EnvironmentStatus.BUSY
        
        # Simulate different outcomes
        if i == 0:  # First test passes
            status = TestStatus.PASSED
            execution_time = test_case.execution_time_estimate * 0.9
            coverage = CoverageData(
                line_coverage=0.85,
                branch_coverage=0.78,
                function_coverage=0.92,
                covered_lines=[f"{path}:{100+j}" for j, path in enumerate(test_case.code_paths)],
                uncovered_lines=[f"{test_case.code_paths[0]}:{200}"]
            )
            failure_info = None
        elif i == 1:  # Second test fails
            status = TestStatus.FAILED
            execution_time = test_case.execution_time_estimate * 0.3
            coverage = CoverageData(line_coverage=0.45, branch_coverage=0.32, function_coverage=0.67)
            from ai_generator.models import FailureInfo
            failure_info = FailureInfo(
                error_message="Kernel panic: Unable to handle kernel paging request",
                stack_trace="Call Trace:\n [<ffffffff81234567>] page_fault_handler+0x123/0x456",
                exit_code=-11,
                kernel_panic=True
            )
        else:  # Third test times out
            status = TestStatus.TIMEOUT
            execution_time = test_case.execution_time_estimate * 1.5
            coverage = None
            failure_info = None
        
        result = TestResult(
            test_id=test_case.id,
            status=status,
            execution_time=execution_time,
            environment=env,
            coverage_data=coverage,
            failure_info=failure_info,
            timestamp=datetime.now() - timedelta(minutes=i*5)
        )
        test_results.append(result)
        
        env.status = EnvironmentStatus.IDLE
    
    print(f"   Executed {len(test_results)} tests")
    for result in test_results:
        print(f"     - {result.test_id}: {result.status.value} ({result.execution_time:.1f}s)")
    
    # Step 5: Results Analysis
    print("\n5️⃣  Results Analysis Phase")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.status == TestStatus.PASSED)
    failed_tests = sum(1 for r in test_results if r.status == TestStatus.FAILED)
    timeout_tests = sum(1 for r in test_results if r.status == TestStatus.TIMEOUT)
    
    pass_rate = passed_tests / total_tests if total_tests > 0 else 0
    avg_execution_time = sum(r.execution_time for r in test_results) / total_tests
    
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Timeouts: {timeout_tests}")
    print(f"   Pass Rate: {pass_rate:.1%}")
    print(f"   Average Execution Time: {avg_execution_time:.1f}s")
    
    # Coverage analysis
    coverage_results = [r.coverage_data for r in test_results if r.coverage_data]
    if coverage_results:
        avg_line_coverage = sum(c.line_coverage for c in coverage_results) / len(coverage_results)
        avg_branch_coverage = sum(c.branch_coverage for c in coverage_results) / len(coverage_results)
        print(f"   Average Line Coverage: {avg_line_coverage:.1%}")
        print(f"   Average Branch Coverage: {avg_branch_coverage:.1%}")
    
    return {
        'code_analysis': code_analysis,
        'test_cases': test_cases,
        'environments': environments,
        'test_results': test_results,
        'statistics': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': pass_rate,
            'avg_execution_time': avg_execution_time
        }
    }

def demonstrate_database_storage():
    """Demonstrate how data would be stored in the database."""
    print("\n💾 Database Storage Simulation")
    print("=" * 40)
    
    # Note: This is a simulation since we don't have SQLAlchemy installed
    # In a real environment, this would use the database repositories
    
    workflow_data = simulate_testing_workflow()
    
    print("\n📊 Data Storage Summary:")
    print(f"   Code Analyses: 1 record")
    print(f"   Hardware Configs: {len(set(tc.required_hardware.architecture for tc in workflow_data['test_cases']))} unique configs")
    print(f"   Test Cases: {len(workflow_data['test_cases'])} records")
    print(f"   Environments: {len(workflow_data['environments'])} records")
    print(f"   Test Results: {len(workflow_data['test_results'])} records")
    print(f"   Coverage Data: {sum(1 for r in workflow_data['test_results'] if r.coverage_data)} records")
    print(f"   Failure Analyses: {sum(1 for r in workflow_data['test_results'] if r.failure_info)} records")
    
    print("\n🔍 Example Database Queries:")
    print("   - Find all failed tests in memory subsystem")
    print("   - Get coverage trend for last 30 days")
    print("   - List environments by utilization")
    print("   - Find similar failures by error pattern")
    print("   - Get performance baselines for kernel version")
    
    print("\n📈 Analytics Possibilities:")
    print("   - Test execution trends over time")
    print("   - Coverage improvement tracking")
    print("   - Failure pattern analysis")
    print("   - Environment utilization metrics")
    print("   - Performance regression detection")
    
    return workflow_data

def demonstrate_repository_usage():
    """Demonstrate repository pattern usage."""
    print("\n🏛️  Repository Pattern Usage")
    print("=" * 35)
    
    print("Example repository operations (pseudo-code):")
    
    print("\n# Test Case Repository")
    print("test_repo = TestCaseRepository(session)")
    print("test_repo.create(test_case)")
    print("memory_tests = test_repo.list_by_subsystem('memory')")
    print("recent_tests = test_repo.list_recent(days=7)")
    
    print("\n# Test Result Repository")
    print("result_repo = TestResultRepository(session)")
    print("result_repo.create(test_result)")
    print("failed_tests = result_repo.list_failures()")
    print("stats = result_repo.get_statistics()")
    
    print("\n# Coverage Repository")
    print("coverage_repo = CoverageRepository(session)")
    print("aggregate = coverage_repo.get_aggregate_coverage()")
    print("trend = coverage_repo.get_coverage_trend(days=30)")
    
    print("\n# Environment Repository")
    print("env_repo = EnvironmentRepository(session)")
    print("idle_envs = env_repo.list_idle()")
    print("env_repo.update_status(env_id, EnvironmentStatus.BUSY)")
    
    print("\n# Failure Repository")
    print("failure_repo = FailureRepository(session)")
    print("similar = failure_repo.list_by_pattern('kernel panic')")
    print("high_conf = failure_repo.list_high_confidence(threshold=0.8)")

def main():
    """Main demonstration function."""
    print("🗄️  Database Integration Example")
    print("=" * 50)
    
    try:
        # Simulate complete workflow
        workflow_data = demonstrate_database_storage()
        
        # Show repository usage
        demonstrate_repository_usage()
        
        print("\n✅ Database Integration Example Completed!")
        
        print("\n🚀 To Use With Real Database:")
        print("   1. Install dependencies: pip install sqlalchemy psycopg2-binary")
        print("   2. Configure database in .env file")
        print("   3. Initialize: python -m database.cli init")
        print("   4. Use repositories in your code:")
        print()
        print("   from database.utils import get_database_service")
        print("   service = get_database_service()")
        print("   with service.get_repositories() as repos:")
        print("       repos['test_case'].create(test_case)")
        print("       results = repos['test_result'].list_recent()")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())