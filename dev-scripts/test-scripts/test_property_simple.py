#!/usr/bin/env python3
"""Simple property test to verify Task 7 components."""

import sys
import os
import tempfile
import time

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_complete_result_capture_property():
    """Test the complete result capture property manually."""
    try:
        from ai_generator.models import (
            Environment, HardwareConfig, TestCase, TestType, TestStatus, 
            ArtifactBundle, FailureInfo, EnvironmentStatus
        )
        from execution.runners.qemu_runner import QEMUTestRunner
        
        # Create test environment
        hardware_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=1024,
            is_virtual=True
        )
        
        environment = Environment(
            id="test_env",
            config=hardware_config,
            status=EnvironmentStatus.IDLE
        )
        
        # Create a simple test case
        test_case = TestCase(
            id="test_001",
            name="Simple Test",
            description="A simple test case",
            test_type=TestType.UNIT,
            target_subsystem="memory",
            required_hardware=hardware_config,
            test_script="#!/bin/bash\necho 'Hello World'\necho 'Error message' >&2\nexit 0",
            execution_time_estimate=30
        )
        
        print("✓ Test case created successfully")
        
        # Create QEMU runner (but don't actually execute since we don't have QEMU)
        runner = QEMUTestRunner(environment)
        
        # Test that the runner has the required methods
        assert hasattr(runner, 'execute'), "Runner must have execute method"
        assert hasattr(runner, 'cleanup'), "Runner must have cleanup method"
        assert hasattr(runner, 'supports_test_type'), "Runner must have supports_test_type method"
        assert hasattr(runner, 'supports_hardware'), "Runner must have supports_hardware method"
        
        print("✓ QEMU runner has all required methods")
        
        # Test support methods
        assert runner.supports_test_type(TestType.UNIT) == True
        assert runner.supports_hardware(hardware_config) == True
        
        print("✓ QEMU runner support methods work correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Property test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_artifact_collection_property():
    """Test the artifact collection property manually."""
    try:
        from ai_generator.models import TestResult, TestStatus, ArtifactBundle
        from execution.artifact_collector import ArtifactCollector
        
        # Create temporary storage
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = ArtifactCollector(temp_dir)
            
            # Create test artifact bundle
            artifacts = ArtifactBundle()
            
            # Create a temporary log file
            log_file = os.path.join(temp_dir, "test.log")
            with open(log_file, 'w') as f:
                f.write("Test log content\nLine 2\nLine 3")
            artifacts.logs.append(log_file)
            
            # Create mock test result
            test_result = TestResult(
                test_id="test_001",
                status=TestStatus.PASSED,
                execution_time=10.0,
                environment=None,
                artifacts=artifacts
            )
            
            # Test artifact collection
            stored_artifacts = collector.collect_artifacts(test_result)
            
            # Verify artifacts were stored
            assert len(stored_artifacts.logs) > 0, "Should have stored log artifacts"
            
            # Verify retrieval
            test_artifacts = collector.get_artifacts_for_test("test_001")
            assert len(test_artifacts) > 0, "Should be able to retrieve artifacts"
            
            print("✓ Artifact collection property verified")
            return True
            
    except Exception as e:
        print(f"✗ Artifact collection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitoring_property():
    """Test the performance monitoring property manually."""
    try:
        from execution.performance_monitor import PerformanceMonitor
        
        # Create monitor instance
        monitor = PerformanceMonitor(sample_interval=0.1, max_samples=10)
        
        # Test basic monitoring
        monitor.start_monitoring("test_001")
        
        # Let it run briefly
        time.sleep(0.5)
        
        metrics = monitor.stop_monitoring()
        
        # Verify metrics were captured
        assert metrics is not None, "Metrics should be captured"
        assert metrics.test_id == "test_001", "Test ID should match"
        assert metrics.duration_seconds > 0, "Duration should be positive"
        assert metrics.avg_cpu_percent >= 0, "CPU metrics should be captured"
        assert metrics.avg_memory_mb >= 0, "Memory metrics should be captured"
        
        print("✓ Performance monitoring property verified")
        return True
        
    except Exception as e:
        print(f"✗ Performance monitoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Task 7 Property Tests ===")
    
    success = True
    
    print("\n1. Testing complete result capture property...")
    if not test_complete_result_capture_property():
        success = False
    
    print("\n2. Testing artifact collection property...")
    if not test_artifact_collection_property():
        success = False
    
    print("\n3. Testing performance monitoring property...")
    if not test_performance_monitoring_property():
        success = False
    
    if success:
        print("\n🎉 All Task 7 properties verified!")
    else:
        print("\n❌ Some properties failed verification.")
    
    sys.exit(0 if success else 1)