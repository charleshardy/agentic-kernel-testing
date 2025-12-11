#!/usr/bin/env python3
"""Validate the metrics test module can be imported and run."""

import sys
sys.path.insert(0, '.')

try:
    print("Step 1: Importing module...")
    from tests.property import test_resource_metrics_collection
    print("✓ Module imported successfully")
    
    print("\nStep 2: Running example test...")
    test_resource_metrics_collection.test_metrics_collection_example()
    print("✓ Example test passed")
    
    print("\nStep 3: Running serialization test...")
    test_resource_metrics_collection.test_metrics_to_dict_serialization()
    print("✓ Serialization test passed")
    
    print("\n" + "="*70)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
