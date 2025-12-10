"""Database utility functions."""

import logging
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from .connection import get_db_manager, db_session_scope
from .repositories import (
    TestCaseRepository, TestResultRepository, EnvironmentRepository,
    CoverageRepository, CodeAnalysisRepository, FailureRepository,
    HardwareConfigRepository, PerformanceRepository, SecurityRepository
)
from .migrations import MigrationManager

logger = logging.getLogger(__name__)


class DatabaseService:
    """High-level database service for common operations."""
    
    def __init__(self):
        self._db_manager = None
    
    @property
    def db_manager(self):
        """Get database manager instance."""
        if self._db_manager is None:
            self._db_manager = get_db_manager()
        return self._db_manager
    
    @contextmanager
    def get_repositories(self):
        """Get all repository instances with a shared session."""
        with db_session_scope() as session:
            yield {
                'test_case': TestCaseRepository(session),
                'test_result': TestResultRepository(session),
                'environment': EnvironmentRepository(session),
                'coverage': CoverageRepository(session),
                'code_analysis': CodeAnalysisRepository(session),
                'failure': FailureRepository(session),
                'hardware_config': HardwareConfigRepository(session),
                'performance': PerformanceRepository(session),
                'security': SecurityRepository(session),
            }
    
    def initialize(self) -> None:
        """Initialize database and run migrations."""
        logger.info("Initializing database service")
        
        try:
            # Initialize database connection
            self.db_manager.initialize()
            
            # Run migrations
            migration_manager = MigrationManager()
            migration_manager.migrate()
            
            logger.info("Database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            with db_session_scope() as session:
                # Simple query to test connection
                session.execute("SELECT 1")
                
                # Get basic statistics
                with self.get_repositories() as repos:
                    stats = repos['test_result'].get_statistics()
                
                return {
                    'status': 'healthy',
                    'connection': 'ok',
                    'statistics': stats
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connection': 'failed',
                'error': str(e)
            }
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        try:
            with self.get_repositories() as repos:
                test_stats = repos['test_result'].get_statistics()
                coverage_stats = repos['coverage'].get_aggregate_coverage()
                security_stats = repos['security'].get_security_summary()
                
                # Count environments by status
                idle_envs = len(repos['environment'].list_idle())
                busy_envs = len(repos['environment'].list_busy())
                
                return {
                    'test_results': test_stats,
                    'coverage': coverage_stats,
                    'security_issues': security_stats,
                    'environments': {
                        'idle': idle_envs,
                        'busy': busy_envs,
                        'total': idle_envs + busy_envs
                    }
                }
        except Exception as e:
            logger.error(f"Failed to get system statistics: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Clean up old data to manage database size."""
        logger.info(f"Cleaning up data older than {days} days")
        
        cleanup_stats = {
            'test_results_deleted': 0,
            'environments_cleaned': 0,
            'errors': 0
        }
        
        try:
            with db_session_scope() as session:
                # Clean up old test results (keep only recent ones)
                from datetime import datetime, timedelta
                from .models import TestResultModel
                
                cutoff = datetime.utcnow() - timedelta(days=days)
                
                # Delete old test results
                old_results = session.query(TestResultModel).filter(
                    TestResultModel.timestamp < cutoff
                ).all()
                
                for result in old_results:
                    session.delete(result)
                    cleanup_stats['test_results_deleted'] += 1
                
                # Clean up stale environments
                env_repo = EnvironmentRepository(session)
                stale_envs = env_repo.list_stale(hours=24 * days)
                
                for env in stale_envs:
                    if env.status.value == 'idle':  # Only clean up idle environments
                        session.delete(env)
                        cleanup_stats['environments_cleaned'] += 1
                
                session.commit()
                logger.info(f"Cleanup completed: {cleanup_stats}")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            cleanup_stats['errors'] = 1
        
        return cleanup_stats
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup (SQLite only)."""
        try:
            from config.settings import get_settings
            settings = get_settings()
            
            if settings.database.type != "sqlite":
                logger.warning("Backup only supported for SQLite databases")
                return False
            
            import shutil
            db_path = f"{settings.database.name}.db"
            shutil.copy2(db_path, backup_path)
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup (SQLite only)."""
        try:
            from config.settings import get_settings
            settings = get_settings()
            
            if settings.database.type != "sqlite":
                logger.warning("Restore only supported for SQLite databases")
                return False
            
            import shutil
            db_path = f"{settings.database.name}.db"
            
            # Close existing connections
            self.db_manager.close()
            
            # Restore backup
            shutil.copy2(backup_path, db_path)
            
            # Reinitialize
            self.db_manager.initialize()
            
            logger.info(f"Database restored from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False


# Global database service instance
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get the global database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def initialize_database_service() -> None:
    """Initialize the database service."""
    service = get_database_service()
    service.initialize()


# Convenience functions for common operations
def store_test_case(test_case) -> bool:
    """Store a test case in the database."""
    try:
        service = get_database_service()
        with service.get_repositories() as repos:
            repos['test_case'].create(test_case)
        return True
    except Exception as e:
        logger.error(f"Failed to store test case: {e}")
        return False


def store_test_result(test_result) -> bool:
    """Store a test result in the database."""
    try:
        service = get_database_service()
        with service.get_repositories() as repos:
            repos['test_result'].create(test_result)
        return True
    except Exception as e:
        logger.error(f"Failed to store test result: {e}")
        return False


def get_test_statistics() -> Dict[str, Any]:
    """Get test execution statistics."""
    try:
        service = get_database_service()
        with service.get_repositories() as repos:
            return repos['test_result'].get_statistics()
    except Exception as e:
        logger.error(f"Failed to get test statistics: {e}")
        return {}


def get_coverage_trend(days: int = 30) -> List[Dict[str, Any]]:
    """Get coverage trend over time."""
    try:
        service = get_database_service()
        with service.get_repositories() as repos:
            return repos['coverage'].get_coverage_trend(days)
    except Exception as e:
        logger.error(f"Failed to get coverage trend: {e}")
        return []


def find_similar_failures(error_pattern: str) -> List[Dict[str, Any]]:
    """Find failures with similar error patterns."""
    try:
        service = get_database_service()
        with service.get_repositories() as repos:
            failures = repos['failure'].list_by_pattern(error_pattern)
            return [failure.to_domain_model().to_dict() for failure in failures]
    except Exception as e:
        logger.error(f"Failed to find similar failures: {e}")
        return []