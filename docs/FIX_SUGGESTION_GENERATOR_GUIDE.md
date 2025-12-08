# Fix Suggestion Generator Guide

## Overview

The Fix Suggestion Generator is an AI-powered component that automatically generates fix suggestions and code patches for test failures. It leverages Large Language Models (LLMs) to analyze failures and provide actionable recommendations for developers.

## Features

- **Multi-Provider Support**: Works with OpenAI, Anthropic, Amazon Bedrock, Amazon Q Developer Pro, and Kiro AI
- **Intelligent Fix Generation**: Generates targeted fix suggestions based on root cause analysis
- **Code Patch Generation**: Creates unified diff patches that can be directly applied
- **Confidence Ranking**: Ranks suggestions by confidence score
- **Context-Aware**: Uses code context and git history for better suggestions
- **Integration**: Seamlessly integrates with the Root Cause Analyzer

## Architecture

### Components

1. **FixSuggestionGenerator**: Main class for generating fix suggestions
2. **CodePatchGenerator**: Utility for creating and formatting code patches
3. **CodeContext**: Data structure for providing code context to the generator

### Workflow

```
Test Failure → Root Cause Analysis → Fix Suggestion Generation → Code Patch Generation
```

## Usage

### Basic Usage

```python
from analysis.fix_suggestion_generator import FixSuggestionGenerator
from ai_generator.models import TestResult, FailureAnalysis

# Initialize generator with OpenAI
generator = FixSuggestionGenerator(
    provider_type="openai",
    api_key="your-api-key",
    model="gpt-4"
)

# Generate fix suggestions for a failure
suggestions = generator.suggest_fixes_for_failure(failure)

for suggestion in suggestions:
    print(f"Fix: {suggestion.description}")
    print(f"Confidence: {suggestion.confidence:.2f}")
    print(f"Rationale: {suggestion.rationale}")
```

### With Code Context

```python
from analysis.fix_suggestion_generator import CodeContext

# Provide code context for more targeted suggestions
code_context = CodeContext(
    file_path="drivers/my_driver/main.c",
    function_name="my_function",
    line_number=156,
    surrounding_code="""
static int my_function(const char *input) {
    char buffer[32];
    strcpy(buffer, input);  // Potential overflow
    return process_buffer(buffer);
}
""",
    error_message="Buffer overflow in strcpy"
)

# Generate suggestions with context
suggestions = generator.generate_fix_suggestions(
    failure_analysis,
    code_context=code_context
)
```

### With Git History

```python
from ai_generator.models import Commit
from datetime import datetime

# Provide suspicious commits
commits = [
    Commit(
        sha="abc123def456",
        message="Refactor cleanup logic",
        author="dev@example.com",
        timestamp=datetime.now(),
        files_changed=["drivers/my_driver/main.c"]
    )
]

# Generate suggestions with commit context
suggestions = generator.generate_fix_suggestions(
    failure_analysis,
    commits=commits
)
```

### Generating Code Patches

```python
# Generate a code patch for a suggestion
patch = generator.generate_code_patch(suggestion, code_context)

if patch:
    print("Generated Patch:")
    print(patch)
    
    # Patch can be saved to a file
    with open("fix.patch", "w") as f:
        f.write(patch)
```

## LLM Provider Configuration

### OpenAI

```python
generator = FixSuggestionGenerator(
    provider_type="openai",
    api_key="sk-...",
    model="gpt-4"
)
```

### Anthropic Claude

```python
generator = FixSuggestionGenerator(
    provider_type="anthropic",
    api_key="sk-ant-...",
    model="claude-3-5-sonnet-20241022"
)
```

### Amazon Bedrock

```python
generator = FixSuggestionGenerator(
    provider_type="bedrock",
    api_key="AKIA...",
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1"
)
```

### Amazon Q Developer Pro

```python
# With AWS SSO
generator = FixSuggestionGenerator(
    provider_type="amazon_q",
    region="us-east-1",
    use_sso=True,
    sso_start_url="https://my-sso.awsapps.com/start",
    sso_region="us-east-1"
)

# With AWS credentials
generator = FixSuggestionGenerator(
    provider_type="amazon_q",
    api_key="AKIA...",
    region="us-east-1"
)
```

### Kiro AI

```python
# With API key
generator = FixSuggestionGenerator(
    provider_type="kiro",
    api_key="your-kiro-key"
)

# With OAuth2 SSO
generator = FixSuggestionGenerator(
    provider_type="kiro",
    use_sso=True,
    client_id="your-client-id",
    client_secret="your-client-secret"
)
```

## Integration with Root Cause Analyzer

The Fix Suggestion Generator integrates seamlessly with the Root Cause Analyzer:

```python
from analysis.root_cause_analyzer import RootCauseAnalyzer

# Initialize analyzer
analyzer = RootCauseAnalyzer(
    provider_type="openai",
    api_key="your-api-key"
)

# Analyze failure and generate fix suggestions in one call
analysis = analyzer.analyze_and_suggest_fixes(
    failure,
    commits=recent_commits,
    code_context=code_context
)

# Access fix suggestions
for fix in analysis.suggested_fixes:
    print(f"Fix: {fix.description}")
    print(f"Confidence: {fix.confidence:.2f}")
```

## Configuration Options

### Generator Parameters

- `llm_provider`: Pre-configured LLM provider instance (optional)
- `provider_type`: Type of LLM provider ("openai", "anthropic", "bedrock", "amazon_q", "kiro")
- `api_key`: API key for the provider
- `model`: Model name to use
- `max_suggestions`: Maximum number of suggestions to generate (default: 3)

### Provider-Specific Parameters

