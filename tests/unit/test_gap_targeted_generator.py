"""Unit tests for gap-targeted test generator."""

import pytest
import json
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile
import os

from ai_generator.gap_targeted_generator import GapTargetedTestGenerator
from ai_generator.models import TestCase, TestType
from ai_generator.llm_providers import LLMResponse
from analysis.coverage_analyzer import CoverageGap, GapType, GapPriority


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    return provider


@pytest.fixture
def generator(mock_llm_provider):
    """Create a gap-targeted test generator with mock LLM."""
    return GapTargetedTestGenerator(llm_provider=mock_llm_provider)


@pytest.fixture
def sample_line_gap():
    """Create a sample line coverage gap."""
    return CoverageGap(
        gap_type=GapType.LINE,
        file_path="kernel/sched/core.c",
        line_number=1234,
        function_name="schedule",
        context="if (unlikely(prev->state == TASK_DEAD)) {\n    prev->sched_class->task_dead(prev);\n}",
        subsystem="scheduler",
        priority=GapPriority.HIGH
    )


@pytest.fixture
def sample_branch_gap():
    """Create a sample branch coverage gap."""
    return CoverageGap(
        gap_type=GapType.BRANCH,
        file_path="fs/ext4/inode.c",
        line_number=567,
        branch_id=2,
        function_name="ext4_write_begin",
        context="if (flags & AOP_FLAG_NOFS) {\n    return -ENOMEM;\n}",
        subsystem="ext4",
        priority=GapPriority.MEDIUM
    )


@pytest.fixture
def temp_source_dir():
    """Create a temporary source directory with sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample source file
        kernel_dir = Path(tmpdir) / "kernel" / "sched"
        kernel_dir.mkdir(parents=True)
        
        source_file = kernel_dir / "core.c"
        source_file.write_text("""
