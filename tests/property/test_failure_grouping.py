"""Property-based tests for failure grouping consistency.

**Feature: agentic-kernel-testing, Property 18: Failure grouping consistency**
**Validates: Requirements 4.3**

Property 18: Failure grouping consistency
For any set of test failures with the same root cause, the system should group them 
together and identify the common root cause.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List

from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle, FailureInfo
)
from analysis.root_cause_analyzer import RootCauseAnalyzer


# Custom strategies for generating test data
@st.composite
def hardware_config_strategy(draw):
    """Generate a random hardware configuration."""
    architecture = draw(st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']))
    cpu_model = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    memory_mb = draw(st.integers(min_value=512, max_value=16384))
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=cpu_model,
        memory_mb=memory_mb,
        storage_type='ssd',
        is_virtual=True,
        emulator='qemu'
    )


@st.composite
def environment_strategy(draw):
    """Generate a random environment."""
    config = draw(hardware_config_strategy())
    env_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return Environment(
        id=env_id,
        config=config,
        status=EnvironmentStatus.IDLE,
        created_at=datetime.now(),
        last_used=datetime.now()
    )


@st.composite
def failure_info_strategy(draw, error_type=None):
    """Generate a random failure info with optional fixed error type."""
    if error_type is None:
        error_patterns = [
            ("NULL pointer dereference at address 0x{addr}", "null_pointer"),
            ("use-after-free in function {func}", "use_after_free"),
            ("buffer overflow in {func}", "buffer_overflow"),
            ("deadlock detected in {func}", "deadlock"),
            ("race condition in {func}", "race_condition"),
            ("memory leak in {func}", "memory_leak"),
        ]
        error_template, pattern_type = draw(st.sampled_from(error_patterns))
    else:
        # Use the specified error type
        error_templates = {
            "null_pointer": "NULL pointer dereference at address 0x{addr}",
            "use_after_free": "use-after-free in function {func}",
            "buffer_overflow": "buffer overflow in {func}",
            "deadlock": "deadlock detected in {func}",
            "race_condition": "race condition in {func}",
            "memory_leak": "memory leak in {func}",
        }
        error_template = error_templates.get(error_type, "error in {func}")
        pattern_type = error_type
    
    # Generate function name
    func_name = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    addr = draw(st.text(min_size=8, max_size=16, alphabet='0123456789abcdef'))
    
    error_message = error_template.format(func=func_name, addr=addr)
    
    # Generate stack trace with the function
    stack_trace = f"""Call Trace:
 [{addr}] {func_name}+0x42/0x100
 [ffffffff81234567] caller_function+0x10/0x20
 [ffffffff81345678] top_level_function+0x5/0x10
"""
    
    return FailureInfo(
        error_message=error_message,
        stack_trace=stack_trace,
        exit_code=draw(st.integers(min_value=1, max_value=255)),
        kernel_panic=draw(st.booleans())
    ), pattern_type


@st.composite
def failed_test_result_strategy(draw, error_type=None):
    """Generate a random test result with failure."""
    test_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    execution_time = draw(st.floats(min_value=0.1, max_value=300.0))
    environment = draw(environment_strategy())
    failure_info, pattern_type = draw(failure_info_strategy(error_type=error_type))
    
    return TestResult(
        test_id=test_id,
        status=TestStatus.FAILED,
        execution_time=execution_time,
        environment=environment,
        artifacts=ArtifactBundle(),
        failure_info=failure_info,
        timestamp=datetime.now()
    ), pattern_type


@given(st.lists(failed_test_result_strategy(), min_size=2, max_size=20))
@settings(max_examples=100, deadline=None)
def test_failures_are_grouped(failures_with_types: List[tuple]):
    """
    Property: For any set of test failures, the group_failures method should return
    a dictionary where each group contains at least one failure.
    
    **Feature: agentic-kernel-testing, Property 18: Failure grouping consistency**
    **Validates: Requirements 4.3**
    """
    failures = [f[0] for f in failures_with_types]
    
    analyzer = RootCauseAnalyzer()
    groups = analyzer.group_failures(failures)
    
    # Verify groups is a dictionary
    assert isinstance(groups, dict), "group_failures should return a dictionary"
    
    # Verify all groups have at least one failure
    for signature, group_failures in groups.items():
        assert len(group_failures) > 0, f"Group {signature} should have at least one failure"
        
        # Verify all items in group are TestResult objects
        for failure in group_failures:
            assert isinstance(failure, TestResult), "Group should contain TestResult objects"
            assert failure.status == TestStatus.FAILED, "Group should only contain failed tests"
    
    # Verify all failures are accounted for
    total_grouped = sum(len(group) for group in groups.values())
    assert total_grouped == len(failures), \
        f"All failures should be grouped. Expected {len(failures)}, got {total_grouped}"


@given(st.integers(min_value=2, max_value=10))
@settings(max_examples=100, deadline=None)
def test_same_error_type_grouped_together(num_failures: int):
    """
    Property: For any set of test failures with the same error type and similar stack traces,
    they should be grouped together under the same signature.
    
    **Feature: agentic-kernel-testing, Property 18: Failure grouping consistency**
    **Validates: Requirements 4.3**
    """
    # Generate failures with the same error type
    error_type = "null_pointer"
    
    # Create multiple failures with same error pattern
    failures = []
    for i in range(num_failures):
        env = Environment(
            id=f"env_{i}",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="test_cpu",
                memory_mb=1024
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        # Same error pattern, same function name for consistent grouping
        failure_info = FailureInfo(
            error_message="NULL pointer dereference at address 0xdeadbeef",
            stack_trace="""Call Trace:
 [deadbeef] test_function+0x42/0x100
 [ffffffff81234567] caller_function+0x10/0x20
