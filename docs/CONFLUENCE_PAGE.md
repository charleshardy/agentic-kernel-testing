# Agentic AI Testing System for Linux Kernel and BSP

## Overview

The Agentic AI Testing System is an autonomous AI-powered testing platform that intelligently tests Linux kernels and Board Support Packages (BSPs) across diverse hardware configurations. The system leverages Large Language Models to generate test cases, analyze failures, and provide actionable feedback to developers.

**Project Goal:** Improve kernel and BSP quality through comprehensive, automated testing that adapts to code changes and discovers edge cases that traditional testing might miss.

---

## Recent Updates

**Latest:** December 5, 2025
- ✅ **Task 12 Complete:** Fault Detection and Monitoring
  - **Comprehensive fault detection system with 4 specialized detectors:**
    - **KernelCrashDetector:** Detects panics, oops, NULL pointer dereferences, general protection faults
    - **HangDetector:** Active monitoring and log-based detection of hangs, timeouts, soft lockups
    - **MemoryLeakDetector:** KASAN integration for use-after-free, double-free, out-of-bounds access
    - **DataCorruptionDetector:** Checksum errors, filesystem corruption, ECC errors, metadata corruption
  - **Unified FaultDetectionSystem** coordinating all detectors with single interface
  - Stack trace extraction and crash type classification
  - Comprehensive statistics tracking for all fault types
  - Severity assessment (critical, high, medium, low) for all detected faults
  - 9 property-based tests with 100+ iterations each - All passing ✅
  - **Property 12 validated:** Fault detection completeness - all crashes, hangs, leaks, and corruption detected ✅
  - Validates Requirements 3.2 (Fault detection during fault injection) ✅
- ✅ **Task 8 Complete:** Physical Hardware Lab Interface
  - Hardware reservation system with time-based expiration and automatic cleanup
  - SSH-based test execution on physical boards with comprehensive result capture
  - Serial console (telnet) test execution for early boot testing and kernel debugging
  - **Bootloader deployment and verification (U-Boot, GRUB, UEFI, custom)**
    - TFTP, storage (USB/SD/eMMC), and serial console deployment methods
    - Comprehensive verification: version, commands, environment, boot script, kernel loading
    - Flexible configuration for custom bootloaders and deployment workflows
  - Power control integration: PDU, IPMI, and manual control methods
  - Comprehensive health checks: SSH, disk, memory, uptime, kernel version, serial console
  - Maintenance mode management and hardware inventory operations
  - 30+ unit tests covering all functionality - All passing ✅
  - Validates Requirements 2.1 (Multi-hardware testing) and 2.3 (Hardware failure isolation) ✅
- ✅ **Task 7 Complete:** Environment Manager for virtual environments (QEMU/KVM)
- ✅ **Task 6 Complete:** Hardware Configuration Management
  - Hardware configuration parser and validator supporting x86_64, arm64, riscv64, arm
  - Test matrix generator for multi-hardware testing (virtual and physical)
  - Hardware capability detection (virtualization, architecture features, memory, storage)
  - Virtual vs physical hardware classifier with preference sorting
  - **Property 6 validated:** Hardware matrix coverage - all configured targets tested ✅
  - **Property 10 validated:** Virtual environment preference - virtual prioritized over physical ✅
  - 2 comprehensive property-based tests with 100+ iterations each - All passing ✅
  - Complete unit test suite for all hardware config components - All passing ✅
- ✅ **Task 5 Complete:** Test case organization and summarization
- ✅ **Task 4 Complete:** AI Test Generator Core Implementation
  - Multi-provider LLM support: OpenAI, Anthropic, Amazon Bedrock
  - **Amazon Q Developer Pro integration with AWS SSO support**
  - **Kiro AI integration with OAuth2 SSO support**
  - **SSO Authentication Layer (AWS SSO/IAM Identity Center & OAuth2/OIDC)**
  - Automatic token caching and refresh
  - Code-to-prompt conversion for test generation
  - Test case template system and validator
  - Retry logic with exponential backoff
