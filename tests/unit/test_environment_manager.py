"""Unit tests for environment manager."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from ai_generator.models import HardwareConfig, EnvironmentStatus
from execution.environment_manager import EnvironmentManager, KernelImage, EnvironmentHealth


class TestEnvironmentManager:
    """Unit tests for EnvironmentManager class."""
    
    def test_initialization(self):
        """Test EnvironmentManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            assert manager.work_dir == work_dir
            assert work_dir.exists()
            assert len(manager.environments) == 0
    
    def test_provision_qemu_environment(self):
        """Test provisioning a QEMU environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            
            assert env.id is not None
            assert env.status == EnvironmentStatus.IDLE
            assert env.config == config
            assert env.id in manager.environments
            
            env_dir = Path(env.metadata.get("env_dir"))
            assert env_dir.exists()
            assert env_dir.parent == work_dir
    
    def test_provision_kvm_environment(self):
        """Test provisioning a KVM environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='kvm'
            )
            
            env = manager.provision_environment(config)
            
            assert env.id is not None
            assert env.status == EnvironmentStatus.IDLE
            assert env.metadata.get("emulator") == "kvm"
    
    def test_provision_physical_environment_raises_error(self):
        """Test that provisioning physical environment raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=False,
                emulator=None
            )
            
            with pytest.raises(ValueError, match="only handles virtual environments"):
                manager.provision_environment(config)
    
    def test_provision_unsupported_emulator_raises_error(self):
        """Test that unsupported emulator raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='unsupported'
            )
            
            with pytest.raises(RuntimeError, match="Unsupported emulator"):
                manager.provision_environment(config)
    
    def test_deploy_kernel(self):
        """Test deploying kernel to environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            
            # Create a fake kernel image
            kernel_path = Path(temp_dir) / "kernel.img"
            kernel_path.write_text("fake kernel")
            
            kernel = KernelImage(
                path=str(kernel_path),
                version="5.15.0",
                architecture='x86_64'
            )
            
            manager.deploy_kernel(env, kernel)
            
            assert env.kernel_version == "5.15.0"
            assert "kernel_path" in env.metadata
    
    def test_deploy_kernel_architecture_mismatch(self):
        """Test that deploying kernel with wrong architecture raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            
            kernel_path = Path(temp_dir) / "kernel.img"
            kernel_path.write_text("fake kernel")
            
            kernel = KernelImage(
                path=str(kernel_path),
                version="5.15.0",
                architecture='arm64'  # Wrong architecture
            )
            
            with pytest.raises(ValueError, match="does not match"):
                manager.deploy_kernel(env, kernel)
    
    def test_deploy_kernel_nonexistent_file(self):
        """Test that deploying nonexistent kernel raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            
            kernel = KernelImage(
                path="/nonexistent/kernel.img",
                version="5.15.0",
                architecture='x86_64'
            )
            
            with pytest.raises(ValueError, match="not found"):
                manager.deploy_kernel(env, kernel)
    
    def test_cleanup_environment(self):
        """Test cleaning up environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            env_id = env.id
            env_dir = Path(env.metadata.get("env_dir"))
            
            assert env_dir.exists()
            assert env_id in manager.environments
            
            manager.cleanup_environment(env)
            
            assert not env_dir.exists()
            assert env_id not in manager.environments
    
    def test_capture_artifacts(self):
        """Test capturing artifacts from environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            env_dir = Path(env.metadata.get("env_dir"))
            
            # Create artifacts
            log_dir = env_dir / "logs"
            log_dir.mkdir()
            (log_dir / "test.log").write_text("log content")
            
            core_dir = env_dir / "cores"
            core_dir.mkdir()
            (core_dir / "core.123").write_text("core dump")
            
            trace_dir = env_dir / "traces"
            trace_dir.mkdir()
            (trace_dir / "trace.trace").write_text("trace data")
            
            artifacts = manager.capture_artifacts(env)
            
            assert len(artifacts.logs) == 1
            assert len(artifacts.core_dumps) == 1
            assert len(artifacts.traces) == 1
            assert artifacts.metadata["environment_id"] == env.id
    
    def test_capture_artifacts_empty(self):
        """Test capturing artifacts when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            
            artifacts = manager.capture_artifacts(env)
            
            assert len(artifacts.logs) == 0
            assert len(artifacts.core_dumps) == 0
            assert len(artifacts.traces) == 0
    
    def test_check_health(self):
        """Test checking environment health."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            
            health = manager.check_health(env)
            
            assert isinstance(health, EnvironmentHealth)
            assert health.is_healthy
            assert len(health.issues) == 0
            assert health.uptime_seconds >= 0
    
    def test_check_health_error_state(self):
        """Test health check for environment in error state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            env.status = EnvironmentStatus.ERROR
            
            health = manager.check_health(env)
            
            assert not health.is_healthy
            assert len(health.issues) > 0
            assert any("error state" in issue.lower() for issue in health.issues)
    
    def test_get_environment(self):
        """Test getting environment by ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env = manager.provision_environment(config)
            
            retrieved = manager.get_environment(env.id)
            
            assert retrieved is not None
            assert retrieved.id == env.id
    
    def test_get_environment_nonexistent(self):
        """Test getting nonexistent environment returns None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            retrieved = manager.get_environment("nonexistent-id")
            
            assert retrieved is None
    
    def test_list_environments(self):
        """Test listing all environments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            
            envs = manager.list_environments()
            
            assert len(envs) == 2
            assert env1 in envs
            assert env2 in envs
    
    def test_list_environments_by_status(self):
        """Test listing environments filtered by status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            env2.status = EnvironmentStatus.BUSY
            
            idle_envs = manager.list_environments(EnvironmentStatus.IDLE)
            busy_envs = manager.list_environments(EnvironmentStatus.BUSY)
            
            assert len(idle_envs) == 1
            assert env1 in idle_envs
            assert len(busy_envs) == 1
            assert env2 in busy_envs
    
    def test_get_idle_environments(self):
        """Test getting idle environments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            env1 = manager.provision_environment(config)
            env2 = manager.provision_environment(config)
            env2.status = EnvironmentStatus.BUSY
            
            idle_envs = manager.get_idle_environments()
            
            assert len(idle_envs) == 1
            assert env1 in idle_envs
            assert env2 not in idle_envs
    
    def test_cleanup_idle_environments(self):
        """Test cleaning up old idle environments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            # Create old idle environment
            old_env = manager.provision_environment(config)
            old_env.last_used = datetime.now() - timedelta(seconds=7200)
            
            # Create recent idle environment
            recent_env = manager.provision_environment(config)
            
            # Create busy environment (should not be cleaned)
            busy_env = manager.provision_environment(config)
            busy_env.status = EnvironmentStatus.BUSY
            busy_env.last_used = datetime.now() - timedelta(seconds=7200)
            
            # Cleanup environments older than 1 hour
            cleaned = manager.cleanup_idle_environments(max_age_seconds=3600)
            
            assert cleaned == 1
            assert old_env.id not in manager.environments
            assert recent_env.id in manager.environments
            assert busy_env.id in manager.environments
    
    def test_multiple_environments_unique_ids(self):
        """Test that multiple environments get unique IDs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            envs = [manager.provision_environment(config) for _ in range(5)]
            ids = [env.id for env in envs]
            
            assert len(ids) == len(set(ids))  # All IDs are unique
    
    def test_environment_timestamps(self):
        """Test that environment timestamps are set correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            manager = EnvironmentManager(work_dir=work_dir)
            
            config = HardwareConfig(
                architecture='x86_64',
                cpu_model='Intel Core i7',
                memory_mb=2048,
                is_virtual=True,
                emulator='qemu'
            )
            
            before = datetime.now()
            env = manager.provision_environment(config)
            after = datetime.now()
            
            assert before <= env.created_at <= after
            assert before <= env.last_used <= after
