# Agentic AI Testing System REST API

A comprehensive REST API for the Agentic AI Testing System that enables external integrations, CI/CD pipeline automation, and programmatic access to kernel and BSP testing capabilities.

## Features

- **Test Submission**: Submit test cases for execution across multiple hardware configurations
- **Status Monitoring**: Real-time monitoring of test execution progress and status
- **Result Retrieval**: Access detailed test results, coverage reports, and failure analyses
- **Code Analysis**: AI-powered analysis of code changes with test recommendations
- **Authentication**: Secure token-based authentication with role-based permissions
- **CI/CD Integration**: Webhook endpoints for seamless integration with version control systems

## Quick Start

### 1. Start the API Server

```bash
# Using the startup script
python api/server.py

# Or with custom options
python api/server.py --host 0.0.0.0 --port 8080 --reload

# Or using uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### 3. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

## Authentication

The API uses JWT (JSON Web Token) based authentication. All endpoints except health checks require authentication.

### Default Users

For development and testing, the following users are available:

| Username | Password | Permissions |
|----------|----------|-------------|
| `admin` | `admin123` | Full access (submit, read, delete, admin) |
| `developer` | `dev123` | Submit and read tests, view results |
| `readonly` | `readonly123` | Read-only access to tests and results |

### Login Example

```bash
# Login to get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/tests"
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login and get access token
- `POST /api/v1/auth/logout` - Logout and revoke token
- `GET /api/v1/auth/me` - Get current user information
- `POST /api/v1/auth/api-key` - Generate long-lived API key

### Health & Status
- `GET /api/v1/health` - Public health check
- `GET /api/v1/health/detailed` - Detailed system health (admin only)
- `GET /api/v1/health/metrics` - System metrics

### Test Management
- `POST /api/v1/tests/submit` - Submit test cases for execution
- `GET /api/v1/tests` - List submitted test cases
- `GET /api/v1/tests/{test_id}` - Get specific test case details
- `DELETE /api/v1/tests/{test_id}` - Delete test case
- `POST /api/v1/tests/analyze-code` - Analyze code changes

### Execution Status
- `GET /api/v1/status/plans/{plan_id}` - Get execution plan status
- `GET /api/v1/status/tests/{test_id}` - Get test execution status
- `GET /api/v1/status/active` - Get all active executions
- `POST /api/v1/status/cancel/{test_id}` - Cancel test execution

### Results
- `GET /api/v1/results/tests` - List test results
- `GET /api/v1/results/tests/{test_id}` - Get specific test result
- `GET /api/v1/results/coverage/{test_id}` - Get coverage report
- `GET /api/v1/results/failures/{test_id}` - Get failure analysis
- `GET /api/v1/results/artifacts/{test_id}` - Download test artifacts
- `GET /api/v1/results/export` - Export results in various formats

## Usage Examples

### Submit a Test Case

```bash
curl -X POST "http://localhost:8000/api/v1/tests/submit" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_cases": [{
      "name": "Network Driver Test",
      "description": "Test e1000e network driver functionality",
      "test_type": "unit",
      "target_subsystem": "networking",
      "test_script": "#!/bin/bash\nmodprobe e1000e\necho \"Test completed\"",
      "execution_time_estimate": 120,
      "required_hardware": {
        "architecture": "x86_64",
        "cpu_model": "Intel Xeon",
        "memory_mb": 2048,
        "is_virtual": true,
        "emulator": "qemu"
      }
    }],
    "priority": 5
  }'
```

### Monitor Test Execution

```bash
# Get execution plan status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/status/plans/PLAN_ID"

# Get individual test status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/status/tests/TEST_ID"
```

### Retrieve Test Results

```bash
# List all results
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/results/tests"

# Get specific result
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/results/tests/TEST_ID"

# Get coverage report
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/results/coverage/TEST_ID"
```

### Code Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/tests/analyze-code" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_url": "https://github.com/torvalds/linux.git",
    "commit_sha": "abc123def456",
    "branch": "main"
  }'
```

## Python Client Example

```python
import requests

class AgenticTestingAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, username, password):
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        data = response.json()
        token = data["data"]["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        return data
    
    def submit_tests(self, test_cases, priority=0):
        return self.session.post(
            f"{self.base_url}/api/v1/tests/submit",
            json={"test_cases": test_cases, "priority": priority}
        ).json()

# Usage
api = AgenticTestingAPI()
api.login("admin", "admin123")
result = api.submit_tests([{
    "name": "My Test",
    "description": "Test description",
    "test_type": "unit",
    "target_subsystem": "networking",
    "test_script": "echo 'test'"
}])
```

## Configuration

The API server can be configured through environment variables or the settings system:

```bash
# API Configuration
API__HOST=0.0.0.0
API__PORT=8000
API__SECRET_KEY=your-secret-key-here
API__TOKEN_EXPIRE_HOURS=24
API__CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Database Configuration  
DATABASE__TYPE=postgresql
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=agentic_testing
DATABASE__USER=postgres
DATABASE__PASSWORD=password
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "success": false,
  "message": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "test_type",
    "error": "Invalid test type"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Common status codes:
- `200` - Success
- `400` - Bad Request (validation error)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Authenticated users**: 1000 requests per hour
- **Unauthenticated requests**: 100 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248600
```

## Webhooks

The API supports webhooks for real-time notifications of test status changes:

```json
{
  "event_type": "test_completed",
  "submission_id": "sub-123",
  "test_id": "test-456",
  "status": "passed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "execution_time": 125.5,
    "coverage": 0.85
  }
}
```

## Security

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**: Fine-grained permissions system
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive request validation using Pydantic
- **Rate Limiting**: Protection against abuse and DoS attacks

## Development

### Running Tests

```bash
# Run API tests
pytest tests/unit/test_api.py -v

# Run with coverage
pytest tests/unit/test_api.py --cov=api --cov-report=html
```

### Development Server

```bash
# Start with auto-reload
python api/server.py --reload --debug

# Or with uvicorn
uvicorn api.main:app --reload --log-level debug
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "api/server.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# Production settings
API__DEBUG=false
API__SECRET_KEY=your-production-secret-key
API__CORS_ORIGINS=["https://yourdomain.com"]
DATABASE__TYPE=postgresql
DATABASE__HOST=db.yourdomain.com
```

## Support

For issues, questions, or contributions:
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Example Usage**: See `examples/api_usage_example.py`