- ✅ **Task 3 Complete:** Code analysis and diff parsing with subsystem identification
- ✅ **Task 2 Complete:** Core data models and interfaces with comprehensive validation
- ✅ **Task 1 Complete:** Project structure and core infrastructure
- ✅ **Task 11 Complete:** Fault injection system
- ✅ **Task 10 Complete:** Compatibility matrix generator
- ✅ **Task 9 Complete:** Test execution engine
- 📋 **Ready for Task 13:** Concurrency testing support

---

## Core Capabilities

### 🤖 Autonomous Test Generation
- AI agents analyze code changes and automatically generate targeted test cases
- Covers normal usage, boundary conditions, and error paths
- Generates 10+ distinct test cases per modified function within 5 minutes

### 🖥️ Multi-Hardware Testing
- Execute tests across virtual environments (QEMU, KVM) and physical hardware boards
- Ensures compatibility across x86_64, ARM, and RISC-V architectures
- Supports SSH-based execution and serial console (telnet) for early boot testing
- Bootloader deployment and verification (U-Boot, GRUB, UEFI) for pre-boot testing
- Generates compatibility matrices showing pass/fail status for each configuration

### 💥 Intelligent Fault Injection & Detection
- Stress testing with memory failures, I/O errors, and timing variations
- Discovers edge cases and race conditions
- **Comprehensive fault detection system:**
  - Kernel crashes (panics, oops, NULL pointer dereferences, GPF)
  - System hangs (blocked tasks, soft lockups, watchdog timeouts)
  - Memory leaks (KASAN integration: use-after-free, double-free, out-of-bounds)
  - Data corruption (checksum errors, filesystem corruption, ECC errors)
- Automatic stack trace extraction and crash classification
- Real-time monitoring with timeout detection

### 🔍 Root Cause Analysis
- AI-powered failure analysis correlating issues with code changes
- Groups related failures and identifies common root causes
- Provides suggested fixes and references to similar historical issues

### 🔒 Security Testing
- Automated fuzzing on system call interfaces, ioctl handlers, and network protocol parsers
- Static analysis detecting buffer overflows, use-after-free, and integer overflows
- Vulnerability classification by severity and exploitability

### ⚡ Performance Monitoring
- Continuous performance benchmarking (throughput, latency, resource utilization)
- Regression detection with commit-level attribution
- Profiling data showing performance hotspots

### 🔄 CI/CD Integration
- Seamless integration with GitHub, GitLab, and Jenkins
- Automatic test triggering on commits, PRs, and branch updates
- Real-time status reporting back to version control systems

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

---

## Technical Architecture

### System Layers

**Intelligence Layer**
- AI Test Generator
- Root Cause Analyzer
- Test Orchestrator

**Execution Layer**
- Virtual Test Environments (QEMU/KVM)
- Physical Hardware Lab
- Test Runner Engine

**Analysis Layer**
- Coverage Analyzer
- Performance Monitor
- Security Scanner
- Fault Detection System

**Integration Layer**
- CI/CD Hooks
- Version Control Interface
- Notification Service

### Technology Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.10+ |
| **AI/ML** | Amazon Q APIs (built on Amazon Bedrock for LLM access), Hypothesis (property-based testing) |
| **Testing** | pytest, gcov/lcov, Syzkaller (fuzzing), Coccinelle (static analysis) |
| **Virtualization** | QEMU, KVM, SSH for physical hardware |
| **Performance** | LMBench, FIO, Netperf, perf |
| **Data** | PostgreSQL/SQLite, FastAPI |
| **Deployment** | Docker, Kubernetes |

---

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

## Project Structure

