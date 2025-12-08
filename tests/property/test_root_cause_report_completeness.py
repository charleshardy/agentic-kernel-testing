"""Property-based tests for root cause report completeness.

**Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
**Validates: Requirements 4.4**

Property 19: Root cause report completeness
For any completed root cause analysis, the report should include failure description,
affected code paths, and suggested fixes.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List

from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle, FailureInfo, FailureAnalysis
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
def failure_info_strategy(draw):
    """Generate a random failure info."""
    error_patterns = [
        ("NULL pointer dereference at address 0x{addr}", "null_pointer"),
        ("use-after-free in function {func}", "use_after_free"),
        ("buffer overflow in {func}", "buffer_overflow"),
        ("deadlock detected in {func}", "deadlock"),
        ("race condition in {func}", "race_condition"),
        ("memory leak in {func}", "memory_leak"),
        ("assertion failed in {func}", "assertion_failure"),
        ("timeout in {func}", "timeout"),
    ]
    error_template, pattern_type = draw(st.sampled_from(error_patterns))
    
    # Generate function name
    func_name = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    addr = draw(st.text(min_size=8, max_size=16, alphabet='0123456789abcdef'))
    
    error_message = error_template.format(func=func_name, addr=addr)
    
    # Generate stack trace with the function and file path
    file_path = f"kernel/{draw(st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))}.c"
    line_num = draw(st.integers(min_value=1, max_value=1000))
    
    stack_trace = f"""Call Trace:
 [{addr}] {func_name}+0x42/0x100 [{file_path}:{line_num}]
 [ffffffff81234567] caller_function+0x10/0x20 [kernel/caller.c:50]
 [ffffffff81345678] top_level_function+0x5/0x10 [kernel/top.c:100]
"""
    
    return FailureInfo(
        error_message=error_message,
        stack_trace=stack_trace,
        exit_code=draw(st.integers(min_value=1, max_value=255)),
        kernel_panic=draw(st.booleans())
    )


@st.composite
def failed_test_result_strategy(draw):
    """Generate a random test result with failure."""
    test_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    execution_time = draw(st.floats(min_value=0.1, max_value=300.0))
    environment = draw(environment_strategy())
    failure_info = draw(failure_info_strategy())
    
    return TestResult(
        test_id=test_id,
        status=TestStatus.FAILED,
        execution_time=execution_time,
        environment=environment,
        artifacts=ArtifactBundle(),
        failure_info=failure_info,
        timestamp=datetime.now()
    )


@given(failed_test_result_strategy())
@settings(max_examples=100, deadline=None)
def test_analysis_has_failure_description(failure: TestResult):
    """
    Property: For any test failure, the root cause analysis should include a
    failure description (root_cause field).
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze_failure(failure)
    
    # Verify analysis is returned
    assert isinstance(analysis, FailureAnalysis), "analyze_failure should return FailureAnalysis"
    
    # Verify root_cause is present and non-empty
    assert hasattr(analysis, 'root_cause'), "Analysis should have root_cause field"
    assert analysis.root_cause, "root_cause should not be empty"
    assert len(analysis.root_cause) > 0, "root_cause should have content"
    assert isinstance(analysis.root_cause, str), "root_cause should be a string"


@given(failed_test_result_strategy())
@settings(max_examples=100, deadline=None)
def test_analysis_has_affected_code_paths(failure: TestResult):
    """
    Property: For any test failure with a stack trace, the root cause analysis should
    include information about affected code paths (via stack_trace or error_pattern).
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze_failure(failure)
    
    # Verify analysis has code path information
    # This can be in stack_trace or error_pattern
    has_stack_trace = analysis.stack_trace is not None and len(analysis.stack_trace) > 0
    has_error_pattern = analysis.error_pattern is not None and len(analysis.error_pattern) > 0
    
    assert has_stack_trace or has_error_pattern, \
        "Analysis should include affected code paths via stack_trace or error_pattern"
    
    # If original failure had stack trace, analysis should preserve it
    if failure.failure_info and failure.failure_info.stack_trace:
        assert analysis.stack_trace is not None, \
            "Analysis should preserve stack trace from failure"


@given(failed_test_result_strategy())
@settings(max_examples=100, deadline=None)
def test_analysis_has_suggested_fixes(failure: TestResult):
    """
    Property: For any test failure, the root cause analysis should include
    suggested fixes (may be empty list, but field should exist).
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze_failure(failure)
    
    # Verify suggested_fixes field exists
    assert hasattr(analysis, 'suggested_fixes'), "Analysis should have suggested_fixes field"
    assert isinstance(analysis.suggested_fixes, list), "suggested_fixes should be a list"
    
    # Verify each fix has required fields
    for fix in analysis.suggested_fixes:
        assert hasattr(fix, 'description'), "Fix should have description"
        assert fix.description, "Fix description should not be empty"
        assert hasattr(fix, 'confidence'), "Fix should have confidence"
        assert 0.0 <= fix.confidence <= 1.0, "Fix confidence should be between 0 and 1"


