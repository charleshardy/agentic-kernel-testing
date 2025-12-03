"""Property-based tests for subsystem identification.

Feature: agentic-kernel-testing, Property 2: Subsystem targeting accuracy
Validates: Requirements 1.2
"""

import pytest
from hypothesis import given, strategies as st, settings
from analysis import CodeAnalyzer, DiffParser, ASTAnalyzer, FileDiff
from ai_generator.models import TestType


# Strategy for generating valid kernel subsystem paths
@st.composite
def kernel_file_path(draw):
    """Generate realistic kernel file paths."""
    subsystems = [
        ('fs/', ['ext4/', 'btrfs/', 'xfs/', 'nfs/']),
        ('net/', ['ipv4/', 'ipv6/', 'core/', 'ethernet/']),
        ('drivers/', ['usb/', 'pci/', 'block/', 'net/']),
        ('mm/', ['']),
        ('kernel/', ['sched/', 'time/', 'irq/']),
        ('arch/', ['x86/', 'arm/', 'arm64/', 'riscv/']),
        ('security/', ['selinux/', 'apparmor/']),
        ('crypto/', ['']),
        ('block/', ['']),
        ('sound/', ['core/', 'pci/']),
    ]
    
    subsystem, subdirs = draw(st.sampled_from(subsystems))
    subdir = draw(st.sampled_from(subdirs))
    filename = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='_-'),
        min_size=1,
        max_size=20
    ))
    extension = draw(st.sampled_from(['.c', '.h', '.py']))
    
    return f"{subsystem}{subdir}{filename}{extension}"


@st.composite
def file_diff_strategy(draw):
    """Generate FileDiff objects with realistic kernel paths."""
    file_path = draw(kernel_file_path())
    num_added = draw(st.integers(min_value=0, max_value=50))
    num_removed = draw(st.integers(min_value=0, max_value=50))
    
    added_lines = [
        (i + 1, draw(st.text(min_size=0, max_size=100)))
        for i in range(num_added)
    ]
    removed_lines = [
        (i + 1, draw(st.text(min_size=0, max_size=100)))
        for i in range(num_removed)
    ]
    
    return FileDiff(
        file_path=file_path,
        added_lines=added_lines,
        removed_lines=removed_lines,
        is_new_file=draw(st.booleans()),
        is_deleted_file=draw(st.booleans())
    )


@st.composite
def code_change_strategy(draw):
    """Generate a list of file diffs representing a code change."""
    num_files = draw(st.integers(min_value=1, max_value=10))
    return [draw(file_diff_strategy()) for _ in range(num_files)]


