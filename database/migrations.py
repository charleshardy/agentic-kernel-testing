"""Database migration system."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from .connection import Base, get_db_manager
from config.settings import get_settings

logger = logging.getLogger(__name__)


class MigrationRecord(Base):
    """Database model for tracking applied migrations."""
    
    __tablename__ = "schema_migrations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)
    checksum = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)


class Migration:
    """Base class for database migrations."""
    
    def __init__(self, version: str, name: str, description: str = ""):
        self.version = version
        self.name = name
        self.description = description
    
    def up(self, session) -> None:
        """Apply the migration."""
        raise NotImplementedError("Subclasses must implement up()")
    
    def down(self, session) -> None:
        """Rollback the migration."""
        raise NotImplementedError("Subclasses must implement down()")
    
    def get_checksum(self) -> str:
        """Get migration checksum for integrity verification."""
        import hashlib
        content = f"{self.version}:{self.name}:{self.description}"
        return hashlib.sha256(content.encode()).hexdigest()


class InitialMigration(Migration):
    """Initial migration to create all tables."""
    
    def __init__(self):
        super().__init__(
            version="001",
            name="initial_schema",
            description="Create initial database schema with all tables"
        )
    
    def up(self, session) -> None:
        """Create all tables."""
        logger.info("Creating initial database schema")
        
        # Import all models to ensure they're registered
        from .models import (
            HardwareConfigModel, TestCaseModel, EnvironmentModel,
            TestResultModel, CoverageDataModel, CodeAnalysisModel,
            FailureAnalysisModel, PerformanceBaselineModel, SecurityIssueModel
        )
        
        # Create all tables
        Base.metadata.create_all(bind=session.bind)
        logger.info("Initial schema created successfully")
    
    def down(self, session) -> None:
        """Drop all tables."""
        logger.info("Dropping all database tables")
        Base.metadata.drop_all(bind=session.bind)
        logger.info("All tables dropped successfully")


class AddIndexesMigration(Migration):
    """Migration to add performance indexes."""
    
    def __init__(self):
        super().__init__(
            version="002",
            name="add_performance_indexes",
            description="Add indexes for better query performance"
        )
    
    def up(self, session) -> None:
        """Add performance indexes."""
        logger.info("Adding performance indexes")
        
        # Add indexes using raw SQL for better control
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_test_results_timestamp ON test_results(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results(status)",
            "CREATE INDEX IF NOT EXISTS idx_test_cases_subsystem ON test_cases(target_subsystem)",
            "CREATE INDEX IF NOT EXISTS idx_test_cases_type ON test_cases(test_type)",
            "CREATE INDEX IF NOT EXISTS idx_environments_status ON environments(status)",
            "CREATE INDEX IF NOT EXISTS idx_environments_last_used ON environments(last_used)",
            "CREATE INDEX IF NOT EXISTS idx_code_analyses_commit ON code_analyses(commit_sha)",
            "CREATE INDEX IF NOT EXISTS idx_code_analyses_risk ON code_analyses(risk_level)",
            "CREATE INDEX IF NOT EXISTS idx_failure_analyses_pattern ON failure_analyses(error_pattern)",
            "CREATE INDEX IF NOT EXISTS idx_security_issues_severity ON security_issues(severity)",
            "CREATE INDEX IF NOT EXISTS idx_performance_baselines_lookup ON performance_baselines(kernel_version, hardware_config_id, benchmark_name, metric_name)",
        ]
        
        for index_sql in indexes:
            try:
                session.execute(index_sql)
                logger.debug(f"Created index: {index_sql}")
            except Exception as e:
                logger.warning(f"Failed to create index: {index_sql}, error: {e}")
        
        session.commit()
        logger.info("Performance indexes added successfully")
    
    def down(self, session) -> None:
        """Remove performance indexes."""
        logger.info("Removing performance indexes")
        
        # Drop indexes
        indexes = [
            "DROP INDEX IF EXISTS idx_test_results_timestamp",
            "DROP INDEX IF EXISTS idx_test_results_status",
            "DROP INDEX IF EXISTS idx_test_cases_subsystem",
            "DROP INDEX IF EXISTS idx_test_cases_type",
            "DROP INDEX IF EXISTS idx_environments_status",
            "DROP INDEX IF EXISTS idx_environments_last_used",
            "DROP INDEX IF EXISTS idx_code_analyses_commit",
            "DROP INDEX IF EXISTS idx_code_analyses_risk",
            "DROP INDEX IF EXISTS idx_failure_analyses_pattern",
            "DROP INDEX IF EXISTS idx_security_issues_severity",
            "DROP INDEX IF EXISTS idx_performance_baselines_lookup",
        ]
        
        for index_sql in indexes:
            try:
                session.execute(index_sql)
                logger.debug(f"Dropped index: {index_sql}")
            except Exception as e:
                logger.warning(f"Failed to drop index: {index_sql}, error: {e}")
        
        session.commit()
        logger.info("Performance indexes removed successfully")


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self):
        self.migrations: List[Migration] = [
            InitialMigration(),
            AddIndexesMigration(),
        ]
    
    def _ensure_migration_table(self, session) -> None:
        """Ensure the migration tracking table exists."""
        try:
            # Try to query the migration table
            session.query(MigrationRecord).first()
        except OperationalError:
            # Table doesn't exist, create it
            logger.info("Creating migration tracking table")
            MigrationRecord.__table__.create(bind=session.bind)
    
    def _get_applied_migrations(self, session) -> List[str]:
        """Get list of applied migration versions."""
        self._ensure_migration_table(session)
        
        records = session.query(MigrationRecord.version).all()
        return [record.version for record in records]
    
    def _record_migration(self, session, migration: Migration) -> None:
        """Record a migration as applied."""
        record = MigrationRecord(
            version=migration.version,
            name=migration.name,
            description=migration.description,
            checksum=migration.get_checksum()
        )
        session.add(record)
        session.commit()
    
    def _remove_migration_record(self, session, version: str) -> None:
        """Remove a migration record."""
        record = session.query(MigrationRecord).filter(
            MigrationRecord.version == version
        ).first()
        if record:
            session.delete(record)
            session.commit()
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        db_manager = get_db_manager()
        with db_manager.session_scope() as session:
            applied = self._get_applied_migrations(session)
            
            pending = []
            for migration in self.migrations:
                if migration.version not in applied:
                    pending.append(migration)
            
            return pending
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations with details."""
        db_manager = get_db_manager()
        with db_manager.session_scope() as session:
            self._ensure_migration_table(session)
            
            records = session.query(MigrationRecord).order_by(
                MigrationRecord.applied_at
            ).all()
            
            return [
                {
                    'version': record.version,
                    'name': record.name,
                    'description': record.description,
                    'applied_at': record.applied_at.isoformat(),
                    'checksum': record.checksum
                }
                for record in records
            ]
    
    def migrate(self, target_version: Optional[str] = None) -> None:
        """Apply pending migrations up to target version."""
        db_manager = get_db_manager()
        
        with db_manager.session_scope() as session:
            applied = self._get_applied_migrations(session)
            
            for migration in self.migrations:
                # Skip if already applied
                if migration.version in applied:
                    continue
                
                # Stop if we've reached the target version
                if target_version and migration.version > target_version:
                    break
                
                logger.info(f"Applying migration {migration.version}: {migration.name}")
                
                try:
                    migration.up(session)
                    self._record_migration(session, migration)
                    logger.info(f"Migration {migration.version} applied successfully")
                except Exception as e:
                    logger.error(f"Migration {migration.version} failed: {e}")
                    session.rollback()
                    raise
    
    def rollback(self, target_version: str) -> None:
        """Rollback migrations to target version."""
        db_manager = get_db_manager()
        
        with db_manager.session_scope() as session:
            applied = self._get_applied_migrations(session)
            
            # Find migrations to rollback (in reverse order)
            to_rollback = []
            for migration in reversed(self.migrations):
                if migration.version in applied and migration.version > target_version:
                    to_rollback.append(migration)
            
            for migration in to_rollback:
                logger.info(f"Rolling back migration {migration.version}: {migration.name}")
                
                try:
                    migration.down(session)
                    self._remove_migration_record(session, migration.version)
                    logger.info(f"Migration {migration.version} rolled back successfully")
                except Exception as e:
                    logger.error(f"Rollback of migration {migration.version} failed: {e}")
                    session.rollback()
                    raise
    
    def reset(self) -> None:
        """Reset database by rolling back all migrations."""
        logger.warning("Resetting database - all data will be lost!")
        
        db_manager = get_db_manager()
        with db_manager.session_scope() as session:
            applied = self._get_applied_migrations(session)
            
            # Rollback all migrations in reverse order
            for migration in reversed(self.migrations):
                if migration.version in applied:
                    logger.info(f"Rolling back migration {migration.version}")
                    try:
                        migration.down(session)
                        self._remove_migration_record(session, migration.version)
                    except Exception as e:
                        logger.error(f"Failed to rollback migration {migration.version}: {e}")
                        # Continue with other migrations
        
        logger.info("Database reset completed")
    
    def status(self) -> Dict[str, Any]:
        """Get migration status."""
        pending = self.get_pending_migrations()
        applied = self.get_applied_migrations()
        
        return {
            'total_migrations': len(self.migrations),
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_migrations': applied,
            'pending_migrations': [
                {
                    'version': m.version,
                    'name': m.name,
                    'description': m.description
                }
                for m in pending
            ]
        }


def create_migration_manager() -> MigrationManager:
    """Create a new migration manager instance."""
    return MigrationManager()


# CLI functions for migration management
def migrate_database(target_version: Optional[str] = None) -> None:
    """Apply database migrations."""
    manager = create_migration_manager()
    manager.migrate(target_version)


def rollback_database(target_version: str) -> None:
    """Rollback database migrations."""
    manager = create_migration_manager()
    manager.rollback(target_version)


def reset_database() -> None:
    """Reset database by removing all migrations."""
    manager = create_migration_manager()
    manager.reset()


def migration_status() -> Dict[str, Any]:
    """Get database migration status."""
    manager = create_migration_manager()
    return manager.status()