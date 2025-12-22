#!/usr/bin/env python3
"""Simple test to verify artifact collection property test works."""

import sys
import os
sys.path.append('.')

from tests.property.test_artifact_collection_completeness import *

def test_single_artifact_collection():
    """Test a single artifact collection scenario."""
    try:
        # Generate test data
        strategy = gen_test_result_with_artifacts()
        test_data = strategy.example()
        
        print(f"Generated test data: test_id={test_data[0].test_id}, artifacts={len(test_data[1])}")
        
        # Run the actual test logic
        test_result, created_files, temp_dir = test_data
        
        try:
            # Create artifact collector with temporary storage
            with tempfile.TemporaryDirectory() as storage_dir:
                collector = ArtifactCollector(storage_dir)
                
                # Collect artifacts from test result
                stored_bundle = collector.collect_artifacts(test_result)
                
                # Verify that stored bundle is not None
                assert stored_bundle is not None, "Stored artifact bundle should not be None"
                
                # Count total artifacts in original bundle
                original_artifact_count = (
                    len(test_result.artifacts.logs) +
                    len(test_result.artifacts.core_dumps) +
                    len(test_result.artifacts.traces) +
                    len(test_result.artifacts.screenshots) +
                    len(test_result.artifacts.metadata.get('other_files', []))
                )
                
                # Count total artifacts in stored bundle
                stored_artifact_count = (
                    len(stored_bundle.logs) +
                    len(stored_bundle.core_dumps) +
                    len(stored_bundle.traces) +
                    len(stored_bundle.screenshots) +
                    len(stored_bundle.metadata.get('other_files', []))
                )
                
                print(f"Original artifacts: {original_artifact_count}")
                print(f"Stored artifacts: {stored_artifact_count}")
                
                # Verify all artifacts were stored
                assert stored_artifact_count == original_artifact_count, \
                    f"All artifacts should be stored. Original: {original_artifact_count}, Stored: {stored_artifact_count}"
                
                # Verify artifacts can be retrieved by test ID
                retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
                print(f"Retrieved artifacts: {len(retrieved_artifacts)}")
                
                assert len(retrieved_artifacts) == original_artifact_count, \
                    f"Should be able to retrieve all artifacts. Expected: {original_artifact_count}, Retrieved: {len(retrieved_artifacts)}"
                
                print("✓ Single artifact collection test passed")
                return True
        
        finally:
            # Clean up temporary files
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                
    except Exception as e:
        print(f"✗ Single artifact collection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_property_test_manually():
    """Run the property test manually with multiple examples."""
    try:
        print("Running manual property test with multiple examples...")
        
        strategy = gen_test_result_with_artifacts()
        success_count = 0
        total_tests = 10
        
        for i in range(total_tests):
            try:
                test_data = strategy.example()
                test_result, created_files, temp_dir = test_data
                
                try:
                    # Create artifact collector with temporary storage
                    with tempfile.TemporaryDirectory() as storage_dir:
                        collector = ArtifactCollector(storage_dir)
                        
                        # Collect artifacts from test result
                        stored_bundle = collector.collect_artifacts(test_result)
                        
                        # Count artifacts
                        original_count = (
                            len(test_result.artifacts.logs) +
                            len(test_result.artifacts.core_dumps) +
                            len(test_result.artifacts.traces) +
                            len(test_result.artifacts.screenshots) +
                            len(test_result.artifacts.metadata.get('other_files', []))
                        )
                        
                        stored_count = (
                            len(stored_bundle.logs) +
                            len(stored_bundle.core_dumps) +
                            len(stored_bundle.traces) +
                            len(stored_bundle.screenshots) +
                            len(stored_bundle.metadata.get('other_files', []))
                        )
                        
                        # Verify
                        assert stored_count == original_count
                        
                        retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
                        assert len(retrieved_artifacts) == original_count
                        
                        success_count += 1
                        print(f"  Test {i+1}: ✓ (artifacts: {original_count})")
                
                finally:
                    # Clean up
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        
            except Exception as e:
                print(f"  Test {i+1}: ✗ {e}")
        
        print(f"Manual property test results: {success_count}/{total_tests} passed")
        return success_count == total_tests
        
    except Exception as e:
        print(f"✗ Manual property test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing artifact collection property...")
    
    # Test single case
    single_success = test_single_artifact_collection()
    
    # Test multiple cases manually
    manual_success = run_property_test_manually()
    
    if single_success and manual_success:
        print("✓ All artifact collection property tests passed!")
        sys.exit(0)
    else:
        print("✗ Some artifact collection property tests failed!")
        sys.exit(1)