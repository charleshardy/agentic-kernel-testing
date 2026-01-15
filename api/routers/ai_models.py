"""AI/ML Model Management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from ..auth import get_current_user
from ..models import APIResponse

router = APIRouter(prefix="/ai-models")


# Request/Response Models
class AIModel(BaseModel):
    id: str
    name: str
    provider: str
    model_type: str
    version: str
    status: str
    endpoint: str
    api_key_configured: bool
    created_at: datetime
    last_used: Optional[datetime]


class ModelMetrics(BaseModel):
    model_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_latency: float
    average_tokens: int
    cost: float
    uptime_percentage: float


class PromptTemplate(BaseModel):
    id: str
    name: str
    description: str
    template: str
    version: int
    model_id: str
    created_at: datetime
    updated_at: datetime


class FallbackConfig(BaseModel):
    primary_model: str
    fallback_models: List[str]
    trigger_conditions: Dict[str, any]
    enabled: bool


@router.get("/", response_model=APIResponse)
async def list_models(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """List all AI models."""
    models = [
        AIModel(
            id="model-001",
            name="GPT-4",
            provider="OpenAI",
            model_type="llm",
            version="gpt-4-turbo",
            status="active",
            endpoint="https://api.openai.com/v1",
            api_key_configured=True,
            created_at=datetime.now(),
            last_used=datetime.now()
        ),
        AIModel(
            id="model-002",
            name="Claude 3",
            provider="Anthropic",
            model_type="llm",
            version="claude-3-opus",
            status="active",
            endpoint="https://api.anthropic.com/v1",
            api_key_configured=True,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(models)} AI models",
        data={"models": [m.dict() for m in models]}
    )


@router.get("/{model_id}/metrics", response_model=APIResponse)
async def get_model_metrics(
    model_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get performance metrics for a specific model."""
    metrics = ModelMetrics(
        model_id=model_id,
        total_requests=1250,
        successful_requests=1200,
        failed_requests=50,
        average_latency=1.2,
        average_tokens=850,
        cost=45.50,
        uptime_percentage=96.0
    )
    
    return APIResponse(
        success=True,
        message="Model metrics retrieved successfully",
        data=metrics.dict()
    )


@router.get("/prompts", response_model=APIResponse)
async def list_prompt_templates(
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    current_user: dict = Depends(get_current_user)
):
    """List prompt templates."""
    templates = [
        PromptTemplate(
            id="prompt-001",
            name="Test Generation",
            description="Generate test cases from code",
            template="Generate test cases for the following code:\n\n{code}",
            version=1,
            model_id="model-001",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(templates)} prompt templates",
        data={"templates": [t.dict() for t in templates]}
    )


@router.get("/fallback-config", response_model=APIResponse)
async def get_fallback_config(current_user: dict = Depends(get_current_user)):
    """Get model fallback configuration."""
    config = FallbackConfig(
        primary_model="model-001",
        fallback_models=["model-002", "model-003"],
        trigger_conditions={
            "error_rate_threshold": 0.1,
            "latency_threshold": 5.0,
            "consecutive_failures": 3
        },
        enabled=True
    )
    
    return APIResponse(
        success=True,
        message="Fallback configuration retrieved successfully",
        data=config.dict()
    )


@router.post("/", response_model=APIResponse)
async def create_model(
    model: AIModel,
    current_user: dict = Depends(get_current_user)
):
    """Register a new AI model."""
    return APIResponse(
        success=True,
        message=f"Model {model.name} registered successfully",
        data={"model_id": "model-new"}
    )


@router.put("/{model_id}", response_model=APIResponse)
async def update_model(
    model_id: str,
    model: AIModel,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing AI model."""
    return APIResponse(
        success=True,
        message=f"Model {model_id} updated successfully",
        data={"model_id": model_id}
    )
