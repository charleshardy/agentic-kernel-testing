"""
Property-based test for performance monitoring setup.

Tests that performance monitoring tools (perf, ftrace) are properly configured
and integrated for comprehensive performance analysis during testing.
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
sample_rates = st.integers(min_value=100, max_value=10000)
monitoring_tools = st.lists(
    st.sampled_from(["perf", "ftrace", "oprofile", "systemtap", "bpftrace"]),
    min_size=0,
    max_size=5
)


class MockPerformanceConnection:
    """Mock connection for testing performance monitoring setup"""
    
    def __init__(self, environment_id: str):
        self.environment_id = environment_id
        self.is_connected = True
        self.executed_commands = []
        self.performance_tools = {
            "perf": {"installed": False, "configured": False, "enabled": False},
            "ftrace": {"installed": False, "configured": False, "enabled": False},
            "oprofile": {"installed": False, "configured": False, "enabled": False},
            "systemtap": {"installed": False, "configured": False, "enabled": False},
            "bpftrace": {"installed": False, "configured": False, "enabled": False}
        }
        self.profiling_config = {}
        self.monitoring_sessions = []
    
    def execute_command(self, command: str):
        """Mock command execution for performance tools"""
        self.executed_commands.append(command)
        
        # Simulate performance tool installation/configuration
        for tool in self.performance_tools:
            if tool in command.lower():
                if "install" in command.lower() or "setup" in command.lower():
                    self.performance_tools[tool]["installed"] = True
                elif "configure" in command.lower():
                    self.performance_tools[tool]["configured"] = True
                elif "enable" in command.lower():
                    self.performance_tools[tool]["enabled"] = True
    
    def set_profiling_config(self, config: dict):
        """Mock profiling configuration setting"""
        self.profiling_config.update(config)
    
    def start_monitoring_session(self, tool: str, config: dict):
        """Mock monitoring session start"""
        self.monitoring_sessions.append({
            "tool": tool,
            "config": config,
            "status": "active"
        })


@given(
    environment_id=environment_ids,
    enable_profiling=st.booleans(),
    sample_rate=sample_rates,
    tools=monitoring_tools
)
@settings(max_examples=40, deadline=5000)
async def test_performance_monitoring_setup(environment_id, enable_profiling, sample_rate, tools):
    """
    Property: Performance monitoring setup enables comprehensive profiling
    
    This test verifies that:
    1. Performance monitoring tools are properly installed and configured
    2. Profiling parameters (sample rates, events) are set correctly
    3. Multiple monitoring tools can work together
    4. Performance data collection is properly initialized
    5. Tool configurations are environment-specific
    """
    assume(len(environment_id.strip()) > 0)
    assume(sample_rate >= 100)
    
    # Create instrumentation manager
    instrumentation_manager = InstrumentationManager()
    
    # Create instrumentation configuration
    config = InstrumentationConfig(
        enable_profiling=enable_profiling,
        profiling_config={
            "perf_enabled": True,
            "ftrace_enabled": True,
            "sample_rate": sample_rate,
            "events": ["cpu-cycles", "instructions", "cache-misses"],
            "output_dir": f"/tmp/profiling/{environment_id.strip()}",
            "duration_seconds": 300
        } if enable_profiling else {},
        monitoring_tools=tools
    )
    
    # Create mock connection
    connection = MockPerformanceConnection(environment_id.strip())
    
    # Track performance tool setup calls
    perf_calls = []
    ftrace_calls = []
    tool_config_calls = []
    
    async def mock_setup_perf(conn):
        perf_calls.append(conn.environment_id)
        conn.execute_command("setup_perf")
        conn.performance_tools["perf"]["installed"] = True
        conn.performance_tools["perf"]["configured"] = True
        
        # Configure perf with profiling settings
        if enable_profiling:
            perf_config = {
                "sample_rate": sample_rate,
                "events": config.profiling_config.get("events", []),
                "output_dir": config.profiling_config.get("output_dir")
            }
            conn.set_profiling_config({"perf": perf_config})
            conn.start_monitoring_session("perf", perf_config)
        
        await asyncio.sleep(0.01)
    
    async def mock_enable_ftrace(conn):
        ftrace_calls.append(conn.environment_id)
        conn.execute_command("enable_ftrace")
        conn.performance_tools["ftrace"]["installed"] = True
        conn.performance_tools["ftrace"]["enabled"] = True
        
        # Configure ftrace
        if enable_profiling:
            ftrace_config = {
                "tracers": ["function", "function_graph"],
                "buffer_size": "1024KB",
                "output_dir": config.profiling_config.get("output_dir")
            }
            conn.set_profiling_config({"ftrace": ftrace_config})
            conn.start_monitoring_session("ftrace", ftrace_config)
        
        await asyncio.sleep(0.01)
    
    async def mock_configure_monitoring_tool(conn, tool):
        tool_config_calls.append((conn.environment_id, tool))
        conn.execute_command(f"configure_{tool}")
        
        if tool in conn.performance_tools:
            conn.performance_tools[tool]["installed"] = True
            conn.performance_tools[tool]["configured"] = True
        
        await asyncio.sleep(0.01)
    
    # Replace private methods with mocks
    instrumentation_manager._setup_perf = mock_setup_perf
    instrumentation_manager._enable_ftrace = mock_enable_ftrace
    instrumentation_manager._configure_monitoring_tool = mock_configure_monitoring_tool
    
    # Configure performance monitoring
    result = await instrumentation_manager.configure_performance_monitoring(connection, config)
    
    # Verify configuration result
    assert result is True, "Performance monitoring configuration should always succeed"
    
    if enable_profiling:
        # Verify perf setup
        assert len(perf_calls) == 1, "perf should be set up once"
        assert perf_calls[0] == environment_id.strip(), "perf should be set up for correct environment"
        assert connection.performance_tools["perf"]["installed"] is True, "perf should be marked as installed"
        assert connection.performance_tools["perf"]["configured"] is True, "perf should be marked as configured"
        
        # Verify ftrace setup
        assert len(ftrace_calls) == 1, "ftrace should be enabled once"
        assert ftrace_calls[0] == environment_id.strip(), "ftrace should be enabled for correct environment"
        assert connection.performance_tools["ftrace"]["installed"] is True, "ftrace should be marked as installed"
        assert connection.performance_tools["ftrace"]["enabled"] is True, "ftrace should be marked as enabled"
        
        # Verify profiling configuration
        assert "perf" in connection.profiling_config, "perf configuration should be set"
        assert connection.profiling_config["perf"]["sample_rate"] == sample_rate, "Sample rate should be configured correctly"
        assert "ftrace" in connection.profiling_config, "ftrace configuration should be set"
        
        # Verify monitoring sessions
        perf_sessions = [s for s in connection.monitoring_sessions if s["tool"] == "perf"]
        ftrace_sessions = [s for s in connection.monitoring_sessions if s["tool"] == "ftrace"]
        assert len(perf_sessions) == 1, "perf monitoring session should be started"
        assert len(ftrace_sessions) == 1, "ftrace monitoring session should be started"
        
        # Verify additional monitoring tools
        expected_tool_calls = len(tools)
        actual_tool_calls = len(tool_config_calls)
        assert actual_tool_calls == expected_tool_calls, f"Expected {expected_tool_calls} tool configurations, got {actual_tool_calls}"
        
        for tool in tools:
            tool_calls_for_env = [call for call in tool_config_calls if call[0] == environment_id.strip() and call[1] == tool]
            assert len(tool_calls_for_env) == 1, f"Tool {tool} should be configured once for environment"
        
    else:
        # When profiling is disabled, no tools should be set up
        assert len(perf_calls) == 0, "perf should not be set up when profiling is disabled"
        assert len(ftrace_calls) == 0, "ftrace should not be enabled when profiling is disabled"
        assert len(tool_config_calls) == 0, "No additional tools should be configured when profiling is disabled"
        
        # Tools should remain in default state
        assert connection.performance_tools["perf"]["installed"] is False, "perf should not be installed"
        assert connection.performance_tools["ftrace"]["installed"] is False, "ftrace should not be installed"


@given(
    environment_count=st.integers(min_value=1, max_value=4),
    profiling_configs=st.lists(
        st.tuples(
            st.booleans(),  # enable_profiling
            sample_rates,
            monitoring_tools
        ),
        min_size=1,
        max_size=4
    )
)
@settings(max_examples=25, deadline=4000)
async def test_multiple_environment_performance_monitoring(environment_count, profiling_configs):
    """
    Property: Multiple environment performance monitoring maintains isolation
    
    This test verifies that:
    1. Each environment gets its own performance monitoring configuration
    2. Profiling settings don't interfere between environments
    3. Different sample rates and tools are used for different environments
    4. Performance monitoring sessions are environment-specific
    """
    assume(environment_count >= 1)
    assume(len(profiling_configs) >= 1)
    
    instrumentation_manager = InstrumentationManager()
    
    # Create multiple environments with different profiling configurations
    environments = []
    configurations = []
    
    for i in range(environment_count):
        env_id = f"perf_env_{i}"
        connection = MockPerformanceConnection(env_id)
        
        # Use cycling profiling configurations
        config_index = i % len(profiling_configs)
        enable_profiling, sample_rate, tools = profiling_configs[config_index]
        
        config = InstrumentationConfig(
            enable_profiling=enable_profiling,
            profiling_config={
                "perf_enabled": True,
                "ftrace_enabled": True,
                "sample_rate": sample_rate,
                "events": [f"event_{i}_cycles", f"event_{i}_instructions"],
                "output_dir": f"/tmp/profiling/env_{i}",
                "environment_id": env_id
            } if enable_profiling else {},
            monitoring_tools=tools
        )
        
        environments.append(connection)
        configurations.append((config, enable_profiling, sample_rate, tools))
    
    # Track all performance monitoring calls
    all_perf_calls = []
    all_ftrace_calls = []
    all_tool_calls = []
    
    async def mock_setup_perf(conn):
        all_perf_calls.append(conn.environment_id)
        conn.execute_command("setup_perf")
        conn.performance_tools["perf"]["installed"] = True
        conn.performance_tools["perf"]["configured"] = True
        
        # Find the configuration for this environment
        env_index = int(conn.environment_id.split("_")[-1])
        config_index = env_index % len(profiling_configs)
        enable_profiling, sample_rate, tools = profiling_configs[config_index]
        
        if enable_profiling:
            perf_config = {
                "sample_rate": sample_rate,
                "environment_id": conn.environment_id,
                "events": [f"event_{env_index}_cycles", f"event_{env_index}_instructions"]
            }
            conn.set_profiling_config({"perf": perf_config})
            conn.start_monitoring_session("perf", perf_config)
    
    async def mock_enable_ftrace(conn):
        all_ftrace_calls.append(conn.environment_id)
        conn.execute_command("enable_ftrace")
        conn.performance_tools["ftrace"]["installed"] = True
        conn.performance_tools["ftrace"]["enabled"] = True
        
        env_index = int(conn.environment_id.split("_")[-1])
        ftrace_config = {
            "tracers": [f"tracer_{env_index}"],
            "environment_id": conn.environment_id
        }
        conn.set_profiling_config({"ftrace": ftrace_config})
        conn.start_monitoring_session("ftrace", ftrace_config)
    
    async def mock_configure_monitoring_tool(conn, tool):
        all_tool_calls.append((conn.environment_id, tool))
        conn.execute_command(f"configure_{tool}")
        if tool in conn.performance_tools:
            conn.performance_tools[tool]["configured"] = True
    
    # Replace private methods
    instrumentation_manager._setup_perf = mock_setup_perf
    instrumentation_manager._enable_ftrace = mock_enable_ftrace
    instrumentation_manager._configure_monitoring_tool = mock_configure_monitoring_tool
    
    # Configure all environments
    results = []
    for connection, (config, enable_profiling, sample_rate, tools) in zip(environments, configurations):
        result = await instrumentation_manager.configure_performance_monitoring(connection, config)
        results.append(result)
    
    # Verify all configurations succeeded
    assert all(results), "All performance monitoring configurations should succeed"
    
    # Verify each environment got correct configuration
    for i, (connection, (config, enable_profiling, sample_rate, tools)) in enumerate(zip(environments, configurations)):
        env_id = f"perf_env_{i}"
        
        if enable_profiling:
            # Verify tools were set up for this environment
            assert env_id in all_perf_calls, f"perf should be set up for {env_id}"
            assert env_id in all_ftrace_calls, f"ftrace should be enabled for {env_id}"
            
            # Verify environment-specific configuration
            assert "perf" in connection.profiling_config, f"perf config should exist for {env_id}"
            assert connection.profiling_config["perf"]["sample_rate"] == sample_rate, \
                f"Sample rate should be correct for {env_id}"
            assert connection.profiling_config["perf"]["environment_id"] == env_id, \
                f"Environment ID should be set in perf config for {env_id}"
            
            # Verify monitoring sessions
            perf_sessions = [s for s in connection.monitoring_sessions if s["tool"] == "perf"]
            assert len(perf_sessions) == 1, f"perf session should exist for {env_id}"
            
            # Verify additional tools
            for tool in tools:
                tool_calls_for_env = [call for call in all_tool_calls if call[0] == env_id and call[1] == tool]
                assert len(tool_calls_for_env) == 1, f"Tool {tool} should be configured for {env_id}"
        
        else:
            # Verify tools were not set up
            assert env_id not in all_perf_calls, f"perf should not be set up for {env_id}"
            assert env_id not in all_ftrace_calls, f"ftrace should not be enabled for {env_id}"
    
    # Verify isolation - each environment should have unique configurations
    enabled_environments = [
        (conn, sample_rate, i) 
        for i, (conn, (config, enable_profiling, sample_rate, tools)) in enumerate(zip(environments, configurations))
        if enable_profiling
    ]
    
    for i, (env1, sample_rate1, index1) in enumerate(enabled_environments):
        for j, (env2, sample_rate2, index2) in enumerate(enabled_environments):
            if i != j:
                # Sample rates might be the same, but environment IDs should be different
                assert env1.profiling_config["perf"]["environment_id"] != env2.profiling_config["perf"]["environment_id"], \
                    "Different environments should have different environment IDs in config"


@given(
    enable_profiling=st.booleans(),
    perf_failure=st.booleans(),
    ftrace_failure=st.booleans()
)
@settings(max_examples=30, deadline=3000)
async def test_performance_monitoring_validation(enable_profiling, perf_failure, ftrace_failure):
    """
    Property: Performance monitoring validation detects configuration issues
    
    This test verifies that:
    1. Validation correctly identifies working performance tools
    2. Validation detects failed performance tool configurations
    3. Partial performance tool failures are properly reported
    4. Validation results reflect actual tool states
    """
    instrumentation_manager = InstrumentationManager()
    
    # Create configuration
    config = InstrumentationConfig(
        enable_profiling=enable_profiling
    )
    
    # Create mock connection
    connection = MockPerformanceConnection("perf_validation_env")
    
    # Set up tool states based on failure flags
    if enable_profiling:
        connection.performance_tools["perf"]["installed"] = not perf_failure
        connection.performance_tools["perf"]["configured"] = not perf_failure
        connection.performance_tools["ftrace"]["installed"] = not ftrace_failure
        connection.performance_tools["ftrace"]["enabled"] = not ftrace_failure
    
    # Mock validation methods
    async def mock_validate_perf(conn):
        await asyncio.sleep(0.01)
        return conn.performance_tools["perf"]["installed"] and conn.performance_tools["perf"]["configured"]
    
    async def mock_validate_ftrace(conn):
        await asyncio.sleep(0.01)
        return conn.performance_tools["ftrace"]["installed"] and conn.performance_tools["ftrace"]["enabled"]
    
    # Replace validation methods
    instrumentation_manager._validate_perf = mock_validate_perf
    instrumentation_manager._validate_ftrace = mock_validate_ftrace
    
    # Validate instrumentation
    validation_results = await instrumentation_manager.validate_instrumentation(connection, config)
    
    # Verify validation results
    if enable_profiling:
        assert "perf" in validation_results, "perf validation should be performed"
        assert "ftrace" in validation_results, "ftrace validation should be performed"
        
        expected_perf_result = not perf_failure
        expected_ftrace_result = not ftrace_failure
        
        assert validation_results["perf"] == expected_perf_result, \
            f"perf validation should return {expected_perf_result}"
        assert validation_results["ftrace"] == expected_ftrace_result, \
            f"ftrace validation should return {expected_ftrace_result}"
    else:
        assert "perf" not in validation_results, "perf validation should not be performed when profiling is disabled"
        assert "ftrace" not in validation_results, "ftrace validation should not be performed when profiling is disabled"


# Synchronous test runners for pytest
def test_performance_monitoring_setup_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_performance_monitoring_setup(
        environment_id="perf_test_env",
        enable_profiling=True,
        sample_rate=1000,
        tools=["perf", "ftrace", "bpftrace"]
    ))


def test_multiple_environment_performance_monitoring_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_environment_performance_monitoring(
        environment_count=2,
        profiling_configs=[
            (True, 1000, ["perf", "ftrace"]),
            (True, 2000, ["bpftrace"])
        ]
    ))


def test_performance_monitoring_validation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_performance_monitoring_validation(
        enable_profiling=True,
        perf_failure=False,
        ftrace_failure=True
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing performance monitoring setup...")
        await test_performance_monitoring_setup(
            "perf_env", True, 1000, ["perf", "ftrace"]
        )
        print("✓ Performance monitoring setup test passed")
        
        print("Testing multiple environment performance monitoring...")
        await test_multiple_environment_performance_monitoring(
            2, [(True, 1000, ["perf"]), (True, 2000, ["ftrace"])]
        )
        print("✓ Multiple environment performance monitoring test passed")
        
        print("Testing performance monitoring validation...")
        await test_performance_monitoring_validation(True, False, True)
        print("✓ Performance monitoring validation test passed")
        
        print("All performance monitoring setup tests completed successfully!")
    
    asyncio.run(run_examples())