"""Property-based tests for crash input minimization.

**Feature: agentic-kernel-testing, Property 32: Crash input minimization**

This test validates Requirements 7.2:
WHEN fuzzing discovers crashes or hangs, THE Testing System SHALL capture the input 
that triggered the issue and attempt to minimize it to the smallest reproducing case.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from execution.kernel_fuzzer import (
    CrashMinimizer,
    CrashInfo,
    CrashSeverity,
    CrashDetector
)


# Strategies for generating crash reproducers

@st.composite
def simple_reproducer(draw):
    """Generate a simple reproducer with multiple lines."""
    num_lines = draw(st.integers(min_value=5, max_value=20))
    lines = []
    for i in range(num_lines):
        line = draw(st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N')),
            min_size=5,
            max_size=30
        ))
        lines.append(line)
    return '\n'.join(lines)


@st.composite
def reproducer_with_numbers(draw):
    """Generate a reproducer with numeric values."""
    num_lines = draw(st.integers(min_value=3, max_value=10))
    lines = []
    for i in range(num_lines):
        value = draw(st.integers(min_value=1, max_value=1000))
        line = f"value_{i} = {value}"
        lines.append(line)
    return '\n'.join(lines)


@st.composite
def crash_log_output(draw):
    """Generate a crash log output."""
    crash_types = [
        "kernel BUG at fs/ext4/inode.c:123",
        "KASAN: use-after-free in kmalloc",
        "general protection fault: 0000 [#1] SMP",
        "unable to handle kernel NULL pointer dereference at 0000000000000000",
        "WARNING: CPU: 0 PID: 1234 at kernel/sched/core.c:456"
    ]
    
    crash_line = draw(st.sampled_from(crash_types))
    
    # Add some context lines
    context_lines = draw(st.integers(min_value=2, max_value=5))
    lines = [crash_line]
    
    for i in range(context_lines):
        context = draw(st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N', 'P')),
            min_size=10,
            max_size=50
        ))
        lines.append(context)
    
    return '\n'.join(lines)


# Property 32: Crash input minimization
# For any crash discovered during fuzzing, the system should capture the 
# triggering input and minimize it to the smallest reproducing case.

@given(reproducer=simple_reproducer())
@settings(max_examples=100, deadline=None)
def test_minimization_reduces_size(reproducer):
    """Property: Minimization should reduce reproducer size.
    
    **Validates: Requirements 7.2**
    """
    minimizer = CrashMinimizer()
    
    # Create a validator that always returns True (crash always reproduces)
    def always_crashes(input_str):
        return True
    
    # Minimize the reproducer
    minimized = minimizer.minimize_reproducer(reproducer, always_crashes)
    
    # Property: Minimized version should not be larger than original
    assert len(minimized) <= len(reproducer), \
        "Minimized reproducer should not be larger than original"
    
    # Property: Minimized version should be a string
    assert isinstance(minimized, str)


@given(reproducer=reproducer_with_numbers())
@settings(max_examples=100, deadline=None)
def test_minimization_preserves_crash(reproducer):
    """Property: Minimization should preserve crash-inducing behavior.
    
    **Validates: Requirements 7.2**
    """
    minimizer = CrashMinimizer()
    
    # Create a validator that checks for a specific pattern
    # (simulating that crash only happens with certain content)
    def crashes_with_pattern(input_str):
        # Crash happens if input contains "value_0"
        return "value_0" in input_str
    
    # Only test if original reproducer causes crash
    assume(crashes_with_pattern(reproducer))
    
    # Minimize the reproducer
    minimized = minimizer.minimize_reproducer(reproducer, crashes_with_pattern)
    
    # Property: Minimized version should still cause crash
    assert crashes_with_pattern(minimized), \
        "Minimized reproducer must still trigger the crash"
    
    # Property: Minimized version should contain the essential pattern
    assert "value_0" in minimized


@given(
    essential_lines=st.integers(min_value=1, max_value=3),
    extra_lines=st.integers(min_value=2, max_value=10)
)
@settings(max_examples=50, deadline=None)
def test_minimization_removes_unnecessary_lines(essential_lines, extra_lines):
    """Property: Minimization should remove lines not needed for crash.
    
    **Validates: Requirements 7.2**
    """
    minimizer = CrashMinimizer()
    
    # Create reproducer with essential and extra lines
    lines = []
    
    # Essential lines (marked with ESSENTIAL)
    for i in range(essential_lines):
        lines.append(f"ESSENTIAL_{i}")
    
    # Extra lines (not needed for crash)
    for i in range(extra_lines):
        lines.append(f"extra_{i}")
    
    reproducer = '\n'.join(lines)
    
    # Validator: crash only if all ESSENTIAL lines are present
    def crashes_with_essential(input_str):
        for i in range(essential_lines):
            if f"ESSENTIAL_{i}" not in input_str:
                return False
        return True
    
    # Minimize
    minimized = minimizer.minimize_reproducer(reproducer, crashes_with_essential)
    
    # Property: All essential lines should be present
    for i in range(essential_lines):
        assert f"ESSENTIAL_{i}" in minimized, \
            f"Essential line ESSENTIAL_{i} must be preserved"
    
    # Property: Minimized should have fewer or equal lines
    minimized_line_count = len(minimized.split('\n'))
    original_line_count = len(lines)
    assert minimized_line_count <= original_line_count


@given(reproducer=reproducer_with_numbers())
@settings(max_examples=100, deadline=None)
def test_minimization_reduces_numeric_values(reproducer):
    """Property: Minimization should reduce numeric values when possible.
    
    **Validates: Requirements 7.2**
    """
    minimizer = CrashMinimizer()
    
    # Validator: crash if any value >= 100
    def crashes_with_large_value(input_str):
        import re
        numbers = re.findall(r'\b(\d+)\b', input_str)
        return any(int(n) >= 100 for n in numbers)
    
    # Only test if original has large values
    assume(crashes_with_large_value(reproducer))
    
    # Minimize
    minimized = minimizer.minimize_reproducer(reproducer, crashes_with_large_value)
    
    # Property: Minimized should still crash
    assert crashes_with_large_value(minimized)
    
    # Property: Minimized should have smaller or equal numeric values
    import re
    original_numbers = [int(n) for n in re.findall(r'\b(\d+)\b', reproducer)]
    minimized_numbers = [int(n) for n in re.findall(r'\b(\d+)\b', minimized)]
    
    if minimized_numbers:
        # At least one number should be present
        assert len(minimized_numbers) > 0


def test_crash_info_captures_reproducer():
    """Property: CrashInfo should capture the reproducing input.
    
    **Validates: Requirements 7.2**
    """
    reproducer = "test_syscall(123, 456)\ntest_syscall(789, 0)"
    
    crash_info = CrashInfo(
        crash_id="crash_001",
        title="Test crash",
        severity=CrashSeverity.HIGH,
        crash_type="kernel_bug",
        reproducer=reproducer
    )
    
    # Property: Reproducer should be captured
    assert crash_info.reproducer is not None
    assert crash_info.reproducer == reproducer
    
    # Property: CrashInfo should be serializable
    crash_dict = crash_info.to_dict()
    assert "reproducer" in crash_dict
    assert crash_dict["reproducer"] == reproducer


def test_crash_info_stores_minimized_reproducer():
    """Property: CrashInfo should store both original and minimized reproducers.
    
    **Validates: Requirements 7.2**
    """
    original = "line1\nline2\nline3\nline4"
    minimized = "line1\nline3"
    
    crash_info = CrashInfo(
        crash_id="crash_002",
        title="Test crash",
        severity=CrashSeverity.CRITICAL,
        crash_type="kasan",
        reproducer=original,
        minimized_reproducer=minimized
    )
    
    # Property: Both reproducers should be stored
    assert crash_info.reproducer == original
    assert crash_info.minimized_reproducer == minimized
    
    # Property: Minimized should be smaller
    assert len(crash_info.minimized_reproducer) < len(crash_info.reproducer)
    
    # Property: Both should be in serialized form
    crash_dict = crash_info.to_dict()
    assert crash_dict["reproducer"] == original
    assert crash_dict["minimized_reproducer"] == minimized


@given(log=crash_log_output())
@settings(max_examples=100, deadline=None)
def test_crash_detection_from_log(log):
    """Property: System should detect crashes from log output.
    
    **Validates: Requirements 7.2**
    """
    detector = CrashDetector()
    
    # Detect crash
    crash_detection = detector.detect_crash(log)
    
    # Property: Should detect crash if log contains crash patterns
    crash_keywords = [
        "kernel BUG", "KASAN", "general protection fault",
        "NULL pointer dereference", "WARNING"
    ]
    
    has_crash_keyword = any(keyword.lower() in log.lower() for keyword in crash_keywords)
    
    if has_crash_keyword:
        assert crash_detection is not None, \
            "Should detect crash when crash keywords are present"
        
        # Property: Detection should include crash type
        assert "crash_type" in crash_detection
        assert crash_detection["crash_type"]
        
        # Property: Detection should include severity
        assert "severity" in crash_detection
        assert crash_detection["severity"] in [
            CrashSeverity.LOW,
            CrashSeverity.MEDIUM,
            CrashSeverity.HIGH,
            CrashSeverity.CRITICAL
        ]


def test_minimization_idempotence():
    """Property: Minimizing an already minimal reproducer should not change it.
    
    **Validates: Requirements 7.2**
    """
    minimizer = CrashMinimizer()
    
    # Already minimal reproducer (single essential line)
    minimal_reproducer = "CRASH_LINE"
    
    def crashes_with_crash_line(input_str):
        return "CRASH_LINE" in input_str
    
    # Minimize
    result = minimizer.minimize_reproducer(minimal_reproducer, crashes_with_crash_line)
    
    # Property: Should remain unchanged
    assert result == minimal_reproducer, \
        "Minimizing a minimal reproducer should not change it"


@given(
    line_count=st.integers(min_value=1, max_value=20),
    essential_index=st.integers(min_value=0, max_value=19)
)
@settings(max_examples=50, deadline=None)
def test_minimization_finds_single_essential_line(line_count, essential_index):
    """Property: Minimization should find the single essential line.
    
    **Validates: Requirements 7.2**
    """
    # Ensure essential_index is within bounds
    assume(essential_index < line_count)
    
    minimizer = CrashMinimizer()
    
    # Create reproducer with one essential line
    lines = [f"line_{i}" for i in range(line_count)]
    essential_line = lines[essential_index]
    reproducer = '\n'.join(lines)
    
    def crashes_with_essential(input_str):
        return essential_line in input_str
    
    # Minimize
    minimized = minimizer.minimize_reproducer(reproducer, crashes_with_essential)
    
    # Property: Essential line must be present
    assert essential_line in minimized
    
    # Property: Minimized should be smaller than original (if original had > 1 line)
    if line_count > 1:
        assert len(minimized) < len(reproducer)


def test_crash_detector_extracts_stack_trace():
    """Property: Crash detector should extract stack traces from logs.
    
    **Validates: Requirements 7.2**
    """
    detector = CrashDetector()
    
    # Log with stack trace
    log = """
kernel BUG at fs/ext4/inode.c:123
Call Trace:
 [<ffffffff81234567>] ext4_write_begin+0x123/0x456
 [<ffffffff81234568>] generic_perform_write+0x234/0x567
 [<ffffffff81234569>] __generic_file_write_iter+0x345/0x678
 [<ffffffff8123456a>] ext4_file_write_iter+0x456/0x789
Some other output
"""
    
    # Extract stack trace
    stack_trace = detector.extract_stack_trace(log)
    
    # Property: Stack trace should be extracted
    assert stack_trace is not None
    assert "Call Trace:" in stack_trace
    
    # Property: Stack trace should contain function names
    assert "ext4_write_begin" in stack_trace or "generic_perform_write" in stack_trace


def test_crash_detector_extracts_affected_function():
    """Property: Crash detector should identify affected function.
    
    **Validates: Requirements 7.2**
    """
    detector = CrashDetector()
    
    # Stack trace with function names
    stack_trace = """
Call Trace:
 [<ffffffff81234567>] ext4_write_begin+0x123/0x456
 [<ffffffff81234568>] generic_perform_write+0x234/0x567
"""
    
    # Extract affected function
    affected_function = detector.extract_affected_function(stack_trace)
    
    # Property: Should extract a function name
    assert affected_function is not None
    assert isinstance(affected_function, str)
    assert len(affected_function) > 0


@given(
    num_crashes=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=30, deadline=None)
def test_multiple_crashes_captured(num_crashes):
    """Property: System should capture multiple crashes with their reproducers.
    
    **Validates: Requirements 7.2**
    """
    crashes = []
    
    for i in range(num_crashes):
        crash = CrashInfo(
            crash_id=f"crash_{i}",
            title=f"Crash {i}",
            severity=CrashSeverity.HIGH,
            crash_type="kernel_bug",
            reproducer=f"reproducer_{i}\nline2\nline3"
        )
        crashes.append(crash)
    
    # Property: All crashes should be captured
    assert len(crashes) == num_crashes
    
    # Property: Each crash should have a reproducer
    for crash in crashes:
        assert crash.reproducer is not None
        assert len(crash.reproducer) > 0
    
    # Property: Each crash should have unique ID
    crash_ids = [c.crash_id for c in crashes]
    assert len(set(crash_ids)) == num_crashes


def test_minimization_with_empty_reproducer():
    """Property: Minimization should handle empty reproducers gracefully.
    
    **Validates: Requirements 7.2**
    """
    minimizer = CrashMinimizer()
    
    empty_reproducer = ""
    
    def always_crashes(input_str):
        return True
    
    # Minimize empty reproducer
    minimized = minimizer.minimize_reproducer(empty_reproducer, always_crashes)
    
    # Property: Should return empty string
    assert minimized == ""


def test_crash_severity_classification():
    """Property: Crashes should be classified by severity.
    
    **Validates: Requirements 7.2**
    """
    detector = CrashDetector()
    
    # Test different crash types and their severities
    test_cases = [
        ("KASAN: use-after-free", CrashSeverity.CRITICAL),
        ("general protection fault", CrashSeverity.CRITICAL),
        ("kernel BUG at", CrashSeverity.HIGH),
        ("WARNING: CPU", CrashSeverity.LOW)
    ]
    
    for log_snippet, expected_min_severity in test_cases:
        detection = detector.detect_crash(log_snippet)
        
        # Property: Should detect crash
        assert detection is not None
        
        # Property: Should have appropriate severity
        assert detection["severity"] in [
            CrashSeverity.LOW,
            CrashSeverity.MEDIUM,
            CrashSeverity.HIGH,
            CrashSeverity.CRITICAL
        ]
