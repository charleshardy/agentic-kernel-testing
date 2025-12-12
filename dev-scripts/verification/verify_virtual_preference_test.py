#!/usr/bin/env python3
"""Verify virtual environment preference implementation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Verifying virtual environment preference implementation...")
print("=" * 70)

try:
    # Import required modules
    from execution.hardware_config import (
        HardwareClassifier,
        TestMatrixGenerator
    )
    from ai_generator.models import HardwareConfig
    
    print("✓ All modules imported successfully")
    
    # Test 1: Virtual configs come before physical in sorting
    print("\n1. Testing virtual preference in sorting...")
    configs = [
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=False),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=True),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=False),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=True),
    ]
    
    sorted_configs = HardwareClassifier.prefer_virtual(configs)
    
    # Check that first two are virtual
    assert sorted_configs[0].is_virtual, "First config should be virtual"
    assert sorted_configs[1].is_virtual, "Second config should be virtual"
    # Check that last two are physical
    assert not sorted_configs[2].is_virtual, "Third config should be physical"
    assert not sorted_configs[3].is_virtual, "Fourth config should be physical"
    
    print("  ✓ Virtual configs sorted before physical configs")
    
    # Test 2: Virtual preferred for equivalent configs
    print("\n2. Testing virtual preference for equivalent configs...")
    virtual_config = HardwareConfig(
        architecture='x86_64',
        cpu_model='Intel Core i7',
        memory_mb=4096,
        is_virtual=True,
        emulator='qemu'
    )
    
    physical_config = HardwareConfig(
        architecture='x86_64',
        cpu_model='Intel Core i7',
        memory_mb=4096,
        is_virtual=False
    )
    
    # Put physical first intentionally
    configs = [physical_config, virtual_config]
    sorted_configs = HardwareClassifier.prefer_virtual(configs)
    
    assert sorted_configs[0].is_virtual, "Virtual should be first"
    assert not sorted_configs[1].is_virtual, "Physical should be second"
    
    print("  ✓ Virtual config preferred over equivalent physical config")
    
    # Test 3: Architecture filtering preserves virtual preference
    print("\n3. Testing virtual preference with architecture filtering...")
    configs = [
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=False),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=True),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=False),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=True),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=False),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=True),
    ]
    
    x86_sorted = HardwareClassifier.prefer_virtual(configs, architecture='x86_64')
    
    # Should have 4 x86_64 configs
    assert len(x86_sorted) == 4, f"Expected 4 x86_64 configs, got {len(x86_sorted)}"
    
    # First two should be virtual
    assert x86_sorted[0].is_virtual, "First x86_64 config should be virtual"
    assert x86_sorted[1].is_virtual, "Second x86_64 config should be virtual"
    
    # Last two should be physical
    assert not x86_sorted[2].is_virtual, "Third x86_64 config should be physical"
    assert not x86_sorted[3].is_virtual, "Fourth x86_64 config should be physical"
    
    print("  ✓ Architecture filtering preserves virtual preference")
    
    # Test 4: Sorting is deterministic
    print("\n4. Testing that sorting is deterministic...")
    configs = [
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=False),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=True),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=4096, is_virtual=False),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=4096, is_virtual=True),
    ]
    
    sorted_1 = HardwareClassifier.prefer_virtual(configs)
    sorted_2 = HardwareClassifier.prefer_virtual(configs)
    
    # Check that both sorts produce the same order
    for i, (c1, c2) in enumerate(zip(sorted_1, sorted_2)):
        assert c1.architecture == c2.architecture, f"Config {i}: architectures should match"
        assert c1.memory_mb == c2.memory_mb, f"Config {i}: memory should match"
        assert c1.is_virtual == c2.is_virtual, f"Config {i}: virtual status should match"
    
    print("  ✓ Sorting is deterministic")
    
    # Test 5: Matrix generation with virtual preference
    print("\n5. Testing matrix generation respects virtual preference...")
    matrix = TestMatrixGenerator.generate_matrix(
        architectures=['x86_64', 'arm64'],
        memory_sizes=[2048, 4096],
        virtual_only=False
    )
    
    virtual_configs = matrix.get_virtual_configs()
    physical_configs = matrix.get_physical_configs()
    
    assert len(virtual_configs) > 0, "Should have virtual configs"
    assert len(physical_configs) > 0, "Should have physical configs"
    
    # When sorted, virtual should come first
    sorted_matrix = HardwareClassifier.prefer_virtual(matrix.configurations)
    
    # Count virtual configs
    virtual_count = len(virtual_configs)
    
    # First N configs should be virtual
    for i in range(virtual_count):
        assert sorted_matrix[i].is_virtual, f"Config {i} should be virtual"
    
    # Remaining configs should be physical
    for i in range(virtual_count, len(sorted_matrix)):
        assert not sorted_matrix[i].is_virtual, f"Config {i} should be physical"
    
    print("  ✓ Matrix generation respects virtual preference")
    
    # Test 6: Finding equivalent configs
    print("\n6. Testing identification of equivalent configs...")
    ref_config = HardwareConfig(
        architecture='x86_64',
        cpu_model='Intel',
        memory_mb=4096,
        is_virtual=True
    )
    
    all_configs = [
        ref_config,
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=False),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=True),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=4096, is_virtual=True),
    ]
    
    equivalents = HardwareClassifier.get_equivalent_configs(ref_config, all_configs)
    
    # Should find the physical config with same arch and memory
    assert len(equivalents) == 1, f"Expected 1 equivalent, got {len(equivalents)}"
    assert equivalents[0].architecture == 'x86_64'
    assert equivalents[0].memory_mb == 4096
    assert not equivalents[0].is_virtual
    
    print("  ✓ Equivalent configs correctly identified")
    
    # Test 7: No configs are lost during sorting
    print("\n7. Testing that no configs are lost during sorting...")
    configs = [
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=True),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=2048, is_virtual=False),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=True),
        HardwareConfig(architecture='x86_64', cpu_model='Intel', memory_mb=4096, is_virtual=False),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=True),
        HardwareConfig(architecture='arm64', cpu_model='ARM', memory_mb=2048, is_virtual=False),
    ]
    
    sorted_configs = HardwareClassifier.prefer_virtual(configs)
    
    assert len(sorted_configs) == len(configs), "All configs should be preserved"
    
    # Count virtual and physical in both
    original_virtual = sum(1 for c in configs if c.is_virtual)
    sorted_virtual = sum(1 for c in sorted_configs if c.is_virtual)
    
    assert original_virtual == sorted_virtual, "Virtual count should be preserved"
    
    print("  ✓ All configs preserved during sorting")
    
    print("\n" + "=" * 70)
    print("✅ ALL VIRTUAL ENVIRONMENT PREFERENCE TESTS PASSED!")
    print("=" * 70)
    print("\nProperty 10: Virtual environment preference - VALIDATED")
    print("For any test that can run on both virtual and physical hardware,")
    print("the system executes on virtual hardware first when both are available.")
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
