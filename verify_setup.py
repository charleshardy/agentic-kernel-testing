#!/usr/bin/env python3
"""
Agentic AI Testing System - Setup Verification Script

This script verifies that the development environment is properly configured
and all required dependencies are available.
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path
from typing import List, Tuple, Optional

# ANSI color codes for output formatting
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def check_python_version() -> bool:
    """Check if Python version is 3.10 or higher."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (requires 3.10+)")
        return False

def check_command_available(command: str) -> bool:
    """Check if a command is available in PATH."""
    try:
        subprocess.run([command, '--version'], 
                      capture_output=True, 
                      check=True, 
                      timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_python_package(package: str) -> Tuple[bool, Optional[str]]:
    """Check if a Python package is installed and return version."""
    try:
        module = importlib.import_module(package)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, None

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()

def check_directory_structure() -> List[Tuple[str, bool]]:
    """Check if required directories exist."""
    required_dirs = [
        'ai_generator',
        'orchestrator', 
        'execution',
        'analysis',
        'integration',
        'tests',
        'docs',
        '.kiro'
    ]
    
    results = []
    for directory in required_dirs:
        exists = Path(directory).is_dir()
        results.append((directory, exists))
    
    return results

def check_configuration_files() -> List[Tuple[str, bool]]:
    """Check if configuration files exist."""
    config_files = [
        'pyproject.toml',
        '.env.example',
        'requirements.txt',
        '.gitignore',
        'README.md'
    ]
    
    results = []
    for config_file in config_files:
        exists = check_file_exists(config_file)
        results.append((config_file, exists))
    
    return results

def check_core_dependencies() -> List[Tuple[str, bool, Optional[str]]]:
    """Check core Python dependencies."""
    core_packages = [
        'pytest',
        'hypothesis',
        'fastapi',
        'pydantic',
        'sqlalchemy',
        'requests',
        'aiohttp',
        'gitpython',
        'pyyaml'
    ]
    
    results = []
    for package in core_packages:
        installed, version = check_python_package(package)
        results.append((package, installed, version))
    
    return results

def check_optional_dependencies() -> List[Tuple[str, bool, Optional[str]]]:
    """Check optional Python dependencies."""
    optional_packages = [
        'openai',
        'anthropic',
        'psycopg2',
        'uvicorn',
        'black',
        'isort',
        'mypy',
        'pylint'
    ]
    
    results = []
    for package in optional_packages:
        installed, version = check_python_package(package)
        results.append((package, installed, version))
    
    return results

def check_system_tools() -> List[Tuple[str, bool]]:
    """Check system tools availability."""
    tools = [
        'git',
        'docker',
        'poetry'
    ]
    
    results = []
    for tool in tools:
        available = check_command_available(tool)
        results.append((tool, available))
    
    return results

def check_environment_variables() -> List[Tuple[str, bool]]:
    """Check important environment variables."""
    env_vars = [
        'PATH',
        'HOME',
        'USER'
    ]
    
    results = []
    for var in env_vars:
        exists = var in os.environ
        results.append((var, exists))
    
    return results

def main():
    """Main verification function."""
    print_header("Agentic AI Testing System - Setup Verification")
    
    all_checks_passed = True
    
    # Python version check
    print_header("Python Environment")
    if not check_python_version():
        all_checks_passed = False
        print_error("Please upgrade to Python 3.10 or higher")
    
    # Directory structure check
    print_header("Project Structure")
    dir_results = check_directory_structure()
    for directory, exists in dir_results:
        if exists:
            print_success(f"Directory: {directory}/")
        else:
            print_error(f"Missing directory: {directory}/")
            all_checks_passed = False
    
    # Configuration files check
    print_header("Configuration Files")
    config_results = check_configuration_files()
    for config_file, exists in config_results:
        if exists:
            print_success(f"Config file: {config_file}")
        else:
            print_error(f"Missing config file: {config_file}")
            all_checks_passed = False
    
    # Core dependencies check
    print_header("Core Dependencies")
    core_deps = check_core_dependencies()
    for package, installed, version in core_deps:
        if installed:
            print_success(f"{package} ({version})")
        else:
            print_error(f"Missing: {package}")
            all_checks_passed = False
    
    # Optional dependencies check
    print_header("Optional Dependencies")
    optional_deps = check_optional_dependencies()
    missing_optional = []
    for package, installed, version in optional_deps:
        if installed:
            print_success(f"{package} ({version})")
        else:
            print_warning(f"Optional: {package} (not installed)")
            missing_optional.append(package)
    
    # System tools check
    print_header("System Tools")
    tool_results = check_system_tools()
    for tool, available in tool_results:
        if available:
            print_success(f"{tool}")
        else:
            print_warning(f"Optional tool not available: {tool}")
    
    # Environment variables check
    print_header("Environment Variables")
    env_results = check_environment_variables()
    for var, exists in env_results:
        if exists:
            print_success(f"{var}")
        else:
            print_error(f"Missing environment variable: {var}")
    
    # Final summary
    print_header("Verification Summary")
    
    if all_checks_passed:
        print_success("🎉 All required components are properly configured!")
        print_info("The Agentic AI Testing System is ready for development.")
        
        if missing_optional:
            print_warning(f"Optional packages not installed: {', '.join(missing_optional)}")
            print_info("Install with: pip install " + " ".join(missing_optional))
    else:
        print_error("❌ Some required components are missing or misconfigured.")
        print_info("Please fix the issues above before proceeding.")
        
        print_info("\n📋 Quick fixes:")
        print_info("1. Install dependencies: pip install -r requirements.txt")
        print_info("2. Or use Poetry: poetry install")
        print_info("3. Create .env file: cp .env.example .env")
        print_info("4. Update .env with your API keys and settings")
    
    # Additional setup instructions
    print_header("Next Steps")
    print_info("1. Copy .env.example to .env and configure your settings")
    print_info("2. Set up your LLM provider credentials (OpenAI, Anthropic, Amazon Q, or Kiro)")
    print_info("3. Run tests: pytest")
    print_info("4. Start the API server: python -m api.server")
    print_info("5. Check the documentation in docs/ for more details")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())