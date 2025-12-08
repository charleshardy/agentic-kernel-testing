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
