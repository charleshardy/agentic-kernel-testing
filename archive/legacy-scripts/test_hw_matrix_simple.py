#!/usr/bin/env python3
"""Simple test runner for hardware matrix coverage."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from execution.hardware_config import TestMatrixGenerator

# Test 1: Basic matrix generation
print("Test 1: Basic matrix generation...")
matrix = TestMatrixGenerator.generate_matrix(
    architectures=['x86_64', 'arm64'],
    memory_sizes=[2048, 4096],
    virtual_only=True
)

print(f"  Generated {len(matrix.configurations)} configurations")
assert len(matrix.configurations) == 4, f"Expected 4 configs, got {len(matrix.configurations)}"

# Check all architectures present
archs = {c.architecture for c in matrix.configurations}
assert archs == {'x86_64', 'arm64'}, f"Expected x86_64 and arm64, got {archs}"

# Check all memory sizes present
memory_sizes = {c.memory_mb for c in matrix.configurations}
assert memory_sizes == {2048, 4096}, f"Expected 2048 and 4096, got {memory_sizes}"

# Check all are virtual
assert all(c.is_virtual for c in matrix.configurations), "All should be virtual"

print("  ✅ PASSED")

# Test 2: Virtual and physical
print("\nTest 2: Virtual and physical configurations...")
matrix = TestMatrixGenerator.generate_matrix(
    architectures=['x86_64'],
    memory_sizes=[4096],
    virtual_only=False
)

print(f"  Generated {len(matrix.configurations)} configurations")
assert len(matrix.configurations) == 2, f"Expected 2 configs, got {len(matrix.configurations)}"

virtual_count = sum(1 for c in matrix.configurations if c.is_virtual)
physical_count = sum(1 for c in matrix.configurations if not c.is_virtual)

assert virtual_count == 1, f"Expected 1 virtual, got {virtual_count}"
assert physical_count == 1, f"Expected 1 physical, got {physical_count}"

print("  ✅ PASSED")

# Test 3: Matrix filtering
print("\nTest 3: Matrix filtering by architecture...")
matrix = TestMatrixGenerator.generate_matrix(
    architectures=['x86_64', 'arm64', 'riscv64'],
    memory_sizes=[2048],
    virtual_only=True
)

x86_configs = matrix.get_by_architecture('x86_64')
assert len(x86_configs) == 1, f"Expected 1 x86_64 config, got {len(x86_configs)}"
assert x86_configs[0].architecture == 'x86_64'

print("  ✅ PASSED")

# Test 4: Virtual/physical separation
print("\nTest 4: Virtual/physical separation...")
matrix = TestMatrixGenerator.generate_matrix(
    architectures=['x86_64', 'arm64'],
    memory_sizes=[2048, 4096],
    virtual_only=False
)

virtual_configs = matrix.get_virtual_configs()
physical_configs = matrix.get_physical_configs()

assert len(virtual_configs) + len(physical_configs) == len(matrix.configurations)
assert all(c.is_virtual for c in virtual_configs)
assert all(not c.is_virtual for c in physical_configs)

print("  ✅ PASSED")

# Test 5: Serialization
print("\nTest 5: Matrix serialization...")
matrix = TestMatrixGenerator.generate_matrix(
    architectures=['x86_64'],
    memory_sizes=[2048],
    virtual_only=True
)

matrix_dict = matrix.to_dict()
restored_matrix = TestMatrixGenerator.load_matrix_from_file.__self__.from_dict(matrix_dict)

assert len(restored_matrix.configurations) == len(matrix.configurations)
assert restored_matrix.configurations[0].architecture == matrix.configurations[0].architecture

print("  ✅ PASSED")

print("\n" + "=" * 70)
print("✅ ALL HARDWARE MATRIX COVERAGE TESTS PASSED!")
print("=" * 70)
