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


---

# Build System Integration

This module provides comprehensive build system integration for automatic test triggering when builds complete.

## Features

- **Multi-System Support**: Jenkins, GitLab CI, GitHub Actions
- **Build Completion Detection**: Automatically detect when builds finish
- **Automatic Test Triggering**: Trigger tests for successful builds
- **Artifact Handling**: Extract kernel images and BSP packages
- **Build Caching**: Cache build information for retrieval
- **Multiple Handlers**: Support multiple test handlers per build

## Quick Start

### Installation

```python
from integration import BuildIntegration
from integration.build_models import BuildSystem, BuildType
```

### Basic Usage

```python
from integration import BuildIntegration

# Initialize build integration
integration = BuildIntegration()

# Register build completion handler
def handle_build_complete(build_event):
    build_info = build_event.build_info
    print(f"Build {build_info.build_id} completed successfully")
    
    # Extract kernel image if available
    kernel_image = integration.extract_kernel_image(build_info)
    if kernel_image:
        print(f"Kernel {kernel_image.version} ready for testing")
        # Trigger kernel tests...
    
    # Extract BSP package if available
    bsp_package = integration.extract_bsp_package(build_info)
    if bsp_package:
        print(f"BSP {bsp_package.name} ready for testing")
        # Trigger BSP tests...

integration.register_build_handler(handle_build_complete)

# Parse Jenkins webhook
jenkins_event = integration.parse_jenkins_event(jenkins_payload)
integration.handle_build_event(jenkins_event)

# Parse GitLab CI webhook
gitlab_event = integration.parse_gitlab_ci_event(gitlab_payload)
integration.handle_build_event(gitlab_event)

# Parse GitHub Actions webhook
github_event = integration.parse_github_actions_event(github_payload)
integration.handle_build_event(github_event)
```

## Components

### Build Models (`build_models.py`)

Data models for build system integration:
- `BuildEvent`: Build system event representation
- `BuildInfo`: Detailed build information
- `BuildArtifact`: Build artifact details
- `KernelImage`: Kernel image information
- `BSPPackage`: BSP package information
- `BuildStatus`: Build status enumeration
- `BuildType`: Build type enumeration
- `BuildSystem`: Build system enumeration

### Build Integration (`build_integration.py`)

Main build integration handler:
- `BuildIntegration.handle_build_event()`: Process build events
- `BuildIntegration.register_build_handler()`: Register callbacks
- `BuildIntegration.detect_build_completion()`: Check if build is complete
- `BuildIntegration.should_trigger_tests()`: Determine if tests should run
- `BuildIntegration.extract_kernel_image()`: Extract kernel from artifacts
- `BuildIntegration.extract_bsp_package()`: Extract BSP from artifacts
- `BuildIntegration.parse_jenkins_event()`: Parse Jenkins webhooks
- `BuildIntegration.parse_gitlab_ci_event()`: Parse GitLab CI webhooks
- `BuildIntegration.parse_github_actions_event()`: Parse GitHub Actions webhooks

## Build Types

The system supports different build types:

- `BuildType.KERNEL`: Linux kernel builds
- `BuildType.BSP`: Board Support Package builds
- `BuildType.MODULE`: Kernel module builds
- `BuildType.FULL_SYSTEM`: Complete system builds (kernel + BSP)

## Build Status

Build status states:

- `BuildStatus.PENDING`: Build is queued
- `BuildStatus.IN_PROGRESS`: Build is running
- `BuildStatus.SUCCESS`: Build completed successfully
- `BuildStatus.FAILURE`: Build failed
- `BuildStatus.CANCELLED`: Build was cancelled

## Automatic Test Triggering

Tests are automatically triggered when:

1. Build completes successfully (`BuildStatus.SUCCESS`)
2. Build type is testable (kernel, BSP, full_system, or module with artifacts)
3. Build has extractable artifacts (kernel images or BSP packages)

The system will NOT trigger tests for:
- Failed builds
- Cancelled builds
- In-progress builds
- Module builds without artifacts

## Artifact Extraction

### Kernel Images

Kernel images can be extracted from:
- Direct `kernel_image` field in build info
- Build artifacts with type `kernel_image`

Extracted kernel images include:
- Version
- Architecture
- Image path
- Config path
- Modules path
- Build timestamp
- Commit SHA

### BSP Packages

BSP packages can be extracted from:
- Direct `bsp_package` field in build info
- Build artifacts with type `bsp_package`

Extracted BSP packages include:
- Name and version
- Target board
- Architecture
- Package path
- Kernel version
- Build timestamp
- Commit SHA

## Build System Support

### Jenkins

Parse Jenkins build notifications:

