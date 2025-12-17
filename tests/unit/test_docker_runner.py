"""Unit tests for the Docker test runner."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from ai_generator.models import (
    TestCase, TestType, TestStatus, Environment, HardwareConfig,
    ArtifactBundle, FailureInfo
)
from execution.runners.docker_runner import DockerTestRunner


class TestDockerTestRunner:
    """Test cases for DockerTestRunner."""
    
    def setup_method(self):
        """Set up test fixtures."""
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
            test_script="echo 'Hello World'",
            execution_time_estimate=60
        )
    
    @patch('execution.runners.docker_runner.docker')
    def test_init(self, mock_docker):
        """Test DockerTestRunner initialization."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        
        runner = DockerTestRunner(self.environment)
        
        assert runner.environment == self.environment
        assert runner.docker_client == mock_client
        assert runner.container is None
        assert runner.temp_dir is None
    
    def test_prepare_test_script(self):
        """Test test script preparation."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                runner.temp_dir = temp_dir
                
                script_path = runner._prepare_test_script(self.test_case)
                
                assert script_path.exists()
                assert script_path.is_file()
                assert os.access(script_path, os.X_OK)  # Check executable
                
                content = script_path.read_text()
                assert "echo 'Hello World'" in content
                assert self.test_case.id in content
                assert self.test_case.name in content
    
    def test_select_base_image_default(self):
        """Test default base image selection."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            image = runner._select_base_image(self.test_case)
            assert image == "ubuntu:22.04"
    
    def test_select_base_image_python(self):
        """Test Python base image selection."""
        python_test = TestCase(
            id="test_python",
            name="Python Test",
            description="A Python test using pytest",
            test_type=TestType.UNIT,
            target_subsystem="python",
            test_script="python -m pytest test.py"
        )
        
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            image = runner._select_base_image(python_test)
            assert image == "python:3.10-slim"
    
    def test_select_base_image_gcc(self):
        """Test GCC base image selection."""
        c_test = TestCase(
            id="test_c",
            name="C Test",
            description="A C compilation test",
            test_type=TestType.UNIT,
            target_subsystem="compiler",
            test_script="gcc -o test test.c && ./test"
        )
        
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            image = runner._select_base_image(c_test)
            assert image == "gcc:latest"
    
    def test_analyze_result_success(self):
        """Test result analysis for successful test."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            result = {
                'stdout': 'Test passed successfully',
                'stderr': '',
                'exit_code': 0,
                'timeout_occurred': False
            }
            
            status, failure_info = runner._analyze_result(result, 300, 10.5)
            
            assert status == TestStatus.PASSED
            assert failure_info is None
    
    def test_analyze_result_failure(self):
        """Test result analysis for failed test."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            result = {
                'stdout': 'Test output',
                'stderr': 'Error: Test failed',
                'exit_code': 1,
                'timeout_occurred': False
            }
            
            status, failure_info = runner._analyze_result(result, 300, 10.5)
            
            assert status == TestStatus.FAILED
            assert failure_info is not None
            assert failure_info.exit_code == 1
            assert "Test failed with exit code 1" in failure_info.error_message
            assert failure_info.timeout_occurred is False
    
    def test_analyze_result_timeout(self):
        """Test result analysis for timed out test."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            result = {
                'stdout': 'Partial output',
                'stderr': 'Test timed out',
                'exit_code': 124,
                'timeout_occurred': True
            }
            
            status, failure_info = runner._analyze_result(result, 300, 305.0)
            
            assert status == TestStatus.TIMEOUT
            assert failure_info is not None
            assert failure_info.timeout_occurred is True
            assert "timed out" in failure_info.error_message.lower()
    
    def test_analyze_result_kernel_panic(self):
        """Test result analysis for kernel panic."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            result = {
                'stdout': 'Starting test...\nKernel panic - not syncing: Fatal error',
                'stderr': 'System crashed',
                'exit_code': 139,
                'timeout_occurred': False
            }
            
            status, failure_info = runner._analyze_result(result, 300, 10.5)
            
            assert status == TestStatus.FAILED
            assert failure_info is not None
            assert failure_info.kernel_panic is True
            assert "crash" in failure_info.error_message.lower()
    
    def test_supports_test_type(self):
        """Test test type support checking."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            assert runner.supports_test_type(TestType.UNIT) is True
            assert runner.supports_test_type(TestType.INTEGRATION) is True
            assert runner.supports_test_type(TestType.SECURITY) is True
            assert runner.supports_test_type(TestType.FUZZ) is True
            assert runner.supports_test_type(TestType.PERFORMANCE) is False  # Not explicitly supported
    
    def test_supports_hardware_virtual(self):
        """Test hardware support for virtual environments."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            virtual_config = HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=2048,
                is_virtual=True
            )
            
            assert runner.supports_hardware(virtual_config) is True
    
    def test_supports_hardware_physical(self):
        """Test hardware support rejection for physical environments."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            physical_config = HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=2048,
                is_virtual=False
            )
            
            assert runner.supports_hardware(physical_config) is False
    
    def test_supports_hardware_unsupported_architecture(self):
        """Test hardware support rejection for unsupported architecture."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            unsupported_config = HardwareConfig(
                architecture="mips64",
                cpu_model="generic",
                memory_mb=1024,
                is_virtual=True
            )
            
            assert runner.supports_hardware(unsupported_config) is False
    
    def test_supports_hardware_excessive_memory(self):
        """Test hardware support rejection for excessive memory requirements."""
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            high_memory_config = HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=32768,  # 32GB
                is_virtual=True
            )
            
            assert runner.supports_hardware(high_memory_config) is False
    
    def test_supports_hardware_many_peripherals(self):
        """Test hardware support rejection for many peripherals."""
        from ai_generator.models import Peripheral
        
        with patch('execution.runners.docker_runner.docker'):
            runner = DockerTestRunner(self.environment)
            
            many_peripherals_config = HardwareConfig(
                architecture="x86_64",
                cpu_model="generic",
                memory_mb=1024,
                is_virtual=True,
                peripherals=[
                    Peripheral(name="uart1", type="serial"),
                    Peripheral(name="uart2", type="serial"),
                    Peripheral(name="spi", type="bus"),
                    Peripheral(name="i2c", type="bus")
                ]
            )
            
            assert runner.supports_hardware(many_peripherals_config) is False
    
    @patch('execution.runners.docker_runner.docker')
    def test_cleanup_container(self, mock_docker):
        """Test container cleanup."""
        mock_container = Mock()
        
        runner = DockerTestRunner(self.environment)
        runner.container = mock_container
        
        runner.cleanup()
        
        mock_container.remove.assert_called_once_with(force=True)
        assert runner.container is None
    
    @patch('execution.runners.docker_runner.docker')
    def test_cleanup_temp_dir(self, mock_docker):
        """Test temporary directory cleanup."""
        runner = DockerTestRunner(self.environment)
        
        # Create a real temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            runner.temp_dir = temp_dir
            
            # Verify directory exists
            assert os.path.exists(temp_dir)
            
            runner.cleanup()
            
            # Directory should be cleaned up
            assert runner.temp_dir is None
    
    @patch('execution.runners.docker_runner.docker')
    def test_context_manager(self, mock_docker):
        """Test context manager functionality."""
        mock_container = Mock()
        
        with DockerTestRunner(self.environment) as runner:
            runner.container = mock_container
            assert isinstance(runner, DockerTestRunner)
        
        # Cleanup should be called automatically
        mock_container.remove.assert_called_once_with(force=True)