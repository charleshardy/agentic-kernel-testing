# Quick Start Guide: Amazon Q Developer Pro & Kiro AI

This guide helps you quickly set up the Agentic AI Testing System with Amazon Q Developer Pro and Kiro AI integration.

## Prerequisites

- Python 3.10+ (✅ Current: 3.12.3)
- Git access to this repository
- AWS SSO access (for Amazon Q Developer Pro)
- Kiro AI account (for IDE integration)

## Quick Setup Steps

### 1. Verify Your Environment

```bash
# Run the setup verification script
python3 verify_setup.py
```

This will check:
- ✅ Python version (3.10+)
- ✅ Project structure
- ✅ Core dependencies (FastAPI, pytest, hypothesis, etc.)
- ✅ Configuration files
- ⚠️ Optional dependencies (OpenAI, Anthropic, etc.)

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

### 3. Amazon Q Developer Pro Setup (Recommended)

#### Option A: AWS SSO (Recommended)
```bash
# Configure AWS SSO profile
aws configure sso --profile my-sso-profile

# Login to AWS SSO
aws sso login --profile my-sso-profile
```

Update your `.env` file:
```bash
LLM__PROVIDER=amazon_q
AWS_PROFILE=my-sso-profile
AWS_REGION=us-east-1
AWS_SSO_ACCOUNT_ID=your-account-id
```

#### Option B: Direct AWS Credentials (Not recommended for production)
```bash
LLM__PROVIDER=amazon_q
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

### 4. Kiro AI Setup (IDE Integration)

#### OAuth2 SSO Setup (Recommended)
1. Get OAuth2 credentials from Kiro dashboard
2. Update your `.env` file:
```bash
KIRO__CLIENT_ID=your-kiro-client-id
KIRO__CLIENT_SECRET=your-kiro-client-secret
KIRO__REDIRECT_URI=http://localhost:8080/callback
```

#### API Key Setup (Alternative)
```bash
KIRO__API_KEY=your-kiro-api-key
```

### 5. Install Dependencies

#### Using pip (System-wide)
```bash
pip3 install --user -r requirements.txt
```

#### Using Poetry (Recommended for development)
```bash
poetry install
```

#### Using Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt
```

### 6. Verify Installation

```bash
# Run verification again to confirm setup
python3 verify_setup.py

# Run basic tests
pytest tests/unit/ -v

# Start the API server (optional)
python -m api.server
```

## Configuration Examples

### Example 1: Amazon Q Developer Pro with SSO
```bash
# .env file
LLM__PROVIDER=amazon_q
AWS_PROFILE=my-company-sso
AWS_REGION=us-east-1
AWS_SSO_START_URL=https://my-company.awsapps.com/start
AWS_SSO_ACCOUNT_ID=123456789012
```

### Example 2: Kiro AI with OAuth2
```bash
# .env file
LLM__PROVIDER=kiro
KIRO__CLIENT_ID=kiro_abc123
KIRO__CLIENT_SECRET=secret_xyz789
KIRO__MODEL=kiro-advanced
```

### Example 3: Multi-provider Fallback
```bash
# .env file
LLM__PROVIDER=amazon_q
# Amazon Q settings...
# Plus OpenAI as fallback
OPENAI__API_KEY=sk-your-openai-key
```

## Programming Interface

### Basic Usage with Amazon Q Developer Pro
```python
from ai_generator.llm_providers_extended import create_provider
from ai_generator.test_generator import AITestGenerator

# Create provider (uses .env configuration)
provider = create_provider("amazon_q", region="us-east-1")
generator = AITestGenerator(llm_provider=provider)

# Analyze code changes
diff = """
diff --git a/src/main.c b/src/main.c
...
"""

analysis = generator.analyze_code_changes(diff)
test_cases = generator.generate_test_cases(analysis)
print(f"Generated {len(test_cases)} tests!")
```

### Basic Usage with Kiro AI
```python
from ai_generator.llm_providers_extended import create_provider
from ai_generator.test_generator import AITestGenerator

# Create provider (uses .env configuration)
provider = create_provider("kiro", api_key="your-key")
generator = AITestGenerator(llm_provider=provider)

# Generate property-based tests
property_tests = generator.generate_property_tests(functions)
print(f"Generated {len(property_tests)} property tests!")
```

## Troubleshooting

### Common Issues

1. **Python Version Error**
   ```bash
   # Check version
   python3 --version
   # Should be 3.10 or higher
   ```

2. **Missing Dependencies**
   ```bash
   # Install missing packages
   pip3 install --user fastapi pytest hypothesis pydantic
   ```

3. **AWS SSO Issues**
   ```bash
   # Re-login to AWS SSO
   aws sso login --profile your-profile
   
   # Check credentials
   aws sts get-caller-identity --profile your-profile
   ```

4. **Permission Errors**
   ```bash
   # Use --user flag for pip
   pip3 install --user package-name
   
   # Or use virtual environment
   python3 -m venv venv && source venv/bin/activate
   ```

### Getting Help

- Run `python3 verify_setup.py` for detailed environment check
- Check the main [README.md](README.md) for full documentation
- Review [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for project layout
- See [docs/](docs/) directory for detailed guides

## Next Steps

1. **Development**: Start with `pytest tests/unit/`
2. **API Server**: Run `python -m api.server`
3. **Web Dashboard**: Check `dashboard/` directory
4. **Documentation**: Explore `docs/` for detailed guides
5. **CI/CD**: Configure webhooks for your repository

## Security Notes

- Never commit `.env` files to git
- Use AWS SSO instead of hardcoded credentials
- Rotate API keys regularly
- Use OAuth2 for Kiro AI integration when possible

## Support

- Amazon Q Developer Pro: https://aws.amazon.com/q/developer/
- Kiro AI: https://kiro.ai
- Issues: https://github.com/charleshardy/agentic-kernel-testing/issues

---

**Status**: ✅ Environment verified and ready for development  
**Last Updated**: December 2025  
**Version**: 1.0.0 Production Ready