"""Test Specifications API endpoints.

Provides CRUD operations for test specifications, requirements parsing,
property generation, test generation, and traceability management.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status, Body
from pydantic import BaseModel, Field

from ..auth import require_permission

# Import agentic test requirements modules
from ai_generator.requirements import (
    RequirementParser,
    PropertyGenerator,
    PropertyTestGenerator,
    TraceabilityManager,
    SpecificationManager,
    SpecificationUpdate,
    ParsedRequirement,
    CorrectnessProperty,
    GeneratedTest,
    TestSpecification,
    EARSPattern,
    PropertyPattern,
    ValidationResult,
    CoverageMatrix,
)

router = APIRouter(prefix="/specifications", tags=["specifications"])

# Initialize services
_spec_manager: Optional[SpecificationManager] = None
_parser: Optional[RequirementParser] = None
_property_generator: Optional[PropertyGenerator] = None
_test_generator: Optional[PropertyTestGenerator] = None
_traceability_manager: Optional[TraceabilityManager] = None


def get_spec_manager() -> SpecificationManager:
    """Get or create specification manager instance."""
    global _spec_manager
    if _spec_manager is None:
        _spec_manager = SpecificationManager(storage_path="./specifications")
    return _spec_manager


def get_parser() -> RequirementParser:
    """Get or create requirement parser instance."""
    global _parser
    if _parser is None:
        _parser = RequirementParser()
    return _parser


def get_property_generator() -> PropertyGenerator:
    """Get or create property generator instance."""
    global _property_generator
    if _property_generator is None:
        _property_generator = PropertyGenerator()
    return _property_generator


def get_test_generator() -> PropertyTestGenerator:
    """Get or create test generator instance."""
    global _test_generator
    if _test_generator is None:
        _test_generator = PropertyTestGenerator()
    return _test_generator


def get_traceability_manager() -> TraceabilityManager:
    """Get or create traceability manager instance."""
    global _traceability_manager
    if _traceability_manager is None:
        _traceability_manager = TraceabilityManager()
    return _traceability_manager


# Request/Response Models

class CreateSpecificationRequest(BaseModel):
    """Request to create a new specification."""
    name: str = Field(..., description="Specification name")
    description: str = Field("", description="Specification description")
    glossary: Optional[Dict[str, str]] = Field(None, description="Glossary of terms")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UpdateSpecificationRequest(BaseModel):
    """Request to update a specification."""
    name: Optional[str] = Field(None, description="New name")
    description: Optional[str] = Field(None, description="New description")
    glossary: Optional[Dict[str, str]] = Field(None, description="Updated glossary")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class ParseRequirementRequest(BaseModel):
    """Request to parse an EARS requirement."""
    text: str = Field(..., description="EARS-formatted requirement text")
    glossary: Optional[Dict[str, str]] = Field(None, description="Glossary for validation")


class AddRequirementRequest(BaseModel):
    """Request to add a requirement to a specification."""
    text: str = Field(..., description="EARS-formatted requirement text")


class GeneratePropertiesRequest(BaseModel):
    """Request to generate properties from a requirement."""
    requirement_id: Optional[str] = Field(None, description="Specific requirement ID")


class GenerateTestsRequest(BaseModel):
    """Request to generate tests from properties."""
    property_ids: Optional[List[str]] = Field(None, description="Specific property IDs")
    output_path: Optional[str] = Field(None, description="Output file path")


class ExportSpecificationRequest(BaseModel):
    """Request to export a specification."""
    format: str = Field("yaml", description="Export format (yaml, json, markdown, html)")


class APIResponse(BaseModel):
    """Standard API response."""
    success: bool
    message: str
    data: Optional[Any] = None


# Specification CRUD Endpoints

@router.post("", response_model=APIResponse)
async def create_specification(
    request: CreateSpecificationRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Create a new test specification."""
    try:
        manager = get_spec_manager()
        spec = manager.create_specification(
            name=request.name,
            description=request.description,
            glossary=request.glossary,
            metadata=request.metadata,
        )
        
        return APIResponse(
            success=True,
            message=f"Specification '{spec.name}' created successfully",
            data=spec.to_dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create specification: {str(e)}"
        )


@router.get("", response_model=APIResponse)
async def list_specifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """List all test specifications."""
    try:
        manager = get_spec_manager()
        specs = manager.list_specifications()
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            specs = [
                s for s in specs
                if search_lower in s.name.lower() or search_lower in s.description.lower()
            ]
        
        # Pagination
        total_items = len(specs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_specs = specs[start_idx:end_idx]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_specs)} specifications",
            data={
                "specifications": [s.to_dict() for s in paginated_specs],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": (total_items + page_size - 1) // page_size if total_items > 0 else 0,
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list specifications: {str(e)}"
        )


@router.get("/{spec_id}", response_model=APIResponse)
async def get_specification(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get a specific test specification."""
    manager = get_spec_manager()
    spec = manager.get_specification(spec_id)
    
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    return APIResponse(
        success=True,
        message="Specification retrieved successfully",
        data=spec.to_dict()
    )


@router.put("/{spec_id}", response_model=APIResponse)
async def update_specification(
    spec_id: str,
    request: UpdateSpecificationRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Update a test specification."""
    manager = get_spec_manager()
    
    updates = SpecificationUpdate(
        name=request.name,
        description=request.description,
        glossary=request.glossary,
        metadata=request.metadata,
    )
    
    spec = manager.update_specification(spec_id, updates)
    
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    return APIResponse(
        success=True,
        message="Specification updated successfully",
        data=spec.to_dict()
    )


@router.delete("/{spec_id}", response_model=APIResponse)
async def delete_specification(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:delete"))
):
    """Delete a test specification."""
    manager = get_spec_manager()
    
    if not manager.delete_specification(spec_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    return APIResponse(
        success=True,
        message="Specification deleted successfully",
        data={"deleted_id": spec_id}
    )


@router.post("/{spec_id}/export", response_model=APIResponse)
async def export_specification(
    spec_id: str,
    request: ExportSpecificationRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Export a specification to a specific format."""
    manager = get_spec_manager()
    
    try:
        content = manager.export_specification(spec_id, request.format)
        
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specification '{spec_id}' not found"
            )
        
        return APIResponse(
            success=True,
            message=f"Specification exported as {request.format}",
            data={
                "format": request.format,
                "content": content
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Requirements API Endpoints
# ============================================================================

@router.post("/requirements/parse", response_model=APIResponse)
async def parse_requirement(
    request: ParseRequirementRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Parse an EARS-formatted requirement.
    
    Extracts trigger condition, system name, and expected response from
    EARS patterns (WHEN/THEN, WHILE, IF/THEN, etc.).
    """
    try:
        parser = get_parser()
        parsed = parser.parse_requirement(request.text)
        
        # Validate if glossary provided
        validation = None
        if request.glossary:
            validation_parser = RequirementParser(request.glossary)
            validation = validation_parser.validate_requirement(parsed)
        
        return APIResponse(
            success=True,
            message="Requirement parsed successfully",
            data={
                "parsed_requirement": parsed.to_dict(),
                "validation": validation.to_dict() if validation else None
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse requirement: {str(e)}"
        )


class ValidateRequirementRequest(BaseModel):
    """Request to validate a requirement."""
    text: str = Field(..., description="EARS-formatted requirement text")
    glossary: Dict[str, str] = Field(default_factory=dict, description="Glossary of terms")


@router.post("/requirements/validate", response_model=APIResponse)
async def validate_requirement(
    request: ValidateRequirementRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Validate an EARS requirement for completeness and clarity.
    
    Checks for undefined terms, ambiguous language, and suggests improvements.
    """
    try:
        parser = get_parser()
        parsed = parser.parse_requirement(request.text)
        
        # Create parser with glossary for validation
        validation_parser = RequirementParser(request.glossary) if request.glossary else parser
        validation = validation_parser.validate_requirement(parsed)
        
        return APIResponse(
            success=True,
            message="Requirement validated",
            data={
                "is_valid": validation.is_valid,
                "issues": validation.issues,
                "suggestions": validation.suggestions,
                "ambiguities": validation.ambiguities,
                "undefined_terms": validation.undefined_terms
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate requirement: {str(e)}"
        )


@router.get("/{spec_id}/requirements", response_model=APIResponse)
async def list_requirements(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """List all requirements in a specification."""
    manager = get_spec_manager()
    spec = manager.get_specification(spec_id)
    
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(spec.requirements)} requirements",
        data={
            "requirements": [r.to_dict() for r in spec.requirements],
            "total": len(spec.requirements)
        }
    )


@router.post("/{spec_id}/requirements", response_model=APIResponse)
async def add_requirement(
    spec_id: str,
    request: AddRequirementRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Add a new requirement to a specification."""
    manager = get_spec_manager()
    parser = get_parser()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # Parse the requirement
        parsed = parser.parse_requirement(request.text)
        
        # Validate against glossary
        validation_parser = RequirementParser(spec.glossary) if spec.glossary else parser
        validation = validation_parser.validate_requirement(parsed)
        
        # Add to specification
        spec = manager.add_requirement(spec_id, parsed)
        
        return APIResponse(
            success=True,
            message="Requirement added successfully",
            data={
                "requirement": parsed.to_dict(),
                "validation": validation.to_dict(),
                "total_requirements": len(spec.requirements)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add requirement: {str(e)}"
        )


@router.get("/{spec_id}/requirements/{req_id}", response_model=APIResponse)
async def get_requirement(
    spec_id: str,
    req_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get a specific requirement from a specification."""
    manager = get_spec_manager()
    spec = manager.get_specification(spec_id)
    
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    # Find the requirement
    requirement = next((r for r in spec.requirements if r.id == req_id), None)
    
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirement '{req_id}' not found in specification"
        )
    
    return APIResponse(
        success=True,
        message="Requirement retrieved successfully",
        data=requirement.to_dict()
    )


@router.delete("/{spec_id}/requirements/{req_id}", response_model=APIResponse)
async def delete_requirement(
    spec_id: str,
    req_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:delete"))
):
    """Delete a requirement from a specification."""
    manager = get_spec_manager()
    
    try:
        spec = manager.remove_requirement(spec_id, req_id)
        
        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specification '{spec_id}' or requirement '{req_id}' not found"
            )
        
        return APIResponse(
            success=True,
            message="Requirement deleted successfully",
            data={"deleted_id": req_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete requirement: {str(e)}"
        )



# ============================================================================
# Properties API Endpoints
# ============================================================================

class GeneratePropertyRequest(BaseModel):
    """Request to generate properties from requirements."""
    requirement_ids: Optional[List[str]] = Field(None, description="Specific requirement IDs to generate properties for")


@router.post("/properties/generate", response_model=APIResponse)
async def generate_properties_from_requirements(
    request: GeneratePropertyRequest,
    spec_id: Optional[str] = Query(None, description="Specification ID"),
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Generate correctness properties from requirements.
    
    Creates universally quantified properties based on EARS patterns,
    identifying appropriate property patterns (invariant, round-trip, etc.).
    """
    if not spec_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="spec_id query parameter is required"
        )
    
    manager = get_spec_manager()
    generator = get_property_generator()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # Filter requirements if specific IDs provided
        requirements = spec.requirements
        if request.requirement_ids:
            requirements = [r for r in requirements if r.id in request.requirement_ids]
        
        if not requirements:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No requirements found to generate properties from"
            )
        
        # Generate properties for each requirement
        all_properties = []
        for req in requirements:
            properties = generator.generate_properties(req)
            all_properties.extend(properties)
        
        # Update specification with new properties
        spec = manager.add_properties(spec_id, all_properties)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(all_properties)} properties from {len(requirements)} requirements",
            data={
                "properties": [p.to_dict() for p in all_properties],
                "total_properties": len(spec.properties)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate properties: {str(e)}"
        )


@router.get("/{spec_id}/properties", response_model=APIResponse)
async def list_properties(
    spec_id: str,
    pattern: Optional[str] = Query(None, description="Filter by property pattern"),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """List all correctness properties in a specification."""
    manager = get_spec_manager()
    spec = manager.get_specification(spec_id)
    
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    properties = spec.properties
    
    # Filter by pattern if specified
    if pattern:
        try:
            pattern_enum = PropertyPattern(pattern.lower())
            properties = [p for p in properties if p.pattern == pattern_enum]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid property pattern: {pattern}"
            )
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(properties)} properties",
        data={
            "properties": [p.to_dict() for p in properties],
            "total": len(properties)
        }
    )


@router.get("/{spec_id}/properties/{prop_id}", response_model=APIResponse)
async def get_property(
    spec_id: str,
    prop_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get a specific correctness property."""
    manager = get_spec_manager()
    spec = manager.get_specification(spec_id)
    
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    # Find the property
    prop = next((p for p in spec.properties if p.id == prop_id), None)
    
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property '{prop_id}' not found in specification"
        )
    
    return APIResponse(
        success=True,
        message="Property retrieved successfully",
        data=prop.to_dict()
    )


@router.post("/{spec_id}/properties/generate", response_model=APIResponse)
async def generate_properties_for_spec(
    spec_id: str,
    request: GeneratePropertiesRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Generate properties for a specific specification.
    
    Optionally specify a requirement ID to generate properties for just that requirement.
    """
    manager = get_spec_manager()
    generator = get_property_generator()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # Get requirements to process
        if request.requirement_id:
            requirements = [r for r in spec.requirements if r.id == request.requirement_id]
            if not requirements:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Requirement '{request.requirement_id}' not found"
                )
        else:
            requirements = spec.requirements
        
        # Generate properties
        all_properties = []
        for req in requirements:
            properties = generator.generate_properties(req)
            all_properties.extend(properties)
        
        # Update specification
        spec = manager.add_properties(spec_id, all_properties)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(all_properties)} properties",
            data={
                "properties": [p.to_dict() for p in all_properties],
                "total_properties": len(spec.properties)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate properties: {str(e)}"
        )


@router.delete("/{spec_id}/properties/{prop_id}", response_model=APIResponse)
async def delete_property(
    spec_id: str,
    prop_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:delete"))
):
    """Delete a property from a specification."""
    manager = get_spec_manager()
    
    try:
        spec = manager.remove_property(spec_id, prop_id)
        
        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specification '{spec_id}' or property '{prop_id}' not found"
            )
        
        return APIResponse(
            success=True,
            message="Property deleted successfully",
            data={"deleted_id": prop_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete property: {str(e)}"
        )



# ============================================================================
# Tests API Endpoints
# ============================================================================

from ai_generator.requirements import (
    PropertyTestOrchestrator,
    ExecutionConfig,
)


def get_orchestrator() -> PropertyTestOrchestrator:
    """Get or create test orchestrator instance."""
    return PropertyTestOrchestrator()


class GenerateTestRequest(BaseModel):
    """Request to generate tests from properties."""
    property_ids: Optional[List[str]] = Field(None, description="Specific property IDs to generate tests for")
    output_path: Optional[str] = Field(None, description="Output file path for generated tests")
    iterations: int = Field(100, ge=1, le=10000, description="Number of test iterations")


class ExecuteTestsRequest(BaseModel):
    """Request to execute property tests."""
    test_ids: Optional[List[str]] = Field(None, description="Specific test IDs to execute")
    iterations: int = Field(100, ge=1, le=10000, description="Number of test iterations")
    parallel: bool = Field(True, description="Run tests in parallel")
    max_workers: int = Field(4, ge=1, le=16, description="Maximum parallel workers")
    timeout_seconds: int = Field(300, ge=10, le=3600, description="Test timeout in seconds")


@router.post("/tests/generate", response_model=APIResponse)
async def generate_tests(
    request: GenerateTestRequest,
    spec_id: Optional[str] = Query(None, description="Specification ID"),
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Generate property-based tests from correctness properties.
    
    Creates Hypothesis-based test functions with appropriate generators
    and traceability annotations.
    """
    if not spec_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="spec_id query parameter is required"
        )
    
    manager = get_spec_manager()
    test_gen = get_test_generator()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # Filter properties if specific IDs provided
        properties = spec.properties
        if request.property_ids:
            properties = [p for p in properties if p.id in request.property_ids]
        
        if not properties:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No properties found to generate tests from"
            )
        
        # Generate tests for each property
        generated_tests = []
        for prop in properties:
            test = test_gen.generate_test(prop, iterations=request.iterations)
            generated_tests.append(test)
        
        # Optionally write to file
        if request.output_path:
            test_gen.generate_test_file(properties, request.output_path)
        
        # Update specification with new tests
        spec = manager.add_tests(spec_id, generated_tests)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(generated_tests)} tests from {len(properties)} properties",
            data={
                "tests": [t.to_dict() for t in generated_tests],
                "output_path": request.output_path,
                "total_tests": len(spec.tests)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tests: {str(e)}"
        )


@router.post("/tests/execute", response_model=APIResponse)
async def execute_tests(
    request: ExecuteTestsRequest,
    spec_id: Optional[str] = Query(None, description="Specification ID"),
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Execute property-based tests.
    
    Runs tests with Hypothesis, captures counter-examples on failure,
    and shrinks to minimal failing cases.
    """
    if not spec_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="spec_id query parameter is required"
        )
    
    manager = get_spec_manager()
    orchestrator = get_orchestrator()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # Filter tests if specific IDs provided
        tests = spec.tests
        if request.test_ids:
            tests = [t for t in tests if t.id in request.test_ids]
        
        if not tests:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tests found to execute"
            )
        
        # Create execution config
        config = ExecutionConfig(
            iterations=request.iterations,
            parallel=request.parallel,
            max_workers=request.max_workers,
            timeout_seconds=request.timeout_seconds,
            shrink_on_failure=True,
        )
        
        # Execute tests
        results = orchestrator.execute_tests(tests, config)
        
        # Summarize results
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        return APIResponse(
            success=True,
            message=f"Executed {len(results)} tests: {passed} passed, {failed} failed",
            data={
                "results": [r.to_dict() for r in results],
                "summary": {
                    "total": len(results),
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": passed / len(results) if results else 0
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute tests: {str(e)}"
        )


@router.get("/{spec_id}/tests", response_model=APIResponse)
async def list_tests(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """List all generated tests in a specification."""
    manager = get_spec_manager()
    spec = manager.get_specification(spec_id)
    
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(spec.tests)} tests",
        data={
            "tests": [t.to_dict() for t in spec.tests],
            "total": len(spec.tests)
        }
    )


@router.get("/{spec_id}/tests/{test_id}", response_model=APIResponse)
async def get_test(
    spec_id: str,
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get a specific generated test."""
    manager = get_spec_manager()
    spec = manager.get_specification(spec_id)
    
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    # Find the test
    test = next((t for t in spec.tests if t.id == test_id), None)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test '{test_id}' not found in specification"
        )
    
    return APIResponse(
        success=True,
        message="Test retrieved successfully",
        data=test.to_dict()
    )


@router.get("/{spec_id}/tests/{test_id}/results", response_model=APIResponse)
async def get_test_results(
    spec_id: str,
    test_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum results to return"),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get execution results for a specific test."""
    manager = get_spec_manager()
    orchestrator = get_orchestrator()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    # Find the test
    test = next((t for t in spec.tests if t.id == test_id), None)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test '{test_id}' not found in specification"
        )
    
    try:
        # Get results from orchestrator
        results = orchestrator.get_test_results(test_id, limit=limit)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(results)} results for test",
            data={
                "test_id": test_id,
                "results": [r.to_dict() for r in results],
                "total": len(results)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test results: {str(e)}"
        )


