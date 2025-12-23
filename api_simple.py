#!/usr/bin/env python3
"""
Simplified API server without orchestrator auto-start to test execution functionality.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Import only the essential components
from api.models import APIResponse
from execution.execution_service import get_execution_service

# Create simple FastAPI app
app = FastAPI(
    title="Simple Test Execution API",
    description="Simplified API for testing execution functionality",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Simple auth for testing
def get_demo_user():
    """Return demo user for testing."""
    return {
        "username": "demo",
        "user_id": "demo-001", 
        "email": "demo@example.com",
        "permissions": ["test:submit", "test:read", "test:delete", "status:read"],
        "is_active": True
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Simple Test Execution API", "status": "running"}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return APIResponse(
        success=True,
        message="API is healthy",
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "execution_service": "available"
        }
    )

@app.get("/api/v1/execution/active")
async def get_active_executions(current_user: Dict[str, Any] = Depends(get_demo_user)):
    """Get all currently active executions."""
    try:
        execution_service = get_execution_service()
        active_executions = execution_service.get_active_executions()
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(active_executions)} active executions",
            data={"executions": active_executions}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active executions: {str(e)}"
        )

@app.get("/api/v1/execution/{plan_id}/status")
async def get_execution_status(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Get detailed execution status for a specific plan."""
    try:
        execution_service = get_execution_service()
        status_data = execution_service.get_execution_status(plan_id)
        
        if status_data:
            return APIResponse(
                success=True,
                message="Execution status retrieved",
                data=status_data
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Execution plan not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get execution status: {str(e)}"
        )

@app.post("/api/v1/execution/{plan_id}/start")
async def start_execution_plan(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Start execution of a queued execution plan."""
    try:
        # For testing, create some mock test cases
        from ai_generator.models import TestCase, TestType
        
        test_cases = [
            TestCase(
                id=f"test-{i}",
                name=f"Test case {i}",
                description=f"Mock test case {i} for execution testing",
                test_type=TestType.UNIT,
                target_subsystem="kernel/test",
                execution_time_estimate=5
            )
            for i in range(1, 4)
        ]
        
        execution_service = get_execution_service()
        
        success = execution_service.start_execution(
            plan_id=plan_id,
            test_cases=test_cases,
            created_by=current_user["username"],
            priority=5,
            timeout=60
        )
        
        if success:
            return APIResponse(
                success=True,
                message=f"Execution plan {plan_id} started successfully",
                data={
                    "plan_id": plan_id,
                    "status": "running",
                    "started_by": current_user["username"],
                    "started_at": datetime.utcnow().isoformat(),
                    "test_count": len(test_cases)
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to start test execution"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start execution plan: {str(e)}"
        )

@app.post("/api/v1/execution/{plan_id}/cancel")
async def cancel_execution(
    plan_id: str,
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Cancel a running execution plan."""
    try:
        execution_service = get_execution_service()
        success = execution_service.cancel_execution(plan_id)
        
        return APIResponse(
            success=True,
            message="Execution cancelled successfully" if success else "Execution plan updated",
            data={
                "plan_id": plan_id,
                "cancelled_by": current_user["username"],
                "cancelled_at": datetime.utcnow().isoformat(),
                "service_cancelled": success
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel execution: {str(e)}"
        )

if __name__ == "__main__":
    print("🚀 Starting Simple Test Execution API...")
    print("📍 Available endpoints:")
    print("  GET  /                              - Root endpoint")
    print("  GET  /api/v1/health                 - Health check")
    print("  GET  /api/v1/execution/active       - Get active executions")
    print("  GET  /api/v1/execution/{id}/status  - Get execution status")
    print("  POST /api/v1/execution/{id}/start   - Start execution")
    print("  POST /api/v1/execution/{id}/cancel  - Cancel execution")
    print("  GET  /docs                          - API documentation")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )