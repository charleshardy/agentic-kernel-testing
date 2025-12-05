#!/usr/bin/env python3
"""Simple test runner for fault detection tests."""

import sys
from execution.fault_detection import (
    FaultDetectionSystem,
    FaultCategory,
    KernelCrashDetector,
    HangDetector,
    MemoryLeakDetector,
    DataCorruptionDetector
)

def test_crash_detection():
    """Test crash detection."""
    print("Testing crash detection...")
    detector = KernelCrashDetector()
    
    crash_log = "Kernel panic - not syncing: Fatal exception\nSome other text"
    faults = detector.detect(crash_log)
    
    assert len(faults) > 0, "Failed to detect crash"
    assert faults[0].category == FaultCategory.KERNEL_CRASH
    print(f"✓ Detected {len(faults)} crash(es)")
    return True

def test_hang_detection():
    """Test hang detection."""
    print("Testing hang detection...")
    detector = HangDetector()
    
    hang_log = "INFO: task blocked for more than 120 seconds"
    faults = detector.detect_from_logs(hang_log)
    
    assert len(faults) > 0, "Failed to detect hang"
    assert faults[0].category == FaultCategory.HANG
    print(f"✓ Detected {len(faults)} hang(s)")
    return True

def test_memory_leak_detection():
    """Test memory leak detection."""
    print("Testing memory leak detection...")
    detector = MemoryLeakDetector()
    
    leak_log = "BUG: KASAN: use-after-free in function_name+0x123/0x456"
    faults = detector.detect(leak_log)
    
    assert len(faults) > 0, "Failed to detect memory leak"
    assert faults[0].category == FaultCategory.MEMORY_LEAK
    print(f"✓ Detected {len(faults)} memory leak(s)")
    return True

def test_corruption_detection():
    """Test corruption detection."""
    print("Testing corruption detection...")
    detector = DataCorruptionDetector()
    
    corruption_log = "CRC error: expected 0x1234, got 0x5678"
    faults = detector.detect(corruption_log)
    
    assert len(faults) > 0, "Failed to detect corruption"
    assert faults[0].category == FaultCategory.DATA_CORRUPTION
    print(f"✓ Detected {len(faults)} corruption(s)")
    return True

def test_all_fault_types():
    """Test detection of all fault types together."""
    print("Testing all fault types together...")
    system = FaultDetectionSystem()
    
    multi_log = """
    Kernel panic - not syncing: Fatal exception
    INFO: task blocked for more than 120 seconds
    BUG: KASAN: use-after-free in function_name
    CRC error: checksum mismatch detected
    """
    
    all_faults = system.detect_all_faults(multi_log)
    detected_categories = {fault.category for fault in all_faults}
    
    assert FaultCategory.KERNEL_CRASH in detected_categories, "Failed to detect crash"
    assert FaultCategory.HANG in detected_categories, "Failed to detect hang"
    assert FaultCategory.MEMORY_LEAK in detected_categories, "Failed to detect memory leak"
    assert FaultCategory.DATA_CORRUPTION in detected_categories, "Failed to detect corruption"
    
    print(f"✓ Detected all 4 fault types ({len(all_faults)} total faults)")
    return True

def test_statistics():
    """Test statistics collection."""
    print("Testing statistics...")
    system = FaultDetectionSystem()
    
    log = """
    Kernel panic - not syncing: Fatal exception
    INFO: task blocked for more than 120 seconds
    BUG: KASAN: use-after-free in function_name
    CRC error: checksum mismatch detected
    """
    
    system.detect_all_faults(log)
    stats = system.get_all_statistics()
    
    assert "crash_detection" in stats
    assert "hang_detection" in stats
    assert "memory_leak_detection" in stats
    assert "corruption_detection" in stats
    assert stats["total_faults"] == 4
    
    print(f"✓ Statistics: {stats['total_faults']} total faults")
    return True

def main():
    """Run all tests."""
    tests = [
        test_crash_detection,
        test_hang_detection,
        test_memory_leak_detection,
        test_corruption_detection,
        test_all_fault_types,
        test_statistics
    ]
    
    print("=" * 60)
    print("Running Fault Detection Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
