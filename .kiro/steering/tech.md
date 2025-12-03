# Technical Stack

## Language and Runtime

- **Python 3.10+**: Primary implementation language
- **Poetry/pip**: Dependency management

## Core Technologies

### AI and Machine Learning
- **LLM Integration**: OpenAI/Anthropic APIs for code analysis and test generation
- **Hypothesis**: Property-based testing framework

### Testing and Analysis
- **pytest**: Unit and integration testing framework
- **gcov/lcov**: Code coverage collection
- **Syzkaller**: Kernel fuzzing
- **Coccinelle**: Static analysis for vulnerability patterns
- **KASAN**: Kernel Address Sanitizer for memory errors
- **KTSAN**: Kernel Thread Sanitizer for race conditions

### Performance Tools
- **LMBench**: System call latency benchmarks
- **FIO**: I/O performance testing
- **Netperf**: Network throughput testing
- **perf**: Kernel profiling and flamegraph generation

### Virtualization and Hardware
- **QEMU**: Virtual machine environments for x86_64, ARM, RISC-V
- **KVM**: Hardware-accelerated virtualization
- **SSH**: Remote execution on physical hardware boards

### Data and APIs
- **PostgreSQL/SQLite**: Test results and metrics storage
- **FastAPI/Flask**: REST API for integrations
- **React/Vue**: Web dashboard frontend

### CI/CD Integration
- **GitHub Actions**: Version control webhooks
- **GitLab CI**: Pipeline integration
- **Jenkins**: Build system integration

### Deployment
- **Docker**: Containerization
- **Kubernetes**: Orchestration and scaling

## Project Structure

```
├── ai_generator/       # AI-powered test generation
├── orchestrator/       # Test scheduling and resource management
├── execution/          # Test runners and environment managers
├── analysis/           # Coverage, performance, security analysis
├── integration/        # CI/CD hooks and VCS integration
├── tests/             # Unit, property-based, and integration tests
├── docs/              # Documentation
└── .kiro/
    ├── specs/         # Feature specifications
    └── steering/      # AI assistant guidance
```

## Common Commands

### Development
```bash
# Install dependencies
poetry install

# Run unit tests
pytest tests/unit/

# Run property-based tests (100+ iterations)
pytest tests/property/ --hypothesis-iterations=100

# Run integration tests
pytest tests/integration/

# Run all tests
pytest
```

### Code Quality
```bash
# Type checking
mypy .

# Linting
pylint ai_generator orchestrator execution analysis integration

# Format code
black .
isort .
```

### Coverage
```bash
# Run tests with coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Running the System
```bash
# Start API server
python -m api.server

# Start web dashboard
cd dashboard && npm run dev

# CLI tool
python -m cli.main --help
```

### Docker
```bash
# Build containers
docker-compose build

# Run system
docker-compose up

# Run tests in container
docker-compose run test
```