@router.post("/{spec_id}/tests/generate", response_model=APIResponse)
async def generate_tests_for_spec(
    spec_id: str,
    request: GenerateTestsRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Generate tests for a specific specification.
    
    Optionally specify property IDs to generate tests for specific properties.
    """
    manager = get_spec_manager()
    test_gen = get_test_generator()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # Get properties to process
        if request.property_ids:
            properties = [p for p in spec.properties if p.id in request.property_ids]
            if not properties:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No matching properties found"
                )
        else:
            properties = spec.properties
        
        if not properties:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No properties found to generate tests from"
            )
        
        # Generate tests
        generated_tests = []
        for prop in properties:
            test = test_gen.generate_test(prop)
            generated_tests.append(test)
        
        # Optionally write to file
        if request.output_path:
            test_gen.generate_test_file(properties, request.output_path)
        
        # Update specification
        spec = manager.add_tests(spec_id, generated_tests)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(generated_tests)} tests",
            data={
                "tests": [t.to_dict() for t in generated_tests],
                "output_path": request.output_path,
                "total_tests": len(spec.tests)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tests: {str(e)}"
        )


@router.delete("/{spec_id}/tests/{test_id}", response_model=APIResponse)
async def delete_test(
    spec_id: str,
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:delete"))
):
    """Delete a test from a specification."""
    manager = get_spec_manager()
    
    try:
        spec = manager.remove_test(spec_id, test_id)
        
        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specification '{spec_id}' or test '{test_id}' not found"
            )
        
        return APIResponse(
            success=True,
            message="Test deleted successfully",
            data={"deleted_id": test_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete test: {str(e)}"
        )



# ============================================================================
# Traceability API Endpoints
# ============================================================================

@router.get("/traceability/matrix/{spec_id}", response_model=APIResponse)
async def get_coverage_matrix(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get the requirement coverage matrix for a specification.
    
    Shows which requirements are covered by which tests, identifies
    untested requirements and orphaned tests.
    """
    manager = get_spec_manager()
    traceability = get_traceability_manager()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        matrix = traceability.generate_coverage_matrix(spec)
        
        return APIResponse(
            success=True,
            message="Coverage matrix generated successfully",
            data=matrix.to_dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate coverage matrix: {str(e)}"
        )


@router.get("/traceability/requirement/{req_id}", response_model=APIResponse)
async def get_tests_for_requirement(
    req_id: str,
    spec_id: Optional[str] = Query(None, description="Specification ID to search in"),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get all tests that cover a specific requirement."""
    traceability = get_traceability_manager()
    
    try:
        tests = traceability.get_tests_for_requirement(req_id, spec_id=spec_id)
        
        return APIResponse(
            success=True,
            message=f"Found {len(tests)} tests for requirement",
            data={
                "requirement_id": req_id,
                "tests": tests,
                "total": len(tests)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tests for requirement: {str(e)}"
        )


@router.get("/traceability/test/{test_id}", response_model=APIResponse)
async def get_requirement_for_test(
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get the requirement that a test validates."""
    traceability = get_traceability_manager()
    
    try:
        requirement_ids = traceability.get_requirements_for_test(test_id)
        
        return APIResponse(
            success=True,
            message=f"Found {len(requirement_ids)} requirements for test",
            data={
                "test_id": test_id,
                "requirement_ids": requirement_ids,
                "total": len(requirement_ids)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get requirement for test: {str(e)}"
        )


@router.get("/traceability/untested/{spec_id}", response_model=APIResponse)
async def get_untested_requirements(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get all requirements without test coverage in a specification."""
    manager = get_spec_manager()
    traceability = get_traceability_manager()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        untested = traceability.find_untested_requirements(spec)
        
        return APIResponse(
            success=True,
            message=f"Found {len(untested)} untested requirements",
            data={
                "spec_id": spec_id,
                "untested_requirements": untested,
                "total": len(untested),
                "total_requirements": len(spec.requirements),
                "coverage_percentage": (
                    (len(spec.requirements) - len(untested)) / len(spec.requirements) * 100
                    if spec.requirements else 0
                )
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find untested requirements: {str(e)}"
        )


@router.get("/traceability/orphaned/{spec_id}", response_model=APIResponse)
async def get_orphaned_tests(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get all tests without requirement links in a specification."""
    manager = get_spec_manager()
    traceability = get_traceability_manager()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        orphaned = traceability.find_orphaned_tests(spec)
        
        return APIResponse(
            success=True,
            message=f"Found {len(orphaned)} orphaned tests",
            data={
                "spec_id": spec_id,
                "orphaned_tests": orphaned,
                "total": len(orphaned),
                "total_tests": len(spec.tests)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find orphaned tests: {str(e)}"
        )


class CreateTraceabilityLinkRequest(BaseModel):
    """Request to create a traceability link."""
    test_id: str = Field(..., description="Test identifier")
    requirement_id: str = Field(..., description="Requirement identifier")
    property_id: Optional[str] = Field(None, description="Property identifier")
    link_type: str = Field("validates", description="Link type (validates, partially_validates, related)")


@router.post("/traceability/link", response_model=APIResponse)
async def create_traceability_link(
    request: CreateTraceabilityLinkRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:submit"))
):
    """Create a traceability link between a test and requirement."""
    traceability = get_traceability_manager()
    
    try:
        link = traceability.link_test_to_requirement(
            test_id=request.test_id,
            requirement_id=request.requirement_id,
            property_id=request.property_id,
            link_type=request.link_type,
        )
        
        return APIResponse(
            success=True,
            message="Traceability link created successfully",
            data=link.to_dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create traceability link: {str(e)}"
        )


@router.delete("/traceability/link", response_model=APIResponse)
async def delete_traceability_link(
    test_id: str = Query(..., description="Test identifier"),
    requirement_id: str = Query(..., description="Requirement identifier"),
    current_user: Dict[str, Any] = Depends(require_permission("test:delete"))
):
    """Delete a traceability link between a test and requirement."""
    traceability = get_traceability_manager()
    
    try:
        success = traceability.unlink_test_from_requirement(test_id, requirement_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traceability link not found"
            )
        
        return APIResponse(
            success=True,
            message="Traceability link deleted successfully",
            data={
                "test_id": test_id,
                "requirement_id": requirement_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete traceability link: {str(e)}"
        )


@router.get("/{spec_id}/traceability/report", response_model=APIResponse)
async def get_traceability_report(
    spec_id: str,
    format: str = Query("json", description="Report format (json, markdown, html)"),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Generate a comprehensive traceability report for a specification."""
    manager = get_spec_manager()
    traceability = get_traceability_manager()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # Generate coverage matrix
        matrix = traceability.generate_coverage_matrix(spec)
        
        # Find untested and orphaned
        untested = traceability.find_untested_requirements(spec)
        orphaned = traceability.find_orphaned_tests(spec)
        
        report_data = {
            "spec_id": spec_id,
            "spec_name": spec.name,
            "coverage_matrix": matrix.to_dict(),
            "untested_requirements": untested,
            "orphaned_tests": orphaned,
            "summary": {
                "total_requirements": len(spec.requirements),
                "total_properties": len(spec.properties),
                "total_tests": len(spec.tests),
                "coverage_percentage": matrix.coverage_percentage,
                "untested_count": len(untested),
                "orphaned_count": len(orphaned)
            }
        }
        
        # Format report if requested
        if format == "markdown":
            content = traceability.format_report_markdown(report_data)
            return APIResponse(
                success=True,
                message="Traceability report generated",
                data={"format": "markdown", "content": content}
            )
        elif format == "html":
            content = traceability.format_report_html(report_data)
            return APIResponse(
                success=True,
                message="Traceability report generated",
                data={"format": "html", "content": content}
            )
        else:
            return APIResponse(
                success=True,
                message="Traceability report generated",
                data=report_data
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate traceability report: {str(e)}"
        )


# ============================================================================
# AI Assistant API Endpoints
# ============================================================================

from ai_generator.requirements import (
    AIAssistant,
    AISuggestion,
    SuggestionType,
    SuggestionPriority,
    CoverageAnalysis,
    TestHistoryAnalysis,
)

_ai_assistant: Optional[AIAssistant] = None


def get_ai_assistant() -> AIAssistant:
    """Get or create AI assistant instance."""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AIAssistant()
    return _ai_assistant


class AnalyzeCoverageRequest(BaseModel):
    """Request to analyze test coverage."""
    include_test_results: bool = Field(False, description="Include test result analysis")


class SuggestPropertiesRequest(BaseModel):
    """Request to get property suggestions for a requirement."""
    requirement_id: str = Field(..., description="Requirement ID to analyze")


class SuggestGeneratorImprovementsRequest(BaseModel):
    """Request to get generator improvement suggestions."""
    test_id: str = Field(..., description="Test ID to analyze")


@router.post("/{spec_id}/ai/analyze-coverage", response_model=APIResponse)
async def analyze_coverage(
    spec_id: str,
    request: AnalyzeCoverageRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Analyze test coverage and get AI suggestions.
    
    Identifies untested requirements, low coverage areas, and provides
    actionable suggestions for improving test coverage.
    """
    manager = get_spec_manager()
    assistant = get_ai_assistant()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # Get test results if requested
        test_results = None
        if request.include_test_results:
            # In a real implementation, fetch from database
            test_results = []
        
        # Analyze coverage
        analysis = await assistant.analyze_coverage(spec, test_results)
        
        return APIResponse(
            success=True,
            message="Coverage analysis complete",
            data={
                "spec_id": analysis.spec_id,
                "total_requirements": analysis.total_requirements,
                "covered_requirements": analysis.covered_requirements,
                "coverage_percentage": analysis.coverage_percentage,
                "untested_requirements": analysis.untested_requirements,
                "low_coverage_areas": analysis.low_coverage_areas,
                "suggestions": [
                    {
                        "id": s.id,
                        "type": s.type.value,
                        "priority": s.priority.value,
                        "title": s.title,
                        "description": s.description,
                        "rationale": s.rationale,
                        "action_items": s.action_items,
                        "related_requirements": s.related_requirements,
                        "confidence": s.confidence
                    }
                    for s in analysis.suggestions
                ],
                "analyzed_at": analysis.analyzed_at.isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze coverage: {str(e)}"
        )


@router.post("/{spec_id}/ai/suggest-properties", response_model=APIResponse)
async def suggest_properties(
    spec_id: str,
    request: SuggestPropertiesRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get AI suggestions for properties to add for a requirement.
    
    Analyzes the requirement pattern and existing properties to suggest
    additional property types that would improve coverage.
    """
    manager = get_spec_manager()
    assistant = get_ai_assistant()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    # Find the requirement
    requirement = next((r for r in spec.requirements if r.id == request.requirement_id), None)
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirement '{request.requirement_id}' not found"
        )
    
    try:
        # Get existing properties for this requirement
        existing_properties = [
            p for p in spec.properties 
            if request.requirement_id in p.requirement_ids
        ]
        
        # Get suggestions
        suggestions = await assistant.suggest_properties(requirement, existing_properties)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(suggestions)} property suggestions",
            data={
                "requirement_id": request.requirement_id,
                "existing_properties_count": len(existing_properties),
                "suggestions": [
                    {
                        "id": s.id,
                        "type": s.type.value,
                        "priority": s.priority.value,
                        "title": s.title,
                        "description": s.description,
                        "rationale": s.rationale,
                        "action_items": s.action_items,
                        "confidence": s.confidence
                    }
                    for s in suggestions
                ]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate property suggestions: {str(e)}"
        )


@router.post("/{spec_id}/ai/suggest-clarifications", response_model=APIResponse)
async def suggest_clarifications(
    spec_id: str,
    request: SuggestPropertiesRequest,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get AI suggestions for clarifying a requirement.
    
    Identifies ambiguous terms, missing quantification, and other
    issues that make the requirement difficult to test.
    """
    manager = get_spec_manager()
    assistant = get_ai_assistant()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    # Find the requirement
    requirement = next((r for r in spec.requirements if r.id == request.requirement_id), None)
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requirement '{request.requirement_id}' not found"
        )
    
    try:
        # Get clarification suggestions
        suggestions = await assistant.suggest_requirement_clarifications(requirement)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(suggestions)} clarification suggestions",
            data={
                "requirement_id": request.requirement_id,
                "requirement_text": requirement.text,
                "suggestions": [
                    {
                        "id": s.id,
                        "type": s.type.value,
                        "priority": s.priority.value,
                        "title": s.title,
                        "description": s.description,
                        "rationale": s.rationale,
                        "action_items": s.action_items,
                        "confidence": s.confidence
                    }
                    for s in suggestions
                ]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate clarification suggestions: {str(e)}"
        )


@router.post("/{spec_id}/ai/analyze-history", response_model=APIResponse)
async def analyze_test_history(
    spec_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Analyze test execution history for patterns and optimization opportunities.
    
    Identifies flaky tests, slow tests, common failures, and provides
    suggestions for improving test reliability and performance.
    """
    manager = get_spec_manager()
    assistant = get_ai_assistant()
    
    spec = manager.get_specification(spec_id)
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Specification '{spec_id}' not found"
        )
    
    try:
        # In a real implementation, fetch test results from database
        # For now, return analysis with empty results
        test_results = []
        
        analysis = await assistant.analyze_test_history(spec, test_results)
        
        return APIResponse(
            success=True,
            message="Test history analysis complete",
            data={
                "spec_id": analysis.spec_id,
                "total_executions": analysis.total_executions,
                "pass_rate": analysis.pass_rate,
                "common_failures": analysis.common_failures,
                "flaky_tests": analysis.flaky_tests,
                "slow_tests": analysis.slow_tests,
                "optimization_opportunities": [
                    {
                        "id": s.id,
                        "type": s.type.value,
                        "priority": s.priority.value,
                        "title": s.title,
                        "description": s.description,
                        "rationale": s.rationale,
                        "action_items": s.action_items,
                        "related_tests": s.related_tests,
                        "confidence": s.confidence
                    }
                    for s in analysis.optimization_opportunities
                ],
                "analyzed_at": analysis.analyzed_at.isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze test history: {str(e)}"
        )


@router.get("/ai/best-practices", response_model=APIResponse)
async def get_best_practices(
    context: str = Query("general", description="Context for recommendations (general, kernel, bsp)"),
    current_user: Dict[str, Any] = Depends(require_permission("test:read"))
):
    """Get AI-powered best practice recommendations.
    
    Returns general or context-specific recommendations for writing
    effective property-based tests.
    """
    assistant = get_ai_assistant()
    
    try:
        suggestions = await assistant.get_best_practices(context)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(suggestions)} best practice recommendations",
            data={
                "context": context,
                "recommendations": [
                    {
                        "id": s.id,
                        "type": s.type.value,
                        "priority": s.priority.value,
                        "title": s.title,
                        "description": s.description,
                        "rationale": s.rationale,
                        "action_items": s.action_items,
                        "confidence": s.confidence
                    }
                    for s in suggestions
                ]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get best practices: {str(e)}"
        )
