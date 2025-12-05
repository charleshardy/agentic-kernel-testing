"""Property-based tests for result aggregation.

**Feature: agentic-kernel-testing, Property 7: Result aggregation structure**
**Validates: Requirements 2.2**

Property 7: Result aggregation structure
For any multi-hardware test execution, results should be aggregated by architecture, 
board type, and peripheral configuration, with all dimensions represented.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from typing import List

from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle, Peripheral
)
from execution.test_runner import TestRunner


# Custom strategies for generating test data
@st.composite
def peripheral_strategy(draw):
    """Generate a random peripheral."""
    return Peripheral(
        name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        type=draw(st.sampled_from(['usb', 'pci', 'i2c', 'spi', 'uart'])),
        model=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    )


@st.composite
def hardware_config_strategy(draw):
    """Generate a random hardware configuration."""
    architecture = draw(st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']))
    cpu_model = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    memory_mb = draw(st.integers(min_value=512, max_value=16384))
    num_peripherals = draw(st.integers(min_value=0, max_value=5))
    peripherals = [draw(peripheral_strategy()) for _ in range(num_peripherals)]
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=cpu_model,
        memory_mb=memory_mb,
        storage_type='ssd',
        peripherals=peripherals,
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
def test_result_strategy(draw):
    """Generate a random test result."""
    test_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    status = draw(st.sampled_from(list(TestStatus)))
    execution_time = draw(st.floats(min_value=0.1, max_value=300.0))
    environment = draw(environment_strategy())
    
    return TestResult(
        test_id=test_id,
        status=status,
        execution_time=execution_time,
        environment=environment,
        artifacts=ArtifactBundle(),
        timestamp=datetime.now()
    )


@given(st.lists(test_result_strategy(), min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_aggregation_by_architecture(results: List[TestResult]):
    """
    Property: For any multi-hardware test execution, results aggregated by architecture
    should include all unique architectures present in the results.
    
    **Feature: agentic-kernel-testing, Property 7: Result aggregation structure**
    **Validates: Requirements 2.2**
    """
    runner = TestRunner()
    
    # Aggregate by architecture
    aggregated = runner.aggregate_results(results, group_by='architecture')
    
    # Extract unique architectures from results
    unique_architectures = set(r.environment.config.architecture for r in results)
    
    # Verify all architectures are represented in groups
    assert set(aggregated['groups'].keys()) == unique_architectures, \
        f"Not all architectures represented. Expected: {unique_architectures}, Got: {set(aggregated['groups'].keys())}"
    
    # Verify each group has correct structure
    for arch, group_data in aggregated['groups'].items():
        assert 'total' in group_data
        assert 'passed' in group_data
        assert 'failed' in group_data
        assert 'pass_rate' in group_data
        
        # Verify counts are non-negative
        assert group_data['total'] >= 0
        assert group_data['passed'] >= 0
        assert group_data['failed'] >= 0
        
        # Verify pass_rate is between 0 and 1
        assert 0.0 <= group_data['pass_rate'] <= 1.0


@given(st.lists(test_result_strategy(), min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_aggregation_by_board_type(results: List[TestResult]):
    """
    Property: For any multi-hardware test execution, results aggregated by board type
    should include all unique board types (cpu_model) present in the results.
    
    **Feature: agentic-kernel-testing, Property 7: Result aggregation structure**
    **Validates: Requirements 2.2**
    """
    runner = TestRunner()
    
    # Aggregate by board type
    aggregated = runner.aggregate_results(results, group_by='board_type')
    
    # Extract unique board types from results
    unique_board_types = set(r.environment.config.cpu_model for r in results)
    
    # Verify all board types are represented in groups
    assert set(aggregated['groups'].keys()) == unique_board_types, \
        f"Not all board types represented. Expected: {unique_board_types}, Got: {set(aggregated['groups'].keys())}"
    
    # Verify each group has correct structure
    for board_type, group_data in aggregated['groups'].items():
        assert 'total' in group_data
        assert 'passed' in group_data
        assert 'failed' in group_data
        assert 'pass_rate' in group_data


@given(st.lists(test_result_strategy(), min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_aggregation_by_peripheral_config(results: List[TestResult]):
    """
    Property: For any multi-hardware test execution, results aggregated by peripheral
    configuration should include all unique peripheral configurations present in the results.
    
    **Feature: agentic-kernel-testing, Property 7: Result aggregation structure**
    **Validates: Requirements 2.2**
    """
    runner = TestRunner()
    
    # Aggregate by peripheral configuration
    aggregated = runner.aggregate_results(results, group_by='peripheral_config')
    
    # Extract unique peripheral configs from results
    unique_configs = set(
        f"{len(r.environment.config.peripherals)}_peripherals" 
        for r in results
    )
    
    # Verify all peripheral configs are represented in groups
    assert set(aggregated['groups'].keys()) == unique_configs, \
        f"Not all peripheral configs represented. Expected: {unique_configs}, Got: {set(aggregated['groups'].keys())}"
    
    # Verify each group has correct structure
    for config, group_data in aggregated['groups'].items():
        assert 'total' in group_data
        assert 'passed' in group_data
        assert 'failed' in group_data
        assert 'pass_rate' in group_data


@given(st.lists(test_result_strategy(), min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_aggregation_overall_statistics(results: List[TestResult]):
    """
    Property: For any test execution, aggregated results should have correct overall
    statistics that match the sum of individual results.
    
    **Feature: agentic-kernel-testing, Property 7: Result aggregation structure**
    **Validates: Requirements 2.2**
    """
    runner = TestRunner()
    
    # Aggregate results
    aggregated = runner.aggregate_results(results)
    
    # Verify total count
    assert aggregated['total'] == len(results)
    
    # Count statuses manually
    passed_count = sum(1 for r in results if r.status == TestStatus.PASSED)
    failed_count = sum(1 for r in results if r.status == TestStatus.FAILED)
    timeout_count = sum(1 for r in results if r.status == TestStatus.TIMEOUT)
    error_count = sum(1 for r in results if r.status == TestStatus.ERROR)
    skipped_count = sum(1 for r in results if r.status == TestStatus.SKIPPED)
    
    # Verify counts match
    assert aggregated['passed'] == passed_count
    assert aggregated['failed'] == failed_count
    assert aggregated['timeout'] == timeout_count
    assert aggregated['error'] == error_count
    assert aggregated['skipped'] == skipped_count
    
    # Verify pass rate calculation
    expected_pass_rate = passed_count / len(results) if len(results) > 0 else 0.0
    assert abs(aggregated['pass_rate'] - expected_pass_rate) < 0.001
    
    # Verify total execution time
    expected_total_time = sum(r.execution_time for r in results)
    assert abs(aggregated['total_execution_time'] - expected_total_time) < 0.001


@given(st.lists(test_result_strategy(), min_size=1, max_size=50))
@settings(max_examples=100, deadline=None)
def test_aggregation_all_dimensions_represented(results: List[TestResult]):
    """
    Property: For any multi-hardware test execution, when aggregating by any dimension
    (architecture, board_type, peripheral_config), all unique values of that dimension
    should be represented in the aggregated groups.
    
    **Feature: agentic-kernel-testing, Property 7: Result aggregation structure**
    **Validates: Requirements 2.2**
    """
    runner = TestRunner()
    
    # Test all three dimensions
    dimensions = ['architecture', 'board_type', 'peripheral_config']
    
    for dimension in dimensions:
        aggregated = runner.aggregate_results(results, group_by=dimension)
        
        # Extract expected keys based on dimension
        if dimension == 'architecture':
            expected_keys = set(r.environment.config.architecture for r in results)
        elif dimension == 'board_type':
            expected_keys = set(r.environment.config.cpu_model for r in results)
        else:  # peripheral_config
            expected_keys = set(
                f"{len(r.environment.config.peripherals)}_peripherals" 
                for r in results
            )
        
        # Verify all dimensions are represented
        actual_keys = set(aggregated['groups'].keys())
        assert actual_keys == expected_keys, \
            f"Dimension {dimension}: Expected keys {expected_keys}, got {actual_keys}"
        
        # Verify sum of group totals equals overall total
        group_total = sum(g['total'] for g in aggregated['groups'].values())
        assert group_total == len(results), \
            f"Dimension {dimension}: Group totals {group_total} != overall total {len(results)}"
