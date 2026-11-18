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
