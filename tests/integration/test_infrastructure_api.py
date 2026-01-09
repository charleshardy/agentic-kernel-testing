"""
Integration tests for Infrastructure Management API endpoints.

Tests the complete API workflow for build servers, hosts, boards, and pipelines.

**Feature: test-infrastructure-management**
**Validates: Requirements 1.1-1.5, 2.1-2.5, 7.1-7.5, 8.1-8.5, 9.1-9.5, 10.1-10.5, 17.1-17.5, 18.1-18.5**
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Import the FastAPI app
from api.routers.infrastructure import router, ResourceStatus, BoardStatus, PowerControlMethod


@pytest.fixture
def test_client():
    """Create test client for infrastructure API."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def sample_build_server_registration() -> Dict[str, Any]:
    """Sample build server registration data."""
    return {
        "hostname": "build-server-01",
        "ip_address": "192.168.1.100",
        "ssh_port": 22,
        "ssh_username": "builder",
        "ssh_key_path": "/home/builder/.ssh/id_rsa",
        "supported_architectures": ["x86_64", "arm64"],
        "max_concurrent_builds": 4,
        "labels": {"team": "kernel", "location": "datacenter-1"}
    }


@pytest.fixture
def sample_host_registration() -> Dict[str, Any]:
    """Sample QEMU host registration data."""
    return {
        "hostname": "qemu-host-01",
        "ip_address": "192.168.1.110",
        "ssh_port": 22,
        "ssh_username": "qemu",
        "ssh_key_path": "/home/qemu/.ssh/id_rsa",
        "architecture": "x86_64",
        "total_cpu_cores": 32,
        "total_memory_mb": 65536,
        "total_storage_gb": 1000,
        "max_vms": 20,
        "labels": {"team": "testing", "kvm": "enabled"}
    }


@pytest.fixture
def sample_board_registration() -> Dict[str, Any]:
    """Sample physical board registration data."""
    return {
        "name": "rpi4-board-01",
        "board_type": "raspberry_pi_4",
        "serial_number": "SN123456789",
        "architecture": "arm64",
        "ip_address": "192.168.1.150",
        "ssh_port": 22,
        "ssh_username": "pi",
        "serial_device": "/dev/ttyUSB0",
        "power_control": {
            "method": "usb_hub",
            "usb_hub_port": 1
        },
        "peripherals": ["gpio", "i2c", "spi", "uart"],
        "labels": {"team": "bsp", "location": "lab-1"}
    }


@pytest.fixture
def sample_pipeline_creation() -> Dict[str, Any]:
    """Sample pipeline creation data."""
    return {
        "name": "kernel-test-pipeline",
        "source_repository": "https://github.com/example/linux-kernel",
        "branch": "main",
        "commit_hash": "abc123def456",
        "target_architecture": "x86_64",
        "environment_type": "qemu",
        "environment_config": {"memory_mb": 2048, "cpu_cores": 4},
        "auto_retry": True
    }


