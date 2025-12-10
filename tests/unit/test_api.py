"""Unit tests for the REST API."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json

from api.main import app
from api.auth import USERS_DB, create_access_token


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # Use the test admin user
    user_data = USERS_DB["admin"]
    token = create_access_token(user_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def readonly_headers():
    """Create readonly user authentication headers."""
    user_data = USERS_DB["readonly"]
    token = create_access_token(user_data)
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check_public(self, client):
        """Test public health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["status"] in ["healthy", "degraded"]
    
    def test_health_detailed_requires_auth(self, client):
        """Test that detailed health check requires authentication."""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 401
    
    def test_health_detailed_with_auth(self, client, auth_headers):
        """Test detailed health check with authentication."""
        response = client.get("/api/v1/health/detailed", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "metrics" in data["data"]
        assert "components" in data["data"]


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_success(self, client):
        """Test successful login."""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user information."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user"]["username"] == "admin"
    
    def test_logout(self, client, auth_headers):
        """Test user logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True


class TestTestSubmission:
    """Test test submission endpoints."""
    
    def test_submit_test_requires_auth(self, client):
        """Test that test submission requires authentication."""
        test_data = {
            "test_cases": [{
                "name": "Test Network Driver",
                "description": "Test e1000e network driver functionality",
                "test_type": "unit",
                "target_subsystem": "networking",
                "test_script": "#!/bin/bash\necho 'test'"
            }],
            "priority": 5
        }
        response = client.post("/api/v1/tests/submit", json=test_data)
        assert response.status_code == 401
    
    def test_submit_test_success(self, client, auth_headers):
        """Test successful test submission."""
        test_data = {
            "test_cases": [{
                "name": "Test Network Driver",
                "description": "Test e1000e network driver functionality",
                "test_type": "unit",
                "target_subsystem": "networking",
                "test_script": "#!/bin/bash\necho 'test'",
                "execution_time_estimate": 120
            }],
            "priority": 5
        }
        response = client.post("/api/v1/tests/submit", json=test_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "submission_id" in data["data"]
        assert "test_case_ids" in data["data"]
        assert len(data["data"]["test_case_ids"]) == 1
    
    def test_submit_test_with_hardware_config(self, client, auth_headers):
        """Test test submission with hardware configuration."""
        test_data = {
            "test_cases": [{
                "name": "Test ARM Driver",
                "description": "Test driver on ARM architecture",
                "test_type": "integration",
                "target_subsystem": "drivers",
                "test_script": "#!/bin/bash\necho 'arm test'",
                "required_hardware": {
                    "architecture": "arm64",
                    "cpu_model": "ARM Cortex-A72",
                    "memory_mb": 2048,
                    "is_virtual": True,
                    "emulator": "qemu"
                }
            }],
            "priority": 3
        }
        response = client.post("/api/v1/tests/submit", json=test_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_list_tests(self, client, auth_headers):
        """Test listing submitted tests."""
        response = client.get("/api/v1/tests", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "tests" in data["data"]
        assert "pagination" in data["data"]
    
    def test_list_tests_with_filters(self, client, auth_headers):
        """Test listing tests with filters."""
        params = {
            "test_type": "unit",
            "page": 1,
            "page_size": 10
        }
        response = client.get("/api/v1/tests", params=params, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True


class TestStatusEndpoints:
    """Test status monitoring endpoints."""
    
    def test_get_execution_plan_status(self, client, auth_headers):
        """Test getting execution plan status."""
        # Use mock plan ID from status.py
        response = client.get("/api/v1/status/plans/plan-001", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "plan_id" in data["data"]
        assert "test_statuses" in data["data"]
    
    def test_get_test_execution_status(self, client, auth_headers):
        """Test getting individual test status."""
        # Use mock test ID from status.py
        response = client.get("/api/v1/status/tests/test-001", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "test_status" in data["data"]
    
    def test_get_active_executions(self, client, auth_headers):
        """Test getting active executions."""
        response = client.get("/api/v1/status/active", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "active_tests" in data["data"]
        assert "active_plans" in data["data"]


class TestResultsEndpoints:
    """Test results retrieval endpoints."""
    
    def test_get_test_result(self, client, auth_headers):
        """Test getting test result."""
        # Use mock test ID from results.py
        response = client.get("/api/v1/results/tests/test-001", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["test_id"] == "test-001"
        assert data["data"]["status"] == "passed"
    
    def test_get_test_result_not_found(self, client, auth_headers):
        """Test getting non-existent test result."""
        response = client.get("/api/v1/results/tests/nonexistent", headers=auth_headers)
        assert response.status_code == 404
    
    def test_list_test_results(self, client, auth_headers):
        """Test listing test results."""
        response = client.get("/api/v1/results/tests", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "results" in data["data"]
        assert "summary" in data["data"]
    
    def test_get_coverage_report(self, client, auth_headers):
        """Test getting coverage report."""
        response = client.get("/api/v1/results/coverage/test-001", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "line_coverage" in data["data"]
        assert "branch_coverage" in data["data"]
    
    def test_get_failure_analysis(self, client, auth_headers):
        """Test getting failure analysis."""
        response = client.get("/api/v1/results/failures/test-002", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "root_cause" in data["data"]
        assert "suggested_fixes" in data["data"]


class TestPermissions:
    """Test permission-based access control."""
    
    def test_readonly_user_cannot_submit_tests(self, client, readonly_headers):
        """Test that readonly user cannot submit tests."""
        test_data = {
            "test_cases": [{
                "name": "Test",
                "description": "Test description",
                "test_type": "unit",
                "target_subsystem": "test",
                "test_script": "echo test"
            }],
            "priority": 1
        }
        response = client.post("/api/v1/tests/submit", json=test_data, headers=readonly_headers)
        assert response.status_code == 403
    
    def test_readonly_user_can_read_results(self, client, readonly_headers):
        """Test that readonly user can read results."""
        response = client.get("/api/v1/results/tests", headers=readonly_headers)
        assert response.status_code == 200
    
    def test_readonly_user_cannot_delete_tests(self, client, readonly_headers):
        """Test that readonly user cannot delete tests."""
        response = client.delete("/api/v1/tests/test-001", headers=readonly_headers)
        assert response.status_code == 403


class TestAPIValidation:
    """Test API input validation."""
    
    def test_invalid_test_type(self, client, auth_headers):
        """Test submission with invalid test type."""
        test_data = {
            "test_cases": [{
                "name": "Test",
                "description": "Test description",
                "test_type": "invalid_type",
                "target_subsystem": "test",
                "test_script": "echo test"
            }],
            "priority": 1
        }
        response = client.post("/api/v1/tests/submit", json=test_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_architecture(self, client, auth_headers):
        """Test submission with invalid architecture."""
        test_data = {
            "test_cases": [{
                "name": "Test",
                "description": "Test description", 
                "test_type": "unit",
                "target_subsystem": "test",
                "test_script": "echo test",
                "required_hardware": {
                    "architecture": "invalid_arch",
                    "cpu_model": "Test CPU",
                    "memory_mb": 1024
                }
            }],
            "priority": 1
        }
        response = client.post("/api/v1/tests/submit", json=test_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error
    
    def test_negative_memory(self, client, auth_headers):
        """Test submission with negative memory."""
        test_data = {
            "test_cases": [{
                "name": "Test",
                "description": "Test description",
                "test_type": "unit", 
                "target_subsystem": "test",
                "test_script": "echo test",
                "required_hardware": {
                    "architecture": "x86_64",
                    "cpu_model": "Test CPU",
                    "memory_mb": -1024
                }
            }],
            "priority": 1
        }
        response = client.post("/api/v1/tests/submit", json=test_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error