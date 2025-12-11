#!/bin/bash
set -e

# Agentic AI Testing System - Kubernetes Deployment Script

NAMESPACE="agentic-testing"
REGISTRY="your-registry.com"  # Replace with your container registry
VERSION="${VERSION:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        error "docker is not installed"
        exit 1
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log "Prerequisites check passed"
}

# Build and push Docker images
build_images() {
    log "Building Docker images..."
    
    # Build all service images
    services=("api" "ai-generator" "orchestrator" "execution" "analysis" "dashboard")
    
    for service in "${services[@]}"; do
        log "Building $service image..."
        
        if [ "$service" = "dashboard" ]; then
            docker build -t "${REGISTRY}/agentic-testing/${service}:${VERSION}" -f dashboard/Dockerfile dashboard/
        else
            docker build -t "${REGISTRY}/agentic-testing/${service}:${VERSION}" -f ${service}/Dockerfile .
        fi
        
        log "Pushing $service image..."
        docker push "${REGISTRY}/agentic-testing/${service}:${VERSION}"
    done
    
    log "All images built and pushed successfully"
}

# Deploy to Kubernetes
deploy_k8s() {
    log "Deploying to Kubernetes..."
    
    # Create namespace
    kubectl apply -f k8s/namespace.yaml
    
    # Apply storage resources first
    log "Creating storage resources..."
    kubectl apply -f k8s/storage.yaml
    
    # Apply configuration and secrets
    log "Creating configuration and secrets..."
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secrets.yaml
    
    # Deploy database and cache
    log "Deploying database and cache..."
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/redis.yaml
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/postgres -n $NAMESPACE
    
    # Deploy core services
    log "Deploying core services..."
    kubectl apply -f k8s/api.yaml
    kubectl apply -f k8s/ai-generator.yaml
    kubectl apply -f k8s/orchestrator.yaml
    kubectl apply -f k8s/execution.yaml
    kubectl apply -f k8s/analysis.yaml
    
    # Deploy dashboard
    log "Deploying dashboard..."
    kubectl apply -f k8s/dashboard.yaml
    
    # Deploy ingress
    log "Deploying ingress..."
    kubectl apply -f k8s/ingress.yaml
    
    # Wait for all deployments to be ready
    log "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/api -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=600s deployment/ai-generator -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=600s deployment/orchestrator -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=600s deployment/execution -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=600s deployment/analysis -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=600s deployment/dashboard -n $NAMESPACE
    
    log "Deployment completed successfully"
}

# Show deployment status
show_status() {
    log "Deployment Status:"
    echo
    kubectl get pods -n $NAMESPACE
    echo
    kubectl get services -n $NAMESPACE
    echo
    kubectl get ingress -n $NAMESPACE
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "check")
            check_prerequisites
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "deploy")
            check_prerequisites
            deploy_k8s
            show_status
            ;;
        "full")
            check_prerequisites
            build_images
            deploy_k8s
            show_status
            ;;
        "status")
            show_status
            ;;
        "clean")
            log "Cleaning up deployment..."
            kubectl delete namespace $NAMESPACE --ignore-not-found=true
            log "Cleanup completed"
            ;;
        *)
            echo "Usage: $0 {check|build|deploy|full|status|clean}"
            echo "  check  - Check prerequisites"
            echo "  build  - Build and push Docker images"
            echo "  deploy - Deploy to Kubernetes"
            echo "  full   - Build images and deploy"
            echo "  status - Show deployment status"
            echo "  clean  - Remove deployment"
            exit 1
            ;;
    esac
}

main "$@"