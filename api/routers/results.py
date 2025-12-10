"""Test results retrieval endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import FileResponse, StreamingResponse
import json
import io

from ..models import (
    APIResponse, TestResultResponse, CoverageReport, 
    FailureAnalysisResponse, PaginationParams
)
from ..auth import get_current_user, require_permission
from ai_generator.models import TestStatus, TestResult, CoverageData, FailureAnalysis

router = APIRouter()

# Mock results data (in production, this would come from database)
test_results = {}
coverage_reports = {}
failure_analyses = {}


def initialize_mock_results():
    """Initialize mock test results for demonstration."""
    # Mock test result 1 - Passed
    result_1 = {
        "test_id": "test-001",
        "status": TestStatus.PASSED,
        "execution_time": 125.5,
        "environment": {
            "id": "env-001",
            "architecture": "x86_64",
            "cpu_model": "Intel Xeon E5-2686 v4",
            "memory_mb": 4096,
            "is_virtual": True,
            "emulator": "qemu"
        },
        "artifacts": {
            "logs": ["/artifacts/test-001/kernel.log", "/artifacts/test-001/test.log"],
            "core_dumps": [],
            "traces": ["/artifacts/test-001/trace.txt"],
            "screenshots": [],
            "metadata": {"kernel_version": "6.1.0-rc1"}
        },
        "coverage_data": {
            "line_coverage": 0.85,
            "branch_coverage": 0.78,
            "function_coverage": 0.92,
            "covered_lines": ["file1.c:123", "file1.c:124", "file2.c:456"],
            "uncovered_lines": ["file1.c:125", "file2.c:457"],
            "report_url": "/coverage/test-001/report.html"
        },
        "failure_info": None,
        "timestamp": datetime.utcnow() - timedelta(minutes=30)
    }
    
    # Mock test result 2 - Failed
    result_2 = {
        "test_id": "test-002",
        "status": TestStatus.FAILED,
        "execution_time": 45.2,
        "environment": {
            "id": "env-002",
            "architecture": "arm64",
            "cpu_model": "ARM Cortex-A72",
            "memory_mb": 2048,
            "is_virtual": False,
            "emulator": None
        },
        "artifacts": {
            "logs": ["/artifacts/test-002/kernel.log", "/artifacts/test-002/panic.log"],
            "core_dumps": ["/artifacts/test-002/vmcore"],
            "traces": [],
            "screenshots": [],
            "metadata": {"kernel_version": "6.1.0-rc1", "panic_reason": "null_pointer_dereference"}
        },
        "coverage_data": None,
        "failure_info": {
            "error_message": "Kernel panic: NULL pointer dereference in network driver",
            "stack_trace": "Call Trace:\n[<ffffffff81234567>] e1000e_setup_rx_resources+0x45/0x120\n[<ffffffff81234890>] e1000e_open+0x123/0x200",
            "exit_code": -1,
            "kernel_panic": True,
            "timeout_occurred": False
        },
        "timestamp": datetime.utcnow() - timedelta(minutes=20)
    }
    
    test_results["test-001"] = result_1
    test_results["test-002"] = result_2
    
    # Mock coverage report
    coverage_reports["test-001"] = {
        "line_coverage": 0.85,
        "branch_coverage": 0.78,
        "function_coverage": 0.92,
        "covered_lines": ["drivers/net/e1000e/netdev.c:123", "drivers/net/e1000e/netdev.c:124"],
        "uncovered_lines": ["drivers/net/e1000e/netdev.c:125", "drivers/net/e1000e/param.c:67"],
        "coverage_gaps": [
            {
                "file": "drivers/net/e1000e/netdev.c",
                "function": "e1000e_setup_rx_resources",
                "lines": [125, 126],
                "reason": "Error handling path not tested"
            }
        ],
        "report_url": "/api/v1/results/test-001/coverage/report.html"
    }
    
    # Mock failure analysis
    failure_analyses["test-002"] = {
        "failure_id": "fail-002",
        "root_cause": "NULL pointer dereference in network driver initialization",
        "confidence": 0.92,
        "suspicious_commits": [
            {
                "sha": "abc123def456",
                "message": "net: e1000e: refactor rx buffer allocation",
                "author": "developer@example.com",
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat()
            }
        ],
        "error_pattern": "null_pointer_dereference_network_driver",
        "stack_trace": "Call Trace:\n[<ffffffff81234567>] e1000e_setup_rx_resources+0x45/0x120",
        "suggested_fixes": [
            {
                "description": "Add null pointer check before buffer allocation",
                "code_patch": "if (!adapter->rx_ring) return -ENOMEM;",
                "confidence": 0.85,
                "rationale": "The crash occurs when rx_ring is NULL during setup"
            }
        ],
        "related_failures": ["fail-001", "fail-003"],
        "reproducibility": 0.95
    }


# Initialize mock data
initialize_mock_results()


@router.get("/results/tests/{test_id}", response_model=APIResponse)
async def get_test_result(
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("results:read"))
):
    """Get detailed results for a specific test."""
    if test_id not in test_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test result not found"
        )
    
    result_data = test_results[test_id]
    
    test_result = TestResultResponse(
        test_id=result_data["test_id"],
        status=result_data["status"],
        execution_time=result_data["execution_time"],
        environment=result_data["environment"],
        artifacts=result_data["artifacts"],
        coverage_data=result_data["coverage_data"],
        failure_info=result_data["failure_info"],
        timestamp=result_data["timestamp"]
    )
    
    return APIResponse(
        success=True,
        message="Test result retrieved successfully",
        data=test_result.dict()
    )


@router.get("/results/tests", response_model=APIResponse)
async def list_test_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TestStatus] = Query(None, description="Filter by test status"),
    subsystem: Optional[str] = Query(None, description="Filter by subsystem"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: Dict[str, Any] = Depends(require_permission("results:read"))
):
    """List test results with pagination and filtering."""
    try:
        results_list = []
        
        for test_id, result_data in test_results.items():
            # Apply filters
            if status_filter and result_data["status"] != status_filter:
                continue
            
            # Date filtering
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if result_data["timestamp"] < start_dt:
                    continue
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if result_data["timestamp"] > end_dt:
                    continue
            
            results_list.append({
                "test_id": test_id,
                "status": result_data["status"].value,
                "execution_time": result_data["execution_time"],
                "environment_id": result_data["environment"]["id"],
                "architecture": result_data["environment"]["architecture"],
                "has_coverage": result_data["coverage_data"] is not None,
                "has_failure_analysis": test_id in failure_analyses,
                "timestamp": result_data["timestamp"].isoformat()
            })
        
        # Sort by timestamp (newest first)
        results_list.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Pagination
        total_items = len(results_list)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = results_list[start_idx:end_idx]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated_results)} test results",
            data={
                "results": paginated_results,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": (total_items + page_size - 1) // page_size
                },
                "summary": {
                    "total_tests": total_items,
                    "passed_tests": len([r for r in results_list if r["status"] == "passed"]),
                    "failed_tests": len([r for r in results_list if r["status"] == "failed"]),
                    "avg_execution_time": sum(r["execution_time"] for r in results_list) / len(results_list) if results_list else 0
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve test results: {str(e)}"
        )


@router.get("/results/coverage/{test_id}", response_model=APIResponse)
async def get_coverage_report(
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("results:read"))
):
    """Get coverage report for a specific test."""
    if test_id not in coverage_reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coverage report not found"
        )
    
    coverage_data = coverage_reports[test_id]
    
    coverage_report = CoverageReport(
        line_coverage=coverage_data["line_coverage"],
        branch_coverage=coverage_data["branch_coverage"],
        function_coverage=coverage_data["function_coverage"],
        covered_lines=coverage_data["covered_lines"],
        uncovered_lines=coverage_data["uncovered_lines"],
        coverage_gaps=coverage_data["coverage_gaps"],
        report_url=coverage_data["report_url"]
    )
    
    return APIResponse(
        success=True,
        message="Coverage report retrieved successfully",
        data=coverage_report.dict()
    )


@router.get("/results/failures/{test_id}", response_model=APIResponse)
async def get_failure_analysis(
    test_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("results:read"))
):
    """Get failure analysis for a failed test."""
    if test_id not in failure_analyses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failure analysis not found"
        )
    
    analysis_data = failure_analyses[test_id]
    
    failure_analysis = FailureAnalysisResponse(
        failure_id=analysis_data["failure_id"],
        root_cause=analysis_data["root_cause"],
        confidence=analysis_data["confidence"],
        suspicious_commits=analysis_data["suspicious_commits"],
        error_pattern=analysis_data["error_pattern"],
        stack_trace=analysis_data["stack_trace"],
        suggested_fixes=analysis_data["suggested_fixes"],
        related_failures=analysis_data["related_failures"],
        reproducibility=analysis_data["reproducibility"]
    )
    
    return APIResponse(
        success=True,
        message="Failure analysis retrieved successfully",
        data=failure_analysis.dict()
    )


@router.get("/results/artifacts/{test_id}")
async def download_test_artifacts(
    test_id: str,
    artifact_type: str = Query(..., description="Type of artifact (logs, traces, dumps)"),
    current_user: Dict[str, Any] = Depends(require_permission("results:read"))
):
    """Download test artifacts (logs, traces, core dumps)."""
    if test_id not in test_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test result not found"
        )
    
    result_data = test_results[test_id]
    artifacts = result_data["artifacts"]
    
    # Mock artifact content based on type
    if artifact_type == "logs":
        content = f"""
