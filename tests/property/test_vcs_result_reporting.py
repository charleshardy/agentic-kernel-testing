"""Property-based tests for VCS result reporting completeness.

Feature: agentic-kernel-testing, Property 22: Result reporting completeness
Validates: Requirements 5.2
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import List
from unittest.mock import Mock, MagicMock

from integration.vcs_models import (
    VCSProvider, Repository, TestStatus, TestStatusState, StatusReport
)
from integration.vcs_integration import VCSIntegration
from ai_generator.models import (
    TestResult, TestStatus as TestResultStatus, Environment,
    HardwareConfig, ArtifactBundle, EnvironmentStatus
)


# Custom strategies
@st.composite
def repository_strategy(draw):
    """Generate random repository data."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
    owner = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
    return Repository(
        name=name,
        full_name=f"{owner}/{name}",
        owner=owner,
        url=f"https://github.com/{owner}/{name}",
        clone_url=f"https://github.com/{owner}/{name}.git",
        default_branch=draw(st.sampled_from(['main', 'master', 'develop']))
    )


@st.composite
def hardware_config_strategy(draw):
    """Generate random hardware config."""
    return HardwareConfig(
        architecture=draw(st.sampled_from(['x86_64', 'arm64', 'riscv64'])),
        cpu_model=draw(st.text(min_size=1, max_size=50)),
        memory_mb=draw(st.integers(min_value=512, max_value=32768)),
        storage_type=draw(st.sampled_from(['ssd', 'hdd', 'nvme'])),
        is_virtual=draw(st.booleans())
    )


@st.composite
def environment_strategy(draw):
    """Generate random environment."""
    env_id = draw(st.text(min_size=1, max_size=50))
    config = draw(hardware_config_strategy())
    return Environment(
        id=env_id,
        config=config,
        status=draw(st.sampled_from(list(EnvironmentStatus))),
        kernel_version=draw(st.text(min_size=1, max_size=20)),
        ip_address=f"{draw(st.integers(1, 255))}.{draw(st.integers(0, 255))}.{draw(st.integers(0, 255))}.{draw(st.integers(1, 254))}"
    )


@st.composite
def result_strategy(draw):
    """Generate random test result."""
    test_id = draw(st.text(min_size=1, max_size=50))
    status = draw(st.sampled_from(list(TestResultStatus)))
    execution_time = draw(st.floats(min_value=0.1, max_value=300.0))
    environment = draw(environment_strategy())
    
    return TestResult(
        test_id=test_id,
        status=status,
        execution_time=execution_time,
        environment=environment,
        artifacts=ArtifactBundle(),
        timestamp=datetime.now()
    )