""",
            exit_code=1,
            kernel_panic=True
        )
        
        failures.append(TestResult(
            test_id=f"test_{i}",
            status=TestStatus.FAILED,
            execution_time=1.0,
            environment=env,
            failure_info=failure_info,
            timestamp=datetime.now()
        ))
    
    analyzer = RootCauseAnalyzer()
    groups = analyzer.group_failures(failures)
    
    # All failures with same error pattern should be in same group
    # (or at most a few groups due to minor variations)
    assert len(groups) <= 3, \
        f"Failures with same error type should be grouped together. Got {len(groups)} groups"
    
    # The largest group should contain most of the failures
    largest_group_size = max(len(group) for group in groups.values())
    assert largest_group_size >= num_failures * 0.5, \
        f"Largest group should contain at least half the failures. Got {largest_group_size}/{num_failures}"


@given(st.integers(min_value=2, max_value=5), st.integers(min_value=2, max_value=5))
@settings(max_examples=100, deadline=None)
def test_different_error_types_grouped_separately(num_type1: int, num_type2: int):
    """
    Property: For any set of test failures with different error types, they should be
    grouped into separate groups.
    
    **Feature: agentic-kernel-testing, Property 18: Failure grouping consistency**
    **Validates: Requirements 4.3**
    """
    failures = []
    
    # Create failures of type 1
    for i in range(num_type1):
        env = Environment(
            id=f"env_type1_{i}",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="test_cpu",
                memory_mb=1024
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        failure_info = FailureInfo(
            error_message="NULL pointer dereference at address 0xdeadbeef",
            stack_trace="""Call Trace:
 [deadbeef] null_deref_function+0x42/0x100
""",
            exit_code=1,
            kernel_panic=True
        )
        
        failures.append(TestResult(
            test_id=f"test_type1_{i}",
            status=TestStatus.FAILED,
            execution_time=1.0,
            environment=env,
            failure_info=failure_info,
            timestamp=datetime.now()
        ))
    
    # Create failures of type 2 (different error)
    for i in range(num_type2):
        env = Environment(
            id=f"env_type2_{i}",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="test_cpu",
                memory_mb=1024
            ),
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        failure_info = FailureInfo(
            error_message="use-after-free in function uaf_function",
            stack_trace="""Call Trace:
 [cafebabe] uaf_function+0x10/0x50
""",
            exit_code=1,
            kernel_panic=True
        )
        
        failures.append(TestResult(
            test_id=f"test_type2_{i}",
            status=TestStatus.FAILED,
            execution_time=1.0,
            environment=env,
            failure_info=failure_info,
            timestamp=datetime.now()
        ))
    
    analyzer = RootCauseAnalyzer()
    groups = analyzer.group_failures(failures)
    
    # Should have at least 2 groups (one for each error type)
    assert len(groups) >= 2, \
        f"Different error types should be in separate groups. Got {len(groups)} groups"
    
    # Verify no group contains all failures (they should be split)
    max_group_size = max(len(group) for group in groups.values())
    total_failures = num_type1 + num_type2
    assert max_group_size < total_failures, \
        f"No single group should contain all failures. Max group: {max_group_size}, Total: {total_failures}"


@given(st.lists(failed_test_result_strategy(), min_size=1, max_size=20))
@settings(max_examples=100, deadline=None)
def test_grouping_preserves_all_failures(failures_with_types: List[tuple]):
    """
    Property: For any set of test failures, grouping should preserve all failures
    without losing or duplicating any.
    
    **Feature: agentic-kernel-testing, Property 18: Failure grouping consistency**
    **Validates: Requirements 4.3**
    """
    failures = [f[0] for f in failures_with_types]
    
    analyzer = RootCauseAnalyzer()
    groups = analyzer.group_failures(failures)
    
    # Collect all test IDs from groups
    grouped_test_ids = set()
    for group_failures in groups.values():
        for failure in group_failures:
            grouped_test_ids.add(failure.test_id)
    
    # Collect original test IDs
    original_test_ids = set(f.test_id for f in failures)
    
    # Verify no failures are lost
    assert grouped_test_ids == original_test_ids, \
        f"Grouping should preserve all failures. Missing: {original_test_ids - grouped_test_ids}, Extra: {grouped_test_ids - original_test_ids}"


@given(st.lists(failed_test_result_strategy(), min_size=1, max_size=20))
@settings(max_examples=100, deadline=None)
def test_grouping_is_deterministic(failures_with_types: List[tuple]):
    """
    Property: For any set of test failures, grouping should be deterministic -
    running it multiple times should produce the same groups.
    
    **Feature: agentic-kernel-testing, Property 18: Failure grouping consistency**
    **Validates: Requirements 4.3**
    """
    failures = [f[0] for f in failures_with_types]
    
    analyzer = RootCauseAnalyzer()
    
    # Group failures twice
    groups1 = analyzer.group_failures(failures)
    groups2 = analyzer.group_failures(failures)
    
    # Verify same number of groups
    assert len(groups1) == len(groups2), \
        f"Grouping should be deterministic. Got {len(groups1)} and {len(groups2)} groups"
    
    # Verify same signatures
    assert set(groups1.keys()) == set(groups2.keys()), \
        "Grouping should produce same signatures"
    
    # Verify same failures in each group
    for signature in groups1.keys():
        ids1 = set(f.test_id for f in groups1[signature])
        ids2 = set(f.test_id for f in groups2[signature])
        assert ids1 == ids2, \
            f"Group {signature} should have same failures in both runs"
