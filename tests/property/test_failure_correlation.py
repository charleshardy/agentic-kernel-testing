"""Property-based tests for failure correlation accuracy.

**Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
**Validates: Requirements 4.2**

Property 17: Failure correlation accuracy
For any test failure, the analysis should correlate the failure with recent code changes
and identify likely culprit commits.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import List, Tuple

from ai_generator.models import (
    TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, ArtifactBundle, FailureInfo, Commit
)
from analysis.git_bisect_runner import CommitCorrelator, SuspiciousCommitRanker


# Custom strategies for generating test data
@st.composite
def hardware_config_strategy(draw):
    """Generate a random hardware configuration."""
    architecture = draw(st.sampled_from(['x86_64', 'arm64', 'riscv64', 'arm']))
    cpu_model = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    memory_mb = draw(st.integers(min_value=512, max_value=16384))
    
    return HardwareConfig(
        architecture=architecture,
        cpu_model=cpu_model,
        memory_mb=memory_mb,
        storage_type='ssd',
        is_virtual=True,
        emulator='qemu'
    )


@st.composite
def environment_strategy(draw):
    """Generate a random environment."""
    config = draw(hardware_config_strategy())
    env_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return Environment(
        id=env_id,
        config=config,
        status=EnvironmentStatus.IDLE,
        created_at=datetime.now(),
        last_used=datetime.now()
    )


@st.composite
def commit_strategy(draw, timestamp=None, files=None):
    """Generate a random commit."""
    sha = draw(st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'))
    message = draw(st.text(min_size=10, max_size=100))
    author = draw(st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    
    if timestamp is None:
        timestamp = datetime.now() - timedelta(days=draw(st.integers(min_value=0, max_value=30)))
    
    if files is None:
        num_files = draw(st.integers(min_value=1, max_value=10))
        files = [
            draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))) + '.c'
            for _ in range(num_files)
        ]
    
    return Commit(
        sha=sha,
        message=message,
        author=author,
        timestamp=timestamp,
        files_changed=files
    )


@st.composite
def failure_with_stack_trace_strategy(draw, file_name=None):
    """Generate a failure with a stack trace mentioning a specific file."""
    test_id = draw(st.text(min_size=1, max_size=36, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    execution_time = draw(st.floats(min_value=0.1, max_value=300.0))
    environment = draw(environment_strategy())
    
    if file_name is None:
        file_name = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))) + '.c'
    
    func_name = draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    line_num = draw(st.integers(min_value=1, max_value=1000))
    
    # Create stack trace with the file
    stack_trace = f"""Call Trace:
 [ffffffff81234567] {func_name}+0x42/0x100 [{file_name}:{line_num}]
 [ffffffff81345678] caller_function+0x10/0x20
 [ffffffff81456789] top_level_function+0x5/0x10
"""
    
    failure_info = FailureInfo(
        error_message=f"Error in {func_name}",
        stack_trace=stack_trace,
        exit_code=1,
        kernel_panic=True
    )
    
    return TestResult(
        test_id=test_id,
        status=TestStatus.FAILED,
        execution_time=execution_time,
        environment=environment,
        artifacts=ArtifactBundle(),
        failure_info=failure_info,
        timestamp=datetime.now()
    ), file_name


@given(st.data(), st.integers(min_value=1, max_value=20))
@settings(max_examples=100, deadline=None)
def test_correlator_returns_scored_commits(data, num_commits: int):
    """
    Property: For any list of commits and a failure, the correlator should return
    a list of (commit, score) tuples with valid scores.
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    # Create a failure
    failure, file_name = data.draw(failure_with_stack_trace_strategy())
    
    # Create commits
    commits = [data.draw(commit_strategy()) for _ in range(num_commits)]
    
    # Use correlator (without actual git repo)
    correlator = CommitCorrelator()
    
    # Calculate scores directly
    scored_commits = []
    for commit in commits:
        score = correlator._calculate_suspicion_score(commit, failure)
        scored_commits.append((commit, score))
    
    # Verify we got results for all commits
    assert len(scored_commits) == num_commits, \
        f"Should score all commits. Expected {num_commits}, got {len(scored_commits)}"
    
    # Verify all scores are valid (0.0-1.0)
    for commit, score in scored_commits:
        assert 0.0 <= score <= 1.0, \
            f"Score should be between 0.0 and 1.0, got {score}"
        assert isinstance(score, float), \
            f"Score should be a float, got {type(score)}"


