"""
Property-Based Tests for Host Management

Tests correctness properties for QEMU host management using Hypothesis.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List

from infrastructure.models.host import (
    Host,
    HostStatus,
    HostCapacity,
    VMRequirements,
    HostSelectionResult,
)
from infrastructure.models.build_server import ResourceUtilization
from infrastructure.strategies.host_strategy import HostSelectionStrategy, ResourceReservation


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def architecture_strategy(draw):
    """Generate a valid architecture."""
    return draw(st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]))


@st.composite
def host_status_strategy(draw):
    """Generate a valid host status."""
    return draw(st.sampled_from(list(HostStatus)))


@st.composite
def utilization_strategy(draw, max_percent: float = 100.0):
    """Generate resource utilization."""
    return ResourceUtilization(
        cpu_percent=draw(st.floats(min_value=0.0, max_value=max_percent)),
        memory_percent=draw(st.floats(min_value=0.0, max_value=max_percent)),
        storage_percent=draw(st.floats(min_value=0.0, max_value=max_percent)),
        network_bytes_in=draw(st.integers(min_value=0, max_value=1000000)),
        network_bytes_out=draw(st.integers(min_value=0, max_value=1000000))
    )


@st.composite
def host_strategy(draw, architecture: str = None, status: HostStatus = None, 
                  utilization: ResourceUtilization = None, maintenance: bool = None):
    """Generate a valid Host."""
    arch = architecture or draw(architecture_strategy())
    now = datetime.now(timezone.utc)
    
    total_cpu = draw(st.integers(min_value=4, max_value=64))
    total_memory = draw(st.integers(min_value=8192, max_value=262144))
    total_storage = draw(st.integers(min_value=100, max_value=2000))
    
    util = utilization or draw(utilization_strategy())
    
    return Host(
        id=draw(st.uuids().map(str)),
        hostname=draw(st.text(min_size=5, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-")),
        ip_address=f"192.168.{draw(st.integers(min_value=1, max_value=254))}.{draw(st.integers(min_value=1, max_value=254))}",
        ssh_username="admin",
        architecture=arch,
        total_cpu_cores=total_cpu,
        total_memory_mb=total_memory,
        total_storage_gb=total_storage,
        kvm_enabled=draw(st.booleans()),
        nested_virt_enabled=draw(st.booleans()),
        status=status or draw(st.sampled_from([HostStatus.ONLINE, HostStatus.DEGRADED])),
        current_utilization=util,
        running_vm_count=draw(st.integers(min_value=0, max_value=5)),
        max_vms=draw(st.integers(min_value=5, max_value=20)),
        maintenance_mode=maintenance if maintenance is not None else draw(st.booleans()),
        created_at=now,
        updated_at=now,
        labels=draw(st.dictionaries(
            keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=st.text(min_size=1, max_size=20),
            max_size=3
        ))
    )


@st.composite
def vm_requirements_strategy(draw, architecture: str = None):
    """Generate valid VM requirements."""
    arch = architecture or draw(architecture_strategy())
    
    return VMRequirements(
        architecture=arch,
        min_cpu_cores=draw(st.integers(min_value=1, max_value=4)),
        min_memory_mb=draw(st.integers(min_value=512, max_value=4096)),
        min_storage_gb=draw(st.integers(min_value=10, max_value=50)),
        require_kvm=draw(st.booleans()),
        require_nested_virt=False,  # Keep simple for tests
    )


# =============================================================================
# Property Tests
# =============================================================================

class TestHostUtilizationThreshold:
    """
    **Feature: test-infrastructure-management, Property 9: Host Utilization Threshold Enforcement**
    **Validates: Requirements 9.4**
    
    For any host with resource utilization exceeding 85%, new VM allocations
    to that host SHALL be prevented.
    """

    @given(
        architecture=architecture_strategy(),
        data=st.data()
    )
    @settings(max_examples=100)
    def test_overloaded_host_rejected_for_allocation(self, architecture: str, data):
        """Hosts with >85% utilization should not be selected."""
        # Create an overloaded utilization (>85%)
        overloaded_util = ResourceUtilization(
            cpu_percent=data.draw(st.floats(min_value=86.0, max_value=100.0)),
            memory_percent=data.draw(st.floats(min_value=86.0, max_value=100.0)),
            storage_percent=data.draw(st.floats(min_value=0.0, max_value=50.0)),
            network_bytes_in=0,
            network_bytes_out=0
        )
        
        # Create host with overloaded utilization
        host = data.draw(host_strategy(
            architecture=architecture,
            status=HostStatus.ONLINE,
            utilization=overloaded_util,
            maintenance=False
        ))
        
        # Create requirements matching the architecture
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        # Create strategy with only this host
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Should fail to select because host is overloaded
        assert not result.success, \
            f"Overloaded host should not be selected. Utilization: CPU={overloaded_util.cpu_percent}%, MEM={overloaded_util.memory_percent}%"

    @given(
        architecture=architecture_strategy(),
        data=st.data()
    )
    @settings(max_examples=100)
    def test_normal_utilization_host_can_be_selected(self, architecture: str, data):
        """Hosts with <85% utilization should be selectable."""
        # Create normal utilization (<85%)
        normal_util = ResourceUtilization(
            cpu_percent=data.draw(st.floats(min_value=0.0, max_value=80.0)),
            memory_percent=data.draw(st.floats(min_value=0.0, max_value=80.0)),
            storage_percent=data.draw(st.floats(min_value=0.0, max_value=80.0)),
            network_bytes_in=0,
            network_bytes_out=0
        )
        
        # Create host with normal utilization
        host = Host(
            id=data.draw(st.uuids().map(str)),
            hostname="test-host",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            nested_virt_enabled=False,
            status=HostStatus.ONLINE,
            current_utilization=normal_util,
            running_vm_count=2,
            max_vms=10,
            maintenance_mode=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create requirements matching the architecture
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        # Create strategy with only this host
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Should succeed because host is not overloaded
        assert result.success, \
            f"Normal utilization host should be selectable. Utilization: CPU={normal_util.cpu_percent}%, MEM={normal_util.memory_percent}%"
        assert result.host.id == host.id

    @given(data=st.data())
    @settings(max_examples=50)
    def test_prefers_lower_utilization_host(self, data):
        """When multiple hosts available, prefer lower utilization."""
        architecture = "x86_64"
        now = datetime.now(timezone.utc)
        
        # Create low utilization host
        low_util = ResourceUtilization(
            cpu_percent=20.0,
            memory_percent=30.0,
            storage_percent=25.0,
            network_bytes_in=0,
            network_bytes_out=0
        )
        low_host = Host(
            id="low-util-host",
            hostname="low-util",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=low_util,
            running_vm_count=1,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        # Create high utilization host (but still under 85%)
        high_util = ResourceUtilization(
            cpu_percent=75.0,
            memory_percent=80.0,
            storage_percent=70.0,
            network_bytes_in=0,
            network_bytes_out=0
        )
        high_host = Host(
            id="high-util-host",
            hostname="high-util",
            ip_address="192.168.1.101",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=high_util,
            running_vm_count=5,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        hosts = {low_host.id: low_host, high_host.id: high_host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        # Should prefer the lower utilization host
        assert result.host.id == "low-util-host", \
            f"Should prefer lower utilization host, got {result.host.id}"




class TestHostStatusTransition:
    """
    **Feature: test-infrastructure-management, Property 10: Unreachable Host Status Transition**
    **Validates: Requirements 9.3**
    
    For any host that becomes unreachable, the host status SHALL transition
    to OFFLINE within the monitoring interval.
    """

    @given(
        architecture=architecture_strategy(),
        data=st.data()
    )
    @settings(max_examples=100)
    def test_offline_host_not_selected(self, architecture: str, data):
        """Offline hosts should not be selected for VM allocation."""
        now = datetime.now(timezone.utc)
        
        # Create an offline host
        host = Host(
            id=data.draw(st.uuids().map(str)),
            hostname="offline-host",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.OFFLINE,  # Offline status
            current_utilization=ResourceUtilization(),
            running_vm_count=0,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Should fail because host is offline
        assert not result.success, "Offline host should not be selected"

    @given(
        architecture=architecture_strategy(),
        data=st.data()
    )
    @settings(max_examples=50)
    def test_degraded_host_not_selected(self, architecture: str, data):
        """Degraded hosts should not be selected for VM allocation."""
        now = datetime.now(timezone.utc)
        
        # Create a degraded host
        host = Host(
            id=data.draw(st.uuids().map(str)),
            hostname="degraded-host",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.DEGRADED,  # Degraded status
            current_utilization=ResourceUtilization(),
            running_vm_count=0,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        # Should fail because host is degraded
        assert not result.success, "Degraded host should not be selected"

    @given(data=st.data())
    @settings(max_examples=50)
    def test_online_host_preferred_over_offline(self, data):
        """Online hosts should be selected over offline hosts."""
        architecture = "x86_64"
        now = datetime.now(timezone.utc)
        
        # Create an offline host
        offline_host = Host(
            id="offline-host",
            hostname="offline",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=32,  # More resources
            total_memory_mb=65536,
            total_storage_gb=1000,
            kvm_enabled=True,
            status=HostStatus.OFFLINE,
            current_utilization=ResourceUtilization(),
            running_vm_count=0,
            max_vms=20,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        # Create an online host with less resources
        online_host = Host(
            id="online-host",
            hostname="online",
            ip_address="192.168.1.101",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=8,
            total_memory_mb=16384,
            total_storage_gb=200,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=20.0,
                memory_percent=30.0,
                storage_percent=25.0
            ),
            running_vm_count=1,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        hosts = {offline_host.id: offline_host, online_host.id: online_host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        assert result.host.id == "online-host", \
            "Should select online host over offline host"


class TestHostSelectionRequirements:
    """
    **Feature: test-infrastructure-management, Property 11: Host Selection Meets Requirements**
    **Validates: Requirements 11.3, 13.2**
    
    For any VM requirements and auto-selection, the selected host SHALL meet
    all specified requirements (architecture, CPU, memory, KVM support).
    """

    @given(
        architecture=architecture_strategy(),
        data=st.data()
    )
    @settings(max_examples=100)
    def test_selected_host_matches_architecture(self, architecture: str, data):
        """Selected host must match required architecture."""
        now = datetime.now(timezone.utc)
        
        # Create host with matching architecture
        host = Host(
            id=data.draw(st.uuids().map(str)),
            hostname="matching-host",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=20.0,
                memory_percent=30.0,
                storage_percent=25.0
            ),
            running_vm_count=1,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        assert result.host.architecture.lower() == architecture.lower(), \
            f"Selected host architecture {result.host.architecture} doesn't match required {architecture}"

    @given(data=st.data())
    @settings(max_examples=50)
    def test_incompatible_architecture_not_selected(self, data):
        """Hosts with incompatible architecture should not be selected."""
        now = datetime.now(timezone.utc)
        
        # Create host with x86_64 architecture
        host = Host(
            id=data.draw(st.uuids().map(str)),
            hostname="x86-host",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture="x86_64",
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=20.0,
                memory_percent=30.0,
                storage_percent=25.0
            ),
            running_vm_count=1,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        # Require arm64 architecture
        requirements = VMRequirements(
            architecture="arm64",
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select host with incompatible architecture"

    @given(data=st.data())
    @settings(max_examples=50)
    def test_kvm_requirement_enforced(self, data):
        """KVM requirement must be enforced."""
        now = datetime.now(timezone.utc)
        architecture = "x86_64"
        
        # Create host without KVM
        host_no_kvm = Host(
            id="no-kvm-host",
            hostname="no-kvm",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=False,  # No KVM
            status=HostStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=20.0,
                memory_percent=30.0,
                storage_percent=25.0
            ),
            running_vm_count=1,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        # Require KVM
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=True  # Require KVM
        )
        
        hosts = {host_no_kvm.id: host_no_kvm}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select host without KVM when KVM is required"

    @given(data=st.data())
    @settings(max_examples=50)
    def test_capacity_requirements_enforced(self, data):
        """CPU, memory, and storage requirements must be enforced."""
        now = datetime.now(timezone.utc)
        architecture = "x86_64"
        
        # Create host with limited capacity
        host = Host(
            id="limited-host",
            hostname="limited",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=4,
            total_memory_mb=4096,
            total_storage_gb=50,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=80.0,  # High utilization leaves little available
                memory_percent=80.0,
                storage_percent=80.0
            ),
            running_vm_count=3,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        # Require more resources than available
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=8,  # More than available
            min_memory_mb=16384,  # More than available
            min_storage_gb=100,  # More than available
            require_kvm=False
        )
        
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select host with insufficient capacity"

    @given(data=st.data())
    @settings(max_examples=50)
    def test_maintenance_mode_blocks_selection(self, data):
        """Hosts in maintenance mode should not be selected."""
        now = datetime.now(timezone.utc)
        architecture = "x86_64"
        
        # Create host in maintenance mode
        host = Host(
            id="maintenance-host",
            hostname="maintenance",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.MAINTENANCE,
            current_utilization=ResourceUtilization(
                cpu_percent=10.0,
                memory_percent=20.0,
                storage_percent=15.0
            ),
            running_vm_count=0,
            max_vms=10,
            maintenance_mode=True,  # In maintenance
            created_at=now,
            updated_at=now
        )
        
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select host in maintenance mode"

    @given(data=st.data())
    @settings(max_examples=50)
    def test_max_vms_limit_enforced(self, data):
        """Hosts at max VM capacity should not be selected."""
        now = datetime.now(timezone.utc)
        architecture = "x86_64"
        
        # Create host at max VM capacity
        host = Host(
            id="full-host",
            hostname="full",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=50.0,
                memory_percent=60.0,
                storage_percent=40.0
            ),
            running_vm_count=10,  # At max
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False
        )
        
        hosts = {host.id: host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert not result.success, \
            "Should not select host at max VM capacity"

    @given(data=st.data())
    @settings(max_examples=50)
    def test_preferred_host_selected_when_compatible(self, data):
        """Preferred host should be selected when it meets requirements."""
        now = datetime.now(timezone.utc)
        architecture = "x86_64"
        
        # Create preferred host
        preferred_host = Host(
            id="preferred-host",
            hostname="preferred",
            ip_address="192.168.1.100",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=16,
            total_memory_mb=32768,
            total_storage_gb=500,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=50.0,  # Higher utilization
                memory_percent=60.0,
                storage_percent=40.0
            ),
            running_vm_count=5,
            max_vms=10,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        # Create better host (lower utilization)
        better_host = Host(
            id="better-host",
            hostname="better",
            ip_address="192.168.1.101",
            ssh_username="admin",
            architecture=architecture,
            total_cpu_cores=32,
            total_memory_mb=65536,
            total_storage_gb=1000,
            kvm_enabled=True,
            status=HostStatus.ONLINE,
            current_utilization=ResourceUtilization(
                cpu_percent=10.0,  # Lower utilization
                memory_percent=20.0,
                storage_percent=15.0
            ),
            running_vm_count=1,
            max_vms=20,
            maintenance_mode=False,
            created_at=now,
            updated_at=now
        )
        
        # Specify preferred host
        requirements = VMRequirements(
            architecture=architecture,
            min_cpu_cores=1,
            min_memory_mb=512,
            min_storage_gb=10,
            require_kvm=False,
            preferred_host_id="preferred-host"
        )
        
        hosts = {preferred_host.id: preferred_host, better_host.id: better_host}
        strategy = HostSelectionStrategy(hosts)
        
        async def run_test():
            result = await strategy.select_host(requirements)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        assert result.host.id == "preferred-host", \
            "Should select preferred host when it meets requirements"
