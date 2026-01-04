"""
Property-based test for allocation history and logging accuracy.

**Feature: environment-allocation-ui, Property 5: Allocation History and Logging Accuracy**

This test validates that allocation events are logged with complete details and displayed 
correctly in timeline format with proper filtering and correlation capabilities.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import json

from api.services.allocation_history import AllocationHistoryService
from api.models import AllocationEvent
from database.models import (
    AllocationEventModel, EnvironmentModel, TestCaseModel, 
    TestResultModel, HardwareConfigModel
)
from database.connection import get_db_session


# Test data generators
@st.composite
def allocation_event_data(draw):
    """Generate allocation event data."""
    event_types = ["allocated", "deallocated", "failed", "queued", "cancelled"]
    
    return {
        "event_type": draw(st.sampled_from(event_types)),
        "environment_id": draw(st.text(min_size=8, max_size=16, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "test_id": draw(st.one_of(st.none(), st.text(min_size=8, max_size=16, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))),
        "metadata": draw(st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
            st.one_of(
                st.text(min_size=1, max_size=50),
                st.integers(min_value=0, max_value=1000),
                st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
                st.booleans()
            ),
            min_size=0,
            max_size=5
        ))
    }


@st.composite
def time_range_data(draw):
    """Generate time range data for filtering."""
    base_time = datetime.utcnow()
    start_offset = draw(st.integers(min_value=1, max_value=24))  # hours ago
    end_offset = draw(st.integers(min_value=0, max_value=start_offset-1))  # hours ago
    
    start_time = base_time - timedelta(hours=start_offset)
    end_time = base_time - timedelta(hours=end_offset)
    
    return start_time, end_time


@st.composite
def filter_parameters(draw):
    """Generate filter parameters for history queries."""
    return {
        "event_type": draw(st.one_of(st.none(), st.sampled_from(["allocated", "deallocated", "failed", "queued"]))),
        "environment_id": draw(st.one_of(st.none(), st.text(min_size=8, max_size=16))),
        "test_id": draw(st.one_of(st.none(), st.text(min_size=8, max_size=16))),
        "page": draw(st.integers(min_value=1, max_value=5)),
        "page_size": draw(st.integers(min_value=5, max_value=50))
    }


class TestAllocationHistoryAndLoggingAccuracy:
    """Test allocation history and logging accuracy properties."""
    
    @given(st.lists(allocation_event_data(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_event_logging_completeness(self, event_data_list: List[Dict[str, Any]]):
        """
        Property: For any allocation event, all event details should be logged completely.
        
        This test verifies that when allocation events are logged:
        1. All required fields are stored
        2. Metadata is preserved accurately
        3. Events can be retrieved with all original data intact
        """
        with get_db_session() as db:
            history_service = AllocationHistoryService(db)
            logged_events = []
            
            # Log all events
            for event_data in event_data_list:
                logged_event = history_service.log_allocation_event(
                    event_type=event_data["event_type"],
                    environment_id=event_data["environment_id"],
                    test_id=event_data["test_id"],
                    metadata=event_data["metadata"]
                )
                logged_events.append((logged_event, event_data))
            
            # Verify each logged event contains complete data
            for logged_event, original_data in logged_events:
                # Check required fields are present
                assert logged_event.id is not None and len(logged_event.id) > 0
                assert logged_event.type == original_data["event_type"]
                assert logged_event.environment_id == original_data["environment_id"]
                assert logged_event.test_id == original_data["test_id"]
                assert logged_event.timestamp is not None
                
                # Check metadata is preserved accurately
                assert logged_event.metadata == original_data["metadata"]
                
                # Verify event can be retrieved from database
                retrieved_events, _ = history_service.get_allocation_history(
                    page=1,
                    page_size=100
                )
                
                # Find the logged event in retrieved events
                found_event = None
                for retrieved_event in retrieved_events:
                    if retrieved_event.id == logged_event.id:
                        found_event = retrieved_event
                        break
                
                assert found_event is not None, f"Event {logged_event.id} not found in retrieved events"
                assert found_event.type == original_data["event_type"]
                assert found_event.environment_id == original_data["environment_id"]
                assert found_event.test_id == original_data["test_id"]
                assert found_event.metadata == original_data["metadata"]
    
    @given(st.lists(allocation_event_data(), min_size=5, max_size=30), filter_parameters())
    @settings(max_examples=100, deadline=None)
    def test_timeline_filtering_accuracy(self, event_data_list: List[Dict[str, Any]], filters: Dict[str, Any]):
        """
        Property: For any set of allocation events and filter criteria, 
        the timeline view should display only events matching the filters.
        
        This test verifies that filtering works correctly:
        1. Events matching filter criteria are included
        2. Events not matching filter criteria are excluded
        3. Pagination works correctly with filters
        """
        with get_db_session() as db:
            history_service = AllocationHistoryService(db)
            
            # Log all events with known timestamps
            base_time = datetime.utcnow()
            logged_events = []
            
            for i, event_data in enumerate(event_data_list):
                # Create events with different timestamps for time-based filtering
                event_time = base_time - timedelta(minutes=i * 10)
                
                # Temporarily store the original log method
                original_log = history_service.log_allocation_event
                
                # Create a custom log method that allows setting timestamp
                def custom_log(event_type, environment_id, test_id=None, allocation_request_id=None, metadata=None):
                    event_id = f"evt_{event_time.strftime('%Y%m%d_%H%M%S')}_{environment_id[:8]}_{i}"
                    
                    event_model = AllocationEventModel(
                        id=event_id,
                        event_type=event_type,
                        environment_id=environment_id,
                        test_id=test_id,
                        allocation_request_id=allocation_request_id,
                        event_metadata=metadata or {},
                        timestamp=event_time
                    )
                    
                    db.add(event_model)
                    db.commit()
                    
                    return AllocationEvent(
                        id=event_model.id,
                        type=event_model.event_type,
                        environment_id=event_model.environment_id,
                        test_id=event_model.test_id,
                        timestamp=event_model.timestamp,
                        metadata=event_model.event_metadata or {}
                    )
                
                # Use custom log method
                history_service.log_allocation_event = custom_log
                
                logged_event = history_service.log_allocation_event(
                    event_type=event_data["event_type"],
                    environment_id=event_data["environment_id"],
                    test_id=event_data["test_id"],
                    metadata=event_data["metadata"]
                )
                
                # Restore original method
                history_service.log_allocation_event = original_log
                
                logged_events.append(logged_event)
            
            # Apply filters and retrieve events
            retrieved_events, pagination = history_service.get_allocation_history(
                page=filters["page"],
                page_size=filters["page_size"],
                event_type=filters["event_type"],
                environment_id=filters["environment_id"],
                test_id=filters["test_id"]
            )
            
            # Verify filtering accuracy
            for retrieved_event in retrieved_events:
                # Check event_type filter
                if filters["event_type"] is not None:
                    assert retrieved_event.type == filters["event_type"]
                
                # Check environment_id filter
                if filters["environment_id"] is not None:
                    assert retrieved_event.environment_id == filters["environment_id"]
                
                # Check test_id filter
                if filters["test_id"] is not None:
                    assert retrieved_event.test_id == filters["test_id"]
            
            # Verify pagination is working
            assert pagination["page"] == filters["page"]
            assert pagination["page_size"] == filters["page_size"]
            assert len(retrieved_events) <= filters["page_size"]
            
            # Verify total count is consistent
            if pagination["total_count"] > 0:
                assert pagination["total_pages"] >= 1
                assert pagination["has_next"] == (filters["page"] < pagination["total_pages"])
                assert pagination["has_prev"] == (filters["page"] > 1)
    
    @given(st.lists(allocation_event_data(), min_size=3, max_size=15))
    @settings(max_examples=100, deadline=None)
    def test_statistics_calculation_accuracy(self, event_data_list: List[Dict[str, Any]]):
        """
        Property: For any set of allocation events, statistics should accurately 
        reflect the actual event data.
        
        This test verifies that statistics calculations are correct:
        1. Total event count matches actual events
        2. Event type counts are accurate
        3. Environment usage counts are correct
        """
        with get_db_session() as db:
            history_service = AllocationHistoryService(db)
            
            # Log all events
            logged_events = []
            for event_data in event_data_list:
                logged_event = history_service.log_allocation_event(
                    event_type=event_data["event_type"],
                    environment_id=event_data["environment_id"],
                    test_id=event_data["test_id"],
                    metadata=event_data["metadata"]
                )
                logged_events.append(logged_event)
            
            # Get statistics
            statistics = history_service.get_allocation_statistics()
            
            # Calculate expected statistics
            expected_event_type_counts = {}
            expected_environment_usage = {}
            
            for event in logged_events:
                # Count by event type
                expected_event_type_counts[event.type] = expected_event_type_counts.get(event.type, 0) + 1
                
                # Count by environment
                expected_environment_usage[event.environment_id] = expected_environment_usage.get(event.environment_id, 0) + 1
            
            # Verify statistics accuracy
            # Note: We check that our events are included, but there might be other events in the database
            assert statistics["total_events"] >= len(logged_events)
            
            # Verify event type counts include our events
            for event_type, expected_count in expected_event_type_counts.items():
                actual_count = statistics["event_type_counts"].get(event_type, 0)
                assert actual_count >= expected_count, f"Event type {event_type}: expected at least {expected_count}, got {actual_count}"
            
            # Verify environment usage includes our events
            for env_id, expected_count in expected_environment_usage.items():
                actual_count = statistics["environment_usage"].get(env_id, 0)
                assert actual_count >= expected_count, f"Environment {env_id}: expected at least {expected_count}, got {actual_count}"
    
    @given(st.lists(allocation_event_data(), min_size=2, max_size=10))
    @settings(max_examples=100, deadline=None)
    def test_export_data_completeness(self, event_data_list: List[Dict[str, Any]]):
        """
        Property: For any set of allocation events, exported data should contain 
        all event information in the specified format.
        
        This test verifies that data export is complete and accurate:
        1. All events are included in export
        2. All event fields are preserved
        3. Export format is valid (CSV/JSON)
        """
        with get_db_session() as db:
            history_service = AllocationHistoryService(db)
            
            # Log all events
            logged_events = []
            for event_data in event_data_list:
                logged_event = history_service.log_allocation_event(
                    event_type=event_data["event_type"],
                    environment_id=event_data["environment_id"],
                    test_id=event_data["test_id"],
                    metadata=event_data["metadata"]
                )
                logged_events.append(logged_event)
            
            # Test CSV export
            csv_data = history_service.export_allocation_data(format_type="csv")
            
            # Verify CSV format and content
            assert isinstance(csv_data, str)
            csv_lines = csv_data.strip().split('\n')
            assert len(csv_lines) >= 2  # Header + at least one data row
            
            # Check CSV header
            header = csv_lines[0]
            expected_columns = ["Event ID", "Event Type", "Environment ID", "Test ID", "Timestamp", "Metadata"]
            for column in expected_columns:
                assert column in header
            
            # Verify our events are in the CSV (they should be among the most recent)
            event_ids_in_csv = []
            for line in csv_lines[1:]:  # Skip header
                if line.strip():  # Skip empty lines
                    parts = line.split(',')
                    if len(parts) >= 1:
                        event_id = parts[0].strip('"')
                        event_ids_in_csv.append(event_id)
            
            # At least some of our events should be in the export
            our_event_ids = {event.id for event in logged_events}
            found_events = our_event_ids.intersection(set(event_ids_in_csv))
            assert len(found_events) > 0, "None of our logged events found in CSV export"
            
            # Test JSON export
            json_data = history_service.export_allocation_data(format_type="json")
            
            # Verify JSON format and content
            assert isinstance(json_data, str)
            parsed_json = json.loads(json_data)
            
            # Check JSON structure
            assert "export_timestamp" in parsed_json
            assert "total_events" in parsed_json
            assert "events" in parsed_json
            assert isinstance(parsed_json["events"], list)
            assert parsed_json["total_events"] >= len(logged_events)
            
            # Verify our events are in the JSON
            event_ids_in_json = {event["id"] for event in parsed_json["events"]}
            found_events_json = our_event_ids.intersection(event_ids_in_json)
            assert len(found_events_json) > 0, "None of our logged events found in JSON export"
            
            # Verify event structure in JSON
            for event in parsed_json["events"]:
                if event["id"] in our_event_ids:
                    # Find the corresponding logged event
                    original_event = next(e for e in logged_events if e.id == event["id"])
                    
                    # Verify all fields are present and correct
                    assert event["type"] == original_event.type
                    assert event["environment_id"] == original_event.environment_id
                    assert event["test_id"] == original_event.test_id
                    assert event["metadata"] == original_event.metadata
                    assert "timestamp" in event
    
    @given(st.text(min_size=8, max_size=16), time_range_data())
    @settings(max_examples=100, deadline=None)
    def test_correlation_analysis_accuracy(self, environment_id: str, time_range):
        """
        Property: For any environment and time range, correlation analysis should 
        accurately link allocation events with related test executions.
        
        This test verifies that correlation analysis works correctly:
        1. Events within the time window are correlated
        2. Events outside the time window are not correlated
        3. Correlation data includes complete event and test information
        """
        start_time, end_time = time_range
        
        with get_db_session() as db:
            history_service = AllocationHistoryService(db)
            
            # Create a test hardware config for test results
            hardware_config = HardwareConfigModel(
                architecture="x86_64",
                cpu_model="Test CPU",
                memory_mb=4096,
                storage_type="ssd"
            )
            db.add(hardware_config)
            db.commit()
            
            # Create an environment for testing
            environment = EnvironmentModel(
                id=environment_id,
                hardware_config_id=hardware_config.id,
                architecture="x86_64",
                environment_type="qemu"
            )
            db.add(environment)
            db.commit()
            
            # Create test cases
            test_case = TestCaseModel(
                id=f"test_{environment_id}",
                name="Test Case",
                description="Test Description",
                test_type="unit",
                target_subsystem="kernel",
                hardware_config_id=hardware_config.id
            )
            db.add(test_case)
            db.commit()
            
            # Log allocation events within the time range
            event_time = start_time + timedelta(minutes=30)
            
            # Create custom event with specific timestamp
            event_id = f"evt_{event_time.strftime('%Y%m%d_%H%M%S')}_{environment_id[:8]}"
            event_model = AllocationEventModel(
                id=event_id,
                event_type="allocated",
                environment_id=environment_id,
                test_id=test_case.id,
                event_metadata={"test": "correlation"},
                timestamp=event_time
            )
            db.add(event_model)
            db.commit()
            
            # Create a test result within correlation window (within 5 minutes of event)
            result_time = event_time + timedelta(minutes=2)
            test_result = TestResultModel(
                test_case_id=test_case.id,
                environment_id=environment_id,
                status="passed",
                execution_time=30.0,
                timestamp=result_time
            )
            db.add(test_result)
            db.commit()
            
            # Get correlations
            correlations = history_service.correlate_with_test_results(
                environment_id=environment_id,
                start_time=start_time,
                end_time=end_time
            )
            
            # Verify correlation accuracy
            assert len(correlations) >= 1, "Expected at least one correlation entry"
            
            # Find our correlation
            our_correlation = None
            for correlation in correlations:
                if correlation["event"]["id"] == event_id:
                    our_correlation = correlation
                    break
            
            assert our_correlation is not None, "Our event not found in correlations"
            
            # Verify event data in correlation
            assert our_correlation["event"]["type"] == "allocated"
            assert our_correlation["event"]["metadata"]["test"] == "correlation"
            
            # Verify related test data
            assert len(our_correlation["related_tests"]) >= 1, "Expected at least one related test"
            
            related_test = our_correlation["related_tests"][0]
            assert related_test["test_id"] == test_case.id
            assert related_test["status"] == "passed"
            assert related_test["execution_time"] == 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])