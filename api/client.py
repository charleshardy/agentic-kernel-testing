"""Advanced Python client for the Agentic AI Testing System API."""

import requests
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union, Iterator
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestCase:
    """Test case data structure."""
    name: str
    description: str
    test_type: str
    target_subsystem: str
    test_script: str
    execution_time_estimate: int = 120
    code_paths: List[str] = None
    required_hardware: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    priority: int = 0
    
    def __post_init__(self):
        if self.code_paths is None:
            self.code_paths = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API submission."""
        return {
            "name": self.name,
            "description": self.description,
            "test_type": self.test_type,
            "target_subsystem": self.target_subsystem,
            "test_script": self.test_script,
            "execution_time_estimate": self.execution_time_estimate,
            "code_paths": self.code_paths,
            "required_hardware": self.required_hardware,
            "metadata": self.metadata
        }


class APIError(Exception):
    """API-specific exception."""
    
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class AgenticTestingClient:
    """Advanced client for the Agentic AI Testing System API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize the API client.
        
        Args:
            base_url: Base URL of the API server
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        self.session = requests.Session()
        self.session.timeout = timeout
        
        self.token = None
        self.user_info = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        files: Dict = None,
        stream: bool = False
    ) -> requests.Response:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    files=files,
                    stream=stream
                )
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                # Raise for HTTP errors
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    raise APIError(f"Request failed after {self.retry_attempts} attempts: {str(e)}")
                
                self.logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        raise APIError("Max retry attempts exceeded")
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and extract data."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response from server")
        
        if not data.get("success", False):
            error_msg = data.get("message", "Unknown API error")
            errors = data.get("errors", [])
            if errors:
                error_msg += f": {', '.join(errors)}"
            
            raise APIError(
                error_msg,
                status_code=response.status_code,
                response_data=data
            )
        
        return data.get("data", {})
    
    # Authentication methods
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and store authentication token."""
        response = self._make_request(
            "POST",
            "/api/v1/auth/login",
            data={"username": username, "password": password}
        )
        
        data = self._handle_response(response)
        
        self.token = data["access_token"]
        self.user_info = data["user_info"]
        
        # Update session headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
        
        self.logger.info(f"Successfully logged in as {username}")
        return data
    
    def logout(self) -> bool:
        """Logout and clear authentication."""
        if not self.token:
            return True
        
        try:
            response = self._make_request("POST", "/api/v1/auth/logout")
            self._handle_response(response)
        except APIError:
            pass  # Ignore logout errors
        
        # Clear authentication
        self.token = None
        self.user_info = None
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        self.logger.info("Successfully logged out")
        return True
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user information."""
        response = self._make_request("GET", "/api/v1/auth/me")
        return self._handle_response(response)
    
    def create_api_key(self, description: str = "") -> str:
        """Create a long-lived API key."""
        response = self._make_request(
            "POST",
            "/api/v1/auth/api-key",
            data={"description": description}
        )
        data = self._handle_response(response)
        return data["api_key"]
    
    # Health and status methods
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self._make_request("GET", "/api/v1/health")
        return self._handle_response(response)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        response = self._make_request("GET", "/api/v1/health/metrics")
        return self._handle_response(response)
    
    # Test management methods
    
    def submit_test(self, test_case: TestCase, priority: int = 0) -> Dict[str, Any]:
        """Submit a single test case."""
        return self.submit_tests([test_case], priority)
    
    def submit_tests(
        self,
        test_cases: List[TestCase],
        priority: int = 0,
        webhook_url: str = None,
        target_environments: List[str] = None
    ) -> Dict[str, Any]:
        """Submit multiple test cases for execution."""
        payload = {
            "test_cases": [tc.to_dict() for tc in test_cases],
            "priority": priority
        }
        
        if webhook_url:
            payload["webhook_url"] = webhook_url
        if target_environments:
            payload["target_environments"] = target_environments
        
        response = self._make_request("POST", "/api/v1/tests/submit", data=payload)
        return self._handle_response(response)
    
    def list_tests(
        self,
        page: int = 1,
        page_size: int = 20,
        test_type: str = None,
        subsystem: str = None,
        status: str = None
    ) -> Dict[str, Any]:
        """List submitted test cases."""
        params = {"page": page, "page_size": page_size}
        if test_type:
            params["test_type"] = test_type
        if subsystem:
            params["subsystem"] = subsystem
        if status:
            params["status"] = status
        
        response = self._make_request("GET", "/api/v1/tests", params=params)
        return self._handle_response(response)
    
    def get_test(self, test_id: str) -> Dict[str, Any]:
        """Get details of a specific test case."""
        response = self._make_request("GET", f"/api/v1/tests/{test_id}")
        return self._handle_response(response)
    
    def delete_test(self, test_id: str) -> bool:
        """Delete a test case."""
        response = self._make_request("DELETE", f"/api/v1/tests/{test_id}")
        self._handle_response(response)
        return True
    
    def analyze_code(
        self,
        repository_url: str,
        commit_sha: str = None,
        branch: str = "main",
        diff_content: str = None,
        webhook_url: str = None
    ) -> Dict[str, Any]:
        """Analyze code changes and get test recommendations."""
        payload = {
            "repository_url": repository_url,
            "branch": branch
        }
        
        if commit_sha:
            payload["commit_sha"] = commit_sha
        if diff_content:
            payload["diff_content"] = diff_content
        if webhook_url:
            payload["webhook_url"] = webhook_url
        
        response = self._make_request("POST", "/api/v1/tests/analyze-code", data=payload)
        return self._handle_response(response)
    
    # Status monitoring methods
    
    def get_execution_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """Get execution plan status."""
        response = self._make_request("GET", f"/api/v1/status/plans/{plan_id}")
        return self._handle_response(response)
    
    def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """Get test execution status."""
        response = self._make_request("GET", f"/api/v1/status/tests/{test_id}")
        return self._handle_response(response)
    
    def get_active_executions(self) -> Dict[str, Any]:
        """Get all active test executions."""
        response = self._make_request("GET", "/api/v1/status/active")
        return self._handle_response(response)
    
    def cancel_test(self, test_id: str) -> bool:
        """Cancel a running test execution."""
        response = self._make_request("POST", f"/api/v1/status/cancel/{test_id}")
        self._handle_response(response)
        return True
    
    def wait_for_completion(
        self,
        plan_id: str,
        timeout: int = 3600,
        poll_interval: int = 30
    ) -> Dict[str, Any]:
        """Wait for execution plan to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_execution_plan_status(plan_id)
            
            if status["overall_status"] in ["completed", "failed", "cancelled"]:
                return status
            
            self.logger.info(
                f"Plan {plan_id}: {status['overall_status']} "
                f"({status['completed_tests']}/{status['total_tests']} tests)"
            )
            
            time.sleep(poll_interval)
        
        raise APIError(f"Execution plan {plan_id} did not complete within {timeout} seconds")
    
    # Results methods
    
    def get_test_result(self, test_id: str) -> Dict[str, Any]:
        """Get detailed test result."""
        response = self._make_request("GET", f"/api/v1/results/tests/{test_id}")
        return self._handle_response(response)
    
    def list_test_results(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: str = None,
        subsystem: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """List test results with filtering."""
        params = {"page": page, "page_size": page_size}
        if status_filter:
            params["status_filter"] = status_filter
        if subsystem:
            params["subsystem"] = subsystem
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = self._make_request("GET", "/api/v1/results/tests", params=params)
        return self._handle_response(response)
    
    def get_coverage_report(self, test_id: str) -> Dict[str, Any]:
        """Get coverage report for a test."""
        response = self._make_request("GET", f"/api/v1/results/coverage/{test_id}")
        return self._handle_response(response)
    
    def get_failure_analysis(self, test_id: str) -> Dict[str, Any]:
        """Get failure analysis for a failed test."""
        response = self._make_request("GET", f"/api/v1/results/failures/{test_id}")
        return self._handle_response(response)
    
    def download_artifacts(
        self,
        test_id: str,
        artifact_type: str,
        output_path: Union[str, Path] = None
    ) -> bytes:
        """Download test artifacts."""
        params = {"artifact_type": artifact_type}
        response = self._make_request(
            "GET",
            f"/api/v1/results/artifacts/{test_id}",
            params=params,
            stream=True
        )
        
        content = response.content
        
        if output_path:
            Path(output_path).write_bytes(content)
            self.logger.info(f"Artifacts saved to {output_path}")
        
        return content
    
    def export_results(
        self,
        format: str = "json",
        test_ids: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        output_path: Union[str, Path] = None
    ) -> bytes:
        """Export test results in various formats."""
        params = {"format": format}
        if test_ids:
            params["test_ids"] = ",".join(test_ids)
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = self._make_request(
            "GET",
            "/api/v1/results/export",
            params=params,
            stream=True
        )
        
        content = response.content
        
        if output_path:
            Path(output_path).write_bytes(content)
            self.logger.info(f"Results exported to {output_path}")
        
        return content
    
    def get_results_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary statistics for test results."""
        params = {"days": days}
        response = self._make_request("GET", "/api/v1/results/summary", params=params)
        return self._handle_response(response)
    
    # Environment methods
    
    def list_environments(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: str = None,
        architecture: str = None,
        is_virtual: bool = None
    ) -> Dict[str, Any]:
        """List available test environments."""
        params = {"page": page, "page_size": page_size}
        if status_filter:
            params["status_filter"] = status_filter
        if architecture:
            params["architecture"] = architecture
        if is_virtual is not None:
            params["is_virtual"] = is_virtual
        
        response = self._make_request("GET", "/api/v1/environments", params=params)
        return self._handle_response(response)
    
    def get_environment(self, env_id: str) -> Dict[str, Any]:
        """Get detailed environment information."""
        response = self._make_request("GET", f"/api/v1/environments/{env_id}")
        return self._handle_response(response)
    
    def create_environment(self, hardware_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test environment."""
        response = self._make_request("POST", "/api/v1/environments", data=hardware_config)
        return self._handle_response(response)
    
    def delete_environment(self, env_id: str, force: bool = False) -> bool:
        """Delete a test environment."""
        params = {"force": force} if force else {}
        response = self._make_request("DELETE", f"/api/v1/environments/{env_id}", params=params)
        self._handle_response(response)
        return True
    
    def reset_environment(self, env_id: str) -> Dict[str, Any]:
        """Reset an environment to clean state."""
        response = self._make_request("POST", f"/api/v1/environments/{env_id}/reset")
        return self._handle_response(response)
    
    def get_environment_stats(self) -> Dict[str, Any]:
        """Get overall environment statistics."""
        response = self._make_request("GET", "/api/v1/environments/stats")
        return self._handle_response(response)
    
    # Utility methods
    
    def iterate_results(
        self,
        page_size: int = 50,
        **filters
    ) -> Iterator[Dict[str, Any]]:
        """Iterate through all test results with pagination."""
        page = 1
        
        while True:
            results = self.list_test_results(page=page, page_size=page_size, **filters)
            
            for result in results["results"]:
                yield result
            
            # Check if there are more pages
            pagination = results["pagination"]
            if not pagination.get("has_next", False):
                break
            
            page += 1
    
    def wait_and_get_results(
        self,
        plan_id: str,
        timeout: int = 3600,
        poll_interval: int = 30
    ) -> List[Dict[str, Any]]:
        """Wait for execution to complete and return all results."""
        # Wait for completion
        final_status = self.wait_for_completion(plan_id, timeout, poll_interval)
        
        # Get all test results
        results = []
        for test_status in final_status["test_statuses"]:
            test_id = test_status["test_id"]
            try:
                result = self.get_test_result(test_id)
                results.append(result)
            except APIError as e:
                self.logger.warning(f"Failed to get result for test {test_id}: {e}")
        
        return results
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()