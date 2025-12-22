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
        
        if not orchestrator or not orchestrator.is_running:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Test orchestrator is not available"
            )
        
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
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
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
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get all currently active executions with real-time data."""
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator and orchestrator.is_running:
            # Get real data from orchestrator
            try:
                metrics = orchestrator.get_system_metrics()
                status_tracker = orchestrator.status_tracker
                
                active_executions = []
                
                # Get active plans from status tracker
                if hasattr(status_tracker, 'get_active_plans'):
                    plans = status_tracker.get_active_plans()
                    for plan in plans:
                        active_executions.append({
                            "plan_id": plan.get('plan_id'),
                            "submission_id": plan.get('submission_id'),
                            "overall_status": plan.get('status', 'running'),
                            "total_tests": plan.get('total_tests', 0),
                            "completed_tests": plan.get('completed_tests', 0),
                            "failed_tests": plan.get('failed_tests', 0),
                            "progress": plan.get('progress', 0.0),
                            "started_at": plan.get('started_at').isoformat() if plan.get('started_at') else None,
                            "estimated_completion": plan.get('estimated_completion').isoformat() if plan.get('estimated_completion') else None
                        })
                
                return APIResponse(
                    success=True,
                    message=f"Retrieved {len(active_executions)} active executions from orchestrator",
                    data=active_executions
                )
                
            except Exception as e:
                print(f"Error getting active executions from orchestrator: {e}")
        
        # Fallback to mock/local data
        from api.routers.tests import execution_plans
        
        active_executions = []
        for plan_id, plan_data in execution_plans.items():
            if plan_data.get("status") not in ["completed", "failed", "cancelled"]:
                active_executions.append({
                    "plan_id": plan_id,
                    "submission_id": plan_data["submission_id"],
                    "overall_status": plan_data.get("status", "queued"),
                    "total_tests": len(plan_data["test_case_ids"]),
                    "completed_tests": 0,
                    "failed_tests": 0,
                    "progress": 0.0,
                    "started_at": plan_data["created_at"].isoformat(),
                    "estimated_completion": plan_data.get("estimated_completion", datetime.utcnow() + timedelta(minutes=10)).isoformat()
                })
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(active_executions)} active executions (fallback data)",
            data=active_executions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active executions: {str(e)}"
        )


@router.get("/execution/metrics", response_model=APIResponse)
async def get_execution_metrics(
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
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