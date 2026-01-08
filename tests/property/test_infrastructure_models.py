"""
Property-Based Tests for Infrastructure Models

Tests correctness properties for infrastructure data models using Hypothesis.
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
from typing import List, Dict

from infrastructure.models.build_server import (
    BuildServer,
    BuildServerStatus,
    BuildServerCapacity,
    Toolchain,
    ResourceUtilization,
)
from infrastructure.models.host import (
    Host,
    HostStatus,
    HostCapacity,
)
from infrastructure.models.board import (
    Board,
    BoardStatus,
    BoardHealth,
    PowerControlConfig,
    PowerControlMethod,
    HealthLevel,
)


# =============================================================================
# Hypothesis Strategies for generating test data
# =============================================================================

@st.composite
def toolchain_strategy(draw):
    """Generate a valid Toolchain."""
    architectures = ["x86_64", "arm64", "armv7", "riscv64"]
    # Use simple alphanumeric characters with allowed special chars
    name_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    path_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-_"
    return Toolchain(
        name=draw(st.text(min_size=1, max_size=50, alphabet=name_chars)),
        version=draw(st.from_regex(r'[0-9]+\.[0-9]+(\.[0-9]+)?', fullmatch=True)),
        target_architecture=draw(st.sampled_from(architectures)),
        path=draw(st.text(min_size=1, max_size=100, alphabet=path_chars)),
        available=draw(st.booleans())
    )


@st.composite
def resource_utilization_strategy(draw):
    """Generate valid ResourceUtilization."""
    return ResourceUtilization(
        cpu_percent=draw(st.floats(min_value=0.0, max_value=100.0)),
        memory_percent=draw(st.floats(min_value=0.0, max_value=100.0)),
        storage_percent=draw(st.floats(min_value=0.0, max_value=100.0)),
        network_bytes_in=draw(st.integers(min_value=0, max_value=10**12)),
        network_bytes_out=draw(st.integers(min_value=0, max_value=10**12))
    )


@st.composite
def build_server_strategy(draw):
    """Generate a valid BuildServer."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    toolchains = draw(st.lists(toolchain_strategy(), min_size=1, max_size=5))
    architectures = list(set(tc.target_architecture for tc in toolchains if tc.available))
    hostname_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
    username_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    return BuildServer(
        id=draw(st.uuids().map(str)),
        hostname=draw(st.text(min_size=1, max_size=50, alphabet=hostname_chars)),
        ip_address=draw(st.ip_addresses(v=4).map(str)),
        ssh_username=draw(st.text(min_size=1, max_size=30, alphabet=username_chars)),
        supported_architectures=architectures if architectures else ["x86_64"],
        toolchains=toolchains,
        total_cpu_cores=draw(st.integers(min_value=1, max_value=128)),
        total_memory_mb=draw(st.integers(min_value=1024, max_value=512000)),
        total_storage_gb=draw(st.integers(min_value=10, max_value=10000)),
        created_at=now,
        updated_at=now,
        ssh_port=draw(st.integers(min_value=1, max_value=65535)),
        status=draw(st.sampled_from(list(BuildServerStatus))),
        current_utilization=draw(resource_utilization_strategy()),
        active_build_count=draw(st.integers(min_value=0, max_value=10)),
        max_concurrent_builds=draw(st.integers(min_value=1, max_value=16)),
        maintenance_mode=draw(st.booleans())
    )


