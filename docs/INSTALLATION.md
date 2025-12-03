# Installation Guide

## System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, Debian 11+, or similar)
- **Python**: 3.10 or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Disk Space**: 10GB+ for system and artifacts
- **Network**: Internet connection for LLM API access

## Installation Methods

### Method 1: Using Poetry (Recommended)

Poetry provides better dependency management and virtual environment handling.

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Method 2: Using pip

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

### Method 3: Using Docker

```bash
# Build the Docker image
docker-compose build

# Run the system
docker-compose up
```

## Configuration

### 1. Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# LLM Configuration
LLM__PROVIDER=openai
LLM__API_KEY=your-api-key-here
LLM__MODEL=gpt-4

# Database Configuration
DATABASE__TYPE=sqlite  # or postgresql
DATABASE__NAME=agentic_testing

# Execution Configuration
EXECUTION__MAX_PARALLEL_TESTS=10
EXECUTION__VIRTUAL_ENV_ENABLED=true
```

### 2. Database Setup

#### SQLite (Default)

No additional setup required. The database file will be created automatically.

#### PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE agentic_testing;
CREATE USER agentic_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE agentic_testing TO agentic_user;
\q

# Update .env
DATABASE__TYPE=postgresql
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=agentic_testing
DATABASE__USER=agentic_user
DATABASE__PASSWORD=your_password
```

### 3. LLM API Setup

#### OpenAI

1. Sign up at https://platform.openai.com/
2. Create an API key
3. Add to `.env`: `LLM__API_KEY=sk-...`

#### Anthropic

1. Sign up at https://console.anthropic.com/
2. Create an API key
3. Update `.env`:
   ```
   LLM__PROVIDER=anthropic
   LLM__API_KEY=sk-ant-...
   LLM__MODEL=claude-3-opus-20240229
   ```

## Verification

Run the verification script to ensure everything is set up correctly:

```bash
python3 verify_setup.py
```

Expected output:
```
============================================================
Agentic AI Testing System - Setup Verification
============================================================
Checking directory structure...
  ✓ ai_generator
  ✓ orchestrator
  ...

✓ All checks passed! Project structure is set up correctly.
```

## Running Tests

Verify the installation by running the test suite:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest tests/unit/
pytest tests/property/
pytest tests/integration/
```

## Troubleshooting

### Import Errors

If you encounter import errors:

```bash
# Ensure you're in the project root directory
cd /path/to/agentic-kernel-testing

# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e .
```

### Dependency Conflicts

```bash
# Clear pip cache
pip cache purge

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Poetry Issues

```bash
# Clear Poetry cache
poetry cache clear pypi --all

# Reinstall dependencies
poetry install --no-cache
```

## Next Steps

After successful installation:

1. Review the [Requirements](.kiro/specs/agentic-kernel-testing/requirements.md)
2. Read the [Design Document](.kiro/specs/agentic-kernel-testing/design.md)
3. Check the [Implementation Tasks](.kiro/specs/agentic-kernel-testing/tasks.md)
4. Start implementing features following the task list

## Additional Tools (Optional)

### QEMU for Virtual Environments

```bash
sudo apt-get install qemu-system-x86 qemu-system-arm qemu-system-misc
```

### Kernel Testing Tools

```bash
# Syzkaller for fuzzing
git clone https://github.com/google/syzkaller
cd syzkaller
make

# Coccinelle for static analysis
sudo apt-get install coccinelle
```

### Performance Tools

```bash
sudo apt-get install linux-tools-generic fio netperf
```

## Support

For issues or questions:
- Check the documentation in `docs/`
- Review the specification files in `.kiro/specs/`
- Open an issue on the project repository
