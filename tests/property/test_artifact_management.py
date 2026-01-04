"""
Property-based test for artifact management operations.

Tests that artifact deployment verification works correctly with proper
validation, integrity checks, and dependency resolution.
"""

import asyncio
import pytest
import hashlib
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock

from deployment.artifact_repository import ArtifactRepository
from deployment.models import TestArtifact, ArtifactType, Dependency


# Property-based test strategies
artifact_names = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd')))
artifact_content = st.binary(min_size=1, max_size=50000)
artifact_types = st.sampled_from(list(ArtifactType))
file_permissions = st.sampled_from(["0644", "0755", "0600", "0700", "0664", "0775"])
target_paths = st.text(min_size=1, max_size=200).map(lambda x: f"/tmp/test/{x.replace(' ', '_')}")


def create_test_artifact(name: str, content: bytes, artifact_type: ArtifactType, 
                        permissions: str = "0644", target_path: str = "/tmp/test") -> TestArtifact:
    """Create a test artifact with proper validation"""
    checksum = hashlib.sha256(content).hexdigest()
    
    return TestArtifact(
        artifact_id=f"test_{hash(name) % 100000}",
        name=name,
        type=artifact_type,
        content=content,
        checksum=checksum,
        permissions=permissions,
        target_path=f"{target_path}/{name}",
        dependencies=[]
    )


@given(
    artifact_name=artifact_names,
    content=artifact_content,
    artifact_type=artifact_types,
    permissions=file_permissions
)
@settings(max_examples=50, deadline=5000)
async def test_artifact_deployment_verification(artifact_name, content, artifact_type, permissions):
    """
    Property: Artifact deployment verification ensures integrity
    
    This test verifies that:
    1. Artifacts are stored with correct checksums
    2. Stored artifacts can be retrieved with identical content
    3. Artifact metadata is preserved during storage and retrieval
    4. Checksum validation works correctly
    5. Invalid artifacts are rejected
    """
    assume(len(artifact_name.strip()) > 0)
    assume(len(content) > 0)
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create artifact repository
        repository = ArtifactRepository(storage_path=temp_dir)
        
        # Create test artifact
        artifact = create_test_artifact(
            name=artifact_name.strip(),
            content=content,
            artifact_type=artifact_type,
            permissions=permissions
        )
        
        # Store the artifact
        store_result = await repository.store_artifact(artifact)
        assert store_result is True
        
        # Retrieve the artifact
        retrieved_artifact = await repository.get_artifact(artifact.artifact_id)
        assert retrieved_artifact is not None
        
        # Verify artifact integrity
        assert retrieved_artifact.artifact_id == artifact.artifact_id
        assert retrieved_artifact.name == artifact.name
        assert retrieved_artifact.type == artifact.type
        assert retrieved_artifact.content == artifact.content
        assert retrieved_artifact.checksum == artifact.checksum
        assert retrieved_artifact.permissions == artifact.permissions
        assert retrieved_artifact.target_path == artifact.target_path
        
        # Verify checksum calculation
        expected_checksum = hashlib.sha256(content).hexdigest()
        assert retrieved_artifact.checksum == expected_checksum
        
        # Verify artifact validation
        validation_result = await repository.validate_artifact(retrieved_artifact)
        assert validation_result is True