```
├── ai_generator/       # AI-powered test generation (✅ Structure created)
├── orchestrator/       # Test scheduling and resource management (✅ Structure created)
├── execution/          # Test runners and environment managers (✅ Structure created)
├── analysis/           # Coverage, performance, security analysis (✅ Structure created)
├── integration/        # CI/CD hooks and VCS integration (✅ Structure created)
├── tests/             # Unit, property-based, and integration tests (✅ Framework configured)
├── config/            # Configuration management (✅ Settings system implemented)
├── docs/              # Comprehensive documentation (✅ Created)
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   ├── INSTALLATION.md
│   └── CONTRIBUTING.md
└── .kiro/
    ├── specs/         # Feature specifications (✅ Complete)
    └── steering/      # AI assistant guidance (✅ Complete)
```

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
- ✅ **Task 12 Complete (Dec 5, 2025):** Fault Detection and Monitoring
  - **KernelCrashDetector:** Pattern-based detection with stack trace extraction
  - **HangDetector:** Active monitoring + log-based detection (blocked tasks, soft lockups, RCU stalls)
  - **MemoryLeakDetector:** KASAN integration (use-after-free, double-free, out-of-bounds)
  - **DataCorruptionDetector:** Checksum verification and corruption pattern detection
  - **FaultDetectionSystem:** Unified coordinator with comprehensive statistics
  - **Property 12 (Fault detection completeness):** All fault types detected when present
  - 9 property-based tests with 100+ iterations each - All passing ✅
  - Validates Requirements 3.2 (Detect all crashes, hangs, leaks, and corruption)
- ✅ **Task 8 Complete (Dec 5, 2025):** Physical Hardware Lab Interface with bootloader deployment
- ✅ **Task 7 Complete (Dec 4, 2025):** Environment Manager for virtual environments
- ✅ **Task 6 Complete (Dec 4, 2025):** Hardware Configuration Management
  - **HardwareConfigParser:** Validates configurations with support for 4 architectures, 5 storage types, 3 emulators
  - **TestMatrixGenerator:** Creates comprehensive test matrices for multi-hardware testing
  - **HardwareCapabilityDetector:** Identifies virtualization, architecture features, memory, and storage capabilities
  - **HardwareClassifier:** Sorts configs to prefer virtual over physical (Requirements 2.5)
  - **Property 6 (Hardware matrix coverage):** Validates all configured targets are tested without skipping
  - **Property 10 (Virtual environment preference):** Ensures virtual hardware is used before physical
  - 2 property-based test files with 18 comprehensive test properties - All passing ✅
  - Complete unit test coverage with 50+ unit tests - All passing ✅
  - Demo script showcasing all features working together
  - Validates Requirements 2.1, 2.2, 2.4, 2.5
- ✅ **Task 5 Complete (Dec 4, 2025):** Test case organization and summarization
- ✅ **Task 4 Complete (Dec 4, 2025):** AI Test Generator Core with multi-provider LLM support
- ✅ **Task 3 Complete (Dec 4, 2025):** Code analysis and diff parsing
- ✅ **Task 2 Complete (Dec 3, 2025):** Core data models and interfaces
- ✅ **Task 1 Complete (Dec 3, 2025):** Project structure and core infrastructure
- ✅ **Task 11 Complete (Dec 5, 2025):** Fault injection system
- ✅ **Task 10 Complete (Dec 5, 2025):** Compatibility matrix generator
- ✅ **Task 9 Complete (Dec 5, 2025):** Test execution engine
- 📋 **Task 13 Ready:** Concurrency testing support

**Development Methodology:** Following spec-driven development with comprehensive testing (unit + property-based) to ensure correctness across all 50 implementation tasks. All tests are required from the start for thorough validation.

---

## Resources

