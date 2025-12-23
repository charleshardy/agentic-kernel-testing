#!/usr/bin/env python3
"""
Complete API server with all endpoints needed by the frontend.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import traceback
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Complete Test Execution API",
    description="Complete API with all endpoints for the frontend",
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

# Mock data storage
mock_tests = {}
mock_executions = {}

@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint called")
    return {"message": "Complete Test Execution API", "status": "running", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check called")
    return {
        "success": True,
        "message": "System is healthy",
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": 100.0,
            "components": {
                "api": {"status": "healthy", "response_time_ms": 1.2},
                "database": {"status": "healthy", "connection_pool": "available"},
                "test_orchestrator": {"status": "healthy", "active_tests": 0},
                "environment_manager": {"status": "healthy", "available_environments": 5}
            },
            "metrics": {
                "cpu_usage": 0.05,
                "memory_usage": 0.3,
                "disk_usage": 0.073,
                "uptime_seconds": 100.0
            },
            "timestamp": datetime.utcnow().isoformat()
        },
        "errors": None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/health/metrics")
async def health_metrics():
    """Health metrics endpoint."""
    return {
        "success": True,
        "message": "System metrics retrieved",
        "data": {
            "active_tests": 0,
            "queued_tests": 0,
            "available_environments": 5,
            "total_environments": 5,
            "cpu_usage": 0.05,
            "memory_usage": 0.3,
            "disk_usage": 0.073,
            "network_io": {"bytes_sent": 1024, "bytes_received": 2048}
        }
    }

@app.post("/api/v1/auth/login")
async def login(credentials: Dict[str, str]):
    """Mock login endpoint."""
    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "access_token": "demo-token-123",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": get_demo_user()
        }
    }

@app.get("/api/v1/tests")
async def get_tests(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    test_type: Optional[str] = None,
    subsystem: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Get tests with pagination."""
    # Return mock test data
    tests = list(mock_tests.values())
    
    return {
        "success": True,
        "message": f"Retrieved {len(tests)} tests",
        "data": {
            "tests": tests,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": len(tests),
                "total_pages": 1,
                "has_next": False,
                "has_prev": False
            },
            "filters_applied": {
                "status": status,
                "test_type": test_type,
                "subsystem": subsystem
            }
        }
    }

