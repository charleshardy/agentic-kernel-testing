#!/usr/bin/env python3
"""
Debug API server with better error handling and logging.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(title="Debug Test API", version="1.0.0")

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
    logger.info("Root endpoint called")
    return {"message": "Debug Test API", "status": "running", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check called")
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
    """Get active executions with detailed logging."""
    logger.info("Getting active executions...")
    
    try:
        logger.info("Importing execution service...")
        from execution.execution_service import get_execution_service
        
        logger.info("Getting service instance...")
        service = get_execution_service()
        
        logger.info("Calling get_active_executions...")
        active_executions = service.get_active_executions()
        
        logger.info(f"Found {len(active_executions)} active executions")
        
        result = {
            "success": True,
            "message": f"Retrieved {len(active_executions)} active executions",
            "data": {"executions": active_executions}
        }
        
        logger.info("Returning result...")
        return result
        
    except Exception as e:
        logger.error(f"Error in get_active_executions: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Failed to get active executions: {str(e)}",
            "data": {"error": str(e), "executions": []}
        }

@app.post("/api/v1/execution/{plan_id}/start")
async def start_execution_plan(plan_id: str):
    """Start execution with detailed logging."""
    logger.info(f"Starting execution plan: {plan_id}")
    
    try:
        logger.info("Importing dependencies...")
        from execution.execution_service import get_execution_service
        from ai_generator.models import TestCase, TestType
        
        logger.info("Creating test cases...")
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
        
        logger.info(f"Created {len(test_cases)} test cases")
        
        logger.info("Getting execution service...")
        service = get_execution_service()
        
        logger.info("Starting execution...")
        success = service.start_execution(
            plan_id=plan_id,
            test_cases=test_cases,
            created_by="demo_user",
            priority=5,
            timeout=60
        )
        
        logger.info(f"Execution start result: {success}")
        
        if success:
            result = {
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
            result = {
                "success": False,
                "message": "Failed to start execution",
                "data": {"plan_id": plan_id}
            }
        
        logger.info("Returning start result...")
        return result
            
    except Exception as e:
        logger.error(f"Error in start_execution_plan: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Execution start failed: {str(e)}",
            "data": {"error": str(e), "plan_id": plan_id}
        }

@app.get("/api/v1/execution/{plan_id}/status")
async def get_execution_status(plan_id: str):
    """Get execution status with detailed logging."""
    logger.info(f"Getting execution status for: {plan_id}")
    
    try:
        logger.info("Importing execution service...")
        from execution.execution_service import get_execution_service
        
        logger.info("Getting service instance...")
        service = get_execution_service()
        
        logger.info("Getting execution status...")
        status_data = service.get_execution_status(plan_id)
        
        logger.info(f"Status data retrieved: {status_data is not None}")
        
        if status_data:
            result = {
                "success": True,
                "message": "Execution status retrieved",
                "data": status_data
            }
        else:
            result = {
                "success": False,
                "message": "Execution plan not found",
                "data": {"plan_id": plan_id}
            }
        
        logger.info("Returning status result...")
        return result
            
    except Exception as e:
        logger.error(f"Error in get_execution_status: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Status retrieval failed: {str(e)}",
            "data": {"error": str(e), "plan_id": plan_id}
        }

if __name__ == "__main__":
    print("🚀 Starting Debug Test API...")
    print("📍 Available endpoints:")
    print("  GET  /                              - Root endpoint")
    print("  GET  /api/v1/health                 - Health check")
    print("  GET  /api/v1/execution/active       - Get active executions")
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