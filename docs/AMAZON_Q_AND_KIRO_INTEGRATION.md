# Amazon Q Developer and Kiro Integration Guide

This guide explains how to use Amazon Q Developer Pro and Kiro AI as LLM providers for the AI Test Generator.

## Overview

The AI Test Generator supports multiple LLM providers through a unified interface. In addition to OpenAI, Anthropic, and Amazon Bedrock, you can now use:

- **Amazon Q Developer Pro**: AWS's AI-powered coding assistant
- **Kiro AI**: AI-powered IDE with autonomous capabilities

## Amazon Q Developer Pro

### What is Amazon Q Developer?

Amazon Q Developer is AWS's generative AI-powered assistant for software development. It can:
- Generate high-quality test code
- Understand AWS-specific contexts
- Integrate with your AWS environment
- Provide enterprise-grade security

### Setup

#### 1. Prerequisites

```bash
# Install AWS SDK
pip install boto3

# Configure AWS credentials
aws configure
```

#### 2. Environment Variables

```bash
# Option 1: Use AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# Option 2: Use AWS profile
export AWS_PROFILE="my-profile"
```

#### 3. Configuration in .env

```env
LLM__PROVIDER=amazon_q
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

### Usage

#### Basic Usage

```python
from ai_generator.test_generator import AITestGenerator
from ai_generator.llm_providers_extended import (
    ExtendedLLMProviderFactory,
    ExtendedLLMProvider
)

# Create Amazon Q provider
provider = ExtendedLLMProviderFactory.create(
    provider=ExtendedLLMProvider.AMAZON_Q,
    region="us-east-1"
)

# Create test generator
generator = AITestGenerator(llm_provider=provider)

# Generate tests
diff = "..." # Your git diff
analysis = generator.analyze_code_changes(diff)
test_cases = generator.generate_test_cases(analysis)
```

#### Using AWS Profile

```python
# Use specific AWS profile
provider = ExtendedLLMProviderFactory.create(
    provider=ExtendedLLMProvider.AMAZON_Q,
    profile="my-dev-profile",
    region="us-west-2"
)
```

#### Advanced Configuration

```python
provider = ExtendedLLMProviderFactory.create(
    provider=ExtendedLLMProvider.AMAZON_Q,
    region="us-east-1",
    temperature=0.7,
    max_tokens=2000,
    timeout=60,
    max_retries=3
)
```

### Benefits of Amazon Q Developer

1. **AWS Integration**: Seamlessly works with AWS services
2. **Enterprise Security**: Built-in security and compliance
3. **Context Awareness**: Understands AWS-specific patterns
4. **Cost Effective**: Pay-as-you-go pricing
5. **Multi-Region**: Available in multiple AWS regions

### Best Practices

1. **Use IAM Roles**: For production, use IAM roles instead of access keys
2. **Region Selection**: Choose region closest to your infrastructure
3. **Profile Management**: Use AWS profiles for different environments
4. **Error Handling**: Implement proper error handling for AWS API calls

## Kiro AI

### What is Kiro?

Kiro is an AI-powered IDE that can:
- Generate test code autonomously
- Understand complex codebases
- Execute tasks with minimal guidance
- Integrate with development workflows

### Setup

#### 1. Prerequisites

```bash
# Install requests library (usually already installed)
pip install requests
```

#### 2. Get API Key

1. Sign up at [Kiro AI](https://kiro.ai)
2. Navigate to API settings
3. Generate an API key

#### 3. Environment Variables

```bash
export KIRO_API_KEY="your-kiro-api-key"
export KIRO_API_URL="https://api.kiro.ai/v1"  # Optional, uses default if not set
```

#### 4. Configuration in .env

```env
LLM__PROVIDER=kiro
KIRO_API_KEY=your-api-key
KIRO_API_URL=https://api.kiro.ai/v1
```

### Usage

#### Basic Usage

```python
from ai_generator.test_generator import AITestGenerator
from ai_generator.llm_providers_extended import create_provider

# Create Kiro provider
provider = create_provider(
    "kiro",
    api_key="your-kiro-api-key"
)

# Create test generator
generator = AITestGenerator(llm_provider=provider)

# Generate tests
test_cases = generator.generate_test_cases(analysis)
```

#### Custom Model

```python
provider = create_provider(
    "kiro",
    api_key="your-key",
    model="kiro-advanced"  # Use specific Kiro model
)
```

#### Advanced Configuration

```python
from ai_generator.llm_providers_extended import KiroProvider

