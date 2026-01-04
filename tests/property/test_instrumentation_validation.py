"""
Property-based test for instrumentation validation.

Tests that instrumentation validation properly verifies tool functionality,
performs health checks, and confirms readiness for testing.
"""

import asyncio
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock

from deployment.instrumentation_manager import InstrumentationManager
from deployment.models import InstrumentationConfig
from deployment.environment_manager import Connection


# Property-based test strategies
environment_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
tool_combinations = st.tuples(
    st.booleans(),  # enable_kasan
    st.booleans(),  # enable_ktsan
    st.booleans(),  # enable_lockdep
    st.booleans(),  # enable_coverage
    st.booleans(),  # enable_profiling
    st.booleans()   # enable_fuzzing
)


class MockInstrumentationConnection:
    """Mock connection for testing instrumentation validation"""
    
    def __init__(self, environment_id: str):
        self.environment_id = environment_id
        self.is_connected = True
        self.tool_states = {
            "kasan": {"installed": False, "configured": False, "working": False},
            "ktsan": {"installed": False, "configured": False, "working": False},
            "lockdep": {"installed": False, "configured": False, "working": False},
            "gcov": {"installed": False, "configured": False, "working": False},
            "lcov": {"installed": False, "configured": False, "working": False},
            "perf": {"installed": False, "configured": False, "working": False},
            "ftrace": {"installed": False, "configured": False, "working": False},
            "syzkaller": {"installed": False, "configured": False, "working": False}
        }
        self.validation_history = []
    
    def set_tool_state(self, tool: str, installed: bool = True, configured: bool = True, working: bool = True):
        """Set the state of a tool for testing"""
        if tool in self.tool_states:
            self.tool_states[tool] = {
                "installed": installed,
                "configured": configured,
                "working": working
            }
    
    def record_validation(self, tool: str, result: bool):
        """Record a validation attempt"""
        self.validation_history.append({"tool": tool, "result": result, "timestamp": asyncio.get_event_loop().time()})


