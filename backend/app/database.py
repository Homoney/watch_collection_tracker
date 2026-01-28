from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=20,              # Maximum pool connections
    max_overflow=10,           # Additional connections beyond pool_size
    pool_pre_ping=True,        # Verify connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False                 # Disable SQL logging in production
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