@pytest.mark.integration
class TestBuildServerAPI:
    """Test build server API endpoints."""

    def test_register_build_server(self, test_client, sample_build_server_registration):
        """Test build server registration endpoint.
        
        **Requirement 1.1**: Register build servers with hostname, IP, SSH credentials
        **Requirement 1.2**: Validate SSH connectivity and toolchain availability
        """
        response = test_client.post(
            "/api/v1/infrastructure/build-servers",
            json=sample_build_server_registration
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["hostname"] == sample_build_server_registration["hostname"]
        assert data["ip_address"] == sample_build_server_registration["ip_address"]
        assert data["status"] == "online"
        assert "id" in data
        assert "created_at" in data

    def test_list_build_servers(self, test_client):
        """Test listing build servers.
        
        **Requirement 2.1**: Display all registered build servers with status
        """
        response = test_client.get("/api/v1/infrastructure/build-servers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_build_servers_with_filters(self, test_client):
        """Test listing build servers with status and architecture filters."""
        response = test_client.get(
            "/api/v1/infrastructure/build-servers",
            params={"status": "online", "architecture": "x86_64"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_build_server_not_found(self, test_client):
        """Test getting non-existent build server returns 404."""
        response = test_client.get("/api/v1/infrastructure/build-servers/nonexistent-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


    def test_get_build_server_status_not_found(self, test_client):
        """Test getting status of non-existent build server."""
        response = test_client.get("/api/v1/infrastructure/build-servers/nonexistent-id/status")
        
        assert response.status_code == 404

    def test_get_build_server_capacity_not_found(self, test_client):
        """Test getting capacity of non-existent build server."""
        response = test_client.get("/api/v1/infrastructure/build-servers/nonexistent-id/capacity")
        
        assert response.status_code == 404

    def test_set_build_server_maintenance_not_found(self, test_client):
        """Test setting maintenance mode on non-existent build server."""
        response = test_client.put(
            "/api/v1/infrastructure/build-servers/nonexistent-id/maintenance",
            params={"enabled": True}
        )
        
        assert response.status_code == 404

    def test_decommission_build_server_not_found(self, test_client):
        """Test decommissioning non-existent build server."""
        response = test_client.delete("/api/v1/infrastructure/build-servers/nonexistent-id")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestBuildJobAPI:
    """Test build job API endpoints."""

    def test_submit_build_job(self, test_client):
        """Test build job submission.
        
        **Requirement 3.1**: Submit build jobs with repository, branch, architecture
        **Requirement 3.2**: Auto-select server based on requirements
        """
        job_data = {
            "source_repository": "https://github.com/example/linux-kernel",
            "branch": "main",
            "commit_hash": "abc123",
            "target_architecture": "x86_64",
            "build_config": {"defconfig": "x86_64_defconfig"},
            "server_id": None  # Auto-select
        }
        
        response = test_client.post(
            "/api/v1/infrastructure/build-jobs",
            json=job_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["source_repository"] == job_data["source_repository"]
        assert data["branch"] == job_data["branch"]
        assert data["status"] == "queued"
        assert "id" in data


    def test_list_build_jobs(self, test_client):
        """Test listing build jobs.
        
        **Requirement 3.5**: Display build history with filtering
        """
        response = test_client.get("/api/v1/infrastructure/build-jobs")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_build_jobs_with_filters(self, test_client):
        """Test listing build jobs with filters."""
        response = test_client.get(
            "/api/v1/infrastructure/build-jobs",
            params={"status": "completed", "limit": 10}
        )
        
        assert response.status_code == 200

    def test_get_build_job_not_found(self, test_client):
        """Test getting non-existent build job."""
        response = test_client.get("/api/v1/infrastructure/build-jobs/nonexistent-id")
        
        assert response.status_code == 404

    def test_cancel_build_job_not_found(self, test_client):
        """Test canceling non-existent build job."""
        response = test_client.put("/api/v1/infrastructure/build-jobs/nonexistent-id/cancel")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestArtifactAPI:
    """Test artifact API endpoints."""

    def test_list_artifacts(self, test_client):
        """Test listing artifacts.
        
        **Requirement 4.3**: Display all builds with artifacts
        """
        response = test_client.get("/api/v1/infrastructure/artifacts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_artifacts_with_filters(self, test_client):
        """Test listing artifacts with filters."""
        response = test_client.get(
            "/api/v1/infrastructure/artifacts",
            params={"build_id": "build-001", "architecture": "x86_64"}
        )
        
        assert response.status_code == 200

    def test_get_latest_artifacts(self, test_client):
        """Test getting latest artifacts.
        
        **Requirement 4.5**: Retrieve by branch and "latest"
        """
        response = test_client.get(
            "/api/v1/infrastructure/artifacts/latest",
            params={"branch": "main", "architecture": "x86_64"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "artifacts" in data


    def test_get_artifact_not_found(self, test_client):
        """Test getting non-existent artifact."""
        response = test_client.get("/api/v1/infrastructure/artifacts/nonexistent-id")
        
        assert response.status_code == 404

    def test_download_artifact_not_found(self, test_client):
        """Test downloading non-existent artifact."""
        response = test_client.get("/api/v1/infrastructure/artifacts/nonexistent-id/download")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestHostAPI:
    """Test QEMU host API endpoints."""

    def test_register_host(self, test_client, sample_host_registration):
        """Test host registration.
        
        **Requirement 7.1**: Register hosts with hostname, IP, SSH credentials
        **Requirement 7.2**: Validate SSH and libvirt connectivity
        """
        response = test_client.post(
            "/api/v1/infrastructure/hosts",
            json=sample_host_registration
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["hostname"] == sample_host_registration["hostname"]
        assert data["ip_address"] == sample_host_registration["ip_address"]
        assert data["architecture"] == sample_host_registration["architecture"]
        assert data["status"] == "online"
        assert "id" in data

    def test_list_hosts(self, test_client):
        """Test listing hosts.
        
        **Requirement 9.1**: Display all hosts with status and utilization
        """
        response = test_client.get("/api/v1/infrastructure/hosts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_hosts_with_filters(self, test_client):
        """Test listing hosts with filters."""
        response = test_client.get(
            "/api/v1/infrastructure/hosts",
            params={"status": "online", "architecture": "x86_64"}
        )
        
        assert response.status_code == 200

    def test_get_host_not_found(self, test_client):
        """Test getting non-existent host."""
        response = test_client.get("/api/v1/infrastructure/hosts/nonexistent-id")
        
        assert response.status_code == 404


    def test_get_host_vms_not_found(self, test_client):
        """Test getting VMs of non-existent host."""
        response = test_client.get("/api/v1/infrastructure/hosts/nonexistent-id/vms")
        
        assert response.status_code == 404

    def test_set_host_maintenance_not_found(self, test_client):
        """Test setting maintenance mode on non-existent host."""
        response = test_client.put(
            "/api/v1/infrastructure/hosts/nonexistent-id/maintenance",
            params={"enabled": True}
        )
        
        assert response.status_code == 404

    def test_decommission_host_not_found(self, test_client):
        """Test decommissioning non-existent host."""
        response = test_client.delete("/api/v1/infrastructure/hosts/nonexistent-id")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestBoardAPI:
    """Test physical board API endpoints."""

    def test_register_board(self, test_client, sample_board_registration):
        """Test board registration.
        
        **Requirement 8.1**: Register boards with type, serial, connection method
        **Requirement 8.4**: Specify power control method
        """
        response = test_client.post(
            "/api/v1/infrastructure/boards",
            json=sample_board_registration
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_board_registration["name"]
        assert data["board_type"] == sample_board_registration["board_type"]
        assert data["architecture"] == sample_board_registration["architecture"]
        assert data["status"] == "available"
        assert "id" in data

    def test_list_boards(self, test_client):
        """Test listing boards.
        
        **Requirement 10.1**: Display all boards with status and health
        """
        response = test_client.get("/api/v1/infrastructure/boards")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_boards_with_filters(self, test_client):
        """Test listing boards with filters."""
        response = test_client.get(
            "/api/v1/infrastructure/boards",
            params={"status": "available", "architecture": "arm64", "board_type": "raspberry_pi_4"}
        )
        
        assert response.status_code == 200


    def test_get_board_not_found(self, test_client):
        """Test getting non-existent board."""
        response = test_client.get("/api/v1/infrastructure/boards/nonexistent-id")
        
        assert response.status_code == 404

    def test_get_board_health_not_found(self, test_client):
        """Test getting health of non-existent board."""
        response = test_client.get("/api/v1/infrastructure/boards/nonexistent-id/health")
        
        assert response.status_code == 404

    def test_power_cycle_board_not_found(self, test_client):
        """Test power cycling non-existent board."""
        response = test_client.post("/api/v1/infrastructure/boards/nonexistent-id/power-cycle")
        
        assert response.status_code == 404

    def test_flash_board_not_found(self, test_client):
        """Test flashing non-existent board."""
        response = test_client.post(
            "/api/v1/infrastructure/boards/nonexistent-id/flash",
            params={"firmware_path": "/path/to/firmware.bin"}
        )
        
        assert response.status_code == 404

    def test_set_board_maintenance_not_found(self, test_client):
        """Test setting maintenance mode on non-existent board."""
        response = test_client.put(
            "/api/v1/infrastructure/boards/nonexistent-id/maintenance",
            params={"enabled": True}
        )
        
        assert response.status_code == 404

    def test_decommission_board_not_found(self, test_client):
        """Test decommissioning non-existent board."""
        response = test_client.delete("/api/v1/infrastructure/boards/nonexistent-id")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestPipelineAPI:
    """Test pipeline API endpoints."""

    def test_create_pipeline(self, test_client, sample_pipeline_creation):
        """Test pipeline creation.
        
        **Requirement 17.1**: Accept source repo, branch, architecture, environment
        """
        response = test_client.post(
            "/api/v1/infrastructure/pipelines",
            json=sample_pipeline_creation
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["source_repository"] == sample_pipeline_creation["source_repository"]
        assert data["branch"] == sample_pipeline_creation["branch"]
        assert data["status"] == "pending"
        assert len(data["stages"]) == 4  # build, deploy, boot, test
        assert "id" in data


    def test_pipeline_stages_order(self, test_client, sample_pipeline_creation):
        """Test pipeline stages are in correct order.
        
        **Requirement 17.2**: Execute stages in order: build → deploy → boot → test
        """
        response = test_client.post(
            "/api/v1/infrastructure/pipelines",
            json=sample_pipeline_creation
        )
        
        assert response.status_code == 200
        data = response.json()
        stage_names = [s["name"] for s in data["stages"]]
        assert stage_names == ["build", "deploy", "boot", "test"]

    def test_list_pipelines(self, test_client):
        """Test listing pipelines.
        
        **Requirement 17.5**: Display pipeline history
        """
        response = test_client.get("/api/v1/infrastructure/pipelines")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_pipelines_with_filters(self, test_client):
        """Test listing pipelines with filters."""
        response = test_client.get(
            "/api/v1/infrastructure/pipelines",
            params={"status": "completed", "limit": 10}
        )
        
        assert response.status_code == 200

    def test_get_pipeline_not_found(self, test_client):
        """Test getting non-existent pipeline."""
        response = test_client.get("/api/v1/infrastructure/pipelines/nonexistent-id")
        
        assert response.status_code == 404

    def test_get_pipeline_stage_logs_not_found(self, test_client):
        """Test getting logs of non-existent pipeline."""
        response = test_client.get("/api/v1/infrastructure/pipelines/nonexistent-id/logs/build")
        
        assert response.status_code == 404

    def test_cancel_pipeline_not_found(self, test_client):
        """Test canceling non-existent pipeline."""
        response = test_client.put("/api/v1/infrastructure/pipelines/nonexistent-id/cancel")
        
        assert response.status_code == 404

    def test_retry_pipeline_stage_not_found(self, test_client):
        """Test retrying stage of non-existent pipeline."""
        response = test_client.post("/api/v1/infrastructure/pipelines/nonexistent-id/retry/build")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestDashboardAPI:
    """Test dashboard/overview API endpoints."""

    def test_get_infrastructure_overview(self, test_client):
        """Test infrastructure overview endpoint.
        
        **Requirement 15.1-15.4**: Display resource counts and health summary
        """
        response = test_client.get("/api/v1/infrastructure/overview")
        
        assert response.status_code == 200
        data = response.json()
        assert "build_servers" in data
        assert "hosts" in data
        assert "boards" in data
        assert "active_builds" in data
        assert "active_pipelines" in data

    def test_get_infrastructure_alerts(self, test_client):
        """Test infrastructure alerts endpoint.
        
        **Requirement 16.1-16.5**: Display alerts with filtering
        """
        response = test_client.get("/api/v1/infrastructure/alerts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_infrastructure_alerts_with_filters(self, test_client):
        """Test infrastructure alerts with filters."""
        response = test_client.get(
            "/api/v1/infrastructure/alerts",
            params={"severity": "critical", "resource_type": "host", "limit": 10}
        )
        
        assert response.status_code == 200

    def test_acknowledge_alert_not_found(self, test_client):
        """Test acknowledging non-existent alert."""
        response = test_client.put(
            "/api/v1/infrastructure/alerts/nonexistent-id/acknowledge",
            params={"acknowledged_by": "admin"}
        )
        
        assert response.status_code == 404


@pytest.mark.integration
class TestInfrastructureWorkflows:
    """Test complete infrastructure workflows."""

    def test_build_server_registration_workflow(self, test_client, sample_build_server_registration):
        """Test complete build server registration workflow."""
        # Step 1: Register build server
        response = test_client.post(
            "/api/v1/infrastructure/build-servers",
            json=sample_build_server_registration
        )
        assert response.status_code == 200
        server_data = response.json()
        
        # Verify registration response
        assert server_data["status"] == "online"
        assert server_data["hostname"] == sample_build_server_registration["hostname"]
        assert "supported_architectures" in server_data

    def test_host_registration_workflow(self, test_client, sample_host_registration):
        """Test complete host registration workflow."""
        # Step 1: Register host
        response = test_client.post(
            "/api/v1/infrastructure/hosts",
            json=sample_host_registration
        )
        assert response.status_code == 200
        host_data = response.json()
        
        # Verify registration response
        assert host_data["status"] == "online"
        assert host_data["total_cpu_cores"] == sample_host_registration["total_cpu_cores"]
        assert host_data["total_memory_mb"] == sample_host_registration["total_memory_mb"]


    def test_board_registration_workflow(self, test_client, sample_board_registration):
        """Test complete board registration workflow."""
        # Step 1: Register board
        response = test_client.post(
            "/api/v1/infrastructure/boards",
            json=sample_board_registration
        )
        assert response.status_code == 200
        board_data = response.json()
        
        # Verify registration response
        assert board_data["status"] == "available"
        assert board_data["board_type"] == sample_board_registration["board_type"]
        assert board_data["power_control"]["method"] == sample_board_registration["power_control"]["method"]

    def test_pipeline_creation_workflow(self, test_client, sample_pipeline_creation):
        """Test complete pipeline creation workflow.
        
        **Requirement 17.1-17.5**: Pipeline creation and stage sequencing
        """
        # Step 1: Create pipeline
        response = test_client.post(
            "/api/v1/infrastructure/pipelines",
            json=sample_pipeline_creation
        )
        assert response.status_code == 200
        pipeline_data = response.json()
        
        # Verify pipeline structure
        assert pipeline_data["status"] == "pending"
        assert len(pipeline_data["stages"]) == 4
        
        # Verify stage order
        expected_stages = ["build", "deploy", "boot", "test"]
        actual_stages = [s["name"] for s in pipeline_data["stages"]]
        assert actual_stages == expected_stages
        
        # Verify all stages start as pending
        for stage in pipeline_data["stages"]:
            assert stage["status"] == "pending"

    def test_build_job_submission_workflow(self, test_client):
        """Test complete build job submission workflow.
        
        **Requirement 3.1-3.5**: Build job submission and tracking
        """
        job_data = {
            "source_repository": "https://github.com/example/linux-kernel",
            "branch": "feature/new-driver",
            "commit_hash": "def456abc789",
            "target_architecture": "arm64",
            "build_config": {
                "defconfig": "arm64_defconfig",
                "extra_options": ["CONFIG_DEBUG_INFO=y"]
            },
            "server_id": None  # Auto-select
        }
        
        # Step 1: Submit build job
        response = test_client.post(
            "/api/v1/infrastructure/build-jobs",
            json=job_data
        )
        assert response.status_code == 200
        job_response = response.json()
        
        # Verify job submission
        assert job_response["status"] == "queued"
        assert job_response["target_architecture"] == "arm64"
        assert "id" in job_response


@pytest.mark.integration
class TestAPIValidation:
    """Test API input validation."""

    def test_build_server_registration_missing_required_fields(self, test_client):
        """Test build server registration with missing required fields."""
        incomplete_data = {
            "hostname": "test-server"
            # Missing ip_address, ssh_username, supported_architectures
        }
        
        response = test_client.post(
            "/api/v1/infrastructure/build-servers",
            json=incomplete_data
        )
        
        assert response.status_code == 422  # Validation error


    def test_host_registration_missing_required_fields(self, test_client):
        """Test host registration with missing required fields."""
        incomplete_data = {
            "hostname": "test-host"
            # Missing ip_address, ssh_username, architecture, cpu/memory/storage
        }
        
        response = test_client.post(
            "/api/v1/infrastructure/hosts",
            json=incomplete_data
        )
        
        assert response.status_code == 422

    def test_board_registration_missing_required_fields(self, test_client):
        """Test board registration with missing required fields."""
        incomplete_data = {
            "name": "test-board"
            # Missing board_type, architecture, power_control
        }
        
        response = test_client.post(
            "/api/v1/infrastructure/boards",
            json=incomplete_data
        )
        
        assert response.status_code == 422

    def test_pipeline_creation_missing_required_fields(self, test_client):
        """Test pipeline creation with missing required fields."""
        incomplete_data = {
            "name": "test-pipeline"
            # Missing source_repository, branch, target_architecture, environment_type
        }
        
        response = test_client.post(
            "/api/v1/infrastructure/pipelines",
            json=incomplete_data
        )
        
        assert response.status_code == 422

    def test_build_job_submission_missing_required_fields(self, test_client):
        """Test build job submission with missing required fields."""
        incomplete_data = {
            "branch": "main"
            # Missing source_repository, target_architecture
        }
        
        response = test_client.post(
            "/api/v1/infrastructure/build-jobs",
            json=incomplete_data
        )
        
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
