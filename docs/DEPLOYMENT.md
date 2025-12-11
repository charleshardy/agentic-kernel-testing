# Deployment Guide

This guide covers deploying the Agentic AI Testing System using Docker Compose and Kubernetes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration Management](#configuration-management)
- [Environment-Specific Deployments](#environment-specific-deployments)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: Minimum 8 cores (16 cores recommended for production)
- **Memory**: Minimum 16GB RAM (32GB recommended for production)
- **Storage**: Minimum 100GB available disk space
- **Network**: Stable internet connection for LLM API calls

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- kubectl configured for your cluster
- Git

### Hardware Requirements (for execution nodes)

- **Virtualization Support**: Intel VT-x or AMD-V
- **KVM Support**: For hardware-accelerated virtualization
- **Network Access**: SSH access to physical hardware boards (if using physical testing)

## Docker Compose Deployment

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd agentic-kernel-testing
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the system**:
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**:
   ```bash
   docker-compose ps
   curl http://localhost:8000/api/v1/health
   ```

### Service Architecture

The Docker Compose deployment includes:

- **api**: Main API server (port 8000)
- **ai-generator**: AI test generation service (port 8004)
- **orchestrator**: Test scheduling service (port 8001)
- **execution**: Test execution service (port 8002)
- **analysis**: Analysis and reporting service (port 8003)
- **dashboard**: Web UI (port 3000)
- **db**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)
- **nginx**: Reverse proxy (ports 80, 443)

### Environment-Specific Deployment

#### Development
```bash
# Use development configuration
cp config/environments/development.env .env
docker-compose up -d

# Enable CLI service
docker-compose --profile cli up -d
```

#### Staging
```bash
# Use staging configuration
cp config/environments/staging.env .env
docker-compose up -d

# Enable monitoring
docker-compose --profile monitoring up -d
```

#### Production
```bash
# Use production configuration
cp config/environments/production.env .env
docker-compose up -d

# Enable all services
docker-compose --profile monitoring --profile cli up -d
```

### Scaling Services

Scale specific services based on load:

```bash
# Scale execution workers
docker-compose up -d --scale execution=5

# Scale AI generators
docker-compose up -d --scale ai-generator=3

# Scale analysis services
docker-compose up -d --scale analysis=2
```

## Kubernetes Deployment

### Prerequisites

1. **Kubernetes cluster** with:
   - Minimum 3 nodes
   - Container runtime (Docker/containerd)
   - Ingress controller (nginx-ingress recommended)
   - Storage classes configured

2. **Container registry** access:
   ```bash
   # Configure registry
   export REGISTRY="your-registry.com"
   docker login $REGISTRY
   ```

### Deployment Steps

1. **Build and push images**:
   ```bash
   cd k8s
   ./deploy.sh build
   ```

2. **Configure secrets**:
   ```bash
   # Edit k8s/secrets.yaml with base64-encoded values
   echo -n "your-api-key" | base64
   ```

3. **Deploy to cluster**:
   ```bash
   ./deploy.sh deploy
   ```

4. **Verify deployment**:
   ```bash
   ./deploy.sh status
   ```

### Kubernetes Architecture

The Kubernetes deployment provides:

- **High Availability**: Multiple replicas of each service
- **Auto-scaling**: Horizontal Pod Autoscaler (HPA) support
- **Load Balancing**: Service-based load balancing
- **Persistent Storage**: Shared storage for artifacts and data
- **Ingress**: External access through ingress controller

### Resource Requirements

| Service | Replicas | CPU Request | Memory Request | CPU Limit | Memory Limit |
|---------|----------|-------------|----------------|-----------|--------------|
| API | 2 | 250m | 512Mi | 500m | 1Gi |
| AI Generator | 2 | 500m | 1Gi | 1000m | 2Gi |
| Orchestrator | 1 | 250m | 512Mi | 500m | 1Gi |
| Execution | 3 | 1000m | 2Gi | 2000m | 4Gi |
| Analysis | 2 | 500m | 1Gi | 1000m | 2Gi |
| Dashboard | 2 | 100m | 128Mi | 200m | 256Mi |

### Storage Configuration

The system uses multiple storage classes:

- **nfs**: Shared storage for artifacts, logs, and data
- **fast-ssd**: High-performance storage for VM images
- **standard**: Standard storage for databases

Configure storage classes in your cluster:

```yaml
# Example NFS storage class
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server.example.com
  share: /exports/agentic-testing
```

## Configuration Management

### Environment Variables

The system uses hierarchical configuration:

1. **Default values** in `config/settings.py`
2. **Environment files** in `config/environments/`
3. **Environment variables** (highest priority)

### Key Configuration Sections

#### LLM Configuration
```bash
LLM__PROVIDER=openai          # openai, anthropic, amazon-bedrock
LLM__API_KEY=your-api-key
LLM__MODEL=gpt-4
LLM__TEMPERATURE=0.7
```

#### Database Configuration
```bash
DATABASE__TYPE=postgresql     # sqlite, postgresql
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=agentic_testing
DATABASE__USER=postgres
DATABASE__PASSWORD=your-password
```

#### Execution Configuration
```bash
EXECUTION__MAX_PARALLEL_TESTS=10
EXECUTION__TEST_TIMEOUT=300
EXECUTION__VIRTUAL_ENV_ENABLED=true
EXECUTION__PHYSICAL_HW_ENABLED=false
```

### Secrets Management

#### Docker Compose
Store secrets in `.env` file (not committed to git):
```bash
API_SECRET_KEY=your-secret-key
DB_PASSWORD=your-db-password
LLM__API_KEY=your-llm-api-key
```

#### Kubernetes
Use Kubernetes secrets:
```bash
kubectl create secret generic agentic-secrets \
  --from-literal=API__SECRET_KEY=your-secret-key \
  --from-literal=DATABASE__PASSWORD=your-db-password \
  --from-literal=LLM__API_KEY=your-llm-api-key \
  -n agentic-testing
```

## Environment-Specific Deployments

### Development Environment

**Characteristics**:
- Single-node deployment
- SQLite database
- Reduced resource limits
- Debug logging enabled
- All services on localhost

**Deployment**:
```bash
# Docker Compose
cp config/environments/development.env .env
docker-compose up -d

# Access services
curl http://localhost:8000/api/v1/health
open http://localhost:3000
```

### Staging Environment

**Characteristics**:
- Multi-node deployment
- PostgreSQL database
- Production-like configuration
- Monitoring enabled
- Limited external access

**Deployment**:
```bash
# Kubernetes
export ENVIRONMENT=staging
./k8s/deploy.sh full
```

### Production Environment

**Characteristics**:
- High availability
- Auto-scaling
- Full monitoring and alerting
- Security hardening
- External ingress

**Deployment**:
```bash
# Kubernetes with production configuration
export ENVIRONMENT=production
./k8s/deploy.sh full
```

## Monitoring and Logging

### Metrics Collection

The system exposes Prometheus metrics:

- **API metrics**: Request rates, response times, error rates
- **Execution metrics**: Test execution times, success rates
- **Resource metrics**: CPU, memory, disk usage
- **Business metrics**: Test generation rates, coverage trends

### Log Aggregation

Logs are structured and can be aggregated using:

- **Docker Compose**: Local log files in `./logs/`
- **Kubernetes**: Centralized logging with Fluentd/Fluent Bit

### Grafana Dashboards

Pre-configured dashboards for:

- System overview
- Test execution metrics
- Performance trends
- Error rates and alerts

Access Grafana:
- **Docker Compose**: http://localhost:3001
- **Kubernetes**: https://grafana.agentic-testing.example.com

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

**Symptoms**: Container exits immediately or fails health checks

**Solutions**:
```bash
# Check logs
docker-compose logs <service-name>
kubectl logs deployment/<service-name> -n agentic-testing

# Check configuration
docker-compose config
kubectl describe deployment <service-name> -n agentic-testing
```

#### 2. Database Connection Issues

**Symptoms**: Services can't connect to database

**Solutions**:
```bash
# Verify database is running
docker-compose ps db
kubectl get pods -l app=postgres -n agentic-testing

# Check connection string
docker-compose exec api python -c "from config.settings import get_settings; print(get_settings().database.connection_string)"

# Test database connectivity
docker-compose exec api python -c "import psycopg2; psycopg2.connect('postgresql://postgres:password@db:5432/agentic_testing')"
```

#### 3. LLM API Issues

**Symptoms**: Test generation fails or times out

**Solutions**:
```bash
# Verify API key
docker-compose exec ai-generator python -c "import openai; openai.api_key='your-key'; print(openai.Model.list())"

# Check rate limits
curl -H "Authorization: Bearer your-api-key" https://api.openai.com/v1/models

# Monitor API usage
docker-compose logs ai-generator | grep -i "rate limit"
```

#### 4. Storage Issues

**Symptoms**: Pods stuck in pending state, storage errors

**Solutions**:
```bash
# Check storage classes
kubectl get storageclass

# Check PVC status
kubectl get pvc -n agentic-testing

# Check available storage
df -h /var/lib/docker  # Docker Compose
kubectl describe pv    # Kubernetes
```

### Performance Tuning

#### Resource Optimization

1. **CPU-bound services** (AI Generator, Analysis):
   - Increase CPU limits
   - Use CPU-optimized instance types

2. **Memory-bound services** (Execution):
   - Increase memory limits
   - Use memory-optimized instance types

3. **I/O-bound services** (Database, Storage):
   - Use SSD storage
   - Optimize database configuration

#### Scaling Guidelines

- **Horizontal scaling**: Add more replicas for stateless services
- **Vertical scaling**: Increase resources for resource-intensive services
- **Auto-scaling**: Configure HPA based on CPU/memory metrics

### Health Checks

All services provide health check endpoints:

```bash
# API health
curl http://localhost:8000/api/v1/health

# Service-specific health
curl http://localhost:8001/health  # Orchestrator
curl http://localhost:8002/health  # Execution
curl http://localhost:8003/health  # Analysis
curl http://localhost:8004/health  # AI Generator
```

### Backup and Recovery

#### Database Backup

```bash
# Docker Compose
docker-compose exec db pg_dump -U postgres agentic_testing > backup.sql

# Kubernetes
kubectl exec deployment/postgres -n agentic-testing -- pg_dump -U postgres agentic_testing > backup.sql
```

#### Artifact Backup

```bash
# Backup artifacts and logs
tar -czf artifacts-backup.tar.gz ./artifacts ./logs ./coverage_data
```

#### Recovery

```bash
# Restore database
docker-compose exec -T db psql -U postgres agentic_testing < backup.sql

# Restore artifacts
tar -xzf artifacts-backup.tar.gz
```

## Security Considerations

### Network Security

- Use TLS/SSL for all external communications
- Implement network policies in Kubernetes
- Restrict database access to application services only

### Secrets Management

- Never commit secrets to version control
- Use Kubernetes secrets or external secret management
- Rotate secrets regularly

### Container Security

- Use non-root users in containers
- Scan images for vulnerabilities
- Keep base images updated

### API Security

- Implement authentication and authorization
- Use rate limiting
- Validate all inputs
- Enable CORS only for trusted origins

For additional support, please refer to the project documentation or create an issue in the repository.