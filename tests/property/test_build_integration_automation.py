"""Property-based tests for build integration automation.

Feature: agentic-kernel-testing, Property 23: Build integration automation
Validates: Requirements 5.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from typing import List

from integration.build_models import (
    BuildEvent, BuildInfo, BuildStatus, BuildSystem, BuildType,
    KernelImage, BSPPackage, BuildArtifact
)
from integration.build_integration import BuildIntegration


# Custom strategies for generating test data
@st.composite
def build_artifact_strategy(draw):
    """Generate random build artifact."""
    artifact_types = ["kernel_image", "bsp_package", "module", "config", "unknown"]
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-_')))
    
    return BuildArtifact(
        name=name,
        path=f"/build/artifacts/{name}",
        artifact_type=draw(st.sampled_from(artifact_types)),
        size_bytes=draw(st.integers(min_value=1, max_value=1000000000)),
        checksum=draw(st.text(min_size=32, max_size=64, alphabet='0123456789abcdef')),
        url=f"https://build.example.com/artifacts/{name}",
        metadata={}
    )


@st.composite
def kernel_image_strategy(draw):
    """Generate random kernel image."""
    architectures = ["x86_64", "arm64", "riscv64", "arm"]
    version = f"{draw(st.integers(min_value=3, max_value=6))}.{draw(st.integers(min_value=0, max_value=20))}.{draw(st.integers(min_value=0, max_value=100))}"
    
    return KernelImage(
        version=version,
        architecture=draw(st.sampled_from(architectures)),
        image_path=f"/build/vmlinuz-{version}",
        config_path=f"/build/config-{version}",
        modules_path=f"/build/modules-{version}",
        build_timestamp=datetime.now() - timedelta(minutes=draw(st.integers(min_value=0, max_value=1440))),
        commit_sha=draw(st.text(min_size=40, max_size=40, alphabet='0123456789abcdef')),
        metadata={}
    )


@st.composite
def bsp_package_strategy(draw):
    """Generate random BSP package."""
    architectures = ["x86_64", "arm64", "riscv64", "arm"]
    boards = ["raspberry-pi-4", "beaglebone-black", "nvidia-jetson", "generic-x86"]
    name = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
    version = f"{draw(st.integers(min_value=1, max_value=10))}.{draw(st.integers(min_value=0, max_value=20))}"
    
    return BSPPackage(
        name=name,
        version=version,
        target_board=draw(st.sampled_from(boards)),
        architecture=draw(st.sampled_from(architectures)),
        package_path=f"/build/{name}-{version}.tar.gz",
        kernel_version=f"{draw(st.integers(min_value=3, max_value=6))}.{draw(st.integers(min_value=0, max_value=20))}",
        build_timestamp=datetime.now() - timedelta(minutes=draw(st.integers(min_value=0, max_value=1440))),
        commit_sha=draw(st.text(min_size=40, max_size=40, alphabet='0123456789abcdef')),
        metadata={}
    )


@st.composite
def build_info_strategy(draw):
    """Generate random build info."""
    build_number = draw(st.integers(min_value=1, max_value=10000))
    build_system = draw(st.sampled_from(list(BuildSystem)))
    build_type = draw(st.sampled_from(list(BuildType)))
    status = draw(st.sampled_from(list(BuildStatus)))
    
    start_time = datetime.now() - timedelta(minutes=draw(st.integers(min_value=10, max_value=1440)))
    
    # Only completed builds have end time
    end_time = None
    duration = None
    if status in [BuildStatus.SUCCESS, BuildStatus.FAILURE, BuildStatus.CANCELLED]:
        duration = draw(st.floats(min_value=1.0, max_value=3600.0))
        end_time = start_time + timedelta(seconds=duration)
    
    # Generate artifacts
    artifacts = draw(st.lists(build_artifact_strategy(), min_size=0, max_size=5))
    
    # Add kernel image for kernel builds
    kernel_image = None
    if build_type in [BuildType.KERNEL, BuildType.FULL_SYSTEM]:
        kernel_image = draw(st.one_of(st.none(), kernel_image_strategy()))
    
    # Add BSP package for BSP builds
    bsp_package = None
    if build_type in [BuildType.BSP, BuildType.FULL_SYSTEM]:
        bsp_package = draw(st.one_of(st.none(), bsp_package_strategy()))
    
    build_id = f"{build_system.value}-{build_number}"
    
    return BuildInfo(
        build_id=build_id,
        build_number=build_number,
        build_system=build_system,
        build_type=build_type,
        status=status,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        commit_sha=draw(st.one_of(st.none(), st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'))),
        branch=draw(st.one_of(st.none(), st.sampled_from(['main', 'master', 'develop', 'feature/test']))),
        artifacts=artifacts,
        kernel_image=kernel_image,
        bsp_package=bsp_package,
        build_log_url=f"https://build.example.com/builds/{build_number}",
        triggered_by=draw(st.one_of(st.none(), st.text(min_size=1, max_size=30))),
        metadata={}
    )


@st.composite
def build_event_strategy(draw):
    """Generate random build event."""
    build_info = draw(build_info_strategy())
    event_id = f"{build_info.build_system.value}-{build_info.build_number}-{draw(st.integers(min_value=1, max_value=1000))}"
    
    return BuildEvent(
        event_id=event_id,
        build_system=build_info.build_system,
        build_info=build_info,
        timestamp=datetime.now(),
        metadata={}
    )


class TestBuildIntegrationAutomation:
    """Test build integration automation property.
    
    Property 23: Build integration automation
    For any newly built kernel image or BSP package, the system should
    automatically initiate testing without manual intervention.
    """
    
    @given(build_event=build_event_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_successful_builds_trigger_handlers(self, build_event: BuildEvent):
        """Test that successful builds trigger registered handlers.
        
        For any build event with successful status, when a handler is registered,
        the handler should be called automatically.
        """
        # Only test successful builds
        assume(build_event.build_info.status == BuildStatus.SUCCESS)
        assume(build_event.build_info.build_type in [BuildType.KERNEL, BuildType.BSP, BuildType.FULL_SYSTEM])
        
        # Arrange
        integration = BuildIntegration()
        handler_called = []
        
        def test_handler(event: BuildEvent):
            handler_called.append(event)
        
        integration.register_build_handler(test_handler)
        
        # Act
        integration.handle_build_event(build_event)
        
        # Assert - handler should have been called for successful builds
        assert len(handler_called) == 1
        assert handler_called[0] == build_event
    
    @given(build_event=build_event_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_failed_builds_do_not_trigger_tests(self, build_event: BuildEvent):
        """Test that failed builds do not trigger test handlers.
        
        For any build event with failed status, handlers should not be called
        since there's nothing to test.
        """
        # Only test failed builds
        assume(build_event.build_info.status == BuildStatus.FAILURE)
        
        # Arrange
        integration = BuildIntegration()
        handler_called = []
        
        def test_handler(event: BuildEvent):
            handler_called.append(event)
        
        integration.register_build_handler(test_handler)
        
        # Act
        integration.handle_build_event(build_event)
        
        # Assert - handler should not have been called for failed builds
        assert len(handler_called) == 0
    
    @given(build_event=build_event_strategy())
    @settings(max_examples=100, deadline=None)
    def test_build_completion_detection(self, build_event: BuildEvent):
        """Test that build completion is correctly detected.
        
        For any build event, the system should correctly identify whether
        the build has completed (success or failure) or is still in progress.
        """
        # Arrange
        integration = BuildIntegration()
        
        # Act
        is_complete = integration.detect_build_completion(build_event.build_info)
        
        # Assert - verify completion detection logic
        if build_event.build_info.status in [BuildStatus.SUCCESS, BuildStatus.FAILURE]:
            assert is_complete is True
        else:
            assert is_complete is False
    
    @given(build_event=build_event_strategy())
    @settings(max_examples=100, deadline=None)
    def test_should_trigger_tests_logic(self, build_event: BuildEvent):
        """Test that should_trigger_tests correctly identifies triggerable builds.
        
        For any build event, the system should correctly determine whether
        tests should be triggered based on build status and type.
        """
        # Arrange
        integration = BuildIntegration()
        
        # Act
        should_trigger = integration.should_trigger_tests(build_event.build_info)
        
        # Assert - verify trigger logic
        if build_event.build_info.status != BuildStatus.SUCCESS:
            # Non-successful builds should not trigger tests
            assert should_trigger is False
        elif build_event.build_info.build_type in [BuildType.KERNEL, BuildType.BSP, BuildType.FULL_SYSTEM]:
            # Successful kernel/BSP/full builds should trigger tests
            assert should_trigger is True
        elif build_event.build_info.build_type == BuildType.MODULE and build_event.build_info.artifacts:
            # Module builds with artifacts should trigger tests
            assert should_trigger is True
        else:
            # Other cases may or may not trigger
            assert isinstance(should_trigger, bool)
    
    @given(build_events=st.lists(build_event_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_multiple_builds_trigger_handlers(self, build_events: List[BuildEvent]):
        """Test that multiple build events all trigger handlers appropriately.
        
        For any list of build events, each successful build should trigger
        its handler, while failed builds should not.
        """
        # Arrange
        integration = BuildIntegration()
        events_received = []
        
        def test_handler(event: BuildEvent):
            events_received.append(event)
        
        integration.register_build_handler(test_handler)
        
        # Act
        for event in build_events:
            integration.handle_build_event(event)
        
        # Assert - count how many should have triggered
        expected_triggers = sum(
            1 for e in build_events
            if integration.should_trigger_tests(e.build_info)
        )
        
        assert len(events_received) == expected_triggers
    
    @given(build_info=build_info_strategy())
    @settings(max_examples=100, deadline=None)
    def test_kernel_image_extraction(self, build_info: BuildInfo):
        """Test that kernel images are correctly extracted from builds.
        
        For any build info, if it contains a kernel image (directly or in artifacts),
        the system should be able to extract it.
        """
        # Arrange
        integration = BuildIntegration()
        
        # Act
        kernel_image = integration.extract_kernel_image(build_info)
        
        # Assert - verify extraction logic
        if build_info.kernel_image:
            # Direct kernel image should be returned
            assert kernel_image == build_info.kernel_image
        elif any(a.artifact_type == "kernel_image" for a in build_info.artifacts):
            # Kernel image should be constructed from artifact
            assert kernel_image is not None
            assert isinstance(kernel_image, KernelImage)
        else:
            # No kernel image available
            assert kernel_image is None
    
    @given(build_info=build_info_strategy())
    @settings(max_examples=100, deadline=None)
    def test_bsp_package_extraction(self, build_info: BuildInfo):
        """Test that BSP packages are correctly extracted from builds.
        
        For any build info, if it contains a BSP package (directly or in artifacts),
        the system should be able to extract it.
        """
        # Arrange
        integration = BuildIntegration()
        
        # Act
        bsp_package = integration.extract_bsp_package(build_info)
        
        # Assert - verify extraction logic
        if build_info.bsp_package:
            # Direct BSP package should be returned
            assert bsp_package == build_info.bsp_package
        elif any(a.artifact_type == "bsp_package" for a in build_info.artifacts):
            # BSP package should be constructed from artifact
            assert bsp_package is not None
            assert isinstance(bsp_package, BSPPackage)
        else:
            # No BSP package available
            assert bsp_package is None
    
    @given(build_event=build_event_strategy())
    @settings(max_examples=100, deadline=None)
    def test_build_caching(self, build_event: BuildEvent):
        """Test that build information is cached for later retrieval.
        
        For any build event, after handling it, the build info should be
        retrievable from the cache.
        """
        # Arrange
        integration = BuildIntegration()
        
        # Act
        integration.handle_build_event(build_event)
        cached_build = integration.get_build_info(build_event.build_info.build_id)
        
        # Assert - build should be cached
        assert cached_build is not None
        assert cached_build.build_id == build_event.build_info.build_id
        assert cached_build.status == build_event.build_info.status
    
    @given(build_event=build_event_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_multiple_handlers_all_called(self, build_event: BuildEvent):
        """Test that multiple handlers are all called for a build event.
        
        For any build event that should trigger tests, when multiple handlers
        are registered, all handlers should be called.
        """
        # Only test builds that should trigger tests
        assume(build_event.build_info.status == BuildStatus.SUCCESS)
        assume(build_event.build_info.build_type in [BuildType.KERNEL, BuildType.BSP, BuildType.FULL_SYSTEM])
        
        # Arrange
        integration = BuildIntegration()
        handler1_called = []
        handler2_called = []
        handler3_called = []
        
        def handler1(event: BuildEvent):
            handler1_called.append(event)
        
        def handler2(event: BuildEvent):
            handler2_called.append(event)
        
        def handler3(event: BuildEvent):
            handler3_called.append(event)
        
        integration.register_build_handler(handler1)
        integration.register_build_handler(handler2)
        integration.register_build_handler(handler3)
        
        # Act
        integration.handle_build_event(build_event)
        
        # Assert - all handlers should have been called
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1
        assert len(handler3_called) == 1
        assert handler1_called[0] == build_event
        assert handler2_called[0] == build_event
        assert handler3_called[0] == build_event
    
    @given(build_event=build_event_strategy())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_in_progress_builds_do_not_trigger(self, build_event: BuildEvent):
        """Test that in-progress builds do not trigger test handlers.
        
        For any build event with in-progress status, handlers should not be
        called since the build is not yet complete.
        """
        # Only test in-progress builds
        assume(build_event.build_info.status == BuildStatus.IN_PROGRESS)
        
        # Arrange
        integration = BuildIntegration()
        handler_called = []
        
        def test_handler(event: BuildEvent):
            handler_called.append(event)
        
        integration.register_build_handler(test_handler)
        
        # Act
        integration.handle_build_event(build_event)
        
        # Assert - handler should not have been called for in-progress builds
        assert len(handler_called) == 0
