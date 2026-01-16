#!/usr/bin/env python3
"""
Test script for Custom Build Commands feature
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1/infrastructure"

def test_kernel_build():
    """Test standard kernel build (default mode)"""
    print("=" * 60)
    print("Test 1: Standard Kernel Build")
    print("=" * 60)
    
    payload = {
        "source_repository": "https://github.com/torvalds/linux.git",
        "branch": "master",
        "target_architecture": "x86_64",
        "build_config": {
            "build_mode": "kernel",
            "kernel_config": "defconfig",
            "extra_make_args": ["ARCH=x86_64"]
        }
    }
    
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{API_BASE}/build-jobs", json=payload)
        print(f"\nStatus: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"❌ FAILED: {response.text}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def test_custom_build_uboot():
    """Test custom build for U-Boot"""
    print("\n" + "=" * 60)
    print("Test 2: Custom Build - U-Boot")
    print("=" * 60)
    
    payload = {
        "source_repository": "https://github.com/u-boot/u-boot.git",
        "branch": "master",
        "target_architecture": "arm64",
        "build_config": {
            "build_mode": "custom",
            "workspace_root": "/tmp/uboot-builds",
            "pre_build_commands": [
                "export CROSS_COMPILE=aarch64-linux-gnu-",
                "export ARCH=arm64"
            ],
            "build_commands": [
                "make qemu_arm64_defconfig",
                "make -j$(nproc)"
            ],
            "post_build_commands": [
                "ls -lh u-boot.bin",
                "file u-boot.bin"
            ],
            "artifact_patterns": [
                "u-boot.bin",
                "u-boot",
                "*.dtb"
            ],
            "custom_env": {
                "MAKEFLAGS": "-j8"
            }
        }
    }
    
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{API_BASE}/build-jobs", json=payload)
        print(f"\nStatus: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"❌ FAILED: {response.text}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def test_custom_build_with_patches():
    """Test custom build with patch application"""
    print("\n" + "=" * 60)
    print("Test 3: Custom Build - Kernel with Patches")
    print("=" * 60)
    
    payload = {
        "source_repository": "https://github.com/torvalds/linux.git",
        "branch": "master",
        "target_architecture": "x86_64",
        "build_config": {
            "build_mode": "custom",
            "pre_build_commands": [
                "# Download and apply patches",
                "curl -O https://example.com/my-patch.patch || true",
                "git apply my-patch.patch || true"
            ],
            "build_commands": [
                "make defconfig",
                "make -j$(nproc)",
                "make modules"
            ],
            "post_build_commands": [
                "# Run basic tests",
                "ls -lh arch/x86/boot/bzImage",
                "file arch/x86/boot/bzImage"
            ],
            "artifact_patterns": [
                "arch/x86/boot/bzImage",
                "vmlinux",
                "System.map"
            ]
        }
    }
    
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{API_BASE}/build-jobs", json=payload)
        print(f"\nStatus: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"❌ FAILED: {response.text}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def test_custom_build_simple_script():
    """Test custom build with simple shell script"""
    print("\n" + "=" * 60)
    print("Test 4: Custom Build - Simple Shell Script")
    print("=" * 60)
    
    payload = {
        "source_repository": "https://github.com/example/my-project.git",
        "branch": "main",
        "target_architecture": "x86_64",
        "build_config": {
            "build_mode": "custom",
            "build_commands": [
                "./build.sh",
                "ls -lh build/"
            ],
            "artifact_patterns": [
                "build/*",
                "dist/*"
            ]
        }
    }
    
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{API_BASE}/build-jobs", json=payload)
        print(f"\nStatus: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS: {json.dumps(response.json(), indent=2)}")
            return response.json()
        else:
            print(f"❌ FAILED: {response.text}")
            return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing Custom Build Commands Feature")
    print("=" * 60 + "\n")
    
    # Test 1: Standard kernel build
    job1 = test_kernel_build()
    
    # Test 2: Custom U-Boot build
    job2 = test_custom_build_uboot()
    
    # Test 3: Custom kernel build with patches
    job3 = test_custom_build_with_patches()
    
    # Test 4: Simple custom script
    job4 = test_custom_build_simple_script()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Standard Kernel Build: {'✅ PASS' if job1 else '❌ FAIL'}")
    print(f"Custom U-Boot Build: {'✅ PASS' if job2 else '❌ FAIL'}")
    print(f"Custom Build with Patches: {'✅ PASS' if job3 else '❌ FAIL'}")
    print(f"Simple Custom Script: {'✅ PASS' if job4 else '❌ FAIL'}")
