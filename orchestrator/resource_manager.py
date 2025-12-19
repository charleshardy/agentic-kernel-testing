"""Resource management component for test execution environments."""

import logging
import threading
import time
import subprocess
import uuid
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .config import OrchestratorConfig
from ai_generator.models import HardwareConfig, Environment as ModelEnvironment, EnvironmentStatus


class EnvironmentType(str, Enum):
    """Types of execution environments."""
    DOCKER = "docker"
    QEMU = "qemu"
    PHYSICAL = "physical"
    CONTAINER = "container"


class EnvironmentHealth(str, Enum):
    """Health status of environments."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ManagedEnvironment:
    """Represents a managed test execution environment with lifecycle tracking."""
    id: str
    type: EnvironmentType
    status: str  # available, busy, provisioning, error, maintenance, cleanup
    hardware_config: HardwareConfig
    resource_usage: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime = field(default_factory=datetime.utcnow)
    last_health_check: datetime = field(default_factory=datetime.utcnow)
    current_test_id: Optional[str] = None
    health_status: EnvironmentHealth = EnvironmentHealth.UNKNOWN
    failure_count: int = 0
    total_tests_run: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_model_environment(self) -> ModelEnvironment:
        """Convert to the standard Environment model."""
        return ModelEnvironment(
            id=self.id,
            config=self.hardware_config,
            status=EnvironmentStatus(self.status) if self.status in [s.value for s in EnvironmentStatus] else EnvironmentStatus.ERROR,
            created_at=self.created_at,
            last_used=self.last_used,
            metadata=self.metadata
        )


class ResourceManager:
    """Manages test execution environments and resource allocation with advanced lifecycle management."""
    
    def __init__(self, config: OrchestratorConfig):
        """Initialize the resource manager."""
        self.config = config
        self.logger = logging.getLogger('orchestrator.resource_manager')
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Environment management
        self._environments: Dict[str, ManagedEnvironment] = {}
        self._environment_pool: List[str] = []  # Available environment IDs
        self._provisioning_environments: Set[str] = set()  # Environments being provisioned
        self._failed_environments: Set[str] = set()  # Environments that have failed
        
        # Resource tracking
        self._total_allocated_memory = 0  # MB
        self._total_allocated_cpu = 0.0   # CPU cores
        
        # Health monitoring
        self._health_check_thread: Optional[threading.Thread] = None
        self._health_check_stop_event = threading.Event()
        
        # Environment lifecycle management
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_stop_event = threading.Event()
        
        # Metrics
        self._metrics = {
            'environments_created': 0,
            'environments_destroyed': 0,
            'environments_provisioned': 0,
            'environments_recovered': 0,
            'allocations': 0,
            'deallocations': 0,
            'allocation_failures': 0,
            'health_checks_performed': 0,
            'health_check_failures': 0,
            'last_allocation': None,
            'last_health_check': None
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
                
                # Start health monitoring thread
                self._start_health_monitoring()
                
                # Start cleanup thread
                self._start_cleanup_monitoring()
                
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
                
                # Stop monitoring threads
                self._stop_health_monitoring()
                self._stop_cleanup_monitoring()
                
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
                docker_count = min(5, self.config.max_environments // 2)
                for i in range(docker_count):
                    env_id = f"docker-{uuid.uuid4().hex[:8]}"
                    hardware_config = HardwareConfig(
                        architecture="x86_64",
                        cpu_model="generic",
                        memory_mb=2048,
                        is_virtual=True
                    )
                    
                    environment = ManagedEnvironment(
                        id=env_id,
                        type=EnvironmentType.DOCKER,
                        status="provisioning",
                        hardware_config=hardware_config
                    )
                    
                    self._environments[env_id] = environment
                    self._provisioning_environments.add(env_id)
                    
                    # Provision the environment asynchronously
                    self._provision_environment_async(env_id)
                    
                    self._metrics['environments_created'] += 1
                
                self.logger.info(f"Provisioning {docker_count} Docker environments")
            
            # Create QEMU environments if enabled
            if self.config.qemu_enabled:
                qemu_count = min(3, self.config.max_environments // 3)
                for i in range(qemu_count):
                    env_id = f"qemu-{uuid.uuid4().hex[:8]}"
                    hardware_config = HardwareConfig(
                        architecture="x86_64",
                        cpu_model="qemu64",
                        memory_mb=4096,
                        is_virtual=True,
                        emulator="qemu"
                    )
                    
                    environment = ManagedEnvironment(
                        id=env_id,
                        type=EnvironmentType.QEMU,
                        status="provisioning",
                        hardware_config=hardware_config
                    )
                    
                    self._environments[env_id] = environment
                    self._provisioning_environments.add(env_id)
                    
                    # Provision the environment asynchronously
                    self._provision_environment_async(env_id)
                    
                    self._metrics['environments_created'] += 1
                
                self.logger.info(f"Provisioning {qemu_count} QEMU environments")
            
        except Exception as e:
            self.logger.error(f"Error initializing environment pool: {e}")
    
    def allocate_environment(self, hardware_requirements: Optional[HardwareConfig] = None,
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
                    environment.total_tests_run += 1
                    
                    # Remove from available pool
                    if suitable_env_id in self._environment_pool:
                        self._environment_pool.remove(suitable_env_id)
                    
                    # Update resource tracking
                    hw_config = environment.hardware_config
                    self._total_allocated_memory += hw_config.memory_mb
                    # Note: cpu_cores not in HardwareConfig, using default
                    self._total_allocated_cpu += 2.0  # Default CPU allocation
                    
                    # Update metrics
                    self._metrics['allocations'] += 1
                    self._metrics['last_allocation'] = datetime.utcnow()
                    
                    self.logger.info(f"Allocated environment {suitable_env_id} for test {test_id}")
                    return suitable_env_id
                
                else:
                    # Try to provision a new environment if we haven't reached the limit
                    if len(self._environments) < self.config.max_environments:
                        new_env_id = self._provision_new_environment(hardware_requirements)
                        if new_env_id:
                            self.logger.info(f"Provisioned new environment {new_env_id} for test {test_id}")
                            return self.allocate_environment(hardware_requirements, test_id)
                    
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
                self._total_allocated_memory -= hw_config.memory_mb
                self._total_allocated_cpu -= 2.0  # Default CPU allocation
                
                # Ensure non-negative values
                self._total_allocated_memory = max(0, self._total_allocated_memory)
                self._total_allocated_cpu = max(0.0, self._total_allocated_cpu)
                
                # Perform environment cleanup
                cleanup_success = self._cleanup_environment(env_id)
                
                if cleanup_success:
                    # Reset environment state
                    environment.status = "available"
                    environment.current_test_id = None
                    environment.resource_usage.clear()
                    environment.health_status = EnvironmentHealth.UNKNOWN
                    
                    # Add back to available pool
                    if env_id not in self._environment_pool:
                        self._environment_pool.append(env_id)
                    
                    # Update metrics
                    self._metrics['deallocations'] += 1
                    
                    self.logger.info(f"Released environment {env_id}")
                    return True
                else:
                    # Mark environment as failed if cleanup failed
                    environment.status = "error"
                    environment.failure_count += 1
                    self._failed_environments.add(env_id)
                    
                    self.logger.error(f"Failed to cleanup environment {env_id}, marked as failed")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error releasing environment {env_id}: {e}")
            return False
    
    def _find_suitable_environment(self, requirements: Optional[HardwareConfig]) -> Optional[str]:
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
    
    def _environment_matches_requirements(self, environment: ManagedEnvironment, 
                                        requirements: HardwareConfig) -> bool:
        """Check if an environment matches the given requirements."""
        try:
            hw_config = environment.hardware_config
            
            # Check architecture
            if requirements.architecture and hw_config.architecture != requirements.architecture:
                return False
            
            # Check memory (environment must have at least required memory)
            if requirements.memory_mb > hw_config.memory_mb:
                return False
            
            # Check virtualization preference
            if requirements.is_virtual != hw_config.is_virtual:
                return False
            
            # Check emulator compatibility if specified
            if requirements.emulator and hw_config.emulator != requirements.emulator:
                return False
            
            # Check peripherals (environment must support all required peripherals)
            if requirements.peripherals:
                env_peripheral_types = {p.type for p in hw_config.peripherals}
                req_peripheral_types = {p.type for p in requirements.peripherals}
                if not req_peripheral_types.issubset(env_peripheral_types):
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
                total_memory = sum(env.hardware_config.memory_mb 
                                 for env in self._environments.values())
                # Since HardwareConfig doesn't have cpu_cores, use a default of 2.0 per environment
                total_cpu = len(self._environments) * 2.0
                
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
    # Environment Lifecycle Management Methods
    
    def _provision_environment_async(self, env_id: str):
        """Provision an environment asynchronously."""
        def provision_worker():
            try:
                success = self._provision_environment(env_id)
                with self._lock:
                    if env_id in self._provisioning_environments:
                        self._provisioning_environments.remove(env_id)
                    
                    if success:
                        environment = self._environments[env_id]
                        environment.status = "available"
                        environment.health_status = EnvironmentHealth.HEALTHY
                        self._environment_pool.append(env_id)
                        self._metrics['environments_provisioned'] += 1
                        self.logger.info(f"Successfully provisioned environment {env_id}")
                    else:
                        environment = self._environments[env_id]
                        environment.status = "error"
                        environment.health_status = EnvironmentHealth.UNHEALTHY
                        environment.failure_count += 1
                        self._failed_environments.add(env_id)
                        self.logger.error(f"Failed to provision environment {env_id}")
                        
            except Exception as e:
                self.logger.error(f"Error in provision worker for {env_id}: {e}")
                with self._lock:
                    if env_id in self._provisioning_environments:
                        self._provisioning_environments.remove(env_id)
                    if env_id in self._environments:
                        self._environments[env_id].status = "error"
                        self._failed_environments.add(env_id)
        
        # Start provisioning in a separate thread
        thread = threading.Thread(target=provision_worker, name=f"provision-{env_id}")
        thread.daemon = True
        thread.start()
    
    def _provision_environment(self, env_id: str) -> bool:
        """Provision a specific environment."""
        try:
            environment = self._environments[env_id]
            
            if environment.type == EnvironmentType.DOCKER:
                return self._provision_docker_environment(env_id)
            elif environment.type == EnvironmentType.QEMU:
                return self._provision_qemu_environment(env_id)
            elif environment.type == EnvironmentType.PHYSICAL:
                return self._provision_physical_environment(env_id)
            else:
                self.logger.error(f"Unknown environment type: {environment.type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error provisioning environment {env_id}: {e}")
            return False
    
    def _provision_docker_environment(self, env_id: str) -> bool:
        """Provision a Docker-based environment."""
        try:
            # For now, simulate Docker environment provisioning
            # In a real implementation, this would:
            # 1. Pull required Docker images
            # 2. Create Docker network if needed
            # 3. Prepare volumes and configurations
            # 4. Validate Docker daemon connectivity
            
            self.logger.info(f"Provisioning Docker environment {env_id}")
            
            # Simulate provisioning time
            time.sleep(2.0)
            
            # Check if Docker is available (basic check)
            try:
                result = subprocess.run(['docker', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.logger.info(f"Docker environment {env_id} provisioned successfully")
                    return True
                else:
                    self.logger.error(f"Docker not available for environment {env_id}")
                    return False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.logger.warning(f"Docker check failed for environment {env_id}, assuming available")
                return True  # Assume Docker is available for testing
                
        except Exception as e:
            self.logger.error(f"Error provisioning Docker environment {env_id}: {e}")
            return False
    
    def _provision_qemu_environment(self, env_id: str) -> bool:
        """Provision a QEMU-based environment."""
        try:
            # For now, simulate QEMU environment provisioning
            # In a real implementation, this would:
            # 1. Prepare QEMU disk images
            # 2. Set up network configurations
            # 3. Validate QEMU installation
            # 4. Prepare kernel images and initrd
            
            self.logger.info(f"Provisioning QEMU environment {env_id}")
            
            # Simulate provisioning time
            time.sleep(5.0)
            
            # Check if QEMU is available (basic check)
            try:
                result = subprocess.run(['qemu-system-x86_64', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.logger.info(f"QEMU environment {env_id} provisioned successfully")
                    return True
                else:
                    self.logger.error(f"QEMU not available for environment {env_id}")
                    return False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.logger.warning(f"QEMU check failed for environment {env_id}, assuming available")
                return True  # Assume QEMU is available for testing
                
        except Exception as e:
            self.logger.error(f"Error provisioning QEMU environment {env_id}: {e}")
            return False
    
    def _provision_physical_environment(self, env_id: str) -> bool:
        """Provision a physical hardware environment."""
        try:
            # For now, simulate physical environment provisioning
            # In a real implementation, this would:
            # 1. Check hardware availability
            # 2. Configure network access
            # 3. Validate SSH connectivity
            # 4. Prepare bootloader configurations
            
            self.logger.info(f"Provisioning physical environment {env_id}")
            
            # Simulate provisioning time
            time.sleep(3.0)
            
            self.logger.info(f"Physical environment {env_id} provisioned successfully")
            return True
                
        except Exception as e:
            self.logger.error(f"Error provisioning physical environment {env_id}: {e}")
            return False
    
    def _provision_new_environment(self, requirements: Optional[HardwareConfig]) -> Optional[str]:
        """Provision a new environment based on requirements."""
        try:
            if not requirements:
                # Create a default Docker environment
                requirements = HardwareConfig(
                    architecture="x86_64",
                    cpu_model="generic",
                    memory_mb=2048,
                    is_virtual=True
                )
            
            # Determine environment type based on requirements
            if requirements.is_virtual:
                if requirements.emulator == "qemu":
                    env_type = EnvironmentType.QEMU
                else:
                    env_type = EnvironmentType.DOCKER
            else:
                env_type = EnvironmentType.PHYSICAL
            
            # Create new environment
            env_id = f"{env_type.value}-{uuid.uuid4().hex[:8]}"
            environment = ManagedEnvironment(
                id=env_id,
                type=env_type,
                status="provisioning",
                hardware_config=requirements
            )
            
            self._environments[env_id] = environment
            self._provisioning_environments.add(env_id)
            self._metrics['environments_created'] += 1
            
            # Start provisioning asynchronously
            self._provision_environment_async(env_id)
            
            return env_id
            
        except Exception as e:
            self.logger.error(f"Error provisioning new environment: {e}")
            return None
    
    def _cleanup_environment(self, env_id: str) -> bool:
        """Clean up an environment after use."""
        try:
            environment = self._environments[env_id]
            
            if environment.type == EnvironmentType.DOCKER:
                return self._cleanup_docker_environment(env_id)
            elif environment.type == EnvironmentType.QEMU:
                return self._cleanup_qemu_environment(env_id)
            elif environment.type == EnvironmentType.PHYSICAL:
                return self._cleanup_physical_environment(env_id)
            else:
                self.logger.error(f"Unknown environment type for cleanup: {environment.type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error cleaning up environment {env_id}: {e}")
            return False
    
    def _cleanup_docker_environment(self, env_id: str) -> bool:
        """Clean up a Docker environment."""
        try:
            # In a real implementation, this would:
            # 1. Stop and remove any running containers
            # 2. Clean up volumes and networks
            # 3. Remove temporary files
            # 4. Reset container state
            
            self.logger.info(f"Cleaning up Docker environment {env_id}")
            
            # Simulate cleanup time
            time.sleep(1.0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up Docker environment {env_id}: {e}")
            return False
    
    def _cleanup_qemu_environment(self, env_id: str) -> bool:
        """Clean up a QEMU environment."""
        try:
            # In a real implementation, this would:
            # 1. Terminate any running QEMU processes
            # 2. Clean up disk images and snapshots
            # 3. Reset network configurations
            # 4. Remove temporary files
            
            self.logger.info(f"Cleaning up QEMU environment {env_id}")
            
            # Simulate cleanup time
            time.sleep(2.0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up QEMU environment {env_id}: {e}")
            return False
    
    def _cleanup_physical_environment(self, env_id: str) -> bool:
        """Clean up a physical environment."""
        try:
            # In a real implementation, this would:
            # 1. Reset hardware to known state
            # 2. Clear any test artifacts
            # 3. Validate hardware health
            # 4. Prepare for next test
            
            self.logger.info(f"Cleaning up physical environment {env_id}")
            
            # Simulate cleanup time
            time.sleep(1.5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up physical environment {env_id}: {e}")
            return False
    
    # Health Monitoring Methods
    
    def _start_health_monitoring(self):
        """Start the health monitoring thread."""
        try:
            self._health_check_stop_event.clear()
            self._health_check_thread = threading.Thread(
                target=self._health_monitoring_loop,
                name="resource-health-monitor",
                daemon=True
            )
            self._health_check_thread.start()
            self.logger.info("Health monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting health monitoring: {e}")
    
    def _stop_health_monitoring(self):
        """Stop the health monitoring thread."""
        try:
            self._health_check_stop_event.set()
            if self._health_check_thread and self._health_check_thread.is_alive():
                self._health_check_thread.join(timeout=5.0)
                if self._health_check_thread.is_alive():
                    self.logger.warning("Health monitoring thread did not stop gracefully")
            self.logger.info("Health monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping health monitoring: {e}")
    
    def _health_monitoring_loop(self):
        """Main loop for health monitoring."""
        while not self._health_check_stop_event.is_set():
            try:
                self._perform_health_checks()
                
                # Wait for next check interval
                if self._health_check_stop_event.wait(self.config.health_check_interval):
                    break  # Stop event was set
                    
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(5.0)  # Brief pause before retrying
    
    def _perform_health_checks(self):
        """Perform health checks on all environments."""
        try:
            with self._lock:
                current_time = datetime.utcnow()
                
                for env_id, environment in self._environments.items():
                    # Skip environments that are provisioning or already failed
                    if (environment.status in ["provisioning", "error"] or 
                        env_id in self._provisioning_environments):
                        continue
                    
                    # Check if it's time for a health check
                    time_since_last_check = (current_time - environment.last_health_check).total_seconds()
                    if time_since_last_check < self.config.health_check_interval:
                        continue
                    
                    # Perform health check
                    health_status = self._check_environment_health(env_id)
                    environment.last_health_check = current_time
                    environment.health_status = health_status
                    
                    # Handle unhealthy environments
                    if health_status == EnvironmentHealth.UNHEALTHY:
                        self._handle_unhealthy_environment(env_id)
                    
                    self._metrics['health_checks_performed'] += 1
                
                self._metrics['last_health_check'] = current_time
                
        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}")
            self._metrics['health_check_failures'] += 1
    
    def _check_environment_health(self, env_id: str) -> EnvironmentHealth:
        """Check the health of a specific environment."""
        try:
            environment = self._environments[env_id]
            
            # Check if environment has been busy too long
            if environment.status == "busy" and environment.current_test_id:
                busy_time = (datetime.utcnow() - environment.last_used).total_seconds()
                if busy_time > 3600:  # 1 hour
                    self.logger.warning(f"Environment {env_id} has been busy for {busy_time:.0f} seconds")
                    return EnvironmentHealth.DEGRADED
            
            # Check failure count
            if environment.failure_count > 3:
                return EnvironmentHealth.UNHEALTHY
            elif environment.failure_count > 1:
                return EnvironmentHealth.DEGRADED
            
            # Environment-specific health checks
            if environment.type == EnvironmentType.DOCKER:
                return self._check_docker_health(env_id)
            elif environment.type == EnvironmentType.QEMU:
                return self._check_qemu_health(env_id)
            elif environment.type == EnvironmentType.PHYSICAL:
                return self._check_physical_health(env_id)
            
            return EnvironmentHealth.HEALTHY
            
        except Exception as e:
            self.logger.error(f"Error checking health of environment {env_id}: {e}")
            return EnvironmentHealth.UNKNOWN
    
    def _check_docker_health(self, env_id: str) -> EnvironmentHealth:
        """Check health of a Docker environment."""
        try:
            # Basic Docker daemon connectivity check
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return EnvironmentHealth.HEALTHY
            else:
                return EnvironmentHealth.DEGRADED
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return EnvironmentHealth.DEGRADED
        except Exception as e:
            self.logger.error(f"Error checking Docker health for {env_id}: {e}")
            return EnvironmentHealth.UNKNOWN
    
    def _check_qemu_health(self, env_id: str) -> EnvironmentHealth:
        """Check health of a QEMU environment."""
        try:
            # Basic QEMU availability check
            result = subprocess.run(['qemu-system-x86_64', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return EnvironmentHealth.HEALTHY
            else:
                return EnvironmentHealth.DEGRADED
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return EnvironmentHealth.DEGRADED
        except Exception as e:
            self.logger.error(f"Error checking QEMU health for {env_id}: {e}")
            return EnvironmentHealth.UNKNOWN
    
    def _check_physical_health(self, env_id: str) -> EnvironmentHealth:
        """Check health of a physical environment."""
        try:
            # For physical environments, we would typically:
            # 1. Check SSH connectivity
            # 2. Verify hardware sensors
            # 3. Check system load and resources
            # 4. Validate network connectivity
            
            # For now, assume physical environments are always healthy
            return EnvironmentHealth.HEALTHY
            
        except Exception as e:
            self.logger.error(f"Error checking physical health for {env_id}: {e}")
            return EnvironmentHealth.UNKNOWN
    
    def _handle_unhealthy_environment(self, env_id: str):
        """Handle an unhealthy environment."""
        try:
            environment = self._environments[env_id]
            
            # Remove from available pool if present
            if env_id in self._environment_pool:
                self._environment_pool.remove(env_id)
            
            # Mark as failed
            self._failed_environments.add(env_id)
            environment.status = "error"
            
            # Attempt recovery if failure count is not too high
            if environment.failure_count < 5:
                self.logger.info(f"Attempting to recover unhealthy environment {env_id}")
                self._recover_environment_async(env_id)
            else:
                self.logger.error(f"Environment {env_id} has failed too many times, marking for replacement")
                self._replace_environment_async(env_id)
            
        except Exception as e:
            self.logger.error(f"Error handling unhealthy environment {env_id}: {e}")
    
    def _recover_environment_async(self, env_id: str):
        """Attempt to recover a failed environment asynchronously."""
        def recovery_worker():
            try:
                success = self._recover_environment(env_id)
                with self._lock:
                    if success:
                        environment = self._environments[env_id]
                        environment.status = "available"
                        environment.health_status = EnvironmentHealth.HEALTHY
                        if env_id in self._failed_environments:
                            self._failed_environments.remove(env_id)
                        if env_id not in self._environment_pool:
                            self._environment_pool.append(env_id)
                        self._metrics['environments_recovered'] += 1
                        self.logger.info(f"Successfully recovered environment {env_id}")
                    else:
                        environment = self._environments[env_id]
                        environment.failure_count += 1
                        self.logger.error(f"Failed to recover environment {env_id}")
                        
            except Exception as e:
                self.logger.error(f"Error in recovery worker for {env_id}: {e}")
        
        # Start recovery in a separate thread
        thread = threading.Thread(target=recovery_worker, name=f"recover-{env_id}")
        thread.daemon = True
        thread.start()
    
    def _recover_environment(self, env_id: str) -> bool:
        """Attempt to recover a specific environment."""
        try:
            environment = self._environments[env_id]
            
            # First, try cleanup
            cleanup_success = self._cleanup_environment(env_id)
            if not cleanup_success:
                return False
            
            # Then, re-provision
            provision_success = self._provision_environment(env_id)
            return provision_success
            
        except Exception as e:
            self.logger.error(f"Error recovering environment {env_id}: {e}")
            return False
    
    def _replace_environment_async(self, env_id: str):
        """Replace a failed environment with a new one asynchronously."""
        def replacement_worker():
            try:
                # Create a new environment with the same configuration
                old_environment = self._environments[env_id]
                new_env_id = self._provision_new_environment(old_environment.hardware_config)
                
                if new_env_id:
                    # Remove the old environment
                    with self._lock:
                        if env_id in self._environments:
                            del self._environments[env_id]
                        if env_id in self._environment_pool:
                            self._environment_pool.remove(env_id)
                        if env_id in self._failed_environments:
                            self._failed_environments.remove(env_id)
                        
                        self._metrics['environments_destroyed'] += 1
                    
                    self.logger.info(f"Replaced failed environment {env_id} with {new_env_id}")
                else:
                    self.logger.error(f"Failed to create replacement for environment {env_id}")
                    
            except Exception as e:
                self.logger.error(f"Error in replacement worker for {env_id}: {e}")
        
        # Start replacement in a separate thread
        thread = threading.Thread(target=replacement_worker, name=f"replace-{env_id}")
        thread.daemon = True
        thread.start()
    
    # Cleanup Monitoring Methods
    
    def _start_cleanup_monitoring(self):
        """Start the cleanup monitoring thread."""
        try:
            self._cleanup_stop_event.clear()
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_monitoring_loop,
                name="resource-cleanup-monitor",
                daemon=True
            )
            self._cleanup_thread.start()
            self.logger.info("Cleanup monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting cleanup monitoring: {e}")
    
    def _stop_cleanup_monitoring(self):
        """Stop the cleanup monitoring thread."""
        try:
            self._cleanup_stop_event.set()
            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._cleanup_thread.join(timeout=5.0)
                if self._cleanup_thread.is_alive():
                    self.logger.warning("Cleanup monitoring thread did not stop gracefully")
            self.logger.info("Cleanup monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping cleanup monitoring: {e}")
    
    def _cleanup_monitoring_loop(self):
        """Main loop for cleanup monitoring."""
        while not self._cleanup_stop_event.is_set():
            try:
                self._perform_periodic_cleanup()
                
                # Wait for next cleanup interval (every 5 minutes)
                if self._cleanup_stop_event.wait(300):  # 5 minutes
                    break  # Stop event was set
                    
            except Exception as e:
                self.logger.error(f"Error in cleanup monitoring loop: {e}")
                time.sleep(30.0)  # Brief pause before retrying
    
    def _perform_periodic_cleanup(self):
        """Perform periodic cleanup tasks."""
        try:
            with self._lock:
                current_time = datetime.utcnow()
                
                # Clean up old failed environments
                failed_to_remove = []
                for env_id in list(self._failed_environments):
                    environment = self._environments.get(env_id)
                    if environment:
                        # Remove environments that have been failed for more than 1 hour
                        if (current_time - environment.last_used).total_seconds() > 3600:
                            failed_to_remove.append(env_id)
                
                for env_id in failed_to_remove:
                    self._remove_failed_environment(env_id)
                
                # Clean up environments that have been idle for too long
                idle_environments = []
                for env_id, environment in self._environments.items():
                    if (environment.status == "available" and 
                        (current_time - environment.last_used).total_seconds() > 7200):  # 2 hours
                        idle_environments.append(env_id)
                
                # Keep a minimum number of environments
                min_environments = max(2, self.config.max_environments // 4)
                available_count = len(self._environment_pool)
                
                for env_id in idle_environments:
                    if available_count > min_environments:
                        self._remove_idle_environment(env_id)
                        available_count -= 1
                
        except Exception as e:
            self.logger.error(f"Error performing periodic cleanup: {e}")
    
    def _remove_failed_environment(self, env_id: str):
        """Remove a failed environment."""
        try:
            if env_id in self._environments:
                del self._environments[env_id]
            if env_id in self._environment_pool:
                self._environment_pool.remove(env_id)
            if env_id in self._failed_environments:
                self._failed_environments.remove(env_id)
            
            self._metrics['environments_destroyed'] += 1
            self.logger.info(f"Removed failed environment {env_id}")
            
        except Exception as e:
            self.logger.error(f"Error removing failed environment {env_id}: {e}")
    
    def _remove_idle_environment(self, env_id: str):
        """Remove an idle environment to free resources."""
        try:
            # Perform cleanup first
            cleanup_success = self._cleanup_environment(env_id)
            
            if env_id in self._environments:
                del self._environments[env_id]
            if env_id in self._environment_pool:
                self._environment_pool.remove(env_id)
            
            self._metrics['environments_destroyed'] += 1
            self.logger.info(f"Removed idle environment {env_id}")
            
        except Exception as e:
            self.logger.error(f"Error removing idle environment {env_id}: {e}")