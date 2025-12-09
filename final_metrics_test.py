#!/usr/bin/env python3
"""Final test runner for metrics collection tests."""

import sys
import subprocess

# Run the test
result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/property/test_resource_metrics_collection.py", 
     "-v", "--tb=short"],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)

# Check if tests passed
if "passed" in result.stdout and "failed" not in result.stdout.lower():
    print("\n✅ All metrics tests PASSED!")
    sys.exit(0)
else:
    print("\n❌ Some tests FAILED")
    sys.exit(1)
