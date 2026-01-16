"""
SSH Build Executor Service

Executes kernel/BSP builds on remote build servers via SSH.
"""

import asyncio
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, AsyncIterator
import paramiko

from infrastructure.models.build_server import BuildServer, BuildConfig, BuildJob


class SSHBuildExecutor:
    """
    Executes builds on remote servers via SSH.
    
    Handles:
    - SSH connection management
    - Repository cloning
    - Build execution
    - Log streaming
    - Artifact collection
    """
    
    def __init__(self, server: BuildServer):
        self.server = server
        self.ssh_client: Optional[paramiko.SSHClient] = None
        
    async def connect(self) -> bool:
        """
        Establish SSH connection to the build server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.server.hostname or self.server.ip_address,
                'username': self.server.ssh_username,
                'port': self.server.ssh_port,
                'timeout': 30,
            }
            
            if self.server.ssh_key_path and os.path.exists(self.server.ssh_key_path):
                connect_kwargs['key_filename'] = self.server.ssh_key_path
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.ssh_client.connect(**connect_kwargs))
            
            return True
            
        except Exception as e:
            print(f"SSH connection failed to {self.server.hostname}: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
    
    async def execute_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict] = None
    ) -> Tuple[int, str, str]:
        """
        Execute a command on the remote server.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.ssh_client:
            raise RuntimeError("Not connected to SSH server")
        
        # Build full command with cd and env
        full_command = ""
        if cwd:
            full_command += f"cd {cwd} && "
        if env:
            env_str = " ".join([f"{k}={v}" for k, v in env.items()])
            full_command += f"{env_str} "
        full_command += command
        
        # Execute command
        loop = asyncio.get_event_loop()
        stdin, stdout, stderr = await loop.run_in_executor(
            None,
            lambda: self.ssh_client.exec_command(full_command, timeout=3600)
        )
        
        # Read output
        stdout_data = await loop.run_in_executor(None, stdout.read)
        stderr_data = await loop.run_in_executor(None, stderr.read)
        exit_code = stdout.channel.recv_exit_status()
        
        return exit_code, stdout_data.decode('utf-8', errors='replace'), stderr_data.decode('utf-8', errors='replace')
    
    async def execute_command_streaming(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict] = None
    ) -> AsyncIterator[Tuple[str, str]]:
        """
        Execute a command and stream output in real-time.
        
        Args:
            command: Command to execute
            cwd: Working directory
            env: Environment variables
            
        Yields:
            Tuples of (stream_type, data) where stream_type is 'stdout' or 'stderr'
        """
        if not self.ssh_client:
            raise RuntimeError("Not connected to SSH server")
        
        # Build full command
        full_command = ""
        if cwd:
            full_command += f"cd {cwd} && "
        if env:
            env_str = " ".join([f"{k}={v}" for k, v in env.items()])
            full_command += f"{env_str} "
        full_command += command
        
        # Execute command
        loop = asyncio.get_event_loop()
        stdin, stdout, stderr = await loop.run_in_executor(
            None,
            lambda: self.ssh_client.exec_command(full_command, timeout=7200)
        )
        
        # Stream output
        while True:
            # Check stdout
            if stdout.channel.recv_ready():
                data = await loop.run_in_executor(None, lambda: stdout.channel.recv(4096))
                if data:
                    yield ('stdout', data.decode('utf-8', errors='replace'))
            
            # Check stderr
            if stdout.channel.recv_stderr_ready():
                data = await loop.run_in_executor(None, lambda: stdout.channel.recv_stderr(4096))
                if data:
                    yield ('stderr', data.decode('utf-8', errors='replace'))
            
            # Check if command finished
            if stdout.channel.exit_status_ready():
                # Read any remaining output
                while stdout.channel.recv_ready():
                    data = await loop.run_in_executor(None, lambda: stdout.channel.recv(4096))
                    if data:
                        yield ('stdout', data.decode('utf-8', errors='replace'))
                while stdout.channel.recv_stderr_ready():
                    data = await loop.run_in_executor(None, lambda: stdout.channel.recv_stderr(4096))
                    if data:
                        yield ('stderr', data.decode('utf-8', errors='replace'))
                break
            
            await asyncio.sleep(0.1)
    
    async def setup_workspace(self, job: BuildJob, config: BuildConfig) -> str:
        """
        Set up build workspace on the remote server.
        
        Args:
            job: Build job
            config: Build configuration
            
        Returns:
            Path to the workspace directory
        """
        workspace_path = f"{config.workspace_root}/job-{job.id}"
        
        # Create workspace directory
        exit_code, stdout, stderr = await self.execute_command(
            f"mkdir -p {workspace_path}"
        )
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to create workspace: {stderr}")
        
        return workspace_path
    
    async def clone_repository(
        self,
        job: BuildJob,
        config: BuildConfig,
        workspace_path: str
    ) -> str:
        """
        Clone the source repository.
        
        Args:
            job: Build job
            config: Build configuration
            workspace_path: Workspace directory path
            
        Returns:
            Path to the cloned repository
        """
        source_path = f"{workspace_path}/source"
        
        # Build git clone command
        clone_cmd = f"git clone --depth {config.git_depth}"
        if config.git_submodules:
            clone_cmd += " --recurse-submodules"
        clone_cmd += f" --branch {job.branch} {job.source_repository} {source_path}"
        
        # Clone repository
        exit_code, stdout, stderr = await self.execute_command(clone_cmd)
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to clone repository: {stderr}")
        
        # Checkout specific commit if specified
        if job.commit_hash and job.commit_hash != "HEAD":
            exit_code, stdout, stderr = await self.execute_command(
                f"git checkout {job.commit_hash}",
                cwd=source_path
            )
            
            if exit_code != 0:
                raise RuntimeError(f"Failed to checkout commit: {stderr}")
        
        return source_path
    
    async def configure_build(
        self,
        job: BuildJob,
        config: BuildConfig,
        source_path: str,
        build_path: str
    ) -> AsyncIterator[str]:
        """
        Configure the kernel build.
        
        Args:
            job: Build job
            config: Build configuration
            source_path: Source directory path
            build_path: Build output directory path
            
        Yields:
            Log lines
        """
        # Create build directory
        exit_code, stdout, stderr = await self.execute_command(
            f"mkdir -p {build_path}"
        )
        
        if exit_code != 0:
            raise RuntimeError(f"Failed to create build directory: {stderr}")
        
        # Determine kernel config
        kernel_config = config.kernel_config or "defconfig"
        
        # Run make config
        make_cmd = f"make -C {source_path} O={build_path} ARCH={job.target_architecture} {kernel_config}"
        
        yield f"Configuring kernel: {make_cmd}\n"
        
        async for stream_type, data in self.execute_command_streaming(make_cmd, env=config.custom_env):
            yield data
    
    async def execute_custom_commands(
        self,
        commands: List[str],
        source_path: str,
        env: Optional[dict] = None,
        command_type: str = "custom"
    ) -> AsyncIterator[str]:
        """
        Execute custom build commands.
        
        Args:
            commands: List of commands to execute
            source_path: Source directory path
            env: Environment variables
            command_type: Type of commands (for logging)
            
        Yields:
            Log lines
        """
        if not commands:
            yield f"No {command_type} commands to execute\n"
            return
        
        yield f"\n[{datetime.now().isoformat()}] Executing {command_type} commands...\n"
        
        for i, command in enumerate(commands, 1):
            yield f"\n[{datetime.now().isoformat()}] Command {i}/{len(commands)}: {command}\n"
            
            async for stream_type, data in self.execute_command_streaming(
                command,
                cwd=source_path,
                env=env
            ):
                yield data
            
            yield f"[{datetime.now().isoformat()}] Command {i} completed\n"
    
    async def execute_build(
        self,
        job: BuildJob,
        config: BuildConfig,
        source_path: str,
        build_path: str
    ) -> AsyncIterator[str]:
        """
        Execute the kernel build.
        
        Args:
            job: Build job
            config: Build configuration
            source_path: Source directory path
            build_path: Build output directory path
            
        Yields:
            Log lines
        """
        # Determine number of parallel jobs
        cpu_cores = self.server.total_cpu_cores
        parallel_jobs = max(1, cpu_cores - 1)  # Leave one core free
        
        # Build make command
        make_args = [f"-j{parallel_jobs}"] + config.extra_make_args
        make_cmd = f"make -C {source_path} O={build_path} ARCH={job.target_architecture} {' '.join(make_args)}"
        
        yield f"Building kernel: {make_cmd}\n"
        
        async for stream_type, data in self.execute_command_streaming(make_cmd, env=config.custom_env):
            yield data
        
        # Build modules if enabled
        if config.enable_modules:
            make_cmd = f"make -C {source_path} O={build_path} ARCH={job.target_architecture} modules -j{parallel_jobs}"
            yield f"\nBuilding modules: {make_cmd}\n"
            
            async for stream_type, data in self.execute_command_streaming(make_cmd, env=config.custom_env):
                yield data
        
        # Build device trees if enabled
        if config.build_dtbs:
            make_cmd = f"make -C {source_path} O={build_path} ARCH={job.target_architecture} dtbs -j{parallel_jobs}"
            yield f"\nBuilding device trees: {make_cmd}\n"
            
            async for stream_type, data in self.execute_command_streaming(make_cmd, env=config.custom_env):
                yield data
    
    async def collect_artifacts(
        self,
        job: BuildJob,
        config: BuildConfig,
        build_path: str,
        artifact_storage_path: str
    ) -> List[str]:
        """
        Collect build artifacts from the build directory.
        
        Args:
            job: Build job
            config: Build configuration
            build_path: Build output directory path
            artifact_storage_path: Local path to store artifacts
            
        Returns:
            List of artifact file paths
        """
        artifacts = []
        
        # Create local artifact directory
        local_artifact_dir = Path(artifact_storage_path) / job.id
        local_artifact_dir.mkdir(parents=True, exist_ok=True)
        
        # Find artifacts matching patterns
        for pattern in config.artifact_patterns:
            find_cmd = f"find {build_path} -path '{build_path}/{pattern}' -type f"
            exit_code, stdout, stderr = await self.execute_command(find_cmd)
            
            if exit_code == 0 and stdout.strip():
                for artifact_path in stdout.strip().split('\n'):
                    if artifact_path:
                        # Get relative path
                        rel_path = artifact_path.replace(f"{build_path}/", "")
                        
                        # Create local subdirectories
                        local_file = local_artifact_dir / rel_path
                        local_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Transfer file via SFTP
                        try:
                            sftp = self.ssh_client.open_sftp()
                            sftp.get(artifact_path, str(local_file))
                            sftp.close()
                            
                            artifacts.append(str(local_file))
                            print(f"Collected artifact: {rel_path}")
                        except Exception as e:
                            print(f"Failed to collect artifact {artifact_path}: {e}")
        
        return artifacts
    
    async def cleanup_workspace(self, workspace_path: str, keep_workspace: bool = False):
        """
        Clean up the build workspace.
        
        Args:
            workspace_path: Workspace directory path
            keep_workspace: Whether to keep the workspace
        """
        if not keep_workspace:
            exit_code, stdout, stderr = await self.execute_command(
                f"rm -rf {workspace_path}"
            )
            
            if exit_code != 0:
                print(f"Warning: Failed to cleanup workspace: {stderr}")
    
    async def execute_full_build(
        self,
        job: BuildJob,
        config: BuildConfig,
        artifact_storage_path: str
    ) -> AsyncIterator[str]:
        """
        Execute the complete build process.
        
        Args:
            job: Build job
            config: Build configuration
            artifact_storage_path: Path to store artifacts
            
        Yields:
            Log lines
        """
        workspace_path = None
        
        try:
            # Connect to server
            yield f"[{datetime.now().isoformat()}] Connecting to build server {self.server.hostname}...\n"
            if not await self.connect():
                raise RuntimeError("Failed to connect to build server")
            yield f"[{datetime.now().isoformat()}] Connected successfully\n"
            
            # Setup workspace
            yield f"[{datetime.now().isoformat()}] Setting up workspace...\n"
            workspace_path = await self.setup_workspace(job, config)
            yield f"[{datetime.now().isoformat()}] Workspace: {workspace_path}\n"
            
            # Clone repository
            yield f"[{datetime.now().isoformat()}] Cloning repository {job.source_repository}...\n"
            source_path = await self.clone_repository(job, config, workspace_path)
            yield f"[{datetime.now().isoformat()}] Repository cloned to {source_path}\n"
            
            # Determine build path
            build_path = config.build_directory or f"{workspace_path}/build"
            
            # Check build mode
            if config.build_mode == "custom":
                # Custom build mode
                yield f"[{datetime.now().isoformat()}] Build mode: Custom Commands\n"
                
                # Execute pre-build commands
                if config.pre_build_commands:
                    async for log_line in self.execute_custom_commands(
                        config.pre_build_commands,
                        source_path,
                        config.custom_env,
                        "pre-build"
                    ):
                        yield log_line
                
                # Execute main build commands
                if config.build_commands:
                    async for log_line in self.execute_custom_commands(
                        config.build_commands,
                        source_path,
                        config.custom_env,
                        "build"
                    ):
                        yield log_line
                else:
                    yield f"[{datetime.now().isoformat()}] WARNING: No build commands specified\n"
                
                # Execute post-build commands
                if config.post_build_commands:
                    async for log_line in self.execute_custom_commands(
                        config.post_build_commands,
                        source_path,
                        config.custom_env,
                        "post-build"
                    ):
                        yield log_line
                
                yield f"[{datetime.now().isoformat()}] Custom build complete\n"
            else:
                # Standard kernel build mode
                yield f"[{datetime.now().isoformat()}] Build mode: Standard Kernel Build\n"
                
                # Configure build
                yield f"[{datetime.now().isoformat()}] Configuring build...\n"
                async for log_line in self.configure_build(job, config, source_path, build_path):
                    yield log_line
                yield f"[{datetime.now().isoformat()}] Configuration complete\n"
                
                # Execute build
                yield f"[{datetime.now().isoformat()}] Starting build...\n"
                async for log_line in self.execute_build(job, config, source_path, build_path):
                    yield log_line
                yield f"[{datetime.now().isoformat()}] Build complete\n"
            
            # Collect artifacts
            yield f"[{datetime.now().isoformat()}] Collecting artifacts...\n"
            artifacts = await self.collect_artifacts(job, config, build_path, artifact_storage_path)
            yield f"[{datetime.now().isoformat()}] Collected {len(artifacts)} artifacts\n"
            
            for artifact in artifacts:
                yield f"  - {artifact}\n"
            
            # Store artifacts in job
            job.artifacts = artifacts
            
        finally:
            # Cleanup
            if workspace_path:
                yield f"[{datetime.now().isoformat()}] Cleaning up workspace...\n"
                await self.cleanup_workspace(workspace_path, config.keep_workspace)
                if config.keep_workspace:
                    yield f"[{datetime.now().isoformat()}] Workspace preserved at {workspace_path}\n"
                else:
                    yield f"[{datetime.now().isoformat()}] Workspace cleaned up\n"
            
            # Disconnect
            self.disconnect()
            yield f"[{datetime.now().isoformat()}] Disconnected from build server\n"