- **GitHub Repository:** https://github.com/charleshardy/agentic-kernel-testing
- **Documentation:**
  - [Quick Start Guide](https://github.com/charleshardy/agentic-kernel-testing/blob/main/docs/QUICKSTART.md) - Get up and running in minutes
  - [Architecture Overview](https://github.com/charleshardy/agentic-kernel-testing/blob/main/docs/ARCHITECTURE.md) - System design and technical architecture
  - [Fault Detection Guide](https://github.com/charleshardy/agentic-kernel-testing/blob/main/docs/FAULT_DETECTION_GUIDE.md) - Comprehensive fault detection and monitoring
  - [Installation Guide](https://github.com/charleshardy/agentic-kernel-testing/blob/main/docs/INSTALLATION.md) - Detailed installation instructions
  - [Contributing Guidelines](https://github.com/charleshardy/agentic-kernel-testing/blob/main/docs/CONTRIBUTING.md) - How to contribute to the project
  - [Changelog](https://github.com/charleshardy/agentic-kernel-testing/blob/main/CHANGELOG.md) - Project updates and version history
- **Specifications:**
  - [Requirements Document](https://github.com/charleshardy/agentic-kernel-testing/blob/main/.kiro/specs/agentic-kernel-testing/requirements.md) - 10 major requirements with 50+ acceptance criteria
  - [Design Document](https://github.com/charleshardy/agentic-kernel-testing/blob/main/.kiro/specs/agentic-kernel-testing/design.md) - Architecture with 50 correctness properties
  - [Implementation Tasks](https://github.com/charleshardy/agentic-kernel-testing/blob/main/.kiro/specs/agentic-kernel-testing/tasks.md) - 50 comprehensive tasks with testing requirements

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- Poetry or pip for dependency management
- Docker (optional, for containerized deployment)

### Quick Start
```bash
# Clone repository
git clone https://github.com/charleshardy/agentic-kernel-testing.git
cd agentic-kernel-testing

# Install dependencies
pip install -r requirements.txt
# Or using Poetry
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your LLM API key

# Verify setup
python3 verify_setup.py

# Run tests
pytest
```

### What's Implemented
- ✅ Complete project structure with all component directories
- ✅ Configuration system with comprehensive settings management
- ✅ Testing framework with pytest and Hypothesis (100+ iterations per property)
- ✅ Core data models with serialization and validation
- ✅ Code analysis and diff parsing with subsystem identification
- ✅ AI test generator with multi-provider LLM support (OpenAI, Anthropic, Amazon Q, Kiro)
- ✅ SSO authentication layer (AWS SSO/IAM Identity Center, OAuth2/OIDC)
- ✅ Test case organization and summarization
- ✅ **Fault detection and monitoring (NEW)**
  - Kernel crash detector with stack trace extraction
  - Hang detector with active monitoring and log analysis
  - Memory leak detector with KASAN integration
  - Data corruption detector with checksum verification
  - Unified fault detection system with comprehensive statistics
- ✅ **Physical hardware lab interface**
  - Hardware reservation system with time-based expiration
  - SSH and serial console (telnet) test execution
  - Bootloader deployment and verification (U-Boot, GRUB, UEFI)
  - Power control integration and health monitoring
- ✅ **Hardware configuration management**
  - Multi-architecture support (x86_64, arm64, riscv64, arm)
  - Test matrix generation for comprehensive hardware coverage
  - Virtual/physical hardware classification with preference sorting
  - Hardware capability detection
- ✅ Documentation suite (Quick Start, Architecture, Installation, Contributing)
- ✅ Verification scripts to validate setup and implementations
- ✅ Development tools (Makefile, pyproject.toml, pytest.ini)

### Next Steps
1. Implement concurrency testing support (Task 13)
   - Thread scheduling variation system
   - Timing variation injector for race condition detection
   - Multiple execution runs with different schedules
2. Implement reproducible test case generation (Task 14)
   - Test case minimization for failures
   - Reproducibility verification
   - Seed-based test execution for determinism
3. Continue through remaining 38 implementation tasks

---

## Testing Approach

The project follows a comprehensive testing strategy to ensure correctness:

### Property-Based Testing
- **50 Correctness Properties** defined in the design document
- Each property validated using Hypothesis with 100+ test iterations
- Properties cover all major system behaviors and requirements
- Examples: test generation time bounds, subsystem targeting accuracy, coverage completeness

### Unit Testing
- Component-level tests for all modules
- Data model validation and serialization tests
- Edge case and error condition testing
- Fast feedback during development

### Integration Testing
- End-to-end workflow validation
- Component interaction testing
- System behavior verification across all layers

### Test Organization
```
tests/
├── unit/           # Fast, isolated component tests
├── property/       # Property-based tests with Hypothesis
├── integration/    # End-to-end system tests
└── fixtures/       # Shared test data and utilities
```

**Testing Philosophy:** All tests are required from the start to ensure comprehensive validation and catch issues early in development.

---

## Contact & Collaboration

For questions or collaboration opportunities, please reach out through the GitHub repository or contact the project maintainers.

**Project Maintainer:** Charles Liu

---

**Last Updated:** December 5, 2025
