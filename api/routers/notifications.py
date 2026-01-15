"""Notification Center API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from ..auth import get_current_user
from ..models import APIResponse

router = APIRouter(prefix="/notifications")


# Request/Response Models
class Notification(BaseModel):
    id: str
    title: str
    message: str
    type: str
    severity: str
    category: str
    source: str
    timestamp: datetime
    read: bool
    action_url: Optional[str]
    metadata: Dict


class NotificationPreferences(BaseModel):
    user_id: str
    email_enabled: bool
    slack_enabled: bool
    in_app_enabled: bool
    categories: Dict[str, bool]
    quiet_hours: Optional[Dict]


class AlertPolicy(BaseModel):
    id: str
    name: str
    description: str
    conditions: Dict
    channels: List[str]
    severity: str
    enabled: bool
    created_at: datetime


@router.get("/", response_model=APIResponse)
async def list_notifications(
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    read: Optional[bool] = Query(None, description="Filter by read status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List notifications for the current user."""
    notifications = [
        Notification(
            id="notif-001",
            title="Test Execution Failed",
            message="Test plan TP-123 failed with 3 errors",
            type="alert",
            severity="high",
            category="test_execution",
            source="execution_engine",
            timestamp=datetime.now(),
            read=False,
            action_url="/tests/TP-123",
            metadata={"test_plan_id": "TP-123", "error_count": 3}
        ),
        Notification(
            id="notif-002",
            title="Security Vulnerability Detected",
            message="Critical vulnerability found in network driver",
            type="alert",
            severity="critical",
            category="security",
            source="security_scanner",
            timestamp=datetime.now(),
            read=False,
            action_url="/security/vulnerabilities/VULN-001",
            metadata={"vulnerability_id": "VULN-001", "cve": "CVE-2024-1234"}
        ),
        Notification(
            id="notif-003",
            title="Resource Usage Warning",
            message="CPU usage exceeded 80% threshold",
            type="warning",
            severity="medium",
            category="resource_monitoring",
            source="resource_monitor",
            timestamp=datetime.now(),
            read=True,
            action_url="/resources",
            metadata={"resource": "cpu", "usage": 85.2}
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(notifications)} notifications",
        data={"notifications": [n.dict() for n in notifications], "total": len(notifications)}
    )


@router.get("/unread-count", response_model=APIResponse)
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications."""
    return APIResponse(
        success=True,
        message="Unread count retrieved",
        data={"unread_count": 5}
    )


@router.get("/preferences", response_model=APIResponse)
async def get_notification_preferences(current_user: dict = Depends(get_current_user)):
    """Get notification preferences for the current user."""
    preferences = NotificationPreferences(
        user_id=current_user.get("user_id", "user-001"),
        email_enabled=True,
        slack_enabled=True,
        in_app_enabled=True,
        categories={
            "test_execution": True,
            "security": True,
            "resource_monitoring": True,
            "compliance": False
        },
        quiet_hours={
            "enabled": True,
            "start": "22:00",
            "end": "08:00"
        }
    )
    
    return APIResponse(
        success=True,
        message="Notification preferences retrieved",
        data=preferences.dict()
    )


@router.put("/preferences", response_model=APIResponse)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update notification preferences."""
    return APIResponse(
        success=True,
        message="Notification preferences updated",
        data=preferences.dict()
    )


@router.get("/policies", response_model=APIResponse)
async def list_alert_policies(current_user: dict = Depends(get_current_user)):
    """List alert policies."""
    policies = [
        AlertPolicy(
            id="policy-001",
            name="Critical Test Failures",
            description="Alert on critical test failures",
            conditions={
                "event": "test.failed",
                "severity": "critical"
            },
            channels=["email", "slack"],
            severity="critical",
            enabled=True,
            created_at=datetime.now()
        ),
        AlertPolicy(
            id="policy-002",
            name="Security Vulnerabilities",
            description="Alert on security vulnerabilities",
            conditions={
                "event": "vulnerability.detected",
                "severity": ["critical", "high"]
            },
            channels=["email", "slack", "in_app"],
            severity="critical",
            enabled=True,
            created_at=datetime.now()
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(policies)} alert policies",
        data={"policies": [p.dict() for p in policies]}
    )


@router.post("/policies", response_model=APIResponse)
async def create_alert_policy(
    policy: AlertPolicy,
    current_user: dict = Depends(get_current_user)
):
    """Create a new alert policy."""
    return APIResponse(
        success=True,
        message=f"Alert policy {policy.name} created",
        data={"policy_id": "policy-new"}
    )


@router.post("/{notification_id}/read", response_model=APIResponse)
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read."""
    return APIResponse(
        success=True,
        message=f"Notification {notification_id} marked as read",
        data={"notification_id": notification_id, "read": True}
    )


@router.post("/mark-all-read", response_model=APIResponse)
async def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read."""
    return APIResponse(
        success=True,
        message="All notifications marked as read",
        data={"marked_count": 5}
    )


@router.delete("/{notification_id}", response_model=APIResponse)
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification."""
    return APIResponse(
        success=True,
        message=f"Notification {notification_id} deleted",
        data={"notification_id": notification_id}
    )
