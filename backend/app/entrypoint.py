"""Container start: prepare /data, migrate the database, start the server.

1. create DATA_DIR/uploads and DATA_DIR/backups, check they are writable
2. without SECRET_KEY, create DATA_DIR/secret_key once and keep it
3. back up watch.db if a migration is about to run
4. alembic upgrade head
5. exec uvicorn (one process; proxy headers trusted from TRUSTED_PROXIES)
"""

import os
import secrets
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _fail(message: str) -> None:
    print(f"watch-tracker: {message}", file=sys.stderr)
    sys.exit(1)


def prepare_data_dir(data_dir: Path) -> None:
    for sub in ("", "uploads", "backups"):
        folder = data_dir / sub
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _fail(f"cannot create {folder}: {exc}")
        if not os.access(folder, os.W_OK):
            _fail(
                f"{folder} is not writable by user id {os.getuid()}. "
                f"For a bind mount run: chown -R {os.getuid()} <host folder>"
            )


def ensure_secret_key(data_dir: Path) -> None:
    if os.environ.get("SECRET_KEY"):
        return
    key_file = data_dir / "secret_key"
    if key_file.exists():
        return
    fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(secrets.token_hex(32))
    print(f"watch-tracker: generated a secret key in {key_file}")


def _alembic_config():
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def migration_pending(cfg) -> bool:
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from app.config import settings
    from app.database import make_engine

    head = ScriptDirectory.from_config(cfg).get_current_head()
    engine = make_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            current = MigrationContext.configure(conn).get_current_revision()
    finally:
        engine.dispose()
    return current != head


def migrate() -> None:
    from alembic import command
    from app.backup import backup_database, database_path

    cfg = _alembic_config()
    db_file = database_path()
    if db_file is not None and db_file.is_file() and migration_pending(cfg):
        saved = backup_database(label="pre-migration")
        print(f"watch-tracker: database backed up to {saved} before migrating")
    command.upgrade(cfg, "head")


def main() -> None:
    data_dir = Path(os.environ.get("DATA_DIR", "/data"))
    prepare_data_dir(data_dir)
    ensure_secret_key(data_dir)
    migrate()

    port = os.environ.get("PORT", "8000")
    proxies = os.environ.get("TRUSTED_PROXIES", "127.0.0.1")
    args = [
        "uvicorn", "app.main:app",
        "--host", "0.0.0.0",
        "--port", port,
        "--proxy-headers",
        "--forwarded-allow-ips", proxies,
    ]  # fmt: skip
    os.chdir(BACKEND_DIR)
    os.execvp(args[0], args)


if __name__ == "__main__":
    main()
