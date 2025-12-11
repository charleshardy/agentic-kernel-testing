#!/usr/bin/env python3
"""
Final cleanup script to move remaining files.
"""

import os
import shutil

def move_remaining_files():
    """Move the remaining files to appropriate locations."""
    
    moves = [
        # Move shell scripts to test-runners
        ('run_pbt_baseline.sh', 'dev-scripts/test-runners/'),
        ('run_pbt_security_report.sh', 'dev-scripts/test-runners/'),
        ('setup_test_env.sh', 'dev-scripts/test-runners/'),
        
        # Move documentation to docs
        ('confluence-page-content.md', 'docs/'),
        
        # Move this script to dev-scripts
        ('organize_files.py', 'dev-scripts/'),
        ('final_cleanup.py', 'dev-scripts/')
    ]
    
    for source, target_dir in moves:
        if os.path.exists(source):
            try:
                target = os.path.join(target_dir, source)
                shutil.move(source, target)
                print(f"Moved: {source} -> {target}")
            except Exception as e:
                print(f"Error moving {source}: {e}")
        else:
            print(f"File not found: {source}")

def create_project_structure_doc():
    """Create a document showing the new project structure."""
    
    structure_doc = """# Project Structure

The Agentic AI Testing System has been organized into a clean, maintainable structure:

## Root Directory (Production Files Only)
```
├── .env.example              # Environment configuration template
├── .gitignore               # Git ignore rules
├── CHANGELOG.md             # Project changelog
├── docker-compose.yml       # Docker deployment configuration
├── LICENSE                  # Project license
├── Makefile                 # Build and development commands
├── pyproject.toml          # Python project configuration
├── pytest.ini             # Test configuration
├── README.md               # Main project documentation
├── setup.py                # Python package setup
├── SYSTEM_STATUS.md        # Current system status
├── QUICK_START_AMAZON_Q_KIRO.md  # Quick start guide
└── SSO_QUICK_REFERENCE.md  # SSO authentication reference
```

## Core Application Directories
```
├── ai_generator/           # AI-powered test generation
├── analysis/              # Coverage, performance, security analysis
├── api/                   # REST API server
├── cli/                   # Command-line interface
├── config/                # Configuration management
├── dashboard/             # Web UI
├── database/              # Database layer
├── execution/             # Test execution engine
├── integration/           # CI/CD and VCS integration
├── orchestrator/          # Test scheduling and resource management
└── tests/                 # Production test suite
```

## Documentation
```
├── docs/                  # Complete documentation
│   ├── QUICKSTART.md
│   ├── INSTALLATION.md
│   ├── ARCHITECTURE.md
│   ├── PRODUCTION_DEPLOYMENT.md
│   └── confluence-page-content.md
└── .kiro/specs/           # System specifications
    └── agentic-kernel-testing/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

## Development and Archive Directories
```
├── dev-scripts/           # Development scripts (organized)
│   ├── demos/            # Demo scripts
│   ├── debug/            # Debug utilities
│   ├── test-runners/     # Test execution scripts
│   ├── verification/     # System verification scripts
│   └── validation/       # Final validation scripts
├── task-summaries/       # Implementation task documentation
├── test-outputs/         # Historical test results
└── archive/              # Legacy scripts and files
    └── legacy-scripts/   # Old test scripts
```

## Deployment
```
├── k8s/                  # Kubernetes manifests
├── scripts/              # Deployment scripts
└── examples/             # Usage examples
```

## Data Directories
```
├── baseline_data/        # Performance baselines
├── benchmark_data/       # Benchmark results
├── coverage_data/        # Coverage reports
└── matrix_output/        # Hardware compatibility matrices
```

## Benefits of This Organization

1. **Clean Root Directory**: Only production-ready files in root
2. **Logical Grouping**: Related files grouped by purpose
3. **Easy Navigation**: Clear directory structure
4. **Maintainability**: Easier to find and maintain files
5. **Professional Appearance**: Clean, organized project structure
6. **Documentation**: README files explain each directory's purpose

## File Categories Moved

- **Demo Scripts**: `demo_*.py` → `dev-scripts/demos/`
- **Debug Scripts**: `debug_*.py` → `dev-scripts/debug/`
- **Test Runners**: `run_*.py`, test runners → `dev-scripts/test-runners/`
- **Verification**: `verify_*.py`, `validate_*.py` → `dev-scripts/verification/`
- **Validation**: Check scripts, simple tests → `dev-scripts/validation/`
- **Legacy Tests**: `test_*.py` → `archive/legacy-scripts/`
- **Task Summaries**: `TASK*.md` → `task-summaries/`
- **Test Outputs**: `*.txt`, `*.json` → `test-outputs/`

This organization makes the project more professional and easier to navigate for both developers and users.
"""
    
    with open('PROJECT_STRUCTURE.md', 'w') as f:
        f.write(structure_doc)
    print("Created: PROJECT_STRUCTURE.md")

if __name__ == "__main__":
    print("🧹 Final cleanup of project files...")
    move_remaining_files()
    create_project_structure_doc()
    print("✅ Final cleanup complete!")