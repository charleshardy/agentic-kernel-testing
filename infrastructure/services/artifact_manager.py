"""
Artifact Repository Manager Service

Manages build artifact storage, retrieval, and lifecycle.
"""

import hashlib
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from infrastructure.models.artifact import Artifact, ArtifactType, ArtifactSelection
from infrastructure.models.build_server import BuildJob


@dataclass
class ArtifactInfo:
    """Information about an artifact to be stored."""
    artifact_type: ArtifactType
    filename: str
    content: bytes
    architecture: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class StoreResult:
    """Result of storing artifacts."""
    success: bool
    artifacts: List[Artifact] = field(default_factory=list)
    error_message: Optional[str] = None
    failed_artifacts: List[str] = field(default_factory=list)


@dataclass
class DeleteResult:
    """Result of deleting artifacts."""
    success: bool
    deleted_count: int = 0
    error_message: Optional[str] = None
    failed_ids: List[str] = field(default_factory=list)


@dataclass
class CleanupResult:
    """Result of artifact cleanup."""
    success: bool
    deleted_count: int = 0
    freed_bytes: int = 0
    preserved_count: int = 0
    error_message: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of artifact verification."""
    success: bool
    artifact_id: str
    checksum_valid: bool = False
    file_exists: bool = False
    error_message: Optional[str] = None


@dataclass
class RetentionPolicy:
    """Artifact retention policy configuration."""
    retention_days: int = 30
    preserve_tagged: bool = True
    preserve_pinned: bool = True
    min_builds_to_keep: int = 5
    max_storage_gb: Optional[int] = None


class ArtifactRepositoryManager:
    """
    Manages build artifact storage and retrieval.
    
    Handles:
    - Artifact storage with checksum verification
    - Retrieval by build ID, commit hash, or "latest"
    - Cleanup and retention policy enforcement
    - Artifact integrity verification
    """

    def __init__(
        self,
        storage_path: str = "/var/lib/artifacts",
        retention_policy: Optional[RetentionPolicy] = None,
    ):
        self._storage_path = Path(storage_path)
        self._retention_policy = retention_policy or RetentionPolicy()
        
        # In-memory artifact index
        self._artifacts: Dict[str, Artifact] = {}
        self._build_artifacts: Dict[str, List[str]] = {}  # build_id -> artifact_ids
        self._branch_latest: Dict[str, Dict[str, str]] = {}  # branch -> arch -> build_id
        
        # Tags and pins
        self._tagged_builds: Dict[str, str] = {}  # tag -> build_id
        self._pinned_builds: set = set()  # build_ids that should not be deleted

    async def store_artifacts(
        self,
        build_id: str,
        artifacts: List[ArtifactInfo]
    ) -> StoreResult:
        """
        Store artifacts for a build.
        
        Args:
            build_id: Build job ID
            artifacts: List of artifacts to store
            
        Returns:
            StoreResult with stored artifact details
        """
        if not artifacts:
            return StoreResult(
                success=False,
                error_message="No artifacts provided"
            )
        
        stored_artifacts = []
        failed_artifacts = []
        
        for artifact_info in artifacts:
            try:
                artifact = await self._store_single_artifact(build_id, artifact_info)
                stored_artifacts.append(artifact)
            except Exception as e:
                failed_artifacts.append(artifact_info.filename)
        
        # Update build artifact index
        if build_id not in self._build_artifacts:
            self._build_artifacts[build_id] = []
        
        self._build_artifacts[build_id].extend([a.id for a in stored_artifacts])
        
        success = len(failed_artifacts) == 0
        error_message = None
        if failed_artifacts:
            error_message = f"Failed to store: {', '.join(failed_artifacts)}"
        
        return StoreResult(
            success=success,
            artifacts=stored_artifacts,
            error_message=error_message,
            failed_artifacts=failed_artifacts,
        )

    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID."""
        return self._artifacts.get(artifact_id)

    async def get_artifacts_by_build(self, build_id: str) -> List[Artifact]:
        """Get all artifacts for a build."""
        artifact_ids = self._build_artifacts.get(build_id, [])
        return [self._artifacts[aid] for aid in artifact_ids if aid in self._artifacts]

    async def get_latest_artifacts(
        self,
        branch: str,
        architecture: str
    ) -> List[Artifact]:
        """
        Get the latest artifacts for a branch and architecture.
        
        Args:
            branch: Git branch name
            architecture: Target architecture
            
        Returns:
            List of artifacts from the latest build
        """
        branch_data = self._branch_latest.get(branch, {})
        build_id = branch_data.get(architecture)
        
        if not build_id:
            return []
        
        return await self.get_artifacts_by_build(build_id)

    async def get_artifacts_by_selection(
        self,
        selection: ArtifactSelection
    ) -> List[Artifact]:
        """
        Get artifacts matching selection criteria.
        
        Args:
            selection: Artifact selection criteria
            
        Returns:
            List of matching artifacts
        """
        if not selection.is_valid():
            return []
        
        # By build ID
        if selection.build_id:
            artifacts = await self.get_artifacts_by_build(selection.build_id)
            if selection.architecture:
                artifacts = [a for a in artifacts if a.matches_architecture(selection.architecture)]
            return artifacts
        
        # By commit hash
        if selection.commit_hash:
            for build_id, artifact_ids in self._build_artifacts.items():
                artifacts = [self._artifacts[aid] for aid in artifact_ids if aid in self._artifacts]
                if artifacts and artifacts[0].metadata.get("commit_hash") == selection.commit_hash:
                    if selection.architecture:
                        artifacts = [a for a in artifacts if a.matches_architecture(selection.architecture)]
                    return artifacts
            return []
        
        # Latest for branch
        if selection.branch and selection.use_latest:
            arch = selection.architecture or "x86_64"
            return await self.get_latest_artifacts(selection.branch, arch)
        
        return []

    async def delete_artifacts(self, artifact_ids: List[str]) -> DeleteResult:
        """
        Delete artifacts by ID.
        
        Args:
            artifact_ids: List of artifact IDs to delete
            
        Returns:
            DeleteResult with deletion status
        """
        deleted_count = 0
        failed_ids = []
        
        for artifact_id in artifact_ids:
            artifact = self._artifacts.get(artifact_id)
            if not artifact:
                failed_ids.append(artifact_id)
                continue
            
            # Check if build is pinned
            if artifact.build_id in self._pinned_builds:
                failed_ids.append(artifact_id)
                continue
            
            try:
                # Remove from storage (simulated)
                del self._artifacts[artifact_id]
                
                # Remove from build index
                if artifact.build_id in self._build_artifacts:
                    if artifact_id in self._build_artifacts[artifact.build_id]:
                        self._build_artifacts[artifact.build_id].remove(artifact_id)
                
                deleted_count += 1
            except Exception:
                failed_ids.append(artifact_id)
        
        return DeleteResult(
            success=len(failed_ids) == 0,
            deleted_count=deleted_count,
            failed_ids=failed_ids,
        )

    async def cleanup_old_artifacts(self, retention_days: Optional[int] = None) -> CleanupResult:
        """
        Clean up artifacts older than retention period.
        
        Args:
            retention_days: Override default retention days
            
        Returns:
            CleanupResult with cleanup statistics
        """
        days = retention_days or self._retention_policy.retention_days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        to_delete = []
        preserved_count = 0
        freed_bytes = 0
        
        # Group artifacts by build
        builds_to_check = set()
        for artifact in self._artifacts.values():
            if artifact.created_at < cutoff_date:
                builds_to_check.add(artifact.build_id)
        
        for build_id in builds_to_check:
            # Check if build should be preserved
            if self._should_preserve_build(build_id):
                preserved_count += len(self._build_artifacts.get(build_id, []))
                continue
            
            # Mark artifacts for deletion
            for artifact_id in self._build_artifacts.get(build_id, []):
                artifact = self._artifacts.get(artifact_id)
                if artifact:
                    to_delete.append(artifact_id)
                    freed_bytes += artifact.size_bytes
        
        # Delete artifacts
        result = await self.delete_artifacts(to_delete)
        
        return CleanupResult(
            success=result.success,
            deleted_count=result.deleted_count,
            freed_bytes=freed_bytes,
            preserved_count=preserved_count,
        )

    async def verify_artifact_integrity(self, artifact_id: str) -> VerificationResult:
        """
        Verify artifact integrity by checking checksum.
        
        Args:
            artifact_id: Artifact ID to verify
            
        Returns:
            VerificationResult with verification status
        """
        artifact = self._artifacts.get(artifact_id)
        
        if not artifact:
            return VerificationResult(
                success=False,
                artifact_id=artifact_id,
                error_message=f"Artifact {artifact_id} not found"
            )
        
        # Check if file exists (simulated - in real impl would check filesystem)
        file_exists = True  # Simulated
        
        # Verify checksum (simulated - in real impl would read file and compute)
        checksum_valid = True  # Simulated
        
        return VerificationResult(
            success=file_exists and checksum_valid,
            artifact_id=artifact_id,
            checksum_valid=checksum_valid,
            file_exists=file_exists,
        )

    async def tag_build(self, build_id: str, tag: str) -> bool:
        """Tag a build for preservation."""
        if build_id not in self._build_artifacts:
            return False
        
        self._tagged_builds[tag] = build_id
        return True

    async def pin_build(self, build_id: str) -> bool:
        """Pin a build to prevent deletion."""
        if build_id not in self._build_artifacts:
            return False
        
        self._pinned_builds.add(build_id)
        return True

    async def unpin_build(self, build_id: str) -> bool:
        """Unpin a build to allow deletion."""
        if build_id in self._pinned_builds:
            self._pinned_builds.remove(build_id)
            return True
        return False

    async def update_latest(
        self,
        branch: str,
        architecture: str,
        build_id: str
    ) -> None:
        """Update the latest build for a branch/architecture."""
        if branch not in self._branch_latest:
            self._branch_latest[branch] = {}
        
        self._branch_latest[branch][architecture] = build_id

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_size = sum(a.size_bytes for a in self._artifacts.values())
        
        by_type: Dict[str, int] = {}
        by_arch: Dict[str, int] = {}
        
        for artifact in self._artifacts.values():
            type_name = artifact.artifact_type.value
            by_type[type_name] = by_type.get(type_name, 0) + artifact.size_bytes
            by_arch[artifact.architecture] = by_arch.get(artifact.architecture, 0) + artifact.size_bytes
        
        return {
            "total_artifacts": len(self._artifacts),
            "total_builds": len(self._build_artifacts),
            "total_size_bytes": total_size,
            "pinned_builds": len(self._pinned_builds),
            "tagged_builds": len(self._tagged_builds),
            "size_by_type": by_type,
            "size_by_architecture": by_arch,
        }

    # Private methods

    async def _store_single_artifact(
        self,
        build_id: str,
        artifact_info: ArtifactInfo
    ) -> Artifact:
        """Store a single artifact."""
        artifact_id = str(uuid.uuid4())
        
        # Compute checksum
        checksum = hashlib.sha256(artifact_info.content).hexdigest()
        
        # Create artifact path
        artifact_path = str(
            self._storage_path / build_id / artifact_info.filename
        )
        
        # Create artifact record
        artifact = Artifact(
            id=artifact_id,
            build_id=build_id,
            artifact_type=artifact_info.artifact_type,
            filename=artifact_info.filename,
            path=artifact_path,
            size_bytes=len(artifact_info.content),
            checksum_sha256=checksum,
            architecture=artifact_info.architecture,
            created_at=datetime.now(timezone.utc),
            metadata=artifact_info.metadata,
        )
        
        # Store in index
        self._artifacts[artifact_id] = artifact
        
        return artifact

    def _should_preserve_build(self, build_id: str) -> bool:
        """Check if a build should be preserved from cleanup."""
        # Check if pinned
        if build_id in self._pinned_builds:
            return True
        
        # Check if tagged
        if self._retention_policy.preserve_tagged:
            if build_id in self._tagged_builds.values():
                return True
        
        return False

    def _compute_checksum(self, content: bytes) -> str:
        """Compute SHA256 checksum of content."""
        return hashlib.sha256(content).hexdigest()
