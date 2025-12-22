"""Test execution status monitoring endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status

from ..models import (
    APIResponse, TestExecutionStatus, ExecutionPlanStatus, 
    WebhookEvent, PaginationParams
)
from ..auth import get_current_user, require_permission
from ai_generator.models import TestStatus
from ..orchestrator_integration import get_orchestrator

router = APIRouter()

# Mock execution status data (fallback when orchestrator not available)
execution_statuses = {}
plan_statuses = {}
webhook_events = {}


def initialize_mock_data():
    """Initialize some mock execution data for demonstration."""
    # Mock execution plan
    plan_id = "plan-001"
    test_ids = ["test-001", "test-002", "test-003"]
    
    plan_statuses[plan_id] = {
        "plan_id": plan_id,
        "submission_id": "sub-001",
        "overall_status": "running",
        "total_tests": 3,
        "completed_tests": 1,
        "failed_tests": 0,
        "progress": 0.33,
        "started_at": datetime.utcnow() - timedelta(minutes=10),
        "estimated_completion": datetime.utcnow() + timedelta(minutes=20)
    }
    
    # Mock test execution statuses
    execution_statuses["test-001"] = {
        "test_id": "test-001",
        "status": TestStatus.PASSED,
        "progress": 1.0,
        "environment_id": "env-001",
        "started_at": datetime.utcnow() - timedelta(minutes=10),
        "completed_at": datetime.utcnow() - timedelta(minutes=5),
        "message": "Test completed successfully"
    }
    
    execution_statuses["test-002"] = {
        "test_id": "test-002", 
        "status": TestStatus.FAILED,
        "progress": 1.0,
        "environment_id": "env-002",
        "started_at": datetime.utcnow() - timedelta(minutes=8),
        "completed_at": datetime.utcnow() - timedelta(minutes=3),
        "message": "Test failed with kernel panic"
    }
    
    execution_statuses["test-003"] = {
        "test_id": "test-003",
        "status": TestStatus.PASSED,
        "progress": 0.6,
        "environment_id": "env-003", 
        "started_at": datetime.utcnow() - timedelta(minutes=5),
        "estimated_completion": datetime.utcnow() + timedelta(minutes=8),
        "message": "Running performance benchmarks"
    }


# Initialize mock data
initialize_mock_data()


@router.get("/status/plans/{plan_id}", response_model=APIResponse)
async def get_execution_plan_status(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get execution status for a specific test plan."""
    if plan_id not in plan_statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution plan not found"
        )
    
    plan_data = plan_statuses[plan_id]
    
    # Get individual test statuses
    test_statuses = []
    for test_id in ["test-001", "test-002", "test-003"]:  # Mock test IDs
        if test_id in execution_statuses:
            test_data = execution_statuses[test_id]
            test_status = TestExecutionStatus(
                test_id=test_data["test_id"],
                status=test_data["status"],
                progress=test_data["progress"],
                environment_id=test_data["environment_id"],
                started_at=test_data["started_at"],
                estimated_completion=test_data.get("estimated_completion"),
                message=test_data["message"]
            )
            test_statuses.append(test_status)
    
    plan_status = ExecutionPlanStatus(
        plan_id=plan_data["plan_id"],
        submission_id=plan_data["submission_id"],
        overall_status=plan_data["overall_status"],
        total_tests=plan_data["total_tests"],
        completed_tests=plan_data["completed_tests"],
        failed_tests=plan_data["failed_tests"],
        progress=plan_data["progress"],
        test_statuses=test_statuses,
        started_at=plan_data["started_at"],
        completed_at=plan_data.get("completed_at"),
        estimated_completion=plan_data.get("estimated_completion")
    )
    
    return APIResponse(
        success=True,
        message="Execution plan status retrieved successfully",
        data=plan_status.dict()
    )


