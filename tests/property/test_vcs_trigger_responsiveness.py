"""Property-based tests for VCS trigger responsiveness.

Feature: agentic-kernel-testing, Property 21: VCS trigger responsiveness
Validates: Requirements 5.1
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from typing import List

from integration.vcs_models import (
    VCSEvent, VCSProvider, EventType, Repository, Author,
    CommitInfo, PullRequest, PRAction
)
from integration.vcs_integration import VCSIntegration


# Custom strategies for generating test data
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
def author_strategy(draw):
    """Generate random author data."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' ')))
    username = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')))
    return Author(
        name=name,
        email=f"{username}@example.com",
        username=username
    )


@st.composite
def commit_info_strategy(draw):
    """Generate random commit info."""
    sha = draw(st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'))
    message = draw(st.text(min_size=1, max_size=200))
    author = draw(author_strategy())
    timestamp = datetime.now() - timedelta(minutes=draw(st.integers(min_value=0, max_value=1440)))
    
    return CommitInfo(
        sha=sha,
        message=message,
        author=author,
        timestamp=timestamp,
        url=f"https://github.com/repo/commit/{sha}",
        added_files=draw(st.lists(st.text(min_size=1, max_size=50), max_size=5)),
        modified_files=draw(st.lists(st.text(min_size=1, max_size=50), max_size=5)),
        removed_files=draw(st.lists(st.text(min_size=1, max_size=50), max_size=5))
    )


@st.composite
def pull_request_strategy(draw):
    """Generate random pull request data."""
    number = draw(st.integers(min_value=1, max_value=10000))
    title = draw(st.text(min_size=1, max_size=100))
    author = draw(author_strategy())
    
    return PullRequest(
        number=number,
        title=title,
        description=draw(st.text(max_size=500)),
        author=author,
        source_branch=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_/'))),
        target_branch=draw(st.sampled_from(['main', 'master', 'develop'])),
        url=f"https://github.com/repo/pull/{number}",
        action=draw(st.sampled_from(list(PRAction))),
        commits=draw(st.lists(commit_info_strategy(), min_size=1, max_size=5)),
        is_merged=draw(st.booleans())
    )


@st.composite
def vcs_event_strategy(draw):
    """Generate random VCS event."""
    event_id = draw(st.text(min_size=1, max_size=50))
    provider = draw(st.sampled_from(list(VCSProvider)))
    event_type = draw(st.sampled_from(list(EventType)))
    repository = draw(repository_strategy())
    timestamp = datetime.now()
    
    # Generate commits for push events
    commits = []
    if event_type in [EventType.PUSH, EventType.COMMIT]:
        commits = draw(st.lists(commit_info_strategy(), min_size=1, max_size=10))
    
    # Generate pull request for PR events
    pull_request = None
    if event_type == EventType.PULL_REQUEST:
        pull_request = draw(pull_request_strategy())
    
    return VCSEvent(
        event_id=event_id,
        provider=provider,
        event_type=event_type,
        repository=repository,
        timestamp=timestamp,
        commits=commits,
        pull_request=pull_request,
        branch=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_/'))),
        ref=draw(st.text(min_size=1, max_size=100)),
        before_sha=draw(st.text(min_size=40, max_size=40, alphabet='0123456789abcdef')),
        after_sha=draw(st.text(min_size=40, max_size=40, alphabet='0123456789abcdef'))
    )


class TestVCSTriggerResponsiveness:
    """Test VCS trigger responsiveness property.
    
    Property 21: VCS trigger responsiveness
    For any version control event (pull request, commit, or branch update),
    the system should trigger a test run automatically.
    """
    
    @given(event=vcs_event_strategy())
    @settings(max_examples=100, deadline=None)
    def test_vcs_events_trigger_handlers(self, event: VCSEvent):
        """Test that VCS events trigger registered handlers.
        
        For any VCS event, when a handler is registered for that event type,
        the handler should be called when the event is processed.
        """
        # Arrange
        integration = VCSIntegration()
        handler_called = []
        
        def test_handler(e: VCSEvent):
            handler_called.append(e)
        
        # Register handler for this event type
        integration.register_event_handler(event.event_type, test_handler)
        
        # Act
        integration._trigger_handlers(event)
        
        # Assert - handler should have been called
        assert len(handler_called) == 1
        assert handler_called[0] == event
    
    @given(events=st.lists(vcs_event_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_multiple_events_trigger_handlers(self, events: List[VCSEvent]):
        """Test that multiple VCS events all trigger handlers.
        
        For any list of VCS events, each event should trigger its
        corresponding handler when processed.
        """
        # Arrange
        integration = VCSIntegration()
        events_received = []
        
        def test_handler(e: VCSEvent):
            events_received.append(e)
        
        # Register handler for all event types
        for event_type in EventType:
            integration.register_event_handler(event_type, test_handler)
        
        # Act
        for event in events:
            integration._trigger_handlers(event)
        
        # Assert - all events should have triggered handlers
        assert len(events_received) == len(events)
        for original, received in zip(events, events_received):
            assert received == original
    
    @given(event=vcs_event_strategy())
    @settings(max_examples=100, deadline=None)
    def test_should_trigger_tests_for_relevant_events(self, event: VCSEvent):
        """Test that should_trigger_tests correctly identifies triggerable events.
        
        For any VCS event, the system should correctly determine whether
        tests should be triggered based on the event type.
        """
        # Arrange
        integration = VCSIntegration()
        
        # Act
        should_trigger = integration.should_trigger_tests(event)
        
        # Assert - verify logic matches requirements
        if event.event_type in [EventType.PUSH, EventType.PULL_REQUEST]:
            assert should_trigger is True
        elif event.event_type == EventType.BRANCH_UPDATE:
            # Branch deletions should not trigger tests
            if event.after_sha == '0' * 40:
                assert should_trigger is False
            else:
                assert should_trigger is True
        else:
            # Other events may or may not trigger
            assert isinstance(should_trigger, bool)
    
    @given(event=vcs_event_strategy())
    @settings(max_examples=100, deadline=None)
    def test_get_commits_to_test_returns_valid_shas(self, event: VCSEvent):
        """Test that get_commits_to_test returns valid commit SHAs.
        
        For any VCS event, the system should extract all relevant commit
        SHAs that need to be tested, without duplicates.
        """
        # Arrange
        integration = VCSIntegration()
        
        # Act
        commit_shas = integration.get_commits_to_test(event)
        
        # Assert - all returned SHAs should be valid
        assert isinstance(commit_shas, list)
        
        # No duplicates
        assert len(commit_shas) == len(set(commit_shas))
        
        # No null commit SHAs
        assert '0' * 40 not in commit_shas
        
        # All SHAs should be 40-character hex strings
        for sha in commit_shas:
            assert isinstance(sha, str)
            assert len(sha) == 40
            assert all(c in '0123456789abcdef' for c in sha)
    
    @given(event=vcs_event_strategy())
    @settings(max_examples=100, deadline=None)
    def test_multiple_handlers_all_called(self, event: VCSEvent):
        """Test that multiple handlers for the same event type are all called.
        
        For any VCS event, when multiple handlers are registered for that
        event type, all handlers should be called.
        """
        # Arrange
        integration = VCSIntegration()
        handler1_called = []
        handler2_called = []
        handler3_called = []
        
        def handler1(e: VCSEvent):
            handler1_called.append(e)
        
        def handler2(e: VCSEvent):
            handler2_called.append(e)
        
        def handler3(e: VCSEvent):
            handler3_called.append(e)
        
        # Register multiple handlers
        integration.register_event_handler(event.event_type, handler1)
        integration.register_event_handler(event.event_type, handler2)
        integration.register_event_handler(event.event_type, handler3)
        
        # Act
        integration._trigger_handlers(event)
        
        # Assert - all handlers should have been called
        assert len(handler1_called) == 1
        assert len(handler2_called) == 1
        assert len(handler3_called) == 1
        assert handler1_called[0] == event
        assert handler2_called[0] == event
        assert handler3_called[0] == event
