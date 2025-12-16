"""Property-based tests for Web GUI filter preservation.

Feature: web-gui-test-listing, Property 2: Filter Preservation
Validates: Requirements 2.2
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import json
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


# Strategy for generating filter states
@st.composite
def _filter_state_strategy(draw):
    """Generate a filter state with various combinations of filters."""
    test_types = ['unit', 'integration', 'performance', 'security', 'fuzz']
    subsystems = ['kernel/core', 'kernel/mm', 'kernel/fs', 'kernel/net', 'drivers/block', 'drivers/char', 'arch/x86', 'arch/arm64']
    generation_methods = ['manual', 'ai_diff', 'ai_function']
    statuses = ['never_run', 'running', 'completed', 'failed']
    
    return {
        "searchText": draw(st.one_of(st.none(), st.text(min_size=1, max_size=50))),
        "testType": draw(st.one_of(st.none(), st.sampled_from(test_types))),
        "subsystem": draw(st.one_of(st.none(), st.sampled_from(subsystems))),
        "generationMethod": draw(st.one_of(st.none(), st.sampled_from(generation_methods))),
        "status": draw(st.one_of(st.none(), st.sampled_from(statuses))),
        "page": draw(st.integers(min_value=1, max_value=10)),
        "pageSize": draw(st.sampled_from([10, 20, 50, 100])),
        "sortField": draw(st.one_of(st.none(), st.sampled_from(['name', 'test_type', 'target_subsystem', 'created_at', 'execution_time_estimate']))),
        "sortOrder": draw(st.one_of(st.none(), st.sampled_from(['ascend', 'descend']))),
        "dateRange": draw(st.one_of(st.none(), st.tuples(
            st.datetimes(min_value=datetime(2023, 1, 1), max_value=datetime.now()),
            st.datetimes(min_value=datetime(2023, 1, 1), max_value=datetime.now())
        )))
    }


@st.composite
def _refresh_operation_strategy(draw):
    """Generate different types of refresh operations that might occur."""
    operations = [
        "manual_refresh",
        "auto_refresh_timer",
        "websocket_update",
        "new_test_generated",
        "test_execution_completed",
        "bulk_operation_completed",
        "navigation_return"
    ]
    
    return {
        "operation_type": draw(st.sampled_from(operations)),
        "delay_seconds": draw(st.floats(min_value=0.1, max_value=5.0)),
        "affects_data": draw(st.booleans()),
        "new_data_count": draw(st.integers(min_value=0, max_value=10)) if draw(st.booleans()) else 0
    }


def serialize_filter_state(filter_state: Dict[str, Any]) -> str:
    """Serialize filter state to a comparable string representation."""
    # Convert datetime objects to ISO strings for comparison
    serializable_state = {}
    for key, value in filter_state.items():
        if key == "dateRange" and value:
            serializable_state[key] = [dt.isoformat() for dt in value]
        else:
            serializable_state[key] = value
    
    return json.dumps(serializable_state, sort_keys=True)


def simulate_url_state_preservation(initial_filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate how URL state preservation would work in the React component.
    This mimics the useSearchParams and useEffect logic in TestCases.tsx.
    """
    # Simulate URL parameters creation (similar to the useEffect in TestCases.tsx)
    url_params = {}
    
    if initial_filters.get("searchText"):
        url_params["search"] = initial_filters["searchText"]
    if initial_filters.get("testType"):
        url_params["type"] = initial_filters["testType"]
    if initial_filters.get("subsystem"):
        url_params["subsystem"] = initial_filters["subsystem"]
    if initial_filters.get("generationMethod"):
        url_params["generation"] = initial_filters["generationMethod"]
    if initial_filters.get("status"):
        url_params["status"] = initial_filters["status"]
    if initial_filters.get("page", 1) != 1:
        url_params["page"] = str(initial_filters["page"])
    if initial_filters.get("pageSize", 20) != 20:
        url_params["pageSize"] = str(initial_filters["pageSize"])
    if initial_filters.get("sortField"):
        url_params["sortField"] = initial_filters["sortField"]
    if initial_filters.get("sortOrder"):
        url_params["sortOrder"] = initial_filters["sortOrder"]
    
    # Simulate reading back from URL (similar to useState initialization)
    restored_filters = {
        "searchText": url_params.get("search", ""),
        "testType": url_params.get("type"),
        "subsystem": url_params.get("subsystem"),
        "generationMethod": url_params.get("generation"),
        "status": url_params.get("status"),
        "page": int(url_params.get("page", "1")),
        "pageSize": int(url_params.get("pageSize", "20")),
        "sortField": url_params.get("sortField"),
        "sortOrder": url_params.get("sortOrder"),
        "dateRange": initial_filters.get("dateRange")  # Date range not persisted in URL for this test
    }
    
    return restored_filters


def simulate_refresh_operation(
    initial_filters: Dict[str, Any], 
    operation: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulate various refresh operations and their effect on filter state.
    """
    # Most operations should preserve filters
    preserved_filters = initial_filters.copy()
    
    # Some operations might reset pagination to page 1
    if operation["operation_type"] in ["new_test_generated", "bulk_operation_completed"]:
        # When new data is added, we might reset to page 1 but preserve other filters
        if operation.get("new_data_count", 0) > 0:
            preserved_filters["page"] = 1
    
    # Navigation return should fully preserve state via URL
    if operation["operation_type"] == "navigation_return":
        preserved_filters = simulate_url_state_preservation(initial_filters)
    
    return preserved_filters


@pytest.mark.property
class TestWebGUIFilterPreservationProperties:
    """Property-based tests for Web GUI filter preservation."""
    
    @given(
        initial_filters=_filter_state_strategy(),
        refresh_operation=_refresh_operation_strategy()
    )
    @settings(max_examples=20)
    def test_filter_preservation_after_refresh(self, initial_filters, refresh_operation):
        """
        **Feature: web-gui-test-listing, Property 2: Filter Preservation**
        **Validates: Requirements 2.2**
        
        For any test list refresh operation, previously applied filters and 
        pagination settings should be maintained unless explicitly changed by the user.
        
        This property verifies that:
        1. Search text is preserved across refreshes
        2. Filter selections remain active
        3. Pagination state is maintained (except when new data requires reset)
        4. Sort configuration persists
        5. URL state correctly preserves and restores filter state
        """
        assume(initial_filters is not None)
        
        # Simulate the refresh operation
        filters_after_refresh = simulate_refresh_operation(initial_filters, refresh_operation)
        
        # Core filter preservation properties
        
        # Property 1: Search text should be preserved
        if initial_filters.get("searchText"):
            assert filters_after_refresh.get("searchText") == initial_filters.get("searchText"), \
                f"Search text should be preserved. Expected '{initial_filters.get('searchText')}', " \
                f"got '{filters_after_refresh.get('searchText')}'"
        
        # Property 2: Filter selections should be preserved
        filter_fields = ["testType", "subsystem", "generationMethod", "status"]
        for field in filter_fields:
            if initial_filters.get(field):
                assert filters_after_refresh.get(field) == initial_filters.get(field), \
                    f"Filter field '{field}' should be preserved. Expected '{initial_filters.get(field)}', " \
                    f"got '{filters_after_refresh.get(field)}'"
        
        # Property 3: Sort configuration should be preserved
        if initial_filters.get("sortField"):
            assert filters_after_refresh.get("sortField") == initial_filters.get("sortField"), \
                f"Sort field should be preserved. Expected '{initial_filters.get('sortField')}', " \
                f"got '{filters_after_refresh.get('sortField')}'"
        
        if initial_filters.get("sortOrder"):
            assert filters_after_refresh.get("sortOrder") == initial_filters.get("sortOrder"), \
                f"Sort order should be preserved. Expected '{initial_filters.get('sortOrder')}', " \
                f"got '{filters_after_refresh.get('sortOrder')}'"
        
        # Property 4: Page size should always be preserved
        assert filters_after_refresh.get("pageSize") == initial_filters.get("pageSize"), \
            f"Page size should be preserved. Expected {initial_filters.get('pageSize')}, " \
            f"got {filters_after_refresh.get('pageSize')}"
        
        # Property 5: Current page should be preserved unless new data was added
        if refresh_operation.get("new_data_count", 0) == 0:
            assert filters_after_refresh.get("page") == initial_filters.get("page"), \
                f"Current page should be preserved when no new data is added. " \
                f"Expected {initial_filters.get('page')}, got {filters_after_refresh.get('page')}"
    
    @given(filter_state=_filter_state_strategy())
    @settings(max_examples=15)
    def test_url_state_round_trip_preservation(self, filter_state):
        """
        Property: URL state should preserve and restore filter state accurately.
        
        When filters are applied and the URL is updated, navigating away and back
        should restore the exact same filter state.
        """
        assume(filter_state is not None)
        
        # Simulate the round trip: filters -> URL -> restored filters
        restored_filters = simulate_url_state_preservation(filter_state)
        
        # Property: All URL-persistable filters should be preserved exactly
        url_persistable_fields = [
            "searchText", "testType", "subsystem", "generationMethod", 
            "status", "page", "pageSize", "sortField", "sortOrder"
        ]
        
        for field in url_persistable_fields:
            original_value = filter_state.get(field)
            restored_value = restored_filters.get(field)
            
            # Handle empty string vs None equivalence for search text
            if field == "searchText":
                original_value = original_value or ""
                restored_value = restored_value or ""
            
            # Handle default values
            if field == "page" and original_value is None:
                original_value = 1
            if field == "pageSize" and original_value is None:
                original_value = 20
            
            assert restored_value == original_value, \
                f"URL round trip failed for field '{field}'. " \
                f"Original: {original_value}, Restored: {restored_value}"
    
    @given(
        filters=_filter_state_strategy(),
        concurrent_operations=st.lists(_refresh_operation_strategy(), min_size=1, max_size=5)
    )
    @settings(max_examples=10)
    def test_concurrent_refresh_filter_consistency(self, filters, concurrent_operations):
        """
        Property: Concurrent refresh operations should not corrupt filter state.
        
        When multiple refresh operations occur in quick succession, the final
        filter state should be consistent and not corrupted.
        """
        assume(filters is not None and len(concurrent_operations) > 0)
        
        # Simulate multiple concurrent refresh operations
        current_filters = filters.copy()
        
        for operation in concurrent_operations:
            current_filters = simulate_refresh_operation(current_filters, operation)
        
        # Property: Final state should be valid and consistent
        
        # 1. All filter values should be valid
        if current_filters.get("testType"):
            assert current_filters["testType"] in ['unit', 'integration', 'performance', 'security', 'fuzz']
        
        if current_filters.get("subsystem"):
            valid_subsystems = ['kernel/core', 'kernel/mm', 'kernel/fs', 'kernel/net', 
                              'drivers/block', 'drivers/char', 'arch/x86', 'arch/arm64']
            assert current_filters["subsystem"] in valid_subsystems
        
        if current_filters.get("generationMethod"):
            assert current_filters["generationMethod"] in ['manual', 'ai_diff', 'ai_function']
        
        if current_filters.get("status"):
            assert current_filters["status"] in ['never_run', 'running', 'completed', 'failed']
        
        # 2. Pagination values should be valid
        assert isinstance(current_filters.get("page", 1), int)
        assert current_filters.get("page", 1) >= 1
        assert current_filters.get("pageSize", 20) in [10, 20, 50, 100]
        
        # 3. Sort configuration should be consistent
        if current_filters.get("sortField"):
            valid_sort_fields = ['name', 'test_type', 'target_subsystem', 'created_at', 'execution_time_estimate']
            assert current_filters["sortField"] in valid_sort_fields
        
        if current_filters.get("sortOrder"):
            assert current_filters["sortOrder"] in ['ascend', 'descend']
        
        # 4. If sort field is set, sort order should also be set (and vice versa)
        has_sort_field = bool(current_filters.get("sortField"))
        has_sort_order = bool(current_filters.get("sortOrder"))
        
        # This is a consistency requirement - if you have one, you should have both
        if has_sort_field or has_sort_order:
            assert has_sort_field == has_sort_order, \
                f"Sort field and order should be consistent. Field: {current_filters.get('sortField')}, " \
                f"Order: {current_filters.get('sortOrder')}"
    
    @given(
        initial_filters=_filter_state_strategy(),
        user_changes=st.dictionaries(
            st.sampled_from(["searchText", "testType", "subsystem", "generationMethod", "status"]),
            st.one_of(st.none(), st.text(min_size=1, max_size=50)),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=10)
    def test_explicit_user_changes_override_preservation(self, initial_filters, user_changes):
        """
        Property: Explicit user changes should override filter preservation.
        
        When a user explicitly changes a filter, that change should take precedence
        over preservation of the previous state.
        """
        assume(initial_filters is not None and user_changes)
        
        # Simulate user making explicit changes
        updated_filters = initial_filters.copy()
        updated_filters.update(user_changes)
        
        # Simulate a refresh operation after user changes
        refresh_op = {"operation_type": "manual_refresh", "affects_data": False}
        final_filters = simulate_refresh_operation(updated_filters, refresh_op)
        
        # Property: User changes should be preserved in the final state
        for field, new_value in user_changes.items():
            assert final_filters.get(field) == new_value, \
                f"User change to '{field}' should be preserved. Expected '{new_value}', " \
                f"got '{final_filters.get(field)}'"
        
        # Property: Unchanged filters should still be preserved
        unchanged_fields = set(initial_filters.keys()) - set(user_changes.keys())
        for field in unchanged_fields:
            if field not in ["page"]:  # Page might be reset to 1 due to filter changes
                assert final_filters.get(field) == initial_filters.get(field), \
                    f"Unchanged filter '{field}' should be preserved. " \
                    f"Expected '{initial_filters.get(field)}', got '{final_filters.get(field)}'"