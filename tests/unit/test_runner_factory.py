"""Unit tests for the test runner factory."""

import pytest
from unittest.mock import Mock, patch

from ai_generator.models import TestCase, TestType, Environment, HardwareConfig
from execution.runner_factory import (
    TestRunnerFactory, BaseTestRunner, RunnerType,
    get_runner_factory, create_test_runner
)


class MockTestRunner(BaseTestRunner):
    """Mock test runner for testing."""
    
    def execute(self, test_case, timeout=None):
        return {"status": "passed", "exit_code": 0}
    
    def cleanup(self):
        pass
    
    def supports_test_type(self, test_type):
        return test_type == TestType.UNIT
    
    def supports_hardware(self, hardware_config):
        return hardware_config.is_virtual


class TestTestRunnerFactory:
    """Test cases for TestRunnerFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = TestRunnerFactory()
        
        # Create test hardware config
        self.hardware_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=1024,
            is_virtual=True
        )
        
        # Create test environment
        self.environment = Environment(
            id="test_env",
            config=self.hardware_config
        )
        
        # Create test case
        self.test_case = TestCase(
            id="test_1",
            name="Test Case 1",
            description="A unit test",
            test_type=TestType.UNIT,
            target_subsystem="memory",
            test_script="echo 'test'"
        )
    
    def test_register_runner(self):
        """Test registering a new runner type."""
        self.factory.register_runner(RunnerType.DOCKER, MockTestRunner)
        
        runners = self.factory.get_available_runners()
        assert RunnerType.DOCKER in runners
        assert runners[RunnerType.DOCKER] == MockTestRunner
    
    def test_register_invalid_runner(self):
        """Test registering an invalid runner class."""
        class InvalidRunner:
            pass
        
        with pytest.raises(ValueError, match="must inherit from BaseTestRunner"):
            self.factory.register_runner(RunnerType.DOCKER, InvalidRunner)
    
    def test_select_runner_type_unit_test(self):
        """Test runner selection for unit tests."""
        runner_type = self.factory._select_runner_type(self.test_case, self.environment)
        assert runner_type == RunnerType.DOCKER
    
    def test_select_runner_type_integration_test(self):
        """Test runner selection for integration tests."""
        integration_test = TestCase(
            id="test_2",
            name="Integration Test",
            description="An integration test",
            test_type=TestType.INTEGRATION,
            target_subsystem="network",
            test_script="echo 'test'"
        )
        
        runner_type = self.factory._select_runner_type(integration_test, self.environment)
        assert runner_type == RunnerType.DOCKER
    
    def test_select_runner_type_kernel_test(self):
        """Test runner selection for kernel-related tests."""
        kernel_test = TestCase(
            id="test_3",
            name="Kernel Test",
            description="A kernel driver test",
            test_type=TestType.INTEGRATION,
            target_subsystem="kernel",
            test_script="insmod test_module.ko"
        )
        
        runner_type = self.factory._select_runner_type(kernel_test, self.environment)
        assert runner_type == RunnerType.QEMU
    
    def test_select_runner_type_physical_environment(self):
        """Test runner selection for physical environments."""
        physical_config = HardwareConfig(
            architecture="arm64",
            cpu_model="cortex-a72",
            memory_mb=2048,
            is_virtual=False
        )
        
        physical_env = Environment(
            id="physical_env",
            config=physical_config
        )
        
        runner_type = self.factory._select_runner_type(self.test_case, physical_env)
        assert runner_type == RunnerType.PHYSICAL
    
    def test_select_runner_type_performance_test(self):
        """Test runner selection for performance tests."""
        perf_test = TestCase(
            id="test_4",
            name="Performance Test",
            description="A performance benchmark",
            test_type=TestType.PERFORMANCE,
            target_subsystem="scheduler",
            test_script="echo 'benchmark'"
        )
        
        runner_type = self.factory._select_runner_type(perf_test, self.environment)
        assert runner_type == RunnerType.QEMU
    
    def test_requires_full_vm_kernel_indicators(self):
        """Test VM requirement detection for kernel tests."""
        kernel_test = TestCase(
            id="test_5",
            name="Kernel Test",
            description="Testing kernel module functionality",
            test_type=TestType.INTEGRATION,
            target_subsystem="driver",
            test_script="echo 'test'"
        )
        
        requires_vm = self.factory._requires_full_vm(kernel_test)
        assert requires_vm is True
    
    def test_requires_full_vm_peripheral_config(self):
        """Test VM requirement detection for peripheral configurations."""
        from ai_generator.models import Peripheral
        
        hardware_with_peripherals = HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=1024,
            peripherals=[
                Peripheral(name="uart", type="serial"),
                Peripheral(name="spi", type="bus")
            ]
        )
        
        peripheral_test = TestCase(
            id="test_6",
            name="Peripheral Test",
            description="Testing peripheral functionality",
            test_type=TestType.INTEGRATION,
            target_subsystem="peripheral",
            test_script="echo 'test'",
            required_hardware=hardware_with_peripherals
        )
        
        requires_vm = self.factory._requires_full_vm(peripheral_test)
        assert requires_vm is True
    
    def test_requires_full_vm_kernel_commands(self):
        """Test VM requirement detection for kernel commands."""
        kernel_command_test = TestCase(
            id="test_7",
            name="Module Test",
            description="Testing module loading",
            test_type=TestType.INTEGRATION,
            target_subsystem="module",
            test_script="modprobe test_module && dmesg | grep test"
        )
        
        requires_vm = self.factory._requires_full_vm(kernel_command_test)
        assert requires_vm is True
    
    def test_requires_full_vm_simple_test(self):
        """Test VM requirement detection for simple tests."""
        simple_test = TestCase(
            id="test_8",
            name="Simple Test",
            description="A simple user-space test",
            test_type=TestType.UNIT,
            target_subsystem="userspace",
            test_script="echo 'hello world'"
        )
        
        requires_vm = self.factory._requires_full_vm(simple_test)
        assert requires_vm is False
    
    def test_get_runner_for_test_type(self):
        """Test getting recommended runner for test types."""
        assert self.factory.get_runner_for_test_type(TestType.UNIT) == RunnerType.DOCKER
        assert self.factory.get_runner_for_test_type(TestType.PERFORMANCE) == RunnerType.QEMU
        assert self.factory.get_runner_for_test_type(TestType.SECURITY) == RunnerType.QEMU
        assert self.factory.get_runner_for_test_type(TestType.FUZZ) == RunnerType.QEMU
    
    def test_create_runner_success(self):
        """Test successful runner creation."""
        factory = TestRunnerFactory()
        factory.register_runner(RunnerType.DOCKER, MockTestRunner)
        
        runner = factory.create_runner(self.test_case, self.environment)
        assert isinstance(runner, MockTestRunner)
        assert runner.environment == self.environment
    
    def test_create_runner_no_implementation(self):
        """Test runner creation when no implementation is available."""
        empty_factory = TestRunnerFactory()
        empty_factory._runners = {}
        
        with pytest.raises(ValueError, match="No runner implementation available"):
            empty_factory.create_runner(self.test_case, self.environment)
    
    def test_validate_runner_compatibility_success(self):
        """Test successful runner compatibility validation."""
        factory = TestRunnerFactory()
        factory.register_runner(RunnerType.DOCKER, MockTestRunner)
        
        is_compatible = factory.validate_runner_compatibility(self.test_case, self.environment)
        assert is_compatible is True
    
    def test_validate_runner_compatibility_failure(self):
        """Test runner compatibility validation failure."""
        empty_factory = TestRunnerFactory()
        empty_factory._runners = {}
        
        is_compatible = empty_factory.validate_runner_compatibility(self.test_case, self.environment)
        assert is_compatible is False


class TestGlobalFactory:
    """Test cases for global factory functions."""
    
    def test_get_runner_factory_singleton(self):
        """Test that get_runner_factory returns the same instance."""
        factory1 = get_runner_factory()
        factory2 = get_runner_factory()
        
        assert factory1 is factory2
        assert isinstance(factory1, TestRunnerFactory)
    
    @patch('execution.runner_factory.get_runner_factory')
    def test_create_test_runner_convenience(self, mock_get_factory):
        """Test the convenience function for creating test runners."""
        mock_factory = Mock()
        mock_runner = Mock()
        mock_factory.create_runner.return_value = mock_runner
        mock_get_factory.return_value = mock_factory
        
        test_case = Mock()
        environment = Mock()
        
        result = create_test_runner(test_case, environment)
        
        assert result == mock_runner
        mock_factory.create_runner.assert_called_once_with(test_case, environment)