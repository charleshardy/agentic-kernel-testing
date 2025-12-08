"""Automated git bisect runner for regression identification.

This module implements automated git bisect to identify the commit that introduced
a regression or failure. It integrates with the test execution system to automatically
test commits and determine good/bad status.
"""

from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass
import logging

from ai_generator.models import Commit, TestResult, TestStatus
from analysis.git_integration import GitRepository


logger = logging.getLogger(__name__)


@dataclass
class BisectResult:
    """Result of a git bisect operation."""
    culprit_commit: Optional[Commit]
    good_commit: Commit
    bad_commit: Commit
    commits_tested: int
    success: bool
    error_message: Optional[str] = None


class GitBisectRunner:
    """Automated git bisect runner for identifying regression commits.
    
    This class automates the git bisect process by:
    1. Starting a bisect session between known good and bad commits
    2. Automatically testing each commit suggested by git bisect
    3. Marking commits as good or bad based on test results
    4. Identifying the first bad commit that introduced the regression
    """
    
    def __init__(self, repo_path: str = "."):
        """Initialize git bisect runner.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo = GitRepository(repo_path)
        self._original_commit: Optional[str] = None
    
    def run_bisect(
        self,
        good_commit: str,
        bad_commit: str,
        test_function: Callable[[str], bool]
    ) -> BisectResult:
        """Run automated git bisect to find regression commit.
        
        Args:
            good_commit: Known good commit reference
            bad_commit: Known bad commit reference
            test_function: Function that tests a commit and returns True if good, False if bad
            
        Returns:
            BisectResult with the culprit commit and bisect statistics
        """
        # Save current commit to restore later
        self._original_commit = self.repo.get_current_commit_sha()
        
        try:
            # Get commit objects for good and bad
            good_commit_obj = self.repo.get_commit_info(good_commit)
            bad_commit_obj = self.repo.get_commit_info(bad_commit)
            
            logger.info(f"Starting bisect between {good_commit} (good) and {bad_commit} (bad)")
            
            # Start bisect
            self.repo.bisect_start(bad_commit, good_commit)
            
            commits_tested = 0
            
            # Bisect loop
            while True:
                current_sha = self.repo.get_current_commit_sha()
                logger.info(f"Testing commit {current_sha}")
                
                # Test current commit
                try:
                    is_good = test_function(current_sha)
                    commits_tested += 1
                except Exception as e:
                    logger.error(f"Test function failed for commit {current_sha}: {e}")
                    # Treat test failures as bad commits
                    is_good = False
                
                # Mark commit as good or bad
                if is_good:
                    logger.info(f"Commit {current_sha} is good")
                    next_commit = self.repo.bisect_good()
                else:
                    logger.info(f"Commit {current_sha} is bad")
                    next_commit = self.repo.bisect_bad()
                
                # Check if bisect is complete
                if next_commit is None:
                    break
            
            # Get bisect result
            culprit = self.repo.get_bisect_result()
            
            if culprit:
                logger.info(f"Found culprit commit: {culprit.sha}")
                return BisectResult(
                    culprit_commit=culprit,
                    good_commit=good_commit_obj,
                    bad_commit=bad_commit_obj,
                    commits_tested=commits_tested,
                    success=True
                )
            else:
                logger.warning("Bisect completed but could not identify culprit")
                return BisectResult(
                    culprit_commit=None,
                    good_commit=good_commit_obj,
                    bad_commit=bad_commit_obj,
                    commits_tested=commits_tested,
                    success=False,
                    error_message="Could not identify culprit commit"
                )
        
        except Exception as e:
            logger.error(f"Bisect failed: {e}")
            return BisectResult(
                culprit_commit=None,
                good_commit=self.repo.get_commit_info(good_commit),
                bad_commit=self.repo.get_commit_info(bad_commit),
                commits_tested=0,
                success=False,
                error_message=str(e)
            )
        
        finally:
            # Clean up bisect and restore original commit
            self.repo.bisect_reset()
            if self._original_commit:
                try:
                    self.repo.checkout(self._original_commit)
                except Exception as e:
                    logger.error(f"Failed to restore original commit: {e}")
    
    def run_bisect_with_test_result(
        self,
        good_commit: str,
        bad_commit: str,
        test_executor: Callable[[str], TestResult]
    ) -> BisectResult:
        """Run automated git bisect using test execution results.
        
        This is a convenience wrapper that converts TestResult objects to boolean
        good/bad status for the bisect process.
        
        Args:
            good_commit: Known good commit reference
            bad_commit: Known bad commit reference
            test_executor: Function that executes a test on a commit and returns TestResult
            
        Returns:
            BisectResult with the culprit commit and bisect statistics
        """
        def test_function(commit_sha: str) -> bool:
            """Test function that converts TestResult to boolean."""
            result = test_executor(commit_sha)
            return result.status == TestStatus.PASSED
        
        return self.run_bisect(good_commit, bad_commit, test_function)


class CommitCorrelator:
    """Correlates test failures with commits to identify suspicious changes.
    
    This class provides algorithms to rank commits by their likelihood of causing
    a failure, based on various heuristics like file changes, timing, and commit messages.
    """
    
    def __init__(self, repo_path: str = "."):
        """Initialize commit correlator.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo = GitRepository(repo_path)
    
    def correlate_failure_with_commits(
        self,
        failure: TestResult,
        start_commit: str,
        end_commit: str
    ) -> List[Tuple[Commit, float]]:
        """Correlate a test failure with commits in a range.
        
        Args:
            failure: TestResult with failure information
            start_commit: Start of commit range to analyze
            end_commit: End of commit range to analyze
            
        Returns:
            List of (Commit, suspicion_score) tuples, sorted by score (highest first)
        """
        # Get commits in range
        commits = self.repo.get_commits_between(start_commit, end_commit)
        
        if not commits:
            return []
        
        # Score each commit
        scored_commits = []
        for commit in commits:
            score = self._calculate_suspicion_score(commit, failure)
            scored_commits.append((commit, score))
        
        # Sort by score (highest first)
        scored_commits.sort(key=lambda x: x[1], reverse=True)
        
        return scored_commits
    
    def _calculate_suspicion_score(self, commit: Commit, failure: TestResult) -> float:
        """Calculate suspicion score for a commit.
        
        The score is based on:
        - Files changed matching failure stack trace
        - Recency of commit relative to failure
        - Commit message keywords
        - Size of change (more changes = higher risk)
        
        Args:
            commit: Commit to score
            failure: TestResult with failure information
            
        Returns:
            Suspicion score (0.0-1.0)
        """
        score = 0.0
        
        # Extract affected files from failure stack trace
        affected_files = self._extract_files_from_failure(failure)
        
        # Check if commit modified files in stack trace (highest weight)
        if affected_files:
            for changed_file in commit.files_changed:
                for affected_file in affected_files:
                    if self._files_match(changed_file, affected_file):
                        score += 0.5
                        break
        
        # Check recency (more recent = more suspicious)
        if failure.timestamp and commit.timestamp:
            time_diff = (failure.timestamp - commit.timestamp).total_seconds()
            if time_diff >= 0:  # Commit is before failure
                if time_diff < 3600:  # Within 1 hour
                    score += 0.3
                elif time_diff < 86400:  # Within 24 hours
                    score += 0.2
                elif time_diff < 604800:  # Within 1 week
                    score += 0.1
        
        # Check commit message for relevant keywords
        keywords = [
            "fix", "bug", "crash", "error", "issue", "problem",
            "regression", "break", "fail", "wrong"
        ]
        message_lower = commit.message.lower()
        keyword_matches = sum(1 for keyword in keywords if keyword in message_lower)
        score += min(0.2, keyword_matches * 0.05)
        
        # Consider size of change (more files = higher risk)
        num_files = len(commit.files_changed)
        if num_files > 10:
            score += 0.1
        elif num_files > 5:
            score += 0.05
        
        return min(1.0, score)
    
    def _extract_files_from_failure(self, failure: TestResult) -> List[str]:
        """Extract file paths from failure stack trace.
        
        Args:
            failure: TestResult with failure information
            
        Returns:
            List of file paths mentioned in stack trace
        """
        if not failure.failure_info or not failure.failure_info.stack_trace:
            return []
        
        files = []
        stack_trace = failure.failure_info.stack_trace
        
        # Look for file paths in common formats
        # Format: file.c:123
        import re
        file_pattern = r'([a-zA-Z0-9_/\-\.]+\.[ch](?:pp)?):(\d+)'
        
        for match in re.finditer(file_pattern, stack_trace):
            file_path = match.group(1)
            files.append(file_path)
        
        return list(set(files))  # Remove duplicates
    
    def _files_match(self, changed_file: str, affected_file: str) -> bool:
        """Check if a changed file matches an affected file.
        
        Handles partial path matching (e.g., "kernel/sched.c" matches "sched.c").
        
        Args:
            changed_file: File path from commit
            affected_file: File path from stack trace
            
        Returns:
            True if files match
        """
        # Exact match
        if changed_file == affected_file:
            return True
        
        # Partial match (basename)
        import os
        if os.path.basename(changed_file) == os.path.basename(affected_file):
            return True
        
        # One is substring of other
        if affected_file in changed_file or changed_file in affected_file:
            return True
        
        return False


