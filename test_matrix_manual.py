#!/usr/bin/env python3
"""Manual test for compatibility matrix implementation."""

import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '.')

from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle, FailureInfo
)
from execution.hardware_config import TestMatrix, TestMatrixGenerator
from analysis.compatibility_matrix import (
    CompatibilityMatrixGenerator, MatrixVisualizer, MatrixExporter
)


def create_test_hardware_config(arch, cpu, memory, is_virtual):
    """Create a test hardware configuration."""
    return HardwareConfig(
        architecture=arch,
        cpu_model=cpu,
        memory_mb=memory,
        storage_type='ssd',
        peripherals=[],
        is_virtual=is_virtual,
        emulator='qemu' if is_virtual else None
    )


def create_test_result(test_id, status, config):
    """Create a test result."""
    env = Environment(
        id=f"env_{test_id}",
        config=config,
        status=EnvironmentStatus.IDLE,
        created_at=datetime.now(),
        last_used=datetime.now()
    )
    
    failure_info = None
    if status == TestStatus.FAILED:
        failure_info = FailureInfo(
            error_message="Test failed",
            exit_code=1
        )
    
    return TestResult(
        test_id=test_id,
        status=status,
        execution_time=1.5,
        environment=env,
        artifacts=ArtifactBundle(),
        failure_info=failure_info,
        timestamp=datetime.now()
    )


def test_basic_matrix_generation():
    """Test basic matrix generation."""
    print("Test 1: Basic matrix generation")
    
    # Create test matrix with 3 configurations
    configs = [
        create_test_hardware_config('x86_64', 'Intel Core i7', 4096, True),
        create_test_hardware_config('arm64', 'ARM Cortex-A72', 2048, True),
        create_test_hardware_config('riscv64', 'SiFive U74', 2048, False),
    ]
    
    test_matrix = TestMatrix(configurations=configs)
    
    # Create test results for each configuration
    results = [
        create_test_result('test1', TestStatus.PASSED, configs[0]),
        create_test_result('test2', TestStatus.PASSED, configs[0]),
        create_test_result('test3', TestStatus.FAILED, configs[1]),
        create_test_result('test4', TestStatus.PASSED, configs[1]),
        create_test_result('test5', TestStatus.PASSED, configs[2]),
    ]
    
    # Generate compatibility matrix
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        results,
        hardware_configs=test_matrix.configurations
    )
    
    # Verify completeness
    assert len(compat_matrix.cells) == len(test_matrix.configurations), \
        f"Expected {len(test_matrix.configurations)} cells, got {len(compat_matrix.cells)}"
    
    # Verify each configuration has a status
    for cell in compat_matrix.cells:
        assert cell.status is not None, "Cell has no status"
    
    print(f"✓ Matrix has {len(compat_matrix.cells)} cells")
    print(f"✓ All cells have status")
    
    # Print summary
    summary = compat_matrix.get_summary()
    print(f"✓ Overall pass rate: {summary['overall_pass_rate']:.2%}")
    print(f"✓ Passed configs: {summary['passed_configs']}")
    print(f"✓ Failed configs: {summary['failed_configs']}")
    print(f"✓ Mixed configs: {summary['mixed_configs']}")
    
    return True


def test_matrix_completeness_property():
    """Test the completeness property."""
    print("\nTest 2: Matrix completeness property")
    
    # Create test matrix
    configs = [
        create_test_hardware_config('x86_64', 'Intel Core i7', 4096, True),
        create_test_hardware_config('arm64', 'ARM Cortex-A72', 2048, True),
        create_test_hardware_config('arm', 'ARM Cortex-A53', 1024, False),
    ]
    
    test_matrix = TestMatrix(configurations=configs)
    
    # Create results for only 2 of the 3 configurations
    results = [
        create_test_result('test1', TestStatus.PASSED, configs[0]),
        create_test_result('test2', TestStatus.FAILED, configs[1]),
    ]
    
    # Generate matrix with all configs
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        results,
        hardware_configs=test_matrix.configurations
    )
    
    # Property: Every configuration in test matrix should appear in compatibility matrix
    assert len(compat_matrix.cells) == len(test_matrix.configurations), \
        "Not all configurations appear in matrix"
    
    # Property: Configurations without results should have NOT_TESTED status
    from analysis.compatibility_matrix import MatrixCellStatus
    not_tested_cells = compat_matrix.get_cells_by_status(MatrixCellStatus.NOT_TESTED)
    assert len(not_tested_cells) == 1, \
        f"Expected 1 NOT_TESTED cell, got {len(not_tested_cells)}"
    
    print(f"✓ All {len(test_matrix.configurations)} configurations present in matrix")
    print(f"✓ Untested configuration has NOT_TESTED status")
    
    return True


def test_matrix_visualization():
    """Test matrix visualization."""
    print("\nTest 3: Matrix visualization")
    
    # Create test data
    configs = [
        create_test_hardware_config('x86_64', 'Intel Core i7', 4096, True),
        create_test_hardware_config('arm64', 'ARM Cortex-A72', 2048, True),
    ]
    
    results = [
        create_test_result('test1', TestStatus.PASSED, configs[0]),
        create_test_result('test2', TestStatus.PASSED, configs[0]),
        create_test_result('test3', TestStatus.FAILED, configs[1]),
    ]
    
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(results, configs)
    
    # Test text visualization
    text_output = MatrixVisualizer.to_text_table(compat_matrix)
    assert 'COMPATIBILITY MATRIX' in text_output
    assert 'x86_64' in text_output or 'X86_64' in text_output
    print("✓ Text visualization works")
    
    # Test CSV export
    csv_output = MatrixVisualizer.to_csv(compat_matrix)
    assert 'Architecture' in csv_output
    assert 'x86_64' in csv_output
    print("✓ CSV export works")
    
    # Test HTML export
    html_output = MatrixVisualizer.to_html(compat_matrix)
    assert '<html>' in html_output
    assert 'Compatibility Matrix' in html_output
    print("✓ HTML export works")
    
    return True


def test_matrix_population():
    """Test matrix population with new results."""
    print("\nTest 4: Matrix population")
    
    configs = [
        create_test_hardware_config('x86_64', 'Intel Core i7', 4096, True),
    ]
    
    # Initial results
    initial_results = [
        create_test_result('test1', TestStatus.PASSED, configs[0]),
    ]
    
    # Generate initial matrix
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        initial_results,
        configs
    )
    
    initial_count = compat_matrix.cells[0].total_count
    print(f"  Initial test count: {initial_count}")
    
    # Add more results
    new_results = [
        create_test_result('test2', TestStatus.PASSED, configs[0]),
        create_test_result('test3', TestStatus.FAILED, configs[0]),
    ]
    
    # Populate matrix
    compat_matrix = CompatibilityMatrixGenerator.populate_matrix(
        compat_matrix,
        new_results
    )
    
    final_count = compat_matrix.cells[0].total_count
    print(f"  Final test count: {final_count}")
    
    assert final_count == initial_count + len(new_results), \
        "Matrix population didn't add all results"
    
    print("✓ Matrix population preserves and adds results")
    
    return True


def main():
    """Run all manual tests."""
    print("=" * 80)
    print("COMPATIBILITY MATRIX MANUAL TESTS")
    print("=" * 80)
    
    tests = [
        test_basic_matrix_generation,
        test_matrix_completeness_property,
        test_matrix_visualization,
        test_matrix_population,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
