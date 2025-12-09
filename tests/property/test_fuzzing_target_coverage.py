"""Property-based tests for fuzzing target coverage.

**Feature: agentic-kernel-testing, Property 31: Fuzzing target coverage**

This test validates Requirements 7.1:
WHEN security testing is enabled, THE Testing System SHALL perform fuzzing on 
system call interfaces, ioctl handlers, and network protocol parsers.
"""

import pytest
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from execution.kernel_fuzzer import (
    KernelFuzzer,
    FuzzingStrategyGenerator,
    FuzzingTarget,
    FuzzingStrategy,
    FuzzingCampaign
)


# Strategies for generating fuzzing configurations

@st.composite
def fuzzing_target_type(draw):
    """Generate a fuzzing target type."""
    return draw(st.sampled_from([
        FuzzingTarget.SYSCALL,
        FuzzingTarget.IOCTL,
        FuzzingTarget.NETWORK
    ]))


@st.composite
def syscall_group(draw):
    """Generate a syscall group name."""
    return draw(st.sampled_from([
        "filesystem",
        "network",
        "process",
        "memory",
        "ipc",
        "all"
    ]))


@st.composite
def network_protocol(draw):
    """Generate a network protocol name."""
    return draw(st.sampled_from([
        "tcp",
        "udp",
        "icmp",
        "raw",
        "sctp"
    ]))


@st.composite
def device_path(draw):
    """Generate a device path."""
    devices = [
        "/dev/null",
        "/dev/zero",
        "/dev/random",
        "/dev/urandom",
        "/dev/tty",
        "/dev/console"
    ]
    return draw(st.sampled_from(devices))


# Property 31: Fuzzing target coverage
# For any security testing execution, fuzzing should be performed on 
# system call interfaces, ioctl handlers, and network protocol parsers.

@given(group=syscall_group())
@settings(max_examples=100, deadline=None)
def test_syscall_fuzzing_coverage(group):
    """Property: Syscall fuzzing strategies should target system call interfaces.
    
    **Validates: Requirements 7.1**
    """
    generator = FuzzingStrategyGenerator()
    
    # Generate syscall fuzzing strategy
    strategy = generator.generate_syscall_strategy(group)
    
    # Property: Strategy should target syscalls
    assert strategy.target_type == FuzzingTarget.SYSCALL
    assert strategy.target_name.startswith("syscall_")
    
    # Property: Strategy should include syscalls
    assert len(strategy.syscalls) > 0, \
        "Syscall fuzzing strategy must include syscalls"
    
    # Property: All syscalls should be valid strings
    for syscall in strategy.syscalls:
        assert isinstance(syscall, str)
        assert len(syscall) > 0
    
    # Property: Coverage should be enabled for syscall fuzzing
    assert strategy.enable_coverage is True
    
    # Property: Strategy should have reasonable execution time
    assert strategy.max_execution_time > 0
    assert strategy.max_execution_time <= 86400  # Max 24 hours


@given(device=device_path())
@settings(max_examples=100, deadline=None)
def test_ioctl_fuzzing_coverage(device):
    """Property: Ioctl fuzzing strategies should target ioctl handlers.
    
    **Validates: Requirements 7.1**
    """
    generator = FuzzingStrategyGenerator()
    
    # Generate ioctl fuzzing strategy
    strategy = generator.generate_ioctl_strategy(device)
    
    # Property: Strategy should target ioctl
    assert strategy.target_type == FuzzingTarget.IOCTL
    assert "ioctl" in strategy.target_name.lower()
    
    # Property: Strategy should include ioctl syscall
    assert "ioctl" in strategy.syscalls, \
        "Ioctl fuzzing strategy must include ioctl syscall"
    
    # Property: Strategy should include open/close for device access
    assert "open" in strategy.syscalls
    assert "close" in strategy.syscalls
    
    # Property: Device path should be stored in metadata
    assert "device_path" in strategy.metadata
    assert strategy.metadata["device_path"] == device
    
    # Property: Coverage should be enabled
    assert strategy.enable_coverage is True


@given(protocol=network_protocol())
@settings(max_examples=100, deadline=None)
def test_network_protocol_fuzzing_coverage(protocol):
    """Property: Network fuzzing strategies should target protocol parsers.
    
    **Validates: Requirements 7.1**
    """
    generator = FuzzingStrategyGenerator()
    
    # Generate network protocol fuzzing strategy
    strategy = generator.generate_network_protocol_strategy(protocol)
    
    # Property: Strategy should target network
    assert strategy.target_type == FuzzingTarget.NETWORK
    assert "network" in strategy.target_name.lower()
    
    # Property: Strategy should include network syscalls
    network_syscalls = ["socket", "bind", "connect", "send", "recv"]
    for syscall in network_syscalls:
        assert syscall in strategy.syscalls, \
            f"Network fuzzing must include {syscall} syscall"
    
    # Property: Protocol should be stored in metadata
    assert "protocol" in strategy.metadata
    assert strategy.metadata["protocol"] == protocol
    
    # Property: Coverage should be enabled
    assert strategy.enable_coverage is True


@settings(max_examples=50, deadline=None)
def test_all_target_types_covered():
    """Property: System should support fuzzing all required target types.
    
    **Validates: Requirements 7.1**
    
    This is the main completeness property: the system must support fuzzing
    syscalls, ioctl handlers, and network protocols.
    """
    generator = FuzzingStrategyGenerator()
    
    # Generate strategies for all required target types
    syscall_strategy = generator.generate_syscall_strategy("all")
    ioctl_strategy = generator.generate_ioctl_strategy("/dev/null")
    network_strategy = generator.generate_network_protocol_strategy("tcp")
    
    strategies = [syscall_strategy, ioctl_strategy, network_strategy]
    
    # Property: All three target types should be present
    target_types = {s.target_type for s in strategies}
    
    assert FuzzingTarget.SYSCALL in target_types, \
        "System must support syscall fuzzing"
    assert FuzzingTarget.IOCTL in target_types, \
        "System must support ioctl fuzzing"
    assert FuzzingTarget.NETWORK in target_types, \
        "System must support network protocol fuzzing"
    
    # Property: Each strategy should be properly configured
    for strategy in strategies:
        assert strategy.target_name
        assert len(strategy.syscalls) > 0
        assert strategy.enable_coverage is True
        assert strategy.max_execution_time > 0


@given(
    syscall_count=st.integers(min_value=1, max_value=3),
    ioctl_count=st.integers(min_value=1, max_value=3),
    network_count=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=30, deadline=None)
def test_multiple_strategies_coverage(syscall_count, ioctl_count, network_count):
    """Property: System should handle multiple fuzzing strategies simultaneously.
    
    **Validates: Requirements 7.1**
    """
    generator = FuzzingStrategyGenerator()
    
    strategies = []
    
    # Generate multiple syscall strategies
    for i in range(syscall_count):
        group = ["filesystem", "network", "process"][i % 3]
        strategy = generator.generate_syscall_strategy(group)
        strategies.append(strategy)
    
    # Generate multiple ioctl strategies
    devices = ["/dev/null", "/dev/zero", "/dev/random"]
    for i in range(ioctl_count):
        device = devices[i % len(devices)]
        strategy = generator.generate_ioctl_strategy(device)
        strategies.append(strategy)
    
    # Generate multiple network strategies
    protocols = ["tcp", "udp", "icmp"]
    for i in range(network_count):
        protocol = protocols[i % len(protocols)]
        strategy = generator.generate_network_protocol_strategy(protocol)
        strategies.append(strategy)
    
    # Property: Total strategies should match requested count
    assert len(strategies) == syscall_count + ioctl_count + network_count
    
    # Property: All target types should be represented
    target_types = {s.target_type for s in strategies}
    assert FuzzingTarget.SYSCALL in target_types
    assert FuzzingTarget.IOCTL in target_types
    assert FuzzingTarget.NETWORK in target_types
    
    # Property: Each strategy should be unique
    strategy_names = [s.target_name for s in strategies]
    # Allow some duplicates since we might generate same group/device/protocol
    # but ensure we have at least some variety
    assert len(set(strategy_names)) >= min(len(strategies), 3)
    
    # Property: All strategies should be valid
    for strategy in strategies:
        assert strategy.target_type in [
            FuzzingTarget.SYSCALL,
            FuzzingTarget.IOCTL,
            FuzzingTarget.NETWORK
        ]
        assert len(strategy.syscalls) > 0
        assert strategy.enable_coverage is True