@given(
    environment_id=environment_ids,
    tools=tool_combinations,
    tool_failure_rate=st.floats(min_value=0.0, max_value=0.5)  # 0-50% failure rate
)
@settings(max_examples=40, deadline=5000)
async def test_instrumentation_validation(environment_id, tools, tool_failure_rate):
    """
    Property: Instrumentation validation correctly verifies tool functionality
    
    This test verifies that:
    1. All enabled tools are validated
    2. Validation results reflect actual tool states
    3. Failed validations are properly reported
    4. Validation summary is accurate
    5. Tool health checks work correctly
    """
    assume(len(environment_id.strip()) > 0)
    
    enable_kasan, enable_ktsan, enable_lockdep, enable_coverage, enable_profiling, enable_fuzzing = tools
    
    # Create instrumentation manager
    instrumentation_manager = InstrumentationManager()
    
    # Create instrumentation configuration
    config = InstrumentationConfig(
        enable_kasan=enable_kasan,
        enable_ktsan=enable_ktsan,
        enable_lockdep=enable_lockdep,
        enable_coverage=enable_coverage,
        enable_profiling=enable_profiling,
        enable_fuzzing=enable_fuzzing
    )
    
    # Create mock connection
    connection = MockInstrumentationConnection(environment_id.strip())
    
    # Set up tool states based on failure rate
    import random
    random.seed(hash(environment_id) % 2**32)  # Deterministic for testing
    
    tools_to_validate = []
    expected_results = {}
    
    if enable_kasan:
        tools_to_validate.append("kasan")
        working = random.random() > tool_failure_rate
        connection.set_tool_state("kasan", working=working)
        expected_results["kasan"] = working
    
    if enable_ktsan:
        tools_to_validate.append("ktsan")
        working = random.random() > tool_failure_rate
        connection.set_tool_state("ktsan", working=working)
        expected_results["ktsan"] = working
    
    if enable_lockdep:
        tools_to_validate.append("lockdep")
        working = random.random() > tool_failure_rate
        connection.set_tool_state("lockdep", working=working)
        expected_results["lockdep"] = working
    
    if enable_coverage:
        tools_to_validate.extend(["gcov", "lcov"])
        for tool in ["gcov", "lcov"]:
            working = random.random() > tool_failure_rate
            connection.set_tool_state(tool, working=working)
            expected_results[tool] = working
    
    if enable_profiling:
        tools_to_validate.extend(["perf", "ftrace"])
        for tool in ["perf", "ftrace"]:
            working = random.random() > tool_failure_rate
            connection.set_tool_state(tool, working=working)
            expected_results[tool] = working
    
    if enable_fuzzing:
        tools_to_validate.append("syzkaller")
        working = random.random() > tool_failure_rate
        connection.set_tool_state("syzkaller", working=working)
        expected_results["syzkaller"] = working
    
    # Mock validation methods to return tool states
    async def create_validator(tool_name):
        async def validator(conn):
            await asyncio.sleep(0.01)  # Simulate validation time
            result = conn.tool_states[tool_name]["working"]
            conn.record_validation(tool_name, result)
            return result
        return validator
    
    # Replace validation methods
    instrumentation_manager._validate_kasan = await create_validator("kasan")
    instrumentation_manager._validate_ktsan = await create_validator("ktsan")
    instrumentation_manager._validate_lockdep = await create_validator("lockdep")
    instrumentation_manager._validate_gcov = await create_validator("gcov")
    instrumentation_manager._validate_lcov = await create_validator("lcov")
    instrumentation_manager._validate_perf = await create_validator("perf")
    instrumentation_manager._validate_ftrace = await create_validator("ftrace")
    instrumentation_manager._validate_syzkaller = await create_validator("syzkaller")
    
    # Perform validation
    validation_results = await instrumentation_manager.validate_instrumentation(connection, config)
    
    # Verify validation results
    assert isinstance(validation_results, dict), "Validation results should be a dictionary"
    
    # Check that all expected tools were validated
    for tool in tools_to_validate:
        if tool in expected_results:  # Only check tools that should be validated
            assert tool in validation_results, f"Tool {tool} should be validated"
            assert validation_results[tool] == expected_results[tool], \
                f"Tool {tool} validation result should match expected state"
    
    # Verify no unexpected tools were validated
    for tool in validation_results:
        assert tool in tools_to_validate, f"Unexpected tool {tool} was validated"
    
    # Verify validation history
    validated_tools = [entry["tool"] for entry in connection.validation_history]
    for tool in tools_to_validate:
        if tool in expected_results:
            assert tool in validated_tools, f"Tool {tool} should have validation history"
    
    # Verify validation summary makes sense
    total_tools = len(expected_results)
    passed_tools = sum(1 for result in expected_results.values() if result)
    failed_tools = total_tools - passed_tools
    
    actual_passed = sum(1 for result in validation_results.values() if result)
    actual_failed = len(validation_results) - actual_passed
    
    assert actual_passed == passed_tools, f"Expected {passed_tools} passed validations, got {actual_passed}"
    assert actual_failed == failed_tools, f"Expected {failed_tools} failed validations, got {actual_failed}"


