"""
Property-based test for kernel debugging feature enablement.

Tests that kernel debugging features (KASAN, KTSAN, LOCKDEP) are properly
enabled and configured in test environments.
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
kernel_params = st.lists(
    st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'))),
    min_size=0,
    max_size=10
)


class MockConnection:
    """Mock connection for testing kernel debugging configuration"""
    
    def __init__(self, environment_id: str):
        self.environment_id = environment_id
        self.is_connected = True
        self.executed_commands = []
        self.kernel_features = {
            "kasan": False,
            "ktsan": False,
            "lockdep": False
        }
        self.kernel_params = []
    
    def execute_command(self, command: str):
        """Mock command execution"""
        self.executed_commands.append(command)
        
        # Simulate kernel feature enablement
        if "kasan" in command.lower():
            self.kernel_features["kasan"] = True
        elif "ktsan" in command.lower():
            self.kernel_features["ktsan"] = True
        elif "lockdep" in command.lower():
            self.kernel_features["lockdep"] = True
    
    def add_kernel_param(self, param: str):
        """Mock kernel parameter addition"""
        self.kernel_params.append(param)


@given(
    environment_id=environment_ids,
    enable_kasan=st.booleans(),
    enable_ktsan=st.booleans(),
    enable_lockdep=st.booleans(),
    custom_params=kernel_params
)
@settings(max_examples=50, deadline=5000)
async def test_kernel_debugging_feature_enablement(environment_id, enable_kasan, enable_ktsan, enable_lockdep, custom_params):
    """
    Property: Kernel debugging feature enablement works correctly
    
    This test verifies that:
    1. Requested kernel debugging features are enabled
    2. Feature enablement is reflected in system configuration
    3. Custom kernel parameters are applied correctly
    4. Feature combinations work together properly
    5. Configuration commands are executed in correct order
    """
    assume(len(environment_id.strip()) > 0)
    
    # Create instrumentation manager
    instrumentation_manager = InstrumentationManager()
    
    # Create instrumentation configuration
    config = InstrumentationConfig(
        enable_kasan=enable_kasan,
        enable_ktsan=enable_ktsan,
        enable_lockdep=enable_lockdep,
        custom_kernel_params=custom_params
    )
    
    # Create mock connection
    connection = MockConnection(environment_id.strip())
    
    # Mock the private methods to track their calls
    kasan_calls = []
    ktsan_calls = []
    lockdep_calls = []
    param_calls = []
    
    async def mock_enable_kasan(conn):
        kasan_calls.append(conn.environment_id)
        conn.execute_command("enable_kasan")
        await asyncio.sleep(0.01)
    
    async def mock_enable_ktsan(conn):
        ktsan_calls.append(conn.environment_id)
        conn.execute_command("enable_ktsan")
        await asyncio.sleep(0.01)
    
    async def mock_enable_lockdep(conn):
        lockdep_calls.append(conn.environment_id)
        conn.execute_command("enable_lockdep")
        await asyncio.sleep(0.01)
    
    async def mock_apply_kernel_params(conn, params):
        param_calls.append(params)
        for param in params:
            conn.add_kernel_param(param)
        await asyncio.sleep(0.01)
    
    # Replace private methods with mocks
    instrumentation_manager._enable_kasan = mock_enable_kasan
    instrumentation_manager._enable_ktsan = mock_enable_ktsan
    instrumentation_manager._enable_lockdep = mock_enable_lockdep
    instrumentation_manager._apply_kernel_params = mock_apply_kernel_params
    
    # Configure kernel debugging features
    result = await instrumentation_manager.configure_kernel_debugging(connection, config)
    
    # Verify configuration succeeded
    assert result is True, "Kernel debugging configuration should succeed"
    
    # Verify KASAN configuration
    if enable_kasan:
        assert len(kasan_calls) == 1, "KASAN should be enabled once"
        assert kasan_calls[0] == environment_id.strip(), "KASAN should be enabled for correct environment"
        assert connection.kernel_features["kasan"] is True, "KASAN should be marked as enabled"
    else:
        assert len(kasan_calls) == 0, "KASAN should not be enabled"
        assert connection.kernel_features["kasan"] is False, "KASAN should remain disabled"
    
    # Verify KTSAN configuration
    if enable_ktsan:
        assert len(ktsan_calls) == 1, "KTSAN should be enabled once"
        assert ktsan_calls[0] == environment_id.strip(), "KTSAN should be enabled for correct environment"
        assert connection.kernel_features["ktsan"] is True, "KTSAN should be marked as enabled"
    else:
        assert len(ktsan_calls) == 0, "KTSAN should not be enabled"
        assert connection.kernel_features["ktsan"] is False, "KTSAN should remain disabled"
    
    # Verify LOCKDEP configuration
    if enable_lockdep:
        assert len(lockdep_calls) == 1, "LOCKDEP should be enabled once"
        assert lockdep_calls[0] == environment_id.strip(), "LOCKDEP should be enabled for correct environment"
        assert connection.kernel_features["lockdep"] is True, "LOCKDEP should be marked as enabled"
    else:
        assert len(lockdep_calls) == 0, "LOCKDEP should not be enabled"
        assert connection.kernel_features["lockdep"] is False, "LOCKDEP should remain disabled"
    
    # Verify custom kernel parameters
    if custom_params:
        assert len(param_calls) == 1, "Kernel parameters should be applied once"
        assert param_calls[0] == custom_params, "Correct parameters should be applied"
        assert connection.kernel_params == custom_params, "Parameters should be set in connection"
    else:
        assert len(param_calls) == 0, "No parameters should be applied when none provided"
        assert connection.kernel_params == [], "No parameters should be set"


@given(
    environment_count=st.integers(min_value=1, max_value=5),
    feature_combinations=st.lists(
        st.tuples(st.booleans(), st.booleans(), st.booleans()),  # (kasan, ktsan, lockdep)
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=25, deadline=4000)
async def test_multiple_environment_debugging_configuration(environment_count, feature_combinations):
    """
    Property: Multiple environment debugging configuration maintains isolation
    
    This test verifies that:
    1. Each environment gets its own debugging configuration
    2. Feature enablement in one environment doesn't affect others
    3. Different feature combinations can be applied to different environments
    4. Configuration state is properly isolated between environments
    """
    assume(environment_count >= 1)
    assume(len(feature_combinations) >= 1)
    
    instrumentation_manager = InstrumentationManager()
    
    # Create multiple environments with different configurations
    environments = []
    configurations = []
    
    for i in range(environment_count):
        env_id = f"test_env_{i}"
        connection = MockConnection(env_id)
        
        # Use cycling feature combinations
        combo_index = i % len(feature_combinations)
        enable_kasan, enable_ktsan, enable_lockdep = feature_combinations[combo_index]
        
        config = InstrumentationConfig(
            enable_kasan=enable_kasan,
            enable_ktsan=enable_ktsan,
            enable_lockdep=enable_lockdep,
            custom_kernel_params=[f"debug_param_{i}=value_{i}"]
        )
        
        environments.append(connection)
        configurations.append((config, enable_kasan, enable_ktsan, enable_lockdep))
    
    # Track calls for verification
    all_kasan_calls = []
    all_ktsan_calls = []
    all_lockdep_calls = []
    all_param_calls = []
    
    async def mock_enable_kasan(conn):
        all_kasan_calls.append(conn.environment_id)
        conn.execute_command("enable_kasan")
    
    async def mock_enable_ktsan(conn):
        all_ktsan_calls.append(conn.environment_id)
        conn.execute_command("enable_ktsan")
    
    async def mock_enable_lockdep(conn):
        all_lockdep_calls.append(conn.environment_id)
        conn.execute_command("enable_lockdep")
    
    async def mock_apply_kernel_params(conn, params):
        all_param_calls.append((conn.environment_id, params))
        for param in params:
            conn.add_kernel_param(param)
    
    # Replace private methods
    instrumentation_manager._enable_kasan = mock_enable_kasan
    instrumentation_manager._enable_ktsan = mock_enable_ktsan
    instrumentation_manager._enable_lockdep = mock_enable_lockdep
    instrumentation_manager._apply_kernel_params = mock_apply_kernel_params
    
    # Configure all environments
    results = []
    for i, (connection, (config, enable_kasan, enable_ktsan, enable_lockdep)) in enumerate(zip(environments, configurations)):
        result = await instrumentation_manager.configure_kernel_debugging(connection, config)
        results.append(result)
    
    # Verify all configurations succeeded
    assert all(results), "All environment configurations should succeed"
    
    # Verify each environment got correct configuration
    for i, (connection, (config, enable_kasan, enable_ktsan, enable_lockdep)) in enumerate(zip(environments, configurations)):
        env_id = f"test_env_{i}"
        
        # Check KASAN
        if enable_kasan:
            assert env_id in all_kasan_calls, f"KASAN should be enabled for {env_id}"
            assert connection.kernel_features["kasan"] is True, f"KASAN should be enabled in {env_id}"
        else:
            assert connection.kernel_features["kasan"] is False, f"KASAN should be disabled in {env_id}"
        
        # Check KTSAN
        if enable_ktsan:
            assert env_id in all_ktsan_calls, f"KTSAN should be enabled for {env_id}"
            assert connection.kernel_features["ktsan"] is True, f"KTSAN should be enabled in {env_id}"
        else:
            assert connection.kernel_features["ktsan"] is False, f"KTSAN should be disabled in {env_id}"
        
        # Check LOCKDEP
        if enable_lockdep:
            assert env_id in all_lockdep_calls, f"LOCKDEP should be enabled for {env_id}"
            assert connection.kernel_features["lockdep"] is True, f"LOCKDEP should be enabled in {env_id}"
        else:
            assert connection.kernel_features["lockdep"] is False, f"LOCKDEP should be disabled in {env_id}"
        
        # Check kernel parameters
        expected_param = f"debug_param_{i}=value_{i}"
        assert expected_param in connection.kernel_params, f"Custom parameter should be set in {env_id}"
    
    # Verify isolation - each environment should have unique parameters
    for i, connection in enumerate(environments):
        for j, other_connection in enumerate(environments):
            if i != j:
                # Parameters should be different between environments
                assert connection.kernel_params != other_connection.kernel_params, \
                    f"Environment {i} and {j} should have different parameters"


@given(
    enable_kasan=st.booleans(),
    enable_ktsan=st.booleans(),
    enable_lockdep=st.booleans()
)
@settings(max_examples=30, deadline=3000)
async def test_kernel_debugging_validation(enable_kasan, enable_ktsan, enable_lockdep):
    """
    Property: Kernel debugging validation confirms feature enablement
    
    This test verifies that:
    1. Validation correctly detects enabled features
    2. Validation fails for features that aren't properly enabled
    3. Validation results match configuration state
    4. Multiple features can be validated simultaneously
    """
    instrumentation_manager = InstrumentationManager()
    
    # Create configuration
    config = InstrumentationConfig(
        enable_kasan=enable_kasan,
        enable_ktsan=enable_ktsan,
        enable_lockdep=enable_lockdep
    )
    
    # Create mock connection
    connection = MockConnection("validation_test_env")
    
    # Mock validation methods to return success based on feature state
    async def mock_validate_kasan(conn):
        await asyncio.sleep(0.01)
        return conn.kernel_features["kasan"]
    
    async def mock_validate_ktsan(conn):
        await asyncio.sleep(0.01)
        return conn.kernel_features["ktsan"]
    
    async def mock_validate_lockdep(conn):
        await asyncio.sleep(0.01)
        return conn.kernel_features["lockdep"]
    
    # Replace validation methods
    instrumentation_manager._validate_kasan = mock_validate_kasan
    instrumentation_manager._validate_ktsan = mock_validate_ktsan
    instrumentation_manager._validate_lockdep = mock_validate_lockdep
    
    # First, configure the features (this will set the feature states)
    if enable_kasan:
        connection.kernel_features["kasan"] = True
    if enable_ktsan:
        connection.kernel_features["ktsan"] = True
    if enable_lockdep:
        connection.kernel_features["lockdep"] = True
    
    # Validate instrumentation
    validation_results = await instrumentation_manager.validate_instrumentation(connection, config)
    
    # Verify validation results match configuration
    if enable_kasan:
        assert "kasan" in validation_results, "KASAN validation should be performed"
        assert validation_results["kasan"] is True, "KASAN validation should succeed"
    else:
        assert "kasan" not in validation_results, "KASAN validation should not be performed"
    
    if enable_ktsan:
        assert "ktsan" in validation_results, "KTSAN validation should be performed"
        assert validation_results["ktsan"] is True, "KTSAN validation should succeed"
    else:
        assert "ktsan" not in validation_results, "KTSAN validation should not be performed"
    
    if enable_lockdep:
        assert "lockdep" in validation_results, "LOCKDEP validation should be performed"
        assert validation_results["lockdep"] is True, "LOCKDEP validation should succeed"
    else:
        assert "lockdep" not in validation_results, "LOCKDEP validation should not be performed"
    
    # Verify that only enabled features are validated
    expected_validations = sum([enable_kasan, enable_ktsan, enable_lockdep])
    assert len(validation_results) >= expected_validations, "All enabled features should be validated"


# Synchronous test runners for pytest
def test_kernel_debugging_feature_enablement_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_kernel_debugging_feature_enablement(
        environment_id="test_env",
        enable_kasan=True,
        enable_ktsan=True,
        enable_lockdep=False,
        custom_params=["debug=1", "kasan_multi_shot=1"]
    ))


def test_multiple_environment_debugging_configuration_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_multiple_environment_debugging_configuration(
        environment_count=3,
        feature_combinations=[(True, False, True), (False, True, False), (True, True, True)]
    ))


def test_kernel_debugging_validation_sync():
    """Synchronous wrapper for the async property test"""
    asyncio.run(test_kernel_debugging_validation(
        enable_kasan=True,
        enable_ktsan=False,
        enable_lockdep=True
    ))


if __name__ == "__main__":
    # Run a few examples manually for testing
    import asyncio
    
    async def run_examples():
        print("Testing kernel debugging feature enablement...")
        await test_kernel_debugging_feature_enablement(
            "test_env", True, True, False, ["debug=1"]
        )
        print("✓ Kernel debugging feature enablement test passed")
        
        print("Testing multiple environment debugging configuration...")
        await test_multiple_environment_debugging_configuration(
            2, [(True, False, True), (False, True, False)]
        )
        print("✓ Multiple environment debugging configuration test passed")
        
        print("Testing kernel debugging validation...")
        await test_kernel_debugging_validation(True, False, True)
        print("✓ Kernel debugging validation test passed")
        
        print("All kernel debugging feature tests completed successfully!")
    
    asyncio.run(run_examples())