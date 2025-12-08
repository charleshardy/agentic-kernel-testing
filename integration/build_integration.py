"""Build system integration for automatic test triggering."""

import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import hashlib

from integration.build_models import (
    BuildEvent, BuildInfo, BuildStatus, BuildSystem, BuildType,
    KernelImage, BSPPackage, BuildArtifact
)

logger = logging.getLogger(__name__)


class BuildIntegration:
    """Main build system integration handler."""
    
    def __init__(self):
        """Initialize build integration."""
        self.build_handlers: List[Callable[[BuildEvent], None]] = []
        self.build_cache: Dict[str, BuildInfo] = {}
    
    def register_build_handler(self, handler: Callable[[BuildEvent], None]) -> None:
        """Register a handler for build completion events.
        
        Args:
            handler: Callback function to handle build events
        """
        self.build_handlers.append(handler)
        logger.info("Registered build completion handler")
    
    def detect_build_completion(self, build_info: BuildInfo) -> bool:
        """Detect if a build has completed.
        
        Args:
            build_info: Build information to check
            
        Returns:
            True if build has completed (success or failure)
        """
        return build_info.status in [BuildStatus.SUCCESS, BuildStatus.FAILURE]
    
    def should_trigger_tests(self, build_info: BuildInfo) -> bool:
        """Determine if tests should be triggered for a build.
        
        Args:
            build_info: Build information
            
        Returns:
            True if tests should be triggered
        """
        # Only trigger tests for successful builds
        if build_info.status != BuildStatus.SUCCESS:
            logger.info(f"Build {build_info.build_id} did not succeed, skipping tests")
            return False
        
        # Trigger tests for kernel and BSP builds
        if build_info.build_type in [BuildType.KERNEL, BuildType.BSP, BuildType.FULL_SYSTEM]:
            return True
        
        # Trigger tests for module builds if they have artifacts
        if build_info.build_type == BuildType.MODULE and build_info.artifacts:
            return True
        
        return False
    
    def handle_build_event(self, build_event: BuildEvent) -> None:
        """Handle incoming build event.
        
        Args:
            build_event: Build event to process
        """
        build_info = build_event.build_info
        
        logger.info(
            f"Received build event {build_event.event_id} for build "
            f"{build_info.build_id} with status {build_info.status.value}"
        )
        
        # Cache build info
        self.build_cache[build_info.build_id] = build_info
        
        # Check if build is complete
        if not self.detect_build_completion(build_info):
            logger.info(f"Build {build_info.build_id} not yet complete")
            return
        
        # Check if tests should be triggered
        if not self.should_trigger_tests(build_info):
            logger.info(f"Tests not triggered for build {build_info.build_id}")
            return
        
        # Trigger registered handlers
        self._trigger_handlers(build_event)
    
    def _trigger_handlers(self, build_event: BuildEvent) -> None:
        """Trigger registered handlers for a build event.
        
        Args:
            build_event: Build event to handle
        """
        for handler in self.build_handlers:
            try:
                handler(build_event)
            except Exception as e:
                logger.error(
                    f"Error in build handler for {build_event.event_id}: {e}",
                    exc_info=True
                )
    
    def extract_kernel_image(self, build_info: BuildInfo) -> Optional[KernelImage]:
        """Extract kernel image from build artifacts.
        
        Args:
            build_info: Build information
            
        Returns:
            Kernel image if found, None otherwise
        """
        # Check if kernel image is directly provided
        if build_info.kernel_image:
            return build_info.kernel_image
        
        # Search for kernel image in artifacts
        for artifact in build_info.artifacts:
            if artifact.artifact_type == "kernel_image":
                # Construct kernel image from artifact
                kernel_image = KernelImage(
                    version=build_info.metadata.get('kernel_version', 'unknown'),
                    architecture=build_info.metadata.get('architecture', 'x86_64'),
                    image_path=artifact.path,
                    config_path=self._find_artifact_path(build_info.artifacts, "config"),
                    modules_path=self._find_artifact_path(build_info.artifacts, "modules"),
                    build_timestamp=build_info.start_time,
                    commit_sha=build_info.commit_sha,
                    metadata=artifact.metadata
                )
                return kernel_image
        
        return None
    
    def extract_bsp_package(self, build_info: BuildInfo) -> Optional[BSPPackage]:
        """Extract BSP package from build artifacts.
        
        Args:
            build_info: Build information
            
        Returns:
            BSP package if found, None otherwise
        """
        # Check if BSP package is directly provided
        if build_info.bsp_package:
            return build_info.bsp_package
        
        # Search for BSP package in artifacts
        for artifact in build_info.artifacts:
            if artifact.artifact_type == "bsp_package":
                # Construct BSP package from artifact
                bsp_package = BSPPackage(
                    name=artifact.name,
                    version=build_info.metadata.get('bsp_version', 'unknown'),
                    target_board=build_info.metadata.get('target_board', 'unknown'),
                    architecture=build_info.metadata.get('architecture', 'x86_64'),
                    package_path=artifact.path,
                    kernel_version=build_info.metadata.get('kernel_version'),
                    build_timestamp=build_info.start_time,
                    commit_sha=build_info.commit_sha,
                    metadata=artifact.metadata
                )
                return bsp_package
        
        return None
    
    def _find_artifact_path(self, artifacts: List[BuildArtifact], artifact_type: str) -> Optional[str]:
        """Find artifact path by type.
        
        Args:
            artifacts: List of artifacts
            artifact_type: Type of artifact to find
            
        Returns:
            Path to artifact if found, None otherwise
        """
        for artifact in artifacts:
            if artifact.artifact_type == artifact_type:
                return artifact.path
        return None
    
    def parse_jenkins_event(self, payload: Dict[str, Any]) -> BuildEvent:
        """Parse Jenkins build event.
        
        Args:
            payload: Jenkins webhook payload
            
        Returns:
            Parsed build event
        """
        build_data = payload.get('build', {})
        
        # Map Jenkins status to our enum
        status_map = {
            'SUCCESS': BuildStatus.SUCCESS,
            'FAILURE': BuildStatus.FAILURE,
            'ABORTED': BuildStatus.CANCELLED,
            'IN_PROGRESS': BuildStatus.IN_PROGRESS
        }
        jenkins_status = build_data.get('status', 'IN_PROGRESS')
        status = status_map.get(jenkins_status, BuildStatus.PENDING)
        
        # Extract build info
        build_id = f"jenkins-{build_data.get('number', 0)}"
        start_time = datetime.fromtimestamp(build_data.get('timestamp', 0) / 1000)
        duration = build_data.get('duration', 0) / 1000  # Convert to seconds
        
        build_info = BuildInfo(
            build_id=build_id,
            build_number=build_data.get('number', 0),
            build_system=BuildSystem.JENKINS,
            build_type=self._infer_build_type(payload),
            status=status,
            start_time=start_time,
            end_time=start_time if duration > 0 else None,
            duration_seconds=duration if duration > 0 else None,
            commit_sha=payload.get('scm', {}).get('commit'),
            branch=payload.get('scm', {}).get('branch'),
            build_log_url=build_data.get('url'),
            triggered_by=payload.get('user', {}).get('name'),
            metadata=payload
        )
        
        # Extract artifacts
        for artifact_data in build_data.get('artifacts', []):
            artifact = BuildArtifact(
                name=artifact_data.get('fileName', ''),
                path=artifact_data.get('relativePath', ''),
                artifact_type=self._infer_artifact_type(artifact_data.get('fileName', '')),
                size_bytes=artifact_data.get('size', 0),
                checksum=artifact_data.get('md5sum', ''),
                url=f"{build_data.get('url')}artifact/{artifact_data.get('relativePath', '')}"
            )
            build_info.artifacts.append(artifact)
        
        event = BuildEvent(
            event_id=f"jenkins-{build_data.get('number', 0)}-{datetime.now().timestamp()}",
            build_system=BuildSystem.JENKINS,
            build_info=build_info
        )
        
        return event
    
    def parse_gitlab_ci_event(self, payload: Dict[str, Any]) -> BuildEvent:
        """Parse GitLab CI build event.
        
        Args:
            payload: GitLab CI webhook payload
            
        Returns:
            Parsed build event
        """
        build_data = payload.get('build', payload)
        
        # Map GitLab status to our enum
        status_map = {
            'success': BuildStatus.SUCCESS,
            'failed': BuildStatus.FAILURE,
            'canceled': BuildStatus.CANCELLED,
            'running': BuildStatus.IN_PROGRESS,
            'pending': BuildStatus.PENDING
        }
        gitlab_status = build_data.get('status', 'pending')
        status = status_map.get(gitlab_status, BuildStatus.PENDING)
        
        # Extract build info
        build_id = f"gitlab-{build_data.get('id', 0)}"
        start_time_str = build_data.get('started_at', build_data.get('created_at'))
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00')) if start_time_str else datetime.now()
        
        end_time = None
        duration = None
        if build_data.get('finished_at'):
            end_time = datetime.fromisoformat(build_data.get('finished_at').replace('Z', '+00:00'))
            duration = build_data.get('duration')
        
        build_info = BuildInfo(
            build_id=build_id,
            build_number=build_data.get('id', 0),
            build_system=BuildSystem.GITLAB_CI,
            build_type=self._infer_build_type(payload),
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            commit_sha=build_data.get('sha', payload.get('commit', {}).get('sha')),
            branch=build_data.get('ref'),
            build_log_url=build_data.get('url'),
            triggered_by=build_data.get('user', {}).get('name'),
            metadata=payload
        )
        
        event = BuildEvent(
            event_id=f"gitlab-{build_data.get('id', 0)}-{datetime.now().timestamp()}",
            build_system=BuildSystem.GITLAB_CI,
            build_info=build_info
        )
        
        return event
    
    def parse_github_actions_event(self, payload: Dict[str, Any]) -> BuildEvent:
        """Parse GitHub Actions build event.
        
        Args:
            payload: GitHub Actions webhook payload
            
        Returns:
            Parsed build event
        """
        workflow_run = payload.get('workflow_run', {})
        
        # Map GitHub Actions status to our enum
        status_map = {
            'completed': BuildStatus.SUCCESS if workflow_run.get('conclusion') == 'success' else BuildStatus.FAILURE,
            'in_progress': BuildStatus.IN_PROGRESS,
            'queued': BuildStatus.PENDING
        }
        github_status = workflow_run.get('status', 'queued')
        status = status_map.get(github_status, BuildStatus.PENDING)
        
        # Extract build info
        build_id = f"github-{workflow_run.get('id', 0)}"
        start_time_str = workflow_run.get('created_at')
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00')) if start_time_str else datetime.now()
        
        end_time = None
        if workflow_run.get('updated_at'):
            end_time = datetime.fromisoformat(workflow_run.get('updated_at').replace('Z', '+00:00'))
        
        build_info = BuildInfo(
            build_id=build_id,
            build_number=workflow_run.get('run_number', 0),
            build_system=BuildSystem.GITHUB_ACTIONS,
            build_type=self._infer_build_type(payload),
            status=status,
            start_time=start_time,
            end_time=end_time,
            commit_sha=workflow_run.get('head_sha'),
            branch=workflow_run.get('head_branch'),
            build_log_url=workflow_run.get('html_url'),
            triggered_by=workflow_run.get('actor', {}).get('login'),
            metadata=payload
        )
        
        event = BuildEvent(
            event_id=f"github-{workflow_run.get('id', 0)}-{datetime.now().timestamp()}",
            build_system=BuildSystem.GITHUB_ACTIONS,
            build_info=build_info
        )
        
        return event
    
    def _infer_build_type(self, payload: Dict[str, Any]) -> BuildType:
        """Infer build type from payload.
        
        Args:
            payload: Build system payload
            
        Returns:
            Inferred build type
        """
        # Check metadata for explicit build type
        metadata = payload.get('metadata', {})
        if 'build_type' in metadata:
            return BuildType(metadata['build_type'])
        
        # Infer from job/workflow name
        name = (
            payload.get('build', {}).get('name', '') or
            payload.get('workflow_run', {}).get('name', '') or
            payload.get('name', '')
        ).lower()
        
        if 'kernel' in name:
            return BuildType.KERNEL
        elif 'bsp' in name:
            return BuildType.BSP
        elif 'module' in name:
            return BuildType.MODULE
        else:
            return BuildType.FULL_SYSTEM
    
    def _infer_artifact_type(self, filename: str) -> str:
        """Infer artifact type from filename.
        
        Args:
            filename: Artifact filename
            
        Returns:
            Inferred artifact type
        """
        filename_lower = filename.lower()
        
        if any(ext in filename_lower for ext in ['.img', 'vmlinuz', 'bzimage', 'zimage']):
            return "kernel_image"
        elif '.config' in filename_lower or 'config' in filename_lower:
            return "config"
        elif 'module' in filename_lower or '.ko' in filename_lower:
            return "module"
        elif any(ext in filename_lower for ext in ['.tar', '.zip', '.deb', '.rpm']):
            return "bsp_package"
        else:
            return "unknown"
    
    def get_build_info(self, build_id: str) -> Optional[BuildInfo]:
        """Get cached build information.
        
        Args:
            build_id: Build identifier
            
        Returns:
            Build info if found, None otherwise
        """
        return self.build_cache.get(build_id)
