#!/usr/bin/env python3
"""Verification script for Task 7 implementation."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_imports():
    """Verify all new modules can be imported."""
    print("Verifying Task 7 Implementation...")
    print("=" * 60)
    
    results = []
    
    # Test QEMU Runner
    try:
        from execution.runners.qemu_runner import QEMUTestRunner
        print("✓ QEMU Test Runner: Available")
        results.append(True)
    except Exception as e:
        print(f"✗ QEMU Test Runner: Failed - {e}")
        results.append(False)
    
    # Test Artifact Collector
    try:
        from execution.artifact_collector import ArtifactCollector, get_artifact_collector
        print("✓ Artifact Collector: Available")
        results.append(True)
    except Exception as e:
        print(f"✗ Artifact Collector: Failed - {e}")
        results.append(False)
    
    # Test Performance Monitor
    try:
        from execution.performance_monitor import PerformanceMonitor, get_performance_monitor
        print("✓ Performance Monitor: Available")
        results.append(True)
    except Exception as e:
        print(f"✗ Performance Monitor: Failed - {e}")
        results.append(False)
    
    # Test Performance API
    try:
        from api.routers.performance import router
        print("✓ Performance API: Available")
        results.append(True)
    except Exception as e:
        print(f"✗ Performance API: Failed - {e}")
        results.append(False)
    
    print("=" * 60)
    
    if all(results):
        print("\nSUCCESS: All Task 7 components implemented and importable")
        return 0
    else:
        print(f"\nFAILURE: {results.count(False)} component(s) failed")
        return 1

def verify_functionality():
    """Verify basic functionality of implemented components."""
    print("\nVerifying Basic Functionality...")
    print("=" * 60)
    
    try:
        # Test Artifact Collector
        from execution.artifact_collector import get_artifact_collector
        collector = get_artifact_collector()
        stats = collector.get_storage_stats()
        print(f"✓ Artifact Collector: {stats['total_artifacts']} artifacts tracked")
        
        # Test Performance Monitor
        from execution.performance_monitor import get_performance_monitor
        monitor = get_performance_monitor()
        all_metrics = monitor.get_all_metrics()
        print(f"✓ Performance Monitor: {len(all_metrics)} metrics stored")
        
        # Test QEMU Runner instantiation
        from execution.runners.qemu_runner import QEMUTestRunner
        from ai_generator.models import Environment, HardwareConfig
        
        env = Environment(
            id="test_env",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=2048,
                is_virtual=True
            )
        )
        runner = QEMUTestRunner(env)
        print(f"✓ QEMU Runner: Initialized with {runner.qemu_binary}")
        
        print("=" * 60)
        print("\nSUCCESS: All components functional")
        return 0
        
    except Exception as e:
        print(f"\n✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import_result = verify_imports()
    
    if import_result == 0:
        func_result = verify_functionality()
        sys.exit(func_result)
    else:
        sys.exit(import_result)
