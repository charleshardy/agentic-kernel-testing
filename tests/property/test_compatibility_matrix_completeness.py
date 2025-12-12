"""Property-based tests for compatibility matrix completeness.

**Feature: agentic-kernel-testing, Property 9: Compatibility matrix completeness**
**Validates: Requirements 2.4**

Property: For any completed BSP test run, the compatibility matrix should show 
pass/fail status for every hardware configuration in the test matrix.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List

from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, Peripheral, ArtifactBundle, FailureInfo
)
from execution.hardware_config import TestMatrix, TestMatrixGenerator
from analysis.compatibility_matrix import (
    CompatibilityMatrixGenerator, CompatibilityMatrix, MatrixCellStatus
)


# Custom strategies for generating test data
@st.composite
def hardware_config_strategy(draw):
    """Generate a random hardware configuration."""
    architecture = draw(st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']))
    cpu_models = {
        'x86_64': ['Intel Core i7', 'AMD Ryzen 9', 'Intel Xeon'],
        'arm64': ['ARM Cortex-A72', 'ARM Cortex-A76', 'Apple M1'],
        'arm': ['ARM Cortex-A53', 'ARM Cortex-A7'],
        'riscv64': ['SiFive U74', 'SiFive U54']
    }
    cpu_model = draw(st.sampled_from(cpu_models[architecture]))
    memory_mb = draw(st.sampled_from([512, 1024, 2048, 4096, 8192]))
    is_virtual = draw(st.booleans())
    emulator = 'qemu' if is_virtual else None
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=cpu_model,
        memory_mb=memory_mb,
        storage_type='ssd',
        peripherals=[],
        is_virtual=is_virtual,
        emulator=emulator
    )


def test_result_strategy(hardware_config):
    @st.composite
    def _strategy(draw):
        """Generate a random test result for a given hardware configuration."""
        test_id = f"test_{draw(st.integers(min_value=1, max_value=10000))}"
        status = draw(st.sampled_from([TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]))
        execution_time = draw(st.floats(min_value=0.1, max_value=300.0))
        
        environment = Environment(
            id=f"env_{draw(st.integers(min_value=1, max_value=1000))}",
            config=hardware_config,
            status=EnvironmentStatus.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        failure_info = None
        if status in [TestStatus.FAILED, TestStatus.ERROR]:
            failure_info = FailureInfo(
                error_message=f"Test failed: {draw(st.text(min_size=10, max_size=50))}",
                exit_code=draw(st.integers(min_value=1, max_value=255))
            )
        
        return TestResult(
            test_id=test_id,
            status=status,
            execution_time=execution_time,
            environment=environment,
            artifacts=ArtifactBundle(),
            failure_info=failure_info,
            timestamp=datetime.now()
        )
    return _strategy()


@st.composite
def test_matrix_with_results_strategy(draw):
    """Generate a test matrix with corresponding test results."""
    # Generate 2-10 hardware configurations
    num_configs = draw(st.integers(min_value=2, max_value=10))
    configs = [draw(hardware_config_strategy()) for _ in range(num_configs)]
    
    # Create test matrix
    test_matrix = TestMatrix(configurations=configs)
    
    # Generate 1-5 test results for each configuration
    all_results = []
    for config in configs:
        num_results = draw(st.integers(min_value=1, max_value=5))
        for _ in range(num_results):
            result = draw(test_result_strategy(config))
            all_results.append(result)
    
    return test_matrix, all_results


@given(test_matrix_with_results_strategy())
@settings(max_examples=100, deadline=None)
def test_compatibility_matrix_completeness(matrix_and_results):
    """
    Property 9: Compatibility matrix completeness
    
    For any completed BSP test run, the compatibility matrix should show 
    pass/fail status for every hardware configuration in the test matrix.
    
    This test verifies that:
    1. Every hardware configuration in the test matrix appears in the compatibility matrix
    2. Each configuration has a defined status (not None or missing)
    3. The matrix contains exactly the configurations from the test matrix
    """
    test_matrix, test_results = matrix_and_results
    
    # Generate compatibility matrix from results
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        test_results,
        hardware_configs=test_matrix.configurations
    )
    
    # Property: Matrix should have a cell for every configuration in test matrix
    assert len(compat_matrix.cells) == len(test_matrix.configurations), \
        f"Matrix has {len(compat_matrix.cells)} cells but test matrix has {len(test_matrix.configurations)} configs"
    
    # Property: Every configuration in test matrix should appear in compatibility matrix
    matrix_config_keys = set()
    for cell in compat_matrix.cells:
        config = cell.hardware_config
        key = f"{config.architecture}_{config.cpu_model}_{config.memory_mb}_{config.is_virtual}"
        matrix_config_keys.add(key)
    
    for config in test_matrix.configurations:
        key = f"{config.architecture}_{config.cpu_model}_{config.memory_mb}_{config.is_virtual}"
        assert key in matrix_config_keys, \
            f"Configuration {config.architecture}/{config.cpu_model} not found in compatibility matrix"
    
    # Property: Every cell should have a defined status
    for cell in compat_matrix.cells:
        assert cell.status is not None, \
            f"Cell for {cell.hardware_config.architecture}/{cell.hardware_config.cpu_model} has no status"
        assert isinstance(cell.status, MatrixCellStatus), \
            f"Cell status is not a MatrixCellStatus enum: {type(cell.status)}"
    
    # Property: Cells with test results should not have NOT_TESTED status
    for cell in compat_matrix.cells:
        if len(cell.test_results) > 0:
            assert cell.status != MatrixCellStatus.NOT_TESTED, \
                f"Cell with {len(cell.test_results)} results has NOT_TESTED status"
    
    # Property: Cells without test results should have NOT_TESTED status
    for cell in compat_matrix.cells:
        if len(cell.test_results) == 0:
            assert cell.status == MatrixCellStatus.NOT_TESTED, \
                f"Cell with no results has status {cell.status} instead of NOT_TESTED"


@given(test_matrix_with_results_strategy())
@settings(max_examples=100, deadline=None)
def test_matrix_cell_status_accuracy(matrix_and_results):
    """
    Property: Matrix cell status should accurately reflect test results.
    
    This verifies that:
    1. PASSED status only when all tests passed
    2. FAILED status when some/all tests failed
    3. MIXED status when both passed and failed tests exist
    4. Counts are accurate
    """
    test_matrix, test_results = matrix_and_results
    
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        test_results,
        hardware_configs=test_matrix.configurations
    )
    
    for cell in compat_matrix.cells:
        if len(cell.test_results) == 0:
            continue
        
        # Count actual statuses
        actual_passed = sum(1 for r in cell.test_results if r.status == TestStatus.PASSED)
        actual_failed = sum(
            1 for r in cell.test_results 
            if r.status in [TestStatus.FAILED, TestStatus.TIMEOUT]
        )
        actual_error = sum(1 for r in cell.test_results if r.status == TestStatus.ERROR)
        
        # Verify counts match
        assert cell.pass_count == actual_passed, \
            f"Pass count mismatch: {cell.pass_count} != {actual_passed}"
        assert cell.fail_count == actual_failed, \
            f"Fail count mismatch: {cell.fail_count} != {actual_failed}"
        assert cell.error_count == actual_error, \
            f"Error count mismatch: {cell.error_count} != {actual_error}"
        assert cell.total_count == len(cell.test_results), \
            f"Total count mismatch: {cell.total_count} != {len(cell.test_results)}"
        
        # Verify status logic
        if actual_passed == len(cell.test_results):
            assert cell.status == MatrixCellStatus.PASSED, \
                f"All tests passed but status is {cell.status}"
        elif actual_passed > 0 and (actual_failed > 0 or actual_error > 0):
            assert cell.status == MatrixCellStatus.MIXED, \
                f"Mixed results but status is {cell.status}"
        elif actual_failed > 0:
            assert cell.status in [MatrixCellStatus.FAILED, MatrixCellStatus.MIXED], \
                f"Tests failed but status is {cell.status}"
        elif actual_error > 0:
            assert cell.status in [MatrixCellStatus.ERROR, MatrixCellStatus.MIXED], \
                f"Tests errored but status is {cell.status}"


@given(test_matrix_with_results_strategy())
@settings(max_examples=100, deadline=None)
def test_matrix_pass_rate_calculation(matrix_and_results):
    """
    Property: Pass rate should be correctly calculated for each cell.
    
    Pass rate = passed tests / total tests
    """
    test_matrix, test_results = matrix_and_results
    
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        test_results,
        hardware_configs=test_matrix.configurations
    )
    
    for cell in compat_matrix.cells:
        if cell.total_count == 0:
            assert cell.pass_rate == 0.0, \
                f"Pass rate should be 0.0 for empty cell, got {cell.pass_rate}"
        else:
            expected_pass_rate = cell.pass_count / cell.total_count
            assert abs(cell.pass_rate - expected_pass_rate) < 0.001, \
                f"Pass rate mismatch: {cell.pass_rate} != {expected_pass_rate}"
            assert 0.0 <= cell.pass_rate <= 1.0, \
                f"Pass rate out of range: {cell.pass_rate}"


@given(test_matrix_with_results_strategy(), test_matrix_with_results_strategy())
@settings(max_examples=50, deadline=None)
def test_matrix_population_preserves_completeness(matrix_and_results1, matrix_and_results2):
    """
    Property: Populating a matrix with new results should preserve completeness.
    
    After adding new results, all original configurations should still be present.
    """
    test_matrix1, test_results1 = matrix_and_results1
    test_matrix2, test_results2 = matrix_and_results2
    
    # Generate initial matrix
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        test_results1,
        hardware_configs=test_matrix1.configurations
    )
    
    original_config_count = len(compat_matrix.cells)
    original_configs = {
        f"{c.hardware_config.architecture}_{c.hardware_config.cpu_model}_{c.hardware_config.memory_mb}"
        for c in compat_matrix.cells
    }
    
    # Populate with new results
    compat_matrix = CompatibilityMatrixGenerator.populate_matrix(
        compat_matrix,
        test_results2
    )
    
    # Property: All original configurations should still be present
    current_configs = {
        f"{c.hardware_config.architecture}_{c.hardware_config.cpu_model}_{c.hardware_config.memory_mb}"
        for c in compat_matrix.cells
    }
    
    assert original_configs.issubset(current_configs), \
        "Some original configurations were lost during population"
    
    # Property: Matrix should have at least as many cells as before
    assert len(compat_matrix.cells) >= original_config_count, \
        f"Matrix shrunk from {original_config_count} to {len(compat_matrix.cells)} cells"


@given(st.lists(test_matrix_with_results_strategy(), min_size=2, max_size=5))
@settings(max_examples=50, deadline=None)
def test_matrix_merge_completeness(matrices_and_results):
    """
    Property: Merging matrices should preserve all configurations.
    
    The merged matrix should contain all configurations from all input matrices.
    """
    all_configs = set()
    matrices = []
    
    for test_matrix, test_results in matrices_and_results:
        compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
            test_results,
            hardware_configs=test_matrix.configurations
        )
        matrices.append(compat_matrix)
        
        for config in test_matrix.configurations:
            key = f"{config.architecture}_{config.cpu_model}_{config.memory_mb}_{config.is_virtual}"
            all_configs.add(key)
    
    # Merge matrices
    merged = CompatibilityMatrixGenerator.merge_matrices(matrices)
    
    # Property: Merged matrix should contain all unique configurations
    merged_configs = {
        f"{c.hardware_config.architecture}_{c.hardware_config.cpu_model}_{c.hardware_config.memory_mb}_{c.hardware_config.is_virtual}"
        for c in merged.cells
    }
    
    assert all_configs == merged_configs, \
        f"Merged matrix missing configurations. Expected {len(all_configs)}, got {len(merged_configs)}"
    
    # Property: Every cell in merged matrix should have a status
    for cell in merged.cells:
        assert cell.status is not None, \
            "Merged matrix has cell with no status"


@given(test_matrix_with_results_strategy())
@settings(max_examples=100, deadline=None)
def test_matrix_summary_consistency(matrix_and_results):
    """
    Property: Matrix summary should be consistent with cell data.
    
    Summary statistics should match the actual cell counts and statuses.
    """
    test_matrix, test_results = matrix_and_results
    
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        test_results,
        hardware_configs=test_matrix.configurations
    )
    
    summary = compat_matrix.get_summary()
    
    # Property: Total configurations should match cell count
    assert summary['total_configurations'] == len(compat_matrix.cells), \
        f"Summary total {summary['total_configurations']} != actual {len(compat_matrix.cells)}"
    
    # Property: Status counts should match actual cells
    actual_passed = len(compat_matrix.get_cells_by_status(MatrixCellStatus.PASSED))
    actual_failed = len(compat_matrix.get_cells_by_status(MatrixCellStatus.FAILED))
    actual_mixed = len(compat_matrix.get_cells_by_status(MatrixCellStatus.MIXED))
    actual_not_tested = len(compat_matrix.get_cells_by_status(MatrixCellStatus.NOT_TESTED))
    
    assert summary['passed_configs'] == actual_passed, \
        f"Passed count mismatch: {summary['passed_configs']} != {actual_passed}"
    assert summary['failed_configs'] == actual_failed, \
        f"Failed count mismatch: {summary['failed_configs']} != {actual_failed}"
    assert summary['mixed_configs'] == actual_mixed, \
        f"Mixed count mismatch: {summary['mixed_configs']} != {actual_mixed}"
    assert summary['not_tested_configs'] == actual_not_tested, \
        f"Not tested count mismatch: {summary['not_tested_configs']} != {actual_not_tested}"
    
    # Property: Overall pass rate should be in valid range
    assert 0.0 <= summary['overall_pass_rate'] <= 1.0, \
        f"Overall pass rate out of range: {summary['overall_pass_rate']}"
    
    # Property: Architectures in summary should match actual architectures
    actual_architectures = compat_matrix.get_architectures()
    assert set(summary['architectures']) == actual_architectures, \
        f"Architecture mismatch in summary"
