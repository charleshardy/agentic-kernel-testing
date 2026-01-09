"""
Health Monitor Service

Monitors health of all infrastructure resources including build servers,
QEMU hosts, and physical test boards.

**Feature: test-infrastructure-management**
**Validates: Requirements 2.1-2.3, 9.1-9.3, 10.1-10.4**
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from uuid import uuid4

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of infrastructure resources."""
    BUILD_SERVER = "build_server"
    QEMU_HOST = "qemu_host"
    PHYSICAL_BOARD = "physical_board"


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNREACHABLE = "unreachable"
    UNKNOWN = "unknown"


@dataclass
class HealthThresholds:
    """Configurable thresholds for health checks."""
    cpu_warning_percent: float = 85.0
    cpu_critical_percent: float = 95.0
    memory_warning_percent: float = 85.0
    memory_critical_percent: float = 95.0
    storage_warning_percent: float = 85.0
    storage_critical_percent: float = 95.0
    disk_space_warning_gb: float = 10.0
    disk_space_critical_gb: float = 5.0
    temperature_warning_celsius: float = 70.0
    temperature_critical_celsius: float = 85.0
    response_time_warning_ms: int = 5000
    response_time_critical_ms: int = 10000
    max_consecutive_failures: int = 3


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    resource_id: str
    resource_type: ResourceType
    status: HealthStatus
    timestamp: datetime
    response_time_ms: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    storage_percent: Optional[float] = None
    disk_space_gb: Optional[float] = None
    temperature_celsius: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    checks_warning: List[str] = field(default_factory=list)


@dataclass
class HealthRecord:
    """Historical health record."""
    id: str
    resource_id: str
    resource_type: ResourceType
    status: HealthStatus
    timestamp: datetime
    response_time_ms: Optional[int] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class TimeRange:
    """Time range for querying health history."""
    start: datetime
    end: datetime


