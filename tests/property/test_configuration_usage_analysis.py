"""Property-based tests for configuration usage analysis.

**Feature: agentic-kernel-testing, Property 45: Configuration usage analysis**
**Validates: Requirements 9.5**

Tests that the system identifies configuration options that are untested or rarely used
for any completed configuration testing.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from pathlib import Path
import tempfile
import shutil
from typing import List, Dict, Set
from contextlib import contextmanager
from datetime import datetime, timedelta

from execution.config_usage_analyzer import (
    ConfigUsageAnalyzer,
    ConfigUsageTracker,
    ConfigOptionUsage,
    UsageFrequency,
    RarelyUsedOptionIdentifier,
    UsageReportGenerator
)
from execution.kernel_config_testing import (
    KernelConfig,
    ConfigTestResult,
    ConfigBuildResult,
    ConfigType
)


# Strategy for generating configuration option names
config_option_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_',
    min_size=8,
    max_size=30
).map(lambda s: f"CONFIG_{s}")

# Strategy for generating option values
option_value_strategy = st.sampled_from(['y', 'n', 'm'])

# Strategy for generating architectures
architecture_strategy = st.sampled_from(['x86_64', 'arm64', 'arm', 'riscv64'])

# Strategy for generating config types
config_type_strategy = st.sampled_from([ConfigType.MINIMAL, ConfigType.DEFAULT, ConfigType.MAXIMAL])

# Strategy for generating configuration options dictionary
config_options_strategy = st.dictionaries(
    keys=config_option_strategy,
    values=option_value_strategy,
    min_size=5,
    max_size=20
)


@contextmanager
def temp_storage_path():
    """Create a temporary storage path for testing."""
    temp_file = Path(tempfile.mktemp(suffix=".json"))
    try:
        yield temp_file
    finally:
        if temp_file.exists():
            temp_file.unlink()


def create_test_config(name: str, options: Dict[str, str], architecture: str, config_type: ConfigType) -> KernelConfig:
    """Create a test kernel configuration."""
    return KernelConfig(
        name=name,
        config_type=config_type,
        options=options,
        architecture=architecture,
        description=f"Test config {name}"
    )


def create_test_result(config: KernelConfig, success: bool = True) -> ConfigTestResult:
    """Create a test configuration result."""
    build_result = ConfigBuildResult(
        config=config,
        success=success,
        build_time=1.0,
        size_bytes=1024 * 1024 if success else None
    )
    
    return ConfigTestResult(
        config=config,
        build_result=build_result,
        boot_success=success,
        boot_time=0.5 if success else None
    )


@given(
    test_configs=st.lists(
        st.tuples(
            st.text(min_size=3, max_size=10),  # config name
            config_options_strategy,            # options
            architecture_strategy,              # architecture
            config_type_strategy               # config type
        ),
        min_size=1,
        max_size=10
    )
)
def test_usage_analysis_identifies_all_tested_options(test_configs):
    """
    **Property 45: Configuration usage analysis**
    
    For any completed configuration testing, the system should identify 
    all configuration options that were tested.
    
    **Validates: Requirements 9.5**
    """
    # Arrange
    with temp_storage_path() as storage_path:
        analyzer = ConfigUsageAnalyzer(storage_path)
        
        # Create test results from the generated configs
        test_results = []
        all_tested_options = set()
        
        for name, options, arch, config_type in test_configs:
            config = create_test_config(f"test_{name}", options, arch, config_type)
            result = create_test_result(config)
            test_results.append(result)
            all_tested_options.update(options.keys())
        
        # Act
        report = analyzer.analyze_configuration_usage(test_results)
        
        # Assert - All tested options should be tracked
        tracked_options = set(report.option_usage.keys())
        assert all_tested_options.issubset(tracked_options), (
            f"All tested options should be tracked. "
            f"Missing: {all_tested_options - tracked_options}"
        )
        
        # Each tracked option should have usage data
        for option_name in all_tested_options:
            usage = report.option_usage[option_name]
            assert usage.total_tests > 0, (
                f"Option {option_name} should have been tested at least once"
            )


@given(
    options_dict=config_options_strategy,
    architecture=architecture_strategy,
    config_type=config_type_strategy,
    num_tests=st.integers(min_value=1, max_value=20)
)
def test_usage_frequency_calculation_accuracy(options_dict, architecture, config_type, num_tests):
    """
    **Property 45: Configuration usage analysis**
    
    For any configuration option usage pattern, the system should accurately 
    calculate usage frequency categories.
    
    **Validates: Requirements 9.5**
    """
    # Arrange
    with temp_storage_path() as storage_path:
        tracker = ConfigUsageTracker(storage_path)
        
        # Create multiple test results with the same options
        for i in range(num_tests):
            config = create_test_config(f"test_{i}", options_dict, architecture, config_type)
            result = create_test_result(config)
            tracker.track_configuration(config, result)
        
        # Act & Assert
        for option_name, option_value in options_dict.items():
            usage = tracker.usage_data[option_name]
            
            # Verify total tests count
            assert usage.total_tests == num_tests, (
                f"Option {option_name} should have {num_tests} total tests, "
                f"got {usage.total_tests}"
            )
            
            # Verify value counts based on option value
            if option_value == 'y':
                assert usage.enabled_count == num_tests, (
                    f"Option {option_name} should have {num_tests} enabled count"
                )
                assert usage.disabled_count == 0
                assert usage.module_count == 0
            elif option_value == 'n':
                assert usage.disabled_count == num_tests, (
                    f"Option {option_name} should have {num_tests} disabled count"
                )
                assert usage.enabled_count == 0
                assert usage.module_count == 0
            elif option_value == 'm':
                assert usage.module_count == num_tests, (
                    f"Option {option_name} should have {num_tests} module count"
                )
                assert usage.enabled_count == 0
                assert usage.disabled_count == 0
            
            # Verify usage rate calculation
            expected_usage_rate = 1.0 if option_value in ['y', 'm'] else 0.0
            assert abs(usage.usage_rate - expected_usage_rate) < 0.001, (
                f"Option {option_name} usage rate should be {expected_usage_rate}, "
                f"got {usage.usage_rate}"
            )
            
            # Verify frequency category
            if option_value in ['y', 'm']:
                assert usage.usage_frequency == UsageFrequency.ALWAYS_USED, (
                    f"Option {option_name} should be ALWAYS_USED when value is {option_value}"
                )
            else:
                assert usage.usage_frequency == UsageFrequency.NEVER_USED, (
                    f"Option {option_name} should be NEVER_USED when value is {option_value}"
                )


@given(
    enabled_options=st.sets(config_option_strategy, min_size=1, max_size=10),
    disabled_options=st.sets(config_option_strategy, min_size=1, max_size=10),
    architecture=architecture_strategy,
    config_type=config_type_strategy
)
def test_rarely_used_option_identification(enabled_options, disabled_options, architecture, config_type):
    """
    **Property 45: Configuration usage analysis**
    
    For any configuration testing results, the system should correctly 
    identify rarely used options based on usage patterns.
    
    **Validates: Requirements 9.5**
    """
    # Ensure no overlap between enabled and disabled options
    assume(enabled_options.isdisjoint(disabled_options))
    
    # Arrange
    with temp_storage_path() as storage_path:
        analyzer = ConfigUsageAnalyzer(storage_path)
        identifier = RarelyUsedOptionIdentifier(rarely_used_threshold=0.5)
        
        # Create test results where some options are rarely used
        test_results = []
        
        # Create 10 tests where enabled_options are always enabled (frequently used)
        for i in range(10):
            options = {}
            for opt in enabled_options:
                options[opt] = 'y'
            for opt in disabled_options:
                options[opt] = 'n'
            
            config = create_test_config(f"frequent_{i}", options, architecture, config_type)
            result = create_test_result(config)
            test_results.append(result)
        
        # Create 2 more tests where enabled_options are disabled (making them rarely used)
        for i in range(2):
            options = {}
            for opt in enabled_options:
                options[opt] = 'n'  # Now disabled, making usage rate = 10/12 = 83% (frequent)
            for opt in disabled_options:
                options[opt] = 'n'  # Still disabled, usage rate = 0% (never used)
            
            config = create_test_config(f"rare_{i}", options, architecture, config_type)
            result = create_test_result(config)
            test_results.append(result)
        
        # Act
        report = analyzer.analyze_configuration_usage(test_results)
        
        # Assert
        # Enabled options should be frequently used (10/12 = 83% > 50% threshold)
        for option in enabled_options:
            usage = report.option_usage[option]
            assert usage.usage_rate > 0.5, (
                f"Option {option} should have high usage rate, got {usage.usage_rate}"
            )
            assert usage.usage_frequency in [UsageFrequency.FREQUENTLY_USED, UsageFrequency.ALWAYS_USED], (
                f"Option {option} should be frequently used, got {usage.usage_frequency}"
            )
        
        # Disabled options should be never used (0% usage rate)
        for option in disabled_options:
            usage = report.option_usage[option]
            assert usage.usage_rate == 0.0, (
                f"Option {option} should have 0% usage rate, got {usage.usage_rate}"
            )
            assert usage.usage_frequency == UsageFrequency.NEVER_USED, (
                f"Option {option} should be never used, got {usage.usage_frequency}"
            )
        
        # Disabled options should be identified as rarely used (actually never used)
        rarely_used = identifier.identify_rarely_used_options(report.option_usage, min_tests=5)
        for option in disabled_options:
            assert option in rarely_used, (
                f"Never-used option {option} should be identified as rarely used"
            )


@given(
    tested_options=st.sets(config_option_strategy, min_size=1, max_size=15),
    untested_options=st.sets(config_option_strategy, min_size=1, max_size=10),
    architecture=architecture_strategy,
    config_type=config_type_strategy
)
def test_untested_option_identification(tested_options, untested_options, architecture, config_type):
    """
    **Property 45: Configuration usage analysis**
    
    For any configuration testing with known options, the system should 
    identify options that have never been tested.
    
    **Validates: Requirements 9.5**
    """
    # Ensure no overlap between tested and untested options
    assume(tested_options.isdisjoint(untested_options))
    
    # Arrange
    with temp_storage_path() as storage_path:
        analyzer = ConfigUsageAnalyzer(storage_path)
        identifier = RarelyUsedOptionIdentifier()
        
        # Create test results that only use tested_options
        test_results = []
        for i in range(3):
            options = {opt: 'y' for opt in tested_options}
            config = create_test_config(f"test_{i}", options, architecture, config_type)
            result = create_test_result(config)
            test_results.append(result)
        
        # Act
        report = analyzer.analyze_configuration_usage(test_results)
        
        # Combine tested and untested options as "known options"
        all_known_options = tested_options | untested_options
        
        # Identify untested options
        untested_identified = identifier.identify_untested_options(
            report.option_usage, 
            all_known_options
        )
        
        # Assert
        # All untested_options should be identified as untested
        for option in untested_options:
            assert option in untested_identified, (
                f"Untested option {option} should be identified as untested"
            )
        
        # No tested_options should be identified as untested
        for option in tested_options:
            assert option not in untested_identified, (
                f"Tested option {option} should not be identified as untested"
            )
        
        # Verify that tested options have usage data
        for option in tested_options:
            assert option in report.option_usage, (
                f"Tested option {option} should have usage data"
            )
            usage = report.option_usage[option]
            assert usage.total_tests > 0, (
                f"Tested option {option} should have positive test count"
            )


@given(
    test_configs=st.lists(
        st.tuples(
            st.text(min_size=3, max_size=10),
            config_options_strategy,
            architecture_strategy,
            config_type_strategy
        ),
        min_size=5,
        max_size=15
    )
)
def test_usage_report_completeness(test_configs):
    """
    **Property 45: Configuration usage analysis**
    
    For any completed configuration testing, the usage report should contain 
    comprehensive analysis including statistics, recommendations, and identified issues.
    
    **Validates: Requirements 9.5**
    """
    # Arrange
    with temp_storage_path() as storage_path:
        analyzer = ConfigUsageAnalyzer(storage_path)
        
        # Create test results
        test_results = []
        all_options = set()
        all_architectures = set()
        all_config_types = set()
        
        for name, options, arch, config_type in test_configs:
            config = create_test_config(f"test_{name}", options, arch, config_type)
            result = create_test_result(config)
            test_results.append(result)
            all_options.update(options.keys())
            all_architectures.add(arch)
            all_config_types.add(config_type.value)
        
        # Act
        report = analyzer.analyze_configuration_usage(test_results)
        
        # Assert - Report completeness
        # Statistics should be present and accurate
        stats = report.statistics
        assert stats.total_configurations_tested == len(test_results), (
            f"Statistics should show {len(test_results)} configurations tested"
        )
        assert stats.total_unique_options == len(all_options), (
            f"Statistics should show {len(all_options)} unique options"
        )
        
        # Architecture coverage should match tested architectures
        for arch in all_architectures:
            assert arch in stats.architecture_coverage, (
                f"Architecture {arch} should be in coverage statistics"
            )
            assert stats.architecture_coverage[arch] > 0, (
                f"Architecture {arch} should have positive coverage count"
            )
        
        # Config type coverage should match tested types
        for config_type in all_config_types:
            assert config_type in stats.config_type_coverage, (
                f"Config type {config_type} should be in coverage statistics"
            )
            assert stats.config_type_coverage[config_type] > 0, (
                f"Config type {config_type} should have positive coverage count"
            )
        
        # Option usage data should be complete
        assert len(report.option_usage) == len(all_options), (
            f"Should have usage data for all {len(all_options)} options"
        )
        
        for option in all_options:
            assert option in report.option_usage, (
                f"Option {option} should have usage data"
            )
            usage = report.option_usage[option]
            assert usage.total_tests > 0, (
                f"Option {option} should have positive test count"
            )
        
        # Recommendations should be present (at least some analysis)
        assert isinstance(report.recommendations, list), (
            "Report should contain recommendations list"
        )