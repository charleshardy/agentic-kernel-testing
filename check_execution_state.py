#!/usr/bin/env python3
"""
Check the current execution state directly
"""

import sys
sys.path.append('.')

def check_execution_state():
    """Check the current execution state"""
    
    print("=== Checking Execution State ===")
    print()
    
    try:
        # Check execution plans
        from api.routers.tests import execution_plans, submitted_tests
        
        print(f"1. Execution Plans: {len(execution_plans)}")
        if execution_plans:
            for plan_id, plan_data in execution_plans.items():
                status = plan_data.get('status', 'unknown')
                test_count = len(plan_data.get('test_case_ids', []))
                created_at = plan_data.get('created_at', 'unknown')
                print(f"   - {plan_id}: {status} ({test_count} tests) - {created_at}")
        
        print()
        print(f"2. Submitted Tests: {len(submitted_tests)}")
        if submitted_tests:
            for test_id, test_data in list(submitted_tests.items())[-5:]:  # Show last 5
                name = test_data['test_case'].name
                status = test_data.get('execution_status', 'unknown')
                method = test_data.get('generation_info', {}).get('method', 'unknown')
                print(f"   - {test_id}: {name} ({status}) - {method}")
        
        print()
        
        # Check orchestrator
        from api.orchestrator_integration import get_orchestrator
        orchestrator = get_orchestrator()
        
        print(f"3. Orchestrator Status:")
        if orchestrator:
            print(f"   - Running: {orchestrator.is_running}")
            if orchestrator.is_running:
                try:
                    health = orchestrator.get_health_status()
                    print(f"   - Health: {health}")
                    
                    if hasattr(orchestrator, 'queue_monitor'):
                        queue_monitor = orchestrator.queue_monitor
                        print(f"   - Queued plans: {queue_monitor.get_queued_plan_count()}")
                        print(f"   - Queued tests: {queue_monitor.get_queued_test_count()}")
                except Exception as e:
                    print(f"   - Error getting status: {e}")
            else:
                print("   - Orchestrator not running")
        else:
            print("   - No orchestrator instance")
        
        print()
        
        # Try to create a simple test and see what happens
        print("4. Creating Test Case...")
        
        from ai_generator.models import TestCase, TestType
        import uuid
        from datetime import datetime
        
        test_id = str(uuid.uuid4())
        test_case = TestCase(
            id=test_id,
            name="Debug Test Case",
            description="Test case for debugging execution flow",
            test_type=TestType.UNIT,
            target_subsystem="debug",
            code_paths=[],
            execution_time_estimate=30,
            test_script="echo 'Debug test'; sleep 2; echo 'Complete'"
        )
        
        # Store the test case
        submitted_tests[test_id] = {
            "test_case": test_case,
            "submission_id": str(uuid.uuid4()),
            "submitted_by": "debug_script",
            "submitted_at": datetime.utcnow(),
            "priority": 5,
            "generation_info": {
                "method": "debug",
                "source_data": {"debug": True}
            },
            "execution_status": "never_run",
            "tags": ["debug"],
            "is_favorite": False,
            "updated_at": datetime.utcnow()
        }
        
        # Create execution plan
        plan_id = str(uuid.uuid4())
        execution_plans[plan_id] = {
            "submission_id": str(uuid.uuid4()),
            "test_case_ids": [test_id],
            "priority": 5,
            "status": "queued",
            "created_at": datetime.utcnow(),
            "created_by": "debug_script"
        }
        
        print(f"   - Created test: {test_id}")
        print(f"   - Created plan: {plan_id}")
        
        # Force orchestrator to poll
        if orchestrator and hasattr(orchestrator, 'queue_monitor'):
            queue_monitor = orchestrator.queue_monitor
            new_plans = queue_monitor.poll_for_new_plans()
            print(f"   - Forced poll detected: {len(new_plans)} plans")
            print(f"   - Queue count after poll: {queue_monitor.get_queued_plan_count()}")
        
        print()
        print("5. Final State:")
        print(f"   - Total execution plans: {len(execution_plans)}")
        print(f"   - Total submitted tests: {len(submitted_tests)}")
        
        if orchestrator and hasattr(orchestrator, 'queue_monitor'):
            queue_monitor = orchestrator.queue_monitor
            print(f"   - Orchestrator queued plans: {queue_monitor.get_queued_plan_count()}")
            print(f"   - Orchestrator queued tests: {queue_monitor.get_queued_test_count()}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_execution_state()