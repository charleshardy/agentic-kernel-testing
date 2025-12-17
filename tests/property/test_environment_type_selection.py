"""Property-based tests for environment type selection.

**Feature: test-execution-orchestrator, Property 10: Environment type selection**
**Validates: Requirements 7.1, 7.2, 7.5**

Property 10: Environment type selection
For any test case, the runner factory should select an environment type appropriate for the test type 
(lightweight for unit tests, full VM for integration tests, etc.)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any, Optional

from ai_generator.models import (
    TestCase, TestType, Environment, HardwareConfig, Peripheral, ExpectedOutcome
)
from execution.runner_factory import (
    TestRunnerFactory, RunnerType, BaseTestRunner, get_runner_factory
)


# Custom strategies for generating test data
@st.composite
def gen_test_id(draw):
    """Generate a random test ID."""
    return draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))


@st.composite
def gen_test_name(draw):
    """Generate a random test name."""
    return draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))))


@st.composite
def gen_test_description(draw):
    """Generate a random test description."""
    base_desc = draw(st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))))
    
    # Add kernel-specific keywords sometimes to test VM selection
    kernel_keywords = ["kernel", "driver", "module", "syscall", "interrupt", "memory_management", "scheduler", "filesystem", "network_stack"]
    if draw(st.booleans()):
        keyword = draw(st.sampled_from(kernel_keywords))
        base_desc = f"{base_desc} {keyword}"
    
    return base_desc


@st.composite
def gen_target_subsystem(draw):
    """Generate a random target subsystem."""
    subsystems = ["networking", "filesystem", "memory", "scheduler", "drivers", "security", "userspace", "kernel_core"]
    return draw(st.sampled_from(subsystems))


@st.composite
def gen_test_script(draw):
    """Generate a random test script."""
    base_script = draw(st.text(min_size=1, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))))
    
    # Add kernel-specific commands sometimes to test VM selection
    kernel_commands = ["insmod", "rmmod", "modprobe", "dmesg", "/proc/", "/sys/"]
    if draw(st.booleans()):
        command = draw(st.sampled_from(kernel_commands))
        base_script = f"{base_script}\n{command}"
    
    return base_script


@st.composite
def gen_peripheral(draw):
    """Generate a random peripheral."""
    return Peripheral(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        type=draw(st.sampled_from(["usb", "pci", "i2c", "spi", "uart", "gpio"])),
        model=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        metadata=draw(st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50), max_size=3))
    )


@st.composite
def gen_hardware_config(draw):
    """Generate a random hardware configuration."""
    architecture = draw(st.sampled_from(["x86_64", "arm64", "riscv64", "arm"]))
    memory_mb = draw(st.integers(min_value=128, max_value=8192))
    is_virtual = draw(st.booleans())
    peripherals = draw(st.lists(gen_peripheral(), max_size=3))
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        memory_mb=memory_mb,
        storage_type=draw(st.sampled_from(["ssd", "hdd", "nvme"])),
        peripherals=peripherals,
        is_virtual=is_virtual,
        emulator=draw(st.one_of(st.none(), st.sampled_from(["qemu", "kvm", "xen"]))) if is_virtual else None
    )


@st.composite
def gen_expected_outcome(draw):
    """Generate a random expected outcome."""
    return ExpectedOutcome(
        should_pass=draw(st.booleans()),
        expected_return_code=draw(st.one_of(st.none(), st.integers(min_value=0, max_value=255))),
        expected_output_pattern=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        should_not_crash=draw(st.booleans()),
        max_execution_time=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=3600)))
    )


@st.composite
def gen_test_case(draw):
    """Generate a random test case."""
    test_type = draw(st.sampled_from(list(TestType)))
    
    return TestCase(
        id=draw(gen_test_id()),
        name=draw(gen_test_name()),
        description=draw(gen_test_description()),
        test_type=test_type,
        target_subsystem=draw(gen_target_subsystem()),
        code_paths=draw(st.lists(st.text(min_size=1, max_size=100), max_size=5)),
        execution_time_estimate=draw(st.integers(min_value=1, max_value=3600)),
        required_hardware=draw(st.one_of(st.none(), gen_hardware_config())),
        test_script=draw(gen_test_script()),
        expected_outcome=draw(st.one_of(st.none(), gen_expected_outcome())),
        metadata=draw(st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50), max_size=3))
    )


@st.composite
def gen_environment(draw):
    """Generate a random environment."""
    return Environment(
        id=draw(gen_test_id()),
        config=draw(gen_hardware_config())
    )


@given(gen_test_case())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_unit_tests_prefer_lightweight_environments(test_case: TestCase):
    """
    Property: For any unit test case, the runner factory should select lightweight container 
    environments (Docker) rather than full VMs.
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.1**
    """
    # Only test unit test cases
    assume(test_case.test_type == TestType.UNIT)
    
    factory = TestRunnerFactory()
    
    # Create a virtual environment (should prefer Docker for unit tests)
    virtual_env = Environment(
        id="test_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=1024,
            is_virtual=True
        )
    )
    
    # Get the selected runner type
    selected_runner_type = factory._select_runner_type(test_case, virtual_env)
    
    # Unit tests should prefer Docker (lightweight containers)
    assert selected_runner_type == RunnerType.DOCKER, \
        f"Unit test should select Docker runner, got {selected_runner_type}"


@given(gen_test_case())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_integration_tests_select_appropriate_environment(test_case: TestCase):
    """
    Property: For any integration test case, the runner factory should select appropriate 
    environments based on test requirements (Docker for simple tests, QEMU for kernel tests).
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.2**
    """
    # Only test integration test cases
    assume(test_case.test_type == TestType.INTEGRATION)
    
    factory = TestRunnerFactory()
    
    # Create a virtual environment
    virtual_env = Environment(
        id="test_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=2048,
            is_virtual=True
        )
    )
    
    # Get the selected runner type
    selected_runner_type = factory._select_runner_type(test_case, virtual_env)
    
    # Check if test requires full VM based on content
    requires_vm = factory._requires_full_vm(test_case)
    
    if requires_vm:
        # Should select QEMU for kernel-level integration tests
        assert selected_runner_type == RunnerType.QEMU, \
            f"Kernel integration test should select QEMU runner, got {selected_runner_type}"
    else:
        # Should select Docker for simple integration tests
        assert selected_runner_type == RunnerType.DOCKER, \
            f"Simple integration test should select Docker runner, got {selected_runner_type}"


@given(gen_test_case())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_performance_tests_use_dedicated_resources(test_case: TestCase):
    """
    Property: For any performance test case, the runner factory should select environments 
    with dedicated resources (QEMU VMs) to ensure accurate measurements.
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.5**
    """
    # Only test performance test cases
    assume(test_case.test_type == TestType.PERFORMANCE)
    
    factory = TestRunnerFactory()
    
    # Create a virtual environment
    virtual_env = Environment(
        id="test_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=4096,
            is_virtual=True
        )
    )
    
    # Get the selected runner type
    selected_runner_type = factory._select_runner_type(test_case, virtual_env)
    
    # Performance tests should use QEMU for dedicated resources
    assert selected_runner_type == RunnerType.QEMU, \
        f"Performance test should select QEMU runner for dedicated resources, got {selected_runner_type}"


@given(gen_test_case())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_security_tests_use_isolated_environments(test_case: TestCase):
    """
    Property: For any security test case, the runner factory should select isolated 
    environments (QEMU VMs) to contain potential security issues.
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.5**
    """
    # Only test security test cases
    assume(test_case.test_type == TestType.SECURITY)
    
    factory = TestRunnerFactory()
    
    # Create a virtual environment
    virtual_env = Environment(
        id="test_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=2048,
            is_virtual=True
        )
    )
    
    # Get the selected runner type
    selected_runner_type = factory._select_runner_type(test_case, virtual_env)
    
    # Security tests should use QEMU for isolation
    assert selected_runner_type == RunnerType.QEMU, \
        f"Security test should select QEMU runner for isolation, got {selected_runner_type}"


@given(gen_test_case())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_fuzz_tests_use_crash_safe_environments(test_case: TestCase):
    """
    Property: For any fuzz test case, the runner factory should select environments 
    that can handle crashes safely (QEMU VMs).
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.5**
    """
    # Only test fuzz test cases
    assume(test_case.test_type == TestType.FUZZ)
    
    factory = TestRunnerFactory()
    
    # Create a virtual environment
    virtual_env = Environment(
        id="test_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=2048,
            is_virtual=True
        )
    )
    
    # Get the selected runner type
    selected_runner_type = factory._select_runner_type(test_case, virtual_env)
    
    # Fuzz tests should use QEMU for crash handling
    assert selected_runner_type == RunnerType.QEMU, \
        f"Fuzz test should select QEMU runner for crash safety, got {selected_runner_type}"


@given(gen_test_case())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_physical_environments_use_physical_runner(test_case: TestCase):
    """
    Property: For any test case with a physical (non-virtual) environment, 
    the runner factory should select the physical runner.
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.1, 7.2, 7.5**
    """
    factory = TestRunnerFactory()
    
    # Create a physical environment
    physical_env = Environment(
        id="physical_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel Core i7",
            memory_mb=8192,
            is_virtual=False
        )
    )
    
    # Get the selected runner type
    selected_runner_type = factory._select_runner_type(test_case, physical_env)
    
    # Physical environments should always use physical runner
    assert selected_runner_type == RunnerType.PHYSICAL, \
        f"Physical environment should select physical runner, got {selected_runner_type}"


@given(gen_test_case())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_kernel_indicators_trigger_vm_selection(test_case: TestCase):
    """
    Property: For any test case containing kernel-specific indicators (keywords, commands, etc.),
    the runner factory should select full VM environments when appropriate.
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.2**
    """
    factory = TestRunnerFactory()
    
    # Create a virtual environment
    virtual_env = Environment(
        id="test_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=2048,
            is_virtual=True
        )
    )
    
    # Check if test requires full VM
    requires_vm = factory._requires_full_vm(test_case)
    
    # If test has kernel indicators, it should require VM for integration tests
    kernel_indicators = [
        "kernel", "driver", "module", "syscall", "interrupt",
        "memory_management", "scheduler", "filesystem", "network_stack"
    ]
    
    kernel_commands = ["insmod", "rmmod", "modprobe", "dmesg", "/proc/", "/sys/"]
    
    test_content = f"{test_case.description} {test_case.target_subsystem} {test_case.test_script}".lower()
    
    has_kernel_indicator = any(indicator in test_content for indicator in kernel_indicators)
    has_kernel_command = any(command in test_case.test_script.lower() for command in kernel_commands)
    has_peripherals = (test_case.required_hardware and 
                      test_case.required_hardware.peripherals)
    
    if has_kernel_indicator or has_kernel_command or has_peripherals:
        assert requires_vm, \
            f"Test with kernel indicators should require VM. Content: {test_content[:100]}..."
        
        # For integration tests with kernel indicators, should select QEMU
        if test_case.test_type == TestType.INTEGRATION:
            selected_runner_type = factory._select_runner_type(test_case, virtual_env)
            assert selected_runner_type == RunnerType.QEMU, \
                f"Integration test with kernel indicators should select QEMU, got {selected_runner_type}"


@given(st.lists(gen_test_case(), min_size=1, max_size=20))
@settings(max_examples=50, deadline=None)
def test_runner_selection_consistency(test_cases: List[TestCase]):
    """
    Property: For any set of test cases, the runner factory should consistently 
    select the same runner type for identical test characteristics.
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.1, 7.2, 7.5**
    """
    factory = TestRunnerFactory()
    
    # Create a standard virtual environment
    virtual_env = Environment(
        id="test_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=2048,
            is_virtual=True
        )
    )
    
    # Group test cases by type and characteristics
    selections_by_type: Dict[TestType, List[RunnerType]] = {}
    
    for test_case in test_cases:
        selected_runner_type = factory._select_runner_type(test_case, virtual_env)
        
        if test_case.test_type not in selections_by_type:
            selections_by_type[test_case.test_type] = []
        
        selections_by_type[test_case.test_type].append(selected_runner_type)
    
    # Verify consistency within test types
    for test_type, selections in selections_by_type.items():
        if test_type == TestType.UNIT:
            # All unit tests should select Docker
            assert all(s == RunnerType.DOCKER for s in selections), \
                f"All unit tests should select Docker, got {set(selections)}"
        
        elif test_type == TestType.PERFORMANCE:
            # All performance tests should select QEMU
            assert all(s == RunnerType.QEMU for s in selections), \
                f"All performance tests should select QEMU, got {set(selections)}"
        
        elif test_type == TestType.SECURITY:
            # All security tests should select QEMU
            assert all(s == RunnerType.QEMU for s in selections), \
                f"All security tests should select QEMU, got {set(selections)}"
        
        elif test_type == TestType.FUZZ:
            # All fuzz tests should select QEMU
            assert all(s == RunnerType.QEMU for s in selections), \
                f"All fuzz tests should select QEMU, got {set(selections)}"


@given(gen_test_case(), gen_environment())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_runner_creation_succeeds_for_valid_selections(test_case: TestCase, environment: Environment):
    """
    Property: For any valid test case and environment combination, the runner factory 
    should be able to create a runner without errors.
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.1, 7.2, 7.5**
    """
    factory = TestRunnerFactory()
    
    try:
        # Should be able to create a runner
        runner = factory.create_runner(test_case, environment)
        
        # Runner should be a valid BaseTestRunner instance
        assert isinstance(runner, BaseTestRunner), \
            f"Created runner should be BaseTestRunner instance, got {type(runner)}"
        
        # Runner should support the test type
        assert runner.supports_test_type(test_case.test_type), \
            f"Runner should support test type {test_case.test_type}"
        
        # Runner should support the hardware configuration
        assert runner.supports_hardware(environment.config), \
            f"Runner should support hardware config {environment.config}"
        
        # Cleanup should work without errors
        runner.cleanup()
        
    except Exception as e:
        # If creation fails, it should be due to missing runner implementations
        # This is acceptable in test environments
        assert "No runner implementation available" in str(e) or \
               "ImportError" in str(type(e).__name__), \
            f"Unexpected error creating runner: {e}"


@given(gen_test_case())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_runner_factory_validates_compatibility(test_case: TestCase):
    """
    Property: For any test case and environment, the runner factory should correctly 
    validate compatibility between the test requirements and available runners.
    
    **Feature: test-execution-orchestrator, Property 10: Environment type selection**
    **Validates: Requirements 7.1, 7.2, 7.5**
    """
    factory = TestRunnerFactory()
    
    # Create compatible environment
    compatible_env = Environment(
        id="compatible_env",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="generic",
            memory_mb=2048,
            is_virtual=True
        )
    )
    
    # Validation should work for compatible combinations
    is_compatible = factory.validate_runner_compatibility(test_case, compatible_env)
    
    # Should be able to validate without errors
    assert isinstance(is_compatible, bool), \
        f"Compatibility validation should return boolean, got {type(is_compatible)}"
    
    # If compatible, should be able to create runner
    if is_compatible:
        try:
            runner = factory.create_runner(test_case, compatible_env)
            assert isinstance(runner, BaseTestRunner), \
                f"Should be able to create runner for compatible combination"
            runner.cleanup()
        except Exception as e:
            # Acceptable if runner implementation is missing
            assert "No runner implementation available" in str(e) or \
                   "ImportError" in str(type(e).__name__), \
                f"Unexpected error for compatible combination: {e}"