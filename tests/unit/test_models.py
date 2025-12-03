"""Unit tests for core data models."""

import pytest
import json
from datetime import datetime
from ai_generator.models import (
    TestCase, TestResult, CodeAnalysis, FailureAnalysis,
    HardwareConfig, Environment, TestType, TestStatus,
    RiskLevel, EnvironmentStatus, Peripheral, ExpectedOutcome,
    ArtifactBundle, CoverageData, FailureInfo, Credentials,
    Function, Commit, FixSuggestion
)


@pytest.mark.unit
class TestPeripheral:
    """Tests for Peripheral model."""
    
    def test_peripheral_creation(self):
        """Test creating a peripheral."""
        peripheral = Peripheral(name="eth0", type="network", model="e1000")
        assert peripheral.name == "eth0"
        assert peripheral.type == "network"
        assert peripheral.model == "e1000"
    
    def test_peripheral_serialization(self):
        """Test peripheral serialization round-trip."""
        peripheral = Peripheral(name="sda", type="storage", metadata={"size": "1TB"})
        data = peripheral.to_dict()
        restored = Peripheral.from_dict(data)
        assert restored.name == peripheral.name
        assert restored.type == peripheral.type
        assert restored.metadata == peripheral.metadata


@pytest.mark.unit
class TestHardwareConfig:
    """Tests for HardwareConfig model."""
    
    def test_hardware_config_creation(self):
        """Test creating a hardware configuration."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel Core i7",
            memory_mb=4096
        )
        assert config.architecture == "x86_64"
        assert config.memory_mb == 4096
        assert config.is_virtual is True
        assert config.emulator == "qemu"
    
    def test_hardware_config_validation_negative_memory(self):
        """Test that negative memory raises ValueError."""
        with pytest.raises(ValueError, match="memory_mb must be positive"):
            HardwareConfig(
                architecture="x86_64",
                cpu_model="test",
                memory_mb=-1
            )
    
    def test_hardware_config_validation_invalid_arch(self):
        """Test that invalid architecture raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported architecture"):
            HardwareConfig(
                architecture="invalid_arch",
                cpu_model="test",
                memory_mb=1024
            )
    
    def test_hardware_config_serialization(self):
        """Test hardware config serialization round-trip."""
        peripheral = Peripheral(name="eth0", type="network")
        config = HardwareConfig(
            architecture="arm64",
            cpu_model="ARM Cortex-A72",
            memory_mb=2048,
            peripherals=[peripheral]
        )
        data = config.to_dict()
        restored = HardwareConfig.from_dict(data)
        assert restored.architecture == config.architecture
        assert restored.memory_mb == config.memory_mb
        assert len(restored.peripherals) == 1
        assert restored.peripherals[0].name == "eth0"


@pytest.mark.unit
class TestExpectedOutcome:
    """Tests for ExpectedOutcome model."""
    
    def test_expected_outcome_creation(self):
        """Test creating an expected outcome."""
        outcome = ExpectedOutcome(should_pass=True, expected_return_code=0)
        assert outcome.should_pass is True
        assert outcome.expected_return_code == 0
    
    def test_expected_outcome_serialization(self):
        """Test expected outcome serialization round-trip."""
        outcome = ExpectedOutcome(
            should_pass=False,
            expected_return_code=1,
            should_not_crash=True
        )
        data = outcome.to_dict()
        restored = ExpectedOutcome.from_dict(data)
        assert restored.should_pass == outcome.should_pass
        assert restored.expected_return_code == outcome.expected_return_code


