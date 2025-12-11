#!/usr/bin/env python3
"""
Script to organize files in the root directory into appropriate subdirectories.
"""

import os
import shutil
from pathlib import Path

def create_directories():
    """Create the directory structure for organizing files."""
    directories = [
        'dev-scripts/test-runners',
        'dev-scripts/demos', 
        'dev-scripts/debug',
        'dev-scripts/verification',
        'dev-scripts/validation',
        'task-summaries',
        'test-outputs',
        'archive/legacy-scripts'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def organize_files():
    """Organize files into appropriate directories."""
    
    # File patterns and their target directories
    file_mappings = {
        # Demo scripts
        'dev-scripts/demos': [
            'demo_*.py',
            'cli_demo.py'
        ],
        
        # Debug scripts
        'dev-scripts/debug': [
            'debug_*.py'
        ],
        
        # Test runners and validation scripts
        'dev-scripts/test-runners': [
            'run_*.py',
            'comprehensive_test_runner.py',
            'direct_*.py',
            'final_*.py',
            'property_test_runner.py',
            'pytest_runner.py',
            'single_test_runner.py',
            'unit_test_runner.py'
        ],
        
        # Verification scripts
        'dev-scripts/verification': [
            'verify_*.py',
            'validate_*.py'
        ],
        
        # Validation and check scripts
        'dev-scripts/validation': [
            'check_*.py',
            'simple_*.py',
            'final_system_validation.py',
            'simplified_final_validation.py'
        ],
        
        # Test scripts
        'archive/legacy-scripts': [
            'test_*.py'
        ],
        
        # Task summaries
        'task-summaries': [
            'TASK*.md',
            'CLI_IMPLEMENTATION_SUMMARY.md',
            'IMPLEMENTATION_SUMMARY.md',
            'SERIAL_CONSOLE_ADDITION.md',
            'BOOTLOADER_DEPLOYMENT_FEATURE.md'
        ],
        
        # Test outputs
        'test-outputs': [
            '*.txt',
            '*.json',
            'test_template.*'
        ]
    }
    
    # Get all files in current directory
    current_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    
    moved_files = []
    
    for target_dir, patterns in file_mappings.items():
        for pattern in patterns:
            # Convert glob pattern to simple matching
            if '*' in pattern:
                prefix = pattern.split('*')[0]
                suffix = pattern.split('*')[-1] if pattern.split('*')[-1] != pattern.split('*')[0] else ''
                
                matching_files = [f for f in current_files 
                                if f.startswith(prefix) and f.endswith(suffix) and f not in moved_files]
            else:
                matching_files = [f for f in current_files if f == pattern and f not in moved_files]
            
            for file in matching_files:
                try:
                    source = file
                    destination = os.path.join(target_dir, file)
                    shutil.move(source, destination)
                    moved_files.append(file)
                    print(f"Moved: {source} -> {destination}")
                except Exception as e:
                    print(f"Error moving {file}: {e}")

def create_readme_files():
    """Create README files for each directory explaining their purpose."""
    
    readme_content = {
        'dev-scripts/README.md': """# Development Scripts

This directory contains various development and testing scripts used during the development of the Agentic AI Testing System.

## Subdirectories

- **demos/**: Demo scripts showing system capabilities
- **debug/**: Debug and diagnostic scripts
- **test-runners/**: Test execution and validation scripts
- **verification/**: System verification and validation scripts
- **validation/**: Final validation and check scripts

These scripts were used during development and are kept for reference and debugging purposes.
""",
        
        'dev-scripts/demos/README.md': """# Demo Scripts

Demo scripts that showcase various system capabilities and features.

These scripts demonstrate:
- Task execution workflows
- Concurrency testing
- Coverage gap identification
- Resource management
- Orchestrator functionality
""",
        
        'dev-scripts/debug/README.md': """# Debug Scripts

Debug and diagnostic scripts used for troubleshooting during development.

These scripts help with:
- Performance analysis
- Failure investigation
- Visualization of system behavior
- Scoring and metrics analysis
""",
        
        'dev-scripts/test-runners/README.md': """# Test Runner Scripts

Scripts for running various types of tests and validations.

Includes:
- Property-based test runners
- Unit test runners
- Integration test runners
- Coverage test runners
- Performance test runners
- Final validation scripts
""",
        
        'dev-scripts/verification/README.md': """# Verification Scripts

Scripts used to verify system implementation and functionality.

These scripts verify:
- Task implementations
- System components
- Integration points
- End-to-end workflows
""",
        
        'dev-scripts/validation/README.md': """# Validation Scripts

Final validation and system check scripts.

Includes:
- System validation scripts
- Import and dependency checks
- Simple test implementations
- Final system validation
""",
        
        'task-summaries/README.md': """# Task Implementation Summaries

Documentation of completed implementation tasks.

Each TASK*.md file contains:
- Implementation details
- Testing results
- Validation outcomes
- Key achievements

These documents provide a complete record of the development process.
""",
        
        'test-outputs/README.md': """# Test Outputs

Output files from various test runs and validations.

Includes:
- Test result files (.txt)
- Validation results (.json)
- Test templates and configurations
- Debug outputs

These files provide historical records of test executions.
""",
        
        'archive/legacy-scripts/README.md': """# Legacy Test Scripts

Legacy test scripts from development phase.

These scripts were used during development for:
- Manual testing
- Component validation
- Integration testing
- Performance testing

Kept for reference and potential future use.
"""
    }
    
    for file_path, content in readme_content.items():
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created: {file_path}")
        except Exception as e:
            print(f"Error creating {file_path}: {e}")

def main():
    """Main function to organize the project files."""
    print("🗂️  Organizing Agentic AI Testing System Files")
    print("=" * 50)
    
    print("\n1. Creating directory structure...")
    create_directories()
    
    print("\n2. Moving files to appropriate directories...")
    organize_files()
    
    print("\n3. Creating README files...")
    create_readme_files()
    
    print("\n✅ File organization complete!")
    print("\nNew directory structure:")
    print("├── dev-scripts/")
    print("│   ├── demos/")
    print("│   ├── debug/")
    print("│   ├── test-runners/")
    print("│   ├── verification/")
    print("│   └── validation/")
    print("├── task-summaries/")
    print("├── test-outputs/")
    print("└── archive/")
    print("    └── legacy-scripts/")

if __name__ == "__main__":
    main()