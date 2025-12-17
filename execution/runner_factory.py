"""Test runner factory for creating appropriate test runners based on test type and requirements.

This module provides functionality for:
- Factory pattern for different test runner types
- Runner selection based on test type and hardware requirements
- Environment type matching for optimal test execution
"""

from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
from enum import Enum

from ai_generator.models import TestCase, TestType, Environment, HardwareConfig


class RunnerType(str, Enum):
    """Types of test runners available."""
    DOCKER = "docker"
    QEMU = "qemu"
    PHYSICAL = "physical"
    CONTAINER = "container"


class BaseTestRunner(ABC):
    """Abstract base class for all test runners."""
    
    def __init__(self, environment: Environment):
        """Initialize the test runner with an environment.
        
        Args:
            environment: The environment to run tests in
        """
        self.environment = environment
    
    @abstractmethod
    def execute(self, test_case: TestCase, timeout: Optional[int] = None) -> Dict:
        """Execute a test case and return results.
        
        Args:
            test_case: The test case to execute
            timeout: Optional timeout in seconds
            
        Returns:
            Dictionary containing execution results
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources after test execution."""
        pass
    
    @abstractmethod
    def supports_test_type(self, test_type: TestType) -> bool:
        """Check if this runner supports the given test type.
        
        Args:
            test_type: The test type to check
            
        Returns:
            True if the runner supports this test type
        """
        pass
    
    @abstractmethod
    def supports_hardware(self, hardware_config: HardwareConfig) -> bool:
        """Check if this runner supports the given hardware configuration.
        
        Args:
            hardware_config: The hardware configuration to check
            
        Returns:
            True if the runner supports this hardware configuration
        """
        pass


class TestRunnerFactory:
    """Factory for creating appropriate test runners based on test requirements."""
    
    def __init__(self):
        """Initialize the factory with available runner types."""
        self._runners: Dict[RunnerType, Type[BaseTestRunner]] = {}
        self._register_default_runners()
    
    def _register_default_runners(self) -> None:
        """Register default runner implementations."""
        # Import here to avoid circular imports
        try:
            from execution.runners.docker_runner import DockerTestRunner, DOCKER_AVAILABLE
            if DOCKER_AVAILABLE:
                self._runners[RunnerType.DOCKER] = DockerTestRunner
        except ImportError:
            pass
        
        try:
            from execution.runners.qemu_runner import QEMUTestRunner
            self._runners[RunnerType.QEMU] = QEMUTestRunner
        except ImportError:
            pass
        
        try:
            from execution.runners.container_runner import ContainerTestRunner
            self._runners[RunnerType.CONTAINER] = ContainerTestRunner
        except ImportError:
            pass
        
        try:
            from execution.runners.physical_runner import PhysicalTestRunner
            self._runners[RunnerType.PHYSICAL] = PhysicalTestRunner
        except ImportError:
            pass
        
        # Always register mock runner for testing
        try:
            from execution.runners.mock_runner import MockTestRunner
            if not self._runners:  # Only use mock if no real runners available
                self._runners[RunnerType.DOCKER] = MockTestRunner
        except ImportError:
            pass
    
    def register_runner(self, runner_type: RunnerType, runner_class: Type[BaseTestRunner]) -> None:
        """Register a new runner type.
        
        Args:
            runner_type: The type identifier for the runner
            runner_class: The runner class implementation
        """
        if not issubclass(runner_class, BaseTestRunner):
            raise ValueError(f"Runner class must inherit from BaseTestRunner")
        
        self._runners[runner_type] = runner_class
    
    def create_runner(self, test_case: TestCase, environment: Environment) -> BaseTestRunner:
        """Create an appropriate test runner for the given test case and environment.
        
        Args:
            test_case: The test case to be executed
            environment: The environment to execute in
            
        Returns:
            An appropriate test runner instance
            
        Raises:
            ValueError: If no suitable runner is found
        """
        # Determine the best runner type based on test requirements
        runner_type = self._select_runner_type(test_case, environment)
        
        if runner_type not in self._runners:
            raise ValueError(f"No runner implementation available for type: {runner_type}")
        
        runner_class = self._runners[runner_type]
        return runner_class(environment)
    
    def _select_runner_type(self, test_case: TestCase, environment: Environment) -> RunnerType:
        """Select the most appropriate runner type for the test case and environment.
        
        Args:
            test_case: The test case to be executed
            environment: The environment to execute in
            
        Returns:
            The most appropriate runner type
            
        Raises:
            ValueError: If no suitable runner type is found
        """
        # Check if environment is virtual or physical
        if not environment.config.is_virtual:
            return RunnerType.PHYSICAL
        
        # For virtual environments, select based on test type and requirements
        if test_case.test_type == TestType.UNIT:
            # Unit tests prefer lightweight containers
            return RunnerType.DOCKER
        
        elif test_case.test_type == TestType.INTEGRATION:
            # Integration tests may need full VM environments
            if self._requires_full_vm(test_case):
                return RunnerType.QEMU
            else:
                return RunnerType.DOCKER
        
        elif test_case.test_type == TestType.PERFORMANCE:
            # Performance tests need dedicated resources
            return RunnerType.QEMU
        
        elif test_case.test_type == TestType.SECURITY:
            # Security tests need isolation
            return RunnerType.QEMU
        
        elif test_case.test_type == TestType.FUZZ:
            # Fuzz tests need isolation and crash handling
            return RunnerType.QEMU
        
        else:
            # Default to Docker for unknown test types
            return RunnerType.DOCKER
    
    def _requires_full_vm(self, test_case: TestCase) -> bool:
        """Determine if a test case requires a full virtual machine.
        
        Args:
            test_case: The test case to analyze
            
        Returns:
            True if the test requires a full VM environment
        """
        # Check for kernel-level testing indicators
        kernel_indicators = [
            "kernel", "driver", "module", "syscall", "interrupt",
            "memory_management", "scheduler", "filesystem", "network_stack"
        ]
        
        # Check test description and target subsystem
        test_content = f"{test_case.description} {test_case.target_subsystem}".lower()
        
        for indicator in kernel_indicators:
            if indicator in test_content:
                return True
        
        # Check if test requires specific hardware peripherals
        if (test_case.required_hardware and 
            test_case.required_hardware.peripherals):
            return True
        
        # Check if test script contains kernel-specific commands
        kernel_commands = ["insmod", "rmmod", "modprobe", "dmesg", "/proc/", "/sys/"]
        test_script_lower = test_case.test_script.lower()
        
        for command in kernel_commands:
            if command in test_script_lower:
                return True
        
        return False
    
    def get_available_runners(self) -> Dict[RunnerType, Type[BaseTestRunner]]:
        """Get all available runner types and their implementations.
        
        Returns:
            Dictionary mapping runner types to their implementations
        """
        return self._runners.copy()
    
    def get_runner_for_test_type(self, test_type: TestType) -> RunnerType:
        """Get the recommended runner type for a specific test type.
        
        Args:
            test_type: The test type to get a runner for
            
        Returns:
            The recommended runner type
        """
        # Create a dummy test case to use selection logic
        from ai_generator.models import HardwareConfig
        
        dummy_test = TestCase(
            id="dummy",
            name="dummy",
            description="",
            test_type=test_type,
            target_subsystem="",
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        dummy_env = Environment(
            id="dummy",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        return self._select_runner_type(dummy_test, dummy_env)
    
    def validate_runner_compatibility(self, test_case: TestCase, environment: Environment) -> bool:
        """Validate that a runner can be created for the given test case and environment.
        
        Args:
            test_case: The test case to validate
            environment: The environment to validate
            
        Returns:
            True if a compatible runner can be created
        """
        try:
            runner_type = self._select_runner_type(test_case, environment)
            
            if runner_type not in self._runners:
                return False
            
            # Check if the runner supports the test type and hardware
            runner_class = self._runners[runner_type]
            
            # Create a temporary instance to check compatibility
            temp_runner = runner_class(environment)
            
            return (temp_runner.supports_test_type(test_case.test_type) and
                    temp_runner.supports_hardware(environment.config))
        
        except Exception:
            return False


# Global factory instance
_factory_instance: Optional[TestRunnerFactory] = None


def get_runner_factory() -> TestRunnerFactory:
    """Get the global test runner factory instance.
    
    Returns:
        The global TestRunnerFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = TestRunnerFactory()
    return _factory_instance


def create_test_runner(test_case: TestCase, environment: Environment) -> BaseTestRunner:
    """Convenience function to create a test runner.
    
    Args:
        test_case: The test case to be executed
        environment: The environment to execute in
        
    Returns:
        An appropriate test runner instance
    """
    factory = get_runner_factory()
    return factory.create_runner(test_case, environment)