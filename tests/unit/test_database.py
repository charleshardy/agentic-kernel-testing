"""Unit tests for database layer."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ai_generator.models import (
    TestCase, TestResult, Environment, CoverageData, 
    TestType, TestStatus, EnvironmentStatus, HardwareConfig
)
from database.models import (
    TestCaseModel, TestResultModel, EnvironmentModel,
    CoverageDataModel, HardwareConfigModel
)
from database.repositories import (
    TestCaseRepository, TestResultRepository, EnvironmentRepository,
    CoverageRepository, HardwareConfigRepository
)
from database.migrations import MigrationManager, InitialMigration
from database.utils import DatabaseService


class TestHardwareConfigModel:
    """Test hardware configuration model."""
    
    def test_to_domain_model(self):
        """Test conversion to domain model."""
        hw_model = HardwareConfigModel(
            architecture="x86_64",
            cpu_model="Intel i7",
            memory_mb=8192,
            storage_type="ssd",
            peripherals=[{"name": "eth0", "type": "network"}],
            is_virtual=True,
            emulator="qemu"
        )
        
        domain_model = hw_model.to_domain_model()
        
        assert domain_model.architecture == "x86_64"
        assert domain_model.cpu_model == "Intel i7"
        assert domain_model.memory_mb == 8192
        assert domain_model.is_virtual is True
        assert len(domain_model.peripherals) == 1
    
    def test_from_domain_model(self):
        """Test creation from domain model."""
        hw_config = HardwareConfig(
            architecture="arm64",
            cpu_model="ARM Cortex-A72",
            memory_mb=4096,
            storage_type="emmc",
            is_virtual=False
        )
        
        hw_model = HardwareConfigModel.from_domain_model(hw_config)
        
        assert hw_model.architecture == "arm64"
        assert hw_model.cpu_model == "ARM Cortex-A72"
        assert hw_model.memory_mb == 4096
        assert hw_model.is_virtual is False


class TestTestCaseModel:
    """Test test case model."""
    
    def test_to_domain_model(self):
        """Test conversion to domain model."""
        hw_model = HardwareConfigModel(
            architecture="x86_64",
            cpu_model="Intel i7",
            memory_mb=8192
        )
        
        test_model = TestCaseModel(
            id="test-001",
            name="Test Memory Allocation",
            description="Test kernel memory allocation",
            test_type=TestType.UNIT,
            target_subsystem="memory",
            code_paths=["mm/page_alloc.c"],
            execution_time_estimate=120,
            test_script="#!/bin/bash\necho 'test'",
            hardware_config=hw_model
        )
        
        domain_model = test_model.to_domain_model()
        
        assert domain_model.id == "test-001"
        assert domain_model.name == "Test Memory Allocation"
        assert domain_model.test_type == TestType.UNIT
        assert domain_model.target_subsystem == "memory"
        assert domain_model.required_hardware is not None
        assert domain_model.required_hardware.architecture == "x86_64"
    
    def test_from_domain_model(self):
        """Test creation from domain model."""
        hw_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel i7",
            memory_mb=8192
        )
        
        test_case = TestCase(
            id="test-002",
            name="Test Network Stack",
            description="Test network protocol handling",
            test_type=TestType.INTEGRATION,
            target_subsystem="network",
            required_hardware=hw_config
        )
        
        test_model = TestCaseModel.from_domain_model(test_case)
        
        assert test_model.id == "test-002"
        assert test_model.name == "Test Network Stack"
        assert test_model.test_type == TestType.INTEGRATION
        assert test_model.target_subsystem == "network"


class TestRepositories:
    """Test repository classes."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        return Mock()
    
    def test_hardware_config_repository(self, mock_session):
        """Test hardware config repository."""
        repo = HardwareConfigRepository(mock_session)
        
        # Test create
        hw_config = HardwareConfigModel(
            architecture="x86_64",
            cpu_model="Intel i7",
            memory_mb=8192
        )
        
        result = repo.create(hw_config)
        
        mock_session.add.assert_called_once_with(hw_config)
        mock_session.flush.assert_called_once()
        assert result == hw_config
    
    def test_test_case_repository_search(self, mock_session):
        """Test test case repository search."""
        repo = TestCaseRepository(mock_session)
        
        # Mock query chain
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        results = repo.search("memory")
        
        mock_session.query.assert_called_once_with(TestCaseModel)
        mock_query.filter.assert_called_once()
        mock_query.all.assert_called_once()
        assert results == []
    
    def test_environment_repository_status_update(self, mock_session):
        """Test environment status update."""
        repo = EnvironmentRepository(mock_session)
        
        # Mock environment
        mock_env = Mock()
        mock_env.status = EnvironmentStatus.IDLE
        mock_session.query.return_value.filter.return_value.first.return_value = mock_env
        
        result = repo.update_status("env-001", EnvironmentStatus.BUSY)
        
        assert result is True
        assert mock_env.status == EnvironmentStatus.BUSY
        assert isinstance(mock_env.last_used, datetime)


