"""The app runs on SQLite: types, pragmas, search and the sign-up lock."""

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.config import Settings
from app.database import make_engine, take_write_lock
from app.models.movement_accuracy import MovementAccuracyReading
from app.models.watch import Watch

KEY = "k" * 40


class TestDatabaseUrl:
    def test_default_is_sqlite_in_data_dir(self, monkeypatch):
        for var in ("DATABASE_URL", "POSTGRES_USER"):
            monkeypatch.delenv(var, raising=False)
        s = Settings(SECRET_KEY=KEY, DATA_DIR="/srv/x", _env_file=None)
        assert s.database_url == "sqlite:////srv/x/watch.db"

    def test_database_url_wins(self, monkeypatch):
        monkeypatch.delenv("POSTGRES_USER", raising=False)
        s = Settings(SECRET_KEY=KEY, DATABASE_URL="sqlite:///tmp/a.db", _env_file=None)
        assert s.database_url == "sqlite:///tmp/a.db"


class TestPragmas:
    def test_foreign_keys_wal_and_timeout(self, test_db):
        conn = test_db.connection()
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert conn.execute(text("PRAGMA busy_timeout")).scalar() == 5000

    def test_cascade_delete_is_enforced(self, test_db, test_watch):
        reading = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=datetime.now(timezone.utc),
            watch_seconds_position=0,
            is_initial_reading=True,
        )
        test_db.add(reading)
        test_db.commit()
        test_db.execute(text("DELETE FROM watches WHERE id = :i"), {"i": test_watch.id.hex})
        test_db.commit()
        assert test_db.query(MovementAccuracyReading).count() == 0


class TestTypes:
    def test_utc_datetime_round_trip(self, test_db, test_watch):
        aware = datetime(2026, 5, 1, 12, 0, tzinfo=timezone(timedelta(hours=2)))
        reading = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=aware,
            watch_seconds_position=15,
            is_initial_reading=True,
        )
        test_db.add(reading)
        test_db.commit()
        test_db.expire_all()
        stored = test_db.get(MovementAccuracyReading, reading.id).reference_time
        assert stored.tzinfo is not None
        assert stored == aware
        assert stored.hour == 10  # kept as UTC

    def test_uuid_accepts_strings(self, test_db, test_watch):
        assert test_db.get(Watch, test_watch.id) is not None
        found = test_db.query(Watch).filter(Watch.id == str(test_watch.id)).one()
        assert found.id == test_watch.id

    def test_complications_json(self, test_db, test_watch):
        test_watch.complications = ["date", "chronograph"]
        test_db.commit()
        test_db.expire_all()
        assert test_db.get(Watch, test_watch.id).complications == ["date", "chronograph"]


class TestSearch:
    def test_search_matches_model_and_brand_case_insensitively(
        self, client, auth_headers, test_watch, test_brand
    ):
        for term in (test_watch.model[:4].upper(), test_brand.name.lower()):
            r = client.get("/api/v1/watches/", params={"search": term}, headers=auth_headers)
            assert r.status_code == 200
            assert r.json()["total"] == 1, term

    def test_search_no_match(self, client, auth_headers, test_watch):
        r = client.get(
            "/api/v1/watches/", params={"search": "zz-no-such"}, headers=auth_headers
        )
        assert r.json()["total"] == 0


class TestWriteLock:
    def test_second_writer_waits_for_the_lock(self, test_db, tmp_path):
        db_file = tmp_path / "lock.db"
        eng = make_engine(f"sqlite:///{db_file}")
        with eng.begin() as conn:
            conn.execute(text("CREATE TABLE users (token_version INTEGER)"))
        from sqlalchemy.orm import sessionmaker

        session = sessionmaker(bind=eng)()
        try:
            take_write_lock(session, 1)
            other = sqlite3.connect(db_file, timeout=0.1)
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                other.execute("INSERT INTO users VALUES (1)")
            other.close()
        finally:
            session.rollback()
            session.close()
            eng.dispose()
