"""Command-line interface for database management."""

import click
import json
from typing import Optional

from .migrations import MigrationManager, migration_status
from .utils import get_database_service
from config.settings import get_settings


@click.group()
def db():
    """Database management commands."""
    pass


@db.command()
def init():
    """Initialize database and run migrations."""
    click.echo("Initializing database...")
    
    try:
        service = get_database_service()
        service.initialize()
        click.echo("✅ Database initialized successfully")
    except Exception as e:
        click.echo(f"❌ Database initialization failed: {e}")
        raise click.Abort()


@db.command()
@click.option('--target', help='Target migration version')
def migrate(target: Optional[str]):
    """Run database migrations."""
    click.echo("Running database migrations...")
    
    try:
        manager = MigrationManager()
        manager.migrate(target)
        click.echo("✅ Migrations completed successfully")
    except Exception as e:
        click.echo(f"❌ Migration failed: {e}")
        raise click.Abort()


@db.command()
@click.argument('target_version')
def rollback(target_version: str):
    """Rollback migrations to target version."""
    click.echo(f"Rolling back migrations to version {target_version}...")
    
    if not click.confirm("This will rollback database changes. Continue?"):
        click.echo("Rollback cancelled")
        return
    
    try:
        manager = MigrationManager()
        manager.rollback(target_version)
        click.echo("✅ Rollback completed successfully")
    except Exception as e:
        click.echo(f"❌ Rollback failed: {e}")
        raise click.Abort()


@db.command()
def reset():
    """Reset database by removing all data."""
    click.echo("⚠️  WARNING: This will delete ALL data in the database!")
    
    if not click.confirm("Are you sure you want to reset the database?"):
        click.echo("Reset cancelled")
        return
    
    if not click.confirm("This action cannot be undone. Continue?"):
        click.echo("Reset cancelled")
        return
    
    try:
        manager = MigrationManager()
        manager.reset()
        click.echo("✅ Database reset completed")
    except Exception as e:
        click.echo(f"❌ Database reset failed: {e}")
        raise click.Abort()


@db.command()
def status():
    """Show migration status."""
    try:
        status_info = migration_status()
        
        click.echo("📊 Database Migration Status")
        click.echo("=" * 40)
        click.echo(f"Total migrations: {status_info['total_migrations']}")
        click.echo(f"Applied: {status_info['applied_count']}")
        click.echo(f"Pending: {status_info['pending_count']}")
        
        if status_info['applied_migrations']:
            click.echo("\n✅ Applied Migrations:")
            for migration in status_info['applied_migrations']:
                click.echo(f"  {migration['version']}: {migration['name']} ({migration['applied_at']})")
        
        if status_info['pending_migrations']:
            click.echo("\n⏳ Pending Migrations:")
            for migration in status_info['pending_migrations']:
                click.echo(f"  {migration['version']}: {migration['name']}")
        else:
            click.echo("\n✅ All migrations are up to date")
            
    except Exception as e:
        click.echo(f"❌ Failed to get migration status: {e}")
        raise click.Abort()


@db.command()
def health():
    """Check database health."""
    try:
        service = get_database_service()
        health_info = service.health_check()
        
        if health_info['status'] == 'healthy':
            click.echo("✅ Database is healthy")
            click.echo(f"Connection: {health_info['connection']}")
            
            stats = health_info.get('statistics', {})
            if stats:
                click.echo(f"Total test results: {stats.get('total', 0)}")
                click.echo(f"Pass rate: {stats.get('pass_rate', 0):.2%}")
                click.echo(f"Average execution time: {stats.get('avg_execution_time', 0):.2f}s")
        else:
            click.echo("❌ Database is unhealthy")
            click.echo(f"Error: {health_info.get('error', 'Unknown error')}")
            
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}")
        raise click.Abort()


