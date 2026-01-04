"""
Property-based test for QEMU deployment operations.

Tests that file permissions are consistently maintained during deployment
to QEMU environments and that deployment operations are reliable.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock

from deployment.environment_manager import QEMUEnvironmentManager, EnvironmentConfig, Connection
from deployment.models import TestArtifact, ArtifactType, Dependency


# Property-based test strategies
environment_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
artifact_names = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd')))
file_permissions = st.sampled_from(["0644", "0755", "0600", "0700", "0664", "0775"])
target_paths = st.text(min_size=1, max_size=200).map(lambda x: f"/tmp/test/{x.replace(' ', '_')}")
artifact_content = st.binary(min_size=1, max_size=10000)


def create_test_artifact(name: str, content: bytes, permissions: str, target_path: str) -> TestArtifact:
    """Create a test artifact with proper validation"""
    import hashlib
    
    return TestArtifact(
        artifact_id=f"test_{hash(name) % 10000}",
        name=name,
        type=ArtifactType.SCRIPT,
        content=content,
        checksum=hashlib.sha256(content).hexdigest(),
        permissions=permissions,
        target_path=target_path,
        dependencies=[]
    )


@given(
    environment_id=environment_ids,
    artifact_name=artifact_names,
    content=artifact_content,
    permissions=file_permissions,
    target_path=target_paths
)
@settings(max_examples=50, deadline=5000)
async def test_file_permission_consistency(environment_id, artifact_name, content, permissions, target_path):
    """
    Property: File permission consistency during QEMU deployment
    
    This test verifies that:
    1. File permissions are correctly set during deployment
    2. Permissions are maintained throughout the deployment process
    3. Different permission values are handled correctly
    4. Permission validation works for various file types
    """
    assume(len(environment_id.strip()) > 0)
    assume(len(artifact_name.strip()) > 0)
    assume(len(target_path.strip()) > 0)
    assume(not target_path.startswith('/'))  # Avoid absolute paths in test
    
    # Create environment configuration
    env_config = EnvironmentConfig(
        environment_id=environment_id,
        environment_type="qemu",
        connection_params={
            "host": "localhost",
            "port": 22,
            "username": "test_user",
            "password": "test_password"
        }
    )
    
    # Create QEMU environment manager
    manager = QEMUEnvironmentManager(env_config)
    
    # Create test artifact with specific permissions
    artifact = create_test_artifact(
        name=artifact_name,
        content=content,
        permissions=permissions,
        target_path=f"/tmp/test/{target_path}"
    )
    
    # Mock the SSH connection and deployment operations
    connection = Connection(environment_id, "ssh")
    connection.is_connected = True
    connection.connection_details = {
        "host": "localhost",
        "port": 22,
        "username": "test_user"
    }
    
    # Track permission operations
    permission_operations = []
    
    # Mock the permission setting method to track operations
    original_set_permissions = manager._set_artifact_permissions
    
    async def mock_set_permissions(conn, art):
        permission_operations.append({
            "artifact_name": art.name,
            "permissions": art.permissions,
            "target_path": art.target_path
        })
        return await original_set_permissions(conn, art)
    
    manager._set_artifact_permissions = mock_set_permissions
    
    # Deploy the artifact
    result = await manager.deploy_artifacts(connection, [artifact])
    
    # Verify deployment succeeded
    assert result is True
    
    # Verify permissions were set correctly
    assert len(permission_operations) == 1
    assert permission_operations[0]["artifact_name"] == artifact_name
    assert permission_operations[0]["permissions"] == permissions
    assert permission_operations[0]["target_path"] == artifact.target_path
    
    # Verify artifact properties are preserved
    assert artifact.permissions == permissions
    assert artifact.name == artifact_name
    assert artifact.content == content


@given(
    environment_id=environment_ids,
    artifact_count=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=30, deadline=5000)
async def test_multiple_artifact_deployment_consistency(environment_id, artifact_count):
    """
    Property: Multiple artifact deployment maintains individual permissions
    
    This test verifies that:
    1. Each artifact maintains its own permissions during batch deployment
    2. Permission setting doesn't interfere between artifacts
    3. All artifacts are deployed successfully in batch operations
    4. Deployment order doesn't affect permission consistency
    """
    assume(len(environment_id.strip()) > 0)
    
    # Create environment configuration
    env_config = EnvironmentConfig(
        environment_id=environment_id,
        environment_type="qemu",
        connection_params={
            "host": "localhost",
            "port": 22,
            "username": "test_user",
            "password": "test_password"
        }
    )
    
    # Create QEMU environment manager
    manager = QEMUEnvironmentManager(env_config)
    
    # Create multiple test artifacts with different permissions
    artifacts = []
    expected_permissions = []
    
    permission_options = ["0644", "0755", "0600", "0700", "0664"]
    
    for i in range(artifact_count):
        permissions = permission_options[i % len(permission_options)]
        content = f"test_content_{i}".encode()
        
        artifact = create_test_artifact(
            name=f"test_artifact_{i}",
            content=content,
            permissions=permissions,
            target_path=f"/tmp/test/artifact_{i}.sh"
        )
        
        artifacts.append(artifact)
        expected_permissions.append(permissions)
    
    # Mock connection
    connection = Connection(environment_id, "ssh")
    connection.is_connected = True
    
    # Track all permission operations
    permission_operations = []
    
    async def mock_set_permissions(conn, art):
        permission_operations.append({
            "artifact_name": art.name,
            "permissions": art.permissions,
            "target_path": art.target_path
        })
    
    manager._set_artifact_permissions = mock_set_permissions
    
    # Deploy all artifacts
    result = await manager.deploy_artifacts(connection, artifacts)
    
    # Verify deployment succeeded
    assert result is True
    
    # Verify all permissions were set correctly
    assert len(permission_operations) == artifact_count
    
    for i, operation in enumerate(permission_operations):
        assert operation["artifact_name"] == f"test_artifact_{i}"
        assert operation["permissions"] == expected_permissions[i]
        assert operation["target_path"] == f"/tmp/test/artifact_{i}.sh"
    
    # Verify original artifacts maintain their properties
    for i, artifact in enumerate(artifacts):
        assert artifact.permissions == expected_permissions[i]
        assert artifact.name == f"test_artifact_{i}"


@given(
    environment_id=environment_ids,
    dependency_count=st.integers(min_value=1, max_value=8)
)
@settings(max_examples=25, deadline=4000)
async def test_dependency_installation_completeness(environment_id, dependency_count):
    """
    Property: Dependency installation completeness in QEMU environments
    
    This test verifies that:
    1. All specified dependencies are installed
    2. Installation commands are executed for each dependency
    3. Verification commands are run for non-optional dependencies
    4. Package managers are used correctly
    """
    assume(len(environment_id.strip()) > 0)
    
    # Create environment configuration
    env_config = EnvironmentConfig(
        environment_id=environment_id,
        environment_type="qemu",
        connection_params={
            "host": "localhost",
            "port": 22,
            "username": "test_user",
            "password": "test_password"
        }
    )
    
    # Create QEMU environment manager
    manager = QEMUEnvironmentManager(env_config)
    
    # Create test dependencies
    dependencies = []
    package_managers = ["apt", "pip", "yum"]
    
    for i in range(dependency_count):
        pkg_manager = package_managers[i % len(package_managers)]
        optional = i % 3 == 0  # Make every 3rd dependency optional
        
        dep = Dependency(
            name=f"test_package_{i}",
            version=f"1.{i}.0" if i % 2 == 0 else None,
            package_manager=pkg_manager,
            optional=optional
        )
        dependencies.append(dep)
    
    # Mock connection
    connection = Connection(environment_id, "ssh")
    connection.is_connected = True
    
    # Track command executions
    executed_commands = []
    
    async def mock_execute_command(conn, command):
        executed_commands.append(command)
    
    manager._execute_command = mock_execute_command
    
    # Install dependencies
    result = await manager.install_dependencies(connection, dependencies)
    
    # Verify installation succeeded
    assert result is True
    
    # Verify commands were executed
    assert len(executed_commands) > 0
    
    # Count expected commands
    expected_install_commands = len(dependencies)
    expected_verify_commands = len([d for d in dependencies if not d.optional])
    
    # Should have at least one command per dependency (install)
    # Plus verification commands for non-optional dependencies
    # Plus potential package manager updates (like apt-get update)
    min_expected_commands = expected_install_commands + expected_verify_commands
    
    # Allow for package manager update commands
    assert len(executed_commands) >= min_expected_commands
    
    # Verify install commands contain dependency names
    install_commands = [cmd for cmd in executed_commands if any(dep.name in cmd for dep in dependencies)]
    assert len(install_commands) >= expected_install_commands


# Synchronous test runners for pytest
def test_file_permission_consistency_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_file_permission_consistency(
        environment_id="test_qemu_env",
        artifact_name="test_script.sh",
        content=b"#!/bin/bash\necho 'test'",
        permissions="0755",
        target_path="scripts/test_script.sh"
    ))


def test_multiple_artifact_deployment_consistency_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_artifact_deployment_consistency(
        environment_id="test_qemu_env",
        artifact_count=3
    ))


def test_dependency_installation_completeness_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_dependency_installation_completeness(
        environment_id="test_qemu_env",
        dependency_count=4
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing QEMU file permission consistency...")
        await test_file_permission_consistency(
            "qemu_test", "test.sh", b"echo test", "0755", "test/test.sh"
        )
        print("✓ Permission consistency test passed")
        
        print("Testing multiple artifact deployment...")
        await test_multiple_artifact_deployment_consistency("qemu_test", 3)
        print("✓ Multiple artifact deployment test passed")
        
        print("Testing dependency installation...")
        await test_dependency_installation_completeness("qemu_test", 3)
        print("✓ Dependency installation test passed")
        
        print("All QEMU deployment tests completed successfully!")
    
    asyncio.run(run_examples())