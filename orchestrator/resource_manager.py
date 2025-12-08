"""Resource management and cleanup for test execution environments.

This module provides functionality for:
- Idle resource detection
- Resource release and power-down logic
- Resource cost tracking
- Resource utilization metrics collection
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum

from ai_generator.models import Environment, EnvironmentStatus, HardwareConfig
from execution.environment_manager import EnvironmentManager


class PowerState(str, Enum):
    """Power state of a resource."""
    ON = "on"
    OFF = "off"
    SUSPENDED = "suspended"


@dataclass
class ResourceCost:
    """Cost tracking for a resource."""
    hourly_rate: float  # Cost per hour
    total_runtime_hours: float = 0.0
    total_cost: float = 0.0
    last_cost_update: datetime = field(default_factory=datetime.now)
    
    def update_cost(self, runtime_seconds: float) -> None:
        """Update cost based on runtime.
        
        Args:
            runtime_seconds: Runtime in seconds since last update
        """
        hours = runtime_seconds / 3600.0
        self.total_runtime_hours += hours
        cost_increment = hours * self.hourly_rate
        self.total_cost += cost_increment
        self.last_cost_update = datetime.now()


@dataclass
class ResourceMetrics:
    """Utilization metrics for a resource."""
    environment_id: str
    total_uptime_seconds: float = 0.0
    total_busy_seconds: float = 0.0
    total_idle_seconds: float = 0.0
    test_executions: int = 0
    last_test_execution: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def utilization_rate(self) -> float:
        """Calculate utilization rate (busy time / uptime).
        
        Returns:
            Utilization rate between 0.0 and 1.0
        """
        if self.total_uptime_seconds == 0:
            return 0.0
        return self.total_busy_seconds / self.total_uptime_seconds
    
    @property
    def idle_rate(self) -> float:
        """Calculate idle rate (idle time / uptime).
        
        Returns:
            Idle rate between 0.0 and 1.0
        """
        if self.total_uptime_seconds == 0:
            return 0.0
        return self.total_idle_seconds / self.total_uptime_seconds
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'environment_id': self.environment_id,
            'total_uptime_seconds': self.total_uptime_seconds,
            'total_busy_seconds': self.total_busy_seconds,
            'total_idle_seconds': self.total_idle_seconds,
            'test_executions': self.test_executions,
            'utilization_rate': self.utilization_rate,
            'idle_rate': self.idle_rate,
            'last_test_execution': self.last_test_execution.isoformat() if self.last_test_execution else None,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ResourceState:
    """Complete state of a managed resource."""
    environment: Environment
    power_state: PowerState = PowerState.ON
    cost: Optional[ResourceCost] = None
    metrics: Optional[ResourceMetrics] = None
    last_state_change: datetime = field(default_factory=datetime.now)
    
    def is_idle(self, idle_threshold_seconds: int = 300) -> bool:
        """Check if resource has been idle for threshold duration.
        
        Args:
            idle_threshold_seconds: Idle threshold in seconds
            
        Returns:
            True if resource is idle beyond threshold
        """
        if self.environment.status != EnvironmentStatus.IDLE:
            return False
        
        idle_duration = (datetime.now() - self.environment.last_used).total_seconds()
        return idle_duration >= idle_threshold_seconds


class ResourceManager:
    """Manager for resource lifecycle, cost tracking, and metrics."""
    
    def __init__(
        self,
        environment_manager: Optional[EnvironmentManager] = None,
        idle_threshold_seconds: int = 300,
        cleanup_interval_seconds: int = 60
    ):
        """Initialize resource manager.
        
        Args:
            environment_manager: Environment manager for cleanup operations
            idle_threshold_seconds: Threshold for considering resource idle
            cleanup_interval_seconds: Interval for automatic cleanup checks
        """
        self.environment_manager = environment_manager or EnvironmentManager()
        self.idle_threshold_seconds = idle_threshold_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        # Resource tracking
        self._resources: Dict[str, ResourceState] = {}
        self._lock = threading.RLock()
        
        # Cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_running = False
        
        # Cost configuration (default rates per hour)
        self._cost_rates = {
            'virtual': 0.10,  # $0.10/hour for virtual environments
            'physical': 1.00  # $1.00/hour for physical hardware
        }
    
    def register_resource(
        self,
        environment: Environment,
        hourly_cost: Optional[float] = None
    ) -> None:
        """Register a resource for management.
        
        Args:
            environment: Environment to register
            hourly_cost: Optional custom hourly cost rate
        """
        with self._lock:
            if environment.id in self._resources:
                return
            
            # Determine cost rate
            if hourly_cost is None:
                hourly_cost = (
                    self._cost_rates['virtual'] if environment.config.is_virtual
                    else self._cost_rates['physical']
                )
            
            # Create resource state
            resource_state = ResourceState(
                environment=environment,
                power_state=PowerState.ON,
                cost=ResourceCost(hourly_rate=hourly_cost),
                metrics=ResourceMetrics(environment_id=environment.id)
            )
            
            self._resources[environment.id] = resource_state
    
    def unregister_resource(self, environment_id: str) -> bool:
        """Unregister a resource from management.
        
        Args:
            environment_id: ID of environment to unregister
            
        Returns:
            True if unregistered successfully
        """
        with self._lock:
            if environment_id in self._resources:
                del self._resources[environment_id]
                return True
            return False
    
    def detect_idle_resources(self) -> List[str]:
        """Detect resources that have been idle beyond threshold.
        
        Returns:
            List of idle resource IDs
        """
        with self._lock:
            idle_resources = []
            for env_id, resource_state in self._resources.items():
                if resource_state.is_idle(self.idle_threshold_seconds):
                    idle_resources.append(env_id)
            return idle_resources
    
    def release_resource(self, environment_id: str) -> bool:
        """Release and power down an idle resource.
        
        Args:
            environment_id: ID of environment to release
            
        Returns:
            True if released successfully
        """
        with self._lock:
            resource_state = self._resources.get(environment_id)
            if not resource_state:
                return False
            
            # Only release if idle
            if resource_state.environment.status != EnvironmentStatus.IDLE:
                return False
            
            # Update metrics before cleanup
            self._update_metrics(environment_id)
            
            # Power down
            resource_state.power_state = PowerState.OFF
            resource_state.last_state_change = datetime.now()
            
            # Cleanup environment
            self.environment_manager.cleanup_environment(resource_state.environment)
            
            return True
    
    def cleanup_idle_resources(self) -> int:
        """Clean up all idle resources beyond threshold.
        
        Returns:
            Number of resources cleaned up
        """
        idle_resources = self.detect_idle_resources()
        cleaned = 0
        
        for env_id in idle_resources:
            if self.release_resource(env_id):
                cleaned += 1
        
        return cleaned
    
    def update_resource_usage(
        self,
        environment_id: str,
        status: EnvironmentStatus,
        test_completed: bool = False
    ) -> None:
        """Update resource usage tracking.
        
        Args:
            environment_id: ID of environment
            status: New status of environment
            test_completed: Whether a test just completed
        """
        with self._lock:
            resource_state = self._resources.get(environment_id)
            if not resource_state:
                return
            
            # Update environment status
            old_status = resource_state.environment.status
            resource_state.environment.status = status
            
            if status == EnvironmentStatus.IDLE:
                resource_state.environment.last_used = datetime.now()
            
            # Update metrics
            if resource_state.metrics:
                if test_completed:
                    resource_state.metrics.test_executions += 1
                    resource_state.metrics.last_test_execution = datetime.now()
            
            # Update cost
            self._update_cost(environment_id)
    
    def _update_cost(self, environment_id: str) -> None:
        """Update cost for a resource.
        
        Args:
            environment_id: ID of environment
        """
        resource_state = self._resources.get(environment_id)
        if not resource_state or not resource_state.cost:
            return
        
        # Calculate runtime since last update
        now = datetime.now()
        elapsed = (now - resource_state.cost.last_cost_update).total_seconds()
        
        # Update cost
        resource_state.cost.update_cost(elapsed)
    
    def _update_metrics(self, environment_id: str) -> None:
        """Update metrics for a resource.
        
        Args:
            environment_id: ID of environment
        """
        resource_state = self._resources.get(environment_id)
        if not resource_state or not resource_state.metrics:
            return
        
        # Calculate time since last update
        now = datetime.now()
        elapsed = (now - resource_state.last_state_change).total_seconds()
        
        # Update uptime
        resource_state.metrics.total_uptime_seconds += elapsed
        
        # Update busy/idle time based on status
        if resource_state.environment.status == EnvironmentStatus.BUSY:
            resource_state.metrics.total_busy_seconds += elapsed
        elif resource_state.environment.status == EnvironmentStatus.IDLE:
            resource_state.metrics.total_idle_seconds += elapsed
        
        resource_state.last_state_change = now
    
    def get_resource_cost(self, environment_id: str) -> Optional[ResourceCost]:
        """Get cost information for a resource.
        
        Args:
            environment_id: ID of environment
            
        Returns:
            ResourceCost or None
        """
        with self._lock:
            resource_state = self._resources.get(environment_id)
            if resource_state:
                # Update cost before returning
                self._update_cost(environment_id)
                return resource_state.cost
            return None
    
    def get_resource_metrics(self, environment_id: str) -> Optional[ResourceMetrics]:
        """Get metrics for a resource.
        
        Args:
            environment_id: ID of environment
            
        Returns:
            ResourceMetrics or None
        """
        with self._lock:
            resource_state = self._resources.get(environment_id)
            if resource_state:
                # Update metrics before returning
                self._update_metrics(environment_id)
                return resource_state.metrics
            return None
    
    def get_all_metrics(self) -> List[ResourceMetrics]:
        """Get metrics for all resources.
        
        Returns:
            List of ResourceMetrics
        """
        with self._lock:
            metrics = []
            for env_id in self._resources:
                self._update_metrics(env_id)
                if self._resources[env_id].metrics:
                    metrics.append(self._resources[env_id].metrics)
            return metrics
    
    def get_total_cost(self) -> float:
        """Get total cost across all resources.
        
        Returns:
            Total cost
        """
        with self._lock:
            total = 0.0
            for env_id, resource_state in self._resources.items():
                if resource_state.cost:
                    self._update_cost(env_id)
                    total += resource_state.cost.total_cost
            return total
    
    def get_utilization_summary(self) -> Dict:
        """Get utilization summary across all resources.
        
        Returns:
            Dictionary with utilization statistics
        """
        with self._lock:
            metrics = self.get_all_metrics()
            
            if not metrics:
                return {
                    'total_resources': 0,
                    'average_utilization': 0.0,
                    'average_idle_rate': 0.0,
                    'total_test_executions': 0
                }
            
            total_utilization = sum(m.utilization_rate for m in metrics)
            total_idle = sum(m.idle_rate for m in metrics)
            total_tests = sum(m.test_executions for m in metrics)
            
            return {
                'total_resources': len(metrics),
                'average_utilization': total_utilization / len(metrics),
                'average_idle_rate': total_idle / len(metrics),
                'total_test_executions': total_tests,
                'total_uptime_hours': sum(m.total_uptime_seconds for m in metrics) / 3600.0,
                'total_busy_hours': sum(m.total_busy_seconds for m in metrics) / 3600.0,
                'total_idle_hours': sum(m.total_idle_seconds for m in metrics) / 3600.0
            }
    
    def start_automatic_cleanup(self) -> None:
        """Start automatic cleanup thread."""
        if self._cleanup_running:
            return
        
        self._cleanup_running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()
    
    def stop_automatic_cleanup(self) -> None:
        """Stop automatic cleanup thread."""
        self._cleanup_running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5.0)
            self._cleanup_thread = None
    
    def _cleanup_loop(self) -> None:
        """Background loop for automatic cleanup."""
        while self._cleanup_running:
            try:
                self.cleanup_idle_resources()
            except Exception:
                pass  # Silently continue on errors
            
            time.sleep(self.cleanup_interval_seconds)
    
    def set_cost_rate(self, resource_type: str, hourly_rate: float) -> None:
        """Set cost rate for a resource type.
        
        Args:
            resource_type: 'virtual' or 'physical'
            hourly_rate: Cost per hour
        """
        if resource_type not in ['virtual', 'physical']:
            raise ValueError("resource_type must be 'virtual' or 'physical'")
        
        self._cost_rates[resource_type] = hourly_rate
    
    def get_resource_state(self, environment_id: str) -> Optional[ResourceState]:
        """Get complete state of a resource.
        
        Args:
            environment_id: ID of environment
            
        Returns:
            ResourceState or None
        """
        with self._lock:
            return self._resources.get(environment_id)
    
    def shutdown(self) -> None:
        """Shutdown resource manager and cleanup all resources."""
        self.stop_automatic_cleanup()
        
        with self._lock:
            # Cleanup all resources
            for env_id in list(self._resources.keys()):
                self.release_resource(env_id)
            
            self._resources.clear()
