"""The Alembic baseline builds the same schema as the models, with seed data."""

import os

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import text

import app.models  # noqa: F401  (registers every model)
from app.config import settings
from app.database import Base, make_engine

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _alembic_config():
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


def test_upgrade_matches_models_and_seeds(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    cfg = _alembic_config()

    command.upgrade(cfg, "head")

    eng = make_engine(url)
    try:
        with eng.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
            assert diff == []
            counts = {
                t: conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                for t in ("brands", "movement_types", "complications")
            }
            assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []
    finally:
        eng.dispose()
    assert counts == {"brands": 110, "movement_types": 6, "complications": 17}

    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


def test_0003_repairs_two_primary_images(tmp_path, monkeypatch):
    """#206: old data with two primaries (and clashing sort_order) is repaired,
    and afterwards the database refuses a second primary image."""
    import sqlite3

    db_file = tmp_path / "old.db"
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{db_file}")
    cfg = _alembic_config()
    command.upgrade(cfg, "0002")

    a, b, c = "a" * 32, "b" * 32, "c" * 32
    rows = [
        # watch a: two primaries sharing sort_order 0 (the #206 case), one more
        ("1" * 32, a, 1, 0, "2026-01-01 10:00:00"),
        ("2" * 32, a, 1, 0, "2026-01-02 10:00:00"),
        ("3" * 32, a, 0, 1, "2026-01-03 10:00:00"),
        # watch b: images but no primary
        ("4" * 32, b, 0, 0, "2026-01-01 10:00:00"),
        ("5" * 32, b, 0, 1, "2026-01-02 10:00:00"),
        # watch c: already fine, primary is not the first image
        ("6" * 32, c, 0, 0, "2026-01-01 10:00:00"),
        ("7" * 32, c, 1, 1, "2026-01-02 10:00:00"),
    ]
    con = sqlite3.connect(db_file)
    con.executemany(
        "INSERT INTO watch_images (id, watch_id, file_path, file_name, file_size,"
        " mime_type, is_primary, sort_order, source, created_at)"
        " VALUES (?, ?, 'p', 'f', 1, 'image/jpeg', ?, ?, 'user_upload', ?)",
        rows,
    )
    con.commit()
    con.close()

    command.upgrade(cfg, "head")

    con = sqlite3.connect(db_file)
    got = {
        r[0][0]: (r[1], r[2])
        for r in con.execute("SELECT id, is_primary, sort_order FROM watch_images")
    }
    assert got == {
        "1": (1, 0), "2": (0, 1), "3": (0, 2),  # first kept, renumbered
        "4": (1, 0), "5": (0, 1),  # first promoted
        "6": (0, 0), "7": (1, 1),  # untouched
    }
    try:
        con.execute("UPDATE watch_images SET is_primary = 1 WHERE id = ?", ("3" * 32,))
        raise AssertionError("second primary image was accepted")
    except sqlite3.IntegrityError:
        pass
    finally:
        con.close()

    command.downgrade(cfg, "0002")
