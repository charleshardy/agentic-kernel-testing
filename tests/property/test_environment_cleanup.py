"""Property-based tests for environment cleanup completeness.

Feature: agentic-kernel-testing, Property 49: Environment cleanup completeness
Validates: Requirements 10.4
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import shutil

from ai_generator.models import HardwareConfig, Environment, EnvironmentStatus
from execution.environment_manager import EnvironmentManager, KernelImage


# Strategies for generating test data
@st.composite
def hardware_config_strategy(draw):
    """Generate a valid virtual HardwareConfig object."""
    architectures = ['x86_64', 'arm64', 'riscv64', 'arm']
    
    architecture = draw(st.sampled_from(architectures))
    memory_mb = draw(st.integers(min_value=512, max_value=8192))
    emulator = draw(st.sampled_from(['qemu', 'kvm']))
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=f'CPU-{architecture}',
        memory_mb=memory_mb,
        storage_type='ssd',
        peripherals=[],
        is_virtual=True,
        emulator=emulator
    )


@pytest.mark.property
class TestEnvironmentCleanupProperties:
    """Property-based tests for environment cleanup completeness."""
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cleanup_removes_all_environment_resources(self, config):
        """
        Property 49: Environment cleanup completeness
        
        For any completed test (passed or failed), the test environment should be 
        cleaned up and prepared for subsequent test runs.
        
        This property verifies that:
        1. Environment directory is removed after cleanup
        2. Environment is removed from manager's tracking
        3. Environment status is updated appropriately
        4. All files associated with the environment are deleted
        """
        # Create temporary work directory
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision environment
            environment = manager.provision_environment(config)
            env_id = environment.id
            env_dir = Path(environment.metadata.get("env_dir"))
            
            # Verify environment was created
            assert env_dir.exists(), "Environment directory should exist after provisioning"
            assert env_id in manager.environments, "Environment should be tracked"
            
            # Cleanup environment
            manager.cleanup_environment(environment)
            
            # Property 1: Environment directory should be removed
            assert not env_dir.exists(), \
                f"Environment directory should be removed after cleanup: {env_dir}"
            
            # Property 2: Environment should be removed from tracking
            assert env_id not in manager.environments, \
                "Environment should be removed from manager's tracking"
            
            # Property 3: Environment status should be IDLE (cleaned up)
            assert environment.status == EnvironmentStatus.IDLE, \
                f"Environment status should be IDLE after cleanup, got {environment.status}"
    
    @given(
        configs=st.lists(hardware_config_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_cleanup_multiple_environments(self, configs):
        """
        Property: Cleanup should work correctly for multiple environments.
        
        When multiple environments are provisioned and cleaned up,
        each should be properly removed without affecting others.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision all environments
            environments = []
            env_dirs = []
            for config in configs:
                env = manager.provision_environment(config)
                environments.append(env)
                env_dirs.append(Path(env.metadata.get("env_dir")))
            
            # Verify all were created
            assert len(manager.environments) == len(configs), \
                "All environments should be tracked"
            
            for env_dir in env_dirs:
                assert env_dir.exists(), "All environment directories should exist"
            
            # Cleanup all environments
            for env in environments:
                manager.cleanup_environment(env)
            
            # Property 1: All environments should be removed from tracking
            assert len(manager.environments) == 0, \
                "All environments should be removed from tracking"
            
            # Property 2: All environment directories should be removed
            for env_dir in env_dirs:
                assert not env_dir.exists(), \
                    f"Environment directory should be removed: {env_dir}"
            
            # Property 3: All environment statuses should be IDLE
            for env in environments:
                assert env.status == EnvironmentStatus.IDLE, \
                    "All environments should have IDLE status after cleanup"
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cleanup_with_artifacts(self, config):
        """
        Property: Cleanup should remove environment even with artifacts present.
        
        When an environment has logs, core dumps, or traces, cleanup should
        still remove everything.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision environment
            environment = manager.provision_environment(config)
            env_dir = Path(environment.metadata.get("env_dir"))
            
            # Create artifact directories and files
            log_dir = env_dir / "logs"
            log_dir.mkdir(exist_ok=True)
            (log_dir / "test.log").write_text("test log content")
            
            core_dir = env_dir / "cores"
            core_dir.mkdir(exist_ok=True)
            (core_dir / "core.123").write_text("core dump")
            
            trace_dir = env_dir / "traces"
            trace_dir.mkdir(exist_ok=True)
            (trace_dir / "trace.txt").write_text("trace data")
            
            # Verify artifacts exist
            assert (log_dir / "test.log").exists(), "Log file should exist"
            assert (core_dir / "core.123").exists(), "Core dump should exist"
            assert (trace_dir / "trace.txt").exists(), "Trace file should exist"
            
            # Cleanup environment
            manager.cleanup_environment(environment)
            
            # Property: Everything should be removed, including artifacts
            assert not env_dir.exists(), \
                "Environment directory with artifacts should be completely removed"
            assert not (log_dir / "test.log").exists(), "Log file should be removed"
            assert not (core_dir / "core.123").exists(), "Core dump should be removed"
            assert not (trace_dir / "trace.txt").exists(), "Trace file should be removed"
    
    @given(
        config=hardware_config_strategy(),
        max_age=st.integers(min_value=1, max_value=7200)
    )
    @settings(max_examples=100, deadline=None)
    def test_idle_environment_cleanup(self, config, max_age):
        """
        Property: Idle environments older than max_age should be cleaned up.
        
        When cleanup_idle_environments is called, environments that have been
        idle longer than max_age should be removed.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision environment
            environment = manager.provision_environment(config)
            env_id = environment.id
            env_dir = Path(environment.metadata.get("env_dir"))
            
            # Make environment idle
            environment.status = EnvironmentStatus.IDLE
            
            # Simulate old environment by setting last_used to past
            from datetime import datetime, timedelta
            environment.last_used = datetime.now() - timedelta(seconds=max_age + 1)
            
            # Cleanup idle environments
            cleaned = manager.cleanup_idle_environments(max_age_seconds=max_age)
            
            # Property 1: At least one environment should be cleaned
            assert cleaned >= 1, \
                f"Should have cleaned at least 1 idle environment, cleaned {cleaned}"
            
            # Property 2: Environment should be removed
            assert env_id not in manager.environments, \
                "Old idle environment should be removed from tracking"
            
            # Property 3: Environment directory should be removed
            assert not env_dir.exists(), \
                "Old idle environment directory should be removed"
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cleanup_idempotency(self, config):
        """
        Property: Cleanup should be idempotent - calling it multiple times is safe.
        
        Cleaning up an already cleaned environment should not cause errors.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision environment
            environment = manager.provision_environment(config)
            env_id = environment.id
            
            # Cleanup once
            manager.cleanup_environment(environment)
            
            # Verify cleanup worked
            assert env_id not in manager.environments
            
            # Property: Cleanup again should not raise an error
            try:
                manager.cleanup_environment(environment)
                # Should complete without error
            except Exception as e:
                pytest.fail(f"Second cleanup should not raise error: {e}")
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cleanup_prepares_for_reuse(self, config):
        """
        Property: After cleanup, manager should be ready to provision new environments.
        
        Cleanup should not leave the manager in a state that prevents
        provisioning new environments.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision and cleanup first environment
            env1 = manager.provision_environment(config)
            manager.cleanup_environment(env1)
            
            # Property: Should be able to provision a new environment
            try:
                env2 = manager.provision_environment(config)
                assert env2.id != env1.id, "New environment should have different ID"
                assert env2.status in [EnvironmentStatus.IDLE, EnvironmentStatus.PROVISIONING], \
                    "New environment should be in valid state"
                
                # Cleanup second environment
                manager.cleanup_environment(env2)
            except Exception as e:
                pytest.fail(f"Should be able to provision after cleanup: {e}")
    
    @given(
        configs=st.lists(hardware_config_strategy(), min_size=2, max_size=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_selective_cleanup(self, configs):
        """
        Property: Cleanup of one environment should not affect others.
        
        When cleaning up a specific environment, other environments
        should remain intact.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision multiple environments
            environments = [manager.provision_environment(config) for config in configs]
            
            # Pick one to cleanup (not the last one)
            target_env = environments[0]
            other_envs = environments[1:]
            
            # Cleanup target environment
            manager.cleanup_environment(target_env)
            
            # Property 1: Target should be removed
            assert target_env.id not in manager.environments, \
                "Target environment should be removed"
            
            # Property 2: Other environments should still exist
            for env in other_envs:
                assert env.id in manager.environments, \
                    f"Other environment {env.id} should still be tracked"
                
                env_dir = Path(env.metadata.get("env_dir"))
                assert env_dir.exists(), \
                    f"Other environment directory should still exist: {env_dir}"
            
            # Cleanup remaining environments
            for env in other_envs:
                manager.cleanup_environment(env)
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cleanup_from_error_state(self, config):
        """
        Property: Cleanup should work even when environment is in ERROR state.
        
        Environments that failed to provision or encountered errors should
        still be cleanable.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision environment
            environment = manager.provision_environment(config)
            env_id = environment.id
            env_dir = Path(environment.metadata.get("env_dir"))
            
            # Simulate error state
            environment.status = EnvironmentStatus.ERROR
            
            # Property: Cleanup should still work
            try:
                manager.cleanup_environment(environment)
                
                assert env_id not in manager.environments, \
                    "Environment in ERROR state should be cleanable"
                assert not env_dir.exists(), \
                    "Environment directory should be removed even from ERROR state"
            except Exception as e:
                pytest.fail(f"Cleanup should work from ERROR state: {e}")
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_cleanup_completeness_verification(self, config):
        """
        Property: After cleanup, no traces of the environment should remain.
        
        This is a comprehensive check that cleanup is truly complete.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision environment
            environment = manager.provision_environment(config)
            env_id = environment.id
            env_dir = Path(environment.metadata.get("env_dir"))
            
            # Record what was created
            disk_path = env_dir / "disk.qcow2"
            
            # Cleanup
            manager.cleanup_environment(environment)
            
            # Property 1: No environment directory
            assert not env_dir.exists(), "Environment directory should not exist"
            
            # Property 2: No disk image
            assert not disk_path.exists(), "Disk image should not exist"
            
            # Property 3: Not in manager's tracking
            assert env_id not in manager.environments, \
                "Environment should not be in manager's tracking"
            
            # Property 4: Work directory should be empty or only contain other envs
            remaining_items = list(work_dir.iterdir())
            assert env_dir not in remaining_items, \
                "Environment directory should not be in work directory"
