from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import structlog

from backend.app.core.config import settings

logger = structlog.get_logger()

# OPTIMIZED: Larger connection pool for production
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=50,              # Increased from 10
    max_overflow=50,           # Increased from 20 (max 100 total)
    pool_recycle=3600,         # Recycle connections every hour
    pool_timeout=30,           # 30 second timeout
    echo=False,                # Disable SQL logging in production
    connect_args={
        "connect_timeout": 10,
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
