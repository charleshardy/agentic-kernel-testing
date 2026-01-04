"""
Test Deployment System

This module provides automated deployment of test scripts, dependencies, and configurations
to allocated environments, bridging the gap between environment allocation and test execution.
"""

from .orchestrator import DeploymentOrchestrator
from .models import (
    DeploymentPlan,
    DeploymentStatus,
    DeploymentResult,
    TestArtifact,
    InstrumentationConfig
)

__all__ = [
    'DeploymentOrchestrator',
    'DeploymentPlan',
    'DeploymentStatus', 
    'DeploymentResult',
    'TestArtifact',
    'InstrumentationConfig'
]