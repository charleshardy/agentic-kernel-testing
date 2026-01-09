"""
Pipeline Manager

Manages end-to-end build and test pipelines with stage sequencing.

**Feature: test-infrastructure-management**
**Validates: Requirements 17.1-17.5**
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, AsyncIterator, Callable, Awaitable
from uuid import uuid4

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Type of test environment."""
    QEMU = "qemu"
    PHYSICAL_BOARD = "physical_board"


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(Enum):
    """Pipeline stage status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageType(Enum):
    """Types of pipeline stages."""
    BUILD = "build"
    DEPLOY = "deploy"
    BOOT = "boot"
    TEST = "test"


@dataclass
class PipelineStage:
    """A stage in the pipeline."""
    name: str
    stage_type: StageType
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    output_id: Optional[str] = None  # build_id, deployment_id, etc.
    error_message: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class PipelineConfig:
    """Configuration for creating a pipeline."""
    source_repository: str
    branch: str
    commit_hash: Optional[str] = None
    target_architecture: str = "x86_64"
    environment_type: EnvironmentType = EnvironmentType.QEMU
    environment_config: Dict[str, Any] = field(default_factory=dict)
    build_config: Dict[str, Any] = field(default_factory=dict)
    test_config: Dict[str, Any] = field(default_factory=dict)
    name: Optional[str] = None
    auto_retry: bool = True
    notify_on_completion: bool = True


@dataclass
class Pipeline:
    """
    Represents an end-to-end build and test pipeline.
    
    **Requirement 17.2**: Pipeline stages execute in order:
    build → deploy → boot → test
    """
    id: str
    name: Optional[str] = None
    source_repository: str = ""
    branch: str = ""
    commit_hash: Optional[str] = None
    target_architecture: str = "x86_64"
    environment_type: EnvironmentType = EnvironmentType.QEMU
    environment_config: Dict[str, Any] = field(default_factory=dict)
    stages: List[PipelineStage] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of pipeline creation or operation."""
    success: bool
    pipeline: Optional[Pipeline] = None
    pipeline_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class CancelResult:
    """Result of pipeline cancellation."""
    success: bool
    message: str
    cancelled_stages: List[str] = field(default_factory=list)


