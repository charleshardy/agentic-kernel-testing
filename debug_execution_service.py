#!/usr/bin/env python3
"""
Debug script to check execution service status and logs.
"""

import sys
import os
import time
import requests
from datetime import datetime

sys.path.insert(0, '.')

def check_api_health():
    """Check if the API server is responding."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"API Health: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"API Health Check Failed: {e}")
        return False

def check_execution_service():
    """Check execution service status."""
    try:
        from execution.execution_service import get_execution_service
        service = get_execution_service()
        
        print(f"=== EXECUTION SERVICE DEBUG ===")
        print(f"Service initialized: {service is not None}")
        
        if service:
            print(f"Active executions: {len(service.active_executions)}")
            print(f"Execution progress: {len(service.execution_progress)}")
            print(f"Execution results: {len(service.execution_results)}")
            
            # List active executions
            for plan_id, plan in service.active_executions.items():
                print(f"  Plan {plan_id[:8]}...: {plan.status} ({len(plan.test_cases)} tests)")
                
                # Check progress
                progress = service.execution_progress.get(plan_id)
                if progress:
                    print(f"    Progress: {progress.completed_tests}/{progress.total_tests} ({progress.progress_percentage:.1f}%)")
                    print(f"    Current test: {progress.current_test}")
                
                # Check results
                results = service.execution_results.get(plan_id, [])
                print(f"    Results collected: {len(results)}")
        
        return True
    except Exception as e:
        print(f"Execution Service Check Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_specific_execution(plan_id):
    """Check a specific execution plan."""
    try:
        print(f"\n=== CHECKING EXECUTION {plan_id[:8]}... ===")
        
        # Try API call with timeout
        response = requests.get(f"http://localhost:8000/api/v1/execution/{plan_id}/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Response: Success")
            print(f"Status: {data['data']['overall_status']}")
            print(f"Progress: {data['data']['progress']*100:.1f}%")
            print(f"Tests: {data['data']['completed_tests']}/{data['data']['total_tests']}")
        else:
            print(f"API Response: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.Timeout:
        print("API call timed out - execution service may be stuck")
    except Exception as e:
        print(f"Error checking execution: {e}")

def main():
    print(f"=== EXECUTION DEBUG - {datetime.now()} ===")
    
    # Check API health
    api_healthy = check_api_health()
    
    if not api_healthy:
        print("API server is not responding properly")
        return
    
    # Check execution service
    service_healthy = check_execution_service()
    
    # Check specific execution if provided
    if len(sys.argv) > 1:
        plan_id = sys.argv[1]
        check_specific_execution(plan_id)
    
    # Check for hanging processes
    print(f"\n=== PROCESS CHECK ===")
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'python' in proc.info['name'] and 'api.server' in ' '.join(proc.info['cmdline'] or []):
                print(f"API Server Process: PID {proc.info['pid']}")
    except ImportError:
        print("psutil not available for process checking")

if __name__ == "__main__":
    main()