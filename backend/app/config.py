import os
from typing import Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database: a SQLite file. DATABASE_URL overrides the path.
    DATA_DIR: str = "/data"
    DATABASE_URL: str = ""

    # Security
    # Unset: read from DATA_DIR/secret_key (generated on first start)
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Built web app (index.html and assets/); not served when missing
    WEB_DIR: str = "/app/web"

    # Storage (default: DATA_DIR/uploads and DATA_DIR/backups)
    UPLOAD_DIR: str = ""
    BACKUP_DIR: str = ""
    # Daily database backup inside the app; 0 hours switches it off
    BACKUP_INTERVAL_HOURS: int = 24
    BACKUP_KEEP_DAYS: int = 30
    MAX_UPLOAD_SIZE: int = 20971520  # 20MB
    MAX_DOCUMENT_SIZE: int = 10485760  # 10MB (service documents)
    MAX_IMAGES_PER_WATCH: int = 50
    MAX_DOCUMENTS_PER_SERVICE: int = 20
    # Lifetime of signed /uploads/ URLs (a URL stays valid 1-2x this long)
    UPLOAD_URL_TTL_SECONDS: int = 3600

    # Registration: closed by default. The first admin is created either by
    # registering with INITIAL_ADMIN_EMAIL on an empty database, or with
    # `python -m app.cli create-user EMAIL --admin`.
    ALLOW_REGISTRATION: bool = False
    INITIAL_ADMIN_EMAIL: str = ""

    # Refresh token cookie. None = Secure when the request came over HTTPS.
    COOKIE_SECURE: Optional[bool] = None

    # Per-address request limits (in memory; one app process)
    RATE_LIMIT_ENABLED: bool = True
    # Proxies whose X-Forwarded-For/-Proto are trusted (passed to uvicorn)
    TRUSTED_PROXIES: str = "127.0.0.1"

    # WatchBase Data Feed API key for reference look-up. Optional: an admin can
    # also set it on the Admin page (kept in DATA_DIR/watchbase_api_key).
    # This variable wins when both are set.
    WATCHBASE_API_KEY: str = ""
    # Days a reference look-up result is reused before asking the sources again
    SPEC_LOOKUP_CACHE_DAYS: int = 90

    # Login throttling per account
    LOGIN_MAX_FAILURES: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    @model_validator(mode="after")
    def _fill_defaults_and_check_secret(self):
        if not self.UPLOAD_DIR:
            self.UPLOAD_DIR = os.path.join(self.DATA_DIR, "uploads")
        if not self.BACKUP_DIR:
            self.BACKUP_DIR = os.path.join(self.DATA_DIR, "backups")
        if not self.SECRET_KEY:
            # Written on first start by app.entrypoint
            try:
                with open(self.secret_key_file) as fh:
                    self.SECRET_KEY = fh.read().strip()
            except OSError:
                raise ValueError(
                    "SECRET_KEY is not set and no generated key was found at "
                    f"{self.secret_key_file}"
                ) from None
        if self.SECRET_KEY.strip().upper().startswith("CHANGE_ME"):
            raise ValueError(
                "SECRET_KEY is still the placeholder; generate one with "
                "`openssl rand -hex 32`"
            )
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters; generate one with "
                "`openssl rand -hex 32`"
            )
        return self

    @property
    def secret_key_file(self) -> str:
        return os.path.join(self.DATA_DIR, "secret_key")

    @field_validator("ALGORITHM")
    @classmethod
    def _fixed_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("ALGORITHM must be HS256")
        return value

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"sqlite:///{os.path.join(self.DATA_DIR, 'watch.db')}"

    # extra="ignore": settings from older installs (POSTGRES_*, ...) are ignored
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


settings = Settings()
