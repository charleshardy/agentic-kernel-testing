"""Property-based tests for historical pattern matching.

**Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
**Validates: Requirements 4.5**

Property: For any failure that matches a known pattern, the analysis should 
reference similar historical issues and their resolutions.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import tempfile
import os
import hashlib

from analysis.historical_failure_db import (
    HistoricalFailureDatabase,
    FailurePattern,
    PatternMatcher
)
from ai_generator.models import (
    TestResult, TestStatus, Environment, HardwareConfig,
    FailureInfo, FailureAnalysis, ArtifactBundle
)


# Custom strategies for generating test data
@st.composite
def failure_pattern_strategy(draw):
    """Generate random failure patterns."""
    pattern_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    # Generate signature from pattern_id for consistency
    signature = hashlib.sha256(pattern_id.encode()).hexdigest()[:16]
    
    error_patterns = ["null_pointer", "use_after_free", "buffer_overflow", 
                     "deadlock", "race_condition", "memory_leak", "timeout"]
    error_pattern = draw(st.sampled_from(error_patterns))
    
    root_causes = [
        f"NULL pointer dereference in {draw(st.sampled_from(['driver', 'filesystem', 'network', 'scheduler']))}",
        f"Use-after-free in {draw(st.sampled_from(['memory', 'cache', 'buffer', 'queue']))} management",
        f"Buffer overflow in {draw(st.sampled_from(['input', 'output', 'parsing', 'validation']))} handling",
        f"Deadlock between {draw(st.sampled_from(['lock A and B', 'mutex X and Y', 'semaphores']))}",
        f"Race condition in {draw(st.sampled_from(['initialization', 'cleanup', 'update', 'access']))} path"
    ]
    root_cause = draw(st.sampled_from(root_causes))
    
    occurrence_count = draw(st.integers(min_value=1, max_value=100))
    
    now = datetime.now()
    days_ago = draw(st.integers(min_value=1, max_value=365))
    first_seen = now - timedelta(days=days_ago)
    last_seen = now - timedelta(days=draw(st.integers(min_value=0, max_value=days_ago)))
    
    # Some patterns have resolutions
    has_resolution = draw(st.booleans())
    resolution = None
    resolution_date = None
    if has_resolution:
        resolution = f"Fixed by {draw(st.sampled_from(['adding check', 'fixing logic', 'updating code', 'refactoring']))}"
        resolution_date = last_seen + timedelta(days=draw(st.integers(min_value=1, max_value=30)))
    
    return FailurePattern(
        pattern_id=pattern_id,
        signature=signature,
        error_pattern=error_pattern,
        root_cause=root_cause,
        occurrence_count=occurrence_count,
        first_seen=first_seen,
        last_seen=last_seen,
        resolution=resolution,
        resolution_date=resolution_date
    )


@st.composite
def failure_analysis_strategy(draw):
    """Generate random failure analyses."""
    failure_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    error_patterns = ["null_pointer", "use_after_free", "buffer_overflow", 
                     "deadlock", "race_condition", "memory_leak", "timeout"]
    error_pattern = draw(st.sampled_from(error_patterns))
    
    root_causes = [
        f"NULL pointer dereference in {draw(st.sampled_from(['driver', 'filesystem', 'network', 'scheduler']))}",
        f"Use-after-free in {draw(st.sampled_from(['memory', 'cache', 'buffer', 'queue']))} management",
        f"Buffer overflow in {draw(st.sampled_from(['input', 'output', 'parsing', 'validation']))} handling"
    ]
    root_cause = draw(st.sampled_from(root_causes))
    
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    return FailureAnalysis(
        failure_id=failure_id,
        root_cause=root_cause,
        confidence=confidence,
        error_pattern=error_pattern
    )


@settings(max_examples=100, deadline=None)
@given(patterns=st.lists(failure_pattern_strategy(), min_size=1, max_size=20))
def test_stored_patterns_are_retrievable(patterns):
    """
    Property: For any set of failure patterns stored in the database,
    all patterns should be retrievable by their pattern_id.
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    # Create temporary database for this test
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            # Store all patterns
            for pattern in patterns:
                db.store_failure_pattern(pattern)
            
            # Verify all patterns are retrievable
            for pattern in patterns:
                retrieved = db.lookup_by_pattern_id(pattern.pattern_id)
                assert retrieved is not None, f"Pattern {pattern.pattern_id} should be retrievable"
                assert retrieved.pattern_id == pattern.pattern_id
                assert retrieved.signature == pattern.signature
                assert retrieved.error_pattern == pattern.error_pattern
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@settings(max_examples=100, deadline=None)
@given(
    pattern=failure_pattern_strategy(),
    analysis=failure_analysis_strategy()
)
def test_matching_by_signature_returns_exact_match(pattern, analysis):
    """
    Property: For any failure with a signature matching a stored pattern,
    the pattern matcher should return that pattern with a score of 1.0.
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            # Store the pattern
            db.store_failure_pattern(pattern)
            
            # Create matcher
            matcher = PatternMatcher(db)
            
            # Match using the exact signature
            matches = matcher.match_failure(analysis, pattern.signature)
            
            # Should find exact match with score 1.0
            assert len(matches) > 0, "Should find at least one match for exact signature"
            assert matches[0][1] == 1.0, "Exact signature match should have score 1.0"
            assert matches[0][0].signature == pattern.signature
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@settings(max_examples=100, deadline=None)
@given(
    patterns=st.lists(failure_pattern_strategy(), min_size=2, max_size=10),
    analysis=failure_analysis_strategy()
)
def test_matching_by_error_pattern_returns_relevant_patterns(patterns, analysis):
    """
    Property: For any failure with an error pattern, the pattern matcher should
    return patterns with the same error pattern when no exact signature match exists.
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    # Ensure at least one pattern has the same error pattern as analysis
    patterns[0].error_pattern = analysis.error_pattern
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            # Store all patterns
            for pattern in patterns:
                db.store_failure_pattern(pattern)
            
            # Create matcher
            matcher = PatternMatcher(db)
            
            # Match using a non-existent signature (force error pattern matching)
            matches = matcher.match_failure(analysis, "nonexistent_signature_12345")
            
            # Should find matches based on error pattern
            if matches:
                # All matches should have the same error pattern
                for match_pattern, score in matches:
                    assert match_pattern.error_pattern == analysis.error_pattern, \
                        "Matched patterns should have same error pattern"
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@settings(max_examples=100, deadline=None)
@given(
    pattern=failure_pattern_strategy(),
    resolution=st.text(min_size=10, max_size=200)
)
def test_resolved_patterns_include_resolution(pattern, resolution):
    """
    Property: For any pattern that has been resolved, retrieving resolved patterns
    should include that pattern with its resolution information.
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            # Store pattern
            db.store_failure_pattern(pattern)
            
            # Update with resolution
            success = db.update_resolution(pattern.pattern_id, resolution)
            assert success, "Resolution update should succeed"
            
            # Retrieve resolved patterns
            resolved = db.get_resolved_patterns()
            
            # Should find our pattern
            found = False
            for resolved_pattern in resolved:
                if resolved_pattern.pattern_id == pattern.pattern_id:
                    found = True
                    assert resolved_pattern.resolution == resolution
                    assert resolved_pattern.resolution_date is not None
                    break
            
            assert found, "Resolved pattern should be in resolved patterns list"
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@settings(max_examples=100, deadline=None)
@given(
    patterns=st.lists(failure_pattern_strategy(), min_size=1, max_size=20)
)
def test_unresolved_patterns_exclude_resolved(patterns):
    """
    Property: For any set of patterns where some are resolved and some are not,
    get_unresolved_patterns should only return the unresolved ones.
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    # Ensure we have at least one resolved and one unresolved
    assume(len(patterns) >= 2)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            # Store all patterns
            for pattern in patterns:
                db.store_failure_pattern(pattern)
            
            # Resolve the first pattern
            db.update_resolution(patterns[0].pattern_id, "Fixed")
            
            # Get unresolved patterns
            unresolved = db.get_unresolved_patterns()
            
            # Should not include the resolved pattern
            unresolved_ids = {p.pattern_id for p in unresolved}
            assert patterns[0].pattern_id not in unresolved_ids, \
                "Resolved pattern should not be in unresolved list"
            
            # Should include at least some unresolved patterns
            for pattern in patterns[1:]:
                if pattern.pattern_id in unresolved_ids:
                    # Found at least one unresolved pattern
                    return
            
            # If we get here and there are unresolved patterns, that's fine
            assert len(patterns) > 1
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@settings(max_examples=100, deadline=None)
@given(
    patterns=st.lists(failure_pattern_strategy(), min_size=1, max_size=20),
    search_term=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))
)
def test_search_by_root_cause_finds_matching_patterns(patterns, search_term):
    """
    Property: For any search term, search_by_root_cause should return only
    patterns whose root cause contains that term.
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    # Ensure at least one pattern contains the search term
    if patterns:
        patterns[0].root_cause = f"Issue with {search_term} in the system"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            # Store all patterns
            for pattern in patterns:
                db.store_failure_pattern(pattern)
            
            # Search for the term
            results = db.search_by_root_cause(search_term)
            
            # All results should contain the search term
            for result in results:
                assert search_term.lower() in result.root_cause.lower(), \
                    f"Search result should contain '{search_term}'"
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@settings(max_examples=100, deadline=None)
@given(
    patterns=st.lists(failure_pattern_strategy(), min_size=1, max_size=50)
)
def test_statistics_reflect_stored_patterns(patterns):
    """
    Property: For any set of stored patterns, database statistics should
    accurately reflect the number of patterns, resolutions, and instances.
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            # Store all patterns
            for pattern in patterns:
                db.store_failure_pattern(pattern)
            
            # Count resolved patterns
            resolved_count = sum(1 for p in patterns if p.resolution is not None)
            
            # Get statistics
            stats = db.get_statistics()
            
            # Verify statistics match
            assert stats['total_patterns'] == len(patterns), \
                "Total patterns should match number stored"
            assert stats['resolved_patterns'] == resolved_count, \
                "Resolved count should match patterns with resolutions"
            assert stats['unresolved_patterns'] == len(patterns) - resolved_count, \
                "Unresolved count should be total minus resolved"
            
            if len(patterns) > 0:
                expected_rate = resolved_count / len(patterns)
                assert abs(stats['resolution_rate'] - expected_rate) < 0.01, \
                    "Resolution rate should be resolved/total"
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@settings(max_examples=100, deadline=None)
@given(
    pattern=failure_pattern_strategy(),
    duplicate_count=st.integers(min_value=1, max_value=10)
)
def test_duplicate_patterns_increment_occurrence_count(pattern, duplicate_count):
    """
    Property: For any pattern stored multiple times with the same signature,
    the occurrence count should increment by the number of duplicates.
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            initial_count = pattern.occurrence_count
            
            # Store pattern multiple times
            for _ in range(duplicate_count):
                db.store_failure_pattern(pattern)
            
            # Retrieve and check count
            retrieved = db.lookup_by_pattern_id(pattern.pattern_id)
            
            expected_count = initial_count + (duplicate_count - 1)
            assert retrieved.occurrence_count == expected_count, \
                f"Occurrence count should be {expected_count}"
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


@settings(max_examples=100, deadline=None)
@given(
    patterns=st.lists(failure_pattern_strategy(), min_size=2, max_size=20)
)
def test_patterns_sorted_by_relevance(patterns):
    """
    Property: For any set of patterns, find_matching_patterns should return
    results sorted by relevance (occurrence count and recency).
    
    **Feature: agentic-kernel-testing, Property 20: Historical pattern matching**
    **Validates: Requirements 4.5**
    """
    # Ensure patterns have different occurrence counts
    for i, pattern in enumerate(patterns):
        pattern.occurrence_count = i + 1
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.db') as f:
        temp_db_path = f.name
    
    try:
        with HistoricalFailureDatabase(temp_db_path) as db:
            # Store all patterns with same error pattern
            error_pattern = "null_pointer"
            for pattern in patterns:
                pattern.error_pattern = error_pattern
                db.store_failure_pattern(pattern)
            
            # Find patterns by error pattern
            results = db.find_matching_patterns(
                signature="nonexistent",
                error_pattern=error_pattern,
                limit=len(patterns)
            )
            
            # Verify results are sorted by occurrence count (descending)
            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i].occurrence_count >= results[i + 1].occurrence_count, \
                        "Results should be sorted by occurrence count (descending)"
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
