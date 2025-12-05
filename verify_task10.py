#!/usr/bin/env python3
"""Comprehensive verification of Task 10 implementation."""

import sys
sys.path.insert(0, '.')

from analysis.compatibility_matrix import (
    CompatibilityMatrixGenerator, CompatibilityMatrix, MatrixCell,
    MatrixCellStatus, MatrixVisualizer, MatrixExporter
)
from execution.hardware_config import TestMatrix, TestMatrixGenerator
from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle, FailureInfo
)
from datetime import datetime
import tempfile
from pathlib import Path


def create_test_config(arch, cpu, memory, is_virtual):
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
    if status in [TestStatus.FAILED, TestStatus.ERROR]:
        failure_info = FailureInfo(
            error_message=f"Test {test_id} failed",
            exit_code=1 if status == TestStatus.FAILED else 2
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


def verify_implementation():
    """Verify all aspects of the compatibility matrix generator."""
    
    print("=" * 70)
    print("TASK 10 IMPLEMENTATION VERIFICATION")
    print("=" * 70)
    
    # Test 1: Matrix data structure creation
    print("\n1. Testing matrix data structure creation...")
    configs = [
        create_test_config('x86_64', 'Intel Core i7', 4096, True),
        create_test_config('arm64', 'ARM Cortex-A72', 2048, True),
        create_test_config('riscv64', 'SiFive U74', 2048, False),
    ]
    
    test_matrix = TestMatrix(configurations=configs)
    assert len(test_matrix) == 3
    assert len(test_matrix.get_virtual_configs()) == 2
    assert len(test_matrix.get_physical_configs()) == 1
    print("   ✅ Matrix data structure works")
    
    # Test 2: Matrix population from test results
    print("\n2. Testing matrix population from test results...")
    results = [
        create_test_result('test1', TestStatus.PASSED, configs[0]),
        create_test_result('test2', TestStatus.PASSED, configs[0]),
        create_test_result('test3', TestStatus.FAILED, configs[1]),
        create_test_result('test4', TestStatus.PASSED, configs[1]),
        create_test_result('test5', TestStatus.PASSED, configs[2]),
    ]
    
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        results,
        hardware_configs=test_matrix.configurations
    )
    
    assert len(compat_matrix.cells) == 3
    assert all(cell.status is not None for cell in compat_matrix.cells)
    print("   ✅ Matrix population works")
    
    # Test 3: Completeness property - all configs present
    print("\n3. Testing completeness property...")
    matrix_config_keys = set()
    for cell in compat_matrix.cells:
        config = cell.hardware_config
        key = f"{config.architecture}_{config.cpu_model}_{config.memory_mb}_{config.is_virtual}"
        matrix_config_keys.add(key)
    
    for config in test_matrix.configurations:
        key = f"{config.architecture}_{config.cpu_model}_{config.memory_mb}_{config.is_virtual}"
        assert key in matrix_config_keys, \
            f"Configuration {config.architecture}/{config.cpu_model} not found in matrix"
    
    print("   ✅ All configurations present in matrix")
    
    # Test 4: Status accuracy
    print("\n4. Testing status accuracy...")
    for cell in compat_matrix.cells:
        if len(cell.test_results) > 0:
            # Verify counts
            actual_passed = sum(1 for r in cell.test_results if r.status == TestStatus.PASSED)
            actual_failed = sum(1 for r in cell.test_results if r.status in [TestStatus.FAILED, TestStatus.TIMEOUT])
            
            assert cell.pass_count == actual_passed
            assert cell.fail_count == actual_failed
            assert cell.total_count == len(cell.test_results)
            
            # Verify pass rate
            expected_pass_rate = actual_passed / len(cell.test_results)
            assert abs(cell.pass_rate - expected_pass_rate) < 0.001
    
    print("   ✅ Status and counts are accurate")
    
    # Test 5: NOT_TESTED status for untested configs
    print("\n5. Testing NOT_TESTED status...")
    configs_with_untested = [
        create_test_config('x86_64', 'Intel Core i7', 4096, True),
        create_test_config('arm64', 'ARM Cortex-A72', 2048, True),
        create_test_config('arm', 'ARM Cortex-A53', 1024, False),  # No results for this
    ]
    
    partial_results = [
        create_test_result('test1', TestStatus.PASSED, configs_with_untested[0]),
        create_test_result('test2', TestStatus.FAILED, configs_with_untested[1]),
    ]
    
    partial_matrix = CompatibilityMatrixGenerator.generate_from_results(
        partial_results,
        hardware_configs=configs_with_untested
    )
    
    not_tested_cells = partial_matrix.get_cells_by_status(MatrixCellStatus.NOT_TESTED)
    assert len(not_tested_cells) == 1
    assert not_tested_cells[0].hardware_config.architecture == 'arm'
    print("   ✅ NOT_TESTED status works correctly")
    
    # Test 6: Matrix visualization - text
    print("\n6. Testing text visualization...")
    text_output = MatrixVisualizer.to_text_table(compat_matrix)
    assert 'COMPATIBILITY MATRIX' in text_output
    assert 'x86_64' in text_output or 'X86_64' in text_output
    assert 'arm64' in text_output or 'ARM64' in text_output
    assert 'Pass Rate' in text_output
    print("   ✅ Text visualization works")
    
    # Test 7: Matrix visualization - CSV
    print("\n7. Testing CSV export...")
    csv_output = MatrixVisualizer.to_csv(compat_matrix)
    assert 'Architecture' in csv_output
    assert 'CPU Model' in csv_output
    assert 'x86_64' in csv_output
    assert 'arm64' in csv_output
    lines = csv_output.split('\n')
    assert len(lines) >= 4  # Header + 3 configs
    print("   ✅ CSV export works")
    
    # Test 8: Matrix visualization - HTML
    print("\n8. Testing HTML export...")
    html_output = MatrixVisualizer.to_html(compat_matrix)
    assert '<html>' in html_output
    assert 'Compatibility Matrix' in html_output
    assert '<table>' in html_output
    assert 'x86_64' in html_output
    print("   ✅ HTML export works")
    
    # Test 9: Matrix summary
    print("\n9. Testing matrix summary...")
    summary = compat_matrix.get_summary()
    assert summary['total_configurations'] == 3
    assert 'architectures' in summary
    assert 'overall_pass_rate' in summary
    assert 0.0 <= summary['overall_pass_rate'] <= 1.0
    assert summary['passed_configs'] + summary['failed_configs'] + summary['mixed_configs'] + summary['not_tested_configs'] == 3
    print("   ✅ Matrix summary works")
    
    # Test 10: Matrix population (adding new results)
    print("\n10. Testing matrix population with new results...")
    initial_count = compat_matrix.cells[0].total_count
    
    new_results = [
        create_test_result('test6', TestStatus.PASSED, configs[0]),
        create_test_result('test7', TestStatus.FAILED, configs[0]),
    ]
    
    compat_matrix = CompatibilityMatrixGenerator.populate_matrix(
        compat_matrix,
        new_results
    )
    
    final_count = compat_matrix.cells[0].total_count
    assert final_count == initial_count + 2
    print("   ✅ Matrix population preserves and adds results")
    
    # Test 11: Matrix merging
    print("\n11. Testing matrix merging...")
    matrix1 = CompatibilityMatrixGenerator.generate_from_results(
        [create_test_result('t1', TestStatus.PASSED, configs[0])],
        [configs[0]]
    )
    
    matrix2 = CompatibilityMatrixGenerator.generate_from_results(
        [create_test_result('t2', TestStatus.PASSED, configs[1])],
        [configs[1]]
    )
    
    merged = CompatibilityMatrixGenerator.merge_matrices([matrix1, matrix2])
    assert len(merged.cells) == 2
    print("   ✅ Matrix merging works")
    
    # Test 12: File export and import
    print("\n12. Testing file export and import...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Export to JSON
        json_path = tmpdir / "matrix.json"
        MatrixExporter.export_to_json(compat_matrix, json_path)
        assert json_path.exists()
        
        # Export to text
        text_path = tmpdir / "matrix.txt"
        MatrixExporter.export_to_text(compat_matrix, text_path)
        assert text_path.exists()
        
        # Export to HTML
        html_path = tmpdir / "matrix.html"
        MatrixExporter.export_to_html(compat_matrix, html_path)
        assert html_path.exists()
        
        # Export to CSV
        csv_path = tmpdir / "matrix.csv"
        MatrixExporter.export_to_csv(compat_matrix, csv_path)
        assert csv_path.exists()
        
        # Load from JSON
        loaded_matrix = MatrixExporter.load_from_json(json_path, results)
        assert len(loaded_matrix.cells) == len(compat_matrix.cells)
        
        print("   ✅ File export and import works")
    
    # Test 13: Architecture grouping
    print("\n13. Testing architecture grouping...")
    architectures = compat_matrix.get_architectures()
    assert len(architectures) == 3
    assert 'x86_64' in architectures
    assert 'arm64' in architectures
    assert 'riscv64' in architectures
    
    x86_cells = compat_matrix.get_cells_by_architecture('x86_64')
    assert len(x86_cells) == 1
    assert x86_cells[0].hardware_config.architecture == 'x86_64'
    print("   ✅ Architecture grouping works")
    
    # Test 14: Pass rate calculation
    print("\n14. Testing pass rate calculation...")
    overall_pass_rate = compat_matrix.get_overall_pass_rate()
    assert 0.0 <= overall_pass_rate <= 1.0
    
    # Calculate manually
    total_tests = sum(cell.total_count for cell in compat_matrix.cells)
    total_passed = sum(cell.pass_count for cell in compat_matrix.cells)
    expected_rate = total_passed / total_tests if total_tests > 0 else 0.0
    assert abs(overall_pass_rate - expected_rate) < 0.001
    print("   ✅ Pass rate calculation is correct")
    
    # Test 15: Matrix cell retrieval
    print("\n15. Testing matrix cell retrieval...")
    cell = compat_matrix.get_cell_by_config(configs[0])
    assert cell is not None
    assert cell.hardware_config.architecture == configs[0].architecture
    assert cell.hardware_config.cpu_model == configs[0].cpu_model
    print("   ✅ Cell retrieval works")
    
    print("\n" + "=" * 70)
    print("✅ ALL VERIFICATION TESTS PASSED!")
    print("=" * 70)
    print("\nTask 10 implementation is complete and verified:")
    print("  ✓ Matrix data structure for hardware configurations")
    print("  ✓ Matrix population from test results")
    print("  ✓ Matrix visualization (text, HTML, CSV)")
    print("  ✓ Matrix export to multiple formats")
    print("  ✓ Completeness property validation")
    print("  ✓ Status accuracy and aggregation")
    print("  ✓ Architecture grouping")
    print("  ✓ Pass rate calculation")
    print("\nRequirements validated:")
    print("  ✓ 2.4: Compatibility matrix with pass/fail status for all configs")
    print("=" * 70)


if __name__ == '__main__':
    try:
        verify_implementation()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
