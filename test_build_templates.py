"""
Test Build Template Management

Tests the build template save/load/delete functionality.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/infrastructure"


def test_template_lifecycle():
    """Test creating, listing, loading, and deleting templates"""
    
    # 1. Create a custom build template
    print("\n1. Creating U-Boot template...")
    template_data = {
        "name": "U-Boot QEMU ARM64",
        "description": "Build U-Boot for QEMU ARM64 target",
        "build_mode": "custom",
        "pre_build_commands": [
            "export CROSS_COMPILE=aarch64-linux-gnu-",
            "export ARCH=arm64"
        ],
        "build_commands": [
            "make clean",
            "make qemu_arm64_defconfig",
            "make -j$(nproc)"
        ],
        "post_build_commands": [
            "ls -lh u-boot.bin"
        ],
        "custom_env": {
            "CC": "gcc-12",
            "CFLAGS": "-O2"
        },
        "workspace_root": "/tmp/uboot-builds",
        "keep_workspace": True
    }
    
    response = requests.post(f"{BASE_URL}/build-templates", json=template_data)
    assert response.status_code == 200, f"Failed to create template: {response.text}"
    template1 = response.json()
    print(f"✅ Created template: {template1['id']} - {template1['name']}")
    
    # 2. Create a kernel build template
    print("\n2. Creating kernel template...")
    kernel_template = {
        "name": "ARM64 Kernel",
        "description": "Standard ARM64 kernel build",
        "build_mode": "kernel",
        "kernel_config": "defconfig",
        "extra_make_args": ["ARCH=arm64", "CROSS_COMPILE=aarch64-linux-gnu-"],
        "artifact_patterns": ["arch/arm64/boot/Image", "vmlinux", "*.dtb"],
        "git_depth": 1,
        "git_submodules": False
    }
    
    response = requests.post(f"{BASE_URL}/build-templates", json=kernel_template)
    assert response.status_code == 200, f"Failed to create template: {response.text}"
    template2 = response.json()
    print(f"✅ Created template: {template2['id']} - {template2['name']}")
    
    # 3. List all templates
    print("\n3. Listing all templates...")
    response = requests.get(f"{BASE_URL}/build-templates")
    assert response.status_code == 200, f"Failed to list templates: {response.text}"
    templates = response.json()
    print(f"✅ Found {len(templates)} templates:")
    for t in templates:
        print(f"   - {t['name']}: {t['build_mode']} mode")
    
    # 4. Get specific template
    print(f"\n4. Getting template {template1['id']}...")
    response = requests.get(f"{BASE_URL}/build-templates/{template1['id']}")
    assert response.status_code == 200, f"Failed to get template: {response.text}"
    loaded_template = response.json()
    print(f"✅ Loaded template: {loaded_template['name']}")
    print(f"   Build commands: {len(loaded_template['build_commands'])} commands")
    print(f"   Environment vars: {list(loaded_template['custom_env'].keys())}")
    
    # 5. Update template
    print(f"\n5. Updating template {template1['id']}...")
    update_data = {
        "description": "Updated: Build U-Boot for QEMU ARM64 with optimizations"
    }
    response = requests.put(f"{BASE_URL}/build-templates/{template1['id']}", json=update_data)
    assert response.status_code == 200, f"Failed to update template: {response.text}"
    updated = response.json()
    print(f"✅ Updated template description: {updated['description']}")
    
    # 6. Delete templates
    print(f"\n6. Deleting templates...")
    response = requests.delete(f"{BASE_URL}/build-templates/{template1['id']}")
    assert response.status_code == 200, f"Failed to delete template: {response.text}"
    print(f"✅ Deleted template {template1['id']}")
    
    response = requests.delete(f"{BASE_URL}/build-templates/{template2['id']}")
    assert response.status_code == 200, f"Failed to delete template: {response.text}"
    print(f"✅ Deleted template {template2['id']}")
    
    # 7. Verify deletion
    print("\n7. Verifying deletion...")
    response = requests.get(f"{BASE_URL}/build-templates")
    templates = response.json()
    print(f"✅ Templates remaining: {len(templates)}")
    
    print("\n✅ All template tests passed!")


if __name__ == "__main__":
    test_template_lifecycle()
