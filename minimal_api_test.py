#!/usr/bin/env python3
"""
Minimal API server test to isolate hanging issue.
"""

import sys
import time

def test_minimal_api():
    """Test minimal API setup."""
    
    print("Testing minimal FastAPI...")
    
    try:
        print("Step 1: Import FastAPI...")
        from fastapi import FastAPI
        print("✅ FastAPI imported")
        
        print("Step 2: Create app...")
        app = FastAPI(title="Minimal Test API")
        print("✅ FastAPI app created")
        
        print("Step 3: Add simple route...")
        @app.get("/test")
        def test_route():
            return {"message": "test"}
        print("✅ Route added")
        
        print("Step 4: Import uvicorn...")
        import uvicorn
        print("✅ uvicorn imported")
        
        print("✅ All minimal API components working")
        return True
        
    except Exception as e:
        print(f"❌ Minimal API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Minimal API Test ===")
    start_time = time.time()
    
    try:
        result = test_minimal_api()
        end_time = time.time()
        
        if result:
            print(f"\n🎉 Minimal API test completed in {end_time - start_time:.2f}s")
            print("The issue is likely in the complex API dependencies, not FastAPI itself.")
        else:
            print(f"\n❌ Minimal API test failed after {end_time - start_time:.2f}s")
            
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)