[    0.000000] Linux version 6.1.0-rc1 (test@builder) (gcc version 11.3.0)
[    0.000000] Command line: BOOT_IMAGE=/boot/vmlinuz root=/dev/sda1
[    0.123456] Test execution started for {test_id}
[    1.234567] Network driver initialization
[    2.345678] Test completed with status: {result_data['status'].value}
"""
    elif artifact_type == "traces":
        content = f"""
Test Trace for {test_id}
========================
Function calls:
  e1000e_probe() -> SUCCESS
  e1000e_setup_rx_resources() -> {'SUCCESS' if result_data['status'] == TestStatus.PASSED else 'FAILED'}
  e1000e_open() -> {'SUCCESS' if result_data['status'] == TestStatus.PASSED else 'FAILED'}

Execution time: {result_data['execution_time']}s
"""
    elif artifact_type == "dumps":
        if result_data["status"] == TestStatus.FAILED:
            content = f"""
Core dump for {test_id}
======================
Crash address: 0xffffffff81234567
Register state:
  RIP: e1000e_setup_rx_resources+0x45/0x120
  RSP: 0xffff888012345678
  RAX: 0x0000000000000000 (NULL pointer)
"""
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No core dumps available for passed test"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid artifact type. Must be 'logs', 'traces', or 'dumps'"
        )
    
    # Return as downloadable file
    filename = f"{test_id}_{artifact_type}.txt"
    
    def generate():
        yield content.encode('utf-8')
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/results/export", response_model=APIResponse)
async def export_results(
    format: str = Query("json", description="Export format (json, csv, xml)"),
    test_ids: Optional[str] = Query(None, description="Comma-separated test IDs"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: Dict[str, Any] = Depends(require_permission("results:read"))
):
    """Export test results in various formats."""
    try:
        # Filter results based on parameters
        results_to_export = []
        
        if test_ids:
            # Export specific test IDs
            test_id_list = [tid.strip() for tid in test_ids.split(",")]
            for test_id in test_id_list:
                if test_id in test_results:
                    results_to_export.append({
                        "test_id": test_id,
                        **test_results[test_id]
                    })
        else:
            # Export all results (with date filtering)
            for test_id, result_data in test_results.items():
                # Apply date filters
                if start_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if result_data["timestamp"] < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if result_data["timestamp"] > end_dt:
                        continue
                
                results_to_export.append({
                    "test_id": test_id,
                    **result_data
                })
        
        if not results_to_export:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No results found matching the criteria"
            )
        
        # Generate export based on format
        if format.lower() == "json":
            # Convert datetime objects to ISO strings for JSON serialization
            export_data = []
            for result in results_to_export:
                result_copy = result.copy()
                result_copy["status"] = result_copy["status"].value
                result_copy["timestamp"] = result_copy["timestamp"].isoformat()
                export_data.append(result_copy)
            
            export_content = json.dumps(export_data, indent=2)
            media_type = "application/json"
            filename = f"test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
        elif format.lower() == "csv":
            # Simple CSV export
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "test_id", "status", "execution_time", "architecture", 
                "environment_id", "timestamp", "has_failure"
            ])
            
            # Write data
            for result in results_to_export:
                writer.writerow([
                    result["test_id"],
                    result["status"].value,
                    result["execution_time"],
                    result["environment"]["architecture"],
                    result["environment"]["id"],
                    result["timestamp"].isoformat(),
                    result["failure_info"] is not None
                ])
            
            export_content = output.getvalue()
            media_type = "text/csv"
            filename = f"test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Use 'json' or 'csv'"
            )
        
        # Return as downloadable file
        def generate():
            yield export_content.encode('utf-8')
        
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/results/summary", response_model=APIResponse)
async def get_results_summary(
    days: int = Query(7, ge=1, le=365, description="Number of days to summarize"),
    current_user: Dict[str, Any] = Depends(require_permission("results:read"))
):
    """Get summary statistics for test results."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter results by date
        recent_results = [
            result for result in test_results.values()
            if result["timestamp"] >= cutoff_date
        ]
        
        if not recent_results:
            return APIResponse(
                success=True,
                message=f"No test results found in the last {days} days",
                data={
                    "period_days": days,
                    "total_tests": 0,
                    "summary": {}
                }
            )
        
        # Calculate statistics
        total_tests = len(recent_results)
        passed_tests = len([r for r in recent_results if r["status"] == TestStatus.PASSED])
        failed_tests = len([r for r in recent_results if r["status"] == TestStatus.FAILED])
        
        avg_execution_time = sum(r["execution_time"] for r in recent_results) / total_tests
        
        # Group by architecture
        arch_stats = {}
        for result in recent_results:
            arch = result["environment"]["architecture"]
            if arch not in arch_stats:
                arch_stats[arch] = {"total": 0, "passed": 0, "failed": 0}
            arch_stats[arch]["total"] += 1
            if result["status"] == TestStatus.PASSED:
                arch_stats[arch]["passed"] += 1
            else:
                arch_stats[arch]["failed"] += 1
        
        summary = {
            "period_days": days,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "avg_execution_time_seconds": round(avg_execution_time, 2),
            "architecture_breakdown": arch_stats,
            "daily_test_counts": {
                # Mock daily breakdown
                (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"): 
                max(0, total_tests // days + (i % 3) - 1)
                for i in range(min(days, 7))
            }
        }
        
        return APIResponse(
            success=True,
            message=f"Test results summary for the last {days} days",
            data=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )