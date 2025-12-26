#!/usr/bin/env python3
"""
Simple script to test if the backend API is running and responding
"""

import requests
import json
import time

def test_backend_connection():
    """Test if the backend is running and responding"""
    
    base_urls = [
        'http://localhost:8000/api/v1',  # Direct backend
        'http://localhost:3000/api/v1',  # Vite proxy
    ]
    
    for base_url in base_urls:
        print(f"\n🔍 Testing connection to: {base_url}")
        
        try:
            # Test health endpoint
            health_url = f"{base_url}/health"
            print(f"   Checking health endpoint: {health_url}")
            
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Health check successful!")
                print(f"   Response: {response.json()}")
                
                # Test tests endpoint
                tests_url = f"{base_url}/tests"
                print(f"   Checking tests endpoint: {tests_url}")
                
                response = requests.get(tests_url, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ Tests endpoint successful!")
                    data = response.json()
                    if 'data' in data and 'tests' in data['data']:
                        print(f"   Found {len(data['data']['tests'])} test cases")
                    return True
                else:
                    print(f"   ❌ Tests endpoint failed: {response.status_code}")
                    
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Connection timeout (>10s)")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection refused - backend not running?")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return False

def check_backend_processes():
    """Check if backend processes are running"""
    import subprocess
    
    print("\n🔍 Checking for running backend processes:")
    
    try:
        # Check for Python API processes
        result = subprocess.run(['pgrep', '-f', 'api'], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"   ✅ Found API processes: {result.stdout.strip()}")
        else:
            print(f"   ❌ No API processes found")
            
        # Check for uvicorn processes
        result = subprocess.run(['pgrep', '-f', 'uvicorn'], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"   ✅ Found uvicorn processes: {result.stdout.strip()}")
        else:
            print(f"   ❌ No uvicorn processes found")
            
    except Exception as e:
        print(f"   ❌ Error checking processes: {e}")

def main():
    print("🚀 Backend Connection Test")
    print("=" * 50)
    
    # Check processes
    check_backend_processes()
    
    # Test connections
    if test_backend_connection():
        print(f"\n✅ Backend is running and responding correctly!")
        print(f"   You can now use the Execution Monitor page.")
    else:
        print(f"\n❌ Backend is not responding properly.")
        print(f"\n💡 To fix this:")
        print(f"   1. Start the backend API server:")
        print(f"      python -m api.server")
        print(f"   2. Or use the start script:")
        print(f"      ./start-backend.sh")
        print(f"   3. Check if port 8000 is available:")
        print(f"      netstat -tlnp | grep 8000")

if __name__ == "__main__":
    main()