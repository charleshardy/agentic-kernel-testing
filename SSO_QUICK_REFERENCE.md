# SSO Authentication - Quick Reference

## Amazon Q Developer

### Option 1: AWS CLI Profile (Easiest)
```bash
# Setup (one-time)
aws configure sso
aws sso login --profile my-sso-profile

# Use in code
from ai_generator.llm_providers_extended import AmazonQDeveloperProvider
provider = AmazonQDeveloperProvider(profile="my-sso-profile")
```

### Option 2: Device Code Flow
```python
provider = AmazonQDeveloperProvider(
    use_sso=True,
    sso_start_url="https://my-company.awsapps.com/start",
    sso_region="us-east-1"
)
# Browser opens automatically for authentication
```

## Kiro AI

### OAuth2 SSO
```bash
# Setup
export KIRO_CLIENT_ID="your-client-id"
export KIRO_CLIENT_SECRET="your-client-secret"
```

```python
from ai_generator.llm_providers_extended import KiroProvider
provider = KiroProvider(use_sso=True)
# Browser opens automatically for authentication
```

## Environment Variables

### Amazon Q
```bash
export AWS_SSO_START_URL="https://my-company.awsapps.com/start"
export AWS_SSO_REGION="us-east-1"
export AWS_PROFILE="my-sso-profile"
```

### Kiro
```bash
export KIRO_CLIENT_ID="your-client-id"
export KIRO_CLIENT_SECRET="your-client-secret"
```

## Token Management

```python
from ai_generator.auth import get_sso_provider

# Get SSO provider
sso = get_sso_provider("amazon_q", profile="my-profile")
# or
sso = get_sso_provider("kiro", client_id="...", client_secret="...")

# Get token (cached automatically)
token = sso.get_token()

# Force refresh
token = sso.get_token(force_refresh=True)

# Clear cache
sso.clear_cache()
```

## Complete Example

```python
from ai_generator.test_generator import AITestGenerator
from ai_generator.llm_providers_extended import AmazonQDeveloperProvider

# Authenticate with SSO
provider = AmazonQDeveloperProvider(
    use_sso=True,
    sso_start_url="https://my-company.awsapps.com/start"
)

# Create generator
generator = AITestGenerator(llm_provider=provider)

# Generate tests
analysis = generator.analyze_code_changes(diff)
tests = generator.generate_test_cases(analysis)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| SSO session expired | `aws sso login --profile my-profile` |
| Invalid credentials | Check `KIRO_CLIENT_ID` and `KIRO_CLIENT_SECRET` |
| Token expired | Auto-refreshes, or use `get_token(force_refresh=True)` |
| Browser doesn't open | Manually visit URL shown in terminal |

## Files

- Token cache: `~/.kiro/sso_tokens.json`
- Permissions: `chmod 600 ~/.kiro/sso_tokens.json`
- Add to .gitignore: `.kiro/sso_tokens.json`

## Documentation

- Full guide: `docs/SSO_AUTHENTICATION_GUIDE.md`
- Examples: `examples/sso_authentication_examples.py`
- API reference: See full guide
