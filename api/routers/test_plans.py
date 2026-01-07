"""Test Plans API router for managing test plan CRUD operations."""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from ..auth import get_current_user
from ..models import APIResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for test plans (in production, this would be a database)
test_plans_store: Dict[str, Dict[str, Any]] = {}

# Test plan model structures
class TestPlanCreate:
    """Test plan creation model."""
    def __init__(self, **data):
        self.name = data.get('name')
        self.description = data.get('description', '')
        self.test_ids = data.get('test_ids', [])
        self.tags = data.get('tags', [])
        self.execution_config = data.get('execution_config', {})
        self.status = data.get('status', 'draft')

class TestPlanUpdate:
    """Test plan update model."""
    def __init__(self, **data):
        self.name = data.get('name')
        self.description = data.get('description')
        self.test_ids = data.get('test_ids')
        self.tags = data.get('tags')
        self.execution_config = data.get('execution_config')
        self.status = data.get('status')


def create_test_plan_dict(plan_data: Dict[str, Any], plan_id: str, created_by: str) -> Dict[str, Any]:
    """Create a test plan dictionary with all required fields."""
    now = datetime.utcnow().isoformat()
    
    # Default execution config
    default_execution_config = {
        'environment_preference': 'qemu-x86',
        'priority': 5,
        'timeout_minutes': 60,
        'retry_failed': False,
        'parallel_execution': True
    }
    
    # Merge with provided config
    execution_config = default_execution_config.copy()
    if plan_data.get('execution_config'):
        execution_config.update(plan_data['execution_config'])
    
    # Calculate statistics (mock for now)
    test_count = len(plan_data.get('test_ids', []))
    
    return {
        'id': plan_id,
        'name': plan_data.get('name', ''),
        'description': plan_data.get('description', ''),
        'test_ids': plan_data.get('test_ids', []),
        'created_by': created_by,
        'created_at': now,
        'updated_at': now,
        'status': plan_data.get('status', 'draft'),
        'tags': plan_data.get('tags', []),
        'execution_config': execution_config,
        'statistics': {
            'total_executions': 0,
            'success_rate': 0.0,
            'avg_execution_time': 0,
            'last_execution': None
        }
    }


@router.get("/test-plans", response_model=APIResponse)
async def get_test_plans(
    current_user: dict = Depends(get_current_user)
):
    """Get all test plans."""
    try:
        plans = list(test_plans_store.values())
        
        logger.info(f"Retrieved {len(plans)} test plans for user {current_user.get('username')}")
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(plans)} test plans",
            data={
                "plans": plans,
                "total": len(plans)
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving test plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve test plans: {str(e)}"
        )


@router.get("/test-plans/{plan_id}", response_model=APIResponse)
async def get_test_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific test plan by ID."""
    try:
        if plan_id not in test_plans_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test plan {plan_id} not found"
            )
        
        plan = test_plans_store[plan_id]
        
        logger.info(f"Retrieved test plan {plan_id} for user {current_user.get('username')}")
        
        return APIResponse(
            success=True,
            message=f"Retrieved test plan {plan_id}",
            data=plan
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve test plan: {str(e)}"
        )


@router.post("/test-plans", response_model=APIResponse)
async def create_test_plan(
    plan_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new test plan."""
    try:
        # Validate required fields
        if not plan_data.get('name'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test plan name is required"
            )
        
        # Generate unique ID
        plan_id = str(uuid.uuid4())
        
        # Create test plan
        test_plan = create_test_plan_dict(
            plan_data, 
            plan_id, 
            current_user.get('username', 'unknown')
        )
        
        # Store the test plan
        test_plans_store[plan_id] = test_plan
        
        logger.info(f"Created test plan {plan_id} '{test_plan['name']}' by user {current_user.get('username')}")
        
        return APIResponse(
            success=True,
            message=f"Test plan '{test_plan['name']}' created successfully",
            data=test_plan
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating test plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test plan: {str(e)}"
        )


