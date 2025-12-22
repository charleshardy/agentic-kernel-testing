"""Artifact collection system for test execution.

This module provides functionality for:
- Artifact capture during test execution
- Storage and retrieval mechanisms for test artifacts
- Artifact cleanup and retention policies
- Artifact metadata management
"""

import os
import shutil
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import tempfile
import tarfile
import gzip

from ai_generator.models import ArtifactBundle, TestResult


@dataclass
class ArtifactMetadata:
    """Metadata for stored artifacts."""
    artifact_id: str
    test_id: str
    artifact_type: str  # log, core_dump, trace, screenshot, etc.
    file_path: str
    file_size: int
    checksum: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    compressed: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArtifactMetadata':
        """Create from dictionary."""
        created_at = datetime.fromisoformat(data.pop('created_at'))
        expires_at_str = data.pop('expires_at', None)
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None
        return cls(**data, created_at=created_at, expires_at=expires_at)


@dataclass
class RetentionPolicy:
    """Artifact retention policy configuration."""
    artifact_type: str
    max_age_days: int
    max_size_mb: Optional[int] = None
    max_count: Optional[int] = None
    compress_after_days: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetentionPolicy':
        """Create from dictionary."""
        return cls(**data)


class ArtifactCollector:
    """System for collecting, storing, and managing test artifacts."""
    
    def __init__(self, storage_root: str = "/tmp/test_artifacts"):
        """Initialize the artifact collector.
        
        Args:
            storage_root: Root directory for artifact storage
        """
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.logs_dir = self.storage_root / "logs"
        self.core_dumps_dir = self.storage_root / "core_dumps"
        self.traces_dir = self.storage_root / "traces"
        self.screenshots_dir = self.storage_root / "screenshots"
        self.metadata_dir = self.storage_root / "metadata"
        
        for directory in [self.logs_dir, self.core_dumps_dir, self.traces_dir, 
                         self.screenshots_dir, self.metadata_dir]:
            directory.mkdir(exist_ok=True)
        
        # Default retention policies
        self.retention_policies = {
            "log": RetentionPolicy("log", max_age_days=30, compress_after_days=7),
            "core_dump": RetentionPolicy("core_dump", max_age_days=14, max_size_mb=1000),
            "trace": RetentionPolicy("trace", max_age_days=21, compress_after_days=3),
            "screenshot": RetentionPolicy("screenshot", max_age_days=7),
            "other": RetentionPolicy("other", max_age_days=14)
        }
        
        # Artifact metadata cache
        self.metadata_cache: Dict[str, ArtifactMetadata] = {}
        self._load_metadata_cache()
    
    def collect_artifacts(self, test_result: TestResult) -> ArtifactBundle:
        """Collect and store artifacts from a test result.
        
        Args:
            test_result: The test result containing artifacts
            
        Returns:
            Updated ArtifactBundle with stored artifact paths
        """
        stored_bundle = ArtifactBundle()
        
        # Process logs
        for log_path in test_result.artifacts.logs:
            if os.path.exists(log_path):
                stored_path = self._store_artifact(
                    test_result.test_id, log_path, "log"
                )
                if stored_path:
                    stored_bundle.logs.append(stored_path)
        
        # Process core dumps
        for core_path in test_result.artifacts.core_dumps:
            if os.path.exists(core_path):
                stored_path = self._store_artifact(
                    test_result.test_id, core_path, "core_dump"
                )
                if stored_path:
                    stored_bundle.core_dumps.append(stored_path)
        
        # Process traces
        for trace_path in test_result.artifacts.traces:
            if os.path.exists(trace_path):
                stored_path = self._store_artifact(
                    test_result.test_id, trace_path, "trace"
                )
                if stored_path:
                    stored_bundle.traces.append(stored_path)
        
        # Process screenshots
        for screenshot_path in test_result.artifacts.screenshots:
            if os.path.exists(screenshot_path):
                stored_path = self._store_artifact(
                    test_result.test_id, screenshot_path, "screenshot"
                )
                if stored_path:
                    stored_bundle.screenshots.append(stored_path)
        
        # Process other files from metadata
        if "other_files" in test_result.artifacts.metadata:
            other_files = test_result.artifacts.metadata["other_files"]
            stored_other_files = []
            
            for file_path in other_files:
                if os.path.exists(file_path):
                    stored_path = self._store_artifact(
                        test_result.test_id, file_path, "other"
                    )
                    if stored_path:
                        stored_other_files.append(stored_path)
            
            if stored_other_files:
                stored_bundle.metadata["other_files"] = stored_other_files
        
        # Copy original metadata
        stored_bundle.metadata.update(test_result.artifacts.metadata)
        
        return stored_bundle
    
    def _store_artifact(self, test_id: str, source_path: str, artifact_type: str) -> Optional[str]:
        """Store a single artifact file.
        
        Args:
            test_id: ID of the test that generated the artifact
            source_path: Path to the source artifact file
            artifact_type: Type of artifact (log, core_dump, trace, etc.)
            
        Returns:
            Path to stored artifact, or None if storage failed
        """
        try:
            source_file = Path(source_path)
            if not source_file.exists():
                return None
            
            # Generate artifact ID
            artifact_id = self._generate_artifact_id(test_id, source_file.name, artifact_type)
            
            # Determine storage directory
            storage_dir = self._get_storage_dir(artifact_type)
            
            # Create test-specific subdirectory
            test_storage_dir = storage_dir / test_id
            test_storage_dir.mkdir(exist_ok=True)
            
            # Determine destination path
            dest_path = test_storage_dir / f"{artifact_id}_{source_file.name}"
            
            # Copy file
            shutil.copy2(source_file, dest_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(dest_path)
            
            # Create metadata
            metadata = ArtifactMetadata(
                artifact_id=artifact_id,
                test_id=test_id,
                artifact_type=artifact_type,
                file_path=str(dest_path),
                file_size=dest_path.stat().st_size,
                checksum=checksum,
                created_at=datetime.now(),
                expires_at=self._calculate_expiry_date(artifact_type)
            )
            
            # Store metadata
            self._store_metadata(metadata)
            
            return str(dest_path)
            
        except Exception as e:
            print(f"Error storing artifact {source_path}: {e}")
            return None
    
    def _generate_artifact_id(self, test_id: str, filename: str, artifact_type: str) -> str:
        """Generate a unique artifact ID.
        
        Args:
            test_id: Test ID
            filename: Original filename
            artifact_type: Type of artifact
            
        Returns:
            Unique artifact ID
        """
        timestamp = str(int(time.time()))
        content = f"{test_id}_{filename}_{artifact_type}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _get_storage_dir(self, artifact_type: str) -> Path:
        """Get storage directory for artifact type.
        
        Args:
            artifact_type: Type of artifact
            
        Returns:
            Path to storage directory
        """
        storage_dirs = {
            "log": self.logs_dir,
            "core_dump": self.core_dumps_dir,
            "trace": self.traces_dir,
            "screenshot": self.screenshots_dir
        }
        
        return storage_dirs.get(artifact_type, self.storage_root / "other")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hexadecimal checksum string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _calculate_expiry_date(self, artifact_type: str) -> Optional[datetime]:
        """Calculate expiry date for artifact based on retention policy.
        
        Args:
            artifact_type: Type of artifact
            
        Returns:
            Expiry datetime, or None if no expiry
        """
        policy = self.retention_policies.get(artifact_type)
        if not policy or policy.max_age_days <= 0:
            return None
        
        return datetime.now() + timedelta(days=policy.max_age_days)
    
    def _store_metadata(self, metadata: ArtifactMetadata):
        """Store artifact metadata.
        
        Args:
            metadata: Artifact metadata to store
        """
        # Store in cache
        self.metadata_cache[metadata.artifact_id] = metadata
        
        # Store to file
        metadata_file = self.metadata_dir / f"{metadata.artifact_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
    
    def _load_metadata_cache(self):
        """Load metadata cache from stored files."""
        if not self.metadata_dir.exists():
            return
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    metadata = ArtifactMetadata.from_dict(data)
                    self.metadata_cache[metadata.artifact_id] = metadata
            except Exception as e:
                print(f"Error loading metadata from {metadata_file}: {e}")
    
    def get_artifacts_for_test(self, test_id: str) -> List[ArtifactMetadata]:
        """Get all artifacts for a specific test.
        
        Args:
            test_id: Test ID to search for
            
        Returns:
            List of artifact metadata for the test
        """
        return [
            metadata for metadata in self.metadata_cache.values()
            if metadata.test_id == test_id
        ]
    
    def get_artifact_by_id(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        """Get artifact metadata by ID.
        
        Args:
            artifact_id: Artifact ID to search for
            
        Returns:
            Artifact metadata, or None if not found
        """
        return self.metadata_cache.get(artifact_id)
    
    def retrieve_artifact(self, artifact_id: str, dest_path: Optional[str] = None) -> Optional[str]:
        """Retrieve an artifact file.
        
        Args:
            artifact_id: ID of artifact to retrieve
            dest_path: Optional destination path, otherwise returns stored path
            
        Returns:
            Path to artifact file, or None if not found
        """
        metadata = self.get_artifact_by_id(artifact_id)
        if not metadata:
            return None
        
        stored_path = Path(metadata.file_path)
        if not stored_path.exists():
            return None
        
        # If artifact is compressed, decompress it
        if metadata.compressed:
            stored_path = self._decompress_artifact(stored_path)
        
        if dest_path:
            dest_file = Path(dest_path)
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(stored_path, dest_file)
            return str(dest_file)
        else:
            return str(stored_path)
    
    def _decompress_artifact(self, compressed_path: Path) -> Path:
        """Decompress an artifact file.
        
        Args:
            compressed_path: Path to compressed file
            
        Returns:
            Path to decompressed file
        """
        if compressed_path.suffix == '.gz':
            decompressed_path = compressed_path.with_suffix('')
            
            if not decompressed_path.exists():
                with gzip.open(compressed_path, 'rb') as f_in:
                    with open(decompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            return decompressed_path
        
        return compressed_path
    
    def create_artifact_archive(self, test_id: str, archive_path: Optional[str] = None) -> Optional[str]:
        """Create a compressed archive of all artifacts for a test.
        
        Args:
            test_id: Test ID to create archive for
            archive_path: Optional path for archive, otherwise auto-generated
            
        Returns:
            Path to created archive, or None if failed
        """
        artifacts = self.get_artifacts_for_test(test_id)
        if not artifacts:
            return None
        
        if not archive_path:
            archive_path = str(self.storage_root / f"{test_id}_artifacts.tar.gz")
        
        try:
            with tarfile.open(archive_path, 'w:gz') as tar:
                for artifact in artifacts:
                    artifact_path = Path(artifact.file_path)
                    if artifact_path.exists():
                        # Add with relative path inside archive
                        arcname = f"{artifact.artifact_type}/{artifact_path.name}"
                        tar.add(artifact_path, arcname=arcname)
                
                # Add metadata
                metadata_content = json.dumps([a.to_dict() for a in artifacts], indent=2)
                metadata_info = tarfile.TarInfo(name="metadata.json")
                metadata_info.size = len(metadata_content.encode())
                tar.addfile(metadata_info, fileobj=tempfile.NamedTemporaryFile(
                    mode='w+b', delete=False
                ))
            
            return archive_path
            
        except Exception as e:
            print(f"Error creating artifact archive: {e}")
            return None
    
    def cleanup_expired_artifacts(self) -> Dict[str, int]:
        """Clean up expired artifacts based on retention policies.
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "expired_removed": 0,
            "compressed": 0,
            "errors": 0,
            "bytes_freed": 0
        }
        
        current_time = datetime.now()
        expired_artifacts = []
        
        # Find expired artifacts
        for artifact_id, metadata in self.metadata_cache.items():
            if metadata.expires_at and current_time > metadata.expires_at:
                expired_artifacts.append(artifact_id)
            else:
                # Check if artifact should be compressed
                policy = self.retention_policies.get(metadata.artifact_type)
                if (policy and policy.compress_after_days and 
                    not metadata.compressed and
                    current_time > metadata.created_at + timedelta(days=policy.compress_after_days)):
                    
                    if self._compress_artifact(metadata):
                        stats["compressed"] += 1
        
        # Remove expired artifacts
        for artifact_id in expired_artifacts:
            try:
                metadata = self.metadata_cache[artifact_id]
                artifact_path = Path(metadata.file_path)
                
                if artifact_path.exists():
                    file_size = artifact_path.stat().st_size
                    artifact_path.unlink()
                    stats["bytes_freed"] += file_size
                
                # Remove metadata file
                metadata_file = self.metadata_dir / f"{artifact_id}.json"
                if metadata_file.exists():
                    metadata_file.unlink()
                
                # Remove from cache
                del self.metadata_cache[artifact_id]
                stats["expired_removed"] += 1
                
            except Exception as e:
                print(f"Error removing expired artifact {artifact_id}: {e}")
                stats["errors"] += 1
        
        return stats
    
    def _compress_artifact(self, metadata: ArtifactMetadata) -> bool:
        """Compress an artifact file.
        
        Args:
            metadata: Artifact metadata
            
        Returns:
            True if compression succeeded
        """
        try:
            artifact_path = Path(metadata.file_path)
            if not artifact_path.exists():
                return False
            
            compressed_path = artifact_path.with_suffix(artifact_path.suffix + '.gz')
            
            with open(artifact_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Update metadata
            original_size = metadata.file_size
            metadata.file_path = str(compressed_path)
            metadata.file_size = compressed_path.stat().st_size
            metadata.compressed = True
            
            # Remove original file
            artifact_path.unlink()
            
            # Update stored metadata
            self._store_metadata(metadata)
            
            print(f"Compressed artifact {metadata.artifact_id}: {original_size} -> {metadata.file_size} bytes")
            return True
            
        except Exception as e:
            print(f"Error compressing artifact {metadata.artifact_id}: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "total_artifacts": len(self.metadata_cache),
            "total_size_bytes": 0,
            "by_type": {},
            "by_test": {},
            "compressed_count": 0,
            "expired_count": 0
        }
        
        current_time = datetime.now()
        
        for metadata in self.metadata_cache.values():
            # Total size
            stats["total_size_bytes"] += metadata.file_size
            
            # By type
            if metadata.artifact_type not in stats["by_type"]:
                stats["by_type"][metadata.artifact_type] = {"count": 0, "size_bytes": 0}
            stats["by_type"][metadata.artifact_type]["count"] += 1
            stats["by_type"][metadata.artifact_type]["size_bytes"] += metadata.file_size
            
            # By test
            if metadata.test_id not in stats["by_test"]:
                stats["by_test"][metadata.test_id] = {"count": 0, "size_bytes": 0}
            stats["by_test"][metadata.test_id]["count"] += 1
            stats["by_test"][metadata.test_id]["size_bytes"] += metadata.file_size
            
            # Compressed count
            if metadata.compressed:
                stats["compressed_count"] += 1
            
            # Expired count
            if metadata.expires_at and current_time > metadata.expires_at:
                stats["expired_count"] += 1
        
        return stats
    
    def set_retention_policy(self, artifact_type: str, policy: RetentionPolicy):
        """Set retention policy for an artifact type.
        
        Args:
            artifact_type: Type of artifact
            policy: Retention policy to set
        """
        self.retention_policies[artifact_type] = policy
    
    def get_retention_policy(self, artifact_type: str) -> Optional[RetentionPolicy]:
        """Get retention policy for an artifact type.
        
        Args:
            artifact_type: Type of artifact
            
        Returns:
            Retention policy, or None if not set
        """
        return self.retention_policies.get(artifact_type)


# Global artifact collector instance
_collector_instance: Optional[ArtifactCollector] = None


def get_artifact_collector(storage_root: Optional[str] = None) -> ArtifactCollector:
    """Get the global artifact collector instance.
    
    Args:
        storage_root: Optional storage root directory
        
    Returns:
        The global ArtifactCollector instance
    """
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = ArtifactCollector(storage_root or "/tmp/test_artifacts")
    return _collector_instance


def collect_test_artifacts(test_result: TestResult) -> ArtifactBundle:
    """Convenience function to collect artifacts from a test result.
    
    Args:
        test_result: The test result containing artifacts
        
    Returns:
        Updated ArtifactBundle with stored artifact paths
    """
    collector = get_artifact_collector()
    return collector.collect_artifacts(test_result)