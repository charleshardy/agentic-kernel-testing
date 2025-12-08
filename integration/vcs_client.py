"""VCS client for reporting test status back to GitHub/GitLab."""

import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from integration.vcs_models import (
    VCSProvider, Repository, TestStatus, TestStatusState, StatusReport
)

logger = logging.getLogger(__name__)


class VCSClient:
    """Client for interacting with VCS APIs."""
    
    def __init__(
        self,
        provider: VCSProvider,
        api_token: str,
        base_url: Optional[str] = None
    ):
        """Initialize VCS client.
        
        Args:
            provider: VCS provider
            api_token: API token for authentication
            base_url: Base URL for API (optional, uses defaults)
        """
        self.provider = provider
        self.api_token = api_token
        
        # Set default base URLs
        if base_url:
            self.base_url = base_url
        elif provider == VCSProvider.GITHUB:
            self.base_url = "https://api.github.com"
        elif provider == VCSProvider.GITLAB:
            self.base_url = "https://gitlab.com/api/v4"
        else:
            raise ValueError(f"Unsupported VCS provider: {provider}")
        
        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set authentication headers
        if provider == VCSProvider.GITHUB:
            self.session.headers.update({
                'Authorization': f'token {api_token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        elif provider == VCSProvider.GITLAB:
            self.session.headers.update({
                'PRIVATE-TOKEN': api_token
            })
    
    def report_status_github(
        self,
        repository: Repository,
        commit_sha: str,
        status: TestStatus
    ) -> bool:
        """Report test status to GitHub.
        
        Args:
            repository: Repository information
            commit_sha: Commit SHA to report status for
            status: Test status to report
            
        Returns:
            True if status was reported successfully
        """
        url = f"{self.base_url}/repos/{repository.full_name}/statuses/{commit_sha}"
        
        # Map our status to GitHub status
        state_map = {
            TestStatusState.PENDING: 'pending',
            TestStatusState.SUCCESS: 'success',
            TestStatusState.FAILURE: 'failure',
            TestStatusState.ERROR: 'error'
        }
        
        payload = {
            'state': state_map[status.state],
            'description': status.description,
            'context': status.context
        }
        
        if status.target_url:
            payload['target_url'] = status.target_url
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully reported status to GitHub for {commit_sha}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report status to GitHub: {e}")
            return False
    
    def report_status_gitlab(
        self,
        repository: Repository,
        commit_sha: str,
        status: TestStatus
    ) -> bool:
        """Report test status to GitLab.
        
        Args:
            repository: Repository information
            commit_sha: Commit SHA to report status for
            status: Test status to report
            
        Returns:
            True if status was reported successfully
        """
        # Get project ID from full name
        project_path = repository.full_name.replace('/', '%2F')
        url = f"{self.base_url}/projects/{project_path}/statuses/{commit_sha}"
        
        # Map our status to GitLab status
        state_map = {
            TestStatusState.PENDING: 'pending',
            TestStatusState.SUCCESS: 'success',
            TestStatusState.FAILURE: 'failed',
            TestStatusState.ERROR: 'failed'
        }
        
        payload = {
            'state': state_map[status.state],
            'description': status.description,
            'name': status.context
        }
        
        if status.target_url:
            payload['target_url'] = status.target_url
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully reported status to GitLab for {commit_sha}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report status to GitLab: {e}")
            return False
    
    def report_status(
        self,
        repository: Repository,
        commit_sha: str,
        status: TestStatus
    ) -> bool:
        """Report test status to VCS.
        
        Args:
            repository: Repository information
            commit_sha: Commit SHA to report status for
            status: Test status to report
            
        Returns:
            True if status was reported successfully
        """
        if self.provider == VCSProvider.GITHUB:
            return self.report_status_github(repository, commit_sha, status)
        elif self.provider == VCSProvider.GITLAB:
            return self.report_status_gitlab(repository, commit_sha, status)
        else:
            logger.error(f"Unsupported VCS provider: {self.provider}")
            return False
    
    def create_comment_github(
        self,
        repository: Repository,
        pr_number: int,
        comment: str
    ) -> bool:
        """Create a comment on a GitHub pull request.
        
        Args:
            repository: Repository information
            pr_number: Pull request number
            comment: Comment text
            
        Returns:
            True if comment was created successfully
        """
        url = f"{self.base_url}/repos/{repository.full_name}/issues/{pr_number}/comments"
        
        payload = {'body': comment}
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully created comment on GitHub PR #{pr_number}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create comment on GitHub: {e}")
            return False
    
    def create_comment_gitlab(
        self,
        repository: Repository,
        mr_number: int,
        comment: str
    ) -> bool:
        """Create a comment on a GitLab merge request.
        
        Args:
            repository: Repository information
            mr_number: Merge request number
            comment: Comment text
            
        Returns:
            True if comment was created successfully
        """
        project_path = repository.full_name.replace('/', '%2F')
        url = f"{self.base_url}/projects/{project_path}/merge_requests/{mr_number}/notes"
        
        payload = {'body': comment}
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully created comment on GitLab MR !{mr_number}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create comment on GitLab: {e}")
            return False
    
    def create_comment(
        self,
        repository: Repository,
        pr_number: int,
        comment: str
    ) -> bool:
        """Create a comment on a pull/merge request.
        
        Args:
            repository: Repository information
            pr_number: Pull/merge request number
            comment: Comment text
            
        Returns:
            True if comment was created successfully
        """
        if self.provider == VCSProvider.GITHUB:
            return self.create_comment_github(repository, pr_number, comment)
        elif self.provider == VCSProvider.GITLAB:
            return self.create_comment_gitlab(repository, pr_number, comment)
        else:
            logger.error(f"Unsupported VCS provider: {self.provider}")
            return False
    
    def get_commit_diff_github(
        self,
        repository: Repository,
        commit_sha: str
    ) -> Optional[str]:
        """Get commit diff from GitHub.
        
        Args:
            repository: Repository information
            commit_sha: Commit SHA
            
        Returns:
            Diff content or None if failed
        """
        url = f"{self.base_url}/repos/{repository.full_name}/commits/{commit_sha}"
        
        try:
            # Request diff format
            headers = {'Accept': 'application/vnd.github.v3.diff'}
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get commit diff from GitHub: {e}")
            return None
    
    def get_commit_diff_gitlab(
        self,
        repository: Repository,
        commit_sha: str
    ) -> Optional[str]:
        """Get commit diff from GitLab.
        
        Args:
            repository: Repository information
            commit_sha: Commit SHA
            
        Returns:
            Diff content or None if failed
        """
        project_path = repository.full_name.replace('/', '%2F')
        url = f"{self.base_url}/projects/{project_path}/repository/commits/{commit_sha}/diff"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            # GitLab returns array of diff objects
            diffs = response.json()
            return '\n'.join(d.get('diff', '') for d in diffs)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get commit diff from GitLab: {e}")
            return None
    
    def get_commit_diff(
        self,
        repository: Repository,
        commit_sha: str
    ) -> Optional[str]:
        """Get commit diff from VCS.
        
        Args:
            repository: Repository information
            commit_sha: Commit SHA
            
        Returns:
            Diff content or None if failed
        """
        if self.provider == VCSProvider.GITHUB:
            return self.get_commit_diff_github(repository, commit_sha)
        elif self.provider == VCSProvider.GITLAB:
            return self.get_commit_diff_gitlab(repository, commit_sha)
        else:
            logger.error(f"Unsupported VCS provider: {self.provider}")
            return None
