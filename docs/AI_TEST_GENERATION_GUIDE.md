# AI Test Generation Guide

This guide explains how to use the AI-powered test generation features in the web GUI.

## Overview

The system provides two main ways to automatically generate test cases using AI:

1. **From Code Diff**: Analyze git diffs and generate targeted tests for changed code
2. **From Function**: Generate comprehensive tests for specific functions

## Getting Started

### 1. Start the System

```bash
# Start API server
python3 -m api.server

# Start web dashboard (in another terminal)
cd dashboard
npm run dev
```

### 2. Access the Web GUI

Open your browser and go to: `http://localhost:5173`

Navigate to the **Test Execution** page.

## AI Test Generation Features

### Method 1: Generate from Code Diff

This method analyzes git diffs to understand what code has changed and generates appropriate tests.

**Steps:**
1. Click **"AI Generate Tests"** button
2. Select **"From Code Diff"** tab
3. Paste your git diff in the text area
4. Configure generation options:
   - **Max Tests**: Number of tests to generate (1-100)
   - **Test Types**: Types of tests (unit, integration, performance, security)
5. Click **"Generate Tests"**

**Sample Git Diff:**
```diff
diff --git a/kernel/sched/core.c b/kernel/sched/core.c
index 1234567..abcdefg 100644
--- a/kernel/sched/core.c
+++ b/kernel/sched/core.c
@@ -1000,6 +1000,15 @@ static void update_rq_clock_task(struct rq *rq, s64 delta)
 	rq->clock_task += delta;
 }
 
+static int new_scheduler_function(struct task_struct *p)
+{
+	if (!p)
+		return -EINVAL;
+	
+	p->priority = calculate_priority(p);
+	return 0;
+}
```

**What the AI analyzes:**
- Changed files and their subsystems
- New/modified functions
- Impact score and risk level
- Suggested test types

### Method 2: Generate from Function

This method generates comprehensive tests for a specific function.

**Steps:**
1. Click **"AI Generate Tests"** button
2. Select **"From Function"** tab
3. Fill in function details:
   - **Function Name**: e.g., `schedule_task`
   - **File Path**: e.g., `kernel/sched/core.c`
   - **Subsystem**: e.g., `scheduler`
   - **Max Tests**: Number of tests to generate (1-50)
4. Click **"Generate Tests"**

**What gets generated:**
- Unit tests for normal usage
- Boundary condition tests
- Error handling tests
- Property-based tests (if enabled)

## Generated Test Structure

Each generated test includes:

```json
{
  "id": "test_abc123",
  "name": "Test schedule_task - normal operation",
  "description": "Tests normal task scheduling with valid parameters",
  "test_type": "unit",
  "target_subsystem": "scheduler",
  "test_script": "#!/bin/bash\n# Generated test script\n...",
  "execution_time_estimate": 60,
  "metadata": {
    "auto_generated": true,
    "function": "schedule_task"
  }
}
```

## API Endpoints

The web GUI uses these API endpoints for generation:

### Generate from Diff
```http
POST /api/v1/tests/generate-from-diff
Content-Type: application/json

Parameters:
- diff_content: string (git diff content)
- max_tests: integer (1-100)
- test_types: array of strings
```

### Generate from Function
```http
POST /api/v1/tests/generate-from-function
Content-Type: application/json

Parameters:
- function_name: string
- file_path: string
- subsystem: string
- max_tests: integer (1-50)
- include_property_tests: boolean
```

## Example Usage

### Python API Client Example

```python
import requests

# Generate from diff
response = requests.post(
    "http://localhost:8000/api/v1/tests/generate-from-diff",
    params={
        "diff_content": your_git_diff,
        "max_tests": 20,
        "test_types": ["unit", "integration"]
    }
)

# Generate from function
response = requests.post(
    "http://localhost:8000/api/v1/tests/generate-from-function",
    params={
        "function_name": "schedule_task",
        "file_path": "kernel/sched/core.c",
        "subsystem": "scheduler",
        "max_tests": 10
    }
)
```

### JavaScript/TypeScript Example

```typescript
// Using the API service
import apiService from './services/api'

// Generate from diff
const result = await apiService.generateTestsFromDiff(
  gitDiff,
  20,
  ['unit', 'integration']
)

// Generate from function
const result = await apiService.generateTestsFromFunction(
  'schedule_task',
  'kernel/sched/core.c',
  'scheduler',
  10
)
```

## AI Analysis Features

When generating from code diffs, the AI provides:

- **Affected Subsystems**: Which kernel subsystems are impacted
- **Impact Score**: 0.0-1.0 indicating change significance
- **Risk Level**: low, medium, high, critical
- **Changed Functions**: List of modified functions
- **Suggested Test Types**: Recommended types of tests

## Test Types

The system can generate various types of tests:

- **Unit Tests**: Test individual functions in isolation
- **Integration Tests**: Test interactions between components
- **Performance Tests**: Measure execution time and resource usage
- **Security Tests**: Check for vulnerabilities and security issues
- **Fuzz Tests**: Generate random inputs to find edge cases

## Best Practices

### For Code Diff Generation:
1. Use clean, focused diffs (avoid massive changes)
2. Include context lines for better analysis
3. Start with 10-20 tests, then adjust based on results
4. Review generated tests before execution

### For Function Generation:
1. Provide accurate file paths and subsystem information
2. Start with fewer tests (5-10) to evaluate quality
3. Use descriptive function names
4. Consider the function's complexity when setting max tests

### General Tips:
1. **Review Generated Tests**: Always review test scripts before execution
2. **Iterative Approach**: Start small, then generate more tests
3. **Combine Methods**: Use both diff and function generation
4. **Monitor Results**: Check test execution results and adjust

## Troubleshooting

### Common Issues:

**"Test generation failed"**
- Check that the AI generator service is running
- Verify your input format (valid git diff, correct function name)
- Try reducing the number of tests requested

**"No tests generated"**
- The diff might not contain analyzable code changes
- Function might not be found or recognized
- Try a different subsystem or file path

**"Generated tests are low quality"**
- The AI model might need more context
- Try providing more detailed diffs
- Consider manual test creation for complex scenarios

### Getting Help:

1. Check the API server logs for detailed error messages
2. Verify that all required dependencies are installed
3. Test with the provided sample data first
4. Check the network connection between frontend and backend

## Advanced Features

### Custom Test Templates:
The AI generator uses templates that can be customized for your specific needs.

### Property-Based Testing:
When generating from functions, the system can create property-based tests using Hypothesis.

### Integration with CI/CD:
Generated tests can be automatically submitted to your CI/CD pipeline.

## Configuration

### Environment Variables:
```bash
# LLM Provider settings
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7

# Generation settings
MAX_TESTS_PER_FUNCTION=50
DEFAULT_TEST_TIMEOUT=300
```

### API Configuration:
The generation endpoints can be configured in `api/routers/tests.py`.

## Monitoring and Analytics

The system tracks:
- Number of tests generated
- Generation success rate
- Test execution results
- AI model performance metrics

Access these metrics through the dashboard's analytics section.