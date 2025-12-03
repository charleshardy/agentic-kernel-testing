# Quick Start Guide

Get up and running with the Agentic AI Testing System in minutes.

## Prerequisites

- Python 3.10+
- pip or Poetry
- Git

## Installation (5 minutes)

```bash
# Clone the repository
git clone <repository-url>
cd agentic-kernel-testing

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your LLM API key

# Verify setup
python3 verify_setup.py
```

## Configuration (2 minutes)

Edit `.env` with your settings:

```bash
# Minimum required configuration
LLM__API_KEY=your-openai-api-key-here
DATABASE__TYPE=sqlite
```

## Run Tests (1 minute)

```bash
# Run the test suite
pytest tests/unit/

# Expected output:
# ===== test session starts =====
# collected X items
# tests/unit/test_config.py ......
# ===== X passed in X.XXs =====
```

## Project Structure

```
agentic-kernel-testing/
├── ai_generator/       # AI test generation
├── orchestrator/       # Test scheduling
├── execution/          # Test execution
├── analysis/           # Result analysis
├── integration/        # CI/CD integration
├── config/             # Configuration system
├── tests/              # Test suite
│   ├── unit/          # Unit tests
│   ├── property/      # Property-based tests
│   └── integration/   # Integration tests
└── docs/              # Documentation
```

## Next Steps

### 1. Explore the Specification

Read the project specifications to understand the system:

- [Requirements](.kiro/specs/agentic-kernel-testing/requirements.md) - What the system does
- [Design](.kiro/specs/agentic-kernel-testing/design.md) - How it's built
- [Tasks](.kiro/specs/agentic-kernel-testing/tasks.md) - Implementation plan

### 2. Start Development

Follow the implementation tasks in order:

```bash
# Task 1: ✓ Project structure (completed)
# Task 2: Implement core data models
# Task 3: Implement code analysis
# ...
```

### 3. Run Development Commands

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-property
make test-integration

# Check code quality
make lint
make format

# Generate coverage report
make coverage
```

## Common Commands

```bash
# Development
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest -k test_name            # Run specific test
pytest --cov=.                 # With coverage

# Code Quality
black .                        # Format code
isort .                        # Sort imports
mypy .                         # Type checking
pylint module_name             # Lint code

# Project Management
python3 verify_setup.py        # Verify installation
pip list                       # Show installed packages
```

## Troubleshooting

### Import Errors

```bash
# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

### Missing Dependencies

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Test Failures

```bash
# Run tests with more detail
pytest -vv --tb=long

# Run a single test file
pytest tests/unit/test_config.py -v
```

## Getting Help

- **Documentation**: Check `docs/` directory
- **Specifications**: Review `.kiro/specs/` for detailed requirements
- **Issues**: Open an issue on the repository
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## What's Next?

The project is currently in active development. **Task 1 is complete** (Dec 3, 2025), and we're ready for the next phase:

### Upcoming Tasks

1. **Task 2**: Implement core data models and interfaces
   - Define TestCase, TestResult, CodeAnalysis, FailureAnalysis, HardwareConfig, Environment
   - Implement serialization/deserialization
   - Create validation logic
   - Write unit tests for data models

2. **Task 3**: Implement code analysis and diff parsing
   - Git integration for detecting code changes
   - Diff parser for extracting changed files and functions
   - AST analyzer for identifying affected subsystems
   - Write property tests for subsystem identification

3. **Task 4**: Implement AI test generator core
   - LLM API integration (OpenAI, Anthropic, Amazon Q via Bedrock)
   - Code-to-prompt conversion
   - Test case template system
   - Write property tests for test generation

Follow the [Implementation Tasks](../.kiro/specs/agentic-kernel-testing/tasks.md) for the complete 50-task roadmap with comprehensive testing.

## Resources

- [Installation Guide](INSTALLATION.md) - Detailed installation instructions
- [Architecture Overview](ARCHITECTURE.md) - System architecture
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Requirements](../.kiro/specs/agentic-kernel-testing/requirements.md) - System requirements
- [Design](../.kiro/specs/agentic-kernel-testing/design.md) - Design document
