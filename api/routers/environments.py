"""Environment management endpoints."""

import uuid
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import asyncio

from ..models import (
    APIResponse, HardwareConfigRequest, PaginationParams,
    EnvironmentResponse, EnvironmentTypeEnum, EnvironmentStatusEnum, EnvironmentHealthEnum,
    AllocationRequest, AllocationStatusEnum, HardwareRequirements, AllocationPreferences,
    AllocationEvent, AllocationMetrics, AllocationQueueResponse, AllocationHistoryResponse,
    ResourceUsage, NetworkMetrics, EnvironmentMetadata, EnvironmentAllocationResponse
)
from ..auth import get_current_user, require_permission
from ai_generator.models import Environment, HardwareConfig, EnvironmentStatus

router = APIRouter()

# Mock environments data (in production, this would come from environment manager)
environments = {}
environment_usage = {}

# Allocation tracking data structures
allocation_requests = {}  # request_id -> AllocationRequest
allocation_queue = []     # List of request_ids in queue order
allocation_history = []   # List of AllocationEvent objects
allocation_metrics = {
    "total_allocations": 0,
    "successful_allocations": 0,
    "failed_allocations": 0,
    "average_allocation_time": 120.0,
    "queue_length": 0,
    "utilization_rate": 0.0
}

# WebSocket connection manager for real-time updates
class AllocationConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

allocation_manager = AllocationConnectionManager()


def initialize_mock_environments():
    """Initialize some mock environments for demonstration."""
    configs = [
        {
            "id": "env-qemu-x86-001",
            "config": HardwareConfig(
                architecture="x86_64",
                cpu_model="QEMU Virtual CPU",
                memory_mb=4096,
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu"
            ),
            "status": EnvironmentStatus.IDLE,
            "kernel_version": None,
            "ip_address": "192.168.122.10",
            "created_at": datetime.utcnow() - timedelta(hours=2),
            "last_used": datetime.utcnow() - timedelta(minutes=30)
        },
        {
            "id": "env-qemu-arm-001", 
            "config": HardwareConfig(
                architecture="arm64",
                cpu_model="ARM Cortex-A72",
                memory_mb=2048,
                storage_type="ssd",
                is_virtual=True,
                emulator="qemu"
            ),
            "status": EnvironmentStatus.BUSY,
            "kernel_version": "6.1.0-rc1",
            "ip_address": "192.168.122.11",
            "created_at": datetime.utcnow() - timedelta(hours=1),
            "last_used": datetime.utcnow() - timedelta(minutes=5)
        },
        {
            "id": "env-physical-rpi-001",
            "config": HardwareConfig(
                architecture="arm64",
                cpu_model="ARM Cortex-A72",
                memory_mb=8192,
                storage_type="microsd",
                is_virtual=False,
                emulator=None
            ),
            "status": EnvironmentStatus.IDLE,
            "kernel_version": "6.1.0-rc1",
            "ip_address": "10.0.1.100",
            "created_at": datetime.utcnow() - timedelta(days=1),
            "last_used": datetime.utcnow() - timedelta(hours=2)
        }
    ]
    
    for env_data in configs:
        env = Environment(
            id=env_data["id"],
            config=env_data["config"],
            status=env_data["status"],
            kernel_version=env_data["kernel_version"],
            ip_address=env_data["ip_address"],
            created_at=env_data["created_at"],
            last_used=env_data["last_used"]
        )
        environments[env.id] = env
        
        # Mock usage statistics
        environment_usage[env.id] = {
            "total_tests_run": 42 if env.id == "env-qemu-x86-001" else 15,
            "total_runtime_hours": 156.5 if env.id == "env-qemu-x86-001" else 45.2,
            "success_rate": 0.92 if env.id == "env-qemu-x86-001" else 0.87,
            "avg_test_duration": 125.3,
            "last_failure": datetime.utcnow() - timedelta(days=2) if env.id == "env-qemu-x86-001" else None
        }
    
    # Initialize some mock allocation requests for demonstration
    mock_requests = [
        {
            "id": "alloc-req-001",
            "test_id": "test-case-001",
            "requirements": HardwareRequirements(
                architecture="x86_64",
                min_memory_mb=2048,
                min_cpu_cores=2,
                required_features=["kvm"],
                isolation_level="vm"
            ),
            "priority": 3,
            "status": AllocationStatusEnum.QUEUED,
            "submitted_at": datetime.utcnow() - timedelta(minutes=5)
        },
        {
            "id": "alloc-req-002", 
            "test_id": "test-case-002",
            "requirements": HardwareRequirements(
                architecture="arm64",
                min_memory_mb=1024,
                min_cpu_cores=1,
                required_features=[],
                isolation_level="container"
            ),
            "priority": 1,
            "status": AllocationStatusEnum.QUEUED,
            "submitted_at": datetime.utcnow() - timedelta(minutes=3)
        }
    ]
    
    for req_data in mock_requests:
        req = AllocationRequest(
            id=req_data["id"],
            test_id=req_data["test_id"],
            requirements=req_data["requirements"],
            priority=req_data["priority"],
            submitted_at=req_data["submitted_at"],
            status=req_data["status"]
        )
        allocation_requests[req.id] = req
        allocation_queue.append(req.id)
    
    # Update allocation metrics
    allocation_metrics["queue_length"] = len(allocation_queue)
    allocation_metrics["utilization_rate"] = len([e for e in environments.values() if e.status == EnvironmentStatus.BUSY]) / len(environments)


# Initialize mock data
initialize_mock_environments()


@router.get("/environments", response_model=APIResponse)
async def list_environments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[EnvironmentStatus] = Query(None, description="Filter by status"),
    architecture: Optional[str] = Query(None, description="Filter by architecture"),
    is_virtual: Optional[bool] = Query(None, description="Filter by virtual/physical"),
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """List available test environments with filtering and pagination."""
    try:
        env_list = []
        
        for env_id, env in environments.items():
            # Apply filters
            if status_filter and env.status != status_filter:
                continue
            if architecture and env.config.architecture != architecture:
                continue
            if is_virtual is not None and env.config.is_virtual != is_virtual:
                continue
            
            usage_stats = environment_usage.get(env_id, {})
            
            env_info = {
                "id": env.id,
                "status": env.status.value,
                "architecture": env.config.architecture,
                "cpu_model": env.config.cpu_model,
                "memory_mb": env.config.memory_mb,
                "storage_type": env.config.storage_type,
                "is_virtual": env.config.is_virtual,
                "emulator": env.config.emulator,
                "kernel_version": env.kernel_version,
                "ip_address": env.ip_address,
                "created_at": env.created_at.isoformat(),
                "last_used": env.last_used.isoformat(),
                "usage_stats": {
                    "total_tests_run": usage_stats.get("total_tests_run", 0),
                    "total_runtime_hours": usage_stats.get("total_runtime_hours", 0.0),
                    "success_rate": usage_stats.get("success_rate", 0.0),
                    "avg_test_duration": usage_stats.get("avg_test_duration", 0.0)
                }
            }
            env_list.append(env_info)
        
        # Sort by last used (most recent first)
        env_list.sort(key=lambda x: x["last_used"], reverse=True)
        
        # Pagination
        total_items = len(env_list)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_envs = env_list[start_idx:end_idx]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_envs)} environments",
            data={
                "environments": paginated_envs,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": (total_items + page_size - 1) // page_size
                },
                "summary": {
                    "total_environments": total_items,
                    "idle_environments": len([e for e in env_list if e["status"] == "idle"]),
                    "busy_environments": len([e for e in env_list if e["status"] == "busy"]),
                    "virtual_environments": len([e for e in env_list if e["is_virtual"]]),
                    "physical_environments": len([e for e in env_list if not e["is_virtual"]])
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve environments: {str(e)}"
        )


