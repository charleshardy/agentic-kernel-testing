"""
Build Job Manager Service

Manages build job submission, execution, queuing, and monitoring.
"""

import asyncio
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Dict, List, Optional, Any
from enum import Enum

from infrastructure.models.build_server import (
    BuildJob,
    BuildJobStatus,
    BuildConfig,
    BuildRequirements,
    BuildServer,
)
from infrastructure.models.artifact import Artifact, ArtifactType
from infrastructure.strategies.build_server_strategy import BuildServerSelectionStrategy


class QueuePriority(Enum):
    """Priority levels for build jobs."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class BuildJobConfig:
    """Configuration for submitting a new build job."""
    source_repository: str
    branch: str
    commit_hash: str
    target_architecture: str
    build_config: BuildConfig = field(default_factory=BuildConfig)
    preferred_server_id: Optional[str] = None
    priority: QueuePriority = QueuePriority.NORMAL
    labels: Dict[str, str] = field(default_factory=dict)
    callback_url: Optional[str] = None


@dataclass
class BuildJobResult:
    """Result of build job submission."""
    success: bool
    job: Optional[BuildJob] = None
    error_message: Optional[str] = None
    estimated_start_time: Optional[datetime] = None
    queue_position: Optional[int] = None


@dataclass
class QueueStatus:
    """Status of the build queue."""
    total_queued: int
    total_building: int
    jobs_by_architecture: Dict[str, int] = field(default_factory=dict)
    estimated_wait_time_seconds: int = 0


@dataclass
class CancelResult:
    """Result of cancelling a build job."""
    success: bool
    job: Optional[BuildJob] = None
    error_message: Optional[str] = None


@dataclass
class BuildHistoryFilters:
    """Filters for querying build history."""
    server_id: Optional[str] = None
    architecture: Optional[str] = None
    status: Optional[BuildJobStatus] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class BuildJobManager:
    """
    Manages build job submission, execution, and monitoring.
    
    Handles:
    - Job submission and queuing
    - Server selection and assignment
    - Build execution coordination
    - Log streaming and progress monitoring
    - Job cancellation and retry
    """

    def __init__(
        self,
        server_pool: Dict[str, BuildServer],
        artifact_storage_path: str = "/var/lib/artifacts",
        max_queue_size: int = 1000,
    ):
        self._server_pool = server_pool
        self._artifact_storage_path = artifact_storage_path
        self._max_queue_size = max_queue_size
        
        # Job storage
        self._jobs: Dict[str, BuildJob] = {}
        self._queue: List[str] = []  # Job IDs in queue order
        self._active_builds: Dict[str, str] = {}  # job_id -> server_id
        
        # Selection strategy
        self._selection_strategy = BuildServerSelectionStrategy(server_pool)
        
        # Log storage
        self._job_logs: Dict[str, List[str]] = {}
        
        # Callbacks
        self._status_callbacks: Dict[str, List[Any]] = {}

    async def submit_build(self, config: BuildJobConfig) -> BuildJobResult:
        """
        Submit a new build job.
        
        Args:
            config: Build job configuration
            
        Returns:
            BuildJobResult with job details or error
        """
        # Validate configuration
        if not config.source_repository:
            return BuildJobResult(
                success=False,
                error_message="Source repository is required"
            )
        
        if not config.target_architecture:
            return BuildJobResult(
                success=False,
                error_message="Target architecture is required"
            )
        
        # Check queue capacity
        if len(self._queue) >= self._max_queue_size:
            return BuildJobResult(
                success=False,
                error_message=f"Build queue is full (max {self._max_queue_size} jobs)"
            )
        
        # Create build job
        now = datetime.now(timezone.utc)
        job_id = str(uuid.uuid4())
        
        job = BuildJob(
            id=job_id,
            source_repository=config.source_repository,
            branch=config.branch,
            commit_hash=config.commit_hash,
            target_architecture=config.target_architecture,
            build_config=config.build_config,
            created_at=now,
            updated_at=now,
            status=BuildJobStatus.QUEUED,
        )
        
        # Store job
        self._jobs[job_id] = job
        self._job_logs[job_id] = []
        
        # Try to assign to a server immediately
        requirements = BuildRequirements(
            target_architecture=config.target_architecture,
            preferred_server_id=config.preferred_server_id,
        )
        
        selection_result = await self._selection_strategy.select_server(requirements)
        
        if selection_result.success and selection_result.server:
            # Assign to server and start build
            job.server_id = selection_result.server.id
            await self._start_build(job)
            
            return BuildJobResult(
                success=True,
                job=job,
                estimated_start_time=now,
                queue_position=0,
            )
        else:
            # Add to queue
            self._add_to_queue(job_id, config.priority)
            queue_position = self._queue.index(job_id) + 1
            
            return BuildJobResult(
                success=True,
                job=job,
                estimated_start_time=self._estimate_start_time(queue_position),
                queue_position=queue_position,
            )

    async def get_build_status(self, build_id: str) -> Optional[BuildJobStatus]:
        """Get the current status of a build job."""
        job = self._jobs.get(build_id)
        return job.status if job else None

    async def get_build(self, build_id: str) -> Optional[BuildJob]:
        """Get a build job by ID."""
        return self._jobs.get(build_id)

    async def get_build_logs(
        self,
        build_id: str,
        stream: bool = False
    ) -> AsyncIterator[str]:
        """
        Get build logs.
        
        Args:
            build_id: Build job ID
            stream: If True, stream logs in real-time
            
        Yields:
            Log lines
        """
        if build_id not in self._jobs:
            return
        
        logs = self._job_logs.get(build_id, [])
        
        # Yield existing logs
        for line in logs:
            yield line
        
        if stream:
            # Stream new logs as they arrive
            last_index = len(logs)
            job = self._jobs[build_id]
            
            while job.is_active():
                await asyncio.sleep(0.5)
                current_logs = self._job_logs.get(build_id, [])
                
                for line in current_logs[last_index:]:
                    yield line
                
                last_index = len(current_logs)
                job = self._jobs[build_id]

    async def cancel_build(self, build_id: str) -> CancelResult:
        """
        Cancel a build job.
        
        Args:
            build_id: Build job ID
            
        Returns:
            CancelResult with status
        """
        job = self._jobs.get(build_id)
        
        if not job:
            return CancelResult(
                success=False,
                error_message=f"Build job {build_id} not found"
            )
        
        if job.is_completed():
            return CancelResult(
                success=False,
                job=job,
                error_message=f"Build job {build_id} is already completed"
            )
        
        # Update job status
        job.status = BuildJobStatus.CANCELLED
        job.updated_at = datetime.now(timezone.utc)
        job.completed_at = job.updated_at
        
        # Remove from queue if queued
        if build_id in self._queue:
            self._queue.remove(build_id)
        
        # Remove from active builds
        if build_id in self._active_builds:
            server_id = self._active_builds.pop(build_id)
            # Update server's active build count
            if server_id in self._server_pool:
                self._server_pool[server_id].active_build_count -= 1
        
        self._append_log(build_id, "Build cancelled by user")
        
        return CancelResult(success=True, job=job)

    async def get_build_history(
        self,
        filters: BuildHistoryFilters
    ) -> List[BuildJob]:
        """
        Get build history with optional filters.
        
        Args:
            filters: Query filters
            
        Returns:
            List of matching build jobs
        """
        results = []
        
        for job in self._jobs.values():
            # Apply filters
            if filters.server_id and job.server_id != filters.server_id:
                continue
            if filters.architecture and job.target_architecture != filters.architecture:
                continue
            if filters.status and job.status != filters.status:
                continue
            if filters.branch and job.branch != filters.branch:
                continue
            if filters.commit_hash and job.commit_hash != filters.commit_hash:
                continue
            if filters.since and job.created_at < filters.since:
                continue
            if filters.until and job.created_at > filters.until:
                continue
            
            results.append(job)
        
        # Sort by creation time (newest first)
        results.sort(key=lambda j: j.created_at, reverse=True)
        
        # Apply pagination
        return results[filters.offset:filters.offset + filters.limit]

    async def retry_build(self, build_id: str) -> BuildJobResult:
        """
        Retry a failed or cancelled build.
        
        Args:
            build_id: Build job ID to retry
            
        Returns:
            BuildJobResult with new job details
        """
        original_job = self._jobs.get(build_id)
        
        if not original_job:
            return BuildJobResult(
                success=False,
                error_message=f"Build job {build_id} not found"
            )
        
        if original_job.is_active():
            return BuildJobResult(
                success=False,
                error_message=f"Build job {build_id} is still active"
            )
        
        # Create new job with same configuration
        config = BuildJobConfig(
            source_repository=original_job.source_repository,
            branch=original_job.branch,
            commit_hash=original_job.commit_hash,
            target_architecture=original_job.target_architecture,
            build_config=original_job.build_config,
            preferred_server_id=original_job.server_id,
        )
        
        return await self.submit_build(config)

    async def get_queue_status(self) -> QueueStatus:
        """Get current queue status."""
        jobs_by_arch: Dict[str, int] = {}
        total_building = 0
        
        for job_id in self._queue:
            job = self._jobs.get(job_id)
            if job:
                arch = job.target_architecture
                jobs_by_arch[arch] = jobs_by_arch.get(arch, 0) + 1
        
        for job_id in self._active_builds:
            job = self._jobs.get(job_id)
            if job and job.status == BuildJobStatus.BUILDING:
                total_building += 1
        
        return QueueStatus(
            total_queued=len(self._queue),
            total_building=total_building,
            jobs_by_architecture=jobs_by_arch,
            estimated_wait_time_seconds=len(self._queue) * 300,  # 5 min estimate per job
        )

    async def process_queue(self) -> int:
        """
        Process the build queue, assigning jobs to available servers.
        
        Returns:
            Number of jobs started
        """
        started = 0
        
        for job_id in list(self._queue):
            job = self._jobs.get(job_id)
            if not job:
                self._queue.remove(job_id)
                continue
            
            requirements = BuildRequirements(
                target_architecture=job.target_architecture,
            )
            
            selection_result = await self._selection_strategy.select_server(requirements)
            
            if selection_result.success and selection_result.server:
                self._queue.remove(job_id)
                job.server_id = selection_result.server.id
                await self._start_build(job)
                started += 1
        
        return started

    # Private methods

    def _add_to_queue(self, job_id: str, priority: QueuePriority) -> None:
        """Add a job to the queue with priority ordering."""
        # Find insertion point based on priority
        insert_index = len(self._queue)
        
        for i, queued_id in enumerate(self._queue):
            queued_job = self._jobs.get(queued_id)
            if queued_job:
                # Higher priority jobs go first
                if priority.value > QueuePriority.NORMAL.value:
                    insert_index = i
                    break
        
        self._queue.insert(insert_index, job_id)

    async def _start_build(self, job: BuildJob) -> None:
        """Start a build job on its assigned server."""
        job.status = BuildJobStatus.BUILDING
        job.started_at = datetime.now(timezone.utc)
        job.updated_at = job.started_at
        
        self._active_builds[job.id] = job.server_id
        
        # Update server's active build count
        if job.server_id in self._server_pool:
            self._server_pool[job.server_id].active_build_count += 1
        
        self._append_log(job.id, f"Build started on server {job.server_id}")
        self._append_log(job.id, f"Repository: {job.source_repository}")
        self._append_log(job.id, f"Branch: {job.branch}")
        self._append_log(job.id, f"Commit: {job.commit_hash}")
        self._append_log(job.id, f"Architecture: {job.target_architecture}")

    def _estimate_start_time(self, queue_position: int) -> datetime:
        """Estimate when a queued job will start."""
        from datetime import timedelta
        # Estimate 5 minutes per job ahead in queue
        seconds_to_wait = queue_position * 300
        return datetime.now(timezone.utc) + timedelta(seconds=seconds_to_wait)

    def _append_log(self, job_id: str, message: str) -> None:
        """Append a log message for a job."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_line = f"[{timestamp}] {message}"
        
        if job_id not in self._job_logs:
            self._job_logs[job_id] = []
        
        self._job_logs[job_id].append(log_line)

    async def complete_build(
        self,
        build_id: str,
        success: bool,
        artifacts: List[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[BuildJob]:
        """
        Mark a build as completed.
        
        Args:
            build_id: Build job ID
            success: Whether the build succeeded
            artifacts: List of artifact IDs produced
            error_message: Error message if failed
            
        Returns:
            Updated BuildJob or None if not found
        """
        job = self._jobs.get(build_id)
        if not job:
            return None
        
        now = datetime.now(timezone.utc)
        job.status = BuildJobStatus.COMPLETED if success else BuildJobStatus.FAILED
        job.completed_at = now
        job.updated_at = now
        
        if job.started_at:
            job.duration_seconds = int((now - job.started_at).total_seconds())
        
        if artifacts:
            job.artifacts = artifacts
        
        if error_message:
            job.error_message = error_message
        
        # Remove from active builds
        if build_id in self._active_builds:
            server_id = self._active_builds.pop(build_id)
            if server_id in self._server_pool:
                self._server_pool[server_id].active_build_count -= 1
        
        status_msg = "completed successfully" if success else f"failed: {error_message}"
        self._append_log(build_id, f"Build {status_msg}")
        
        if job.duration_seconds:
            self._append_log(build_id, f"Duration: {job.duration_seconds} seconds")
        
        return job
