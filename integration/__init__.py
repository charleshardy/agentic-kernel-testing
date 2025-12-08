"""External system integration module."""

__version__ = "0.1.0"

from integration.vcs_models import (
    VCSProvider, EventType, PRAction, TestStatusState,
    Repository, Author, CommitInfo, PullRequest,
    VCSEvent, TestStatus, StatusReport
)
from integration.webhook_parser import WebhookParser
from integration.vcs_client import VCSClient
from integration.vcs_integration import VCSIntegration

__all__ = [
    'VCSProvider',
    'EventType',
    'PRAction',
    'TestStatusState',
    'Repository',
    'Author',
    'CommitInfo',
    'PullRequest',
    'VCSEvent',
    'TestStatus',
    'StatusReport',
    'WebhookParser',
    'VCSClient',
    'VCSIntegration',
]
