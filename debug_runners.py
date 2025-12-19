#!/usr/bin/env python3
"""Debug runner availability."""

import sys
import os
sys.path.insert(0, os.getcwd())

from execution.runner_factory import TestRunnerFactory

def debug_runners():
    """Debug available runners."""
    factory = TestRunnerFactory()
    available_runners = factory.get_available_runners()
    
    print("Available runners:")
    for runner_type, runner_class in available_runners.items():
        print(f"  {runner_type}: {runner_class}")
    
    # Check Docker availability
    try:
        import docker
        print("Docker library available")
        try:
            client = docker.from_env()
            print("Docker daemon accessible")
        except Exception as e:
            print(f"Docker daemon not accessible: {e}")
    except ImportError:
        print("Docker library not available")

if __name__ == "__main__":
    debug_runners()