@router.put("/test-plans/{plan_id}", response_model=APIResponse)
async def update_test_plan(
    plan_id: str,
    plan_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing test plan."""
    try:
        if plan_id not in test_plans_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test plan {plan_id} not found"
            )
        
        existing_plan = test_plans_store[plan_id]
        
        # Update fields that are provided
        if 'name' in plan_data:
            existing_plan['name'] = plan_data['name']
        if 'description' in plan_data:
            existing_plan['description'] = plan_data['description']
        if 'test_ids' in plan_data:
            existing_plan['test_ids'] = plan_data['test_ids']
        if 'tags' in plan_data:
            existing_plan['tags'] = plan_data['tags']
        if 'execution_config' in plan_data:
            existing_plan['execution_config'].update(plan_data['execution_config'])
        if 'status' in plan_data:
            existing_plan['status'] = plan_data['status']
        
        # Update timestamp
        existing_plan['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated test plan {plan_id} by user {current_user.get('username')}")
        
        return APIResponse(
            success=True,
            message=f"Test plan '{existing_plan['name']}' updated successfully",
            data=existing_plan
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating test plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update test plan: {str(e)}"
        )


@router.delete("/test-plans/{plan_id}", response_model=APIResponse)
async def delete_test_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a test plan."""
    try:
        if plan_id not in test_plans_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test plan {plan_id} not found"
            )
        
        plan_name = test_plans_store[plan_id]['name']
        del test_plans_store[plan_id]
        
        logger.info(f"Deleted test plan {plan_id} '{plan_name}' by user {current_user.get('username')}")
        
        return APIResponse(
            success=True,
            message=f"Test plan '{plan_name}' deleted successfully",
            data={
                "deleted_plan_id": plan_id,
                "deleted_plan_name": plan_name
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting test plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete test plan: {str(e)}"
        )


@router.post("/test-plans/{plan_id}/execute", response_model=APIResponse)
async def execute_test_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Execute a test plan."""
    try:
        if plan_id not in test_plans_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test plan {plan_id} not found"
            )
        
        test_plan = test_plans_store[plan_id]
        test_ids = test_plan['test_ids']
        
        # Import submitted_tests to check for valid test cases
        from .tests import execution_plans, submitted_tests
        
        # If test plan has no test IDs, check if there are any available tests
        if not test_ids:
            # Get available test IDs from submitted_tests
            available_test_ids = list(submitted_tests.keys())
            if available_test_ids:
                # Use available tests for execution
                test_ids = available_test_ids[:10]  # Limit to 10 tests
                logger.info(f"Test plan {plan_id} has no test IDs, using {len(test_ids)} available tests")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Test plan has no test cases and no tests are available. Please add test cases to the test plan first."
                )
        
        # Validate that test cases exist
        valid_test_ids = [tid for tid in test_ids if tid in submitted_tests]
        if not valid_test_ids and test_ids:
            # Test IDs specified but none found - use available tests instead
            available_test_ids = list(submitted_tests.keys())
            if available_test_ids:
                valid_test_ids = available_test_ids[:10]
                logger.info(f"Test plan {plan_id} test IDs not found, using {len(valid_test_ids)} available tests")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid test cases found. Please create test cases first using AI generation or manual submission."
                )
        
        # Generate execution plan ID
        execution_plan_id = f"exec-{uuid.uuid4()}"
        
        # Create execution plan with valid test IDs
        execution_plans[execution_plan_id] = {
            "plan_id": execution_plan_id,
            "test_plan_id": plan_id,
            "submission_id": str(uuid.uuid4()),
            "test_case_ids": valid_test_ids,
            "status": "queued",
            "created_at": datetime.utcnow(),
            "priority": test_plan['execution_config'].get('priority', 5),
            "environment_preference": test_plan['execution_config'].get('environment_preference'),
            "timeout_minutes": test_plan['execution_config'].get('timeout_minutes', 60),
            "retry_failed": test_plan['execution_config'].get('retry_failed', False),
            "parallel_execution": test_plan['execution_config'].get('parallel_execution', True),
            "test_plan_name": test_plan['name'],
            "created_by": current_user.get('username', 'unknown')
        }
        
        # Auto-start execution immediately
        try:
            from execution.execution_service import get_execution_service
            
            # Get test case objects
            test_cases = []
            for test_id in valid_test_ids:
                if test_id in submitted_tests:
                    test_cases.append(submitted_tests[test_id]["test_case"])
            
            if test_cases:
                execution_service = get_execution_service()
                success = execution_service.start_execution(
                    plan_id=execution_plan_id,
                    test_cases=test_cases,
                    created_by=current_user.get('username', 'unknown'),
                    priority=test_plan['execution_config'].get('priority', 5),
                    timeout=test_plan['execution_config'].get('timeout_minutes', 60) * 60
                )
                
                if success:
                    execution_plans[execution_plan_id]["status"] = "running"
                    logger.info(f"Auto-started execution {execution_plan_id} with {len(test_cases)} tests")
                else:
                    logger.warning(f"Failed to auto-start execution {execution_plan_id}")
        except Exception as e:
            logger.warning(f"Could not auto-start execution: {e}")
        
        # Update test plan statistics
        test_plan['statistics']['total_executions'] += 1
        test_plan['statistics']['last_execution'] = datetime.utcnow().isoformat()
        test_plan['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Started execution of test plan {plan_id} with execution ID {execution_plan_id}")
        
        return APIResponse(
            success=True,
            message=f"Test plan '{test_plan['name']}' execution started with {len(valid_test_ids)} tests",
            data={
                "execution_plan_id": execution_plan_id,
                "test_plan_id": plan_id,
                "test_case_count": len(valid_test_ids),
                "status": execution_plans[execution_plan_id]["status"],
                "estimated_completion": (datetime.utcnow() + timedelta(
                    minutes=test_plan['execution_config'].get('timeout_minutes', 60)
                )).isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing test plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute test plan: {str(e)}"
        )


# Initialize with some sample test plans for demonstration
def initialize_sample_test_plans():
    """Initialize some sample test plans for demonstration."""
    if not test_plans_store:  # Only initialize if empty
        sample_plans = [
            {
                'name': 'Kernel Core Tests',
                'description': 'Comprehensive testing of kernel core functionality',
                'test_ids': [],  # Will be populated when real tests exist
                'tags': ['kernel', 'core', 'critical'],
                'execution_config': {
                    'environment_preference': 'qemu-x86',
                    'priority': 8,
                    'timeout_minutes': 120,
                    'retry_failed': True,
                    'parallel_execution': True
                },
                'status': 'active'
            },
            {
                'name': 'Memory Management Suite',
                'description': 'Tests for memory allocation, deallocation, and management',
                'test_ids': [],
                'tags': ['memory', 'mm', 'performance'],
                'execution_config': {
                    'environment_preference': 'qemu-arm64',
                    'priority': 7,
                    'timeout_minutes': 90,
                    'retry_failed': False,
                    'parallel_execution': True
                },
                'status': 'active'
            },
            {
                'name': 'Security Validation',
                'description': 'Security-focused tests including fuzzing and vulnerability checks',
                'test_ids': [],
                'tags': ['security', 'fuzzing', 'vulnerability'],
                'execution_config': {
                    'environment_preference': 'physical-hw',
                    'priority': 9,
                    'timeout_minutes': 180,
                    'retry_failed': True,
                    'parallel_execution': False
                },
                'status': 'draft'
            }
        ]
        
        for plan_data in sample_plans:
            plan_id = str(uuid.uuid4())
            test_plan = create_test_plan_dict(plan_data, plan_id, 'admin')
            
            # Add some mock statistics
            test_plan['statistics'] = {
                'total_executions': 15 + len(test_plans_store) * 10,
                'success_rate': 85.0 + len(test_plans_store) * 2.5,
                'avg_execution_time': 1800 + len(test_plans_store) * 300,
                'last_execution': (datetime.utcnow() - timedelta(hours=len(test_plans_store) + 1)).isoformat()
            }
            
            test_plans_store[plan_id] = test_plan
        
        logger.info(f"Initialized {len(sample_plans)} sample test plans")

# Initialize sample data on module load
initialize_sample_test_plans()