"""Property-based tests for hardware failure isolation.

**Feature: agentic-kernel-testing, Property 8: Hardware failure isolation**
**Validates: Requirements 2.3**

This module tests the property that for any hardware-specific test failure,
the diagnostic information should uniquely identify the failing hardware configuration.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime
from typing import List, Dict

from ai_generator.models import (
    HardwareConfig, TestResult, TestStatus, FailureInfo, Environment,
    EnvironmentStatus, ArtifactBundle, Peripheral, Credentials
)
from execution.hardware_failure_isolation import (
    HardwareFailureIsolationSystem, HardwareSpecificDiagnosticCollector,
    FailureToHardwareCorrelator, HardwareFailureReportGenerator,
    HardwareFailureType, HardwareSpecificDiagnostic
)


# Test data generators
@st.composite
def generate_peripheral(draw):
    """Generate a peripheral configuration."""
    peripheral_types = ["network", "storage", "serial", "usb", "pci"]
    return Peripheral(
        name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
        type=draw(st.sampled_from(peripheral_types)),
        model=draw(st.one_of(st.none(), st.text(min_size=1, max_size=30))),
        metadata=draw(st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=20), max_size=3))
    )


@st.composite
def generate_hardware_config(draw):
    """Generate a hardware configuration."""
    architectures = ["x86_64", "arm64", "riscv64", "arm"]
    storage_types = ["ssd", "hdd", "nvme", "emmc", "sd"]
    emulators = ["qemu", "kvm", "bochs"]
    
    is_virtual = draw(st.booleans())
    emulator = draw(st.sampled_from(emulators)) if is_virtual else None
    
    return HardwareConfig(
        architecture=draw(st.sampled_from(architectures)),
        cpu_model=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")))),
        memory_mb=draw(st.integers(min_value=512, max_value=32768)),
        storage_type=draw(st.sampled_from(storage_types)),
        peripherals=draw(st.lists(generate_peripheral(), max_size=5)),
        is_virtual=is_virtual,
        emulator=emulator
    )


@st.composite
def generate_credentials(draw):
    """Generate SSH credentials."""
    return Credentials(
        username=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
        password=draw(st.one_of(st.none(), st.text(min_size=1, max_size=30))),
        private_key_path=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    )


@st.composite
def generate_environment(draw, hardware_config):
    """Generate a test environment."""
    return Environment(
        id=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
        config=hardware_config,
        status=draw(st.sampled_from(list(EnvironmentStatus))),
        kernel_version=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        ip_address=draw(st.one_of(st.none(), st.text(min_size=7, max_size=15))),
        ssh_credentials=draw(st.one_of(st.none(), generate_credentials())),
        created_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2025, 12, 31))),
        last_used=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2025, 12, 31))),
        metadata=draw(st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=20), max_size=3))
    )


@st.composite
def generate_failure_info(draw):
    """Generate failure information."""
    return FailureInfo(
        error_message=draw(st.text(min_size=1, max_size=200)),
        stack_trace=draw(st.one_of(st.none(), st.text(min_size=1, max_size=500))),
        exit_code=draw(st.one_of(st.none(), st.integers(min_value=-128, max_value=127))),
        kernel_panic=draw(st.booleans()),
        timeout_occurred=draw(st.booleans()),
        metadata=draw(st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=20), max_size=3))
    )


@st.composite
def generate_hardware_specific_log(draw, hardware_config, include_hardware_error=True):
    """Generate log content with optional hardware-specific errors."""
    base_logs = [
        "System boot completed",
        "Kernel version 5.15.0",
        "Starting test execution",
        "Test completed"
    ]
    
    logs = list(base_logs)
    
    if include_hardware_error:
        # Add hardware-specific error patterns based on config
        if hardware_config.architecture in ["arm", "arm64"]:
            logs.append("ARM: CPU exception occurred")
        
        if hardware_config.memory_mb < 1024:
            logs.append("Memory allocation failed: insufficient memory")
        
        if not hardware_config.is_virtual:
            # Physical hardware errors
            error_patterns = [
                "Machine Check Exception: CPU 0 BANK 1",
                "EDAC MC0: memory error detected",
                "I/O error, dev sda, sector 12345",
                "thermal error: CPU temperature critical",
                "power error: voltage out of range"
            ]
            logs.append(draw(st.sampled_from(error_patterns)))
        else:
            # Virtual hardware errors
            logs.append("virtio: device error detected")
    
    return logs


@st.composite
def generate_test_result(draw, hardware_config, should_fail=True):
    """Generate a test result."""
    environment = draw(generate_environment(hardware_config))
    
    status = TestStatus.FAILED if should_fail else draw(st.sampled_from([TestStatus.PASSED, TestStatus.SKIPPED]))
    
    # Generate logs with hardware-specific content
    logs = draw(generate_hardware_specific_log(hardware_config, include_hardware_error=should_fail))
    
    artifacts = ArtifactBundle(
        logs=logs,
        core_dumps=draw(st.lists(st.text(min_size=1, max_size=50), max_size=3)),
        traces=draw(st.lists(st.text(min_size=1, max_size=50), max_size=3)),
        metadata=draw(st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=20), max_size=3))
    )
    
    failure_info = draw(generate_failure_info()) if should_fail else None
    
    return TestResult(
        test_id=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))),
        status=status,
        execution_time=draw(st.floats(min_value=0.1, max_value=300.0)),
        environment=environment,
        artifacts=artifacts,
        failure_info=failure_info,
        timestamp=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2025, 12, 31)))
    )


class TestHardwareFailureIsolation:
    """Test hardware failure isolation functionality."""
    
    @given(
        hardware_configs=st.lists(generate_hardware_config(), min_size=1, max_size=3),
        failure_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))
    )
    @settings(max_examples=20, deadline=None)
    def test_hardware_failure_isolation_uniquely_identifies_hardware(self, hardware_configs, failure_id):
        """
        **Property 8: Hardware failure isolation**
        
        For any hardware-specific test failure, the diagnostic information should 
        uniquely identify the failing hardware configuration.
        
        This property ensures that when a test fails on specific hardware,
        the isolation system can distinguish which hardware configuration
        is responsible for the failure.
        """
        # Arrange: Create hardware failure isolation system
        isolation_system = HardwareFailureIsolationSystem()
        
        # Create hardware ID mapping
        hardware_id_mapping = {}
        for i, config in enumerate(hardware_configs):
            hardware_id = f"hw_{i}"
            hardware_id_mapping[hardware_id] = config
        
        # Generate test results for each hardware (some failing, some passing)
        test_results = []
        for hardware_id, config in hardware_id_mapping.items():
            # Create both failing and passing results for variety
            failing_result = generate_test_result(config, should_fail=True).example()
            failing_result.environment.id = hardware_id
            test_results.append(failing_result)
            
            # Sometimes add a passing result too
            if len(test_results) % 2 == 0:
                passing_result = generate_test_result(config, should_fail=False).example()
                passing_result.environment.id = hardware_id
                test_results.append(passing_result)
        
        # Act: Perform hardware failure isolation
        reports = isolation_system.isolate_hardware_failure(
            failure_id, test_results, hardware_id_mapping
        )
        
        # Assert: Verify hardware failure isolation properties
        
        # Property 1: Each report should uniquely identify a hardware configuration
        hardware_ids_in_reports = set()
        for report in reports:
            assert report.hardware_id not in hardware_ids_in_reports, \
                f"Hardware ID {report.hardware_id} appears in multiple reports - not unique identification"
            hardware_ids_in_reports.add(report.hardware_id)
        
        # Property 2: Each report should contain the correct hardware configuration
        for report in reports:
            expected_config = hardware_id_mapping[report.hardware_id]
            assert report.hardware_config.architecture == expected_config.architecture, \
                f"Report hardware config architecture mismatch for {report.hardware_id}"
            assert report.hardware_config.memory_mb == expected_config.memory_mb, \
                f"Report hardware config memory mismatch for {report.hardware_id}"
            assert report.hardware_config.is_virtual == expected_config.is_virtual, \
                f"Report hardware config virtual flag mismatch for {report.hardware_id}"
        
        # Property 3: Reports should only be generated for hardware with failures
        failed_hardware_ids = set()
        for result in test_results:
            if result.status == TestStatus.FAILED:
                failed_hardware_ids.add(result.environment.id)
        
        report_hardware_ids = {report.hardware_id for report in reports}
        
        # All reports should be for hardware that had failures
        assert report_hardware_ids.issubset(failed_hardware_ids), \
            f"Reports generated for hardware without failures: {report_hardware_ids - failed_hardware_ids}"
        
        # Property 4: Each report should have diagnostics that are specific to that hardware
        for report in reports:
            for diagnostic in report.diagnostics:
                assert diagnostic.hardware_id == report.hardware_id, \
                    f"Diagnostic hardware ID {diagnostic.hardware_id} doesn't match report hardware ID {report.hardware_id}"
                assert diagnostic.hardware_config.architecture == report.hardware_config.architecture, \
                    f"Diagnostic hardware config doesn't match report config for {report.hardware_id}"
        
        # Property 5: Correlations should correctly link failures to hardware
        for report in reports:
            for correlation in report.correlations:
                assert correlation.hardware_id == report.hardware_id, \
                    f"Correlation hardware ID {correlation.hardware_id} doesn't match report hardware ID {report.hardware_id}"
                assert correlation.failure_id == failure_id, \
                    f"Correlation failure ID {correlation.failure_id} doesn't match expected {failure_id}"
                assert 0.0 <= correlation.correlation_score <= 1.0, \
                    f"Correlation score {correlation.correlation_score} out of valid range [0.0, 1.0]"
    
    @given(
        hardware_config=generate_hardware_config(),
        hardware_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))
    )
    @settings(max_examples=10, deadline=None)
    def test_diagnostic_collector_identifies_hardware_specific_errors(self, hardware_config, hardware_id):
        """Test that diagnostic collector properly identifies hardware-specific errors."""
        # Arrange
        collector = HardwareSpecificDiagnosticCollector()
        
        # Create a test result with hardware-specific failure
        test_result = generate_test_result(hardware_config, should_fail=True).example()
        
        # Act
        diagnostics = collector.collect_diagnostics(hardware_id, hardware_config, test_result)
        
        # Assert: Diagnostics should be collected for failed tests
        if test_result.status == TestStatus.FAILED:
            assert len(diagnostics) > 0, "Should collect diagnostics for failed tests"
            
            for diagnostic in diagnostics:
                # Each diagnostic should be associated with the correct hardware
                assert diagnostic.hardware_id == hardware_id
                assert diagnostic.hardware_config.architecture == hardware_config.architecture
                assert diagnostic.hardware_config.memory_mb == hardware_config.memory_mb
                assert diagnostic.hardware_config.is_virtual == hardware_config.is_virtual
                
                # Diagnostic should have valid failure type
                assert isinstance(diagnostic.failure_type, HardwareFailureType)
                
                # Diagnostic data should contain hardware information
                assert "hardware_architecture" in diagnostic.diagnostic_data
                assert "hardware_memory_mb" in diagnostic.diagnostic_data
                assert "is_virtual" in diagnostic.diagnostic_data
                
                assert diagnostic.diagnostic_data["hardware_architecture"] == hardware_config.architecture
                assert diagnostic.diagnostic_data["hardware_memory_mb"] == hardware_config.memory_mb
                assert diagnostic.diagnostic_data["is_virtual"] == hardware_config.is_virtual
    
    @given(
        hardware_configs=st.lists(generate_hardware_config(), min_size=2, max_size=3),
        failure_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))
    )
    @settings(max_examples=10, deadline=None)
    def test_correlator_distinguishes_between_hardware_configurations(self, hardware_configs, failure_id):
        """Test that correlator can distinguish between different hardware configurations."""
        # Arrange
        correlator = FailureToHardwareCorrelator()
        
        # Create hardware mapping
        hardware_mapping = {}
        test_results = []
        
        for i, config in enumerate(hardware_configs):
            hardware_id = f"hw_{i}"
            hardware_mapping[hardware_id] = config
            
            # Create test result for this hardware
            result = generate_test_result(config, should_fail=True).example()
            result.environment.id = hardware_id
            test_results.append(result)
        
        # Act
        correlations = correlator.correlate_failure_to_hardware(
            failure_id, test_results, hardware_mapping
        )
        
        # Assert: Each correlation should be for a different hardware
        hardware_ids_in_correlations = set()
        for correlation in correlations:
            assert correlation.hardware_id not in hardware_ids_in_correlations, \
                f"Hardware ID {correlation.hardware_id} appears in multiple correlations"
            hardware_ids_in_correlations.add(correlation.hardware_id)
            
            # Correlation should match the correct hardware config
            expected_config = hardware_mapping[correlation.hardware_id]
            assert correlation.hardware_config.architecture == expected_config.architecture
            assert correlation.hardware_config.memory_mb == expected_config.memory_mb
            assert correlation.hardware_config.is_virtual == expected_config.is_virtual
            
            # Correlation score should be valid
            assert 0.0 <= correlation.correlation_score <= 1.0
            
            # Should have correlation factors explaining the score
            assert isinstance(correlation.correlation_factors, list)
            assert isinstance(correlation.diagnostic_evidence, dict)
    
    @given(
        hardware_config=generate_hardware_config(),
        hardware_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        failure_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")))
    )
    @settings(max_examples=10, deadline=None)
    def test_report_generator_creates_hardware_specific_reports(self, hardware_config, hardware_id, failure_id):
        """Test that report generator creates hardware-specific reports."""
        # Arrange
        generator = HardwareFailureReportGenerator()
        
        # Create sample diagnostics and correlations
        diagnostic = HardwareSpecificDiagnostic(
            hardware_id=hardware_id,
            hardware_config=hardware_config,
            failure_type=HardwareFailureType.MEMORY_ERROR,
            diagnostic_data={
                "hardware_architecture": hardware_config.architecture,
                "hardware_memory_mb": hardware_config.memory_mb,
                "is_virtual": hardware_config.is_virtual
            }
        )
        
        from execution.hardware_failure_isolation import HardwareFailureCorrelation
        correlation = HardwareFailureCorrelation(
            failure_id=failure_id,
            hardware_id=hardware_id,
            hardware_config=hardware_config,
            correlation_score=0.8,
            correlation_factors=["High failure rate"],
            diagnostic_evidence={"failure_rate": 0.8}
        )
        
        # Act
        report = generator.generate_report(
            failure_id, hardware_id, hardware_config, [diagnostic], [correlation]
        )
        
        # Assert: Report should uniquely identify the hardware
        assert report.failure_id == failure_id
        assert report.hardware_id == hardware_id
        assert report.hardware_config.architecture == hardware_config.architecture
        assert report.hardware_config.memory_mb == hardware_config.memory_mb
        assert report.hardware_config.is_virtual == hardware_config.is_virtual
        
        # Report should contain the provided diagnostics and correlations
        assert len(report.diagnostics) == 1
        assert report.diagnostics[0].hardware_id == hardware_id
        
        assert len(report.correlations) == 1
        assert report.correlations[0].hardware_id == hardware_id
        assert report.correlations[0].failure_id == failure_id
        
        # Report should have valid confidence and recommendations
        assert 0.0 <= report.isolation_confidence <= 1.0
        assert isinstance(report.recommendations, list)
        assert len(report.recommendations) > 0  # Should have some recommendations
        
        # Report should have a unique ID
        assert report.report_id is not None
        assert len(report.report_id) > 0


if __name__ == "__main__":
    pytest.main([__file__])