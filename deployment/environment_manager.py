"""
Environment Manager Factory and Base Classes

Provides environment-specific deployment operations for different environment types
(QEMU/KVM, Physical Hardware, Containers).
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from .models import TestArtifact, Dependency, ValidationResult


logger = logging.getLogger(__name__)


class Connection:
    """Represents a connection to an environment"""
    
    def __init__(self, environment_id: str, connection_type: str):
        self.environment_id = environment_id
        self.connection_type = connection_type
        self.is_connected = False
        self.connection_details: Dict[str, Any] = {}
    
    async def close(self):
        """Close the connection"""
        self.is_connected = False
        logger.info(f"Closed connection to environment {self.environment_id}")


class EnvironmentConfig:
    """Configuration for an environment"""
    
    def __init__(self, 
                 environment_id: str,
                 environment_type: str,
                 connection_params: Dict[str, Any]):
        self.environment_id = environment_id
        self.environment_type = environment_type
        self.connection_params = connection_params


class EnvironmentManager(ABC):
    """
    Abstract base class for environment-specific deployment operations.
    
    Handles environment-specific deployment operations including:
    - QEMU/KVM virtual machine management
    - Physical hardware board communication via SSH
    - Container-based environment setup
    - Network and storage configuration
    """
    
    def __init__(self, environment_config: EnvironmentConfig):
        self.environment_config = environment_config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    @abstractmethod
    async def connect(self, env_config: EnvironmentConfig) -> Connection:
        """
        Establish connection to the environment.
        
        Args:
            env_config: Environment configuration
            
        Returns:
            Connection object
            
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    async def deploy_artifacts(self, connection: Connection, artifacts: List[TestArtifact]) -> bool:
        """
        Deploy test artifacts to the environment.
        
        Args:
            connection: Active connection to environment
            artifacts: List of artifacts to deploy
            
        Returns:
            True if deployment successful, False otherwise
            
        Raises:
            DeploymentError: If deployment fails
        """
        pass
    
    @abstractmethod
    async def install_dependencies(self, connection: Connection, dependencies: List[Dependency]) -> bool:
        """
        Install dependencies in the environment.
        
        Args:
            connection: Active connection to environment
            dependencies: List of dependencies to install
            
        Returns:
            True if installation successful, False otherwise
            
        Raises:
            InstallationError: If installation fails
        """
        pass
    
    @abstractmethod
    async def configure_instrumentation(self, connection: Connection, config: Any) -> bool:
        """
        Configure instrumentation and monitoring tools.
        
        Args:
            connection: Active connection to environment
            config: Instrumentation configuration
            
        Returns:
            True if configuration successful, False otherwise
            
        Raises:
            ConfigurationError: If configuration fails
        """
        pass
    
    @abstractmethod
    async def validate_readiness(self, connection: Connection) -> ValidationResult:
        """
        Validate that environment is ready for test execution.
        
        Args:
            connection: Active connection to environment
            
        Returns:
            ValidationResult with readiness status and details
        """
        pass
    
    async def test_connection(self) -> bool:
        """
        Test connection to environment.
        
        Returns:
            True if connection test successful, False otherwise
        """
        try:
            connection = await self.connect(self.environment_config)
            await connection.close()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


