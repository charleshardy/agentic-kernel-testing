"""Example demonstrating kernel fuzzing system usage.

This example shows how to:
1. Generate fuzzing strategies for different targets
2. Start fuzzing campaigns
3. Detect and minimize crashes
4. Generate fuzzing reports
"""

from execution.kernel_fuzzer import (
    KernelFuzzer,
    FuzzingStrategyGenerator,
    CrashInfo,
    CrashSeverity,
    CrashDetector,
    CrashMinimizer
)


def example_generate_fuzzing_strategies():
    """Example: Generate fuzzing strategies for different targets."""
    print("=" * 60)
    print("Example 1: Generating Fuzzing Strategies")
    print("=" * 60)
    
    generator = FuzzingStrategyGenerator()
    
    # Generate syscall fuzzing strategy
    syscall_strategy = generator.generate_syscall_strategy("filesystem")
    print(f"\n1. Syscall Fuzzing Strategy:")
    print(f"   Target: {syscall_strategy.target_name}")
    print(f"   Type: {syscall_strategy.target_type.value}")
    print(f"   Syscalls: {', '.join(syscall_strategy.syscalls[:5])}...")
    print(f"   Coverage enabled: {syscall_strategy.enable_coverage}")
    
    # Generate ioctl fuzzing strategy
    ioctl_strategy = generator.generate_ioctl_strategy("/dev/null")
    print(f"\n2. Ioctl Fuzzing Strategy:")
    print(f"   Target: {ioctl_strategy.target_name}")
    print(f"   Type: {ioctl_strategy.target_type.value}")
    print(f"   Syscalls: {', '.join(ioctl_strategy.syscalls)}")
    print(f"   Device: {ioctl_strategy.metadata['device_path']}")
    
    # Generate network protocol fuzzing strategy
    network_strategy = generator.generate_network_protocol_strategy("tcp")
    print(f"\n3. Network Protocol Fuzzing Strategy:")
    print(f"   Target: {network_strategy.target_name}")
    print(f"   Type: {network_strategy.target_type.value}")
    print(f"   Syscalls: {', '.join(network_strategy.syscalls[:5])}...")
    print(f"   Protocol: {network_strategy.metadata['protocol']}")
    
    # Generate filesystem fuzzing strategy
    fs_strategy = generator.generate_filesystem_strategy("ext4")
    print(f"\n4. Filesystem Fuzzing Strategy:")
    print(f"   Target: {fs_strategy.target_name}")
    print(f"   Type: {fs_strategy.target_type.value}")
    print(f"   Syscalls: {', '.join(fs_strategy.syscalls[:5])}...")
    print(f"   Filesystem: {fs_strategy.metadata['filesystem_type']}")


def example_crash_detection():
    """Example: Detect crashes from kernel logs."""
    print("\n" + "=" * 60)
    print("Example 2: Crash Detection")
    print("=" * 60)
    
    detector = CrashDetector()
    
    # Example crash logs
    crash_logs = [
        {
            "name": "Kernel BUG",
            "log": "kernel BUG at fs/ext4/inode.c:123\nCall Trace:\n [<ffffffff>] ext4_write_begin+0x123"
        },
        {
            "name": "KASAN Use-After-Free",
            "log": "KASAN: use-after-free in kmalloc+0x234\nRead of size 8 at addr ffff8880"
        },
        {
            "name": "General Protection Fault",
            "log": "general protection fault: 0000 [#1] SMP\nRIP: 0010:some_function+0x45"
        },
        {
            "name": "NULL Pointer Dereference",
            "log": "unable to handle kernel NULL pointer dereference at 0000000000000000"
        }
    ]
    
    for crash_log in crash_logs:
        detection = detector.detect_crash(crash_log["log"])
        if detection:
            print(f"\n{crash_log['name']}:")
            print(f"   Crash Type: {detection['crash_type']}")
            print(f"   Severity: {detection['severity'].value}")
            print(f"   Pattern: {detection['pattern_matched']}")


def example_crash_minimization():
    """Example: Minimize crash reproducers."""
    print("\n" + "=" * 60)
    print("Example 3: Crash Input Minimization")
    print("=" * 60)
    
    minimizer = CrashMinimizer()
    
    # Original reproducer with unnecessary lines
    original_reproducer = """
open("/dev/test", O_RDWR)
write(fd, buffer, 1024)
ioctl(fd, CMD_1, arg1)
ioctl(fd, CMD_2, arg2)
ioctl(fd, CMD_3, arg3)
read(fd, buffer, 512)
close(fd)
"""
    
    print(f"\nOriginal Reproducer ({len(original_reproducer)} bytes):")
    print(original_reproducer)
    
    # Validator: crash only happens with CMD_2
    def crashes_with_cmd2(input_str):
        return "CMD_2" in input_str
    
    # Minimize
    minimized = minimizer.minimize_reproducer(original_reproducer, crashes_with_cmd2)
    
    print(f"\nMinimized Reproducer ({len(minimized)} bytes):")
    print(minimized)
    print(f"\nReduction: {len(original_reproducer) - len(minimized)} bytes")


def example_crash_info_management():
    """Example: Manage crash information."""
    print("\n" + "=" * 60)
    print("Example 4: Crash Information Management")
    print("=" * 60)
    
    # Create crash info
    crash = CrashInfo(
        crash_id="crash_001",
        title="Use-after-free in ext4_write_begin",
        severity=CrashSeverity.CRITICAL,
        crash_type="kasan",
        reproducer="open('/test', O_RDWR)\nwrite(fd, data, 1024)",
        crash_log="KASAN: use-after-free in ext4_write_begin+0x123",
        stack_trace="Call Trace:\n [<ffffffff>] ext4_write_begin+0x123",
        affected_function="ext4_write_begin"
    )
    
    print(f"\nCrash Information:")
    print(f"   ID: {crash.crash_id}")
    print(f"   Title: {crash.title}")
    print(f"   Severity: {crash.severity.value}")
    print(f"   Type: {crash.crash_type}")
    print(f"   Affected Function: {crash.affected_function}")
    print(f"   Has Reproducer: {crash.reproducer is not None}")
    
    # Serialize to dict
    crash_dict = crash.to_dict()
    print(f"\n   Serialized Keys: {', '.join(crash_dict.keys())}")


def example_fuzzer_statistics():
    """Example: Get fuzzer statistics."""
    print("\n" + "=" * 60)
    print("Example 5: Fuzzer Statistics")
    print("=" * 60)
    
    fuzzer = KernelFuzzer()
    
    # Get statistics
    stats = fuzzer.get_statistics()
    
    print(f"\nFuzzer Statistics:")
    print(f"   Total Campaigns: {stats['total_campaigns']}")
    print(f"   Completed Campaigns: {stats['completed_campaigns']}")
    print(f"   Running Campaigns: {stats['running_campaigns']}")
    print(f"   Total Crashes Found: {stats['total_crashes_found']}")
    print(f"   Total Executions: {stats['total_executions']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Kernel Fuzzing System Examples")
    print("=" * 60)
    
    try:
        example_generate_fuzzing_strategies()
        example_crash_detection()
        example_crash_minimization()
        example_crash_info_management()
        example_fuzzer_statistics()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