**Amazon Q:**
- `region`: AWS region
- `profile`: AWS profile name
- `use_sso`: Use AWS SSO authentication
- `sso_start_url`: AWS SSO start URL
- `sso_region`: AWS SSO region

**Kiro:**
- `api_url`: Kiro API endpoint
- `use_sso`: Use OAuth2 SSO
- `client_id`: OAuth2 client ID
- `client_secret`: OAuth2 client secret

**Bedrock:**
- `region`: AWS region

## Output Format

### FixSuggestion Object

```python
@dataclass
class FixSuggestion:
    description: str          # Clear description of the fix
    code_patch: Optional[str] # Unified diff patch (if generated)
    confidence: float         # Confidence score (0.0-1.0)
    rationale: str           # Explanation of why this fix works
```

### Code Patch Format

Patches are generated in unified diff format:

```diff
--- a/drivers/my_driver/main.c
+++ b/drivers/my_driver/main.c
@@ -156,1 +156,1 @@
-    strcpy(buffer, input);
+    strncpy(buffer, input, sizeof(buffer) - 1);
+    buffer[sizeof(buffer) - 1] = '\0';
```

## Best Practices

### 1. Provide Rich Context

The more context you provide, the better the suggestions:

```python
code_context = CodeContext(
    file_path="path/to/file.c",
    function_name="function_name",
    line_number=42,
    surrounding_code="...",  # Include surrounding code
    error_message="...",      # Include error message
    stack_trace="..."         # Include stack trace
)
```

### 2. Use Appropriate Temperature

- Lower temperature (0.2-0.3) for code patches: More deterministic, precise code
- Medium temperature (0.5-0.7) for fix suggestions: Balance between creativity and accuracy

### 3. Rank by Confidence

Always review suggestions in order of confidence:

```python
suggestions = generator.generate_fix_suggestions(analysis)
# Suggestions are already ranked by confidence
for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. [{suggestion.confidence:.2f}] {suggestion.description}")
```

### 4. Validate Generated Patches

Always review and test generated patches before applying:

```python
patch = generator.generate_code_patch(suggestion, code_context)
if patch:
    # Review the patch
    print(patch)
    
    # Test the patch
    # Apply to a test branch first
    # Run tests to verify the fix
```

### 5. Handle Failures Gracefully

The generator returns empty lists on failure:

```python
suggestions = generator.generate_fix_suggestions(analysis)
if not suggestions:
    print("Could not generate fix suggestions")
    # Fall back to manual analysis
```

## Error Handling

The Fix Suggestion Generator handles errors gracefully:

- **LLM API Failures**: Returns empty list, logs warning
- **Invalid Responses**: Parses what it can, skips malformed suggestions
- **Missing Context**: Works with minimal information, generates generic suggestions

## Performance Considerations

### Token Usage

- Fix suggestions: ~500-1000 tokens per request
- Code patches: ~800-1500 tokens per request
- Use `max_suggestions` to control cost

### Caching

Consider caching suggestions for identical failures:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_suggestions(failure_signature):
    return generator.generate_fix_suggestions(analysis)
```

### Batch Processing

For multiple failures, process in batches:

```python
for failure in failures:
    suggestions = generator.suggest_fixes_for_failure(failure)
    # Process suggestions
    time.sleep(1)  # Rate limiting
```

## Examples

See `examples/fix_suggestion_examples.py` for comprehensive examples including:

1. Basic fix suggestion generation
2. Fix suggestions with code context
3. Fix suggestions with git history
4. Using Amazon Q Developer Pro
5. Using Kiro AI

## Troubleshooting

### No Suggestions Generated

**Cause**: LLM API failure or invalid credentials

**Solution**:
- Check API key is valid
- Verify network connectivity
- Check API rate limits
- Review error messages in logs

### Low Confidence Scores

**Cause**: Insufficient context or ambiguous failure

**Solution**:
- Provide more code context
- Include git commit history
- Ensure root cause analysis has high confidence

### Invalid Patches

**Cause**: LLM generated incorrect code

**Solution**:
- Lower temperature for more conservative generation
- Provide more surrounding code context
- Review and manually adjust patches

## API Reference

### FixSuggestionGenerator

#### `__init__(llm_provider, provider_type, api_key, model, max_suggestions, **kwargs)`

Initialize the fix suggestion generator.

#### `generate_fix_suggestions(failure_analysis, code_context, commits) -> List[FixSuggestion]`

Generate fix suggestions for a failure.

#### `generate_code_patch(fix_suggestion, code_context) -> Optional[str]`

Generate a code patch for a fix suggestion.

#### `suggest_fixes_for_failure(failure, failure_analysis, code_context, commits, generate_patches) -> List[FixSuggestion]`

High-level method to suggest fixes for a test failure.

### CodePatchGenerator

#### `format_patch(file_path, original_code, fixed_code, line_number) -> str`

Format a code patch in unified diff format.

#### `extract_code_from_response(response) -> Optional[str]`

Extract code from LLM response.

### CodeContext

Data class for providing code context:

- `file_path`: Path to the file
- `function_name`: Name of the function
- `line_number`: Line number of the error
- `surrounding_code`: Code surrounding the error
- `error_message`: Error message
- `stack_trace`: Stack trace

## Related Documentation

- [Root Cause Analyzer Guide](ROOT_CAUSE_ANALYZER_GUIDE.md)
- [LLM Provider Configuration](../ai_generator/README.md)
- [SSO Authentication Guide](SSO_AUTHENTICATION_GUIDE.md)

## Support

For issues or questions:
1. Check the examples in `examples/fix_suggestion_examples.py`
2. Review the test suite in `tests/unit/test_fix_suggestion_generator.py`
3. Consult the API reference above
