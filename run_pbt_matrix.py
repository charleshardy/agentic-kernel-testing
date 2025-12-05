#!/usr/bin/env python3
"""Run property-based tests for compatibility matrix."""

import sys
import subprocess

# Run the property-based tests
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 
     'tests/property/test_compatibility_matrix_completeness.py', 
     '-v', '--tb=short', '--hypothesis-show-statistics'],
    capture_output=False,
    text=True
)

sys.exit(result.returncode)