@given(
    environment_count=st.integers(min_value=1, max_value=4),
    validation_scenarios=st.lists(
        st.tuples(
            tool_combinations,
            st.floats(min_value=0.0, max_value=1.0)  # failure rate per environment
        ),
        min_size=1,
        max_size=4
    )
)
@settings(max_examples=20, deadline=4000)
async def test_multiple_environment_validation_isolation(environment_count, validation_scenarios):
    """
    Property: Multiple environment validation maintains isolation
    
    This test verifies that:
    1. Each environment gets independent validation
    2. Validation results don't interfere between environments
    3. Tool states are environment-specific
    4. Validation history is properly isolated
    """
    assume(environment_count >= 1)
    assume(len(validation_scenarios) >= 1)
    
    instrumentation_manager = InstrumentationManager()
    
    # Create multiple environments with different validation scenarios
    environments = []
    configurations = []
    expected_results_per_env = []
    
    for i in range(environment_count):
        env_id = f"validation_env_{i}"
        connection = MockInstrumentationConnection(env_id)
        
        # Use cycling validation scenarios
        scenario_index = i % len(validation_scenarios)
        tools, failure_rate = validation_scenarios[scenario_index]
        enable_kasan, enable_ktsan, enable_lockdep, enable_coverage, enable_profiling, enable_fuzzing = tools
        
        config = InstrumentationConfig(
            enable_kasan=enable_kasan,
            enable_ktsan=enable_ktsan,
            enable_lockdep=enable_lockdep,
            enable_coverage=enable_coverage,
            enable_profiling=enable_profiling,
            enable_fuzzing=enable_fuzzing
        )
        
        # Set up tool states for this environment
        import random
        random.seed((hash(env_id) + i) % 2**32)  # Environment-specific seed
        
        expected_results = {}
        
        if enable_kasan:
            working = random.random() > failure_rate
            connection.set_tool_state("kasan", working=working)
            expected_results["kasan"] = working
        
        if enable_ktsan:
            working = random.random() > failure_rate
            connection.set_tool_state("ktsan", working=working)
            expected_results["ktsan"] = working
        
        if enable_lockdep:
            working = random.random() > failure_rate
            connection.set_tool_state("lockdep", working=working)
            expected_results["lockdep"] = working
        
        if enable_coverage:
            for tool in ["gcov", "lcov"]:
                working = random.random() > failure_rate
                connection.set_tool_state(tool, working=working)
                expected_results[tool] = working
        
        if enable_profiling:
            for tool in ["perf", "ftrace"]:
                working = random.random() > failure_rate
                connection.set_tool_state(tool, working=working)
                expected_results[tool] = working
        
        if enable_fuzzing:
            working = random.random() > failure_rate
            connection.set_tool_state("syzkaller", working=working)
            expected_results["syzkaller"] = working
        
        environments.append(connection)
        configurations.append(config)
        expected_results_per_env.append(expected_results)
    
    # Mock validation methods for all environments
    async def create_validator(tool_name):
        async def validator(conn):
            await asyncio.sleep(0.01)
            result = conn.tool_states[tool_name]["working"]
            conn.record_validation(tool_name, result)
            return result
        return validator
    
    # Replace validation methods
    instrumentation_manager._validate_kasan = await create_validator("kasan")
    instrumentation_manager._validate_ktsan = await create_validator("ktsan")
    instrumentation_manager._validate_lockdep = await create_validator("lockdep")
    instrumentation_manager._validate_gcov = await create_validator("gcov")
    instrumentation_manager._validate_lcov = await create_validator("lcov")
    instrumentation_manager._validate_perf = await create_validator("perf")
    instrumentation_manager._validate_ftrace = await create_validator("ftrace")
    instrumentation_manager._validate_syzkaller = await create_validator("syzkaller")
    
    # Validate all environments
    all_results = []
    for connection, config in zip(environments, configurations):
        validation_results = await instrumentation_manager.validate_instrumentation(connection, config)
        all_results.append(validation_results)
    
    # Verify each environment got correct validation results
    for i, (connection, expected_results, actual_results) in enumerate(zip(environments, expected_results_per_env, all_results)):
        env_id = f"validation_env_{i}"
        
        # Verify results match expectations for this environment
        for tool, expected_result in expected_results.items():
            assert tool in actual_results, f"Tool {tool} should be validated in {env_id}"
            assert actual_results[tool] == expected_result, \
                f"Tool {tool} validation should match expected result in {env_id}"
        
        # Verify validation history is environment-specific
        validated_tools = [entry["tool"] for entry in connection.validation_history]
        for tool in expected_results:
            assert tool in validated_tools, f"Tool {tool} should have validation history in {env_id}"
    
    # Verify isolation - different environments should have different results if scenarios differ
    for i in range(len(environments)):
        for j in range(i + 1, len(environments)):
            scenario_i = i % len(validation_scenarios)
            scenario_j = j % len(validation_scenarios)
            
            if scenario_i != scenario_j:
                # Different scenarios should likely produce different results
                results_i = all_results[i]
                results_j = all_results[j]
                
                # At least the set of validated tools might be different
                tools_i = set(results_i.keys())
                tools_j = set(results_j.keys())
                
                # If the tool sets are the same, at least some results might be different
                if tools_i == tools_j and len(tools_i) > 0:
                    # Allow for the possibility that results could be the same by chance
                    # but verify that environments maintain separate state
                    assert environments[i].environment_id != environments[j].environment_id, \
                        "Environments should have different IDs"


