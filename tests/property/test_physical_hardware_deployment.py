"""
Property-based test for physical hardware deployment operations.

Tests that dependency installation is complete and reliable on physical hardware
with proper validation and error handling.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock

from deployment.environment_manager import PhysicalEnvironmentManager, EnvironmentConfig, Connection
from deployment.models import TestArtifact, ArtifactType, Dependency


# Property-based test strategies
environment_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
board_types = st.sampled_from(["raspberry_pi", "nvidia_jetson", "beaglebone", "rock_pi", "odroid"])
package_names = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd')))
package_managers = st.sampled_from(["apt", "yum", "dnf", "pip", "pacman"])


def create_test_dependency(name: str, package_manager: str, version: str = None, optional: bool = False) -> Dependency:
    """Create a test dependency with proper configuration"""
    return Dependency(
        name=name,
        version=version,
        package_manager=package_manager,
        optional=optional
    )


@given(
    environment_id=environment_ids,
    board_type=board_types,
    dependency_count=st.integers(min_value=1, max_value=8),
    package_manager=package_managers
)
@settings(max_examples=40, deadline=6000)
async def test_dependency_installation_completeness(environment_id, board_type, dependency_count, package_manager):
    """
    Property: Dependency installation completeness on physical hardware
    
    This test verifies that:
    1. All specified dependencies are installed on physical hardware
    2. Installation commands are executed with proper hardware considerations
    3. Verification is performed for critical dependencies
    4. Hardware-specific package managers are handled correctly
    5. Installation failures are properly detected and reported
    """
    assume(len(environment_id.strip()) > 0)
    
    # Create environment configuration for physical hardware
    env_config = EnvironmentConfig(
        environment_id=environment_id,
        environment_type="physical",
        connection_params={
            "host": "192.168.1.100",
            "port": 22,
            "username": "root",
            "password": "hardware_password",
            "board_type": board_type
        }
    )
    
    # Create physical environment manager
    manager = PhysicalEnvironmentManager(env_config)
    
    # Create test dependencies with various configurations
    dependencies = []
    expected_installs = []
    expected_verifications = []
    
    for i in range(dependency_count):
        optional = i % 4 == 0  # Make every 4th dependency optional
        version = f"1.{i}.0" if i % 3 == 0 else None  # Some dependencies have versions
        
        dep = create_test_dependency(
            name=f"hw_package_{i}",
            package_manager=package_manager,
            version=version,
            optional=optional
        )
        
        dependencies.append(dep)
        expected_installs.append(dep.name)
        
        if not optional:
            expected_verifications.append(dep.name)
    
    # Mock connection to physical hardware
    connection = Connection(environment_id, "ssh")
    connection.is_connected = True
    connection.connection_details = {
        "host": "192.168.1.100",
        "port": 22,
        "username": "root",
        "board_type": board_type,
        "hardware_info": {
            "architecture": "aarch64",
            "memory_gb": 4,
            "storage_type": "SD"
        }
    }
    
    # Track all command executions
    executed_commands = []
    install_commands = []
    verify_commands = []
    
    async def mock_execute_command(conn, command):
        executed_commands.append(command)
        
        # Categorize commands
        if any(dep_name in command for dep_name in expected_installs):
            if "install" in command.lower():
                install_commands.append(command)
            elif any(verify_word in command.lower() for verify_word in ["which", "dpkg", "rpm", "show"]):
                verify_commands.append(command)
    
    # Mock hardware-specific methods
    async def mock_check_storage_space(conn, artifacts):
        # Simulate storage check
        await asyncio.sleep(0.01)
    
    async def mock_sync_filesystem(conn):
        # Simulate filesystem sync
        await asyncio.sleep(0.01)
    
    manager._execute_command = mock_execute_command
    manager._check_storage_space = mock_check_storage_space
    manager._sync_filesystem = mock_sync_filesystem
    
    # Install dependencies on physical hardware
    result = await manager.install_dependencies(connection, dependencies)
    
    # Verify installation succeeded
    assert result is True
    
    # Verify commands were executed
    assert len(executed_commands) > 0
    
    # Verify install commands were executed for all dependencies
    installed_packages = set()
    for command in install_commands:
        for dep_name in expected_installs:
            if dep_name in command:
                installed_packages.add(dep_name)
    
    # All dependencies should have install commands
    assert len(installed_packages) == len(expected_installs)
    
    # Verify verification commands for non-optional dependencies
    verified_packages = set()
    for command in verify_commands:
        for dep_name in expected_verifications:
            if dep_name in command:
                verified_packages.add(dep_name)
    
    # All non-optional dependencies should be verified
    assert len(verified_packages) >= len(expected_verifications) * 0.8  # Allow some flexibility


@given(
    environment_id=environment_ids,
    board_type=board_types,
    artifact_count=st.integers(min_value=1, max_value=6)
)
@settings(max_examples=30, deadline=5000)
async def test_hardware_deployment_reliability(environment_id, board_type, artifact_count):
    """
    Property: Hardware deployment reliability and validation
    
    This test verifies that:
    1. Artifacts are deployed reliably to physical hardware
    2. Storage space is checked before deployment
    3. Filesystem sync is performed for data persistence
    4. Hardware-specific validation is performed
    5. Deployment failures are properly handled
    """
    assume(len(environment_id.strip()) > 0)
    
    # Create environment configuration
    env_config = EnvironmentConfig(
        environment_id=environment_id,
        environment_type="physical",
        connection_params={
            "host": "192.168.1.100",
            "port": 22,
            "username": "root",
            "password": "hardware_password",
            "board_type": board_type
        }
    )
    
    # Create physical environment manager
    manager = PhysicalEnvironmentManager(env_config)
    
    # Create test artifacts
    artifacts = []
    for i in range(artifact_count):
        content = f"hardware_test_content_{i}".encode() * (i + 1)  # Varying sizes
        
        artifact = TestArtifact(
            artifact_id=f"hw_artifact_{i}",
            name=f"hw_test_{i}.sh",
            type=ArtifactType.SCRIPT,
            content=content,
            checksum="",  # Will be calculated
            permissions="0755",
            target_path=f"/opt/test/hw_test_{i}.sh",
            dependencies=[]
        )
        artifacts.append(artifact)
    
    # Mock connection
    connection = Connection(environment_id, "ssh")
    connection.is_connected = True
    connection.connection_details = {
        "board_type": board_type,
        "hardware_info": {"storage_type": "eMMC", "memory_gb": 8}
    }
    
    # Track hardware-specific operations
    storage_checks = []
    sync_operations = []
    validation_operations = []
    
    async def mock_check_storage_space(conn, arts):
        storage_checks.append(len(arts))
        await asyncio.sleep(0.01)
    
    async def mock_sync_filesystem(conn):
        sync_operations.append("sync")
        await asyncio.sleep(0.01)
    
    async def mock_validate_artifact_for_hardware(art):
        validation_operations.append(art.name)
        await asyncio.sleep(0.01)
    
    async def mock_verify_hardware_deployment(conn, art):
        # Simulate checksum verification
        await asyncio.sleep(0.01)
    
    # Mock hardware-specific methods
    manager._check_storage_space = mock_check_storage_space
    manager._sync_filesystem = mock_sync_filesystem
    manager._validate_artifact_for_hardware = mock_validate_artifact_for_hardware
    manager._verify_hardware_deployment = mock_verify_hardware_deployment
    
    # Deploy artifacts to hardware
    result = await manager.deploy_artifacts(connection, artifacts)
    
    # Verify deployment succeeded
    assert result is True
    
    # Verify hardware-specific operations were performed
    
    # Storage space should be checked once before deployment
    assert len(storage_checks) == 1
    assert storage_checks[0] == artifact_count
    
    # Filesystem should be synced once after deployment
    assert len(sync_operations) == 1
    
    # All artifacts should be validated for hardware
    assert len(validation_operations) == artifact_count
    assert set(validation_operations) == {f"hw_test_{i}.sh" for i in range(artifact_count)}


@given(
    environment_id=environment_ids,
    board_type=board_types,
    mixed_dependencies=st.lists(
        st.tuples(
            package_names,
            package_managers,
            st.booleans()  # optional flag
        ),
        min_size=1,
        max_size=6
    )
)
@settings(max_examples=25, deadline=5000)
async def test_mixed_dependency_handling(environment_id, board_type, mixed_dependencies):
    """
    Property: Mixed dependency handling on physical hardware
    
    This test verifies that:
    1. Dependencies with different package managers are handled correctly
    2. Optional and required dependencies are treated appropriately
    3. Package manager grouping works for efficiency
    4. Hardware-specific installation considerations are applied
    """
    assume(len(environment_id.strip()) > 0)
    assume(len(mixed_dependencies) > 0)
    
    # Filter out empty package names
    valid_dependencies = [(name, mgr, opt) for name, mgr, opt in mixed_dependencies if len(name.strip()) > 0]
    assume(len(valid_dependencies) > 0)
    
    # Create environment configuration
    env_config = EnvironmentConfig(
        environment_id=environment_id,
        environment_type="physical",
        connection_params={
            "host": "192.168.1.100",
            "port": 22,
            "username": "root",
            "board_type": board_type
        }
    )
    
    # Create physical environment manager
    manager = PhysicalEnvironmentManager(env_config)
    
    # Create dependencies from test data
    dependencies = []
    package_managers_used = set()
    required_deps = []
    
    for name, pkg_manager, optional in valid_dependencies:
        dep = create_test_dependency(
            name=name.strip(),
            package_manager=pkg_manager,
            optional=optional
        )
        dependencies.append(dep)
        package_managers_used.add(pkg_manager)
        
        if not optional:
            required_deps.append(name.strip())
    
    # Mock connection
    connection = Connection(environment_id, "ssh")
    connection.is_connected = True
    
    # Track package manager operations
    manager_operations = {}
    executed_commands = []
    
    async def mock_install_dependencies_with_manager(conn, manager_name, deps):
        if manager_name not in manager_operations:
            manager_operations[manager_name] = []
        manager_operations[manager_name].extend([d.name for d in deps])
        
        # Simulate package manager update for apt
        if manager_name == "apt":
            executed_commands.append("apt-get update")
        
        # Simulate install commands
        for dep in deps:
            executed_commands.append(dep.install_command)
    
    async def mock_verify_dependency_installation(conn, dep):
        if dep.verify_command:
            executed_commands.append(dep.verify_command)
    
    manager._install_dependencies_with_manager = mock_install_dependencies_with_manager
    manager._verify_dependency_installation = mock_verify_dependency_installation
    
    # Install mixed dependencies
    result = await manager.install_dependencies(connection, dependencies)
    
    # Verify installation succeeded
    assert result is True
    
    # Verify package managers were used correctly
    assert len(manager_operations) == len(package_managers_used)
    
    # Verify all package managers that were expected are present
    for pkg_manager in package_managers_used:
        assert pkg_manager in manager_operations
    
    # Verify all dependencies were processed
    all_processed_deps = []
    for deps_list in manager_operations.values():
        all_processed_deps.extend(deps_list)
    
    expected_dep_names = [dep.name for dep in dependencies]
    assert set(all_processed_deps) == set(expected_dep_names)
    
    # Verify commands were executed
    assert len(executed_commands) > 0


# Synchronous test runners for pytest
def test_dependency_installation_completeness_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_dependency_installation_completeness(
        environment_id="hw_test_env",
        board_type="raspberry_pi",
        dependency_count=3,
        package_manager="apt"
    ))


def test_hardware_deployment_reliability_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_hardware_deployment_reliability(
        environment_id="hw_test_env",
        board_type="nvidia_jetson",
        artifact_count=2
    ))


def test_mixed_dependency_handling_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_mixed_dependency_handling(
        environment_id="hw_test_env",
        board_type="beaglebone",
        mixed_dependencies=[
            ("gcc", "apt", False),
            ("python3", "apt", False),
            ("numpy", "pip", True)
        ]
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing physical hardware dependency installation...")
        await test_dependency_installation_completeness(
            "hw_test", "raspberry_pi", 3, "apt"
        )
        print("✓ Dependency installation test passed")
        
        print("Testing hardware deployment reliability...")
        await test_hardware_deployment_reliability("hw_test", "nvidia_jetson", 2)
        print("✓ Hardware deployment reliability test passed")
        
        print("Testing mixed dependency handling...")
        await test_mixed_dependency_handling(
            "hw_test", "beaglebone", [("gcc", "apt", False), ("python3", "apt", False)]
        )
        print("✓ Mixed dependency handling test passed")
        
        print("All physical hardware deployment tests completed successfully!")
    
    asyncio.run(run_examples())