"""Unit tests for fix suggestion generator."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from analysis.fix_suggestion_generator import (
    FixSuggestionGenerator,
    CodePatchGenerator,
    CodeContext
)
from ai_generator.models import (
    TestResult, FailureAnalysis, FixSuggestion, Commit,
    TestStatus, FailureInfo, Environment, HardwareConfig,
    EnvironmentStatus, ArtifactBundle
)
from ai_generator.llm_providers import LLMResponse


class TestCodePatchGenerator:
    """Tests for CodePatchGenerator."""
    
    def test_format_patch_basic(self):
        """Test basic patch formatting."""
        generator = CodePatchGenerator()
        
        original = "int x = 0;"
        fixed = "int x = 1;"
        
        patch = generator.format_patch(
            file_path="test.c",
            original_code=original,
            fixed_code=fixed,
            line_number=10
        )
        
        assert "--- a/test.c" in patch
        assert "+++ b/test.c" in patch
        assert "-int x = 0;" in patch
        assert "+int x = 1;" in patch
        assert "@@ -10,1 +10,1 @@" in patch
    
    def test_format_patch_multiline(self):
        """Test patch formatting with multiple lines."""
        generator = CodePatchGenerator()
        
        original = "int x = 0;\nint y = 0;"
        fixed = "int x = 1;\nint y = 1;"
        
        patch = generator.format_patch(
            file_path="test.c",
            original_code=original,
            fixed_code=fixed
        )
        
        assert "-int x = 0;" in patch
        assert "-int y = 0;" in patch
        assert "+int x = 1;" in patch
        assert "+int y = 1;" in patch
    
    def test_extract_code_from_markdown(self):
        """Test extracting code from markdown code blocks."""
        generator = CodePatchGenerator()
        
        response = """Here's the fix:
```c
int x = 1;
return x;
```
This should work."""
        
        code = generator.extract_code_from_response(response)
        assert code == "int x = 1;\nreturn x;"
    
    def test_extract_code_from_marker(self):
        """Test extracting code from CODE: marker."""
        generator = CodePatchGenerator()
        
        response = """CODE:
int x = 1;
return x;

That's the fix."""
        
        code = generator.extract_code_from_response(response)
        assert code == "int x = 1;\nreturn x;"
    
    def test_extract_code_no_code(self):
        """Test extracting code when none present."""
        generator = CodePatchGenerator()
        
        response = "Just some text without code"
        code = generator.extract_code_from_response(response)
        assert code is None


class TestFixSuggestionGenerator:
    """Tests for FixSuggestionGenerator."""
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create a mock LLM provider."""
        provider = Mock()
        provider.generate_with_retry = Mock()
        return provider
    
    @pytest.fixture
    def generator(self, mock_llm_provider):
        """Create a fix suggestion generator with mock provider."""
        return FixSuggestionGenerator(llm_provider=mock_llm_provider)
    
    @pytest.fixture
    def sample_failure_analysis(self):
        """Create a sample failure analysis."""
        return FailureAnalysis(
            failure_id="test-001",
            root_cause="NULL pointer dereference in function foo",
            confidence=0.8,
            error_pattern="null_pointer",
            stack_trace="foo+0x10\nbar+0x20",
            reproducibility=0.9
        )
    
    @pytest.fixture
    def sample_code_context(self):
        """Create a sample code context."""
        return CodeContext(
            file_path="kernel/foo.c",
            function_name="foo",
            line_number=42,
            surrounding_code="int *ptr = NULL;\n*ptr = 1;",
            error_message="NULL pointer dereference"
        )
    
    def test_initialization_with_provider(self, mock_llm_provider):
        """Test initialization with pre-configured provider."""
        generator = FixSuggestionGenerator(llm_provider=mock_llm_provider)
        assert generator.llm_provider == mock_llm_provider
        assert generator.max_suggestions == 3
    
    def test_initialization_with_provider_type(self):
        """Test initialization with provider type."""
        # This will fail without actual API keys, so we expect an error
        with pytest.raises(RuntimeError):
            FixSuggestionGenerator(provider_type="openai")
    
    def test_initialization_no_provider(self):
        """Test initialization without provider raises error."""
        with pytest.raises(ValueError):
            FixSuggestionGenerator()
    
    def test_generate_fix_suggestions_success(
        self,
        generator,
        mock_llm_provider,
        sample_failure_analysis
    ):
        """Test successful fix suggestion generation."""
        # Mock LLM response
        mock_response = LLMResponse(
            content="""FIX_1:
DESCRIPTION: Add NULL pointer check before dereferencing
RATIONALE: The error indicates a NULL pointer dereference
CONFIDENCE: 0.9

