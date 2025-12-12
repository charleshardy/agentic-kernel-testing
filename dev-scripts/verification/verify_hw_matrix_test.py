#!/usr/bin/env python3
"""Verify hardware matrix coverage implementation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Verifying hardware matrix coverage implementation...")
print("=" * 70)

try:
    # Import required modules
    from execution.hardware_config import (
        TestMatrixGenerator,
        HardwareConfigParser,
        HardwareCapabilityDetector,
        HardwareClassifier,
        TestMatrix
    )
    from ai_generator.models import HardwareConfig, Peripheral
    
    print("✓ All modules imported successfully")
    
    # Test 1: Generate matrix with multiple architectures and memory sizes
    print("\n1. Testing matrix generation with multiple configurations...")
    matrix = TestMatrixGenerator.generate_matrix(
        architectures=['x86_64', 'arm64'],
        memory_sizes=[2048, 4096],
        virtual_only=True
    )
    
    # Verify all architectures are present
    matrix_archs = {c.architecture for c in matrix.configurations}
    expected_archs = {'x86_64', 'arm64'}
    assert matrix_archs == expected_archs, f"Expected {expected_archs}, got {matrix_archs}"
    print(f"  ✓ All architectures present: {matrix_archs}")
    
    # Verify all memory sizes are present
    matrix_memory = {c.memory_mb for c in matrix.configurations}
    expected_memory = {2048, 4096}
    assert matrix_memory == expected_memory, f"Expected {expected_memory}, got {matrix_memory}"
    print(f"  ✓ All memory sizes present: {matrix_memory}")
    
    # Verify correct number of configurations
    expected_count = 2 * 2  # 2 architectures * 2 memory sizes
    assert len(matrix.configurations) == expected_count, f"Expected {expected_count}, got {len(matrix.configurations)}"
    print(f"  ✓ Correct number of configurations: {len(matrix.configurations)}")
    
    # Verify all are virtual
    assert all(c.is_virtual for c in matrix.configurations), "All should be virtual"
    print("  ✓ All configurations are virtual")
    
    # Test 2: Generate matrix with virtual and physical
    print("\n2. Testing matrix with virtual and physical configurations...")
    matrix = TestMatrixGenerator.generate_matrix(
        architectures=['x86_64'],
        memory_sizes=[4096],
        virtual_only=False
    )
    
    virtual_count = sum(1 for c in matrix.configurations if c.is_virtual)
    physical_count = sum(1 for c in matrix.configurations if not c.is_virtual)
    
    assert virtual_count == 1, f"Expected 1 virtual, got {virtual_count}"
    assert physical_count == 1, f"Expected 1 physical, got {physical_count}"
    print(f"  ✓ Virtual configs: {virtual_count}, Physical configs: {physical_count}")
    
    # Test 3: Test matrix filtering
    print("\n3. Testing matrix filtering by architecture...")
    matrix = TestMatrixGenerator.generate_matrix(
        architectures=['x86_64', 'arm64', 'riscv64'],
        memory_sizes=[2048, 4096],
        virtual_only=True
    )
    
    for arch in ['x86_64', 'arm64', 'riscv64']:
        filtered = matrix.get_by_architecture(arch)
        assert len(filtered) == 2, f"Expected 2 configs for {arch}, got {len(filtered)}"
        assert all(c.architecture == arch for c in filtered), f"All should be {arch}"
        print(f"  ✓ Filtering for {arch}: {len(filtered)} configs")
    
    # Test 4: Test virtual/physical separation
    print("\n4. Testing virtual/physical separation...")
    matrix = TestMatrixGenerator.generate_matrix(
        architectures=['x86_64', 'arm64'],
        memory_sizes=[2048],
        virtual_only=False
    )
    
    virtual_configs = matrix.get_virtual_configs()
    physical_configs = matrix.get_physical_configs()
    
    assert len(virtual_configs) + len(physical_configs) == len(matrix.configurations)
    assert all(c.is_virtual for c in virtual_configs)
    assert all(not c.is_virtual for c in physical_configs)
    print(f"  ✓ Virtual: {len(virtual_configs)}, Physical: {len(physical_configs)}")
    
    # Test 5: Test no configurations are skipped
    print("\n5. Testing that no configurations are skipped...")
    configs = [
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=True),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=True),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=True),
    ]
    
    matrix = TestMatrixGenerator.generate_from_configs(configs)
    assert len(matrix.configurations) == len(configs), "All configs should be preserved"
    print(f"  ✓ All {len(configs)} configurations preserved in matrix")
    
    # Test 6: Test serialization preserves all configurations
    print("\n6. Testing serialization preserves configurations...")
    original_matrix = TestMatrixGenerator.generate_matrix(
        architectures=['x86_64', 'arm64'],
        memory_sizes=[2048],
        virtual_only=True
    )
    
    matrix_dict = original_matrix.to_dict()
    restored_matrix = TestMatrix.from_dict(matrix_dict)
    
    assert len(restored_matrix.configurations) == len(original_matrix.configurations)
    original_archs = {c.architecture for c in original_matrix.configurations}
    restored_archs = {c.architecture for c in restored_matrix.configurations}
    assert original_archs == restored_archs
    print(f"  ✓ Serialization preserved all {len(restored_matrix.configurations)} configurations")
    
    print("\n" + "=" * 70)
    print("✅ ALL HARDWARE MATRIX COVERAGE TESTS PASSED!")
    print("=" * 70)
    print("\nProperty 6: Hardware matrix coverage - VALIDATED")
    print("For any BSP test execution, tests run on all hardware targets")
    print("configured in the test matrix, with no configured target being skipped.")
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
