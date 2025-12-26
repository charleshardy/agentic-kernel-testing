#!/usr/bin/env python3
"""Start API server and test the Test Plans functionality."""

import sys
import os
import subprocess
import time
import requests
import signal
from threading import Thread

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def start_api_server():
    """Start the API server in a subprocess."""
    try:
        print("🚀 Starting API server...")
        
        # Start the server
        process = subprocess.Popen([
            sys.executable, "-m", "api.server", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server started successfully!")
                return process
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def test_test_plans_integration():
    """Test the test plans integration."""
    print("\n🧪 Testing Test Plans API...")
    
    try:
        # Import and run the test
        from test_test_plans_api import test_test_plans_api
        return test_test_plans_api()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function to start server and run tests."""
    print("🎯 Test Plans API Integration Test")
    print("=" * 50)
    
    # Start API server
    server_process = start_api_server()
    
    if not server_process:
        print("❌ Could not start API server. Exiting.")
        return False
    
    try:
        # Run the test
        success = test_test_plans_integration()
        
        if success:
            print("\n🎉 SUCCESS: Test Plans API is working correctly!")
            print("\nNext steps:")
            print("1. Start the frontend: cd dashboard && npm run dev")
            print("2. Navigate to Test Plans page")
            print("3. The warning banner should disappear")
            print("4. You should see real test plans instead of mock data")
            print("5. Try creating a new test plan")
            print("6. Add test cases to the plan from the Test Cases page")
        else:
            print("\n❌ FAILED: Some API tests failed")
        
        return success
        
    finally:
        # Clean up: stop the server
        print(f"\n🛑 Stopping API server (PID: {server_process.pid})...")
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
            print("✅ API server stopped")
        except subprocess.TimeoutExpired:
            print("⚠️ Server didn't stop gracefully, killing...")
            server_process.kill()
        except Exception as e:
            print(f"⚠️ Error stopping server: {e}")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)