@router.get("/status/tests/{test_id}", response_model=APIResponse)
async def get_test_execution_status(
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get execution status for a specific test."""
    if test_id not in execution_statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test execution not found"
        )
    
    test_data = execution_statuses[test_id]
    
    test_status = TestExecutionStatus(
        test_id=test_data["test_id"],
        status=test_data["status"],
        progress=test_data["progress"],
        environment_id=test_data["environment_id"],
        started_at=test_data["started_at"],
        estimated_completion=test_data.get("estimated_completion"),
        message=test_data["message"]
    )
    
    # Add additional execution details
    execution_details = {
        "test_status": test_status.dict(),
        "execution_log": [
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                "level": "INFO",
                "message": "Test execution started"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=8)).isoformat(),
                "level": "INFO", 
                "message": "Environment provisioned successfully"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "level": "INFO",
                "message": "Kernel deployed and booted"
            }
        ],
        "resource_usage": {
            "cpu_usage_percent": 45.2,
            "memory_usage_mb": 2048,
            "disk_io_mb": 156.7,
            "network_io_mb": 23.4
        }
    }
    
    return APIResponse(
        success=True,
        message="Test execution status retrieved successfully",
        data=execution_details
    )


@router.get("/status/plans", response_model=APIResponse)
async def list_execution_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """List execution plans with pagination and filtering."""
    try:
        plans_list = []
        for plan_id, plan_data in plan_statuses.items():
            # Apply status filter
            if status_filter and plan_data["overall_status"] != status_filter:
                continue
                
            plans_list.append({
                "plan_id": plan_id,
                "submission_id": plan_data["submission_id"],
                "overall_status": plan_data["overall_status"],
                "total_tests": plan_data["total_tests"],
                "completed_tests": plan_data["completed_tests"],
                "failed_tests": plan_data["failed_tests"],
                "progress": plan_data["progress"],
                "started_at": plan_data["started_at"].isoformat(),
                "estimated_completion": plan_data.get("estimated_completion").isoformat() if plan_data.get("estimated_completion") else None
            })
        
        # Pagination
        total_items = len(plans_list)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_plans = plans_list[start_idx:end_idx]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_plans)} execution plans",
            data={
                "plans": paginated_plans,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": (total_items + page_size - 1) // page_size
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve execution plans: {str(e)}"
        )


@router.get("/status/active", response_model=APIResponse)
async def get_active_executions(
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get all currently active test executions."""
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator and orchestrator.is_running:
            # Get real data from orchestrator
            try:
                orchestrator_status = orchestrator.get_system_metrics()
                status_tracker = orchestrator.status_tracker
                
                # Get active execution plans from orchestrator
                active_plans = []
                if hasattr(status_tracker, 'get_active_plans'):
                    plans = status_tracker.get_active_plans()
                    for plan in plans:
                        active_plans.append({
                            "plan_id": plan.get('plan_id'),
                            "submission_id": plan.get('submission_id'),
                            "overall_status": plan.get('status', 'running'),
                            "total_tests": plan.get('total_tests', 0),
                            "completed_tests": plan.get('completed_tests', 0),
                            "failed_tests": plan.get('failed_tests', 0),
                            "progress": plan.get('progress', 0.0),
                            "started_at": plan.get('started_at', datetime.utcnow()).isoformat() if plan.get('started_at') else None,
                            "estimated_completion": plan.get('estimated_completion').isoformat() if plan.get('estimated_completion') else None
                        })
                
                return APIResponse(
                    success=True,
                    message=f"Found {len(active_plans)} active executions from orchestrator",
                    data=active_plans
                )
                
            except Exception as e:
                # Fall back to mock data if orchestrator fails
                print(f"Orchestrator error, using fallback: {e}")
        
        # Fallback to mock data when orchestrator not available
        active_tests = []
        active_plans = []
        
        # Find active tests
        for test_id, test_data in execution_statuses.items():
            if test_data["status"] in [TestStatus.PASSED, TestStatus.FAILED]:
                continue  # Skip completed tests
                
            active_tests.append({
                "test_id": test_id,
                "status": test_data["status"].value,
                "progress": test_data["progress"],
                "environment_id": test_data["environment_id"],
                "started_at": test_data["started_at"].isoformat(),
                "estimated_completion": test_data.get("estimated_completion").isoformat() if test_data.get("estimated_completion") else None,
                "message": test_data["message"]
            })
        
        # Find active plans
        for plan_id, plan_data in plan_statuses.items():
            if plan_data["overall_status"] in ["completed", "failed"]:
                continue  # Skip completed plans
                
            active_plans.append({
                "plan_id": plan_id,
                "submission_id": plan_data["submission_id"],
                "overall_status": plan_data["overall_status"],
                "progress": plan_data["progress"],
                "total_tests": plan_data["total_tests"],
                "completed_tests": plan_data["completed_tests"],
                "failed_tests": plan_data["failed_tests"],
                "started_at": plan_data["started_at"].isoformat(),
                "estimated_completion": plan_data.get("estimated_completion").isoformat() if plan_data.get("estimated_completion") else None
            })
        
        return APIResponse(
            success=True,
            message=f"Found {len(active_plans)} active executions (mock data)",
            data=active_plans
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active executions: {str(e)}"
        )


@router.post("/status/cancel/{test_id}", response_model=APIResponse)
async def cancel_test_execution(
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Cancel a running test execution."""
    if test_id not in execution_statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test execution not found"
        )
    
    test_data = execution_statuses[test_id]
    
    # Check if test can be cancelled
    if test_data["status"] in [TestStatus.PASSED, TestStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed test"
        )
    
    # Update status to cancelled (mock implementation)
    execution_statuses[test_id]["status"] = TestStatus.SKIPPED
    execution_statuses[test_id]["progress"] = 1.0
    execution_statuses[test_id]["message"] = f"Test cancelled by {current_user['username']}"
    execution_statuses[test_id]["completed_at"] = datetime.utcnow()
    
    return APIResponse(
        success=True,
        message="Test execution cancelled successfully",
        data={
            "test_id": test_id,
            "cancelled_by": current_user["username"],
            "cancelled_at": datetime.utcnow().isoformat()
        }
    )


@router.get("/status/events", response_model=APIResponse)
async def get_webhook_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    current_user: Dict[str, Any] = Depends(require_permission("status:read"))
):
    """Get webhook events for status updates."""
    try:
        # Mock webhook events
        events = [
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "test_started",
                "submission_id": "sub-001",
                "test_id": "test-001",
                "status": "running",
                "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                "data": {"environment_id": "env-001"}
            },
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "test_completed",
                "submission_id": "sub-001", 
                "test_id": "test-001",
                "status": "passed",
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "data": {"execution_time": 300, "coverage": 0.85}
            }
        ]
        
        # Apply event type filter
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        
        # Pagination
        total_items = len(events)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_events = events[start_idx:end_idx]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_events)} webhook events",
            data={
                "events": paginated_events,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": (total_items + page_size - 1) // page_size
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve webhook events: {str(e)}"
        )