.PHONY: install test test-unit test-property test-integration coverage lint format clean help docker-build docker-run deploy-dev deploy-staging deploy-prod k8s-deploy validate-config setup-env kernel-monitor kernel-setup

help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests"
	@echo "  make test-property    - Run property-based tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make coverage         - Run tests with coverage"
	@echo "  make lint             - Run linters"
	@echo "  make format           - Format code"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make validate-config  - Validate configuration"
	@echo "  make setup-env        - Setup development environment"
	@echo ""
	@echo "Docker Compose:"
	@echo "  make docker-build     - Build Docker images"
	@echo "  make docker-run       - Run with Docker Compose"
	@echo "  make deploy-dev       - Deploy development environment"
	@echo "  make deploy-staging   - Deploy staging environment"
	@echo "  make deploy-prod      - Deploy production environment"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-build        - Build and push K8s images"
	@echo "  make k8s-deploy       - Deploy to Kubernetes"
	@echo "  make k8s-status       - Show K8s deployment status"
	@echo "  make k8s-clean        - Clean K8s deployment"
	@echo ""
	@echo "Kernel Monitoring:"
	@echo "  make kernel-monitor   - Monitor Linux kernel for major changes"
	@echo "  make kernel-setup     - Setup kernel monitoring configuration"

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

# Configuration validation
validate-config:
	python3 scripts/validate-config.py

# Environment setup
setup-env:
	./scripts/setup-environment.sh --environment development

# Docker Compose targets
docker-build:
	docker-compose build --no-cache

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Environment-specific deployments
deploy-dev:
	cp config/environments/development.env .env
	docker-compose up -d
	@echo "Development environment deployed at http://localhost:8000"

deploy-staging:
	cp config/environments/staging.env .env
	docker-compose --profile monitoring up -d
	@echo "Staging environment deployed with monitoring"

deploy-prod:
	cp config/environments/production.env .env
	docker-compose --profile monitoring --profile cli up -d
	@echo "Production environment deployed"

# Kubernetes targets
k8s-build:
	cd k8s && ./deploy.sh build

k8s-deploy:
	cd k8s && ./deploy.sh deploy

k8s-full:
	cd k8s && ./deploy.sh full

k8s-status:
	cd k8s && ./deploy.sh status

k8s-clean:
	cd k8s && ./deploy.sh clean

# Health checks
health-check:
	@echo "Checking system health..."
	@curl -f http://localhost:8000/api/v1/health || echo "API not responding"
	@curl -f http://localhost:8001/health || echo "Orchestrator not responding"
	@curl -f http://localhost:8002/health || echo "Execution service not responding"
	@curl -f http://localhost:8003/health || echo "Analysis service not responding"
	@curl -f http://localhost:8004/health || echo "AI Generator not responding"

# Database operations
db-migrate:
	python3 database/migrations.py

db-backup:
	docker-compose exec db pg_dump -U postgres agentic_testing > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore:
	@echo "Usage: make db-restore BACKUP_FILE=backup_file.sql"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "Please specify BACKUP_FILE"; exit 1; fi
	docker-compose exec -T db psql -U postgres agentic_testing < $(BACKUP_FILE)

# Kernel monitoring targets
kernel-monitor:
	@echo "Monitoring Linux kernel for major changes..."
	python3 scripts/kernel-monitor.py --days 7 --email le.liu@windriver.com

kernel-setup:
	@echo "Setting up kernel monitoring configuration..."
	python3 scripts/kernel-monitor.py --setup-config

kernel-monitor-weekly:
	@echo "Running weekly kernel monitoring..."
	python3 scripts/kernel-monitor.py --days 7

kernel-monitor-daily:
	@echo "Running daily kernel monitoring..."
	python3 scripts/kernel-monitor.py --days 1

# Quick start
quick-start: setup-env validate-config deploy-dev health-check
	@echo "Quick start completed! System is ready at http://localhost:8000"