@given(failed_test_result_strategy())
@settings(max_examples=100, deadline=None)
def test_analysis_has_all_required_fields(failure: TestResult):
    """
    Property: For any test failure, the root cause analysis should have all required
    fields: failure_id, root_cause, confidence, error_pattern, and suggested_fixes.
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze_failure(failure)
    
    # Verify all required fields exist
    required_fields = [
        'failure_id',
        'root_cause',
        'confidence',
        'error_pattern',
        'suggested_fixes'
    ]
    
    for field in required_fields:
        assert hasattr(analysis, field), f"Analysis should have {field} field"
    
    # Verify field types and constraints
    assert isinstance(analysis.failure_id, str), "failure_id should be string"
    assert len(analysis.failure_id) > 0, "failure_id should not be empty"
    
    assert isinstance(analysis.root_cause, str), "root_cause should be string"
    assert len(analysis.root_cause) > 0, "root_cause should not be empty"
    
    assert isinstance(analysis.confidence, float), "confidence should be float"
    assert 0.0 <= analysis.confidence <= 1.0, "confidence should be between 0 and 1"
    
    assert isinstance(analysis.error_pattern, str), "error_pattern should be string"
    
    assert isinstance(analysis.suggested_fixes, list), "suggested_fixes should be list"


@given(failed_test_result_strategy())
@settings(max_examples=100, deadline=None)
def test_analysis_confidence_is_valid(failure: TestResult):
    """
    Property: For any test failure, the root cause analysis confidence should be
    a valid probability value between 0.0 and 1.0.
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze_failure(failure)
    
    # Verify confidence is valid
    assert isinstance(analysis.confidence, (int, float)), "confidence should be numeric"
    assert 0.0 <= analysis.confidence <= 1.0, \
        f"confidence should be between 0 and 1, got {analysis.confidence}"


@given(failed_test_result_strategy())
@settings(max_examples=100, deadline=None)
def test_analysis_failure_id_matches_test_id(failure: TestResult):
    """
    Property: For any test failure, the root cause analysis failure_id should match
    the test_id from the original failure.
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze_failure(failure)
    
    # Verify failure_id matches test_id
    assert analysis.failure_id == failure.test_id, \
        f"failure_id should match test_id. Expected {failure.test_id}, got {analysis.failure_id}"


@given(st.lists(failed_test_result_strategy(), min_size=1, max_size=10))
@settings(max_examples=100, deadline=None)
def test_analysis_completeness_for_multiple_failures(failures: List[TestResult]):
    """
    Property: For any set of test failures, each analysis should be complete with
    all required fields populated.
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    
    for failure in failures:
        analysis = analyzer.analyze_failure(failure)
        
        # Verify completeness for each analysis
        assert analysis.failure_id, "failure_id should be populated"
        assert analysis.root_cause, "root_cause should be populated"
        assert analysis.confidence >= 0.0, "confidence should be non-negative"
        assert analysis.error_pattern, "error_pattern should be populated"
        assert isinstance(analysis.suggested_fixes, list), "suggested_fixes should be a list"
        
        # Verify failure_id matches
        assert analysis.failure_id == failure.test_id, \
            "failure_id should match test_id"


@given(failed_test_result_strategy())
@settings(max_examples=100, deadline=None)
def test_analysis_serialization(failure: TestResult):
    """
    Property: For any test failure analysis, it should be serializable to JSON
    and deserializable back to the same structure.
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze_failure(failure)
    
    # Serialize to JSON
    json_str = analysis.to_json()
    assert isinstance(json_str, str), "to_json should return string"
    assert len(json_str) > 0, "JSON string should not be empty"
    
    # Deserialize back
    deserialized = FailureAnalysis.from_json(json_str)
    
    # Verify key fields match
    assert deserialized.failure_id == analysis.failure_id
    assert deserialized.root_cause == analysis.root_cause
    assert abs(deserialized.confidence - analysis.confidence) < 0.001
    assert deserialized.error_pattern == analysis.error_pattern
    assert len(deserialized.suggested_fixes) == len(analysis.suggested_fixes)


@given(failed_test_result_strategy())
@settings(max_examples=100, deadline=None)
def test_analysis_has_reproducibility_score(failure: TestResult):
    """
    Property: For any test failure, the root cause analysis should include a
    reproducibility score indicating how reliably the failure can be reproduced.
    
    **Feature: agentic-kernel-testing, Property 19: Root cause report completeness**
    **Validates: Requirements 4.4**
    """
    analyzer = RootCauseAnalyzer()
    analysis = analyzer.analyze_failure(failure)
    
    # Verify reproducibility field exists
    assert hasattr(analysis, 'reproducibility'), "Analysis should have reproducibility field"
    assert isinstance(analysis.reproducibility, (int, float)), "reproducibility should be numeric"
    assert 0.0 <= analysis.reproducibility <= 1.0, \
        f"reproducibility should be between 0 and 1, got {analysis.reproducibility}"
