"""
Property-Based Tests for Build Server Selection

Tests correctness properties for build server selection using Hypothesis.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List

from infrastructure.models.build_server import (
    BuildServer,
    BuildServerStatus,
    BuildRequirements,
    Toolchain,
    ResourceUtilization,
)
from infrastructure.strategies.build_server_strategy import (
    BuildServerSelectionStrategy,
)


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def toolchain_strategy(draw, architecture: str = None):
    """Generate a valid Toolchain."""
    architectures = ["x86_64", "arm64", "armv7", "riscv64"]
    arch = architecture or draw(st.sampled_from(architectures))
    name_chars = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    
    return Toolchain(
        name=draw(st.text(min_size=3, max_size=30, alphabet=name_chars)),
        version=draw(st.from_regex(r'[0-9]+\.[0-9]+', fullmatch=True)),
        target_architecture=arch,
        path=f"/usr/bin/{draw(st.text(min_size=3, max_size=20, alphabet=name_chars))}",
        available=True  # Always available for selection tests
    )


@st.composite
def resource_utilization_strategy(draw, max_percent: float = 84.0):
    """Generate ResourceUtilization below threshold."""
    return ResourceUtilization(
        cpu_percent=draw(st.floats(min_value=0.0, max_value=max_percent)),
        memory_percent=draw(st.floats(min_value=0.0, max_value=max_percent)),
        storage_percent=draw(st.floats(min_value=0.0, max_value=max_percent)),
        network_bytes_in=draw(st.integers(min_value=0, max_value=10**9)),
        network_bytes_out=draw(st.integers(min_value=0, max_value=10**9))
    )


@st.composite
def online_build_server_strategy(draw, architecture: str = None):
    """Generate an online BuildServer with specified architecture support."""
    now = datetime.now(timezone.utc)
    arch = architecture or draw(st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]))
    
    # Generate toolchains including one for the target architecture
    toolchains = [draw(toolchain_strategy(architecture=arch))]
    # Add some random additional toolchains
    extra_count = draw(st.integers(min_value=0, max_value=3))
    for _ in range(extra_count):
        toolchains.append(draw(toolchain_strategy()))
    
    hostname_chars = "abcdefghijklmnopqrstuvwxyz0123456789-"
    username_chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    
    total_cpu = draw(st.integers(min_value=4, max_value=64))
    total_memory = draw(st.integers(min_value=8192, max_value=256000))
    total_storage = draw(st.integers(min_value=100, max_value=2000))
    
    return BuildServer(
        id=draw(st.uuids().map(str)),
        hostname=draw(st.text(min_size=3, max_size=30, alphabet=hostname_chars)),
        ip_address=draw(st.ip_addresses(v=4).map(str)),
        ssh_username=draw(st.text(min_size=3, max_size=20, alphabet=username_chars)),
        supported_architectures=[tc.target_architecture for tc in toolchains],
        toolchains=toolchains,
        total_cpu_cores=total_cpu,
        total_memory_mb=total_memory,
        total_storage_gb=total_storage,
        created_at=now,
        updated_at=now,
        ssh_port=22,
        status=BuildServerStatus.ONLINE,  # Always online for selection tests
        current_utilization=draw(resource_utilization_strategy()),
        active_build_count=draw(st.integers(min_value=0, max_value=3)),
        max_concurrent_builds=draw(st.integers(min_value=4, max_value=16)),
        maintenance_mode=False  # Never in maintenance for selection tests
    )


@st.composite
def build_requirements_strategy(draw, architecture: str = None):
    """Generate valid BuildRequirements."""
    arch = architecture or draw(st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]))
    
    return BuildRequirements(
        target_architecture=arch,
        min_cpu_cores=draw(st.integers(min_value=1, max_value=4)),
        min_memory_mb=draw(st.integers(min_value=1024, max_value=4096)),
        min_storage_gb=draw(st.integers(min_value=5, max_value=20))
    )


# =============================================================================
# Property Tests
# =============================================================================

class TestBuildServerSelectionMeetsArchitecture:
    """
    **Feature: test-infrastructure-management, Property 2: Build Server Selection Meets Architecture Requirements**
    **Validates: Requirements 3.2, 3.3**
    
    For any build job with a target architecture, the selected build server
    SHALL have a toolchain supporting that architecture.
    """

    @given(
        architecture=st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]),
        num_servers=st.integers(min_value=1, max_value=5),
        data=st.data()
    )
    @settings(max_examples=100)
    def test_selected_server_has_required_toolchain(self, architecture: str, num_servers: int, data):
        """Selected server must have toolchain for target architecture."""
        # Generate servers with at least one supporting the architecture
        servers = {}
        
        # Ensure at least one server supports the architecture
        server = data.draw(online_build_server_strategy(architecture=architecture))
        servers[server.id] = server
        
        # Add more random servers
        for _ in range(num_servers - 1):
            s = data.draw(online_build_server_strategy())
            servers[s.id] = s
        
        # Create requirements
        requirements = BuildRequirements(
            target_architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=1024,
            min_storage_gb=5
        )
        
        # Create strategy and select
        strategy = BuildServerSelectionStrategy(servers)
        
        async def run_test():
            result = await strategy.select_server(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # If selection succeeded, verify architecture support
        if result.success and result.server:
            assert result.server.has_toolchain_for(architecture), \
                f"Selected server {result.server.id} does not have toolchain for {architecture}"

    @given(
        architecture=st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]),
        data=st.data()
    )
    @settings(max_examples=50)
    def test_no_selection_when_no_compatible_servers(self, architecture: str, data):
        """Selection should fail when no servers support the architecture."""
        # Generate servers that DON'T support the target architecture
        other_archs = [a for a in ["x86_64", "arm64", "armv7", "riscv64"] if a != architecture]
        assume(len(other_archs) > 0)
        
        servers = {}
        for other_arch in other_archs[:2]:
            server = data.draw(online_build_server_strategy(architecture=other_arch))
            # Filter out any toolchains that accidentally support the target architecture
            server.toolchains = [tc for tc in server.toolchains if tc.target_architecture != architecture]
            server.supported_architectures = [tc.target_architecture for tc in server.toolchains]
            # Skip if no toolchains left
            assume(len(server.toolchains) > 0)
            servers[server.id] = server
        
        # Verify none of the servers support the target architecture
        for s in servers.values():
            assume(not s.has_toolchain_for(architecture))
        
        requirements = BuildRequirements(
            target_architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=1024,
            min_storage_gb=5
        )
        
        strategy = BuildServerSelectionStrategy(servers)
        
        async def run_test():
            result = await strategy.select_server(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Selection should fail
        assert not result.success, \
            f"Selection should fail when no servers support {architecture}"

    @given(
        architecture=st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]),
        num_compatible=st.integers(min_value=2, max_value=5),
        data=st.data()
    )
    @settings(max_examples=50)
    def test_all_alternatives_have_required_toolchain(self, architecture: str, num_compatible: int, data):
        """All alternative servers must also have the required toolchain."""
        servers = {}
        
        # Generate multiple compatible servers
        for _ in range(num_compatible):
            server = data.draw(online_build_server_strategy(architecture=architecture))
            servers[server.id] = server
        
        requirements = BuildRequirements(
            target_architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=1024,
            min_storage_gb=5
        )
        
        strategy = BuildServerSelectionStrategy(servers)
        
        async def run_test():
            result = await strategy.select_server(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        if result.success:
            # Check all alternatives
            for alt_server in result.alternative_servers:
                assert alt_server.has_toolchain_for(architecture), \
                    f"Alternative server {alt_server.id} does not have toolchain for {architecture}"


class TestBuildServerDiskSpaceWarning:
    """
    **Feature: test-infrastructure-management, Property 3: Build Server Disk Space Warning**
    **Validates: Requirements 2.4**
    
    For any build server with disk space below 10GB, the system SHALL display
    warning indicators and optionally prevent new build assignments.
    """

    @given(
        storage_gb=st.integers(min_value=1, max_value=9),
        storage_percent=st.floats(min_value=90.0, max_value=99.0)
    )
    @settings(max_examples=100)
    def test_low_disk_space_prevents_selection(self, storage_gb: int, storage_percent: float):
        """Servers with low disk space should not be selected."""
        now = datetime.now(timezone.utc)
        
        # Create server with low disk space
        server = BuildServer(
            id="low-disk-server",
            hostname="low-disk",
            ip_address="192.168.1.100",
            ssh_username="user",
            supported_architectures=["x86_64"],
            toolchains=[Toolchain(
                name="gcc",
                version="10.0",
                target_architecture="x86_64",
                path="/usr/bin/gcc",
                available=True
            )],
            total_cpu_cores=8,
            total_memory_mb=16384,
            total_storage_gb=storage_gb,  # Low storage
            created_at=now,
            updated_at=now,
            status=BuildServerStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=20.0,
                memory_percent=30.0,
                storage_percent=storage_percent  # High usage
            ),
            maintenance_mode=False
        )
        
        servers = {server.id: server}
        
        # Requirements need more storage than available
        requirements = BuildRequirements(
            target_architecture="x86_64",
            min_cpu_cores=1,
            min_memory_mb=1024,
            min_storage_gb=storage_gb + 5  # More than available
        )
        
        strategy = BuildServerSelectionStrategy(servers)
        
        async def run_test():
            result = await strategy.select_server(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Selection should fail due to insufficient storage
        assert not result.success, \
            f"Server with only {storage_gb}GB should not be selected for {requirements.min_storage_gb}GB requirement"

    @given(
        available_storage=st.integers(min_value=50, max_value=500)
    )
    @settings(max_examples=50)
    def test_adequate_disk_space_allows_selection(self, available_storage: int):
        """Servers with adequate disk space should be selectable."""
        now = datetime.now(timezone.utc)
        
        server = BuildServer(
            id="good-disk-server",
            hostname="good-disk",
            ip_address="192.168.1.100",
            ssh_username="user",
            supported_architectures=["x86_64"],
            toolchains=[Toolchain(
                name="gcc",
                version="10.0",
                target_architecture="x86_64",
                path="/usr/bin/gcc",
                available=True
            )],
            total_cpu_cores=8,
            total_memory_mb=16384,
            total_storage_gb=available_storage,
            created_at=now,
            updated_at=now,
            status=BuildServerStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=20.0,
                memory_percent=30.0,
                storage_percent=20.0  # Low usage
            ),
            maintenance_mode=False
        )
        
        servers = {server.id: server}
        
        requirements = BuildRequirements(
            target_architecture="x86_64",
            min_cpu_cores=1,
            min_memory_mb=1024,
            min_storage_gb=10  # Reasonable requirement
        )
        
        strategy = BuildServerSelectionStrategy(servers)
        
        async def run_test():
            result = await strategy.select_server(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Selection should succeed
        assert result.success, \
            f"Server with {available_storage}GB should be selected for 10GB requirement"


class TestLoadBalancingPreference:
    """
    **Feature: test-infrastructure-management, Property 17: Load Balancing Preference**
    **Validates: Requirements 13.4**
    
    For any set of resources that equally meet requirements, the selection
    strategy SHALL prefer resources with lower current utilization.
    """

    @given(
        low_util=st.floats(min_value=10.0, max_value=30.0),
        high_util=st.floats(min_value=60.0, max_value=80.0)
    )
    @settings(max_examples=100)
    def test_prefers_lower_utilization(self, low_util: float, high_util: float):
        """Strategy should prefer servers with lower utilization."""
        assume(high_util > low_util + 20)  # Ensure significant difference
        
        now = datetime.now(timezone.utc)
        
        # Create two identical servers except for utilization
        low_util_server = BuildServer(
            id="low-util-server",
            hostname="low-util",
            ip_address="192.168.1.100",
            ssh_username="user",
            supported_architectures=["x86_64"],
            toolchains=[Toolchain(
                name="gcc",
                version="10.0",
                target_architecture="x86_64",
                path="/usr/bin/gcc",
                available=True
            )],
            total_cpu_cores=8,
            total_memory_mb=16384,
            total_storage_gb=500,
            created_at=now,
            updated_at=now,
            status=BuildServerStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=low_util,
                memory_percent=low_util,
                storage_percent=low_util
            ),
            queue_depth=0,
            maintenance_mode=False
        )
        
        high_util_server = BuildServer(
            id="high-util-server",
            hostname="high-util",
            ip_address="192.168.1.101",
            ssh_username="user",
            supported_architectures=["x86_64"],
            toolchains=[Toolchain(
                name="gcc",
                version="10.0",
                target_architecture="x86_64",
                path="/usr/bin/gcc",
                available=True
            )],
            total_cpu_cores=8,
            total_memory_mb=16384,
            total_storage_gb=500,
            created_at=now,
            updated_at=now,
            status=BuildServerStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=high_util,
                memory_percent=high_util,
                storage_percent=high_util
            ),
            queue_depth=0,
            maintenance_mode=False
        )
        
        servers = {
            low_util_server.id: low_util_server,
            high_util_server.id: high_util_server
        }
        
        requirements = BuildRequirements(
            target_architecture="x86_64",
            min_cpu_cores=1,
            min_memory_mb=1024,
            min_storage_gb=10
        )
        
        strategy = BuildServerSelectionStrategy(servers)
        
        async def run_test():
            result = await strategy.select_server(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        assert result.server.id == "low-util-server", \
            f"Should prefer low utilization server, got {result.server.id}"
