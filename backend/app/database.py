"""
Database connection and session management
"""
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import QueuePool
from .config import get_settings

settings = get_settings()

# Create database engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)


def create_db_and_tables():
    """Create database tables from SQLModel metadata"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency for getting database sessions"""
    with Session(engine) as session:
        yield session
