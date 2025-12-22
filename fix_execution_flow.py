#!/usr/bin/env python3
"""
Fix the execution flow by ensuring orchestrator starts and processes plans
"""

import sys
import os
sys.path.append('.')

def fix_execution_flow():
    """Fix the execution flow issues"""
    
    print("=== Fixing Execution Flow ===")
    print()
    
    # Step 1: Start the orchestrator
    print("1. Starting Orchestrator...")
    try:
        from api.orchestrator_integration import start_orchestrator, get_orchestrator
        
        success = start_orchestrator()
        print(f"   - Orchestrator start result: {success}")
        
        if success:
            orchestrator = get_orchestrator()
            if orchestrator:
                health = orchestrator.get_health_status()
                print(f"   - Health status: {health}")
                print("   ✅ Orchestrator is now running!")
            else:
                print("   ❌ Orchestrator instance not available")
        else:
            print("   ❌ Failed to start orchestrator")
            
    except Exception as e:
        print(f"   ❌ Error starting orchestrator: {e}")
        return False
    
    print()
    
    # Step 2: Check if there are existing execution plans to process
    print("2. Checking Existing Execution Plans...")
    try:
        from api.routers.tests import execution_plans, submitted_tests
        
        print(f"   - Execution plans: {len(execution_plans)}")
        print(f"   - Submitted tests: {len(submitted_tests)}")
        
        if execution_plans:
            print("   - Existing plans:")
            for plan_id, plan_data in execution_plans.items():
                status = plan_data.get('status', 'unknown')
                test_count = len(plan_data.get('test_case_ids', []))
                print(f"     * {plan_id}: {status} ({test_count} tests)")
        
    except Exception as e:
        print(f"   ❌ Error checking plans: {e}")
    
    print()
    
    # Step 3: Force orchestrator to poll for plans
    print("3. Forcing Orchestrator to Poll for Plans...")
    try:
        orchestrator = get_orchestrator()
        if orchestrator and hasattr(orchestrator, 'queue_monitor'):
            queue_monitor = orchestrator.queue_monitor
            
            print("   - Polling for new plans...")
            new_plans = queue_monitor.poll_for_new_plans()
            print(f"   - Plans detected: {len(new_plans)}")
            print(f"   - Queue count: {queue_monitor.get_queued_plan_count()}")
            print(f"   - Queued tests: {queue_monitor.get_queued_test_count()}")
            
            if new_plans:
                print("   - Detected plans:")
                for plan in new_plans:
                    print(f"     * {plan.get('plan_id')}: {plan.get('status')}")
                    
        else:
            print("   ❌ Queue monitor not available")
            
    except Exception as e:
        print(f"   ❌ Error polling plans: {e}")
    
    print()
    
    # Step 4: Create a test to verify the flow works
    print("4. Testing End-to-End Flow...")
    try:
        # Create a test case
        from ai_generator.models import TestCase, TestType, HardwareConfig
        from api.routers.tests import submitted_tests, execution_plans
        import uuid
        from datetime import datetime
        
        test_id = str(uuid.uuid4())
        test_case = TestCase(
            id=test_id,
            name="Test Flow Verification",
            description="Test to verify execution flow works",
            test_type=TestType.UNIT,
            target_subsystem="test",
            code_paths=[],
            execution_time_estimate=30,
            test_script="echo 'Test flow verification'; sleep 5; echo 'Complete'"
        )
        
        # Store the test case
        submitted_tests[test_id] = {
            "test_case": test_case,
            "submission_id": str(uuid.uuid4()),
            "submitted_by": "fix_script",
            "submitted_at": datetime.utcnow(),
            "priority": 5,
            "generation_info": {
                "method": "manual",
                "source_data": {"test": "flow_verification"}
            },
            "execution_status": "never_run",
            "tags": ["test", "verification"],
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
            "created_by": "fix_script"
        }
        
        print(f"   - Created test case: {test_id}")
        print(f"   - Created execution plan: {plan_id}")
        
        # Force orchestrator to detect it
        orchestrator = get_orchestrator()
        if orchestrator and hasattr(orchestrator, 'queue_monitor'):
            queue_monitor = orchestrator.queue_monitor
            
            new_plans = queue_monitor.poll_for_new_plans()
            print(f"   - Plans detected after creation: {len(new_plans)}")
            print(f"   - Queue count: {queue_monitor.get_queued_plan_count()}")
            
            if queue_monitor.get_queued_plan_count() > 0:
                print("   ✅ Test plan successfully queued in orchestrator!")
            else:
                print("   ❌ Test plan not detected by orchestrator")
        
    except Exception as e:
        print(f"   ❌ Error testing flow: {e}")
    
    print()
    
    # Step 5: Provide instructions
    print("5. Next Steps:")
    print("   1. Start the API server: python -m api.server")
    print("   2. Start the dashboard: cd dashboard && npm run dev")
    print("   3. Go to Test Cases page and create an AI test")
    print("   4. Check Test Execution page for real-time updates")
    print()
    print("=== Fix Complete ===")
    
    return True

if __name__ == "__main__":
    fix_execution_flow()