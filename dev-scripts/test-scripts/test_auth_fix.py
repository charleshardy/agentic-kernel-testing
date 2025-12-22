#!/usr/bin/env python3
"""Test script to verify the authentication fix works."""

import requests
import json

def test_demo_login():
    """Test the demo login endpoint."""
    print("🔐 Testing demo login endpoint...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/demo-login"
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data", {}).get("access_token"):
                token = data["data"]["access_token"]
                print(f"✅ Demo login successful, got token: {token[:20]}...")
                return token
            else:
                print(f"❌ Login response missing token: {data}")
                return None
        else:
            print(f"❌ Login failed with status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return None

def test_generate_from_diff(token):
    """Test the generate-from-diff endpoint with authentication."""
    print("\n🤖 Testing generate-from-diff endpoint...")
    
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
"""
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/tests/generate-from-diff",
            params={
                "diff_content": sample_diff,
                "max_tests": 3,
                "test_types": ["unit"]
            },
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                generated_count = data.get("data", {}).get("generated_count", 0)
                print(f"✅ Test generation successful! Generated {generated_count} tests")
                return True
            else:
                print(f"❌ Generation failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Generation request failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Generation request failed: {e}")
        return False

def test_without_auth():
    """Test the endpoint without authentication (should work with demo user)."""
    print("\n🔓 Testing generate-from-diff without authentication...")
    
    sample_diff = "diff --git a/test.c b/test.c\n+int test_func() { return 0; }"
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/tests/generate-from-diff",
            params={
                "diff_content": sample_diff,
                "max_tests": 2,
                "test_types": ["unit"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                generated_count = data.get("data", {}).get("generated_count", 0)
                print(f"✅ No-auth generation successful! Generated {generated_count} tests")
                return True
            else:
                print(f"❌ No-auth generation failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ No-auth request failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ No-auth request failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Authentication Fix")
    print("=" * 40)
    
    # Test 1: Demo login
    token = test_demo_login()
    
    # Test 2: Generate with auth
    if token:
        test_generate_from_diff(token)
    
    # Test 3: Generate without auth (should work with demo user dependency)
    test_without_auth()
    
    print("\n" + "=" * 40)
    print("🎯 Test Summary:")
    print("- If all tests pass, the authentication fix is working")
    print("- The web GUI should now be able to generate tests")
    print("- Try the web interface at http://localhost:5173")

if __name__ == "__main__":
    main()