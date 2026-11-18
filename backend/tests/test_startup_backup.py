"""Container start-up (data folder, secret key, migrations) and backups."""

import os
import sqlite3
import stat
import time

import pytest
from pydantic import ValidationError

from app import backup, cli, entrypoint
from app.config import Settings, settings


@pytest.fixture
def sqlite_db(tmp_path, monkeypatch):
    """Point settings at a SQLite file in tmp_path with one table and row."""
    db = tmp_path / "watch.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    conn.close()
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setattr(settings, "BACKUP_DIR", str(tmp_path / "backups"))
    return db


class TestSettings:
    def test_dirs_default_under_data_dir(self, monkeypatch):
        for var in ("UPLOAD_DIR", "BACKUP_DIR"):
            monkeypatch.delenv(var, raising=False)
        s = Settings(SECRET_KEY="k" * 40, DATA_DIR="/srv/d", _env_file=None)
        assert s.UPLOAD_DIR == "/srv/d/uploads"
        assert s.BACKUP_DIR == "/srv/d/backups"

    def test_secret_key_read_from_data_dir(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        (tmp_path / "secret_key").write_text("f" * 64 + "\n")
        s = Settings(DATA_DIR=str(tmp_path), _env_file=None)
        assert s.SECRET_KEY == "f" * 64

    def test_missing_secret_key_is_an_error(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        with pytest.raises(ValidationError, match="no generated key"):
            Settings(DATA_DIR=str(tmp_path), _env_file=None)


class TestEntrypoint:
    def test_prepare_data_dir(self, tmp_path):
        entrypoint.prepare_data_dir(tmp_path / "data")
        assert (tmp_path / "data" / "uploads").is_dir()
        assert (tmp_path / "data" / "backups").is_dir()

    @pytest.mark.skipif(os.getuid() == 0, reason="root can write anywhere")
    def test_unwritable_data_dir_stops_with_hint(self, tmp_path, capsys):
        locked = tmp_path / "locked"
        locked.mkdir()
        locked.chmod(0o500)
        try:
            with pytest.raises(SystemExit):
                entrypoint.prepare_data_dir(locked)
        finally:
            locked.chmod(0o700)
        assert "chown" in capsys.readouterr().err

    def test_secret_key_generated_once(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        entrypoint.ensure_secret_key(tmp_path)
        key_file = tmp_path / "secret_key"
        first = key_file.read_text()
        assert len(first) == 64
        assert stat.S_IMODE(key_file.stat().st_mode) == 0o600
        entrypoint.ensure_secret_key(tmp_path)
        assert key_file.read_text() == first

    def test_secret_key_env_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "x" * 40)
        entrypoint.ensure_secret_key(tmp_path)
        assert not (tmp_path / "secret_key").exists()

    def test_migrate_fresh_database_without_backup(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 'new.db'}")
        monkeypatch.setattr(settings, "BACKUP_DIR", str(tmp_path / "backups"))
        entrypoint.migrate()
        conn = sqlite3.connect(tmp_path / "new.db")
        assert conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0] > 0
        conn.close()
        assert backup.list_backups() == []
        entrypoint.migrate()  # nothing pending: still no backup
        assert backup.list_backups() == []

    def test_migrate_backs_up_existing_database_first(self, sqlite_db):
        entrypoint.migrate()
        saved = backup.list_backups()
        assert len(saved) == 1 and "pre-migration" in saved[0].name
        conn = sqlite3.connect(saved[0])
        assert conn.execute("SELECT x FROM t").fetchone() == (42,)
        conn.close()


class TestBackup:
    def test_backup_copies_data(self, sqlite_db):
        path = backup.backup_database()
        conn = sqlite3.connect(path)
        assert conn.execute("SELECT x FROM t").fetchone() == (42,)
        conn.close()
        assert not list(path.parent.glob("*.part"))

    def test_nothing_to_back_up(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{tmp_path / 'none.db'}")
        assert backup.backup_database() is None

    def test_prune_keeps_recent_and_newest(self, sqlite_db):
        old = backup.backup_database(label="a")
        os.utime(old, (time.time() - 40 * 86400,) * 2)
        recent = backup.backup_database(label="b")
        assert backup.prune_backups(keep_days=30) == 1
        assert backup.list_backups() == [recent]
        os.utime(recent, (time.time() - 90 * 86400,) * 2)
        assert backup.prune_backups(keep_days=30) == 0  # newest is always kept

    def test_due_time(self, sqlite_db, monkeypatch):
        monkeypatch.setattr(settings, "BACKUP_INTERVAL_HOURS", 24)
        assert backup.seconds_until_due() == 0
        backup.backup_database()
        assert 23 * 3600 < backup.seconds_until_due() <= 24 * 3600

    def test_cli_backup(self, sqlite_db, capsys):
        assert cli.main(["backup"]) == 0
        assert "Backup written to" in capsys.readouterr().out
        assert len(backup.list_backups()) == 1


def test_trusted_proxies_accepts_a_network_range():
    """docker-compose.yml suggests TRUSTED_PROXIES=172.16.0.0/12 for a proxy
    on a Docker network; uvicorn must honour X-Forwarded-For from that range."""
    import asyncio

    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

    seen = {}

    async def app(scope, receive, send):
        seen["client"] = scope["client"][0]

    mw = ProxyHeadersMiddleware(app, trusted_hosts="172.16.0.0/12")

    def call(peer):
        scope = {
            "type": "http",
            "client": (peer, 1234),
            "scheme": "http",
            "headers": [(b"x-forwarded-for", b"203.0.113.9")],
        }
        asyncio.run(mw(scope, None, None))
        return seen["client"]

    assert call("172.18.0.5") == "203.0.113.9"
    assert call("10.0.0.7") == "10.0.0.7"
