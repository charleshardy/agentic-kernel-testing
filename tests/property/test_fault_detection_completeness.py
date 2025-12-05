"""Property-based tests for fault detection completeness.

**Feature: agentic-kernel-testing, Property 12: Fault detection completeness**

This test validates Requirements 3.2:
WHEN fault injection is active, THE Testing System SHALL detect and report 
all kernel crashes, hangs, memory leaks, and data corruption that occur.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from execution.fault_detection import (
    FaultDetectionSystem,
    FaultCategory,
    KernelCrashDetector,
    HangDetector,
    MemoryLeakDetector,
    DataCorruptionDetector
)


# Strategies for generating log content with known faults

@st.composite
def kernel_crash_log(draw):
    """Generate log content with a kernel crash."""
    crash_patterns = [
        "Kernel panic - not syncing: Fatal exception",
        "BUG: unable to handle kernel NULL pointer dereference at 0000000000000000",
        "Oops: 0002 [#1] SMP",
        "general protection fault: 0000 [#1] PREEMPT SMP",
        "kernel NULL pointer dereference at virtual address 00000000",
        "Call Trace:\n dump_stack+0x5c/0x80\n panic+0xe7/0x220"
    ]
    
    crash_line = draw(st.sampled_from(crash_patterns))
    prefix = draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), max_size=50))
    suffix = draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), max_size=50))
    
    return f"{prefix}\n{crash_line}\n{suffix}"


@st.composite
def hang_log(draw):
    """Generate log content with a hang."""
    hang_patterns = [
        "INFO: task blocked for more than 120 seconds",
        "watchdog: BUG: soft lockup - CPU#0 stuck for 22s!",
        "NMI watchdog: BUG: soft lockup on CPU#1",
        "rcu_sched detected stalls on CPUs/tasks"
    ]
    
    hang_line = draw(st.sampled_from(hang_patterns))
    prefix = draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), max_size=50))
    suffix = draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), max_size=50))
    
    return f"{prefix}\n{hang_line}\n{suffix}"


@st.composite
def memory_leak_log(draw):
    """Generate log content with a memory leak."""
    leak_patterns = [
        "BUG: KASAN: use-after-free in function_name+0x123/0x456",
        "BUG: KASAN: slab-out-of-bounds in kmalloc",
        "BUG: KASAN: heap-out-of-bounds in memcpy",
        "BUG: KASAN: double-free detected",
        "Memory leak detected: 1024 bytes at address 0xffff888012345678"
    ]
    
    leak_line = draw(st.sampled_from(leak_patterns))
    prefix = draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), max_size=50))
    suffix = draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), max_size=50))
    
    return f"{prefix}\n{leak_line}\n{suffix}"


@st.composite
def corruption_log(draw):
    """Generate log content with data corruption."""
    corruption_patterns = [
        "EXT4-fs error: data corruption detected in inode 12345",
        "CRC error: expected 0x1234, got 0x5678",
        "filesystem corruption detected on /dev/sda1",
        "checksum mismatch in block 98765",
        "bad magic number in superblock"
    ]
    
    corruption_line = draw(st.sampled_from(corruption_patterns))
    prefix = draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), max_size=50))
    suffix = draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), max_size=50))
    
    return f"{prefix}\n{corruption_line}\n{suffix}"


@st.composite
def multi_fault_log(draw):
    """Generate log content with multiple types of faults."""
    # Generate at least one of each fault type
    crash = draw(kernel_crash_log())
    hang = draw(hang_log())
    leak = draw(memory_leak_log())
    corruption = draw(corruption_log())
    
    # Shuffle them together
    parts = [crash, hang, leak, corruption]
    draw(st.randoms()).shuffle(parts)
    
    return "\n".join(parts)


# Property 12: Fault detection completeness
# For any test execution with fault injection active, the system should detect 
# and report all kernel crashes, hangs, memory leaks, and data corruption that occur.

@given(crash_log=kernel_crash_log())
@settings(max_examples=100, deadline=None)
def test_crash_detection_completeness(crash_log):
    """Property: All kernel crashes in logs should be detected.
    
    **Validates: Requirements 3.2**
    """
    detector = KernelCrashDetector()
    
    # Detect crashes
    detected_faults = detector.detect(crash_log)
    
    # Property: At least one crash should be detected
    assert len(detected_faults) > 0, "Crash detector failed to detect kernel crash"
    
    # Property: All detected faults should be crashes
    for fault in detected_faults:
        assert fault.category == FaultCategory.KERNEL_CRASH
        assert fault.severity == "critical"
        assert fault.description
        assert "crash" in fault.description.lower()


@given(hang_log=hang_log())
@settings(max_examples=100, deadline=None)
def test_hang_detection_completeness(hang_log):
    """Property: All hangs in logs should be detected.
    
    **Validates: Requirements 3.2**
    """
    detector = HangDetector()
    
    # Detect hangs
    detected_faults = detector.detect_from_logs(hang_log)
    
    # Property: At least one hang should be detected
    assert len(detected_faults) > 0, "Hang detector failed to detect system hang"
    
    # Property: All detected faults should be hangs
    for fault in detected_faults:
        assert fault.category == FaultCategory.HANG
        assert fault.severity == "high"
        assert fault.description
        assert "hang" in fault.description.lower() or "timeout" in fault.description.lower()


@given(leak_log=memory_leak_log())
@settings(max_examples=100, deadline=None)
def test_memory_leak_detection_completeness(leak_log):
    """Property: All memory leaks in logs should be detected.
    
    **Validates: Requirements 3.2**
    """
    detector = MemoryLeakDetector()
    
    # Detect memory leaks
    detected_faults = detector.detect(leak_log)
    
    # Property: At least one memory leak should be detected
    assert len(detected_faults) > 0, "Memory leak detector failed to detect memory issue"
    
    # Property: All detected faults should be memory leaks
    for fault in detected_faults:
        assert fault.category == FaultCategory.MEMORY_LEAK
        assert fault.severity in ["medium", "high", "critical"]
        assert fault.description
        assert "memory" in fault.description.lower()


@given(corruption_log=corruption_log())
@settings(max_examples=100, deadline=None)
def test_corruption_detection_completeness(corruption_log):
    """Property: All data corruption in logs should be detected.
    
    **Validates: Requirements 3.2**
    """
    detector = DataCorruptionDetector()
    
    # Detect corruption
    detected_faults = detector.detect(corruption_log)
    
    # Property: At least one corruption should be detected
    assert len(detected_faults) > 0, "Corruption detector failed to detect data corruption"
    
    # Property: All detected faults should be corruption
    for fault in detected_faults:
        assert fault.category == FaultCategory.DATA_CORRUPTION
        assert fault.severity in ["medium", "high", "critical"]
        assert fault.description
        assert "corruption" in fault.description.lower() or "error" in fault.description.lower()


@given(multi_log=multi_fault_log())
@settings(max_examples=100, deadline=None)
def test_all_fault_types_detected(multi_log):
    """Property: System should detect all fault types when multiple faults occur.
    
    **Validates: Requirements 3.2**
    
    This is the main completeness property: when fault injection is active and 
    multiple types of faults occur, ALL of them should be detected and reported.
    """
    system = FaultDetectionSystem()
    
    # Detect all faults
    all_faults = system.detect_all_faults(multi_log)
    
    # Property: All four fault types should be detected
    detected_categories = {fault.category for fault in all_faults}
    
    # We expect at least one of each type since we injected all types
    assert FaultCategory.KERNEL_CRASH in detected_categories, \
        "Failed to detect kernel crash when present"
    assert FaultCategory.HANG in detected_categories, \
        "Failed to detect hang when present"
    assert FaultCategory.MEMORY_LEAK in detected_categories, \
        "Failed to detect memory leak when present"
    assert FaultCategory.DATA_CORRUPTION in detected_categories, \
        "Failed to detect data corruption when present"
    
    # Property: Each fault should have proper metadata
    for fault in all_faults:
        assert fault.timestamp is not None
        assert fault.description
        assert fault.severity in ["low", "medium", "high", "critical"]
        assert fault.details
        assert isinstance(fault.details, dict)


@given(
    crash_count=st.integers(min_value=1, max_value=5),
    hang_count=st.integers(min_value=1, max_value=5),
    leak_count=st.integers(min_value=1, max_value=5),
    corruption_count=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=50, deadline=None)
def test_detection_count_accuracy(crash_count, hang_count, leak_count, corruption_count):
    """Property: Number of detected faults should match number of injected faults.
    
    **Validates: Requirements 3.2**
    """
    # Generate log with specific number of each fault type
    log_parts = []
    
    # Add crashes
    for _ in range(crash_count):
        log_parts.append("Kernel panic - not syncing: Fatal exception")
    
    # Add hangs
    for _ in range(hang_count):
        log_parts.append("INFO: task blocked for more than 120 seconds")
    
    # Add memory leaks
    for _ in range(leak_count):
        log_parts.append("BUG: KASAN: use-after-free in function_name")
    
    # Add corruptions
    for _ in range(corruption_count):
        log_parts.append("CRC error: checksum mismatch detected")
    
    log_content = "\n".join(log_parts)
    
    system = FaultDetectionSystem()
    all_faults = system.detect_all_faults(log_content)
    
    # Count detected faults by category
    detected_crashes = len([f for f in all_faults if f.category == FaultCategory.KERNEL_CRASH])
    detected_hangs = len([f for f in all_faults if f.category == FaultCategory.HANG])
    detected_leaks = len([f for f in all_faults if f.category == FaultCategory.MEMORY_LEAK])
    detected_corruptions = len([f for f in all_faults if f.category == FaultCategory.DATA_CORRUPTION])
    
    # Property: Detection count should match injection count
    assert detected_crashes == crash_count, \
        f"Expected {crash_count} crashes, detected {detected_crashes}"
    assert detected_hangs == hang_count, \
        f"Expected {hang_count} hangs, detected {detected_hangs}"
    assert detected_leaks == leak_count, \
        f"Expected {leak_count} leaks, detected {detected_leaks}"
    assert detected_corruptions == corruption_count, \
        f"Expected {corruption_count} corruptions, detected {detected_corruptions}"


@given(log_content=st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=10, max_size=1000))
@settings(max_examples=100, deadline=None)
def test_no_false_positives_on_clean_logs(log_content):
    """Property: Clean logs without faults should not trigger false detections.
    
    **Validates: Requirements 3.2**
    """
    # Ensure log doesn't contain fault patterns
    fault_keywords = [
        "panic", "oops", "bug:", "crash", "blocked for more than",
        "kasan", "use-after-free", "corruption", "crc error"
    ]
    
    # Skip if log contains fault keywords
    assume(not any(keyword in log_content.lower() for keyword in fault_keywords))
    
    system = FaultDetectionSystem()
    detected_faults = system.detect_all_faults(log_content)
    
    # Property: No faults should be detected in clean logs
    assert len(detected_faults) == 0, \
        f"False positive: detected {len(detected_faults)} faults in clean log"


def test_hang_timeout_monitoring():
    """Property: Hang detector should detect timeouts for monitored operations.
    
    **Validates: Requirements 3.2**
    """
    detector = HangDetector(default_timeout=1)  # 1 second timeout
    
    # Start monitoring an operation
    detector.start_monitoring("test_op", timeout=1)
    
    # Wait for timeout
    import time
    time.sleep(1.5)
    
    # Check for timeout
    fault = detector.check_timeout("test_op", timeout=1)
    
    # Property: Timeout should be detected
    assert fault is not None, "Hang detector failed to detect timeout"
    assert fault.category == FaultCategory.HANG
    assert fault.details["operation_id"] == "test_op"
    assert fault.details["elapsed_seconds"] > 1.0


def test_statistics_completeness():
    """Property: Statistics should accurately reflect all detected faults.
    
    **Validates: Requirements 3.2**
    """
    system = FaultDetectionSystem()
    
    # Inject known faults
    log = """
    Kernel panic - not syncing: Fatal exception
    INFO: task blocked for more than 120 seconds
    BUG: KASAN: use-after-free in function_name
    CRC error: checksum mismatch detected
    """
    
    system.detect_all_faults(log)
    
    # Get statistics
    stats = system.get_all_statistics()
    
    # Property: Statistics should be complete
    assert "crash_detection" in stats
    assert "hang_detection" in stats
    assert "memory_leak_detection" in stats
    assert "corruption_detection" in stats
    assert "total_faults" in stats
    
    # Property: Total should match sum of individual counts
    total = (
        stats["crash_detection"]["total_crashes"] +
        stats["hang_detection"]["total_hangs"] +
        stats["memory_leak_detection"]["total_leaks"] +
        stats["corruption_detection"]["total_corruptions"]
    )
    assert stats["total_faults"] == total
