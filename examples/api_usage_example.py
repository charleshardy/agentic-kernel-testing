#!/usr/bin/env python3
"""Example script demonstrating API usage."""

import requests
import json
import time
from typing import Dict, Any


class AgenticTestingAPIClient:
    """Client for the Agentic AI Testing System API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token = None
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and get access token."""
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        if data["success"]:
            self.token = data["data"]["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            print(f"✓ Logged in as {username}")
            return data["data"]
        else:
            raise Exception(f"Login failed: {data.get('message', 'Unknown error')}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self.session.get(f"{self.base_url}/api/v1/health")
        response.raise_for_status()
        return response.json()
    
    def submit_tests(self, test_cases: list, priority: int = 0) -> Dict[str, Any]:
        """Submit test cases for execution."""
        payload = {
            "test_cases": test_cases,
            "priority": priority
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/tests/submit",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_execution_status(self, plan_id: str) -> Dict[str, Any]:
        """Get execution plan status."""
        response = self.session.get(
            f"{self.base_url}/api/v1/status/plans/{plan_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def get_test_result(self, test_id: str) -> Dict[str, Any]:
        """Get test result."""
        response = self.session.get(
            f"{self.base_url}/api/v1/results/tests/{test_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def list_test_results(self, **filters) -> Dict[str, Any]:
        """List test results with optional filters."""
        response = self.session.get(
            f"{self.base_url}/api/v1/results/tests",
            params=filters
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_code(self, repository_url: str, commit_sha: str = None) -> Dict[str, Any]:
        """Analyze code changes."""
        payload = {
            "repository_url": repository_url,
            "commit_sha": commit_sha
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/tests/analyze-code",
            json=payload
        )
        response.raise_for_status()
        return response.json()


def main():
    """Demonstrate API usage."""
    print("🚀 Agentic AI Testing System API Example")
    print("=" * 50)
    
    # Initialize client
    client = AgenticTestingAPIClient()
    
    try:
        # 1. Health check
        print("\n1. Checking API health...")
        health = client.health_check()
        print(f"   Status: {health['data']['status']}")
        print(f"   Version: {health['data']['version']}")
        
        # 2. Login
        print("\n2. Logging in...")
        login_result = client.login("admin", "admin123")
        print(f"   User: {login_result['user_info']['username']}")
        print(f"   Permissions: {', '.join(login_result['user_info']['permissions'])}")
        
        # 3. Submit test cases
        print("\n3. Submitting test cases...")
        test_cases = [
            {
                "name": "Network Driver Unit Test",
                "description": "Test e1000e network driver basic functionality",
                "test_type": "unit",
                "target_subsystem": "networking",
                "code_paths": ["drivers/net/ethernet/intel/e1000e/"],
                "execution_time_estimate": 120,
                "test_script": """#!/bin/bash
# Test e1000e driver loading and basic operations
modprobe e1000e
ip link show
echo "Driver test completed"
""",
                "required_hardware": {
                    "architecture": "x86_64",
                    "cpu_model": "Intel Xeon",
                    "memory_mb": 2048,
                    "is_virtual": True,
                    "emulator": "qemu"
                }
            },
            {
                "name": "Memory Management Stress Test",
                "description": "Stress test memory allocation and deallocation",
                "test_type": "performance",
                "target_subsystem": "memory_management",
                "execution_time_estimate": 300,
                "test_script": """#!/bin/bash
# Memory stress test
stress-ng --vm 4 --vm-bytes 1G --timeout 60s
echo "Memory stress test completed"
"""
            }
        ]
        
        submission = client.submit_tests(test_cases, priority=5)
        submission_id = submission["data"]["submission_id"]
        plan_id = submission["data"]["execution_plan_id"]
        test_ids = submission["data"]["test_case_ids"]
        
        print(f"   ✓ Submitted {len(test_ids)} tests")
        print(f"   Submission ID: {submission_id}")
        print(f"   Execution Plan ID: {plan_id}")
        print(f"   Test IDs: {', '.join(test_ids)}")
        
        # 4. Monitor execution status
        print(f"\n4. Monitoring execution status...")
        status = client.get_execution_status(plan_id)
        print(f"   Plan Status: {status['data']['overall_status']}")
        print(f"   Progress: {status['data']['progress']:.1%}")
        print(f"   Completed: {status['data']['completed_tests']}/{status['data']['total_tests']}")
        
        # 5. Get test results
        print(f"\n5. Retrieving test results...")
        results = client.list_test_results(page=1, page_size=10)
        print(f"   Found {len(results['data']['results'])} results")
        
        for result in results['data']['results'][:3]:  # Show first 3
            print(f"   - {result['test_id']}: {result['status']} ({result['execution_time']:.1f}s)")
        
        # 6. Code analysis example
        print(f"\n6. Analyzing code changes...")
        analysis = client.analyze_code(
            repository_url="https://github.com/torvalds/linux.git",
            commit_sha="abc123def456"
        )
        print(f"   Analysis ID: {analysis['data']['analysis_id']}")
        print(f"   Impact Score: {analysis['data']['impact_score']:.2f}")
        print(f"   Risk Level: {analysis['data']['risk_level']}")
        print(f"   Affected Subsystems: {', '.join(analysis['data']['affected_subsystems'])}")
        
        print(f"\n✅ API demonstration completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server")
        print("   Make sure the API server is running on http://localhost:8000")
        print("   Start it with: python api/server.py")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response.status_code == 401:
            print("   Authentication failed - check credentials")
        elif e.response.status_code == 403:
            print("   Permission denied - check user permissions")
        else:
            try:
                error_data = e.response.json()
                print(f"   Details: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {e.response.text}")
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()