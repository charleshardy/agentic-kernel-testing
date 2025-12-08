"""Main VCS integration handler for automatic test triggering."""

import logging
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

from integration.vcs_models import (
    VCSEvent, VCSProvider, EventType, Repository, TestStatus,
    TestStatusState, StatusReport
)
from integration.webhook_parser import WebhookParser
from integration.vcs_client import VCSClient
from ai_generator.models import TestResult, TestStatus as TestResultStatus

logger = logging.getLogger(__name__)


class VCSIntegration:
    """Main VCS integration handler."""
    
    def __init__(
        self,
        webhook_secret: Optional[str] = None,
        github_token: Optional[str] = None,
        gitlab_token: Optional[str] = None,
        github_base_url: Optional[str] = None,
        gitlab_base_url: Optional[str] = None
    ):
        """Initialize VCS integration.
        
        Args:
            webhook_secret: Secret for webhook signature verification
            github_token: GitHub API token
            gitlab_token: GitLab API token
            github_base_url: Custom GitHub API base URL
            gitlab_base_url: Custom GitLab API base URL
        """
        self.parser = WebhookParser(webhook_secret)
        
        # Initialize VCS clients
        self.github_client = None
        if github_token:
            self.github_client = VCSClient(
                VCSProvider.GITHUB,
                github_token,
                github_base_url
            )
        
        self.gitlab_client = None
        if gitlab_token:
            self.gitlab_client = VCSClient(
                VCSProvider.GITLAB,
                gitlab_token,
                gitlab_base_url
            )
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = {
            EventType.PUSH: [],
            EventType.PULL_REQUEST: [],
            EventType.BRANCH_UPDATE: [],
            EventType.COMMIT: [],
            EventType.TAG: []
        }
    
    def register_event_handler(
        self,
        event_type: EventType,
        handler: Callable[[VCSEvent], None]
    ) -> None:
        """Register a handler for VCS events.
        
        Args:
            event_type: Type of event to handle
            handler: Callback function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type.value} events")
    
    def handle_webhook(
        self,
        provider: VCSProvider,
        event_type: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> VCSEvent:
        """Handle incoming webhook event.
        
        Args:
            provider: VCS provider
            event_type: Event type header value
            payload: Parsed JSON payload
            signature: Signature/token for verification
            
        Returns:
            Parsed VCS event
            
        Raises:
            ValueError: If signature verification fails
        """
        # Parse the event
        event = self.parser.parse_event(provider, event_type, payload, signature)
        logger.info(
            f"Received {event.event_type.value} event from {event.provider.value} "
            f"for {event.repository.full_name}"
        )
        
        # Trigger registered handlers
        self._trigger_handlers(event)
        
        return event
    
    def _trigger_handlers(self, event: VCSEvent) -> None:
        """Trigger registered handlers for an event.
        
        Args:
            event: VCS event to handle
        """
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event.event_type.value}: {e}",
                    exc_info=True
                )
    
    def report_status(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str,
        status: TestStatus
    ) -> bool:
        """Report test status back to VCS.
        
        Args:
            provider: VCS provider
            repository: Repository information
            commit_sha: Commit SHA to report status for
            status: Test status to report
            
        Returns:
            True if status was reported successfully
        """
        client = self._get_client(provider)
        if not client:
            logger.error(f"No client configured for {provider.value}")
            return False
        
        return client.report_status(repository, commit_sha, status)
    
    def report_test_results(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str,
        test_results: List[TestResult],
        logs_url: Optional[str] = None
    ) -> bool:
        """Report aggregated test results to VCS.
        
        Args:
            provider: VCS provider
            repository: Repository information
            commit_sha: Commit SHA
            test_results: List of test results
            logs_url: URL to detailed logs
            
        Returns:
            True if status was reported successfully
        """
        # Aggregate results
        total_tests = len(test_results)
        passed = sum(1 for r in test_results if r.status == TestResultStatus.PASSED)
        failed = sum(1 for r in test_results if r.status == TestResultStatus.FAILED)
        errors = sum(1 for r in test_results if r.status == TestResultStatus.ERROR)
        
        # Determine overall status
        if errors > 0:
            state = TestStatusState.ERROR
            description = f"Tests completed with errors: {passed}/{total_tests} passed, {failed} failed, {errors} errors"
        elif failed > 0:
            state = TestStatusState.FAILURE
            description = f"Tests failed: {passed}/{total_tests} passed, {failed} failed"
        else:
            state = TestStatusState.SUCCESS
            description = f"All tests passed: {passed}/{total_tests}"
        
        status = TestStatus(
            state=state,
            description=description,
            target_url=logs_url,
            context="agentic-testing"
        )
        
        return self.report_status(provider, repository, commit_sha, status)
    
    def report_pending(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str,
        message: str = "Tests are running..."
    ) -> bool:
        """Report pending status to VCS.
        
        Args:
            provider: VCS provider
            repository: Repository information
            commit_sha: Commit SHA
            message: Pending message
            
        Returns:
            True if status was reported successfully
        """
        status = TestStatus(
            state=TestStatusState.PENDING,
            description=message,
            context="agentic-testing"
        )
        
        return self.report_status(provider, repository, commit_sha, status)
    
    def create_pr_comment(
        self,
        provider: VCSProvider,
        repository: Repository,
        pr_number: int,
        comment: str
    ) -> bool:
        """Create a comment on a pull/merge request.
        
        Args:
            provider: VCS provider
            repository: Repository information
            pr_number: Pull/merge request number
            comment: Comment text
            
        Returns:
            True if comment was created successfully
        """
        client = self._get_client(provider)
        if not client:
            logger.error(f"No client configured for {provider.value}")
            return False
        
        return client.create_comment(repository, pr_number, comment)
    
    def get_commit_diff(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str
    ) -> Optional[str]:
        """Get commit diff from VCS.
        
        Args:
            provider: VCS provider
            repository: Repository information
            commit_sha: Commit SHA
            
        Returns:
            Diff content or None if failed
        """
        client = self._get_client(provider)
        if not client:
            logger.error(f"No client configured for {provider.value}")
            return None
        
        return client.get_commit_diff(repository, commit_sha)
    
    def _get_client(self, provider: VCSProvider) -> Optional[VCSClient]:
        """Get VCS client for provider.
        
        Args:
            provider: VCS provider
            
        Returns:
            VCS client or None if not configured
        """
        if provider == VCSProvider.GITHUB:
            return self.github_client
        elif provider == VCSProvider.GITLAB:
            return self.gitlab_client
        else:
            return None
    
    def should_trigger_tests(self, event: VCSEvent) -> bool:
        """Determine if tests should be triggered for an event.
        
        Args:
            event: VCS event
            
        Returns:
            True if tests should be triggered
        """
        # Trigger tests for pushes and pull requests
        if event.event_type in [EventType.PUSH, EventType.PULL_REQUEST]:
            return True
        
        # Don't trigger for branch deletions
        if event.event_type == EventType.BRANCH_UPDATE and event.after_sha == '0' * 40:
            return False
        
        # Trigger for other branch updates
        if event.event_type == EventType.BRANCH_UPDATE:
            return True
        
        return False
    
    def get_commits_to_test(self, event: VCSEvent) -> List[str]:
        """Get list of commit SHAs to test from an event.
        
        Args:
            event: VCS event
            
        Returns:
            List of commit SHAs
        """
        commit_shas = []
        
        # For pull requests, test all commits in the PR
        if event.pull_request:
            commit_shas = [c.sha for c in event.pull_request.commits]
        
        # For pushes, test all commits in the push
        if event.commits:
            commit_shas.extend([c.sha for c in event.commits])
        
        # If we have after_sha, include it
        if event.after_sha and event.after_sha not in commit_shas:
            commit_shas.append(event.after_sha)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_shas = []
        for sha in commit_shas:
            if sha not in seen and sha != '0' * 40:
                seen.add(sha)
                unique_shas.append(sha)
        
        return unique_shas
