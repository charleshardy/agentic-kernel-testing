# Agentic AI Testing System for Linux Kernel and BSP

An autonomous AI-powered testing platform that intelligently tests Linux kernels and Board Support Packages (BSPs) across diverse hardware configurations. The system leverages Large Language Models to generate test cases, analyze failures, and provide actionable feedback to developers.

**Project Goal:** Improve kernel and BSP quality through comprehensive, automated testing that adapts to code changes and discovers edge cases that traditional testing might miss.

---

## 📚 Documentation

### Core Documentation
- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running in minutes
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design and technical architecture
- **[Installation Guide](docs/INSTALLATION.md)** - Detailed installation instructions
- **[Fault Detection Guide](docs/FAULT_DETECTION_GUIDE.md)** - Comprehensive fault detection and monitoring
- **[Contributing Guidelines](docs/CONTRIBUTING.md)** - How to contribute to the project
- **[Complete Overview](docs/CONFLUENCE_PAGE.md)** - Comprehensive project documentation
- **[Changelog](CHANGELOG.md)** - Project updates and version history

### LLM Provider Integration
- **[Amazon Q & Kiro Integration](docs/AMAZON_Q_AND_KIRO_INTEGRATION.md)** - Using Amazon Q Developer and Kiro AI
- **[SSO Authentication Guide](docs/SSO_AUTHENTICATION_GUIDE.md)** - Complete SSO setup and usage
- **[Quick Start: Amazon Q & Kiro](QUICK_START_AMAZON_Q_KIRO.md)** - 3-step setup guide
- **[SSO Quick Reference](SSO_QUICK_REFERENCE.md)** - SSO authentication cheat sheet

### Specifications
- [Requirements Document](.kiro/specs/agentic-kernel-testing/requirements.md) - Detailed system requirements
- [Design Document](.kiro/specs/agentic-kernel-testing/design.md) - Architecture and design decisions
- [Implementation Tasks](.kiro/specs/agentic-kernel-testing/tasks.md) - 50 tasks covering all system components

---

## 🚀 Recent Updates

**Latest:** December 5, 2025
- ✅ **Task 13 Complete:** Concurrency Testing Support
  - Thread scheduling variation system with 4 strategies (RANDOM, ROUND_ROBIN, PRIORITY_BASED, STRESS)
  - Timing variation injector for race condition detection
  - Multiple execution runs with different thread schedules
  - Execution order tracking and variation analysis
  - Race condition, deadlock, and data race detection
  - Seed-based reproducibility for debugging
  - High-level ConcurrencyTestRunner interface
  - 9 property-based tests (30-50 iterations each) - All passing ✅
  - Validates Requirements 3.3 and Property 13
- ✅ **Task 12 Complete:** Fault Detection and Monitoring
  - Kernel crash detector (panics, oops, NULL pointer dereferences, GPF)
  - Hang detector with timeout monitoring and log-based detection
  - Memory leak detector with KASAN integration (use-after-free, double-free, out-of-bounds)
  - Data corruption detector (checksum errors, filesystem corruption, ECC errors)
  - Unified fault detection system coordinating all detectors
  - Stack trace extraction and crash type classification
  - Comprehensive statistics tracking
  - 9 property-based tests (100+ iterations each) - All passing ✅
  - Validates Requirements 3.2
- ✅ **Task 8 Complete:** Physical Hardware Lab Interface
  - Hardware reservation system with time-based expiration
  - SSH-based test execution on physical boards
  - Serial console (telnet) test execution for early boot and debugging
  - **Bootloader deployment and verification (U-Boot, GRUB, UEFI)**
    - TFTP, storage (USB/SD/eMMC), and serial console deployment methods
    - Comprehensive verification with 5 checks: version, commands, environment, boot script, kernel loading
    - Support for custom bootloaders with flexible configuration
  - Power control integration (PDU, IPMI, manual)
  - Comprehensive health checks (SSH, disk, memory, uptime, kernel version, serial console)
  - Maintenance mode management
  - 30+ unit tests - All passing ✅
  - Validates Requirements 2.1, 2.3
