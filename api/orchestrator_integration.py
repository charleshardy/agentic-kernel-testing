"""Integration module for connecting the orchestrator with the API server."""

import logging
import atexit
from typing import Optional

from orchestrator import OrchestratorService, OrchestratorConfig
from .routers.health import set_orchestrator_service

# Global orchestrator instance
_orchestrator: Optional[OrchestratorService] = None

logger = logging.getLogger(__name__)


def start_orchestrator() -> bool:
    """Start the orchestrator service."""
    global _orchestrator
    
    try:
        if _orchestrator and _orchestrator.is_running:
            logger.warning("Orchestrator is already running")
            return True
        
        # Create orchestrator configuration
        config = OrchestratorConfig.from_env()
        
        # Create and start orchestrator service
        _orchestrator = OrchestratorService(config)
        
        if _orchestrator.start():
            # Register orchestrator with health endpoint
            set_orchestrator_service(_orchestrator)
            
            # Register shutdown handler
            atexit.register(stop_orchestrator)
            
            logger.info("Orchestrator service started successfully")
            return True
        else:
            logger.error("Failed to start orchestrator service")
            return False
            
    except Exception as e:
        logger.error(f"Error starting orchestrator: {e}")
        return False


def stop_orchestrator() -> bool:
    """Stop the orchestrator service."""
    global _orchestrator
    
    try:
        if _orchestrator and _orchestrator.is_running:
            if _orchestrator.stop():
                logger.info("Orchestrator service stopped successfully")
                return True
            else:
                logger.error("Failed to stop orchestrator service")
                return False
        else:
            logger.warning("Orchestrator is not running")
            return True
            
    except Exception as e:
        logger.error(f"Error stopping orchestrator: {e}")
        return False


def get_orchestrator() -> Optional[OrchestratorService]:
    """Get the current orchestrator instance."""
    return _orchestrator


def is_orchestrator_running() -> bool:
    """Check if the orchestrator is currently running."""
    return _orchestrator is not None and _orchestrator.is_running


def get_orchestrator_status() -> dict:
    """Get the current status of the orchestrator."""
    if _orchestrator:
        return _orchestrator.get_health_status()
    else:
        return {
            'status': 'not_initialized',
            'is_running': False,
            'message': 'Orchestrator service not initialized'
        }