@pytest.mark.unit
class TestTestCase:
    """Tests for TestCase model."""
    
    def test_test_case_creation(self):
        """Test creating a test case."""
        test = TestCase(
            id="test_001",
            name="Test scheduler",
            description="Test FIFO scheduling",
            test_type=TestType.UNIT,
            target_subsystem="scheduler"
        )
        assert test.id == "test_001"
        assert test.test_type == TestType.UNIT
        assert test.execution_time_estimate == 60
    
    def test_test_case_validation_empty_id(self):
        """Test that empty id raises ValueError."""
        with pytest.raises(ValueError, match="id cannot be empty"):
            TestCase(
                id="",
                name="Test",
                description="Test",
                test_type=TestType.UNIT,
                target_subsystem="test"
            )
    
    def test_test_case_validation_negative_time(self):
        """Test that negative execution time raises ValueError."""
        with pytest.raises(ValueError, match="execution_time_estimate must be positive"):
            TestCase(
                id="test_001",
                name="Test",
                description="Test",
                test_type=TestType.UNIT,
                target_subsystem="test",
                execution_time_estimate=-1
            )
    
    def test_test_case_serialization(self):
        """Test test case serialization round-trip."""
        hw_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        outcome = ExpectedOutcome(should_pass=True)
        test = TestCase(
            id="test_001",
            name="Test",
            description="Test description",
            test_type=TestType.UNIT,
            target_subsystem="scheduler",
            required_hardware=hw_config,
            expected_outcome=outcome
        )
        data = test.to_dict()
        restored = TestCase.from_dict(data)
        assert restored.id == test.id
        assert restored.test_type == test.test_type
        assert restored.required_hardware.architecture == "x86_64"
    
    def test_test_case_json_serialization(self):
        """Test test case JSON serialization round-trip."""
        test = TestCase(
            id="test_001",
            name="Test",
            description="Test",
            test_type=TestType.UNIT,
            target_subsystem="test"
        )
        json_str = test.to_json()
        restored = TestCase.from_json(json_str)
        assert restored.id == test.id
        assert restored.name == test.name


@pytest.mark.unit
class TestCoverageData:
    """Tests for CoverageData model."""
    
    def test_coverage_data_creation(self):
        """Test creating coverage data."""
        coverage = CoverageData(
            line_coverage=0.85,
            branch_coverage=0.75,
            function_coverage=0.90
        )
        assert coverage.line_coverage == 0.85
        assert coverage.branch_coverage == 0.75
    
    def test_coverage_data_validation_invalid_range(self):
        """Test that coverage values outside 0-1 raise ValueError."""
        with pytest.raises(ValueError, match="Coverage values must be between 0.0 and 1.0"):
            CoverageData(line_coverage=1.5)
    
    def test_coverage_data_serialization(self):
        """Test coverage data serialization round-trip."""
        coverage = CoverageData(
            line_coverage=0.8,
            covered_lines=["file.c:10", "file.c:20"],
            uncovered_lines=["file.c:30"]
        )
        data = coverage.to_dict()
        restored = CoverageData.from_dict(data)
        assert restored.line_coverage == coverage.line_coverage
        assert restored.covered_lines == coverage.covered_lines


@pytest.mark.unit
class TestFailureInfo:
    """Tests for FailureInfo model."""
    
    def test_failure_info_creation(self):
        """Test creating failure info."""
        failure = FailureInfo(
            error_message="Kernel panic",
            stack_trace="trace...",
            kernel_panic=True
        )
        assert failure.error_message == "Kernel panic"
        assert failure.kernel_panic is True
    
    def test_failure_info_serialization(self):
        """Test failure info serialization round-trip."""
        failure = FailureInfo(
            error_message="Test failed",
            exit_code=1,
            timeout_occurred=True
        )
        data = failure.to_dict()
        restored = FailureInfo.from_dict(data)
        assert restored.error_message == failure.error_message
        assert restored.exit_code == failure.exit_code