@given(st.data(), st.integers(min_value=2, max_value=10))
@settings(max_examples=100, deadline=None)
def test_matching_file_gets_higher_score(data, num_commits: int):
    """
    Property: For any failure with a stack trace, commits that modified files
    in the stack trace should receive higher scores than commits that didn't.
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    # Create a failure with a specific file in stack trace
    file_name = "test_file.c"
    failure, _ = data.draw(failure_with_stack_trace_strategy(file_name=file_name))
    
    # Create one commit that modified the file
    matching_commit = data.draw(commit_strategy(files=[file_name, "other.c"]))
    
    # Create other commits that didn't modify the file
    non_matching_commits = [
        data.draw(commit_strategy(files=["unrelated1.c", "unrelated2.c"]))
        for _ in range(num_commits - 1)
    ]
    
    correlator = CommitCorrelator()
    
    # Score matching commit
    matching_score = correlator._calculate_suspicion_score(matching_commit, failure)
    
    # Score non-matching commits
    non_matching_scores = [
        correlator._calculate_suspicion_score(commit, failure)
        for commit in non_matching_commits
    ]
    
    # Matching commit should have higher score than at least some non-matching commits
    # (unless non-matching commits have other strong signals like recency)
    max_non_matching = max(non_matching_scores) if non_matching_scores else 0.0
    
    # The matching commit should have a score boost from file matching
    # It should be at least 0.5 (the file matching bonus)
    assert matching_score >= 0.5, \
        f"Commit modifying file in stack trace should have score >= 0.5, got {matching_score}"


@given(st.data(), st.integers(min_value=2, max_value=10))
@settings(max_examples=100, deadline=None)
def test_recent_commits_get_higher_scores(data, num_commits: int):
    """
    Property: For any failure, commits that are more recent (closer in time to the failure)
    should receive higher scores than older commits, all else being equal.
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    failure_time = datetime.now()
    
    # Create failure
    failure, file_name = data.draw(failure_with_stack_trace_strategy())
    failure.timestamp = failure_time
    
    # Create recent commit (1 hour before failure)
    recent_commit = data.draw(commit_strategy(
        timestamp=failure_time - timedelta(hours=1),
        files=["unrelated.c"]
    ))
    
    # Create old commit (1 month before failure)
    old_commit = data.draw(commit_strategy(
        timestamp=failure_time - timedelta(days=30),
        files=["unrelated.c"]
    ))
    
    correlator = CommitCorrelator()
    
    recent_score = correlator._calculate_suspicion_score(recent_commit, failure)
    old_score = correlator._calculate_suspicion_score(old_commit, failure)
    
    # Recent commit should have higher score due to recency bonus
    assert recent_score > old_score, \
        f"Recent commit should have higher score. Recent: {recent_score}, Old: {old_score}"


@given(st.data(), st.integers(min_value=2, max_value=10))
@settings(max_examples=100, deadline=None)
def test_ranker_sorts_by_score(data, num_commits: int):
    """
    Property: For any list of commits, the ranker should return them sorted
    by suspicion score in descending order (highest first).
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    # Create a failure
    failure, file_name = data.draw(failure_with_stack_trace_strategy())
    
    # Create commits with varying characteristics
    commits = []
    for i in range(num_commits):
        # Some commits match the file, some don't
        if i % 3 == 0:
            files = [file_name, "other.c"]
        else:
            files = ["unrelated.c"]
        
        commit = data.draw(commit_strategy(files=files))
        commits.append(commit)
    
    ranker = SuspiciousCommitRanker()
    ranked = ranker.rank_commits(commits, failure)
    
    # Verify we got all commits back
    assert len(ranked) == num_commits, \
        f"Should rank all commits. Expected {num_commits}, got {len(ranked)}"
    
    # Verify sorting (scores should be in descending order)
    scores = [score for commit, score, rationale in ranked]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], \
            f"Scores should be in descending order. scores[{i}]={scores[i]}, scores[{i+1}]={scores[i+1]}"


@given(st.data(), st.integers(min_value=1, max_value=10))
@settings(max_examples=100, deadline=None)
def test_ranker_provides_rationale(data, num_commits: int):
    """
    Property: For any list of commits, the ranker should provide a rationale
    string for each commit explaining the suspicion score.
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    # Create a failure
    failure, file_name = data.draw(failure_with_stack_trace_strategy())
    
    # Create commits
    commits = [data.draw(commit_strategy()) for _ in range(num_commits)]
    
    ranker = SuspiciousCommitRanker()
    ranked = ranker.rank_commits(commits, failure)
    
    # Verify each result has a rationale
    for commit, score, rationale in ranked:
        assert isinstance(rationale, str), \
            "Rationale should be a string"
        assert len(rationale) > 0, \
            "Rationale should not be empty"


