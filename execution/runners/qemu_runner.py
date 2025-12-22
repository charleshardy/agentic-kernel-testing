"""QEMU-based test runner for VM-based testing.

This module provides functionality for:
- Test execution in QEMU virtual machines for kernel testing
- Kernel image loading and VM boot logic
- Test execution inside QEMU VMs with console interaction
- Artifact collection from VM environments
"""

import os
import time
import tempfile
import shutil
import subprocess
import threading
import socket
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
import json

from ai_generator.models import (
    TestCase, TestType, TestStatus, Environment, HardwareConfig,
    ArtifactBundle, FailureInfo, CoverageData
)
from execution.runner_factory import BaseTestRunner
from execution.artifact_collector import get_artifact_collector
from execution.performance_monitor import get_performance_monitor


class QEMUTestRunner(BaseTestRunner):
    """Test runner that executes tests in QEMU virtual machines."""
    
    def __init__(self, environment: Environment):
        """Initialize the QEMU test runner.
        
        Args:
            environment: The environment configuration
        """
        super().__init__(environment)
        self.qemu_process = None
        self.temp_dir = None
        self.console_output = []
        self.console_thread = None
        self.monitor_socket = None
        self.serial_socket = None
        
        # QEMU configuration
        self.qemu_binary = self._get_qemu_binary()
        self.kernel_image = None
        self.initrd_image = None
        self.disk_image = None
    
    def _get_qemu_binary(self) -> str:
        """Get the appropriate QEMU binary for the target architecture.
        
        Returns:
            Path to QEMU binary
        """
        arch = self.environment.config.architecture
        
        qemu_binaries = {
            "x86_64": "qemu-system-x86_64",
            "arm64": "qemu-system-aarch64", 
            "arm": "qemu-system-arm",
            "riscv64": "qemu-system-riscv64"
        }
        
        binary = qemu_binaries.get(arch, "qemu-system-x86_64")
        
        # Check if binary exists
        if shutil.which(binary):
            return binary
        else:
            # Fallback to generic qemu if specific arch not found
            return "qemu-system-x86_64"
    
    def execute(self, test_case: TestCase, timeout: Optional[int] = None,
                timeout_manager=None) -> Dict[str, Any]:
        """Execute a test case in a QEMU virtual machine.
        
        Args:
            test_case: The test case to execute
            timeout: Optional timeout in seconds
            timeout_manager: Optional timeout manager for monitoring
            
        Returns:
            Dictionary containing execution results
        """
        if timeout is None:
            timeout = test_case.execution_time_estimate or 600  # 10 minute default for VM tests
        
        start_time = time.time()
        
        # Start performance monitoring
        performance_monitor = get_performance_monitor()
        performance_monitor.start_monitoring(test_case.id)
        
        try:
            # Create temporary directory for VM files
            self.temp_dir = tempfile.mkdtemp(prefix=f"qemu_test_{test_case.id}_")
            
            # Prepare VM environment
            self._prepare_vm_environment(test_case)
            
            # Boot VM with kernel
            self._boot_vm(test_case)
            
            # Register with timeout manager if provided
            if timeout_manager:
                timeout_manager.add_monitor(
                    test_id=test_case.id,
                    timeout_seconds=timeout,
                    process_id=self.qemu_process.pid if self.qemu_process else None,
                    callback=lambda tid, reason: self._handle_timeout_callback(tid, reason)
                )
            
            # Add QEMU process to performance monitoring
            if self.qemu_process:
                performance_monitor.add_process(self.qemu_process.pid)
            
            # Execute test in VM
            result = self._execute_test_in_vm(test_case, timeout)
            
            # Remove from timeout manager if registered
            if timeout_manager:
                timeout_manager.remove_monitor(test_case.id)
            
            # Stop performance monitoring and get metrics
            performance_metrics = performance_monitor.stop_monitoring()
            
            # Capture artifacts from VM
            artifacts = self._capture_vm_artifacts(test_case.id)
            
            # Store artifacts using artifact collector
            collector = get_artifact_collector()
            from ai_generator.models import TestResult
            temp_result = TestResult(
                test_id=test_case.id,
                status=TestStatus.PASSED,  # Temporary status
                execution_time=execution_time,
                environment=self.environment,
                artifacts=artifacts
            )
            stored_artifacts = collector.collect_artifacts(temp_result)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Analyze results
            status, failure_info = self._analyze_vm_result(result, timeout, execution_time)
            
            # Add performance metrics to artifacts metadata
            if performance_metrics:
                stored_artifacts.metadata['performance_metrics'] = performance_metrics.to_dict()
            
            return {
                'status': status,
                'stdout': result.get('stdout', ''),
                'stderr': result.get('stderr', ''),
                'exit_code': result.get('exit_code', -1),
                'execution_time': execution_time,
                'artifacts': stored_artifacts,
                'failure_info': failure_info
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Stop performance monitoring
            try:
                performance_monitor = get_performance_monitor()
                performance_monitor.stop_monitoring()
            except:
                pass
            
            failure_info = FailureInfo(
                error_message=f"QEMU execution error: {str(e)}",
                stack_trace=None,
                exit_code=None,
                kernel_panic=False,
                timeout_occurred=False
            )
            
            return {
                'status': TestStatus.ERROR,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1,
                'execution_time': execution_time,
                'artifacts': ArtifactBundle(),
                'failure_info': failure_info
            }
        
        finally:
            self.cleanup()
    
    def _handle_timeout_callback(self, test_id: str, reason: str):
        """Handle timeout callbacks from the timeout manager.
        
        Args:
            test_id: Test ID that timed out
            reason: Reason for the callback
        """
        if reason == "timeout_exceeded" and self.qemu_process:
            try:
                # Send shutdown command to QEMU monitor
                self._send_monitor_command("quit")
                
                # If that doesn't work, force kill
                if self.qemu_process.poll() is None:
                    self.qemu_process.terminate()
                    time.sleep(2)
                    if self.qemu_process.poll() is None:
                        self.qemu_process.kill()
                
                print(f"QEMU process for test {test_id} terminated due to timeout")
            except Exception as e:
                print(f"Error terminating QEMU process for test {test_id}: {e}")
        elif reason.startswith("timeout_warning:"):
            print(f"Timeout warning for test {test_id}: {reason}")
    
    def _prepare_vm_environment(self, test_case: TestCase):
        """Prepare the VM environment including kernel and test files.
        
        Args:
            test_case: The test case to prepare for
        """
        # Create test script
        test_script_path = Path(self.temp_dir) / "test_script.sh"
        self._create_test_script(test_case, test_script_path)
        
        # Prepare kernel image (use default if not specified)
        self.kernel_image = self._get_kernel_image(test_case)
        
        # Create initrd with test script
        self.initrd_image = self._create_initrd_with_test(test_script_path)
        
        # Create disk image for artifacts
        self.disk_image = self._create_disk_image()
    
    def _create_test_script(self, test_case: TestCase, script_path: Path):
        """Create the test script to run inside the VM.
        
        Args:
            test_case: The test case
            script_path: Path where to save the script
        """
        script_content = f"""#!/bin/bash

# Test execution script for QEMU VM
echo "=== QEMU VM Test Execution Started ==="
echo "Test ID: {test_case.id}"
echo "Test Name: {test_case.name}"
echo "Test Type: {test_case.test_type.value}"
echo "Target Subsystem: {test_case.target_subsystem}"
echo "Start Time: $(date)"
echo "Kernel Version: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "================================"

# Set up environment
export TEST_ID="{test_case.id}"
export TEST_NAME="{test_case.name}"
export TEST_TYPE="{test_case.test_type.value}"
export TARGET_SUBSYSTEM="{test_case.target_subsystem}"

# Create output directories
mkdir -p /tmp/artifacts
mkdir -p /tmp/logs

# Redirect output to log file
exec > >(tee /tmp/logs/execution.log) 2>&1

echo "VM environment setup complete"

# Mount disk for artifacts if available
if [ -e /dev/vdb ]; then
    mkdir -p /mnt/artifacts
    mount /dev/vdb /mnt/artifacts 2>/dev/null || echo "Could not mount artifact disk"
fi

# Execute the actual test script
echo "=== Executing Test Script ==="
cd /tmp

{test_case.test_script}

# Capture exit code
TEST_EXIT_CODE=$?

echo "=== Test Execution Completed ==="
echo "Exit Code: $TEST_EXIT_CODE"
echo "End Time: $(date)"

# Copy artifacts to mounted disk if available
if mountpoint -q /mnt/artifacts; then
    cp -r /tmp/logs /mnt/artifacts/ 2>/dev/null || true
    cp -r /tmp/artifacts/* /mnt/artifacts/ 2>/dev/null || true
    sync
    umount /mnt/artifacts 2>/dev/null || true
fi

# Signal completion and shutdown
echo "TEST_COMPLETED_EXIT_CODE_$TEST_EXIT_CODE"
echo "Shutting down VM..."
poweroff -f

exit $TEST_EXIT_CODE
"""
        
        script_path.write_text(script_content)
        script_path.chmod(0o755)
    
    def _get_kernel_image(self, test_case: TestCase) -> str:
        """Get the kernel image to boot.
        
        Args:
            test_case: The test case (may specify kernel requirements)
            
        Returns:
            Path to kernel image
        """
        # Check if test case specifies a kernel
        if (test_case.metadata and 
            'kernel_image' in test_case.metadata):
            kernel_path = test_case.metadata['kernel_image']
            if os.path.exists(kernel_path):
                return kernel_path
        
        # Look for default kernel images in common locations
        arch = self.environment.config.architecture
        
        kernel_locations = [
            f"/boot/vmlinuz-$(uname -r)",
            f"/usr/lib/modules/$(uname -r)/vmlinuz",
            f"/boot/vmlinuz",
            f"/usr/share/qemu/kernels/vmlinuz-{arch}",
            f"/usr/share/kernels/vmlinuz-{arch}"
        ]
        
        for location in kernel_locations:
            # Expand shell variables
            expanded = os.path.expandvars(location)
            if os.path.exists(expanded):
                return expanded
        
        # If no kernel found, we'll boot without kernel (use QEMU's built-in)
        return None
    
    def _create_initrd_with_test(self, test_script_path: Path) -> str:
        """Create an initrd image containing the test script.
        
        Args:
            test_script_path: Path to the test script
            
        Returns:
            Path to created initrd image
        """
        initrd_dir = Path(self.temp_dir) / "initrd"
        initrd_dir.mkdir()
        
        # Create basic directory structure
        (initrd_dir / "bin").mkdir()
        (initrd_dir / "sbin").mkdir()
        (initrd_dir / "etc").mkdir()
        (initrd_dir / "proc").mkdir()
        (initrd_dir / "sys").mkdir()
        (initrd_dir / "dev").mkdir()
        (initrd_dir / "tmp").mkdir()
        
        # Copy test script
        shutil.copy2(test_script_path, initrd_dir / "init")
        (initrd_dir / "init").chmod(0o755)
        
        # Create initrd archive
        initrd_path = Path(self.temp_dir) / "initrd.cpio.gz"
        
        try:
            # Create cpio archive
            subprocess.run([
                "sh", "-c", 
                f"cd {initrd_dir} && find . | cpio -o -H newc | gzip > {initrd_path}"
            ], check=True, capture_output=True)
            
            return str(initrd_path)
        except subprocess.CalledProcessError:
            # Fallback: create simple initrd with just the script
            with open(initrd_path, 'wb') as f:
                # Simple initrd with just the test script
                subprocess.run([
                    "sh", "-c",
                    f"echo '{test_script_path.read_text()}' | gzip"
                ], stdout=f, check=True)
            
            return str(initrd_path)
    
    def _create_disk_image(self) -> str:
        """Create a disk image for artifact storage.
        
        Returns:
            Path to created disk image
        """
        disk_path = Path(self.temp_dir) / "artifacts.img"
        
        try:
            # Create a small disk image (100MB)
            subprocess.run([
                "qemu-img", "create", "-f", "raw", str(disk_path), "100M"
            ], check=True, capture_output=True)
            
            # Format it with ext4
            subprocess.run([
                "mkfs.ext4", "-F", str(disk_path)
            ], check=True, capture_output=True)
            
            return str(disk_path)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If qemu-img or mkfs.ext4 not available, return None
            return None
    
    def _boot_vm(self, test_case: TestCase):
        """Boot the QEMU virtual machine.
        
        Args:
            test_case: The test case being executed
        """
        # Prepare QEMU command
        qemu_cmd = [self.qemu_binary]
        
        # Basic VM configuration
        memory_mb = self.environment.config.memory_mb
        qemu_cmd.extend([
            "-m", str(memory_mb),
            "-smp", "1",  # Single CPU for simplicity
            "-nographic",  # No graphics
            "-serial", "stdio",  # Serial console to stdout
        ])
        
        # Architecture-specific settings
        arch = self.environment.config.architecture
        if arch == "x86_64":
            qemu_cmd.extend(["-machine", "pc"])
        elif arch == "arm64":
            qemu_cmd.extend(["-machine", "virt", "-cpu", "cortex-a57"])
        elif arch == "arm":
            qemu_cmd.extend(["-machine", "virt", "-cpu", "cortex-a15"])
        elif arch == "riscv64":
            qemu_cmd.extend(["-machine", "virt"])
        
        # Add kernel if available
        if self.kernel_image:
            qemu_cmd.extend(["-kernel", self.kernel_image])
        
        # Add initrd if available
        if self.initrd_image:
            qemu_cmd.extend(["-initrd", self.initrd_image])
        
        # Add disk for artifacts if available
        if self.disk_image:
            qemu_cmd.extend([
                "-drive", f"file={self.disk_image},format=raw,if=virtio"
            ])
        
        # Kernel command line
        kernel_cmdline = [
            "console=ttyS0",
            "panic=1",
            "init=/init",
            "rw"
        ]
        qemu_cmd.extend(["-append", " ".join(kernel_cmdline)])
        
        # Disable default devices to speed up boot
        qemu_cmd.extend([
            "-nodefaults",
            "-no-user-config"
        ])
        
        # Start QEMU process
        try:
            self.qemu_process = subprocess.Popen(
                qemu_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Start console monitoring thread
            self.console_thread = threading.Thread(
                target=self._monitor_console,
                daemon=True
            )
            self.console_thread.start()
            
        except Exception as e:
            raise RuntimeError(f"Failed to start QEMU: {e}")
    
    def _monitor_console(self):
        """Monitor QEMU console output in a separate thread."""
        if not self.qemu_process:
            return
        
        try:
            while self.qemu_process.poll() is None:
                line = self.qemu_process.stdout.readline()
                if line:
                    self.console_output.append(line.strip())
                    # Print to our stdout for debugging
                    print(f"QEMU: {line.strip()}")
                else:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Console monitoring error: {e}")
    
    def _execute_test_in_vm(self, test_case: TestCase, timeout: int) -> Dict[str, Any]:
        """Execute the test inside the VM and wait for completion.
        
        Args:
            test_case: The test case being executed
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        completion_marker = "TEST_COMPLETED_EXIT_CODE_"
        
        # Wait for VM to boot and test to complete
        while time.time() - start_time < timeout:
            if self.qemu_process.poll() is not None:
                # Process has terminated
                break
            
            # Check console output for completion marker
            console_text = "\n".join(self.console_output)
            if completion_marker in console_text:
                # Test completed, extract exit code
                for line in self.console_output:
                    if completion_marker in line:
                        try:
                            exit_code = int(line.split(completion_marker)[1])
                            return {
                                'stdout': console_text,
                                'stderr': '',
                                'exit_code': exit_code,
                                'timeout_occurred': False
                            }
                        except (IndexError, ValueError):
                            pass
                break
            
            time.sleep(1)
        
        # Check if we timed out
        if time.time() - start_time >= timeout:
            # Timeout occurred
            self._send_monitor_command("quit")
            return {
                'stdout': "\n".join(self.console_output),
                'stderr': f"Test timed out after {timeout} seconds",
                'exit_code': 124,
                'timeout_occurred': True
            }
        
        # Process terminated without completion marker
        return_code = self.qemu_process.returncode if self.qemu_process else -1
        stderr_output = ""
        
        if self.qemu_process and self.qemu_process.stderr:
            try:
                stderr_output = self.qemu_process.stderr.read()
            except:
                pass
        
        return {
            'stdout': "\n".join(self.console_output),
            'stderr': stderr_output,
            'exit_code': return_code,
            'timeout_occurred': False
        }
    
    def _send_monitor_command(self, command: str):
        """Send a command to the QEMU monitor.
        
        Args:
            command: Monitor command to send
        """
        if self.qemu_process and self.qemu_process.stdin:
            try:
                # Send Ctrl+A, C to enter monitor mode, then command
                self.qemu_process.stdin.write(f"\x01c{command}\n")
                self.qemu_process.stdin.flush()
            except Exception as e:
                print(f"Error sending monitor command: {e}")
    
    def _capture_vm_artifacts(self, test_id: str) -> ArtifactBundle:
        """Capture artifacts from the VM execution.
        
        Args:
            test_id: The test ID for artifact naming
            
        Returns:
            ArtifactBundle containing captured artifacts
        """
        artifacts = ArtifactBundle()
        
        try:
            # Save console output as log
            console_log_path = Path(self.temp_dir) / "console.log"
            console_log_path.write_text("\n".join(self.console_output))
            artifacts.logs.append(str(console_log_path))
            
            # Try to mount and extract artifacts from disk image
            if self.disk_image and os.path.exists(self.disk_image):
                artifacts_dir = Path(self.temp_dir) / "extracted_artifacts"
                artifacts_dir.mkdir(exist_ok=True)
                
                try:
                    # Mount the disk image
                    mount_point = artifacts_dir / "mount"
                    mount_point.mkdir(exist_ok=True)
                    
                    # Try to mount (requires root privileges)
                    mount_result = subprocess.run([
                        "sudo", "mount", "-o", "loop", str(self.disk_image), str(mount_point)
                    ], capture_output=True)
                    
                    if mount_result.returncode == 0:
                        # Copy artifacts
                        for item in mount_point.rglob("*"):
                            if item.is_file():
                                relative_path = str(item.relative_to(mount_point))
                                dest_path = artifacts_dir / relative_path
                                dest_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(item, dest_path)
                                
                                if "log" in relative_path.lower():
                                    artifacts.logs.append(str(dest_path))
                                elif any(ext in relative_path.lower() for ext in [".core", ".dump"]):
                                    artifacts.core_dumps.append(str(dest_path))
                                elif any(ext in relative_path.lower() for ext in [".trace", ".strace"]):
                                    artifacts.traces.append(str(dest_path))
                        
                        # Unmount
                        subprocess.run(["sudo", "umount", str(mount_point)], capture_output=True)
                
                except Exception as e:
                    artifacts.metadata["artifact_extraction_error"] = str(e)
            
            # Add VM metadata
            artifacts.metadata.update({
                "vm_architecture": self.environment.config.architecture,
                "vm_memory_mb": self.environment.config.memory_mb,
                "qemu_binary": self.qemu_binary,
                "kernel_image": self.kernel_image,
                "console_lines": len(self.console_output)
            })
            
        except Exception as e:
            artifacts.metadata["artifact_capture_error"] = str(e)
        
        return artifacts
    
    def _analyze_vm_result(self, result: Dict[str, Any], timeout: int, execution_time: float) -> tuple:
        """Analyze VM execution result and determine status.
        
        Args:
            result: Execution result dictionary
            timeout: Configured timeout
            execution_time: Actual execution time
            
        Returns:
            Tuple of (TestStatus, Optional[FailureInfo])
        """
        exit_code = result.get('exit_code', -1)
        stdout = result.get('stdout', '')
        stderr = result.get('stderr', '')
        timeout_occurred = result.get('timeout_occurred', False)
        
        # Check for timeout
        if timeout_occurred or execution_time >= timeout:
            failure_info = FailureInfo(
                error_message=f"VM test timed out after {timeout} seconds",
                stack_trace=stderr if stderr else None,
                exit_code=exit_code,
                kernel_panic=False,
                timeout_occurred=True
            )
            return TestStatus.TIMEOUT, failure_info
        
        # Check for kernel panic or VM crashes
        crash_indicators = [
            "kernel panic", "oops", "segmentation fault", "general protection fault",
            "invalid opcode", "stack overflow", "out of memory", "call trace"
        ]
        
        output_text = (stdout + stderr).lower()
        kernel_panic = any(indicator in output_text for indicator in crash_indicators)
        
        if kernel_panic:
            failure_info = FailureInfo(
                error_message="Kernel panic or system crash detected in VM",
                stack_trace=stdout,  # Console output contains kernel traces
                exit_code=exit_code,
                kernel_panic=True,
                timeout_occurred=False
            )
            return TestStatus.FAILED, failure_info
        
        # Check if VM failed to boot
        if "failed to boot" in output_text or "boot failed" in output_text:
            failure_info = FailureInfo(
                error_message="VM failed to boot properly",
                stack_trace=stderr if stderr else stdout,
                exit_code=exit_code,
                kernel_panic=False,
                timeout_occurred=False
            )
            return TestStatus.ERROR, failure_info
        
        # Check exit code
        if exit_code == 0:
            return TestStatus.PASSED, None
        else:
            failure_info = FailureInfo(
                error_message=f"VM test failed with exit code {exit_code}",
                stack_trace=stderr if stderr else None,
                exit_code=exit_code,
                kernel_panic=False,
                timeout_occurred=False
            )
            return TestStatus.FAILED, failure_info
    
    def cleanup(self) -> None:
        """Clean up QEMU process and temporary resources."""
        # Stop console monitoring thread
        if self.console_thread and self.console_thread.is_alive():
            # Thread is daemon, so it will stop when main thread stops
            pass
        
        # Terminate QEMU process
        if self.qemu_process:
            try:
                if self.qemu_process.poll() is None:
                    # Send quit command first
                    self._send_monitor_command("quit")
                    time.sleep(2)
                    
                    # If still running, terminate
                    if self.qemu_process.poll() is None:
                        self.qemu_process.terminate()
                        time.sleep(2)
                        
                        # If still running, kill
                        if self.qemu_process.poll() is None:
                            self.qemu_process.kill()
                
                # Close pipes
                if self.qemu_process.stdin:
                    self.qemu_process.stdin.close()
                if self.qemu_process.stdout:
                    self.qemu_process.stdout.close()
                if self.qemu_process.stderr:
                    self.qemu_process.stderr.close()
                    
            except Exception as e:
                print(f"Warning: Error cleaning up QEMU process: {e}")
            finally:
                self.qemu_process = None
        
        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Could not remove temp directory {self.temp_dir}: {e}")
            finally:
                self.temp_dir = None
        
        # Reset state
        self.console_output = []
        self.console_thread = None
        self.kernel_image = None
        self.initrd_image = None
        self.disk_image = None
    
    def supports_test_type(self, test_type: TestType) -> bool:
        """Check if this runner supports the given test type.
        
        Args:
            test_type: The test type to check
            
        Returns:
            True if the runner supports this test type
        """
        # QEMU runner supports all test types, especially kernel-level tests
        return True
    
    def supports_hardware(self, hardware_config: HardwareConfig) -> bool:
        """Check if this runner supports the given hardware configuration.
        
        Args:
            hardware_config: The hardware configuration to check
            
        Returns:
            True if the runner supports this hardware configuration
        """
        # QEMU runner only supports virtual environments
        if not hardware_config.is_virtual:
            return False
        
        # Check architecture support
        supported_architectures = {"x86_64", "arm64", "arm", "riscv64"}
        
        if hardware_config.architecture not in supported_architectures:
            return False
        
        # Check memory requirements (QEMU can handle large amounts)
        if hardware_config.memory_mb > 32768:  # 32GB limit
            return False
        
        # QEMU can emulate various peripherals
        return True
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()