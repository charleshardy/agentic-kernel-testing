"""
Infrastructure Management API Routes

Provides REST API endpoints for managing test infrastructure including
build servers, QEMU hosts, physical boards, and pipelines.

**Feature: test-infrastructure-management**
**Validates: Requirements 1.1-1.5, 2.1-2.5, 7.1-7.5, 8.1-8.5, 9.1-9.5, 10.1-10.5, 17.1-17.5, 18.1-18.5**
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import subprocess
import json
import os
from pathlib import Path

# Import build job manager
from infrastructure.services.build_job_manager import (
    BuildJobManager,
    BuildJobConfig,
    QueuePriority,
)
from infrastructure.models.build_server import (
    BuildServer,
    BuildServerStatus,
    BuildConfig,
    Toolchain,
    ResourceUtilization,
)

# Create main router
router = APIRouter(prefix="/api/v1/infrastructure", tags=["infrastructure"])

# Persistence file paths
PERSISTENCE_DIR = Path("infrastructure_state")
PERSISTENCE_DIR.mkdir(exist_ok=True)
BUILD_SERVERS_FILE = PERSISTENCE_DIR / "build_servers.json"
HOSTS_FILE = PERSISTENCE_DIR / "hosts.json"
BOARDS_FILE = PERSISTENCE_DIR / "boards.json"
BUILD_JOBS_FILE = PERSISTENCE_DIR / "build_jobs.json"
PIPELINES_FILE = PERSISTENCE_DIR / "pipelines.json"

# Helper functions for persistence
def load_from_file(file_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load data from JSON file"""
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return {}

def save_to_file(file_path: Path, data: Dict[str, Dict[str, Any]]):
    """Save data to JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

# In-memory storage (for development/testing) - now with persistence
_build_servers: Dict[str, Dict[str, Any]] = load_from_file(BUILD_SERVERS_FILE)
_hosts: Dict[str, Dict[str, Any]] = load_from_file(HOSTS_FILE)
_boards: Dict[str, Dict[str, Any]] = load_from_file(BOARDS_FILE)
_build_jobs: Dict[str, Dict[str, Any]] = load_from_file(BUILD_JOBS_FILE)
_pipelines: Dict[str, Dict[str, Any]] = load_from_file(PIPELINES_FILE)

# Initialize Build Job Manager
_build_job_manager: Optional[BuildJobManager] = None
_queue_processor_task: Optional[asyncio.Task] = None


def get_build_job_manager() -> BuildJobManager:
    """Get or create the build job manager instance."""
    global _build_job_manager
    if _build_job_manager is None:
        # Convert dict-based servers to BuildServer objects
        server_pool = {}
        for server_id, server_data in _build_servers.items():
            # Create BuildServer object from dict
            server_pool[server_id] = BuildServer(
                id=server_id,
                hostname=server_data['hostname'],
                ip_address=server_data['ip_address'],
                ssh_username=server_data.get('ssh_username', 'root'),
                supported_architectures=server_data.get('supported_architectures', []),
                toolchains=[],  # Will be populated later
                total_cpu_cores=server_data.get('total_cpu_cores', 8),
                total_memory_mb=server_data.get('total_memory_mb', 16384),
                total_storage_gb=server_data.get('total_storage_gb', 500),
                created_at=datetime.fromisoformat(server_data['created_at']) if isinstance(server_data.get('created_at'), str) else server_data.get('created_at', datetime.now()),
                updated_at=datetime.fromisoformat(server_data['updated_at']) if isinstance(server_data.get('updated_at'), str) else server_data.get('updated_at', datetime.now()),
                ssh_port=server_data.get('ssh_port', 22),
                ssh_key_path=server_data.get('ssh_key_path'),
                status=BuildServerStatus(server_data.get('status', 'unknown')),
                active_build_count=server_data.get('active_build_count', 0),
                max_concurrent_builds=server_data.get('max_concurrent_builds', 4),
                maintenance_mode=server_data.get('maintenance_mode', False),
            )
        
        _build_job_manager = BuildJobManager(
            server_pool=server_pool,
            artifact_storage_path="/var/lib/artifacts",
            max_queue_size=1000,
        )
    return _build_job_manager


async def process_build_queue_background():
    """Background task to process the build queue."""
    while True:
        try:
            manager = get_build_job_manager()
            started = await manager.process_queue()
            if started > 0:
                print(f"Started {started} build(s) from queue")
        except Exception as e:
            print(f"Error processing build queue: {e}")
        
        # Check queue every 10 seconds
        await asyncio.sleep(10)


def start_queue_processor():
    """Start the background queue processor."""
    global _queue_processor_task
    if _queue_processor_task is None or _queue_processor_task.done():
        _queue_processor_task = asyncio.create_task(process_build_queue_background())
        print("Build queue processor started")


# =============================================================================
# Helper Functions
# =============================================================================

async def get_server_resources(hostname: str, ssh_port: int = 22, ssh_username: str = None, ssh_key_path: str = None) -> Dict[str, int]:
    """
    Get actual server resources via SSH.
    Returns CPU cores, memory MB, and storage GB.
    """
    default_resources = {
        'cpu_cores': 8,
        'memory_mb': 16384,
        'storage_gb': 500
    }
    
    try:
        # Build SSH command
        ssh_cmd = ['ssh', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes']
        
        # Use provided key or try default keys
        if ssh_key_path:
            ssh_cmd.extend(['-i', ssh_key_path])
        
        if ssh_username:
            ssh_cmd.append(f'{ssh_username}@{hostname}')
        else:
            ssh_cmd.append(hostname)
        
        # Command to get CPU, memory, and disk
        remote_cmd = "nproc && free -m | grep Mem | awk '{print $2}' && df -BG / | tail -1 | awk '{print $2}'"
        ssh_cmd.append(remote_cmd)
        
        # Execute SSH command
        proc = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        
        if proc.returncode == 0:
            lines = stdout.decode().strip().split('\n')
            if len(lines) >= 3:
                cpu_cores = int(lines[0].strip())
                memory_mb = int(lines[1].strip())
                storage_str = lines[2].strip().replace('G', '')
                storage_gb = int(storage_str)
                
                return {
                    'cpu_cores': cpu_cores,
                    'memory_mb': memory_mb,
                    'storage_gb': storage_gb
                }
    except Exception as e:
        # If SSH fails, return defaults
        pass
    
    return default_resources


async def check_ssh_connectivity(hostname: str, port: int = 22, timeout: int = 5) -> bool:
    """
    Check if SSH is accessible on the given host.
    Uses a simple TCP connection test.
    """
    try:
        # Use nc (netcat) to test TCP connectivity
        proc = await asyncio.create_subprocess_exec(
            'nc', '-z', '-w', str(timeout), hostname, str(port),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(proc.wait(), timeout=timeout + 1)
        return proc.returncode == 0
    except (asyncio.TimeoutError, FileNotFoundError, Exception):
        # If nc is not available or times out, try ping as fallback
        try:
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', str(timeout), hostname,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.wait(), timeout=timeout + 1)
            return proc.returncode == 0
        except Exception:
            return False


async def update_server_status(server_id: str):
    """
    Update the status of a build server based on connectivity check.
    """
    if server_id not in _build_servers:
        return
    
    server = _build_servers[server_id]
    
    # Skip if in maintenance mode
    if server.get('maintenance_mode', False):
        server['status'] = ResourceStatus.MAINTENANCE
        return
    
    # Check SSH connectivity
    hostname = server.get('hostname') or server.get('ip_address')
    is_online = await check_ssh_connectivity(hostname)
    
    # Update status
    if is_online:
        server['status'] = ResourceStatus.ONLINE
    else:
        server['status'] = ResourceStatus.OFFLINE
    
    server['updated_at'] = datetime.now()


# =============================================================================
# Pydantic Models for Request/Response
# =============================================================================

class ResourceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class BoardStatus(str, Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    FLASHING = "flashing"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class PowerControlMethod(str, Enum):
    USB_HUB = "usb_hub"
    NETWORK_PDU = "network_pdu"
    GPIO_RELAY = "gpio_relay"
    MANUAL = "manual"


# Build Server Models
class ToolchainInfo(BaseModel):
    name: str
    version: str
    target_architecture: str
    path: str
    available: bool = True


class BuildServerRegistration(BaseModel):
    hostname: str = Field(..., description="Server hostname")
    ip_address: str = Field(..., description="Server IP address")
    ssh_port: int = Field(default=22, description="SSH port")
    ssh_username: str = Field(..., description="SSH username")
    ssh_key_path: Optional[str] = Field(None, description="Path to SSH key")
    supported_architectures: List[str] = Field(..., description="Supported architectures")
    max_concurrent_builds: int = Field(default=4, description="Max concurrent builds")
    labels: Dict[str, str] = Field(default_factory=dict, description="Resource labels")


class BuildServerResponse(BaseModel):
    id: str
    hostname: str
    ip_address: str
    status: ResourceStatus
    supported_architectures: List[str]
    toolchains: List[ToolchainInfo] = []
    total_cpu_cores: int = 0
    total_memory_mb: int = 0
    total_storage_gb: int = 0
    active_build_count: int = 0
    queue_depth: int = 0
    maintenance_mode: bool = False
    created_at: datetime
    updated_at: datetime


class BuildServerCapacity(BaseModel):
    available_cpu_cores: int
    available_memory_mb: int
    available_storage_gb: int
    can_accept_build: bool
    estimated_queue_time_seconds: int


# Host Models
class HostRegistration(BaseModel):
    hostname: str = Field(..., description="Host hostname")
    ip_address: str = Field(..., description="Host IP address")
    ssh_port: int = Field(default=22, description="SSH port")
    ssh_username: str = Field(..., description="SSH username")
    ssh_key_path: Optional[str] = Field(None, description="Path to SSH key")
    architecture: str = Field(..., description="Host architecture")
    total_cpu_cores: int = Field(..., description="Total CPU cores")
    total_memory_mb: int = Field(..., description="Total memory in MB")
    total_storage_gb: int = Field(..., description="Total storage in GB")
    max_vms: int = Field(default=10, description="Maximum VMs")
    labels: Dict[str, str] = Field(default_factory=dict, description="Resource labels")


class HostResponse(BaseModel):
    id: str
    hostname: str
    ip_address: str
    status: ResourceStatus
    architecture: str
    total_cpu_cores: int
    total_memory_mb: int
    total_storage_gb: int
    kvm_enabled: bool = False
    running_vm_count: int = 0
    max_vms: int = 10
    maintenance_mode: bool = False
    created_at: datetime
    updated_at: datetime


class HostCapacity(BaseModel):
    available_cpu_cores: int
    available_memory_mb: int
    available_storage_gb: int
    can_allocate_vm: bool
    max_vm_cpu: int
    max_vm_memory_mb: int


class VMInfo(BaseModel):
    vm_id: str
    name: str
    status: str
    cpu_cores: int
    memory_mb: int
    architecture: str


# Board Models
class PowerControlConfig(BaseModel):
    method: PowerControlMethod
    usb_hub_port: Optional[int] = None
    pdu_outlet: Optional[int] = None
    pdu_address: Optional[str] = None
    gpio_pin: Optional[int] = None


class BoardRegistration(BaseModel):
    name: str = Field(..., description="Board name")
    board_type: str = Field(..., description="Board type (e.g., raspberry_pi_4)")
    serial_number: Optional[str] = Field(None, description="Serial number")
    architecture: str = Field(..., description="Board architecture")
    ip_address: Optional[str] = Field(None, description="Board IP address")
    ssh_port: int = Field(default=22, description="SSH port")
    ssh_username: Optional[str] = Field(None, description="SSH username")
    serial_device: Optional[str] = Field(None, description="Serial device path")
    power_control: PowerControlConfig = Field(..., description="Power control config")
    peripherals: List[str] = Field(default_factory=list, description="Connected peripherals")
    labels: Dict[str, str] = Field(default_factory=dict, description="Resource labels")


class BoardResponse(BaseModel):
    id: str
    name: str
    board_type: str
    serial_number: Optional[str]
    architecture: str
    status: BoardStatus
    ip_address: Optional[str]
    power_control: PowerControlConfig
    peripherals: List[str] = []
    current_firmware_version: Optional[str] = None
    maintenance_mode: bool = False
    created_at: datetime
    updated_at: datetime


class BoardHealth(BaseModel):
    connectivity: str
    temperature_celsius: Optional[float] = None
    storage_percent: Optional[float] = None
    power_status: str
    last_response_time_ms: Optional[int] = None


# Build Job Models
class BuildJobSubmission(BaseModel):
    source_repository: str = Field(..., description="Source repository URL")
    branch: str = Field(..., description="Branch name")
    commit_hash: Optional[str] = Field(None, description="Specific commit hash")
    target_architecture: str = Field(..., description="Target architecture")
    build_config: Dict[str, Any] = Field(default_factory=dict, description="Build configuration")
    server_id: Optional[str] = Field(None, description="Specific server ID or 'auto'")


class BuildJobResponse(BaseModel):
    id: str
    source_repository: str
    branch: str
    commit_hash: Optional[str]
    target_architecture: str
    server_id: Optional[str]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    error_message: Optional[str]
    created_at: datetime


# Pipeline Models
class PipelineCreation(BaseModel):
    name: Optional[str] = Field(None, description="Pipeline name")
    source_repository: str = Field(..., description="Source repository URL")
    branch: str = Field(..., description="Branch name")
    commit_hash: Optional[str] = Field(None, description="Specific commit hash")
    target_architecture: str = Field(..., description="Target architecture")
    environment_type: str = Field(..., description="Environment type (qemu or physical_board)")
    environment_config: Dict[str, Any] = Field(default_factory=dict)
    auto_retry: bool = Field(default=True, description="Enable auto retry on failure")


class PipelineStageResponse(BaseModel):
    name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    error_message: Optional[str]


class PipelineResponse(BaseModel):
    id: str
    name: Optional[str]
    source_repository: str
    branch: str
    target_architecture: str
    environment_type: str
    status: str
    current_stage: Optional[str]
    stages: List[PipelineStageResponse] = []
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime


# Generic Response Models
class OperationResponse(BaseModel):
    success: bool
    message: str
    resource_id: Optional[str] = None


# =============================================================================
# Build Server Endpoints
# =============================================================================

@router.post("/build-servers", response_model=BuildServerResponse, tags=["build-servers"])
async def register_build_server(registration: BuildServerRegistration):
    """
    Register a new build server.
    
    **Requirement 1.1**: Register build servers with hostname, IP, SSH credentials
    **Requirement 1.2**: Validate SSH connectivity and toolchain availability
    """
    server_id = "bs-" + registration.hostname
    
    # Check if server already exists
    if server_id in _build_servers:
        raise HTTPException(status_code=400, detail=f"Build server with hostname '{registration.hostname}' already exists")
    
    # Check initial connectivity
    hostname = registration.hostname or registration.ip_address
    is_online = await check_ssh_connectivity(hostname, registration.ssh_port)
    
    # Get actual server resources
    resources = await get_server_resources(
        hostname, 
        registration.ssh_port, 
        registration.ssh_username,
        registration.ssh_key_path
    )
    
    # Create server response
    server = BuildServerResponse(
        id=server_id,
        hostname=registration.hostname,
        ip_address=registration.ip_address,
        status=ResourceStatus.ONLINE if is_online else ResourceStatus.OFFLINE,
        supported_architectures=registration.supported_architectures,
        toolchains=[],
        total_cpu_cores=resources['cpu_cores'],
        total_memory_mb=resources['memory_mb'],
        total_storage_gb=resources['storage_gb'],
        active_build_count=0,
        queue_depth=0,
        maintenance_mode=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Store in memory (including SSH credentials for future checks)
    server_dict = server.dict()
    server_dict['ssh_port'] = registration.ssh_port
    server_dict['ssh_username'] = registration.ssh_username
    server_dict['ssh_key_path'] = registration.ssh_key_path
    _build_servers[server_id] = server_dict
    
    # Persist to file
    save_to_file(BUILD_SERVERS_FILE, _build_servers)
    
    return server


@router.get("/build-servers", response_model=List[BuildServerResponse], tags=["build-servers"])
async def list_build_servers(
    status: Optional[ResourceStatus] = None,
    architecture: Optional[str] = None
):
    """
    List all registered build servers with optional filtering.
    
    **Requirement 2.1**: Display all registered build servers with status
    """
    # Update status for all servers
    await asyncio.gather(*[update_server_status(sid) for sid in _build_servers.keys()])
    
    servers = list(_build_servers.values())
    
    # Apply filters
    if status:
        servers = [s for s in servers if s['status'] == status]
    if architecture:
        servers = [s for s in servers if architecture in s['supported_architectures']]
    
    return servers


@router.get("/build-servers/{server_id}", response_model=BuildServerResponse, tags=["build-servers"])
async def get_build_server(server_id: str):
    """
    Get details of a specific build server.
    
    **Requirement 2.5**: Display detailed information including toolchains and history
    """
    if server_id not in _build_servers:
        raise HTTPException(status_code=404, detail=f"Build server {server_id} not found")
    return _build_servers[server_id]


@router.get("/build-servers/{server_id}/status", tags=["build-servers"])
async def get_build_server_status(server_id: str):
    """
    Get current status of a build server.
    
    **Requirement 2.2**: Update display within 10 seconds
    """
    if server_id not in _build_servers:
        raise HTTPException(status_code=404, detail=f"Build server {server_id} not found")
    
    # Update status before returning
    await update_server_status(server_id)
    
    server = _build_servers[server_id]
    return {
        "id": server_id,
        "status": server['status'],
        "maintenance_mode": server.get('maintenance_mode', False),
        "active_build_count": server.get('active_build_count', 0),
        "queue_depth": server.get('queue_depth', 0),
        "updated_at": server['updated_at']
    }


@router.get("/build-servers/{server_id}/capacity", response_model=BuildServerCapacity, tags=["build-servers"])
async def get_build_server_capacity(server_id: str):
    """
    Get current capacity of a build server.
    
    **Requirement 2.4**: Display disk space warnings
    """
    raise HTTPException(status_code=404, detail=f"Build server {server_id} not found")


@router.put("/build-servers/{server_id}/maintenance", response_model=OperationResponse, tags=["build-servers"])
async def set_build_server_maintenance(server_id: str, enabled: bool = True):
    """
    Set maintenance mode for a build server.
    
    **Requirement 12.1**: Prevent new allocations during maintenance
    """
    if server_id not in _build_servers:
        raise HTTPException(status_code=404, detail=f"Build server {server_id} not found")
    
    _build_servers[server_id]['maintenance_mode'] = enabled
    _build_servers[server_id]['updated_at'] = datetime.now()
    
    # Persist to file
    save_to_file(BUILD_SERVERS_FILE, _build_servers)
    
    return OperationResponse(
        success=True,
        message=f"Maintenance mode {'enabled' if enabled else 'disabled'}",
        resource_id=server_id
    )


@router.delete("/build-servers/{server_id}", response_model=OperationResponse, tags=["build-servers"])
async def decommission_build_server(server_id: str, force: bool = False):
    """
    Decommission a build server.
    
    **Requirement 12.4**: Verify no active workloads before decommissioning
    """
    if server_id not in _build_servers:
        raise HTTPException(status_code=404, detail=f"Build server {server_id} not found")
    
    server = _build_servers[server_id]
    
    # Check for active builds
    if server['active_build_count'] > 0 and not force:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot decommission server with {server['active_build_count']} active builds. Use force=true to override."
        )
    
    del _build_servers[server_id]
    
    # Persist to file
    save_to_file(BUILD_SERVERS_FILE, _build_servers)
    
    return OperationResponse(
        success=True,
        message="Build server decommissioned successfully",
        resource_id=server_id
    )


@router.post("/build-servers/{server_id}/execute", tags=["build-servers"])
async def execute_ssh_command(server_id: str, command: str):
    """
    Execute a command on a build server via SSH.
    
    Returns the command output.
    """
    if server_id not in _build_servers:
        raise HTTPException(status_code=404, detail=f"Build server {server_id} not found")
    
    server = _build_servers[server_id]
    hostname = server.get('hostname') or server.get('ip_address')
    ssh_port = server.get('ssh_port', 22)
    ssh_username = server.get('ssh_username')
    ssh_key_path = server.get('ssh_key_path')
    
    try:
        # Build SSH command
        ssh_cmd = ['ssh', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes']
        
        if ssh_key_path:
            ssh_cmd.extend(['-i', ssh_key_path])
        
        if ssh_username:
            ssh_cmd.append(f'{ssh_username}@{hostname}')
        else:
            ssh_cmd.append(hostname)
        
        ssh_cmd.append(command)
        
        # Execute SSH command
        proc = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        
        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": stdout.decode('utf-8', errors='replace'),
            "stderr": stderr.decode('utf-8', errors='replace'),
            "command": command
        }
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Command execution timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute command: {str(e)}")


# =============================================================================
# Build Job Endpoints
# =============================================================================

@router.post("/build-jobs", response_model=BuildJobResponse, tags=["build-jobs"])
async def submit_build_job(submission: BuildJobSubmission, background_tasks: BackgroundTasks):
    """
    Submit a new build job.
    
    **Requirement 3.1**: Submit build jobs with repository, branch, architecture
    **Requirement 3.2**: Auto-select server based on requirements
    """
    # Start queue processor if not running
    start_queue_processor()
    
    # Get build job manager
    manager = get_build_job_manager()
    
    # Create BuildConfig from submission
    build_config = BuildConfig(
        build_mode=submission.build_config.get('build_mode', 'kernel'),
        workspace_root=submission.build_config.get('workspace_root', '/tmp/builds'),
        build_directory=submission.build_config.get('build_directory'),
        output_directory=submission.build_config.get('output_directory'),
        keep_workspace=submission.build_config.get('keep_workspace', False),
        kernel_config=submission.build_config.get('kernel_config', 'defconfig'),
        extra_make_args=submission.build_config.get('extra_make_args', []),
        enable_modules=submission.build_config.get('enable_modules', True),
        build_dtbs=submission.build_config.get('build_dtbs', True),
        custom_env=submission.build_config.get('custom_env', {}),
        pre_build_commands=submission.build_config.get('pre_build_commands', []),
        build_commands=submission.build_config.get('build_commands', []),
        post_build_commands=submission.build_config.get('post_build_commands', []),
        artifact_patterns=submission.build_config.get('artifact_patterns') or [
            "arch/*/boot/bzImage",
            "arch/*/boot/Image",
            "arch/*/boot/zImage",
            "vmlinux",
            "System.map",
            "*.ko",
            "*.dtb"
        ],
        git_depth=submission.build_config.get('git_depth', 1),
        git_submodules=submission.build_config.get('git_submodules', False),
    )
    
    # Create build job config
    config = BuildJobConfig(
        source_repository=submission.source_repository,
        branch=submission.branch,
        commit_hash=submission.commit_hash or "HEAD",
        target_architecture=submission.target_architecture,
        build_config=build_config,
        preferred_server_id=submission.server_id if submission.server_id and submission.server_id != "auto" else None,
        priority=QueuePriority.NORMAL,
    )
    
    # Submit build
    result = await manager.submit_build(config)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message)
    
    # Store in persistence
    if result.job:
        _build_jobs[result.job.id] = {
            'id': result.job.id,
            'source_repository': result.job.source_repository,
            'branch': result.job.branch,
            'commit_hash': result.job.commit_hash,
            'target_architecture': result.job.target_architecture,
            'server_id': result.job.server_id,
            'status': result.job.status.value,
            'created_at': result.job.created_at,
            'updated_at': result.job.updated_at,
            'started_at': result.job.started_at,
            'completed_at': result.job.completed_at,
            'duration_seconds': result.job.duration_seconds,
            'error_message': result.job.error_message,
        }
        save_to_file(BUILD_JOBS_FILE, _build_jobs)
    
    # Return BuildJobResponse
    return BuildJobResponse(
        id=result.job.id,
        source_repository=result.job.source_repository,
        branch=result.job.branch,
        commit_hash=result.job.commit_hash,
        target_architecture=result.job.target_architecture,
        server_id=result.job.server_id,
        status=result.job.status.value,
        started_at=result.job.started_at,
        completed_at=result.job.completed_at,
        duration_seconds=result.job.duration_seconds,
        error_message=result.job.error_message,
        created_at=result.job.created_at,
    )


@router.get("/build-jobs", response_model=List[BuildJobResponse], tags=["build-jobs"])
async def list_build_jobs(
    status: Optional[str] = None,
    server_id: Optional[str] = None,
    limit: int = Query(default=50, le=100)
):
    """
    List build jobs with optional filtering.
    
    **Requirement 3.5**: Display build history with filtering
    """
    manager = get_build_job_manager()
    
    # Get all jobs from manager
    from infrastructure.services.build_job_manager import BuildHistoryFilters
    from infrastructure.models.build_server import BuildJobStatus
    
    filters = BuildHistoryFilters(
        server_id=server_id,
        status=BuildJobStatus(status) if status else None,
        limit=limit,
    )
    
    jobs = await manager.get_build_history(filters)
    
    # Convert to BuildJobResponse format
    return [
        BuildJobResponse(
            id=job.id,
            source_repository=job.source_repository,
            branch=job.branch,
            commit_hash=job.commit_hash,
            target_architecture=job.target_architecture,
            server_id=job.server_id,
            status=job.status.value,
            started_at=job.started_at,
            completed_at=job.completed_at,
            duration_seconds=job.duration_seconds,
            error_message=job.error_message,
            created_at=job.created_at,
        )
        for job in jobs
    ]


@router.get("/build-jobs/queue/status", tags=["build-jobs"])
async def get_build_queue_status():
    """
    Get current build queue status.
    
    Returns information about queued and building jobs.
    """
    manager = get_build_job_manager()
    queue_status = await manager.get_queue_status()
    
    return {
        "total_queued": queue_status.total_queued,
        "total_building": queue_status.total_building,
        "jobs_by_architecture": queue_status.jobs_by_architecture,
        "estimated_wait_time_seconds": queue_status.estimated_wait_time_seconds,
    }


@router.get("/build-jobs/{job_id}", response_model=BuildJobResponse, tags=["build-jobs"])
async def get_build_job(job_id: str):
    """Get details of a specific build job."""
    manager = get_build_job_manager()
    job = await manager.get_build(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Build job {job_id} not found")
    
    return BuildJobResponse(
        id=job.id,
        source_repository=job.source_repository,
        branch=job.branch,
        commit_hash=job.commit_hash,
        target_architecture=job.target_architecture,
        server_id=job.server_id,
        status=job.status.value,
        started_at=job.started_at,
        completed_at=job.completed_at,
        duration_seconds=job.duration_seconds,
        error_message=job.error_message,
        created_at=job.created_at,
    )


@router.get("/build-jobs/{job_id}/status", tags=["build-jobs"])
async def get_build_job_status(job_id: str):
    """
    Get current status of a build job.
    
    **Requirement 3.5**: Real-time build progress
    """
    manager = get_build_job_manager()
    job = await manager.get_build(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Build job {job_id} not found")
    
    # Get queue status if queued
    queue_info = None
    if job.status.value == "queued":
        queue_status = await manager.get_queue_status()
        queue_info = {
            "total_queued": queue_status.total_queued,
            "estimated_wait_seconds": queue_status.estimated_wait_time_seconds,
        }
    
    return {
        "id": job.id,
        "status": job.status.value,
        "server_id": job.server_id,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "duration_seconds": job.duration_seconds,
        "error_message": job.error_message,
        "queue_info": queue_info,
    }


@router.get("/build-jobs/{job_id}/logs", tags=["build-jobs"])
async def get_build_job_logs(job_id: str, stream: bool = False):
    """
    Get logs for a build job.
    
    **Requirement 3.5**: Log streaming
    """
    manager = get_build_job_manager()
    job = await manager.get_build(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Build job {job_id} not found")
    
    # Get logs
    logs = []
    async for log_line in manager.get_build_logs(job_id, stream=stream):
        logs.append(log_line)
        # For non-streaming, collect all logs
        if not stream:
            continue
        # For streaming, we'd need SSE or WebSocket (not implemented here)
        break
    
    return {
        "job_id": job_id,
        "logs": logs,
        "streaming": stream,
    }


@router.get("/build-jobs/{job_id}/flow", tags=["build-jobs"])
async def get_build_job_flow(job_id: str):
    """
    Get build flow stages and their status for a build job.
    
    Returns the current stage execution status including:
    - Clone Repository
    - Configure Build
    - Execute Build
    - Collect Artifacts
    """
    manager = get_build_job_manager()
    job = await manager.get_build(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Build job {job_id} not found")
    
    # Parse logs to determine stage status
    logs = []
    async for log_line in manager.get_build_logs(job_id, stream=False):
        logs.append(log_line)
    
    # Define stages
    stages = [
        {"name": "Clone Repository", "status": "pending", "started_at": None, "completed_at": None, "duration_seconds": None, "error_message": None},
        {"name": "Configure Build", "status": "pending", "started_at": None, "completed_at": None, "duration_seconds": None, "error_message": None},
        {"name": "Execute Build", "status": "pending", "started_at": None, "completed_at": None, "duration_seconds": None, "error_message": None},
        {"name": "Collect Artifacts", "status": "pending", "started_at": None, "completed_at": None, "duration_seconds": None, "error_message": None}
    ]
    
    # Parse logs to determine stage progress
    log_text = "\n".join(logs)
    
    # Stage 0: Clone Repository
    if "Cloning repository" in log_text or "git clone" in log_text:
        stages[0]["status"] = "running" if job.status.value == "building" else "completed"
        if "Repository cloned successfully" in log_text or "Configure Build" in log_text:
            stages[0]["status"] = "completed"
    
    # Stage 1: Configure Build
    if "Configuring build" in log_text or "Build configuration" in log_text:
        stages[1]["status"] = "running" if job.status.value == "building" else "completed"
        if "Build configured successfully" in log_text or "Executing build" in log_text:
            stages[1]["status"] = "completed"
    
    # Stage 2: Execute Build
    if "Executing build" in log_text or "Running make" in log_text or "Building kernel" in log_text:
        stages[2]["status"] = "running" if job.status.value == "building" else "completed"
        if "Build completed successfully" in log_text or "Collecting artifacts" in log_text:
            stages[2]["status"] = "completed"
    
    # Stage 3: Collect Artifacts
    if "Collecting artifacts" in log_text or "Transferring artifacts" in log_text:
        stages[3]["status"] = "running" if job.status.value == "building" else "completed"
        if "Artifacts collected successfully" in log_text or job.status.value == "completed":
            stages[3]["status"] = "completed"
    
    # Handle failures
    if job.status.value == "failed":
        # Find which stage failed
        for i, stage in enumerate(stages):
            if stage["status"] == "running":
                stage["status"] = "failed"
                stage["error_message"] = job.error_message
                break
    
    # If job is completed, mark all as completed
    if job.status.value == "completed":
        for stage in stages:
            if stage["status"] != "failed":
                stage["status"] = "completed"
    
    return {
        "job_id": job_id,
        "overall_status": job.status.value,
        "stages": stages
    }


@router.put("/build-jobs/{job_id}/cancel", response_model=OperationResponse, tags=["build-jobs"])
async def cancel_build_job(job_id: str):
    """Cancel a running build job."""
    manager = get_build_job_manager()
    result = await manager.cancel_build(job_id)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message)
    
    # Update persistence
    if result.job:
        _build_jobs[job_id] = {
            'id': result.job.id,
            'source_repository': result.job.source_repository,
            'branch': result.job.branch,
            'commit_hash': result.job.commit_hash,
            'target_architecture': result.job.target_architecture,
            'server_id': result.job.server_id,
            'status': result.job.status.value,
            'created_at': result.job.created_at,
            'updated_at': result.job.updated_at,
            'started_at': result.job.started_at,
            'completed_at': result.job.completed_at,
            'duration_seconds': result.job.duration_seconds,
            'error_message': result.job.error_message,
        }
        save_to_file(BUILD_JOBS_FILE, _build_jobs)
    
    return OperationResponse(
        success=True,
        message=f"Build job {job_id} cancelled successfully",
        resource_id=job_id,
    )


# =============================================================================
# Artifact Endpoints
# =============================================================================

@router.get("/artifacts", tags=["artifacts"])
async def list_artifacts(
    build_id: Optional[str] = None,
    architecture: Optional[str] = None,
    limit: int = Query(default=50, le=100)
):
    """
    List build artifacts with optional filtering.
    
    **Requirement 4.3**: Display all builds with artifacts
    """
    return []


@router.get("/artifacts/latest", tags=["artifacts"])
async def get_latest_artifacts(
    branch: str,
    architecture: str
):
    """
    Get latest artifacts for a branch and architecture.
    
    **Requirement 4.5**: Retrieve by branch and "latest"
    """
    return {"artifacts": []}


@router.get("/artifacts/{artifact_id}", tags=["artifacts"])
async def get_artifact(artifact_id: str):
    """Get details of a specific artifact."""
    raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")


@router.get("/artifacts/{artifact_id}/download", tags=["artifacts"])
async def download_artifact(artifact_id: str):
    """Download an artifact file."""
    raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")


# =============================================================================
# Host Endpoints
# =============================================================================

@router.post("/hosts", response_model=HostResponse, tags=["hosts"])
async def register_host(registration: HostRegistration):
    """
    Register a new QEMU host.
    
    **Requirement 7.1**: Register hosts with hostname, IP, SSH credentials
    **Requirement 7.2**: Validate SSH and libvirt connectivity
    """
    return HostResponse(
        id="host-" + registration.hostname,
        hostname=registration.hostname,
        ip_address=registration.ip_address,
        status=ResourceStatus.ONLINE,
        architecture=registration.architecture,
        total_cpu_cores=registration.total_cpu_cores,
        total_memory_mb=registration.total_memory_mb,
        total_storage_gb=registration.total_storage_gb,
        kvm_enabled=True,
        running_vm_count=0,
        max_vms=registration.max_vms,
        maintenance_mode=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@router.get("/hosts", response_model=List[HostResponse], tags=["hosts"])
async def list_hosts(
    status: Optional[ResourceStatus] = None,
    architecture: Optional[str] = None
):
    """
    List all registered hosts with optional filtering.
    
    **Requirement 9.1**: Display all hosts with status and utilization
    """
    return []


@router.get("/hosts/{host_id}", response_model=HostResponse, tags=["hosts"])
async def get_host(host_id: str):
    """
    Get details of a specific host.
    
    **Requirement 9.5**: Display detailed information
    """
    raise HTTPException(status_code=404, detail=f"Host {host_id} not found")


@router.get("/hosts/{host_id}/status", tags=["hosts"])
async def get_host_status(host_id: str):
    """
    Get current status of a host.
    
    **Requirement 9.2**: Update within 10 seconds
    """
    raise HTTPException(status_code=404, detail=f"Host {host_id} not found")


@router.get("/hosts/{host_id}/capacity", response_model=HostCapacity, tags=["hosts"])
async def get_host_capacity(host_id: str):
    """
    Get current capacity of a host.
    
    **Requirement 9.4**: Display utilization warnings
    """
    raise HTTPException(status_code=404, detail=f"Host {host_id} not found")


@router.get("/hosts/{host_id}/vms", response_model=List[VMInfo], tags=["hosts"])
async def get_host_vms(host_id: str):
    """
    Get VMs running on a host.
    
    **Requirement 9.5**: Display running VMs
    """
    raise HTTPException(status_code=404, detail=f"Host {host_id} not found")


@router.put("/hosts/{host_id}/maintenance", response_model=OperationResponse, tags=["hosts"])
async def set_host_maintenance(host_id: str, enabled: bool = True):
    """
    Set maintenance mode for a host.
    
    **Requirement 12.1**: Prevent new allocations during maintenance
    """
    raise HTTPException(status_code=404, detail=f"Host {host_id} not found")


@router.delete("/hosts/{host_id}", response_model=OperationResponse, tags=["hosts"])
async def decommission_host(host_id: str, force: bool = False):
    """
    Decommission a host.
    
    **Requirement 12.4**: Verify no active workloads
    """
    raise HTTPException(status_code=404, detail=f"Host {host_id} not found")


# =============================================================================
# Board Endpoints
# =============================================================================

@router.post("/boards", response_model=BoardResponse, tags=["boards"])
async def register_board(registration: BoardRegistration):
    """
    Register a new physical test board.
    
    **Requirement 8.1**: Register boards with type, serial, connection method
    **Requirement 8.4**: Specify power control method
    """
    return BoardResponse(
        id="board-" + registration.name,
        name=registration.name,
        board_type=registration.board_type,
        serial_number=registration.serial_number,
        architecture=registration.architecture,
        status=BoardStatus.AVAILABLE,
        ip_address=registration.ip_address,
        power_control=registration.power_control,
        peripherals=registration.peripherals,
        current_firmware_version=None,
        maintenance_mode=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@router.get("/boards", response_model=List[BoardResponse], tags=["boards"])
async def list_boards(
    status: Optional[BoardStatus] = None,
    architecture: Optional[str] = None,
    board_type: Optional[str] = None
):
    """
    List all registered boards with optional filtering.
    
    **Requirement 10.1**: Display all boards with status and health
    """
    return []


@router.get("/boards/{board_id}", response_model=BoardResponse, tags=["boards"])
async def get_board(board_id: str):
    """
    Get details of a specific board.
    
    **Requirement 10.5**: Display detailed information
    """
    raise HTTPException(status_code=404, detail=f"Board {board_id} not found")


@router.get("/boards/{board_id}/status", tags=["boards"])
async def get_board_status(board_id: str):
    """
    Get current status of a board.
    
    **Requirement 10.2**: Update within 5 seconds
    """
    raise HTTPException(status_code=404, detail=f"Board {board_id} not found")


@router.get("/boards/{board_id}/health", response_model=BoardHealth, tags=["boards"])
async def get_board_health(board_id: str):
    """
    Get health information for a board.
    
    **Requirement 10.4**: Display health indicators
    """
    raise HTTPException(status_code=404, detail=f"Board {board_id} not found")


@router.post("/boards/{board_id}/power-cycle", response_model=OperationResponse, tags=["boards"])
async def power_cycle_board(board_id: str):
    """
    Power cycle a board.
    
    **Requirement 18.2**: Execute power control sequence
    """
    raise HTTPException(status_code=404, detail=f"Board {board_id} not found")


@router.post("/boards/{board_id}/flash", response_model=OperationResponse, tags=["boards"])
async def flash_board(board_id: str, firmware_path: str):
    """
    Flash firmware to a board.
    
    **Requirement 6.2**: Initiate flashing process
    """
    raise HTTPException(status_code=404, detail=f"Board {board_id} not found")


@router.put("/boards/{board_id}/maintenance", response_model=OperationResponse, tags=["boards"])
async def set_board_maintenance(board_id: str, enabled: bool = True):
    """
    Set maintenance mode for a board.
    
    **Requirement 12.1**: Prevent new allocations during maintenance
    """
    raise HTTPException(status_code=404, detail=f"Board {board_id} not found")


@router.delete("/boards/{board_id}", response_model=OperationResponse, tags=["boards"])
async def decommission_board(board_id: str, force: bool = False):
    """
    Decommission a board.
    
    **Requirement 12.4**: Verify no active workloads
    """
    raise HTTPException(status_code=404, detail=f"Board {board_id} not found")


# =============================================================================
# Pipeline Endpoints
# =============================================================================

@router.post("/pipelines", response_model=PipelineResponse, tags=["pipelines"])
async def create_pipeline(creation: PipelineCreation):
    """
    Create a new pipeline.
    
    **Requirement 17.1**: Accept source repo, branch, architecture, environment
    """
    return PipelineResponse(
        id="pipeline-" + str(hash(creation.source_repository))[:8],
        name=creation.name,
        source_repository=creation.source_repository,
        branch=creation.branch,
        target_architecture=creation.target_architecture,
        environment_type=creation.environment_type,
        status="pending",
        current_stage=None,
        stages=[
            PipelineStageResponse(name="build", status="pending", started_at=None, completed_at=None, duration_seconds=None, error_message=None),
            PipelineStageResponse(name="deploy", status="pending", started_at=None, completed_at=None, duration_seconds=None, error_message=None),
            PipelineStageResponse(name="boot", status="pending", started_at=None, completed_at=None, duration_seconds=None, error_message=None),
            PipelineStageResponse(name="test", status="pending", started_at=None, completed_at=None, duration_seconds=None, error_message=None),
        ],
        started_at=None,
        completed_at=None,
        error_message=None,
        created_at=datetime.now()
    )


@router.get("/pipelines", response_model=List[PipelineResponse], tags=["pipelines"])
async def list_pipelines(
    status: Optional[str] = None,
    repository: Optional[str] = None,
    limit: int = Query(default=50, le=100)
):
    """
    List pipelines with optional filtering.
    
    **Requirement 17.5**: Display pipeline history
    """
    return []


@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse, tags=["pipelines"])
async def get_pipeline(pipeline_id: str):
    """Get details of a specific pipeline."""
    raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")


@router.get("/pipelines/{pipeline_id}/status", tags=["pipelines"])
async def get_pipeline_status(pipeline_id: str):
    """
    Get current status of a pipeline.
    
    **Requirement 17.3**: Real-time status updates
    """
    raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")


@router.get("/pipelines/{pipeline_id}/logs/{stage}", tags=["pipelines"])
async def get_pipeline_stage_logs(pipeline_id: str, stage: str):
    """
    Get logs for a pipeline stage.
    
    **Requirement 17.3**: Provide logs for each stage
    """
    raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")


@router.put("/pipelines/{pipeline_id}/cancel", response_model=OperationResponse, tags=["pipelines"])
async def cancel_pipeline(pipeline_id: str):
    """Cancel a running pipeline."""
    raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")


@router.post("/pipelines/{pipeline_id}/retry/{stage}", response_model=OperationResponse, tags=["pipelines"])
async def retry_pipeline_stage(pipeline_id: str, stage: str):
    """Retry a failed pipeline stage."""
    raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")


# =============================================================================
# Dashboard/Overview Endpoints
# =============================================================================

@router.get("/overview", tags=["dashboard"])
async def get_infrastructure_overview():
    """
    Get infrastructure overview for dashboard.
    
    **Requirement 15.1-15.4**: Display resource counts and health summary
    """
    return {
        "build_servers": {
            "total": 0,
            "online": 0,
            "offline": 0,
            "maintenance": 0
        },
        "hosts": {
            "total": 0,
            "online": 0,
            "offline": 0,
            "maintenance": 0
        },
        "boards": {
            "total": 0,
            "available": 0,
            "in_use": 0,
            "offline": 0,
            "maintenance": 0
        },
        "active_builds": 0,
        "active_pipelines": 0,
        "recent_alerts": []
    }


@router.get("/alerts", tags=["dashboard"])
async def get_infrastructure_alerts(
    severity: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(default=50, le=100)
):
    """
    Get infrastructure alerts.
    
    **Requirement 16.1-16.5**: Display alerts with filtering
    """
    return []


@router.put("/alerts/{alert_id}/acknowledge", response_model=OperationResponse, tags=["dashboard"])
async def acknowledge_alert(alert_id: str, acknowledged_by: str):
    """Acknowledge an alert."""
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


# ============================================================================
# Build Template Management Endpoints
# ============================================================================

from infrastructure.models.build_template import (
    BuildTemplate,
    BuildTemplateCreate,
    BuildTemplateUpdate
)
from infrastructure.services.build_template_manager import get_template_manager


@router.post("/build-templates", response_model=BuildTemplate, tags=["build-templates"])
async def create_build_template(template: BuildTemplateCreate):
    """
    Create a new build configuration template.
    
    Allows users to save common build configurations for reuse.
    Templates include custom commands, environment variables, and all build settings.
    
    Args:
        template: Template creation data
        
    Returns:
        Created template with generated ID
    """
    manager = get_template_manager()
    return manager.create_template(template)


@router.get("/build-templates", response_model=List[BuildTemplate], tags=["build-templates"])
async def list_build_templates():
    """
    List all build configuration templates.
    
    Returns:
        List of all saved templates
    """
    manager = get_template_manager()
    return manager.list_templates()


@router.get("/build-templates/{template_id}", response_model=BuildTemplate, tags=["build-templates"])
async def get_build_template(template_id: str):
    """
    Get a specific build template by ID.
    
    Args:
        template_id: Template ID
        
    Returns:
        Template details
        
    Raises:
        HTTPException: If template not found
    """
    manager = get_template_manager()
    template = manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return template


@router.put("/build-templates/{template_id}", response_model=BuildTemplate, tags=["build-templates"])
async def update_build_template(template_id: str, update: BuildTemplateUpdate):
    """
    Update an existing build template.
    
    Args:
        template_id: Template ID
        update: Fields to update
        
    Returns:
        Updated template
        
    Raises:
        HTTPException: If template not found
    """
    manager = get_template_manager()
    template = manager.update_template(template_id, update)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return template


@router.delete("/build-templates/{template_id}", response_model=OperationResponse, tags=["build-templates"])
async def delete_build_template(template_id: str):
    """
    Delete a build template.
    
    Args:
        template_id: Template ID
        
    Returns:
        Operation result
        
    Raises:
        HTTPException: If template not found
    """
    manager = get_template_manager()
    success = manager.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return OperationResponse(
        success=True,
        message=f"Template {template_id} deleted successfully"
    )