@db.command()
def stats():
    """Show database statistics."""
    try:
        service = get_database_service()
        stats = service.get_system_statistics()
        
        click.echo("📈 Database Statistics")
        click.echo("=" * 30)
        
        # Test results
        test_stats = stats.get('test_results', {})
        click.echo(f"\n🧪 Test Results:")
        click.echo(f"  Total: {test_stats.get('total', 0)}")
        click.echo(f"  Passed: {test_stats.get('passed', 0)}")
        click.echo(f"  Failed: {test_stats.get('failed', 0)}")
        click.echo(f"  Pass Rate: {test_stats.get('pass_rate', 0):.2%}")
        
        # Coverage
        coverage_stats = stats.get('coverage', {})
        click.echo(f"\n📊 Coverage:")
        click.echo(f"  Line: {coverage_stats.get('line_coverage', 0):.2%}")
        click.echo(f"  Branch: {coverage_stats.get('branch_coverage', 0):.2%}")
        click.echo(f"  Function: {coverage_stats.get('function_coverage', 0):.2%}")
        
        # Security
        security_stats = stats.get('security_issues', {})
        if security_stats:
            click.echo(f"\n🔒 Security Issues:")
            for severity, count in security_stats.items():
                click.echo(f"  {severity.title()}: {count}")
        
        # Environments
        env_stats = stats.get('environments', {})
        click.echo(f"\n🖥️  Environments:")
        click.echo(f"  Total: {env_stats.get('total', 0)}")
        click.echo(f"  Idle: {env_stats.get('idle', 0)}")
        click.echo(f"  Busy: {env_stats.get('busy', 0)}")
        
    except Exception as e:
        click.echo(f"❌ Failed to get statistics: {e}")
        raise click.Abort()


@db.command()
@click.option('--days', default=30, help='Number of days of data to keep')
def cleanup(days: int):
    """Clean up old data."""
    click.echo(f"Cleaning up data older than {days} days...")
    
    if not click.confirm(f"This will delete test results older than {days} days. Continue?"):
        click.echo("Cleanup cancelled")
        return
    
    try:
        service = get_database_service()
        cleanup_stats = service.cleanup_old_data(days)
        
        click.echo("✅ Cleanup completed")
        click.echo(f"Test results deleted: {cleanup_stats['test_results_deleted']}")
        click.echo(f"Environments cleaned: {cleanup_stats['environments_cleaned']}")
        
        if cleanup_stats['errors'] > 0:
            click.echo(f"⚠️  Errors encountered: {cleanup_stats['errors']}")
            
    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}")
        raise click.Abort()


@db.command()
@click.argument('backup_path')
def backup(backup_path: str):
    """Create database backup (SQLite only)."""
    click.echo(f"Creating database backup at {backup_path}...")
    
    try:
        service = get_database_service()
        success = service.backup_database(backup_path)
        
        if success:
            click.echo("✅ Backup created successfully")
        else:
            click.echo("❌ Backup failed (only SQLite databases supported)")
            
    except Exception as e:
        click.echo(f"❌ Backup failed: {e}")
        raise click.Abort()


@db.command()
@click.argument('backup_path')
def restore(backup_path: str):
    """Restore database from backup (SQLite only)."""
    click.echo(f"Restoring database from {backup_path}...")
    
    if not click.confirm("This will replace the current database. Continue?"):
        click.echo("Restore cancelled")
        return
    
    try:
        service = get_database_service()
        success = service.restore_database(backup_path)
        
        if success:
            click.echo("✅ Database restored successfully")
        else:
            click.echo("❌ Restore failed (only SQLite databases supported)")
            
    except Exception as e:
        click.echo(f"❌ Restore failed: {e}")
        raise click.Abort()


@db.command()
def config():
    """Show database configuration."""
    try:
        settings = get_settings()
        db_config = settings.database
        
        click.echo("⚙️  Database Configuration")
        click.echo("=" * 30)
        click.echo(f"Type: {db_config.type}")
        click.echo(f"Host: {db_config.host}")
        click.echo(f"Port: {db_config.port}")
        click.echo(f"Database: {db_config.name}")
        click.echo(f"User: {db_config.user or 'N/A'}")
        
        # Don't show password for security
        click.echo(f"Password: {'***' if db_config.password else 'N/A'}")
        
    except Exception as e:
        click.echo(f"❌ Failed to show configuration: {e}")
        raise click.Abort()


if __name__ == '__main__':
    db()