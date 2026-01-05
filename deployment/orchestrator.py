"""
Deployment Orchestrator

Main orchestrator class responsible for coordinating deployment activities
across multiple environments with error recovery and retry logic.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from concurrent.futures import ThreadPoolExecutor
import heapq
import json
from pathlib import Path

from .models import (
    DeploymentPlan,
    DeploymentResult,
    DeploymentStatus,
    DeploymentStep,
    TestArtifact,
    ValidationResult,
    Priority
)
from .environment_manager import EnvironmentManagerFactory
from .artifact_repository import ArtifactRepository
from .instrumentation_manager import InstrumentationManager
from .security import (
    EncryptionManager,
    CredentialManager,
    AccessControlManager,
    SecureArtifactHandler,
    SecurityLevel
)
from .log_sanitizer import (
    LogSanitizer,
    TemporaryFileManager,
    SecureLogStorage,
    DeploymentCleanupManager
)
from .validation_manager import ValidationManager


logger = logging.getLogger(__name__)


class DeploymentQueue:
    """Priority queue for deployment scheduling with resource management"""
    
    def __init__(self):
        self._queue = []
        self._entry_finder = {}
        self._counter = 0
        self.REMOVED = '<removed-task>'
    
    def add_deployment(self, deployment_plan: DeploymentPlan, priority: int = None):
        """Add deployment to queue with priority"""
        if priority is None:
            priority = deployment_plan.deployment_config.priority.value
        
        if deployment_plan.plan_id in self._entry_finder:
            self.remove_deployment(deployment_plan.plan_id)
        
        count = self._counter
        self._counter += 1
        entry = [priority, count, deployment_plan]
        self._entry_finder[deployment_plan.plan_id] = entry
        heapq.heappush(self._queue, entry)
    
    def remove_deployment(self, plan_id: str):
        """Remove deployment from queue"""
        entry = self._entry_finder.pop(plan_id, None)
        if entry:
            entry[-1] = self.REMOVED
    
    def pop_deployment(self) -> Optional[DeploymentPlan]:
        """Pop highest priority deployment"""
        while self._queue:
            priority, count, deployment_plan = heapq.heappop(self._queue)
            if deployment_plan is not self.REMOVED:
                del self._entry_finder[deployment_plan.plan_id]
                return deployment_plan
        return None
    
    def size(self) -> int:
        """Get queue size"""
        return len(self._entry_finder)
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._entry_finder) == 0


class ResourceManager:
    """Manages environment resources and allocation"""
    
    def __init__(self):
        self.environment_locks: Dict[str, asyncio.Lock] = {}
        self.environment_usage: Dict[str, int] = {}
        self.max_concurrent_per_env = 3  # Max concurrent deployments per environment
    
    async def acquire_environment(self, environment_id: str) -> bool:
        """Acquire lock for environment"""
        if environment_id not in self.environment_locks:
            self.environment_locks[environment_id] = asyncio.Lock()
        
        # Check if environment is at capacity
        current_usage = self.environment_usage.get(environment_id, 0)
        if current_usage >= self.max_concurrent_per_env:
            return False
        
        # Increment usage counter
        self.environment_usage[environment_id] = current_usage + 1
        return True
    
    async def release_environment(self, environment_id: str):
        """Release environment lock"""
        current_usage = self.environment_usage.get(environment_id, 0)
        if current_usage > 0:
            self.environment_usage[environment_id] = current_usage - 1
    
    def get_environment_usage(self) -> Dict[str, int]:
        """Get current environment usage"""
        return self.environment_usage.copy()


class DeploymentLogger:
    """Handles deployment logging and metrics collection with sanitization"""
    
    def __init__(self, log_dir: str = "./deployment_logs", log_sanitizer=None, secure_log_storage=None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log sanitization components
        self.log_sanitizer = log_sanitizer
        self.secure_log_storage = secure_log_storage
        
        # Metrics storage
        self.metrics = {
            "total_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "cancelled_deployments": 0,
            "average_duration_seconds": 0.0,
            "retry_count": 0
        }
        
        # Load existing metrics
        self._load_metrics()
    
    def log_deployment_start(self, deployment_id: str, plan: DeploymentPlan):
        """Log deployment start with sanitization"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "deployment_start",
            "deployment_id": deployment_id,
            "environment_id": plan.environment_id,
            "artifact_count": len(plan.test_artifacts),
            "priority": plan.deployment_config.priority.value
        }
        self._write_log(deployment_id, log_entry)
        self.metrics["total_deployments"] += 1
    
    def log_deployment_end(self, deployment_id: str, result: DeploymentResult):
        """Log deployment completion with sanitization"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "deployment_end",
            "deployment_id": deployment_id,
            "status": result.status.value,
            "duration_seconds": result.duration_seconds,
            "artifacts_deployed": result.artifacts_deployed,
            "error_message": result.error_message
        }
        self._write_log(deployment_id, log_entry)
        
        # Update metrics
        if result.is_successful:
            self.metrics["successful_deployments"] += 1
        elif result.is_failed:
            self.metrics["failed_deployments"] += 1
        elif result.is_cancelled:
            self.metrics["cancelled_deployments"] += 1
        
        # Update average duration
        if result.duration_seconds:
            total_successful = self.metrics["successful_deployments"]
            if total_successful > 1:
                current_avg = self.metrics["average_duration_seconds"]
                new_avg = ((current_avg * (total_successful - 1)) + result.duration_seconds) / total_successful
                self.metrics["average_duration_seconds"] = new_avg
            else:
                self.metrics["average_duration_seconds"] = result.duration_seconds
    
    def log_retry_attempt(self, deployment_id: str, attempt: int, error: str):
        """Log retry attempt with sanitization"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "retry_attempt",
            "deployment_id": deployment_id,
            "attempt": attempt,
            "error": error
        }
        self._write_log(deployment_id, log_entry)
        self.metrics["retry_count"] += 1
    
    def _write_log(self, deployment_id: str, log_entry: dict):
        """Write log entry to file with sanitization"""
        if self.secure_log_storage:
            # Use secure log storage with sanitization
            self.secure_log_storage.store_log_entry(deployment_id, log_entry, sanitize=True)
        else:
            # Fallback to regular file logging with sanitization if available
            if self.log_sanitizer:
                # Sanitize the log entry before writing
                sanitized_entry = self.log_sanitizer.sanitize_json_log(log_entry)
            else:
                sanitized_entry = log_entry
            
            log_file = self.log_dir / f"{deployment_id}.log"
            with open(log_file, "a") as f:
                f.write(json.dumps(sanitized_entry) + "\n")
    
    def get_deployment_logs(self, deployment_id: str) -> List[dict]:
        """Get logs for a specific deployment (sanitized by default)"""
        if self.secure_log_storage:
            # Use secure log storage to get sanitized logs
            return self.secure_log_storage.get_log_entries(deployment_id, sanitized_only=True)
        else:
            # Fallback to file-based logs
            log_file = self.log_dir / f"{deployment_id}.log"
            if not log_file.exists():
                return []
            
            logs = []
            with open(log_file, "r") as f:
                for line in f:
                    try:
                        logs.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            return logs
    
    def get_metrics(self) -> dict:
        """Get current metrics"""
        self._save_metrics()
        return self.metrics.copy()
    
    def _load_metrics(self):
        """Load metrics from file"""
        metrics_file = self.log_dir / "metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, "r") as f:
                    saved_metrics = json.load(f)
                    self.metrics.update(saved_metrics)
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save_metrics(self):
        """Save metrics to file"""
        metrics_file = self.log_dir / "metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)


