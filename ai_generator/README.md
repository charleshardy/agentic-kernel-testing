# AI Test Generator

This module implements the AI-powered test generation core for the Agentic AI Testing System.

## Components

### 1. LLM Provider Abstraction (`llm_providers.py`)

A unified interface for multiple LLM providers:

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus
- **Amazon Bedrock**: Claude via Bedrock, Amazon Titan

Features:
- Unified `BaseLLMProvider` interface
- Automatic retry with exponential backoff
- Provider-specific configuration
- Credential management via environment variables

Example usage:
```python
from ai_generator.llm_providers import LLMProviderFactory, LLMProvider

# Create OpenAI provider
provider = LLMProviderFactory.create(
    provider=LLMProvider.OPENAI,
    api_key="your-api-key",
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000
)

# Generate completion
response = provider.generate_with_retry("Your prompt here")
print(response.content)
```

### 2. AI Test Generator (`test_generator.py`)

Implements the `ITestGenerator` interface with AI-powered test generation:

**Key Features:**
- Analyzes code changes using LLM and AST analysis
- Generates comprehensive test cases (minimum 10 per function)
- Supports multiple test types: unit, integration, property-based
- Validates generated tests for correctness
- Fallback to template-based generation when LLM fails

**Main Methods:**

```python
from ai_generator.test_generator import AITestGenerator

generator = AITestGenerator()

# Analyze code changes
analysis = generator.analyze_code_changes(diff_string)

# Generate test cases
test_cases = generator.generate_test_cases(analysis)

# Generate property-based tests
property_tests = generator.generate_property_tests(functions)
```

### 3. Test Case Templates

Built-in templates for different test types:
- Unit test template
- API/system call test template
- Property-based test template

### 4. Test Case Validator

Validates generated test cases:
- Required fields present
- Valid test types
- Reasonable execution time estimates
- Syntax validation for test scripts

## Property-Based Tests

The implementation includes comprehensive property-based tests:

### Test Generation Quantity (Property 4)
- Validates that at least 10 tests are generated per function
- Tests scale linearly with number of functions
- All tests are valid and distinct

### API Test Coverage (Property 3)
- Ensures comprehensive coverage for APIs/system calls
- Tests normal usage, boundary conditions, and error paths
- Validates error path diversity

### Test Generation Time Bound (Property 1)
- Verifies generation completes within time limits
- Tests time scaling with complexity
- Ensures no hangs or timeouts

## Configuration

Configure via environment variables or settings:

```python
from config import get_settings

settings = get_settings()
settings.llm.provider = "openai"  # or "anthropic", "bedrock"
settings.llm.api_key = "your-key"
settings.llm.model = "gpt-4"
settings.llm.temperature = 0.7
settings.llm.max_tokens = 2000
settings.llm.max_retries = 3
```

Or via `.env` file:
```
LLM__PROVIDER=openai
LLM__API_KEY=your-key
LLM__MODEL=gpt-4
LLM__TEMPERATURE=0.7
LLM__MAX_TOKENS=2000
```

## Requirements Validation

This implementation satisfies:

- **Requirement 1.1**: Test generation completes within 5 minutes
- **Requirement 1.3**: API tests cover normal usage, boundary conditions, and error paths
- **Requirement 1.4**: At least 10 distinct test cases per modified function

## Testing

Run the property-based tests:
```bash
pytest tests/property/test_test_generation_quantity.py -v
pytest tests/property/test_api_test_coverage.py -v
pytest tests/property/test_test_generation_time_bound.py -v
```

Run all tests:
```bash
pytest tests/property/ -v
pytest tests/unit/ -v
```

## Future Enhancements

- Support for additional LLM providers (Google PaLM, Cohere)
- Enhanced code analysis with deeper AST inspection
- Integration with existing test frameworks
- Test case optimization and deduplication
- Adaptive test generation based on code complexity
