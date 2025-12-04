# SSO Authentication Guide

Complete guide for using Single Sign-On (SSO) authentication with Amazon Q Developer and Kiro AI.

## Overview

SSO authentication provides:
- **Enhanced Security**: No need to store API keys
- **Centralized Access**: Use your organization's identity provider
- **Token Management**: Automatic token refresh and caching
- **Audit Trail**: Better tracking of API usage

## Amazon Q Developer SSO

### Authentication Methods

Amazon Q supports three SSO methods:

1. **AWS CLI Profile** (Recommended)
2. **Device Code Flow** (Interactive)
3. **IAM Identity Center** (Enterprise)

### Method 1: AWS CLI Profile

**Setup:**
```bash
# Configure AWS SSO
aws configure sso

# Follow prompts:
# SSO start URL: https://my-company.awsapps.com/start
# SSO region: us-east-1
# Account ID: 123456789012
# Role name: DeveloperAccess
# Profile name: my-sso-profile

# Login
aws sso login --profile my-sso-profile
```

**Usage:**
```python
from ai_generator.llm_providers_extended import AmazonQDeveloperProvider
from ai_generator.test_generator import AITestGenerator

# Use SSO profile
provider = AmazonQDeveloperProvider(
    profile="my-sso-profile",
    region="us-east-1"
)

generator = AITestGenerator(llm_provider=provider)
```

**Benefits:**
- ✅ No code changes needed after initial setup
- ✅ Uses existing AWS CLI configuration
- ✅ Automatic token refresh
- ✅ Works with all AWS services

### Method 2: Device Code Flow

**Setup:**
```bash
# Set environment variables
export AWS_SSO_START_URL="https://my-company.awsapps.com/start"
export AWS_SSO_REGION="us-east-1"
```

**Usage:**
```python
provider = AmazonQDeveloperProvider(
    use_sso=True,
    sso_start_url="https://my-company.awsapps.com/start",
    sso_region="us-east-1",
    region="us-east-1"
)

# This will:
# 1. Open browser automatically
# 2. Display device code
# 3. Wait for authentication
# 4. Cache token for future use

generator = AITestGenerator(llm_provider=provider)
```

**Benefits:**
- ✅ Works in CLI/terminal environments
- ✅ No browser cookies needed
- ✅ Token caching for reuse
- ✅ Automatic token refresh

### Method 3: IAM Identity Center

**Setup:**
```bash
# Configure IAM Identity Center
export AWS_SSO_START_URL="https://my-company.awsapps.com/start"
export AWS_SSO_REGION="us-east-1"
export AWS_SSO_ACCOUNT_ID="123456789012"
export AWS_SSO_ROLE_NAME="DeveloperAccess"
```

**Usage:**
```python
from ai_generator.auth import AmazonQSSOProvider

# Create SSO provider
sso = AmazonQSSOProvider(
    sso_start_url="https://my-company.awsapps.com/start",
    sso_region="us-east-1",
    sso_account_id="123456789012",
    sso_role_name="DeveloperAccess"
)

# Get token
token = sso.get_token()

# Use with provider
provider = AmazonQDeveloperProvider(
    api_key=token.access_token,
    region="us-east-1"
)
```

## Kiro AI SSO

### Authentication Method: OAuth2/OIDC

Kiro uses standard OAuth2 with device code flow for CLI authentication.

### Setup

