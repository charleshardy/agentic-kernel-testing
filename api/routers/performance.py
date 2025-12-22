"""Performance metrics API endpoints."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta

from execution.performance_monitor import get_performance_monitor, PerformanceMetrics
from api.models import APIResponse

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/metrics/{test_id}")
async def get_test_performance_metrics(test_id: str) -> APIResponse:
    """Get performance metrics for a specific test.
    
    Args:
        test_id: ID of the test to get metrics for
        
    Returns:
        APIResponse with performance metrics data
    """
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_metrics(test_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail=f"No performance metrics found for test {test_id}")
        
        return APIResponse(
            success=True,
            data=metrics.to_dict(),
            message=f"Performance metrics retrieved for test {test_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")


@router.get("/metrics")
async def get_all_performance_metrics(
    limit: Optional[int] = Query(100, description="Maximum number of metrics to return"),
    offset: Optional[int] = Query(0, description="Number of metrics to skip")
) -> APIResponse:
    """Get performance metrics for all tests.
    
    Args:
        limit: Maximum number of metrics to return
        offset: Number of metrics to skip
        
    Returns:
        APIResponse with list of performance metrics
    """
    try:
        monitor = get_performance_monitor()
        all_metrics = monitor.get_all_metrics()
        
        # Convert to list and apply pagination
        metrics_list = list(all_metrics.values())
        total_count = len(metrics_list)
        
        # Sort by start time (most recent first)
        metrics_list.sort(key=lambda m: m.start_time, reverse=True)
        
        # Apply pagination
        paginated_metrics = metrics_list[offset:offset + limit]
        
        return APIResponse(
            success=True,
            data={
                "metrics": [m.to_dict() for m in paginated_metrics],
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            },
            message=f"Retrieved {len(paginated_metrics)} performance metrics"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")


@router.get("/summary")
async def get_performance_summary(
    hours: Optional[int] = Query(24, description="Number of hours to include in summary")
) -> APIResponse:
    """Get performance summary statistics.
    
    Args:
        hours: Number of hours to include in summary
        
    Returns:
        APIResponse with performance summary data
    """
    try:
        monitor = get_performance_monitor()
        all_metrics = monitor.get_all_metrics()
        
        # Filter metrics by time window
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in all_metrics.values()
            if m.start_time >= cutoff_time
        ]
        
        if not recent_metrics:
            return APIResponse(
                success=True,
                data={
                    "total_tests": 0,
                    "avg_duration_seconds": 0,
                    "avg_cpu_percent": 0,
                    "avg_memory_mb": 0,
                    "avg_performance_score": 0,
                    "common_bottlenecks": [],
                    "time_window_hours": hours
                },
                message=f"No performance data found for the last {hours} hours"
            )
        
        # Calculate summary statistics
        total_tests = len(recent_metrics)
        avg_duration = sum(m.duration_seconds for m in recent_metrics) / total_tests
        avg_cpu = sum(m.avg_cpu_percent for m in recent_metrics) / total_tests
        avg_memory = sum(m.avg_memory_mb for m in recent_metrics) / total_tests
        avg_score = sum(m.performance_score for m in recent_metrics) / total_tests
        
        # Count bottlenecks
        bottleneck_counts = {}
        for metrics in recent_metrics:
            for bottleneck in metrics.bottlenecks:
                bottleneck_counts[bottleneck] = bottleneck_counts.get(bottleneck, 0) + 1
        
        # Get most common bottlenecks
        common_bottlenecks = sorted(
            bottleneck_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5
        
        return APIResponse(
            success=True,
            data={
                "total_tests": total_tests,
                "avg_duration_seconds": round(avg_duration, 2),
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_mb": round(avg_memory, 2),
                "avg_performance_score": round(avg_score, 2),
                "common_bottlenecks": [{"bottleneck": b, "count": c} for b, c in common_bottlenecks],
                "time_window_hours": hours
            },
            message=f"Performance summary for {total_tests} tests in the last {hours} hours"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating performance summary: {str(e)}")


@router.get("/trends")
async def get_performance_trends(
    days: Optional[int] = Query(7, description="Number of days to include in trends"),
    metric: Optional[str] = Query("performance_score", description="Metric to analyze trends for")
) -> APIResponse:
    """Get performance trends over time.
    
    Args:
        days: Number of days to include in trends
        metric: Metric to analyze trends for
        
    Returns:
        APIResponse with trend data
    """
    try:
        monitor = get_performance_monitor()
        all_metrics = monitor.get_all_metrics()
        
        # Filter metrics by time window
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_metrics = [
            m for m in all_metrics.values()
            if m.start_time >= cutoff_time
        ]
        
        if not recent_metrics:
            return APIResponse(
                success=True,
                data={
                    "trend_data": [],
                    "metric": metric,
                    "days": days,
                    "trend_direction": "stable"
                },
                message=f"No performance data found for the last {days} days"
            )
        
        # Sort by time
        recent_metrics.sort(key=lambda m: m.start_time)
        
        # Extract metric values
        valid_metrics = {
            "performance_score": lambda m: m.performance_score,
            "avg_cpu_percent": lambda m: m.avg_cpu_percent,
            "avg_memory_mb": lambda m: m.avg_memory_mb,
            "duration_seconds": lambda m: m.duration_seconds
        }
        
        if metric not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")
        
        metric_extractor = valid_metrics[metric]
        
        # Group by day and calculate daily averages
        daily_data = {}
        for m in recent_metrics:
            day_key = m.start_time.date().isoformat()
            if day_key not in daily_data:
                daily_data[day_key] = []
            daily_data[day_key].append(metric_extractor(m))
        
        # Calculate daily averages
        trend_data = []
        for day, values in sorted(daily_data.items()):
            avg_value = sum(values) / len(values)
            trend_data.append({
                "date": day,
                "value": round(avg_value, 2),
                "count": len(values)
            })
        
        # Determine trend direction
        trend_direction = "stable"
        if len(trend_data) >= 2:
            first_half = trend_data[:len(trend_data)//2]
            second_half = trend_data[len(trend_data)//2:]
            
            first_avg = sum(d["value"] for d in first_half) / len(first_half)
            second_avg = sum(d["value"] for d in second_half) / len(second_half)
            
            change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
            
            if change_percent > 5:
                trend_direction = "improving" if metric == "performance_score" else "increasing"
            elif change_percent < -5:
                trend_direction = "declining" if metric == "performance_score" else "decreasing"
        
        return APIResponse(
            success=True,
            data={
                "trend_data": trend_data,
                "metric": metric,
                "days": days,
                "trend_direction": trend_direction,
                "total_tests": len(recent_metrics)
            },
            message=f"Performance trends for {metric} over the last {days} days"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating performance trends: {str(e)}")


@router.get("/bottlenecks")
async def get_bottleneck_analysis(
    hours: Optional[int] = Query(24, description="Number of hours to analyze")
) -> APIResponse:
    """Get bottleneck analysis for recent tests.
    
    Args:
        hours: Number of hours to analyze
        
    Returns:
        APIResponse with bottleneck analysis
    """
    try:
        monitor = get_performance_monitor()
        all_metrics = monitor.get_all_metrics()
        
        # Filter metrics by time window
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in all_metrics.values()
            if m.start_time >= cutoff_time
        ]
        
        if not recent_metrics:
            return APIResponse(
                success=True,
                data={
                    "bottlenecks": [],
                    "total_tests": 0,
                    "hours": hours
                },
                message=f"No performance data found for the last {hours} hours"
            )
        
        # Analyze bottlenecks
        bottleneck_analysis = {}
        total_tests = len(recent_metrics)
        
        for metrics in recent_metrics:
            for bottleneck in metrics.bottlenecks:
                if bottleneck not in bottleneck_analysis:
                    bottleneck_analysis[bottleneck] = {
                        "count": 0,
                        "percentage": 0,
                        "affected_tests": [],
                        "avg_performance_score": 0,
                        "description": _get_bottleneck_description(bottleneck)
                    }
                
                analysis = bottleneck_analysis[bottleneck]
                analysis["count"] += 1
                analysis["affected_tests"].append(metrics.test_id)
                analysis["avg_performance_score"] += metrics.performance_score
        
        # Calculate percentages and averages
        for bottleneck, analysis in bottleneck_analysis.items():
            analysis["percentage"] = round((analysis["count"] / total_tests) * 100, 1)
            analysis["avg_performance_score"] = round(
                analysis["avg_performance_score"] / analysis["count"], 2
            )
        
        # Sort by frequency
        sorted_bottlenecks = sorted(
            bottleneck_analysis.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        return APIResponse(
            success=True,
            data={
                "bottlenecks": [
                    {"type": bottleneck, **analysis}
                    for bottleneck, analysis in sorted_bottlenecks
                ],
                "total_tests": total_tests,
                "hours": hours
            },
            message=f"Bottleneck analysis for {total_tests} tests in the last {hours} hours"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing bottlenecks: {str(e)}")


def _get_bottleneck_description(bottleneck: str) -> str:
    """Get human-readable description for a bottleneck type.
    
    Args:
        bottleneck: Bottleneck type identifier
        
    Returns:
        Human-readable description
    """
    descriptions = {
        "high_cpu_usage": "High CPU usage (>80% average)",
        "cpu_saturation": "CPU saturation (>95% peak)",
        "high_memory_usage": "High memory usage (>80% average)",
        "memory_pressure": "Memory pressure (>95% peak)",
        "high_disk_io": "High disk I/O (>1GB total)",
        "high_network_io": "High network I/O (>500MB total)",
        "system_overload": "System overload (load > 2x CPU count)",
        "high_system_load": "High system load (load > CPU count)"
    }
    
    return descriptions.get(bottleneck, f"Unknown bottleneck: {bottleneck}")


@router.delete("/metrics/{test_id}")
async def delete_test_performance_metrics(test_id: str) -> APIResponse:
    """Delete performance metrics for a specific test.
    
    Args:
        test_id: ID of the test to delete metrics for
        
    Returns:
        APIResponse confirming deletion
    """
    try:
        monitor = get_performance_monitor()
        
        if test_id not in monitor.metrics_storage:
            raise HTTPException(status_code=404, detail=f"No performance metrics found for test {test_id}")
        
        del monitor.metrics_storage[test_id]
        
        return APIResponse(
            success=True,
            data={"deleted_test_id": test_id},
            message=f"Performance metrics deleted for test {test_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting performance metrics: {str(e)}")