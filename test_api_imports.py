#!/usr/bin/env python3
"""
Test API imports to find hanging issue.
"""

import sys
import time

def test_api_imports():
    """Test API imports step by step."""
    
    print("Step 1: Basic FastAPI imports...")
    from fastapi import FastAPI, HTTPException
    print("✅ FastAPI imports OK")
    
    print("Step 2: API models...")
    try:
        from api.models import APIResponse
        print("✅ API models OK")
    except Exception as e:
        print(f"⚠️  API models failed: {e}")
    
    print("Step 3: API auth...")
    try:
        from api.auth import get_current_user
        print("✅ API auth OK")
    except Exception as e:
        print(f"⚠️  API auth failed: {e}")
    
    print("Step 4: Orchestrator integration...")
    try:
        from api.orchestrator_integration import get_orchestrator
        print("✅ Orchestrator integration OK")
    except Exception as e:
        print(f"⚠️  Orchestrator integration failed: {e}")
    
    print("Step 5: Execution service...")
    from execution.execution_service import get_execution_service
    print("✅ Execution service OK")
    
    print("Step 6: API execution router...")
    from api.routers.execution import router
    print("✅ API execution router OK")
    
    print("Step 7: API server app...")
    from api.server import app
    print("✅ API server app OK")
    
    return True

if __name__ == "__main__":
    try:
        print("=== API Imports Test ===")
        start_time = time.time()
        result = test_api_imports()
        end_time = time.time()
        
        if result:
            print(f"\n🎉 All imports completed in {end_time - start_time:.2f}s")
        else:
            print(f"\n❌ Import test failed after {end_time - start_time:.2f}s")
            
    except Exception as e:
        print(f"\n💥 Import test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)