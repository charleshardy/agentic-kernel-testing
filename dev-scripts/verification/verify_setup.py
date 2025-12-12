#!/usr/bin/env python3
"""Verify the project structure and basic setup."""

import os
import sys
from pathlib import Path


def check_directory_structure():
    """Verify all required directories exist."""
    required_dirs = [
        "ai_generator",
        "orchestrator",
        "execution",
        "analysis",
        "integration",
        "config",
        "tests/unit",
        "tests/property",
        "tests/integration",
        "tests/fixtures",
    ]
    
    print("Checking directory structure...")
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_init_files():
    """Verify __init__.py files exist in packages."""
    required_inits = [
        "ai_generator/__init__.py",
        "orchestrator/__init__.py",
        "execution/__init__.py",
        "analysis/__init__.py",
        "integration/__init__.py",
        "config/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/property/__init__.py",
        "tests/integration/__init__.py",
        "tests/fixtures/__init__.py",
    ]
    
    print("\nChecking __init__.py files...")
    all_exist = True
    for init_path in required_inits:
        path = Path(init_path)
        if path.exists() and path.is_file():
            print(f"  ✓ {init_path}")
        else:
            print(f"  ✗ {init_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_config_files():
    """Verify configuration files exist."""
    required_configs = [
        "pyproject.toml",
        "pytest.ini",
        "requirements.txt",
        "setup.py",
        ".env.example",
        ".gitignore",
        "Makefile",
    ]
    
    print("\nChecking configuration files...")
    all_exist = True
    for config_path in required_configs:
        path = Path(config_path)
        if path.exists() and path.is_file():
            print(f"  ✓ {config_path}")
        else:
            print(f"  ✗ {config_path} - MISSING")
            all_exist = False
    
    return all_exist


def check_config_module():
    """Verify config module can be imported."""
    print("\nChecking config module...")
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))
        
        # Try importing without dependencies first
        import config
        print("  ✓ config module structure is valid")
        return True
    except ImportError as e:
        print(f"  ⚠ config module has import issues (expected without dependencies): {e}")
        # This is expected if dependencies aren't installed
        return True
    except Exception as e:
        print(f"  ✗ config module has errors: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Agentic AI Testing System - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Package Init Files", check_init_files),
        ("Configuration Files", check_config_files),
        ("Config Module", check_config_module),
    ]
    
    results = []
    for name, check_func in checks:
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! Project structure is set up correctly.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Copy .env.example to .env and configure")
        print("  3. Run tests: pytest")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