@given(group=syscall_group())
@settings(max_examples=100, deadline=None)
def test_syscall_group_specificity(group):
    """Property: Syscall strategies should target specific syscall groups.
    
    **Validates: Requirements 7.1**
    """
    generator = FuzzingStrategyGenerator()
    
    strategy = generator.generate_syscall_strategy(group)
    
    # Property: Group name should be in target name
    assert group in strategy.target_name
    
    # Property: Syscalls should be appropriate for the group
    if group == "filesystem":
        # Should include filesystem syscalls
        fs_syscalls = ["open", "read", "write", "close"]
        assert any(sc in strategy.syscalls for sc in fs_syscalls)
    elif group == "network":
        # Should include network syscalls
        net_syscalls = ["socket", "bind", "connect"]
        assert any(sc in strategy.syscalls for sc in net_syscalls)
    elif group == "all":
        # Should include syscalls from multiple groups
        assert len(strategy.syscalls) > 10


def test_strategy_configuration_completeness():
    """Property: All strategies should have complete configuration.
    
    **Validates: Requirements 7.1**
    """
    generator = FuzzingStrategyGenerator()
    
    # Generate one of each type
    strategies = [
        generator.generate_syscall_strategy("all"),
        generator.generate_ioctl_strategy("/dev/null"),
        generator.generate_network_protocol_strategy("tcp"),
        generator.generate_filesystem_strategy("ext4")
    ]
    
    for strategy in strategies:
        # Property: All required fields should be present
        assert strategy.target_type is not None
        assert strategy.target_name
        assert isinstance(strategy.syscalls, list)
        assert isinstance(strategy.enable_coverage, bool)
        assert isinstance(strategy.enable_comparisons, bool)
        assert isinstance(strategy.enable_fault_injection, bool)
        assert strategy.max_execution_time > 0
        assert strategy.max_crashes > 0
        assert isinstance(strategy.metadata, dict)


@given(
    enable_coverage=st.booleans(),
    enable_comparisons=st.booleans(),
    enable_fault_injection=st.booleans()
)
@settings(max_examples=50, deadline=None)
def test_strategy_options_respected(enable_coverage, enable_comparisons, enable_fault_injection):
    """Property: Strategy options should be properly configured.
    
    **Validates: Requirements 7.1**
    """
    # Create custom strategy
    strategy = FuzzingStrategy(
        target_type=FuzzingTarget.SYSCALL,
        target_name="test_strategy",
        syscalls=["open", "read", "write"],
        enable_coverage=enable_coverage,
        enable_comparisons=enable_comparisons,
        enable_fault_injection=enable_fault_injection
    )
    
    # Property: Options should match what was set
    assert strategy.enable_coverage == enable_coverage
    assert strategy.enable_comparisons == enable_comparisons
    assert strategy.enable_fault_injection == enable_fault_injection


def test_filesystem_fuzzing_coverage():
    """Property: Filesystem fuzzing should target filesystem operations.
    
    **Validates: Requirements 7.1**
    """
    generator = FuzzingStrategyGenerator()
    
    fs_types = ["ext4", "xfs", "btrfs", "f2fs"]
    
    for fs_type in fs_types:
        strategy = generator.generate_filesystem_strategy(fs_type)
        
        # Property: Should target filesystem
        assert strategy.target_type == FuzzingTarget.FILESYSTEM
        assert fs_type in strategy.target_name
        
        # Property: Should include filesystem syscalls
        fs_syscalls = ["open", "read", "write", "close", "mkdir", "rmdir"]
        for syscall in fs_syscalls:
            assert syscall in strategy.syscalls, \
                f"Filesystem fuzzing must include {syscall}"
        
        # Property: Filesystem type should be in metadata
        assert strategy.metadata.get("filesystem_type") == fs_type
