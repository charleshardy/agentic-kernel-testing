#!/bin/bash
set -e

# Agentic AI Testing System - Environment Setup Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Default values
ENVIRONMENT="development"
SKIP_DEPS=false
SKIP_CONFIG=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --skip-config)
            SKIP_CONFIG=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -e, --environment ENV    Environment to setup (development, staging, production)"
            echo "  --skip-deps             Skip dependency installation"
            echo "  --skip-config           Skip configuration setup"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log "Setting up Agentic AI Testing System for $ENVIRONMENT environment"

# Check if running as root (not recommended)
if [[ $EUID -eq 0 ]]; then
    warn "Running as root is not recommended for security reasons"
fi

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    directories=(
        "artifacts"
        "logs"
        "coverage_data"
        "performance_data"
        "security_reports"
        "generated_tests"
        "test_templates"
        "environments"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
}

# Install system dependencies
install_system_deps() {
    if [[ "$SKIP_DEPS" == "true" ]]; then
        log "Skipping dependency installation"
        return
    fi
    
    log "Installing system dependencies..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                git \
                curl \
                wget \
                build-essential \
                gcc \
                g++ \
                lcov \
                gcov \
                qemu-system-x86 \
                qemu-system-arm \
                qemu-utils \
                kvm \
                libvirt-daemon-system \
                libvirt-clients \
                bridge-utils \
                ssh \
                telnet \
                docker.io \
                docker-compose
        elif command -v yum &> /dev/null; then
            # RHEL/CentOS/Fedora
            sudo yum update -y
            sudo yum install -y \
                python3 \
                python3-pip \
                git \
                curl \
                wget \
                gcc \
                gcc-c++ \
                lcov \
                qemu-kvm \
                qemu-img \
                libvirt \
                libvirt-client \
                bridge-utils \
                openssh-clients \
                telnet \
                docker \
                docker-compose
        else
            warn "Unsupported Linux distribution. Please install dependencies manually."
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew update
            brew install \
                python3 \
                git \
                curl \
                wget \
                gcc \
                lcov \
                qemu \
                docker \
                docker-compose
        else
            warn "Homebrew not found. Please install dependencies manually."
        fi
    else
        warn "Unsupported operating system: $OSTYPE"
    fi
}

# Setup Python environment
setup_python_env() {
    log "Setting up Python environment..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    required_version="3.10"
    
    if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
        error "Python $required_version or higher is required. Found: $python_version"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    if [[ -f "requirements.txt" ]]; then
        log "Installing Python dependencies..."
        pip install -r requirements.txt
    fi
    
    # Install development dependencies if in development mode
    if [[ "$ENVIRONMENT" == "development" ]]; then
        if [[ -f "requirements-dev.txt" ]]; then
            pip install -r requirements-dev.txt
        fi
    fi
}

# Setup configuration
setup_configuration() {
    if [[ "$SKIP_CONFIG" == "true" ]]; then
        log "Skipping configuration setup"
        return
    fi
    
    log "Setting up configuration for $ENVIRONMENT environment..."
    
    # Copy environment-specific configuration
    env_file="config/environments/${ENVIRONMENT}.env"
    if [[ -f "$env_file" ]]; then
        cp "$env_file" .env
        log "Copied $env_file to .env"
    else
        warn "Environment file $env_file not found. Using .env.example"
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
        else
            error ".env.example not found"
            exit 1
        fi
    fi
    
    # Generate secret key if not set
    if ! grep -q "API__SECRET_KEY=" .env || grep -q "your-secret-key-change-in-production" .env; then
        log "Generating API secret key..."
        secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i "s/API__SECRET_KEY=.*/API__SECRET_KEY=$secret_key/" .env
    fi
    
    # Prompt for LLM API key if not set
    if ! grep -q "LLM__API_KEY=" .env || grep -q "your-.*-api-key" .env; then
        warn "LLM API key not configured"
        echo "Please set your LLM API key in .env file:"
        echo "  LLM__API_KEY=your-actual-api-key"
    fi
}

# Setup Docker environment
setup_docker() {
    log "Setting up Docker environment..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        warn "Docker is not running. Please start Docker daemon."
        return
    fi
    
    # Check if user is in docker group (Linux only)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if ! groups | grep -q docker; then
            warn "User is not in docker group. Run: sudo usermod -aG docker \$USER"
            warn "Then log out and log back in."
        fi
    fi
    
    # Build Docker images for development
    if [[ "$ENVIRONMENT" == "development" ]]; then
        log "Building Docker images for development..."
        docker-compose build --no-cache
    fi
}

# Initialize database
init_database() {
    log "Initializing database..."
    
    # Check if using SQLite (development) or PostgreSQL
    if grep -q "DATABASE__TYPE=sqlite" .env; then
        log "Using SQLite database"
        # SQLite database will be created automatically
    else
        log "Using PostgreSQL database"
        # Start PostgreSQL container if using Docker Compose
        if [[ -f "docker-compose.yml" ]]; then
            docker-compose up -d db
            log "Waiting for database to be ready..."
            sleep 10
        fi
    fi
    
    # Run database migrations (if migration script exists)
    if [[ -f "database/migrations.py" ]]; then
        log "Running database migrations..."
        python3 database/migrations.py
    fi
}

# Validate configuration
validate_config() {
    log "Validating configuration..."
    
    if [[ -f "scripts/validate-config.py" ]]; then
        python3 scripts/validate-config.py
        if [[ $? -ne 0 ]]; then
            error "Configuration validation failed"
            exit 1
        fi
    else
        warn "Configuration validation script not found"
    fi
}

# Run tests to verify setup
run_tests() {
    log "Running basic tests to verify setup..."
    
    # Run a simple import test
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from config.settings import get_settings
    settings = get_settings()
    print('✅ Configuration loaded successfully')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"
    
    # Run unit tests if available
    if [[ -d "tests" ]]; then
        log "Running unit tests..."
        python3 -m pytest tests/unit/ -v --tb=short || warn "Some tests failed"
    fi
}

# Print setup summary
print_summary() {
    log "Setup completed for $ENVIRONMENT environment"
    echo
    info "Next steps:"
    echo "1. Review and update .env file with your configuration"
    echo "2. Set your LLM API key: LLM__API_KEY=your-api-key"
    echo "3. Start the system:"
    echo "   - Docker Compose: docker-compose up -d"
    echo "   - Development: python3 api/server.py"
    echo "4. Access the system:"
    echo "   - API: http://localhost:8000"
    echo "   - Dashboard: http://localhost:3000"
    echo "   - Health check: curl http://localhost:8000/api/v1/health"
    echo
    info "For more information, see docs/DEPLOYMENT.md"
}

# Main setup function
main() {
    create_directories
    install_system_deps
    setup_python_env
    setup_configuration
    setup_docker
    init_database
    validate_config
    run_tests
    print_summary
}

# Run main function
main