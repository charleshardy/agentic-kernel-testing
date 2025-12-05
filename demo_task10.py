#!/usr/bin/env python3
"""Demo script for Task 10: Compatibility Matrix Generator."""

import sys
sys.path.insert(0, '.')

from analysis.compatibility_matrix import (
    CompatibilityMatrixGenerator, MatrixVisualizer, MatrixExporter
)
from execution.hardware_config import TestMatrix
from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle, FailureInfo
)
from datetime import datetime
from pathlib import Path


def create_demo_config(arch, cpu, memory, is_virtual):
    """Create a demo hardware configuration."""
    return HardwareConfig(
        architecture=arch,
        cpu_model=cpu,
        memory_mb=memory,
        storage_type='ssd',
        peripherals=[],
        is_virtual=is_virtual,
        emulator='qemu' if is_virtual else None
    )


def create_demo_result(test_id, status, config):
    """Create a demo test result."""
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


def main():
    """Run compatibility matrix demo."""
    print("=" * 80)
    print("COMPATIBILITY MATRIX GENERATOR DEMO")
    print("=" * 80)
    
    # Create a diverse set of hardware configurations
    print("\n1. Creating test matrix with 6 hardware configurations...")
    configs = [
        create_demo_config('x86_64', 'Intel Core i7-9700K', 8192, True),
        create_demo_config('x86_64', 'AMD Ryzen 9 5900X', 16384, True),
        create_demo_config('arm64', 'ARM Cortex-A72', 4096, True),
        create_demo_config('arm64', 'ARM Cortex-A76', 4096, False),
        create_demo_config('arm', 'ARM Cortex-A53', 2048, False),
        create_demo_config('riscv64', 'SiFive U74', 2048, True),
    ]
    
    test_matrix = TestMatrix(configurations=configs)
    print(f"   Created test matrix with {len(test_matrix)} configurations")
    print(f"   - Virtual configs: {len(test_matrix.get_virtual_configs())}")
    print(f"   - Physical configs: {len(test_matrix.get_physical_configs())}")
    
    # Create test results with various outcomes
    print("\n2. Generating test results...")
    results = [
        # x86_64 Intel - all pass
        create_demo_result('test_001', TestStatus.PASSED, configs[0]),
        create_demo_result('test_002', TestStatus.PASSED, configs[0]),
        create_demo_result('test_003', TestStatus.PASSED, configs[0]),
        
        # x86_64 AMD - mixed results
        create_demo_result('test_004', TestStatus.PASSED, configs[1]),
        create_demo_result('test_005', TestStatus.FAILED, configs[1]),
        create_demo_result('test_006', TestStatus.PASSED, configs[1]),
        create_demo_result('test_007', TestStatus.PASSED, configs[1]),
        
        # arm64 A72 - mostly pass
        create_demo_result('test_008', TestStatus.PASSED, configs[2]),
        create_demo_result('test_009', TestStatus.PASSED, configs[2]),
        create_demo_result('test_010', TestStatus.FAILED, configs[2]),
        
        # arm64 A76 - all fail
        create_demo_result('test_011', TestStatus.FAILED, configs[3]),
        create_demo_result('test_012', TestStatus.FAILED, configs[3]),
        
        # arm A53 - single pass
        create_demo_result('test_013', TestStatus.PASSED, configs[4]),
        
        # riscv64 - not tested (no results)
    ]
    
    print(f"   Generated {len(results)} test results")
    
    # Generate compatibility matrix
    print("\n3. Generating compatibility matrix...")
    compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
        results,
        hardware_configs=test_matrix.configurations
    )
    
    print(f"   Matrix contains {len(compat_matrix.cells)} cells")
    
    # Display summary
    print("\n4. Matrix Summary:")
    summary = compat_matrix.get_summary()
    print(f"   Total Configurations: {summary['total_configurations']}")
    print(f"   Architectures: {', '.join(summary['architectures'])}")
    print(f"   Overall Pass Rate: {summary['overall_pass_rate']:.1%}")
    print(f"   Passed Configs: {summary['passed_configs']}")
    print(f"   Failed Configs: {summary['failed_configs']}")
    print(f"   Mixed Configs: {summary['mixed_configs']}")
    print(f"   Not Tested Configs: {summary['not_tested_configs']}")
    
    # Display text visualization
    print("\n5. Text Visualization:")
    print(MatrixVisualizer.to_text_table(compat_matrix))
    
    # Export to files
    print("\n6. Exporting to files...")
    output_dir = Path("matrix_output")
    output_dir.mkdir(exist_ok=True)
    
    MatrixExporter.export_to_text(compat_matrix, output_dir / "matrix.txt")
    print(f"   ✓ Exported to {output_dir / 'matrix.txt'}")
    
    MatrixExporter.export_to_html(compat_matrix, output_dir / "matrix.html")
    print(f"   ✓ Exported to {output_dir / 'matrix.html'}")
    
    MatrixExporter.export_to_csv(compat_matrix, output_dir / "matrix.csv")
    print(f"   ✓ Exported to {output_dir / 'matrix.csv'}")
    
    MatrixExporter.export_to_json(compat_matrix, output_dir / "matrix.json")
    print(f"   ✓ Exported to {output_dir / 'matrix.json'}")
    
    # Demonstrate incremental update
    print("\n7. Demonstrating incremental update...")
    print("   Adding 3 new test results...")
    new_results = [
        create_demo_result('test_014', TestStatus.PASSED, configs[0]),
        create_demo_result('test_015', TestStatus.PASSED, configs[5]),  # First test for riscv64
        create_demo_result('test_016', TestStatus.FAILED, configs[5]),
    ]
    
    compat_matrix = CompatibilityMatrixGenerator.populate_matrix(
        compat_matrix,
        new_results
    )
    
    print(f"   Matrix now has {sum(c.total_count for c in compat_matrix.cells)} total test results")
    
    # Show updated summary
    summary = compat_matrix.get_summary()
    print(f"   Updated pass rate: {summary['overall_pass_rate']:.1%}")
    print(f"   Not tested configs: {summary['not_tested_configs']}")
    
    # Demonstrate filtering
    print("\n8. Demonstrating filtering capabilities...")
    
    from analysis.compatibility_matrix import MatrixCellStatus
    
    passed_cells = compat_matrix.get_cells_by_status(MatrixCellStatus.PASSED)
    print(f"   Configurations with all tests passed: {len(passed_cells)}")
    for cell in passed_cells:
        print(f"     - {cell.hardware_config.architecture} / {cell.hardware_config.cpu_model}")
    
    failed_cells = compat_matrix.get_cells_by_status(MatrixCellStatus.FAILED)
    print(f"   Configurations with all tests failed: {len(failed_cells)}")
    for cell in failed_cells:
        print(f"     - {cell.hardware_config.architecture} / {cell.hardware_config.cpu_model}")
    
    mixed_cells = compat_matrix.get_cells_by_status(MatrixCellStatus.MIXED)
    print(f"   Configurations with mixed results: {len(mixed_cells)}")
    for cell in mixed_cells:
        print(f"     - {cell.hardware_config.architecture} / {cell.hardware_config.cpu_model} ({cell.pass_rate:.0%} pass rate)")
    
    # Architecture-specific analysis
    print("\n9. Architecture-specific analysis...")
    for arch in sorted(compat_matrix.get_architectures()):
        cells = compat_matrix.get_cells_by_architecture(arch)
        total_tests = sum(c.total_count for c in cells)
        total_passed = sum(c.pass_count for c in cells)
        pass_rate = total_passed / total_tests if total_tests > 0 else 0.0
        
        print(f"   {arch}:")
        print(f"     Configurations: {len(cells)}")
        print(f"     Total tests: {total_tests}")
        print(f"     Pass rate: {pass_rate:.1%}")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Matrix generation from test results")
    print("  ✓ Completeness guarantee (all configs present)")
    print("  ✓ Status tracking (PASSED, FAILED, MIXED, NOT_TESTED)")
    print("  ✓ Multiple export formats (text, HTML, CSV, JSON)")
    print("  ✓ Incremental updates")
    print("  ✓ Filtering by status and architecture")
    print("  ✓ Summary statistics and pass rates")
    print("\nCheck the 'matrix_output' directory for exported files!")
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
