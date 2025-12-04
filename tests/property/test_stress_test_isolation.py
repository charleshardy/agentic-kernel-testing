"""Property-based tests for stress test isolation.

Feature: agentic-kernel-testing, Property 15: Stress test isolation
Validates: Requirements 3.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from pathlib import Path
import tempfile
import os

from ai_generator.models import HardwareConfig, Environment, EnvironmentStatus
from execution.environment_manager import EnvironmentManager


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
class TestStressTestIsolationProperties:
    """Property-based tests for stress test isolation."""
    
    @given(
        config1=hardware_config_strategy(),
        config2=hardware_config_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_environment_isolation_separate_directories(self, config1, config2):
        """
        Property 15: Stress test isolation
        
        For any fault injection test execution, no effects should propagate 
        outside the test environment to other systems or tests.
        
        This property verifies that:
        1. Each environment has its own isolated directory
        2. Environments do not share resources
        3. Changes in one environment do not affect another
        4. Environment directories are completely separate
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision two environments
            env1 = manager.provision_environment(config1)
            env2 = manager.provision_environment(config2)
            
            env1_dir = Path(env1.metadata.get("env_dir"))
            env2_dir = Path(env2.metadata.get("env_dir"))
            
            # Property 1: Environments should have different IDs
            assert env1.id != env2.id, \
                "Environments should have unique IDs"
            
            # Property 2: Environments should have different directories
            assert env1_dir != env2_dir, \
                "Environments should have separate directories"
            
            # Property 3: Directories should not be nested
            assert not str(env1_dir).startswith(str(env2_dir)), \
                "Environment directories should not be nested"
            assert not str(env2_dir).startswith(str(env1_dir)), \
                "Environment directories should not be nested"
            
            # Property 4: Both directories should exist
            assert env1_dir.exists(), "Environment 1 directory should exist"
            assert env2_dir.exists(), "Environment 2 directory should exist"
            
            # Cleanup
            manager.cleanup_environment(env1)
            manager.cleanup_environment(env2)
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_environment_file_isolation(self, config):
        """
        Property: Files created in one environment should not affect others.
        
        When files are created in an environment's directory, they should
        be isolated to that environment only.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision two environments
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            
            env1_dir = Path(env1.metadata.get("env_dir"))
            env2_dir = Path(env2.metadata.get("env_dir"))
            
            # Create a file in env1
            test_file1 = env1_dir / "test_artifact.txt"
            test_file1.write_text("test data from env1")
            
            # Property 1: File should exist in env1
            assert test_file1.exists(), "File should exist in env1"
            
            # Property 2: File should NOT exist in env2
            test_file2 = env2_dir / "test_artifact.txt"
            assert not test_file2.exists(), \
                "File from env1 should not appear in env2"
            
            # Property 3: Env2 directory should not contain env1's file
            env2_files = list(env2_dir.rglob("*"))
            assert test_file1 not in env2_files, \
                "Env1's file should not be in env2's file list"
            
            # Cleanup
            manager.cleanup_environment(env1)
            manager.cleanup_environment(env2)
    
    @given(
        configs=st.lists(hardware_config_strategy(), min_size=2, max_size=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_environment_isolation(self, configs):
        """
        Property: Multiple environments should all be isolated from each other.
        
        When multiple environments are provisioned, each should be completely
        isolated with no shared state.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision all environments
            environments = [manager.provision_environment(config) for config in configs]
            env_dirs = [Path(env.metadata.get("env_dir")) for env in environments]
            
            # Property 1: All environments should have unique IDs
            env_ids = [env.id for env in environments]
            assert len(env_ids) == len(set(env_ids)), \
                "All environment IDs should be unique"
            
            # Property 2: All directories should be unique
            assert len(env_dirs) == len(set(env_dirs)), \
                "All environment directories should be unique"
            
            # Property 3: No directory should be a parent of another
            for i, dir1 in enumerate(env_dirs):
                for j, dir2 in enumerate(env_dirs):
                    if i != j:
                        assert not str(dir2).startswith(str(dir1) + os.sep), \
                            f"Directory {dir2} should not be nested under {dir1}"
            
            # Property 4: Create files in each environment and verify isolation
            for i, (env, env_dir) in enumerate(zip(environments, env_dirs)):
                test_file = env_dir / f"test_{i}.txt"
                test_file.write_text(f"data from env {i}")
                
                # Verify file exists in this environment
                assert test_file.exists(), f"File should exist in env {i}"
                
                # Verify file does NOT exist in other environments
                for j, other_dir in enumerate(env_dirs):
                    if i != j:
                        other_file = other_dir / f"test_{i}.txt"
                        assert not other_file.exists(), \
                            f"File from env {i} should not exist in env {j}"
            
            # Cleanup all
            for env in environments:
                manager.cleanup_environment(env)
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_environment_cleanup_isolation(self, config):
        """
        Property: Cleaning up one environment should not affect others.
        
        When one environment is cleaned up, other environments should
        remain completely unaffected.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision three environments
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            env3 = manager.provision_environment(config)
            
            env1_dir = Path(env1.metadata.get("env_dir"))
            env2_dir = Path(env2.metadata.get("env_dir"))
            env3_dir = Path(env3.metadata.get("env_dir"))
            
            # Create files in all environments
            (env1_dir / "file1.txt").write_text("env1 data")
            (env2_dir / "file2.txt").write_text("env2 data")
            (env3_dir / "file3.txt").write_text("env3 data")
            
            # Cleanup env2
            manager.cleanup_environment(env2)
            
            # Property 1: Env2 should be removed
            assert not env2_dir.exists(), "Env2 directory should be removed"
            assert env2.id not in manager.environments, "Env2 should not be tracked"
            
            # Property 2: Env1 should be unaffected
            assert env1_dir.exists(), "Env1 directory should still exist"
            assert (env1_dir / "file1.txt").exists(), "Env1 file should still exist"
            assert env1.id in manager.environments, "Env1 should still be tracked"
            
            # Property 3: Env3 should be unaffected
            assert env3_dir.exists(), "Env3 directory should still exist"
            assert (env3_dir / "file3.txt").exists(), "Env3 file should still exist"
            assert env3.id in manager.environments, "Env3 should still be tracked"
            
            # Cleanup remaining
            manager.cleanup_environment(env1)
            manager.cleanup_environment(env3)
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_environment_status_isolation(self, config):
        """
        Property: Status changes in one environment should not affect others.
        
        When an environment's status changes, other environments should
        maintain their own independent status.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision two environments
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            
            # Both should start as IDLE
            assert env1.status == EnvironmentStatus.IDLE
            assert env2.status == EnvironmentStatus.IDLE
            
            # Change env1 status to BUSY
            env1.status = EnvironmentStatus.BUSY
            
            # Property 1: Env1 should be BUSY
            assert env1.status == EnvironmentStatus.BUSY
            
            # Property 2: Env2 should still be IDLE (unaffected)
            assert env2.status == EnvironmentStatus.IDLE, \
                "Env2 status should not be affected by env1 status change"
            
            # Change env1 to ERROR
            env1.status = EnvironmentStatus.ERROR
            
            # Property 3: Env2 should still be IDLE
            assert env2.status == EnvironmentStatus.IDLE, \
                "Env2 should remain IDLE even when env1 is in ERROR"
            
            # Cleanup
            manager.cleanup_environment(env1)
            manager.cleanup_environment(env2)
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_environment_metadata_isolation(self, config):
        """
        Property: Metadata in one environment should not affect others.
        
        Each environment should have its own isolated metadata that doesn't
        interfere with other environments.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision two environments
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            
            # Add metadata to env1
            env1.metadata["test_key"] = "test_value_1"
            env1.metadata["custom_data"] = {"nested": "data1"}
            
            # Property 1: Env1 should have the metadata
            assert "test_key" in env1.metadata
            assert env1.metadata["test_key"] == "test_value_1"
            
            # Property 2: Env2 should NOT have env1's metadata
            assert "test_key" not in env2.metadata or env2.metadata.get("test_key") != "test_value_1", \
                "Env2 should not have env1's custom metadata"
            
            # Add different metadata to env2
            env2.metadata["test_key"] = "test_value_2"
            
            # Property 3: Metadata should remain separate
            assert env1.metadata["test_key"] == "test_value_1", \
                "Env1 metadata should not be affected by env2"
            assert env2.metadata["test_key"] == "test_value_2", \
                "Env2 should have its own metadata value"
            
            # Cleanup
            manager.cleanup_environment(env1)
            manager.cleanup_environment(env2)
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_environment_artifact_isolation(self, config):
        """
        Property: Artifacts captured from one environment should not include others.
        
        When capturing artifacts from an environment, only that environment's
        artifacts should be included.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision two environments
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            
            env1_dir = Path(env1.metadata.get("env_dir"))
            env2_dir = Path(env2.metadata.get("env_dir"))
            
            # Create artifacts in env1
            log_dir1 = env1_dir / "logs"
            log_dir1.mkdir(exist_ok=True)
            (log_dir1 / "test1.log").write_text("log from env1")
            
            # Create artifacts in env2
            log_dir2 = env2_dir / "logs"
            log_dir2.mkdir(exist_ok=True)
            (log_dir2 / "test2.log").write_text("log from env2")
            
            # Capture artifacts from env1
            artifacts1 = manager.capture_artifacts(env1)
            
            # Property 1: Artifacts should include env1's log
            assert len(artifacts1.logs) > 0, "Should capture logs from env1"
            assert any("test1.log" in log for log in artifacts1.logs), \
                "Should include env1's log file"
            
            # Property 2: Artifacts should NOT include env2's log
            assert not any("test2.log" in log for log in artifacts1.logs), \
                "Should not include env2's log file"
            
            # Capture artifacts from env2
            artifacts2 = manager.capture_artifacts(env2)
            
            # Property 3: Artifacts should include env2's log
            assert len(artifacts2.logs) > 0, "Should capture logs from env2"
            assert any("test2.log" in log for log in artifacts2.logs), \
                "Should include env2's log file"
            
            # Property 4: Artifacts should NOT include env1's log
            assert not any("test1.log" in log for log in artifacts2.logs), \
                "Should not include env1's log file"
            
            # Cleanup
            manager.cleanup_environment(env1)
            manager.cleanup_environment(env2)
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_environment_health_check_isolation(self, config):
        """
        Property: Health checks should be isolated per environment.
        
        Health status of one environment should not affect health checks
        of other environments.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision two environments
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            
            # Put env1 in error state
            env1.status = EnvironmentStatus.ERROR
            
            # Check health of both
            health1 = manager.check_health(env1)
            health2 = manager.check_health(env2)
            
            # Property 1: Env1 should be unhealthy
            assert not health1.is_healthy, "Env1 should be unhealthy (ERROR state)"
            assert len(health1.issues) > 0, "Env1 should have issues"
            
            # Property 2: Env2 should be healthy (unaffected by env1)
            assert health2.is_healthy, \
                "Env2 should be healthy despite env1 being in ERROR"
            assert len(health2.issues) == 0, \
                "Env2 should have no issues"
            
            # Cleanup
            manager.cleanup_environment(env1)
            manager.cleanup_environment(env2)
    
    @given(
        config=hardware_config_strategy(),
        num_envs=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_concurrent_environment_isolation(self, config, num_envs):
        """
        Property: Multiple concurrent environments should be fully isolated.
        
        When multiple environments exist simultaneously, they should all
        be completely independent with no shared state or resources.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision multiple environments
            environments = [manager.provision_environment(config) for _ in range(num_envs)]
            
            # Property 1: All should have unique IDs
            ids = [env.id for env in environments]
            assert len(ids) == len(set(ids)), "All IDs should be unique"
            
            # Property 2: All should have unique directories
            dirs = [Path(env.metadata.get("env_dir")) for env in environments]
            assert len(dirs) == len(set(dirs)), "All directories should be unique"
            
            # Property 3: All directories should exist
            for env_dir in dirs:
                assert env_dir.exists(), f"Directory should exist: {env_dir}"
            
            # Property 4: Modify each environment independently
            for i, env in enumerate(environments):
                env.metadata[f"test_{i}"] = f"value_{i}"
            
            # Verify isolation of modifications
            for i, env in enumerate(environments):
                # Should have its own metadata
                assert env.metadata.get(f"test_{i}") == f"value_{i}"
                
                # Should NOT have other environments' metadata
                for j in range(num_envs):
                    if i != j:
                        assert f"test_{j}" not in env.metadata or \
                               env.metadata.get(f"test_{j}") != f"value_{j}", \
                            f"Env {i} should not have env {j}'s metadata"
            
            # Cleanup all
            for env in environments:
                manager.cleanup_environment(env)
    
    @given(config=hardware_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_environment_work_directory_isolation(self, config):
        """
        Property: Each environment should have its own subdirectory in work_dir.
        
        Environments should not share directories or create files outside
        their designated subdirectory.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            # Provision environment
            env = manager.provision_environment(config)
            env_dir = Path(env.metadata.get("env_dir"))
            
            # Property 1: Environment directory should be under work_dir
            assert str(env_dir).startswith(str(work_dir)), \
                f"Environment directory should be under work_dir: {env_dir} not under {work_dir}"
            
            # Property 2: Environment directory should be a direct child of work_dir
            assert env_dir.parent == work_dir, \
                f"Environment directory should be direct child of work_dir"
            
            # Property 3: Environment should not create files in work_dir root
            work_dir_files = [f for f in work_dir.iterdir() if f.is_file()]
            assert len(work_dir_files) == 0, \
                "Environment should not create files in work_dir root"
            
            # Cleanup
            manager.cleanup_environment(env)