class TestMigrations:
    """Test migration system."""
    
    def test_initial_migration(self):
        """Test initial migration."""
        migration = InitialMigration()
        
        assert migration.version == "001"
        assert migration.name == "initial_schema"
        assert "initial" in migration.description.lower()
    
    def test_migration_checksum(self):
        """Test migration checksum generation."""
        migration = InitialMigration()
        
        checksum1 = migration.get_checksum()
        checksum2 = migration.get_checksum()
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex length
    
    @patch('database.migrations.get_db_manager')
    def test_migration_manager_status(self, mock_get_db_manager):
        """Test migration manager status."""
        # Mock database manager and session
        mock_db_manager = Mock()
        mock_session = Mock()
        mock_context_manager = Mock()
        mock_context_manager.__enter__.return_value = mock_session
        mock_context_manager.__exit__.return_value = None
        mock_db_manager.session_scope.return_value = mock_context_manager
        mock_get_db_manager.return_value = mock_db_manager
        
        # Mock migration records
        mock_session.query.return_value.first.return_value = None  # No migration table
        mock_session.query.return_value.all.return_value = []  # No applied migrations
        
        manager = MigrationManager()
        status = manager.status()
        
        assert 'total_migrations' in status
        assert 'applied_count' in status
        assert 'pending_count' in status
        assert status['total_migrations'] > 0


class TestDatabaseService:
    """Test database service."""
    
    @patch('database.utils.get_db_manager')
    def test_health_check_healthy(self, mock_get_db_manager):
        """Test healthy database check."""
        # Mock database manager
        mock_db_manager = Mock()
        mock_session = Mock()
        mock_context_manager = Mock()
        mock_context_manager.__enter__.return_value = mock_session
        mock_context_manager.__exit__.return_value = None
        mock_db_manager.session_scope.return_value = mock_context_manager
        mock_get_db_manager.return_value = mock_db_manager
        
        # Mock repositories
        with patch('database.utils.TestResultRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_statistics.return_value = {
                'total': 100,
                'passed': 80,
                'failed': 20,
                'pass_rate': 0.8
            }
            mock_repo_class.return_value = mock_repo
            
            service = DatabaseService()
            health = service.health_check()
            
            assert health['status'] == 'healthy'
            assert health['connection'] == 'ok'
            assert 'statistics' in health
    
    @patch('database.utils.get_db_manager')
    def test_health_check_unhealthy(self, mock_get_db_manager):
        """Test unhealthy database check."""
        # Mock database manager to raise exception
        mock_db_manager = Mock()
        mock_db_manager.session_scope.side_effect = Exception("Connection failed")
        mock_get_db_manager.return_value = mock_db_manager
        
        service = DatabaseService()
        health = service.health_check()
        
        assert health['status'] == 'unhealthy'
        assert health['connection'] == 'failed'
        assert 'error' in health
    
    @patch('database.utils.db_session_scope')
    def test_cleanup_old_data(self, mock_session_scope):
        """Test old data cleanup."""
        # Mock session and query results
        mock_session = Mock()
        mock_session_scope.return_value.__enter__.return_value = mock_session
        
        # Mock old test results
        old_result1 = Mock()
        old_result2 = Mock()
        mock_session.query.return_value.filter.return_value.all.return_value = [
            old_result1, old_result2
        ]
        
        # Mock environment repository
        with patch('database.utils.EnvironmentRepository') as mock_env_repo_class:
            mock_env_repo = Mock()
            mock_env_repo.list_stale.return_value = []
            mock_env_repo_class.return_value = mock_env_repo
            
            service = DatabaseService()
            stats = service.cleanup_old_data(30)
            
            assert stats['test_results_deleted'] == 2
            assert stats['environments_cleaned'] == 0
            assert stats['errors'] == 0
            
            # Verify deletions
            assert mock_session.delete.call_count == 2
            mock_session.commit.assert_called_once()


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    def test_test_case_lifecycle(self):
        """Test complete test case lifecycle."""
        # This would be an integration test with a real database
        # For now, just test the model conversions work end-to-end
        
        # Create hardware config
        hw_config = HardwareConfig(
            architecture="x86_64",
            cpu_model="Intel i7",
            memory_mb=8192
        )
        
        # Create test case
        test_case = TestCase(
            id="integration-test-001",
            name="Integration Test",
            description="Test integration workflow",
            test_type=TestType.INTEGRATION,
            target_subsystem="filesystem",
            required_hardware=hw_config
        )
        
        # Convert to model and back
        hw_model = HardwareConfigModel.from_domain_model(hw_config)
        test_model = TestCaseModel.from_domain_model(test_case)
        test_model.hardware_config = hw_model
        
        # Convert back to domain
        restored_test = test_model.to_domain_model()
        
        assert restored_test.id == test_case.id
        assert restored_test.name == test_case.name
        assert restored_test.test_type == test_case.test_type
        assert restored_test.required_hardware.architecture == hw_config.architecture
    
    def test_coverage_data_conversion(self):
        """Test coverage data model conversion."""
        coverage = CoverageData(
            line_coverage=0.85,
            branch_coverage=0.75,
            function_coverage=0.90,
            covered_lines=["file1.c:10", "file1.c:15"],
            uncovered_lines=["file1.c:20"]
        )
        
        # Convert to model and back
        coverage_model = CoverageDataModel.from_domain_model(coverage, test_result_id=1)
        restored_coverage = coverage_model.to_domain_model()
        
        assert restored_coverage.line_coverage == coverage.line_coverage
        assert restored_coverage.branch_coverage == coverage.branch_coverage
        assert restored_coverage.function_coverage == coverage.function_coverage
        assert restored_coverage.covered_lines == coverage.covered_lines
        assert restored_coverage.uncovered_lines == coverage.uncovered_lines