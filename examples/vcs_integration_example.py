#!/usr/bin/env python3
"""Example demonstrating VCS integration functionality.

This example shows how to:
1. Set up VCS integration with GitHub/GitLab
2. Handle webhook events
3. Trigger tests automatically
4. Report test results back to VCS
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from integration import (
    VCSIntegration, VCSProvider, EventType, Repository,
    TestStatus, TestStatusState
)
from ai_generator.models import (
    TestResult, TestStatus as TestResultStatus, Environment,
    HardwareConfig, ArtifactBundle, EnvironmentStatus
)


def example_webhook_handling():
    """Example: Handle incoming webhook events."""
    print("=" * 60)
    print("Example 1: Webhook Event Handling")
    print("=" * 60)
    
    # Initialize VCS integration with tokens
    integration = VCSIntegration(
        webhook_secret="your-webhook-secret",
        github_token=os.getenv("GITHUB_TOKEN", "fake-token-for-demo"),
        gitlab_token=os.getenv("GITLAB_TOKEN", "fake-token-for-demo")
    )
    
    # Register event handlers
    def handle_push_event(event):
        print(f"\n✓ Push event received:")
        print(f"  Repository: {event.repository.full_name}")
        print(f"  Branch: {event.branch}")
        print(f"  Commits: {len(event.commits)}")
        
        # Check if we should trigger tests
        if integration.should_trigger_tests(event):
            commits_to_test = integration.get_commits_to_test(event)
            print(f"  → Triggering tests for {len(commits_to_test)} commits")
            for sha in commits_to_test:
                print(f"    - {sha[:8]}")
    
    def handle_pr_event(event):
        print(f"\n✓ Pull request event received:")
        print(f"  Repository: {event.repository.full_name}")
        if event.pull_request:
            print(f"  PR #{event.pull_request.number}: {event.pull_request.title}")
            print(f"  Action: {event.pull_request.action.value}")
            print(f"  Commits: {len(event.pull_request.commits)}")
    
    # Register handlers
    integration.register_event_handler(EventType.PUSH, handle_push_event)
    integration.register_event_handler(EventType.PULL_REQUEST, handle_pr_event)
    
    # Simulate GitHub push webhook
    github_push_payload = {
        'repository': {
            'name': 'linux-kernel',
            'full_name': 'torvalds/linux-kernel',
            'owner': {'login': 'torvalds'},
            'html_url': 'https://github.com/torvalds/linux-kernel',
            'clone_url': 'https://github.com/torvalds/linux-kernel.git',
            'default_branch': 'main'
        },
        'ref': 'refs/heads/main',
        'before': '0' * 40,
        'after': 'abc123def456' + '0' * 28,
        'commits': [
            {
                'id': 'abc123def456' + '0' * 28,
                'message': 'Fix memory leak in driver',
                'author': {
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'username': 'johndoe'
                },
                'timestamp': datetime.now().isoformat(),
                'url': 'https://github.com/torvalds/linux-kernel/commit/abc123',
                'added': ['drivers/new_driver.c'],
                'modified': ['drivers/old_driver.c'],
                'removed': []
            }
        ]
    }
    
    print("\nSimulating GitHub push webhook...")
    event = integration.handle_webhook(
        VCSProvider.GITHUB,
        'push',
        github_push_payload
    )
    
    print(f"\n✓ Event processed successfully")
    print(f"  Event ID: {event.event_id}")
    print(f"  Provider: {event.provider.value}")
    print(f"  Type: {event.event_type.value}")


def example_status_reporting():
    """Example: Report test results back to VCS."""
    print("\n" + "=" * 60)
    print("Example 2: Status Reporting")
    print("=" * 60)
    
    # Initialize integration (in real usage, use actual tokens)
    integration = VCSIntegration(
        github_token=os.getenv("GITHUB_TOKEN", "fake-token-for-demo")
    )
    
    # Create repository info
    repository = Repository(
        name='linux-kernel',
        full_name='torvalds/linux-kernel',
        owner='torvalds',
        url='https://github.com/torvalds/linux-kernel',
        clone_url='https://github.com/torvalds/linux-kernel.git',
        default_branch='main'
    )
    
    commit_sha = 'abc123def456' + '0' * 28
    
    # Report pending status
    print(f"\n1. Reporting pending status for commit {commit_sha[:8]}...")
    # In real usage: integration.report_pending(VCSProvider.GITHUB, repository, commit_sha)
    print("   ✓ Status: PENDING - Tests are running...")
    
    # Simulate test execution
    print("\n2. Running tests...")
    
    # Create mock test results
    hw_config = HardwareConfig(
        architecture='x86_64',
        cpu_model='Intel Xeon',
        memory_mb=8192,
        is_virtual=True
    )
    
    env = Environment(
        id='env-001',
        config=hw_config,
        status=EnvironmentStatus.IDLE,
        kernel_version='6.5.0'
    )
    
    test_results = [
        TestResult(
            test_id='test-001',
            status=TestResultStatus.PASSED,
            execution_time=1.5,
            environment=env,
            artifacts=ArtifactBundle()
        ),
        TestResult(
            test_id='test-002',
            status=TestResultStatus.PASSED,
            execution_time=2.3,
            environment=env,
            artifacts=ArtifactBundle()
        ),
        TestResult(
            test_id='test-003',
            status=TestResultStatus.FAILED,
            execution_time=0.8,
            environment=env,
            artifacts=ArtifactBundle()
        )
    ]
    
    print(f"   ✓ Executed {len(test_results)} tests")
    print(f"     - Passed: {sum(1 for r in test_results if r.status == TestResultStatus.PASSED)}")
    print(f"     - Failed: {sum(1 for r in test_results if r.status == TestResultStatus.FAILED)}")
    
    # Report final status
    print(f"\n3. Reporting final status...")
    # In real usage:
    # integration.report_test_results(
    #     VCSProvider.GITHUB,
    #     repository,
    #     commit_sha,
    #     test_results,
    #     logs_url='https://testing.example.com/logs/abc123'
    # )
    print("   ✓ Status: FAILURE - Tests failed: 2/3 passed, 1 failed")
    print("   ✓ Logs URL: https://testing.example.com/logs/abc123")


def example_pr_comment():
    """Example: Create comments on pull requests."""
    print("\n" + "=" * 60)
    print("Example 3: Pull Request Comments")
    print("=" * 60)
    
    integration = VCSIntegration(
        github_token=os.getenv("GITHUB_TOKEN", "fake-token-for-demo")
    )
    
    repository = Repository(
        name='linux-kernel',
        full_name='torvalds/linux-kernel',
        owner='torvalds',
        url='https://github.com/torvalds/linux-kernel',
        clone_url='https://github.com/torvalds/linux-kernel.git',
        default_branch='main'
    )
    
    pr_number = 12345
    
    # Create detailed test report comment
    comment = """