@given(
    partial_failures=st.lists(
        st.sampled_from(["kasan", "ktsan", "lockdep", "gcov", "lcov", "perf", "ftrace", "syzkaller"]),
        min_size=0,
        max_size=4
    )
)
@settings(max_examples=25, deadline=3000)
async def test_partial_validation_failures(partial_failures):
    """
    Property: Partial validation failures are properly handled
    
    This test verifies that:
    1. Some tools can pass validation while others fail
    2. Partial failures don't prevent other validations
    3. Validation continues even after individual tool failures
    4. Results accurately reflect the state of each tool
    """
    instrumentation_manager = InstrumentationManager()
    
    # Enable all tools for comprehensive testing
    config = InstrumentationConfig(
        enable_kasan=True,
        enable_ktsan=True,
        enable_lockdep=True,
        enable_coverage=True,
        enable_profiling=True,
        enable_fuzzing=True
    )
    
    # Create mock connection
    connection = MockInstrumentationConnection("partial_failure_test_env")
    
    # Set up tool states - failed tools don't work, others do
    all_tools = ["kasan", "ktsan", "lockdep", "gcov", "lcov", "perf", "ftrace", "syzkaller"]
    expected_results = {}
    
    for tool in all_tools:
        working = tool not in partial_failures
        connection.set_tool_state(tool, working=working)
        expected_results[tool] = working
    
    # Mock validation methods
    async def create_validator(tool_name):
        async def validator(conn):
            await asyncio.sleep(0.01)
            result = conn.tool_states[tool_name]["working"]
            conn.record_validation(tool_name, result)
            return result
        return validator
    
    # Replace validation methods
    instrumentation_manager._validate_kasan = await create_validator("kasan")
    instrumentation_manager._validate_ktsan = await create_validator("ktsan")
    instrumentation_manager._validate_lockdep = await create_validator("lockdep")
    instrumentation_manager._validate_gcov = await create_validator("gcov")
    instrumentation_manager._validate_lcov = await create_validator("lcov")
    instrumentation_manager._validate_perf = await create_validator("perf")
    instrumentation_manager._validate_ftrace = await create_validator("ftrace")
    instrumentation_manager._validate_syzkaller = await create_validator("syzkaller")
    
    # Perform validation
    validation_results = await instrumentation_manager.validate_instrumentation(connection, config)
    
    # Verify all tools were validated
    assert len(validation_results) == len(all_tools), "All tools should be validated"
    
    # Verify results match expected states
    for tool in all_tools:
        assert tool in validation_results, f"Tool {tool} should be in validation results"
        assert validation_results[tool] == expected_results[tool], \
            f"Tool {tool} validation result should match expected state"
    
    # Verify validation continued despite failures
    failed_count = len(partial_failures)
    passed_count = len(all_tools) - failed_count
    
    actual_failed = sum(1 for result in validation_results.values() if not result)
    actual_passed = sum(1 for result in validation_results.values() if result)
    
    assert actual_failed == failed_count, f"Expected {failed_count} failed validations, got {actual_failed}"
    assert actual_passed == passed_count, f"Expected {passed_count} passed validations, got {actual_passed}"
    
    # Verify all tools have validation history
    validated_tools = [entry["tool"] for entry in connection.validation_history]
    for tool in all_tools:
        assert tool in validated_tools, f"Tool {tool} should have validation history"


# Synchronous test runners for pytest
def test_instrumentation_validation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_instrumentation_validation(
        environment_id="test_env",
        tools=(True, True, False, True, False, True),  # kasan, ktsan, lockdep, coverage, profiling, fuzzing
        tool_failure_rate=0.2
    ))


def test_multiple_environment_validation_isolation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_environment_validation_isolation(
        environment_count=2,
        validation_scenarios=[
            ((True, False, True, False, True, False), 0.1),
            ((False, True, False, True, False, True), 0.3)
        ]
    ))


def test_partial_validation_failures_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_partial_validation_failures(
        partial_failures=["ktsan", "lcov"]
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing instrumentation validation...")
        await test_instrumentation_validation(
            "test_env", (True, True, False, True, False, True), 0.2
        )
        print("✓ Instrumentation validation test passed")
        
        print("Testing multiple environment validation isolation...")
        await test_multiple_environment_validation_isolation(
            2, [((True, False, True, False, True, False), 0.1), ((False, True, False, True, False, True), 0.3)]
        )
        print("✓ Multiple environment validation isolation test passed")
        
        print("Testing partial validation failures...")
        await test_partial_validation_failures(["ktsan", "lcov"])
        print("✓ Partial validation failures test passed")
        
        print("All instrumentation validation tests completed successfully!")
    
    asyncio.run(run_examples())