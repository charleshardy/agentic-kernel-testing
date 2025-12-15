"""Main orchestrator service for test execution management."""

import asyncio
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path

from .config import OrchestratorConfig
from .status_tracker import StatusTracker
from .queue_monitor import QueueMonitor
from .resource_manager import ResourceManager


class OrchestratorService:
    """Main orchestrator service that coordinates test execution."""
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """Initialize the orchestrator service."""
        self.config = config or OrchestratorConfig.from_env()
        self.logger = self._setup_logging()
        
        # Core components
        self.status_tracker = StatusTracker()
        self.queue_monitor = QueueMonitor(self.config)
        self.resource_manager = ResourceManager(self.config)
        
        # Service state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self._main_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Statistics
        self.stats = {
            'tests_processed': 0,
            'tests_completed': 0,
            'tests_failed': 0,
            'uptime_seconds': 0.0
        }
        
        self.logger.info("Orchestrator service initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the orchestrator service."""
        logger = logging.getLogger('orchestrator')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def start(self) -> bool:
        """Start the orchestrator service."""
        if self.is_running:
            self.logger.warning("Orchestrator service is already running")
            return False
        
        try:
            self.logger.info("Starting orchestrator service...")
            
            # Initialize components
            self.status_tracker.start()
            self.resource_manager.start()
            
            # Load persisted state if enabled
            if self.config.enable_persistence:
                self._load_state()
            
            # Start main processing thread
            self.is_running = True
            self.start_time = datetime.utcnow()
            self._shutdown_event.clear()
            
            self._main_thread = threading.Thread(
                target=self._main_loop,
                name="orchestrator-main",
                daemon=True
            )
            self._main_thread.start()
            
            self.logger.info("Orchestrator service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start orchestrator service: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """Stop the orchestrator service gracefully."""
        if not self.is_running:
            self.logger.warning("Orchestrator service is not running")
            return False
        
        try:
            self.logger.info("Stopping orchestrator service...")
            
            # Signal shutdown
            self.is_running = False
            self._shutdown_event.set()
            
            # Wait for main thread to finish
            if self._main_thread and self._main_thread.is_alive():
                self._main_thread.join(timeout=10.0)
                if self._main_thread.is_alive():
                    self.logger.warning("Main thread did not stop gracefully")
            
            # Stop components
            self.resource_manager.stop()
            self.status_tracker.stop()
            
            # Save state if enabled
            if self.config.enable_persistence:
                self._save_state()
            
            self.logger.info("Orchestrator service stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping orchestrator service: {e}")
            return False
    
    def _main_loop(self):
        """Main processing loop for the orchestrator."""
        self.logger.info("Orchestrator main loop started")
        
        while self.is_running and not self._shutdown_event.is_set():
            try:
                # Update uptime statistics
                if self.start_time:
                    self.stats['uptime_seconds'] = (datetime.utcnow() - self.start_time).total_seconds()
                
                # Process execution plans
                self._process_execution_plans()
                
                # Update system metrics
                self._update_metrics()
                
                # Sleep until next poll
                if not self._shutdown_event.wait(self.config.poll_interval):
                    continue  # Normal poll interval
                else:
                    break  # Shutdown requested
                    
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                # Continue running despite errors
                time.sleep(1.0)
        
        self.logger.info("Orchestrator main loop stopped")
    
    def _process_execution_plans(self):
        """Process queued execution plans."""
        try:
            # Get next execution plan to process
            execution_plan = self.queue_monitor.get_next_execution_plan()
            
            if execution_plan:
                self.logger.info(f"Processing execution plan: {execution_plan['plan_id']}")
                self._execute_plan(execution_plan)
                self.stats['tests_processed'] += len(execution_plan.get('test_case_ids', []))
            
        except Exception as e:
            self.logger.error(f"Error processing execution plans: {e}")
    
    def _execute_plan(self, execution_plan: Dict[str, Any]):
        """Execute a specific execution plan."""
        plan_id = execution_plan['plan_id']
        test_case_ids = execution_plan.get('test_case_ids', [])
        
        try:
            # Update plan status to running
            self.status_tracker.update_plan_status(plan_id, 'running')
            
            # For now, simulate test execution
            # TODO: Replace with actual test execution logic
            for test_id in test_case_ids:
                self._simulate_test_execution(test_id, plan_id)
            
            # Update plan status to completed
            self.status_tracker.update_plan_status(plan_id, 'completed')
            self.logger.info(f"Completed execution plan: {plan_id}")
            
        except Exception as e:
            self.logger.error(f"Error executing plan {plan_id}: {e}")
            self.status_tracker.update_plan_status(plan_id, 'failed')
    
    def _simulate_test_execution(self, test_id: str, plan_id: str):
        """Simulate test execution (temporary implementation)."""
        try:
            # Update test status to running
            self.status_tracker.update_test_status(test_id, 'running')
            self.status_tracker.increment_active_tests()
            
            self.logger.info(f"Simulating execution of test: {test_id}")
            
            # Simulate test execution time (2-5 seconds)
            import random
            execution_time = random.uniform(2.0, 5.0)
            time.sleep(execution_time)
            
            # Simulate success/failure (90% success rate)
            success = random.random() > 0.1
            
            if success:
                self.status_tracker.update_test_status(test_id, 'completed')
                self.stats['tests_completed'] += 1
                self.logger.info(f"Test {test_id} completed successfully")
            else:
                self.status_tracker.update_test_status(test_id, 'failed')
                self.stats['tests_failed'] += 1
                self.logger.info(f"Test {test_id} failed")
            
            # Decrement active test count
            self.status_tracker.decrement_active_tests()
            
        except Exception as e:
            self.logger.error(f"Error simulating test {test_id}: {e}")
            self.status_tracker.update_test_status(test_id, 'error')
            self.status_tracker.decrement_active_tests()
    
    def _update_metrics(self):
        """Update system metrics."""
        try:
            # Update resource manager metrics
            self.resource_manager.update_metrics()
            
            # Update status tracker metrics
            self.status_tracker.update_metrics()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def _load_state(self):
        """Load persisted orchestrator state."""
        try:
            state_file = Path(self.config.state_file)
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Restore statistics
                self.stats.update(state.get('stats', {}))
                
                self.logger.info("Orchestrator state loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading orchestrator state: {e}")
    
    def _save_state(self):
        """Save orchestrator state to disk."""
        try:
            state = {
                'stats': self.stats,
                'timestamp': datetime.utcnow().isoformat(),
                'config': self.config.to_dict()
            }
            
            with open(self.config.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            self.logger.info("Orchestrator state saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving orchestrator state: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the orchestrator."""
        return {
            'status': 'healthy' if self.is_running else 'stopped',
            'uptime_seconds': self.stats['uptime_seconds'],
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'config': self.config.to_dict(),
            'stats': self.stats.copy(),
            'components': {
                'status_tracker': self.status_tracker.get_health_status(),
                'resource_manager': self.resource_manager.get_health_status(),
                'queue_monitor': self.queue_monitor.get_health_status()
            }
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return {
            'active_tests': self.status_tracker.get_active_test_count(),
            'queued_tests': self.queue_monitor.get_queued_test_count(),
            'completed_tests': self.stats['tests_completed'],
            'failed_tests': self.stats['tests_failed'],
            'total_processed': self.stats['tests_processed'],
            'available_environments': self.resource_manager.get_available_environment_count(),
            'uptime_seconds': self.stats['uptime_seconds']
        }