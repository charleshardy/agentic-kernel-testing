#!/usr/bin/env python3
"""Manual test for task 9 implementation."""

import sys
sys.path.insert(0, '.')

from execution.test_runner import TestRunner
from execution.environment_manager import EnvironmentManager
from ai_generator.models import (
    TestCase, TestType, HardwareConfig, Environment, EnvironmentStatus
)
from datetime import datetime
import tempfile
from pathlib import Path

def test_basic_execution():
    """Test basic test execution."""
    print("Testing basic test execution...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        # Create environment manager
        env_manager = EnvironmentManager(work_dir=work_dir)
        runner = TestRunner(environment_manager=env_manager)
        
        # Create hardware config
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='test_cpu',
            memory_mb=1024,
            is_virtual=True,
            emulator='qemu'
        )
        
        # Provision environment
        environment = env_manager.provision_environment(config)
        print(f"✓ Environment provisioned: {environment.id}")
        
        # Create a simple passing test
        test = TestCase(
            id='test_001',
            name='simple_test',
            description='A simple test',
            test_type=TestType.UNIT,
            target_subsystem='test',
            test_script='#!/bin/bash\necho "Test passed"\nexit 0',
            execution_time_estimate=10
        )
        
        # Execute test
        result = runner.execute_test(test, environment, timeout=5)
        print(f"✓ Test executed: {result.test_id}")
        print(f"  Status: {result.status}")
        print(f"  Execution time: {result.execution_time:.2f}s")
        
        # Verify result
        assert result.test_id == test.id
        assert result.execution_time >= 0
        assert result.artifacts is not None
        print("✓ Result structure verified")
        
        # Cleanup
        env_manager.cleanup_environment(environment)
        print("✓ Environment cleaned up")
    
    print("\n✅ Basic execution test PASSED\n")

def test_aggregation():
    """Test result aggregation."""
    print("Testing result aggregation...")
    
    from ai_generator.models import TestResult, TestStatus, ArtifactBundle
    
    runner = TestRunner()
    
    # Create some test results
    results = []
    for i in range(5):
        config = HardwareConfig(
            architecture='x86_64' if i < 3 else 'arm64',
            cpu_model=f'cpu_{i}',
            memory_mb=1024,
            is_virtual=True,
            emulator='qemu'
        )
        
        env = Environment(
            id=f'env_{i}',
            config=config,
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        result = TestResult(
            test_id=f'test_{i}',
            status=TestStatus.PASSED if i < 3 else TestStatus.FAILED,
            execution_time=float(i + 1),
            environment=env,
            artifacts=ArtifactBundle(),
            timestamp=datetime.now()
        )
        results.append(result)
    
    # Aggregate results
    aggregated = runner.aggregate_results(results)
    
    print(f"✓ Total tests: {aggregated['total']}")
    print(f"  Passed: {aggregated['passed']}")
    print(f"  Failed: {aggregated['failed']}")
    print(f"  Pass rate: {aggregated['pass_rate']:.2%}")
    
    # Verify aggregation
    assert aggregated['total'] == 5
    assert aggregated['passed'] == 3
    assert aggregated['failed'] == 2
    assert abs(aggregated['pass_rate'] - 0.6) < 0.01
    print("✓ Aggregation verified")
    
    # Test grouping by architecture
    aggregated_by_arch = runner.aggregate_results(results, group_by='architecture')
    print(f"✓ Groups: {list(aggregated_by_arch['groups'].keys())}")
    
    assert 'x86_64' in aggregated_by_arch['groups']
    assert 'arm64' in aggregated_by_arch['groups']
    assert aggregated_by_arch['groups']['x86_64']['total'] == 3
    assert aggregated_by_arch['groups']['arm64']['total'] == 2
    print("✓ Grouping by architecture verified")
    
    print("\n✅ Aggregation test PASSED\n")

def test_diagnostic_capture():
    """Test diagnostic capture on failure."""
    print("Testing diagnostic capture...")
    
    from ai_generator.models import TestStatus
    
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        env_manager = EnvironmentManager(work_dir=work_dir)
        runner = TestRunner(environment_manager=env_manager)
        
        config = HardwareConfig(
            architecture='x86_64',
            cpu_model='test_cpu',
            memory_mb=1024,
            is_virtual=True,
            emulator='qemu'
        )
        
        environment = env_manager.provision_environment(config)
        
        # Create a failing test
        test = TestCase(
            id='test_fail',
            name='failing_test',
            description='A failing test',
            test_type=TestType.UNIT,
            target_subsystem='test',
            test_script='#!/bin/bash\necho "Error message" >&2\nexit 1',
            execution_time_estimate=10
        )
        
        result = runner.execute_test(test, environment, timeout=5)
        
        print(f"✓ Test executed: {result.test_id}")
        print(f"  Status: {result.status}")
        
        # Verify diagnostic capture
        assert result.artifacts is not None
        print("✓ Artifacts captured")
        
        if result.status == TestStatus.FAILED:
            assert result.failure_info is not None
            assert result.failure_info.error_message
            print(f"✓ Failure info captured: {result.failure_info.error_message}")
        
        env_manager.cleanup_environment(environment)
    
    print("\n✅ Diagnostic capture test PASSED\n")

if __name__ == '__main__':
    try:
        test_basic_execution()
        test_aggregation()
        test_diagnostic_capture()
        
        print("=" * 70)
        print("✅ ALL MANUAL TESTS PASSED!")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
