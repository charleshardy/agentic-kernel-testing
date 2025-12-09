#!/usr/bin/env python3
"""Check if hypothesis is installed."""

import sys

try:
    import hypothesis
    print(f"✓ Hypothesis is installed: version {hypothesis.__version__}")
    
    from hypothesis import given, strategies as st, settings
    print("✓ Can import hypothesis decorators and strategies")
    
    # Try a simple test
    @given(st.integers())
    @settings(max_examples=10)
    def test_simple(x):
        assert isinstance(x, int)
    
    test_simple()
    print("✓ Simple hypothesis test works")
    
    sys.exit(0)
    
except ImportError as e:
    print(f"✗ Hypothesis not installed: {e}")
    print("\nTo install: pip install hypothesis")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
