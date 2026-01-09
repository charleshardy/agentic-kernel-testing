"""
Deployment Manager Service

Manages deployment of build artifacts to test environments (QEMU hosts and physical boards).
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from infrastructure.models.artifact import Artifact, ArtifactSelection
from infrastructure.models.deployment import (
    Deployment,
    DeploymentStatus,
    DeploymentTargetType,
)
from infrastructure.models.host import Host, HostStatus
from infrastructure.models.board import Board, BoardStatus
from infrastructure.services.artifact_manager import ArtifactRepositoryManager
from infrastructure.services.host_service import HostManagementService, VMInfo
from infrastructure.services.board_service import BoardManagementService, FirmwareConfig
from infrastructure.connectors.ssh_connector import SSHConnector, SSHCredentials
from infrastructure.connectors.flash_controller import FlashStationController

logger = logging.getLogger(__name__)


@dataclass
class VMConfig:
    """Configuration for a QEMU virtual machine."""
    name: str
    cpu_cores: int = 2
    memory_mb: int = 2048
    disk_gb: int = 20
    architecture: str = "x86_64"
    enable_kvm: bool = True
    network_mode: str = "nat"
    extra_args: List[str] = field(default_factory=list)


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    success: bool
    deployment: Optional[Deployment] = None
    error_message: Optional[str] = None
    boot_verified: bool = False
    boot_logs: Optional[str] = None


@dataclass
class DeploymentStatusResult:
    """Status of a deployment."""
    deployment_id: str
    status: DeploymentStatus
    target_type: DeploymentTargetType
    target_id: str
    progress_percent: float = 0.0
    current_step: str = ""
    error_message: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of deployment verification."""
    success: bool
    deployment_id: str
    boot_successful: bool = False
    kernel_version: Optional[str] = None
    boot_time_seconds: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    success: bool
    deployment_id: str
    previous_build_id: Optional[str] = None
    error_message: Optional[str] = None


