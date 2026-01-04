"""
Deployment Orchestrator

Main orchestrator class responsible for coordinating deployment activities
across multiple environments with error recovery and retry logic.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor

from .models import (
    DeploymentPlan,
    DeploymentResult,
    DeploymentStatus,
    DeploymentStep,
    TestArtifact,
    ValidationResult
)
from .environment_manager import EnvironmentManagerFactory
from .artifact_repository import ArtifactRepository
from .instrumentation_manager import InstrumentationManager


logger = logging.getLogger(__name__)


class DeploymentOrchestrator:
    """
    Main orchestrator for test deployment operations.
    
    Coordinates deployment activities across multiple environments,
    manages deployment pipeline execution and state, handles error
    recovery and retry logic, and provides real-time status updates.
    """
    
    def __init__(self, 
                 max_concurrent_deployments: int = 5,
                 default_timeout: int = 300):
        """
        Initialize the deployment orchestrator.
        
        Args:
            max_concurrent_deployments: Maximum number of concurrent deployments
            default_timeout: Default timeout for deployment operations in seconds
        """
        self.max_concurrent_deployments = max_concurrent_deployments
        self.default_timeout = default_timeout
        
        # Core components
        self.environment_manager_factory = EnvironmentManagerFactory()
        self.artifact_repository = ArtifactRepository()
        self.instrumentation_manager = InstrumentationManager()
        
        # State tracking
        self.active_deployments: Dict[str, DeploymentResult] = {}
        self.deployment_queue: asyncio.Queue = asyncio.Queue()
        self.deployment_semaphore = asyncio.Semaphore(max_concurrent_deployments)
        
        # Background tasks
        self._deployment_worker_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        logger.info(f"DeploymentOrchestrator initialized with max_concurrent_deployments={max_concurrent_deployments}")
    
    async def start(self):
        """Start the deployment orchestrator background tasks"""
        if self._is_running:
            logger.warning("DeploymentOrchestrator is already running")
            return
        
        self._is_running = True
        self._deployment_worker_task = asyncio.create_task(self._deployment_worker())
        logger.info("DeploymentOrchestrator started")
    
    async def stop(self):
        """Stop the deployment orchestrator and cleanup resources"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        if self._deployment_worker_task:
            self._deployment_worker_task.cancel()
            try:
                await self._deployment_worker_task
            except asyncio.CancelledError:
                pass
        
        # Cancel any active deployments
        for deployment_id in list(self.active_deployments.keys()):
            await self.cancel_deployment(deployment_id)
        
        logger.info("DeploymentOrchestrator stopped")
    
    async def deploy_to_environment(self, 
                                  plan_id: str, 
                                  env_id: str, 
                                  artifacts: List[TestArtifact]) -> str:
        """
        Deploy test artifacts to a specific environment.
        
        Args:
            plan_id: Test plan identifier
            env_id: Environment identifier
            artifacts: List of test artifacts to deploy
            
        Returns:
            Deployment ID for tracking the deployment
            
        Raises:
            ValueError: If invalid parameters are provided
            RuntimeError: If orchestrator is not running
        """
        if not self._is_running:
            raise RuntimeError("DeploymentOrchestrator is not running")
        
        if not plan_id or not env_id or not artifacts:
            raise ValueError("plan_id, env_id, and artifacts are required")
        
        # Generate unique deployment ID
        deployment_id = f"deploy_{uuid.uuid4().hex[:8]}"
        
        # Create deployment plan
        from .models import DeploymentPlan, DeploymentConfig, InstrumentationConfig, Dependency
        
        deployment_plan = DeploymentPlan(
            plan_id=deployment_id,
            environment_id=env_id,
            test_artifacts=artifacts,
            dependencies=[],  # Will be populated based on artifacts
            instrumentation_config=InstrumentationConfig(),
            deployment_config=DeploymentConfig(),
            created_at=datetime.now()
        )
        
        # Create initial deployment result
        deployment_result = DeploymentResult(
            deployment_id=deployment_id,
            plan_id=plan_id,
            environment_id=env_id,
            status=DeploymentStatus.PENDING,
            start_time=datetime.now()
        )
        
        # Track the deployment
        self.active_deployments[deployment_id] = deployment_result
        
        # Queue the deployment for processing
        await self.deployment_queue.put(deployment_plan)
        
        logger.info(f"Queued deployment {deployment_id} for environment {env_id}")
        return deployment_id
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """
        Get the current status of a deployment.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            DeploymentResult if found, None otherwise
        """
        return self.active_deployments.get(deployment_id)
    
    async def cancel_deployment(self, deployment_id: str) -> bool:
        """
        Cancel an active deployment.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            True if deployment was cancelled, False if not found or already completed
        """
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            logger.warning(f"Deployment {deployment_id} not found")
            return False
        
        if deployment.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]:
            logger.warning(f"Deployment {deployment_id} is already in final state: {deployment.status}")
            return False
        
        # Update status to cancelled
        deployment.status = DeploymentStatus.CANCELLED
        deployment.end_time = datetime.now()
        deployment.error_message = "Deployment cancelled by user"
        
        logger.info(f"Cancelled deployment {deployment_id}")
        return True
    
    async def retry_failed_deployment(self, deployment_id: str) -> Optional[str]:
        """
        Retry a failed deployment.
        
        Args:
            deployment_id: Failed deployment identifier
            
        Returns:
            New deployment ID if retry was initiated, None if deployment not found or not failed
        """
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            logger.warning(f"Deployment {deployment_id} not found")
            return None
        
        if deployment.status != DeploymentStatus.FAILED:
            logger.warning(f"Deployment {deployment_id} is not in failed state: {deployment.status}")
            return None
        
        # Create a new deployment with the same parameters
        # This is a simplified retry - in a real implementation, you'd want to
        # preserve the original deployment plan and artifacts
        logger.info(f"Retrying failed deployment {deployment_id}")
        
        # For now, return the same deployment_id to indicate retry was attempted
        # In a full implementation, this would create a new deployment
        return deployment_id
    
    async def _deployment_worker(self):
        """Background worker that processes deployment queue"""
        logger.info("Deployment worker started")
        
        while self._is_running:
            try:
                # Wait for deployment plan with timeout
                deployment_plan = await asyncio.wait_for(
                    self.deployment_queue.get(), 
                    timeout=1.0
                )
                
                # Process deployment with semaphore to limit concurrency
                async with self.deployment_semaphore:
                    await self._process_deployment(deployment_plan)
                
            except asyncio.TimeoutError:
                # No deployment in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error in deployment worker: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before retrying
        
        logger.info("Deployment worker stopped")
    
    async def _process_deployment(self, deployment_plan: DeploymentPlan):
        """
        Process a single deployment plan.
        
        Args:
            deployment_plan: The deployment plan to process
        """
        deployment_id = deployment_plan.plan_id
        deployment = self.active_deployments.get(deployment_id)
        
        if not deployment:
            logger.error(f"Deployment result not found for {deployment_id}")
            return
        
        logger.info(f"Processing deployment {deployment_id} for environment {deployment_plan.environment_id}")
        
        try:
            # Update status to preparing
            deployment.status = DeploymentStatus.PREPARING
            
            # Execute deployment pipeline stages
            await self._execute_deployment_pipeline(deployment_plan, deployment)
            
            # Mark as completed if all stages succeeded
            if deployment.status not in [DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]:
                deployment.status = DeploymentStatus.COMPLETED
                deployment.end_time = datetime.now()
                logger.info(f"Deployment {deployment_id} completed successfully")
            
        except Exception as e:
            # Mark deployment as failed
            deployment.status = DeploymentStatus.FAILED
            deployment.end_time = datetime.now()
            deployment.error_message = str(e)
            logger.error(f"Deployment {deployment_id} failed: {e}", exc_info=True)
    
    async def _execute_deployment_pipeline(self, 
                                         deployment_plan: DeploymentPlan, 
                                         deployment: DeploymentResult):
        """
        Execute the deployment pipeline stages.
        
        Args:
            deployment_plan: The deployment plan
            deployment: The deployment result to update
        """
        pipeline_stages = [
            ("artifact_preparation", self._prepare_artifacts),
            ("environment_connection", self._connect_to_environment),
            ("dependency_installation", self._install_dependencies),
            ("script_deployment", self._deploy_scripts),
            ("instrumentation_setup", self._setup_instrumentation),
            ("readiness_validation", self._validate_readiness)
        ]
        
        for stage_name, stage_func in pipeline_stages:
            if deployment.status in [DeploymentStatus.FAILED, DeploymentStatus.CANCELLED]:
                break
            
            # Create deployment step
            step = DeploymentStep(
                step_id=f"{deployment.deployment_id}_{stage_name}",
                name=stage_name.replace("_", " ").title(),
                status=DeploymentStatus.PENDING,
                start_time=datetime.now()
            )
            deployment.steps.append(step)
            
            try:
                # Update deployment status
                deployment.status = getattr(DeploymentStatus, stage_name.upper(), DeploymentStatus.PREPARING)
                
                # Execute stage
                step.status = DeploymentStatus.PREPARING
                await stage_func(deployment_plan, deployment, step)
                
                # Mark step as completed
                step.status = DeploymentStatus.COMPLETED
                step.end_time = datetime.now()
                
                logger.info(f"Completed stage {stage_name} for deployment {deployment.deployment_id}")
                
            except Exception as e:
                # Mark step and deployment as failed
                step.status = DeploymentStatus.FAILED
                step.end_time = datetime.now()
                step.error_message = str(e)
                
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = f"Failed at stage {stage_name}: {e}"
                
                logger.error(f"Stage {stage_name} failed for deployment {deployment.deployment_id}: {e}")
                raise
    
    async def _prepare_artifacts(self, 
                               deployment_plan: DeploymentPlan, 
                               deployment: DeploymentResult, 
                               step: DeploymentStep):
        """Prepare artifacts for deployment"""
        logger.info(f"Preparing {len(deployment_plan.test_artifacts)} artifacts")
        
        # Validate artifacts
        for artifact in deployment_plan.test_artifacts:
            if not artifact.content:
                raise ValueError(f"Artifact {artifact.name} has no content")
            
            # Verify checksum
            import hashlib
            calculated_checksum = hashlib.sha256(artifact.content).hexdigest()
            if artifact.checksum != calculated_checksum:
                raise ValueError(f"Checksum mismatch for artifact {artifact.name}")
        
        step.details["artifacts_prepared"] = len(deployment_plan.test_artifacts)
        deployment.artifacts_deployed = len(deployment_plan.test_artifacts)
    
    async def _connect_to_environment(self, 
                                    deployment_plan: DeploymentPlan, 
                                    deployment: DeploymentResult, 
                                    step: DeploymentStep):
        """Establish connection to target environment"""
        logger.info(f"Connecting to environment {deployment_plan.environment_id}")
        
        # Get environment manager for the environment type
        env_manager = await self.environment_manager_factory.get_manager(deployment_plan.environment_id)
        
        # Test connection
        connection_result = await env_manager.test_connection()
        if not connection_result:
            raise RuntimeError(f"Failed to connect to environment {deployment_plan.environment_id}")
        
        step.details["connection_established"] = True
    
    async def _install_dependencies(self, 
                                  deployment_plan: DeploymentPlan, 
                                  deployment: DeploymentResult, 
                                  step: DeploymentStep):
        """Install required dependencies"""
        logger.info(f"Installing {len(deployment_plan.dependencies)} dependencies")
        
        # For now, simulate dependency installation
        await asyncio.sleep(0.1)  # Simulate installation time
        
        step.details["dependencies_installed"] = len(deployment_plan.dependencies)
        deployment.dependencies_installed = len(deployment_plan.dependencies)
    
    async def _deploy_scripts(self, 
                            deployment_plan: DeploymentPlan, 
                            deployment: DeploymentResult, 
                            step: DeploymentStep):
        """Deploy test scripts to environment"""
        logger.info(f"Deploying {len(deployment_plan.test_artifacts)} scripts")
        
        # For now, simulate script deployment
        await asyncio.sleep(0.1)  # Simulate deployment time
        
        step.details["scripts_deployed"] = len(deployment_plan.test_artifacts)
    
    async def _setup_instrumentation(self, 
                                   deployment_plan: DeploymentPlan, 
                                   deployment: DeploymentResult, 
                                   step: DeploymentStep):
        """Setup instrumentation and monitoring tools"""
        config = deployment_plan.instrumentation_config
        logger.info(f"Setting up instrumentation: KASAN={config.enable_kasan}, Coverage={config.enable_coverage}")
        
        # For now, simulate instrumentation setup
        await asyncio.sleep(0.1)  # Simulate setup time
        
        step.details["instrumentation_configured"] = True
    
    async def _validate_readiness(self, 
                                deployment_plan: DeploymentPlan, 
                                deployment: DeploymentResult, 
                                step: DeploymentStep):
        """Validate environment readiness"""
        logger.info(f"Validating readiness for environment {deployment_plan.environment_id}")
        
        # For now, simulate readiness validation
        await asyncio.sleep(0.1)  # Simulate validation time
        
        step.details["validation_passed"] = True
    
    def get_active_deployments(self) -> Dict[str, DeploymentResult]:
        """Get all active deployments"""
        return self.active_deployments.copy()
    
    def get_deployment_statistics(self) -> Dict[str, int]:
        """Get deployment statistics"""
        stats = {
            "total_deployments": len(self.active_deployments),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for deployment in self.active_deployments.values():
            if deployment.status == DeploymentStatus.PENDING:
                stats["pending"] += 1
            elif deployment.status in [DeploymentStatus.PREPARING, DeploymentStatus.CONNECTING, 
                                     DeploymentStatus.INSTALLING_DEPS, DeploymentStatus.DEPLOYING_SCRIPTS,
                                     DeploymentStatus.CONFIGURING_INSTRUMENTATION, DeploymentStatus.VALIDATING]:
                stats["running"] += 1
            elif deployment.status == DeploymentStatus.COMPLETED:
                stats["completed"] += 1
            elif deployment.status == DeploymentStatus.FAILED:
                stats["failed"] += 1
            elif deployment.status == DeploymentStatus.CANCELLED:
                stats["cancelled"] += 1
        
        return stats