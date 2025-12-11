#!/usr/bin/env python3
"""Direct test execution for metrics collection."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import and run the example test
from tests.property.test_resource_metrics_collection import test_metrics_collection_example

try:
    test_metrics_collection_example()
    print("✓ test_metrics_collection_example PASSED")
except Exception as e:
    print(f"✗ test_metrics_collection_example FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll tests passed!")