```python
jenkins_payload = {
    "build": {
        "number": 1234,
        "status": "SUCCESS",
        "timestamp": 1234567890000,
        "duration": 300000,
        "url": "https://jenkins.example.com/job/kernel/1234",
        "artifacts": [...]
    },
    "scm": {
        "commit": "abc123...",
        "branch": "main"
    }
}

event = integration.parse_jenkins_event(jenkins_payload)
```

### GitLab CI

Parse GitLab CI pipeline webhooks:

```python
gitlab_payload = {
    "build": {
        "id": 5678,
        "status": "success",
        "started_at": "2024-01-01T12:00:00Z",
        "finished_at": "2024-01-01T12:05:00Z",
        "duration": 300,
        "sha": "def456...",
        "ref": "main"
    }
}

event = integration.parse_gitlab_ci_event(gitlab_payload)
```

### GitHub Actions

Parse GitHub Actions workflow run webhooks:

```python
github_payload = {
    "workflow_run": {
        "id": 9999,
        "status": "completed",
        "conclusion": "success",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:05:00Z",
        "head_sha": "ghi789...",
        "head_branch": "main"
    }
}

event = integration.parse_github_actions_event(github_payload)
```

## Examples

See `examples/build_integration_example.py` for comprehensive examples:
1. Successful kernel build handling
2. Successful BSP build handling
3. Failed build handling (no tests triggered)
4. Jenkins webhook parsing
5. Artifact extraction

## Testing

Run property-based tests:

```bash
# Test build integration automation
pytest tests/property/test_build_integration_automation.py -v
```

The test suite validates:
- Successful builds trigger handlers
- Failed builds do not trigger tests
- Build completion detection
- Test triggering logic
- Multiple build handling
- Kernel image extraction
- BSP package extraction
- Build caching
- Multiple handler support
- In-progress build handling

## API Reference

### BuildIntegration

Main build integration class.

**Methods:**
- `register_build_handler(handler)`: Register build completion callback
- `detect_build_completion(build_info)`: Check if build is complete
- `should_trigger_tests(build_info)`: Determine if tests should run
- `handle_build_event(build_event)`: Process build event
- `extract_kernel_image(build_info)`: Extract kernel from build
- `extract_bsp_package(build_info)`: Extract BSP from build
- `parse_jenkins_event(payload)`: Parse Jenkins webhook
- `parse_gitlab_ci_event(payload)`: Parse GitLab CI webhook
- `parse_github_actions_event(payload)`: Parse GitHub Actions webhook
- `get_build_info(build_id)`: Retrieve cached build info

## Configuration

Build integration works out of the box without configuration. Build events are parsed automatically based on the webhook payload structure.

Optional metadata can be included in build payloads:
- `build_type`: Explicitly specify build type
- `kernel_version`: Kernel version being built
- `architecture`: Target architecture
- `target_board`: Target board for BSP builds
- `bsp_version`: BSP version

## Error Handling

- Invalid build events are logged and skipped
- Handler exceptions are caught and logged
- Missing artifacts are handled gracefully
- Build cache prevents duplicate processing

## Integration with VCS

Build integration works seamlessly with VCS integration:

```python
from integration import VCSIntegration, BuildIntegration

vcs = VCSIntegration(...)
build = BuildIntegration()

# When VCS event triggers a build
def handle_vcs_push(vcs_event):
    # Trigger build...
    pass

# When build completes, trigger tests
def handle_build_complete(build_event):
    # Extract artifacts and run tests...
    # Report results back to VCS
    vcs.report_test_results(...)

vcs.register_event_handler(EventType.PUSH, handle_vcs_push)
build.register_build_handler(handle_build_complete)
```

## Requirements

- Python 3.10+
- pydantic
- hypothesis (for testing)
- pytest (for testing)

## License

See LICENSE file in project root.


---

# Notification System

This module provides comprehensive notification capabilities for sending alerts through multiple channels (Email, Slack, Microsoft Teams).

## Features

- **Multi-Channel Support**: Email, Slack, Microsoft Teams
- **Severity-Based Routing**: Automatic channel selection based on severity
- **Flexible Filtering**: Filter notifications by severity threshold
- **Rich Formatting**: HTML emails, Slack attachments, Teams cards
- **Metadata Support**: Include additional context in notifications
- **Configurable**: Enable/disable channels via configuration

## Quick Start

### Installation

```python
from integration.notification_service import NotificationDispatcher
from integration.notification_models import (
    Notification,
    NotificationSeverity,
    NotificationChannel,
    NotificationRecipient
)
```

### Basic Usage

