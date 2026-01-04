"""
Allocation History Service

This service handles allocation event logging, storage, and retrieval
for the Environment Allocation UI.
"""

import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from database.models import (
    AllocationEventModel, EnvironmentModel, TestCaseModel, 
    AllocationRequestModel, TestResultModel
)
from api.models import AllocationEvent


class AllocationHistoryService:
    """Service for managing allocation history and logging."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def log_allocation_event(
        self,
        event_type: str,
        environment_id: str,
        test_id: Optional[str] = None,
        allocation_request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AllocationEvent:
        """
        Log an allocation event to the database.
        
        Args:
            event_type: Type of event (allocated, deallocated, failed, queued)
            environment_id: ID of the environment
            test_id: Optional test ID
            allocation_request_id: Optional allocation request ID
            metadata: Optional event metadata
            
        Returns:
            AllocationEvent: The logged event
        """
        # Generate unique event ID
        event_id = f"evt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{environment_id[:8]}"
        
        # Create database model
        event_model = AllocationEventModel(
            id=event_id,
            event_type=event_type,
            environment_id=environment_id,
            test_id=test_id,
            allocation_request_id=allocation_request_id,
            event_metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        
        self.db.add(event_model)
        self.db.commit()
        
        # Convert to API model
        return AllocationEvent(
            id=event_model.id,
            type=event_model.event_type,
            environment_id=event_model.environment_id,
            test_id=event_model.test_id,
            timestamp=event_model.timestamp,
            metadata=event_model.event_metadata or {}
        )
    
    def get_allocation_history(
        self,
        page: int = 1,
        page_size: int = 20,
        event_type: Optional[str] = None,
        environment_id: Optional[str] = None,
        test_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sort_order: str = "desc"
    ) -> Tuple[List[AllocationEvent], Dict[str, Any]]:
        """
        Retrieve allocation history with filtering and pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Number of events per page
            event_type: Filter by event type
            environment_id: Filter by environment ID
            test_id: Filter by test ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            sort_order: Sort order ("asc" or "desc")
            
        Returns:
            Tuple of (events, pagination_info)
        """
        query = self.db.query(AllocationEventModel)
        
        # Apply filters
        if event_type:
            query = query.filter(AllocationEventModel.event_type == event_type)
        
        if environment_id:
            query = query.filter(AllocationEventModel.environment_id == environment_id)
        
        if test_id:
            query = query.filter(AllocationEventModel.test_id == test_id)
        
        if start_time:
            query = query.filter(AllocationEventModel.timestamp >= start_time)
        
        if end_time:
            query = query.filter(AllocationEventModel.timestamp <= end_time)
        
        # Apply sorting
        if sort_order == "asc":
            query = query.order_by(asc(AllocationEventModel.timestamp))
        else:
            query = query.order_by(desc(AllocationEventModel.timestamp))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        events_query = query.offset(offset).limit(page_size)
        
        # Execute query
        event_models = events_query.all()
        
        # Convert to API models
        events = [
            AllocationEvent(
                id=event.id,
                type=event.event_type,
                environment_id=event.environment_id,
                test_id=event.test_id,
                timestamp=event.timestamp,
                metadata=event.event_metadata or {}
            )
            for event in event_models
        ]
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        pagination_info = {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return events, pagination_info
    
    def get_allocation_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get allocation statistics for the specified time period.
        
        Args:
            start_time: Start of time period
            end_time: End of time period
            
        Returns:
            Dictionary containing allocation statistics
        """
        query = self.db.query(AllocationEventModel)
        
        # Apply time filters
        if start_time:
            query = query.filter(AllocationEventModel.timestamp >= start_time)
        
        if end_time:
            query = query.filter(AllocationEventModel.timestamp <= end_time)
        
        # Get all events in the time period
        events = query.all()
        
        # Calculate statistics
        total_events = len(events)
        event_type_counts = {}
        environment_usage = {}
        hourly_distribution = {}
        
        for event in events:
            # Count by event type
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
            
            # Count by environment
            env_id = event.environment_id
            environment_usage[env_id] = environment_usage.get(env_id, 0) + 1
            
            # Count by hour
            hour_key = event.timestamp.strftime('%Y-%m-%d %H:00')
            hourly_distribution[hour_key] = hourly_distribution.get(hour_key, 0) + 1
        
        return {
            "total_events": total_events,
            "event_type_counts": event_type_counts,
            "environment_usage": environment_usage,
            "hourly_distribution": hourly_distribution,
            "time_period": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None
            }
        }
    
    def correlate_with_test_results(
        self,
        environment_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Correlate allocation events with test execution results.
        
        Args:
            environment_id: Environment to analyze
            start_time: Start of time period
            end_time: End of time period
            
        Returns:
            List of correlated events and test results
        """
        # Get allocation events for the environment
        events_query = self.db.query(AllocationEventModel).filter(
            AllocationEventModel.environment_id == environment_id
        )
        
        if start_time:
            events_query = events_query.filter(AllocationEventModel.timestamp >= start_time)
        
        if end_time:
            events_query = events_query.filter(AllocationEventModel.timestamp <= end_time)
        
        events = events_query.order_by(AllocationEventModel.timestamp).all()
        
        # Get test results for the same time period
        results_query = self.db.query(TestResultModel).filter(
            TestResultModel.environment_id == environment_id
        )
        
        if start_time:
            results_query = results_query.filter(TestResultModel.timestamp >= start_time)
        
        if end_time:
            results_query = results_query.filter(TestResultModel.timestamp <= end_time)
        
        test_results = results_query.order_by(TestResultModel.timestamp).all()
        
        # Correlate events with test results
        correlations = []
        
        for event in events:
            correlation = {
                "event": {
                    "id": event.id,
                    "type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "metadata": event.event_metadata or {}
                },
                "related_tests": []
            }
            
            # Find test results within 5 minutes of the event
            event_time = event.timestamp
            time_window = timedelta(minutes=5)
            
            for result in test_results:
                if abs((result.timestamp - event_time).total_seconds()) <= time_window.total_seconds():
                    correlation["related_tests"].append({
                        "test_id": result.test_case_id,
                        "status": result.status.value,
                        "execution_time": result.execution_time,
                        "timestamp": result.timestamp.isoformat(),
                        "failure_info": result.failure_info
                    })
            
            correlations.append(correlation)
        
        return correlations
    
    def export_allocation_data(
        self,
        format_type: str = "csv",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None
    ) -> str:
        """
        Export allocation data in the specified format.
        
        Args:
            format_type: Export format ("csv" or "json")
            start_time: Start of time period
            end_time: End of time period
            event_type: Filter by event type
            
        Returns:
            Exported data as string
        """
        # Get all events matching the criteria
        events, _ = self.get_allocation_history(
            page=1,
            page_size=10000,  # Large page size to get all events
            event_type=event_type,
            start_time=start_time,
            end_time=end_time
        )
        
        if format_type.lower() == "csv":
            return self._export_to_csv(events)
        elif format_type.lower() == "json":
            return self._export_to_json(events)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_to_csv(self, events: List[AllocationEvent]) -> str:
        """Export events to CSV format."""
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Event ID", "Event Type", "Environment ID", "Test ID", 
            "Timestamp", "Metadata"
        ])
        
        # Write data
        for event in events:
            writer.writerow([
                event.id,
                event.type,
                event.environment_id,
                event.test_id or "",
                event.timestamp.isoformat(),
                json.dumps(event.metadata)
            ])
        
        return output.getvalue()
    
    def _export_to_json(self, events: List[AllocationEvent]) -> str:
        """Export events to JSON format."""
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_events": len(events),
            "events": [
                {
                    "id": event.id,
                    "type": event.type,
                    "environment_id": event.environment_id,
                    "test_id": event.test_id,
                    "timestamp": event.timestamp.isoformat(),
                    "metadata": event.metadata
                }
                for event in events
            ]
        }
        
        return json.dumps(export_data, indent=2)