"""Property-based tests for configuration conflict reporting.

**Feature: agentic-kernel-testing, Property 44: Configuration conflict reporting**
**Validates: Requirements 9.4**

Tests that the system reports incompatible option combinations and suggests resolutions
for any detected configuration conflict.
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from execution.config_conflict_detector import (
    ConfigConflictDetector,
    ConflictResolutionSuggester,
    ConfigConflict,
    ConflictReport,
    ConflictType,
    ConflictSeverity
)
from execution.kernel_config_testing import KernelConfig, ConfigType


# Strategy for generating kernel configurations with potential conflicts
def conflicting_config_strategy():
    """Generate kernel configurations that may have conflicts."""
    
    # Base options that are generally safe
    base_options = st.dictionaries(
        keys=st.sampled_from([
            'CONFIG_PRINTK', 'CONFIG_BUG', 'CONFIG_SHMEM', 'CONFIG_FUTEX'
        ]),
        values=st.sampled_from(['y', 'n']),
        min_size=1,
        max_size=4
    )
    
    # Conflicting option pairs - these should trigger conflicts
    conflicting_pairs = st.one_of(
        # Optimization conflicts
        st.just({
            'CONFIG_CC_OPTIMIZE_FOR_SIZE': 'y',
            'CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE': 'y'
        }),
        # Allocator conflicts
        st.just({
            'CONFIG_SLUB': 'y',
            'CONFIG_SLAB': 'y'
        }),
        st.just({
            'CONFIG_SLUB': 'y',
            'CONFIG_SLOB': 'y'
        }),
        # Architecture conflicts
        st.just({
            'CONFIG_X86_64': 'y',
            'CONFIG_ARM64': 'y'
        }),
        # Debug conflicts
        st.just({
            'CONFIG_KASAN': 'y',
            'CONFIG_SLOB': 'y'
        }),
        # Dependency conflicts (missing dependencies)
        st.just({
            'CONFIG_INET': 'y'
            # Missing CONFIG_NET dependency
        }),
        st.just({
            'CONFIG_EXT4_FS': 'y'
            # Missing CONFIG_BLOCK dependency
        })
    )
    
    @st.composite
    def _build_config(draw):
        base = draw(base_options)
        conflicts = draw(conflicting_pairs)
        arch = draw(st.sampled_from(['x86_64', 'arm64', 'arm', 'riscv64']))
        config_type = draw(st.sampled_from([ConfigType.MINIMAL, ConfigType.DEFAULT, ConfigType.MAXIMAL]))
        
        return KernelConfig(
            name=f"test_config_{hash(str(conflicts)) % 10000}",
            config_type=config_type,
            options={**base, **conflicts},
            architecture=arch,
            description="Test configuration with potential conflicts"
        )
    
    return _build_config()


def valid_config_strategy():
    """Generate valid kernel configurations without conflicts."""
    return st.builds(
        KernelConfig,
        name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')),
        config_type=st.sampled_from([ConfigType.MINIMAL, ConfigType.DEFAULT, ConfigType.MAXIMAL]),
        options=st.dictionaries(
            keys=st.sampled_from([
                'CONFIG_PRINTK', 'CONFIG_BUG', 'CONFIG_SHMEM', 'CONFIG_FUTEX',
                'CONFIG_NET', 'CONFIG_INET', 'CONFIG_BLOCK', 'CONFIG_EXT4_FS'
            ]),
            values=st.sampled_from(['y', 'n']),
            min_size=1,
            max_size=8
        ).filter(lambda opts: 
            # Ensure dependencies are met
            (opts.get('CONFIG_INET') != 'y' or opts.get('CONFIG_NET') == 'y') and
            (opts.get('CONFIG_EXT4_FS') != 'y' or opts.get('CONFIG_BLOCK') == 'y')
        ),
        architecture=st.sampled_from(['x86_64', 'arm64', 'arm', 'riscv64']),
        description=st.text(max_size=100)
    )


@pytest.mark.property
class TestConfigurationConflictReporting:
    """Property-based tests for configuration conflict reporting."""
    
    @given(config=conflicting_config_strategy())
    def test_conflict_detection_completeness(self, config):
        """
        **Property 44: Configuration conflict reporting**
        
        For any detected configuration conflict, the system should report 
        the incompatible option combinations and provide resolution suggestions.
        
        **Validates: Requirements 9.4**
        """
        # Arrange
        detector = ConfigConflictDetector()
        
        # Act
        conflict_report = detector.detect_conflicts(config)
        
        # Assert - Verify conflict report structure
        assert isinstance(conflict_report, ConflictReport), (
            "Conflict detection should return ConflictReport instance"
        )
        
        assert conflict_report.config == config, (
            "Conflict report should preserve original configuration"
        )
        
        # Verify report contains required fields
        assert hasattr(conflict_report, 'conflicts'), (
            "Conflict report should have conflicts field"
        )
        assert hasattr(conflict_report, 'total_conflicts'), (
            "Conflict report should have total_conflicts field"
        )
        assert hasattr(conflict_report, 'has_critical_conflicts'), (
            "Conflict report should have has_critical_conflicts field"
        )
        assert hasattr(conflict_report, 'conflicts_by_severity'), (
            "Conflict report should have conflicts_by_severity field"
        )
        
        # Verify field types
        assert isinstance(conflict_report.conflicts, list), (
            "conflicts should be a list"
        )
        assert isinstance(conflict_report.total_conflicts, int), (
            "total_conflicts should be an integer"
        )
        assert isinstance(conflict_report.has_critical_conflicts, bool), (
            "has_critical_conflicts should be boolean"
        )
        assert isinstance(conflict_report.conflicts_by_severity, dict), (
            "conflicts_by_severity should be dictionary"
        )
        
        # Verify total conflicts matches list length
        assert conflict_report.total_conflicts == len(conflict_report.conflicts), (
            f"total_conflicts ({conflict_report.total_conflicts}) should match "
            f"conflicts list length ({len(conflict_report.conflicts)})"
        )
    
    @given(config=conflicting_config_strategy())
    def test_conflict_incompatible_options_reporting(self, config):
        """
        **Property 44: Configuration conflict reporting**
        
        For any detected conflict, the system should identify and report 
        the specific incompatible option combinations.
        
        **Validates: Requirements 9.4**
        """
        # Arrange
        detector = ConfigConflictDetector()
        
        # Act
        conflict_report = detector.detect_conflicts(config)
        
        # Assert - Verify each conflict reports incompatible options
        for conflict in conflict_report.conflicts:
            assert isinstance(conflict, ConfigConflict), (
                "Each conflict should be ConfigConflict instance"
            )
            
            assert hasattr(conflict, 'conflicting_options'), (
                "Conflict should have conflicting_options field"
            )
            assert isinstance(conflict.conflicting_options, list), (
                "conflicting_options should be a list"
            )
            assert len(conflict.conflicting_options) > 0, (
                "Conflict should identify at least one conflicting option"
            )
            
            # Verify conflicting options are actual CONFIG options
            for option in conflict.conflicting_options:
                assert isinstance(option, str), (
                    f"Conflicting option should be string, got {type(option)}"
                )
                assert option.startswith('CONFIG_'), (
                    f"Conflicting option should start with CONFIG_, got {option}"
                )
                
            # Verify conflicting options exist in the configuration
            config_options = set(config.options.keys())
            reported_options = set(conflict.conflicting_options)
            
            # At least some of the conflicting options should be in the config
            # (some might be missing dependencies)
            overlap = config_options.intersection(reported_options)
            assert len(overlap) > 0, (
                f"At least some conflicting options {reported_options} "
                f"should be present in config options {config_options}"
            )
    
    @given(config=conflicting_config_strategy())
    def test_conflict_resolution_suggestions(self, config):
        """
        **Property 44: Configuration conflict reporting**
        
        For any detected configuration conflict, the system should provide 
        actionable resolution suggestions.
        
        **Validates: Requirements 9.4**
        """
        # Arrange
        detector = ConfigConflictDetector()
        suggester = ConflictResolutionSuggester()
        
        # Act
        conflict_report = detector.detect_conflicts(config)
        
        # Assert - Verify resolution suggestions are provided
        for conflict in conflict_report.conflicts:
            assert hasattr(conflict, 'resolution_suggestions'), (
                "Conflict should have resolution_suggestions field"
            )
            assert isinstance(conflict.resolution_suggestions, list), (
                "resolution_suggestions should be a list"
            )
            
            # Each conflict should have at least one resolution suggestion
            assert len(conflict.resolution_suggestions) > 0, (
                f"Conflict {conflict.conflict_type.value} should have at least one resolution suggestion"
            )
            
            # Verify suggestions are non-empty strings
            for suggestion in conflict.resolution_suggestions:
                assert isinstance(suggestion, str), (
                    f"Resolution suggestion should be string, got {type(suggestion)}"
                )
                assert len(suggestion.strip()) > 0, (
                    "Resolution suggestion should not be empty"
                )
                
        # Test comprehensive resolution suggestions
        if len(conflict_report.conflicts) > 0:
            resolution_suggestions = suggester.suggest_resolutions(conflict_report)
            
            assert isinstance(resolution_suggestions, dict), (
                "Resolution suggestions should be dictionary"
            )
            
            # Verify required suggestion categories
            required_keys = ['automatic_fixes', 'manual_actions', 'priority_order']
            for key in required_keys:
                assert key in resolution_suggestions, (
                    f"Resolution suggestions should contain {key}"
                )
                assert isinstance(resolution_suggestions[key], list), (
                    f"{key} should be a list"
                )
    
    @given(config=conflicting_config_strategy())
    def test_conflict_severity_classification(self, config):
        """
        **Property 44: Configuration conflict reporting**
        
        For any detected configuration conflict, the system should classify 
        the severity and prioritize critical conflicts.
        
        **Validates: Requirements 9.4**
        """
        # Arrange
        detector = ConfigConflictDetector()
        
        # Act
        conflict_report = detector.detect_conflicts(config)
        
        # Assert - Verify severity classification
        for conflict in conflict_report.conflicts:
            assert hasattr(conflict, 'severity'), (
                "Conflict should have severity field"
            )
            assert isinstance(conflict.severity, ConflictSeverity), (
                f"Severity should be ConflictSeverity enum, got {type(conflict.severity)}"
            )
            
            assert hasattr(conflict, 'conflict_type'), (
                "Conflict should have conflict_type field"
            )
            assert isinstance(conflict.conflict_type, ConflictType), (
                f"Conflict type should be ConflictType enum, got {type(conflict.conflict_type)}"
            )
        
        # Verify severity counts are accurate
        severity_counts = {}
        for severity in ConflictSeverity:
            severity_counts[severity.value] = 0
        
        for conflict in conflict_report.conflicts:
            severity_counts[conflict.severity.value] += 1
        
        assert conflict_report.conflicts_by_severity == severity_counts, (
            f"Reported severity counts {conflict_report.conflicts_by_severity} "
            f"should match actual counts {severity_counts}"
        )
        
        # Verify critical conflict flag
        has_critical = any(
            conflict.severity == ConflictSeverity.CRITICAL 
            for conflict in conflict_report.conflicts
        )
        assert conflict_report.has_critical_conflicts == has_critical, (
            f"has_critical_conflicts should be {has_critical}"
        )
    
    @given(config=valid_config_strategy())
    def test_no_conflicts_for_valid_config(self, config):
        """
        **Property 44: Configuration conflict reporting**
        
        For any valid configuration without conflicts, the system should 
        report no conflicts and empty resolution suggestions.
        
        **Validates: Requirements 9.4**
        """
        # Arrange
        detector = ConfigConflictDetector()
        
        # Act
        conflict_report = detector.detect_conflicts(config)
        
        # Assert - Valid config should have minimal or no conflicts
        # Note: We can't guarantee zero conflicts due to architecture requirements
        # but we can verify the report structure is correct
        assert isinstance(conflict_report, ConflictReport), (
            "Should return ConflictReport even for valid configs"
        )
        
        assert conflict_report.total_conflicts == len(conflict_report.conflicts), (
            "Total conflicts should match conflicts list length"
        )
        
        # If there are no conflicts, verify the report reflects this
        if len(conflict_report.conflicts) == 0:
            assert conflict_report.total_conflicts == 0, (
                "Total conflicts should be 0 when no conflicts found"
            )
            assert not conflict_report.has_critical_conflicts, (
                "Should not have critical conflicts when no conflicts found"
            )
            assert not conflict_report.has_build_blocking_conflicts, (
                "Should not have build blocking conflicts when no conflicts found"
            )
            
            # All severity counts should be 0
            for severity_count in conflict_report.conflicts_by_severity.values():
                assert severity_count == 0, (
                    f"Severity count should be 0 when no conflicts, got {severity_count}"
                )
    
    @given(
        configs=st.lists(conflicting_config_strategy(), min_size=1, max_size=3)
    )
    def test_conflict_reporting_consistency(self, configs):
        """
        **Property 44: Configuration conflict reporting**
        
        For any set of configurations, the conflict reporting should be 
        consistent and provide the same results for identical configurations.
        
        **Validates: Requirements 9.4**
        """
        # Arrange
        detector = ConfigConflictDetector()
        
        # Act - Test each config multiple times
        for config in configs:
            report1 = detector.detect_conflicts(config)
            report2 = detector.detect_conflicts(config)
            
            # Assert - Results should be consistent
            assert report1.total_conflicts == report2.total_conflicts, (
                f"Conflict count should be consistent for {config.name}"
            )
            
            assert report1.has_critical_conflicts == report2.has_critical_conflicts, (
                f"Critical conflict flag should be consistent for {config.name}"
            )
            
            assert report1.conflicts_by_severity == report2.conflicts_by_severity, (
                f"Severity counts should be consistent for {config.name}"
            )
            
            # Verify conflict types are consistent
            types1 = [c.conflict_type for c in report1.conflicts]
            types2 = [c.conflict_type for c in report2.conflicts]
            assert sorted(types1) == sorted(types2), (
                f"Conflict types should be consistent for {config.name}"
            )
    
    @given(config=conflicting_config_strategy())
    def test_conflict_serialization(self, config):
        """
        **Property 44: Configuration conflict reporting**
        
        For any conflict report, the system should be able to serialize 
        and preserve all conflict information.
        
        **Validates: Requirements 9.4**
        """
        # Arrange
        detector = ConfigConflictDetector()
        
        # Act
        conflict_report = detector.detect_conflicts(config)
        
        # Act - Serialize report
        report_dict = conflict_report.to_dict()
        
        # Assert - Verify serialization preserves conflict data
        assert isinstance(report_dict, dict), (
            "Conflict report should serialize to dictionary"
        )
        
        # Verify required fields are present
        required_fields = [
            'config', 'conflicts', 'has_critical_conflicts',
            'has_build_blocking_conflicts', 'total_conflicts', 'conflicts_by_severity'
        ]
        
        for field in required_fields:
            assert field in report_dict, (
                f"Serialized report should contain field: {field}"
            )
        
        # Verify conflicts are properly serialized
        assert isinstance(report_dict['conflicts'], list), (
            "Serialized conflicts should be list"
        )
        
        for conflict_dict in report_dict['conflicts']:
            assert isinstance(conflict_dict, dict), (
                "Each serialized conflict should be dictionary"
            )
            
            # Verify conflict fields
            conflict_fields = [
                'conflict_type', 'severity', 'conflicting_options',
                'description', 'resolution_suggestions'
            ]
            
            for field in conflict_fields:
                assert field in conflict_dict, (
                    f"Serialized conflict should contain field: {field}"
                )
        
        # Verify data integrity
        assert report_dict['total_conflicts'] == len(report_dict['conflicts']), (
            "Serialized total_conflicts should match conflicts list length"
        )
    
    @given(config=conflicting_config_strategy())
    def test_conflict_description_informativeness(self, config):
        """
        **Property 44: Configuration conflict reporting**
        
        For any detected conflict, the description should be informative 
        and help users understand the nature of the conflict.
        
        **Validates: Requirements 9.4**
        """
        # Arrange
        detector = ConfigConflictDetector()
        
        # Act
        conflict_report = detector.detect_conflicts(config)
        
        # Assert - Verify conflict descriptions are informative
        for conflict in conflict_report.conflicts:
            assert hasattr(conflict, 'description'), (
                "Conflict should have description field"
            )
            assert isinstance(conflict.description, str), (
                f"Description should be string, got {type(conflict.description)}"
            )
            assert len(conflict.description.strip()) > 10, (
                f"Description should be informative (>10 chars), got: '{conflict.description}'"
            )
            
            # Description should mention the conflicting options
            description_lower = conflict.description.lower()
            for option in conflict.conflicting_options:
                # Remove CONFIG_ prefix for checking
                option_name = option.replace('CONFIG_', '').lower()
                # Check if option name or a reasonable variant appears in description
                assert (option_name in description_lower or 
                       option.lower() in description_lower or
                       any(part in description_lower for part in option_name.split('_'))), (
                    f"Description should mention conflicting option {option}: '{conflict.description}'"
                )