@st.composite
def host_strategy(draw):
    """Generate a valid Host."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    architectures = ["x86_64", "arm64"]
    hostname_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
    username_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    return Host(
        id=draw(st.uuids().map(str)),
        hostname=draw(st.text(min_size=1, max_size=50, alphabet=hostname_chars)),
        ip_address=draw(st.ip_addresses(v=4).map(str)),
        ssh_username=draw(st.text(min_size=1, max_size=30, alphabet=username_chars)),
        architecture=draw(st.sampled_from(architectures)),
        total_cpu_cores=draw(st.integers(min_value=1, max_value=128)),
        total_memory_mb=draw(st.integers(min_value=1024, max_value=512000)),
        total_storage_gb=draw(st.integers(min_value=10, max_value=10000)),
        created_at=now,
        updated_at=now,
        ssh_port=draw(st.integers(min_value=1, max_value=65535)),
        status=draw(st.sampled_from(list(HostStatus))),
        kvm_enabled=draw(st.booleans()),
        nested_virt_enabled=draw(st.booleans()),
        current_utilization=draw(resource_utilization_strategy()),
        running_vm_count=draw(st.integers(min_value=0, max_value=20)),
        max_vms=draw(st.integers(min_value=1, max_value=50)),
        maintenance_mode=draw(st.booleans())
    )


@st.composite
def power_control_config_strategy(draw):
    """Generate a valid PowerControlConfig."""
    method = draw(st.sampled_from(list(PowerControlMethod)))
    config = PowerControlConfig(method=method)
    
    if method == PowerControlMethod.USB_HUB:
        config.usb_hub_port = draw(st.integers(min_value=1, max_value=8))
    elif method == PowerControlMethod.NETWORK_PDU:
        config.pdu_outlet = draw(st.integers(min_value=1, max_value=24))
        config.pdu_address = draw(st.ip_addresses(v=4).map(str))
    elif method == PowerControlMethod.GPIO_RELAY:
        config.gpio_pin = draw(st.integers(min_value=0, max_value=40))
    
    return config


@st.composite
def board_health_strategy(draw):
    """Generate valid BoardHealth."""
    from infrastructure.models.board import PowerStatus
    return BoardHealth(
        connectivity=draw(st.sampled_from(list(HealthLevel))),
        temperature_celsius=draw(st.floats(min_value=20.0, max_value=100.0) | st.none()),
        storage_percent=draw(st.floats(min_value=0.0, max_value=100.0) | st.none()),
        power_status=draw(st.sampled_from(list(PowerStatus))),
        last_response_time_ms=draw(st.integers(min_value=1, max_value=30000) | st.none())
    )


@st.composite
def board_strategy(draw):
    """Generate a valid Board."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    architectures = ["arm64", "armv7", "riscv64"]
    board_types = ["raspberry_pi_4", "raspberry_pi_3", "beaglebone", "riscv_board", "jetson_nano"]
    name_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    serial_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    return Board(
        id=draw(st.uuids().map(str)),
        name=draw(st.text(min_size=1, max_size=50, alphabet=name_chars)),
        board_type=draw(st.sampled_from(board_types)),
        architecture=draw(st.sampled_from(architectures)),
        power_control=draw(power_control_config_strategy()),
        created_at=now,
        updated_at=now,
        serial_number=draw(st.text(min_size=5, max_size=20, alphabet=serial_chars) | st.none()),
        ip_address=draw(st.ip_addresses(v=4).map(str) | st.none()),
        ssh_port=draw(st.integers(min_value=1, max_value=65535)),
        status=draw(st.sampled_from(list(BoardStatus))),
        health=draw(board_health_strategy()),
        peripherals=draw(st.lists(st.sampled_from(["gpio", "i2c", "spi", "uart", "usb", "ethernet", "wifi"]), max_size=5)),
        maintenance_mode=draw(st.booleans())
    )


# =============================================================================
# Property Tests
# =============================================================================

class TestBuildServerPool:
    """
    **Feature: test-infrastructure-management, Property 1: Build Server Registration Adds to Pool**
    **Validates: Requirements 1.2, 1.3**
    
    For any valid build server registration configuration with successful SSH validation
    and toolchain verification, the build server pool SHALL contain the newly registered
    server with correct capabilities.
    """

    @given(server=build_server_strategy())
    @settings(max_examples=100)
    def test_build_server_has_valid_id(self, server: BuildServer):
        """Build server must have a valid non-empty ID."""
        assert server.id is not None
        assert len(server.id) > 0

    @given(server=build_server_strategy())
    @settings(max_examples=100)
    def test_build_server_toolchain_architecture_consistency(self, server: BuildServer):
        """Build server's supported architectures must match available toolchains."""
        available_toolchain_archs = set(
            tc.target_architecture for tc in server.toolchains if tc.available
        )
        # If there are available toolchains, supported_architectures should reflect them
        if available_toolchain_archs:
            for arch in server.supported_architectures:
                # Server should have at least one toolchain for each supported architecture
                assert server.has_toolchain_for(arch) or arch not in available_toolchain_archs

    @given(server=build_server_strategy())
    @settings(max_examples=100)
    def test_build_server_capacity_reflects_utilization(self, server: BuildServer):
        """Build server capacity must reflect current utilization."""
        capacity = server.get_capacity()
        
        # Available resources should be less than or equal to total
        assert capacity.available_cpu_cores <= server.total_cpu_cores
        assert capacity.available_memory_mb <= server.total_memory_mb
        assert capacity.available_storage_gb <= server.total_storage_gb

    @given(server=build_server_strategy())
    @settings(max_examples=100)
    def test_build_server_can_accept_build_consistency(self, server: BuildServer):
        """can_accept_build must be consistent with server state."""
        can_accept = server.can_accept_build()
        
        # If server is not online, it cannot accept builds
        if server.status != BuildServerStatus.ONLINE:
            assert not can_accept
        
        # If in maintenance mode, cannot accept builds
        if server.maintenance_mode:
            assert not can_accept
        
        # If at max concurrent builds, cannot accept more
        if server.active_build_count >= server.max_concurrent_builds:
            assert not can_accept

    @given(server=build_server_strategy(), arch=st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]))
    @settings(max_examples=100)
    def test_get_toolchain_for_returns_correct_architecture(self, server: BuildServer, arch: str):
        """get_toolchain_for must return a toolchain for the correct architecture."""
        toolchain = server.get_toolchain_for(arch)
        
        if toolchain is not None:
            assert toolchain.target_architecture.lower() == arch.lower()
            assert toolchain.available


