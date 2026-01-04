"""
Property-based test for security tool configuration.

Tests that security testing tools (Syzkaller, Coccinelle, vulnerability scanners)
are properly configured and validated in test environments.
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
fuzzing_targets = st.lists(
    st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
    min_size=0,
    max_size=8
)


class MockSecurityConnection:
    """Mock connection for testing security tool configuration"""
    
    def __init__(self, environment_id: str):
        self.environment_id = environment_id
        self.is_connected = True
        self.executed_commands = []
        self.installed_tools = set()
        self.security_configs = {}
        self.fuzzing_targets = []
        self.analysis_rules = []
    
    def execute_command(self, command: str):
        """Mock command execution for security tools"""
        self.executed_commands.append(command)
        
        # Simulate tool installation/configuration
        if "syzkaller" in command.lower():
            self.installed_tools.add("syzkaller")
            self.security_configs["syzkaller"] = {"status": "configured"}
        elif "coccinelle" in command.lower():
            self.installed_tools.add("coccinelle")
            self.security_configs["coccinelle"] = {"status": "configured"}
        elif "install" in command.lower() and "security" in command.lower():
            self.installed_tools.add("security_scanner")
    
    def add_fuzzing_target(self, target: str):
        """Mock fuzzing target addition"""
        self.fuzzing_targets.append(target)
    
    def add_analysis_rule(self, rule: str):
        """Mock static analysis rule addition"""
        self.analysis_rules.append(rule)


@given(
    environment_id=environment_ids,
    enable_fuzzing=st.booleans(),
    fuzzing_targets=fuzzing_targets
)
@settings(max_examples=40, deadline=5000)
async def test_security_tool_configuration(environment_id, enable_fuzzing, fuzzing_targets):
    """
    Property: Security tool configuration enables proper security testing
    
    This test verifies that:
    1. Security tools are properly installed and configured
    2. Fuzzing tools are set up with correct targets
    3. Static analysis tools are configured with appropriate rules
    4. Security tool validation confirms proper setup
    5. Tool configurations are environment-specific
    """
    assume(len(environment_id.strip()) > 0)
    
    # Create instrumentation manager
    instrumentation_manager = InstrumentationManager()
    
    # Create instrumentation configuration
    config = InstrumentationConfig(
        enable_fuzzing=enable_fuzzing,
        fuzzing_config={
            "targets": fuzzing_targets,
            "duration_hours": 24,
            "coverage_guided": True
        } if enable_fuzzing else {}
    )
    
    # Create mock connection
    connection = MockSecurityConnection(environment_id.strip())
    
    # Track security tool setup calls
    syzkaller_calls = []
    coccinelle_calls = []
    security_tools_calls = []
    
    async def mock_setup_syzkaller(conn):
        syzkaller_calls.append(conn.environment_id)
        conn.execute_command("setup_syzkaller")
        # Configure fuzzing targets
        for target in fuzzing_targets:
            conn.add_fuzzing_target(target)
        await asyncio.sleep(0.01)
    
    async def mock_install_coccinelle(conn):
        coccinelle_calls.append(conn.environment_id)
        conn.execute_command("install_coccinelle")
        # Add some default analysis rules
        conn.add_analysis_rule("null_pointer_check")
        conn.add_analysis_rule("buffer_overflow_check")
        await asyncio.sleep(0.01)
    
    async def mock_setup_security_tools(conn):
        security_tools_calls.append(conn.environment_id)
        conn.execute_command("install_security_scanner")
        await asyncio.sleep(0.01)
    
    # Replace private methods with mocks
    instrumentation_manager._setup_syzkaller = mock_setup_syzkaller
    instrumentation_manager._install_coccinelle = mock_install_coccinelle
    instrumentation_manager._setup_security_tools = mock_setup_security_tools
    
    # Configure security testing tools
    result = await instrumentation_manager.configure_security_testing(connection, config)
    
    # Verify configuration result
    if enable_fuzzing:
        assert result is True, "Security tool configuration should succeed when fuzzing is enabled"
        
        # Verify Syzkaller setup
        assert len(syzkaller_calls) == 1, "Syzkaller should be set up once"
        assert syzkaller_calls[0] == environment_id.strip(), "Syzkaller should be set up for correct environment"
        assert "syzkaller" in connection.installed_tools, "Syzkaller should be marked as installed"
        
        # Verify fuzzing targets
        assert connection.fuzzing_targets == fuzzing_targets, "Fuzzing targets should be configured correctly"
        
        # Verify Coccinelle setup
        assert len(coccinelle_calls) == 1, "Coccinelle should be installed once"
        assert coccinelle_calls[0] == environment_id.strip(), "Coccinelle should be installed for correct environment"
        assert "coccinelle" in connection.installed_tools, "Coccinelle should be marked as installed"
        
        # Verify analysis rules
        assert "null_pointer_check" in connection.analysis_rules, "Null pointer check rule should be added"
        assert "buffer_overflow_check" in connection.analysis_rules, "Buffer overflow check rule should be added"
        
        # Verify additional security tools
        assert len(security_tools_calls) == 1, "Security tools should be set up once"
        assert security_tools_calls[0] == environment_id.strip(), "Security tools should be set up for correct environment"
        
    else:
        # When fuzzing is disabled, configuration should still succeed but do nothing
        assert result is True, "Security tool configuration should succeed even when fuzzing is disabled"
        assert len(syzkaller_calls) == 0, "Syzkaller should not be set up when fuzzing is disabled"
        assert len(coccinelle_calls) == 0, "Coccinelle should not be installed when fuzzing is disabled"
        assert len(security_tools_calls) == 0, "Security tools should not be set up when fuzzing is disabled"


@given(
    environment_count=st.integers(min_value=1, max_value=4),
    fuzzing_configs=st.lists(
        st.tuples(
            st.booleans(),  # enable_fuzzing
            st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5)  # targets
        ),
        min_size=1,
        max_size=4
    )
)
@settings(max_examples=25, deadline=4000)
async def test_multiple_environment_security_configuration(environment_count, fuzzing_configs):
    """
    Property: Multiple environment security configuration maintains isolation
    
    This test verifies that:
    1. Each environment gets its own security tool configuration
    2. Fuzzing targets are environment-specific
    3. Security tool states don't interfere between environments
    4. Different security configurations can coexist
    """
    assume(environment_count >= 1)
    assume(len(fuzzing_configs) >= 1)
    
    instrumentation_manager = InstrumentationManager()
    
    # Create multiple environments with different security configurations
    environments = []
    configurations = []
    
    for i in range(environment_count):
        env_id = f"security_env_{i}"
        connection = MockSecurityConnection(env_id)
        
        # Use cycling fuzzing configurations
        config_index = i % len(fuzzing_configs)
        enable_fuzzing, targets = fuzzing_configs[config_index]
        
        config = InstrumentationConfig(
            enable_fuzzing=enable_fuzzing,
            fuzzing_config={
                "targets": targets,
                "environment_specific": f"config_{i}"
            } if enable_fuzzing else {}
        )
        
        environments.append(connection)
        configurations.append((config, enable_fuzzing, targets))
    
    # Track all security tool calls
    all_syzkaller_calls = []
    all_coccinelle_calls = []
    all_security_calls = []
    
    async def mock_setup_syzkaller(conn):
        all_syzkaller_calls.append(conn.environment_id)
        conn.execute_command("setup_syzkaller")
        # Find the configuration for this environment
        env_index = int(conn.environment_id.split("_")[-1])
        config_index = env_index % len(fuzzing_configs)
        _, targets = fuzzing_configs[config_index]
        for target in targets:
            conn.add_fuzzing_target(target)
    
    async def mock_install_coccinelle(conn):
        all_coccinelle_calls.append(conn.environment_id)
        conn.execute_command("install_coccinelle")
        conn.add_analysis_rule(f"rule_for_{conn.environment_id}")
    
    async def mock_setup_security_tools(conn):
        all_security_calls.append(conn.environment_id)
        conn.execute_command("install_security_scanner")
    
    # Replace private methods
    instrumentation_manager._setup_syzkaller = mock_setup_syzkaller
    instrumentation_manager._install_coccinelle = mock_install_coccinelle
    instrumentation_manager._setup_security_tools = mock_setup_security_tools
    
    # Configure all environments
    results = []
    for connection, (config, enable_fuzzing, targets) in zip(environments, configurations):
        result = await instrumentation_manager.configure_security_testing(connection, config)
        results.append(result)
    
    # Verify all configurations succeeded
    assert all(results), "All security configurations should succeed"
    
    # Verify each environment got correct configuration
    for i, (connection, (config, enable_fuzzing, targets)) in enumerate(zip(environments, configurations)):
        env_id = f"security_env_{i}"
        
        if enable_fuzzing:
            # Verify tools were set up for this environment
            assert env_id in all_syzkaller_calls, f"Syzkaller should be set up for {env_id}"
            assert env_id in all_coccinelle_calls, f"Coccinelle should be installed for {env_id}"
            assert env_id in all_security_calls, f"Security tools should be set up for {env_id}"
            
            # Verify fuzzing targets are correct
            assert connection.fuzzing_targets == targets, f"Fuzzing targets should be correct for {env_id}"
            
            # Verify environment-specific analysis rules
            expected_rule = f"rule_for_{env_id}"
            assert expected_rule in connection.analysis_rules, f"Environment-specific rule should exist for {env_id}"
        else:
            # Verify tools were not set up
            assert env_id not in all_syzkaller_calls, f"Syzkaller should not be set up for {env_id}"
            assert env_id not in all_coccinelle_calls, f"Coccinelle should not be installed for {env_id}"
            assert env_id not in all_security_calls, f"Security tools should not be set up for {env_id}"
    
    # Verify isolation - each environment should have unique configurations
    enabled_environments = [conn for conn, (_, enable_fuzzing, _) in zip(environments, configurations) if enable_fuzzing]
    
    for i, env1 in enumerate(enabled_environments):
        for j, env2 in enumerate(enabled_environments):
            if i != j:
                # Fuzzing targets should be different if configurations are different
                config1_index = int(env1.environment_id.split("_")[-1]) % len(fuzzing_configs)
                config2_index = int(env2.environment_id.split("_")[-1]) % len(fuzzing_configs)
                
                if config1_index != config2_index:
                    assert env1.fuzzing_targets != env2.fuzzing_targets, \
                        f"Different environments should have different fuzzing targets"


@given(
    enable_fuzzing=st.booleans(),
    tool_failures=st.lists(st.sampled_from(["syzkaller", "coccinelle", "security_tools"]), max_size=3)
)
@settings(max_examples=30, deadline=3000)
async def test_security_tool_validation(enable_fuzzing, tool_failures):
    """
    Property: Security tool validation detects configuration issues
    
    This test verifies that:
    1. Validation correctly identifies successfully configured tools
    2. Validation detects failed tool configurations
    3. Validation results reflect actual tool states
    4. Partial failures are properly reported
    """
    instrumentation_manager = InstrumentationManager()
    
    # Create configuration
    config = InstrumentationConfig(
        enable_fuzzing=enable_fuzzing
    )
    
    # Create mock connection
    connection = MockSecurityConnection("validation_test_env")
    
    # Simulate tool installation states
    if enable_fuzzing:
        # Install tools unless they're in the failure list
        if "syzkaller" not in tool_failures:
            connection.installed_tools.add("syzkaller")
        if "coccinelle" not in tool_failures:
            connection.installed_tools.add("coccinelle")
        if "security_tools" not in tool_failures:
            connection.installed_tools.add("security_scanner")
    
    # Mock validation methods
    async def mock_validate_syzkaller(conn):
        await asyncio.sleep(0.01)
        return "syzkaller" in conn.installed_tools
    
    # Replace validation method
    instrumentation_manager._validate_syzkaller = mock_validate_syzkaller
    
    # Validate instrumentation
    validation_results = await instrumentation_manager.validate_instrumentation(connection, config)
    
    # Verify validation results
    if enable_fuzzing:
        assert "syzkaller" in validation_results, "Syzkaller validation should be performed"
        
        expected_syzkaller_result = "syzkaller" not in tool_failures
        assert validation_results["syzkaller"] == expected_syzkaller_result, \
            f"Syzkaller validation should return {expected_syzkaller_result}"
    else:
        assert "syzkaller" not in validation_results, "Syzkaller validation should not be performed when fuzzing is disabled"


# Synchronous test runners for pytest
def test_security_tool_configuration_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_security_tool_configuration(
        environment_id="security_test_env",
        enable_fuzzing=True,
        fuzzing_targets=["syscall_fuzzer", "network_fuzzer"]
    ))


def test_multiple_environment_security_configuration_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_environment_security_configuration(
        environment_count=2,
        fuzzing_configs=[(True, ["target1", "target2"]), (False, [])]
    ))


def test_security_tool_validation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_security_tool_validation(
        enable_fuzzing=True,
        tool_failures=["coccinelle"]
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing security tool configuration...")
        await test_security_tool_configuration(
            "security_env", True, ["syscall_fuzzer", "fs_fuzzer"]
        )
        print("✓ Security tool configuration test passed")
        
        print("Testing multiple environment security configuration...")
        await test_multiple_environment_security_configuration(
            2, [(True, ["target1"]), (False, [])]
        )
        print("✓ Multiple environment security configuration test passed")
        
        print("Testing security tool validation...")
        await test_security_tool_validation(True, ["coccinelle"])
        print("✓ Security tool validation test passed")
        
        print("All security tool configuration tests completed successfully!")
    
    asyncio.run(run_examples())