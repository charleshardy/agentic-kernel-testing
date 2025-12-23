"""
Mock Test Runner for testing and development.

This runner simulates test execution without requiring actual virtualization.
"""

import time
import random
from typing import Dict, Optional
from datetime import datetime

from ai_generator.models import TestCase, TestType, HardwareConfig, TestStatus, Environment
from execution.runner_factory import BaseTestRunner


class MockTestRunner(BaseTestRunner):
    """Mock test runner that simulates test execution."""
    
    def __init__(self, environment: Environment):
        """Initialize mock runner."""
        super().__init__(environment)
        self.execution_count = 0
    
    def execute(self, test_case: TestCase, timeout: Optional[int] = None,
                timeout_manager=None) -> Dict:
        """Simulate test execution.
        
        Args:
            test_case: Test case to execute
            timeout: Timeout in seconds
            timeout_manager: Timeout manager (unused)
            
        Returns:
            Mock execution results
        """
        self.execution_count += 1
        
        # Simulate execution time
        execution_time = random.uniform(0.5, 3.0)
        time.sleep(execution_time)
        
        # Simulate different outcomes based on test content
        test_content = f"{test_case.name} {test_case.description}".lower()
        
        # Determine outcome based on test characteristics
        if "error" in test_content or "fail" in test_content:
            # Tests with "error" or "fail" in name/description have higher failure rate
            success_rate = 0.3
        elif "timeout" in test_content:
            # Simulate timeout
            return {
                'status': TestStatus.TIMEOUT,
                'execution_time': execution_time,
                'output': 'Test execution timed out',
                'error': 'Timeout after simulated execution',
                'exit_code': None
            }
        elif test_case.test_type == TestType.PERFORMANCE:
            # Performance tests have moderate success rate
            success_rate = 0.8
        elif test_case.test_type == TestType.SECURITY:
            # Security tests may find issues
            success_rate = 0.7
        else:
            # Most tests should pass
            success_rate = 0.9
        
        # Random outcome based on success rate
        if random.random() < success_rate:
            status = TestStatus.PASSED
            output = f"Mock test {test_case.name} executed successfully"
            error = None
            exit_code = 0
        else:
            status = TestStatus.FAILED
            output = f"Mock test {test_case.name} failed during execution"
            error = f"Simulated failure in {test_case.target_subsystem}"
            exit_code = 1
        
        return {
            'status': status,
            'execution_time': execution_time,
            'output': output,
            'error': error,
            'exit_code': exit_code,
            'mock_execution': True,
            'execution_count': self.execution_count
        }
    
    def cleanup(self) -> None:
        """Clean up mock runner resources."""
        # Nothing to clean up for mock runner
        pass
    
    def supports_test_type(self, test_type: TestType) -> bool:
        """Mock runner supports all test types."""
        return True
    
    def supports_hardware(self, hardware_config: HardwareConfig) -> bool:
        """Mock runner supports all hardware configurations."""
        return True