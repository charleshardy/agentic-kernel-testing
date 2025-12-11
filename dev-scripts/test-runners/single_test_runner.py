#!/usr/bin/env python3
"""
Single test runner to debug issues.
"""

import subprocess
import sys
import os

def run_single_test():
    """Run a single test to see the error."""
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    cmd = "python3 -m pytest tests/unit/test_models.py::TestPeripheral::test_peripheral_creation -v --tb=long -s"
    
    print(f"Running: {cmd}")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=60
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
        print(f"Error running test: {e}")
        return False

if __name__ == "__main__":
    run_single_test()