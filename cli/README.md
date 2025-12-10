# Agentic AI Testing System - CLI

A comprehensive command-line interface for the Agentic AI Testing System, providing full control over kernel and BSP testing workflows.

## Features

- **Test Management**: Submit, monitor, and manage test cases
- **Status Monitoring**: Real-time status updates and execution tracking
- **Results Analysis**: View detailed test results, coverage, and failure analysis
- **Environment Management**: Control test execution environments
- **Configuration Management**: Manage system configuration
- **Interactive Mode**: Explore system data interactively

## Installation

### From Source

```bash
# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x cli/agentic-test

# Add to PATH (optional)
export PATH=$PATH:$(pwd)/cli
```

### Using pip (if packaged)

```bash
pip install agentic-testing-cli
```

## Quick Start

### Basic Usage

```bash
# Check system health
agentic-test health

# Submit a test
agentic-test test submit \
  --name "Memory allocation test" \
  --description "Test kernel memory allocation" \
  --type unit \
  --subsystem mm \
  --script "echo 'Test script here'"

# Check test status
agentic-test status active

# View results
agentic-test results list --failed-only
```

### Interactive Mode

```bash
# Start interactive shell
agentic-test interactive shell

# Explore system data
agentic-test interactive explore
```

## Command Reference

### Global Options

- `--debug`: Enable debug logging
- `--config-file PATH`: Path to configuration file
- `--api-url URL`: API server URL (overrides config)
- `--api-key KEY`: API key for authentication

### Test Commands

#### Submit Tests

```bash
# Submit single test
agentic-test test submit \
  --name "Test name" \
  --description "Test description" \
  --type unit \
  --subsystem mm \
  --script "test script content" \
  --priority 5

# Submit from configuration file
agentic-test test submit-batch --config-file tests.yaml

# Generate template
agentic-test test template --format yaml
```

#### List and Manage Tests

```bash
# List tests
agentic-test test list --type unit --subsystem mm

# Show test details
agentic-test test show <test-id>

# Delete test
agentic-test test delete <test-id>

# Analyze code changes
agentic-test test analyze \
  --repository-url https://github.com/torvalds/linux.git \
  --commit-sha abc123 \
  --auto-submit
```

### Status Commands

#### Monitor Execution

```bash
# Show execution plan status
agentic-test status plan <plan-id>

# Show individual test status
agentic-test status test <test-id>

# Show all active executions
agentic-test status active

# Wait for completion
agentic-test status wait <plan-id> --timeout 3600

# Cancel test
agentic-test status cancel <test-id>

# System summary
agentic-test status summary
```

#### Watch Mode

```bash
# Watch plan status (updates every 10 seconds)
agentic-test status plan <plan-id> --watch --interval 10

# Watch active executions
agentic-test status active --watch
```

### Results Commands

#### View Results

```bash
# List results
agentic-test results list --failed-only --start-date 2024-01-01

# Show detailed result
agentic-test results show <test-id>

# Show coverage report
agentic-test results coverage <test-id>

# Show failure analysis
agentic-test results failure <test-id>

# Results summary
agentic-test results summary --days 30
```

#### Export and Download

```bash
# Download artifacts
agentic-test results download <test-id> logs --output-path test_logs.tar.gz

# Export results
agentic-test results export \
  --format json \
  --start-date 2024-01-01 \
  --output-path results.json

# Cleanup old results
agentic-test results cleanup --days 30 --dry-run
```

### Environment Commands

#### Manage Environments

```bash
# List environments
agentic-test env list --architecture x86_64 --virtual

# Show environment details
agentic-test env show <env-id>

# Create environment
agentic-test env create \
  --architecture x86_64 \
  --memory 4096 \
  --virtual \
  --emulator qemu

# Delete environment
agentic-test env delete <env-id>

# Reset environment
agentic-test env reset <env-id>
```

#### Environment Status

```bash
# Show available environments
agentic-test env available --architecture arm64 --min-memory 2048

# Environment statistics
agentic-test env stats

# Cleanup unused environments
agentic-test env cleanup --idle-only --older-than 24
```

### Configuration Commands

#### View and Modify Configuration

```bash
# Show current configuration
agentic-test config show

# Get specific value
agentic-test config get llm.provider

# Set configuration value
agentic-test config set llm.provider openai --type str

# Validate configuration
agentic-test config validate
```

#### Import/Export Configuration

```bash
# Export configuration
agentic-test config export --format yaml --output-file config.yaml

# Import configuration
agentic-test config import config.yaml

# Configuration wizard
agentic-test config wizard

# Reset to defaults
agentic-test config reset
```

### Interactive Commands

#### Interactive Shell

```bash
# Start interactive shell
agentic-test interactive shell
```

Available shell commands:
- `status` - Show system status
- `tests` - List recent tests
- `tests active` - Show active tests
- `tests submit` - Submit new test interactively
- `results` - List recent results
- `results failed` - Show failed tests
- `results summary` - Show results summary
- `envs` - List environments
- `envs available` - Show available environments
- `envs stats` - Show environment statistics
- `help` - Show help
- `exit` - Exit shell

#### System Explorer