```python
from integration.notification_service import NotificationDispatcher
from integration.notification_models import (
    Notification,
    NotificationSeverity,
    NotificationChannel,
    NotificationRecipient
)

# Initialize dispatcher
dispatcher = NotificationDispatcher()

# Create a notification
notification = Notification(
    id="test_001",
    title="Test Execution Started",
    message="Test suite for kernel module xyz has started execution.",
    severity=NotificationSeverity.INFO,
    channels=[NotificationChannel.SLACK],
    recipients=[
        NotificationRecipient(
            name="Developer",
            email="dev@example.com",
            slack_user_id="U12345"
        )
    ],
    test_id="test_xyz_001"
)

# Send notification
results = dispatcher.send_notification(notification)

for result in results:
    print(f"Channel: {result.channel.value}, Success: {result.success}")
```

### Critical Failure Notification

```python
# Send critical failure notification (convenience method)
results = dispatcher.send_critical_failure_notification(
    title="Kernel Panic Detected",
    message="A kernel panic was detected during test execution.",
    test_id="test_network_driver_042",
    failure_id="failure_20231208_001",
    recipients=[
        NotificationRecipient(
            name="Kernel Team Lead",
            email="kernel-lead@example.com"
        )
    ],
    metadata={
        "subsystem": "network",
        "driver": "e1000e",
        "kernel_version": "6.5.0",
        "crash_type": "NULL pointer dereference"
    }
)
```

## Components

### Notification Models (`notification_models.py`)

Data models for notifications:
- `Notification`: Complete notification with title, message, severity, channels, recipients
- `NotificationRecipient`: Recipient information (name, email, Slack/Teams IDs)
- `NotificationResult`: Result of sending a notification
- `NotificationSeverity`: Severity levels (INFO, WARNING, ERROR, CRITICAL)
- `NotificationChannel`: Delivery channels (EMAIL, SLACK, TEAMS, WEBHOOK)

### Notification Service (`notification_service.py`)

Notification delivery service:
- `NotificationDispatcher`: Main dispatcher for sending notifications
- `EmailChannel`: Email notification handler
- `SlackChannel`: Slack notification handler
- `TeamsChannel`: Microsoft Teams notification handler

## Severity Levels

Notifications support four severity levels:

- `NotificationSeverity.INFO`: Informational messages
- `NotificationSeverity.WARNING`: Warning messages
- `NotificationSeverity.ERROR`: Error messages
- `NotificationSeverity.CRITICAL`: Critical failures requiring immediate attention

## Notification Channels

### Email

Send notifications via SMTP:

**Configuration:**
```bash
NOTIFICATION__EMAIL_ENABLED=true
NOTIFICATION__EMAIL_SMTP_HOST=smtp.gmail.com
NOTIFICATION__EMAIL_SMTP_PORT=587
NOTIFICATION__EMAIL_FROM=noreply@example.com
```

**Features:**
- Plain text and HTML formatting
- Severity-based color coding
- Metadata display
- Test and failure ID inclusion

### Slack

Send notifications to Slack via webhooks:

**Configuration:**
```bash
NOTIFICATION__SLACK_ENABLED=true
NOTIFICATION__SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Features:**
- Rich message attachments
- Severity-based emojis and colors
- Structured field display
- Metadata support

### Microsoft Teams

Send notifications to Teams via webhooks:

**Configuration:**
```python
# Teams webhook URL passed to dispatcher
dispatcher = NotificationDispatcher(
    teams_webhook_url="https://outlook.office.com/webhook/..."
)
```

**Features:**
- MessageCard format
- Severity-based color coding
- Structured facts display
- Metadata support

## Automatic Routing

The dispatcher can automatically route notifications to appropriate channels based on severity:

```python
# Default routing rules
routing_rules = {
    NotificationSeverity.INFO: [NotificationChannel.SLACK],
    NotificationSeverity.WARNING: [NotificationChannel.SLACK],
    NotificationSeverity.ERROR: [NotificationChannel.SLACK, NotificationChannel.EMAIL],
    NotificationSeverity.CRITICAL: [
        NotificationChannel.SLACK,
        NotificationChannel.EMAIL,
        NotificationChannel.TEAMS
    ]
}

# Apply routing
notification = dispatcher.route_notification(notification)
```

### Custom Routing

Define custom routing rules:

```python
custom_rules = {
    NotificationSeverity.INFO: [NotificationChannel.SLACK],
    NotificationSeverity.WARNING: [NotificationChannel.EMAIL],
    NotificationSeverity.ERROR: [NotificationChannel.EMAIL, NotificationChannel.TEAMS],
    NotificationSeverity.CRITICAL: [
        NotificationChannel.EMAIL,
        NotificationChannel.SLACK,
        NotificationChannel.TEAMS
    ]
}