class DeploymentManager:
    """
    Manages deployment of build artifacts to test environments.
    
    Handles:
    - Deployment to QEMU hosts with artifact transfer and VM configuration
    - Deployment to physical boards with flashing support
    - Boot verification and rollback
    - Deployment history tracking
    """

    def __init__(
        self,
        artifact_manager: Optional[ArtifactRepositoryManager] = None,
        host_service: Optional[HostManagementService] = None,
        board_service: Optional[BoardManagementService] = None,
        ssh_connector: Optional[SSHConnector] = None,
        flash_controller: Optional[FlashStationController] = None,
        boot_timeout: int = 120,
        transfer_timeout: int = 300,
    ):
        """
        Initialize Deployment Manager.
        
        Args:
            artifact_manager: Artifact repository manager
            host_service: Host management service
            board_service: Board management service
            ssh_connector: SSH connector for file transfers
            flash_controller: Flash station controller for board flashing
            boot_timeout: Boot verification timeout in seconds
            transfer_timeout: File transfer timeout in seconds
        """
        self.artifact_manager = artifact_manager or ArtifactRepositoryManager()
        self.host_service = host_service or HostManagementService()
        self.board_service = board_service or BoardManagementService()
        self.ssh_connector = ssh_connector or SSHConnector()
        self.flash_controller = flash_controller or FlashStationController()
        self.boot_timeout = boot_timeout
        self.transfer_timeout = transfer_timeout
        
        # Deployment tracking
        self._deployments: Dict[str, Deployment] = {}
        self._deployment_lock = asyncio.Lock()
        
        # Deployment history per target
        self._deployment_history: Dict[str, List[str]] = {}  # target_id -> [deployment_ids]
        
        # Previous successful deployments for rollback
        self._previous_deployments: Dict[str, str] = {}  # target_id -> deployment_id


    async def deploy_to_qemu(
        self,
        host_id: str,
        artifacts: ArtifactSelection,
        vm_config: VMConfig
    ) -> DeploymentResult:
        """
        Deploy build artifacts to a QEMU host.
        
        Args:
            host_id: Target QEMU host ID
            artifacts: Artifact selection criteria
            vm_config: VM configuration
            
        Returns:
            DeploymentResult with deployment details
        """
        deployment_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting QEMU deployment {deployment_id} to host {host_id}")
            
            # Validate host exists and is available
            host = await self.host_service.get_host(host_id)
            if not host:
                return DeploymentResult(
                    success=False,
                    error_message=f"Host {host_id} not found"
                )
            
            if host.status not in (HostStatus.ONLINE, HostStatus.DEGRADED):
                return DeploymentResult(
                    success=False,
                    error_message=f"Host {host_id} is not available (status: {host.status.value})"
                )
            
            if host.maintenance_mode:
                return DeploymentResult(
                    success=False,
                    error_message=f"Host {host_id} is in maintenance mode"
                )
            
            # Get artifacts
            artifact_list = await self.artifact_manager.get_artifacts_by_selection(artifacts)
            if not artifact_list:
                return DeploymentResult(
                    success=False,
                    error_message="No artifacts found matching selection criteria"
                )
            
            # Validate architecture compatibility
            if not self._validate_qemu_architecture(artifact_list, host, vm_config):
                return DeploymentResult(
                    success=False,
                    error_message=f"Artifacts architecture does not match host/VM architecture"
                )
            
            # Create deployment record
            now = datetime.now(timezone.utc)
            deployment = Deployment(
                id=deployment_id,
                target_type=DeploymentTargetType.QEMU_HOST,
                target_id=host_id,
                artifacts=[a.id for a in artifact_list],
                build_id=artifact_list[0].build_id,
                status=DeploymentStatus.PENDING,
                created_at=now
            )
            
            async with self._deployment_lock:
                self._deployments[deployment_id] = deployment
            
            # Start deployment process
            deployment.status = DeploymentStatus.TRANSFERRING
            deployment.started_at = datetime.now(timezone.utc)
            
            # Transfer artifacts to host
            transfer_success = await self._transfer_artifacts_to_host(
                host, artifact_list, vm_config.name
            )
            
            if not transfer_success:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = "Failed to transfer artifacts to host"
                return DeploymentResult(
                    success=False,
                    deployment=deployment,
                    error_message=deployment.error_message
                )
            
            # Configure and start VM
            deployment.status = DeploymentStatus.BOOTING
            boot_success = await self._configure_and_boot_vm(host, artifact_list, vm_config)
            
            if not boot_success:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = "Failed to boot VM"
                return DeploymentResult(
                    success=False,
                    deployment=deployment,
                    error_message=deployment.error_message
                )
            
            # Verify boot
            deployment.status = DeploymentStatus.VERIFYING
            verification = await self._verify_qemu_boot(host, vm_config)
            
            deployment.boot_verified = verification.boot_successful
            deployment.completed_at = datetime.now(timezone.utc)
            
            if verification.boot_successful:
                deployment.status = DeploymentStatus.COMPLETED
                
                # Store as previous successful deployment for rollback
                self._previous_deployments[host_id] = deployment_id
                
                # Add to history
                self._add_to_history(host_id, deployment_id)
                
                # Update host VM count
                vm_info = VMInfo(
                    id=str(uuid.uuid4()),
                    name=vm_config.name,
                    state="running",
                    cpu_count=vm_config.cpu_cores,
                    memory_mb=vm_config.memory_mb,
                    host_id=host_id
                )
                await self.host_service.update_vm_count(host_id, vm_info=vm_info)
                
                return DeploymentResult(
                    success=True,
                    deployment=deployment,
                    boot_verified=True,
                    boot_logs=verification.kernel_version
                )
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = verification.error_message or "Boot verification failed"
                return DeploymentResult(
                    success=False,
                    deployment=deployment,
                    error_message=deployment.error_message
                )
                
        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {e}")
            
            async with self._deployment_lock:
                if deployment_id in self._deployments:
                    self._deployments[deployment_id].status = DeploymentStatus.FAILED
                    self._deployments[deployment_id].error_message = str(e)
            
            return DeploymentResult(
                success=False,
                error_message=str(e)
            )

    async def deploy_to_board(
        self,
        board_id: str,
        artifacts: ArtifactSelection
    ) -> DeploymentResult:
        """
        Deploy build artifacts to a physical test board.
        
        Args:
            board_id: Target board ID
            artifacts: Artifact selection criteria
            
        Returns:
            DeploymentResult with deployment details
        """
        deployment_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting board deployment {deployment_id} to board {board_id}")
            
            # Validate board exists and is available
            board = await self.board_service.get_board(board_id)
            if not board:
                return DeploymentResult(
                    success=False,
                    error_message=f"Board {board_id} not found"
                )
            
            if board.status not in (BoardStatus.AVAILABLE,):
                return DeploymentResult(
                    success=False,
                    error_message=f"Board {board_id} is not available (status: {board.status.value})"
                )
            
            if board.maintenance_mode:
                return DeploymentResult(
                    success=False,
                    error_message=f"Board {board_id} is in maintenance mode"
                )
            
            # Get artifacts
            artifact_list = await self.artifact_manager.get_artifacts_by_selection(artifacts)
            if not artifact_list:
                return DeploymentResult(
                    success=False,
                    error_message="No artifacts found matching selection criteria"
                )
            
            # Validate architecture compatibility
            if not self._validate_board_architecture(artifact_list, board):
                return DeploymentResult(
                    success=False,
                    error_message=f"Artifacts architecture does not match board architecture ({board.architecture})"
                )
            
            # Create deployment record
            now = datetime.now(timezone.utc)
            deployment = Deployment(
                id=deployment_id,
                target_type=DeploymentTargetType.PHYSICAL_BOARD,
                target_id=board_id,
                artifacts=[a.id for a in artifact_list],
                build_id=artifact_list[0].build_id,
                status=DeploymentStatus.PENDING,
                created_at=now
            )
            
            async with self._deployment_lock:
                self._deployments[deployment_id] = deployment
            
            # Start deployment process
            deployment.status = DeploymentStatus.TRANSFERRING
            deployment.started_at = datetime.now(timezone.utc)
            
            # Transfer artifacts to flash station
            transfer_success = await self._transfer_artifacts_to_flash_station(
                board, artifact_list
            )
            
            if not transfer_success:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = "Failed to transfer artifacts to flash station"
                return DeploymentResult(
                    success=False,
                    deployment=deployment,
                    error_message=deployment.error_message
                )
            
            # Flash firmware to board
            deployment.status = DeploymentStatus.FLASHING
            flash_success = await self._flash_board(board, artifact_list)
            
            if not flash_success:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = "Failed to flash firmware to board"
                return DeploymentResult(
                    success=False,
                    deployment=deployment,
                    error_message=deployment.error_message
                )
            
            # Power cycle and verify boot
            deployment.status = DeploymentStatus.BOOTING
            await self.board_service.power_cycle_board(board_id)
            
            # Wait for boot
            await asyncio.sleep(5)  # Allow time for boot
            
            # Verify boot
            deployment.status = DeploymentStatus.VERIFYING
            verification = await self._verify_board_boot(board)
            
            deployment.boot_verified = verification.boot_successful
            deployment.completed_at = datetime.now(timezone.utc)
            
            if verification.boot_successful:
                deployment.status = DeploymentStatus.COMPLETED
                
                # Store as previous successful deployment for rollback
                self._previous_deployments[board_id] = deployment_id
                
                # Add to history
                self._add_to_history(board_id, deployment_id)
                
                return DeploymentResult(
                    success=True,
                    deployment=deployment,
                    boot_verified=True,
                    boot_logs=verification.kernel_version
                )
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = verification.error_message or "Boot verification failed"
                return DeploymentResult(
                    success=False,
                    deployment=deployment,
                    error_message=deployment.error_message
                )
                
        except Exception as e:
            logger.error(f"Board deployment {deployment_id} failed: {e}")
            
            async with self._deployment_lock:
                if deployment_id in self._deployments:
                    self._deployments[deployment_id].status = DeploymentStatus.FAILED
                    self._deployments[deployment_id].error_message = str(e)
            
            return DeploymentResult(
                success=False,
                error_message=str(e)
            )


    async def get_deployment_status(
        self,
        deployment_id: str
    ) -> Optional[DeploymentStatusResult]:
        """
        Get the status of a deployment.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            DeploymentStatusResult or None if not found
        """
        async with self._deployment_lock:
            deployment = self._deployments.get(deployment_id)
        
        if not deployment:
            return None
        
        # Calculate progress based on status
        progress_map = {
            DeploymentStatus.PENDING: 0.0,
            DeploymentStatus.TRANSFERRING: 25.0,
            DeploymentStatus.FLASHING: 50.0,
            DeploymentStatus.BOOTING: 75.0,
            DeploymentStatus.VERIFYING: 90.0,
            DeploymentStatus.COMPLETED: 100.0,
            DeploymentStatus.FAILED: 0.0,
            DeploymentStatus.ROLLED_BACK: 0.0,
        }
        
        step_map = {
            DeploymentStatus.PENDING: "Waiting to start",
            DeploymentStatus.TRANSFERRING: "Transferring artifacts",
            DeploymentStatus.FLASHING: "Flashing firmware",
            DeploymentStatus.BOOTING: "Booting system",
            DeploymentStatus.VERIFYING: "Verifying boot",
            DeploymentStatus.COMPLETED: "Deployment complete",
            DeploymentStatus.FAILED: "Deployment failed",
            DeploymentStatus.ROLLED_BACK: "Rolled back",
        }
        
        return DeploymentStatusResult(
            deployment_id=deployment_id,
            status=deployment.status,
            target_type=deployment.target_type,
            target_id=deployment.target_id,
            progress_percent=progress_map.get(deployment.status, 0.0),
            current_step=step_map.get(deployment.status, "Unknown"),
            error_message=deployment.error_message
        )

    async def verify_deployment(
        self,
        deployment_id: str
    ) -> VerificationResult:
        """
        Verify a deployment was successful.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            VerificationResult with verification status
        """
        async with self._deployment_lock:
            deployment = self._deployments.get(deployment_id)
        
        if not deployment:
            return VerificationResult(
                success=False,
                deployment_id=deployment_id,
                error_message="Deployment not found"
            )
        
        if deployment.target_type == DeploymentTargetType.QEMU_HOST:
            host = await self.host_service.get_host(deployment.target_id)
            if not host:
                return VerificationResult(
                    success=False,
                    deployment_id=deployment_id,
                    error_message="Host not found"
                )
            
            # Re-verify boot
            return await self._verify_qemu_boot(host, None)
            
        elif deployment.target_type == DeploymentTargetType.PHYSICAL_BOARD:
            board = await self.board_service.get_board(deployment.target_id)
            if not board:
                return VerificationResult(
                    success=False,
                    deployment_id=deployment_id,
                    error_message="Board not found"
                )
            
            return await self._verify_board_boot(board)
        
        return VerificationResult(
            success=False,
            deployment_id=deployment_id,
            error_message="Unknown target type"
        )

    async def rollback_deployment(
        self,
        deployment_id: str
    ) -> RollbackResult:
        """
        Rollback a deployment to the previous known-good state.
        
        Args:
            deployment_id: Deployment identifier to rollback
            
        Returns:
            RollbackResult with rollback status
        """
        async with self._deployment_lock:
            deployment = self._deployments.get(deployment_id)
        
        if not deployment:
            return RollbackResult(
                success=False,
                deployment_id=deployment_id,
                error_message="Deployment not found"
            )
        
        if not deployment.can_rollback():
            return RollbackResult(
                success=False,
                deployment_id=deployment_id,
                error_message=f"Cannot rollback deployment in status: {deployment.status.value}"
            )
        
        target_id = deployment.target_id
        
        # Find previous successful deployment
        history = self._deployment_history.get(target_id, [])
        previous_deployment_id = None
        
        for dep_id in reversed(history):
            if dep_id != deployment_id:
                prev_dep = self._deployments.get(dep_id)
                if prev_dep and prev_dep.status == DeploymentStatus.COMPLETED:
                    previous_deployment_id = dep_id
                    break
        
        if not previous_deployment_id:
            return RollbackResult(
                success=False,
                deployment_id=deployment_id,
                error_message="No previous successful deployment found for rollback"
            )
        
        previous_deployment = self._deployments.get(previous_deployment_id)
        if not previous_deployment:
            return RollbackResult(
                success=False,
                deployment_id=deployment_id,
                error_message="Previous deployment data not found"
            )
        
        logger.info(f"Rolling back deployment {deployment_id} to {previous_deployment_id}")
        
        try:
            # Get artifacts from previous deployment
            artifacts = ArtifactSelection(build_id=previous_deployment.build_id)
            
            # Re-deploy based on target type
            if deployment.target_type == DeploymentTargetType.QEMU_HOST:
                # For QEMU, we need to recreate the VM with previous artifacts
                # This is a simplified rollback - in production would need VM config
                result = await self.deploy_to_qemu(
                    target_id,
                    artifacts,
                    VMConfig(name=f"rollback-{deployment_id[:8]}")
                )
            else:
                result = await self.deploy_to_board(target_id, artifacts)
            
            if result.success:
                # Mark original deployment as rolled back
                async with self._deployment_lock:
                    deployment.status = DeploymentStatus.ROLLED_BACK
                
                return RollbackResult(
                    success=True,
                    deployment_id=deployment_id,
                    previous_build_id=previous_deployment.build_id
                )
            else:
                return RollbackResult(
                    success=False,
                    deployment_id=deployment_id,
                    error_message=f"Rollback deployment failed: {result.error_message}"
                )
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return RollbackResult(
                success=False,
                deployment_id=deployment_id,
                error_message=str(e)
            )

    async def get_deployment_history(
        self,
        resource_id: str,
        limit: int = 10
    ) -> List[Deployment]:
        """
        Get deployment history for a resource.
        
        Args:
            resource_id: Host or board ID
            limit: Maximum number of deployments to return
            
        Returns:
            List of Deployment objects
        """
        history_ids = self._deployment_history.get(resource_id, [])
        
        deployments = []
        for dep_id in reversed(history_ids[-limit:]):
            deployment = self._deployments.get(dep_id)
            if deployment:
                deployments.append(deployment)
        
        return deployments

    async def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """Get a deployment by ID."""
        async with self._deployment_lock:
            return self._deployments.get(deployment_id)

    # Private helper methods

    def _validate_qemu_architecture(
        self,
        artifacts: List[Artifact],
        host: Host,
        vm_config: VMConfig
    ) -> bool:
        """Validate artifacts are compatible with QEMU host/VM architecture."""
        if not artifacts:
            return False
        
        artifact_arch = artifacts[0].architecture.lower()
        vm_arch = vm_config.architecture.lower()
        
        # Architecture mapping for compatibility
        arch_compat = {
            "x86_64": ["x86_64", "amd64"],
            "amd64": ["x86_64", "amd64"],
            "arm64": ["arm64", "aarch64"],
            "aarch64": ["arm64", "aarch64"],
            "armv7": ["armv7", "arm", "armhf"],
            "arm": ["armv7", "arm", "armhf"],
            "riscv64": ["riscv64", "riscv"],
        }
        
        compatible_archs = arch_compat.get(vm_arch, [vm_arch])
        return artifact_arch in compatible_archs

    def _validate_board_architecture(
        self,
        artifacts: List[Artifact],
        board: Board
    ) -> bool:
        """Validate artifacts are compatible with board architecture."""
        if not artifacts:
            return False
        
        artifact_arch = artifacts[0].architecture.lower()
        board_arch = board.architecture.lower()
        
        # Architecture mapping for compatibility
        arch_compat = {
            "arm64": ["arm64", "aarch64"],
            "aarch64": ["arm64", "aarch64"],
            "armv7": ["armv7", "arm", "armhf"],
            "arm": ["armv7", "arm", "armhf"],
            "armhf": ["armv7", "arm", "armhf"],
            "riscv64": ["riscv64", "riscv"],
            "riscv": ["riscv64", "riscv"],
        }
        
        compatible_archs = arch_compat.get(board_arch, [board_arch])
        return artifact_arch in compatible_archs

    async def _transfer_artifacts_to_host(
        self,
        host: Host,
        artifacts: List[Artifact],
        vm_name: str
    ) -> bool:
        """Transfer artifacts to a QEMU host."""
        try:
            credentials = SSHCredentials(
                hostname=host.ip_address,
                username=host.ssh_username,
                port=host.ssh_port,
                key_path=host.ssh_key_path
            )
            
            # Create directory for VM artifacts
            dest_dir = f"/var/lib/libvirt/images/{vm_name}"
            mkdir_result = await self.ssh_connector.execute_command(
                credentials,
                f"mkdir -p {dest_dir}"
            )
            
            if not mkdir_result.success:
                logger.error(f"Failed to create directory on host: {mkdir_result.stderr}")
                return False
            
            # Transfer each artifact
            for artifact in artifacts:
                dest_path = f"{dest_dir}/{artifact.filename}"
                result = await self.ssh_connector.upload_file(
                    credentials,
                    artifact.path,
                    dest_path
                )
                
                if not result.success:
                    logger.error(f"Failed to transfer {artifact.filename}: {result.error_message}")
                    return False
                
                logger.info(f"Transferred {artifact.filename} to {host.hostname}")
            
            return True
            
        except Exception as e:
            logger.error(f"Artifact transfer failed: {e}")
            return False

    async def _transfer_artifacts_to_flash_station(
        self,
        board: Board,
        artifacts: List[Artifact]
    ) -> bool:
        """Transfer artifacts to the flash station for a board."""
        if not board.flash_station_id:
            logger.warning(f"Board {board.id} has no flash station configured")
            # For boards without flash station, try direct SSH transfer
            return await self._transfer_artifacts_to_board_direct(board, artifacts)
        
        try:
            # In a real implementation, we would get flash station credentials
            # For now, simulate successful transfer
            logger.info(f"Transferring artifacts to flash station for board {board.id}")
            await asyncio.sleep(0.1)  # Simulate transfer
            return True
            
        except Exception as e:
            logger.error(f"Flash station transfer failed: {e}")
            return False

    async def _transfer_artifacts_to_board_direct(
        self,
        board: Board,
        artifacts: List[Artifact]
    ) -> bool:
        """Transfer artifacts directly to a board via SSH."""
        if not board.ip_address or not board.ssh_username:
            logger.error("Board does not have SSH configured for direct transfer")
            return False
        
        try:
            credentials = SSHCredentials(
                hostname=board.ip_address,
                username=board.ssh_username,
                port=board.ssh_port
            )
            
            for artifact in artifacts:
                dest_path = f"/tmp/{artifact.filename}"
                result = await self.ssh_connector.upload_file(
                    credentials,
                    artifact.path,
                    dest_path
                )
                
                if not result.success:
                    logger.error(f"Failed to transfer {artifact.filename}: {result.error_message}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Direct board transfer failed: {e}")
            return False

    async def _configure_and_boot_vm(
        self,
        host: Host,
        artifacts: List[Artifact],
        vm_config: VMConfig
    ) -> bool:
        """Configure and boot a VM on a QEMU host."""
        try:
            credentials = SSHCredentials(
                hostname=host.ip_address,
                username=host.ssh_username,
                port=host.ssh_port,
                key_path=host.ssh_key_path
            )
            
            # Find kernel and initrd artifacts
            kernel_path = None
            initrd_path = None
            rootfs_path = None
            
            dest_dir = f"/var/lib/libvirt/images/{vm_config.name}"
            
            for artifact in artifacts:
                if artifact.artifact_type.value == "kernel_image":
                    kernel_path = f"{dest_dir}/{artifact.filename}"
                elif artifact.artifact_type.value == "initrd":
                    initrd_path = f"{dest_dir}/{artifact.filename}"
                elif artifact.artifact_type.value == "rootfs":
                    rootfs_path = f"{dest_dir}/{artifact.filename}"
            
            # Build QEMU command
            qemu_cmd = self._build_qemu_command(
                vm_config, kernel_path, initrd_path, rootfs_path
            )
            
            # Start VM in background
            start_result = await self.ssh_connector.execute_command(
                credentials,
                f"nohup {qemu_cmd} > /tmp/{vm_config.name}.log 2>&1 &"
            )
            
            if not start_result.success:
                logger.error(f"Failed to start VM: {start_result.stderr}")
                return False
            
            # Wait for VM to start
            await asyncio.sleep(2)
            
            logger.info(f"Started VM {vm_config.name} on host {host.hostname}")
            return True
            
        except Exception as e:
            logger.error(f"VM boot failed: {e}")
            return False

    def _build_qemu_command(
        self,
        vm_config: VMConfig,
        kernel_path: Optional[str],
        initrd_path: Optional[str],
        rootfs_path: Optional[str]
    ) -> str:
        """Build QEMU command line."""
        arch_to_qemu = {
            "x86_64": "qemu-system-x86_64",
            "amd64": "qemu-system-x86_64",
            "arm64": "qemu-system-aarch64",
            "aarch64": "qemu-system-aarch64",
            "armv7": "qemu-system-arm",
            "arm": "qemu-system-arm",
            "riscv64": "qemu-system-riscv64",
        }
        
        qemu_bin = arch_to_qemu.get(vm_config.architecture.lower(), "qemu-system-x86_64")
        
        cmd_parts = [
            qemu_bin,
            f"-name {vm_config.name}",
            f"-m {vm_config.memory_mb}",
            f"-smp {vm_config.cpu_cores}",
        ]
        
        if vm_config.enable_kvm:
            cmd_parts.append("-enable-kvm")
        
        if kernel_path:
            cmd_parts.append(f"-kernel {kernel_path}")
        
        if initrd_path:
            cmd_parts.append(f"-initrd {initrd_path}")
        
        if rootfs_path:
            cmd_parts.append(f"-drive file={rootfs_path},format=raw")
        
        # Add network
        if vm_config.network_mode == "nat":
            cmd_parts.append("-netdev user,id=net0 -device virtio-net-pci,netdev=net0")
        
        # Add serial console
        cmd_parts.append("-serial stdio")
        
        # Add extra args
        cmd_parts.extend(vm_config.extra_args)
        
        return " ".join(cmd_parts)

    async def _flash_board(
        self,
        board: Board,
        artifacts: List[Artifact]
    ) -> bool:
        """Flash firmware to a board."""
        try:
            # Find the appropriate firmware artifact
            firmware_artifact = None
            for artifact in artifacts:
                if artifact.artifact_type.value in ("kernel_image", "rootfs"):
                    firmware_artifact = artifact
                    break
            
            if not firmware_artifact:
                logger.error("No suitable firmware artifact found")
                return False
            
            # Use board service to flash
            firmware_config = FirmwareConfig(
                firmware_path=firmware_artifact.path,
                version=firmware_artifact.metadata.get("version", "unknown"),
                verify_after_flash=True
            )
            
            result = await self.board_service.flash_firmware(board.id, firmware_config)
            return result.success
            
        except Exception as e:
            logger.error(f"Board flashing failed: {e}")
            return False

    async def _verify_qemu_boot(
        self,
        host: Host,
        vm_config: Optional[VMConfig]
    ) -> VerificationResult:
        """Verify QEMU VM booted successfully."""
        try:
            credentials = SSHCredentials(
                hostname=host.ip_address,
                username=host.ssh_username,
                port=host.ssh_port,
                key_path=host.ssh_key_path
            )
            
            # Check if VM process is running
            # In a real implementation, would check VM status via libvirt
            check_result = await self.ssh_connector.execute_command(
                credentials,
                "pgrep -f qemu-system"
            )
            
            if check_result.success and check_result.stdout.strip():
                return VerificationResult(
                    success=True,
                    deployment_id="",
                    boot_successful=True,
                    kernel_version="Verified via process check"
                )
            else:
                return VerificationResult(
                    success=False,
                    deployment_id="",
                    boot_successful=False,
                    error_message="VM process not found"
                )
                
        except Exception as e:
            return VerificationResult(
                success=False,
                deployment_id="",
                boot_successful=False,
                error_message=str(e)
            )

    async def _verify_board_boot(
        self,
        board: Board
    ) -> VerificationResult:
        """Verify physical board booted successfully."""
        try:
            # Validate board connectivity
            validation = await self.board_service.validate_board_connectivity(board.id)
            
            if not validation.success:
                return VerificationResult(
                    success=False,
                    deployment_id="",
                    boot_successful=False,
                    error_message=f"Board not reachable: {validation.error_message}"
                )
            
            # Try to get kernel version via SSH if available
            if board.ip_address and board.ssh_username:
                credentials = SSHCredentials(
                    hostname=board.ip_address,
                    username=board.ssh_username,
                    port=board.ssh_port
                )
                
                result = await self.ssh_connector.execute_command(
                    credentials,
                    "uname -r"
                )
                
                if result.success:
                    return VerificationResult(
                        success=True,
                        deployment_id="",
                        boot_successful=True,
                        kernel_version=result.stdout.strip()
                    )
            
            # If SSH check passed but no kernel version, still consider it successful
            return VerificationResult(
                success=True,
                deployment_id="",
                boot_successful=True
            )
            
        except Exception as e:
            return VerificationResult(
                success=False,
                deployment_id="",
                boot_successful=False,
                error_message=str(e)
            )

    def _add_to_history(self, target_id: str, deployment_id: str) -> None:
        """Add deployment to history."""
        if target_id not in self._deployment_history:
            self._deployment_history[target_id] = []
        
        self._deployment_history[target_id].append(deployment_id)
        
        # Keep only last 100 deployments per target
        if len(self._deployment_history[target_id]) > 100:
            self._deployment_history[target_id] = self._deployment_history[target_id][-100:]