class HealthMonitorService:
    """
    Monitors health of all infrastructure resources.
    
    Provides periodic health checks for build servers, QEMU hosts, and
    physical test boards with configurable thresholds and alerting.
    """
    
    def __init__(
        self,
        check_interval_seconds: int = 30,
        alert_callback: Optional[Callable[[str, ResourceType, HealthStatus, str], Awaitable[None]]] = None
    ):
        """
        Initialize the health monitor service.
        
        Args:
            check_interval_seconds: Interval between health checks
            alert_callback: Async callback for alert generation
        """
        self._check_interval = check_interval_seconds
        self._alert_callback = alert_callback
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Resource registrations
        self._build_servers: Dict[str, Dict[str, Any]] = {}
        self._hosts: Dict[str, Dict[str, Any]] = {}
        self._boards: Dict[str, Dict[str, Any]] = {}
        
        # Health thresholds per resource
        self._thresholds: Dict[str, HealthThresholds] = {}
        self._default_thresholds = HealthThresholds()
        
        # Health history
        self._health_history: Dict[str, List[HealthRecord]] = {}
        self._max_history_per_resource = 1000
        
        # Consecutive failure tracking for alerting
        self._consecutive_failures: Dict[str, int] = {}
        
        # Last known status for change detection
        self._last_status: Dict[str, HealthStatus] = {}
        
        # SSH connector for remote checks (injected)
        self._ssh_connector = None
        self._libvirt_connector = None
        self._serial_connector = None
    
    def set_connectors(
        self,
        ssh_connector=None,
        libvirt_connector=None,
        serial_connector=None
    ):
        """Set connectors for remote health checks."""
        self._ssh_connector = ssh_connector
        self._libvirt_connector = libvirt_connector
        self._serial_connector = serial_connector
    
    def register_build_server(self, server_id: str, server_info: Dict[str, Any]) -> None:
        """Register a build server for health monitoring."""
        self._build_servers[server_id] = server_info
        self._health_history[server_id] = []
        self._consecutive_failures[server_id] = 0
        self._last_status[server_id] = HealthStatus.UNKNOWN
        logger.info(f"Registered build server {server_id} for health monitoring")
    
    def unregister_build_server(self, server_id: str) -> None:
        """Unregister a build server from health monitoring."""
        self._build_servers.pop(server_id, None)
        logger.info(f"Unregistered build server {server_id} from health monitoring")
    
    def register_host(self, host_id: str, host_info: Dict[str, Any]) -> None:
        """Register a QEMU host for health monitoring."""
        self._hosts[host_id] = host_info
        self._health_history[host_id] = []
        self._consecutive_failures[host_id] = 0
        self._last_status[host_id] = HealthStatus.UNKNOWN
        logger.info(f"Registered host {host_id} for health monitoring")
    
    def unregister_host(self, host_id: str) -> None:
        """Unregister a QEMU host from health monitoring."""
        self._hosts.pop(host_id, None)
        logger.info(f"Unregistered host {host_id} from health monitoring")
    
    def register_board(self, board_id: str, board_info: Dict[str, Any]) -> None:
        """Register a physical board for health monitoring."""
        self._boards[board_id] = board_info
        self._health_history[board_id] = []
        self._consecutive_failures[board_id] = 0
        self._last_status[board_id] = HealthStatus.UNKNOWN
        logger.info(f"Registered board {board_id} for health monitoring")
    
    def unregister_board(self, board_id: str) -> None:
        """Unregister a physical board from health monitoring."""
        self._boards.pop(board_id, None)
        logger.info(f"Unregistered board {board_id} from health monitoring")
    
    async def start_monitoring(self) -> None:
        """Start the health monitoring loop."""
        if self._monitoring:
            logger.warning("Health monitoring is already running")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop the health monitoring loop."""
        if not self._monitoring:
            logger.warning("Health monitoring is not running")
            return
        
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                # Check all resources in parallel
                tasks = []
                
                for server_id in list(self._build_servers.keys()):
                    tasks.append(self._check_and_record_build_server(server_id))
                
                for host_id in list(self._hosts.keys()):
                    tasks.append(self._check_and_record_host(host_id))
                
                for board_id in list(self._boards.keys()):
                    tasks.append(self._check_and_record_board(board_id))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                await asyncio.sleep(self._check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def _check_and_record_build_server(self, server_id: str) -> None:
        """Check build server health and record result."""
        try:
            result = await self.check_build_server_health(server_id)
            await self._record_and_alert(result)
        except Exception as e:
            logger.error(f"Error checking build server {server_id}: {e}")
    
    async def _check_and_record_host(self, host_id: str) -> None:
        """Check host health and record result."""
        try:
            result = await self.check_host_health(host_id)
            await self._record_and_alert(result)
        except Exception as e:
            logger.error(f"Error checking host {host_id}: {e}")
    
    async def _check_and_record_board(self, board_id: str) -> None:
        """Check board health and record result."""
        try:
            result = await self.check_board_health(board_id)
            await self._record_and_alert(result)
        except Exception as e:
            logger.error(f"Error checking board {board_id}: {e}")
    
    async def _record_and_alert(self, result: HealthCheckResult) -> None:
        """Record health check result and generate alerts if needed."""
        # Record to history
        record = HealthRecord(
            id=str(uuid4()),
            resource_id=result.resource_id,
            resource_type=result.resource_type,
            status=result.status,
            timestamp=result.timestamp,
            response_time_ms=result.response_time_ms,
            metrics={
                "cpu_percent": result.cpu_percent,
                "memory_percent": result.memory_percent,
                "storage_percent": result.storage_percent,
                "disk_space_gb": result.disk_space_gb,
                "temperature_celsius": result.temperature_celsius,
            },
            error_message=result.error_message
        )
        
        history = self._health_history.get(result.resource_id, [])
        history.append(record)
        
        # Trim history if needed
        if len(history) > self._max_history_per_resource:
            history = history[-self._max_history_per_resource:]
        
        self._health_history[result.resource_id] = history
        
        # Track consecutive failures
        if result.status in (HealthStatus.UNHEALTHY, HealthStatus.UNREACHABLE):
            self._consecutive_failures[result.resource_id] = \
                self._consecutive_failures.get(result.resource_id, 0) + 1
        else:
            self._consecutive_failures[result.resource_id] = 0
        
        # Check for status change and generate alert
        last_status = self._last_status.get(result.resource_id, HealthStatus.UNKNOWN)
        self._last_status[result.resource_id] = result.status
        
        # Generate alert on status degradation or unreachable
        should_alert = False
        alert_message = ""
        
        if result.status == HealthStatus.UNREACHABLE and last_status != HealthStatus.UNREACHABLE:
            should_alert = True
            alert_message = f"Resource became unreachable: {result.error_message or 'Connection failed'}"
        elif result.status == HealthStatus.UNHEALTHY and last_status not in (HealthStatus.UNHEALTHY, HealthStatus.UNREACHABLE):
            should_alert = True
            alert_message = f"Resource health degraded to unhealthy: {', '.join(result.checks_failed)}"
        elif result.status == HealthStatus.DEGRADED and last_status == HealthStatus.HEALTHY:
            should_alert = True
            alert_message = f"Resource health degraded: {', '.join(result.checks_warning)}"
        
        if should_alert and self._alert_callback:
            try:
                await self._alert_callback(
                    result.resource_id,
                    result.resource_type,
                    result.status,
                    alert_message
                )
            except Exception as e:
                logger.error(f"Error calling alert callback: {e}")
    
    async def check_build_server_health(self, server_id: str) -> HealthCheckResult:
        """
        Check health of a specific build server.
        
        Args:
            server_id: Build server ID
            
        Returns:
            HealthCheckResult with current health status
        """
        server_info = self._build_servers.get(server_id)
        if not server_info:
            return HealthCheckResult(
                resource_id=server_id,
                resource_type=ResourceType.BUILD_SERVER,
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.now(timezone.utc),
                error_message="Build server not registered"
            )
        
        thresholds = self._thresholds.get(server_id, self._default_thresholds)
        start_time = datetime.now(timezone.utc)
        
        checks_passed = []
        checks_failed = []
        checks_warning = []
        
        try:
            # Simulate health check (in real implementation, use SSH connector)
            # For now, use mock data or data from server_info
            response_time_ms = 100  # Mock response time
            
            cpu_percent = server_info.get("cpu_percent", 50.0)
            memory_percent = server_info.get("memory_percent", 50.0)
            storage_percent = server_info.get("storage_percent", 50.0)
            disk_space_gb = server_info.get("disk_space_gb", 100.0)
            
            # Check CPU
            if cpu_percent >= thresholds.cpu_critical_percent:
                checks_failed.append(f"CPU critical: {cpu_percent}%")
            elif cpu_percent >= thresholds.cpu_warning_percent:
                checks_warning.append(f"CPU warning: {cpu_percent}%")
            else:
                checks_passed.append("CPU OK")
            
            # Check memory
            if memory_percent >= thresholds.memory_critical_percent:
                checks_failed.append(f"Memory critical: {memory_percent}%")
            elif memory_percent >= thresholds.memory_warning_percent:
                checks_warning.append(f"Memory warning: {memory_percent}%")
            else:
                checks_passed.append("Memory OK")
            
            # Check storage
            if storage_percent >= thresholds.storage_critical_percent:
                checks_failed.append(f"Storage critical: {storage_percent}%")
            elif storage_percent >= thresholds.storage_warning_percent:
                checks_warning.append(f"Storage warning: {storage_percent}%")
            else:
                checks_passed.append("Storage OK")
            
            # Check disk space (Requirement 2.4)
            if disk_space_gb <= thresholds.disk_space_critical_gb:
                checks_failed.append(f"Disk space critical: {disk_space_gb}GB")
            elif disk_space_gb <= thresholds.disk_space_warning_gb:
                checks_warning.append(f"Disk space warning: {disk_space_gb}GB")
            else:
                checks_passed.append("Disk space OK")
            
            # Determine overall status
            if checks_failed:
                status = HealthStatus.UNHEALTHY
            elif checks_warning:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return HealthCheckResult(
                resource_id=server_id,
                resource_type=ResourceType.BUILD_SERVER,
                status=status,
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time_ms,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                storage_percent=storage_percent,
                disk_space_gb=disk_space_gb,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                checks_warning=checks_warning
            )
            
        except Exception as e:
            return HealthCheckResult(
                resource_id=server_id,
                resource_type=ResourceType.BUILD_SERVER,
                status=HealthStatus.UNREACHABLE,
                timestamp=datetime.now(timezone.utc),
                error_message=str(e),
                checks_failed=["Connection failed"]
            )
    
    async def check_host_health(self, host_id: str) -> HealthCheckResult:
        """
        Check health of a specific QEMU host.
        
        Args:
            host_id: Host ID
            
        Returns:
            HealthCheckResult with current health status
        """
        host_info = self._hosts.get(host_id)
        if not host_info:
            return HealthCheckResult(
                resource_id=host_id,
                resource_type=ResourceType.QEMU_HOST,
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.now(timezone.utc),
                error_message="Host not registered"
            )
        
        thresholds = self._thresholds.get(host_id, self._default_thresholds)
        
        checks_passed = []
        checks_failed = []
        checks_warning = []
        
        try:
            # Simulate health check
            response_time_ms = 100
            
            cpu_percent = host_info.get("cpu_percent", 50.0)
            memory_percent = host_info.get("memory_percent", 50.0)
            storage_percent = host_info.get("storage_percent", 50.0)
            
            # Check CPU (Requirement 9.4 - 85% threshold)
            if cpu_percent >= thresholds.cpu_critical_percent:
                checks_failed.append(f"CPU critical: {cpu_percent}%")
            elif cpu_percent >= thresholds.cpu_warning_percent:
                checks_warning.append(f"CPU warning: {cpu_percent}%")
            else:
                checks_passed.append("CPU OK")
            
            # Check memory (Requirement 9.4 - 85% threshold)
            if memory_percent >= thresholds.memory_critical_percent:
                checks_failed.append(f"Memory critical: {memory_percent}%")
            elif memory_percent >= thresholds.memory_warning_percent:
                checks_warning.append(f"Memory warning: {memory_percent}%")
            else:
                checks_passed.append("Memory OK")
            
            # Check storage
            if storage_percent >= thresholds.storage_critical_percent:
                checks_failed.append(f"Storage critical: {storage_percent}%")
            elif storage_percent >= thresholds.storage_warning_percent:
                checks_warning.append(f"Storage warning: {storage_percent}%")
            else:
                checks_passed.append("Storage OK")
            
            # Check libvirt connectivity
            libvirt_ok = host_info.get("libvirt_available", True)
            if not libvirt_ok:
                checks_failed.append("Libvirt unavailable")
            else:
                checks_passed.append("Libvirt OK")
            
            # Determine overall status
            if checks_failed:
                status = HealthStatus.UNHEALTHY
            elif checks_warning:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return HealthCheckResult(
                resource_id=host_id,
                resource_type=ResourceType.QEMU_HOST,
                status=status,
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time_ms,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                storage_percent=storage_percent,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                checks_warning=checks_warning
            )
            
        except Exception as e:
            return HealthCheckResult(
                resource_id=host_id,
                resource_type=ResourceType.QEMU_HOST,
                status=HealthStatus.UNREACHABLE,
                timestamp=datetime.now(timezone.utc),
                error_message=str(e),
                checks_failed=["Connection failed"]
            )
    
    async def check_board_health(self, board_id: str) -> HealthCheckResult:
        """
        Check health of a specific physical test board.
        
        Args:
            board_id: Board ID
            
        Returns:
            HealthCheckResult with current health status
        """
        board_info = self._boards.get(board_id)
        if not board_info:
            return HealthCheckResult(
                resource_id=board_id,
                resource_type=ResourceType.PHYSICAL_BOARD,
                status=HealthStatus.UNKNOWN,
                timestamp=datetime.now(timezone.utc),
                error_message="Board not registered"
            )
        
        thresholds = self._thresholds.get(board_id, self._default_thresholds)
        
        checks_passed = []
        checks_failed = []
        checks_warning = []
        
        try:
            # Simulate health check
            response_time_ms = 150
            
            temperature_celsius = board_info.get("temperature_celsius", 45.0)
            storage_percent = board_info.get("storage_percent", 50.0)
            connectivity_ok = board_info.get("connectivity", True)
            power_ok = board_info.get("power_status", True)
            
            # Check connectivity (Requirement 10.3)
            if not connectivity_ok:
                checks_failed.append("Board unreachable")
            else:
                checks_passed.append("Connectivity OK")
            
            # Check temperature (Requirement 10.4)
            if temperature_celsius >= thresholds.temperature_critical_celsius:
                checks_failed.append(f"Temperature critical: {temperature_celsius}°C")
            elif temperature_celsius >= thresholds.temperature_warning_celsius:
                checks_warning.append(f"Temperature warning: {temperature_celsius}°C")
            else:
                checks_passed.append("Temperature OK")
            
            # Check storage
            if storage_percent >= thresholds.storage_critical_percent:
                checks_failed.append(f"Storage critical: {storage_percent}%")
            elif storage_percent >= thresholds.storage_warning_percent:
                checks_warning.append(f"Storage warning: {storage_percent}%")
            else:
                checks_passed.append("Storage OK")
            
            # Check power status
            if not power_ok:
                checks_failed.append("Power issue detected")
            else:
                checks_passed.append("Power OK")
            
            # Check response time
            if response_time_ms >= thresholds.response_time_critical_ms:
                checks_failed.append(f"Response time critical: {response_time_ms}ms")
            elif response_time_ms >= thresholds.response_time_warning_ms:
                checks_warning.append(f"Response time warning: {response_time_ms}ms")
            else:
                checks_passed.append("Response time OK")
            
            # Determine overall status
            if not connectivity_ok:
                status = HealthStatus.UNREACHABLE
            elif checks_failed:
                status = HealthStatus.UNHEALTHY
            elif checks_warning:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
            
            return HealthCheckResult(
                resource_id=board_id,
                resource_type=ResourceType.PHYSICAL_BOARD,
                status=status,
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time_ms,
                storage_percent=storage_percent,
                temperature_celsius=temperature_celsius,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                checks_warning=checks_warning
            )
            
        except Exception as e:
            return HealthCheckResult(
                resource_id=board_id,
                resource_type=ResourceType.PHYSICAL_BOARD,
                status=HealthStatus.UNREACHABLE,
                timestamp=datetime.now(timezone.utc),
                error_message=str(e),
                checks_failed=["Connection failed"]
            )
    
    async def get_health_history(
        self,
        resource_id: str,
        time_range: Optional[TimeRange] = None
    ) -> List[HealthRecord]:
        """
        Get health history for a resource.
        
        Args:
            resource_id: Resource ID
            time_range: Optional time range filter
            
        Returns:
            List of health records
        """
        history = self._health_history.get(resource_id, [])
        
        if time_range:
            history = [
                record for record in history
                if time_range.start <= record.timestamp <= time_range.end
            ]
        
        return history
    
    async def set_health_thresholds(
        self,
        resource_id: str,
        thresholds: HealthThresholds
    ) -> None:
        """
        Set custom health thresholds for a resource.
        
        Args:
            resource_id: Resource ID
            thresholds: Custom thresholds
        """
        self._thresholds[resource_id] = thresholds
        logger.info(f"Updated health thresholds for resource {resource_id}")
    
    def get_health_thresholds(self, resource_id: str) -> HealthThresholds:
        """Get health thresholds for a resource."""
        return self._thresholds.get(resource_id, self._default_thresholds)
    
    def get_last_health_status(self, resource_id: str) -> HealthStatus:
        """Get the last known health status for a resource."""
        return self._last_status.get(resource_id, HealthStatus.UNKNOWN)
    
    def get_consecutive_failures(self, resource_id: str) -> int:
        """Get the number of consecutive health check failures."""
        return self._consecutive_failures.get(resource_id, 0)
    
    @property
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    @property
    def registered_build_servers(self) -> List[str]:
        """Get list of registered build server IDs."""
        return list(self._build_servers.keys())
    
    @property
    def registered_hosts(self) -> List[str]:
        """Get list of registered host IDs."""
        return list(self._hosts.keys())
    
    @property
    def registered_boards(self) -> List[str]:
        """Get list of registered board IDs."""
        return list(self._boards.keys())