FIX_2:
DESCRIPTION: Initialize pointer properly
RATIONALE: Uninitialized pointer can cause crashes
CONFIDENCE: 0.7""",
            model="gpt-4",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        suggestions = generator.generate_fix_suggestions(sample_failure_analysis)
        
        assert len(suggestions) <= 3
        assert len(suggestions) >= 1
        assert all(isinstance(s, FixSuggestion) for s in suggestions)
        assert all(0.0 <= s.confidence <= 1.0 for s in suggestions)
        
        # Check that suggestions are ranked by confidence
        confidences = [s.confidence for s in suggestions]
        assert confidences == sorted(confidences, reverse=True)
    
    def test_generate_fix_suggestions_with_context(
        self,
        generator,
        mock_llm_provider,
        sample_failure_analysis,
        sample_code_context
    ):
        """Test fix suggestion generation with code context."""
        mock_response = LLMResponse(
            content="""FIX_1:
DESCRIPTION: Check pointer before use
RATIONALE: Prevents NULL dereference
CONFIDENCE: 0.85""",
            model="gpt-4",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        suggestions = generator.generate_fix_suggestions(
            sample_failure_analysis,
            code_context=sample_code_context
        )
        
        assert len(suggestions) >= 1
        # Verify that prompt included code context
        call_args = mock_llm_provider.generate_with_retry.call_args
        prompt = call_args[0][0]
        assert "kernel/foo.c" in prompt
        assert "foo" in prompt
    
    def test_generate_fix_suggestions_with_commits(
        self,
        generator,
        mock_llm_provider,
        sample_failure_analysis
    ):
        """Test fix suggestion generation with suspicious commits."""
        commits = [
            Commit(
                sha="abc123",
                message="Fix memory allocation",
                author="dev@example.com",
                timestamp=datetime.now(),
                files_changed=["kernel/foo.c"]
            )
        ]
        
        mock_response = LLMResponse(
            content="""FIX_1:
DESCRIPTION: Revert recent memory changes
RATIONALE: Commit abc123 may have introduced the bug
CONFIDENCE: 0.75""",
            model="gpt-4",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        suggestions = generator.generate_fix_suggestions(
            sample_failure_analysis,
            commits=commits
        )
        
        assert len(suggestions) >= 1
        # Verify that prompt included commits
        call_args = mock_llm_provider.generate_with_retry.call_args
        prompt = call_args[0][0]
        assert "abc123" in prompt
    
    def test_generate_fix_suggestions_llm_failure(
        self,
        generator,
        mock_llm_provider,
        sample_failure_analysis
    ):
        """Test fix suggestion generation when LLM fails."""
        mock_llm_provider.generate_with_retry.side_effect = Exception("API error")
        
        suggestions = generator.generate_fix_suggestions(sample_failure_analysis)
        
        # Should return empty list on failure
        assert suggestions == []
    
    def test_generate_code_patch_success(
        self,
        generator,
        mock_llm_provider,
        sample_code_context
    ):
        """Test successful code patch generation."""
        fix_suggestion = FixSuggestion(
            description="Add NULL check",
            confidence=0.8,
            rationale="Prevents crash"
        )
        
        mock_response = LLMResponse(
            content="""```c
int *ptr = NULL;
if (ptr != NULL) {
    *ptr = 1;
}
```""",
            model="gpt-4",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        patch = generator.generate_code_patch(fix_suggestion, sample_code_context)
        
        assert patch is not None
        assert "--- a/kernel/foo.c" in patch
        assert "+++ b/kernel/foo.c" in patch
        assert "if (ptr != NULL)" in patch
    
    def test_generate_code_patch_no_code_context(
        self,
        generator,
        sample_code_context
    ):
        """Test patch generation without surrounding code."""
        fix_suggestion = FixSuggestion(
            description="Add NULL check",
            confidence=0.8,
            rationale="Prevents crash"
        )
        
        # Remove surrounding code
        sample_code_context.surrounding_code = None
        
        patch = generator.generate_code_patch(fix_suggestion, sample_code_context)
        
        assert patch is None
    
    def test_generate_code_patch_llm_failure(
        self,
        generator,
        mock_llm_provider,
        sample_code_context
    ):
        """Test patch generation when LLM fails."""
        fix_suggestion = FixSuggestion(
            description="Add NULL check",
            confidence=0.8,
            rationale="Prevents crash"
        )
        
        mock_llm_provider.generate_with_retry.side_effect = Exception("API error")
        
        patch = generator.generate_code_patch(fix_suggestion, sample_code_context)
        
        assert patch is None
    
    def test_parse_fix_response_multiple_fixes(self, generator):
        """Test parsing response with multiple fixes."""
        response = """FIX_1:
