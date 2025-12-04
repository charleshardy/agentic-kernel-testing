# Quick Start: Using Amazon Q Developer & Kiro with AI Test Generator

## TL;DR

```python
# Amazon Q Developer
from ai_generator.llm_providers_extended import create_provider
from ai_generator.test_generator import AITestGenerator

provider = create_provider("amazon_q", region="us-east-1")
generator = AITestGenerator(llm_provider=provider)
test_cases = generator.generate_test_cases(analysis)

# Kiro AI
provider = create_provider("kiro", api_key="your-key")
generator = AITestGenerator(llm_provider=provider)
test_cases = generator.generate_test_cases(analysis)
```

## Amazon Q Developer - 3 Steps

### 1. Install & Configure
```bash
pip install boto3
aws configure  # Enter your AWS credentials
```

### 2. Set Environment
```bash
export AWS_REGION="us-east-1"
```

### 3. Use in Code
```python
from ai_generator.llm_providers_extended import create_provider
from ai_generator.test_generator import AITestGenerator

provider = create_provider("amazon_q")
generator = AITestGenerator(llm_provider=provider)

# Your code diff
diff = """
diff --git a/src/main.c b/src/main.c
...
"""

analysis = generator.analyze_code_changes(diff)
tests = generator.generate_test_cases(analysis)
print(f"Generated {len(tests)} tests!")
```

## Kiro AI - 3 Steps

### 1. Get API Key
Visit https://kiro.ai and get your API key

### 2. Set Environment
```bash
export KIRO_API_KEY="your-api-key-here"
```

### 3. Use in Code
```python
from ai_generator.llm_providers_extended import create_provider
from ai_generator.test_generator import AITestGenerator

provider = create_provider("kiro")
generator = AITestGenerator(llm_provider=provider)

# Generate tests
tests = generator.generate_test_cases(analysis)
print(f"Generated {len(tests)} tests!")
```

## Configuration via .env File

Create a `.env` file in your project root:

```env
# For Amazon Q Developer
LLM__PROVIDER=amazon_q
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1

# OR for Kiro AI
LLM__PROVIDER=kiro
KIRO_API_KEY=your-kiro-key
```

Then just use:
```python
generator = AITestGenerator()  # Automatically uses .env config
```

## Interface Summary

### Task 4 Interface with Amazon Q / Kiro

The interface remains the same as other providers:

```python
# 1. Create Provider
provider = create_provider("amazon_q")  # or "kiro"

# 2. Create Generator
generator = AITestGenerator(llm_provider=provider)

# 3. Analyze Code
analysis = generator.analyze_code_changes(diff_string)

# 4. Generate Tests
test_cases = generator.generate_test_cases(analysis)

# 5. Generate Property Tests
property_tests = generator.generate_property_tests(functions)
```

### All Methods Available

```python
# Code analysis
analysis = generator.analyze_code_changes(diff: str) -> CodeAnalysis

# Test generation
tests = generator.generate_test_cases(analysis: CodeAnalysis) -> List[TestCase]

# Property test generation
prop_tests = generator.generate_property_tests(functions: List[Function]) -> List[TestCase]
```

## Comparison

| Provider | Setup Time | Best For |
|----------|-----------|----------|
| Amazon Q | 5 min | AWS environments, enterprise |
| Kiro | 2 min | IDE integration, fast iteration |
| OpenAI | 2 min | General purpose, proven |
| Anthropic | 2 min | Long context, detailed analysis |

## Common Issues

### Amazon Q: "Credentials not found"
```bash
aws configure
# Enter your AWS credentials when prompted
```

### Kiro: "Invalid API key"
```bash
# Check your API key
echo $KIRO_API_KEY
# Make sure it's set correctly
export KIRO_API_KEY="your-actual-key"
```

## Next Steps

- Read full documentation: `docs/AMAZON_Q_AND_KIRO_INTEGRATION.md`
- See examples: `examples/using_amazon_q_and_kiro.py`
- Run tests: `pytest tests/property/ -v`

## Support

- Amazon Q: https://aws.amazon.com/q/developer/
- Kiro: https://kiro.ai
- Issues: https://github.com/your-repo/issues