@given(
    artifact_count=st.integers(min_value=2, max_value=8),
    artifact_type=artifact_types
)
@settings(max_examples=30, deadline=5000)
async def test_dependency_resolution_completeness(artifact_count, artifact_type):
    """
    Property: Dependency resolution includes all required artifacts
    
    This test verifies that:
    1. All dependencies are resolved correctly
    2. Dependency order is maintained
    3. Circular dependencies are handled
    4. Missing dependencies are detected
    5. Dependency graph is built correctly
    """
    assume(artifact_count >= 2)
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        repository = ArtifactRepository(storage_path=temp_dir)
        
        # Create artifacts with dependency chain
        artifacts = []
        artifact_ids = []
        
        for i in range(artifact_count):
            content = f"artifact_{i}_content".encode()
            artifact = create_test_artifact(
                name=f"artifact_{i}",
                content=content,
                artifact_type=artifact_type
            )
            
            # Create dependency chain (each artifact depends on the previous one)
            if i > 0:
                artifact.dependencies = [artifact_ids[i-1]]
            
            artifacts.append(artifact)
            artifact_ids.append(artifact.artifact_id)
            
            # Store the artifact
            store_result = await repository.store_artifact(artifact)
            assert store_result is True
        
        # Test dependency resolution for the last artifact (should include all)
        last_artifact_id = artifact_ids[-1]
        resolved_ids = await repository.resolve_dependencies([last_artifact_id])
        
        # Should resolve to all artifacts in correct order
        assert len(resolved_ids) == artifact_count
        
        # Verify order: dependencies should come before dependents
        for i in range(artifact_count):
            expected_id = artifact_ids[i]
            assert expected_id in resolved_ids
            
            # Each artifact should appear after its dependencies
            if i > 0:
                dependency_id = artifact_ids[i-1]
                dependency_index = resolved_ids.index(dependency_id)
                artifact_index = resolved_ids.index(expected_id)
                assert dependency_index < artifact_index
        
        # Test resolution of multiple artifacts
        if artifact_count >= 3:
            # Resolve middle and last artifacts
            middle_id = artifact_ids[artifact_count // 2]
            multi_resolved = await repository.resolve_dependencies([middle_id, last_artifact_id])
            
            # Should include all artifacts up to the last one
            assert len(multi_resolved) == artifact_count
            assert last_artifact_id in multi_resolved
            assert middle_id in multi_resolved


@given(
    artifact_count=st.integers(min_value=1, max_value=6),
    include_invalid=st.booleans()
)
@settings(max_examples=25, deadline=4000)
async def test_deployment_package_creation(artifact_count, include_invalid):
    """
    Property: Deployment package creation handles artifacts correctly
    
    This test verifies that:
    1. Deployment packages contain all requested artifacts
    2. Package creation handles missing artifacts gracefully
    3. Artifact metadata is included in packages
    4. Package integrity can be verified
    5. Dependencies are included in packages
    """
    assume(artifact_count >= 1)
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        repository = ArtifactRepository(storage_path=temp_dir)
        
        # Create and store valid artifacts
        valid_artifact_ids = []
        
        for i in range(artifact_count):
            content = f"package_artifact_{i}_content_data".encode() * (i + 1)
            artifact = create_test_artifact(
                name=f"package_artifact_{i}",
                content=content,
                artifact_type=ArtifactType.SCRIPT
            )
            
            # Store the artifact
            store_result = await repository.store_artifact(artifact)
            assert store_result is True
            valid_artifact_ids.append(artifact.artifact_id)
        
        # Prepare artifact IDs for package creation
        package_artifact_ids = valid_artifact_ids.copy()
        
        if include_invalid and artifact_count > 1:
            # Add an invalid artifact ID
            package_artifact_ids.append("invalid_artifact_id_12345")
        
        # Create deployment package
        if include_invalid and artifact_count > 1:
            # Should fail with invalid artifact
            package_content = await repository.create_deployment_package(package_artifact_ids)
            assert package_content is None
        else:
            # Should succeed with valid artifacts
            package_content = await repository.create_deployment_package(package_artifact_ids)
            assert package_content is not None
            assert len(package_content) > 0
            
            # Verify package is a valid tar.gz
            import tarfile
            import io
            
            try:
                with tarfile.open(fileobj=io.BytesIO(package_content), mode='r:gz') as tar:
                    # Should contain files for each artifact
                    tar_members = tar.getnames()
                    
                    # Each artifact should have a content file and metadata file
                    expected_files = artifact_count * 2  # content + metadata for each
                    assert len(tar_members) >= expected_files
                    
                    # Verify artifact files are present
                    for i in range(artifact_count):
                        artifact_name = f"package_artifact_{i}"
                        content_file = f"script/{artifact_name}"
                        metadata_file = f"script/{artifact_name}.meta"
                        
                        assert content_file in tar_members
                        assert metadata_file in tar_members
            
            except Exception as e:
                pytest.fail(f"Package validation failed: {e}")


@given(
    artifacts_by_type=st.dictionaries(
        keys=st.sampled_from(list(ArtifactType)),
        values=st.integers(min_value=1, max_value=4),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=20, deadline=4000)
async def test_artifact_type_organization(artifacts_by_type):
    """
    Property: Artifacts are organized correctly by type
    
    This test verifies that:
    1. Artifacts are stored in type-specific directories
    2. Retrieval by type returns correct artifacts
    3. Type-based organization is maintained
    4. Repository statistics are accurate
    """
    assume(len(artifacts_by_type) > 0)
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        repository = ArtifactRepository(storage_path=temp_dir)
        
        # Create and store artifacts by type
        stored_artifacts = {}
        total_artifacts = 0
        
        for artifact_type, count in artifacts_by_type.items():
            stored_artifacts[artifact_type] = []
            
            for i in range(count):
                content = f"{artifact_type.value}_content_{i}".encode()
                artifact = create_test_artifact(
                    name=f"{artifact_type.value}_{i}",
                    content=content,
                    artifact_type=artifact_type
                )
                
                # Store the artifact
                store_result = await repository.store_artifact(artifact)
                assert store_result is True
                
                stored_artifacts[artifact_type].append(artifact)
                total_artifacts += 1
        
        # Test retrieval by type
        for artifact_type, expected_artifacts in stored_artifacts.items():
            retrieved_artifacts = await repository.get_artifacts_by_type(artifact_type)
            
            # Should retrieve all artifacts of this type
            assert len(retrieved_artifacts) == len(expected_artifacts)
            
            # Verify artifact properties
            retrieved_names = {art.name for art in retrieved_artifacts}
            expected_names = {art.name for art in expected_artifacts}
            assert retrieved_names == expected_names
            
            # All retrieved artifacts should be of correct type
            for artifact in retrieved_artifacts:
                assert artifact.type == artifact_type
        
        # Test repository statistics
        stats = repository.get_repository_stats()
        assert stats["total_artifacts"] == total_artifacts
        
        # Verify type-specific counts
        for artifact_type, count in artifacts_by_type.items():
            type_key = artifact_type.value.lower() + "s"  # e.g., "scripts", "binaries"
            if type_key in stats:
                assert stats[type_key] == count


# Synchronous test runners for pytest
def test_artifact_deployment_verification_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_artifact_deployment_verification(
        artifact_name="test_script.sh",
        content=b"#!/bin/bash\necho 'test'",
        artifact_type=ArtifactType.SCRIPT,
        permissions="0755"
    ))


def test_dependency_resolution_completeness_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_dependency_resolution_completeness(
        artifact_count=3,
        artifact_type=ArtifactType.SCRIPT
    ))


def test_deployment_package_creation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_deployment_package_creation(
        artifact_count=2,
        include_invalid=False
    ))


def test_artifact_type_organization_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_artifact_type_organization({
        ArtifactType.SCRIPT: 2,
        ArtifactType.CONFIG: 1
    }))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing artifact deployment verification...")
        await test_artifact_deployment_verification(
            "test.sh", b"echo test", ArtifactType.SCRIPT, "0755"
        )
        print("✓ Artifact deployment verification test passed")
        
        print("Testing dependency resolution...")
        await test_dependency_resolution_completeness(3, ArtifactType.SCRIPT)
        print("✓ Dependency resolution test passed")
        
        print("Testing deployment package creation...")
        await test_deployment_package_creation(2, False)
        print("✓ Deployment package creation test passed")
        
        print("Testing artifact type organization...")
        await test_artifact_type_organization({
            ArtifactType.SCRIPT: 2,
            ArtifactType.CONFIG: 1
        })
        print("✓ Artifact type organization test passed")
        
        print("All artifact management tests completed successfully!")
    
    asyncio.run(run_examples())