class QEMUEnvironmentManager(EnvironmentManager):
    """
    Environment manager for QEMU/KVM virtual machines.
    
    Handles QEMU/KVM virtual machine deployment with SSH-based artifact deployment,
    VM state management, and monitoring capabilities.
    """
    
    def __init__(self, environment_config: EnvironmentConfig):
        super().__init__(environment_config)
        self.vm_state = "unknown"
        self.ssh_client = None
    
    async def connect(self, env_config: EnvironmentConfig) -> Connection:
        """
        Connect to QEMU environment via SSH with enhanced error handling.
        
        Args:
            env_config: Environment configuration with connection parameters
            
        Returns:
            Connection object with SSH details
            
        Raises:
            ConnectionError: If SSH connection fails
        """
        self.logger.info(f"Connecting to QEMU environment {env_config.environment_id}")
        
        try:
            # Validate connection parameters
            host = env_config.connection_params.get("host")
            port = env_config.connection_params.get("port", 22)
            username = env_config.connection_params.get("username")
            
            if not host or not username:
                raise ValueError("Host and username are required for QEMU connection")
            
            # Check VM state first
            await self._check_vm_state(env_config)
            
            # Establish SSH connection (simulated)
            await self._establish_ssh_connection(host, port, username, env_config.connection_params)
            
            connection = Connection(env_config.environment_id, "ssh")
            connection.is_connected = True
            connection.connection_details = {
                "host": host,
                "port": port,
                "username": username,
                "vm_state": self.vm_state,
                "connection_type": "qemu_ssh",
                "established_at": asyncio.get_event_loop().time()
            }
            
            self.logger.info(f"Successfully connected to QEMU environment {env_config.environment_id}")
            return connection
            
        except Exception as e:
            self.logger.error(f"Failed to connect to QEMU environment {env_config.environment_id}: {e}")
            raise ConnectionError(f"QEMU connection failed: {e}")
    
    async def _check_vm_state(self, env_config: EnvironmentConfig):
        """Check QEMU VM state before connecting"""
        self.logger.debug("Checking QEMU VM state")
        
        # Simulate VM state check
        await asyncio.sleep(0.05)
        
        # In a real implementation, this would use QEMU monitor or libvirt
        vm_states = ["running", "paused", "stopped"]
        self.vm_state = "running"  # Assume running for simulation
        
        if self.vm_state != "running":
            raise ConnectionError(f"VM is not running (state: {self.vm_state})")
    
    async def _establish_ssh_connection(self, host: str, port: int, username: str, params: dict):
        """Establish SSH connection to QEMU VM"""
        self.logger.debug(f"Establishing SSH connection to {username}@{host}:{port}")
        
        # Simulate SSH connection establishment
        await asyncio.sleep(0.1)
        
        # In a real implementation, this would use paramiko or asyncssh
        auth_method = params.get("auth_method", "password")
        
        if auth_method == "password":
            password = params.get("password")
            if not password:
                raise ConnectionError("Password required for password authentication")
        elif auth_method == "key":
            private_key = params.get("private_key_path")
            if not private_key:
                raise ConnectionError("Private key path required for key authentication")
        
        # Simulate successful authentication
        self.ssh_client = "mock_ssh_client"
    
    async def deploy_artifacts(self, connection: Connection, artifacts: List[TestArtifact]) -> bool:
        """
        Deploy artifacts to QEMU environment via SSH/SCP.
        
        Args:
            connection: Active SSH connection to QEMU VM
            artifacts: List of artifacts to deploy
            
        Returns:
            True if all artifacts deployed successfully
            
        Raises:
            DeploymentError: If artifact deployment fails
        """
        self.logger.info(f"Deploying {len(artifacts)} artifacts to QEMU environment")
        
        try:
            for artifact in artifacts:
                # Validate artifact before deployment
                if not artifact.content:
                    raise ValueError(f"Artifact {artifact.name} has no content")
                
                # Create target directory if needed
                await self._ensure_target_directory(connection, artifact.target_path)
                
                # Transfer artifact content via SCP/SFTP (simulated)
                await self._transfer_artifact(connection, artifact)
                
                # Set proper permissions
                await self._set_artifact_permissions(connection, artifact)
                
                # Verify deployment
                await self._verify_artifact_deployment(connection, artifact)
                
                self.logger.debug(f"Successfully deployed artifact {artifact.name} to {artifact.target_path}")
            
            self.logger.info(f"Successfully deployed all {len(artifacts)} artifacts")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy artifacts to QEMU environment: {e}")
            raise RuntimeError(f"Artifact deployment failed: {e}")
    
    async def _ensure_target_directory(self, connection: Connection, target_path: str):
        """Ensure target directory exists"""
        import os
        target_dir = os.path.dirname(target_path)
        if target_dir:
            self.logger.debug(f"Creating directory: {target_dir}")
            # Simulate mkdir -p command
            await asyncio.sleep(0.01)
    
    async def _transfer_artifact(self, connection: Connection, artifact: TestArtifact):
        """Transfer artifact content to target"""
        self.logger.debug(f"Transferring {len(artifact.content)} bytes for {artifact.name}")
        
        # Simulate file transfer time based on size
        transfer_time = min(0.1, len(artifact.content) / 1000000)  # Max 0.1s, 1MB/s rate
        await asyncio.sleep(transfer_time)
    
    async def _set_artifact_permissions(self, connection: Connection, artifact: TestArtifact):
        """Set proper file permissions"""
        if artifact.permissions:
            self.logger.debug(f"Setting permissions {artifact.permissions} for {artifact.name}")
            # Simulate chmod command
            await asyncio.sleep(0.01)
    
    async def _verify_artifact_deployment(self, connection: Connection, artifact: TestArtifact):
        """Verify artifact was deployed correctly"""
        # Simulate file existence and checksum verification
        await asyncio.sleep(0.02)
    
    async def install_dependencies(self, connection: Connection, dependencies: List[Dependency]) -> bool:
        """
        Install dependencies in QEMU environment using appropriate package managers.
        
        Args:
            connection: Active SSH connection to QEMU VM
            dependencies: List of dependencies to install
            
        Returns:
            True if all dependencies installed successfully
            
        Raises:
            InstallationError: If dependency installation fails
        """
        self.logger.info(f"Installing {len(dependencies)} dependencies in QEMU environment")
        
        try:
            # Group dependencies by package manager for efficiency
            deps_by_manager = {}
            for dep in dependencies:
                manager = dep.package_manager
                if manager not in deps_by_manager:
                    deps_by_manager[manager] = []
                deps_by_manager[manager].append(dep)
            
            # Install dependencies by package manager
            for manager, deps in deps_by_manager.items():
                await self._install_dependencies_with_manager(connection, manager, deps)
            
            # Verify all dependencies are installed
            for dep in dependencies:
                if not dep.optional:
                    await self._verify_dependency_installation(connection, dep)
            
            self.logger.info(f"Successfully installed all {len(dependencies)} dependencies")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install dependencies in QEMU environment: {e}")
            raise RuntimeError(f"Dependency installation failed: {e}")
    
    async def _install_dependencies_with_manager(self, connection: Connection, manager: str, deps: List[Dependency]):
        """Install dependencies using specific package manager"""
        self.logger.debug(f"Installing {len(deps)} dependencies with {manager}")
        
        if manager == "apt":
            # Update package list first
            await self._execute_command(connection, "apt-get update")
            
            # Install packages
            for dep in deps:
                await self._execute_command(connection, dep.install_command)
        
        elif manager == "pip":
            # Install Python packages
            for dep in deps:
                await self._execute_command(connection, dep.install_command)
        
        elif manager in ["yum", "dnf"]:
            # Install RPM packages
            for dep in deps:
                await self._execute_command(connection, dep.install_command)
        
        else:
            # Generic installation
            for dep in deps:
                await self._execute_command(connection, dep.install_command)
    
    async def _execute_command(self, connection: Connection, command: str):
        """Execute command via SSH"""
        self.logger.debug(f"Executing: {command}")
        # Simulate command execution time
        await asyncio.sleep(0.1)
    
    async def _verify_dependency_installation(self, connection: Connection, dep: Dependency):
        """Verify dependency was installed correctly"""
        if dep.verify_command:
            self.logger.debug(f"Verifying installation of {dep.name}")
            await self._execute_command(connection, dep.verify_command)
    
    async def configure_instrumentation(self, connection: Connection, config: Any) -> bool:
        """Configure instrumentation in QEMU environment"""
        self.logger.info("Configuring instrumentation in QEMU environment")
        
        # Simulate instrumentation setup
        await asyncio.sleep(0.1)  # Simulate configuration time
        
        return True
    
    async def validate_readiness(self, connection: Connection) -> ValidationResult:
        """Validate QEMU environment readiness"""
        self.logger.info("Validating QEMU environment readiness")
        
        # Simulate readiness checks
        await asyncio.sleep(0.1)  # Simulate validation time
        
        return ValidationResult(
            environment_id=connection.environment_id,
            is_ready=True,
            checks_performed=["network_connectivity", "disk_space", "kernel_version"],
            failed_checks=[],
            warnings=[]
        )


