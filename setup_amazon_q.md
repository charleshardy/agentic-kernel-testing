# Setup Amazon Q Developer Pro for AI Test Generation

## Current Issue
The system is configured to use Amazon Q Developer Pro (`LLM__PROVIDER=amazon_q`) but AWS CLI is not installed, so it's falling back to basic template-based test generation.

## Solution: Install and Configure AWS CLI with SSO

### Step 1: Install AWS CLI v2
```bash
# Download and install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

### Step 2: Configure AWS SSO Profile
```bash
# Configure SSO profile (use the settings from .env file)
aws configure sso --profile default

# When prompted, enter:
# - SSO session name: default
# - SSO start URL: https://d-926706e585.awsapps.com/start
# - SSO region: us-west-2
# - Account ID: 926706e585
# - Role name: AmazonQDeveloperAccess
# - CLI default client Region: us-west-2
# - CLI default output format: json
```

### Step 3: Login to AWS SSO
```bash
# Login to AWS SSO
aws sso login --profile default

# Verify access
aws sts get-caller-identity --profile default
```

### Step 4: Test AI Generation
After AWS SSO is configured:
1. Restart the API server: `python -m api.server`
2. Go to the web dashboard: http://localhost:3001/test-cases
3. Click "AI Generate Tests" → "From Function"
4. Fill in the form and submit
5. You should now see real AI-generated test cases instead of basic templates

## Alternative Options

### Option 2: Use OpenAI (Simpler Setup)
If you have an OpenAI API key, you can switch to OpenAI:

1. Get an API key from https://platform.openai.com/api-keys
2. Update `.env` file:
   ```bash
   LLM__PROVIDER=openai
   OPENAI__API_KEY=sk-your-openai-api-key-here
   OPENAI__MODEL=gpt-4
   ```
3. Restart the API server

### Option 3: Use Anthropic Claude
If you have an Anthropic API key:

1. Get an API key from https://console.anthropic.com/
2. Update `.env` file:
   ```bash
   LLM__PROVIDER=anthropic
   ANTHROPIC__API_KEY=sk-ant-your-anthropic-api-key-here
   ANTHROPIC__MODEL=claude-3-5-sonnet-20241022
   ```
3. Restart the API server

## Expected Results After Setup

Once properly configured, AI-generated test cases will include:
- Real test logic instead of just "pass"
- Proper assertions and test scenarios
- Edge case testing
- Input validation tests
- Error condition testing
- Performance considerations

Example of what you'll see instead of basic templates:
```python
def test_schedule_task_normal_operation():
    """Test schedule_task with valid parameters."""
    task = create_test_task(priority=5, cpu_mask=0x1)
    result = schedule_task(task)
    
    assert result == 0, "Task scheduling should succeed"
    assert task.state == TASK_RUNNING, "Task should be in running state"
    assert get_current_task() == task, "Task should be current"

def test_schedule_task_invalid_priority():
    """Test schedule_task with invalid priority values."""
    task = create_test_task(priority=-1, cpu_mask=0x1)
    result = schedule_task(task)
    
    assert result == -EINVAL, "Should return error for invalid priority"
    assert task.state == TASK_UNINTERRUPTIBLE, "Task state should not change"
```

## Troubleshooting

If you still see basic templates after setup:
1. Check API server logs for LLM provider initialization errors
2. Verify AWS credentials: `aws sts get-caller-identity --profile default`
3. Restart the API server after configuration changes
4. Check the browser console for any authentication errors