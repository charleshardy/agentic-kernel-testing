"""Unit tests for historical failure database."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from analysis.historical_failure_db import (
    HistoricalFailureDatabase,
    FailurePattern,
    PatternMatcher
)
from ai_generator.models import (
    TestResult, TestStatus, Environment, HardwareConfig,
    FailureInfo, FailureAnalysis, ArtifactBundle
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        db_path = f.name
    
    db = HistoricalFailureDatabase(db_path)
    yield db
    db.close()
    
    # Clean up
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_pattern():
    """Create a sample failure pattern."""
    return FailurePattern(
        pattern_id="pattern_001",
        signature="abc123def456",
        error_pattern="null_pointer",
        root_cause="NULL pointer dereference in network driver",
        occurrence_count=5,
        first_seen=datetime.now() - timedelta(days=7),
        last_seen=datetime.now() - timedelta(days=1)
    )


@pytest.fixture
def sample_test_result():
    """Create a sample test result with failure."""
    env = Environment(
        id="env_001",
        config=HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel Core i7",
            memory_mb=8192
        )
    )
    
    failure_info = FailureInfo(
        error_message="NULL pointer dereference at address 0x0000000000000000",
        stack_trace="kernel_function+0x42/0x100\ndriver_init+0x10/0x50",
        kernel_panic=True
    )
    
    return TestResult(
        test_id="test_001",
        status=TestStatus.FAILED,
        execution_time=10.5,
        environment=env,
        failure_info=failure_info,
        artifacts=ArtifactBundle()
    )


def test_database_initialization(temp_db):
    """Test database initialization creates tables."""
    cursor = temp_db.conn.cursor()
    
    # Check failure_patterns table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='failure_patterns'
    """)
    assert cursor.fetchone() is not None
    
    # Check failure_instances table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='failure_instances'
    """)
    assert cursor.fetchone() is not None


def test_store_failure_pattern(temp_db, sample_pattern):
    """Test storing a failure pattern."""
    temp_db.store_failure_pattern(sample_pattern)
    
    # Verify it was stored
    retrieved = temp_db.lookup_by_pattern_id(sample_pattern.pattern_id)
    assert retrieved is not None
    assert retrieved.pattern_id == sample_pattern.pattern_id
    assert retrieved.signature == sample_pattern.signature
    assert retrieved.error_pattern == sample_pattern.error_pattern
    assert retrieved.root_cause == sample_pattern.root_cause


def test_store_duplicate_pattern_updates_count(temp_db, sample_pattern):
    """Test storing duplicate pattern increments occurrence count."""
    # Store pattern twice
    temp_db.store_failure_pattern(sample_pattern)
    temp_db.store_failure_pattern(sample_pattern)
    
    # Check occurrence count increased
    cursor = temp_db.conn.cursor()
    cursor.execute(
        "SELECT occurrence_count FROM failure_patterns WHERE signature = ?",
        (sample_pattern.signature,)
    )
    count = cursor.fetchone()[0]
    assert count == 6  # Original 5 + 1


def test_store_failure_instance(temp_db, sample_pattern, sample_test_result):
    """Test storing a failure instance."""
    # First store the pattern
    temp_db.store_failure_pattern(sample_pattern)
    
    # Then store an instance
    temp_db.store_failure_instance(
        instance_id="instance_001",
        pattern_id=sample_pattern.pattern_id,
        test_result=sample_test_result
    )
    
    # Verify instance was stored
    instances = temp_db.get_pattern_instances(sample_pattern.pattern_id)
    assert len(instances) == 1
    assert instances[0]['instance_id'] == "instance_001"
    assert instances[0]['test_id'] == sample_test_result.test_id


def test_find_matching_patterns_by_signature(temp_db, sample_pattern):
    """Test finding patterns by signature."""
    temp_db.store_failure_pattern(sample_pattern)
    
    matches = temp_db.find_matching_patterns(signature=sample_pattern.signature)
    assert len(matches) == 1
    assert matches[0].signature == sample_pattern.signature


def test_find_matching_patterns_by_error_pattern(temp_db):
    """Test finding patterns by error pattern type."""
    # Store multiple patterns with same error pattern
    for i in range(3):
        pattern = FailurePattern(
            pattern_id=f"pattern_{i}",
            signature=f"sig_{i}",
            error_pattern="null_pointer",
            root_cause=f"NULL pointer in module {i}"
        )
        temp_db.store_failure_pattern(pattern)
    
    matches = temp_db.find_matching_patterns(
        signature="nonexistent",
        error_pattern="null_pointer"
    )
    assert len(matches) == 3


def test_update_resolution(temp_db, sample_pattern):
    """Test updating pattern resolution."""
    temp_db.store_failure_pattern(sample_pattern)
    
    resolution = "Fixed by adding NULL check in driver initialization"
    success = temp_db.update_resolution(
        pattern_id=sample_pattern.pattern_id,
        resolution=resolution
    )
    
    assert success is True
    
    # Verify resolution was stored
    retrieved = temp_db.lookup_by_pattern_id(sample_pattern.pattern_id)
    assert retrieved.resolution == resolution
    assert retrieved.resolution_date is not None


def test_get_resolved_patterns(temp_db):
    """Test retrieving resolved patterns."""
    # Store resolved and unresolved patterns
    resolved_pattern = FailurePattern(
        pattern_id="resolved_001",
        signature="sig_resolved",
        error_pattern="null_pointer",
        root_cause="Fixed issue",
        resolution="Added NULL check"
    )
    
    unresolved_pattern = FailurePattern(
        pattern_id="unresolved_001",
        signature="sig_unresolved",
        error_pattern="deadlock",
        root_cause="Deadlock in scheduler"
    )
    
    temp_db.store_failure_pattern(resolved_pattern)
    temp_db.store_failure_pattern(unresolved_pattern)
    temp_db.update_resolution(resolved_pattern.pattern_id, "Fixed")
    
    resolved = temp_db.get_resolved_patterns()
    assert len(resolved) == 1
    assert resolved[0].pattern_id == resolved_pattern.pattern_id


def test_get_unresolved_patterns(temp_db):
    """Test retrieving unresolved patterns."""
    # Store patterns with different occurrence counts
    for i in range(3):
        pattern = FailurePattern(
            pattern_id=f"pattern_{i}",
            signature=f"sig_{i}",
            error_pattern="race_condition",
            root_cause=f"Race condition {i}",
            occurrence_count=i + 1
        )
        temp_db.store_failure_pattern(pattern)
    
    # Get unresolved with min occurrences
    unresolved = temp_db.get_unresolved_patterns(min_occurrences=2)
    assert len(unresolved) == 2  # Only patterns with 2+ occurrences


def test_search_by_root_cause(temp_db):
    """Test searching patterns by root cause."""
    patterns = [
        FailurePattern(
            pattern_id="p1",
            signature="s1",
            error_pattern="null_pointer",
            root_cause="NULL pointer in network driver"
        ),
        FailurePattern(
            pattern_id="p2",
            signature="s2",
            error_pattern="null_pointer",
            root_cause="NULL pointer in filesystem"
        ),
        FailurePattern(
            pattern_id="p3",
            signature="s3",
            error_pattern="deadlock",
            root_cause="Deadlock in scheduler"
        )
    ]
    
    for pattern in patterns:
        temp_db.store_failure_pattern(pattern)
    
    # Search for "network"
    results = temp_db.search_by_root_cause("network")
    assert len(results) == 1
    assert results[0].pattern_id == "p1"
    
    # Search for "NULL pointer"
    results = temp_db.search_by_root_cause("NULL pointer")
    assert len(results) == 2


def test_get_statistics(temp_db):
    """Test getting database statistics."""
    # Store some patterns
    for i in range(5):
        pattern = FailurePattern(
            pattern_id=f"pattern_{i}",
            signature=f"sig_{i}",
            error_pattern="null_pointer" if i < 3 else "deadlock",
            root_cause=f"Issue {i}"
        )
        temp_db.store_failure_pattern(pattern)
    
    # Resolve some patterns
    temp_db.update_resolution("pattern_0", "Fixed")
    temp_db.update_resolution("pattern_1", "Fixed")
    
    stats = temp_db.get_statistics()
    
    assert stats['total_patterns'] == 5
    assert stats['resolved_patterns'] == 2
    assert stats['unresolved_patterns'] == 3
    assert stats['resolution_rate'] == 0.4
    assert len(stats['common_error_patterns']) > 0


def test_pattern_matcher_exact_match(temp_db, sample_pattern):
    """Test pattern matcher with exact signature match."""
    temp_db.store_failure_pattern(sample_pattern)
    
    matcher = PatternMatcher(temp_db)
    
    failure_analysis = FailureAnalysis(
        failure_id="fail_001",
        root_cause="NULL pointer dereference",
        confidence=0.9,
        error_pattern="null_pointer"
    )
    
    matches = matcher.match_failure(failure_analysis, sample_pattern.signature)
    
    assert len(matches) > 0
    assert matches[0][1] == 1.0  # Exact match score
    assert matches[0][0].pattern_id == sample_pattern.pattern_id


def test_pattern_matcher_error_pattern_match(temp_db):
    """Test pattern matcher with error pattern match."""
    pattern = FailurePattern(
        pattern_id="pattern_001",
        signature="different_sig",
        error_pattern="null_pointer",
        root_cause="NULL pointer dereference in driver initialization"
    )
    temp_db.store_failure_pattern(pattern)
    
    matcher = PatternMatcher(temp_db)
    
    failure_analysis = FailureAnalysis(
        failure_id="fail_001",
        root_cause="NULL pointer dereference in driver startup",
        confidence=0.9,
        error_pattern="null_pointer"
    )
    
    matches = matcher.match_failure(failure_analysis, "nonexistent_sig")
    
    assert len(matches) > 0
    assert matches[0][1] > 0.3  # Similarity threshold
    assert matches[0][0].error_pattern == "null_pointer"


def test_pattern_to_dict_and_from_dict():
    """Test FailurePattern serialization."""
    pattern = FailurePattern(
        pattern_id="test_pattern",
        signature="test_sig",
        error_pattern="null_pointer",
        root_cause="Test root cause",
        occurrence_count=3,
        metadata={"key": "value"}
    )
    
    # Convert to dict and back
    pattern_dict = pattern.to_dict()
    restored = FailurePattern.from_dict(pattern_dict)
    
    assert restored.pattern_id == pattern.pattern_id
    assert restored.signature == pattern.signature
    assert restored.error_pattern == pattern.error_pattern
    assert restored.root_cause == pattern.root_cause
    assert restored.occurrence_count == pattern.occurrence_count
    assert restored.metadata == pattern.metadata


def test_context_manager(temp_db):
    """Test database context manager."""
    db_path = temp_db.db_path
    temp_db.close()
    
    with HistoricalFailureDatabase(db_path) as db:
        pattern = FailurePattern(
            pattern_id="test",
            signature="sig",
            error_pattern="test",
            root_cause="test"
        )
        db.store_failure_pattern(pattern)
    
    # Database should be closed after context
    # Reopen to verify data was saved
    with HistoricalFailureDatabase(db_path) as db:
        retrieved = db.lookup_by_pattern_id("test")
        assert retrieved is not None
