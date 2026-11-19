"""The WatchBase API key: from WATCHBASE_API_KEY, or set by an admin.

An admin-set key lives in DATA_DIR/watchbase_api_key (mode 0600), next to
the generated secret_key. The key is never logged and never returned by the
API; callers only learn whether one is configured.
"""

import os
import tempfile

from app.config import settings

KEY_FILE_NAME = "watchbase_api_key"


def _key_file() -> str:
    return os.path.join(settings.DATA_DIR, KEY_FILE_NAME)


def get_watchbase_key() -> str:
    if settings.WATCHBASE_API_KEY.strip():
        return settings.WATCHBASE_API_KEY.strip()
    try:
        with open(_key_file()) as fh:
            return fh.read().strip()
    except OSError:
        return ""


def key_status() -> dict:
    return {
        "configured": bool(get_watchbase_key()),
        "from_environment": bool(settings.WATCHBASE_API_KEY.strip()),
    }


def save_watchbase_key(key: str) -> None:
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=settings.DATA_DIR, prefix=".wbkey-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(key.strip())
        os.replace(tmp, _key_file())
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def clear_watchbase_key() -> None:
    try:
        os.unlink(_key_file())
    except FileNotFoundError:
        pass