static void schedule_task(struct task_struct *task) {
    if (task->state == TASK_RUNNING) {
        enqueue_task(task);
    }
    
    if (unlikely(task->state == TASK_DEAD)) {
        task->sched_class->task_dead(task);
    }
    
    context_switch(task);
}
""")
        
        yield tmpdir


class TestGapTargetedTestGenerator:
    """Tests for GapTargetedTestGenerator."""
    
    def test_generate_test_for_line_gap(self, generator, mock_llm_provider, sample_line_gap):
        """Test generating a test for a line gap."""
        # Mock LLM response
        mock_response = LLMResponse(
            content=json.dumps({
                'name': 'Test TASK_DEAD handling',
                'description': 'Test that dead tasks are handled correctly',
                'test_script': 'def test_task_dead(): pass',
                'expected_outcome': {'should_pass': True}
            }),
            model='gpt-4',
            tokens_used=100,
            finish_reason='stop',
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        # Generate test
        test_case = generator.generate_test_for_gap(sample_line_gap)
        
        # Verify test case
        assert test_case is not None
        assert test_case.name == 'Test TASK_DEAD handling'
        assert test_case.target_subsystem == 'scheduler'
        assert 'kernel/sched/core.c:1234' in test_case.code_paths
        assert test_case.metadata['gap_targeted'] is True
        assert test_case.metadata['target_gap']['line_number'] == 1234
        
        # Verify LLM was called
        mock_llm_provider.generate_with_retry.assert_called_once()
    
    def test_generate_test_for_branch_gap(self, generator, mock_llm_provider, sample_branch_gap):
        """Test generating a test for a branch gap."""
        # Mock LLM response
        mock_response = LLMResponse(
            content=json.dumps({
                'name': 'Test AOP_FLAG_NOFS branch',
                'description': 'Test NOFS flag handling',
                'test_script': 'def test_nofs_flag(): pass',
                'expected_outcome': {'should_pass': True}
            }),
            model='gpt-4',
            tokens_used=100,
            finish_reason='stop',
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        # Generate test
        test_case = generator.generate_test_for_gap(sample_branch_gap)
        
        # Verify test case
        assert test_case is not None
        assert test_case.target_subsystem == 'ext4'
        assert test_case.metadata['target_gap']['branch_id'] == 2
        assert test_case.metadata['target_gap']['gap_type'] == 'branch'
    
    def test_generate_tests_for_multiple_gaps(self, generator, mock_llm_provider, 
                                             sample_line_gap, sample_branch_gap):
        """Test generating tests for multiple gaps."""
        # Mock LLM responses
        mock_response = LLMResponse(
            content=json.dumps({
                'name': 'Test gap',
                'description': 'Test description',
                'test_script': 'def test(): pass',
                'expected_outcome': {'should_pass': True}
            }),
            model='gpt-4',
            tokens_used=100,
            finish_reason='stop',
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        # Generate tests for multiple gaps
        gaps = [sample_line_gap, sample_branch_gap]
        test_cases = generator.generate_tests_for_gaps(gaps)
        
        # Verify we got tests for both gaps
        assert len(test_cases) == 2
        assert all(tc.metadata['gap_targeted'] for tc in test_cases)
    
    def test_fallback_test_generation(self, generator, mock_llm_provider, sample_line_gap):
        """Test fallback test generation when LLM fails."""
        # Make LLM fail
        mock_llm_provider.generate_with_retry.side_effect = Exception("LLM failed")
        
        # Generate test (should fall back)
        test_case = generator.generate_test_for_gap(sample_line_gap)
        
        # Verify fallback test was created
        assert test_case is not None
        assert test_case.metadata['fallback'] is True
        assert 'TODO' in test_case.test_script
        assert test_case.target_subsystem == 'scheduler'
    
    def test_path_to_test_case_line(self, generator, mock_llm_provider):
        """Test converting a line path to test case."""
        # Mock LLM response
        mock_response = LLMResponse(
            content=json.dumps({
                'name': 'Test from path',
                'description': 'Test description',
                'test_script': 'def test(): pass',
                'expected_outcome': {'should_pass': True}
            }),
            model='gpt-4',
            tokens_used=100,
            finish_reason='stop',
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        # Convert path to test case
        test_case = generator.path_to_test_case("kernel/sched/core.c:1234")
        
        # Verify test case
        assert test_case is not None
        assert 'kernel/sched/core.c:1234' in test_case.code_paths
        assert test_case.metadata['gap_targeted'] is True
    
    def test_path_to_test_case_branch(self, generator, mock_llm_provider):
        """Test converting a branch path to test case."""
        # Mock LLM response
        mock_response = LLMResponse(
            content=json.dumps({
                'name': 'Test branch',
                'description': 'Test description',
                'test_script': 'def test(): pass',
                'expected_outcome': {'should_pass': True}
            }),
            model='gpt-4',
            tokens_used=100,
            finish_reason='stop',
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        # Convert branch path to test case
        test_case = generator.path_to_test_case("fs/ext4/inode.c:567:2")
        
        # Verify test case
        assert test_case is not None
        assert test_case.metadata['target_gap']['branch_id'] == 2
        assert test_case.metadata['target_gap']['gap_type'] == 'branch'
    
    def test_path_to_test_case_invalid(self, generator):
        """Test handling invalid path format."""
        test_case = generator.path_to_test_case("invalid")
        assert test_case is None
    
    def test_verify_gap_coverage_by_metadata(self, generator, sample_line_gap):
        """Test verifying gap coverage using metadata."""
        test_case = TestCase(
            id="test_1",
            name="Test",
            description="Test",
            test_type=TestType.UNIT,
            target_subsystem="scheduler",
            test_script="pass",
            metadata={
                'target_gap': {
                    'file_path': 'kernel/sched/core.c',
                    'line_number': 1234
                }
            }
        )
        
        assert generator.verify_gap_coverage(test_case, sample_line_gap) is True
    
    def test_verify_gap_coverage_by_code_paths(self, generator, sample_line_gap):
        """Test verifying gap coverage using code paths."""
        test_case = TestCase(
            id="test_1",
            name="Test",
            description="Test",
            test_type=TestType.UNIT,
            target_subsystem="scheduler",
            code_paths=["kernel/sched/core.c:1234"],
            test_script="pass"
        )
        
        assert generator.verify_gap_coverage(test_case, sample_line_gap) is True
    
    def test_verify_gap_coverage_by_function(self, generator, sample_line_gap):
        """Test verifying gap coverage using function name."""
        test_case = TestCase(
            id="test_1",
            name="Test",
            description="Test",
            test_type=TestType.UNIT,
            target_subsystem="scheduler",
            test_script="def test_schedule(): pass"
        )
        
        assert generator.verify_gap_coverage(test_case, sample_line_gap) is True
    
    def test_verify_gap_coverage_no_match(self, generator, sample_line_gap):
        """Test verifying gap coverage with no match."""
        test_case = TestCase(
            id="test_1",
            name="Test",
            description="Test",
            test_type=TestType.UNIT,
            target_subsystem="memory",
            test_script="def test_other(): pass"
        )
        
        assert generator.verify_gap_coverage(test_case, sample_line_gap) is False
    
    def test_read_code_context(self, generator, temp_source_dir):
        """Test reading code context from source file."""
        context = generator._read_code_context(
            temp_source_dir,
            "kernel/sched/core.c",
            7
        )
        
        assert context != ""
        assert "TASK_DEAD" in context
    
    def test_read_code_context_nonexistent_file(self, generator):
        """Test reading context from nonexistent file."""
        context = generator._read_code_context(
            "/nonexistent",
            "file.c",
            10
        )
        
        assert context == ""
    
    def test_extract_function_name(self, generator, temp_source_dir):
        """Test extracting function name from source."""
        function_name = generator._extract_function_name(
            temp_source_dir,
            "kernel/sched/core.c",
            7
        )
        
        assert function_name == "schedule_task"
    
    def test_determine_subsystem_drivers(self, generator):
        """Test determining subsystem from drivers path."""
        subsystem = generator._determine_subsystem("drivers/net/ethernet/intel/e1000.c")
        assert subsystem == "net"
    
    def test_determine_subsystem_kernel(self, generator):
        """Test determining subsystem from kernel path."""
        subsystem = generator._determine_subsystem("kernel/sched/core.c")
        assert subsystem == "sched"
    
    def test_determine_subsystem_unknown(self, generator):
        """Test determining subsystem for unknown path."""
        subsystem = generator._determine_subsystem("unknown.c")
        assert subsystem == "unknown"
    
    def test_extract_json_from_code_block(self, generator):
        """Test extracting JSON from markdown code block."""
        text = """
Here is the test:
```json
{"name": "test", "value": 123}
```
"""
        result = generator._extract_json(text)
        assert result == {"name": "test", "value": 123}
    
    def test_extract_json_from_plain_text(self, generator):
        """Test extracting JSON from plain text."""
        text = '{"name": "test", "value": 123}'
        result = generator._extract_json(text)
        assert result == {"name": "test", "value": 123}
    
    def test_generate_test_with_source_dir(self, generator, mock_llm_provider, 
                                          sample_line_gap, temp_source_dir):
        """Test generating test with source directory for context."""
        # Mock LLM response
        mock_response = LLMResponse(
            content=json.dumps({
                'name': 'Test with context',
                'description': 'Test description',
                'test_script': 'def test(): pass',
                'expected_outcome': {'should_pass': True}
            }),
            model='gpt-4',
            tokens_used=100,
            finish_reason='stop',
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        # Generate test with source directory
        test_case = generator.generate_test_for_gap(sample_line_gap, temp_source_dir)
        
        # Verify test was generated
        assert test_case is not None
        
        # Verify LLM was called with context
        call_args = mock_llm_provider.generate_with_retry.call_args[0][0]
        assert "Code Context:" in call_args
