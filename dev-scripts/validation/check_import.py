#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

try:
    print("Attempting to import test module...")
    from tests.property import test_resource_metrics_collection
    print("✓ Import successful!")
    print(f"Found {len(dir(test_resource_metrics_collection))} items in module")
    
    # List test functions
    test_funcs = [name for name in dir(test_resource_metrics_collection) if name.startswith('test_')]
    print(f"\nFound {len(test_funcs)} test functions:")
    for func in test_funcs:
        print(f"  - {func}")
    
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
