"""Unit tests for the queue monitor component."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys

from orchestrator.queue_monitor import QueueMonitor
from orchestrator.config import OrchestratorConfig


class TestQueueMonitor:
    """Test cases for the QueueMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = OrchestratorConfig()
        self.monitor = QueueMonitor(self.config)
        
        # Mock execution_plans dictionary
        self.execution_plans = {}
        
        # Create mock module for api.routers.tests
        self.mock_tests_module = MagicMock()
        self.mock_tests_module.execution_plans = self.execution_plans
        
        # Patch sys.modules
        self.modules_patcher = patch.dict('sys.modules', {
            'api': MagicMock(),
            'api.routers': MagicMock(),
            'api.routers.tests': self.mock_tests_module
        })
        self.modules_patcher.start()
    
    def teardown_method(self):
        """Clean up after tests."""
        self.modules_patcher.stop()
    
    def test_initial_state(self):
        """Test queue monitor initial state."""
        assert self.monitor.get_queued_plan_count() == 0
        assert self.monitor.get_queued_test_count() == 0
        
        status = self.monitor.get_queue_status()
        assert status['total_plans'] == 0
        assert status['total_tests'] == 0
        
        health = self.monitor.get_health_status()
        assert health['status'] == 'healthy'
        assert health['queued_plans'] == 0
    
    def test_poll_empty_execution_plans(self):
        """Test polling when no execution plans exist."""
        new_plans = self.monitor.poll_for_new_plans()
        assert new_plans == []
        assert self.monitor.get_queued_plan_count() == 0
    
    def test_poll_new_execution_plans(self):
        """Test polling detects new execution plans."""
        # Add execution plans
        plan1_id = str(uuid.uuid4())
        plan2_id = str(uuid.uuid4())
        
        self.execution_plans[plan1_id] = {
            'submission_id': 'sub1',
            'test_case_ids': ['test1', 'test2'],
            'priority': 1,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        self.execution_plans[plan2_id] = {
            'submission_id': 'sub2',
            'test_case_ids': ['test3'],
            'priority': 5,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        # Poll for new plans
        new_plans = self.monitor.poll_for_new_plans()
        
        assert len(new_plans) == 2
        assert self.monitor.get_queued_plan_count() == 2
        assert self.monitor.get_queued_test_count() == 3  # 2 + 1 tests
        
        # Verify plan data
        plan_ids = [plan['plan_id'] for plan in new_plans]
        assert plan1_id in plan_ids
        assert plan2_id in plan_ids
    
    def test_priority_ordering(self):
        """Test that plans are returned in correct priority order."""
        # Add plans with different priorities (1=highest, 10=lowest)
        plan_high = str(uuid.uuid4())
        plan_medium = str(uuid.uuid4())
        plan_low = str(uuid.uuid4())
        
        self.execution_plans[plan_high] = {
            'submission_id': 'sub_high',
            'test_case_ids': ['test1'],
            'priority': 1,  # Highest priority
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        self.execution_plans[plan_medium] = {
            'submission_id': 'sub_medium',
            'test_case_ids': ['test2'],
            'priority': 5,  # Medium priority
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        self.execution_plans[plan_low] = {
            'submission_id': 'sub_low',
            'test_case_ids': ['test3'],
            'priority': 9,  # Low priority
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        # Poll to detect plans
        self.monitor.poll_for_new_plans()
        
        # Get plans in priority order
        first_plan = self.monitor.get_next_execution_plan()
        second_plan = self.monitor.get_next_execution_plan()
        third_plan = self.monitor.get_next_execution_plan()
        
        # Verify priority ordering (1 = highest, 9 = lowest)
        assert first_plan['priority'] == 1
        assert first_plan['plan_id'] == plan_high
        
        assert second_plan['priority'] == 5
        assert second_plan['plan_id'] == plan_medium
        
        assert third_plan['priority'] == 9
        assert third_plan['plan_id'] == plan_low
    
    def test_fifo_ordering_same_priority(self):
        """Test FIFO ordering for plans with same priority."""
        import time
        
        # Add plans with same priority but different timestamps
        plan1_id = str(uuid.uuid4())
        plan2_id = str(uuid.uuid4())
        
        self.execution_plans[plan1_id] = {
            'submission_id': 'sub1',
            'test_case_ids': ['test1'],
            'priority': 5,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        # Small delay to ensure different timestamps
        time.sleep(0.001)
        
        self.execution_plans[plan2_id] = {
            'submission_id': 'sub2',
            'test_case_ids': ['test2'],
            'priority': 5,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        # Poll to detect plans
        self.monitor.poll_for_new_plans()
        
        # Get plans - should be in FIFO order for same priority
        first_plan = self.monitor.get_next_execution_plan()
        second_plan = self.monitor.get_next_execution_plan()
        
        # First submitted should be first returned
        assert first_plan['plan_id'] == plan1_id
        assert second_plan['plan_id'] == plan2_id
    
    def test_default_priority(self):
        """Test that plans without priority get default priority."""
        plan_id = str(uuid.uuid4())
        
        self.execution_plans[plan_id] = {
            'submission_id': 'sub1',
            'test_case_ids': ['test1'],
            # No priority specified
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        self.monitor.poll_for_new_plans()
        plan = self.monitor.get_next_execution_plan()
        
        assert plan['priority'] == 5  # Default priority
    
    def test_queue_status_details(self):
        """Test detailed queue status information."""
        # Add some plans
        plan1_id = str(uuid.uuid4())
        plan2_id = str(uuid.uuid4())
        
        self.execution_plans[plan1_id] = {
            'submission_id': 'sub1',
            'test_case_ids': ['test1', 'test2'],
            'priority': 1,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        self.execution_plans[plan2_id] = {
            'submission_id': 'sub2',
            'test_case_ids': ['test3'],
            'priority': 9,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        self.monitor.poll_for_new_plans()
        status = self.monitor.get_queue_status()
        
        assert status['total_plans'] == 2
        assert status['total_tests'] == 3
        assert len(status['queue_details']) == 2
        
        # Verify queue details are sorted by priority (highest first)
        details = status['queue_details']
        assert details[0]['priority'] == 1  # Highest priority first
        assert details[1]['priority'] == 9  # Lower priority second
        
        # Verify plan details
        high_priority_plan = details[0]
        assert high_priority_plan['plan_id'] == plan1_id
        assert high_priority_plan['test_count'] == 2
        assert high_priority_plan['submission_id'] == 'sub1'
    
    def test_processed_plans_tracking(self):
        """Test that processed plans are not re-detected."""
        plan_id = str(uuid.uuid4())
        
        self.execution_plans[plan_id] = {
            'submission_id': 'sub1',
            'test_case_ids': ['test1'],
            'priority': 5,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        # First poll should detect the plan
        new_plans = self.monitor.poll_for_new_plans()
        assert len(new_plans) == 1
        
        # Second poll should not detect it again
        new_plans = self.monitor.poll_for_new_plans()
        assert len(new_plans) == 0
        
        # Plan should still be in queue until retrieved
        assert self.monitor.get_queued_plan_count() == 1
    
    def test_get_next_execution_plan_empty_queue(self):
        """Test getting next plan when queue is empty."""
        plan = self.monitor.get_next_execution_plan()
        assert plan is None
    
    def test_get_next_execution_plan_with_polling(self):
        """Test that get_next_execution_plan polls for new plans."""
        # Add a plan after monitor is created
        plan_id = str(uuid.uuid4())
        
        self.execution_plans[plan_id] = {
            'submission_id': 'sub1',
            'test_case_ids': ['test1'],
            'priority': 5,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        # get_next_execution_plan should poll and find the new plan
        plan = self.monitor.get_next_execution_plan()
        assert plan is not None
        assert plan['plan_id'] == plan_id
    
    def test_metrics_tracking(self):
        """Test that metrics are properly tracked."""
        initial_metrics = self.monitor.get_metrics()
        assert initial_metrics['plans_detected'] == 0
        assert initial_metrics['plans_queued'] == 0
        assert initial_metrics['total_processed_plans'] == 0
        
        # Add and process a plan
        plan_id = str(uuid.uuid4())
        self.execution_plans[plan_id] = {
            'submission_id': 'sub1',
            'test_case_ids': ['test1'],
            'priority': 5,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        self.monitor.poll_for_new_plans()
        self.monitor.get_next_execution_plan()
        
        final_metrics = self.monitor.get_metrics()
        assert final_metrics['plans_detected'] == 1
        assert final_metrics['plans_queued'] == 1
        assert final_metrics['total_processed_plans'] == 1
    
    def test_reset_processed_plans(self):
        """Test resetting processed plans tracking."""
        plan_id = str(uuid.uuid4())
        
        self.execution_plans[plan_id] = {
            'submission_id': 'sub1',
            'test_case_ids': ['test1'],
            'priority': 5,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        # Process the plan
        self.monitor.poll_for_new_plans()
        self.monitor.get_next_execution_plan()
        
        # Reset processed plans
        self.monitor.reset_processed_plans()
        
        # Should be able to detect the same plan again
        new_plans = self.monitor.poll_for_new_plans()
        assert len(new_plans) == 1
        assert new_plans[0]['plan_id'] == plan_id
    
    def test_clear_queue(self):
        """Test clearing the execution queue."""
        # Add some plans
        for i in range(3):
            plan_id = str(uuid.uuid4())
            self.execution_plans[plan_id] = {
                'submission_id': f'sub{i}',
                'test_case_ids': [f'test{i}'],
                'priority': 5,
                'status': 'queued',
                'created_at': datetime.now()
            }
        
        self.monitor.poll_for_new_plans()
        assert self.monitor.get_queued_plan_count() == 3
        
        # Clear the queue
        self.monitor.clear_queue()
        assert self.monitor.get_queued_plan_count() == 0
        assert self.monitor.get_next_execution_plan() is None
    
    def test_error_handling_import_error(self):
        """Test handling of import errors when execution_plans is not available."""
        # Remove the mock module to simulate import error
        self.modules_patcher.stop()
        
        # Should handle gracefully
        new_plans = self.monitor.poll_for_new_plans()
        assert new_plans == []
        
        plan = self.monitor.get_next_execution_plan()
        assert plan is None
        
        # Restart the patcher for cleanup
        self.modules_patcher.start()