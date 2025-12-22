"""Property-based tests for artifact collection completeness.

**Feature: test-execution-orchestrator, Property 13: Artifact collection completeness**
**Validates: Requirements 4.4**

Property 13: Artifact collection completeness
For any test that generates artifacts (logs, core dumps, traces, screenshots, etc.), 
the system should collect and store all generated artifacts completely and make them 
retrievable.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
from typing import Dict, Any, Optional, List
import tempfile
import os
import time
import shutil
from pathlib import Path

from ai_generator.models import (
    TestCase, TestType, TestStatus, Environment, HardwareConfig,
    ArtifactBundle, FailureInfo, EnvironmentStatus, TestResult
)
from execution.artifact_collector import ArtifactCollector, ArtifactMetadata


# Custom strategies for generating test data
@st.composite
def gen_test_id(draw):
    """Generate a random test ID with safe characters."""
    return draw(st.text(min_size=1, max_size=36, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'))


@st.composite
def gen_artifact_content(draw):
    """Generate random artifact content with safe characters."""
    return draw(st.text(min_size=1, max_size=1000, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-_()[]{}'))


@st.composite
def gen_artifact_filename(draw):
    """Generate a random artifact filename with safe characters."""
    base_name = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'))
    extension = draw(st.sampled_from(['.log', '.txt', '.core', '.trace', '.png', '.json', '.xml']))
    return f"{base_name}{extension}"


@st.composite
def gen_artifact_type(draw):
    """Generate a random artifact type."""
    return draw(st.sampled_from(['log', 'core_dump', 'trace', 'screenshot', 'other']))


@st.composite
def gen_artifact_files(draw):
    """Generate a list of artifact files with content and unique filenames."""
    num_artifacts = draw(st.integers(min_value=1, max_value=10))
    artifacts = []
    used_filenames = set()
    
    for i in range(num_artifacts):
        # Generate unique filename
        attempts = 0
        while attempts < 10:  # Prevent infinite loop
            filename = draw(gen_artifact_filename())
            if filename not in used_filenames:
                used_filenames.add(filename)
                break
            attempts += 1
        else:
            # If we can't generate a unique name, use index-based name
            filename = f"artifact_{i}.log"
        
        content = draw(gen_artifact_content())
        artifact_type = draw(gen_artifact_type())
        artifacts.append((filename, content, artifact_type))
    
    return artifacts


@st.composite
def gen_test_result_with_artifacts(draw):
    """Generate a test result with various artifacts."""
    test_id = draw(gen_test_id())
    status = draw(st.sampled_from([TestStatus.PASSED, TestStatus.FAILED]))
    
    # Generate artifact files
    artifact_files = draw(gen_artifact_files())
    
    # Create temporary files for artifacts
    temp_dir = tempfile.mkdtemp()
    artifact_bundle = ArtifactBundle()
    created_files = []
    
    for filename, content, artifact_type in artifact_files:
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        created_files.append((file_path, content, artifact_type))
        
        # Add to appropriate artifact bundle list
        if artifact_type == 'log':
            artifact_bundle.logs.append(file_path)
        elif artifact_type == 'core_dump':
            artifact_bundle.core_dumps.append(file_path)
        elif artifact_type == 'trace':
            artifact_bundle.traces.append(file_path)
        elif artifact_type == 'screenshot':
            artifact_bundle.screenshots.append(file_path)
        else:
            # Add to metadata as other files
            if 'other_files' not in artifact_bundle.metadata:
                artifact_bundle.metadata['other_files'] = []
            artifact_bundle.metadata['other_files'].append(file_path)
    
    # Create environment
    hardware_config = draw(gen_hardware_config())
    environment = Environment(
        id=f"env_{test_id}",
        config=hardware_config,
        status=EnvironmentStatus.IDLE
    )
    
    test_result = TestResult(
        test_id=test_id,
        status=status,
        execution_time=1.5,
        environment=environment,
        artifacts=artifact_bundle,
        timestamp=datetime.now()
    )
    
    return test_result, created_files, temp_dir


@st.composite
def gen_hardware_config(draw):
    """Generate a random hardware configuration."""
    return HardwareConfig(
        architecture=draw(st.sampled_from(["x86_64", "arm64", "arm"])),
        cpu_model=draw(st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')),
        memory_mb=draw(st.integers(min_value=512, max_value=8192)),
        is_virtual=True,
        emulator="qemu"
    )


@given(gen_test_result_with_artifacts())
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_artifact_collection_stores_all_generated_artifacts(test_result_data):
    """
    Property: For any test result with generated artifacts, the artifact collector 
    should store all artifacts and make them retrievable.
    
    **Feature: test-execution-orchestrator, Property 13: Artifact collection completeness**
    **Validates: Requirements 4.4**
    """
    test_result, created_files, temp_dir = test_result_data
    
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
            
            # Verify all artifacts were stored
            assert stored_artifact_count == original_artifact_count, \
                f"All artifacts should be stored. Original: {original_artifact_count}, Stored: {stored_artifact_count}"
            
            # Verify artifacts can be retrieved by test ID
            retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
            assert len(retrieved_artifacts) == original_artifact_count, \
                f"Should be able to retrieve all artifacts. Expected: {original_artifact_count}, Retrieved: {len(retrieved_artifacts)}"
            
            # Verify each artifact type is preserved
            if test_result.artifacts.logs:
                assert len(stored_bundle.logs) == len(test_result.artifacts.logs), \
                    "All log artifacts should be stored"
                
            if test_result.artifacts.core_dumps:
                assert len(stored_bundle.core_dumps) == len(test_result.artifacts.core_dumps), \
                    "All core dump artifacts should be stored"
                
            if test_result.artifacts.traces:
                assert len(stored_bundle.traces) == len(test_result.artifacts.traces), \
                    "All trace artifacts should be stored"
                
            if test_result.artifacts.screenshots:
                assert len(stored_bundle.screenshots) == len(test_result.artifacts.screenshots), \
                    "All screenshot artifacts should be stored"
            
            # Verify stored artifacts exist as files
            for artifact_metadata in retrieved_artifacts:
                stored_path = Path(artifact_metadata.file_path)
                assert stored_path.exists(), f"Stored artifact file should exist: {stored_path}"
                assert stored_path.is_file(), f"Stored artifact should be a file: {stored_path}"
                assert stored_path.stat().st_size > 0, f"Stored artifact should not be empty: {stored_path}"
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@given(gen_test_result_with_artifacts())
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_artifact_collection_preserves_content_integrity(test_result_data):
    """
    Property: For any test artifacts, the artifact collector should preserve 
    the exact content of each artifact without modification.
    
    **Feature: test-execution-orchestrator, Property 13: Artifact collection completeness**
    **Validates: Requirements 4.4**
    """
    test_result, created_files, temp_dir = test_result_data
    
    try:
        # Create artifact collector with temporary storage
        with tempfile.TemporaryDirectory() as storage_dir:
            collector = ArtifactCollector(storage_dir)
            
            # Collect artifacts from test result
            stored_bundle = collector.collect_artifacts(test_result)
            
            # Verify content integrity for each created file
            for original_path, expected_content, artifact_type in created_files:
                # Find the corresponding stored artifact
                retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
                
                # Find artifact by matching original filename
                original_filename = os.path.basename(original_path)
                matching_artifacts = [
                    artifact for artifact in retrieved_artifacts
                    if original_filename in artifact.file_path and artifact.artifact_type == artifact_type
                ]
                
                assert len(matching_artifacts) >= 1, \
                    f"Should find stored artifact for {original_filename} of type {artifact_type}"
                
                # Verify content of the first matching artifact
                stored_artifact = matching_artifacts[0]
                stored_path = Path(stored_artifact.file_path)
                
                assert stored_path.exists(), f"Stored artifact should exist: {stored_path}"
                
                # Read and compare content
                with open(stored_path, 'r') as f:
                    stored_content = f.read()
                
                assert stored_content == expected_content, \
                    f"Stored content should match original for {original_filename}. " \
                    f"Expected: '{expected_content}', Got: '{stored_content}'"
                
                # Verify file size matches
                expected_size = len(expected_content.encode('utf-8'))
                actual_size = stored_path.stat().st_size
                assert actual_size >= expected_size, \
                    f"Stored file size should be at least as large as content for {original_filename}"
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@given(gen_test_result_with_artifacts())
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_artifact_collection_generates_proper_metadata(test_result_data):
    """
    Property: For any collected artifacts, the artifact collector should generate 
    proper metadata including checksums, timestamps, and type information.
    
    **Feature: test-execution-orchestrator, Property 13: Artifact collection completeness**
    **Validates: Requirements 4.4**
    """
    test_result, created_files, temp_dir = test_result_data
    
    try:
        # Create artifact collector with temporary storage
        with tempfile.TemporaryDirectory() as storage_dir:
            collector = ArtifactCollector(storage_dir)
            
            # Collect artifacts from test result
            stored_bundle = collector.collect_artifacts(test_result)
            
            # Retrieve artifact metadata
            retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
            
            # Verify metadata for each artifact
            for artifact_metadata in retrieved_artifacts:
                # Verify required metadata fields
                assert artifact_metadata.artifact_id is not None, "artifact_id should be set"
                assert len(artifact_metadata.artifact_id) > 0, "artifact_id should not be empty"
                
                assert artifact_metadata.test_id == test_result.test_id, \
                    f"test_id should match. Expected: {test_result.test_id}, Got: {artifact_metadata.test_id}"
                
                assert artifact_metadata.artifact_type in ['log', 'core_dump', 'trace', 'screenshot', 'other'], \
                    f"artifact_type should be valid: {artifact_metadata.artifact_type}"
                
                assert artifact_metadata.file_path is not None, "file_path should be set"
                assert len(artifact_metadata.file_path) > 0, "file_path should not be empty"
                
                assert artifact_metadata.file_size > 0, "file_size should be positive"
                
                assert artifact_metadata.checksum is not None, "checksum should be set"
                assert len(artifact_metadata.checksum) > 0, "checksum should not be empty"
                
                assert artifact_metadata.created_at is not None, "created_at should be set"
                assert isinstance(artifact_metadata.created_at, datetime), "created_at should be datetime"
                
                # Verify checksum is valid (should be hex string)
                try:
                    int(artifact_metadata.checksum, 16)
                except ValueError:
                    pytest.fail(f"checksum should be valid hex string: {artifact_metadata.checksum}")
                
                # Verify file actually exists and size matches
                stored_path = Path(artifact_metadata.file_path)
                assert stored_path.exists(), f"Stored file should exist: {stored_path}"
                
                actual_size = stored_path.stat().st_size
                assert actual_size == artifact_metadata.file_size, \
                    f"File size should match metadata. Expected: {artifact_metadata.file_size}, Actual: {actual_size}"
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@st.composite
def gen_multiple_test_results_with_unique_ids(draw):
    """Generate multiple test results with unique test IDs."""
    num_tests = draw(st.integers(min_value=2, max_value=5))
    test_results = []
    used_test_ids = set()
    
    for i in range(num_tests):
        # Generate unique test ID
        attempts = 0
        while attempts < 10:
            test_id = draw(gen_test_id())
            if test_id not in used_test_ids:
                used_test_ids.add(test_id)
                break
            attempts += 1
        else:
            # Fallback to index-based ID
            test_id = f"test_{i}"
        
        # Generate test result with unique ID
        status = draw(st.sampled_from([TestStatus.PASSED, TestStatus.FAILED]))
        artifact_files = draw(gen_artifact_files())
        
        # Create temporary files for artifacts
        temp_dir = tempfile.mkdtemp()
        artifact_bundle = ArtifactBundle()
        created_files = []
        
        for filename, content, artifact_type in artifact_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
            created_files.append((file_path, content, artifact_type))
            
            # Add to appropriate artifact bundle list
            if artifact_type == 'log':
                artifact_bundle.logs.append(file_path)
            elif artifact_type == 'core_dump':
                artifact_bundle.core_dumps.append(file_path)
            elif artifact_type == 'trace':
                artifact_bundle.traces.append(file_path)
            elif artifact_type == 'screenshot':
                artifact_bundle.screenshots.append(file_path)
            else:
                # Add to metadata as other files
                if 'other_files' not in artifact_bundle.metadata:
                    artifact_bundle.metadata['other_files'] = []
                artifact_bundle.metadata['other_files'].append(file_path)
        
        # Create environment
        hardware_config = draw(gen_hardware_config())
        environment = Environment(
            id=f"env_{test_id}",
            config=hardware_config,
            status=EnvironmentStatus.IDLE
        )
        
        test_result = TestResult(
            test_id=test_id,  # Use the unique test ID
            status=status,
            execution_time=1.5,
            environment=environment,
            artifacts=artifact_bundle,
            timestamp=datetime.now()
        )
        
        test_results.append((test_result, created_files, temp_dir))
    
    return test_results


@given(gen_multiple_test_results_with_unique_ids())
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_artifact_collection_handles_multiple_tests_independently(test_results_data):
    """
    Property: For any collection of test results with artifacts, the artifact 
    collector should handle each test's artifacts independently without interference.
    
    **Feature: test-execution-orchestrator, Property 13: Artifact collection completeness**
    **Validates: Requirements 4.4**
    """
    temp_dirs = []
    
    try:
        # Create artifact collector with temporary storage
        with tempfile.TemporaryDirectory() as storage_dir:
            collector = ArtifactCollector(storage_dir)
            
            # Process each test result
            test_artifact_counts = {}
            
            for test_result, created_files, temp_dir in test_results_data:
                temp_dirs.append(temp_dir)
                
                # Count artifacts for this test
                original_count = (
                    len(test_result.artifacts.logs) +
                    len(test_result.artifacts.core_dumps) +
                    len(test_result.artifacts.traces) +
                    len(test_result.artifacts.screenshots) +
                    len(test_result.artifacts.metadata.get('other_files', []))
                )
                test_artifact_counts[test_result.test_id] = original_count
                
                # Collect artifacts
                stored_bundle = collector.collect_artifacts(test_result)
                assert stored_bundle is not None, f"Should store artifacts for test {test_result.test_id}"
            
            # Verify each test's artifacts are stored independently
            for test_result, created_files, temp_dir in test_results_data:
                retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
                expected_count = test_artifact_counts[test_result.test_id]
                
                assert len(retrieved_artifacts) == expected_count, \
                    f"Test {test_result.test_id} should have {expected_count} artifacts, got {len(retrieved_artifacts)}"
                
                # Verify all retrieved artifacts belong to this test
                for artifact in retrieved_artifacts:
                    assert artifact.test_id == test_result.test_id, \
                        f"Artifact should belong to test {test_result.test_id}, got {artifact.test_id}"
            
            # Verify total artifact count across all tests
            all_artifacts = []
            for test_result, _, _ in test_results_data:
                test_artifacts = collector.get_artifacts_for_test(test_result.test_id)
                all_artifacts.extend(test_artifacts)
            
            expected_total = sum(test_artifact_counts.values())
            assert len(all_artifacts) == expected_total, \
                f"Total artifacts should be {expected_total}, got {len(all_artifacts)}"
            
            # Verify no artifact ID collisions
            artifact_ids = [artifact.artifact_id for artifact in all_artifacts]
            unique_ids = set(artifact_ids)
            assert len(artifact_ids) == len(unique_ids), \
                "All artifact IDs should be unique across tests"
    
    finally:
        # Clean up temporary files
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


@given(gen_test_result_with_artifacts())
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_artifact_collection_handles_missing_source_files_gracefully(test_result_data):
    """
    Property: For any test result where some artifact source files are missing, 
    the artifact collector should handle missing files gracefully and still 
    collect available artifacts.
    
    **Feature: test-execution-orchestrator, Property 13: Artifact collection completeness**
    **Validates: Requirements 4.4**
    """
    test_result, created_files, temp_dir = test_result_data
    
    try:
        # Remove some of the created files to simulate missing artifacts
        files_to_remove = created_files[::2]  # Remove every other file
        remaining_files = created_files[1::2]  # Keep the rest
        
        for file_path, _, _ in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Create artifact collector with temporary storage
        with tempfile.TemporaryDirectory() as storage_dir:
            collector = ArtifactCollector(storage_dir)
            
            # Collect artifacts from test result (some files are now missing)
            stored_bundle = collector.collect_artifacts(test_result)
            
            # Verify that collection doesn't fail
            assert stored_bundle is not None, "Artifact collection should not fail with missing files"
            
            # Verify that available artifacts are still collected
            retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
            
            # Count how many artifacts should have been collected (only existing files)
            expected_collected = len(remaining_files)
            
            # Allow for the case where all files were removed
            if expected_collected == 0:
                assert len(retrieved_artifacts) == 0, "No artifacts should be collected if all files are missing"
            else:
                assert len(retrieved_artifacts) <= expected_collected, \
                    f"Should collect at most {expected_collected} artifacts, got {len(retrieved_artifacts)}"
                
                # Verify that collected artifacts correspond to existing files
                for artifact in retrieved_artifacts:
                    stored_path = Path(artifact.file_path)
                    assert stored_path.exists(), f"Collected artifact should exist: {stored_path}"
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@given(gen_test_result_with_artifacts())
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_artifact_collection_supports_retrieval_by_artifact_id(test_result_data):
    """
    Property: For any collected artifact, the artifact collector should support 
    retrieval by artifact ID and return the correct artifact.
    
    **Feature: test-execution-orchestrator, Property 13: Artifact collection completeness**
    **Validates: Requirements 4.4**
    """
    test_result, created_files, temp_dir = test_result_data
    
    try:
        # Create artifact collector with temporary storage
        with tempfile.TemporaryDirectory() as storage_dir:
            collector = ArtifactCollector(storage_dir)
            
            # Collect artifacts from test result
            stored_bundle = collector.collect_artifacts(test_result)
            
            # Get all artifacts for the test
            retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
            
            # Test retrieval by artifact ID for each artifact
            for artifact_metadata in retrieved_artifacts:
                # Retrieve by ID
                retrieved_by_id = collector.get_artifact_by_id(artifact_metadata.artifact_id)
                
                assert retrieved_by_id is not None, \
                    f"Should be able to retrieve artifact by ID: {artifact_metadata.artifact_id}"
                
                # Verify it's the same artifact
                assert retrieved_by_id.artifact_id == artifact_metadata.artifact_id, \
                    "Retrieved artifact should have matching ID"
                
                assert retrieved_by_id.test_id == artifact_metadata.test_id, \
                    "Retrieved artifact should have matching test_id"
                
                assert retrieved_by_id.file_path == artifact_metadata.file_path, \
                    "Retrieved artifact should have matching file_path"
                
                assert retrieved_by_id.artifact_type == artifact_metadata.artifact_type, \
                    "Retrieved artifact should have matching artifact_type"
                
                assert retrieved_by_id.checksum == artifact_metadata.checksum, \
                    "Retrieved artifact should have matching checksum"
                
                # Test actual file retrieval
                retrieved_file_path = collector.retrieve_artifact(artifact_metadata.artifact_id)
                assert retrieved_file_path is not None, \
                    f"Should be able to retrieve artifact file: {artifact_metadata.artifact_id}"
                
                retrieved_path = Path(retrieved_file_path)
                assert retrieved_path.exists(), f"Retrieved file should exist: {retrieved_path}"
                assert retrieved_path.is_file(), f"Retrieved path should be a file: {retrieved_path}"
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@given(gen_test_result_with_artifacts())
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_artifact_collection_maintains_type_organization(test_result_data):
    """
    Property: For any test artifacts of different types, the artifact collector 
    should maintain proper type organization and categorization.
    
    **Feature: test-execution-orchestrator, Property 13: Artifact collection completeness**
    **Validates: Requirements 4.4**
    """
    test_result, created_files, temp_dir = test_result_data
    
    try:
        # Create artifact collector with temporary storage
        with tempfile.TemporaryDirectory() as storage_dir:
            collector = ArtifactCollector(storage_dir)
            
            # Collect artifacts from test result
            stored_bundle = collector.collect_artifacts(test_result)
            
            # Get all artifacts for the test
            retrieved_artifacts = collector.get_artifacts_for_test(test_result.test_id)
            
            # Group artifacts by type
            artifacts_by_type = {}
            for artifact in retrieved_artifacts:
                artifact_type = artifact.artifact_type
                if artifact_type not in artifacts_by_type:
                    artifacts_by_type[artifact_type] = []
                artifacts_by_type[artifact_type].append(artifact)
            
            # Verify type organization matches original
            original_types = set()
            for _, _, artifact_type in created_files:
                original_types.add(artifact_type)
            
            collected_types = set(artifacts_by_type.keys())
            
            # All original types should be represented (if files existed)
            for original_type in original_types:
                if any(os.path.exists(file_path) for file_path, _, file_type in created_files if file_type == original_type):
                    assert original_type in collected_types, \
                        f"Artifact type {original_type} should be collected"
            
            # Verify each artifact has correct type assignment
            for artifact_type, artifacts in artifacts_by_type.items():
                for artifact in artifacts:
                    assert artifact.artifact_type == artifact_type, \
                        f"Artifact should have correct type: expected {artifact_type}, got {artifact.artifact_type}"
                    
                    # Verify file is stored in appropriate location
                    stored_path = Path(artifact.file_path)
                    assert stored_path.exists(), f"Artifact file should exist: {stored_path}"
                    
                    # Verify path structure includes test ID
                    assert test_result.test_id in str(stored_path), \
                        f"Artifact path should include test ID: {stored_path}"
    
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)