class PhysicalEnvironmentManager(EnvironmentManager):
    """
    Environment manager for physical hardware boards.
    
    Handles physical hardware board deployment via SSH with hardware-specific
    configuration, board availability monitoring, and health checks.
    """
    
    def __init__(self, environment_config: EnvironmentConfig):
        super().__init__(environment_config)
        self.board_info = {}
        self.health_status = "unknown"
    
    async def connect(self, env_config: EnvironmentConfig) -> Connection:
        """
        Connect to physical hardware via SSH with hardware validation.
        
        Args:
            env_config: Environment configuration with hardware connection parameters
            
        Returns:
            Connection object with hardware details
            
        Raises:
            ConnectionError: If hardware connection fails
        """
        self.logger.info(f"Connecting to physical hardware {env_config.environment_id}")
        
        try:
            # Validate hardware-specific connection parameters
            host = env_config.connection_params.get("host")
            port = env_config.connection_params.get("port", 22)
            username = env_config.connection_params.get("username")
            board_type = env_config.connection_params.get("board_type", "unknown")
            
            if not host or not username:
                raise ValueError("Host and username are required for hardware connection")
            
            # Check hardware availability and health
            await self._check_hardware_health(env_config)
            
            # Establish SSH connection with hardware-specific timeouts
            await self._establish_hardware_connection(host, port, username, env_config.connection_params)
            
            # Gather hardware information
            await self._gather_hardware_info(env_config)
            
            connection = Connection(env_config.environment_id, "ssh")
            connection.is_connected = True
            connection.connection_details = {
                "host": host,
                "port": port,
                "username": username,
                "board_type": board_type,
                "hardware_info": self.board_info,
                "health_status": self.health_status,
                "connection_type": "physical_ssh",
                "established_at": asyncio.get_event_loop().time()
            }
            
            self.logger.info(f"Successfully connected to physical hardware {env_config.environment_id}")
            return connection
            
        except Exception as e:
            self.logger.error(f"Failed to connect to physical hardware {env_config.environment_id}: {e}")
            raise ConnectionError(f"Hardware connection failed: {e}")
    
    async def _check_hardware_health(self, env_config: EnvironmentConfig):
        """Check physical hardware health and availability"""
        self.logger.debug("Checking physical hardware health")
        
        # Simulate hardware health check (longer for physical hardware)
        await asyncio.sleep(0.2)
        
        # In a real implementation, this would check:
        # - Network connectivity
        # - Hardware temperature sensors
        # - Power status
        # - Board responsiveness
        
        # Simulate health check results
        self.health_status = "healthy"  # Could be: healthy, warning, critical, offline
        
        if self.health_status == "offline":
            raise ConnectionError("Hardware board is offline")
        elif self.health_status == "critical":
            raise ConnectionError("Hardware board has critical issues")
    
    async def _establish_hardware_connection(self, host: str, port: int, username: str, params: dict):
        """Establish SSH connection to physical hardware with extended timeouts"""
        self.logger.debug(f"Establishing SSH connection to hardware {username}@{host}:{port}")
        
        # Simulate SSH connection with longer timeout for physical hardware
        await asyncio.sleep(0.2)
        
        # Hardware-specific authentication handling
        auth_method = params.get("auth_method", "password")
        
        if auth_method == "password":
            password = params.get("password")
            if not password:
                raise ConnectionError("Password required for hardware authentication")
        elif auth_method == "key":
            private_key = params.get("private_key_path")
            if not private_key:
                raise ConnectionError("Private key path required for hardware key authentication")
    
    async def _gather_hardware_info(self, env_config: EnvironmentConfig):
        """Gather hardware-specific information"""
        self.logger.debug("Gathering hardware information")
        
        # Simulate hardware info gathering
        await asyncio.sleep(0.1)
        
        # In a real implementation, this would gather:
        # - CPU architecture and model
        # - Memory configuration
        # - Storage devices
        # - Network interfaces
        # - Kernel version
        # - Board-specific details
        
        self.board_info = {
            "architecture": "aarch64",
            "cpu_model": "ARM Cortex-A78",
            "memory_gb": 8,
            "storage_type": "eMMC",
            "network_interfaces": ["eth0", "wlan0"],
            "kernel_version": "5.15.0",
            "board_revision": "1.2"
        }
    
    async def deploy_artifacts(self, connection: Connection, artifacts: List[TestArtifact]) -> bool:
        """
        Deploy artifacts to physical hardware with hardware-specific optimizations.
        
        Args:
            connection: Active SSH connection to physical hardware
            artifacts: List of artifacts to deploy
            
        Returns:
            True if all artifacts deployed successfully
            
        Raises:
            DeploymentError: If artifact deployment fails
        """
        self.logger.info(f"Deploying {len(artifacts)} artifacts to physical hardware")
        
        try:
            # Check available storage space first
            await self._check_storage_space(connection, artifacts)
            
            for artifact in artifacts:
                # Validate artifact for hardware deployment
                await self._validate_artifact_for_hardware(artifact)
                
                # Create target directory with hardware-appropriate permissions
                await self._ensure_hardware_target_directory(connection, artifact.target_path)
                
                # Transfer artifact with hardware-optimized settings
                await self._transfer_artifact_to_hardware(connection, artifact)
                
                # Set hardware-appropriate permissions
                await self._set_hardware_permissions(connection, artifact)
                
                # Verify deployment on hardware
                await self._verify_hardware_deployment(connection, artifact)
                
                self.logger.debug(f"Successfully deployed artifact {artifact.name} to hardware")
            
            # Sync filesystem to ensure data persistence
            await self._sync_filesystem(connection)
            
            self.logger.info(f"Successfully deployed all {len(artifacts)} artifacts to hardware")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy artifacts to physical hardware: {e}")
            raise RuntimeError(f"Hardware artifact deployment failed: {e}")
    
    async def _check_storage_space(self, connection: Connection, artifacts: List[TestArtifact]):
        """Check available storage space on hardware"""
        total_size = sum(len(artifact.content) for artifact in artifacts)
        self.logger.debug(f"Checking storage space for {total_size} bytes")
        
        # Simulate df command to check disk space
        await asyncio.sleep(0.05)
        
        # In a real implementation, would parse df output and check available space
    
    async def _validate_artifact_for_hardware(self, artifact: TestArtifact):
        """Validate artifact is suitable for hardware deployment"""
        # Check for hardware-specific constraints
        if len(artifact.content) > 100 * 1024 * 1024:  # 100MB limit for demo
            self.logger.warning(f"Large artifact {artifact.name} may take time to deploy to hardware")
    
    async def _ensure_hardware_target_directory(self, connection: Connection, target_path: str):
        """Ensure target directory exists with hardware-appropriate settings"""
        import os
        target_dir = os.path.dirname(target_path)
        if target_dir:
            self.logger.debug(f"Creating hardware directory: {target_dir}")
            # Simulate mkdir with sync for hardware reliability
            await asyncio.sleep(0.02)
    
    async def _transfer_artifact_to_hardware(self, connection: Connection, artifact: TestArtifact):
        """Transfer artifact to hardware with reliability checks"""
        self.logger.debug(f"Transferring {len(artifact.content)} bytes to hardware for {artifact.name}")
        
        # Simulate slower transfer to physical hardware
        transfer_time = min(0.2, len(artifact.content) / 500000)  # 500KB/s rate for hardware
        await asyncio.sleep(transfer_time)
    
    async def _set_hardware_permissions(self, connection: Connection, artifact: TestArtifact):
        """Set permissions appropriate for hardware environment"""
        if artifact.permissions:
            self.logger.debug(f"Setting hardware permissions {artifact.permissions} for {artifact.name}")
            # Simulate chmod with sync
            await asyncio.sleep(0.02)
    
    async def _verify_hardware_deployment(self, connection: Connection, artifact: TestArtifact):
        """Verify artifact deployment on hardware with checksum validation"""
        # Simulate checksum verification on hardware
        await asyncio.sleep(0.03)
    
    async def _sync_filesystem(self, connection: Connection):
        """Sync filesystem to ensure data persistence on hardware"""
        self.logger.debug("Syncing filesystem on hardware")
        # Simulate sync command
        await asyncio.sleep(0.05)
    
    async def install_dependencies(self, connection: Connection, dependencies: List[Dependency]) -> bool:
        """Install dependencies on physical hardware"""
        self.logger.info(f"Installing {len(dependencies)} dependencies on physical hardware")
        
        for dep in dependencies:
            # Simulate package installation (slower for physical hardware)
            await asyncio.sleep(0.2)  # Simulate installation time
            self.logger.debug(f"Installed dependency {dep.name}")
        
        return True
    
    async def configure_instrumentation(self, connection: Connection, config: Any) -> bool:
        """Configure instrumentation on physical hardware"""
        self.logger.info("Configuring instrumentation on physical hardware")
        
        # Simulate instrumentation setup
        await asyncio.sleep(0.2)  # Simulate configuration time
        
        return True
    
    async def validate_readiness(self, connection: Connection) -> ValidationResult:
        """Validate physical hardware readiness"""
        self.logger.info("Validating physical hardware readiness")
        
        # Simulate readiness checks
        await asyncio.sleep(0.2)  # Simulate validation time
        
        return ValidationResult(
            environment_id=connection.environment_id,
            is_ready=True,
            checks_performed=["network_connectivity", "disk_space", "hardware_health", "kernel_version"],
            failed_checks=[],
            warnings=["Hardware temperature slightly elevated"]
        )