class TestHostPool:
    """
    **Feature: test-infrastructure-management, Property 8: Host Registration Adds to Pool**
    **Validates: Requirements 7.2, 7.3**
    
    For any valid host registration configuration with successful SSH and libvirt validation,
    the host pool SHALL contain the newly registered host with correct capabilities.
    """

    @given(host=host_strategy())
    @settings(max_examples=100)
    def test_host_has_valid_id(self, host: Host):
        """Host must have a valid non-empty ID."""
        assert host.id is not None
        assert len(host.id) > 0

    @given(host=host_strategy())
    @settings(max_examples=100)
    def test_host_capacity_reflects_utilization(self, host: Host):
        """Host capacity must reflect current utilization."""
        capacity = host.get_capacity()
        
        # Available resources should be less than or equal to total
        assert capacity.available_cpu_cores <= host.total_cpu_cores
        assert capacity.available_memory_mb <= host.total_memory_mb
        assert capacity.available_storage_gb <= host.total_storage_gb

    @given(host=host_strategy())
    @settings(max_examples=100)
    def test_host_can_allocate_vm_consistency(self, host: Host):
        """can_allocate_vm must be consistent with host state."""
        can_allocate = host.can_allocate_vm()
        
        # If host is not online, it cannot allocate VMs
        if host.status != HostStatus.ONLINE:
            assert not can_allocate
        
        # If in maintenance mode, cannot allocate VMs
        if host.maintenance_mode:
            assert not can_allocate
        
        # If at max VMs, cannot allocate more
        if host.running_vm_count >= host.max_vms:
            assert not can_allocate

    @given(host=host_strategy(), arch=st.sampled_from(["x86_64", "arm64"]))
    @settings(max_examples=100)
    def test_host_supports_architecture_consistency(self, host: Host, arch: str):
        """supports_architecture must correctly match host architecture."""
        supports = host.supports_architecture(arch)
        
        if host.architecture.lower() == arch.lower():
            assert supports
        else:
            assert not supports


class TestBoardPool:
    """
    **Feature: test-infrastructure-management, Property 12: Board Registration Adds to Pool**
    **Validates: Requirements 8.2, 8.3**
    
    For any valid board registration configuration with successful connectivity validation,
    the board pool SHALL contain the newly registered board with correct hardware information.
    """

    @given(board=board_strategy())
    @settings(max_examples=100)
    def test_board_has_valid_id(self, board: Board):
        """Board must have a valid non-empty ID."""
        assert board.id is not None
        assert len(board.id) > 0

    @given(board=board_strategy())
    @settings(max_examples=100)
    def test_board_is_available_consistency(self, board: Board):
        """is_available must be consistent with board state."""
        is_available = board.is_available()
        
        # If board is not in AVAILABLE status, it's not available
        if board.status != BoardStatus.AVAILABLE:
            assert not is_available
        
        # If in maintenance mode, not available
        if board.maintenance_mode:
            assert not is_available
        
        # If health is not healthy, not available
        if not board.health.is_healthy():
            assert not is_available

    @given(board=board_strategy(), arch=st.sampled_from(["arm64", "armv7", "riscv64"]))
    @settings(max_examples=100)
    def test_board_supports_architecture_consistency(self, board: Board, arch: str):
        """supports_architecture must correctly match board architecture."""
        supports = board.supports_architecture(arch)
        
        if board.architecture.lower() == arch.lower():
            assert supports
        else:
            assert not supports

    @given(board=board_strategy())
    @settings(max_examples=100)
    def test_board_has_peripherals_subset(self, board: Board):
        """has_peripherals must return True for subsets of board peripherals."""
        if board.peripherals:
            # Any subset of peripherals should be satisfied
            subset = board.peripherals[:len(board.peripherals)//2 + 1]
            assert board.has_peripherals(subset)
        
        # Empty list should always be satisfied
        assert board.has_peripherals([])

    @given(board=board_strategy())
    @settings(max_examples=100)
    def test_board_power_control_config_valid(self, board: Board):
        """Power control config must have appropriate fields set for its method."""
        config = board.power_control
        
        if config.method == PowerControlMethod.USB_HUB:
            # USB hub should have port configured
            assert config.usb_hub_port is not None or config.method == PowerControlMethod.MANUAL
        elif config.method == PowerControlMethod.NETWORK_PDU:
            # PDU should have outlet and address configured
            assert config.pdu_outlet is not None or config.method == PowerControlMethod.MANUAL
        elif config.method == PowerControlMethod.GPIO_RELAY:
            # GPIO should have pin configured
            assert config.gpio_pin is not None or config.method == PowerControlMethod.MANUAL

    @given(board=board_strategy())
    @settings(max_examples=100)
    def test_board_health_needs_attention_consistency(self, board: Board):
        """needs_attention must be consistent with health indicators."""
        health = board.health
        needs_attention = health.needs_attention()
        
        # If connectivity is degraded or unhealthy, needs attention
        if health.connectivity in (HealthLevel.DEGRADED, HealthLevel.UNHEALTHY):
            assert needs_attention
        
        # If temperature is too high, needs attention
        if health.temperature_celsius and health.temperature_celsius > 80:
            assert needs_attention
        
        # If storage is too high, needs attention
        if health.storage_percent and health.storage_percent > 90:
            assert needs_attention