provider = KiroProvider(
    api_key="your-key",
    api_url="https://api.kiro.ai/v1",
    model="kiro-default",
    temperature=0.7,
    max_tokens=2000,
    timeout=60
)
```

### Benefits of Kiro

1. **IDE Integration**: Native integration with development environment
2. **Autonomous Execution**: Can execute tasks independently
3. **Context Understanding**: Deep understanding of codebases
4. **Fast Iteration**: Quick test generation and refinement
5. **Developer-Friendly**: Designed specifically for developers

### Best Practices

1. **API Key Security**: Store API keys securely, never commit to git
2. **Rate Limiting**: Be aware of API rate limits
3. **Error Handling**: Handle network errors gracefully
4. **Caching**: Cache responses when appropriate

## Comparison Matrix

| Feature | Amazon Q Developer | Kiro AI | OpenAI | Anthropic |
|---------|-------------------|---------|--------|-----------|
| AWS Integration | ✅ Native | ❌ | ❌ | ❌ |
| IDE Integration | ⚠️ Limited | ✅ Native | ❌ | ❌ |
| Code Generation | ✅ Excellent | ✅ Excellent | ✅ Excellent | ✅ Excellent |
| Test Generation | ✅ Specialized | ✅ Specialized | ✅ Good | ✅ Good |
| Enterprise Support | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Pricing | Pay-per-use | Subscription | Pay-per-token | Pay-per-token |
| Setup Complexity | Medium | Low | Low | Low |

## Configuration Examples

### Using Settings File

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = "amazon_q"  # or "kiro"
    
    # Amazon Q settings
    aws_region: str = "us-east-1"
    aws_profile: str = None
    
    # Kiro settings
    kiro_api_key: str = None
    kiro_api_url: str = "https://api.kiro.ai/v1"
    
    class Config:
        env_file = ".env"
```

### Environment-Specific Configuration

```bash
# Development
LLM__PROVIDER=kiro
KIRO_API_KEY=dev-key

# Staging
LLM__PROVIDER=amazon_q
AWS_PROFILE=staging-profile

# Production
LLM__PROVIDER=amazon_q
AWS_PROFILE=production-profile
```

## Testing

### Unit Tests with Mock Providers

```python
from ai_generator.llm_providers_extended import BaseLLMProvider, LLMResponse

class MockAmazonQProvider(BaseLLMProvider):
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(
            content='{"test": "data"}',
            model="mock-amazon-q",
            tokens_used=100,
            finish_reason="stop",
            metadata={"provider": "amazon_q"}
        )

# Use in tests
generator = AITestGenerator(llm_provider=MockAmazonQProvider())
```

## Troubleshooting

### Amazon Q Developer

**Issue**: "Unable to locate credentials"
```bash
# Solution: Configure AWS credentials
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

**Issue**: "Access denied to Amazon Q"
```bash
# Solution: Ensure IAM permissions include Q access
# Required permissions: q:InvokeModel, q:GetModel
```

### Kiro AI

**Issue**: "Invalid API key"
```bash
# Solution: Verify API key is correct
echo $KIRO_API_KEY
# Regenerate key if needed from Kiro dashboard
```

**Issue**: "Connection timeout"
```python
# Solution: Increase timeout
provider = create_provider(
    "kiro",
    api_key="your-key",
    timeout=120  # Increase to 120 seconds
)
```

## Migration Guide

### From OpenAI to Amazon Q

```python
# Before
from ai_generator.llm_providers import LLMProviderFactory, LLMProvider

provider = LLMProviderFactory.create(
    provider=LLMProvider.OPENAI,
    api_key="openai-key"
)

# After
from ai_generator.llm_providers_extended import ExtendedLLMProviderFactory, ExtendedLLMProvider

provider = ExtendedLLMProviderFactory.create(
    provider=ExtendedLLMProvider.AMAZON_Q,
    region="us-east-1"
)
```

### From Anthropic to Kiro

```python
# Before
provider = LLMProviderFactory.create(
    provider=LLMProvider.ANTHROPIC,
    api_key="anthropic-key"
)

# After
provider = ExtendedLLMProviderFactory.create(
    provider=ExtendedLLMProvider.KIRO,
    api_key="kiro-key"
)
```

## API Reference

### AmazonQDeveloperProvider

```python
class AmazonQDeveloperProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        region: str = "us-east-1",
        profile: Optional[str] = None,
        **kwargs
    )
```

**Parameters:**
- `api_key`: AWS access key (optional if using profile)
- `region`: AWS region for Q Developer
- `profile`: AWS profile name
- `**kwargs`: Additional BaseLLMProvider parameters

### KiroProvider

```python
class KiroProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: str = "kiro-default",
        **kwargs
    )
```

**Parameters:**
- `api_key`: Kiro API key (required)
- `api_url`: Kiro API endpoint
- `model`: Kiro model to use
- `**kwargs`: Additional BaseLLMProvider parameters

## Support

For issues or questions:
- Amazon Q Developer: [AWS Support](https://aws.amazon.com/support/)
- Kiro AI: [Kiro Support](https://kiro.ai/support)
- This Project: [GitHub Issues](https://github.com/your-repo/issues)

## License

This integration follows the same license as the main project.
