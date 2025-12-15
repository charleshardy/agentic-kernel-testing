"""Resource management component for test execution environments."""

import logging
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import uuid

from .config import OrchestratorConfig


@dataclass
class Environment:
    """Represents a test execution environment."""
    id: str
    type: str  # docker, qemu, physical
    status: str  # available, busy, provisioning, error, maintenance
    hardware_config: Dict[str, Any]
    resource_usage: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime = field(default_factory=datetime.utcnow)
    current_test_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceManager:
    """Manages test execution environments and resource allocation."""
    
    def __init__(self, config: OrchestratorConfig):
        """Initialize the resource manager."""
        self.config = config
        self.logger = logging.getLogger('orchestrator.resource_manager')
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Environment management
        self._environments: Dict[str, Environment] = {}
        self._environment_pool: List[str] = []  # Available environment IDs
        
        # Resource tracking
        self._total_allocated_memory = 0  # MB
        self._total_allocated_cpu = 0.0   # CPU cores
        
        # Metrics
        self._metrics = {
            'environments_created': 0,
            'environments_destroyed': 0,
            'allocations': 0,
            'deallocations': 0,
            'allocation_failures': 0,
            'last_allocation': None
        }
        
        self._is_running = False
        self.logger.info("Resource manager initialized")
    
    def start(self):
        """Start the resource manager and initialize default environments."""
        try:
            with self._lock:
                if self._is_running:
                    self.logger.warning("Resource manager is already running")
                    return
                
                self._is_running = True
                
                # Create initial pool of environments
                self._initialize_environment_pool()
                
                self.logger.info(f"Resource manager started with {len(self._environments)} environments")
                
        except Exception as e:
            self.logger.error(f"Error starting resource manager: {e}")
            self._is_running = False
    
    def stop(self):
        """Stop the resource manager and clean up environments."""
        try:
            with self._lock:
                if not self._is_running:
                    self.logger.warning("Resource manager is not running")
                    return
                
                self._is_running = False
                
                # Clean up all environments
                self._cleanup_all_environments()
                
                self.logger.info("Resource manager stopped")
                
        except Exception as e:
            self.logger.error(f"Error stopping resource manager: {e}")
    
    def _initialize_environment_pool(self):
        """Initialize the default pool of environments."""
        try:
            # Create default Docker environments if enabled
            if self.config.docker_enabled:
                for i in range(min(5, self.config.max_environments)):
                    env_id = f"docker-{i+1}"
                    environment = Environment(
                        id=env_id,
                        type="docker",
                        status="available",
                        hardware_config={
                            "architecture": "x86_64",
                            "cpu_cores": 2.0,
                            "memory_mb": 2048,
                            "storage_gb": 10,
                            "is_virtual": True
                        }
                    )
                    
                    self._environments[env_id] = environment
                    self._environment_pool.append(env_id)
                    self._metrics['environments_created'] += 1
                
                self.logger.info(f"Created {len([e for e in self._environments.values() if e.type == 'docker'])} Docker environments")
            
            # TODO: Add QEMU environments when QEMU support is implemented
            if self.config.qemu_enabled:
                self.logger.info("QEMU support not yet implemented")
            
        except Exception as e:
            self.logger.error(f"Error initializing environment pool: {e}")
    
    def allocate_environment(self, hardware_requirements: Optional[Dict[str, Any]] = None,
                           test_id: Optional[str] = None) -> Optional[str]:
        """Allocate an environment that matches the hardware requirements."""
        try:
            with self._lock:
                if not self._is_running:
                    self.logger.error("Resource manager is not running")
                    return None
                
                # Find a suitable available environment
                suitable_env_id = self._find_suitable_environment(hardware_requirements)
                
                if suitable_env_id:
                    environment = self._environments[suitable_env_id]
                    
                    # Mark environment as busy
                    environment.status = "busy"
                    environment.current_test_id = test_id
                    environment.last_used = datetime.utcnow()
                    
                    # Remove from available pool
                    if suitable_env_id in self._environment_pool:
                        self._environment_pool.remove(suitable_env_id)
                    
                    # Update resource tracking
                    hw_config = environment.hardware_config
                    self._total_allocated_memory += hw_config.get('memory_mb', 0)
                    self._total_allocated_cpu += hw_config.get('cpu_cores', 0)
                    
                    # Update metrics
                    self._metrics['allocations'] += 1
                    self._metrics['last_allocation'] = datetime.utcnow()
                    
                    self.logger.info(f"Allocated environment {suitable_env_id} for test {test_id}")
                    return suitable_env_id
                
                else:
                    # No suitable environment available
                    self._metrics['allocation_failures'] += 1
                    self.logger.warning(f"No suitable environment available for requirements: {hardware_requirements}")
                    return None
                
        except Exception as e:
            self.logger.error(f"Error allocating environment: {e}")
            self._metrics['allocation_failures'] += 1
            return None
    
    def release_environment(self, env_id: str) -> bool:
        """Release an environment and make it available for reuse."""
        try:
            with self._lock:
                if env_id not in self._environments:
                    self.logger.error(f"Environment {env_id} not found")
                    return False
                
                environment = self._environments[env_id]
                
                # Update resource tracking
                hw_config = environment.hardware_config
                self._total_allocated_memory -= hw_config.get('memory_mb', 0)
                self._total_allocated_cpu -= hw_config.get('cpu_cores', 0)
                
                # Ensure non-negative values
                self._total_allocated_memory = max(0, self._total_allocated_memory)
                self._total_allocated_cpu = max(0.0, self._total_allocated_cpu)
                
                # Clean and reset environment
                environment.status = "available"
                environment.current_test_id = None
                environment.resource_usage.clear()
                
                # Add back to available pool
                if env_id not in self._environment_pool:
                    self._environment_pool.append(env_id)
                
                # Update metrics
                self._metrics['deallocations'] += 1
                
                self.logger.info(f"Released environment {env_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error releasing environment {env_id}: {e}")
            return False
    
    def _find_suitable_environment(self, requirements: Optional[Dict[str, Any]]) -> Optional[str]:
        """Find an available environment that matches the requirements."""
        try:
            # If no requirements specified, return any available environment
            if not requirements:
                return self._environment_pool[0] if self._environment_pool else None
            
            # Check each available environment
            for env_id in self._environment_pool:
                environment = self._environments[env_id]
                
                if self._environment_matches_requirements(environment, requirements):
                    return env_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding suitable environment: {e}")
            return None
    
    def _environment_matches_requirements(self, environment: Environment, 
                                        requirements: Dict[str, Any]) -> bool:
        """Check if an environment matches the given requirements."""
        try:
            hw_config = environment.hardware_config
            
            # Check architecture
            req_arch = requirements.get('architecture')
            if req_arch and hw_config.get('architecture') != req_arch:
                return False
            
            # Check memory (environment must have at least required memory)
            req_memory = requirements.get('memory_mb', 0)
            if req_memory > hw_config.get('memory_mb', 0):
                return False
            
            # Check CPU cores
            req_cpu = requirements.get('cpu_cores', 0)
            if req_cpu > hw_config.get('cpu_cores', 0):
                return False
            
            # Check virtualization preference
            req_virtual = requirements.get('is_virtual')
            if req_virtual is not None and hw_config.get('is_virtual') != req_virtual:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking environment requirements: {e}")
            return False
    
    def get_available_environment_count(self) -> int:
        """Get the number of available environments."""
        with self._lock:
            return len(self._environment_pool)
    
    def get_total_environment_count(self) -> int:
        """Get the total number of environments."""
        with self._lock:
            return len(self._environments)
    
    def get_busy_environment_count(self) -> int:
        """Get the number of busy environments."""
        with self._lock:
            return len([env for env in self._environments.values() if env.status == "busy"])
    
    def get_environment_status(self, env_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a specific environment."""
        try:
            with self._lock:
                if env_id not in self._environments:
                    return None
                
                environment = self._environments[env_id]
                return {
                    'id': environment.id,
                    'type': environment.type,
                    'status': environment.status,
                    'hardware_config': environment.hardware_config,
                    'resource_usage': environment.resource_usage,
                    'current_test_id': environment.current_test_id,
                    'created_at': environment.created_at.isoformat(),
                    'last_used': environment.last_used.isoformat(),
                    'metadata': environment.metadata
                }
                
        except Exception as e:
            self.logger.error(f"Error getting environment status for {env_id}: {e}")
            return None
    
    def get_all_environments_status(self) -> List[Dict[str, Any]]:
        """Get status of all environments."""
        try:
            with self._lock:
                return [
                    self.get_environment_status(env_id)
                    for env_id in self._environments.keys()
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting all environments status: {e}")
            return []
    
    def get_resource_utilization(self) -> Dict[str, Any]:
        """Get current resource utilization statistics."""
        try:
            with self._lock:
                total_memory = sum(env.hardware_config.get('memory_mb', 0) 
                                 for env in self._environments.values())
                total_cpu = sum(env.hardware_config.get('cpu_cores', 0) 
                              for env in self._environments.values())
                
                return {
                    'total_memory_mb': total_memory,
                    'allocated_memory_mb': self._total_allocated_memory,
                    'memory_utilization': self._total_allocated_memory / total_memory if total_memory > 0 else 0,
                    'total_cpu_cores': total_cpu,
                    'allocated_cpu_cores': self._total_allocated_cpu,
                    'cpu_utilization': self._total_allocated_cpu / total_cpu if total_cpu > 0 else 0,
                    'total_environments': len(self._environments),
                    'available_environments': len(self._environment_pool),
                    'busy_environments': self.get_busy_environment_count()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting resource utilization: {e}")
            return {}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the resource manager."""
        try:
            with self._lock:
                utilization = self.get_resource_utilization()
                
                return {
                    'status': 'healthy' if self._is_running else 'stopped',
                    'is_running': self._is_running,
                    'total_environments': len(self._environments),
                    'available_environments': len(self._environment_pool),
                    'busy_environments': self.get_busy_environment_count(),
                    'resource_utilization': utilization,
                    'metrics': self._metrics.copy()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def update_metrics(self):
        """Update resource manager metrics (called periodically)."""
        try:
            with self._lock:
                # Update environment statuses and clean up any stale environments
                current_time = datetime.utcnow()
                
                for env_id, environment in self._environments.items():
                    # Check for environments that have been busy too long
                    if (environment.status == "busy" and 
                        environment.current_test_id and
                        (current_time - environment.last_used).total_seconds() > 3600):  # 1 hour
                        
                        self.logger.warning(f"Environment {env_id} has been busy for over 1 hour, may be stuck")
                        # Could implement automatic cleanup here
                
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def _cleanup_all_environments(self):
        """Clean up all environments during shutdown."""
        try:
            with self._lock:
                for env_id in list(self._environments.keys()):
                    self.release_environment(env_id)
                
                self._environments.clear()
                self._environment_pool.clear()
                self._total_allocated_memory = 0
                self._total_allocated_cpu = 0.0
                
                self.logger.info("All environments cleaned up")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up environments: {e}")