class DeploymentOrchestrator:
    """
    Main orchestrator for test deployment operations.
    
    Coordinates deployment activities across multiple environments,
    manages deployment pipeline execution and state, handles error
    recovery and retry logic, and provides real-time status updates.
    """
    
    def __init__(self, 
                 max_concurrent_deployments: int = 5,
                 default_timeout: int = 300,
                 log_dir: str = "./deployment_logs",
                 enable_security: bool = True):
        """
        Initialize the deployment orchestrator.
        
        Args:
            max_concurrent_deployments: Maximum number of concurrent deployments
            default_timeout: Default timeout for deployment operations in seconds
            log_dir: Directory for deployment logs
            enable_security: Enable security features (encryption, access control)
        """
        self.max_concurrent_deployments = max_concurrent_deployments
        self.default_timeout = default_timeout
        self.enable_security = enable_security
        
        # Core components
        self.environment_manager_factory = EnvironmentManagerFactory()
        self.artifact_repository = ArtifactRepository()
        self.instrumentation_manager = InstrumentationManager()
        
        # Security components
        if enable_security:
            self.encryption_manager = EncryptionManager()
            self.credential_manager = CredentialManager(self.encryption_manager)
            self.access_control_manager = AccessControlManager()
            self.secure_artifact_handler = SecureArtifactHandler(
                self.encryption_manager,
                self.credential_manager,
                self.access_control_manager
            )
        else:
            self.encryption_manager = None
            self.credential_manager = None
            self.access_control_manager = None
            self.secure_artifact_handler = None
        
        # Enhanced resource management
        self.deployment_queue = DeploymentQueue()
        self.resource_manager = ResourceManager()
        
        # Log sanitization and cleanup components
        self.log_sanitizer = LogSanitizer()
        self.temp_file_manager = TemporaryFileManager()
        self.secure_log_storage = SecureLogStorage(log_dir, self.log_sanitizer)
        self.cleanup_manager = DeploymentCleanupManager(
            self.log_sanitizer,
            self.temp_file_manager,
            self.secure_log_storage
        )
        
        # Validation management
        self.validation_manager = ValidationManager()
        
        # Initialize deployment logger with sanitization components
        self.deployment_logger = DeploymentLogger(
            log_dir, 
            self.log_sanitizer, 
            self.secure_log_storage
        )
        
        # State tracking
        self.active_deployments: Dict[str, DeploymentResult] = {}
        self.deployment_semaphore = asyncio.Semaphore(max_concurrent_deployments)
        
        # Background tasks
        self._deployment_worker_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        logger.info(f"DeploymentOrchestrator initialized with max_concurrent_deployments={max_concurrent_deployments}, security_enabled={enable_security}")
    
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
                                  artifacts: List[TestArtifact],
                                  priority: Priority = Priority.NORMAL) -> str:
        """
        Deploy test artifacts to a specific environment with priority scheduling.
        
        Args:
            plan_id: Test plan identifier
            env_id: Environment identifier
            artifacts: List of test artifacts to deploy
            priority: Deployment priority
            
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
        
        deployment_config = DeploymentConfig(priority=priority)
        
        deployment_plan = DeploymentPlan(
            plan_id=deployment_id,
            environment_id=env_id,
            test_artifacts=artifacts,
            dependencies=[],  # Will be populated based on artifacts
            instrumentation_config=InstrumentationConfig(),
            deployment_config=deployment_config,
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
        
        # Add to priority queue
        self.deployment_queue.add_deployment(deployment_plan)
        
        # Log deployment start
        self.deployment_logger.log_deployment_start(deployment_id, deployment_plan)
        
        logger.info(f"Queued deployment {deployment_id} for environment {env_id} with priority {priority.name}")
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
        Retry a failed deployment with exponential backoff.
        
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
        
        # Check retry limits
        if deployment.retry_count >= 3:  # Max 3 retries
            logger.warning(f"Deployment {deployment_id} has exceeded retry limit")
            return None
        
        # Calculate retry delay with exponential backoff
        retry_delay = 5 * (2 ** deployment.retry_count)  # 5s, 10s, 20s
        
        logger.info(f"Retrying failed deployment {deployment_id} after {retry_delay}s delay (attempt {deployment.retry_count + 1})")
        
        # Log retry attempt
        self.deployment_logger.log_retry_attempt(deployment_id, deployment.retry_count + 1, deployment.error_message or "Unknown error")
        
        # Schedule retry after delay
        await asyncio.sleep(retry_delay)
        
        # Reset deployment status for retry
        deployment.status = DeploymentStatus.PENDING
        deployment.error_message = None
        deployment.retry_count += 1
        deployment.start_time = datetime.now()
        deployment.end_time = None
        
        # Re-queue the deployment (get original plan from logs)
        original_plan = await self._reconstruct_deployment_plan(deployment_id)
        if original_plan:
            self.deployment_queue.add_deployment(original_plan)
            return deployment_id
        
        return None
    
    async def _reconstruct_deployment_plan(self, deployment_id: str) -> Optional[DeploymentPlan]:
        """Reconstruct deployment plan from logs for retry"""
        try:
            logs = self.deployment_logger.get_deployment_logs(deployment_id)
            start_log = next((log for log in logs if log["event"] == "deployment_start"), None)
            
            if not start_log:
                return None
            
            # Create a basic deployment plan for retry
            # In a real implementation, you'd store the full plan
            from .models import DeploymentPlan, DeploymentConfig, InstrumentationConfig
            
            deployment = self.active_deployments[deployment_id]
            
            return DeploymentPlan(
                plan_id=deployment_id,
                environment_id=deployment.environment_id,
                test_artifacts=[],  # Would need to be reconstructed from storage
                dependencies=[],
                instrumentation_config=InstrumentationConfig(),
                deployment_config=DeploymentConfig(),
                created_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to reconstruct deployment plan for {deployment_id}: {e}")
            return None
    
    async def rollback_deployment(self, deployment_id: str) -> bool:
        """
        Rollback a deployment by removing deployed artifacts.
        
        Args:
            deployment_id: Deployment identifier to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            logger.warning(f"Deployment {deployment_id} not found for rollback")
            return False
        
        logger.info(f"Rolling back deployment {deployment_id}")
        
        try:
            # Get environment manager
            env_manager = await self.environment_manager_factory.get_manager(deployment.environment_id)
            
            # Connect to environment
            env_config = self.environment_manager_factory._environment_configs.get(deployment.environment_id)
            if not env_config:
                logger.error(f"Environment config not found for {deployment.environment_id}")
                return False
            
            connection = await env_manager.connect(env_config)
            
            # Remove deployed artifacts (simulated)
            await self._cleanup_deployed_artifacts(connection, deployment)
            
            # Close connection
            await connection.close()
            
            # Update deployment status
            deployment.status = DeploymentStatus.CANCELLED
            deployment.end_time = datetime.now()
            deployment.error_message = "Deployment rolled back"
            
            logger.info(f"Successfully rolled back deployment {deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback deployment {deployment_id}: {e}")
            return False
    
    async def _cleanup_deployed_artifacts(self, connection, deployment: DeploymentResult):
        """Clean up deployed artifacts during rollback"""
        # Simulate artifact cleanup
        await asyncio.sleep(0.1)
        logger.debug(f"Cleaned up {deployment.artifacts_deployed} artifacts")
    
    def get_deployment_logs(self, deployment_id: str) -> List[dict]:
        """Get logs for a specific deployment"""
        return self.deployment_logger.get_deployment_logs(deployment_id)
    
    def get_deployment_metrics(self) -> dict:
        """Get deployment metrics and statistics"""
        base_metrics = self.deployment_logger.get_metrics()
        
        # Add real-time statistics
        base_metrics.update({
            "active_deployments": len(self.active_deployments),
            "queue_size": self.deployment_queue.size(),
            "environment_usage": self.resource_manager.get_environment_usage()
        })
        
        return base_metrics
    
    async def _deployment_worker(self):
        """Background worker that processes deployment queue with resource management"""
        logger.info("Deployment worker started")
        
        while self._is_running:
            try:
                # Get next deployment from priority queue
                deployment_plan = self.deployment_queue.pop_deployment()
                
                if deployment_plan is None:
                    # No deployments in queue, wait briefly
                    await asyncio.sleep(0.1)
                    continue
                
                # Check if we can acquire environment resource
                if not await self.resource_manager.acquire_environment(deployment_plan.environment_id):
                    # Environment at capacity, re-queue with lower priority
                    self.deployment_queue.add_deployment(deployment_plan, deployment_plan.deployment_config.priority.value + 1)
                    await asyncio.sleep(0.5)  # Wait before retrying
                    continue
                
                # Process deployment with semaphore to limit total concurrency
                async with self.deployment_semaphore:
                    try:
                        await self._process_deployment(deployment_plan)
                    finally:
                        # Always release environment resource
                        await self.resource_manager.release_environment(deployment_plan.environment_id)
                
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
                
                # Clean up deployment resources
                try:
                    await self.cleanup_manager.cleanup_deployment_resources(deployment_id)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup resources for deployment {deployment_id}: {cleanup_error}")
            
            # Log deployment completion
            self.deployment_logger.log_deployment_end(deployment_id, deployment)
            
        except Exception as e:
            # Mark deployment as failed
            deployment.status = DeploymentStatus.FAILED
            deployment.end_time = datetime.now()
            deployment.error_message = str(e)
            logger.error(f"Deployment {deployment_id} failed: {e}", exc_info=True)
            
            # Clean up deployment resources even on failure
            try:
                await self.cleanup_manager.cleanup_deployment_resources(deployment_id)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup resources for failed deployment {deployment_id}: {cleanup_error}")
            
            # Log deployment failure
            self.deployment_logger.log_deployment_end(deployment_id, deployment)
            
            # Attempt automatic retry if within limits
            if deployment.retry_count < 3:  # Max 3 retries
                logger.info(f"Scheduling automatic retry for deployment {deployment_id}")
                asyncio.create_task(self._schedule_retry(deployment_id))
    
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
        """Validate environment readiness with comprehensive checks"""
        logger.info(f"Validating readiness for environment {deployment_plan.environment_id}")
        
        try:
            # Perform comprehensive validation
            validation_result = await self.validation_manager.validate_environment_readiness(
                deployment_plan.environment_id,
                deployment_config=deployment_plan.deployment_config.__dict__ if deployment_plan.deployment_config else None
            )
            
            # Store validation result in step details
            step.details["validation_result"] = validation_result
            step.details["validation_passed"] = validation_result.is_ready
            step.details["validation_success_rate"] = validation_result.success_rate
            step.details["failed_checks"] = validation_result.failed_checks
            step.details["warnings"] = validation_result.warnings
            
            # If validation failed, attempt recovery
            if not validation_result.is_ready:
                logger.warning(f"Environment {deployment_plan.environment_id} failed readiness validation. "
                             f"Failed checks: {validation_result.failed_checks}")
                
                # Attempt failure recovery
                recovery_result = await self.validation_manager.attempt_failure_recovery(
                    deployment_plan.environment_id, validation_result
                )
                
                step.details["recovery_attempted"] = True
                step.details["recovery_results"] = recovery_result.details.get("recovery_attempts", {})
                
                # Check if recovery was successful
                if recovery_result.is_ready:
                    logger.info(f"Recovery successful for environment {deployment_plan.environment_id}")
                    step.details["validation_passed"] = True
                    step.details["recovery_successful"] = True
                else:
                    logger.error(f"Recovery failed for environment {deployment_plan.environment_id}")
                    step.details["recovery_successful"] = False
                    
                    # Prevent test execution by raising an exception
                    failure_details = self._format_validation_failure_message(validation_result)
                    raise RuntimeError(f"Environment readiness validation failed: {failure_details}")
            else:
                logger.info(f"Environment {deployment_plan.environment_id} passed readiness validation "
                           f"(success rate: {validation_result.success_rate:.1f}%)")
                
                # Log any warnings
                if validation_result.warnings:
                    for warning in validation_result.warnings:
                        logger.warning(f"Validation warning: {warning}")
        
        except Exception as e:
            step.details["validation_passed"] = False
            step.details["validation_error"] = str(e)
            logger.error(f"Validation failed for environment {deployment_plan.environment_id}: {e}")
            raise
    
    def _format_validation_failure_message(self, validation_result: ValidationResult) -> str:
        """Format a comprehensive validation failure message"""
        message_parts = []
        
        # Add basic failure info
        message_parts.append(f"Environment {validation_result.environment_id} failed readiness validation")
        message_parts.append(f"Success rate: {validation_result.success_rate:.1f}%")
        
        # Add failed checks
        if validation_result.failed_checks:
            message_parts.append(f"Failed checks: {', '.join(validation_result.failed_checks)}")
        
        # Add specific failure details with remediation suggestions
        for failed_check in validation_result.failed_checks:
            failure_key = f"{failed_check}_failure"
            if failure_key in validation_result.details:
                failure = validation_result.details[failure_key]
                message_parts.append(f"  - {failed_check}: {failure.error_message}")
                
                if failure.remediation_suggestions:
                    suggestions = "; ".join(failure.remediation_suggestions[:3])  # Limit to 3 suggestions
                    message_parts.append(f"    Suggestions: {suggestions}")
        
        return ". ".join(message_parts)
    
    async def _schedule_retry(self, deployment_id: str):
        """Schedule automatic retry for failed deployment"""
        try:
            await asyncio.sleep(2)  # Brief delay before retry
            await self.retry_failed_deployment(deployment_id)
        except Exception as e:
            logger.error(f"Failed to schedule retry for deployment {deployment_id}: {e}")
    
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
    
    # Security-related methods
    
    def store_environment_credential(self, 
                                   environment_id: str,
                                   credential_type: str,
                                   credential_data: Dict[str, Any],
                                   expires_in_hours: Optional[int] = None) -> Optional[str]:
        """
        Store secure credentials for environment access.
        
        Args:
            environment_id: Environment identifier
            credential_type: Type of credential (password, ssh_key, etc.)
            credential_data: Credential data to encrypt and store
            expires_in_hours: Hours until credential expires
            
        Returns:
            Credential ID for retrieval or None if security disabled
        """
        if not self.enable_security or not self.credential_manager:
            logger.warning("Security is disabled, cannot store credentials")
            return None
        
        return self.credential_manager.store_credential(
            environment_id, credential_type, credential_data, expires_in_hours
        )
    
    def retrieve_environment_credential(self, credential_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt environment credentials.
        
        Args:
            credential_id: Credential identifier
            
        Returns:
            Decrypted credential data or None if not found/security disabled
        """
        if not self.enable_security or not self.credential_manager:
            logger.warning("Security is disabled, cannot retrieve credentials")
            return None
        
        return self.credential_manager.retrieve_credential(credential_id)
    
    def secure_artifact(self, 
                       artifact: TestArtifact, 
                       user_id: str,
                       security_level: str = SecurityLevel.INTERNAL) -> TestArtifact:
        """
        Apply security measures to an artifact.
        
        Args:
            artifact: Test artifact to secure
            user_id: User requesting the operation
            security_level: Security level to apply
            
        Returns:
            Secured test artifact
        """
        if not self.enable_security or not self.secure_artifact_handler:
            logger.warning("Security is disabled, returning artifact unchanged")
            return artifact
        
        return self.secure_artifact_handler.secure_artifact(
            artifact, security_level, user_id
        )
    
    def decrypt_artifact(self, artifact: TestArtifact, user_id: str) -> Optional[TestArtifact]:
        """
        Decrypt a secured artifact.
        
        Args:
            artifact: Encrypted test artifact
            user_id: User requesting decryption
            
        Returns:
            Decrypted artifact or None if access denied/security disabled
        """
        if not self.enable_security or not self.secure_artifact_handler:
            logger.warning("Security is disabled, returning artifact unchanged")
            return artifact
        
        return self.secure_artifact_handler.decrypt_artifact(artifact, user_id)
    
    def check_deployment_permission(self, 
                                  artifact: TestArtifact, 
                                  user_id: str, 
                                  environment_id: str) -> bool:
        """
        Check if user has permission to deploy artifact to environment.
        
        Args:
            artifact: Test artifact to deploy
            user_id: User requesting deployment
            environment_id: Target environment
            
        Returns:
            True if deployment is allowed, False otherwise
        """
        if not self.enable_security or not self.secure_artifact_handler:
            logger.warning("Security is disabled, allowing deployment")
            return True
        
        return self.secure_artifact_handler.enforce_deployment_permissions(
            artifact, user_id, environment_id
        )
    
    def add_access_control_rule(self, 
                               resource_id: str,
                               user_id: str,
                               permissions: List[str],
                               environment_restrictions: Optional[List[str]] = None,
                               expires_in_hours: Optional[int] = None):
        """
        Add access control rule for a resource.
        
        Args:
            resource_id: Resource identifier
            user_id: User identifier
            permissions: List of permissions to grant
            environment_restrictions: Optional environment restrictions
            expires_in_hours: Hours until rule expires
        """
        if not self.enable_security or not self.access_control_manager:
            logger.warning("Security is disabled, cannot add access control rule")
            return
        
        from .security import AccessControlRule
        from datetime import datetime, timedelta
        
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        rule = AccessControlRule(
            resource_id=resource_id,
            user_id=user_id,
            permissions=permissions,
            environment_restrictions=environment_restrictions or [],
            expires_at=expires_at
        )
        
        self.access_control_manager.add_access_rule(rule)
    
    def cleanup_security_resources(self):
        """Clean up expired security resources"""
        if not self.enable_security:
            return
        
        if self.credential_manager:
            self.credential_manager.cleanup_expired_credentials()
        
        if self.access_control_manager:
            self.access_control_manager.cleanup_expired_rules()
        
        logger.info("Cleaned up expired security resources")
    
    def create_temporary_file(self, 
                            content: bytes, 
                            suffix: str = ".tmp",
                            contains_sensitive_data: bool = False,
                            cleanup_priority: str = "normal") -> str:
        """
        Create a temporary file with tracking for cleanup.
        
        Args:
            content: File content
            suffix: File suffix
            contains_sensitive_data: Whether file contains sensitive data
            cleanup_priority: Cleanup priority (immediate, high, normal, low)
            
        Returns:
            Path to created temporary file
        """
        return self.temp_file_manager.create_temporary_file(
            content, suffix, contains_sensitive_data, cleanup_priority
        )
    
    def mark_file_for_cleanup(self, file_path: str, priority: str = "normal"):
        """
        Mark an existing file for cleanup.
        
        Args:
            file_path: Path to file to track
            priority: Cleanup priority
        """
        self.temp_file_manager.mark_file_for_cleanup(file_path, priority)
    
    def get_cleanup_status(self) -> Dict[str, Any]:
        """Get comprehensive cleanup status including sanitization stats"""
        return self.cleanup_manager.get_cleanup_status()
    
    async def emergency_cleanup(self):
        """Perform emergency cleanup of all sensitive resources"""
        await self.cleanup_manager.emergency_cleanup()
        logger.warning("Emergency cleanup completed for all sensitive resources")
    
    def get_validation_history(self, environment_id: str) -> List:
        """Get validation history for an environment"""
        return self.validation_manager.get_validation_history(environment_id)
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics across all environments"""
        return self.validation_manager.get_validation_statistics()
    
    def add_custom_validation_check(self, check):
        """Add a custom validation check"""
        self.validation_manager.add_custom_validation_check(check)
    
    async def validate_environment_readiness(self, environment_id: str, deployment_config: Dict[str, Any] = None):
        """Manually validate environment readiness"""
        return await self.validation_manager.validate_environment_readiness(environment_id, deployment_config)