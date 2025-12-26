"""Database migration to add environment allocation tracking tables.

This migration adds the following tables:
- allocation_requests: Track environment allocation requests
- allocation_events: Log allocation events for history
- environment_resource_metrics: Store resource usage metrics over time

It also extends the environments table with allocation tracking fields.
"""

from sqlalchemy import text
from database.connection import get_engine, get_session
from database.models import Base
import logging

logger = logging.getLogger(__name__)


def upgrade():
    """Apply the migration."""
    engine = get_engine()
    
    logger.info("Starting environment allocation tables migration...")
    
    with engine.connect() as conn:
        # Add new columns to environments table
        try:
            conn.execute(text("""
                ALTER TABLE environments 
                ADD COLUMN IF NOT EXISTS health VARCHAR(20) DEFAULT 'unknown',
                ADD COLUMN IF NOT EXISTS architecture VARCHAR(50) DEFAULT 'x86_64',
                ADD COLUMN IF NOT EXISTS environment_type VARCHAR(50) DEFAULT 'qemu',
                ADD COLUMN IF NOT EXISTS assigned_tests JSON DEFAULT '[]',
                ADD COLUMN IF NOT EXISTS current_cpu_usage FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS current_memory_usage FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS current_disk_usage FLOAT DEFAULT 0.0,
                ADD COLUMN IF NOT EXISTS allocation_count INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS last_allocated_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS last_deallocated_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            logger.info("Extended environments table with allocation tracking fields")
        except Exception as e:
            logger.warning(f"Failed to extend environments table (may already exist): {e}")
        
        # Create allocation_requests table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS allocation_requests (
                    id VARCHAR(255) PRIMARY KEY,
                    test_id VARCHAR(255) NOT NULL,
                    requirements JSON NOT NULL,
                    preferences JSON,
                    priority INTEGER NOT NULL DEFAULT 5,
                    status VARCHAR(50) NOT NULL DEFAULT 'queued',
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    estimated_start_time TIMESTAMP,
                    allocated_environment_id VARCHAR(255),
                    allocation_metadata JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES test_cases(id) ON DELETE CASCADE,
                    FOREIGN KEY (allocated_environment_id) REFERENCES environments(id) ON DELETE SET NULL
                )
            """))
            logger.info("Created allocation_requests table")
        except Exception as e:
            logger.warning(f"Failed to create allocation_requests table (may already exist): {e}")
        
        # Create allocation_events table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS allocation_events (
                    id VARCHAR(255) PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    environment_id VARCHAR(255) NOT NULL,
                    test_id VARCHAR(255),
                    allocation_request_id VARCHAR(255),
                    event_metadata JSON DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (environment_id) REFERENCES environments(id) ON DELETE CASCADE,
                    FOREIGN KEY (test_id) REFERENCES test_cases(id) ON DELETE SET NULL,
                    FOREIGN KEY (allocation_request_id) REFERENCES allocation_requests(id) ON DELETE SET NULL
                )
            """))
            logger.info("Created allocation_events table")
        except Exception as e:
            logger.warning(f"Failed to create allocation_events table (may already exist): {e}")
        
        # Create environment_resource_metrics table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS environment_resource_metrics (
                    id SERIAL PRIMARY KEY,
                    environment_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage FLOAT NOT NULL DEFAULT 0.0,
                    cpu_cores INTEGER NOT NULL DEFAULT 1,
                    cpu_frequency FLOAT,
                    memory_used INTEGER NOT NULL DEFAULT 0,
                    memory_total INTEGER NOT NULL DEFAULT 0,
                    memory_available INTEGER NOT NULL DEFAULT 0,
                    disk_used INTEGER NOT NULL DEFAULT 0,
                    disk_total INTEGER NOT NULL DEFAULT 0,
                    disk_iops INTEGER,
                    network_bytes_in INTEGER NOT NULL DEFAULT 0,
                    network_bytes_out INTEGER NOT NULL DEFAULT 0,
                    network_packets_in INTEGER NOT NULL DEFAULT 0,
                    network_packets_out INTEGER NOT NULL DEFAULT 0,
                    metrics_metadata JSON DEFAULT '{}',
                    FOREIGN KEY (environment_id) REFERENCES environments(id) ON DELETE CASCADE
                )
            """))
            logger.info("Created environment_resource_metrics table")
        except Exception as e:
            logger.warning(f"Failed to create environment_resource_metrics table (may already exist): {e}")
        
        # Create indexes for better performance
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_allocation_requests_status ON allocation_requests(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_allocation_requests_test_id ON allocation_requests(test_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_allocation_events_environment_id ON allocation_events(environment_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_allocation_events_timestamp ON allocation_events(timestamp)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resource_metrics_environment_id ON environment_resource_metrics(environment_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resource_metrics_timestamp ON environment_resource_metrics(timestamp)"))
            logger.info("Created performance indexes")
        except Exception as e:
            logger.warning(f"Failed to create indexes (may already exist): {e}")
        
        conn.commit()
    
    logger.info("Environment allocation tables migration completed successfully")


def downgrade():
    """Rollback the migration."""
    engine = get_engine()
    
    logger.info("Rolling back environment allocation tables migration...")
    
    with engine.connect() as conn:
        # Drop tables in reverse order
        conn.execute(text("DROP TABLE IF EXISTS environment_resource_metrics"))
        conn.execute(text("DROP TABLE IF EXISTS allocation_events"))
        conn.execute(text("DROP TABLE IF EXISTS allocation_requests"))
        
        # Remove added columns from environments table
        try:
            conn.execute(text("""
                ALTER TABLE environments 
                DROP COLUMN IF EXISTS health,
                DROP COLUMN IF EXISTS architecture,
                DROP COLUMN IF EXISTS environment_type,
                DROP COLUMN IF EXISTS assigned_tests,
                DROP COLUMN IF EXISTS current_cpu_usage,
                DROP COLUMN IF EXISTS current_memory_usage,
                DROP COLUMN IF EXISTS current_disk_usage,
                DROP COLUMN IF EXISTS allocation_count,
                DROP COLUMN IF EXISTS last_allocated_at,
                DROP COLUMN IF EXISTS last_deallocated_at,
                DROP COLUMN IF EXISTS updated_at
            """))
        except Exception as e:
            logger.warning(f"Failed to remove columns from environments table: {e}")
        
        conn.commit()
    
    logger.info("Environment allocation tables migration rollback completed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()