**1. Get OAuth2 Credentials:**
- Log in to [Kiro Dashboard](https://dashboard.kiro.ai)
- Navigate to Settings → API → OAuth2
- Create new OAuth2 application
- Note your Client ID and Client Secret

**2. Set Environment Variables:**
```bash
export KIRO_CLIENT_ID="your-client-id"
export KIRO_CLIENT_SECRET="your-client-secret"
```

### Usage

**Basic Usage:**
```python
from ai_generator.llm_providers_extended import KiroProvider
from ai_generator.test_generator import AITestGenerator

# Use SSO
provider = KiroProvider(
    use_sso=True,
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# This will:
# 1. Open browser for OAuth2 authorization
# 2. Display device code
# 3. Wait for user authorization
# 4. Cache token for future use
# 5. Auto-refresh when expired

generator = AITestGenerator(llm_provider=provider)
```

**Standalone SSO Provider:**
```python
from ai_generator.auth import KiroSSOProvider

# Create SSO provider
sso = KiroSSOProvider(
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Get token (authenticates if needed)
token = sso.get_token()

# Token info
print(f"Access Token: {token.access_token}")
print(f"Expires: {token.expires_at}")
print(f"Scopes: {token.scope}")

# Use with provider
provider = KiroProvider(api_key=token.access_token)
```

## Token Management

### Token Caching

Tokens are automatically cached to `~/.kiro/sso_tokens.json`:

```json
{
  "AmazonQSSOProvider": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": "2024-12-05T10:30:00",
    "token_type": "Bearer"
  },
  "KiroSSOProvider": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": "2024-12-05T12:00:00",
    "token_type": "Bearer",
    "scope": "api test_generation"
  }
}
```

### Token Refresh

Tokens are automatically refreshed when expired:

```python
# Get token (uses cache if valid)
token = sso.get_token()

# Force refresh
token = sso.get_token(force_refresh=True)

# Clear cache
sso.clear_cache()
```

### Token Security

**Best Practices:**
1. ✅ Token cache has restrictive permissions (0600)
2. ✅ Never commit token cache to git
3. ✅ Use environment variables for credentials
4. ✅ Rotate tokens regularly
5. ✅ Clear cache when switching accounts

**Add to .gitignore:**
```
# SSO token cache
.kiro/sso_tokens.json
```

## Configuration

### Environment Variables

**Amazon Q:**
```bash
# SSO Configuration
export AWS_SSO_START_URL="https://my-company.awsapps.com/start"
export AWS_SSO_REGION="us-east-1"
export AWS_SSO_ACCOUNT_ID="123456789012"
export AWS_SSO_ROLE_NAME="DeveloperAccess"

# Or use AWS Profile
export AWS_PROFILE="my-sso-profile"
```

**Kiro:**
```bash
# OAuth2 Configuration
export KIRO_CLIENT_ID="your-client-id"
export KIRO_CLIENT_SECRET="your-client-secret"
export KIRO_AUTH_URL="https://auth.kiro.ai/oauth/authorize"
export KIRO_TOKEN_URL="https://auth.kiro.ai/oauth/token"
```

### .env File

Create `.env` in your project root:

```env
# Amazon Q SSO
AWS_SSO_START_URL=https://my-company.awsapps.com/start
AWS_SSO_REGION=us-east-1
AWS_PROFILE=my-sso-profile

# Kiro SSO
KIRO_CLIENT_ID=your-client-id
KIRO_CLIENT_SECRET=your-client-secret
```

## Complete Examples

### Example 1: Amazon Q with AWS CLI Profile

```python
from ai_generator.test_generator import AITestGenerator
from ai_generator.llm_providers_extended import AmazonQDeveloperProvider

# Setup (one-time)
# $ aws configure sso
# $ aws sso login --profile my-sso-profile

# Use in code
provider = AmazonQDeveloperProvider(profile="my-sso-profile")
generator = AITestGenerator(llm_provider=provider)

# Generate tests
diff = "..." # Your git diff
analysis = generator.analyze_code_changes(diff)
tests = generator.generate_test_cases(analysis)
```

### Example 2: Kiro with OAuth2

```python
from ai_generator.test_generator import AITestGenerator
from ai_generator.llm_providers_extended import KiroProvider

# First run - will open browser for authentication
provider = KiroProvider(
    use_sso=True,
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Subsequent runs - uses cached token
generator = AITestGenerator(llm_provider=provider)

# Generate tests
tests = generator.generate_test_cases(analysis)
```

### Example 3: Token Reuse

```python
from ai_generator.auth import get_sso_provider

# Authenticate once
sso = get_sso_provider(
    "kiro",
    client_id="your-client-id",
    client_secret="your-client-secret"
)
token = sso.get_token()

# Use token multiple times
from ai_generator.llm_providers_extended import KiroProvider

provider1 = KiroProvider(api_key=token.access_token)
provider2 = KiroProvider(api_key=token.access_token)

# Both use same token (no re-authentication)
```

## Troubleshooting

### Amazon Q SSO

**Issue: "SSO session has expired"**
```bash
# Solution: Re-login
aws sso login --profile my-sso-profile
```

**Issue: "Unable to locate credentials"**
```bash
# Solution: Configure SSO
aws configure sso
```

**Issue: "Access denied"**
```bash
# Solution: Check IAM permissions
# Required permissions:
# - sso:GetRoleCredentials
# - sso:ListAccounts
# - sso:ListAccountRoles
```

### Kiro SSO

**Issue: "Invalid client credentials"**
```python
# Solution: Verify credentials
import os
print(f"Client ID: {os.getenv('KIRO_CLIENT_ID')}")
# Regenerate if needed from Kiro dashboard
```

**Issue: "Token expired"**
```python
# Solution: Force refresh
token = sso.get_token(force_refresh=True)
```

**Issue: "Authentication timeout"**
```python
# Solution: Complete authentication faster
# Or increase timeout in SSO provider
```

### General Issues

**Issue: "Token cache permission denied"**
```bash
# Solution: Fix permissions
chmod 600 ~/.kiro/sso_tokens.json
```

**Issue: "Browser doesn't open"**
```bash
# Solution: Manually visit the URL
# The URL will be displayed in terminal
```

## Security Considerations

### Do's ✅
- Use SSO in production environments
- Store tokens in secure cache with restrictive permissions
- Rotate credentials regularly
- Use environment variables for sensitive data
- Enable MFA on your SSO provider
- Monitor token usage and access logs

### Don'ts ❌
- Don't commit tokens to version control
- Don't share tokens between users
- Don't disable token expiration
- Don't use SSO tokens in public repositories
- Don't store tokens in plain text files

## Migration from API Keys

### Before (API Key):
```python
provider = KiroProvider(api_key="hardcoded-key")
```

### After (SSO):
```python
provider = KiroProvider(
    use_sso=True,
    client_id=os.getenv("KIRO_CLIENT_ID"),
    client_secret=os.getenv("KIRO_CLIENT_SECRET")
)
```

### Migration Steps:
1. Get OAuth2 credentials from provider
2. Set environment variables
3. Update code to use SSO
4. Test authentication flow
5. Remove hardcoded API keys
6. Update documentation

## API Reference

### AmazonQSSOProvider

```python
class AmazonQSSOProvider(BaseSSOProvider):
    def __init__(
        self,
        sso_start_url: Optional[str] = None,
        sso_region: Optional[str] = None,
        sso_account_id: Optional[str] = None,
        sso_role_name: Optional[str] = None,
        profile_name: Optional[str] = None,
        **kwargs
    )
    
    def authenticate(self) -> SSOToken
    def refresh_token(self, token: SSOToken) -> SSOToken
    def get_token(self, force_refresh: bool = False) -> SSOToken
    def clear_cache(self) -> None
```

### KiroSSOProvider

```python
class KiroSSOProvider(BaseSSOProvider):
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        auth_url: Optional[str] = None,
        token_url: Optional[str] = None,
        redirect_uri: str = "http://localhost:8080/callback",
        scopes: Optional[list] = None,
        **kwargs
    )
    
    def authenticate(self) -> SSOToken
    def refresh_token(self, token: SSOToken) -> SSOToken
    def get_token(self, force_refresh: bool = False) -> SSOToken
    def clear_cache(self) -> None
```

### SSOToken

```python
@dataclass
class SSOToken:
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    token_type: str = "Bearer"
    scope: Optional[str] = None
    
    def is_expired(self) -> bool
    def to_dict(self) -> Dict[str, Any]
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SSOToken'
```

## Support

- Amazon Q SSO: [AWS SSO Documentation](https://docs.aws.amazon.com/singlesignon/)
- Kiro OAuth2: [Kiro API Documentation](https://docs.kiro.ai/oauth)
- Issues: [GitHub Issues](https://github.com/your-repo/issues)
