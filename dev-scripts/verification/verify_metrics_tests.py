#!/usr/bin/env python3
"""Verify metrics tests run successfully."""

import subprocess
import sys
import re

print("Running resource metrics collection tests...")
print("=" * 70)

result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/property/test_resource_metrics_collection.py", 
     "-v", "--tb=short"],
    capture_output=True,
    text=True
)

output = result.stdout + result.stderr

print(output)

# Check for test results
if "passed" in output.lower():
    # Extract number of passed tests
    match = re.search(r'(\d+) passed', output)
    if match:
        num_passed = int(match.group(1))
        print(f"\n{'='*70}")
        print(f"✅ SUCCESS: {num_passed} tests passed!")
        print(f"{'='*70}")
        sys.exit(0)

if "failed" in output.lower() or "error" in output.lower():
    print(f"\n{'='*70}")
    print("❌ FAILURE: Some tests failed or had errors")
    print(f"{'='*70}")
    sys.exit(1)

print(f"\n{'='*70}")
print("⚠️  WARNING: Could not determine test status")
print(f"{'='*70}")
sys.exit(1)
