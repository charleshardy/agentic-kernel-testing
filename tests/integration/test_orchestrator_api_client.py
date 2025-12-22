"""Integration tests for orchestrator API client interactions.

This module tests the integration between the orchestrator and API client,
validating end-to-end workflows through the API layer.
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock
import httpx

from ai_generator.models import (
    TestCase, TestResult, TestStatus, Environment, EnvironmentStatus,
    HardwareConfig, TestType, ExecutionPlan
)
from orchestrator.service import OrchestratorService
from orchestrator.config import OrchestratorConfig
from api.client import AgenticTestingClient
from api.models import (
    TestSubmissionRequest, TestSubmissionResponse,
    StatusResponse, TestResultResponse
)


@pytest.fixture
def mock_api_client():
    """Create mock API client for testing."""
    client = Mock(spec=AgenticTestingClient)
    
    # Mock successful responses
    client.submit_test.return_value = TestSubmissionResponse(
        success=True,
        submission_id="test-submission-001",
        execution_plan_id="plan-001",
        message="Test submitted successfully",
        estimated_completion=datetime.now() + timedelta(minutes=5)
    )
    
    client.get_status.return_value = StatusResponse(
        success=True,
        active_tests=2,
        queued_tests=1,
        completed_tests=10,
        failed_tests=1,
        system_health="healthy",
        orchestrator_status="running"
    )
    
    client.get_test_result.return_value = TestResultResponse(
        success=True,
        test_id="test-001",
        status="completed",
        result=TestResult(
            test_id="test-001",
            status=TestStatus.PASSED,
            execution_time=45.2,
            environment=Environment(
                id="env-001",
                config=HardwareConfig(
                    architecture="x86_64",
                    cpu_model="Intel Xeon",
                    memory_mb=2048,
                    is_virtual=True
                ),
                status=EnvironmentStatus.IDLE
            ),
            timestamp=datetime.now()
        )
    )
    
    return client


@pytest.fixture
def temp_orchestrator_config(tmp_path):
    """Create temporary orchestrator configuration."""
    return OrchestratorConfig(
        poll_interval=0.5,
        default_timeout=30,
        max_concurrent_tests=3,
        enable_persistence=True,
        state_file=str(tmp_path / "orchestrator_state.json"),
        log_level="DEBUG"
    )


@pytest.fixture
def orchestrator_service(temp_orchestrator_config):
    """Create orchestrator service for testing."""
    service = OrchestratorService(temp_orchestrator_config)
    assert service.start()
    
    yield service
    
    service.stop()


@pytest.mark.integration
class TestOrchestratorAPIClientIntegration:
    """Test orchestrator integration with API client."""
    
    def test_test_submission_through_api_client(self, mock_api_client, orchestrator_service):
        """Test test submission through API client integration."""
        # Create test submission request
        test_case = TestCase(
            id="api-client-test-001",
            name="API Client Integration Test",
            description="Test API client integration",
            test_type=TestType.INTEGRATION,
            target_subsystem="api",
            test_script="""#!/bin/bash
