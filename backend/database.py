"""Database initialization and utilities."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import Config
from backend.models import Base


# Create engine
engine = create_engine(
    Config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in Config.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables."""
    # Create data directory if it doesn't exist
    db_path = Config.DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a database session (non-generator version)."""
    return SessionLocal()


