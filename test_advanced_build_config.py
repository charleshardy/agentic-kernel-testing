#!/usr/bin/env python3
"""
Test script to verify Advanced Build Config integration
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1/infrastructure"

def test_submit_with_advanced_config():
    """Test submitting a build job with advanced configuration"""
    
    payload = {
        "source_repository": "https://github.com/torvalds/linux.git",
        "branch": "master",
        "commit_hash": "HEAD",
        "target_architecture": "x86_64",
        "server_id": None,  # Auto-select
        "build_config": {
            # Build paths
            "workspace_root": "/tmp/test-builds",
            "output_directory": "/tmp/test-builds/output",
            "keep_workspace": True,
            
            # Git options
            "git_depth": 1,
            "git_submodules": False,
            
            # Build config
            "kernel_config": "defconfig",
            "extra_make_args": ["ARCH=x86_64", "CC=gcc"],
            "artifact_patterns": [
                "arch/x86/boot/bzImage",
                "vmlinux",
                "System.map"
            ],
            
            # Environment
            "custom_env": {
                "MAKEFLAGS": "-j8",
                "CFLAGS": "-O2"
            }
        }
    }
    
    print("Submitting build job with advanced config...")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{API_BASE}/build-jobs", json=payload)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Build job submitted with advanced config!")
            return response.json()
        else:
            print(f"\n❌ FAILED: {response.text}")
            return None
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return None


def test_list_build_jobs():
    """List all build jobs"""
    try:
        response = requests.get(f"{API_BASE}/build-jobs")
        print(f"\nBuild Jobs: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error listing jobs: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Advanced Build Config Integration")
    print("=" * 60)
    
    # Test submission
    job = test_submit_with_advanced_config()
    
    if job:
        print("\n" + "=" * 60)
        print("Listing all build jobs...")
        print("=" * 60)
        test_list_build_jobs()