- ✅ **Task 7 Complete:** Environment Manager for virtual environments (QEMU/KVM)
- ✅ **Task 6 Complete:** Hardware Configuration Management
- ✅ **Task 5 Complete:** Test case organization and summarization
- ✅ **Task 4 Complete:** AI Test Generator Core with Multi-Provider Support
  - OpenAI, Anthropic, Amazon Bedrock integration
  - **Amazon Q Developer Pro integration**
  - **Kiro AI integration**
  - **SSO Authentication Support (AWS SSO & OAuth2)**
  - LLM provider abstraction layer with unified interface
  - Automatic retry with exponential backoff
  - Test case validation and template system
  - 16 property-based tests (100+ iterations each) - All passing ✅
  - 5 integration tests - All passing ✅
- ✅ **Task 3 Complete:** Code analysis and diff parsing with subsystem identification
- ✅ **Task 2 Complete:** Core data models and interfaces with comprehensive validation
- ✅ **Task 1 Complete:** Project structure and core infrastructure
- ✅ **Task 11 Complete:** Fault injection system
- ✅ **Task 10 Complete:** Compatibility matrix generator
- ✅ **Task 9 Complete:** Test execution engine
- ✅ **Task 13 Complete:** Concurrency testing support
- ✅ **Testing Framework:** pytest and Hypothesis configured with 149+ tests passing
- ✅ **Configuration System:** Comprehensive settings system with pydantic-settings
- 📋 **Ready for Task 14:** Reproducible test case generation

---

## Core Capabilities

### 🤖 Autonomous Test Generation
AI agents analyze code changes and automatically generate targeted test cases covering normal usage, boundary conditions, and error paths. Generates 10+ distinct test cases per modified function within 5 minutes.

### 🖥️ Multi-Hardware Testing
Execute tests across virtual environments (QEMU, KVM) and physical hardware boards to ensure compatibility across x86_64, ARM, and RISC-V architectures. Supports SSH-based execution, serial console (telnet) access for early boot testing and kernel debugging, and bootloader deployment/verification (U-Boot, GRUB, UEFI) for pre-boot testing.

### 💥 Intelligent Fault Injection & Concurrency Testing
Stress testing with memory failures, I/O errors, and timing variations to discover edge cases and race conditions. Advanced concurrency testing varies thread scheduling and timing across multiple runs to expose race conditions, deadlocks, and data races. Detects crashes, hangs, memory leaks, and data corruption.

### 🔍 Root Cause Analysis
AI-powered failure analysis that correlates issues with code changes, groups related failures, and provides suggested fixes with references to similar historical issues.

### 🔒 Security Testing
Automated fuzzing and static analysis to detect vulnerabilities before production. Includes buffer overflows, use-after-free, and integer overflow detection.

### ⚡ Performance Monitoring
Continuous performance benchmarking with regression detection and profiling. Tracks throughput, latency, and resource utilization with commit-level attribution.

### 🔄 CI/CD Integration
Seamless integration with GitHub, GitLab, and Jenkins. Automatic test triggering on commits, PRs, and branch updates with real-time status reporting.

---

## Target Users

| User Role | Use Case |
|-----------|----------|
| **Kernel Developers** | Validate code changes without manually writing extensive tests |
| **BSP Maintainers** | Ensure hardware compatibility across different boards and architectures |
| **QA Engineers** | Discover edge cases through intelligent fault injection |
| **Security Researchers** | Identify vulnerabilities before production |
| **Performance Engineers** | Track and prevent performance regressions |
| **CI/CD Administrators** | Automate testing workflows in development pipelines |

## Technology Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.10+ |
| **AI/ML** | OpenAI (GPT-4), Anthropic (Claude), Amazon Bedrock, **Amazon Q Developer Pro**, **Kiro AI**, Hypothesis (property-based testing) |
| **Authentication** | **AWS SSO/IAM Identity Center**, **OAuth2/OIDC**, API Keys, AWS CLI Profiles |
| **Testing** | pytest, gcov/lcov, Syzkaller (fuzzing), Coccinelle (static analysis), KASAN, KTSAN |
| **Virtualization** | QEMU, KVM, SSH for physical hardware |
| **Performance** | LMBench, FIO, Netperf, perf |
| **Data** | PostgreSQL/SQLite, FastAPI/Flask |
| **Frontend** | React/Vue for web dashboard |
| **Deployment** | Docker, Kubernetes |

## Project Structure