```bash
# Start system explorer
agentic-test interactive explore
```

## Configuration

### Environment Variables

The CLI uses the same configuration system as the main application. Key environment variables:

```bash
# API Configuration
API_HOST=localhost
API_PORT=8000

# LLM Configuration
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_NAME=agentic_testing

# Execution Configuration
EXECUTION_MAX_PARALLEL_TESTS=10
EXECUTION_TEST_TIMEOUT=300
```

### Configuration File

Create a YAML configuration file:

```yaml
# config.yaml
llm:
  provider: openai
  api_key: your-api-key
  model: gpt-4

database:
  type: sqlite
  name: agentic_testing

execution:
  max_parallel_tests: 10
  test_timeout: 300
  virtual_env_enabled: true

api:
  host: localhost
  port: 8000
```

Use with: `agentic-test --config-file config.yaml`

### Test Configuration File

Create test batch configuration:

```yaml
# tests.yaml
tests:
  - name: "Memory allocation test"
    description: "Test kernel memory allocation functions"
    test_type: "unit"
    target_subsystem: "mm"
    execution_time_estimate: 300
    priority: 5
    code_paths:
      - "mm/page_alloc.c:alloc_pages"
      - "mm/slab.c:kmalloc"
    required_hardware:
      architecture: "x86_64"
      memory_mb: 2048
      is_virtual: true
    test_script: |
      #!/bin/bash
      echo "Running memory allocation test"
      # Add your test commands here
      exit 0
    metadata:
      author: "test-author"
      category: "memory"

  - name: "Network stack test"
    description: "Test network protocol handling"
    test_type: "integration"
    target_subsystem: "net"
    script_file: "./scripts/network_test.sh"
    priority: 3
```

## Examples

### Complete Workflow Example

```bash
# 1. Check system health
agentic-test health

# 2. Create test configuration
agentic-test test template --format yaml --output-file my_tests.yaml

# 3. Edit my_tests.yaml with your test cases

# 4. Submit tests
agentic-test test submit-batch --config-file my_tests.yaml

# 5. Monitor execution
agentic-test status active --watch

# 6. View results when complete
agentic-test results list

# 7. Analyze failures
agentic-test results list --failed-only
agentic-test results failure <failed-test-id>
```

### Code Analysis Workflow

```bash
# Analyze recent changes
agentic-test test analyze \
  --repository-url https://github.com/torvalds/linux.git \
  --branch master \
  --auto-submit \
  --priority 8

# Monitor the generated tests
agentic-test status active --watch
```

### Environment Management Workflow

```bash
# Check available environments
agentic-test env available

# Create additional environment if needed
agentic-test env create \
  --architecture arm64 \
  --memory 4096 \
  --virtual

# Run tests on specific architecture
agentic-test test submit \
  --name "ARM64 test" \
  --type unit \
  --subsystem mm \
  --hardware-arch arm64 \
  --script "echo 'ARM64 specific test'"

# Clean up when done
agentic-test env cleanup --idle-only
```

## Troubleshooting

### Common Issues

1. **Connection refused**
   ```bash
   # Check if API server is running
   agentic-test health
   
   # Check configuration
   agentic-test config show
   ```

2. **Authentication errors**
   ```bash
   # Set API key
   export API_KEY=your-api-key
   
   # Or use command line option
   agentic-test --api-key your-key health
   ```

3. **Configuration issues**
   ```bash
   # Validate configuration
   agentic-test config validate
   
   # Reset to defaults
   agentic-test config reset
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
agentic-test --debug test submit --name "Debug test" --type unit --subsystem mm
```

### Getting Help

```bash
# General help
agentic-test --help

# Command-specific help
agentic-test test --help
agentic-test test submit --help

# Interactive help
agentic-test interactive shell
# Then type: help
```

## Integration

### CI/CD Integration

Use the CLI in CI/CD pipelines:

```bash
#!/bin/bash
# ci-test.sh

# Submit tests
PLAN_ID=$(agentic-test test submit-batch --config-file ci-tests.yaml --format json | jq -r '.execution_plan_id')

# Wait for completion
agentic-test status wait $PLAN_ID --timeout 1800 --quiet

# Check results
FAILED_COUNT=$(agentic-test results summary --days 1 --format json | jq '.failed_tests')

if [ "$FAILED_COUNT" -gt 0 ]; then
    echo "Tests failed: $FAILED_COUNT"
    exit 1
fi

echo "All tests passed"
```

### Scripting

Use the CLI in scripts with JSON output:

```bash
#!/bin/bash
# get-test-status.sh

TEST_ID=$1
STATUS=$(agentic-test status test $TEST_ID --format json | jq -r '.status')

case $STATUS in
    "passed")
        echo "✅ Test passed"
        ;;
    "failed")
        echo "❌ Test failed"
        agentic-test results failure $TEST_ID
        ;;
    "running")
        echo "🏃 Test still running"
        ;;
    *)
        echo "❓ Unknown status: $STATUS"
        ;;
esac
```

## Contributing

The CLI is part of the Agentic AI Testing System. See the main project documentation for contribution guidelines.

## License

See the main project LICENSE file.