#!/usr/bin/env python3
"""Example usage of build system integration.

This example demonstrates how to use the build integration system to
automatically trigger tests when builds complete.
"""

from datetime import datetime
from integration.build_integration import BuildIntegration
from integration.build_models import (
    BuildEvent, BuildInfo, BuildStatus, BuildSystem, BuildType,
    KernelImage, BSPPackage, BuildArtifact
)


def test_handler(build_event: BuildEvent):
    """Handler that gets called when a build completes successfully."""
    build_info = build_event.build_info
    print(f"\n=== Build Completed Successfully ===")
    print(f"Build ID: {build_info.build_id}")
    print(f"Build Type: {build_info.build_type.value}")
    print(f"Build System: {build_info.build_system.value}")
    print(f"Commit SHA: {build_info.commit_sha}")
    print(f"Branch: {build_info.branch}")
    print(f"Duration: {build_info.duration_seconds:.2f}s")
    
    # Extract kernel image if available
    integration = BuildIntegration()
    kernel_image = integration.extract_kernel_image(build_info)
    if kernel_image:
        print(f"\nKernel Image:")
        print(f"  Version: {kernel_image.version}")
        print(f"  Architecture: {kernel_image.architecture}")
        print(f"  Path: {kernel_image.image_path}")
    
    # Extract BSP package if available
    bsp_package = integration.extract_bsp_package(build_info)
    if bsp_package:
        print(f"\nBSP Package:")
        print(f"  Name: {bsp_package.name}")
        print(f"  Version: {bsp_package.version}")
        print(f"  Target Board: {bsp_package.target_board}")
        print(f"  Path: {bsp_package.package_path}")
    
    print(f"\n=== Triggering Tests ===")
    print("Tests would be initiated here...")


def main():
    """Demonstrate build integration usage."""
    print("Build System Integration Example")
    print("=" * 50)
    
    # Create build integration instance
    integration = BuildIntegration()
    
    # Register handler for build completion
    integration.register_build_handler(test_handler)
    print("Registered build completion handler")
    
    # Example 1: Successful kernel build
    print("\n\nExample 1: Successful Kernel Build")
    print("-" * 50)
    
    kernel_build = BuildInfo(
        build_id="jenkins-1234",
        build_number=1234,
        build_system=BuildSystem.JENKINS,
        build_type=BuildType.KERNEL,
        status=BuildStatus.SUCCESS,
        start_time=datetime.now(),
        duration_seconds=300.5,
        commit_sha="abc123def456789012345678901234567890abcd",
        branch="main",
        build_log_url="https://jenkins.example.com/job/kernel-build/1234",
        triggered_by="developer@example.com"
    )
    
    # Add kernel image
    kernel_build.kernel_image = KernelImage(
        version="6.5.0",
        architecture="x86_64",
        image_path="/build/vmlinuz-6.5.0",
        config_path="/build/config-6.5.0",
        build_timestamp=datetime.now(),
        commit_sha="abc123def456789012345678901234567890abcd"
    )
    
    kernel_event = BuildEvent(
        event_id="jenkins-1234-event",
        build_system=BuildSystem.JENKINS,
        build_info=kernel_build
    )
    
    integration.handle_build_event(kernel_event)
    
    # Example 2: Successful BSP build
    print("\n\nExample 2: Successful BSP Build")
    print("-" * 50)
    
    bsp_build = BuildInfo(
        build_id="gitlab-5678",
        build_number=5678,
        build_system=BuildSystem.GITLAB_CI,
        build_type=BuildType.BSP,
        status=BuildStatus.SUCCESS,
        start_time=datetime.now(),
        duration_seconds=450.2,
        commit_sha="def456abc123789012345678901234567890abcd",
        branch="develop",
        build_log_url="https://gitlab.example.com/bsp-build/5678",
        triggered_by="ci-bot"
    )
    
    # Add BSP package
    bsp_build.bsp_package = BSPPackage(
        name="raspberry-pi-bsp",
        version="2.1.0",
        target_board="raspberry-pi-4",
        architecture="arm64",
        package_path="/build/raspberry-pi-bsp-2.1.0.tar.gz",
        kernel_version="6.5.0",
        build_timestamp=datetime.now(),
        commit_sha="def456abc123789012345678901234567890abcd"
    )
    
    bsp_event = BuildEvent(
        event_id="gitlab-5678-event",
        build_system=BuildSystem.GITLAB_CI,
        build_info=bsp_build
    )
    
    integration.handle_build_event(bsp_event)
    
    # Example 3: Failed build (should not trigger tests)
    print("\n\nExample 3: Failed Build (No Tests Triggered)")
    print("-" * 50)
    
    failed_build = BuildInfo(
        build_id="github-9999",
        build_number=9999,
        build_system=BuildSystem.GITHUB_ACTIONS,
        build_type=BuildType.KERNEL,
        status=BuildStatus.FAILURE,
        start_time=datetime.now(),
        duration_seconds=120.0,
        commit_sha="bad123def456789012345678901234567890abcd",
        branch="feature/broken",
        build_log_url="https://github.com/repo/actions/runs/9999"
    )
    
    failed_event = BuildEvent(
        event_id="github-9999-event",
        build_system=BuildSystem.GITHUB_ACTIONS,
        build_info=failed_build
    )
    
    integration.handle_build_event(failed_event)
    print("Failed build - no tests triggered (as expected)")
    
    # Example 4: Parse Jenkins webhook
    print("\n\nExample 4: Parse Jenkins Webhook")
    print("-" * 50)
    
    jenkins_payload = {
        "build": {
            "number": 2000,
            "status": "SUCCESS",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "duration": 250000,  # milliseconds
            "url": "https://jenkins.example.com/job/kernel/2000",
            "artifacts": [
                {
                    "fileName": "vmlinuz-6.6.0",
                    "relativePath": "build/vmlinuz-6.6.0",
                    "size": 8388608,
                    "md5sum": "abc123def456"
                },
                {
                    "fileName": "config-6.6.0",
                    "relativePath": "build/config-6.6.0",
                    "size": 204800,
                    "md5sum": "def456abc123"
                }
            ]
        },
        "scm": {
            "commit": "new123def456789012345678901234567890abcd",
            "branch": "main"
        },
        "user": {
            "name": "jenkins-bot"
        }
    }
    
    jenkins_event = integration.parse_jenkins_event(jenkins_payload)
    print(f"Parsed Jenkins event: {jenkins_event.event_id}")
    print(f"Build artifacts: {len(jenkins_event.build_info.artifacts)}")
    
    integration.handle_build_event(jenkins_event)
    
    print("\n\n" + "=" * 50)
    print("Build integration example completed!")


if __name__ == "__main__":
    main()
