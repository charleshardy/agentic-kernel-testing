"""
Artifact Repository

Manages test artifacts and deployment packages including storage, versioning,
and secure distribution.
"""

import hashlib
import logging
from typing import Dict, List, Optional, Set
from pathlib import Path

from .models import TestArtifact, ArtifactType


logger = logging.getLogger(__name__)


class ArtifactRepository:
    """
    Manages test artifacts and deployment packages.
    
    Handles:
    - Store and version test scripts, binaries, and configurations
    - Handle artifact dependencies and packaging
    - Provide secure artifact distribution
    - Support artifact caching and optimization
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize artifact repository.
        
        Args:
            storage_path: Path to artifact storage directory
        """
        self.storage_path = Path(storage_path) if storage_path else Path("./artifacts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for quick access
        self._artifact_cache: Dict[str, TestArtifact] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        
        logger.info(f"ArtifactRepository initialized with storage path: {self.storage_path}")
    
    async def store_artifact(self, artifact: TestArtifact) -> bool:
        """
        Store a test artifact in the repository.
        
        Args:
            artifact: Test artifact to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Validate artifact
            if not artifact.artifact_id or not artifact.name:
                raise ValueError("Artifact must have ID and name")
            
            # Calculate checksum if not provided
            if not artifact.checksum:
                artifact.checksum = hashlib.sha256(artifact.content).hexdigest()
            
            # Create storage directory for artifact type
            type_dir = self.storage_path / artifact.type.value
            type_dir.mkdir(exist_ok=True)
            
            # Store artifact content
            artifact_path = type_dir / f"{artifact.artifact_id}_{artifact.name}"
            artifact_path.write_bytes(artifact.content)
            
            # Store metadata
            metadata_path = type_dir / f"{artifact.artifact_id}_{artifact.name}.meta"
            metadata = {
                "artifact_id": artifact.artifact_id,
                "name": artifact.name,
                "type": artifact.type.value,
                "checksum": artifact.checksum,
                "permissions": artifact.permissions,
                "target_path": artifact.target_path,
                "dependencies": artifact.dependencies
            }
            
            import json
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            # Cache the artifact
            self._artifact_cache[artifact.artifact_id] = artifact
            
            # Update dependency graph
            if artifact.dependencies:
                self._dependency_graph[artifact.artifact_id] = set(artifact.dependencies)
            
            logger.info(f"Stored artifact {artifact.name} ({artifact.artifact_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store artifact {artifact.name}: {e}")
            return False
    
    async def get_artifact(self, artifact_id: str) -> Optional[TestArtifact]:
        """
        Retrieve an artifact by ID.
        
        Args:
            artifact_id: Artifact identifier
            
        Returns:
            TestArtifact if found, None otherwise
        """
        # Check cache first
        if artifact_id in self._artifact_cache:
            return self._artifact_cache[artifact_id]
        
        # Search in storage
        for type_dir in self.storage_path.iterdir():
            if not type_dir.is_dir():
                continue
            
            # Look for metadata file
            for meta_file in type_dir.glob(f"{artifact_id}_*.meta"):
                try:
                    import json
                    metadata = json.loads(meta_file.read_text())
                    
                    # Load artifact content
                    content_file = meta_file.with_suffix("")
                    if content_file.exists():
                        content = content_file.read_bytes()
                        
                        artifact = TestArtifact(
                            artifact_id=metadata["artifact_id"],
                            name=metadata["name"],
                            type=ArtifactType(metadata["type"]),
                            content=content,
                            checksum=metadata["checksum"],
                            permissions=metadata["permissions"],
                            target_path=metadata["target_path"],
                            dependencies=metadata.get("dependencies", [])
                        )
                        
                        # Cache the artifact
                        self._artifact_cache[artifact_id] = artifact
                        return artifact
                
                except Exception as e:
                    logger.error(f"Error loading artifact {artifact_id}: {e}")
        
        logger.warning(f"Artifact {artifact_id} not found")
        return None
    
    async def get_artifacts_by_type(self, artifact_type: ArtifactType) -> List[TestArtifact]:
        """
        Get all artifacts of a specific type.
        
        Args:
            artifact_type: Type of artifacts to retrieve
            
        Returns:
            List of artifacts of the specified type
        """
        artifacts = []
        type_dir = self.storage_path / artifact_type.value
        
        if not type_dir.exists():
            return artifacts
        
        for meta_file in type_dir.glob("*.meta"):
            try:
                import json
                metadata = json.loads(meta_file.read_text())
                artifact_id = metadata["artifact_id"]
                
                artifact = await self.get_artifact(artifact_id)
                if artifact:
                    artifacts.append(artifact)
            
            except Exception as e:
                logger.error(f"Error loading artifact metadata from {meta_file}: {e}")
        
        return artifacts
    
    async def resolve_dependencies(self, artifact_ids: List[str]) -> List[str]:
        """
        Resolve dependencies for a list of artifacts.
        
        Args:
            artifact_ids: List of artifact IDs
            
        Returns:
            List of artifact IDs including all dependencies in correct order
        """
        resolved = []
        visited = set()
        
        async def _resolve_recursive(artifact_id: str):
            if artifact_id in visited:
                return
            
            visited.add(artifact_id)
            
            # Get dependencies for this artifact
            dependencies = self._dependency_graph.get(artifact_id, set())
            
            # Resolve dependencies first
            for dep_id in dependencies:
                await _resolve_recursive(dep_id)
            
            # Add this artifact
            if artifact_id not in resolved:
                resolved.append(artifact_id)
        
        # Resolve dependencies for all requested artifacts
        for artifact_id in artifact_ids:
            await _resolve_recursive(artifact_id)
        
        logger.info(f"Resolved {len(artifact_ids)} artifacts to {len(resolved)} including dependencies")
        return resolved
    
    async def validate_artifact(self, artifact: TestArtifact) -> bool:
        """
        Validate an artifact's integrity.
        
        Args:
            artifact: Artifact to validate
            
        Returns:
            True if artifact is valid, False otherwise
        """
        try:
            # Check required fields
            if not all([artifact.artifact_id, artifact.name, artifact.content]):
                logger.error(f"Artifact {artifact.name} missing required fields")
                return False
            
            # Validate checksum
            calculated_checksum = hashlib.sha256(artifact.content).hexdigest()
            if artifact.checksum and artifact.checksum != calculated_checksum:
                logger.error(f"Checksum mismatch for artifact {artifact.name}")
                return False
            
            # Validate permissions format
            if artifact.permissions and not artifact.permissions.startswith(('0', '1', '2', '3', '4', '5', '6', '7')):
                logger.warning(f"Invalid permissions format for artifact {artifact.name}: {artifact.permissions}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating artifact {artifact.name}: {e}")
            return False
    
    async def create_deployment_package(self, artifact_ids: List[str]) -> Optional[bytes]:
        """
        Create a deployment package containing multiple artifacts.
        
        Args:
            artifact_ids: List of artifact IDs to include
            
        Returns:
            Deployment package as bytes, None if creation failed
        """
        try:
            import tarfile
            import io
            
            # Resolve dependencies
            resolved_ids = await self.resolve_dependencies(artifact_ids)
            
            # Create tar archive in memory
            tar_buffer = io.BytesIO()
            
            with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
                for artifact_id in resolved_ids:
                    artifact = await self.get_artifact(artifact_id)
                    if not artifact:
                        logger.error(f"Artifact {artifact_id} not found for packaging")
                        return None
                    
                    # Add artifact to tar
                    artifact_info = tarfile.TarInfo(name=f"{artifact.type.value}/{artifact.name}")
                    artifact_info.size = len(artifact.content)
                    artifact_info.mode = int(artifact.permissions, 8) if artifact.permissions else 0o644
                    
                    tar.addfile(artifact_info, io.BytesIO(artifact.content))
                    
                    # Add metadata
                    metadata = {
                        "artifact_id": artifact.artifact_id,
                        "name": artifact.name,
                        "type": artifact.type.value,
                        "checksum": artifact.checksum,
                        "target_path": artifact.target_path,
                        "dependencies": artifact.dependencies
                    }
                    
                    import json
                    metadata_content = json.dumps(metadata, indent=2).encode()
                    metadata_info = tarfile.TarInfo(name=f"{artifact.type.value}/{artifact.name}.meta")
                    metadata_info.size = len(metadata_content)
                    
                    tar.addfile(metadata_info, io.BytesIO(metadata_content))
            
            package_content = tar_buffer.getvalue()
            logger.info(f"Created deployment package with {len(resolved_ids)} artifacts ({len(package_content)} bytes)")
            return package_content
            
        except Exception as e:
            logger.error(f"Failed to create deployment package: {e}")
            return None
    
    def get_repository_stats(self) -> Dict[str, int]:
        """
        Get repository statistics.
        
        Returns:
            Dictionary with repository statistics
        """
        stats = {
            "total_artifacts": len(self._artifact_cache),
            "scripts": 0,
            "binaries": 0,
            "configs": 0,
            "data": 0
        }
        
        for artifact in self._artifact_cache.values():
            if artifact.type == ArtifactType.SCRIPT:
                stats["scripts"] += 1
            elif artifact.type == ArtifactType.BINARY:
                stats["binaries"] += 1
            elif artifact.type == ArtifactType.CONFIG:
                stats["configs"] += 1
            elif artifact.type == ArtifactType.DATA:
                stats["data"] += 1
        
        return stats