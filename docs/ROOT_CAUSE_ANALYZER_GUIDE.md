# Root Cause Analyzer Guide

The Root Cause Analyzer is an AI-powered component that analyzes test failures, identifies root causes, correlates failures with code changes, and suggests fixes.

## Features

- **Stack Trace Parsing**: Parses kernel stack traces into structured data
- **Error Pattern Recognition**: Identifies common kernel error patterns (NULL pointer, use-after-free, buffer overflow, etc.)
- **Failure Signature Generation**: Groups related failures by signature
- **AI-Powered Analysis**: Uses LLMs to analyze failures and suggest fixes
- **Failure Correlation**: Correlates failures with recent code changes
- **Multiple LLM Provider Support**: OpenAI, Anthropic, Amazon Bedrock, Amazon Q Developer Pro, Kiro AI

## Supported LLM Providers

### 1. OpenAI (GPT-4, GPT-3.5)

```python
from analysis.root_cause_analyzer import RootCauseAnalyzer

analyzer = RootCauseAnalyzer(
    provider_type="openai",
    api_key="your-openai-api-key",  # or set OPENAI_API_KEY env var
    model="gpt-4"
)
```

### 2. Anthropic (Claude)

```python
analyzer = RootCauseAnalyzer(
    provider_type="anthropic",
    api_key="your-anthropic-api-key",  # or set ANTHROPIC_API_KEY env var
    model="claude-3-5-sonnet-20241022"
)
```

### 3. Amazon Bedrock

```python
analyzer = RootCauseAnalyzer(
    provider_type="bedrock",
    api_key="your-aws-access-key",  # or set AWS_ACCESS_KEY_ID env var
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1"
)
```

### 4. Amazon Q Developer Pro

Amazon Q Developer is AWS's AI-powered coding assistant that can analyze kernel failures and suggest fixes.

#### Option A: Using AWS API Keys

```python
analyzer = RootCauseAnalyzer(
    provider_type="amazon_q",
    api_key="your-aws-access-key",  # or set AWS_ACCESS_KEY_ID env var
    region="us-east-1"
)
```

#### Option B: Using AWS SSO (IAM Identity Center)

```python
analyzer = RootCauseAnalyzer(
    provider_type="amazon_q",
    region="us-east-1",
    use_sso=True,
    sso_start_url="https://my-company.awsapps.com/start",
    sso_region="us-east-1",
    profile="my-sso-profile"
)
```

#### Option C: Using AWS CLI Profile

```python
analyzer = RootCauseAnalyzer(
    provider_type="amazon_q",
    region="us-east-1",
    profile="my-aws-profile"  # Uses credentials from ~/.aws/credentials
)
```

**Setting up AWS SSO:**

1. Configure AWS SSO in your organization
2. Install AWS CLI v2: `pip install awscli`
3. Configure SSO: `aws configure sso`
4. Use the profile name in the analyzer

### 5. Kiro AI

Kiro is an AI-powered IDE that can analyze code and suggest improvements.

#### Option A: Using API Key

```python
analyzer = RootCauseAnalyzer(
    provider_type="kiro",
    api_key="your-kiro-api-key",  # or set KIRO_API_KEY env var
    api_url="https://api.kiro.ai/v1"
)
```

#### Option B: Using OAuth2 SSO

```python
analyzer = RootCauseAnalyzer(
    provider_type="kiro",
    use_sso=True,
    client_id="your-oauth-client-id",
    client_secret="your-oauth-client-secret"
)
```

### 6. Pattern-Based Analysis (No LLM)

If no LLM provider is configured, the analyzer falls back to pattern-based analysis:

```python
analyzer = RootCauseAnalyzer()  # No LLM provider
```

## Usage Examples

### Basic Failure Analysis

```python
from analysis.root_cause_analyzer import RootCauseAnalyzer
from ai_generator.models import TestResult, FailureInfo

# Create analyzer
analyzer = RootCauseAnalyzer(
    provider_type="amazon_q",
    region="us-east-1"
)

# Analyze a failure
analysis = analyzer.analyze_failure(test_failure)

print(f"Root Cause: {analysis.root_cause}")
print(f"Confidence: {analysis.confidence}")
print(f"Error Pattern: {analysis.error_pattern}")

for fix in analysis.suggested_fixes:
    print(f"Suggested Fix: {fix.description}")
    print(f"  Confidence: {fix.confidence}")
```

