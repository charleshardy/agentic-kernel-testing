#!/usr/bin/env python3
"""
Pytest runner that captures output properly.
"""

import subprocess
import sys
import os

def run_pytest_with_output(test_path, extra_args=""):
    """Run pytest and capture all output."""
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    cmd = f"python3 -m pytest {test_path} -v --tb=short {extra_args}"
    
    print(f"Running: {cmd}")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=300
        )
        
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Test execution timed out!")
        return False
    except Exception as e:
        print(f"Error running pytest: {e}")
        return False

def main():
    """Main function."""
    print("Pytest Runner for Checkpoint 47")
    print("=" * 60)
    
    tests_to_run = [
        ("Unit Tests", "tests/unit/", ""),
        ("Property Tests", "tests/property/", "--hypothesis-iterations=100"),
        ("Integration Tests", "tests/integration/", ""),
    ]
    
    results = {}
    
    for test_name, test_path, extra_args in tests_to_run:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        if not os.path.exists(test_path):
            print(f"Test path {test_path} does not exist")
            results[test_name] = False
            continue
        
        results[test_name] = run_pytest_with_output(test_path, extra_args)
    
    # Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("✅ ALL TEST SUITES PASSED!")
        return True
    else:
        print(f"❌ {total - passed} TEST SUITES FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)