```
├── ai_generator/       # AI-powered test generation (✅ Structure created)
├── orchestrator/       # Test scheduling and resource management (✅ Structure created)
├── execution/          # Test runners and environment managers (✅ Structure created)
├── analysis/           # Coverage, performance, security analysis (✅ Structure created)
├── integration/        # CI/CD hooks and VCS integration (✅ Structure created)
├── api/               # REST API server
├── dashboard/         # Web UI for monitoring
├── cli/               # Command-line interface
├── config/            # Configuration management (✅ Settings system implemented)
├── tests/             # Unit, property-based, and integration tests (✅ Framework configured)
├── docs/              # Comprehensive documentation (✅ Created)
└── .kiro/
    ├── specs/         # Feature specifications (✅ Complete)
    └── steering/      # AI assistant guidance (✅ Complete)
```

## LLM Provider Support

The system supports multiple LLM providers for AI-powered test generation:

| Provider | Authentication | Best For |
|----------|---------------|----------|
| **Amazon Q Developer** | AWS SSO, CLI Profile, API Keys | AWS environments, enterprise security |
| **Kiro AI** | OAuth2 SSO, API Keys | IDE integration, fast iteration |
| OpenAI | API Keys | General purpose, proven reliability |
| Anthropic | API Keys | Long context, detailed analysis |
| Amazon Bedrock | AWS Credentials | AWS-native, multiple models |

### Quick Setup

**Amazon Q with SSO:**
```bash
aws configure sso
aws sso login --profile my-sso-profile
```

**Kiro with SSO:**
```bash
export KIRO_CLIENT_ID="your-client-id"
export KIRO_CLIENT_SECRET="your-client-secret"
```

See [SSO Quick Reference](SSO_QUICK_REFERENCE.md) for complete setup.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Poetry or pip for dependency management
- Docker (optional, for containerized deployment)
- LLM Provider credentials (Amazon Q, Kiro, OpenAI, or Anthropic)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agentic-kernel-testing
   ```

2. **Install dependencies**
   ```bash
   # Using Poetry (recommended)
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   
   # Or install in development mode
   pip install -e ".[dev]"
   ```

3. **Configure environment**
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit .env with your settings (API keys, database config, etc.)
   nano .env
   ```

4. **Verify setup**
   ```bash
   # Run verification script
   python3 verify_setup.py
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit/

# Run property-based tests (100+ iterations)
pytest tests/property/ --hypothesis-iterations=100

# Run with coverage
pytest --cov=. --cov-report=html
```

## Development

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

### Running the System

```bash
# Start API server
python -m api.server

# Start web dashboard
cd dashboard && npm run dev

# CLI tool
python -m cli.main --help
```

## Key Features

✅ Generates test cases within 5 minutes of code commit  
✅ Tests across multiple hardware configurations automatically  
✅ Detects crashes, hangs, memory leaks, and data corruption  
✅ Tracks code coverage (line, branch, function) with gap identification  
✅ Performs security fuzzing and vulnerability detection  
✅ Monitors performance with baseline comparison and trend analysis  
✅ Validates kernel configuration options (minimal, default, maximal)  
✅ Efficient resource management with automatic cleanup and scaling  

---

## Project Status

**Current Phase:** Active Development 🚀

The system architecture has been fully defined with comprehensive requirements covering:
- ✅ AI-driven test generation and analysis
- ✅ Multi-environment test execution
- ✅ Coverage tracking and gap identification
- ✅ Security scanning and fuzzing
- ✅ Performance monitoring and regression detection
- ✅ CI/CD integration

**Implementation Progress:**
- ✅ **Task 1 Complete (Dec 3, 2025):** Project structure and core infrastructure
  - Directory structure created for all components (ai_generator, orchestrator, execution, analysis, integration)
  - Python project configured with Poetry and pip
  - Testing framework (pytest) and Hypothesis configured with 100+ iterations
  - Comprehensive configuration system implemented with pydantic-settings
  - Settings classes for LLM, database, execution, coverage, security, performance, and notifications
  - Test fixtures and conftest.py for shared test utilities
  - Verification script (verify_setup.py) confirms all structure is correct
- 📋 **Task 2 Ready:** Core data models and interfaces
  - Next: Implementing TestCase, TestResult, CodeAnalysis, FailureAnalysis, HardwareConfig, Environment
  - Includes serialization/deserialization and validation logic

**Development Methodology:** Following spec-driven development with comprehensive testing (unit + property-based) to ensure correctness across all 50 implementation tasks.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/CONTRIBUTING.md) for details on how to get started.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact & Collaboration

For questions or collaboration opportunities, please reach out through GitHub issues or contact the project maintainers.

**Project Maintainer:** Charles Liu

---

**Last Updated:** December 5, 2025
