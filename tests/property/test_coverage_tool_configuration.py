"""
Property-based test for coverage tool configuration.

Tests that code coverage tools (gcov, lcov) are properly configured
and integrated into the deployment pipeline for comprehensive testing coverage.
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
coverage_output_dirs = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd')))
coverage_formats = st.lists(
    st.sampled_from(["html", "xml", "json", "lcov"]),
    min_size=1,
    max_size=4
)


class MockCoverageConnection:
    """Mock connection for testing coverage tool configuration"""
    
    def __init__(self, environment_id: str):
        self.environment_id = environment_id
        self.is_connected = True
        self.executed_commands = []
        self.coverage_tools = {
            "gcov": {"installed": False, "configured": False, "enabled": False},
            "lcov": {"installed": False, "configured": False, "enabled": False}
        }
        self.coverage_config = {}
        self.coverage_data_paths = []
    
    def execute_command(self, command: str):
        """Mock command execution for coverage tools"""
        self.executed_commands.append(command)
        
        # Simulate coverage tool installation/configuration
        if "gcov" in command.lower():
            if "install" in command.lower() or "enable" in command.lower():
                self.coverage_tools["gcov"]["installed"] = True
                self.coverage_tools["gcov"]["enabled"] = True
            elif "configure" in command.lower():
                self.coverage_tools["gcov"]["configured"] = True
        
        elif "lcov" in command.lower():
            if "install" in command.lower():
                self.coverage_tools["lcov"]["installed"] = True
            elif "configure" in command.lower():
                self.coverage_tools["lcov"]["configured"] = True
    
    def set_coverage_config(self, config: dict):
        """Mock coverage configuration setting"""
        self.coverage_config.update(config)
    
    def add_coverage_path(self, path: str):
        """Mock coverage data path addition"""
        self.coverage_data_paths.append(path)


@given(
    environment_id=environment_ids,
    enable_coverage=st.booleans(),
    output_dir=coverage_output_dirs,
    formats=coverage_formats
)
@settings(max_examples=40, deadline=5000)
async def test_coverage_tool_configuration(environment_id, enable_coverage, output_dir, formats):
    """
    Property: Coverage tool configuration enables proper code coverage collection
    
    This test verifies that:
    1. Coverage tools are properly installed and configured
    2. Coverage data collection is set up correctly
    3. Output directories and formats are configured as specified
    4. Coverage tools work together (gcov + lcov)
    5. Configuration is environment-specific
    """
    assume(len(environment_id.strip()) > 0)
    assume(len(output_dir.strip()) > 0)
    
    # Create instrumentation manager
    instrumentation_manager = InstrumentationManager()
    
    # Create instrumentation configuration
    config = InstrumentationConfig(
        enable_coverage=enable_coverage,
        coverage_config={
            "gcov_enabled": True,
            "lcov_enabled": True,
            "output_dir": f"/tmp/coverage/{output_dir.strip()}",
            "formats": formats,
            "include_patterns": ["*.c", "*.h"],
            "exclude_patterns": ["test_*", "*_test.c"]
        } if enable_coverage else {}
    )
    
    # Create mock connection
    connection = MockCoverageConnection(environment_id.strip())
    
    # Track coverage tool setup calls
    gcov_calls = []
    lcov_calls = []
    collection_calls = []
    
    async def mock_enable_gcov(conn):
        gcov_calls.append(conn.environment_id)
        conn.execute_command("enable_gcov")
        conn.coverage_tools["gcov"]["installed"] = True
        conn.coverage_tools["gcov"]["enabled"] = True
        await asyncio.sleep(0.01)
    
    async def mock_install_lcov(conn):
        lcov_calls.append(conn.environment_id)
        conn.execute_command("install_lcov")
        conn.coverage_tools["lcov"]["installed"] = True
        await asyncio.sleep(0.01)
    
    async def mock_setup_coverage_collection(conn):
        collection_calls.append(conn.environment_id)
        conn.execute_command("setup_coverage_collection")
        
        # Configure coverage based on config
        if enable_coverage:
            coverage_config = config.coverage_config
            conn.set_coverage_config({
                "output_dir": coverage_config.get("output_dir"),
                "formats": coverage_config.get("formats", []),
                "gcov_enabled": coverage_config.get("gcov_enabled", False),
                "lcov_enabled": coverage_config.get("lcov_enabled", False)
            })
            conn.add_coverage_path(coverage_config.get("output_dir", "/tmp/coverage"))
        
        await asyncio.sleep(0.01)
    
    # Replace private methods with mocks
    instrumentation_manager._enable_gcov = mock_enable_gcov
    instrumentation_manager._install_lcov = mock_install_lcov
    instrumentation_manager._setup_coverage_collection = mock_setup_coverage_collection
    
    # Configure code coverage
    result = await instrumentation_manager.configure_code_coverage(connection, config)
    
    # Verify configuration result
    assert result is True, "Coverage configuration should always succeed"
    
    if enable_coverage:
        # Verify gcov setup
        assert len(gcov_calls) == 1, "gcov should be enabled once"
        assert gcov_calls[0] == environment_id.strip(), "gcov should be enabled for correct environment"
        assert connection.coverage_tools["gcov"]["installed"] is True, "gcov should be marked as installed"
        assert connection.coverage_tools["gcov"]["enabled"] is True, "gcov should be marked as enabled"
        
        # Verify lcov setup
        assert len(lcov_calls) == 1, "lcov should be installed once"
        assert lcov_calls[0] == environment_id.strip(), "lcov should be installed for correct environment"
        assert connection.coverage_tools["lcov"]["installed"] is True, "lcov should be marked as installed"
        
        # Verify coverage collection setup
        assert len(collection_calls) == 1, "Coverage collection should be set up once"
        assert collection_calls[0] == environment_id.strip(), "Coverage collection should be set up for correct environment"
        
        # Verify coverage configuration
        expected_output_dir = f"/tmp/coverage/{output_dir.strip()}"
        assert connection.coverage_config.get("output_dir") == expected_output_dir, "Output directory should be configured correctly"
        assert connection.coverage_config.get("formats") == formats, "Coverage formats should be configured correctly"
        assert connection.coverage_config.get("gcov_enabled") is True, "gcov should be enabled in config"
        assert connection.coverage_config.get("lcov_enabled") is True, "lcov should be enabled in config"
        
        # Verify coverage data paths
        assert expected_output_dir in connection.coverage_data_paths, "Coverage output directory should be added to paths"
        
    else:
        # When coverage is disabled, no tools should be set up
        assert len(gcov_calls) == 0, "gcov should not be enabled when coverage is disabled"
        assert len(lcov_calls) == 0, "lcov should not be installed when coverage is disabled"
        assert len(collection_calls) == 0, "Coverage collection should not be set up when coverage is disabled"
        
        # Tools should remain in default state
        assert connection.coverage_tools["gcov"]["installed"] is False, "gcov should not be installed"
        assert connection.coverage_tools["lcov"]["installed"] is False, "lcov should not be installed"


@given(
    environment_count=st.integers(min_value=1, max_value=4),
    coverage_configs=st.lists(
        st.tuples(
            st.booleans(),  # enable_coverage
            coverage_output_dirs,
            coverage_formats
        ),
        min_size=1,
        max_size=4
    )
)
@settings(max_examples=25, deadline=4000)
async def test_multiple_environment_coverage_configuration(environment_count, coverage_configs):
    """
    Property: Multiple environment coverage configuration maintains isolation
    
    This test verifies that:
    1. Each environment gets its own coverage configuration
    2. Coverage settings don't interfere between environments
    3. Different output directories are used for different environments
    4. Coverage tool states are environment-specific
    """
    assume(environment_count >= 1)
    assume(len(coverage_configs) >= 1)
    
    instrumentation_manager = InstrumentationManager()
    
    # Create multiple environments with different coverage configurations
    environments = []
    configurations = []
    
    for i in range(environment_count):
        env_id = f"coverage_env_{i}"
        connection = MockCoverageConnection(env_id)
        
        # Use cycling coverage configurations
        config_index = i % len(coverage_configs)
        enable_coverage, output_dir, formats = coverage_configs[config_index]
        
        config = InstrumentationConfig(
            enable_coverage=enable_coverage,
            coverage_config={
                "gcov_enabled": True,
                "lcov_enabled": True,
                "output_dir": f"/tmp/coverage/{output_dir.strip()}_{i}",
                "formats": formats,
                "environment_id": env_id
            } if enable_coverage else {}
        )
        
        environments.append(connection)
        configurations.append((config, enable_coverage, output_dir, formats))
    
    # Track all coverage tool calls
    all_gcov_calls = []
    all_lcov_calls = []
    all_collection_calls = []
    
    async def mock_enable_gcov(conn):
        all_gcov_calls.append(conn.environment_id)
        conn.execute_command("enable_gcov")
        conn.coverage_tools["gcov"]["installed"] = True
        conn.coverage_tools["gcov"]["enabled"] = True
    
    async def mock_install_lcov(conn):
        all_lcov_calls.append(conn.environment_id)
        conn.execute_command("install_lcov")
        conn.coverage_tools["lcov"]["installed"] = True
    
    async def mock_setup_coverage_collection(conn):
        all_collection_calls.append(conn.environment_id)
        conn.execute_command("setup_coverage_collection")
        
        # Find the configuration for this environment
        env_index = int(conn.environment_id.split("_")[-1])
        config_index = env_index % len(coverage_configs)
        enable_coverage, output_dir, formats = coverage_configs[config_index]
        
        if enable_coverage:
            conn.set_coverage_config({
                "output_dir": f"/tmp/coverage/{output_dir.strip()}_{env_index}",
                "formats": formats,
                "environment_id": conn.environment_id
            })
            conn.add_coverage_path(f"/tmp/coverage/{output_dir.strip()}_{env_index}")
    
    # Replace private methods
    instrumentation_manager._enable_gcov = mock_enable_gcov
    instrumentation_manager._install_lcov = mock_install_lcov
    instrumentation_manager._setup_coverage_collection = mock_setup_coverage_collection
    
    # Configure all environments
    results = []
    for connection, (config, enable_coverage, output_dir, formats) in zip(environments, configurations):
        result = await instrumentation_manager.configure_code_coverage(connection, config)
        results.append(result)
    
    # Verify all configurations succeeded
    assert all(results), "All coverage configurations should succeed"
    
    # Verify each environment got correct configuration
    for i, (connection, (config, enable_coverage, output_dir, formats)) in enumerate(zip(environments, configurations)):
        env_id = f"coverage_env_{i}"
        
        if enable_coverage:
            # Verify tools were set up for this environment
            assert env_id in all_gcov_calls, f"gcov should be enabled for {env_id}"
            assert env_id in all_lcov_calls, f"lcov should be installed for {env_id}"
            assert env_id in all_collection_calls, f"Coverage collection should be set up for {env_id}"
            
            # Verify environment-specific configuration
            expected_output_dir = f"/tmp/coverage/{output_dir.strip()}_{i}"
            assert connection.coverage_config.get("output_dir") == expected_output_dir, \
                f"Output directory should be environment-specific for {env_id}"
            assert connection.coverage_config.get("formats") == formats, \
                f"Coverage formats should be correct for {env_id}"
            assert connection.coverage_config.get("environment_id") == env_id, \
                f"Environment ID should be set in config for {env_id}"
            
        else:
            # Verify tools were not set up
            assert env_id not in all_gcov_calls, f"gcov should not be enabled for {env_id}"
            assert env_id not in all_lcov_calls, f"lcov should not be installed for {env_id}"
            assert env_id not in all_collection_calls, f"Coverage collection should not be set up for {env_id}"
    
    # Verify isolation - each environment should have unique output directories
    enabled_environments = [
        (conn, config, output_dir, i) 
        for i, (conn, (config, enable_coverage, output_dir, formats)) in enumerate(zip(environments, configurations))
        if enable_coverage
    ]
    
    for i, (env1, _, output_dir1, index1) in enumerate(enabled_environments):
        for j, (env2, _, output_dir2, index2) in enumerate(enabled_environments):
            if i != j:
                # Output directories should be different
                expected_dir1 = f"/tmp/coverage/{output_dir1.strip()}_{index1}"
                expected_dir2 = f"/tmp/coverage/{output_dir2.strip()}_{index2}"
                
                actual_dir1 = env1.coverage_config.get("output_dir")
                actual_dir2 = env2.coverage_config.get("output_dir")
                
                assert actual_dir1 != actual_dir2, \
                    f"Different environments should have different output directories: {actual_dir1} vs {actual_dir2}"


@given(
    enable_coverage=st.booleans(),
    gcov_failure=st.booleans(),
    lcov_failure=st.booleans()
)
@settings(max_examples=30, deadline=3000)
async def test_coverage_tool_validation(enable_coverage, gcov_failure, lcov_failure):
    """
    Property: Coverage tool validation detects configuration issues
    
    This test verifies that:
    1. Validation correctly identifies working coverage tools
    2. Validation detects failed coverage tool configurations
    3. Partial coverage tool failures are properly reported
    4. Validation results reflect actual tool states
    """
    instrumentation_manager = InstrumentationManager()
    
    # Create configuration
    config = InstrumentationConfig(
        enable_coverage=enable_coverage
    )
    
    # Create mock connection
    connection = MockCoverageConnection("coverage_validation_env")
    
    # Set up tool states based on failure flags
    if enable_coverage:
        connection.coverage_tools["gcov"]["installed"] = not gcov_failure
        connection.coverage_tools["gcov"]["enabled"] = not gcov_failure
        connection.coverage_tools["lcov"]["installed"] = not lcov_failure
        connection.coverage_tools["lcov"]["configured"] = not lcov_failure
    
    # Mock validation methods
    async def mock_validate_gcov(conn):
        await asyncio.sleep(0.01)
        return conn.coverage_tools["gcov"]["installed"] and conn.coverage_tools["gcov"]["enabled"]
    
    async def mock_validate_lcov(conn):
        await asyncio.sleep(0.01)
        return conn.coverage_tools["lcov"]["installed"] and conn.coverage_tools["lcov"]["configured"]
    
    # Replace validation methods
    instrumentation_manager._validate_gcov = mock_validate_gcov
    instrumentation_manager._validate_lcov = mock_validate_lcov
    
    # Validate instrumentation
    validation_results = await instrumentation_manager.validate_instrumentation(connection, config)
    
    # Verify validation results
    if enable_coverage:
        assert "gcov" in validation_results, "gcov validation should be performed"
        assert "lcov" in validation_results, "lcov validation should be performed"
        
        expected_gcov_result = not gcov_failure
        expected_lcov_result = not lcov_failure
        
        assert validation_results["gcov"] == expected_gcov_result, \
            f"gcov validation should return {expected_gcov_result}"
        assert validation_results["lcov"] == expected_lcov_result, \
            f"lcov validation should return {expected_lcov_result}"
    else:
        assert "gcov" not in validation_results, "gcov validation should not be performed when coverage is disabled"
        assert "lcov" not in validation_results, "lcov validation should not be performed when coverage is disabled"


# Synchronous test runners for pytest
def test_coverage_tool_configuration_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_coverage_tool_configuration(
        environment_id="coverage_test_env",
        enable_coverage=True,
        output_dir="test_coverage_output",
        formats=["html", "xml", "lcov"]
    ))


def test_multiple_environment_coverage_configuration_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_environment_coverage_configuration(
        environment_count=2,
        coverage_configs=[
            (True, "env1_coverage", ["html", "xml"]),
            (True, "env2_coverage", ["lcov", "json"])
        ]
    ))


def test_coverage_tool_validation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_coverage_tool_validation(
        enable_coverage=True,
        gcov_failure=False,
        lcov_failure=True
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing coverage tool configuration...")
        await test_coverage_tool_configuration(
            "coverage_env", True, "test_output", ["html", "xml"]
        )
        print("✓ Coverage tool configuration test passed")
        
        print("Testing multiple environment coverage configuration...")
        await test_multiple_environment_coverage_configuration(
            2, [(True, "env1", ["html"]), (True, "env2", ["xml"])]
        )
        print("✓ Multiple environment coverage configuration test passed")
        
        print("Testing coverage tool validation...")
        await test_coverage_tool_validation(True, False, True)
        print("✓ Coverage tool validation test passed")
        
        print("All coverage tool configuration tests completed successfully!")
    
    asyncio.run(run_examples())