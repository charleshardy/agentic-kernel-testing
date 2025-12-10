# Database Layer

The database layer provides persistent storage for the Agentic AI Testing System using SQLAlchemy ORM with support for both SQLite and PostgreSQL databases.

## Features

- **ORM Models**: SQLAlchemy models for all core data types
- **Repository Pattern**: Clean data access layer with repositories
- **Migration System**: Database schema versioning and migration management
- **Connection Management**: Automatic connection pooling and session management
- **CLI Tools**: Command-line interface for database operations
- **Backup/Restore**: Database backup and restore capabilities (SQLite)

## Architecture

```
database/
├── __init__.py          # Module exports
├── connection.py        # Database connection and session management
├── models.py           # SQLAlchemy ORM models
├── repositories.py     # Data access layer (Repository pattern)
├── migrations.py       # Migration system
├── utils.py           # Utility functions and high-level service
├── cli.py             # Command-line interface
└── README.md          # This file
```

## Quick Start

### 1. Installation

Install required dependencies:

```bash
pip install sqlalchemy psycopg2-binary  # For PostgreSQL
# OR
pip install sqlalchemy                   # For SQLite only
```

### 2. Configuration

Configure database settings in your `.env` file:

```env
# SQLite (default)
DATABASE__TYPE=sqlite
DATABASE__NAME=agentic_testing

# PostgreSQL
DATABASE__TYPE=postgresql
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=agentic_testing
DATABASE__USER=your_user
DATABASE__PASSWORD=your_password
```

### 3. Initialize Database

```python
from database import initialize_database_service

# Initialize database and run migrations
initialize_database_service()
```

Or use the CLI:

```bash
python -m database.cli init
```

## Usage Examples

### Basic Data Operations

```python
from database.utils import get_database_service
from ai_generator.models import TestCase, TestType, HardwareConfig

# Create test case
hw_config = HardwareConfig(
    architecture="x86_64",
    cpu_model="Intel i7",
    memory_mb=8192
)

test_case = TestCase(
    id="test-001",
    name="Memory Test",
    description="Test memory allocation",
    test_type=TestType.UNIT,
    target_subsystem="memory",
    required_hardware=hw_config
)

# Store in database
service = get_database_service()
with service.get_repositories() as repos:
    repos['test_case'].create(test_case)
```

### Repository Usage

```python
from database import get_db_session
from database.repositories import TestCaseRepository, TestResultRepository

# Using repositories directly
with get_db_session() as session:
    test_repo = TestCaseRepository(session)
    
    # Create test case
    test_model = test_repo.create(test_case)
    
    # Search test cases
    memory_tests = test_repo.list_by_subsystem("memory")
    
    # Get statistics
    result_repo = TestResultRepository(session)
    stats = result_repo.get_statistics()
    print(f"Pass rate: {stats['pass_rate']:.2%}")
```

### Coverage Analysis

```python
from database.repositories import CoverageRepository

with get_db_session() as session:
    coverage_repo = CoverageRepository(session)
    
    # Get aggregate coverage
    coverage_stats = coverage_repo.get_aggregate_coverage()
    print(f"Line coverage: {coverage_stats['line_coverage']:.2%}")
    
    # Get coverage trend
    trend = coverage_repo.get_coverage_trend(days=30)
    for day_data in trend:
        print(f"{day_data['date']}: {day_data['line_coverage']:.2%}")
```

## Database Models

### Core Models

- **HardwareConfigModel**: Hardware configurations for test execution
- **TestCaseModel**: Test case definitions and metadata
- **EnvironmentModel**: Test execution environments
- **TestResultModel**: Test execution results and outcomes
- **CoverageDataModel**: Code coverage metrics
- **CodeAnalysisModel**: Code change analysis results
- **FailureAnalysisModel**: Failure analysis and root cause data

### Security and Performance Models

- **SecurityIssueModel**: Security vulnerabilities and issues
- **PerformanceBaselineModel**: Performance benchmarks and baselines

## Migration System

### Running Migrations

```bash
# Check migration status
python -m database.cli status

# Run all pending migrations
python -m database.cli migrate

# Migrate to specific version
python -m database.cli migrate --target 002

# Rollback to previous version
python -m database.cli rollback 001
```

### Creating New Migrations

```python
from database.migrations import Migration

class MyMigration(Migration):
    def __init__(self):
        super().__init__(
            version="003",
            name="add_new_feature",
            description="Add support for new feature"
        )
    
    def up(self, session):
        # Apply migration
        session.execute("ALTER TABLE test_cases ADD COLUMN new_field TEXT")
    
    def down(self, session):
        # Rollback migration
        session.execute("ALTER TABLE test_cases DROP COLUMN new_field")
```

