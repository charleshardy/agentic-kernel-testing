#!/usr/bin/env python3
"""
Example demonstrating how to use the AI test generation features from the web GUI.

This example shows:
1. How to start the API server with AI generation endpoints
2. How to use the web GUI to auto-generate tests
3. Sample code diffs and functions for testing
"""

import asyncio
import subprocess
import time
import requests
import json
from pathlib import Path


def start_api_server():
    """Start the API server in the background."""
    print("🚀 Starting API server...")
    try:
        # Start the API server
        process = subprocess.Popen(
            ["python3", "-m", "api.server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server started successfully")
                return process
            else:
                print("❌ API server failed to start properly")
                return None
        except requests.exceptions.RequestException:
            print("❌ API server not responding")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None


def start_dashboard():
    """Start the web dashboard."""
    print("🌐 Starting web dashboard...")
    try:
        # Change to dashboard directory and start
        dashboard_dir = Path("dashboard")
        if not dashboard_dir.exists():
            print("❌ Dashboard directory not found")
            return None
            
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=dashboard_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for dashboard to start
        time.sleep(5)
        print("✅ Dashboard started at http://localhost:5173")
        return process
        
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return None


def test_api_endpoints():
    """Test the AI generation API endpoints directly."""
    print("\n🧪 Testing AI generation API endpoints...")
    
    base_url = "http://localhost:8000/api/v1"
    
    # Sample code diff for testing
    sample_diff = """
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -1000,6 +1000,15 @@ static void update_rq_clock_task(struct rq *rq, s64 delta)
 	rq->clock_task += delta;
 }
 
+static int new_scheduler_function(struct task_struct *p)
+{
+	if (!p)
+		return -EINVAL;
+	
+	p->priority = calculate_priority(p);
+	return 0;
+}
+
 /*
  * Update the per-runqueue clocks as we tick
  */
"""
    
    # Test 1: Generate tests from diff
    print("\n1. Testing generate-from-diff endpoint...")
    try:
        response = requests.post(
            f"{base_url}/tests/generate-from-diff",
            params={
                "diff_content": sample_diff,
                "max_tests": 5,
                "test_types": ["unit"]
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated {data['data']['generated_count']} tests from diff")
            print(f"   Affected subsystems: {data['data']['analysis']['affected_subsystems']}")
            print(f"   Risk level: {data['data']['analysis']['risk_level']}")
        else:
            print(f"❌ Failed to generate from diff: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing diff endpoint: {e}")
    
    # Test 2: Generate tests from function
    print("\n2. Testing generate-from-function endpoint...")
    try:
        response = requests.post(
            f"{base_url}/tests/generate-from-function",
            params={
                "function_name": "schedule_task",
                "file_path": "kernel/sched/core.c",
                "subsystem": "scheduler",
                "max_tests": 3
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Generated {data['data']['generated_count']} tests for function")
            print(f"   Function: {data['data']['function']['name']}")
            print(f"   Subsystem: {data['data']['function']['subsystem']}")
        else:
            print(f"❌ Failed to generate from function: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing function endpoint: {e}")


def show_usage_instructions():
    """Show instructions for using the web GUI."""
    print("\n" + "="*60)
    print("🎯 HOW TO USE AI TEST GENERATION IN WEB GUI")
    print("="*60)
    
    print("\n1. 🌐 Open the web dashboard:")
    print("   → Go to: http://localhost:5173")
    print("   → Navigate to 'Test Execution' page")
    
    print("\n2. 🤖 Click 'AI Generate Tests' button")
    
    print("\n3. 📝 Choose generation method:")
    print("   → 'From Code Diff': Paste a git diff to generate tests")
    print("   → 'From Function': Specify a function to test")
    
    print("\n4. 🔧 For Code Diff generation:")
    print("   → Paste your git diff in the text area")
    print("   → Set max tests to generate (1-100)")
    print("   → Select test types (unit, integration, etc.)")
    print("   → Click 'Generate Tests'")
    
    print("\n5. ⚙️ For Function generation:")
    print("   → Enter function name (e.g., 'schedule_task')")
    print("   → Enter file path (e.g., 'kernel/sched/core.c')")
    print("   → Select subsystem")
    print("   → Set max tests to generate")
    print("   → Click 'Generate Tests'")
    
    print("\n6. ✅ View generated tests:")
    print("   → Tests appear in the execution table")
    print("   → Click 'View' to see test details and scripts")
    print("   → Tests are automatically queued for execution")
    
    print("\n" + "="*60)
    print("📋 SAMPLE CODE DIFF FOR TESTING:")
    print("="*60)
    
    sample_diff = '''diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -1000,6 +1000,15 @@ static void update_rq_clock_task(struct rq *rq, s64 delta)
 	rq->clock_task += delta;
 }
 
+static int new_scheduler_function(struct task_struct *p)
+{
+	if (!p)
+		return -EINVAL;
+	
+	p->priority = calculate_priority(p);
+	return 0;
+}'''
    
    print(sample_diff)
    
    print("\n" + "="*60)
    print("🔧 SAMPLE FUNCTION PARAMETERS:")
    print("="*60)
    print("Function Name: schedule_task")
    print("File Path: kernel/sched/core.c")
    print("Subsystem: scheduler")
    print("Max Tests: 10")


def main():
    """Main function to demonstrate AI test generation."""
    print("🚀 AI Test Generation Demo")
    print("=" * 50)
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Cannot continue without API server")
        return
    
    try:
        # Test API endpoints
        test_api_endpoints()
        
        # Start dashboard
        dashboard_process = start_dashboard()
        
        # Show usage instructions
        show_usage_instructions()
        
        print("\n🎉 Demo setup complete!")
        print("\n⏳ Press Ctrl+C to stop all services...")
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            
    finally:
        # Clean up processes
        if api_process:
            api_process.terminate()
            api_process.wait()
        
        if 'dashboard_process' in locals() and dashboard_process:
            dashboard_process.terminate()
            dashboard_process.wait()
        
        print("✅ All services stopped")


if __name__ == "__main__":
    main()