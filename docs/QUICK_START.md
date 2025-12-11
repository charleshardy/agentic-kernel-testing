# Quick Start Guide

Get the Agentic AI Testing System up and running in minutes.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Git
- 8GB+ RAM
- 20GB+ disk space

## 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd agentic-kernel-testing

# Quick setup (automated)
make quick-start
```

## 2. Manual Setup (Alternative)

If the automated setup doesn't work, follow these steps:

```bash
# Setup environment
./scripts/setup-environment.sh --environment development

# Configure environment variables
cp config/environments/development.env .env

# Edit .env file with your LLM API key
nano .env
# Set: LLM__API_KEY=your-openai-api-key

# Validate configuration
make validate-config

# Deploy with Docker Compose
make deploy-dev
```

## 3. Verify Installation

```bash
# Check system health
make health-check

# Or manually check each service
curl http://localhost:8000/api/v1/health  # API
curl http://localhost:8001/health         # Orchestrator
curl http://localhost:8002/health         # Execution
curl http://localhost:8003/health         # Analysis
curl http://localhost:8004/health         # AI Generator
```

## 4. Access the System

- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/api/v1/health
- **Grafana Monitoring**: http://localhost:3001 (admin/admin)

## 5. First Test Run

```bash
# Using CLI
docker-compose exec cli python -m cli.main test submit \
  --name "Hello World Test" \
  --type unit \
  --subsystem core

# Using API
curl -X POST http://localhost:8000/api/v1/tests \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hello World Test",
    "type": "unit",
    "subsystem": "core",
    "description": "First test run"
  }'
```

## 6. View Results

```bash
# Check test status
docker-compose exec cli python -m cli.main status list

# View logs
make docker-logs

# Check dashboard
open http://localhost:3000
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Permission errors**: Check Docker permissions
3. **Memory issues**: Increase Docker memory limit
4. **API key errors**: Verify LLM__API_KEY in .env

### Getting Help

```bash
# View logs
docker-compose logs <service-name>

# Check configuration
make validate-config

# Reset everything
make docker-clean
make deploy-dev
```

## Next Steps

- Read the [Deployment Guide](DEPLOYMENT.md) for production setup
- Check the [API Documentation](http://localhost:8000/docs)
- Explore the [CLI Commands](CLI.md)
- Configure [CI/CD Integration](INTEGRATION.md)

## Development Mode

For development with hot reloading:

```bash
# Install Python dependencies locally
make install

# Run services individually
python api/server.py --reload
python -m orchestrator.scheduler
python -m execution.test_runner
```

This gives you a fully functional Agentic AI Testing System ready for kernel and BSP testing!