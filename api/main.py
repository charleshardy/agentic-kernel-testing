"""Main FastAPI application for the Agentic AI Testing System."""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import uvicorn
from typing import Optional
import os

from .routers import tests, status, results, health, auth, webhooks, environments
from .middleware import RequestLoggingMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from .auth import verify_token, get_current_user
from .models import APIResponse, ErrorResponse
from .orchestrator_integration import start_orchestrator, stop_orchestrator
from config.settings import Settings

# Initialize settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Testing System API",
    description="""
    REST API for the Agentic AI Testing System - an autonomous AI-powered testing platform 
    for Linux kernels and Board Support Packages (BSPs).
    
    ## Features
    
    * **Test Submission**: Submit test cases for execution across multiple hardware configurations
    * **Status Monitoring**: Query test execution status and progress
    * **Result Retrieval**: Retrieve detailed test results, coverage data, and failure analysis
    * **CI/CD Integration**: Webhook endpoints for version control system integration
    * **Authentication**: Secure API access with token-based authentication
    
    ## Authentication
    
    All API endpoints require authentication using Bearer tokens. Include your token in the 
    Authorization header:
    
    ```
    Authorization: Bearer <your-token>
    ```
    
    ## Rate Limiting
    
    API requests are rate-limited to prevent abuse. Current limits:
    - 1000 requests per hour for authenticated users
    - 100 requests per hour for unauthenticated requests
    
    ## Error Handling
    
    The API uses standard HTTP status codes and returns detailed error messages in JSON format.
    """,
    version="1.0.0",
    contact={
        "name": "Agentic AI Testing System",
        "url": "https://github.com/your-org/agentic-kernel-testing",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
if settings.api.rate_limit_enabled:
    # Convert hourly limit to per-minute, with a minimum of 100 per minute for tests
    requests_per_minute = max(settings.api.rate_limit_requests // 60, 100)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=requests_per_minute)

# Security scheme
security = HTTPBearer()

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(tests.router, prefix="/api/v1", tags=["Tests"])
app.include_router(status.router, prefix="/api/v1", tags=["Status"])
app.include_router(results.router, prefix="/api/v1", tags=["Results"])
app.include_router(environments.router, prefix="/api/v1", tags=["Environments"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["Webhooks"])


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint providing API information."""
    return APIResponse(
        success=True,
        message="Agentic AI Testing System API",
        data={
            "version": "1.0.0",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "openapi_url": "/openapi.json",
            "health_check": "/api/v1/health"
        }
    )


@app.get("/api/v1/info", response_model=APIResponse)
async def api_info(current_user: dict = Depends(get_current_user)):
    """Get API information for authenticated users."""
    return APIResponse(
        success=True,
        message="API Information",
        data={
            "user": current_user.get("username", "unknown"),
            "permissions": current_user.get("permissions", []),
            "rate_limits": {
                "requests_per_hour": 1000,
                "concurrent_tests": 50
            },
            "supported_features": [
                "test_submission",
                "status_monitoring", 
                "result_retrieval",
                "webhook_integration",
                "coverage_analysis",
                "performance_monitoring",
                "security_scanning"
            ]
        }
    )


def custom_openapi():
    """Generate custom OpenAPI schema with authentication."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your Bearer token"
        }
    }
    
    # Add security requirement to all endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method != "options":
                openapi_schema["paths"][path][method]["security"] = [
                    {"BearerAuth": []}
                ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("🚀 Starting Agentic AI Testing System API...")
    
    # Start the orchestrator service
    if start_orchestrator():
        print("✅ Test execution orchestrator started successfully")
    else:
        print("❌ Failed to start test execution orchestrator")
    
    print("🎯 API server ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown."""
    print("🛑 Shutting down Agentic AI Testing System API...")
    
    # Stop the orchestrator service
    if stop_orchestrator():
        print("✅ Test execution orchestrator stopped successfully")
    else:
        print("❌ Failed to stop test execution orchestrator gracefully")
    
    print("👋 API server shutdown complete")


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level="info" if not settings.api.debug else "debug"
    )