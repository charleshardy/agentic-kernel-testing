#!/usr/bin/env python3
"""
Debug script to test BuildConfig creation
"""
import sys
sys.path.insert(0, '.')

from infrastructure.models.build_server import BuildConfig

# Test creating BuildConfig with dict data
build_config_dict = {
    'workspace_root': '/tmp/test-builds',
    'output_directory': '/tmp/test-builds/output',
    'keep_workspace': True,
    'git_depth': 1,
    'git_submodules': False,
    'kernel_config': 'defconfig',
    'extra_make_args': ['ARCH=x86_64', 'CC=gcc'],
    'artifact_patterns': [
        'arch/x86/boot/bzImage',
        'vmlinux',
        'System.map'
    ],
    'custom_env': {
        'MAKEFLAGS': '-j8',
        'CFLAGS': '-O2'
    }
}

print("Testing BuildConfig creation...")
print(f"Input dict: {build_config_dict}")

try:
    # Test with .get() method like in the API
    config = BuildConfig(
        workspace_root=build_config_dict.get('workspace_root', '/tmp/builds'),
        build_directory=build_config_dict.get('build_directory'),
        output_directory=build_config_dict.get('output_directory'),
        keep_workspace=build_config_dict.get('keep_workspace', False),
        kernel_config=build_config_dict.get('kernel_config', 'defconfig'),
        extra_make_args=build_config_dict.get('extra_make_args', []),
        enable_modules=build_config_dict.get('enable_modules', True),
        build_dtbs=build_config_dict.get('build_dtbs', True),
        custom_env=build_config_dict.get('custom_env', {}),
        artifact_patterns=build_config_dict.get('artifact_patterns') or [
            "arch/*/boot/bzImage",
            "arch/*/boot/Image",
            "arch/*/boot/zImage",
            "vmlinux",
            "System.map",
            "*.ko",
            "*.dtb"
        ],
        git_depth=build_config_dict.get('git_depth', 1),
        git_submodules=build_config_dict.get('git_submodules', False),
    )
    
    print("\n✅ SUCCESS: BuildConfig created successfully!")
    print(f"Config: {config}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
