"""Configuration for the Test Execution Orchestrator."""

from dataclasses import dataclass
from typing import Dict, Any
import os


@dataclass
class OrchestratorConfig:
    """Configuration settings for the orchestrator service."""
    
    # Service settings
    poll_interval: float = 5.0  # Seconds between queue polls
    max_concurrent_tests: int = 10  # Maximum tests running simultaneously
    default_timeout: int = 300  # Default test timeout in seconds
    
    # Environment settings
    docker_enabled: bool = True
    qemu_enabled: bool = False  # Enable when QEMU support is added
    max_environments: int = 20
    environment_cleanup_timeout: int = 30
    
    # Resource limits
    max_memory_per_test: int = 2048  # MB
    max_cpu_per_test: float = 2.0  # CPU cores
    
    # Logging and monitoring
    log_level: str = "INFO"
    metrics_enabled: bool = True
    health_check_interval: float = 30.0
    
    # Persistence
    state_file: str = "orchestrator_state.json"
    enable_persistence: bool = True
    
    @classmethod
    def from_env(cls) -> 'OrchestratorConfig':
        """Create configuration from environment variables."""
        return cls(
            poll_interval=float(os.getenv('ORCHESTRATOR_POLL_INTERVAL', '5.0')),
            max_concurrent_tests=int(os.getenv('ORCHESTRATOR_MAX_CONCURRENT', '10')),
            default_timeout=int(os.getenv('ORCHESTRATOR_DEFAULT_TIMEOUT', '300')),
            docker_enabled=os.getenv('ORCHESTRATOR_DOCKER_ENABLED', 'true').lower() == 'true',
            qemu_enabled=os.getenv('ORCHESTRATOR_QEMU_ENABLED', 'false').lower() == 'true',
            max_environments=int(os.getenv('ORCHESTRATOR_MAX_ENVIRONMENTS', '20')),
            log_level=os.getenv('ORCHESTRATOR_LOG_LEVEL', 'INFO'),
            metrics_enabled=os.getenv('ORCHESTRATOR_METRICS_ENABLED', 'true').lower() == 'true',
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'poll_interval': self.poll_interval,
            'max_concurrent_tests': self.max_concurrent_tests,
            'default_timeout': self.default_timeout,
            'docker_enabled': self.docker_enabled,
            'qemu_enabled': self.qemu_enabled,
            'max_environments': self.max_environments,
            'log_level': self.log_level,
            'metrics_enabled': self.metrics_enabled,
        }