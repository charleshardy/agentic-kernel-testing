"""Database connection and session management."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Base class for all ORM models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        
    def initialize(self) -> None:
        """Initialize database connection."""
        settings = get_settings()
        db_config = settings.database
        
        logger.info(f"Initializing database connection: {db_config.type}")
        
        # Create engine based on database type
        if db_config.type == "sqlite":
            # SQLite configuration
            self._engine = create_engine(
                db_config.connection_string,
                echo=settings.debug,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
        elif db_config.type == "postgresql":
            # PostgreSQL configuration
            self._engine = create_engine(
                db_config.connection_string,
                echo=settings.debug,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
        else:
            raise ValueError(f"Unsupported database type: {db_config.type}")
        
        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("Database connection initialized successfully")
    
    def create_tables(self) -> None:
        """Create all database tables."""
        if not self._engine:
            raise RuntimeError("Database not initialized")
        
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=self._engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self) -> None:
        """Drop all database tables."""
        if not self._engine:
            raise RuntimeError("Database not initialized")
        
        logger.info("Dropping database tables")
        Base.metadata.drop_all(bind=self._engine)
        logger.info("Database tables dropped successfully")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        
        return self._session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Close database connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.initialize()
    return _db_manager


def get_db_session() -> Session:
    """Get a new database session."""
    return get_db_manager().get_session()


@contextmanager
def db_session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    with get_db_manager().session_scope() as session:
        yield session


def initialize_database() -> None:
    """Initialize database and create tables."""
    db_manager = get_db_manager()
    db_manager.create_tables()


def close_database() -> None:
    """Close database connections."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None