## CLI Commands

### Database Management

```bash
# Initialize database
python -m database.cli init

# Check database health
python -m database.cli health

# Show statistics
python -m database.cli stats

# Clean up old data
python -m database.cli cleanup --days 30
```

### Backup and Restore (SQLite)

```bash
# Create backup
python -m database.cli backup /path/to/backup.db

# Restore from backup
python -m database.cli restore /path/to/backup.db
```

### Configuration

```bash
# Show current configuration
python -m database.cli config
```

## Repository Pattern

The database layer uses the Repository pattern to provide a clean abstraction over data access:

### Available Repositories

- **TestCaseRepository**: CRUD operations for test cases
- **TestResultRepository**: Test result storage and querying
- **EnvironmentRepository**: Environment management
- **CoverageRepository**: Coverage data analysis
- **CodeAnalysisRepository**: Code analysis results
- **FailureRepository**: Failure analysis data
- **PerformanceRepository**: Performance baselines
- **SecurityRepository**: Security issue tracking

### Repository Methods

Each repository provides standard methods:

- `create()`: Create new records
- `get_by_id()`: Retrieve by primary key
- `list_by_*()`: List records by various criteria
- `update()`: Update existing records
- `delete()`: Delete records

Plus specialized methods for each domain.

## Performance Considerations

### Indexing

The migration system automatically creates performance indexes:

- Test results by timestamp and status
- Test cases by subsystem and type
- Environments by status and last used
- Code analyses by commit SHA and risk level

### Connection Pooling

PostgreSQL connections use connection pooling:

```python
# Configured automatically
pool_size=10
max_overflow=20
pool_pre_ping=True
```

### Query Optimization

- Use repository methods for common queries
- Leverage database indexes for filtering
- Use aggregate functions for statistics
- Implement pagination for large result sets

## Error Handling

The database layer provides comprehensive error handling:

```python
from database.utils import store_test_case

# Automatic error handling
success = store_test_case(test_case)
if not success:
    print("Failed to store test case")
```

### Common Error Scenarios

- **Connection failures**: Automatic retry with exponential backoff
- **Constraint violations**: Graceful handling of duplicate keys
- **Migration failures**: Automatic rollback on error
- **Session management**: Automatic cleanup and transaction handling

## Testing

### Unit Tests

```bash
# Run database unit tests
python -m pytest tests/unit/test_database.py -v
```

### Integration Tests

```bash
# Run with real database
python -m pytest tests/integration/test_database_integration.py -v
```

## Monitoring and Maintenance

### Health Checks

```python
from database.utils import get_database_service

service = get_database_service()
health = service.health_check()
print(f"Status: {health['status']}")
```

### Statistics

```python
stats = service.get_system_statistics()
print(f"Total tests: {stats['test_results']['total']}")
print(f"Pass rate: {stats['test_results']['pass_rate']:.2%}")
```

### Cleanup

```python
# Clean up old data
cleanup_stats = service.cleanup_old_data(days=30)
print(f"Deleted {cleanup_stats['test_results_deleted']} old results")
```

## Configuration Reference

### Database Settings

```python
class DatabaseConfig:
    type: str = "sqlite"              # Database type
    host: str = "localhost"           # Database host
    port: int = 5432                  # Database port
    name: str = "agentic_testing"     # Database name
    user: str = None                  # Database user
    password: str = None              # Database password
```

### Environment Variables

- `DATABASE__TYPE`: Database type (sqlite, postgresql)
- `DATABASE__HOST`: Database host
- `DATABASE__PORT`: Database port
- `DATABASE__NAME`: Database name
- `DATABASE__USER`: Database user
- `DATABASE__PASSWORD`: Database password

## Troubleshooting

### Common Issues

1. **Module not found**: Install SQLAlchemy dependencies
2. **Connection refused**: Check database server is running
3. **Permission denied**: Verify database user permissions
4. **Migration failed**: Check database schema and constraints

### Debug Mode

Enable debug mode to see SQL queries:

```env
DEBUG=true
```

### Logging

Database operations are logged at INFO level:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Best Practices

1. **Use repositories**: Don't access models directly
2. **Handle transactions**: Use session scopes for consistency
3. **Index queries**: Ensure queries use appropriate indexes
4. **Clean up data**: Regularly remove old test results
5. **Monitor performance**: Track query execution times
6. **Backup regularly**: Create regular database backups
7. **Test migrations**: Test migrations on development data first

## Future Enhancements

- **Read replicas**: Support for read-only database replicas
- **Sharding**: Horizontal partitioning for large datasets
- **Caching**: Redis integration for frequently accessed data
- **Metrics**: Detailed performance metrics and monitoring
- **Compression**: Automatic compression of old test data