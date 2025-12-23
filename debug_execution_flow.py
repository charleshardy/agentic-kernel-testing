#!/usr/bin/env python3
"""
Debug script to check the execution flow between API and orchestrator
"""

import sys
import os
sys.path.append('.')

def check_execution_flow():
    """Check the current state of execution flow"""
    
    print("=== Execution Flow Debug ===")
    print()
    
    # Check if orchestrator is running
    try:
        from api.orchestrator_integration import get_orchestrator, is_orchestrator_running
        
        orchestrator = get_orchestrator()
        is_running = is_orchestrator_running()
        
        print(f"1. Orchestrator Status:")
        print(f"   - Instance exists: {orchestrator is not None}")
        print(f"   - Is running: {is_running}")
        
        if orchestrator:
            try:
                health = orchestrator.get_health_status()
                print(f"   - Health status: {health}")
            except Exception as e:
                print(f"   - Health check failed: {e}")
        
    except Exception as e:
        print(f"1. Orchestrator Status: ERROR - {e}")
    
    print()
    
    # Check execution plans
    try:
        from api.routers.tests import execution_plans, submitted_tests
        
        print(f"2. Execution Plans:")
        print(f"   - Total execution plans: {len(execution_plans)}")
        print(f"   - Total submitted tests: {len(submitted_tests)}")
        
        if execution_plans:
            print("   - Recent execution plans:")
            for plan_id, plan_data in list(execution_plans.items())[-3:]:
                print(f"     * {plan_id}: {plan_data.get('status', 'unknown')} ({len(plan_data.get('test_case_ids', []))} tests)")
        
        if submitted_tests:
            print("   - Recent submitted tests:")
            for test_id, test_data in list(submitted_tests.items())[-3:]:
                print(f"     * {test_id}: {test_data.get('execution_status', 'unknown')} - {test_data['test_case'].name}")
        
    except Exception as e:
        print(f"2. Execution Plans: ERROR - {e}")
    
    print()
    
    # Check queue monitor
    try:
        from api.orchestrator_integration import get_orchestrator
        
        orchestrator = get_orchestrator()
        if orchestrator and hasattr(orchestrator, 'queue_monitor'):
            queue_monitor = orchestrator.queue_monitor
            
            print(f"3. Queue Monitor:")
            print(f"   - Queued plans: {queue_monitor.get_queued_plan_count()}")
            print(f"   - Queued tests: {queue_monitor.get_queued_test_count()}")
            
            # Try to poll for new plans
            try:
                new_plans = queue_monitor.poll_for_new_plans()
                print(f"   - New plans detected: {len(new_plans)}")
                
                if new_plans:
                    for plan in new_plans:
                        print(f"     * {plan.get('plan_id')}: {plan.get('status')}")
                        
            except Exception as e:
                print(f"   - Poll error: {e}")
        else:
            print("3. Queue Monitor: Not available")
            
    except Exception as e:
        print(f"3. Queue Monitor: ERROR - {e}")
    
    print()
    
    # Check if we can create a test execution plan
    try:
        print("4. Testing Execution Plan Creation:")
        
        from api.routers.tests import execution_plans
        import uuid
        from datetime import datetime
        
        # Create a test execution plan
        test_plan_id = str(uuid.uuid4())
        test_plan = {
            "submission_id": str(uuid.uuid4()),
            "test_case_ids": ["test-123-debug"],
            "priority": 5,
            "status": "queued",
            "created_at": datetime.utcnow(),
            "created_by": "debug_script"
        }
        
        execution_plans[test_plan_id] = test_plan
        print(f"   - Created test plan: {test_plan_id}")
        
        # Check if orchestrator can detect it
        from api.orchestrator_integration import get_orchestrator
        orchestrator = get_orchestrator()
        
        if orchestrator and hasattr(orchestrator, 'queue_monitor'):
            queue_monitor = orchestrator.queue_monitor
            
            # Force a poll
            new_plans = queue_monitor.poll_for_new_plans()
            print(f"   - Plans detected after creation: {len(new_plans)}")
            print(f"   - Queue count: {queue_monitor.get_queued_plan_count()}")
        
        # Always clean up the test plan
        if test_plan_id in execution_plans:
            del execution_plans[test_plan_id]
            print(f"   - Cleaned up test plan")
        
        # Clean up any other debug test plans
        debug_plans_to_remove = []
        for plan_id, plan_data in execution_plans.items():
            created_by = plan_data.get("created_by", "")
            test_case_ids = plan_data.get("test_case_ids", [])
            
            is_debug_test = (
                created_by == "debug_script" or 
                any(test_id.startswith("test-123") for test_id in test_case_ids) or
                any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
            )
            
            if is_debug_test:
                debug_plans_to_remove.append(plan_id)
        
        for plan_id in debug_plans_to_remove:
            if plan_id in execution_plans:
                del execution_plans[plan_id]
        
        if debug_plans_to_remove:
            print(f"   - Cleaned up {len(debug_plans_to_remove)} additional debug plans")
        
    except Exception as e:
        print(f"4. Testing Execution Plan Creation: ERROR - {e}")
        
        # Try to clean up even if there was an error
        try:
            from api.routers.tests import execution_plans
            debug_plans_to_remove = []
            for plan_id, plan_data in execution_plans.items():
                created_by = plan_data.get("created_by", "")
                test_case_ids = plan_data.get("test_case_ids", [])
                
                is_debug_test = (
                    created_by == "debug_script" or 
                    any(test_id.startswith("test-123") for test_id in test_case_ids) or
                    any(test_id.startswith("test_") and test_id.endswith("123") for test_id in test_case_ids)
                )
                
                if is_debug_test:
                    debug_plans_to_remove.append(plan_id)
            
            for plan_id in debug_plans_to_remove:
                if plan_id in execution_plans:
                    del execution_plans[plan_id]
            
            if debug_plans_to_remove:
                print(f"   - Emergency cleanup: removed {len(debug_plans_to_remove)} debug plans")
        except:
            pass
    
    print()
    print("=== Debug Complete ===")

if __name__ == "__main__":
    check_execution_flow()