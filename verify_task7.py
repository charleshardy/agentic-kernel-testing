#!/usr/bin/env python3
"""Verification script for Task 7 implementation.

This script verifies that all components of Task 7 are correctly implemented
and all tests pass.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✓ {description} - PASSED")
        return True
    else:
        print(f"✗ {description} - FAILED")
        print(f"\nOutput:\n{result.stdout}")
        print(f"\nErrors:\n{result.stderr}")
        return False


def check_file_exists(filepath, description):
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("  Task 7 Implementation Verification")
    print("  Environment Manager for Virtual Environments")
    print("="*60)
    
    all_passed = True
    
    # Check implementation files
    print("\n1. Checking Implementation Files...")
    files_to_check = [
        ("execution/environment_manager.py", "Main implementation"),
        ("tests/unit/test_environment_manager.py", "Unit tests"),
        ("tests/property/test_environment_cleanup.py", "Cleanup property tests"),
        ("tests/property/test_stress_test_isolation.py", "Isolation property tests"),
        ("demo_task7.py", "Demo script"),
        ("TASK7_IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_passed = False
    
    # Check imports
    print("\n2. Checking Module Imports...")
    import_checks = [
        ("from execution.environment_manager import EnvironmentManager", "EnvironmentManager"),
        ("from execution.environment_manager import KernelImage", "KernelImage"),
        ("from execution.environment_manager import EnvironmentHealth", "EnvironmentHealth"),
    ]
    
    for import_stmt, description in import_checks:
        try:
            exec(import_stmt)
            print(f"✓ {description} import successful")
        except Exception as e:
            print(f"✗ {description} import failed: {e}")
            all_passed = False
    
    # Run unit tests
    print("\n3. Running Unit Tests...")
    if not run_command(
        "python3 -m pytest tests/unit/test_environment_manager.py -v --tb=no -q",
        "Unit Tests (21 tests)"
    ):
        all_passed = False
    
    # Run property tests for cleanup
    print("\n4. Running Cleanup Property Tests...")
    if not run_command(
        "python3 -m pytest tests/property/test_environment_cleanup.py -v --tb=no -q",
        "Cleanup Property Tests (9 tests, 100 iterations each)"
    ):
        all_passed = False
    
    # Run property tests for isolation
    print("\n5. Running Isolation Property Tests...")
    if not run_command(
        "python3 -m pytest tests/property/test_stress_test_isolation.py -v --tb=no -q",
        "Isolation Property Tests (10 tests, 100 iterations each)"
    ):
        all_passed = False
    
    # Run all task 7 tests together
    print("\n6. Running All Task 7 Tests Together...")
    if not run_command(
        "python3 -m pytest tests/unit/test_environment_manager.py "
        "tests/property/test_environment_cleanup.py "
        "tests/property/test_stress_test_isolation.py -v --tb=no -q",
        "All Task 7 Tests (40 tests total)"
    ):
        all_passed = False
    
    # Verify demo runs
    print("\n7. Running Demo Script...")
    if not run_command(
        "python3 demo_task7.py",
        "Demo Script Execution"
    ):
        all_passed = False
    
    # Check test count
    print("\n8. Verifying Test Count...")
    result = subprocess.run(
        "python3 -m pytest tests/ --collect-only -q 2>&1 | grep 'tests collected'",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if "206 tests collected" in result.stdout:
        print("✓ Total test count: 206 tests (increased from 185)")
        print("  - Added 21 unit tests")
        print("  - Added 19 property tests (9 cleanup + 10 isolation)")
    else:
        print(f"✗ Unexpected test count: {result.stdout}")
        all_passed = False
    
    # Summary
    print("\n" + "="*60)
    print("  Verification Summary")
    print("="*60)
    
    if all_passed:
        print("\n✓ ALL CHECKS PASSED!")
        print("\nTask 7 Implementation Status:")
        print("  ✓ Environment manager implemented")
        print("  ✓ QEMU/KVM provisioning working")
        print("  ✓ Lifecycle management complete")
        print("  ✓ Artifact capture functional")
        print("  ✓ Health monitoring operational")
        print("  ✓ 21 unit tests passing")
        print("  ✓ 9 cleanup property tests passing (900 iterations)")
        print("  ✓ 10 isolation property tests passing (1000 iterations)")
        print("  ✓ All 40 tests passing")
        print("  ✓ Demo script runs successfully")
        print("\nRequirements Validated:")
        print("  ✓ Requirement 2.1: Multi-hardware testing")
        print("  ✓ Requirement 3.5: Stress test isolation")
        print("  ✓ Requirement 10.4: Environment cleanup")
        print("\nTask Status:")
        print("  ✓ Task 7: COMPLETED")
        print("  ✓ Subtask 7.1: COMPLETED (Property 49 passing)")
        print("  ✓ Subtask 7.2: COMPLETED (Property 15 passing)")
        return 0
    else:
        print("\n✗ SOME CHECKS FAILED")
        print("\nPlease review the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
