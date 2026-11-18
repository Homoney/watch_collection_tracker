from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings


def make_engine(url: str) -> Engine:
    """Create the SQLite engine with the settings a small web app needs."""
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


def take_write_lock(db: Session) -> None:
    """Serialise a check-then-insert section until the transaction ends.

    A write statement (it matches no rows) makes this transaction SQLite's
    single writer now, so other writers wait on busy_timeout.
    """
    db.execute(text("UPDATE users SET token_version = token_version WHERE 0"))


def get_db():
    """Dependency for getting database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
