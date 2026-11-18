from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings


def make_engine(url: str) -> Engine:
    """Create the engine. SQLite gets the settings a small web app needs."""
    if not url.startswith("sqlite"):
        return create_engine(url, pool_pre_ping=True, pool_recycle=3600)

    eng = create_engine(url, connect_args={"check_same_thread": False, "timeout": 5})

    @event.listens_for(eng, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):
        # Let SQLAlchemy issue BEGIN itself so "BEGIN IMMEDIATE" works
        dbapi_conn.isolation_level = None
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

    @event.listens_for(eng, "begin")
    def _sqlite_begin(conn):
        conn.exec_driver_sql("BEGIN")

    return eng


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def take_write_lock(db: Session, pg_lock_key: int) -> None:
    """Serialise a check-then-insert section until the transaction ends.

    SQLite: a write statement makes this transaction the single writer now
    (it matches no rows), so other writers wait on busy_timeout.
    PostgreSQL: a transaction-scoped advisory lock.
    """
    if db.get_bind().dialect.name == "sqlite":
        db.execute(text("UPDATE users SET token_version = token_version WHERE 0"))
    else:
        db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": pg_lock_key})


def get_db():
    """Dependency for getting database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
