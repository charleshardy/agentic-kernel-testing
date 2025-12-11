#!/usr/bin/env python3
"""Simple test script for fault injection system."""

from execution.fault_injection import (
    FaultInjectionSystem,
    FaultInjectionConfig,
    FaultType
)

def test_basic_functionality():
    """Test basic fault injection functionality."""
    print("Testing fault injection system...")
    
    # Test 1: All three fault types
    config = FaultInjectionConfig(
        enabled_fault_types=[
            FaultType.MEMORY_ALLOCATION_FAILURE,
            FaultType.IO_ERROR,
            FaultType.TIMING_VARIATION
        ],
        memory_failure_rate=0.5,
        io_error_rate=0.5,
        timing_variation_range_ms=(0, 1),
        seed=42
    )
    
    system = FaultInjectionSystem(config)
    
    # Check all injectors are initialized
    assert system.memory_injector is not None, "Memory injector should be initialized"
    assert system.io_injector is not None, "I/O injector should be initialized"
    assert system.timing_injector is not None, "Timing injector should be initialized"
    
    print("✓ All injectors initialized correctly")
    
    # Check enabled types
    enabled = system.get_enabled_fault_types()
    assert len(enabled) == 3, f"Expected 3 enabled types, got {len(enabled)}"
    assert FaultType.MEMORY_ALLOCATION_FAILURE in enabled
    assert FaultType.IO_ERROR in enabled
    assert FaultType.TIMING_VARIATION in enabled
    
    print("✓ All fault types enabled correctly")
    
    # Test injections
    mem_result = system.inject_memory_failure("test")
    print(f"  Memory injection: {type(mem_result).__name__ if mem_result else 'None'}")
    
    io_result = system.inject_io_error("test", "read")
    print(f"  I/O injection: {type(io_result).__name__ if io_result else 'None'}")
    
    timing_result = system.inject_timing_variation("test")
    print(f"  Timing injection: {timing_result:.6f}s")
    
    print("✓ All injection methods work")
    
    # Test statistics
    stats = system.get_all_statistics()
    assert "enabled_fault_types" in stats
    assert len(stats["enabled_fault_types"]) == 3
    
    print("✓ Statistics collection works")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_basic_functionality()
