"""Git integration for detecting code changes."""

import subprocess
from typing import List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from ai_generator.models import Commit


class GitRepository:
    """Interface to a Git repository for change detection."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize Git repository interface.
        
        Args:
            repo_path: Path to Git repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self._validate_repo()
    
    def _validate_repo(self) -> None:
        """Validate that the path is a Git repository."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise ValueError(f"Not a Git repository: {self.repo_path}")
    
    def _run_git_command(self, args: List[str]) -> Tuple[str, str, int]:
        """Run a Git command and return output.
        
        Args:
            args: Git command arguments (without 'git' prefix)
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        cmd = ["git"] + args
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    
    def get_diff(self, base: str = "HEAD~1", target: str = "HEAD") -> str:
        """Get diff between two commits.
        
        Args:
            base: Base commit reference (default: previous commit)
            target: Target commit reference (default: current commit)
            
        Returns:
            Git diff output as string
        """
        stdout, stderr, returncode = self._run_git_command([
            "diff", base, target
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git diff failed: {stderr}")
        
        return stdout
    
    def get_uncommitted_diff(self) -> str:
        """Get diff of uncommitted changes.
        
        Returns:
            Git diff output for uncommitted changes
        """
        stdout, stderr, returncode = self._run_git_command([
            "diff", "HEAD"
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git diff failed: {stderr}")
        
        return stdout
    
    def get_staged_diff(self) -> str:
        """Get diff of staged changes.
        
        Returns:
            Git diff output for staged changes
        """
        stdout, stderr, returncode = self._run_git_command([
            "diff", "--cached"
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git diff failed: {stderr}")
        
        return stdout
    
    def get_commit_info(self, commit_ref: str = "HEAD") -> Commit:
        """Get information about a specific commit.
        
        Args:
            commit_ref: Commit reference (SHA, branch, tag, etc.)
            
        Returns:
            Commit object with commit information
        """
        # Get commit details
        stdout, stderr, returncode = self._run_git_command([
            "show", "--no-patch", "--format=%H%n%an%n%at%n%s", commit_ref
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git show failed: {stderr}")
        
        lines = stdout.strip().split('\n')
        if len(lines) < 4:
            raise ValueError(f"Invalid commit format: {stdout}")
        
        sha = lines[0]
        author = lines[1]
        timestamp = datetime.fromtimestamp(int(lines[2]))
        message = lines[3]
        
        # Get changed files
        stdout, stderr, returncode = self._run_git_command([
            "diff-tree", "--no-commit-id", "--name-only", "-r", commit_ref
        ])
        
        files_changed = stdout.strip().split('\n') if stdout.strip() else []
        
        return Commit(
            sha=sha,
            message=message,
            author=author,
            timestamp=timestamp,
            files_changed=files_changed
        )
    
    def get_recent_commits(self, count: int = 10, branch: str = "HEAD") -> List[Commit]:
        """Get recent commits from a branch.
        
        Args:
            count: Number of commits to retrieve
            branch: Branch reference
            
        Returns:
            List of Commit objects
        """
        commits = []
        
        # Get commit SHAs
        stdout, stderr, returncode = self._run_git_command([
            "log", f"-{count}", "--format=%H", branch
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git log failed: {stderr}")
        
        shas = stdout.strip().split('\n')
        
        # Get info for each commit
        for sha in shas:
            if sha:
                try:
                    commit = self.get_commit_info(sha)
                    commits.append(commit)
                except Exception:
                    # Skip commits that fail to parse
                    continue
        
        return commits
    
    def get_file_content(self, file_path: str, commit_ref: str = "HEAD") -> str:
        """Get content of a file at a specific commit.
        
        Args:
            file_path: Path to file relative to repo root
            commit_ref: Commit reference
            
        Returns:
            File content as string
        """
        stdout, stderr, returncode = self._run_git_command([
            "show", f"{commit_ref}:{file_path}"
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git show failed: {stderr}")
        
        return stdout
    
    def get_changed_files(self, base: str = "HEAD~1", target: str = "HEAD") -> List[str]:
        """Get list of files changed between commits.
        
        Args:
            base: Base commit reference
            target: Target commit reference
            
        Returns:
            List of changed file paths
        """
        stdout, stderr, returncode = self._run_git_command([
            "diff", "--name-only", base, target
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git diff failed: {stderr}")
        
        return [f for f in stdout.strip().split('\n') if f]
    
    def get_current_branch(self) -> str:
        """Get name of current branch.
        
        Returns:
            Current branch name
        """
        stdout, stderr, returncode = self._run_git_command([
            "rev-parse", "--abbrev-ref", "HEAD"
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git rev-parse failed: {stderr}")
        
        return stdout.strip()
    
    def get_current_commit_sha(self) -> str:
        """Get SHA of current commit.
        
        Returns:
            Current commit SHA
        """
        stdout, stderr, returncode = self._run_git_command([
            "rev-parse", "HEAD"
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git rev-parse failed: {stderr}")
        
        return stdout.strip()
    
    def get_commits_between(self, start: str, end: str) -> List[Commit]:
        """Get all commits between two references.
        
        Args:
            start: Starting commit reference (exclusive)
            end: Ending commit reference (inclusive)
            
        Returns:
            List of Commit objects between start and end
        """
        stdout, stderr, returncode = self._run_git_command([
            "log", f"{start}..{end}", "--format=%H"
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git log failed: {stderr}")
        
        shas = [sha for sha in stdout.strip().split('\n') if sha]
        
        commits = []
        for sha in shas:
            try:
                commit = self.get_commit_info(sha)
                commits.append(commit)
            except Exception:
                # Skip commits that fail to parse
                continue
        
        return commits
    
    def checkout(self, commit_ref: str) -> None:
        """Checkout a specific commit.
        
        Args:
            commit_ref: Commit reference to checkout
        """
        stdout, stderr, returncode = self._run_git_command([
            "checkout", commit_ref
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git checkout failed: {stderr}")
    
    def bisect_start(self, bad: str, good: str) -> None:
        """Start a git bisect session.
        
        Args:
            bad: Known bad commit reference
            good: Known good commit reference
        """
        # Reset any existing bisect
        self._run_git_command(["bisect", "reset"])
        
        # Start bisect
        stdout, stderr, returncode = self._run_git_command([
            "bisect", "start", bad, good
        ])
        
        if returncode != 0:
            raise RuntimeError(f"Git bisect start failed: {stderr}")
    
    def bisect_good(self) -> Optional[str]:
        """Mark current commit as good in bisect.
        
        Returns:
            Next commit SHA to test, or None if bisect is complete
        """
        stdout, stderr, returncode = self._run_git_command([
            "bisect", "good"
        ])
        
        # Check if bisect is complete
        if "is the first bad commit" in stdout:
            return None
        
        # Extract next commit to test
        return self.get_current_commit_sha()
    
    def bisect_bad(self) -> Optional[str]:
        """Mark current commit as bad in bisect.
        
        Returns:
            Next commit SHA to test, or None if bisect is complete
        """
        stdout, stderr, returncode = self._run_git_command([
            "bisect", "bad"
        ])
        
        # Check if bisect is complete
        if "is the first bad commit" in stdout:
            return None
        
        # Extract next commit to test
        return self.get_current_commit_sha()
    
    def bisect_reset(self) -> None:
        """Reset/end a git bisect session."""
        self._run_git_command(["bisect", "reset"])
    
    def get_bisect_result(self) -> Optional[Commit]:
        """Get the result of a completed bisect.
        
        Returns:
            Commit object for the first bad commit, or None if bisect not complete
        """
        stdout, stderr, returncode = self._run_git_command([
            "bisect", "log"
        ])
        
        if returncode != 0:
            return None
        
        # Parse bisect log to find first bad commit
        # Look for pattern: "# first bad commit: [SHA]"
        import re
        match = re.search(r'first bad commit:\s*\[([0-9a-f]+)\]', stdout)
        if match:
            sha = match.group(1)
            try:
                return self.get_commit_info(sha)
            except Exception:
                return None
        
        return None
