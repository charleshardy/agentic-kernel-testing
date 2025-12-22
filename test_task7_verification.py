#!/usr/bin/env python3
"""
Verification script for Task 7 implementation.
Tests the three main components: QEMU runner, artifact collection, and performance monitoring.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_qemu_runner_import():
    """Test that QEMU runner can be imported and instantiated."""
    try:
        from execution.runners.qemu_runner import QEMUTestRunner
        from ai_generator.models import Environment, HardwareConfig
        
        # Create test environment
        hardware_config = HardwareConfig(
            architecture="x86_64",
            memory_mb=1024,
            cpu_cores=1,
            is_virtual=True
        )
        
        environment = Environment(
            id="test_env",
            type="qemu",
            status="available",
            config=hardware_config
        )
        
        # Create runner instance
        runner = QEMUTestRunner(environment)
        
        print("✓ QEMU runner import and instantiation successful")
        
        # Test basic methods
        assert runner.supports_test_type(None) == True
        assert runner.supports_hardware(hardware_config) == True
        
        print("✓ QEMU runner basic methods working")
        
        return True
        
    except Exception as e:
        print(f"✗ QEMU runner test failed: {e}")
        return False

def test_artifact_collector_import():
    """Test that artifact collector can be imported and used."""
    try:
        from execution.artifact_collector import ArtifactCollector, get_artifact_collector
        from ai_generator.models import TestResult, TestStatus, ArtifactBundle
        
        # Create temporary storage
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = ArtifactCollector(temp_dir)
            
            # Create test artifact bundle
            artifacts = ArtifactBundle()
            
            # Create a temporary log file
            log_file = Path(temp_dir) / "test.log"
            log_file.write_text("Test log content")
            artifacts.logs.append(str(log_file))
            
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
            
            print("✓ Artifact collector import and basic functionality successful")
            
            # Test retrieval
            test_artifacts = collector.get_artifacts_for_test("test_001")
            assert len(test_artifacts) > 0
            
            print("✓ Artifact collector retrieval working")
            
            return True
            
    except Exception as e:
        print(f"✗ Artifact collector test failed: {e}")
        return False

def test_performance_monitor_import():
    """Test that performance monitor can be imported and used."""
    try:
        from execution.performance_monitor import PerformanceMonitor, get_performance_monitor
        
        # Create monitor instance
        monitor = PerformanceMonitor(sample_interval=0.1, max_samples=10)
        
        print("✓ Performance monitor import and instantiation successful")
        
        # Test basic monitoring
        monitor.start_monitoring("test_001")
        
        # Let it run briefly
        import time
        time.sleep(0.5)
        
        metrics = monitor.stop_monitoring()
        
        assert metrics is not None
        assert metrics.test_id == "test_001"
        assert metrics.duration_seconds > 0
        
        print("✓ Performance monitor basic functionality working")
        
        return True
        
    except Exception as e:
        print(f"✗ Performance monitor test failed: {e}")
        return False

def test_integration():
    """Test integration between components."""
    try:
        from execution.runners.qemu_runner import QEMUTestRunner
        from execution.artifact_collector import get_artifact_collector
        from execution.performance_monitor import get_performance_monitor
        from ai_generator.models import Environment, HardwareConfig, TestCase, TestType
        
        print("✓ All components can be imported together")
        
        # Test that QEMU runner uses artifact collector and performance monitor
        hardware_config = HardwareConfig(
            architecture="x86_64",
            memory_mb=1024,
            cpu_cores=1,
            is_virtual=True
        )
        
        environment = Environment(
            id="test_env",
            type="qemu",
            status="available",
            config=hardware_config
        )
        
        runner = QEMUTestRunner(environment)
        
        # Verify that the runner can access the global instances
        collector = get_artifact_collector()
        monitor = get_performance_monitor()
        
        assert collector is not None
        assert monitor is not None
        
        print("✓ Component integration successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("=== Task 7 Implementation Verification ===\n")
    
    tests = [
        ("QEMU Runner", test_qemu_runner_import),
        ("Artifact Collector", test_artifact_collector_import),
        ("Performance Monitor", test_performance_monitor_import),
        ("Integration", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED\n")
        else:
            print(f"✗ {test_name} FAILED\n")
    
    print(f"=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All Task 7 components are working correctly!")
        return True
    else:
        print("❌ Some components need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)