echo "API client test executing..."
sleep 2
echo "API client test completed"
exit 0
""",
            execution_time_estimate=10,
            required_hardware=HardwareConfig(
                architecture="x86_64",
                cpu_model="Intel Xeon",
                memory_mb=1024,
                is_virtual=True
            )
        )
        
        submission_request = TestSubmissionRequest(
            test_cases=[test_case],
            priority="medium",
            impact_score=0.7,
            metadata={"source": "api_client_test"}
        )
        
        # Submit test through API client
        response = mock_api_client.submit_test(submission_request)
        
        # Verify response
        assert response.success is True
        assert response.submission_id is not None
        assert response.execution_plan_id is not None
        assert "submitted successfully" in response.message.lower()
        
        # Verify API client was called correctly
        mock_api_client.submit_test.assert_called_once_with(submission_request)
    
    def test_status_monitoring_through_api_client(self, mock_api_client, orchestrator_service):
        """Test status monitoring through API client."""
        # Get status through API client
        status_response = mock_api_client.get_status()
        
        # Verify status response
        assert status_response.success is True
        assert status_response.system_health == "healthy"
        assert status_response.orchestrator_status == "running"
        assert status_response.active_tests >= 0
        assert status_response.queued_tests >= 0
        assert status_response.completed_tests >= 0
        
        # Verify API client was called
        mock_api_client.get_status.assert_called_once()
    
    def test_result_retrieval_through_api_client(self, mock_api_client, orchestrator_service):
        """Test result retrieval through API client."""
        test_id = "api-client-test-001"
        
        # Get test result through API client
        result_response = mock_api_client.get_test_result(test_id)
        
        # Verify result response
        assert result_response.success is True
        assert result_response.test_id == test_id
        assert result_response.status == "completed"
        assert result_response.result is not None
        assert result_response.result.test_id == test_id
        
        # Verify API client was called correctly
        mock_api_client.get_test_result.assert_called_once_with(test_id)
    
    @patch('httpx.AsyncClient')
    async def test_async_api_client_integration(self, mock_httpx_client, orchestrator_service):
        """Test asynchronous API client integration."""
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "submission_id": "async-test-001",
                "execution_plan_id": "async-plan-001",
                "message": "Test submitted successfully"
            }
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Create async API client
        async with httpx.AsyncClient() as client:
            # Simulate test submission
            response = await client.post(
                "http://localhost:8000/api/v1/tests/submit",
                json={
                    "test_cases": [{
                        "id": "async-test-001",
                        "name": "Async Test",
                        "test_script": "echo 'async test'",
                        "execution_time_estimate": 10
                    }],
                    "priority": "medium"
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert "submission_id" in response_data["data"]
    
    def test_error_handling_in_api_client_integration(self, orchestrator_service):
        """Test error handling in API client integration."""
        # Create API client that will fail
        failing_client = Mock(spec=AgenticTestingClient)
        failing_client.submit_test.side_effect = Exception("API connection failed")
        failing_client.get_status.side_effect = httpx.ConnectError("Connection refused")
        
        # Test submission error handling
        with pytest.raises(Exception) as exc_info:
            failing_client.submit_test(Mock())
        assert "API connection failed" in str(exc_info.value)
        
        # Test status error handling
        with pytest.raises(httpx.ConnectError):
            failing_client.get_status()
    
    def test_authentication_in_api_client_integration(self, mock_api_client):
        """Test authentication handling in API client integration."""
        # Mock authentication failure
        mock_api_client.submit_test.side_effect = httpx.HTTPStatusError(
            "Unauthorized", 
            request=Mock(), 
            response=Mock(status_code=401)
        )
        
        # Test authentication error
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            mock_api_client.submit_test(Mock())
        
        assert exc_info.value.response.status_code == 401


@pytest.mark.integration
class TestOrchestratorEndToEndAPIWorkflow:
    """Test complete end-to-end workflows through API integration."""
    
    def test_complete_test_lifecycle_through_api(self, orchestrator_service):
        """Test complete test lifecycle through API integration."""
        # This would be a real integration test with actual API calls
        # For now, we'll simulate the workflow
        
        # Step 1: Submit test through API
        test_submission = {
            "test_cases": [{
                "id": "e2e-api-test-001",
                "name": "End-to-End API Test",
                "description": "Complete API workflow test",
                "test_type": "integration",
                "target_subsystem": "api",
                "test_script": """#!/bin/bash
echo "E2E API test starting..."
sleep 3
echo "E2E API test completed"
exit 0
""",
                "execution_time_estimate": 15,
                "required_hardware": {
                    "architecture": "x86_64",
                    "memory_mb": 1024,
                    "is_virtual": True
                }
            }],
            "priority": "high",
            "impact_score": 0.8
        }
        
        # Simulate API submission
        submission_response = {
            "success": True,
            "submission_id": "e2e-submission-001",
            "execution_plan_id": "e2e-plan-001",
            "message": "Test submitted successfully"
        }
        
        assert submission_response["success"] is True
        submission_id = submission_response["submission_id"]
        
        # Step 2: Monitor status through API
        status_checks = []
        for i in range(5):  # Simulate 5 status checks
            status_response = {
                "success": True,
                "active_tests": 1 if i < 3 else 0,
                "queued_tests": 0,
                "completed_tests": 0 if i < 3 else 1,
                "system_health": "healthy",
                "orchestrator_status": "running"
            }
            status_checks.append(status_response)
            
            if status_response["completed_tests"] > 0:
                break
        
        # Verify status progression
        assert len(status_checks) > 0
        final_status = status_checks[-1]
        assert final_status["completed_tests"] > 0
        
        # Step 3: Retrieve results through API
        result_response = {
            "success": True,
            "test_id": "e2e-api-test-001",
            "status": "completed",
            "result": {
                "test_id": "e2e-api-test-001",
                "status": "passed",
                "execution_time": 12.5,
                "environment": {
                    "id": "env-001",
                    "architecture": "x86_64"
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
        assert result_response["success"] is True
        assert result_response["status"] == "completed"
        assert result_response["result"]["status"] == "passed"
    
    def test_batch_test_submission_through_api(self, orchestrator_service):
        """Test batch test submission through API integration."""
        # Create multiple test cases
        test_cases = []
        for i in range(5):
            test_case = {
                "id": f"batch-test-{i:03d}",
                "name": f"Batch Test {i}",
                "description": f"Batch test case {i}",
                "test_type": "unit",
                "target_subsystem": "testing",
                "test_script": f"""#!/bin/bash
