"""
Property-Based Tests for Deployment Artifact Compatibility

**Feature: test-infrastructure-management, Property 6: Deployment Artifact Compatibility**
**Validates: Requirements 5.1, 6.1**

For any deployment to a QEMU host or physical board, the selected artifacts
SHALL be compatible with the target architecture.
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, assume
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.models.artifact import Artifact, ArtifactType, ArtifactSelection
from infrastructure.models.host import Host, HostStatus
from infrastructure.models.board import (
    Board,
    BoardStatus,
    BoardHealth,
    PowerControlConfig,
    PowerControlMethod,
    HealthLevel,
)
from infrastructure.models.board import PowerStatus
from infrastructure.services.deployment_manager import (
    DeploymentManager,
    VMConfig,
    DeploymentResult,
)


# =============================================================================
# Hypothesis Strategies for generating test data
# =============================================================================

# Architecture compatibility mappings
QEMU_ARCHITECTURES = ["x86_64", "amd64", "arm64", "aarch64", "armv7", "arm", "riscv64"]
BOARD_ARCHITECTURES = ["arm64", "aarch64", "armv7", "arm", "armhf", "riscv64", "riscv"]

# Compatible architecture pairs
ARCH_COMPATIBILITY = {
    "x86_64": ["x86_64", "amd64"],
    "amd64": ["x86_64", "amd64"],
    "arm64": ["arm64", "aarch64"],
    "aarch64": ["arm64", "aarch64"],
    "armv7": ["armv7", "arm", "armhf"],
    "arm": ["armv7", "arm", "armhf"],
    "armhf": ["armv7", "arm", "armhf"],
    "riscv64": ["riscv64", "riscv"],
    "riscv": ["riscv64", "riscv"],
}


def are_architectures_compatible(arch1: str, arch2: str) -> bool:
    """Check if two architectures are compatible."""
    arch1_lower = arch1.lower()
    arch2_lower = arch2.lower()
    
    compatible_archs = ARCH_COMPATIBILITY.get(arch1_lower, [arch1_lower])
    return arch2_lower in compatible_archs


@st.composite
def artifact_strategy(draw, architecture: Optional[str] = None):
    """Generate a valid Artifact."""
    now = datetime.now(timezone.utc)
    arch = architecture or draw(st.sampled_from(QEMU_ARCHITECTURES + BOARD_ARCHITECTURES))
    filename_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    path_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-_."
    hex_chars = "0123456789abcdef"
    
    return Artifact(
        id=draw(st.uuids().map(str)),
        build_id=draw(st.uuids().map(str)),
        artifact_type=draw(st.sampled_from(list(ArtifactType))),
        filename=draw(st.text(min_size=1, max_size=50, alphabet=filename_chars)),
        path=draw(st.text(min_size=1, max_size=100, alphabet=path_chars)),
        size_bytes=draw(st.integers(min_value=1, max_value=10**10)),
        checksum_sha256=draw(st.text(min_size=64, max_size=64, alphabet=hex_chars)),
        architecture=arch,
        created_at=now,
    )


@st.composite
def artifact_list_strategy(draw, architecture: Optional[str] = None, min_size: int = 1, max_size: int = 5):
    """Generate a list of artifacts with the same architecture."""
    arch = architecture or draw(st.sampled_from(QEMU_ARCHITECTURES + BOARD_ARCHITECTURES))
    artifacts = []
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    
    for _ in range(count):
        artifacts.append(draw(artifact_strategy(architecture=arch)))
    
    return artifacts


@st.composite
def resource_utilization_strategy(draw):
    """Generate valid ResourceUtilization."""
    from infrastructure.models.host import ResourceUtilization
    return ResourceUtilization(
        cpu_percent=draw(st.floats(min_value=0.0, max_value=100.0)),
        memory_percent=draw(st.floats(min_value=0.0, max_value=100.0)),
        storage_percent=draw(st.floats(min_value=0.0, max_value=100.0)),
        network_bytes_in=draw(st.integers(min_value=0, max_value=10**12)),
        network_bytes_out=draw(st.integers(min_value=0, max_value=10**12))
    )


@st.composite
def host_strategy(draw, architecture: Optional[str] = None):
    """Generate a valid Host."""
    now = datetime.now(timezone.utc)
    arch = architecture or draw(st.sampled_from(["x86_64", "arm64"]))
    hostname_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
    username_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    return Host(
        id=draw(st.uuids().map(str)),
        hostname=draw(st.text(min_size=1, max_size=50, alphabet=hostname_chars)),
        ip_address=draw(st.ip_addresses(v=4).map(str)),
        ssh_username=draw(st.text(min_size=1, max_size=30, alphabet=username_chars)),
        architecture=arch,
        total_cpu_cores=draw(st.integers(min_value=1, max_value=128)),
        total_memory_mb=draw(st.integers(min_value=1024, max_value=512000)),
        total_storage_gb=draw(st.integers(min_value=10, max_value=10000)),
        created_at=now,
        updated_at=now,
        ssh_port=draw(st.integers(min_value=1, max_value=65535)),
        status=HostStatus.ONLINE,  # Must be online for deployment
        kvm_enabled=draw(st.booleans()),
        nested_virt_enabled=draw(st.booleans()),
        current_utilization=draw(resource_utilization_strategy()),
        running_vm_count=draw(st.integers(min_value=0, max_value=5)),
        max_vms=draw(st.integers(min_value=10, max_value=50)),
        maintenance_mode=False,  # Must not be in maintenance
    )


@st.composite
def board_health_strategy(draw):
    """Generate valid BoardHealth."""
    return BoardHealth(
        connectivity=HealthLevel.HEALTHY,  # Must be healthy for deployment
        temperature_celsius=draw(st.floats(min_value=20.0, max_value=60.0)),
        storage_percent=draw(st.floats(min_value=0.0, max_value=80.0)),
        power_status=PowerStatus.ON,
        last_response_time_ms=draw(st.integers(min_value=1, max_value=1000)),
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
def board_strategy(draw, architecture: Optional[str] = None):
    """Generate a valid Board."""
    now = datetime.now(timezone.utc)
    arch = architecture or draw(st.sampled_from(["arm64", "armv7", "riscv64"]))
    board_types = ["raspberry_pi_4", "raspberry_pi_3", "beaglebone", "riscv_board", "jetson_nano"]
    name_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    serial_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    username_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    return Board(
        id=draw(st.uuids().map(str)),
        name=draw(st.text(min_size=1, max_size=50, alphabet=name_chars)),
        board_type=draw(st.sampled_from(board_types)),
        architecture=arch,
        power_control=draw(power_control_config_strategy()),
        created_at=now,
        updated_at=now,
        serial_number=draw(st.text(min_size=5, max_size=20, alphabet=serial_chars)),
        ip_address=draw(st.ip_addresses(v=4).map(str)),
        ssh_port=draw(st.integers(min_value=1, max_value=65535)),
        ssh_username=draw(st.text(min_size=1, max_size=30, alphabet=username_chars)),
        status=BoardStatus.AVAILABLE,  # Must be available for deployment
        health=draw(board_health_strategy()),
        peripherals=draw(st.lists(st.sampled_from(["gpio", "i2c", "spi", "uart", "usb"]), max_size=3)),
        maintenance_mode=False,  # Must not be in maintenance
    )


@st.composite
def vm_config_strategy(draw, architecture: Optional[str] = None):
    """Generate a valid VMConfig."""
    arch = architecture or draw(st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]))
    name_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    
    return VMConfig(
        name=draw(st.text(min_size=1, max_size=30, alphabet=name_chars)),
        cpu_cores=draw(st.integers(min_value=1, max_value=16)),
        memory_mb=draw(st.integers(min_value=512, max_value=16384)),
        disk_gb=draw(st.integers(min_value=5, max_value=100)),
        architecture=arch,
        enable_kvm=draw(st.booleans()),
        network_mode=draw(st.sampled_from(["nat", "bridge", "none"])),
    )


# =============================================================================
# Property Tests for Deployment Artifact Compatibility
# =============================================================================

class TestDeploymentArtifactCompatibility:
    """
    **Feature: test-infrastructure-management, Property 6: Deployment Artifact Compatibility**
    **Validates: Requirements 5.1, 6.1**
    
    For any deployment to a QEMU host or physical board, the selected artifacts
    SHALL be compatible with the target architecture.
    """

    def test_architecture_compatibility_function(self):
        """Test the architecture compatibility helper function."""
        # Same architecture should be compatible
        assert are_architectures_compatible("x86_64", "x86_64")
        assert are_architectures_compatible("arm64", "arm64")
        
        # Equivalent architectures should be compatible
        assert are_architectures_compatible("x86_64", "amd64")
        assert are_architectures_compatible("amd64", "x86_64")
        assert are_architectures_compatible("arm64", "aarch64")
        assert are_architectures_compatible("aarch64", "arm64")
        assert are_architectures_compatible("armv7", "arm")
        assert are_architectures_compatible("arm", "armhf")
        assert are_architectures_compatible("riscv64", "riscv")
        
        # Incompatible architectures
        assert not are_architectures_compatible("x86_64", "arm64")
        assert not are_architectures_compatible("arm64", "riscv64")
        assert not are_architectures_compatible("armv7", "arm64")

    @given(
        artifact_arch=st.sampled_from(QEMU_ARCHITECTURES),
        vm_arch=st.sampled_from(QEMU_ARCHITECTURES)
    )
    @settings(max_examples=100)
    def test_qemu_architecture_validation_consistency(self, artifact_arch: str, vm_arch: str):
        """
        For any artifact and VM architecture combination, the validation result
        must be consistent with the architecture compatibility mapping.
        """
        dm = DeploymentManager()
        
        # Create mock artifact with the given architecture
        artifact = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture=artifact_arch,
            created_at=datetime.now(timezone.utc),
        )
        
        # Create mock host
        host = Host(
            id="test-host",
            hostname="test-host",
            ip_address="192.168.1.1",
            ssh_username="root",
            architecture="x86_64",  # Host arch doesn't matter for QEMU
            total_cpu_cores=8,
            total_memory_mb=16384,
            total_storage_gb=500,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status=HostStatus.ONLINE,
            kvm_enabled=True,
            current_utilization=MagicMock(cpu_percent=50.0, memory_percent=50.0, storage_percent=50.0),
        )
        
        # Create VM config with the given architecture
        vm_config = VMConfig(
            name="test-vm",
            architecture=vm_arch,
        )
        
        # Validate using the deployment manager's internal method
        result = dm._validate_qemu_architecture([artifact], host, vm_config)
        
        # Result should match our compatibility function
        expected = are_architectures_compatible(artifact_arch, vm_arch)
        assert result == expected, f"Expected {expected} for {artifact_arch} -> {vm_arch}, got {result}"

    @given(
        artifact_arch=st.sampled_from(BOARD_ARCHITECTURES),
        board_arch=st.sampled_from(BOARD_ARCHITECTURES)
    )
    @settings(max_examples=100)
    def test_board_architecture_validation_consistency(self, artifact_arch: str, board_arch: str):
        """
        For any artifact and board architecture combination, the validation result
        must be consistent with the architecture compatibility mapping.
        """
        dm = DeploymentManager()
        
        # Create mock artifact with the given architecture
        artifact = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture=artifact_arch,
            created_at=datetime.now(timezone.utc),
        )
        
        # Create mock board with the given architecture
        board = Board(
            id="test-board",
            name="test-board",
            board_type="raspberry_pi_4",
            architecture=board_arch,
            power_control=PowerControlConfig(method=PowerControlMethod.MANUAL),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status=BoardStatus.AVAILABLE,
            health=BoardHealth(connectivity=HealthLevel.HEALTHY),
        )
        
        # Validate using the deployment manager's internal method
        result = dm._validate_board_architecture([artifact], board)
        
        # Result should match our compatibility function
        expected = are_architectures_compatible(artifact_arch, board_arch)
        assert result == expected, f"Expected {expected} for {artifact_arch} -> {board_arch}, got {result}"

    @given(artifacts=artifact_list_strategy(min_size=1, max_size=3))
    @settings(max_examples=100)
    def test_empty_artifact_list_fails_validation(self, artifacts: List[Artifact]):
        """Empty artifact list should fail validation."""
        dm = DeploymentManager()
        
        # Create mock host and VM config
        host = MagicMock()
        vm_config = VMConfig(name="test-vm", architecture="x86_64")
        
        # Empty list should return False
        assert dm._validate_qemu_architecture([], host, vm_config) == False
        
        # Create mock board
        board = MagicMock()
        board.architecture = "arm64"
        
        # Empty list should return False
        assert dm._validate_board_architecture([], board) == False

    @given(
        host=host_strategy(architecture="x86_64"),
        vm_config=vm_config_strategy(architecture="x86_64"),
    )
    @settings(max_examples=50)
    def test_compatible_qemu_deployment_passes_validation(self, host: Host, vm_config: VMConfig):
        """
        For any QEMU deployment with matching artifact and VM architecture,
        the architecture validation must pass.
        """
        dm = DeploymentManager()
        
        # Create artifacts with same architecture as VM
        artifact = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture=vm_config.architecture,
            created_at=datetime.now(timezone.utc),
        )
        
        # Validation should pass
        result = dm._validate_qemu_architecture([artifact], host, vm_config)
        assert result == True

    @given(board=board_strategy(architecture="arm64"))
    @settings(max_examples=50)
    def test_compatible_board_deployment_passes_validation(self, board: Board):
        """
        For any board deployment with matching artifact and board architecture,
        the architecture validation must pass.
        """
        dm = DeploymentManager()
        
        # Create artifacts with same architecture as board
        artifact = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture=board.architecture,
            created_at=datetime.now(timezone.utc),
        )
        
        # Validation should pass
        result = dm._validate_board_architecture([artifact], board)
        assert result == True

    @given(
        host=host_strategy(architecture="x86_64"),
        vm_config=vm_config_strategy(architecture="x86_64"),
    )
    @settings(max_examples=50)
    def test_incompatible_qemu_deployment_fails_validation(self, host: Host, vm_config: VMConfig):
        """
        For any QEMU deployment with incompatible artifact and VM architecture,
        the architecture validation must fail.
        """
        dm = DeploymentManager()
        
        # Create artifacts with incompatible architecture
        incompatible_arch = "arm64" if vm_config.architecture in ["x86_64", "amd64"] else "x86_64"
        
        artifact = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture=incompatible_arch,
            created_at=datetime.now(timezone.utc),
        )
        
        # Validation should fail
        result = dm._validate_qemu_architecture([artifact], host, vm_config)
        assert result == False

    @given(board=board_strategy(architecture="arm64"))
    @settings(max_examples=50)
    def test_incompatible_board_deployment_fails_validation(self, board: Board):
        """
        For any board deployment with incompatible artifact and board architecture,
        the architecture validation must fail.
        """
        dm = DeploymentManager()
        
        # Create artifacts with incompatible architecture
        incompatible_arch = "x86_64" if board.architecture in ["arm64", "aarch64"] else "arm64"
        
        artifact = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture=incompatible_arch,
            created_at=datetime.now(timezone.utc),
        )
        
        # Validation should fail
        result = dm._validate_board_architecture([artifact], board)
        assert result == False

    @given(
        artifacts=artifact_list_strategy(architecture="arm64", min_size=2, max_size=4),
        board=board_strategy(architecture="arm64"),
    )
    @settings(max_examples=50)
    def test_multiple_artifacts_same_architecture(self, artifacts: List[Artifact], board: Board):
        """
        For any deployment with multiple artifacts of the same architecture,
        validation should use the first artifact's architecture.
        """
        dm = DeploymentManager()
        
        # All artifacts have the same architecture (arm64)
        # Board also has arm64 architecture
        result = dm._validate_board_architecture(artifacts, board)
        
        # Should pass since all architectures match
        assert result == True

    def test_architecture_case_insensitivity(self):
        """Architecture comparison should be case-insensitive."""
        dm = DeploymentManager()
        
        # Create artifact with uppercase architecture
        artifact = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture="ARM64",  # Uppercase
            created_at=datetime.now(timezone.utc),
        )
        
        # Create board with lowercase architecture
        board = Board(
            id="test-board",
            name="test-board",
            board_type="raspberry_pi_4",
            architecture="arm64",  # Lowercase
            power_control=PowerControlConfig(method=PowerControlMethod.MANUAL),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status=BoardStatus.AVAILABLE,
            health=BoardHealth(connectivity=HealthLevel.HEALTHY),
        )
        
        # Should still match
        result = dm._validate_board_architecture([artifact], board)
        assert result == True


class TestDeploymentArchitectureEdgeCases:
    """Test edge cases for deployment architecture validation."""

    def test_aarch64_arm64_equivalence(self):
        """aarch64 and arm64 should be treated as equivalent."""
        dm = DeploymentManager()
        
        # Test aarch64 artifact with arm64 board
        artifact_aarch64 = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture="aarch64",
            created_at=datetime.now(timezone.utc),
        )
        
        board_arm64 = Board(
            id="test-board",
            name="test-board",
            board_type="raspberry_pi_4",
            architecture="arm64",
            power_control=PowerControlConfig(method=PowerControlMethod.MANUAL),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status=BoardStatus.AVAILABLE,
            health=BoardHealth(connectivity=HealthLevel.HEALTHY),
        )
        
        assert dm._validate_board_architecture([artifact_aarch64], board_arm64) == True
        
        # Test arm64 artifact with aarch64 board
        artifact_arm64 = Artifact(
            id="test-artifact",
            build_id="test-build",
            artifact_type=ArtifactType.KERNEL_IMAGE,
            filename="vmlinuz",
            path="/artifacts/vmlinuz",
            size_bytes=10000000,
            checksum_sha256="a" * 64,
            architecture="arm64",
            created_at=datetime.now(timezone.utc),
        )
        
        board_aarch64 = Board(
            id="test-board",
            name="test-board",
            board_type="raspberry_pi_4",
            architecture="aarch64",
            power_control=PowerControlConfig(method=PowerControlMethod.MANUAL),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status=BoardStatus.AVAILABLE,
            health=BoardHealth(connectivity=HealthLevel.HEALTHY),
        )
        
        assert dm._validate_board_architecture([artifact_arm64], board_aarch64) == True

    def test_armv7_arm_armhf_equivalence(self):
        """armv7, arm, and armhf should be treated as equivalent."""
        dm = DeploymentManager()
        
        arm_variants = ["armv7", "arm", "armhf"]
        
        for artifact_arch in arm_variants:
            for board_arch in arm_variants:
                artifact = Artifact(
                    id="test-artifact",
                    build_id="test-build",
                    artifact_type=ArtifactType.KERNEL_IMAGE,
                    filename="vmlinuz",
                    path="/artifacts/vmlinuz",
                    size_bytes=10000000,
                    checksum_sha256="a" * 64,
                    architecture=artifact_arch,
                    created_at=datetime.now(timezone.utc),
                )
                
                board = Board(
                    id="test-board",
                    name="test-board",
                    board_type="beaglebone",
                    architecture=board_arch,
                    power_control=PowerControlConfig(method=PowerControlMethod.MANUAL),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    status=BoardStatus.AVAILABLE,
                    health=BoardHealth(connectivity=HealthLevel.HEALTHY),
                )
                
                result = dm._validate_board_architecture([artifact], board)
                assert result == True, f"Expected {artifact_arch} and {board_arch} to be compatible"

    def test_x86_64_amd64_equivalence(self):
        """x86_64 and amd64 should be treated as equivalent."""
        dm = DeploymentManager()
        
        x86_variants = ["x86_64", "amd64"]
        
        for artifact_arch in x86_variants:
            for vm_arch in x86_variants:
                artifact = Artifact(
                    id="test-artifact",
                    build_id="test-build",
                    artifact_type=ArtifactType.KERNEL_IMAGE,
                    filename="vmlinuz",
                    path="/artifacts/vmlinuz",
                    size_bytes=10000000,
                    checksum_sha256="a" * 64,
                    architecture=artifact_arch,
                    created_at=datetime.now(timezone.utc),
                )
                
                host = MagicMock()
                vm_config = VMConfig(name="test-vm", architecture=vm_arch)
                
                result = dm._validate_qemu_architecture([artifact], host, vm_config)
                assert result == True, f"Expected {artifact_arch} and {vm_arch} to be compatible"

    def test_riscv64_riscv_equivalence(self):
        """riscv64 and riscv should be treated as equivalent."""
        dm = DeploymentManager()
        
        riscv_variants = ["riscv64", "riscv"]
        
        for artifact_arch in riscv_variants:
            for board_arch in riscv_variants:
                artifact = Artifact(
                    id="test-artifact",
                    build_id="test-build",
                    artifact_type=ArtifactType.KERNEL_IMAGE,
                    filename="vmlinuz",
                    path="/artifacts/vmlinuz",
                    size_bytes=10000000,
                    checksum_sha256="a" * 64,
                    architecture=artifact_arch,
                    created_at=datetime.now(timezone.utc),
                )
                
                board = Board(
                    id="test-board",
                    name="test-board",
                    board_type="riscv_board",
                    architecture=board_arch,
                    power_control=PowerControlConfig(method=PowerControlMethod.MANUAL),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    status=BoardStatus.AVAILABLE,
                    health=BoardHealth(connectivity=HealthLevel.HEALTHY),
                )
                
                result = dm._validate_board_architecture([artifact], board)
                assert result == True, f"Expected {artifact_arch} and {board_arch} to be compatible"
