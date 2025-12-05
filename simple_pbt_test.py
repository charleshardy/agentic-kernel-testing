#!/usr/bin/env python3
"""Simple test to verify property-based tests work."""

import sys
sys.path.insert(0, '.')

print("Importing modules...")
try:
    from hypothesis import given, strategies as st, settings
    from datetime import datetime
    
    from ai_generator.models import (
        TestResult, TestStatus, Environment, EnvironmentStatus,
        HardwareConfig, ArtifactBundle, FailureInfo
    )
    from execution.hardware_config import TestMatrix
    from analysis.compatibility_matrix import (
        CompatibilityMatrixGenerator, MatrixCellStatus
    )
    
    print("✓ All imports successful")
    
    # Define a simple strategy
    @st.composite
    def simple_config_strategy(draw):
        arch = draw(st.sampled_from(['x86_64', 'arm64']))
        return HardwareConfig(
            architecture=arch,
            cpu_model='Test CPU',
            memory_mb=draw(st.sampled_from([1024, 2048])),
            storage_type='ssd',
            peripherals=[],
            is_virtual=True,
            emulator='qemu'
        )
    
    # Define a simple test
    @given(st.lists(simple_config_strategy(), min_size=1, max_size=5))
    @settings(max_examples=10, deadline=None)
    def test_simple_matrix(configs):
        """Simple test that matrix can be created."""
        test_matrix = TestMatrix(configurations=configs)
        
        # Create one result per config
        results = []
        for i, config in enumerate(configs):
            env = Environment(
                id=f"env_{i}",
                config=config,
                status=EnvironmentStatus.IDLE,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            result = TestResult(
                test_id=f"test_{i}",
                status=TestStatus.PASSED,
                execution_time=1.0,
                environment=env,
                artifacts=ArtifactBundle(),
                timestamp=datetime.now()
            )
            results.append(result)
        
        # Generate matrix
        compat_matrix = CompatibilityMatrixGenerator.generate_from_results(
            results,
            hardware_configs=test_matrix.configurations
        )
        
        # Check completeness
        assert len(compat_matrix.cells) == len(test_matrix.configurations)
        
        for cell in compat_matrix.cells:
            assert cell.status is not None
    
    print("\nRunning simple property test...")
    test_simple_matrix()
    print("✓ Simple property test passed!")
    
    print("\n" + "=" * 70)
    print("SUCCESS: Property-based testing framework works!")
    print("=" * 70)
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Test error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
