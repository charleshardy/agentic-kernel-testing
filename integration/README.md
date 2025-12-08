# VCS Integration Module

This module provides comprehensive version control system (VCS) integration for automatic test triggering and result reporting.

## Features

- **Multi-Provider Support**: GitHub and GitLab
- **Webhook Handling**: Parse and process webhook events
- **Automatic Test Triggering**: Trigger tests on commits, PRs, and branch updates
- **Status Reporting**: Report test results back to VCS
- **PR Comments**: Create detailed comments on pull/merge requests
- **Security**: Webhook signature verification and token authentication

## Quick Start

### Installation

```python
from integration import VCSIntegration, VCSProvider, EventType
```

### Basic Usage

```python
import os
from integration import VCSIntegration, EventType

# Initialize with API tokens
integration = VCSIntegration(
    webhook_secret=os.getenv("WEBHOOK_SECRET"),
    github_token=os.getenv("GITHUB_TOKEN"),
    gitlab_token=os.getenv("GITLAB_TOKEN")
)

# Register event handler
def handle_push(event):
    print(f"Push to {event.repository.full_name}")
    if integration.should_trigger_tests(event):
        commits = integration.get_commits_to_test(event)
        # Trigger tests for commits
        
integration.register_event_handler(EventType.PUSH, handle_push)

# Handle webhook
event = integration.handle_webhook(
    VCSProvider.GITHUB,
    'push',
    webhook_payload,
    signature_header
)

# Report results
integration.report_test_results(
    VCSProvider.GITHUB,
    repository,
    commit_sha,
    test_results,
    logs_url='https://example.com/logs'
)
```

## Components

### VCS Models (`vcs_models.py`)

Data models for VCS integration:
- `VCSEvent`: Webhook event representation
- `Repository`: Repository information
- `CommitInfo`: Commit details with file changes
- `PullRequest`: PR/MR information
- `TestStatus`: Status for reporting
- `StatusReport`: Complete status report

### Webhook Parser (`webhook_parser.py`)

Parse webhook events from VCS providers:
- `WebhookParser.parse_event()`: Parse any webhook
- `WebhookParser.verify_github_signature()`: Verify GitHub webhooks
- `WebhookParser.verify_gitlab_signature()`: Verify GitLab webhooks

### VCS Client (`vcs_client.py`)

API client for VCS operations:
- `VCSClient.report_status()`: Report commit status
- `VCSClient.create_comment()`: Create PR/MR comments
- `VCSClient.get_commit_diff()`: Fetch commit diffs

### VCS Integration (`vcs_integration.py`)

Main integration handler:
- `VCSIntegration.handle_webhook()`: Process webhooks
- `VCSIntegration.register_event_handler()`: Register callbacks
- `VCSIntegration.report_test_results()`: Report aggregated results
- `VCSIntegration.should_trigger_tests()`: Determine if tests should run

## Configuration

Set environment variables:

```bash
# Webhook signature verification
export VCS_WEBHOOK_SECRET="your-webhook-secret"

# GitHub API token
export GITHUB_TOKEN="ghp_your_github_token"

# GitLab API token
export GITLAB_TOKEN="glpat-your_gitlab_token"
```

Or configure in code:

```python
from config import get_settings

settings = get_settings()
integration = VCSIntegration(
    webhook_secret=settings.vcs_webhook_secret,
    github_token=settings.github_token,
    gitlab_token=settings.gitlab_token
)
```

## Event Types

Supported event types:
- `EventType.PUSH`: Push to repository
- `EventType.PULL_REQUEST`: PR opened/updated/closed
- `EventType.BRANCH_UPDATE`: Branch created/deleted
- `EventType.COMMIT`: Individual commit
- `EventType.TAG`: Tag created

## Status States

Test status states for reporting:
- `TestStatusState.PENDING`: Tests are running
- `TestStatusState.SUCCESS`: All tests passed
- `TestStatusState.FAILURE`: Some tests failed
- `TestStatusState.ERROR`: Tests encountered errors

## Examples

See `examples/vcs_integration_example.py` for comprehensive examples:
1. Webhook event handling
2. Status reporting
3. PR commenting
4. Multi-provider support

## Testing

Run property-based tests:

```bash
# Test VCS trigger responsiveness
pytest tests/property/test_vcs_trigger_responsiveness.py -v

# Test result reporting completeness
pytest tests/property/test_vcs_result_reporting.py -v
```

## API Reference

### VCSIntegration

Main integration class.

**Methods:**
- `handle_webhook(provider, event_type, payload, signature)`: Process webhook
- `register_event_handler(event_type, handler)`: Register event callback
- `report_status(provider, repository, commit_sha, status)`: Report status
- `report_test_results(provider, repository, commit_sha, results, logs_url)`: Report results
- `report_pending(provider, repository, commit_sha, message)`: Report pending
- `create_pr_comment(provider, repository, pr_number, comment)`: Create comment
- `get_commit_diff(provider, repository, commit_sha)`: Get diff
- `should_trigger_tests(event)`: Check if tests should run
- `get_commits_to_test(event)`: Extract commits to test

### WebhookParser

Webhook parsing utility.

**Methods:**
- `parse_event(provider, event_type, payload, signature)`: Parse webhook
- `verify_github_signature(payload, signature)`: Verify GitHub signature
- `verify_gitlab_signature(token)`: Verify GitLab token

### VCSClient

VCS API client.

**Methods:**
- `report_status(repository, commit_sha, status)`: Report status
- `create_comment(repository, pr_number, comment)`: Create comment
- `get_commit_diff(repository, commit_sha)`: Get diff

## Security

- Webhook signatures are verified using HMAC-SHA256 (GitHub) or tokens (GitLab)
- API tokens are stored securely and never logged
- All API requests use HTTPS
- Automatic retry with exponential backoff prevents abuse

## Error Handling

- Invalid signatures raise `ValueError`
- Missing clients return `False` from operations
- Network errors are logged and retried automatically
- Malformed payloads are caught and logged

## Requirements

- Python 3.10+
- requests
- pydantic
- hypothesis (for testing)
- pytest (for testing)

## License

See LICENSE file in project root.
