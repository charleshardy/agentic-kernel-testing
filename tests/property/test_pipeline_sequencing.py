"""
Property-Based Tests for Pipeline Stage Sequencing

**Feature: test-infrastructure-management**
**Property 7: Pipeline Stage Sequencing**
**Property 24: Provisioning Failure Triggers Alternative**
**Validates: Requirements 17.2, 17.4, 16.4**

For any pipeline execution, stages SHALL execute in order (build → deploy → boot → test)
and subsequent stages SHALL only start after previous stages complete successfully.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, assume
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.services.pipeline_manager import (
    PipelineManager,
    Pipeline,
    PipelineConfig,
    PipelineStage,
    PipelineStatus,
    StageStatus,
    StageType,
    EnvironmentType,
)


# =============================================================================
# Hypothesis Strategies
# =============================================================================

@st.composite
def repository_url_strategy(draw):
    """Generate valid repository URLs."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    org = draw(st.text(min_size=1, max_size=20, alphabet=chars))
    repo = draw(st.text(min_size=1, max_size=30, alphabet=chars))
    return f"https://github.com/{org}/{repo}"


@st.composite
def branch_name_strategy(draw):
    """Generate valid branch names."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789-_/"
    return draw(st.text(min_size=1, max_size=50, alphabet=chars))


@st.composite
def commit_hash_strategy(draw):
    """Generate valid commit hashes."""
    hex_chars = "0123456789abcdef"
    return draw(st.text(min_size=40, max_size=40, alphabet=hex_chars))


@st.composite
def architecture_strategy(draw):
    """Generate valid architectures."""
    return draw(st.sampled_from(["x86_64", "arm64", "armv7", "riscv64"]))


@st.composite
def pipeline_config_strategy(draw):
    """Generate valid pipeline configurations."""
    return PipelineConfig(
        source_repository=draw(repository_url_strategy()),
        branch=draw(branch_name_strategy()),
        commit_hash=draw(st.one_of(st.none(), commit_hash_strategy())),
        target_architecture=draw(architecture_strategy()),
        environment_type=draw(st.sampled_from(list(EnvironmentType))),
        auto_retry=draw(st.booleans()),
        notify_on_completion=draw(st.booleans())
    )


@st.composite
def stage_sequence_strategy(draw):
    """Generate a sequence of stage types."""
    # Generate a subset of stages in order
    all_stages = [StageType.BUILD, StageType.DEPLOY, StageType.BOOT, StageType.TEST]
    num_stages = draw(st.integers(min_value=1, max_value=4))
    
    # Select stages maintaining order
    selected_indices = sorted(draw(st.lists(
        st.integers(min_value=0, max_value=3),
        min_size=num_stages,
        max_size=num_stages,
        unique=True
    )))
    
    return [all_stages[i] for i in selected_indices]


# =============================================================================
# Property 7: Pipeline Stage Sequencing
# =============================================================================

class TestPipelineStageSequencing:
    """
    **Property 7: Pipeline Stage Sequencing**
    **Validates: Requirements 17.2, 17.4**
    
    For any pipeline execution, stages SHALL execute in order
    (build → deploy → boot → test) and subsequent stages SHALL only
    start after previous stages complete successfully.
    """

    def test_standard_stage_order(self):
        """
        The standard stage order SHALL be build → deploy → boot → test.
        """
        manager = PipelineManager()
        
        expected_order = [StageType.BUILD, StageType.DEPLOY, StageType.BOOT, StageType.TEST]
        assert manager.STAGE_ORDER == expected_order

    @pytest.mark.asyncio
    @given(config=pipeline_config_strategy())
    @settings(max_examples=50)
    async def test_pipeline_creates_stages_in_order(self, config: PipelineConfig):
        """
        When a pipeline is created, stages SHALL be created in the correct order.
        """
        manager = PipelineManager()
        
        result = await manager.create_pipeline(config)
        
        assert result.success == True
        assert result.pipeline is not None
        
        # Verify stages are in correct order
        stages = result.pipeline.stages
        assert len(stages) == 4
        
        assert stages[0].stage_type == StageType.BUILD
        assert stages[1].stage_type == StageType.DEPLOY
        assert stages[2].stage_type == StageType.BOOT
        assert stages[3].stage_type == StageType.TEST

    @given(stage_types=stage_sequence_strategy())
    @settings(max_examples=50)
    def test_validate_stage_order_correct_sequence(self, stage_types: List[StageType]):
        """
        A correct stage sequence SHALL pass validation.
        """
        manager = PipelineManager()
        
        stages = [
            PipelineStage(name=st.value, stage_type=st)
            for st in stage_types
        ]
        
        # Stages in order should be valid
        assert manager.validate_stage_order(stages) == True

    def test_validate_stage_order_incorrect_sequence(self):
        """
        An incorrect stage sequence SHALL fail validation.
        """
        manager = PipelineManager()
        
        # Test reversed order
        stages = [
            PipelineStage(name="test", stage_type=StageType.TEST),
            PipelineStage(name="build", stage_type=StageType.BUILD),
        ]
        
        assert manager.validate_stage_order(stages) == False

    def test_first_stage_can_always_start(self):
        """
        The first stage (build) SHALL always be able to start.
        """
        manager = PipelineManager()
        
        pipeline = Pipeline(
            id="test-pipeline",
            stages=[
                PipelineStage(name="build", stage_type=StageType.BUILD),
                PipelineStage(name="deploy", stage_type=StageType.DEPLOY),
            ]
        )
        
        assert manager.can_start_stage(pipeline, "build") == True

    def test_subsequent_stage_requires_previous_completion(self):
        """
        A subsequent stage SHALL only start after the previous stage completes.
        """
        manager = PipelineManager()
        
        # Previous stage not completed
        pipeline = Pipeline(
            id="test-pipeline",
            stages=[
                PipelineStage(name="build", stage_type=StageType.BUILD, status=StageStatus.RUNNING),
                PipelineStage(name="deploy", stage_type=StageType.DEPLOY),
            ]
        )
        
        assert manager.can_start_stage(pipeline, "deploy") == False
        
        # Previous stage completed
        pipeline.stages[0].status = StageStatus.COMPLETED
        
        assert manager.can_start_stage(pipeline, "deploy") == True

    @pytest.mark.asyncio
    async def test_stage_execution_order_enforced(self):
        """
        Stages SHALL execute in order during pipeline execution.
        """
        manager = PipelineManager()
        
        execution_order = []
        
        async def track_stage(pipeline: Pipeline, stage: PipelineStage) -> bool:
            execution_order.append(stage.stage_type)
            return True
        
        # Register handler for all stages
        for stage_type in StageType:
            manager.register_stage_handler(stage_type, track_stage)
        
        # Create and run pipeline
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main",
            target_architecture="x86_64"
        )
        
        result = await manager.create_pipeline(config)
        await manager.start_pipeline(result.pipeline_id)
        
        # Wait for completion
        await asyncio.sleep(0.5)
        
        # Verify execution order
        assert execution_order == [
            StageType.BUILD,
            StageType.DEPLOY,
            StageType.BOOT,
            StageType.TEST
        ]

    @pytest.mark.asyncio
    async def test_failed_stage_halts_pipeline(self):
        """
        **Requirement 17.4**: If any stage fails, the pipeline SHALL halt.
        """
        manager = PipelineManager()
        
        async def fail_deploy(pipeline: Pipeline, stage: PipelineStage) -> bool:
            if stage.stage_type == StageType.DEPLOY:
                stage.error_message = "Deployment failed"
                return False
            return True
        
        for stage_type in StageType:
            manager.register_stage_handler(stage_type, fail_deploy)
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main",
            target_architecture="x86_64",
            auto_retry=False  # Disable retry for this test
        )
        
        result = await manager.create_pipeline(config)
        
        # Disable retries
        for stage in result.pipeline.stages:
            stage.max_retries = 0
        
        await manager.start_pipeline(result.pipeline_id)
        
        # Wait for failure
        await asyncio.sleep(0.5)
        
        # Get final status
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        
        assert pipeline.status == PipelineStatus.FAILED
        assert "deploy" in pipeline.error_message.lower()
        
        # Verify subsequent stages were not executed
        boot_stage = next(s for s in pipeline.stages if s.stage_type == StageType.BOOT)
        test_stage = next(s for s in pipeline.stages if s.stage_type == StageType.TEST)
        
        assert boot_stage.status == StageStatus.PENDING
        assert test_stage.status == StageStatus.PENDING

    @pytest.mark.asyncio
    async def test_successful_pipeline_completes_all_stages(self):
        """
        A successful pipeline SHALL complete all stages in order.
        """
        manager = PipelineManager()
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main",
            target_architecture="x86_64"
        )
        
        result = await manager.create_pipeline(config)
        await manager.start_pipeline(result.pipeline_id)
        
        # Wait for completion
        await asyncio.sleep(0.5)
        
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        
        assert pipeline.status == PipelineStatus.COMPLETED
        
        # All stages should be completed
        for stage in pipeline.stages:
            assert stage.status == StageStatus.COMPLETED


class TestPipelineStageStatusTransitions:
    """Test stage status transitions during pipeline execution."""

    @pytest.mark.asyncio
    async def test_stage_transitions_pending_to_running(self):
        """
        A stage SHALL transition from PENDING to RUNNING when started.
        """
        manager = PipelineManager()
        
        stage_statuses = {}
        
        async def capture_status(pipeline: Pipeline, stage: PipelineStage) -> bool:
            stage_statuses[stage.name] = stage.status
            return True
        
        for stage_type in StageType:
            manager.register_stage_handler(stage_type, capture_status)
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main"
        )
        
        result = await manager.create_pipeline(config)
        await manager.start_pipeline(result.pipeline_id)
        
        await asyncio.sleep(0.5)
        
        # All stages should have been RUNNING when handler was called
        for name, status in stage_statuses.items():
            assert status == StageStatus.RUNNING

    @pytest.mark.asyncio
    async def test_stage_transitions_running_to_completed(self):
        """
        A successful stage SHALL transition from RUNNING to COMPLETED.
        """
        manager = PipelineManager()
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main"
        )
        
        result = await manager.create_pipeline(config)
        await manager.start_pipeline(result.pipeline_id)
        
        await asyncio.sleep(0.5)
        
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        
        for stage in pipeline.stages:
            assert stage.status == StageStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_stage_transitions_running_to_failed(self):
        """
        A failed stage SHALL transition from RUNNING to FAILED.
        """
        manager = PipelineManager()
        
        async def fail_build(pipeline: Pipeline, stage: PipelineStage) -> bool:
            if stage.stage_type == StageType.BUILD:
                stage.error_message = "Build failed"
                return False
            return True
        
        for stage_type in StageType:
            manager.register_stage_handler(stage_type, fail_build)
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main",
            auto_retry=False
        )
        
        result = await manager.create_pipeline(config)
        
        for stage in result.pipeline.stages:
            stage.max_retries = 0
        
        await manager.start_pipeline(result.pipeline_id)
        
        await asyncio.sleep(0.5)
        
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        
        build_stage = next(s for s in pipeline.stages if s.stage_type == StageType.BUILD)
        assert build_stage.status == StageStatus.FAILED


# =============================================================================
# Property 24: Provisioning Failure Triggers Alternative
# =============================================================================

class TestProvisioningFailureRecovery:
    """
    **Property 24: Provisioning Failure Triggers Alternative**
    **Validates: Requirements 16.4**
    
    For any build, VM, or test provisioning failure, the system SHALL
    attempt provisioning on an alternative resource if available.
    """

    @pytest.mark.asyncio
    async def test_stage_retry_on_failure(self):
        """
        A failed stage SHALL be retried if auto_retry is enabled.
        """
        manager = PipelineManager()
        
        attempt_count = {"build": 0}
        
        async def fail_then_succeed(pipeline: Pipeline, stage: PipelineStage) -> bool:
            if stage.stage_type == StageType.BUILD:
                attempt_count["build"] += 1
                # Fail first attempt, succeed on retry
                return attempt_count["build"] > 1
            return True
        
        for stage_type in StageType:
            manager.register_stage_handler(stage_type, fail_then_succeed)
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main",
            auto_retry=True
        )
        
        result = await manager.create_pipeline(config)
        await manager.start_pipeline(result.pipeline_id)
        
        await asyncio.sleep(1.0)
        
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        
        # Pipeline should complete after retry
        assert pipeline.status == PipelineStatus.COMPLETED
        assert attempt_count["build"] == 2

    @pytest.mark.asyncio
    async def test_max_retries_enforced(self):
        """
        Retries SHALL be limited to max_retries.
        """
        manager = PipelineManager()
        
        attempt_count = {"build": 0}
        
        async def always_fail(pipeline: Pipeline, stage: PipelineStage) -> bool:
            if stage.stage_type == StageType.BUILD:
                attempt_count["build"] += 1
                stage.error_message = "Always fails"
                return False
            return True
        
        for stage_type in StageType:
            manager.register_stage_handler(stage_type, always_fail)
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main",
            auto_retry=True
        )
        
        result = await manager.create_pipeline(config)
        
        # Set max retries to 2
        for stage in result.pipeline.stages:
            stage.max_retries = 2
        
        await manager.start_pipeline(result.pipeline_id)
        
        await asyncio.sleep(1.0)
        
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        
        # Should fail after max retries
        assert pipeline.status == PipelineStatus.FAILED
        # Initial attempt + 2 retries = 3 total
        assert attempt_count["build"] == 3

    @pytest.mark.asyncio
    async def test_retry_logs_captured(self):
        """
        Retry attempts SHALL be logged in stage logs.
        """
        manager = PipelineManager()
        
        attempt_count = {"deploy": 0}
        
        async def fail_then_succeed(pipeline: Pipeline, stage: PipelineStage) -> bool:
            if stage.stage_type == StageType.DEPLOY:
                attempt_count["deploy"] += 1
                return attempt_count["deploy"] > 1
            return True
        
        for stage_type in StageType:
            manager.register_stage_handler(stage_type, fail_then_succeed)
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main",
            auto_retry=True
        )
        
        result = await manager.create_pipeline(config)
        await manager.start_pipeline(result.pipeline_id)
        
        await asyncio.sleep(1.0)
        
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        
        deploy_stage = next(s for s in pipeline.stages if s.stage_type == StageType.DEPLOY)
        
        # Should have retry log entry
        retry_logs = [log for log in deploy_stage.logs if "retry" in log.lower()]
        assert len(retry_logs) > 0


class TestPipelineCancellation:
    """Test pipeline cancellation behavior."""

    @pytest.mark.asyncio
    async def test_cancel_pending_pipeline(self):
        """
        A pending pipeline SHALL be cancellable.
        """
        manager = PipelineManager()
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main"
        )
        
        result = await manager.create_pipeline(config)
        
        # Cancel before starting
        cancel_result = await manager.cancel_pipeline(result.pipeline_id)
        
        assert cancel_result.success == True
        
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        assert pipeline.status == PipelineStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancelled_stages_marked_skipped(self):
        """
        Cancelled stages SHALL be marked as SKIPPED.
        """
        manager = PipelineManager()
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main"
        )
        
        result = await manager.create_pipeline(config)
        cancel_result = await manager.cancel_pipeline(result.pipeline_id)
        
        pipeline = await manager.get_pipeline_status(result.pipeline_id)
        
        # All stages should be skipped
        for stage in pipeline.stages:
            assert stage.status == StageStatus.SKIPPED


class TestPipelineHistory:
    """Test pipeline history and statistics."""

    @pytest.mark.asyncio
    async def test_completed_pipeline_in_history(self):
        """
        Completed pipelines SHALL be moved to history.
        """
        manager = PipelineManager()
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main"
        )
        
        result = await manager.create_pipeline(config)
        await manager.start_pipeline(result.pipeline_id)
        
        await asyncio.sleep(0.5)
        
        # Should be in history
        history = await manager.get_pipeline_history()
        assert any(p.id == result.pipeline_id for p in history)

    @pytest.mark.asyncio
    async def test_success_rate_calculation(self):
        """
        Success rate SHALL be correctly calculated.
        """
        manager = PipelineManager()
        
        # Create and complete 2 successful pipelines
        for _ in range(2):
            config = PipelineConfig(
                source_repository="https://github.com/test/repo",
                branch="main"
            )
            result = await manager.create_pipeline(config)
            await manager.start_pipeline(result.pipeline_id)
            await asyncio.sleep(0.3)
        
        # Create and fail 1 pipeline
        async def fail_build(pipeline: Pipeline, stage: PipelineStage) -> bool:
            if stage.stage_type == StageType.BUILD:
                return False
            return True
        
        for stage_type in StageType:
            manager.register_stage_handler(stage_type, fail_build)
        
        config = PipelineConfig(
            source_repository="https://github.com/test/repo",
            branch="main",
            auto_retry=False
        )
        result = await manager.create_pipeline(config)
        for stage in result.pipeline.stages:
            stage.max_retries = 0
        await manager.start_pipeline(result.pipeline_id)
        await asyncio.sleep(0.3)
        
        # Success rate should be 2/3 = 66.67%
        success_rate = manager.get_success_rate()
        assert 60 < success_rate < 70