@router.get("/environments/{env_id}", response_model=APIResponse)
async def get_environment(
    env_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get detailed information about a specific environment."""
    if env_id not in environments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )
    
    env = environments[env_id]
    usage_stats = environment_usage.get(env_id, {})
    
    # Mock detailed information
    detailed_info = {
        "environment": {
            "id": env.id,
            "status": env.status.value,
            "config": env.config.to_dict(),
            "kernel_version": env.kernel_version,
            "ip_address": env.ip_address,
            "created_at": env.created_at.isoformat(),
            "last_used": env.last_used.isoformat(),
            "metadata": env.metadata
        },
        "usage_statistics": {
            "total_tests_run": usage_stats.get("total_tests_run", 0),
            "total_runtime_hours": usage_stats.get("total_runtime_hours", 0.0),
            "success_rate": usage_stats.get("success_rate", 0.0),
            "avg_test_duration": usage_stats.get("avg_test_duration", 0.0),
            "last_failure": usage_stats.get("last_failure").isoformat() if usage_stats.get("last_failure") else None
        },
        "current_status": {
            "cpu_usage": 25.3 if env.status == EnvironmentStatus.BUSY else 2.1,
            "memory_usage": 1024 if env.status == EnvironmentStatus.BUSY else 256,
            "disk_usage": 45.2,
            "network_io": {
                "bytes_sent": 1024000,
                "bytes_received": 2048000
            },
            "uptime_seconds": 3600 * 24 * 2  # 2 days
        },
        "capabilities": {
            "supports_kvm": env.config.is_virtual and env.config.architecture == "x86_64",
            "supports_nested_virtualization": False,
            "max_memory_mb": env.config.memory_mb * 2,  # Can be expanded
            "supported_kernel_versions": ["6.1.0", "6.0.0", "5.19.0"],
            "available_tools": ["gdb", "perf", "strace", "tcpdump"]
        }
    }
    
    return APIResponse(
        success=True,
        message="Environment details retrieved successfully",
        data=detailed_info
    )


@router.post("/environments", response_model=APIResponse)
async def create_environment(
    hardware_config: HardwareConfigRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Create a new test environment."""
    try:
        # Generate environment ID
        env_id = f"env-{hardware_config.architecture}-{str(uuid.uuid4())[:8]}"
        
        # Create hardware config
        hw_config = HardwareConfig(
            architecture=hardware_config.architecture,
            cpu_model=hardware_config.cpu_model,
            memory_mb=hardware_config.memory_mb,
            storage_type=hardware_config.storage_type,
            peripherals=[],  # Convert from dict if needed
            is_virtual=hardware_config.is_virtual,
            emulator=hardware_config.emulator
        )
        
        # Create environment
        env = Environment(
            id=env_id,
            config=hw_config,
            status=EnvironmentStatus.PROVISIONING,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        # Store environment
        environments[env_id] = env
        environment_usage[env_id] = {
            "total_tests_run": 0,
            "total_runtime_hours": 0.0,
            "success_rate": 0.0,
            "avg_test_duration": 0.0,
            "last_failure": None
        }
        
        # Mock provisioning process
        # In production, this would trigger actual environment provisioning
        print(f"Provisioning environment {env_id} with {hardware_config.architecture} architecture")
        
        # Simulate provisioning completion
        env.status = EnvironmentStatus.IDLE
        env.ip_address = f"192.168.122.{len(environments) + 10}"
        
        return APIResponse(
            success=True,
            message="Environment created successfully",
            data={
                "environment_id": env_id,
                "status": env.status.value,
                "ip_address": env.ip_address,
                "estimated_ready_time": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create environment: {str(e)}"
        )


@router.delete("/environments/{env_id}", response_model=APIResponse)
async def delete_environment(
    env_id: str,
    force: bool = Query(False, description="Force deletion even if busy"),
    current_user: Dict[str, Any] = Depends(require_permission("system:admin"))
):
    """Delete a test environment."""
    if env_id not in environments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )
    
    env = environments[env_id]
    
    # Check if environment is busy
    if env.status == EnvironmentStatus.BUSY and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete busy environment. Use force=true to override."
        )
    
    # Remove environment
    del environments[env_id]
    if env_id in environment_usage:
        del environment_usage[env_id]
    
    return APIResponse(
        success=True,
        message="Environment deleted successfully",
        data={
            "deleted_environment_id": env_id,
            "was_forced": force
        }
    )


@router.post("/environments/{env_id}/reset", response_model=APIResponse)
async def reset_environment(
    env_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Reset an environment to clean state."""
    if env_id not in environments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )
    
    env = environments[env_id]
    
    # Check if environment can be reset
    if env.status == EnvironmentStatus.BUSY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset busy environment"
        )
    
    # Reset environment
    env.status = EnvironmentStatus.PROVISIONING
    env.kernel_version = None
    env.last_used = datetime.utcnow()
    
    # Mock reset process
    print(f"Resetting environment {env_id}")
    
    # Simulate reset completion
    env.status = EnvironmentStatus.IDLE
    
    return APIResponse(
        success=True,
        message="Environment reset successfully",
        data={
            "environment_id": env_id,
            "status": env.status.value,
            "reset_at": datetime.utcnow().isoformat()
        }
    )


@router.get("/environments/stats", response_model=APIResponse)
async def get_environment_statistics(
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get overall environment statistics."""
    try:
        total_envs = len(environments)
        idle_envs = len([e for e in environments.values() if e.status == EnvironmentStatus.IDLE])
        busy_envs = len([e for e in environments.values() if e.status == EnvironmentStatus.BUSY])
        error_envs = len([e for e in environments.values() if e.status == EnvironmentStatus.ERROR])
        
        virtual_envs = len([e for e in environments.values() if e.config.is_virtual])
        physical_envs = total_envs - virtual_envs
        
        # Architecture breakdown
        arch_stats = {}
        for env in environments.values():
            arch = env.config.architecture
            if arch not in arch_stats:
                arch_stats[arch] = {"total": 0, "idle": 0, "busy": 0}
            arch_stats[arch]["total"] += 1
            if env.status == EnvironmentStatus.IDLE:
                arch_stats[arch]["idle"] += 1
            elif env.status == EnvironmentStatus.BUSY:
                arch_stats[arch]["busy"] += 1
        
        # Usage statistics
        total_tests = sum(stats.get("total_tests_run", 0) for stats in environment_usage.values())
        total_runtime = sum(stats.get("total_runtime_hours", 0.0) for stats in environment_usage.values())
        avg_success_rate = sum(stats.get("success_rate", 0.0) for stats in environment_usage.values()) / len(environment_usage) if environment_usage else 0.0
        
        statistics = {
            "environment_counts": {
                "total": total_envs,
                "idle": idle_envs,
                "busy": busy_envs,
                "error": error_envs,
                "virtual": virtual_envs,
                "physical": physical_envs
            },
            "architecture_breakdown": arch_stats,
            "usage_statistics": {
                "total_tests_executed": total_tests,
                "total_runtime_hours": round(total_runtime, 2),
                "average_success_rate": round(avg_success_rate, 3),
                "utilization_rate": round(busy_envs / total_envs if total_envs > 0 else 0.0, 3)
            },
            "capacity_info": {
                "max_concurrent_tests": total_envs,
                "available_capacity": idle_envs,
                "capacity_utilization": round(busy_envs / total_envs if total_envs > 0 else 0.0, 3)
            }
        }
        
        return APIResponse(
            success=True,
            message="Environment statistics retrieved successfully",
            data=statistics
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


# ============================================================================
# ENHANCED ALLOCATION TRACKING ENDPOINTS
# ============================================================================

@router.get("/environments/allocation", response_model=APIResponse)
async def get_environment_allocation_data(
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get comprehensive environment allocation data including queue, metrics, and history."""
    try:
        # Convert environments to response format
        env_responses = []
        for env_id, env in environments.items():
            usage_stats = environment_usage.get(env_id, {})
            
            # Create mock resource usage
            resource_usage = ResourceUsage(
                cpu=25.3 if env.status == EnvironmentStatus.BUSY else 2.1,
                memory=45.2 if env.status == EnvironmentStatus.BUSY else 8.5,
                disk=67.8,
                network=NetworkMetrics(
                    bytes_in=1024000,
                    bytes_out=2048000,
                    packets_in=5000,
                    packets_out=7500
                )
            )
            
            # Create environment metadata
            metadata = EnvironmentMetadata(
                kernel_version=env.kernel_version,
                ip_address=env.ip_address,
                provisioned_at=env.created_at,
                last_health_check=datetime.utcnow() - timedelta(minutes=1),
                additional_metadata={
                    "is_virtual": env.config.is_virtual,
                    "emulator": env.config.emulator,
                    "total_tests_run": usage_stats.get("total_tests_run", 0)
                }
            )
            
            # Determine assigned tests (mock data)
            assigned_tests = []
            if env.status == EnvironmentStatus.BUSY:
                assigned_tests = [f"test-{env_id[-3:]}-001"]
            
            env_response = EnvironmentResponse(
                id=env.id,
                type=EnvironmentTypeEnum.QEMU_X86 if "x86" in env.id else EnvironmentTypeEnum.QEMU_ARM if "arm" in env.id else EnvironmentTypeEnum.PHYSICAL,
                status=EnvironmentStatusEnum.READY if env.status == EnvironmentStatus.IDLE else EnvironmentStatusEnum.RUNNING if env.status == EnvironmentStatus.BUSY else EnvironmentStatusEnum.ERROR,
                architecture=env.config.architecture,
                assigned_tests=assigned_tests,
                resources=resource_usage,
                health=EnvironmentHealthEnum.HEALTHY if env.status != EnvironmentStatus.ERROR else EnvironmentHealthEnum.UNHEALTHY,
                metadata=metadata,
                created_at=env.created_at,
                updated_at=env.last_used
            )
            env_responses.append(env_response)
        
        # Get allocation queue
        queue_requests = [allocation_requests[req_id] for req_id in allocation_queue if req_id in allocation_requests]
        
        # Create allocation metrics
        metrics = AllocationMetrics(
            total_allocations=allocation_metrics["total_allocations"],
            successful_allocations=allocation_metrics["successful_allocations"],
            failed_allocations=allocation_metrics["failed_allocations"],
            average_allocation_time=allocation_metrics["average_allocation_time"],
            queue_length=len(allocation_queue),
            utilization_rate=allocation_metrics["utilization_rate"]
        )
        
        # Get recent allocation history
        recent_history = allocation_history[-20:] if allocation_history else []
        
        allocation_data = EnvironmentAllocationResponse(
            environments=env_responses,
            queue=queue_requests,
            metrics=metrics,
            history=recent_history
        )
        
        return APIResponse(
            success=True,
            message="Environment allocation data retrieved successfully",
            data=allocation_data.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve allocation data: {str(e)}"
        )


@router.get("/environments/allocation/queue", response_model=APIResponse)
async def get_allocation_queue(
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get current allocation queue with estimated wait times."""
    try:
        # Get queue requests sorted by priority and submission time
        queue_requests = []
        for req_id in allocation_queue:
            if req_id in allocation_requests:
                queue_requests.append(allocation_requests[req_id])
        
        # Sort by priority (lower number = higher priority) and submission time
        queue_requests.sort(key=lambda r: (r.priority, r.submitted_at))
        
        # Calculate estimated wait times
        estimated_wait_times = {}
        avg_allocation_time = allocation_metrics["average_allocation_time"]
        available_environments = len([e for e in environments.values() if e.status == EnvironmentStatus.IDLE])
        
        for i, request in enumerate(queue_requests):
            # Calculate wait time based on position and available environments
            if available_environments > 0:
                batch_number = i // available_environments
                wait_time_seconds = batch_number * avg_allocation_time
            else:
                wait_time_seconds = i * avg_allocation_time
            
            estimated_wait_times[request.id] = int(wait_time_seconds)
        
        total_wait_time = max(estimated_wait_times.values()) if estimated_wait_times else 0
        
        queue_response = AllocationQueueResponse(
            queue=queue_requests,
            estimated_wait_times=estimated_wait_times,
            total_wait_time=total_wait_time
        )
        
        return APIResponse(
            success=True,
            message=f"Retrieved allocation queue with {len(queue_requests)} requests",
            data=queue_response.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve allocation queue: {str(e)}"
        )


@router.post("/environments/allocation/request", response_model=APIResponse)
async def create_allocation_request(
    test_id: str,
    requirements: HardwareRequirements,
    preferences: Optional[AllocationPreferences] = None,
    priority: int = 5,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Create a new environment allocation request."""
    try:
        # Generate request ID
        request_id = f"alloc-req-{str(uuid.uuid4())[:8]}"
        
        # Create allocation request
        allocation_request = AllocationRequest(
            id=request_id,
            test_id=test_id,
            requirements=requirements,
            preferences=preferences,
            priority=priority,
            submitted_at=datetime.utcnow(),
            status=AllocationStatusEnum.QUEUED
        )
        
        # Store request
        allocation_requests[request_id] = allocation_request
        allocation_queue.append(request_id)
        
        # Update metrics
        allocation_metrics["queue_length"] = len(allocation_queue)
        
        # Create allocation event
        event = AllocationEvent(
            id=f"event-{str(uuid.uuid4())[:8]}",
            type="queued",
            environment_id="",  # No environment assigned yet
            test_id=test_id,
            timestamp=datetime.utcnow(),
            metadata={
                "request_id": request_id,
                "priority": priority,
                "requirements": requirements.dict()
            }
        )
        allocation_history.append(event)
        
        # Broadcast to WebSocket clients
        await allocation_manager.broadcast(json.dumps({
            "type": "allocation_queued",
            "request_id": request_id,
            "test_id": test_id,
            "priority": priority,
            "queue_position": len(allocation_queue),
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        return APIResponse(
            success=True,
            message="Allocation request created successfully",
            data={
                "request_id": request_id,
                "status": "queued",
                "queue_position": len(allocation_queue),
                "estimated_wait_time": len(allocation_queue) * allocation_metrics["average_allocation_time"]
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create allocation request: {str(e)}"
        )


@router.delete("/environments/allocation/request/{request_id}", response_model=APIResponse)
async def cancel_allocation_request(
    request_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Cancel an allocation request."""
    try:
        if request_id not in allocation_requests:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Allocation request not found"
            )
        
        request = allocation_requests[request_id]
        
        # Check if request can be cancelled
        if request.status not in [AllocationStatusEnum.QUEUED, AllocationStatusEnum.ALLOCATING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel request with status: {request.status}"
            )
        
        # Update request status
        request.status = AllocationStatusEnum.CANCELLED
        
        # Remove from queue
        if request_id in allocation_queue:
            allocation_queue.remove(request_id)
        
        # Update metrics
        allocation_metrics["queue_length"] = len(allocation_queue)
        
        # Create allocation event
        event = AllocationEvent(
            id=f"event-{str(uuid.uuid4())[:8]}",
            type="cancelled",
            environment_id="",
            test_id=request.test_id,
            timestamp=datetime.utcnow(),
            metadata={
                "request_id": request_id,
                "cancelled_by": current_user["username"]
            }
        )
        allocation_history.append(event)
        
        # Broadcast to WebSocket clients
        await allocation_manager.broadcast(json.dumps({
            "type": "allocation_cancelled",
            "request_id": request_id,
            "test_id": request.test_id,
            "cancelled_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        return APIResponse(
            success=True,
            message="Allocation request cancelled successfully",
            data={
                "request_id": request_id,
                "cancelled_by": current_user["username"],
                "cancelled_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel allocation request: {str(e)}"
        )


@router.get("/environments/allocation/history", response_model=APIResponse)
async def get_allocation_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    test_id: Optional[str] = Query(None, description="Filter by test ID"),
    environment_id: Optional[str] = Query(None, description="Filter by environment ID"),
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get allocation history with filtering and pagination."""
    try:
        # Filter events
        filtered_events = allocation_history.copy()
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.type == event_type]
        
        if test_id:
            filtered_events = [e for e in filtered_events if e.test_id == test_id]
        
        if environment_id:
            filtered_events = [e for e in filtered_events if e.environment_id == environment_id]
        
        # Sort by timestamp (most recent first)
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Pagination
        total_items = len(filtered_events)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_events = filtered_events[start_idx:end_idx]
        
        history_response = AllocationHistoryResponse(
            events=paginated_events,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": (total_items + page_size - 1) // page_size,
                "has_next": end_idx < total_items,
                "has_prev": page > 1
            }
        )
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_events)} allocation events",
            data=history_response.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve allocation history: {str(e)}"
        )


@router.get("/environments/allocation/events")
async def allocation_events_stream(
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Server-Sent Events stream for real-time allocation updates."""
    async def event_generator():
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            # Send periodic updates
            while True:
                # Send current queue status
                queue_status = {
                    "type": "queue_status",
                    "queue_length": len(allocation_queue),
                    "available_environments": len([e for e in environments.values() if e.status == EnvironmentStatus.IDLE]),
                    "busy_environments": len([e for e in environments.values() if e.status == EnvironmentStatus.BUSY]),
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(queue_status)}\n\n"
                
                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds
                
        except asyncio.CancelledError:
            # Client disconnected
            pass
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.utcnow().isoformat()})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.websocket("/environments/allocation/ws")
async def allocation_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time allocation updates."""
    await allocation_manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            try:
                # Get current allocation status
                status_data = {
                    "type": "allocation_status",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "queue_length": len(allocation_queue),
                        "available_environments": len([e for e in environments.values() if e.status == EnvironmentStatus.IDLE]),
                        "busy_environments": len([e for e in environments.values() if e.status == EnvironmentStatus.BUSY]),
                        "total_environments": len(environments),
                        "utilization_rate": allocation_metrics["utilization_rate"]
                    }
                }
                await allocation_manager.send_personal_message(json.dumps(status_data), websocket)
            except Exception as e:
                print(f"Error sending WebSocket update: {e}")
            
            # Wait before next update
            await asyncio.sleep(3)  # Update every 3 seconds
            
    except WebSocketDisconnect:
        allocation_manager.disconnect(websocket)