@app.post("/api/v1/tests/generate-from-function")
async def generate_tests_from_function(
    function_name: str,
    file_path: str,
    subsystem: str = "unknown",
    max_tests: int = 10,
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Generate tests from function."""
    logger.info(f"Generating tests for function: {function_name}")
    
    # Create mock test cases
    generated_tests = []
    for i in range(max_tests):
        test_id = str(uuid.uuid4())
        test = {
            "id": test_id,
            "name": f"Test {function_name} - case {i+1}",
            "description": f"Generated test case {i+1} for function {function_name}",
            "test_type": "unit",
            "target_subsystem": subsystem,
            "code_paths": [file_path],
            "execution_time_estimate": 5,
            "test_script": f"# Test script for {function_name}\npass",
            "metadata": {
                "generated_from": "function",
                "source_function": function_name,
                "source_file": file_path
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "generation_info": {
                "method": "ai_function",
                "source_data": {"function_name": function_name, "file_path": file_path},
                "generated_at": datetime.utcnow().isoformat(),
                "ai_model": "mock-ai-model"
            },
            "execution_status": "never_run"
        }
        generated_tests.append(test)
        mock_tests[test_id] = test
    
    # Create execution plan
    plan_id = str(uuid.uuid4())
    execution_plan = {
        "plan_id": plan_id,
        "submission_id": str(uuid.uuid4()),
        "test_case_ids": [t["id"] for t in generated_tests],
        "priority": 5,
        "status": "queued",
        "created_at": datetime.utcnow(),
        "created_by": current_user["username"],
        "overall_status": "queued",
        "total_tests": len(generated_tests),
        "completed_tests": 0,
        "failed_tests": 0,
        "progress": 0.0,
        "started_at": datetime.utcnow().isoformat(),
        "estimated_completion": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
        "test_cases": [
            {
                "test_id": t["id"],
                "name": t["name"],
                "description": t["description"],
                "test_type": t["test_type"],
                "target_subsystem": t["target_subsystem"],
                "execution_status": "queued",
                "execution_time_estimate": t["execution_time_estimate"]
            }
            for t in generated_tests
        ]
    }
    mock_executions[plan_id] = execution_plan
    
    return {
        "success": True,
        "message": f"Generated {len(generated_tests)} test cases successfully",
        "data": {
            "generated_count": len(generated_tests),
            "test_ids": [t["id"] for t in generated_tests],
            "execution_plan_id": plan_id,
            "tests": generated_tests
        }
    }

@app.get("/api/v1/execution/active")
async def get_active_executions(current_user: Dict[str, Any] = Depends(get_demo_user)):
    """Get active executions."""
    logger.info("Getting active executions...")
    
    try:
        # Get executions from execution service
        from execution.execution_service import get_execution_service
        service = get_execution_service()
        service_executions = service.get_active_executions()
        
        # Combine with mock executions
        all_executions = service_executions + [
            exec_data for exec_data in mock_executions.values()
            if exec_data["status"] in ["queued", "running"]
        ]
        
        logger.info(f"Found {len(all_executions)} active executions")
        
        return {
            "success": True,
            "message": f"Retrieved {len(all_executions)} active executions",
            "data": {"executions": all_executions}
        }
        
    except Exception as e:
        logger.error(f"Error getting active executions: {e}")
        # Fallback to mock data only
        mock_active = [
            exec_data for exec_data in mock_executions.values()
            if exec_data["status"] in ["queued", "running"]
        ]
        
        return {
            "success": True,
            "message": f"Retrieved {len(mock_active)} active executions (fallback)",
            "data": {"executions": mock_active}
        }

@app.get("/api/v1/execution/{plan_id}/status")
async def get_execution_status(plan_id: str, current_user: Dict[str, Any] = Depends(get_demo_user)):
    """Get execution status."""
    logger.info(f"Getting execution status for: {plan_id}")
    
    try:
        # Try execution service first
        from execution.execution_service import get_execution_service
        service = get_execution_service()
        status_data = service.get_execution_status(plan_id)
        
        if status_data:
            return {
                "success": True,
                "message": "Execution status retrieved from service",
                "data": status_data
            }
    except Exception as e:
        logger.error(f"Error getting status from service: {e}")
    
    # Fallback to mock data
    if plan_id in mock_executions:
        return {
            "success": True,
            "message": "Execution status retrieved from mock data",
            "data": mock_executions[plan_id]
        }
    
    raise HTTPException(status_code=404, detail="Execution plan not found")

@app.post("/api/v1/execution/{plan_id}/start")
async def start_execution_plan(plan_id: str, current_user: Dict[str, Any] = Depends(get_demo_user)):
    """Start execution plan."""
    logger.info(f"Starting execution plan: {plan_id}")
    
    try:
        # Try to start with execution service
        from execution.execution_service import get_execution_service
        from ai_generator.models import TestCase, TestType
        
        if plan_id in mock_executions:
            # Get test cases from mock data
            exec_plan = mock_executions[plan_id]
            test_cases = []
            
            for test_data in exec_plan.get("test_cases", []):
                test_case = TestCase(
                    id=test_data["test_id"],
                    name=test_data["name"],
                    description=test_data["description"],
                    test_type=TestType.UNIT,
                    target_subsystem=test_data["target_subsystem"],
                    execution_time_estimate=test_data["execution_time_estimate"]
                )
                test_cases.append(test_case)
            
            service = get_execution_service()
            success = service.start_execution(
                plan_id=plan_id,
                test_cases=test_cases,
                created_by=current_user["username"],
                priority=5,
                timeout=60
            )
            
            if success:
                # Update mock data
                mock_executions[plan_id]["status"] = "running"
                mock_executions[plan_id]["overall_status"] = "running"
                
                return {
                    "success": True,
                    "message": f"Execution plan {plan_id} started successfully",
                    "data": {
                        "plan_id": plan_id,
                        "status": "running",
                        "started_by": current_user["username"],
                        "started_at": datetime.utcnow().isoformat(),
                        "test_count": len(test_cases)
                    }
                }
        
        raise HTTPException(status_code=404, detail="Execution plan not found")
        
    except Exception as e:
        logger.error(f"Error starting execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start execution: {str(e)}")

@app.post("/api/v1/execution/{plan_id}/cancel")
async def cancel_execution(plan_id: str, current_user: Dict[str, Any] = Depends(get_demo_user)):
    """Cancel execution."""
    logger.info(f"Cancelling execution: {plan_id}")
    
    try:
        # Try execution service
        from execution.execution_service import get_execution_service
        service = get_execution_service()
        success = service.cancel_execution(plan_id)
        
        # Update mock data
        if plan_id in mock_executions:
            mock_executions[plan_id]["status"] = "cancelled"
            mock_executions[plan_id]["overall_status"] = "cancelled"
        
        return {
            "success": True,
            "message": "Execution cancelled successfully",
            "data": {
                "plan_id": plan_id,
                "cancelled_by": current_user["username"],
                "cancelled_at": datetime.utcnow().isoformat(),
                "service_cancelled": success
            }
        }
        
    except Exception as e:
        logger.error(f"Error cancelling execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")

@app.get("/api/v1/results")
async def get_results(current_user: Dict[str, Any] = Depends(get_demo_user)):
    """Get test results."""
    return {
        "success": True,
        "message": "Test results retrieved",
        "data": {
            "results": [],
            "total": 0
        }
    }

@app.get("/api/v1/environments")
async def get_environments(current_user: Dict[str, Any] = Depends(get_demo_user)):
    """Get environments."""
    return {
        "success": True,
        "message": "Environments retrieved",
        "data": [
            {
                "id": "env-1",
                "name": "Virtual Environment 1",
                "status": "idle",
                "architecture": "x86_64"
            }
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Complete Test Execution API...")
    print("📍 Available endpoints:")
    print("  GET  /                              - Root endpoint")
    print("  GET  /api/v1/health                 - Health check")
    print("  GET  /api/v1/health/metrics         - System metrics")
    print("  POST /api/v1/auth/login             - Authentication")
    print("  GET  /api/v1/tests                  - Get tests")
    print("  POST /api/v1/tests/generate-from-function - Generate tests")
    print("  GET  /api/v1/execution/active       - Get active executions")
    print("  POST /api/v1/execution/{id}/start   - Start execution plan")
    print("  GET  /api/v1/execution/{id}/status  - Get execution status")
    print("  POST /api/v1/execution/{id}/cancel  - Cancel execution")
    print("  GET  /api/v1/results                - Get test results")
    print("  GET  /api/v1/environments           - Get environments")
    print("  GET  /docs                          - API documentation")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )