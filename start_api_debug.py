#!/usr/bin/env python3
"""
Start API server with debug information.
"""

import sys
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_api_server():
    """Start API server with error handling."""
    
    try:
        print("Step 1: Testing imports...")
        import uvicorn
        from api.server import app
        print("✅ API imports OK")
        
        print("Step 2: Testing execution service integration...")
        from execution.execution_service import get_execution_service
        service = get_execution_service()
        print("✅ Execution service integration OK")
        
        print("Step 3: Testing API routes...")
        from api.routers.execution import router
        print("✅ API routes OK")
        
        print("Step 4: Starting server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        print(f"❌ API server failed to start: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("=== API Server Debug Start ===")
    success = start_api_server()
    sys.exit(0 if success else 1)