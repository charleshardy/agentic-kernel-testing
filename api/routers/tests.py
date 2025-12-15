"""Test submission and management endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status

from ..models import (
    APIResponse, ErrorResponse, TestSubmissionRequest, TestSubmissionResponse,
    TestCaseRequest, TestCaseResponse, CodeAnalysisRequest, CodeAnalysisResponse,
    PaginationParams
)
from ..auth import get_current_user, require_permission
from ai_generator.models import TestCase, TestType, RiskLevel, HardwareConfig
from ai_generator.interfaces import ITestGenerator, ITestOrchestrator

router = APIRouter()

# Mock data stores (in production, these would be database operations)
submitted_tests = {}
execution_plans = {}
code_analyses = {}


@router.post("/tests/submit", response_model=APIResponse)
async def submit_tests(
    submission: TestSubmissionRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Submit test cases for execution."""
    try:
        submission_id = str(uuid.uuid4())
        test_case_ids = []
        
        # Convert and validate test cases
        for test_req in submission.test_cases:
            test_id = str(uuid.uuid4())
            
            # Create hardware config if provided
            hardware_config = None
            if test_req.required_hardware:
                hw_req = test_req.required_hardware
                hardware_config = HardwareConfig(
                    architecture=hw_req.get("architecture", "x86_64"),
                    cpu_model=hw_req.get("cpu_model", "generic"),
                    memory_mb=hw_req.get("memory_mb", 2048),
                    storage_type=hw_req.get("storage_type", "ssd"),
                    peripherals=hw_req.get("peripherals", []),
                    is_virtual=hw_req.get("is_virtual", True),
                    emulator=hw_req.get("emulator", "qemu")
                )
            
            # Create test case
            test_case = TestCase(
                id=test_id,
                name=test_req.name,
                description=test_req.description,
                test_type=test_req.test_type,
                target_subsystem=test_req.target_subsystem,
                code_paths=test_req.code_paths,
                execution_time_estimate=test_req.execution_time_estimate,
                required_hardware=hardware_config,
                test_script=test_req.test_script,
                metadata=test_req.metadata
            )
            
            # Store test case
            submitted_tests[test_id] = {
                "test_case": test_case,
                "submission_id": submission_id,
                "submitted_by": current_user["username"],
                "submitted_at": datetime.utcnow(),
                "priority": submission.priority
            }
            
            test_case_ids.append(test_id)
        
        # Create execution plan
        plan_id = str(uuid.uuid4())
        estimated_completion = datetime.utcnow() + timedelta(
            minutes=sum(test.execution_time_estimate for test in submission.test_cases) // 60
        )
        
        execution_plans[plan_id] = {
            "submission_id": submission_id,
            "test_case_ids": test_case_ids,
            "priority": submission.priority,
            "target_environments": submission.target_environments,
            "webhook_url": submission.webhook_url,
            "status": "queued",
            "created_at": datetime.utcnow(),
            "estimated_completion": estimated_completion,
            "created_by": current_user["username"]
        }
        
        response = TestSubmissionResponse(
            submission_id=submission_id,
            test_case_ids=test_case_ids,
            execution_plan_id=plan_id,
            estimated_completion_time=estimated_completion,
            status="queued",
            webhook_url=submission.webhook_url
        )
        
        return APIResponse(
            success=True,
            message=f"Successfully submitted {len(test_case_ids)} test cases",
            data=response.model_dump()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to submit tests: {str(e)}"
        )


@router.get("/tests", response_model=APIResponse)
async def list_tests(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    test_type: Optional[TestType] = Query(None, description="Filter by test type"),
    subsystem: Optional[str] = Query(None, description="Filter by subsystem"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """List submitted test cases with pagination and filtering."""
    try:
        # Filter tests
        filtered_tests = []
        for test_id, test_data in submitted_tests.items():
            test_case = test_data["test_case"]
            
            # Apply filters
            if test_type and test_case.test_type != test_type:
                continue
            if subsystem and test_case.target_subsystem != subsystem:
                continue
            # Status filtering would require execution status lookup
            
            test_response = TestCaseResponse(
                id=test_case.id,
                name=test_case.name,
                description=test_case.description,
                test_type=test_case.test_type,
                target_subsystem=test_case.target_subsystem,
                code_paths=test_case.code_paths,
                execution_time_estimate=test_case.execution_time_estimate,
                required_hardware=test_case.required_hardware.to_dict() if test_case.required_hardware else None,
                test_script=test_case.test_script,
                expected_outcome=test_case.expected_outcome.to_dict() if test_case.expected_outcome else None,
                test_metadata=test_case.metadata or {},
                created_at=test_data["submitted_at"],
                updated_at=test_data["submitted_at"]
            )
            
            filtered_tests.append(test_response.model_dump())
        
        # Pagination
        total_items = len(filtered_tests)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_tests = filtered_tests[start_idx:end_idx]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_tests)} test cases",
            data={
                "tests": paginated_tests,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": (total_items + page_size - 1) // page_size,
                    "has_next": end_idx < total_items,
                    "has_prev": page > 1
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tests: {str(e)}"
        )


