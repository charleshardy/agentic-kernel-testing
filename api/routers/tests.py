"""Test submission and management endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import Body
from fastapi import APIRouter, HTTPException, Depends, Query, status

from ..models import (
    APIResponse, ErrorResponse, TestSubmissionRequest, TestSubmissionResponse,
    TestCaseRequest, TestCaseResponse, CodeAnalysisRequest, CodeAnalysisResponse,
    PaginationParams
)
from ..auth import get_current_user, require_permission

def get_demo_user():
    """Return demo user for testing."""
    return {
        "username": "demo",
        "user_id": "demo-001", 
        "email": "demo@example.com",
        "permissions": ["test:submit", "test:read", "test:delete"],
        "is_active": True
    }
from ai_generator.models import TestCase, TestType, RiskLevel, HardwareConfig
from ai_generator.interfaces import ITestGenerator, ITestOrchestrator

router = APIRouter()

# Mock data stores (in production, these would be database operations)
submitted_tests = {}
execution_plans = {}
code_analyses = {}


@router.post("/auth/demo-login", response_model=APIResponse)
async def demo_login():
    """Demo login endpoint that returns a token for testing without credentials."""
    from ..auth import create_access_token
    
    # Create token for demo user
    demo_user = {
        "user_id": "demo-001",
        "username": "demo", 
        "email": "demo@example.com",
        "permissions": ["test:submit", "test:read", "test:delete"],
        "is_active": True
    }
    
    token = create_access_token(demo_user)
    
    return APIResponse(
        success=True,
        message="Demo login successful",
        data={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user_info": demo_user
        }
    )


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
            
            # Create generation metadata for manual submission
            generation_info = {
                "method": "manual",
                "source_data": {
                    "submitted_by": current_user["username"],
                    "submission_type": "manual_api"
                },
                "generated_at": datetime.utcnow().isoformat(),
                "ai_model": None,
                "generation_params": {}
            }
            
            # Store test case
            submitted_tests[test_id] = {
                "test_case": test_case,
                "submission_id": submission_id,
                "submitted_by": current_user["username"],
                "submitted_at": datetime.utcnow(),
                "priority": submission.priority,
                "generation_info": generation_info,
                "execution_status": "never_run",
                "last_execution_at": None,
                "tags": ["manual"],
                "is_favorite": False,
                "updated_at": datetime.utcnow()
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
    test_type: Optional[str] = Query(None, description="Filter by test type"),
    subsystem: Optional[str] = Query(None, description="Filter by subsystem"),
    status_filter: Optional[str] = Query(None, description="Filter by execution status"),
    generation_method: Optional[str] = Query(None, description="Filter by generation method"),
    date_range_start: Optional[str] = Query(None, description="Filter by creation date start (ISO format)"),
    date_range_end: Optional[str] = Query(None, description="Filter by creation date end (ISO format)"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    search: Optional[str] = Query(None, description="Search in test name and description"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """List submitted test cases with advanced filtering, pagination, and sorting."""
    try:
        from datetime import datetime as dt
        
        # Parse date range filters
        date_start = None
        date_end = None
        if date_range_start:
            try:
                date_start = dt.fromisoformat(date_range_start.replace('Z', '+00:00'))
            except ValueError:
                pass
        if date_range_end:
            try:
                date_end = dt.fromisoformat(date_range_end.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Parse tags filter
        tag_filters = []
        if tags:
            tag_filters = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Filter tests
        filtered_tests = []
        for test_id, test_data in submitted_tests.items():
            test_case = test_data["test_case"]
            
            # Apply type filter
            if test_type and test_case.test_type.value != test_type:
                continue
                
            # Apply subsystem filter
            if subsystem and test_case.target_subsystem.lower() != subsystem.lower():
                continue
                
            # Apply status filter
            execution_status = test_data.get("execution_status", "never_run")
            if status_filter and execution_status != status_filter:
                continue
                
            # Apply generation method filter
            generation_info = test_data.get("generation_info")
            if generation_method:
                if not generation_info or generation_info.get("method") != generation_method:
                    continue
                    
            # Apply date range filter
            created_at = test_data["submitted_at"]
            if date_start and created_at < date_start:
                continue
            if date_end and created_at > date_end:
                continue
                
            # Apply tags filter
            test_tags = test_data.get("tags", [])
            if tag_filters and not any(tag in test_tags for tag in tag_filters):
                continue
                
            # Apply search filter
            if search:
                search_lower = search.lower()
                if (search_lower not in test_case.name.lower() and 
                    search_lower not in test_case.description.lower()):
                    continue
            
            # Create enhanced test response
            test_response = TestCaseResponse(
                id=test_case.id,
                name=test_case.name,
                description=test_case.description,
                test_type=test_case.test_type,
                target_subsystem=test_case.target_subsystem,
                code_paths=test_case.code_paths,
                execution_time_estimate=test_case.execution_time_estimate,
                hardware_config_id=None,
                required_hardware=test_case.required_hardware.to_dict() if test_case.required_hardware else None,
                test_script=test_case.test_script,
                expected_outcome=test_case.expected_outcome.to_dict() if test_case.expected_outcome else None,
                test_metadata=test_case.metadata or {},
                generation_info=generation_info,
                execution_status=execution_status,
                last_execution_at=test_data.get("last_execution_at"),
                tags=test_tags,
                is_favorite=test_data.get("is_favorite", False),
                created_at=test_data["submitted_at"],
                updated_at=test_data.get("updated_at", test_data["submitted_at"])
            )
            
            filtered_tests.append(test_response)
        
        # Sort tests
        reverse_sort = sort_order.lower() == "desc"
        if sort_by == "name":
            filtered_tests.sort(key=lambda x: x.name.lower(), reverse=reverse_sort)
        elif sort_by == "test_type":
            filtered_tests.sort(key=lambda x: x.test_type.value, reverse=reverse_sort)
        elif sort_by == "target_subsystem":
            filtered_tests.sort(key=lambda x: x.target_subsystem.lower(), reverse=reverse_sort)
        elif sort_by == "execution_status":
            filtered_tests.sort(key=lambda x: x.execution_status, reverse=reverse_sort)
        elif sort_by == "updated_at":
            filtered_tests.sort(key=lambda x: x.updated_at, reverse=reverse_sort)
        else:  # Default to created_at
            filtered_tests.sort(key=lambda x: x.created_at, reverse=reverse_sort)
        
        # Pagination
        total_items = len(filtered_tests)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_tests = filtered_tests[start_idx:end_idx]
        
        # Convert to dict for response
        paginated_tests_dict = [test.model_dump() for test in paginated_tests]
        
        # Build applied filters response
        applied_filters = {
            "test_type": test_type,
            "subsystem": subsystem,
            "status": status_filter,
            "generation_method": generation_method,
            "date_range": [date_range_start, date_range_end] if date_range_start or date_range_end else None,
            "tags": tag_filters if tag_filters else None,
            "search": search
        }
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_tests_dict)} test cases (filtered from {total_items} total)",
            data={
                "tests": paginated_tests_dict,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": (total_items + page_size - 1) // page_size if total_items > 0 else 0,
                    "has_next": end_idx < total_items,
                    "has_prev": page > 1
                },
                "filters_applied": applied_filters,
                "sort": {
                    "sort_by": sort_by,
                    "sort_order": sort_order
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


@router.post("/tests/generate-from-diff", response_model=APIResponse)
async def generate_tests_from_diff(
    diff_content: str,
    max_tests: int = Query(20, ge=1, le=100, description="Maximum tests to generate"),
    test_types: List[str] = Query(["unit"], description="Types of tests to generate"),
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Auto-generate test cases from code diff using AI."""
    try:
        from ai_generator.test_generator import AITestGenerator
        from ai_generator.models import TestType as AITestType
        
        # Initialize AI generator
        generator = AITestGenerator()
        
        # Analyze the code changes
        analysis = generator.analyze_code_changes(diff_content)
        
        # Generate test cases
        generated_tests = generator.generate_test_cases(analysis)
        
        # Limit to requested number
        generated_tests = generated_tests[:max_tests]
        
        # Convert to API format and store
        test_case_ids = []
        submission_id = str(uuid.uuid4())
        generation_timestamp = datetime.utcnow()
        
        for test_case in generated_tests:
            test_id = test_case.id
            
            # Create generation metadata
            generation_info = {
                "method": "ai_diff",
                "source_data": {
                    "diff_content": diff_content[:1000] + "..." if len(diff_content) > 1000 else diff_content,
                    "diff_size": len(diff_content),
                    "analysis_id": analysis.id if hasattr(analysis, 'id') else None
                },
                "generated_at": generation_timestamp.isoformat(),
                "ai_model": "ai_test_generator",  # Could be made configurable
                "generation_params": {
                    "max_tests": max_tests,
                    "test_types": test_types,
                    "affected_subsystems": analysis.affected_subsystems if hasattr(analysis, 'affected_subsystems') else []
                }
            }
            
            # Store test case with enhanced metadata
            submitted_tests[test_id] = {
                "test_case": test_case,
                "submission_id": submission_id,
                "submitted_by": current_user["username"],
                "submitted_at": generation_timestamp,
                "priority": 5,  # Default priority
                "auto_generated": True,
                "generation_info": generation_info,
                "execution_status": "never_run",
                "last_execution_at": None,
                "tags": ["ai_generated", "diff_based"] + (analysis.affected_subsystems if hasattr(analysis, 'affected_subsystems') else []),
                "is_favorite": False,
                "updated_at": generation_timestamp
            }
            
            test_case_ids.append(test_id)
        
        # Create execution plan
        plan_id = str(uuid.uuid4())
        estimated_completion = datetime.utcnow() + timedelta(
            minutes=sum(tc.execution_time_estimate for tc in generated_tests) // 60
        )
        
        execution_plans[plan_id] = {
            "submission_id": submission_id,
            "test_case_ids": test_case_ids,
            "priority": 5,
            "target_environments": None,
            "webhook_url": None,
            "status": "queued",
            "created_at": datetime.utcnow(),
            "estimated_completion": estimated_completion,
            "created_by": current_user["username"],
            "auto_generated": True
        }
        
        return APIResponse(
            success=True,
            message=f"Generated {len(generated_tests)} test cases from code diff",
            data={
                "submission_id": submission_id,
                "execution_plan_id": plan_id,
                "test_case_ids": test_case_ids,
                "generated_count": len(generated_tests),
                "analysis": {
                    "affected_subsystems": analysis.affected_subsystems,
                    "impact_score": analysis.impact_score,
                    "risk_level": analysis.risk_level,
                    "changed_files": analysis.changed_files
                },
                "estimated_completion": estimated_completion.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
        )


@router.post("/tests/generate-from-function", response_model=APIResponse)
async def generate_tests_from_function(
    function_name: str,
    file_path: str,
    subsystem: str = "unknown",
    max_tests: int = Query(10, ge=1, le=50, description="Maximum tests to generate"),
    include_property_tests: bool = Query(True, description="Include property-based tests"),
    current_user: Dict[str, Any] = Depends(get_demo_user)
):
    """Auto-generate test cases for a specific function using AI."""
    try:
        from ai_generator.test_generator import AITestGenerator
        from ai_generator.models import Function
        
        # Initialize AI generator
        generator = AITestGenerator()
        
        # Create function object
        function = Function(
            name=function_name,
            file_path=file_path,
            line_number=1,  # Default
            subsystem=subsystem
        )
        
        # Generate regular test cases
        generated_tests = generator._generate_function_tests(function, min_tests=max_tests)
        
        # Generate property tests if requested
        if include_property_tests:
            property_tests = generator.generate_property_tests([function])
            generated_tests.extend(property_tests)
        
        # Convert to API format and store
        test_case_ids = []
        submission_id = str(uuid.uuid4())
        generation_timestamp = datetime.utcnow()
        
        for test_case in generated_tests:
            test_id = test_case.id
            
            # Create generation metadata
            generation_info = {
                "method": "ai_function",
                "source_data": {
                    "function_name": function_name,
                    "file_path": file_path,
                    "subsystem": subsystem,
                    "function_signature": f"{function_name}(...)"  # Could be enhanced with actual signature
                },
                "generated_at": generation_timestamp.isoformat(),
                "ai_model": "ai_test_generator",
                "generation_params": {
                    "max_tests": max_tests,
                    "include_property_tests": include_property_tests,
                    "target_function": function_name
                }
            }
            
            # Store test case with enhanced metadata
            submitted_tests[test_id] = {
                "test_case": test_case,
                "submission_id": submission_id,
                "submitted_by": current_user["username"],
                "submitted_at": generation_timestamp,
                "priority": 5,
                "auto_generated": True,
                "generation_info": generation_info,
                "execution_status": "never_run",
                "last_execution_at": None,
                "tags": ["ai_generated", "function_based", subsystem],
                "is_favorite": False,
                "updated_at": generation_timestamp
            }
            
            test_case_ids.append(test_id)
        
        # Create execution plan
        plan_id = str(uuid.uuid4())
        estimated_completion = datetime.utcnow() + timedelta(
            minutes=sum(tc.execution_time_estimate for tc in generated_tests) // 60
        )
        
        execution_plans[plan_id] = {
            "submission_id": submission_id,
            "test_case_ids": test_case_ids,
            "priority": 5,
            "target_environments": None,
            "webhook_url": None,
            "status": "queued",
            "created_at": datetime.utcnow(),
            "estimated_completion": estimated_completion,
            "created_by": current_user["username"],
            "auto_generated": True
        }
        
        return APIResponse(
            success=True,
            message=f"Generated {len(generated_tests)} test cases for function {function_name}",
            data={
                "submission_id": submission_id,
                "execution_plan_id": plan_id,
                "test_case_ids": test_case_ids,
                "generated_count": len(generated_tests),
                "function": {
                    "name": function_name,
                    "file_path": file_path,
                    "subsystem": subsystem
                },
                "estimated_completion": estimated_completion.isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
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