@pytest.mark.unit
class TestEnvironment:
    """Tests for Environment model."""
    
    def test_environment_creation(self):
        """Test creating an environment."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        env = Environment(
            id="env_001",
            config=config,
            status=EnvironmentStatus.IDLE
        )
        assert env.id == "env_001"
        assert env.status == EnvironmentStatus.IDLE
    
    def test_environment_validation_empty_id(self):
        """Test that empty id raises ValueError."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        with pytest.raises(ValueError, match="id cannot be empty"):
            Environment(id="", config=config)
    
    def test_environment_serialization(self):
        """Test environment serialization round-trip."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        creds = Credentials(username="test", password="pass")
        env = Environment(
            id="env_001",
            config=config,
            ssh_credentials=creds,
            kernel_version="5.15.0"
        )
        data = env.to_dict()
        restored = Environment.from_dict(data)
        assert restored.id == env.id
        assert restored.kernel_version == env.kernel_version
        assert restored.ssh_credentials.username == "test"


@pytest.mark.unit
class TestTestResult:
    """Tests for TestResult model."""
    
    def test_test_result_creation(self):
        """Test creating a test result."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        env = Environment(id="env_001", config=config)
        result = TestResult(
            test_id="test_001",
            status=TestStatus.PASSED,
            execution_time=5.5,
            environment=env
        )
        assert result.test_id == "test_001"
        assert result.status == TestStatus.PASSED
        assert result.execution_time == 5.5
    
    def test_test_result_validation_negative_time(self):
        """Test that negative execution time raises ValueError."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        env = Environment(id="env_001", config=config)
        with pytest.raises(ValueError, match="execution_time cannot be negative"):
            TestResult(
                test_id="test_001",
                status=TestStatus.PASSED,
                execution_time=-1.0,
                environment=env
            )
    
    def test_test_result_serialization(self):
        """Test test result serialization round-trip."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        env = Environment(id="env_001", config=config)
        coverage = CoverageData(line_coverage=0.8)
        failure = FailureInfo(error_message="Failed")
        result = TestResult(
            test_id="test_001",
            status=TestStatus.FAILED,
            execution_time=10.0,
            environment=env,
            coverage_data=coverage,
            failure_info=failure
        )
        data = result.to_dict()
        restored = TestResult.from_dict(data)
        assert restored.test_id == result.test_id
        assert restored.status == result.status
        assert restored.coverage_data.line_coverage == 0.8
        assert restored.failure_info.error_message == "Failed"
    
    def test_test_result_json_serialization(self):
        """Test test result JSON serialization round-trip."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        env = Environment(id="env_001", config=config)
        result = TestResult(
            test_id="test_001",
            status=TestStatus.PASSED,
            execution_time=5.0,
            environment=env
        )
        json_str = result.to_json()
        restored = TestResult.from_json(json_str)
        assert restored.test_id == result.test_id
        assert restored.status == result.status


@pytest.mark.unit
class TestCodeAnalysis:
    """Tests for CodeAnalysis model."""
    
    def test_code_analysis_creation(self):
        """Test creating a code analysis."""
        func = Function(
            name="schedule",
            file_path="kernel/sched/core.c",
            line_number=100
        )
        analysis = CodeAnalysis(
            changed_files=["kernel/sched/core.c"],
            changed_functions=[func],
            affected_subsystems=["scheduler"],
            impact_score=0.7,
            risk_level=RiskLevel.MEDIUM
        )
        assert analysis.impact_score == 0.7
        assert analysis.risk_level == RiskLevel.MEDIUM
        assert len(analysis.changed_functions) == 1
    
    def test_code_analysis_validation_invalid_impact(self):
        """Test that impact score outside 0-1 raises ValueError."""
        with pytest.raises(ValueError, match="impact_score must be between 0.0 and 1.0"):
            CodeAnalysis(impact_score=1.5)
    
    def test_code_analysis_serialization(self):
        """Test code analysis serialization round-trip."""
        func = Function(
            name="test_func",
            file_path="test.c",
            line_number=10
        )
        analysis = CodeAnalysis(
            changed_functions=[func],
            impact_score=0.5,
            suggested_test_types=[TestType.UNIT, TestType.INTEGRATION]
        )
        data = analysis.to_dict()
        restored = CodeAnalysis.from_dict(data)
        assert restored.impact_score == analysis.impact_score
        assert len(restored.changed_functions) == 1
        assert restored.changed_functions[0].name == "test_func"
    
    def test_code_analysis_json_serialization(self):
        """Test code analysis JSON serialization round-trip."""
        analysis = CodeAnalysis(
            changed_files=["test.c"],
            impact_score=0.3,
            risk_level=RiskLevel.LOW
        )
        json_str = analysis.to_json()
        restored = CodeAnalysis.from_json(json_str)
        assert restored.impact_score == analysis.impact_score
        assert restored.risk_level == analysis.risk_level


@pytest.mark.unit
class TestFailureAnalysis:
    """Tests for FailureAnalysis model."""
    
    def test_failure_analysis_creation(self):
        """Test creating a failure analysis."""
        commit = Commit(
            sha="abc123",
            message="Fix bug",
            author="dev@example.com",
            timestamp=datetime.now()
        )
        fix = FixSuggestion(
            description="Add null check",
            confidence=0.8
        )
        analysis = FailureAnalysis(
            failure_id="fail_001",
            root_cause="Null pointer dereference",
            confidence=0.9,
            suspicious_commits=[commit],
            suggested_fixes=[fix],
            reproducibility=0.95
        )
        assert analysis.failure_id == "fail_001"
        assert analysis.confidence == 0.9
        assert len(analysis.suspicious_commits) == 1
    
    def test_failure_analysis_validation_empty_id(self):
        """Test that empty failure_id raises ValueError."""
        with pytest.raises(ValueError, match="failure_id cannot be empty"):
            FailureAnalysis(
                failure_id="",
                root_cause="test",
                confidence=0.5
            )
    
    def test_failure_analysis_validation_invalid_confidence(self):
        """Test that confidence outside 0-1 raises ValueError."""
        with pytest.raises(ValueError, match="confidence must be between 0.0 and 1.0"):
            FailureAnalysis(
                failure_id="fail_001",
                root_cause="test",
                confidence=1.5
            )
    
    def test_failure_analysis_serialization(self):
        """Test failure analysis serialization round-trip."""
        commit = Commit(
            sha="abc123",
            message="Test",
            author="dev@example.com",
            timestamp=datetime.now()
        )
        fix = FixSuggestion(description="Fix it", confidence=0.7)
        analysis = FailureAnalysis(
            failure_id="fail_001",
            root_cause="Bug",
            confidence=0.8,
            suspicious_commits=[commit],
            suggested_fixes=[fix]
        )
        data = analysis.to_dict()
        restored = FailureAnalysis.from_dict(data)
        assert restored.failure_id == analysis.failure_id
        assert restored.confidence == analysis.confidence
        assert len(restored.suspicious_commits) == 1
        assert restored.suspicious_commits[0].sha == "abc123"
    
    def test_failure_analysis_json_serialization(self):
        """Test failure analysis JSON serialization round-trip."""
        analysis = FailureAnalysis(
            failure_id="fail_001",
            root_cause="Test failure",
            confidence=0.75,
            reproducibility=0.9
        )
        json_str = analysis.to_json()
        restored = FailureAnalysis.from_json(json_str)
        assert restored.failure_id == analysis.failure_id
        assert restored.confidence == analysis.confidence



@pytest.mark.unit
class TestEdgeCases:
    """Tests for edge cases in data models."""
    
    def test_test_case_with_string_enum(self):
        """Test that TestCase accepts string enum values."""
        test = TestCase(
            id="test_001",
            name="Test",
            description="Test",
            test_type="unit",  # String instead of enum
            target_subsystem="test"
        )
        assert test.test_type == TestType.UNIT
    
    def test_environment_with_string_status(self):
        """Test that Environment accepts string status values."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        env = Environment(
            id="env_001",
            config=config,
            status="idle"  # String instead of enum
        )
        assert env.status == EnvironmentStatus.IDLE
    
    def test_hardware_config_with_zero_peripherals(self):
        """Test hardware config with no peripherals."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024,
            peripherals=[]
        )
        assert len(config.peripherals) == 0
    
    def test_test_result_with_minimal_data(self):
        """Test test result with only required fields."""
        config = HardwareConfig(
            architecture="x86_64",
            cpu_model="test",
            memory_mb=1024
        )
        env = Environment(id="env_001", config=config)
        result = TestResult(
            test_id="test_001",
            status=TestStatus.PASSED,
            execution_time=0.0,
            environment=env
        )
        assert result.coverage_data is None
        assert result.failure_info is None
