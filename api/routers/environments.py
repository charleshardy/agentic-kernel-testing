"""Environment management endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status

from ..models import APIResponse, HardwareConfigRequest, PaginationParams
from ..auth import get_current_user, require_permission
from ai_generator.models import Environment, HardwareConfig, EnvironmentStatus

router = APIRouter()

# Mock environments data (in production, this would come from environment manager)
environments = {}
environment_usage = {}


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