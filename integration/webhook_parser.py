"""Webhook event parser for GitHub and GitLab."""

import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from integration.vcs_models import (
    VCSEvent, VCSProvider, EventType, Repository, Author,
    CommitInfo, PullRequest, PRAction
)

logger = logging.getLogger(__name__)


class WebhookParser:
    """Parse webhook events from VCS providers."""
    
    def __init__(self, webhook_secret: Optional[str] = None):
        """Initialize webhook parser.
        
        Args:
            webhook_secret: Secret for validating webhook signatures
        """
        self.webhook_secret = webhook_secret
    
    def verify_github_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        if not signature.startswith('sha256='):
            return False
        
        expected_signature = 'sha256=' + hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def verify_gitlab_signature(self, token: str) -> bool:
        """Verify GitLab webhook token.
        
        Args:
            token: X-Gitlab-Token header value
            
        Returns:
            True if token is valid
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping token verification")
            return True
        
        return hmac.compare_digest(self.webhook_secret, token)
    
    def parse_github_event(self, event_type: str, payload: Dict[str, Any]) -> VCSEvent:
        """Parse GitHub webhook event.
        
        Args:
            event_type: X-GitHub-Event header value
            payload: Parsed JSON payload
            
        Returns:
            Parsed VCS event
        """
        # Extract repository info
        repo_data = payload.get('repository', {})
        repository = Repository(
            name=repo_data.get('name', ''),
            full_name=repo_data.get('full_name', ''),
            owner=repo_data.get('owner', {}).get('login', ''),
            url=repo_data.get('html_url', ''),
            clone_url=repo_data.get('clone_url', ''),
            default_branch=repo_data.get('default_branch', 'main')
        )
        
        # Determine event type
        if event_type == 'push':
            vcs_event_type = EventType.PUSH
        elif event_type == 'pull_request':
            vcs_event_type = EventType.PULL_REQUEST
        elif event_type == 'create' or event_type == 'delete':
            vcs_event_type = EventType.BRANCH_UPDATE
        else:
            vcs_event_type = EventType.COMMIT
        
        # Parse commits
        commits = []
        for commit_data in payload.get('commits', []):
            author_data = commit_data.get('author', {})
            author = Author(
                name=author_data.get('name', ''),
                email=author_data.get('email', ''),
                username=author_data.get('username')
            )
            
            commit = CommitInfo(
                sha=commit_data.get('id', ''),
                message=commit_data.get('message', ''),
                author=author,
                timestamp=datetime.fromisoformat(
                    commit_data.get('timestamp', datetime.now().isoformat()).replace('Z', '+00:00')
                ),
                url=commit_data.get('url', ''),
                added_files=commit_data.get('added', []),
                modified_files=commit_data.get('modified', []),
                removed_files=commit_data.get('removed', [])
            )
            commits.append(commit)
        
        # Parse pull request if present
        pull_request = None
        if 'pull_request' in payload:
            pr_data = payload['pull_request']
            pr_author_data = pr_data.get('user', {})
            pr_author = Author(
                name=pr_author_data.get('name', pr_author_data.get('login', '')),
                email=pr_author_data.get('email', ''),
                username=pr_author_data.get('login')
            )
            
            # Map GitHub PR action to our enum
            action_map = {
                'opened': PRAction.OPENED,
                'closed': PRAction.CLOSED,
                'reopened': PRAction.REOPENED,
                'synchronize': PRAction.SYNCHRONIZED
            }
            pr_action = action_map.get(payload.get('action', 'opened'), PRAction.OPENED)
            
            pull_request = PullRequest(
                number=pr_data.get('number', 0),
                title=pr_data.get('title', ''),
                description=pr_data.get('body', ''),
                author=pr_author,
                source_branch=pr_data.get('head', {}).get('ref', ''),
                target_branch=pr_data.get('base', {}).get('ref', ''),
                url=pr_data.get('html_url', ''),
                action=pr_action,
                is_merged=pr_data.get('merged', False)
            )
        
        # Create VCS event
        event = VCSEvent(
            event_id=payload.get('delivery', payload.get('hook_id', str(datetime.now().timestamp()))),
            provider=VCSProvider.GITHUB,
            event_type=vcs_event_type,
            repository=repository,
            timestamp=datetime.now(),
            commits=commits,
            pull_request=pull_request,
            branch=payload.get('ref', '').replace('refs/heads/', ''),
            ref=payload.get('ref'),
            before_sha=payload.get('before'),
            after_sha=payload.get('after'),
            metadata={'raw_event_type': event_type}
        )
        
        return event
    
    def parse_gitlab_event(self, event_type: str, payload: Dict[str, Any]) -> VCSEvent:
        """Parse GitLab webhook event.
        
        Args:
            event_type: X-Gitlab-Event header value
            payload: Parsed JSON payload
            
        Returns:
            Parsed VCS event
        """
        # Extract repository info
        project = payload.get('project', {})
        repository = Repository(
            name=project.get('name', ''),
            full_name=project.get('path_with_namespace', ''),
            owner=project.get('namespace', ''),
            url=project.get('web_url', ''),
            clone_url=project.get('git_http_url', ''),
            default_branch=project.get('default_branch', 'main')
        )
        
        # Determine event type
        if event_type == 'Push Hook':
            vcs_event_type = EventType.PUSH
        elif event_type == 'Merge Request Hook':
            vcs_event_type = EventType.PULL_REQUEST
        elif event_type == 'Tag Push Hook':
            vcs_event_type = EventType.TAG
        else:
            vcs_event_type = EventType.COMMIT
        
        # Parse commits
        commits = []
        for commit_data in payload.get('commits', []):
            author_data = commit_data.get('author', {})
            author = Author(
                name=author_data.get('name', ''),
                email=author_data.get('email', '')
            )
            
            commit = CommitInfo(
                sha=commit_data.get('id', ''),
                message=commit_data.get('message', ''),
                author=author,
                timestamp=datetime.fromisoformat(
                    commit_data.get('timestamp', datetime.now().isoformat()).replace('Z', '+00:00')
                ),
                url=commit_data.get('url', ''),
                added_files=commit_data.get('added', []),
                modified_files=commit_data.get('modified', []),
                removed_files=commit_data.get('removed', [])
            )
            commits.append(commit)
        
        # Parse merge request if present
        pull_request = None
        if 'object_attributes' in payload and event_type == 'Merge Request Hook':
            mr_data = payload['object_attributes']
            mr_author_data = mr_data.get('author', payload.get('user', {}))
            mr_author = Author(
                name=mr_author_data.get('name', ''),
                email=mr_author_data.get('email', ''),
                username=mr_author_data.get('username')
            )
            
            # Map GitLab MR action to our enum
            action_map = {
                'open': PRAction.OPENED,
                'close': PRAction.CLOSED,
                'reopen': PRAction.REOPENED,
                'update': PRAction.SYNCHRONIZED,
                'merge': PRAction.MERGED
            }
            mr_action = action_map.get(mr_data.get('action', 'open'), PRAction.OPENED)
            
            pull_request = PullRequest(
                number=mr_data.get('iid', 0),
                title=mr_data.get('title', ''),
                description=mr_data.get('description', ''),
                author=mr_author,
                source_branch=mr_data.get('source_branch', ''),
                target_branch=mr_data.get('target_branch', ''),
                url=mr_data.get('url', ''),
                action=mr_action,
                is_merged=mr_data.get('state', '') == 'merged'
            )
        
        # Create VCS event
        event = VCSEvent(
            event_id=str(payload.get('event_id', payload.get('object_kind', str(datetime.now().timestamp())))),
            provider=VCSProvider.GITLAB,
            event_type=vcs_event_type,
            repository=repository,
            timestamp=datetime.now(),
            commits=commits,
            pull_request=pull_request,
            branch=payload.get('ref', '').replace('refs/heads/', ''),
            ref=payload.get('ref'),
            before_sha=payload.get('before'),
            after_sha=payload.get('after'),
            metadata={'raw_event_type': event_type}
        )
        
        return event
    
    def parse_event(
        self,
        provider: VCSProvider,
        event_type: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> VCSEvent:
        """Parse webhook event from any supported provider.
        
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
        if provider == VCSProvider.GITHUB:
            if signature and not self.verify_github_signature(
                str(payload).encode(), signature
            ):
                raise ValueError("Invalid GitHub webhook signature")
            return self.parse_github_event(event_type, payload)
        elif provider == VCSProvider.GITLAB:
            if signature and not self.verify_gitlab_signature(signature):
                raise ValueError("Invalid GitLab webhook token")
            return self.parse_gitlab_event(event_type, payload)
        else:
            raise ValueError(f"Unsupported VCS provider: {provider}")