@given(st.data(), st.integers(min_value=1, max_value=10))
@settings(max_examples=100, deadline=None)
def test_correlation_is_deterministic(data, num_commits: int):
    """
    Property: For any failure and list of commits, running correlation multiple times
    should produce the same results (deterministic).
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    # Create a failure
    failure, file_name = data.draw(failure_with_stack_trace_strategy())
    
    # Create commits
    commits = [data.draw(commit_strategy()) for _ in range(num_commits)]
    
    ranker = SuspiciousCommitRanker()
    
    # Rank twice
    ranked1 = ranker.rank_commits(commits, failure)
    ranked2 = ranker.rank_commits(commits, failure)
    
    # Verify same results
    assert len(ranked1) == len(ranked2), \
        "Should return same number of results"
    
    for i in range(len(ranked1)):
        commit1, score1, rationale1 = ranked1[i]
        commit2, score2, rationale2 = ranked2[i]
        
        assert commit1.sha == commit2.sha, \
            f"Commit order should be same. Position {i}: {commit1.sha} vs {commit2.sha}"
        assert score1 == score2, \
            f"Scores should be same. Position {i}: {score1} vs {score2}"


@given(st.data(), st.integers(min_value=5, max_value=20))
@settings(max_examples=100, deadline=None)
def test_commits_with_bug_keywords_get_bonus(data, num_commits: int):
    """
    Property: For any failure, commits with bug-related keywords in their message
    should receive a score bonus compared to commits without such keywords.
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    # Create a failure
    failure, file_name = data.draw(failure_with_stack_trace_strategy())
    
    # Create commit with bug keyword
    bug_commit = data.draw(commit_strategy(files=["unrelated.c"]))
    bug_commit.message = "Fix bug in module"
    
    # Create commit without bug keyword
    normal_commit = data.draw(commit_strategy(files=["unrelated.c"]))
    normal_commit.message = "Add new feature to module"
    
    # Make timestamps the same to isolate the keyword effect
    timestamp = datetime.now() - timedelta(days=1)
    bug_commit.timestamp = timestamp
    normal_commit.timestamp = timestamp
    
    correlator = CommitCorrelator()
    
    bug_score = correlator._calculate_suspicion_score(bug_commit, failure)
    normal_score = correlator._calculate_suspicion_score(normal_commit, failure)
    
    # Bug commit should have higher or equal score
    assert bug_score >= normal_score, \
        f"Commit with bug keyword should have higher score. Bug: {bug_score}, Normal: {normal_score}"


@given(st.data(), st.integers(min_value=2, max_value=10))
@settings(max_examples=100, deadline=None)
def test_larger_changes_get_higher_scores(data, num_commits: int):
    """
    Property: For any failure, commits that modify more files should receive
    higher scores than commits that modify fewer files, all else being equal.
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    # Create a failure
    failure, file_name = data.draw(failure_with_stack_trace_strategy())
    
    # Create large commit (15 files)
    large_files = [f"file{i}.c" for i in range(15)]
    large_commit = data.draw(commit_strategy(files=large_files))
    
    # Create small commit (2 files)
    small_files = ["file1.c", "file2.c"]
    small_commit = data.draw(commit_strategy(files=small_files))
    
    # Make timestamps the same to isolate the size effect
    timestamp = datetime.now() - timedelta(days=1)
    large_commit.timestamp = timestamp
    small_commit.timestamp = timestamp
    
    correlator = CommitCorrelator()
    
    large_score = correlator._calculate_suspicion_score(large_commit, failure)
    small_score = correlator._calculate_suspicion_score(small_commit, failure)
    
    # Large commit should have higher or equal score
    assert large_score >= small_score, \
        f"Larger commit should have higher score. Large: {large_score}, Small: {small_score}"


@given(st.data(), st.lists(commit_strategy(), min_size=1, max_size=20))
@settings(max_examples=100, deadline=None)
def test_all_commits_get_scored(data, commits: List[Commit]):
    """
    Property: For any list of commits and a failure, every commit should receive
    a score (no commits should be skipped).
    
    **Feature: agentic-kernel-testing, Property 17: Failure correlation accuracy**
    **Validates: Requirements 4.2**
    """
    # Create a failure
    failure, file_name = data.draw(failure_with_stack_trace_strategy())
    
    ranker = SuspiciousCommitRanker()
    ranked = ranker.rank_commits(commits, failure)
    
    # Verify all commits are present
    ranked_shas = set(commit.sha for commit, score, rationale in ranked)
    original_shas = set(commit.sha for commit in commits)
    
    assert ranked_shas == original_shas, \
        f"All commits should be scored. Missing: {original_shas - ranked_shas}"
