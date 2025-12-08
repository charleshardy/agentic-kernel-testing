"""Fix suggestion generator for test failures using AI-powered code generation.

This module generates fix suggestions and code patches for test failures using
LLM providers (OpenAI, Anthropic, Amazon Q, Kiro, Bedrock).
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ai_generator.llm_providers import BaseLLMProvider
from ai_generator.llm_providers_extended import (
    ExtendedLLMProviderFactory, ExtendedLLMProvider
)
from ai_generator.models import (
    TestResult, FailureAnalysis, FixSuggestion, Commit
)


@dataclass
class CodeContext:
    """Context information for generating fix suggestions."""
    file_path: str
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    surrounding_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


class CodePatchGenerator:
    """Generates code patches for fixing failures."""
    
    @staticmethod
    def format_patch(
        file_path: str,
        original_code: str,
        fixed_code: str,
        line_number: Optional[int] = None
    ) -> str:
        """Format a code patch in unified diff format.
        
        Args:
            file_path: Path to the file being patched
            original_code: Original code snippet
            fixed_code: Fixed code snippet
            line_number: Starting line number (optional)
            
        Returns:
            Formatted patch string
        """
        lines = []
        lines.append(f"--- a/{file_path}")
        lines.append(f"+++ b/{file_path}")
        
        if line_number:
            lines.append(f"@@ -{line_number},1 +{line_number},1 @@")
        else:
            lines.append("@@ -1,1 +1,1 @@")
        
        # Add original lines with '-' prefix
        for line in original_code.split('\n'):
            lines.append(f"-{line}")
        
        # Add fixed lines with '+' prefix
        for line in fixed_code.split('\n'):
            lines.append(f"+{line}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def extract_code_from_response(response: str) -> Optional[str]:
        """Extract code from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Extracted code or None
        """
        # Try to extract code from markdown code blocks
        code_block_pattern = r'```(?:c|cpp|python|java|rust)?\n(.*?)```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Try to extract code from CODE: markers
        code_match = re.search(r'CODE:\s*\n(.*?)(?:\n\n|$)', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        return None


class FixSuggestionGenerator:
    """AI-powered fix suggestion generator.
    
    Generates fix suggestions and code patches for test failures using
    multiple LLM providers:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Amazon Bedrock (Claude via Bedrock)
    - Amazon Q Developer Pro (AWS's AI coding assistant)
    - Kiro AI (AI-powered IDE)
    """
    
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_suggestions: int = 3,
        **provider_kwargs
    ):
        """Initialize fix suggestion generator.
        
        Args:
            llm_provider: Pre-configured LLM provider (optional)
            provider_type: Type of LLM provider ("openai", "anthropic", "bedrock", "amazon_q", "kiro")
            api_key: API key for LLM provider
            model: Model name to use
            max_suggestions: Maximum number of suggestions to generate
            **provider_kwargs: Additional provider-specific parameters:
                - For Amazon Q: region, profile, use_sso, sso_start_url, sso_region
                - For Kiro: api_url, use_sso, client_id, client_secret
                - For Bedrock: region
        
        Examples:
            # Using Amazon Q Developer Pro
            generator = FixSuggestionGenerator(
                provider_type="amazon_q",
                region="us-east-1",
                use_sso=True,
                sso_start_url="https://my-sso.awsapps.com/start"
            )
            
            # Using Kiro AI
            generator = FixSuggestionGenerator(
                provider_type="kiro",
                api_key="your-kiro-key"
            )
            
            # Using OpenAI (default)
            generator = FixSuggestionGenerator(
                provider_type="openai",
                api_key="your-openai-key",
                model="gpt-4"
            )
        """
        if llm_provider:
            self.llm_provider = llm_provider
        elif provider_type:
            try:
                self.llm_provider = ExtendedLLMProviderFactory.create(
                    provider=ExtendedLLMProvider(provider_type),
                    api_key=api_key,
                    model=model,
                    **provider_kwargs
                )
            except (ImportError, Exception) as e:
                raise RuntimeError(
                    f"Failed to initialize LLM provider '{provider_type}': {e}"
                )
        else:
            raise ValueError(
                "Either llm_provider or provider_type must be specified"
            )
        
        self.max_suggestions = max_suggestions
        self.patch_generator = CodePatchGenerator()
    
    def generate_fix_suggestions(
        self,
        failure_analysis: FailureAnalysis,
        code_context: Optional[CodeContext] = None,
        commits: Optional[List[Commit]] = None
    ) -> List[FixSuggestion]:
        """Generate fix suggestions for a failure.
        
        Args:
            failure_analysis: FailureAnalysis from root cause analyzer
            code_context: Optional code context for more targeted suggestions
            commits: Optional list of suspicious commits
            
        Returns:
            List of FixSuggestion objects ranked by confidence
        """
        # Build prompt for LLM
        prompt = self._build_fix_prompt(failure_analysis, code_context, commits)
        
        try:
            # Call LLM with retry logic
            response = self.llm_provider.generate_with_retry(
                prompt,
                temperature=0.3,  # Lower temperature for more focused suggestions
                max_tokens=2000
            )
            
            # Parse response into fix suggestions
            suggestions = self._parse_fix_response(response.content, code_context)
            
            # Rank suggestions by confidence
            ranked_suggestions = self._rank_suggestions(suggestions, failure_analysis)
            
            return ranked_suggestions[:self.max_suggestions]
            
        except Exception as e:
            # Return empty list if generation fails
            print(f"Warning: Fix suggestion generation failed: {e}")
            return []
    
    def generate_code_patch(
        self,
        fix_suggestion: FixSuggestion,
        code_context: CodeContext
    ) -> Optional[str]:
        """Generate a code patch for a fix suggestion.
        
        Args:
            fix_suggestion: FixSuggestion to generate patch for
            code_context: Code context with original code
            
        Returns:
            Formatted patch string or None if generation fails
        """
        if not code_context.surrounding_code:
            return None
        
        # Build prompt for patch generation
        prompt = self._build_patch_prompt(fix_suggestion, code_context)
        
        try:
            # Call LLM to generate fixed code
            response = self.llm_provider.generate_with_retry(
                prompt,
                temperature=0.2,  # Very low temperature for precise code generation
                max_tokens=1500
            )
            
            # Extract code from response
            fixed_code = self.patch_generator.extract_code_from_response(response.content)
            
            if not fixed_code:
                return None
            
            # Format as patch
            patch = self.patch_generator.format_patch(
                file_path=code_context.file_path,
                original_code=code_context.surrounding_code,
                fixed_code=fixed_code,
                line_number=code_context.line_number
            )
            
            return patch
            
        except Exception as e:
            print(f"Warning: Patch generation failed: {e}")
            return None
    
    def _build_fix_prompt(
        self,
        failure_analysis: FailureAnalysis,
        code_context: Optional[CodeContext],
        commits: Optional[List[Commit]]
    ) -> str:
        """Build prompt for fix suggestion generation.
        
        Args:
            failure_analysis: FailureAnalysis object
            code_context: Optional code context
            commits: Optional suspicious commits
            
        Returns:
            Prompt string
        """
        prompt_parts = [
            "You are an expert kernel developer. Analyze this test failure and suggest fixes.",
            "",
            f"Root Cause: {failure_analysis.root_cause}",
            f"Error Pattern: {failure_analysis.error_pattern}",
            f"Confidence: {failure_analysis.confidence:.2f}",
        ]
        
        if failure_analysis.stack_trace:
            prompt_parts.extend([
                "",
                "Stack Trace:",
                failure_analysis.stack_trace[:500]  # Limit length
            ])
        
        if code_context:
            prompt_parts.extend([
                "",
                f"File: {code_context.file_path}",
            ])
            if code_context.function_name:
                prompt_parts.append(f"Function: {code_context.function_name}")
            if code_context.line_number:
                prompt_parts.append(f"Line: {code_context.line_number}")
            if code_context.surrounding_code:
                prompt_parts.extend([
                    "",
                    "Code Context:",
                    "```",
                    code_context.surrounding_code[:300],  # Limit length
                    "```"
                ])
        
        if commits:
            prompt_parts.extend([
                "",
                "Suspicious Commits:",
            ])
            for commit in commits[:3]:  # Show top 3
                prompt_parts.append(f"- {commit.sha[:8]}: {commit.message[:80]}")
        
        prompt_parts.extend([
            "",
            f"Please provide {self.max_suggestions} fix suggestions.",
            "For each suggestion, provide:",
            "1. A clear description of the fix",
            "2. The rationale for why this fix addresses the root cause",
            "3. A confidence score (0.0-1.0)",
            "",
            "Format your response as:",
            "FIX_1:",
            "DESCRIPTION: <description>",
            "RATIONALE: <rationale>",
            "CONFIDENCE: <0.0-1.0>",
            "",
            "FIX_2:",
            "...",
        ])
        
        return '\n'.join(prompt_parts)
    
    def _build_patch_prompt(
        self,
        fix_suggestion: FixSuggestion,
        code_context: CodeContext
    ) -> str:
        """Build prompt for code patch generation.
        
        Args:
            fix_suggestion: FixSuggestion to generate patch for
            code_context: Code context
            
        Returns:
            Prompt string
        """
        prompt_parts = [
            "Generate fixed code based on this suggestion.",
            "",
            f"Fix Description: {fix_suggestion.description}",
            f"Rationale: {fix_suggestion.rationale}",
            "",
            f"File: {code_context.file_path}",
        ]
        
        if code_context.function_name:
            prompt_parts.append(f"Function: {code_context.function_name}")
        
        if code_context.error_message:
            prompt_parts.extend([
                "",
                f"Error: {code_context.error_message}"
            ])
        
        prompt_parts.extend([
            "",
            "Original Code:",
            "```",
            code_context.surrounding_code or "",
            "```",
            "",
            "Provide the fixed code that implements the suggested fix.",
            "Return ONLY the fixed code in a code block, no explanations.",
        ])
        
        return '\n'.join(prompt_parts)
    
    def _parse_fix_response(
        self,
        response: str,
        code_context: Optional[CodeContext]
    ) -> List[FixSuggestion]:
        """Parse LLM response into fix suggestions.
        
        Args:
            response: LLM response text
            code_context: Optional code context
            
        Returns:
            List of FixSuggestion objects
        """
        suggestions = []
        
        # Split response into individual fixes
        fix_pattern = r'FIX_(\d+):(.*?)(?=FIX_\d+:|$)'
        matches = re.findall(fix_pattern, response, re.DOTALL | re.IGNORECASE)
        
        for fix_num, fix_content in matches:
            # Extract description
            desc_match = re.search(
                r'DESCRIPTION:\s*(.+?)(?=RATIONALE:|CONFIDENCE:|$)',
                fix_content,
                re.DOTALL | re.IGNORECASE
            )
            description = desc_match.group(1).strip() if desc_match else "No description"
            
            # Extract rationale
            rat_match = re.search(
                r'RATIONALE:\s*(.+?)(?=CONFIDENCE:|$)',
                fix_content,
                re.DOTALL | re.IGNORECASE
            )
            rationale = rat_match.group(1).strip() if rat_match else "No rationale"
            
            # Extract confidence
            conf_match = re.search(
                r'CONFIDENCE:\s*(0?\.\d+|1\.0)',
                fix_content,
                re.IGNORECASE
            )
            confidence = float(conf_match.group(1)) if conf_match else 0.5
            
            # Create fix suggestion
            suggestion = FixSuggestion(
                description=description[:200],  # Limit length
                confidence=confidence,
                rationale=rationale[:300]  # Limit length
            )
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def _rank_suggestions(
        self,
        suggestions: List[FixSuggestion],
        failure_analysis: FailureAnalysis
    ) -> List[FixSuggestion]:
        """Rank fix suggestions by confidence and relevance.
        
        Args:
            suggestions: List of FixSuggestion objects
            failure_analysis: FailureAnalysis object
            
        Returns:
            Sorted list of FixSuggestion objects
        """
        # Adjust confidence based on failure analysis confidence
        for suggestion in suggestions:
            # Scale suggestion confidence by failure analysis confidence
            suggestion.confidence *= failure_analysis.confidence
            
            # Boost confidence if suggestion mentions error pattern
            if failure_analysis.error_pattern in suggestion.description.lower():
                suggestion.confidence = min(1.0, suggestion.confidence * 1.1)
            
            # Boost confidence if rationale is detailed
            if len(suggestion.rationale) > 50:
                suggestion.confidence = min(1.0, suggestion.confidence * 1.05)
        
        # Sort by confidence (highest first)
        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)
    
    def suggest_fixes_for_failure(
        self,
        failure: TestResult,
        failure_analysis: Optional[FailureAnalysis] = None,
        code_context: Optional[CodeContext] = None,
        commits: Optional[List[Commit]] = None,
        generate_patches: bool = False
    ) -> List[FixSuggestion]:
        """High-level method to suggest fixes for a test failure.
        
        This is a convenience method that combines failure analysis
        and fix suggestion generation.
        
        Args:
            failure: TestResult with failure information
            failure_analysis: Optional pre-computed FailureAnalysis
            code_context: Optional code context
            commits: Optional suspicious commits
            generate_patches: Whether to generate code patches
            
        Returns:
            List of FixSuggestion objects with optional patches
        """
        # If no failure analysis provided, create a minimal one
        if not failure_analysis:
            if not failure.failure_info:
                return []
            
            failure_analysis = FailureAnalysis(
                failure_id=failure.test_id,
                root_cause=failure.failure_info.error_message,
                confidence=0.5,
                error_pattern="unknown",
                stack_trace=failure.failure_info.stack_trace
            )
        
        # Generate fix suggestions
        suggestions = self.generate_fix_suggestions(
            failure_analysis,
            code_context,
            commits
        )
        
        # Generate patches if requested and code context available
        if generate_patches and code_context and code_context.surrounding_code:
            for suggestion in suggestions:
                patch = self.generate_code_patch(suggestion, code_context)
                if patch:
                    suggestion.code_patch = patch
        
        return suggestions
