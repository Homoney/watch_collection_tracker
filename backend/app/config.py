from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost"

    # Storage
    UPLOAD_DIR: str = "/app/storage/uploads"
    BACKUP_DIR: str = "/app/storage/backups"
    MAX_UPLOAD_SIZE: int = 20971520  # 20MB
    # Lifetime of signed /uploads/ URLs (a URL stays valid 1-2x this long)
    UPLOAD_URL_TTL_SECONDS: int = 3600

    # Registration: closed by default. The first admin is created either by
    # registering with INITIAL_ADMIN_EMAIL on an empty database, or with
    # `python -m app.cli create-user EMAIL --admin`.
    ALLOW_REGISTRATION: bool = False
    INITIAL_ADMIN_EMAIL: str = ""

    # Refresh token cookie. None = Secure when the request came over HTTPS.
    COOKIE_SECURE: Optional[bool] = None

    # Login throttling per account
    LOGIN_MAX_FAILURES: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