### Grouping Related Failures

```python
# Group multiple failures by signature
groups = analyzer.group_failures(list_of_failures)

for signature, failures in groups.items():
    print(f"Group {signature}: {len(failures)} failures")
    # Analyze one failure from the group
    analysis = analyzer.analyze_failure(failures[0])
    print(f"  Root Cause: {analysis.root_cause}")
```

### Correlating Failures with Code Changes

```python
from ai_generator.models import Commit

# Get recent commits
commits = [...]  # List of Commit objects

# Correlate failure with commits
suspicious_commits = analyzer.correlate_with_changes(test_failure, commits)

for commit in suspicious_commits:
    print(f"Suspicious commit: {commit.sha}")
    print(f"  Message: {commit.message}")
    print(f"  Files changed: {commit.files_changed}")
```

## Error Patterns Recognized

The analyzer recognizes the following common kernel error patterns:

- **NULL Pointer Dereference**: `NULL pointer dereference at address 0x...`
- **Use-After-Free**: `use-after-free in function ...`
- **Buffer Overflow**: `buffer overflow in ...`
- **Deadlock**: `deadlock detected in ...`
- **Race Condition**: `race condition in ...`
- **Memory Leak**: `memory leak in ...`
- **Assertion Failure**: `BUG_ON`, `WARN_ON`, `assertion failed`
- **Timeout**: `timeout`, `hung task`, `soft lockup`

## Stack Trace Parsing

The analyzer parses kernel stack traces in the following formats:

```
Call Trace:
 [<ffffffffa0123456>] function_name+0x42/0x100 [module_name]
 [<ffffffff81234567>] caller_function+0x10/0x20
```

Or:

```
file.c:123 function_name
caller.c:456 caller_function
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `KIRO_API_KEY`: Kiro API key
- `KIRO_API_URL`: Kiro API endpoint (default: https://api.kiro.ai/v1)

### AWS Configuration

For Amazon Q Developer Pro, you can use:

1. **Environment variables**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
2. **AWS CLI profile**: Configure with `aws configure` or `aws configure sso`
3. **IAM roles**: When running on EC2 or ECS

### Kiro Configuration

For Kiro AI, you can use:

1. **API key**: Set `KIRO_API_KEY` environment variable
2. **OAuth2 SSO**: Configure client ID and secret

## Best Practices

1. **Use LLM providers for complex failures**: LLMs provide better analysis for complex, multi-layered failures
2. **Use pattern-based analysis for simple failures**: Faster and doesn't require API calls
3. **Group related failures**: Reduces analysis time and identifies common root causes
4. **Correlate with code changes**: Helps identify regression-causing commits
5. **Review suggested fixes**: AI suggestions should be reviewed before applying

## Troubleshooting

### LLM Provider Initialization Fails

If the LLM provider fails to initialize, the analyzer automatically falls back to pattern-based analysis. Check:

- API keys are set correctly
- Network connectivity to the provider
- Provider-specific dependencies are installed (e.g., `boto3` for AWS)

### AWS SSO Issues

If AWS SSO authentication fails:

1. Ensure AWS CLI v2 is installed
2. Run `aws sso login --profile your-profile`
3. Check SSO configuration in `~/.aws/config`

### Kiro API Issues

If Kiro API calls fail:

1. Verify API key is valid
2. Check API endpoint URL
3. Ensure network connectivity

## API Reference

### RootCauseAnalyzer

```python
class RootCauseAnalyzer:
    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        provider_type: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **provider_kwargs
    )
    
    def analyze_failure(self, failure: TestResult) -> FailureAnalysis
    
    def correlate_with_changes(
        self, 
        failure: TestResult, 
        commits: List[Commit]
    ) -> List[Commit]
    
    def group_failures(
        self, 
        failures: List[TestResult]
    ) -> Dict[str, List[TestResult]]
```

### FailureAnalysis

```python
@dataclass
class FailureAnalysis:
    failure_id: str
    root_cause: str
    confidence: float  # 0.0 to 1.0
    suspicious_commits: List[Commit]
    error_pattern: str
    stack_trace: Optional[str]
    suggested_fixes: List[FixSuggestion]
    related_failures: List[str]
    reproducibility: float  # 0.0 to 1.0
```

## Examples

See `examples/root_cause_analysis_examples.py` for complete working examples.