@dataclass
class PipelineFilters:
    """Filters for listing pipelines."""
    status: Optional[PipelineStatus] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    architecture: Optional[str] = None
    environment_type: Optional[EnvironmentType] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class PipelineManager:
    """
    Manages end-to-end build and test pipelines.
    
    **Requirement 17.1**: Accept source repository, branch, architecture, and environment preferences
    **Requirement 17.2**: Execute stages in order: build → deploy → boot → test
    **Requirement 17.3**: Update status in real-time and provide logs for each stage
    **Requirement 17.4**: Halt pipeline on stage failure, preserve artifacts and logs
    **Requirement 17.5**: Display pipeline history with stage durations and success rates
    """
    
    # Standard pipeline stages in execution order
    STAGE_ORDER = [StageType.BUILD, StageType.DEPLOY, StageType.BOOT, StageType.TEST]
    
    def __init__(
        self,
        build_job_manager=None,
        deployment_manager=None,
        alert_service=None
    ):
        """
        Initialize the pipeline manager.
        
        Args:
            build_job_manager: Optional BuildJobManager for build stage
            deployment_manager: Optional DeploymentManager for deploy stage
            alert_service: Optional AlertService for failure notifications
        """
        self._build_job_manager = build_job_manager
        self._deployment_manager = deployment_manager
        self._alert_service = alert_service
        
        # Pipelines by ID
        self._pipelines: Dict[str, Pipeline] = {}
        
        # Pipeline history (completed/failed/cancelled)
        self._pipeline_history: List[Pipeline] = []
        self._max_history = 1000
        
        # Stage execution handlers
        self._stage_handlers: Dict[StageType, Callable[[Pipeline, PipelineStage], Awaitable[bool]]] = {}
        
        # Running pipeline tasks
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    def register_stage_handler(
        self,
        stage_type: StageType,
        handler: Callable[[Pipeline, PipelineStage], Awaitable[bool]]
    ) -> None:
        """
        Register a handler for a pipeline stage.
        
        Args:
            stage_type: Type of stage
            handler: Async handler that returns True on success
        """
        self._stage_handlers[stage_type] = handler
        logger.info(f"Registered handler for stage: {stage_type.value}")
    
    async def create_pipeline(self, config: PipelineConfig) -> PipelineResult:
        """
        Create a new pipeline.
        
        **Requirement 17.1**: Accept source repository, branch, architecture, and environment preferences
        
        Args:
            config: Pipeline configuration
            
        Returns:
            PipelineResult with created pipeline
        """
        # Create pipeline
        pipeline = Pipeline(
            id=str(uuid4()),
            name=config.name or f"Pipeline-{config.branch}-{config.target_architecture}",
            source_repository=config.source_repository,
            branch=config.branch,
            commit_hash=config.commit_hash,
            target_architecture=config.target_architecture,
            environment_type=config.environment_type,
            environment_config=config.environment_config,
            metadata={
                "build_config": config.build_config,
                "test_config": config.test_config,
                "auto_retry": config.auto_retry,
                "notify_on_completion": config.notify_on_completion
            }
        )
        
        # Create stages in order
        for stage_type in self.STAGE_ORDER:
            stage = PipelineStage(
                name=stage_type.value,
                stage_type=stage_type,
                max_retries=2 if config.auto_retry else 0
            )
            pipeline.stages.append(stage)
        
        # Store pipeline
        self._pipelines[pipeline.id] = pipeline
        
        logger.info(f"Created pipeline: {pipeline.id} for {config.source_repository}:{config.branch}")
        
        return PipelineResult(
            success=True,
            pipeline=pipeline,
            pipeline_id=pipeline.id
        )
    
    async def start_pipeline(self, pipeline_id: str) -> PipelineResult:
        """
        Start executing a pipeline.
        
        **Requirement 17.2**: Queue build job, upon completion create test environment
        
        Args:
            pipeline_id: Pipeline ID
            
        Returns:
            PipelineResult
        """
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return PipelineResult(
                success=False,
                error_message="Pipeline not found"
            )
        
        if pipeline.status != PipelineStatus.PENDING:
            return PipelineResult(
                success=False,
                error_message=f"Pipeline is not pending (status: {pipeline.status.value})"
            )
        
        # Start pipeline execution
        pipeline.status = PipelineStatus.RUNNING
        pipeline.started_at = datetime.now(timezone.utc)
        pipeline.updated_at = datetime.now(timezone.utc)
        
        # Create execution task
        task = asyncio.create_task(self._execute_pipeline(pipeline))
        self._running_tasks[pipeline_id] = task
        
        logger.info(f"Started pipeline: {pipeline_id}")
        
        return PipelineResult(
            success=True,
            pipeline=pipeline,
            pipeline_id=pipeline_id
        )
    
    async def _execute_pipeline(self, pipeline: Pipeline) -> None:
        """
        Execute pipeline stages in order.
        
        **Requirement 17.2**: Stages execute in order, subsequent stages only start
        after previous stages complete successfully.
        """
        try:
            for stage in pipeline.stages:
                pipeline.current_stage = stage.name
                pipeline.updated_at = datetime.now(timezone.utc)
                
                # Execute stage
                success = await self._execute_stage(pipeline, stage)
                
                if not success:
                    # Stage failed - halt pipeline
                    pipeline.status = PipelineStatus.FAILED
                    pipeline.error_message = f"Stage '{stage.name}' failed: {stage.error_message}"
                    pipeline.completed_at = datetime.now(timezone.utc)
                    pipeline.updated_at = datetime.now(timezone.utc)
                    
                    logger.error(f"Pipeline {pipeline.id} failed at stage {stage.name}")
                    
                    # Notify on failure
                    if self._alert_service and pipeline.metadata.get("notify_on_completion"):
                        await self._notify_failure(pipeline, stage)
                    
                    # Move to history
                    self._move_to_history(pipeline)
                    return
            
            # All stages completed successfully
            pipeline.status = PipelineStatus.COMPLETED
            pipeline.current_stage = None
            pipeline.completed_at = datetime.now(timezone.utc)
            pipeline.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Pipeline {pipeline.id} completed successfully")
            
            # Move to history
            self._move_to_history(pipeline)
            
        except asyncio.CancelledError:
            pipeline.status = PipelineStatus.CANCELLED
            pipeline.completed_at = datetime.now(timezone.utc)
            pipeline.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Pipeline {pipeline.id} was cancelled")
            
            self._move_to_history(pipeline)
            raise
            
        except Exception as e:
            pipeline.status = PipelineStatus.FAILED
            pipeline.error_message = str(e)
            pipeline.completed_at = datetime.now(timezone.utc)
            pipeline.updated_at = datetime.now(timezone.utc)
            
            logger.error(f"Pipeline {pipeline.id} failed with error: {e}")
            
            self._move_to_history(pipeline)
    
    async def _execute_stage(self, pipeline: Pipeline, stage: PipelineStage) -> bool:
        """
        Execute a single pipeline stage with retry support.
        
        **Requirement 17.4**: If stage fails, halt pipeline and preserve artifacts/logs
        
        Args:
            pipeline: Pipeline
            stage: Stage to execute
            
        Returns:
            True if stage completed successfully
        """
        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.now(timezone.utc)
        
        while stage.retry_count <= stage.max_retries:
            try:
                # Get handler for this stage type
                handler = self._stage_handlers.get(stage.stage_type)
                
                if handler:
                    success = await handler(pipeline, stage)
                else:
                    # Default mock execution
                    success = await self._default_stage_handler(pipeline, stage)
                
                if success:
                    stage.status = StageStatus.COMPLETED
                    stage.completed_at = datetime.now(timezone.utc)
                    stage.duration_seconds = int(
                        (stage.completed_at - stage.started_at).total_seconds()
                    )
                    stage.logs.append(f"Stage {stage.name} completed successfully")
                    return True
                else:
                    # Stage failed
                    if stage.retry_count < stage.max_retries:
                        stage.retry_count += 1
                        stage.logs.append(
                            f"Stage {stage.name} failed, retrying ({stage.retry_count}/{stage.max_retries})"
                        )
                        await asyncio.sleep(1)  # Brief delay before retry
                        continue
                    else:
                        stage.status = StageStatus.FAILED
                        stage.completed_at = datetime.now(timezone.utc)
                        stage.duration_seconds = int(
                            (stage.completed_at - stage.started_at).total_seconds()
                        )
                        return False
                        
            except Exception as e:
                stage.error_message = str(e)
                stage.logs.append(f"Stage {stage.name} error: {e}")
                
                if stage.retry_count < stage.max_retries:
                    stage.retry_count += 1
                    stage.logs.append(
                        f"Retrying after error ({stage.retry_count}/{stage.max_retries})"
                    )
                    await asyncio.sleep(1)
                    continue
                else:
                    stage.status = StageStatus.FAILED
                    stage.completed_at = datetime.now(timezone.utc)
                    stage.duration_seconds = int(
                        (stage.completed_at - stage.started_at).total_seconds()
                    )
                    return False
        
        return False
    
    async def _default_stage_handler(
        self,
        pipeline: Pipeline,
        stage: PipelineStage
    ) -> bool:
        """Default stage handler for testing."""
        stage.logs.append(f"Executing {stage.name} stage (default handler)")
        
        # Simulate stage execution
        await asyncio.sleep(0.1)
        
        # Generate mock output ID
        stage.output_id = f"{stage.stage_type.value}-{str(uuid4())[:8]}"
        
        return True
    
    async def _notify_failure(self, pipeline: Pipeline, stage: PipelineStage) -> None:
        """Notify about pipeline failure."""
        if self._alert_service:
            try:
                from infrastructure.services.alert_service import AlertSeverity, AlertCategory
                await self._alert_service.generate_alert(
                    resource_id=pipeline.id,
                    resource_type="pipeline",
                    severity=AlertSeverity.ERROR,
                    category=AlertCategory.PROVISIONING,
                    title=f"Pipeline Failed: {pipeline.name}",
                    message=f"Pipeline failed at stage '{stage.name}': {stage.error_message}",
                    metadata={
                        "pipeline_id": pipeline.id,
                        "stage": stage.name,
                        "repository": pipeline.source_repository,
                        "branch": pipeline.branch
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send failure notification: {e}")
    
    def _move_to_history(self, pipeline: Pipeline) -> None:
        """Move completed pipeline to history."""
        # Remove from active pipelines
        self._pipelines.pop(pipeline.id, None)
        self._running_tasks.pop(pipeline.id, None)
        
        # Add to history
        self._pipeline_history.append(pipeline)
        
        # Trim history if needed
        if len(self._pipeline_history) > self._max_history:
            self._pipeline_history = self._pipeline_history[-self._max_history:]
    
    async def get_pipeline_status(self, pipeline_id: str) -> Optional[Pipeline]:
        """
        Get current pipeline status.
        
        **Requirement 17.3**: Update status in real-time
        
        Args:
            pipeline_id: Pipeline ID
            
        Returns:
            Pipeline or None if not found
        """
        # Check active pipelines
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline:
            return pipeline
        
        # Check history
        for p in self._pipeline_history:
            if p.id == pipeline_id:
                return p
        
        return None
    
    async def cancel_pipeline(self, pipeline_id: str) -> CancelResult:
        """
        Cancel a running pipeline.
        
        Args:
            pipeline_id: Pipeline ID
            
        Returns:
            CancelResult
        """
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return CancelResult(
                success=False,
                message="Pipeline not found"
            )
        
        if pipeline.status not in (PipelineStatus.PENDING, PipelineStatus.RUNNING):
            return CancelResult(
                success=False,
                message=f"Pipeline cannot be cancelled (status: {pipeline.status.value})"
            )
        
        # Cancel running task
        task = self._running_tasks.get(pipeline_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Mark cancelled stages
        cancelled_stages = []
        for stage in pipeline.stages:
            if stage.status in (StageStatus.PENDING, StageStatus.RUNNING):
                stage.status = StageStatus.SKIPPED
                cancelled_stages.append(stage.name)
        
        pipeline.status = PipelineStatus.CANCELLED
        pipeline.completed_at = datetime.now(timezone.utc)
        pipeline.updated_at = datetime.now(timezone.utc)
        
        self._move_to_history(pipeline)
        
        logger.info(f"Cancelled pipeline: {pipeline_id}")
        
        return CancelResult(
            success=True,
            message="Pipeline cancelled",
            cancelled_stages=cancelled_stages
        )
    
    async def get_pipeline_history(
        self,
        filters: Optional[PipelineFilters] = None
    ) -> List[Pipeline]:
        """
        Get pipeline history with optional filters.
        
        **Requirement 17.5**: Display pipeline history with stage durations and success rates
        
        Args:
            filters: Optional filters
            
        Returns:
            List of pipelines
        """
        pipelines = list(self._pipeline_history)
        
        if filters:
            if filters.status:
                pipelines = [p for p in pipelines if p.status == filters.status]
            if filters.repository:
                pipelines = [p for p in pipelines if p.source_repository == filters.repository]
            if filters.branch:
                pipelines = [p for p in pipelines if p.branch == filters.branch]
            if filters.architecture:
                pipelines = [p for p in pipelines if p.target_architecture == filters.architecture]
            if filters.environment_type:
                pipelines = [p for p in pipelines if p.environment_type == filters.environment_type]
            if filters.created_after:
                pipelines = [p for p in pipelines if p.created_at >= filters.created_after]
            if filters.created_before:
                pipelines = [p for p in pipelines if p.created_at <= filters.created_before]
        
        return sorted(pipelines, key=lambda p: p.created_at, reverse=True)
    
    async def get_stage_logs(
        self,
        pipeline_id: str,
        stage: str
    ) -> AsyncIterator[str]:
        """
        Get logs for a specific pipeline stage.
        
        **Requirement 17.3**: Provide logs for each stage
        
        Args:
            pipeline_id: Pipeline ID
            stage: Stage name
            
        Yields:
            Log lines
        """
        pipeline = await self.get_pipeline_status(pipeline_id)
        if not pipeline:
            yield "Pipeline not found"
            return
        
        for s in pipeline.stages:
            if s.name == stage:
                for log_line in s.logs:
                    yield log_line
                return
        
        yield f"Stage '{stage}' not found"
    
    async def retry_pipeline_stage(
        self,
        pipeline_id: str,
        stage: str
    ) -> PipelineResult:
        """
        Retry a failed pipeline stage.
        
        Args:
            pipeline_id: Pipeline ID
            stage: Stage name to retry
            
        Returns:
            PipelineResult
        """
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            # Check history
            for p in self._pipeline_history:
                if p.id == pipeline_id:
                    pipeline = p
                    break
        
        if not pipeline:
            return PipelineResult(
                success=False,
                error_message="Pipeline not found"
            )
        
        # Find the stage
        target_stage = None
        for s in pipeline.stages:
            if s.name == stage:
                target_stage = s
                break
        
        if not target_stage:
            return PipelineResult(
                success=False,
                error_message=f"Stage '{stage}' not found"
            )
        
        if target_stage.status != StageStatus.FAILED:
            return PipelineResult(
                success=False,
                error_message=f"Stage '{stage}' is not failed (status: {target_stage.status.value})"
            )
        
        # Reset stage and subsequent stages
        found = False
        for s in pipeline.stages:
            if s.name == stage:
                found = True
            if found:
                s.status = StageStatus.PENDING
                s.started_at = None
                s.completed_at = None
                s.duration_seconds = None
                s.error_message = None
                s.retry_count = 0
        
        # Move back to active pipelines if in history
        if pipeline_id not in self._pipelines:
            self._pipelines[pipeline_id] = pipeline
            self._pipeline_history = [p for p in self._pipeline_history if p.id != pipeline_id]
        
        # Restart pipeline
        pipeline.status = PipelineStatus.RUNNING
        pipeline.error_message = None
        pipeline.completed_at = None
        pipeline.updated_at = datetime.now(timezone.utc)
        
        # Create new execution task
        task = asyncio.create_task(self._execute_pipeline_from_stage(pipeline, stage))
        self._running_tasks[pipeline_id] = task
        
        logger.info(f"Retrying pipeline {pipeline_id} from stage {stage}")
        
        return PipelineResult(
            success=True,
            pipeline=pipeline,
            pipeline_id=pipeline_id
        )
    
    async def _execute_pipeline_from_stage(
        self,
        pipeline: Pipeline,
        start_stage: str
    ) -> None:
        """Execute pipeline starting from a specific stage."""
        try:
            started = False
            for stage in pipeline.stages:
                if stage.name == start_stage:
                    started = True
                
                if not started:
                    continue
                
                pipeline.current_stage = stage.name
                pipeline.updated_at = datetime.now(timezone.utc)
                
                success = await self._execute_stage(pipeline, stage)
                
                if not success:
                    pipeline.status = PipelineStatus.FAILED
                    pipeline.error_message = f"Stage '{stage.name}' failed: {stage.error_message}"
                    pipeline.completed_at = datetime.now(timezone.utc)
                    pipeline.updated_at = datetime.now(timezone.utc)
                    
                    self._move_to_history(pipeline)
                    return
            
            pipeline.status = PipelineStatus.COMPLETED
            pipeline.current_stage = None
            pipeline.completed_at = datetime.now(timezone.utc)
            pipeline.updated_at = datetime.now(timezone.utc)
            
            self._move_to_history(pipeline)
            
        except asyncio.CancelledError:
            pipeline.status = PipelineStatus.CANCELLED
            pipeline.completed_at = datetime.now(timezone.utc)
            pipeline.updated_at = datetime.now(timezone.utc)
            
            self._move_to_history(pipeline)
            raise
    
    def get_success_rate(
        self,
        repository: Optional[str] = None,
        branch: Optional[str] = None
    ) -> float:
        """
        Calculate pipeline success rate.
        
        **Requirement 17.5**: Display success rates
        
        Args:
            repository: Optional repository filter
            branch: Optional branch filter
            
        Returns:
            Success rate as percentage (0-100)
        """
        pipelines = self._pipeline_history
        
        if repository:
            pipelines = [p for p in pipelines if p.source_repository == repository]
        if branch:
            pipelines = [p for p in pipelines if p.branch == branch]
        
        if not pipelines:
            return 0.0
        
        completed = sum(1 for p in pipelines if p.status == PipelineStatus.COMPLETED)
        return (completed / len(pipelines)) * 100
    
    def get_average_duration(
        self,
        repository: Optional[str] = None,
        branch: Optional[str] = None
    ) -> Optional[float]:
        """
        Calculate average pipeline duration in seconds.
        
        Args:
            repository: Optional repository filter
            branch: Optional branch filter
            
        Returns:
            Average duration in seconds or None if no data
        """
        pipelines = [
            p for p in self._pipeline_history
            if p.status == PipelineStatus.COMPLETED
            and p.started_at and p.completed_at
        ]
        
        if repository:
            pipelines = [p for p in pipelines if p.source_repository == repository]
        if branch:
            pipelines = [p for p in pipelines if p.branch == branch]
        
        if not pipelines:
            return None
        
        durations = [
            (p.completed_at - p.started_at).total_seconds()
            for p in pipelines
        ]
        
        return sum(durations) / len(durations)
    
    def validate_stage_order(self, stages: List[PipelineStage]) -> bool:
        """
        Validate that stages are in correct order.
        
        **Property 7: Pipeline Stage Sequencing**
        
        Args:
            stages: List of stages
            
        Returns:
            True if stages are in correct order
        """
        if not stages:
            return True
        
        stage_types = [s.stage_type for s in stages]
        
        # Check order matches STAGE_ORDER
        expected_idx = 0
        for stage_type in stage_types:
            while expected_idx < len(self.STAGE_ORDER):
                if self.STAGE_ORDER[expected_idx] == stage_type:
                    expected_idx += 1
                    break
                expected_idx += 1
            else:
                # Stage type not found in remaining order
                return False
        
        return True
    
    def can_start_stage(self, pipeline: Pipeline, stage_name: str) -> bool:
        """
        Check if a stage can be started based on previous stage completion.
        
        **Property 7**: Subsequent stages only start after previous stages complete
        
        Args:
            pipeline: Pipeline
            stage_name: Stage to check
            
        Returns:
            True if stage can be started
        """
        for i, stage in enumerate(pipeline.stages):
            if stage.name == stage_name:
                # First stage can always start
                if i == 0:
                    return True
                
                # Check previous stage is completed
                prev_stage = pipeline.stages[i - 1]
                return prev_stage.status == StageStatus.COMPLETED
        
        return False
    
    @property
    def active_pipeline_count(self) -> int:
        """Get count of active pipelines."""
        return len(self._pipelines)
    
    @property
    def history_count(self) -> int:
        """Get count of pipelines in history."""
        return len(self._pipeline_history)
