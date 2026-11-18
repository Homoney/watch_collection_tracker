"""SQLite backups: online copies into BACKUP_DIR, pruned after BACKUP_KEEP_DAYS.

Uses SQLite's backup API, which is safe while the app is running. Restore:
stop the container, copy a backup over DATA_DIR/watch.db, start it again.
"""

import asyncio
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.engine import make_url

from app.config import settings

logger = logging.getLogger(__name__)

PREFIX = "watch-"


def database_path() -> Optional[Path]:
    """Path of the SQLite file, or None for another database."""
    url = make_url(settings.database_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        return None
    return Path(url.database)


def backup_database(label: str = "") -> Optional[Path]:
    """Copy the database into BACKUP_DIR. Returns the file, or None if nothing to copy."""
    source = database_path()
    if source is None or not source.is_file():
        return None
    dest_dir = Path(settings.BACKUP_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = f"-{label}" if label else ""
    dest = dest_dir / f"{PREFIX}{stamp}{suffix}.db"
    tmp = dest.with_suffix(".db.part")
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    try:
        out = sqlite3.connect(tmp)
        try:
            src.backup(out)
        finally:
            out.close()
    finally:
        src.close()
    tmp.replace(dest)
    return dest


def list_backups() -> list:
    folder = Path(settings.BACKUP_DIR)
    if not folder.is_dir():
        return []
    return sorted(folder.glob(f"{PREFIX}*.db"), key=lambda p: p.stat().st_mtime)


def prune_backups(keep_days: Optional[int] = None, now: Optional[float] = None) -> int:
    """Delete backups older than keep_days. Always keeps the newest one."""
    keep_days = settings.BACKUP_KEEP_DAYS if keep_days is None else keep_days
    now = time.time() if now is None else now
    backups = list_backups()
    removed = 0
    for path in backups[:-1]:
        if now - path.stat().st_mtime > keep_days * 86400:
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def seconds_until_due(now: Optional[float] = None) -> float:
    interval = settings.BACKUP_INTERVAL_HOURS * 3600
    backups = list_backups()
    if not backups:
        return 0.0
    now = time.time() if now is None else now
    return max(0.0, backups[-1].stat().st_mtime + interval - now)


def run_scheduled_backup() -> Optional[Path]:
    path = backup_database()
    removed = prune_backups()
    if path:
        logger.info("Database backup written to %s (%d old removed)", path, removed)
    return path


async def backup_loop() -> None:
    """Back up when the newest backup is older than the interval, then repeat."""
    while True:
        await asyncio.sleep(seconds_until_due())
        try:
            await asyncio.to_thread(run_scheduled_backup)
        except Exception:  # keep the loop alive; the next run tries again
            logger.exception("Scheduled database backup failed")
            await asyncio.sleep(3600)
            continue
        if not list_backups():  # nothing to back up yet (empty install)
            await asyncio.sleep(settings.BACKUP_INTERVAL_HOURS * 3600)