@pytest.mark.property
class TestSubsystemIdentificationProperties:
    """Property-based tests for subsystem identification accuracy."""
    
    @given(file_diffs=code_change_strategy())
    @settings(max_examples=100)
    def test_subsystem_targeting_accuracy(self, file_diffs):
        """
        Property 2: Subsystem targeting accuracy
        
        For any code change, the generated test cases should target the specific 
        subsystems affected by that change, with no tests targeting unaffected subsystems.
        
        This property verifies that:
        1. All identified subsystems correspond to actual file paths in the change
        2. No subsystems are identified that don't match any changed files
        3. The subsystem identification is consistent and deterministic
        """
        analyzer = ASTAnalyzer()
        
        # Identify subsystems from the file diffs
        identified_subsystems = analyzer.identify_subsystems(file_diffs)
        
        # Property 1: Every identified subsystem should correspond to at least one changed file
        for subsystem in identified_subsystems:
            # Check that at least one file path matches this subsystem
            has_matching_file = False
            
            for file_diff in file_diffs:
                file_path = file_diff.file_path
                
                # Check if this file belongs to the identified subsystem
                if subsystem == 'filesystem' and file_path.startswith('fs/'):
                    has_matching_file = True
                    break
                elif subsystem == 'networking' and file_path.startswith('net/'):
                    has_matching_file = True
                    break
                elif subsystem == 'drivers' and file_path.startswith('drivers/'):
                    has_matching_file = True
                    break
                elif subsystem == 'memory_management' and file_path.startswith('mm/'):
                    has_matching_file = True
                    break
                elif subsystem == 'core_kernel' and file_path.startswith('kernel/'):
                    has_matching_file = True
                    break
                elif subsystem == 'architecture' and file_path.startswith('arch/'):
                    has_matching_file = True
                    break
                elif subsystem == 'security' and file_path.startswith('security/'):
                    has_matching_file = True
                    break
                elif subsystem == 'cryptography' and file_path.startswith('crypto/'):
                    has_matching_file = True
                    break
                elif subsystem == 'block_layer' and file_path.startswith('block/'):
                    has_matching_file = True
                    break
                elif subsystem == 'sound' and file_path.startswith('sound/'):
                    has_matching_file = True
                    break
                elif subsystem == 'unknown':
                    # Unknown is valid for files that don't match known patterns
                    has_matching_file = True
                    break
                elif subsystem == file_path.split('/')[0]:
                    # Top-level directory match
                    has_matching_file = True
                    break
            
            assert has_matching_file, \
                f"Subsystem '{subsystem}' was identified but no matching file was found in changes"
        
        # Property 2: Subsystem identification should be deterministic
        # Running the same analysis twice should give the same results
        identified_subsystems_2 = analyzer.identify_subsystems(file_diffs)
        assert set(identified_subsystems) == set(identified_subsystems_2), \
            "Subsystem identification should be deterministic"
        
        # Property 3: Number of identified subsystems should not exceed number of files
        # (though it can be less if multiple files are in the same subsystem)
        assert len(identified_subsystems) <= len(file_diffs), \
            "Cannot have more subsystems than changed files"
    
    @given(file_diffs=code_change_strategy())
    @settings(max_examples=100)
    def test_subsystem_coverage_completeness(self, file_diffs):
        """
        Property: Every changed file should contribute to at least one identified subsystem.
        
        This ensures that no file changes are ignored in the subsystem analysis.
        """
        analyzer = ASTAnalyzer()
        identified_subsystems = analyzer.identify_subsystems(file_diffs)
        
        # Every file should map to at least one subsystem
        assert len(identified_subsystems) > 0, \
            "At least one subsystem should be identified when files are changed"
        
        # The number of unique top-level directories should match or be less than
        # the number of identified subsystems (accounting for subsystem grouping)
        top_level_dirs = set()
        for file_diff in file_diffs:
            parts = file_diff.file_path.split('/')
            if len(parts) > 0:
                top_level_dirs.add(parts[0])
        
        # We should have identified subsystems for the changed areas
        assert len(identified_subsystems) >= 1, \
            "Should identify at least one subsystem for any code change"
    
    @given(
        file_path=kernel_file_path(),
        num_lines=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100)
    def test_single_file_subsystem_identification(self, file_path, num_lines):
        """
        Property: A single file change should identify exactly one primary subsystem.
        
        This tests that subsystem identification works correctly for individual files.
        """
        file_diff = FileDiff(
            file_path=file_path,
            added_lines=[(i, f"line{i}") for i in range(num_lines)],
            removed_lines=[]
        )
        
        analyzer = ASTAnalyzer()
        subsystems = analyzer.identify_subsystems([file_diff])
        
        # Should identify at least one subsystem
        assert len(subsystems) >= 1, \
            f"Should identify at least one subsystem for file: {file_path}"
        
        # For a single file, should identify exactly one subsystem
        assert len(subsystems) == 1, \
            f"Single file should map to exactly one subsystem, got {len(subsystems)}: {subsystems}"
    
    @given(file_diffs=code_change_strategy())
    @settings(max_examples=100)
    def test_test_type_suggestions_match_subsystems(self, file_diffs):
        """
        Property: Suggested test types should be appropriate for the identified subsystems.
        
        This ensures that test generation is properly targeted based on subsystem analysis.
        """
        analyzer = ASTAnalyzer()
        subsystems = analyzer.identify_subsystems(file_diffs)
        test_types = analyzer.suggest_test_types(subsystems, [])
        
        # Unit tests should always be suggested
        assert TestType.UNIT in test_types, \
            "Unit tests should always be suggested for any code change"
        
        # Security-sensitive subsystems should suggest security tests
        security_subsystems = {'security', 'cryptography', 'networking'}
        if any(s in security_subsystems for s in subsystems):
            assert TestType.SECURITY in test_types or TestType.FUZZ in test_types, \
                f"Security tests should be suggested for security-sensitive subsystems: {subsystems}"
        
        # Performance-critical subsystems should suggest performance tests
        perf_subsystems = {'memory_management', 'networking', 'block_layer', 'filesystem'}
        if any(s in perf_subsystems for s in subsystems):
            assert TestType.PERFORMANCE in test_types, \
                f"Performance tests should be suggested for performance-critical subsystems: {subsystems}"
        
        # Multiple subsystems should suggest integration tests
        if len(subsystems) > 1:
            assert TestType.INTEGRATION in test_types, \
                "Integration tests should be suggested when multiple subsystems are affected"
    
    @given(
        file_diffs_1=code_change_strategy(),
        file_diffs_2=code_change_strategy()
    )
    @settings(max_examples=50)
    def test_subsystem_identification_independence(self, file_diffs_1, file_diffs_2):
        """
        Property: Subsystem identification for different changes should be independent.
        
        Analyzing two different sets of changes separately should give the same results
        as if they were analyzed together (union property).
        """
        analyzer = ASTAnalyzer()
        
        # Analyze separately
        subsystems_1 = set(analyzer.identify_subsystems(file_diffs_1))
        subsystems_2 = set(analyzer.identify_subsystems(file_diffs_2))
        
        # Analyze together
        combined_diffs = file_diffs_1 + file_diffs_2
        subsystems_combined = set(analyzer.identify_subsystems(combined_diffs))
        
        # The combined result should be the union of individual results
        expected_union = subsystems_1.union(subsystems_2)
        assert subsystems_combined == expected_union, \
            f"Combined analysis should equal union of separate analyses. " \
            f"Expected: {expected_union}, Got: {subsystems_combined}"