@router.get("/tests/{test_id}", response_model=APIResponse)
async def get_test(
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get details of a specific test case."""
    if test_id not in submitted_tests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    test_data = submitted_tests[test_id]
    test_case = test_data["test_case"]
    
    response = TestCaseResponse(
        id=test_case.id,
        name=test_case.name,
        description=test_case.description,
        test_type=test_case.test_type,
        target_subsystem=test_case.target_subsystem,
        code_paths=test_case.code_paths,
        execution_time_estimate=test_case.execution_time_estimate,
        required_hardware=test_case.required_hardware.to_dict() if test_case.required_hardware else None,
        test_script=test_case.test_script,
        expected_outcome=test_case.expected_outcome.to_dict() if test_case.expected_outcome else None,
        test_metadata=test_case.metadata or {},
        created_at=test_data["submitted_at"],
        updated_at=test_data["submitted_at"]
    )
    
    return APIResponse(
        success=True,
        message="Test case retrieved successfully",
        data={
            "test": response.model_dump(),
            "submission_info": {
                "submission_id": test_data["submission_id"],
                "submitted_by": test_data["submitted_by"],
                "submitted_at": test_data["submitted_at"].isoformat(),
                "priority": test_data["priority"]
            }
        }
    )


@router.delete("/tests/{test_id}", response_model=APIResponse)
async def delete_test(
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:delete"))
):
    """Delete a test case (if not yet executed)."""
    if test_id not in submitted_tests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    # Check if test is already running (in production, check execution status)
    # For now, just delete from submitted tests
    del submitted_tests[test_id]
    
    return APIResponse(
        success=True,
        message="Test case deleted successfully",
        data={"deleted_test_id": test_id}
    )


@router.post("/tests/analyze-code", response_model=APIResponse)
async def analyze_code(
    analysis_request: CodeAnalysisRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Analyze code changes and generate test recommendations."""
    try:
        analysis_id = str(uuid.uuid4())
        
        # Mock code analysis (in production, use actual AI generator)
        analysis = CodeAnalysisResponse(
            analysis_id=analysis_id,
            commit_sha=analysis_request.commit_sha or "abc123def456",
            changed_files=[
                "drivers/net/ethernet/intel/e1000e/netdev.c",
                "include/linux/netdevice.h"
            ],
            changed_functions=[
                {
                    "name": "e1000e_setup_rx_resources",
                    "file_path": "drivers/net/ethernet/intel/e1000e/netdev.c",
                    "line_number": 1234,
                    "signature": "int e1000e_setup_rx_resources(struct e1000_adapter *adapter)",
                    "subsystem": "networking"
                }
            ],
            affected_subsystems=["networking", "memory_management"],
            impact_score=0.7,
            risk_level=RiskLevel.MEDIUM,
            suggested_test_types=[TestType.UNIT, TestType.INTEGRATION, TestType.PERFORMANCE],
            generated_tests=[],  # Would be populated by actual test generation
            analysis_timestamp=datetime.utcnow()
        )
        
        # Store analysis
        code_analyses[analysis_id] = {
            "analysis": analysis,
            "request": analysis_request,
            "analyzed_by": current_user["username"],
            "analyzed_at": datetime.utcnow()
        }
        
        return APIResponse(
            success=True,
            message="Code analysis completed successfully",
            data=analysis.model_dump()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code analysis failed: {str(e)}"
        )


@router.get("/tests/analyses", response_model=APIResponse)
async def list_code_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """List code analyses with pagination."""
    try:
        analyses_list = []
        for analysis_id, analysis_data in code_analyses.items():
            analysis = analysis_data["analysis"]
            analyses_list.append({
                "analysis_id": analysis_id,
                "commit_sha": analysis.commit_sha,
                "impact_score": analysis.impact_score,
                "risk_level": analysis.risk_level,
                "affected_subsystems": analysis.affected_subsystems,
                "analyzed_by": analysis_data["analyzed_by"],
                "analyzed_at": analysis_data["analyzed_at"].isoformat()
            })
        
        # Pagination
        total_items = len(analyses_list)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_analyses = analyses_list[start_idx:end_idx]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_analyses)} code analyses",
            data={
                "analyses": paginated_analyses,
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
            detail=f"Failed to retrieve analyses: {str(e)}"
        )


@router.get("/tests/analyses/{analysis_id}", response_model=APIResponse)
async def get_code_analysis(
    analysis_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get details of a specific code analysis."""
    if analysis_id not in code_analyses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Code analysis not found"
        )
    
    analysis_data = code_analyses[analysis_id]
    
    return APIResponse(
        success=True,
        message="Code analysis retrieved successfully",
        data={
            "analysis": analysis_data["analysis"].model_dump(),
            "metadata": {
                "analyzed_by": analysis_data["analyzed_by"],
                "analyzed_at": analysis_data["analyzed_at"].isoformat(),
                "request": analysis_data["request"].model_dump()
            }
        }
    )