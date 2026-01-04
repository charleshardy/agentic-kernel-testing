"""
Deployment Management API Routes

Provides REST API endpoints for managing test deployments including
starting deployments, monitoring status, cancellation, and log access.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
import io

from pydantic import BaseModel, Field
from deployment.orchestrator import DeploymentOrchestrator
from deployment.models import (
    TestArtifact, ArtifactType, DeploymentStatus, Priority,
    DeploymentResult, DeploymentPlan
)
from api.auth import get_current_user


router = APIRouter(prefix="/api/v1/deployments", tags=["deployments"])

# Global orchestrator instance (in production, this would be dependency injected)
_orchestrator: Optional[DeploymentOrchestrator] = None


async def get_orchestrator() -> DeploymentOrchestrator:
    """Get or create deployment orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DeploymentOrchestrator(
            max_concurrent_deployments=5,
            default_timeout=300
        )
        await _orchestrator.start()
    return _orchestrator


# Request/Response Models
class ArtifactRequest(BaseModel):
    """Request model for test artifact"""
    name: str = Field(..., description="Artifact name")
    type: str = Field(..., description="Artifact type (script, binary, config, data)")
    content_base64: str = Field(..., description="Base64 encoded artifact content")
    permissions: str = Field(default="0755", description="File permissions")
    target_path: str = Field(..., description="Target deployment path")
    dependencies: List[str] = Field(default_factory=list, description="Artifact dependencies")


class DeploymentRequest(BaseModel):
    """Request model for starting a deployment"""
    plan_id: str = Field(..., description="Test plan identifier")
    environment_id: str = Field(..., description="Target environment ID")
    artifacts: List[ArtifactRequest] = Field(..., description="Test artifacts to deploy")
    priority: str = Field(default="normal", description="Deployment priority (low, normal, high, critical)")
    timeout_seconds: Optional[int] = Field(default=300, description="Deployment timeout")


class DeploymentResponse(BaseModel):
    """Response model for deployment operations"""
    deployment_id: str = Field(..., description="Unique deployment identifier")
    status: str = Field(..., description="Current deployment status")
    message: str = Field(..., description="Status message")


class DeploymentStatusResponse(BaseModel):
    """Response model for deployment status"""
    deployment_id: str
    plan_id: str
    environment_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    artifacts_deployed: int = 0
    dependencies_installed: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    completion_percentage: float = 0.0
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class DeploymentMetricsResponse(BaseModel):
    """Response model for deployment metrics"""
    total_deployments: int
    successful_deployments: int
    failed_deployments: int
    cancelled_deployments: int
    active_deployments: int
    queue_size: int
    average_duration_seconds: float
    retry_count: int
    environment_usage: Dict[str, int]


# API Endpoints
@router.post("/", response_model=DeploymentResponse)
async def start_deployment(
    request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Start a new deployment.
    
    Creates and queues a new deployment for execution with the specified
    artifacts and configuration.
    """
    try:
        # Validate priority
        priority_map = {
            "low": Priority.LOW,
            "normal": Priority.NORMAL,
            "high": Priority.HIGH,
            "critical": Priority.CRITICAL
        }
        
        if request.priority.lower() not in priority_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority '{request.priority}'. Must be one of: {list(priority_map.keys())}"
            )
        
        priority = priority_map[request.priority.lower()]
        
        # Convert artifacts
        artifacts = []
        for artifact_req in request.artifacts:
            try:
                import base64
                content = base64.b64decode(artifact_req.content_base64)
                
                artifact = TestArtifact(
                    artifact_id="",  # Will be auto-generated
                    name=artifact_req.name,
                    type=ArtifactType(artifact_req.type.lower()),
                    content=content,
                    checksum="",  # Will be auto-calculated
                    permissions=artifact_req.permissions,
                    target_path=artifact_req.target_path,
                    dependencies=artifact_req.dependencies
                )
                artifacts.append(artifact)
                
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid artifact '{artifact_req.name}': {str(e)}"
                )
        
        # Start deployment
        deployment_id = await orchestrator.deploy_to_environment(
            plan_id=request.plan_id,
            env_id=request.environment_id,
            artifacts=artifacts,
            priority=priority
        )
        
        return DeploymentResponse(
            deployment_id=deployment_id,
            status="pending",
            message=f"Deployment {deployment_id} started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start deployment: {str(e)}"
        )


@router.get("/{deployment_id}/status", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    deployment_id: str,
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Get the current status of a deployment.
    
    Returns detailed information about the deployment including progress,
    timing, and any error messages.
    """
    try:
        deployment = await orchestrator.get_deployment_status(deployment_id)
        
        if not deployment:
            raise HTTPException(
                status_code=404,
                detail=f"Deployment {deployment_id} not found"
            )
        
        # Convert steps to dict format
        steps = []
        for step in deployment.steps:
            step_dict = {
                "step_id": step.step_id,
                "name": step.name,
                "status": step.status.value,
                "start_time": step.start_time.isoformat() if step.start_time else None,
                "end_time": step.end_time.isoformat() if step.end_time else None,
                "duration_seconds": step.duration_seconds,
                "error_message": step.error_message,
                "progress_percentage": getattr(step, 'progress_percentage', 0.0),
                "details": step.details
            }
            steps.append(step_dict)
        
        return DeploymentStatusResponse(
            deployment_id=deployment.deployment_id,
            plan_id=deployment.plan_id,
            environment_id=deployment.environment_id,
            status=deployment.status.value,
            start_time=deployment.start_time,
            end_time=deployment.end_time,
            duration_seconds=deployment.duration_seconds,
            artifacts_deployed=deployment.artifacts_deployed,
            dependencies_installed=deployment.dependencies_installed,
            error_message=deployment.error_message,
            retry_count=deployment.retry_count,
            completion_percentage=deployment.completion_percentage,
            steps=steps
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment status: {str(e)}"
        )


@router.put("/{deployment_id}/cancel", response_model=DeploymentResponse)
async def cancel_deployment(
    deployment_id: str,
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Cancel an active deployment.
    
    Attempts to cancel the specified deployment if it's still running.
    Already completed or failed deployments cannot be cancelled.
    """
    try:
        success = await orchestrator.cancel_deployment(deployment_id)
        
        if not success:
            # Check if deployment exists
            deployment = await orchestrator.get_deployment_status(deployment_id)
            if not deployment:
                raise HTTPException(
                    status_code=404,
                    detail=f"Deployment {deployment_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel deployment {deployment_id} in state {deployment.status.value}"
                )
        
        return DeploymentResponse(
            deployment_id=deployment_id,
            status="cancelled",
            message=f"Deployment {deployment_id} cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel deployment: {str(e)}"
        )


@router.get("/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    format: str = "json",
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Get logs for a specific deployment.
    
    Returns deployment logs in the specified format (json or text).
    Supports streaming for large log files.
    """
    try:
        logs = orchestrator.get_deployment_logs(deployment_id)
        
        if not logs:
            # Check if deployment exists
            deployment = await orchestrator.get_deployment_status(deployment_id)
            if not deployment:
                raise HTTPException(
                    status_code=404,
                    detail=f"Deployment {deployment_id} not found"
                )
            else:
                # Deployment exists but no logs yet
                logs = []
        
        if format.lower() == "text":
            # Return logs as plain text
            def generate_text_logs():
                for log_entry in logs:
                    timestamp = log_entry.get("timestamp", "")
                    event = log_entry.get("event", "")
                    message = log_entry.get("message", "")
                    yield f"[{timestamp}] {event}: {message}\n"
            
            return StreamingResponse(
                generate_text_logs(),
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename={deployment_id}_logs.txt"}
            )
        else:
            # Return logs as JSON (default)
            return {
                "deployment_id": deployment_id,
                "log_count": len(logs),
                "logs": logs
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment logs: {str(e)}"
        )


@router.get("/metrics", response_model=DeploymentMetricsResponse)
async def get_deployment_metrics(
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Get deployment statistics and metrics.
    
    Returns comprehensive metrics about deployment performance,
    success rates, and resource usage.
    """
    try:
        metrics = orchestrator.get_deployment_metrics()
        
        return DeploymentMetricsResponse(
            total_deployments=metrics.get("total_deployments", 0),
            successful_deployments=metrics.get("successful_deployments", 0),
            failed_deployments=metrics.get("failed_deployments", 0),
            cancelled_deployments=metrics.get("cancelled_deployments", 0),
            active_deployments=metrics.get("active_deployments", 0),
            queue_size=metrics.get("queue_size", 0),
            average_duration_seconds=metrics.get("average_duration_seconds", 0.0),
            retry_count=metrics.get("retry_count", 0),
            environment_usage=metrics.get("environment_usage", {})
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment metrics: {str(e)}"
        )


@router.get("/history")
async def get_deployment_history(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    environment_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Get deployment history with filtering and pagination.
    
    Returns a paginated list of deployments with optional filtering
    by status and environment.
    """
    try:
        # Get all active deployments (in a real implementation, this would query a database)
        all_deployments = orchestrator.get_active_deployments()
        
        # Apply filters
        filtered_deployments = []
        for deployment in all_deployments.values():
            # Filter by status if specified
            if status and deployment.status.value != status.lower():
                continue
            
            # Filter by environment if specified
            if environment_id and deployment.environment_id != environment_id:
                continue
            
            filtered_deployments.append(deployment)
        
        # Sort by start time (newest first)
        filtered_deployments.sort(key=lambda d: d.start_time, reverse=True)
        
        # Apply pagination
        total_count = len(filtered_deployments)
        paginated_deployments = filtered_deployments[offset:offset + limit]
        
        # Convert to response format
        deployment_list = []
        for deployment in paginated_deployments:
            deployment_dict = {
                "deployment_id": deployment.deployment_id,
                "plan_id": deployment.plan_id,
                "environment_id": deployment.environment_id,
                "status": deployment.status.value,
                "start_time": deployment.start_time.isoformat(),
                "end_time": deployment.end_time.isoformat() if deployment.end_time else None,
                "duration_seconds": deployment.duration_seconds,
                "artifacts_deployed": deployment.artifacts_deployed,
                "error_message": deployment.error_message,
                "retry_count": deployment.retry_count
            }
            deployment_list.append(deployment_dict)
        
        return {
            "deployments": deployment_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment history: {str(e)}"
        )


@router.post("/{deployment_id}/retry", response_model=DeploymentResponse)
async def retry_deployment(
    deployment_id: str,
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Retry a failed deployment.
    
    Attempts to retry a failed deployment with exponential backoff.
    Only failed deployments within retry limits can be retried.
    """
    try:
        new_deployment_id = await orchestrator.retry_failed_deployment(deployment_id)
        
        if not new_deployment_id:
            # Check deployment status to provide better error message
            deployment = await orchestrator.get_deployment_status(deployment_id)
            if not deployment:
                raise HTTPException(
                    status_code=404,
                    detail=f"Deployment {deployment_id} not found"
                )
            elif deployment.status != DeploymentStatus.FAILED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot retry deployment {deployment_id} in state {deployment.status.value}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Deployment {deployment_id} has exceeded retry limit"
                )
        
        return DeploymentResponse(
            deployment_id=new_deployment_id,
            status="pending",
            message=f"Deployment {deployment_id} retry initiated as {new_deployment_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retry deployment: {str(e)}"
        )


@router.get("/analytics/performance")
async def get_performance_analytics(
    time_range: str = "24h",
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Get deployment performance analytics.
    
    Returns performance metrics over the specified time range including
    throughput, success rates, and timing statistics.
    """
    try:
        # Get base metrics
        metrics = orchestrator.get_deployment_metrics()
        
        # Calculate performance analytics
        total_deployments = metrics.get("total_deployments", 0)
        successful_deployments = metrics.get("successful_deployments", 0)
        failed_deployments = metrics.get("failed_deployments", 0)
        
        success_rate = (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0
        failure_rate = (failed_deployments / total_deployments * 100) if total_deployments > 0 else 0
        
        # Calculate throughput (deployments per hour)
        # In a real implementation, this would use actual time-based data
        throughput_per_hour = total_deployments  # Simplified for demo
        
        return {
            "time_range": time_range,
            "performance_metrics": {
                "total_deployments": total_deployments,
                "success_rate_percentage": round(success_rate, 2),
                "failure_rate_percentage": round(failure_rate, 2),
                "average_duration_seconds": metrics.get("average_duration_seconds", 0.0),
                "throughput_per_hour": throughput_per_hour,
                "retry_rate_percentage": round((metrics.get("retry_count", 0) / total_deployments * 100) if total_deployments > 0 else 0, 2)
            },
            "resource_utilization": {
                "active_deployments": metrics.get("active_deployments", 0),
                "queue_size": metrics.get("queue_size", 0),
                "environment_usage": metrics.get("environment_usage", {})
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance analytics: {str(e)}"
        )


@router.get("/analytics/trends")
async def get_deployment_trends(
    metric: str = "success_rate",
    period: str = "hourly",
    current_user: dict = Depends(get_current_user),
    orchestrator: DeploymentOrchestrator = Depends(get_orchestrator)
):
    """
    Get deployment trend analytics.
    
    Returns trend data for the specified metric over time periods.
    Useful for monitoring deployment health and performance over time.
    """
    try:
        # Get current metrics
        current_metrics = orchestrator.get_deployment_metrics()
        
        # Generate trend data (in a real implementation, this would query historical data)
        trend_data = []
        
        if metric == "success_rate":
            total = current_metrics.get("total_deployments", 0)
            successful = current_metrics.get("successful_deployments", 0)
            rate = (successful / total * 100) if total > 0 else 0
            
            # Simulate trend data points
            for i in range(24):  # Last 24 hours/periods
                trend_data.append({
                    "timestamp": datetime.now().replace(hour=i, minute=0, second=0).isoformat(),
                    "value": max(0, rate + (i - 12) * 2)  # Simulate variation
                })
        
        elif metric == "throughput":
            base_throughput = current_metrics.get("total_deployments", 0)
            
            for i in range(24):
                trend_data.append({
                    "timestamp": datetime.now().replace(hour=i, minute=0, second=0).isoformat(),
                    "value": max(0, base_throughput + (i % 6) - 3)  # Simulate variation
                })
        
        elif metric == "average_duration":
            base_duration = current_metrics.get("average_duration_seconds", 60.0)
            
            for i in range(24):
                trend_data.append({
                    "timestamp": datetime.now().replace(hour=i, minute=0, second=0).isoformat(),
                    "value": max(10, base_duration + (i % 8) * 5)  # Simulate variation
                })
        
        return {
            "metric": metric,
            "period": period,
            "data_points": len(trend_data),
            "trend_data": trend_data,
            "summary": {
                "current_value": trend_data[-1]["value"] if trend_data else 0,
                "average_value": sum(point["value"] for point in trend_data) / len(trend_data) if trend_data else 0,
                "min_value": min(point["value"] for point in trend_data) if trend_data else 0,
                "max_value": max(point["value"] for point in trend_data) if trend_data else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment trends: {str(e)}"
        )


# Cleanup function for graceful shutdown
async def cleanup_orchestrator():
    """Cleanup orchestrator on shutdown"""
    global _orchestrator
    if _orchestrator:
        await _orchestrator.stop()
        _orchestrator = None