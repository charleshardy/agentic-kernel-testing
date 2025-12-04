"""Environment manager for virtual test environments.

This module provides functionality for:
- QEMU environment provisioning
- KVM environment setup
- Environment lifecycle management (provision, deploy, cleanup)
- Artifact capture (logs, core dumps, traces)
- Environment health monitoring
"""

import subprocess
import time
import uuid
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from ai_generator.models import (
    Environment, EnvironmentStatus, HardwareConfig, 
    ArtifactBundle, Credentials
)


@dataclass
class KernelImage:
    """Kernel image to deploy to environment."""
    path: str
    version: str
    architecture: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EnvironmentHealth:
    """Health status of an environment."""
    is_healthy: bool
    uptime_seconds: float
    last_check: datetime
    issues: List[str]
    metrics: Dict[str, Any]


class EnvironmentManager:
    """Manager for virtual test execution environments."""
    
    def __init__(self, work_dir: Optional[Path] = None):
        """Initialize environment manager.
        
        Args:
            work_dir: Working directory for environment files
        """
        self.work_dir = work_dir or Path("/tmp/test_environments")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.environments: Dict[str, Environment] = {}
    
    def provision_environment(self, config: HardwareConfig) -> Environment:
        """Provision a new test environment.
        
        Args:
            config: Hardware configuration for the environment
            
        Returns:
            Provisioned Environment instance
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If provisioning fails
        """
        if not config.is_virtual:
            raise ValueError("EnvironmentManager only handles virtual environments")
        
        env_id = str(uuid.uuid4())
        env_dir = self.work_dir / env_id
        env_dir.mkdir(parents=True, exist_ok=True)
        
        # Create environment with provisioning status
        environment = Environment(
            id=env_id,
            config=config,
            status=EnvironmentStatus.PROVISIONING,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        self.environments[env_id] = environment
        
        try:
            if config.emulator == "qemu":
                self._provision_qemu(environment, env_dir)
            elif config.emulator == "kvm":
                self._provision_kvm(environment, env_dir)
            else:
                raise ValueError(f"Unsupported emulator: {config.emulator}")
            
            environment.status = EnvironmentStatus.IDLE
            return environment
            
        except Exception as e:
            environment.status = EnvironmentStatus.ERROR
            raise RuntimeError(f"Failed to provision environment: {e}") from e
    
    def _provision_qemu(self, environment: Environment, env_dir: Path) -> None:
        """Provision QEMU virtual environment.
        
        Args:
            environment: Environment being provisioned
            env_dir: Directory for environment files
        """
        config = environment.config
        
        # Create disk image
        disk_path = env_dir / "disk.qcow2"
        disk_size = f"{config.memory_mb * 4}M"  # 4x memory for disk
        
        # Check if qemu-img is available
        qemu_img_available = shutil.which("qemu-img") is not None
        
        if qemu_img_available:
            # Create qcow2 disk image
            subprocess.run(
                ["qemu-img", "create", "-f", "qcow2", str(disk_path), disk_size],
                check=True,
                capture_output=True
            )
        else:
            # For testing without qemu-img, create a placeholder file
            disk_path.write_text(f"placeholder disk image: {disk_size}")
        
        # Store environment metadata
        environment.metadata = {
            "env_dir": str(env_dir),
            "disk_path": str(disk_path),
            "emulator": "qemu"
        }
    
    def _provision_kvm(self, environment: Environment, env_dir: Path) -> None:
        """Provision KVM virtual environment.
        
        Args:
            environment: Environment being provisioned
            env_dir: Directory for environment files
        """
        config = environment.config
        
        # Create disk image (same as QEMU)
        disk_path = env_dir / "disk.qcow2"
        disk_size = f"{config.memory_mb * 4}M"
        
        # Check if qemu-img is available
        qemu_img_available = shutil.which("qemu-img") is not None
        
        if qemu_img_available:
            subprocess.run(
                ["qemu-img", "create", "-f", "qcow2", str(disk_path), disk_size],
                check=True,
                capture_output=True
            )
        else:
            # For testing without qemu-img, create a placeholder file
            disk_path.write_text(f"placeholder disk image: {disk_size}")
        
        # Store environment metadata
        environment.metadata = {
            "env_dir": str(env_dir),
            "disk_path": str(disk_path),
            "emulator": "kvm",
            "kvm_enabled": Path("/dev/kvm").exists()
        }
    
    def deploy_kernel(self, environment: Environment, kernel: KernelImage) -> None:
        """Deploy kernel image to environment.
        
        Args:
            environment: Target environment
            kernel: Kernel image to deploy
            
        Raises:
            ValueError: If environment or kernel is invalid
            RuntimeError: If deployment fails
        """
        if environment.status not in [EnvironmentStatus.IDLE, EnvironmentStatus.BUSY]:
            raise ValueError(f"Cannot deploy to environment in {environment.status} status")
        
        if kernel.architecture != environment.config.architecture:
            raise ValueError(
                f"Kernel architecture {kernel.architecture} does not match "
                f"environment architecture {environment.config.architecture}"
            )
        
        # Verify kernel image exists
        kernel_path = Path(kernel.path)
        if not kernel_path.exists():
            raise ValueError(f"Kernel image not found: {kernel.path}")
        
        # Copy kernel to environment directory
        env_dir = Path(environment.metadata.get("env_dir", self.work_dir / environment.id))
        kernel_dest = env_dir / "kernel"
        shutil.copy2(kernel_path, kernel_dest)
        
        # Update environment
        environment.kernel_version = kernel.version
        environment.last_used = datetime.now()
        environment.metadata["kernel_path"] = str(kernel_dest)
    
    def cleanup_environment(self, environment: Environment) -> None:
        """Clean up and remove environment.
        
        Args:
            environment: Environment to clean up
        """
        env_id = environment.id
        
        # Stop any running processes
        if environment.status == EnvironmentStatus.BUSY:
            self._stop_environment(environment)
        
        # Remove environment directory
        env_dir = Path(environment.metadata.get("env_dir", self.work_dir / env_id))
        if env_dir.exists():
            shutil.rmtree(env_dir)
        
        # Remove from tracking
        if env_id in self.environments:
            del self.environments[env_id]
        
        environment.status = EnvironmentStatus.IDLE
    
    def _stop_environment(self, environment: Environment) -> None:
        """Stop a running environment.
        
        Args:
            environment: Environment to stop
        """
        # In a real implementation, this would kill the QEMU/KVM process
        # For now, just update status
        environment.status = EnvironmentStatus.IDLE
    
    def capture_artifacts(self, environment: Environment) -> ArtifactBundle:
        """Capture execution artifacts from environment.
        
        Args:
            environment: Environment to capture artifacts from
            
        Returns:
            Bundle of captured artifacts
        """
        env_dir = Path(environment.metadata.get("env_dir", self.work_dir / environment.id))
        
        artifacts = ArtifactBundle()
        
        # Capture logs
        log_dir = env_dir / "logs"
        if log_dir.exists():
            artifacts.logs = [str(f) for f in log_dir.glob("*.log")]
        
        # Capture core dumps
        core_dir = env_dir / "cores"
        if core_dir.exists():
            artifacts.core_dumps = [str(f) for f in core_dir.glob("core.*")]
        
        # Capture traces
        trace_dir = env_dir / "traces"
        if trace_dir.exists():
            artifacts.traces = [str(f) for f in trace_dir.glob("*.trace")]
        
        # Add metadata
        artifacts.metadata = {
            "environment_id": environment.id,
            "captured_at": datetime.now().isoformat(),
            "kernel_version": environment.kernel_version
        }
        
        return artifacts
    
    def check_health(self, environment: Environment) -> EnvironmentHealth:
        """Check health status of environment.
        
        Args:
            environment: Environment to check
            
        Returns:
            Health status information
        """
        issues = []
        metrics = {}
        
        # Check if environment directory exists
        env_dir = Path(environment.metadata.get("env_dir", self.work_dir / environment.id))
        if not env_dir.exists():
            issues.append("Environment directory does not exist")
        
        # Check disk space
        if env_dir.exists():
            stat = shutil.disk_usage(env_dir)
            free_gb = stat.free / (1024**3)
            metrics["disk_free_gb"] = free_gb
            if free_gb < 1.0:
                issues.append(f"Low disk space: {free_gb:.2f}GB free")
        
        # Calculate uptime
        uptime = (datetime.now() - environment.created_at).total_seconds()
        metrics["uptime_seconds"] = uptime
        
        # Check status
        if environment.status == EnvironmentStatus.ERROR:
            issues.append("Environment is in error state")
        
        is_healthy = len(issues) == 0
        
        return EnvironmentHealth(
            is_healthy=is_healthy,
            uptime_seconds=uptime,
            last_check=datetime.now(),
            issues=issues,
            metrics=metrics
        )
    
    def get_environment(self, env_id: str) -> Optional[Environment]:
        """Get environment by ID.
        
        Args:
            env_id: Environment ID
            
        Returns:
            Environment if found, None otherwise
        """
        return self.environments.get(env_id)
    
    def list_environments(self, status: Optional[EnvironmentStatus] = None) -> List[Environment]:
        """List all environments, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of environments
        """
        envs = list(self.environments.values())
        if status:
            envs = [e for e in envs if e.status == status]
        return envs
    
    def get_idle_environments(self) -> List[Environment]:
        """Get all idle environments.
        
        Returns:
            List of idle environments
        """
        return self.list_environments(EnvironmentStatus.IDLE)
    
    def cleanup_idle_environments(self, max_age_seconds: int = 3600) -> int:
        """Clean up idle environments older than specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds before cleanup
            
        Returns:
            Number of environments cleaned up
        """
        now = datetime.now()
        cleaned = 0
        
        for env in list(self.environments.values()):
            if env.status == EnvironmentStatus.IDLE:
                age = (now - env.last_used).total_seconds()
                if age > max_age_seconds:
                    self.cleanup_environment(env)
                    cleaned += 1
        
        return cleaned
