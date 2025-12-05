#!/usr/bin/env python3
"""Run property-based tests directly."""

import sys
sys.path.insert(0, '.')

try:
    import pytest
    print("pytest is available")
    
    # Run the tests
    exit_code = pytest.main([
        'tests/property/test_compatibility_matrix_completeness.py',
        '-v',
        '--tb=short',
        '--hypothesis-show-statistics'
    ])
    
    sys.exit(exit_code)
    
except ImportError as e:
    print(f"Error importing pytest: {e}")
    print("\nTrying to install pytest...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest', 'hypothesis'])
    print("\nPlease run this script again.")
    sys.exit(1)
