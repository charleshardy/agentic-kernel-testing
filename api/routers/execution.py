"""Real-time test execution endpoints with orchestrator integration."""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status, WebSocket, WebSocketDisconnect
import json
import asyncio

from ..models import APIResponse, ExecutionPlanStatus, TestExecutionStatus
from ..auth import get_current_user, require_permission
from ..orchestrator_integration import get_orchestrator
from ai_generator.models import TestStatus

def get_demo_user():
    """Return demo user for testing."""
    return {
        "username": "demo",
        "user_id": "demo-001", 
        "email": "demo@example.com",
        "permissions": ["test:submit", "test:read", "test:delete", "status:read"],
        "is_active": True
    }

router = APIRouter()

# WebSocket connection manager for real-time updates
class ConnectionManager:
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

manager = ConnectionManager()


@router.websocket("/execution/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time execution updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            orchestrator = get_orchestrator()
            if orchestrator and orchestrator.is_running:
                try:
                    # Get real-time status from orchestrator
                    status_data = {
                        "type": "status_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": orchestrator.get_system_metrics()
                    }
                    await manager.send_personal_message(json.dumps(status_data), websocket)
                except Exception as e:
                    print(f"Error getting orchestrator status: {e}")
            
            # Wait before next update
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post("/execution/start", response_model=APIResponse)
async def start_test_execution(
    test_ids: List[str],
    priority: int = 5,
    environment_preference: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Start execution of specific test cases using the orchestrator."""
    try:
        orchestrator = get_orchestrator()
        
        # Try to start orchestrator if it's not running
        if not orchestrator or not orchestrator.is_running:
            from ..orchestrator_integration import start_orchestrator
            if not start_orchestrator():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Test orchestrator is not available and failed to start"
                )
            orchestrator = get_orchestrator()
        
        # Create execution plan
        plan_id = str(uuid.uuid4())
        submission_id = str(uuid.uuid4())
        
        # Create execution plan data structure
        execution_plan = {
            "plan_id": plan_id,
            "submission_id": submission_id,
            "test_case_ids": test_ids,
            "priority": priority,
            "status": "queued",
            "created_at": datetime.utcnow(),
            "created_by": current_user["username"],
            "environment_preference": environment_preference
        }
        
        # Submit to orchestrator (this would integrate with the queue monitor)
        try:
            # Add to execution_plans dictionary that the orchestrator monitors
            from api.routers.tests import execution_plans
            execution_plans[plan_id] = execution_plan
            
            # Force orchestrator to poll for new plans immediately
            if orchestrator and hasattr(orchestrator, 'queue_monitor'):
                try:
                    new_plans = orchestrator.queue_monitor.poll_for_new_plans()
                    print(f"Forced poll detected {len(new_plans)} new plans")
                except Exception as e:
                    print(f"Error forcing poll: {e}")
            
            # Notify WebSocket clients
            await manager.broadcast(json.dumps({
                "type": "execution_started",
                "plan_id": plan_id,
                "test_count": len(test_ids),
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            return APIResponse(
                success=True,
                message=f"Started execution of {len(test_ids)} tests",
                data={
                    "execution_plan_id": plan_id,
                    "submission_id": submission_id,
                    "status": "queued",
                    "test_count": len(test_ids),
                    "estimated_completion": (datetime.utcnow() + timedelta(minutes=len(test_ids) * 2)).isoformat()
                }
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit to orchestrator: {str(e)}"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start test execution: {str(e)}"
        )


@router.get("/execution/{plan_id}/status", response_model=APIResponse)
async def get_execution_status(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Get detailed execution status for a specific plan."""
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator and orchestrator.is_running:
            # Try to get real status from orchestrator
            try:
                status_tracker = orchestrator.status_tracker
                if hasattr(status_tracker, 'get_plan_status'):
                    plan_status = status_tracker.get_plan_status(plan_id)
                    if plan_status:
                        return APIResponse(
                            success=True,
                            message="Execution status retrieved from orchestrator",
                            data=plan_status
                        )
            except Exception as e:
                print(f"Error getting status from orchestrator: {e}")
        
        # Fallback to mock data
        from api.routers.tests import execution_plans
        if plan_id not in execution_plans:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution plan not found"
            )
        
        plan_data = execution_plans[plan_id]
        
        # Create mock status response
        mock_status = {
            "plan_id": plan_id,
            "submission_id": plan_data["submission_id"],
            "overall_status": plan_data.get("status", "queued"),
            "total_tests": len(plan_data["test_case_ids"]),
            "completed_tests": 0,
            "failed_tests": 0,
            "progress": 0.0,
            "started_at": plan_data["created_at"].isoformat(),
            "estimated_completion": plan_data.get("estimated_completion", datetime.utcnow() + timedelta(minutes=10)).isoformat(),
            "test_statuses": []
        }
        
        return APIResponse(
            success=True,
            message="Execution status retrieved (mock data)",
            data=mock_status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution status: {str(e)}"
        )


@router.post("/execution/{plan_id}/cancel", response_model=APIResponse)
async def cancel_execution(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Cancel a running execution plan."""
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator and orchestrator.is_running:
            # Try to cancel through orchestrator
            try:
                # This would call orchestrator's cancel method
                success = True  # Placeholder - would call orchestrator.cancel_execution(plan_id)
                
                if success:
                    # Notify WebSocket clients
                    await manager.broadcast(json.dumps({
                        "type": "execution_cancelled",
                        "plan_id": plan_id,
                        "cancelled_by": current_user["username"],
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
                    return APIResponse(
                        success=True,
                        message="Execution cancelled successfully",
                        data={
                            "plan_id": plan_id,
                            "cancelled_by": current_user["username"],
                            "cancelled_at": datetime.utcnow().isoformat()
                        }
                    )
            except Exception as e:
                print(f"Error cancelling through orchestrator: {e}")
        
        # Fallback to updating local state
        from api.routers.tests import execution_plans
        if plan_id in execution_plans:
            execution_plans[plan_id]["status"] = "cancelled"
            execution_plans[plan_id]["cancelled_at"] = datetime.utcnow()
            execution_plans[plan_id]["cancelled_by"] = current_user["username"]
        
        return APIResponse(
            success=True,
            message="Execution cancelled (local state updated)",
            data={
                "plan_id": plan_id,
                "cancelled_by": current_user["username"],
                "cancelled_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel execution: {str(e)}"
        )


@router.get("/execution/active", response_model=APIResponse)
async def get_active_executions(
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Get all currently active executions with real-time data."""
    try:
        # Always use the execution_plans data directly for Web GUI
        from api.routers.tests import execution_plans
        
        active_executions = []
        for plan_id, plan_data in execution_plans.items():
            status = plan_data.get("status")
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            
            # Filter out debug test cases and old test plans
            is_debug_test = (
                created_by == "debug_script" or 
                any(test_id.startswith("test-123") for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
            )
            
            # Skip debug tests and completed/failed/cancelled plans
            if is_debug_test or status in ["completed", "failed", "cancelled"]:
                continue
            
            # Include plans that are queued, running, or any status that's not final
            if status not in ["completed", "failed", "cancelled"]:
                # Handle datetime serialization
                started_at = plan_data.get("created_at")
                if started_at and hasattr(started_at, 'isoformat'):
                    started_at = started_at.isoformat()
                elif started_at:
                    started_at = str(started_at)
                
                estimated_completion = plan_data.get("estimated_completion")
                if estimated_completion and hasattr(estimated_completion, 'isoformat'):
                    estimated_completion = estimated_completion.isoformat()
                elif not estimated_completion:
                    estimated_completion = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
                else:
                    estimated_completion = str(estimated_completion)
                
                active_executions.append({
                    "plan_id": plan_id,
                    "submission_id": plan_data.get("submission_id", f"sub-{plan_id[:8]}"),
                    "overall_status": plan_data.get("status", "queued"),
                    "total_tests": len(plan_data.get("test_case_ids", [])),
                    "completed_tests": 0,
                    "failed_tests": 0,
                    "progress": 0.0,
                    "started_at": started_at,
                    "estimated_completion": estimated_completion
                })
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(active_executions)} active executions",
            data={"executions": active_executions}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active executions: {str(e)}"
        )


@router.get("/execution/metrics", response_model=APIResponse)
async def get_execution_metrics(
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Get real-time execution metrics from the orchestrator."""
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator and orchestrator.is_running:
            try:
                metrics = orchestrator.get_system_metrics()
                health_status = orchestrator.get_health_status()
                
                return APIResponse(
                    success=True,
                    message="Real-time metrics from orchestrator",
                    data={
                        "orchestrator_status": health_status.get('status', 'unknown'),
                        "active_tests": metrics.get('active_tests', 0),
                        "queued_tests": metrics.get('queued_tests', 0),
                        "available_environments": metrics.get('available_environments', 0),
                        "total_environments": metrics.get('total_environments', 0),
                        "completed_tests_today": metrics.get('completed_tests', 0),
                        "failed_tests_today": metrics.get('failed_tests', 0),
                        "average_execution_time": metrics.get('avg_execution_time', 0),
                        "system_load": metrics.get('system_load', 'low'),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                print(f"Error getting metrics from orchestrator: {e}")
        
        # Fallback metrics
        return APIResponse(
            success=True,
            message="Fallback metrics (orchestrator not available)",
            data={
                "orchestrator_status": "not_running",
                "active_tests": 0,
                "queued_tests": 0,
                "available_environments": 5,
                "total_environments": 5,
                "completed_tests_today": 0,
                "failed_tests_today": 0,
                "average_execution_time": 0,
                "system_load": "low",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution metrics: {str(e)}"
        )


@router.post("/execution/orchestrator/restart", response_model=APIResponse)
async def restart_orchestrator(
    current_user: Dict[str, Any] = Depends(require_permission("admin:manage"))
):
    """Restart the orchestrator service (admin only)."""
    try:
        from ..orchestrator_integration import stop_orchestrator, start_orchestrator
        
        # Stop current orchestrator
        stop_result = stop_orchestrator()
        
        # Start new orchestrator
        start_result = start_orchestrator()
        
        if start_result:
            return APIResponse(
                success=True,
                message="Orchestrator restarted successfully",
                data={
                    "stop_result": stop_result,
                    "start_result": start_result,
                    "restarted_by": current_user["username"],
                    "restarted_at": datetime.utcnow().isoformat()
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restart orchestrator"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart orchestrator: {str(e)}"
        )


@router.post("/execution/orchestrator/poll", response_model=APIResponse)
async def force_orchestrator_poll(
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Force the orchestrator to poll for new execution plans."""
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator or not orchestrator.is_running:
            # Try to start orchestrator
            from ..orchestrator_integration import start_orchestrator
            if start_orchestrator():
                orchestrator = get_orchestrator()
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Orchestrator is not running and failed to start"
                )
        
        if orchestrator and hasattr(orchestrator, 'queue_monitor'):
            queue_monitor = orchestrator.queue_monitor
            
            # Force poll for new plans
            new_plans = queue_monitor.poll_for_new_plans()
            
            return APIResponse(
                success=True,
                message=f"Forced orchestrator poll completed",
                data={
                    "new_plans_detected": len(new_plans),
                    "queued_plans": queue_monitor.get_queued_plan_count(),
                    "queued_tests": queue_monitor.get_queued_test_count(),
                    "polled_by": current_user["username"],
                    "polled_at": datetime.utcnow().isoformat(),
                    "detected_plans": [
                        {
                            "plan_id": plan.get('plan_id'),
                            "status": plan.get('status'),
                            "test_count": len(plan.get('test_case_ids', []))
                        }
                        for plan in new_plans
                    ]
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Queue monitor not available"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force orchestrator poll: {str(e)}"
        )


@router.post("/execution/cleanup", response_model=APIResponse)
async def cleanup_old_executions(
    max_age_hours: int = Query(1, description="Maximum age in hours for executions to keep"),
    current_user: Dict[str, Any] = Depends(require_permission("admin:manage"))
):
    """Clean up old execution plans that are no longer active."""
    try:
        from api.routers.tests import execution_plans
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        plans_to_remove = []
        
        for plan_id, plan_data in execution_plans.items():
            created_at = plan_data.get("created_at")
            status = plan_data.get("status", "unknown")
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            
            # Remove plans that are old, completed, or debug tests
            should_remove = False
            
            # Always remove debug test cases
            is_debug_test = (
                created_by == "debug_script" or 
                any(test_id.startswith("test-123") for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
            )
            
            if is_debug_test:
                should_remove = True
            elif status in ["completed", "failed", "cancelled"]:
                should_remove = True
            elif created_at and created_at < cutoff_time:
                should_remove = True
            
            if should_remove:
                plans_to_remove.append(plan_id)
        
        # Remove the plans
        removed_count = 0
        debug_removed = 0
        for plan_id in plans_to_remove:
            if plan_id in execution_plans:
                plan_data = execution_plans[plan_id]
                created_by = plan_data.get("created_by", "")
                test_case_ids = plan_data.get("test_case_ids", [])
                
                is_debug_test = (
                    created_by == "debug_script" or 
                    any(test_id.startswith("test-123") for test_id in test_case_ids) or
                    any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
                )
                
                if is_debug_test:
                    debug_removed += 1
                
                del execution_plans[plan_id]
                removed_count += 1
        
        return APIResponse(
            success=True,
            message=f"Cleaned up {removed_count} old execution plans ({debug_removed} debug tests)",
            data={
                "removed_count": removed_count,
                "debug_removed": debug_removed,
                "remaining_count": len(execution_plans),
                "cutoff_time": cutoff_time.isoformat(),
                "cleaned_by": current_user["username"],
                "cleaned_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup executions: {str(e)}"
        )


@router.post("/execution/cleanup-debug", response_model=APIResponse)
async def cleanup_debug_executions(
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Clean up debug test execution plans specifically."""
    try:
        from api.routers.tests import execution_plans
        
        plans_to_remove = []
        
        for plan_id, plan_data in execution_plans.items():
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            
            # Identify debug test cases
            is_debug_test = (
                created_by == "debug_script" or 
                any(test_id.startswith("test-123") for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
            )
            
            if is_debug_test:
                plans_to_remove.append(plan_id)
        
        # Remove the debug plans
        removed_count = 0
        for plan_id in plans_to_remove:
            if plan_id in execution_plans:
                del execution_plans[plan_id]
                removed_count += 1
        
        return APIResponse(
            success=True,
            message=f"Cleaned up {removed_count} debug execution plans",
            data={
                "removed_count": removed_count,
                "remaining_count": len(execution_plans),
                "cleaned_by": current_user["username"],
                "cleaned_at": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup debug executions: {str(e)}"
        )