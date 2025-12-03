.PHONY: install test test-unit test-property test-integration coverage lint format clean help

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests"
	@echo "  make test-property    - Run property-based tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make coverage         - Run tests with coverage"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo "  make clean            - Clean build artifacts"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-property:
	pytest tests/property/ -v --hypothesis-show-statistics

test-integration:
	pytest tests/integration/ -v

coverage:
	pytest --cov=. --cov-report=html --cov-report=term

lint:
	pylint ai_generator orchestrator execution analysis integration
	mypy .

format:
	black .
	isort .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ .hypothesis/
