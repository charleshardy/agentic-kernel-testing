"""Mock test runner for testing purposes when Docker is not available."""

import time
from typing import Dict, Optional, Any
from datetime import datetime

from ai_generator.models import (
    TestCase, TestType, TestStatus, Environment, HardwareConfig,
    ArtifactBundle, FailureInfo
)
from execution.runner_factory import BaseTestRunner


class MockTestRunner(BaseTestRunner):
    """Mock test runner that simulates test execution without external dependencies."""
    
    def __init__(self, environment: Environment):
        """Initialize the mock test runner.
        
        Args:
            environment: The environment configuration
        """
        super().__init__(environment)
        self.execution_count = 0
    
    def execute(self, test_case: TestCase, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute a test case by simulating the execution.
        
        Args:
            test_case: The test case to execute
            timeout: Optional timeout in seconds
            
        Returns:
            Dictionary containing simulated execution results
        """
        self.execution_count += 1
        start_time = time.time()
        
        # Simulate execution time
        execution_time = min(0.1, test_case.execution_time_estimate / 100.0)
        time.sleep(execution_time)
        
        # Simulate different outcomes based on test case properties
        if "fail" in test_case.name.lower() or "error" in test_case.description.lower():
            status = TestStatus.FAILED
            failure_info = FailureInfo(
                error_message="Simulated test failure",
                exit_code=1,
                kernel_panic=False,
                timeout_occurred=False
            )
        elif "timeout" in test_case.name.lower():
            status = TestStatus.TIMEOUT
            failure_info = FailureInfo(
                error_message="Simulated timeout",
                exit_code=124,
                kernel_panic=False,
                timeout_occurred=True
            )
        else:
            status = TestStatus.PASSED
            failure_info = None
        
        # Create mock artifacts
        artifacts = ArtifactBundle(
            logs=[f"/tmp/mock_log_{test_case.id}.log"],
            metadata={"mock_execution": True, "execution_count": self.execution_count}
        )
        
        return {
            'status': status,
            'stdout': f"Mock execution of test {test_case.id}",
            'stderr': "Mock stderr" if failure_info else "",
            'exit_code': failure_info.exit_code if failure_info else 0,
            'execution_time': time.time() - start_time,
            'artifacts': artifacts,
            'failure_info': failure_info
        }
    
    def cleanup(self) -> None:
        """Clean up mock resources (no-op for mock runner)."""
        pass
    
    def supports_test_type(self, test_type: TestType) -> bool:
        """Check if this runner supports the given test type.
        
        Args:
            test_type: The test type to check
            
        Returns:
            True for all test types (mock runner is flexible)
        """
        return True
    
    def supports_hardware(self, hardware_config: HardwareConfig) -> bool:
        """Check if this runner supports the given hardware configuration.
        
        Args:
            hardware_config: The hardware configuration to check
            
        Returns:
            True for all hardware configurations (mock runner is flexible)
        """
        return True