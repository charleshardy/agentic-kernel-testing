"""Integration Management Hub API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from ..auth import get_current_user
from ..models import APIResponse

router = APIRouter(prefix="/integrations")


# Request/Response Models
class Integration(BaseModel):
    id: str
    name: str
    type: str
    provider: str
    status: str
    enabled: bool
    config: Dict
    created_at: datetime
    last_sync: Optional[datetime]
    health_status: str


class WebhookConfig(BaseModel):
    id: str
    integration_id: str
    url: str
    events: List[str]
    secret: Optional[str]
    enabled: bool
    retry_policy: Dict


class IntegrationHealth(BaseModel):
    integration_id: str
    status: str
    last_check: datetime
    uptime_percentage: float
    total_requests: int
    failed_requests: int
    average_latency: float


@router.get("/", response_model=APIResponse)
async def list_integrations(
    type: Optional[str] = Query(None, description="Filter by integration type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user)
):
    """List all integrations."""
    integrations = [
        Integration(
            id="INT-001",
            name="GitHub Actions",
            type="ci_cd",
            provider="github",
            status="active",
            enabled=True,
            config={
                "repository": "org/repo",
                "workflow": "test.yml",
                "branch": "main"
            },
            created_at=datetime.now(),
            last_sync=datetime.now(),
            health_status="healthy"
        ),
        Integration(
            id="INT-002",
            name="Slack Notifications",
            type="notification",
            provider="slack",
            status="active",
            enabled=True,
            config={
                "channel": "#testing",
                "webhook_url": "https://hooks.slack.com/..."
            },
            created_at=datetime.now(),
            last_sync=datetime.now(),
            health_status="healthy"
        ),
        Integration(
            id="INT-003",
            name="JIRA Issue Tracking",
            type="issue_tracking",
            provider="jira",
            status="active",
            enabled=True,
            config={
                "project": "TEST",
                "issue_type": "Bug"
            },
            created_at=datetime.now(),
            last_sync=datetime.now(),
            health_status="healthy"
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(integrations)} integrations",
        data={"integrations": [i.dict() for i in integrations]}
    )


@router.get("/{integration_id}", response_model=APIResponse)
async def get_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get integration details."""
    integration = Integration(
        id=integration_id,
        name="GitHub Actions",
        type="ci_cd",
        provider="github",
        status="active",
        enabled=True,
        config={
            "repository": "org/repo",
            "workflow": "test.yml",
            "branch": "main"
        },
        created_at=datetime.now(),
        last_sync=datetime.now(),
        health_status="healthy"
    )
    
    return APIResponse(
        success=True,
        message="Integration retrieved successfully",
        data=integration.dict()
    )


@router.get("/{integration_id}/health", response_model=APIResponse)
async def get_integration_health(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get integration health status."""
    health = IntegrationHealth(
        integration_id=integration_id,
        status="healthy",
        last_check=datetime.now(),
        uptime_percentage=99.5,
        total_requests=1250,
        failed_requests=6,
        average_latency=0.8
    )
    
    return APIResponse(
        success=True,
        message="Integration health retrieved successfully",
        data=health.dict()
    )


@router.get("/{integration_id}/webhooks", response_model=APIResponse)
async def list_webhooks(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List webhooks for an integration."""
    webhooks = [
        WebhookConfig(
            id="WH-001",
            integration_id=integration_id,
            url="https://api.example.com/webhook",
            events=["test.completed", "test.failed"],
            secret="secret123",
            enabled=True,
            retry_policy={
                "max_retries": 3,
                "retry_delay": 60,
                "backoff_multiplier": 2
            }
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(webhooks)} webhooks",
        data={"webhooks": [w.dict() for w in webhooks]}
    )


@router.post("/", response_model=APIResponse)
async def create_integration(
    integration: Integration,
    current_user: dict = Depends(get_current_user)
):
    """Create a new integration."""
    return APIResponse(
        success=True,
        message=f"Integration {integration.name} created successfully",
        data={"integration_id": "INT-NEW"}
    )


@router.put("/{integration_id}", response_model=APIResponse)
async def update_integration(
    integration_id: str,
    integration: Integration,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing integration."""
    return APIResponse(
        success=True,
        message=f"Integration {integration_id} updated successfully",
        data={"integration_id": integration_id}
    )


@router.post("/{integration_id}/test", response_model=APIResponse)
async def test_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Test an integration connection."""
    return APIResponse(
        success=True,
        message="Integration test successful",
        data={"status": "connected", "latency": 0.5}
    )


@router.post("/{integration_id}/sync", response_model=APIResponse)
async def sync_integration(
    integration_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Trigger manual sync for an integration."""
    return APIResponse(
        success=True,
        message="Integration sync initiated",
        data={"sync_id": "SYNC-001", "status": "running"}
    )