class SuspiciousCommitRanker:
    """Ranks commits by suspicion level for causing failures.
    
    This class combines multiple signals to rank commits, including:
    - File overlap with failure stack traces
    - Temporal proximity to failure
    - Commit message analysis
    - Change size and complexity
    - Historical failure patterns
    """
    
    def __init__(self, repo_path: str = "."):
        """Initialize suspicious commit ranker.
        
        Args:
            repo_path: Path to git repository
        """
        self.correlator = CommitCorrelator(repo_path)
    
    def rank_commits(
        self,
        commits: List[Commit],
        failure: TestResult
    ) -> List[Tuple[Commit, float, str]]:
        """Rank commits by suspicion level.
        
        Args:
            commits: List of commits to rank
            failure: TestResult with failure information
            
        Returns:
            List of (Commit, score, rationale) tuples, sorted by score (highest first)
        """
        ranked = []
        
        for commit in commits:
            score = self.correlator._calculate_suspicion_score(commit, failure)
            rationale = self._generate_rationale(commit, failure, score)
            ranked.append((commit, score, rationale))
        
        # Sort by score (highest first)
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
    
    def _generate_rationale(self, commit: Commit, failure: TestResult, score: float) -> str:
        """Generate human-readable rationale for suspicion score.
        
        Args:
            commit: Commit being ranked
            failure: TestResult with failure information
            score: Calculated suspicion score
            
        Returns:
            Rationale string explaining the score
        """
        reasons = []
        
        # Check file overlap
        affected_files = self.correlator._extract_files_from_failure(failure)
        matching_files = []
        for changed_file in commit.files_changed:
            for affected_file in affected_files:
                if self.correlator._files_match(changed_file, affected_file):
                    matching_files.append(changed_file)
        
        if matching_files:
            reasons.append(f"Modified files in stack trace: {', '.join(matching_files)}")
        
        # Check recency
        if failure.timestamp and commit.timestamp:
            time_diff = (failure.timestamp - commit.timestamp).total_seconds()
            if time_diff >= 0:
                if time_diff < 3600:
                    reasons.append("Very recent commit (< 1 hour before failure)")
                elif time_diff < 86400:
                    reasons.append("Recent commit (< 24 hours before failure)")
                elif time_diff < 604800:
                    reasons.append("Commit within past week")
        
        # Check commit message
        keywords = ["fix", "bug", "crash", "error", "issue", "problem"]
        if any(keyword in commit.message.lower() for keyword in keywords):
            reasons.append("Commit message mentions bug/fix keywords")
        
        # Check change size
        num_files = len(commit.files_changed)
        if num_files > 10:
            reasons.append(f"Large change ({num_files} files modified)")
        elif num_files > 5:
            reasons.append(f"Moderate change ({num_files} files modified)")
        
        if not reasons:
            return "No strong indicators"
        
        return "; ".join(reasons)
