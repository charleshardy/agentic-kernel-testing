#!/usr/bin/env python3
"""
Minimal API server to test basic functionality.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

# Create minimal FastAPI app
app = FastAPI(title="Minimal Test API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Minimal Test API", "status": "running", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "message": "API is healthy",
        "data": {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@app.get("/api/v1/execution/active")
async def get_active_executions():
    """Get active executions - real implementation."""
    try:
        from execution.execution_service import get_execution_service
        
        service = get_execution_service()
        active_executions = service.get_active_executions()
        
        return {
            "success": True,
            "message": f"Retrieved {len(active_executions)} active executions",
            "data": {"executions": active_executions}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get active executions: {str(e)}",
            "data": {"error": str(e), "executions": []}
        }

@app.post("/api/v1/execution/test")
async def test_execution_service():
    """Test execution service import."""
    try:
        # Try to import execution service
        from execution.execution_service import get_execution_service
        service = get_execution_service()
        active = service.get_active_executions()
        
        return {
            "success": True,
            "message": "Execution service working",
            "data": {
                "active_executions": len(active),
                "service_type": str(type(service))
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Execution service failed: {str(e)}",
            "data": {"error": str(e)}
        }

@app.post("/api/v1/execution/{plan_id}/start")
async def start_execution_plan(plan_id: str):
    """Start execution of a test plan."""
    try:
        from execution.execution_service import get_execution_service
        from ai_generator.models import TestCase, TestType
        
        # Create some test cases for demonstration
        test_cases = [
            TestCase(
                id=f"test-{i}",
                name=f"Test execution {i}",
                description=f"Mock test case {i} for real execution testing",
                test_type=TestType.UNIT,
                target_subsystem="kernel/test",
                execution_time_estimate=5
            )
            for i in range(1, 4)
        ]
        
        service = get_execution_service()
        success = service.start_execution(
            plan_id=plan_id,
            test_cases=test_cases,
            created_by="demo_user",
            priority=5,
            timeout=60
        )
        
        if success:
            return {
                "success": True,
                "message": f"Execution plan {plan_id} started successfully",
                "data": {
                    "plan_id": plan_id,
                    "status": "running",
                    "test_count": len(test_cases),
                    "started_at": datetime.utcnow().isoformat()
                }
            }
        else:
            return {
                "success": False,
                "message": "Failed to start execution",
                "data": {"plan_id": plan_id}
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Execution start failed: {str(e)}",
            "data": {"error": str(e), "plan_id": plan_id}
        }

@app.get("/api/v1/execution/{plan_id}/status")
async def get_execution_status(plan_id: str):
    """Get execution status."""
    try:
        from execution.execution_service import get_execution_service
        
        service = get_execution_service()
        status_data = service.get_execution_status(plan_id)
        
        if status_data:
            return {
                "success": True,
                "message": "Execution status retrieved",
                "data": status_data
            }
        else:
            return {
                "success": False,
                "message": "Execution plan not found",
                "data": {"plan_id": plan_id}
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Status retrieval failed: {str(e)}",
            "data": {"error": str(e), "plan_id": plan_id}
        }

@app.get("/api/v1/execution/active")
async def get_active_executions():
    """Get active executions - real implementation."""
    try:
        from execution.execution_service import get_execution_service
        
        service = get_execution_service()
        active_executions = service.get_active_executions()
        
        return {
            "success": True,
            "message": f"Retrieved {len(active_executions)} active executions",
            "data": {"executions": active_executions}
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get active executions: {str(e)}",
            "data": {"error": str(e), "executions": []}
        }

if __name__ == "__main__":
    print("🚀 Starting Minimal Test API...")
    print("📍 Available endpoints:")
    print("  GET  /                              - Root endpoint")
    print("  GET  /api/v1/health                 - Health check")
    print("  GET  /api/v1/execution/active       - Get active executions")
    print("  POST /api/v1/execution/test         - Test execution service")
    print("  POST /api/v1/execution/{id}/start   - Start execution plan")
    print("  GET  /api/v1/execution/{id}/status  - Get execution status")
    print("  GET  /docs                          - API documentation")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )