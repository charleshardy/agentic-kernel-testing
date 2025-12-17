"""Queue monitoring component for detecting and managing execution plans."""

import logging
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
import heapq

from .config import OrchestratorConfig


class QueueMonitor:
    """Monitors execution plans and manages the execution queue."""
    
    def __init__(self, config: OrchestratorConfig):
        """Initialize the queue monitor."""
        self.config = config
        self.logger = logging.getLogger('orchestrator.queue_monitor')
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Queue management
        self._priority_queue: List[tuple] = []  # (priority, timestamp, plan_id, plan_data)
        self._processed_plans: set = set()  # Track processed plan IDs
        self._last_poll_time: Optional[datetime] = None
        
        # Metrics
        self._metrics = {
            'plans_detected': 0,
            'plans_queued': 0,
            'plans_processed': 0,
            'last_poll': None
        }
        
        self.logger.info("Queue monitor initialized")
    
    def poll_for_new_plans(self) -> List[Dict[str, Any]]:
        """Poll for new execution plans from the global execution_plans dictionary."""
        new_plans = []
        
        try:
            with self._lock:
                # Import here to avoid circular imports
                from api.routers.tests import execution_plans
                
                current_time = datetime.utcnow()
                self._last_poll_time = current_time
                self._metrics['last_poll'] = current_time
                
                # Check for new plans
                for plan_id, plan_data in execution_plans.items():
                    if plan_id not in self._processed_plans:
                        # This is a new plan
                        self._processed_plans.add(plan_id)
                        new_plans.append({
                            'plan_id': plan_id,
                            **plan_data
                        })
                        
                        # Add to priority queue
                        priority = plan_data.get('priority', 5)  # Default priority 5
                        
                        # Use the plan's creation time if available, otherwise use current time
                        # This ensures FIFO ordering for plans with equal priority
                        if 'created_at' in plan_data and plan_data['created_at']:
                            timestamp = plan_data['created_at'].timestamp()
                        elif 'submitted_at' in plan_data and plan_data['submitted_at']:
                            timestamp = plan_data['submitted_at'].timestamp()
                        else:
                            # Fallback: use current time with a small increment to maintain order
                            timestamp = current_time.timestamp() + len(self._processed_plans) * 0.001
                        
                        # Priority: 1=highest, 10=lowest, so use priority directly for min-heap
                        heapq.heappush(self._priority_queue, (priority, timestamp, plan_id, plan_data))
                        
                        self._metrics['plans_detected'] += 1
                        self._metrics['plans_queued'] += 1
                        
                        self.logger.info(f"Detected new execution plan: {plan_id} (priority: {priority})")
                
                return new_plans
                
        except ImportError:
            # execution_plans not available yet (during startup)
            self.logger.debug("execution_plans not available yet")
            return []
        except Exception as e:
            self.logger.error(f"Error polling for new plans: {e}")
            return []
    
    def get_next_execution_plan(self) -> Optional[Dict[str, Any]]:
        """Get the next execution plan to process based on priority."""
        try:
            with self._lock:
                # First, poll for any new plans
                self.poll_for_new_plans()
                
                # Get the highest priority plan from the queue (lowest number = highest priority)
                if self._priority_queue:
                    priority, timestamp, plan_id, plan_data = heapq.heappop(self._priority_queue)
                    
                    self._metrics['plans_processed'] += 1
                    
                    result = {
                        'plan_id': plan_id,
                        'priority': priority,
                        'queued_at': datetime.fromtimestamp(timestamp),
                        **plan_data
                    }
                    
                    self.logger.info(f"Retrieved execution plan: {plan_id} (priority: {priority})")
                    return result
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting next execution plan: {e}")
            return None
    
    def get_queued_test_count(self) -> int:
        """Get the number of tests currently queued for execution."""
        try:
            with self._lock:
                # Poll for new plans first
                self.poll_for_new_plans()
                
                # Count total tests in all queued plans
                total_tests = 0
                for _, _, plan_id, plan_data in self._priority_queue:
                    test_case_ids = plan_data.get('test_case_ids', [])
                    total_tests += len(test_case_ids)
                
                return total_tests
                
        except Exception as e:
            self.logger.error(f"Error getting queued test count: {e}")
            return 0
    
    def get_queued_plan_count(self) -> int:
        """Get the number of execution plans currently queued."""
        with self._lock:
            return len(self._priority_queue)
    
    def prioritize_queue(self) -> bool:
        """Re-prioritize the queue (called when priorities change)."""
        try:
            with self._lock:
                # The heap automatically maintains priority order
                # This method is here for future enhancements
                self.logger.debug("Queue prioritization completed")
                return True
                
        except Exception as e:
            self.logger.error(f"Error prioritizing queue: {e}")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get detailed status of the execution queue."""
        try:
            with self._lock:
                # Poll for updates
                self.poll_for_new_plans()
                
                # Analyze queue contents
                queue_info = []
                for priority, timestamp, plan_id, plan_data in self._priority_queue:
                    test_count = len(plan_data.get('test_case_ids', []))
                    
                    queue_info.append({
                        'plan_id': plan_id,
                        'priority': priority,
                        'test_count': test_count,
                        'queued_at': datetime.fromtimestamp(timestamp).isoformat(),
                        'submission_id': plan_data.get('submission_id', 'unknown')
                    })
                
                # Sort by priority for display (highest priority first = lowest number first)
                queue_info.sort(key=lambda x: x['priority'])
                
                return {
                    'total_plans': len(self._priority_queue),
                    'total_tests': self.get_queued_test_count(),
                    'queue_details': queue_info,
                    'metrics': self._metrics.copy(),
                    'last_poll': self._last_poll_time.isoformat() if self._last_poll_time else None
                }
                
        except Exception as e:
            self.logger.error(f"Error getting queue status: {e}")
            return {
                'total_plans': 0,
                'total_tests': 0,
                'queue_details': [],
                'error': str(e)
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the queue monitor."""
        try:
            with self._lock:
                return {
                    'status': 'healthy',
                    'queued_plans': len(self._priority_queue),
                    'processed_plans': len(self._processed_plans),
                    'last_poll': self._last_poll_time.isoformat() if self._last_poll_time else None,
                    'metrics': self._metrics.copy()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def reset_processed_plans(self):
        """Reset the processed plans set (useful for testing or recovery)."""
        with self._lock:
            old_count = len(self._processed_plans)
            self._processed_plans.clear()
            self.logger.info(f"Reset processed plans set (was tracking {old_count} plans)")
    
    def clear_queue(self):
        """Clear the entire execution queue (use with caution)."""
        with self._lock:
            old_count = len(self._priority_queue)
            self._priority_queue.clear()
            self.logger.warning(f"Cleared execution queue (removed {old_count} plans)")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics about queue operations."""
        with self._lock:
            return {
                **self._metrics,
                'current_queue_size': len(self._priority_queue),
                'total_processed_plans': len(self._processed_plans),
                'last_poll': self._last_poll_time.isoformat() if self._last_poll_time else None
            }