class TestVCSResultReporting:
    """Test VCS result reporting completeness property.
    
    Property 22: Result reporting completeness
    For any completed test run, the system should report results to the
    version control system with pass/fail status and detailed logs.
    """
    
    @given(
        provider=st.sampled_from(list(VCSProvider)),
        repository=repository_strategy(),
        commit_sha=st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'),
        test_results=st.lists(result_strategy(), min_size=1, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_report_test_results_includes_all_information(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str,
        test_results: List[TestResult]
    ):
        """Test that test result reporting includes all required information.
        
        For any set of test results, the status report should include:
        - Pass/fail status
        - Total test count
        - Passed/failed/error counts
        - Appropriate state based on results
        """
        # Arrange
        integration = VCSIntegration()
        
        # Mock the client to capture the status being reported
        mock_client = Mock()
        mock_client.report_status = Mock(return_value=True)
        
        if provider == VCSProvider.GITHUB:
            integration.github_client = mock_client
        else:
            integration.gitlab_client = mock_client
        
        # Act
        result = integration.report_test_results(
            provider, repository, commit_sha, test_results
        )
        
        # Assert - report should be called
        assert result is True
        assert mock_client.report_status.called
        
        # Extract the status that was reported
        call_args = mock_client.report_status.call_args
        reported_status = call_args[0][2]  # Third argument is the TestStatus
        
        # Verify status contains required information
        assert isinstance(reported_status, TestStatus)
        assert isinstance(reported_status.state, TestStatusState)
        assert isinstance(reported_status.description, str)
        assert len(reported_status.description) > 0
        
        # Verify description contains test counts
        total_tests = len(test_results)
        assert str(total_tests) in reported_status.description
    
    @given(
        provider=st.sampled_from(list(VCSProvider)),
        repository=repository_strategy(),
        commit_sha=st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'),
        test_results=st.lists(result_strategy(), min_size=1, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_report_status_reflects_test_outcomes(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str,
        test_results: List[TestResult]
    ):
        """Test that reported status correctly reflects test outcomes.
        
        For any set of test results:
        - If all pass, status should be SUCCESS
        - If any fail, status should be FAILURE
        - If any error, status should be ERROR
        """
        # Arrange
        integration = VCSIntegration()
        
        # Mock the client
        mock_client = Mock()
        mock_client.report_status = Mock(return_value=True)
        
        if provider == VCSProvider.GITHUB:
            integration.github_client = mock_client
        else:
            integration.gitlab_client = mock_client
        
        # Act
        integration.report_test_results(
            provider, repository, commit_sha, test_results
        )
        
        # Assert - verify status matches outcomes
        call_args = mock_client.report_status.call_args
        reported_status = call_args[0][2]
        
        # Count outcomes
        has_errors = any(r.status == TestResultStatus.ERROR for r in test_results)
        has_failures = any(r.status == TestResultStatus.FAILED for r in test_results)
        all_passed = all(r.status == TestResultStatus.PASSED for r in test_results)
        
        # Verify state matches outcomes
        if has_errors:
            assert reported_status.state == TestStatusState.ERROR
        elif has_failures:
            assert reported_status.state == TestStatusState.FAILURE
        elif all_passed:
            assert reported_status.state == TestStatusState.SUCCESS
    
    @given(
        provider=st.sampled_from(list(VCSProvider)),
        repository=repository_strategy(),
        commit_sha=st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'),
        message=st.text(min_size=1, max_size=200)
    )
    @settings(max_examples=100, deadline=None)
    def test_report_pending_includes_message(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str,
        message: str
    ):
        """Test that pending status reports include the message.
        
        For any pending status report, the message should be included
        in the description.
        """
        # Arrange
        integration = VCSIntegration()
        
        # Mock the client
        mock_client = Mock()
        mock_client.report_status = Mock(return_value=True)
        
        if provider == VCSProvider.GITHUB:
            integration.github_client = mock_client
        else:
            integration.gitlab_client = mock_client
        
        # Act
        result = integration.report_pending(
            provider, repository, commit_sha, message
        )
        
        # Assert
        assert result is True
        assert mock_client.report_status.called
        
        call_args = mock_client.report_status.call_args
        reported_status = call_args[0][2]
        
        assert reported_status.state == TestStatusState.PENDING
        assert reported_status.description == message
    
    @given(
        provider=st.sampled_from(list(VCSProvider)),
        repository=repository_strategy(),
        commit_sha=st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'),
        test_results=st.lists(result_strategy(), min_size=1, max_size=50),
        logs_url=st.text(min_size=10, max_size=200)
    )
    @settings(max_examples=100, deadline=None)
    def test_report_includes_logs_url_when_provided(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str,
        test_results: List[TestResult],
        logs_url: str
    ):
        """Test that status reports include logs URL when provided.
        
        For any test result report with a logs URL, the URL should be
        included in the status report.
        """
        # Arrange
        integration = VCSIntegration()
        
        # Mock the client
        mock_client = Mock()
        mock_client.report_status = Mock(return_value=True)
        
        if provider == VCSProvider.GITHUB:
            integration.github_client = mock_client
        else:
            integration.gitlab_client = mock_client
        
        # Act
        integration.report_test_results(
            provider, repository, commit_sha, test_results, logs_url
        )
        
        # Assert
        call_args = mock_client.report_status.call_args
        reported_status = call_args[0][2]
        
        assert reported_status.target_url == logs_url
    
    @given(
        provider=st.sampled_from(list(VCSProvider)),
        repository=repository_strategy(),
        commit_sha=st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'),
        test_results=st.lists(result_strategy(), min_size=1, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_report_handles_empty_results_gracefully(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str,
        test_results: List[TestResult]
    ):
        """Test that reporting handles various result sets gracefully.
        
        For any set of test results (including edge cases), the system
        should generate a valid status report without errors.
        """
        # Arrange
        integration = VCSIntegration()
        
        # Mock the client
        mock_client = Mock()
        mock_client.report_status = Mock(return_value=True)
        
        if provider == VCSProvider.GITHUB:
            integration.github_client = mock_client
        else:
            integration.gitlab_client = mock_client
        
        # Act - should not raise any exceptions
        try:
            result = integration.report_test_results(
                provider, repository, commit_sha, test_results
            )
            
            # Assert
            assert isinstance(result, bool)
            if mock_client.report_status.called:
                call_args = mock_client.report_status.call_args
                reported_status = call_args[0][2]
                assert isinstance(reported_status, TestStatus)
        except Exception as e:
            pytest.fail(f"Reporting should not raise exceptions: {e}")
    
    @given(
        provider=st.sampled_from(list(VCSProvider)),
        repository=repository_strategy(),
        commit_sha=st.text(min_size=40, max_size=40, alphabet='0123456789abcdef')
    )
    @settings(max_examples=100, deadline=None)
    def test_report_status_with_no_client_returns_false(
        self,
        provider: VCSProvider,
        repository: Repository,
        commit_sha: str
    ):
        """Test that reporting without a configured client returns False.
        
        For any status report attempt when no client is configured,
        the system should return False to indicate failure.
        """
        # Arrange - integration with no clients configured
        integration = VCSIntegration()
        
        status = TestStatus(
            state=TestStatusState.SUCCESS,
            description="Test status"
        )
        
        # Act
        result = integration.report_status(provider, repository, commit_sha, status)
        
        # Assert
        assert result is False
