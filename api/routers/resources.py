"""Resource Monitoring and Capacity Planning API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..auth import get_current_user
from ..models import APIResponse

router = APIRouter(prefix="/resources")


# Request/Response Models
class ResourceMetrics(BaseModel):
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in: float
    network_out: float
    active_tests: int
    queued_tests: int


class InfrastructureMetrics(BaseModel):
    total_vms: int
    active_vms: int
    total_physical_devices: int
    active_physical_devices: int
    total_cpu_cores: int
    used_cpu_cores: int
    total_memory_gb: float
    used_memory_gb: float
    total_storage_tb: float
    used_storage_tb: float


class CapacityForecast(BaseModel):
    resource_type: str
    current_usage: float
    predicted_usage: float
    forecast_date: datetime
    confidence: float
    recommendation: str


class ResourceAlert(BaseModel):
    id: str
    resource_type: str
    severity: str
    threshold: float
    current_value: float
    message: str
    timestamp: datetime
    acknowledged: bool


@router.get("/metrics/current", response_model=APIResponse)
async def get_current_metrics(current_user: dict = Depends(get_current_user)):
    """Get current resource metrics."""
    metrics = ResourceMetrics(
        timestamp=datetime.now(),
        cpu_usage=65.5,
        memory_usage=72.3,
        disk_usage=45.8,
        network_in=125.5,
        network_out=98.2,
        active_tests=15,
        queued_tests=5
    )
    
    return APIResponse(
        success=True,
        message="Current metrics retrieved successfully",
        data=metrics.dict()
    )


@router.get("/metrics/history", response_model=APIResponse)
async def get_metrics_history(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    interval: str = Query("1h", description="Data interval: 1m, 5m, 1h, 1d"),
    current_user: dict = Depends(get_current_user)
):
    """Get historical resource metrics."""
    # Mock data - replace with actual time series data
    history = [
        ResourceMetrics(
            timestamp=datetime.now(),
            cpu_usage=65.5,
            memory_usage=72.3,
            disk_usage=45.8,
            network_in=125.5,
            network_out=98.2,
            active_tests=15,
            queued_tests=5
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(history)} metric data points",
        data={"metrics": [m.dict() for m in history]}
    )


@router.get("/infrastructure", response_model=APIResponse)
async def get_infrastructure_metrics(current_user: dict = Depends(get_current_user)):
    """Get infrastructure overview metrics."""
    metrics = InfrastructureMetrics(
        total_vms=50,
        active_vms=35,
        total_physical_devices=10,
        active_physical_devices=8,
        total_cpu_cores=400,
        used_cpu_cores=260,
        total_memory_gb=2048.0,
        used_memory_gb=1480.0,
        total_storage_tb=100.0,
        used_storage_tb=45.8
    )
    
    return APIResponse(
        success=True,
        message="Infrastructure metrics retrieved successfully",
        data=metrics.dict()
    )


@router.get("/capacity/forecast", response_model=APIResponse)
async def get_capacity_forecast(
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    days_ahead: int = Query(30, ge=1, le=365, description="Forecast days ahead"),
    current_user: dict = Depends(get_current_user)
):
    """Get capacity planning forecasts."""
    forecasts = [
        CapacityForecast(
            resource_type="cpu",
            current_usage=65.0,
            predicted_usage=78.5,
            forecast_date=datetime.now(),
            confidence=0.85,
            recommendation="Consider adding 2 more VM instances"
        ),
        CapacityForecast(
            resource_type="memory",
            current_usage=72.3,
            predicted_usage=85.0,
            forecast_date=datetime.now(),
            confidence=0.82,
            recommendation="Plan for memory upgrade in 2 months"
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(forecasts)} capacity forecasts",
        data={"forecasts": [f.dict() for f in forecasts]}
    )


@router.get("/alerts", response_model=APIResponse)
async def get_resource_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    current_user: dict = Depends(get_current_user)
):
    """Get resource alerts."""
    alerts = [
        ResourceAlert(
            id="ALERT-001",
            resource_type="memory",
            severity="warning",
            threshold=80.0,
            current_value=85.2,
            message="Memory usage exceeds threshold",
            timestamp=datetime.now(),
            acknowledged=False
        )
    ]
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(alerts)} resource alerts",
        data={"alerts": [a.dict() for a in alerts]}
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=APIResponse)
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Acknowledge a resource alert."""
    return APIResponse(
        success=True,
        message=f"Alert {alert_id} acknowledged",
        data={"alert_id": alert_id, "acknowledged": True}
    )
