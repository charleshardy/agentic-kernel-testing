"""Docker-based test runner for isolated test execution.

This module provides functionality for:
- Test execution in Docker containers for isolation
- Result capture (stdout, stderr, exit code, timing)
- Container lifecycle management
- Artifact collection from containers
"""

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False

import time
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime

from ai_generator.models import (
    TestCase, TestType, TestStatus, Environment, HardwareConfig,
    ArtifactBundle, FailureInfo, CoverageData
)
from execution.runner_factory import BaseTestRunner
from execution.artifact_collector import get_artifact_collector
from execution.performance_monitor import get_performance_monitor


class DockerTestRunner(BaseTestRunner):
    """Test runner that executes tests in Docker containers."""
    
    def __init__(self, environment: Environment):
        """Initialize the Docker test runner.
        
        Args:
            environment: The environment configuration
        """
        super().__init__(environment)
        if not DOCKER_AVAILABLE:
            raise ImportError("Docker library not available. Install with: pip install docker")
        self.docker_client = docker.from_env()
        self.container = None
        self.temp_dir = None
    
    def execute(self, test_case: TestCase, timeout: Optional[int] = None,
                timeout_manager=None) -> Dict[str, Any]:
        """Execute a test case in a Docker container.
        
        Args:
            test_case: The test case to execute
            timeout: Optional timeout in seconds
            timeout_manager: Optional timeout manager for monitoring
            
        Returns:
            Dictionary containing execution results with keys:
            - status: TestStatus
            - stdout: str
            - stderr: str
            - exit_code: int
            - execution_time: float
            - artifacts: ArtifactBundle
            - failure_info: Optional[FailureInfo]
        """
        if timeout is None:
            timeout = test_case.execution_time_estimate or 300  # 5 minute default
        
        start_time = time.time()
        
        # Start performance monitoring
        performance_monitor = get_performance_monitor()
        performance_monitor.start_monitoring(test_case.id)
        
        try:
            # Create temporary directory for test files
            self.temp_dir = tempfile.mkdtemp(prefix=f"test_{test_case.id}_")
            
            # Prepare test script
            script_path = self._prepare_test_script(test_case)
            
            # Create and start container
            self.container = self._create_container(test_case, script_path)
            
            # Register with timeout manager if provided
            if timeout_manager:
                timeout_manager.add_monitor(
                    test_id=test_case.id,
                    timeout_seconds=timeout,
                    container_id=self.container.id,
                    callback=lambda tid, reason: self._handle_timeout_callback(tid, reason)
                )
            
            # Add container process to performance monitoring
            try:
                # Get container's main process PID
                container_info = self.container.attrs
                if 'State' in container_info and 'Pid' in container_info['State']:
                    container_pid = container_info['State']['Pid']
                    if container_pid > 0:
                        performance_monitor.add_process(container_pid)
            except Exception as e:
                print(f"Warning: Could not add container process to monitoring: {e}")
            
            # Execute the test
            result = self._execute_in_container(timeout)
            
            # Remove from timeout manager if registered
            if timeout_manager:
                timeout_manager.remove_monitor(test_case.id)
            
            # Stop performance monitoring and get metrics
            performance_metrics = performance_monitor.stop_monitoring()
            
            # Capture artifacts
            artifacts = self._capture_artifacts(test_case.id)
            
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
            
            # Determine test status and create failure info if needed
            status, failure_info = self._analyze_result(result, timeout, execution_time)
            
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
                error_message=f"Docker execution error: {str(e)}",
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
        if reason == "timeout_exceeded" and self.container:
            try:
                # Force kill the container
                self.container.kill()
                print(f"Container for test {test_id} killed due to timeout")
            except Exception as e:
                print(f"Error killing container for test {test_id}: {e}")
        elif reason.startswith("timeout_warning:"):
            print(f"Timeout warning for test {test_id}: {reason}")
    
    def _prepare_test_script(self, test_case: TestCase) -> Path:
        """Prepare the test script file.
        
        Args:
            test_case: The test case containing the script
            
        Returns:
            Path to the prepared script file
        """
        script_path = Path(self.temp_dir) / "test_script.sh"
        
        # Create a comprehensive test script
        script_content = f"""#!/bin/bash
set -e

# Test metadata
echo "=== Test Execution Started ==="
echo "Test ID: {test_case.id}"
echo "Test Name: {test_case.name}"
echo "Test Type: {test_case.test_type.value}"
echo "Target Subsystem: {test_case.target_subsystem}"
echo "Start Time: $(date)"
echo "================================"

# Change to test directory
cd /test

# Set up environment variables
export TEST_ID="{test_case.id}"
export TEST_NAME="{test_case.name}"
export TEST_TYPE="{test_case.test_type.value}"
export TARGET_SUBSYSTEM="{test_case.target_subsystem}"

# Create output directories
mkdir -p /test/artifacts
mkdir -p /test/logs

# Redirect all output to log file as well
exec > >(tee /test/logs/execution.log) 2>&1

echo "Environment setup complete"

# Execute the actual test script
echo "=== Executing Test Script ==="
{test_case.test_script}

# Capture exit code
TEST_EXIT_CODE=$?

echo "=== Test Execution Completed ==="
echo "Exit Code: $TEST_EXIT_CODE"
echo "End Time: $(date)"

# Exit with the test's exit code
exit $TEST_EXIT_CODE
"""
        
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        return script_path
    
    def _create_container(self, test_case: TestCase, script_path: Path) -> Any:
        """Create and configure a Docker container for test execution.
        
        Args:
            test_case: The test case to execute
            script_path: Path to the test script
            
        Returns:
            Docker container object
        """
        # Select appropriate base image based on test requirements
        image = self._select_base_image(test_case)
        
        # Configure container resources based on hardware requirements
        memory_limit = None
        cpu_limit = None
        
        if test_case.required_hardware:
            memory_limit = f"{test_case.required_hardware.memory_mb}m"
            # Docker CPU limit is in terms of CPU shares (1024 = 1 CPU)
            cpu_limit = 1024  # Default to 1 CPU equivalent
        
        # Create container with mounted test directory
        container = self.docker_client.containers.create(
            image=image,
            command=["/test/test_script.sh"],
            volumes={
                str(self.temp_dir): {'bind': '/test', 'mode': 'rw'}
            },
            working_dir='/test',
            mem_limit=memory_limit,
            cpu_shares=cpu_limit,
            network_disabled=False,  # Allow network access for tests that need it
            detach=True,
            remove=False,  # Keep container for artifact collection
            name=f"test_{test_case.id}_{int(time.time())}"
        )
        
        return container
    
    def _select_base_image(self, test_case: TestCase) -> str:
        """Select appropriate Docker base image for the test.
        
        Args:
            test_case: The test case to analyze
            
        Returns:
            Docker image name
        """
        # Default to Ubuntu for most tests
        default_image = "ubuntu:22.04"
        
        # Check if test requires specific tools or environments
        test_content = f"{test_case.description} {test_case.test_script}".lower()
        
        # Kernel testing might need specific images
        if any(keyword in test_content for keyword in ["kernel", "module", "driver"]):
            return "ubuntu:22.04"  # Use Ubuntu with kernel headers available
        
        # Python tests
        if any(keyword in test_content for keyword in ["python", "pytest", "pip"]):
            return "python:3.10-slim"
        
        # C/C++ compilation tests
        if any(keyword in test_content for keyword in ["gcc", "make", "cmake", "compile"]):
            return "gcc:latest"
        
        # Network tests
        if any(keyword in test_content for keyword in ["network", "socket", "tcp", "udp"]):
            return "ubuntu:22.04"
        
        return default_image
    
    def _execute_in_container(self, timeout: int) -> Dict[str, Any]:
        """Execute the test in the container and capture results.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with stdout, stderr, exit_code
        """
        # Start the container
        self.container.start()
        
        try:
            # Wait for container to complete with timeout
            result = self.container.wait(timeout=timeout)
            exit_code = result['StatusCode']
            
            # Get logs (stdout and stderr combined)
            logs = self.container.logs(stdout=True, stderr=True).decode('utf-8', errors='ignore')
            
            # Try to separate stdout and stderr if possible
            # Docker logs combine them, so we'll put everything in stdout
            return {
                'stdout': logs,
                'stderr': '',
                'exit_code': exit_code,
                'timeout_occurred': False
            }
            
        except docker.errors.APIError as e:
            if "timeout" in str(e).lower():
                # Container timed out, kill it
                try:
                    self.container.kill()
                except:
                    pass
                
                # Get partial logs
                try:
                    logs = self.container.logs(stdout=True, stderr=True).decode('utf-8', errors='ignore')
                except:
                    logs = "Container timed out and logs could not be retrieved"
                
                return {
                    'stdout': logs,
                    'stderr': f"Test timed out after {timeout} seconds",
                    'exit_code': 124,  # Standard timeout exit code
                    'timeout_occurred': True
                }
            else:
                raise
    
    def _capture_artifacts(self, test_id: str) -> ArtifactBundle:
        """Capture artifacts from the container.
        
        Args:
            test_id: The test ID for artifact naming
            
        Returns:
            ArtifactBundle containing captured artifacts
        """
        artifacts = ArtifactBundle()
        
        if not self.container:
            return artifacts
        
        try:
            # Create artifacts directory
            artifacts_dir = Path(self.temp_dir) / "captured_artifacts"
            artifacts_dir.mkdir(exist_ok=True)
            
            # Copy artifacts from container
            artifact_paths = ["/test/artifacts", "/test/logs"]
            
            for container_path in artifact_paths:
                try:
                    # Get tar archive from container
                    tar_stream, _ = self.container.get_archive(container_path)
                    
                    # Extract to local directory
                    import tarfile
                    import io
                    
                    tar_data = b''.join(tar_stream)
                    tar_file = tarfile.open(fileobj=io.BytesIO(tar_data))
                    tar_file.extractall(artifacts_dir)
                    tar_file.close()
                    
                except docker.errors.NotFound:
                    # Path doesn't exist in container, skip
                    continue
                except Exception as e:
                    # Log error but continue
                    print(f"Warning: Could not capture artifacts from {container_path}: {e}")
            
            # Collect artifact file paths
            if artifacts_dir.exists():
                for artifact_file in artifacts_dir.rglob("*"):
                    if artifact_file.is_file():
                        relative_path = str(artifact_file.relative_to(artifacts_dir))
                        
                        if "log" in relative_path.lower():
                            artifacts.logs.append(str(artifact_file))
                        elif any(ext in relative_path.lower() for ext in [".core", ".dump"]):
                            artifacts.core_dumps.append(str(artifact_file))
                        elif any(ext in relative_path.lower() for ext in [".trace", ".strace"]):
                            artifacts.traces.append(str(artifact_file))
                        else:
                            # Add to metadata for other files
                            if "other_files" not in artifacts.metadata:
                                artifacts.metadata["other_files"] = []
                            artifacts.metadata["other_files"].append(str(artifact_file))
            
        except Exception as e:
            # Log error but don't fail the test
            artifacts.metadata["artifact_capture_error"] = str(e)
        
        return artifacts
    
    def _analyze_result(self, result: Dict[str, Any], timeout: int, execution_time: float) -> tuple:
        """Analyze test execution result and determine status.
        
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
                error_message=f"Test timed out after {timeout} seconds",
                stack_trace=stderr if stderr else None,
                exit_code=exit_code,
                kernel_panic=False,
                timeout_occurred=True
            )
            return TestStatus.TIMEOUT, failure_info
        
        # Check for kernel panic or system crashes
        crash_indicators = [
            "kernel panic", "segmentation fault", "core dumped",
            "killed by signal", "abort", "assertion failed"
        ]
        
        output_text = (stdout + stderr).lower()
        kernel_panic = any(indicator in output_text for indicator in crash_indicators)
        
        if kernel_panic:
            failure_info = FailureInfo(
                error_message="System crash or kernel panic detected",
                stack_trace=stderr if stderr else stdout,
                exit_code=exit_code,
                kernel_panic=True,
                timeout_occurred=False
            )
            return TestStatus.FAILED, failure_info
        
        # Check exit code
        if exit_code == 0:
            return TestStatus.PASSED, None
        else:
            failure_info = FailureInfo(
                error_message=f"Test failed with exit code {exit_code}",
                stack_trace=stderr if stderr else None,
                exit_code=exit_code,
                kernel_panic=False,
                timeout_occurred=False
            )
            return TestStatus.FAILED, failure_info
    
    def cleanup(self) -> None:
        """Clean up container and temporary resources."""
        # Remove container if it exists
        if self.container:
            try:
                self.container.remove(force=True)
            except Exception as e:
                print(f"Warning: Could not remove container: {e}")
            finally:
                self.container = None
        
        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Could not remove temp directory {self.temp_dir}: {e}")
            finally:
                self.temp_dir = None
    
    def supports_test_type(self, test_type: TestType) -> bool:
        """Check if this runner supports the given test type.
        
        Args:
            test_type: The test type to check
            
        Returns:
            True if the runner supports this test type
        """
        # Docker runner supports most test types except those requiring bare metal
        supported_types = {
            TestType.UNIT,
            TestType.INTEGRATION,
            TestType.SECURITY,
            TestType.FUZZ
        }
        
        return test_type in supported_types
    
    def supports_hardware(self, hardware_config: HardwareConfig) -> bool:
        """Check if this runner supports the given hardware configuration.
        
        Args:
            hardware_config: The hardware configuration to check
            
        Returns:
            True if the runner supports this hardware configuration
        """
        # Docker runner only supports virtual environments
        if not hardware_config.is_virtual:
            return False
        
        # Check architecture support (Docker can emulate some architectures)
        supported_architectures = {"x86_64", "arm64", "arm"}
        
        if hardware_config.architecture not in supported_architectures:
            return False
        
        # Check memory requirements (Docker can limit memory)
        if hardware_config.memory_mb > 16384:  # 16GB limit for containers
            return False
        
        # Docker doesn't support complex peripheral configurations
        if hardware_config.peripherals and len(hardware_config.peripherals) > 2:
            return False
        
        return True
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()