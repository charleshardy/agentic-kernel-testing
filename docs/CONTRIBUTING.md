# Contributing Guide

Thank you for your interest in contributing to the Agentic AI Testing System!

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/agentic-kernel-testing.git
   cd agentic-kernel-testing
   ```

2. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Follow the project structure and coding standards:

- Place new features in the appropriate module (`ai_generator`, `orchestrator`, etc.)
- Add tests for all new functionality
- Update documentation as needed

### 3. Write Tests

We use a dual testing approach:

#### Unit Tests

Place unit tests in `tests/unit/`:

```python
import pytest

@pytest.mark.unit
def test_your_feature():
    """Test description."""
    # Test implementation
    assert result == expected
```

#### Property-Based Tests

Place property tests in `tests/property/`:

```python
from hypothesis import given, strategies as st
import pytest

@pytest.mark.property
@given(st.integers())
def test_property_holds(value):
    """Property description."""
    # Property test implementation
    assert property_holds(value)
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/property/

# Run with coverage
pytest --cov=. --cov-report=html
```

### 5. Code Quality Checks

```bash
# Format code
black .
isort .

# Type checking
mypy .

# Linting
pylint ai_generator orchestrator execution analysis integration
```

### 6. Commit Your Changes

Follow conventional commit format:

```bash
git add .
git commit -m "feat: add new test generation feature"
```

Commit types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Build or tooling changes

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use docstrings for all public functions and classes

Example:

```python
def analyze_code(diff: str, context: Optional[str] = None) -> CodeAnalysis:
    """Analyze code changes and generate insights.
    
    Args:
        diff: Git diff string containing code changes
        context: Optional additional context for analysis
        
    Returns:
        CodeAnalysis object with analysis results
        
    Raises:
        ValueError: If diff is empty or invalid
    """
    # Implementation
    pass
```

### Testing Standards

- All new features must have tests
- Aim for >80% code coverage
- Property-based tests should run 100+ iterations
- Tests should be independent and idempotent

### Documentation Standards

- Update README.md for user-facing changes
- Add docstrings to all public APIs
- Update design documents for architectural changes
- Include examples in documentation

## Project Structure

When adding new features, follow this structure:

```
module_name/
├── __init__.py          # Module exports
├── core.py              # Core functionality
├── models.py            # Data models
├── utils.py             # Utility functions
└── tests/
    ├── unit/
    │   └── test_module.py
    └── property/
        └── test_module_properties.py
```

## Spec-Driven Development

This project follows spec-driven development:

1. **Requirements**: Define what the system should do
2. **Design**: Specify how it will be implemented
3. **Tasks**: Break down into actionable steps
4. **Implementation**: Write code following the tasks

When adding major features:

1. Update or create requirements in `.kiro/specs/`
2. Update design document with architecture changes
3. Add tasks to the implementation plan
4. Implement following the task list

## Review Process

Pull requests will be reviewed for:

- **Correctness**: Does it work as intended?
- **Tests**: Are there adequate tests?
- **Code Quality**: Does it follow coding standards?
- **Documentation**: Is it properly documented?
- **Design**: Does it fit the architecture?

## Getting Help

- Check existing documentation in `docs/`
- Review specification files in `.kiro/specs/`
- Ask questions in pull request discussions
- Open an issue for clarification

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