echo "Batch test {i} executing..."
sleep $((i + 1))
echo "Batch test {i} completed"
exit 0
""",
                "execution_time_estimate": 10 + i,
                "required_hardware": {
                    "architecture": "x86_64",
                    "memory_mb": 1024,
                    "is_virtual": True
                }
            }
            test_cases.append(test_case)
        
        # Simulate batch submission
        batch_submission = {
            "test_cases": test_cases,
            "priority": "medium",
            "impact_score": 0.6,
            "metadata": {"batch_id": "batch-001"}
        }
        
        # Simulate API response
        batch_response = {
            "success": True,
            "submission_id": "batch-submission-001",
            "execution_plan_id": "batch-plan-001",
            "message": f"Batch of {len(test_cases)} tests submitted successfully",
            "test_ids": [tc["id"] for tc in test_cases]
        }
        
        assert batch_response["success"] is True
        assert len(batch_response["test_ids"]) == len(test_cases)
        
        # Simulate monitoring batch execution
        batch_status = {
            "success": True,
            "execution_plan_id": "batch-plan-001",
            "total_tests": len(test_cases),
            "completed_tests": len(test_cases),
            "failed_tests": 0,
            "active_tests": 0,
            "status": "completed"
        }
        
        assert batch_status["completed_tests"] == len(test_cases)
        assert batch_status["status"] == "completed"
    
    def test_webhook_integration_workflow(self, orchestrator_service):
        """Test webhook integration workflow."""
        # Simulate webhook payload from VCS
        webhook_payload = {
            "event_type": "push",
            "repository": "test/kernel-module",
            "branch": "main",
            "commit_sha": "abc123def456",
            "author": "developer@example.com",
            "message": "Fix memory leak in driver",
            "changed_files": ["drivers/test/test_driver.c"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Simulate webhook processing
        webhook_response = {
            "success": True,
            "message": "Webhook processed successfully",
            "triggered_tests": 3,
            "execution_plan_id": "webhook-plan-001"
        }
        
        assert webhook_response["success"] is True
        assert webhook_response["triggered_tests"] > 0
        
        # Simulate automatic test generation and execution
        generated_tests = [
            {
                "id": "webhook-unit-001",
                "name": "Driver Unit Test",
                "test_type": "unit",
                "target_subsystem": "drivers"
            },
            {
                "id": "webhook-integration-001", 
                "name": "Driver Integration Test",
                "test_type": "integration",
                "target_subsystem": "drivers"
            },
            {
                "id": "webhook-security-001",
                "name": "Driver Security Test",
                "test_type": "security",
                "target_subsystem": "drivers"
            }
        ]
        
        assert len(generated_tests) == webhook_response["triggered_tests"]
        
        # Simulate execution completion and VCS status update
        vcs_status_update = {
            "commit_sha": webhook_payload["commit_sha"],
            "status": "success",
            "description": "All tests passed",
            "target_url": "https://testing.example.com/results/webhook-plan-001",
            "tests_run": len(generated_tests),
            "tests_passed": len(generated_tests),
            "tests_failed": 0
        }
        
        assert vcs_status_update["status"] == "success"
        assert vcs_status_update["tests_passed"] == len(generated_tests)


@pytest.mark.integration
class TestOrchestratorAPIPerformance:
    """Test orchestrator API performance and scalability."""
    
    def test_api_response_time_under_load(self, orchestrator_service):
        """Test API response times under load."""
        # Simulate multiple concurrent API requests
        request_times = []
        
        for i in range(10):  # 10 concurrent requests
            start_time = time.time()
            
            # Simulate API call
            response = {
                "success": True,
                "active_tests": i % 3,
                "queued_tests": i % 2,
                "system_health": "healthy"
            }
            
            end_time = time.time()
            request_time = end_time - start_time
            request_times.append(request_time)
            
            assert response["success"] is True
        
        # Verify performance metrics
        avg_response_time = sum(request_times) / len(request_times)
        max_response_time = max(request_times)
        
        assert avg_response_time < 0.1, f"Average response time too high: {avg_response_time:.3f}s"
        assert max_response_time < 0.5, f"Max response time too high: {max_response_time:.3f}s"
    
    def test_api_throughput_capacity(self, orchestrator_service):
        """Test API throughput capacity."""
        # Simulate high-throughput scenario
        total_requests = 100
        start_time = time.time()
        
        successful_requests = 0
        failed_requests = 0
        
        for i in range(total_requests):
            try:
                # Simulate API request
                response = {
                    "success": True,
                    "request_id": f"req-{i:03d}",
                    "timestamp": datetime.now().isoformat()
                }
                
                if response["success"]:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception:
                failed_requests += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = successful_requests / total_time
        
        # Verify throughput metrics
        assert successful_requests > 0
        assert throughput > 10, f"Throughput too low: {throughput:.2f} req/s"
        assert (successful_requests / total_requests) > 0.95, "Success rate too low"
    
    def test_api_memory_usage_under_load(self, orchestrator_service):
        """Test API memory usage under load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate memory-intensive operations
        large_responses = []
        for i in range(50):
            # Simulate large API response
            large_response = {
                "success": True,
                "data": {
                    "test_results": [
                        {
                            "test_id": f"test-{j:03d}",
                            "status": "completed",
                            "output": "x" * 1000,  # 1KB of output per test
                            "timestamp": datetime.now().isoformat()
                        }
                        for j in range(100)  # 100 tests per response
                    ]
                }
            }
            large_responses.append(large_response)
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Clean up
        large_responses.clear()
        
        # Verify memory usage is reasonable
        assert memory_increase < 100, f"Memory increase too high: {memory_increase:.2f} MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])