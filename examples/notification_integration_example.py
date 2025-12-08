#!/usr/bin/env python3
"""
Integration example showing how to use notifications with test execution.

This demonstrates how the notification system integrates with the test
execution pipeline to alert developers of critical failures.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from integration.notification_service import NotificationDispatcher
from integration.notification_models import (
    Notification,
    NotificationSeverity,
    NotificationRecipient
)
from ai_generator.models import (
    TestResult,
    TestStatus,
    Environment,
    HardwareConfig,
    EnvironmentStatus,
    FailureInfo,
    ArtifactBundle
)


def simulate_test_execution_with_notifications():
    """Simulate a test execution that triggers notifications."""
    
    print("="*70)
    print("Notification System Integration Example")
    print("="*70)
    print()
    
    # Initialize notification dispatcher
    dispatcher = NotificationDispatcher()
    
    # Define recipients
    recipients = [
        NotificationRecipient(
            name="Kernel Team Lead",
            email="kernel-lead@example.com",
            slack_user_id="U12345"
        ),
        NotificationRecipient(
            name="Network Driver Maintainer",
            email="network-maintainer@example.com",
            slack_user_id="U67890"
        )
    ]
    
    # Simulate test execution
    print("1. Simulating test execution...")
    print()
    
    # Create test environment
    hw_config = HardwareConfig(
        architecture="x86_64",
        cpu_model="Intel Xeon",
        memory_mb=8192,
        is_virtual=True,
        emulator="qemu"
    )
    
    environment = Environment(
        id="env_001",
        config=hw_config,
        status=EnvironmentStatus.BUSY,
        kernel_version="6.5.0",
        ip_address="192.168.1.100"
    )
    
    # Simulate a kernel panic failure
    failure_info = FailureInfo(
        error_message="NULL pointer dereference in network driver",
        stack_trace="""
        [  123.456789] BUG: kernel NULL pointer dereference, address: 0000000000000000
        [  123.456790] #PF: supervisor read access in kernel mode
        [  123.456791] #PF: error_code(0x0000) - not-present page
        [  123.456792] PGD 0 P4D 0
        [  123.456793] Oops: 0000 [#1] SMP PTI
        [  123.456794] CPU: 2 PID: 1234 Comm: test_network Not tainted 6.5.0 #1
        [  123.456795] Hardware name: QEMU Standard PC (i440FX + PIIX, 1996)
        [  123.456796] RIP: 0010:e1000e_xmit_frame+0x123/0x456
        """,
        exit_code=-1,
        kernel_panic=True
    )
    
    test_result = TestResult(
        test_id="test_network_driver_042",
        status=TestStatus.FAILED,
        execution_time=45.2,
        environment=environment,
        artifacts=ArtifactBundle(
            logs=["kernel.log", "dmesg.log"],
            core_dumps=["core.dump"]
        ),
        failure_info=failure_info
    )
    
    print(f"   Test ID: {test_result.test_id}")
    print(f"   Status: {test_result.status.value}")
    print(f"   Failure: {failure_info.error_message}")
    print(f"   Kernel Panic: {failure_info.kernel_panic}")
    print()
    
    # Check if this is a critical failure requiring notification
    if test_result.status == TestStatus.FAILED and failure_info.kernel_panic:
        print("2. Critical failure detected - sending notifications...")
        print()
        
        # Send critical failure notification
        results = dispatcher.send_critical_failure_notification(
            title=f"Kernel Panic in {test_result.test_id}",
            message=f"A kernel panic was detected during test execution.\n\n"
                    f"Error: {failure_info.error_message}\n\n"
                    f"The system crashed while testing the network driver module. "
                    f"Immediate attention required.",
            test_id=test_result.test_id,
            failure_id=f"failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            recipients=recipients,
            metadata={
                "subsystem": "network",
                "driver": "e1000e",
                "kernel_version": environment.kernel_version,
                "architecture": hw_config.architecture,
                "crash_type": "NULL pointer dereference",
                "execution_time": f"{test_result.execution_time}s",
                "environment": environment.id,
                "artifacts": ", ".join(test_result.artifacts.logs)
            }
        )
        
        print(f"   Notification sent to {len(recipients)} recipients")
        print(f"   Channels attempted: {len(results)}")
        print()
        
        for result in results:
            status = "✓" if result.success else "✗"
            print(f"   {status} {result.channel.value}: ", end="")
            if result.success:
                print("Sent successfully")
            else:
                print(f"Failed - {result.error_message}")
        print()
    
    # Simulate a warning-level notification for performance regression
    print("3. Simulating performance regression notification...")
    print()
    
    perf_notification = Notification(
        id=f"perf_{datetime.now().timestamp()}",
        title="Performance Regression Detected",
        message="A 30% performance regression was detected in the I/O subsystem.\n\n"
                "Baseline: 500 MB/s\n"
                "Current: 350 MB/s\n\n"
                "This may impact production performance.",
        severity=NotificationSeverity.WARNING,
        test_id="perf_io_test_001",
        recipients=recipients,
        metadata={
            "subsystem": "I/O",
            "benchmark": "FIO sequential write",
            "baseline_throughput": "500 MB/s",
            "current_throughput": "350 MB/s",
            "regression_percentage": "30%",
            "commit_range": "abc123..def456"
        }
    )
    
    # Route based on severity
    perf_notification = dispatcher.route_notification(perf_notification)
    
    print(f"   Severity: {perf_notification.severity.value}")
    print(f"   Routed to channels: {[ch.value for ch in perf_notification.channels]}")
    print()
    
    # Send the notification
    perf_results = dispatcher.send_notification(perf_notification)
    
    for result in perf_results:
        status = "✓" if result.success else "✗"
        print(f"   {status} {result.channel.value}: ", end="")
        if result.success:
            print("Sent successfully")
        else:
            print(f"Failed - {result.error_message}")
    print()
    
    # Demonstrate severity filtering
    print("4. Demonstrating severity filtering...")
    print()
    
    # Create notifications of different severities
    test_notifications = [
        ("Info: Test started", NotificationSeverity.INFO),
        ("Warning: High memory usage", NotificationSeverity.WARNING),
        ("Error: Test timeout", NotificationSeverity.ERROR),
        ("Critical: System crash", NotificationSeverity.CRITICAL)
    ]
    
    min_severity = NotificationSeverity.ERROR
    print(f"   Minimum severity filter: {min_severity.value}")
    print()
    
    for title, severity in test_notifications:
        notification = Notification(
            id=f"filter_{severity.value}",
            title=title,
            message="Test message",
            severity=severity
        )
        
        should_send = dispatcher.filter_by_severity(notification, min_severity)
        status = "✓ Send" if should_send else "✗ Skip"
        print(f"   {status}: {severity.value.upper()} - {title}")
    
    print()
    print("="*70)
    print("Integration example complete!")
    print("="*70)
    print()
    print("Key integration points demonstrated:")
    print("  • Detecting critical failures (kernel panics)")
    print("  • Sending multi-channel notifications")
    print("  • Including test context and metadata")
    print("  • Severity-based routing")
    print("  • Performance regression alerts")
    print("  • Severity filtering")
    print()
    print("Note: Actual delivery requires channel configuration in .env")


if __name__ == "__main__":
    simulate_test_execution_with_notifications()
