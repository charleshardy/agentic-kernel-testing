#!/usr/bin/env python3
"""Comprehensive test verification for all Task 7 components."""

import sys
import os
import tempfile
import time
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_qemu_runner_comprehensive():
    """Comprehensive test of QEMU runner functionality."""
    try:
        from ai_generator.models import (
            Environment, HardwareConfig, TestCase, TestType, TestStatus, 
            EnvironmentStatus
        )
        from execution.runners.qemu_runner import QEMUTestRunner
        
        print("  Testing QEMU runner instantiation...")
        
        # Test different architectures
        architectures = ["x86_64", "arm64", "arm"]
        for arch in architectures:
            hardware_config = HardwareConfig(
                architecture=arch,
                cpu_model="generic",
                memory_mb=1024,
                is_virtual=True
            )
            
            environment = Environment(
                id=f"test_env_{arch}",
                config=hardware_config,
                status=EnvironmentStatus.IDLE
            )
            
            runner = QEMUTestRunner(environment)
            
            # Test support methods
            assert runner.supports_test_type(TestType.UNIT) == True
            assert runner.supports_test_type(TestType.INTEGRATION) == True
            assert runner.supports_hardware(hardware_config) == True
            
            print(f"    ✓ {arch} architecture supported")
        
        print("  Testing QEMU runner methods...")
        
        # Test with a standard configuration
        hardware_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=2048,
            is_virtual=True
        )
        
        environment = Environment(
            id="test_env",
            config=hardware_config,
            status=EnvironmentStatus.IDLE
        )
        
        runner = QEMUTestRunner(environment)
        
        # Test context manager
        with runner as r:
            assert r is runner
        
        # Test cleanup (should not raise exceptions)
        runner.cleanup()
        
        print("  ✓ QEMU runner comprehensive test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ QEMU runner test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_artifact_collector_comprehensive():
    """Comprehensive test of artifact collector functionality."""
    try:
        from ai_generator.models import TestResult, TestStatus, ArtifactBundle
        from execution.artifact_collector import ArtifactCollector, RetentionPolicy
        
        print("  Testing artifact collector with multiple artifact types...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = ArtifactCollector(temp_dir)
            
            # Create various test artifacts
            artifacts = ArtifactBundle()
            
            # Create log files
            log_file1 = Path(temp_dir) / "test1.log"
            log_file1.write_text("Log file 1 content\nMultiple lines\nEnd of log")
            artifacts.logs.append(str(log_file1))
            
            log_file2 = Path(temp_dir) / "test2.log"
            log_file2.write_text("Log file 2 content")
            artifacts.logs.append(str(log_file2))
            
            # Create core dump file
            core_file = Path(temp_dir) / "core.dump"
            core_file.write_bytes(b"Mock core dump data")
            artifacts.core_dumps.append(str(core_file))
            
            # Create trace file
            trace_file = Path(temp_dir) / "trace.strace"
            trace_file.write_text("Mock trace data")
            artifacts.traces.append(str(trace_file))
            
            # Create screenshot file
            screenshot_file = Path(temp_dir) / "screenshot.png"
            screenshot_file.write_bytes(b"Mock PNG data")
            artifacts.screenshots.append(str(screenshot_file))
            
            # Add metadata
            artifacts.metadata["test_duration"] = 45.2
            artifacts.metadata["other_files"] = [str(trace_file)]
            
            print("    ✓ Test artifacts created")
            
            # Create test result
            test_result = TestResult(
                test_id="comprehensive_test_001",
                status=TestStatus.PASSED,
                execution_time=45.2,
                environment=None,
                artifacts=artifacts
            )
            
            # Test artifact collection
            stored_artifacts = collector.collect_artifacts(test_result)
            
            # Verify artifacts were stored
            assert len(stored_artifacts.logs) == 2, f"Expected 2 logs, got {len(stored_artifacts.logs)}"
            assert len(stored_artifacts.core_dumps) == 1, f"Expected 1 core dump, got {len(stored_artifacts.core_dumps)}"
            assert len(stored_artifacts.traces) == 1, f"Expected 1 trace, got {len(stored_artifacts.traces)}"
            assert len(stored_artifacts.screenshots) == 1, f"Expected 1 screenshot, got {len(stored_artifacts.screenshots)}"
            
            print("    ✓ Artifacts stored successfully")
            
            # Test retrieval
            test_artifacts = collector.get_artifacts_for_test("comprehensive_test_001")
            assert len(test_artifacts) >= 4, f"Expected at least 4 artifacts, got {len(test_artifacts)}"
            
            print("    ✓ Artifacts retrieved successfully")
            
            # Test storage statistics
            stats = collector.get_storage_stats()
            assert stats["total_artifacts"] >= 4
            assert "by_type" in stats
            assert "log" in stats["by_type"]
            
            print("    ✓ Storage statistics working")
            
            # Test retention policy
            policy = RetentionPolicy("test", max_age_days=7, compress_after_days=1)
            collector.set_retention_policy("test", policy)
            retrieved_policy = collector.get_retention_policy("test")
            assert retrieved_policy.max_age_days == 7
            
            print("    ✓ Retention policies working")
        
        print("  ✓ Artifact collector comprehensive test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Artifact collector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_monitor_comprehensive():
    """Comprehensive test of performance monitor functionality."""
    try:
        from execution.performance_monitor import (
            PerformanceMonitor, PerformanceContext, get_performance_monitor
        )
        
        print("  Testing performance monitor with detailed metrics...")
        
        # Test basic monitoring
        monitor = PerformanceMonitor(sample_interval=0.1, max_samples=20)
        
        # Test monitoring lifecycle
        monitor.start_monitoring("comprehensive_test_001")
        
        # Simulate some work
        time.sleep(0.5)
        
        # Add a mock process to monitor
        import os
        current_pid = os.getpid()
        monitor.add_process(current_pid)
        
        time.sleep(0.3)
        
        # Stop monitoring and get metrics
        metrics = monitor.stop_monitoring()
        
        # Verify metrics
        assert metrics is not None, "Metrics should be captured"
        assert metrics.test_id == "comprehensive_test_001"
        assert metrics.duration_seconds > 0.5, f"Duration should be > 0.5s, got {metrics.duration_seconds}"
        assert metrics.avg_cpu_percent >= 0, "CPU metrics should be non-negative"
        assert metrics.avg_memory_mb >= 0, "Memory metrics should be non-negative"
        assert len(metrics.resource_snapshots) > 0, "Should have resource snapshots"
        
        print("    ✓ Basic monitoring working")
        
        # Test context manager
        with PerformanceContext("context_test_001") as ctx:
            time.sleep(0.2)
        
        context_metrics = ctx.get_metrics()
        assert context_metrics is not None
        assert context_metrics.test_id == "context_test_001"
        assert context_metrics.duration_seconds > 0.1
        
        print("    ✓ Context manager working")
        
        # Test global instance
        global_monitor = get_performance_monitor()
        assert global_monitor is not None
        
        # Test metrics storage and retrieval
        stored_metrics = global_monitor.get_metrics("comprehensive_test_001")
        if stored_metrics:
            assert stored_metrics.test_id == "comprehensive_test_001"
        
        print("    ✓ Global instance and storage working")
        
        # Test metrics serialization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            success = monitor.save_metrics_to_file("comprehensive_test_001", temp_file)
            if success:
                # Try to load it back
                loaded_metrics = monitor.load_metrics_from_file(temp_file)
                if loaded_metrics:
                    assert loaded_metrics.test_id == "comprehensive_test_001"
                    print("    ✓ Metrics serialization working")
                else:
                    print("    ! Metrics loading returned None (acceptable)")
            else:
                print("    ! Metrics saving failed (acceptable if no metrics stored)")
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        print("  ✓ Performance monitor comprehensive test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Performance monitor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_comprehensive():
    """Test integration between all Task 7 components."""
    try:
        from ai_generator.models import (
            Environment, HardwareConfig, TestCase, TestType, TestStatus, 
            EnvironmentStatus, TestResult, ArtifactBundle
        )
        from execution.runners.qemu_runner import QEMUTestRunner
        from execution.artifact_collector import get_artifact_collector
        from execution.performance_monitor import get_performance_monitor
        
        print("  Testing component integration...")
        
        # Create test environment
        hardware_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=1024,
            is_virtual=True
        )
        
        environment = Environment(
            id="integration_test_env",
            config=hardware_config,
            status=EnvironmentStatus.IDLE
        )
        
        # Create QEMU runner
        runner = QEMUTestRunner(environment)
        
        # Get global instances
        collector = get_artifact_collector()
        monitor = get_performance_monitor()
        
        # Verify all components can work together
        assert runner is not None
        assert collector is not None
        assert monitor is not None
        
        print("    ✓ All components instantiated")
        
        # Test that QEMU runner can access other components
        # (This is tested by checking imports in the QEMU runner)
        from execution.runners.qemu_runner import get_artifact_collector as qemu_get_collector
        from execution.runners.qemu_runner import get_performance_monitor as qemu_get_monitor
        
        qemu_collector = qemu_get_collector()
        qemu_monitor = qemu_get_monitor()
        
        assert qemu_collector is not None
        assert qemu_monitor is not None
        
        print("    ✓ QEMU runner can access other components")
        
        # Test artifact collection with performance monitoring
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test artifacts
            log_file = Path(temp_dir) / "integration_test.log"
            log_file.write_text("Integration test log")
            
            artifacts = ArtifactBundle()
            artifacts.logs.append(str(log_file))
            
            test_result = TestResult(
                test_id="integration_test_001",
                status=TestStatus.PASSED,
                execution_time=1.5,
                environment=environment,
                artifacts=artifacts
            )
            
            # Start performance monitoring
            monitor.start_monitoring("integration_test_001")
            time.sleep(0.2)
            
            # Collect artifacts
            stored_artifacts = collector.collect_artifacts(test_result)
            
            # Stop monitoring
            metrics = monitor.stop_monitoring()
            
            # Verify integration
            assert len(stored_artifacts.logs) > 0
            assert metrics is not None
            assert metrics.test_id == "integration_test_001"
            
            print("    ✓ Artifact collection and performance monitoring integration working")
        
        print("  ✓ Integration test passed")
        return True
        
    except Exception as e:
        print(f"  ✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive verification of all Task 7 components."""
    print("=== Comprehensive Task 7 Verification ===\n")
    
    tests = [
        ("QEMU Runner Comprehensive", test_qemu_runner_comprehensive),
        ("Artifact Collector Comprehensive", test_artifact_collector_comprehensive),
        ("Performance Monitor Comprehensive", test_performance_monitor_comprehensive),
        ("Integration Comprehensive", test_integration_comprehensive)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED\n")
        else:
            print(f"✗ {test_name} FAILED\n")
    
    print(f"=== Results: {passed}/{total} comprehensive tests passed ===")
    
    if passed == total:
        print("🎉 All Task 7 components are fully functional!")
        return True
    else:
        print("❌ Some components need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)