DESCRIPTION: Add NULL check
RATIONALE: Prevents NULL dereference
CONFIDENCE: 0.9

FIX_2:
DESCRIPTION: Initialize pointer
RATIONALE: Uninitialized pointers are dangerous
CONFIDENCE: 0.7

FIX_3:
DESCRIPTION: Use safe allocation
RATIONALE: Ensures memory is available
CONFIDENCE: 0.6"""
        
        suggestions = generator._parse_fix_response(response, None)
        
        assert len(suggestions) == 3
        assert suggestions[0].description == "Add NULL check"
        assert suggestions[0].confidence == 0.9
        assert suggestions[1].description == "Initialize pointer"
        assert suggestions[1].confidence == 0.7
    
    def test_parse_fix_response_malformed(self, generator):
        """Test parsing malformed response."""
        response = "This is not a properly formatted response"
        
        suggestions = generator._parse_fix_response(response, None)
        
        # Should handle gracefully
        assert isinstance(suggestions, list)
    
    def test_rank_suggestions(self, generator, sample_failure_analysis):
        """Test suggestion ranking."""
        suggestions = [
            FixSuggestion(
                description="Fix with null_pointer mention",
                confidence=0.7,
                rationale="Short"
            ),
            FixSuggestion(
                description="Generic fix",
                confidence=0.9,
                rationale="This is a very detailed rationale explaining the fix"
            ),
            FixSuggestion(
                description="Another fix",
                confidence=0.5,
                rationale="Medium"
            )
        ]
        
        ranked = generator._rank_suggestions(suggestions, sample_failure_analysis)
        
        # Should be sorted by confidence (after adjustments)
        confidences = [s.confidence for s in ranked]
        assert confidences == sorted(confidences, reverse=True)
        
        # All confidences should be scaled by failure analysis confidence
        assert all(s.confidence <= 0.8 for s in ranked)
    
    def test_suggest_fixes_for_failure_with_analysis(
        self,
        generator,
        mock_llm_provider,
        sample_failure_analysis
    ):
        """Test high-level fix suggestion method with analysis."""
        # Create a test failure
        env = Environment(
            id="env-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel",
                memory_mb=4096
            ),
            status=EnvironmentStatus.IDLE
        )
        
        failure = TestResult(
            test_id="test-001",
            status=TestStatus.FAILED,
            execution_time=1.5,
            environment=env,
            failure_info=FailureInfo(
                error_message="NULL pointer dereference",
                stack_trace="foo+0x10"
            )
        )
        
        mock_response = LLMResponse(
            content="""FIX_1:
DESCRIPTION: Add NULL check
RATIONALE: Prevents crash
CONFIDENCE: 0.8""",
            model="gpt-4",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        suggestions = generator.suggest_fixes_for_failure(
            failure,
            failure_analysis=sample_failure_analysis
        )
        
        assert len(suggestions) >= 1
        assert all(isinstance(s, FixSuggestion) for s in suggestions)
    
    def test_suggest_fixes_for_failure_without_analysis(
        self,
        generator,
        mock_llm_provider
    ):
        """Test high-level fix suggestion method without pre-computed analysis."""
        env = Environment(
            id="env-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel",
                memory_mb=4096
            ),
            status=EnvironmentStatus.IDLE
        )
        
        failure = TestResult(
            test_id="test-001",
            status=TestStatus.FAILED,
            execution_time=1.5,
            environment=env,
            failure_info=FailureInfo(
                error_message="Test failed",
                stack_trace=None
            )
        )
        
        mock_response = LLMResponse(
            content="""FIX_1:
DESCRIPTION: Debug the test
RATIONALE: Need more information
CONFIDENCE: 0.5""",
            model="gpt-4",
            tokens_used=100,
            finish_reason="stop",
            metadata={}
        )
        mock_llm_provider.generate_with_retry.return_value = mock_response
        
        suggestions = generator.suggest_fixes_for_failure(failure)
        
        assert isinstance(suggestions, list)
    
    def test_suggest_fixes_for_failure_no_failure_info(
        self,
        generator
    ):
        """Test fix suggestion for failure without failure info."""
        env = Environment(
            id="env-1",
            config=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel",
                memory_mb=4096
            ),
            status=EnvironmentStatus.IDLE
        )
        
        failure = TestResult(
            test_id="test-001",
            status=TestStatus.FAILED,
            execution_time=1.5,
            environment=env,
            failure_info=None
        )
        
        suggestions = generator.suggest_fixes_for_failure(failure)
        
        # Should return empty list
        assert suggestions == []