notification = dispatcher.route_notification(notification, custom_rules)
```

## Severity Filtering

Filter notifications by minimum severity:

```python
# Only send ERROR and CRITICAL notifications
min_severity = NotificationSeverity.ERROR

if dispatcher.filter_by_severity(notification, min_severity):
    results = dispatcher.send_notification(notification)
```

## Metadata Enrichment

Include additional context in notifications:

```python
notification = Notification(
    id="perf_001",
    title="Performance Regression Detected",
    message="A performance regression was detected in the I/O subsystem.",
    severity=NotificationSeverity.WARNING,
    test_id="perf_io_test_001",
    metadata={
        "subsystem": "I/O",
        "benchmark": "FIO sequential write",
        "baseline_throughput": "500 MB/s",
        "current_throughput": "350 MB/s",
        "regression_percentage": "30%",
        "commit_range": "abc123..def456"
    }
)
```

## Configuration

Configure notification channels in `.env`:

```bash
# Enable notifications
NOTIFICATION__ENABLED=true

# Email configuration
NOTIFICATION__EMAIL_ENABLED=true
NOTIFICATION__EMAIL_SMTP_HOST=smtp.gmail.com
NOTIFICATION__EMAIL_SMTP_PORT=587
NOTIFICATION__EMAIL_FROM=noreply@example.com

# Slack configuration
NOTIFICATION__SLACK_ENABLED=true
NOTIFICATION__SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Or configure programmatically:

```python
from config import get_settings

settings = get_settings()
settings.notification.email_enabled = True
settings.notification.slack_enabled = True
```

## Examples

See `examples/notification_examples.py` for comprehensive examples:
1. Basic notification
2. Critical failure notification
3. Severity-based routing
4. Custom routing rules
5. Severity filtering
6. Metadata enrichment

## Testing

Run property-based tests:

```bash
# Test critical failure notification
pytest tests/property/test_critical_failure_notification.py -v
```

The test suite validates:
- Critical failures trigger notifications
- All configured channels receive notifications
- Notification content is complete
- Severity routing works correctly
- Filtering by severity works
- Multiple recipients are supported

## API Reference

### NotificationDispatcher

Main notification dispatcher class.

**Methods:**
- `send_notification(notification)`: Send notification through specified channels
- `route_notification(notification, routing_rules)`: Route based on severity
- `filter_by_severity(notification, min_severity)`: Check severity threshold
- `send_critical_failure_notification(...)`: Convenience method for critical failures

### Notification

Notification data model.

**Fields:**
- `id`: Unique notification identifier
- `title`: Notification title
- `message`: Notification message
- `severity`: Severity level
- `channels`: List of delivery channels
- `recipients`: List of recipients
- `metadata`: Additional context
- `timestamp`: Notification timestamp
- `test_id`: Associated test ID (optional)
- `failure_id`: Associated failure ID (optional)

### NotificationRecipient

Recipient information.

**Fields:**
- `name`: Recipient name
- `email`: Email address (for email channel)
- `slack_user_id`: Slack user ID (for Slack channel)
- `teams_user_id`: Teams user ID (for Teams channel)

### NotificationResult

Result of sending a notification.

**Fields:**
- `notification_id`: Notification ID
- `channel`: Channel used
- `success`: Whether sending succeeded
- `error_message`: Error message if failed
- `timestamp`: Result timestamp

## Integration with Test System

Integrate notifications with test execution:

```python
from integration.notification_service import NotificationDispatcher
from integration.notification_models import (
    Notification,
    NotificationSeverity,
    NotificationRecipient
)

dispatcher = NotificationDispatcher()

# When test fails
def handle_test_failure(test_result):
    if test_result.failure_info and test_result.failure_info.kernel_panic:
        # Send critical notification for kernel panic
        dispatcher.send_critical_failure_notification(
            title=f"Kernel Panic in {test_result.test_id}",
            message=test_result.failure_info.error_message,
            test_id=test_result.test_id,
            recipients=[
                NotificationRecipient(
                    name="Kernel Team",
                    email="kernel-team@example.com"
                )
            ],
            metadata={
                "environment": test_result.environment.id,
                "kernel_version": test_result.environment.kernel_version,
                "execution_time": test_result.execution_time
            }
        )
```

## Error Handling

- Channel configuration errors are logged and returned in results
- Network errors are caught and reported
- Missing recipients are handled gracefully
- Invalid configurations prevent sending

## Security

- SMTP credentials should be stored securely
- Webhook URLs should be kept confidential
- Email addresses are validated
- API tokens are never logged

## Requirements

- Python 3.10+
- requests (for Slack/Teams webhooks)
- pydantic (for data models)
- smtplib (built-in, for email)

## License

See LICENSE file in project root.