class EnvironmentManagerFactory:
    """Factory for creating environment managers based on environment type"""
    
    def __init__(self):
        self._managers: Dict[str, EnvironmentManager] = {}
        self._environment_configs: Dict[str, EnvironmentConfig] = {}
    
    def register_environment(self, environment_id: str, environment_config: EnvironmentConfig):
        """Register an environment configuration"""
        self._environment_configs[environment_id] = environment_config
        logger.info(f"Registered environment {environment_id} of type {environment_config.environment_type}")
    
    async def get_manager(self, environment_id: str) -> EnvironmentManager:
        """
        Get environment manager for the specified environment.
        
        Args:
            environment_id: Environment identifier
            
        Returns:
            EnvironmentManager instance
            
        Raises:
            ValueError: If environment not found or unsupported type
        """
        # Check if manager already exists
        if environment_id in self._managers:
            return self._managers[environment_id]
        
        # Get environment configuration
        env_config = self._environment_configs.get(environment_id)
        if not env_config:
            # Create default configuration for demo purposes
            env_config = EnvironmentConfig(
                environment_id=environment_id,
                environment_type="qemu",  # Default to QEMU
                connection_params={"host": "localhost", "port": 22, "username": "root"}
            )
            self._environment_configs[environment_id] = env_config
        
        # Create manager based on environment type
        if env_config.environment_type.lower() in ["qemu", "kvm"]:
            manager = QEMUEnvironmentManager(env_config)
        elif env_config.environment_type.lower() in ["physical", "hardware"]:
            manager = PhysicalEnvironmentManager(env_config)
        else:
            raise ValueError(f"Unsupported environment type: {env_config.environment_type}")
        
        # Cache the manager
        self._managers[environment_id] = manager
        
        logger.info(f"Created {manager.__class__.__name__} for environment {environment_id}")
        return manager
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported environment types"""
        return ["qemu", "kvm", "physical", "hardware"]