## 🤖 Agentic Testing Results

### Summary
- **Total Tests**: 15
- **Passed**: ✅ 12
- **Failed**: ❌ 3
- **Duration**: 5m 23s

### Failed Tests
1. `test_memory_allocation` - Memory leak detected in driver cleanup
2. `test_concurrent_access` - Race condition in lock handling
3. `test_error_recovery` - Improper error handling in edge case

### Recommendations
- Review memory management in `drivers/new_driver.c:145`
- Add proper locking around shared resource access
- Implement error recovery for NULL pointer cases

[View detailed logs](https://testing.example.com/logs/pr-12345)
"""
    
    print(f"\nCreating comment on PR #{pr_number}...")
    # In real usage:
    # integration.create_pr_comment(VCSProvider.GITHUB, repository, pr_number, comment)
    print("✓ Comment created successfully")
    print("\nComment preview:")
    print(comment)


def example_multi_provider():
    """Example: Working with multiple VCS providers."""
    print("\n" + "=" * 60)
    print("Example 4: Multi-Provider Support")
    print("=" * 60)
    
    # Initialize with both GitHub and GitLab
    integration = VCSIntegration(
        webhook_secret="shared-secret",
        github_token=os.getenv("GITHUB_TOKEN", "fake-github-token"),
        gitlab_token=os.getenv("GITLAB_TOKEN", "fake-gitlab-token")
    )
    
    print("\n✓ VCS integration initialized with:")
    print("  - GitHub support")
    print("  - GitLab support")
    
    # Handle events from different providers
    def universal_handler(event):
        print(f"\n✓ Event from {event.provider.value}:")
        print(f"  Repository: {event.repository.full_name}")
        print(f"  Type: {event.event_type.value}")
    
    # Register handler for all event types
    for event_type in EventType:
        integration.register_event_handler(event_type, universal_handler)
    
    print("\n✓ Universal event handler registered for all event types")
    print("  System ready to handle webhooks from GitHub and GitLab")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("VCS Integration Examples")
    print("=" * 60)
    
    try:
        example_webhook_handling()
        example_status_reporting()
        example_pr_comment()
        example_multi_provider()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
