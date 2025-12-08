"""Unit tests for coverage gap identification functionality."""

import pytest
from analysis.coverage_analyzer import (
    CoverageAnalyzer, CoverageGap, GapType, GapPriority
)
from ai_generator.models import CoverageData


class TestCoverageGapIdentification:
    """Test coverage gap identification."""
    
    def test_identify_line_gaps(self):
        """Test identification of uncovered lines."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=["file.c:1", "file.c:2"],
            uncovered_lines=["file.c:3", "file.c:4"],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        
        assert len(gaps) == 2
        assert all(g.gap_type == GapType.LINE for g in gaps)
        assert {g.line_number for g in gaps} == {3, 4}
    
    def test_identify_branch_gaps(self):
        """Test identification of uncovered branches."""
        coverage_data = CoverageData(
            line_coverage=1.0,
            branch_coverage=0.5,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=[],
            covered_branches=["file.c:10:0"],
            uncovered_branches=["file.c:10:1", "file.c:10:2"]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        
        assert len(gaps) == 2
        assert all(g.gap_type == GapType.BRANCH for g in gaps)
        assert all(g.line_number == 10 for g in gaps)
        assert {g.branch_id for g in gaps} == {1, 2}
    
    def test_identify_mixed_gaps(self):
        """Test identification of both line and branch gaps."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=0.5,
            function_coverage=1.0,
            covered_lines=["file.c:1"],
            uncovered_lines=["file.c:2", "file.c:3"],
            covered_branches=["file.c:10:0"],
            uncovered_branches=["file.c:10:1"]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        
        assert len(gaps) == 3
        line_gaps = [g for g in gaps if g.gap_type == GapType.LINE]
        branch_gaps = [g for g in gaps if g.gap_type == GapType.BRANCH]
        
        assert len(line_gaps) == 2
        assert len(branch_gaps) == 1
    
    def test_no_gaps_when_full_coverage(self):
        """Test that no gaps are identified with full coverage."""
        coverage_data = CoverageData(
            line_coverage=1.0,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=["file.c:1", "file.c:2"],
            uncovered_lines=[],
            covered_branches=["file.c:10:0", "file.c:10:1"],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        
        assert len(gaps) == 0


class TestGapPrioritization:
    """Test gap prioritization."""
    
    def test_security_subsystem_gets_critical_priority(self):
        """Test that security subsystem gaps get critical priority."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=["security/keys/keyring.c:100"],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        prioritized = analyzer.prioritize_gaps(gaps)
        
        assert len(prioritized) == 1
        assert prioritized[0].priority == GapPriority.CRITICAL
    
    def test_branch_gaps_get_high_priority(self):
        """Test that branch gaps generally get high priority."""
        coverage_data = CoverageData(
            line_coverage=1.0,
            branch_coverage=0.5,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=[],
            covered_branches=[],
            uncovered_branches=["drivers/block/virtio.c:50:0"]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        prioritized = analyzer.prioritize_gaps(gaps)
        
        assert len(prioritized) == 1
        assert prioritized[0].priority == GapPriority.HIGH
    
    def test_prioritization_ordering(self):
        """Test that gaps are ordered by priority."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=0.5,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=[
                "security/keys/keyring.c:100",  # Critical
                "drivers/net/ethernet.c:200",    # Medium
                "fs/ext4/inode.c:300"            # Low
            ],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        prioritized = analyzer.prioritize_gaps(gaps)
        
        # Check ordering: critical should come first
        priorities = [g.priority for g in prioritized]
        priority_values = [
            0 if p == GapPriority.CRITICAL else
            1 if p == GapPriority.HIGH else
            2 if p == GapPriority.MEDIUM else 3
            for p in priorities
        ]
        
        # Verify non-decreasing order
        assert all(priority_values[i] <= priority_values[i+1] 
                  for i in range(len(priority_values)-1))


class TestGapReporting:
    """Test gap report generation."""
    
    def test_report_includes_total_count(self):
        """Test that report includes total gap count."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=["file.c:1", "file.c:2", "file.c:3"],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        prioritized = analyzer.prioritize_gaps(gaps)
        report = analyzer.generate_gap_report(prioritized)
        
        assert "Total Gaps: 3" in report
    
    def test_report_includes_priority_sections(self):
        """Test that report includes priority sections."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=[
                "security/keys/keyring.c:100",
                "drivers/net/ethernet.c:200"
            ],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        prioritized = analyzer.prioritize_gaps(gaps)
        report = analyzer.generate_gap_report(prioritized)
        
        assert "CRITICAL Priority:" in report or "HIGH Priority:" in report
    
    def test_report_with_no_gaps(self):
        """Test report generation with no gaps."""
        coverage_data = CoverageData(
            line_coverage=1.0,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=["file.c:1"],
            uncovered_lines=[],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        prioritized = analyzer.prioritize_gaps(gaps)
        report = analyzer.generate_gap_report(prioritized)
        
        assert "Total Gaps: 0" in report


class TestSubsystemIdentification:
    """Test subsystem identification from file paths."""
    
    def test_identify_kernel_subsystem(self):
        """Test identification of kernel subsystem."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=["kernel/sched/core.c:100"],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        
        assert len(gaps) == 1
        assert gaps[0].subsystem == "sched"
    
    def test_identify_driver_subsystem(self):
        """Test identification of driver subsystem."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=["drivers/net/ethernet.c:100"],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        
        assert len(gaps) == 1
        assert gaps[0].subsystem == "net"
    
    def test_identify_fs_subsystem(self):
        """Test identification of filesystem subsystem."""
        coverage_data = CoverageData(
            line_coverage=0.5,
            branch_coverage=1.0,
            function_coverage=1.0,
            covered_lines=[],
            uncovered_lines=["fs/ext4/inode.c:100"],
            covered_branches=[],
            uncovered_branches=[]
        )
        
        analyzer = CoverageAnalyzer()
        gaps = analyzer.identify_coverage_gaps(coverage_data)
        
        assert len(gaps) == 1
        assert gaps[0].subsystem == "ext4"


class TestGapDataModel:
    """Test CoverageGap data model."""
    
    def test_gap_to_dict(self):
        """Test gap serialization to dictionary."""
        gap = CoverageGap(
            gap_type=GapType.LINE,
            file_path="test.c",
            line_number=100,
            priority=GapPriority.HIGH,
            subsystem="test"
        )
        
        gap_dict = gap.to_dict()
        
        assert gap_dict['gap_type'] == 'line'
        assert gap_dict['file_path'] == 'test.c'
        assert gap_dict['line_number'] == 100
        assert gap_dict['priority'] == 'high'
        assert gap_dict['subsystem'] == 'test'
    
    def test_gap_from_dict(self):
        """Test gap deserialization from dictionary."""
        gap_dict = {
            'gap_type': 'branch',
            'file_path': 'test.c',
            'line_number': 100,
            'branch_id': 1,
            'priority': 'critical',
            'subsystem': 'test',
            'context': '',
            'complexity_score': 0.5
        }
        
        gap = CoverageGap.from_dict(gap_dict)
        
        assert gap.gap_type == GapType.BRANCH
        assert gap.file_path == 'test.c'
        assert gap.line_number == 100
        assert gap.branch_id == 1
        assert gap.priority == GapPriority.CRITICAL
    
    def test_gap_string_representation(self):
        """Test gap string representation."""
        line_gap = CoverageGap(
            gap_type=GapType.LINE,
            file_path="test.c",
            line_number=100,
            priority=GapPriority.HIGH
        )
        
        branch_gap = CoverageGap(
            gap_type=GapType.BRANCH,
            file_path="test.c",
            line_number=100,
            branch_id=1,
            priority=GapPriority.CRITICAL
        )
        
        assert "test.c:100" in str(line_gap)
        assert "[high]" in str(line_gap)
        assert "test.c:100:branch1" in str(branch_gap)
        assert "[critical]" in str(branch_gap)
