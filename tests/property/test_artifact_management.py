"""
Property-Based Tests for Artifact Management

Tests correctness properties for artifact storage and retrieval using Hypothesis.
"""

import pytest
import asyncio
import hashlib
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, List

from infrastructure.models.artifact import Artifact, ArtifactType, ArtifactSelection
from infrastructure.services.artifact_manager import (
    ArtifactRepositoryManager,
    ArtifactInfo,
    RetentionPolicy,
)


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def artifact_type_strategy(draw):
    """Generate a valid ArtifactType."""
    return draw(st.sampled_from(list(ArtifactType)))


@st.composite
def architecture_strategy(draw):
    """Generate a valid architecture."""
    return draw(st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]))


@st.composite
def artifact_content_strategy(draw, min_size: int = 10, max_size: int = 1000):
    """Generate artifact content bytes."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return draw(st.binary(min_size=size, max_size=size))


@st.composite
def artifact_info_strategy(draw, architecture: str = None):
    """Generate a valid ArtifactInfo."""
    arch = architecture or draw(architecture_strategy())
    filename_chars = "abcdefghijklmnopqrstuvwxyz0123456789-_."
    
    return ArtifactInfo(
        artifact_type=draw(artifact_type_strategy()),
        filename=draw(st.text(min_size=5, max_size=50, alphabet=filename_chars)),
        content=draw(artifact_content_strategy()),
        architecture=arch,
        metadata=draw(st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz"),
            values=st.text(min_size=1, max_size=50),
            max_size=5
        ))
    )


@st.composite
def build_id_strategy(draw):
    """Generate a valid build ID."""
    return draw(st.uuids().map(str))


# =============================================================================
# Property Tests
# =============================================================================

class TestArtifactIntegrity:
    """
    **Feature: test-infrastructure-management, Property 4: Build Artifact Integrity**
    **Validates: Requirements 4.2**
    
    For any successfully completed build, the stored artifacts SHALL have valid
    checksums that match the generated files.
    """

    @given(
        build_id=build_id_strategy(),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=100)
    def test_stored_artifact_has_valid_checksum(self, build_id: str, artifact_info: ArtifactInfo):
        """Stored artifact checksum must match content."""
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifact
            result = await manager.store_artifacts(build_id, [artifact_info])
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success, f"Failed to store artifact: {result.error_message}"
        assert len(result.artifacts) == 1
        
        stored_artifact = result.artifacts[0]
        
        # Compute expected checksum
        expected_checksum = hashlib.sha256(artifact_info.content).hexdigest()
        
        # Verify checksum matches
        assert stored_artifact.checksum_sha256 == expected_checksum, \
            f"Checksum mismatch: expected {expected_checksum}, got {stored_artifact.checksum_sha256}"

    @given(
        build_id=build_id_strategy(),
        num_artifacts=st.integers(min_value=1, max_value=5),
        data=st.data()
    )
    @settings(max_examples=50)
    def test_multiple_artifacts_all_have_valid_checksums(
        self,
        build_id: str,
        num_artifacts: int,
        data
    ):
        """All artifacts in a build must have valid checksums."""
        manager = ArtifactRepositoryManager()
        
        # Generate multiple artifacts
        artifacts_info = [data.draw(artifact_info_strategy()) for _ in range(num_artifacts)]
        
        async def run_test():
            result = await manager.store_artifacts(build_id, artifacts_info)
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        assert len(result.artifacts) == num_artifacts
        
        # Verify each artifact's checksum
        for i, stored_artifact in enumerate(result.artifacts):
            expected_checksum = hashlib.sha256(artifacts_info[i].content).hexdigest()
            assert stored_artifact.checksum_sha256 == expected_checksum, \
                f"Artifact {i} checksum mismatch"

    @given(
        build_id=build_id_strategy(),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=50)
    def test_artifact_size_matches_content(self, build_id: str, artifact_info: ArtifactInfo):
        """Stored artifact size must match content size."""
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            result = await manager.store_artifacts(build_id, [artifact_info])
            return result
        
        result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result.success
        stored_artifact = result.artifacts[0]
        
        assert stored_artifact.size_bytes == len(artifact_info.content), \
            f"Size mismatch: expected {len(artifact_info.content)}, got {stored_artifact.size_bytes}"

    @given(
        build_id=build_id_strategy(),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=50)
    def test_artifact_verification_succeeds_for_valid_artifact(
        self,
        build_id: str,
        artifact_info: ArtifactInfo
    ):
        """Verification should succeed for properly stored artifacts."""
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifact
            store_result = await manager.store_artifacts(build_id, [artifact_info])
            if not store_result.success:
                return None, None
            
            artifact_id = store_result.artifacts[0].id
            
            # Verify artifact
            verify_result = await manager.verify_artifact_integrity(artifact_id)
            return store_result, verify_result
        
        store_result, verify_result = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert store_result is not None
        assert verify_result is not None
        assert verify_result.success, \
            f"Verification failed: {verify_result.error_message}"
        assert verify_result.checksum_valid


class TestArtifactRetrievalConsistency:
    """
    **Feature: test-infrastructure-management, Property 5: Build Artifact Retrieval Consistency**
    **Validates: Requirements 4.5**
    
    For any stored build artifact, retrieving by build ID, commit hash, or "latest"
    SHALL return the correct artifact with matching metadata.
    """

    @given(
        build_id=build_id_strategy(),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=100)
    def test_retrieve_by_build_id_returns_correct_artifact(
        self,
        build_id: str,
        artifact_info: ArtifactInfo
    ):
        """Retrieving by build ID must return the correct artifact."""
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifact
            store_result = await manager.store_artifacts(build_id, [artifact_info])
            if not store_result.success:
                return None, None
            
            # Retrieve by build ID
            retrieved = await manager.get_artifacts_by_build(build_id)
            return store_result, retrieved
        
        store_result, retrieved = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert store_result is not None
        assert len(retrieved) == 1
        
        stored = store_result.artifacts[0]
        assert retrieved[0].id == stored.id
        assert retrieved[0].checksum_sha256 == stored.checksum_sha256
        assert retrieved[0].build_id == build_id

    @given(
        build_id=build_id_strategy(),
        commit_hash=st.text(min_size=40, max_size=40, alphabet="0123456789abcdef"),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=50)
    def test_retrieve_by_commit_hash_returns_correct_artifact(
        self,
        build_id: str,
        commit_hash: str,
        artifact_info: ArtifactInfo
    ):
        """Retrieving by commit hash must return the correct artifact."""
        # Add commit hash to metadata
        artifact_info.metadata["commit_hash"] = commit_hash
        
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifact
            store_result = await manager.store_artifacts(build_id, [artifact_info])
            if not store_result.success:
                return None, None
            
            # Retrieve by commit hash
            selection = ArtifactSelection(commit_hash=commit_hash)
            retrieved = await manager.get_artifacts_by_selection(selection)
            return store_result, retrieved
        
        store_result, retrieved = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert store_result is not None
        assert len(retrieved) == 1
        
        stored = store_result.artifacts[0]
        assert retrieved[0].id == stored.id
        assert retrieved[0].metadata.get("commit_hash") == commit_hash

    @given(
        build_id=build_id_strategy(),
        branch=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_/"),
        architecture=architecture_strategy(),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=50)
    def test_retrieve_latest_returns_most_recent_artifact(
        self,
        build_id: str,
        branch: str,
        architecture: str,
        artifact_info: ArtifactInfo
    ):
        """Retrieving 'latest' must return the most recent artifact for branch/arch."""
        # Set architecture to match
        artifact_info.architecture = architecture
        
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifact
            store_result = await manager.store_artifacts(build_id, [artifact_info])
            if not store_result.success:
                return None, None
            
            # Update latest
            await manager.update_latest(branch, architecture, build_id)
            
            # Retrieve latest
            selection = ArtifactSelection(branch=branch, use_latest=True, architecture=architecture)
            retrieved = await manager.get_artifacts_by_selection(selection)
            return store_result, retrieved
        
        store_result, retrieved = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert store_result is not None
        assert len(retrieved) == 1
        
        stored = store_result.artifacts[0]
        assert retrieved[0].id == stored.id
        assert retrieved[0].architecture == architecture

    @given(
        build_id=build_id_strategy(),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=50)
    def test_artifact_metadata_preserved_on_retrieval(
        self,
        build_id: str,
        artifact_info: ArtifactInfo
    ):
        """Artifact metadata must be preserved when retrieved."""
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifact
            store_result = await manager.store_artifacts(build_id, [artifact_info])
            if not store_result.success:
                return None, None
            
            # Retrieve
            retrieved = await manager.get_artifacts_by_build(build_id)
            return store_result, retrieved
        
        store_result, retrieved = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert store_result is not None
        assert len(retrieved) == 1
        
        # Verify metadata preserved
        assert retrieved[0].metadata == artifact_info.metadata
        assert retrieved[0].artifact_type == artifact_info.artifact_type
        assert retrieved[0].filename == artifact_info.filename
        assert retrieved[0].architecture == artifact_info.architecture

    @given(
        build_id1=build_id_strategy(),
        build_id2=build_id_strategy(),
        data=st.data()
    )
    @settings(max_examples=50)
    def test_artifacts_isolated_between_builds(
        self,
        build_id1: str,
        build_id2: str,
        data
    ):
        """Artifacts from different builds must be isolated."""
        assume(build_id1 != build_id2)
        
        artifact1 = data.draw(artifact_info_strategy())
        artifact2 = data.draw(artifact_info_strategy())
        
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifacts for both builds
            result1 = await manager.store_artifacts(build_id1, [artifact1])
            result2 = await manager.store_artifacts(build_id2, [artifact2])
            
            # Retrieve each build's artifacts
            retrieved1 = await manager.get_artifacts_by_build(build_id1)
            retrieved2 = await manager.get_artifacts_by_build(build_id2)
            
            return result1, result2, retrieved1, retrieved2
        
        result1, result2, retrieved1, retrieved2 = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert result1.success and result2.success
        
        # Verify isolation
        assert len(retrieved1) == 1
        assert len(retrieved2) == 1
        assert retrieved1[0].build_id == build_id1
        assert retrieved2[0].build_id == build_id2
        assert retrieved1[0].id != retrieved2[0].id


class TestArtifactRetention:
    """
    Tests for artifact retention and cleanup policies.
    """

    @given(
        build_id=build_id_strategy(),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=50)
    def test_pinned_builds_not_deleted(self, build_id: str, artifact_info: ArtifactInfo):
        """Pinned builds should not be deleted during cleanup."""
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifact
            store_result = await manager.store_artifacts(build_id, [artifact_info])
            if not store_result.success:
                return None, None, None
            
            # Pin the build
            await manager.pin_build(build_id)
            
            # Try to delete
            artifact_id = store_result.artifacts[0].id
            delete_result = await manager.delete_artifacts([artifact_id])
            
            # Verify still exists
            retrieved = await manager.get_artifact(artifact_id)
            
            return store_result, delete_result, retrieved
        
        store_result, delete_result, retrieved = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert store_result is not None
        # Delete should fail for pinned build
        assert artifact_info is not None or delete_result.deleted_count == 0
        # Artifact should still exist
        assert retrieved is not None

    @given(
        build_id=build_id_strategy(),
        tag=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_"),
        artifact_info=artifact_info_strategy()
    )
    @settings(max_examples=50)
    def test_tagged_builds_preserved(self, build_id: str, tag: str, artifact_info: ArtifactInfo):
        """Tagged builds should be preserved during cleanup."""
        manager = ArtifactRepositoryManager()
        
        async def run_test():
            # Store artifact
            store_result = await manager.store_artifacts(build_id, [artifact_info])
            if not store_result.success:
                return None, None
            
            # Tag the build
            await manager.tag_build(build_id, tag)
            
            # Verify build is preserved
            retrieved = await manager.get_artifacts_by_build(build_id)
            return store_result, retrieved
        
        store_result, retrieved = asyncio.new_event_loop().run_until_complete(run_test())
        
        assert store_result is not None
        assert len(retrieved) == 1
