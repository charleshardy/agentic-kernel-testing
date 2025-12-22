#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    from orchestrator.timeout_manager import TimeoutManager
    print("Import successful")
    
    manager = TimeoutManager()
    print("Manager created")
    
    result = manager.start()
    print(f"Manager start result: {result}")
    
    stats = manager.get_statistics()
    print(f"Manager stats: {stats}")
    
    health = manager.get_health_status()
    print(f"Manager health: {health}")
    
    manager.stop()
    print("Manager stopped")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()