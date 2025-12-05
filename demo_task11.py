#!/usr/bin/env python3
"""Demo script for Task 11: Fault Injection System.

This script demonstrates the fault injection system capabilities:
- Memory allocation failure injection
- I/O error injection
- Timing variation injection
- Fault injection configuration and control
"""

from execution.fault_injection import (
    FaultInjectionSystem,
    FaultInjectionConfig,
    FaultType
)


def demo_memory_injection():
    """Demonstrate memory allocation failure injection."""
    print("\n" + "="*70)
    print("DEMO 1: Memory Allocation Failure Injection")
    print("="*70)
    
    config = FaultInjectionConfig(
        enabled_fault_types=[FaultType.MEMORY_ALLOCATION_FAILURE],
        memory_failure_rate=0.3,  # 30% failure rate
        seed=42
    )
    
    system = FaultInjectionSystem(config)
    
    print(f"Configuration: {config.memory_failure_rate*100}% failure rate")
    print("\nAttempting 10 memory allocations:")
    
    failures = 0
    for i in range(10):
        error = system.inject_memory_failure(f"allocation_{i}")
        if error:
            print(f"  [{i+1}] ❌ FAILED: {error}")
            failures += 1
        else:
            print(f"  [{i+1}] ✓ Success")
    
    print(f"\nResult: {failures}/10 allocations failed")
    print(f"Statistics: {system.memory_injector.get_statistics()}")


def demo_io_injection():
    """Demonstrate I/O error injection."""
    print("\n" + "="*70)
    print("DEMO 2: I/O Error Injection")
    print("="*70)
    
    config = FaultInjectionConfig(
        enabled_fault_types=[FaultType.IO_ERROR],
        io_error_rate=0.25,  # 25% error rate
        seed=123
    )
    
    system = FaultInjectionSystem(config)
    
    print(f"Configuration: {config.io_error_rate*100}% error rate")
    print("\nAttempting 10 I/O operations:")
    
    operations = ["read", "write", "open", "close"]
    errors = 0
    
    for i in range(10):
        op = operations[i % len(operations)]
        error = system.inject_io_error(f"file_{i}.txt", op)
        if error:
            print(f"  [{i+1}] ❌ {op.upper()} FAILED: {error}")
            errors += 1
        else:
            print(f"  [{i+1}] ✓ {op.upper()} Success")
    
    print(f"\nResult: {errors}/10 operations failed")
    print(f"Statistics: {system.io_injector.get_statistics()}")


def demo_timing_injection():
    """Demonstrate timing variation injection."""
    print("\n" + "="*70)
    print("DEMO 3: Timing Variation Injection")
    print("="*70)
    
    config = FaultInjectionConfig(
        enabled_fault_types=[FaultType.TIMING_VARIATION],
        timing_variation_range_ms=(10, 50),  # 10-50ms delays
        seed=456
    )
    
    system = FaultInjectionSystem(config)
    
    print(f"Configuration: {config.timing_variation_range_ms[0]}-{config.timing_variation_range_ms[1]}ms delay range")
    print("\nInjecting timing variations:")
    
    total_delay = 0.0
    for i in range(5):
        delay = system.inject_timing_variation(f"operation_{i}")
        delay_ms = delay * 1000
        total_delay += delay
        print(f"  [{i+1}] Injected {delay_ms:.2f}ms delay")
    
    print(f"\nTotal delay: {total_delay*1000:.2f}ms")
    print(f"Statistics: {system.timing_injector.get_statistics()}")


def demo_combined_injection():
    """Demonstrate all fault types together."""
    print("\n" + "="*70)
    print("DEMO 4: Combined Fault Injection (All Types)")
    print("="*70)
    
    config = FaultInjectionConfig(
        enabled_fault_types=[
            FaultType.MEMORY_ALLOCATION_FAILURE,
            FaultType.IO_ERROR,
            FaultType.TIMING_VARIATION
        ],
        memory_failure_rate=0.2,
        io_error_rate=0.2,
        timing_variation_range_ms=(5, 20),
        seed=789
    )
    
    system = FaultInjectionSystem(config)
    
    print("Configuration: All three fault types enabled")
    print(f"  - Memory failure rate: {config.memory_failure_rate*100}%")
    print(f"  - I/O error rate: {config.io_error_rate*100}%")
    print(f"  - Timing variation: {config.timing_variation_range_ms[0]}-{config.timing_variation_range_ms[1]}ms")
    
    print("\nSimulating a complex operation with multiple fault points:")
    
    # Simulate a complex operation
    print("\n  Step 1: Allocate memory")
    mem_error = system.inject_memory_failure("buffer_allocation")
    if mem_error:
        print(f"    ❌ {mem_error}")
    else:
        print("    ✓ Memory allocated")
    
    print("\n  Step 2: Open file")
    io_error = system.inject_io_error("data.bin", "open")
    if io_error:
        print(f"    ❌ {io_error}")
    else:
        print("    ✓ File opened")
    
    print("\n  Step 3: Process data (with timing variation)")
    delay = system.inject_timing_variation("data_processing")
    print(f"    ⏱ Processing took {delay*1000:.2f}ms")
    
    print("\n  Step 4: Write results")
    io_error = system.inject_io_error("results.bin", "write")
    if io_error:
        print(f"    ❌ {io_error}")
    else:
        print("    ✓ Results written")
    
    # Show overall statistics
    print("\n" + "-"*70)
    print("Overall Statistics:")
    stats = system.get_all_statistics()
    print(f"  Enabled fault types: {', '.join(stats['enabled_fault_types'])}")
    for injector_name, injector_stats in stats['injectors'].items():
        print(f"  {injector_name.capitalize()}: {injector_stats['injection_count']} injections")


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("FAULT INJECTION SYSTEM DEMONSTRATION")
    print("Task 11: Implement fault injection system")
    print("="*70)
    
    demo_memory_injection()
    demo_io_injection()
    demo_timing_injection()
    demo_combined_injection()
    
    print("\n" + "="*70)
    print("✅ All demonstrations completed successfully!")
    print("="*70)
    print("\nThe fault injection system provides:")
    print("  ✓ Memory allocation failure injection")
    print("  ✓ I/O error injection")
    print("  ✓ Timing variation injection")
    print("  ✓ Configurable injection rates and parameters")
    print("  ✓ Statistics tracking for all fault types")
    print("  ✓ Reproducible behavior with seed control")
    print()


if __name__ == "__main__":
    main()
