from urllib.parse import quote

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "localhost"
    trusted_hosts: str = "*"
    database_url: str | None = None
    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str = "mobile-money-corpus-db"
    postgres_port: int = 5432

    jwt_secret: str
    workshop_code_secret: str | None = None
    access_token_minutes: int = 720
    cookie_secure: bool = True
    max_audio_mb: int = 50
    min_audio_duration_seconds: float = 0.25
    max_audio_duration_seconds: float = 120.0
    ffmpeg_timeout_seconds: int = 60
    ffprobe_timeout_seconds: int = 10
    max_concurrent_conversions: int = 2

    minio_endpoint: str = "minio:9000"
    minio_root_user: str | None = None
    minio_root_password: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_secure: bool = False
    minio_bucket: str = "mobile-money-corpus"

    admin_username: str = "admin"
    admin_password: str = "ChangeMeNow!"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_runtime_configuration(self):
        if self.app_env not in {"development", "test", "production"}:
            raise ValueError("APP_ENV must be development, test or production")
        if self.max_audio_mb < 1 or self.min_audio_duration_seconds < 0 or self.max_audio_duration_seconds <= self.min_audio_duration_seconds:
            raise ValueError("Invalid audio duration or size limits")
        if self.ffmpeg_timeout_seconds < 1 or self.ffprobe_timeout_seconds < 1 or self.max_concurrent_conversions < 1:
            raise ValueError("Audio limits and timeouts must be positive")
        if self.app_env == "production":
            forbidden = {
                "change_me", "change_this_db_password", "change_this_minio_password",
                "change_me_now!", "changemenow!", "minioadmin", "minioadmin123", "admin", "password",
                "password123", "secret", "changeme", "changeit",
            }
            if len(self.jwt_secret) < 32 or self.jwt_secret.lower() in forbidden:
                raise ValueError("JWT_SECRET must be strong and non-example in production")
            if not self.workshop_code_secret or len(self.workshop_code_secret) < 32 or self.workshop_code_secret.lower() in forbidden:
                raise ValueError("WORKSHOP_CODE_SECRET must be strong and non-example in production")
            if self.workshop_code_secret == self.jwt_secret:
                raise ValueError("WORKSHOP_CODE_SECRET must be distinct from JWT_SECRET in production")
            if not self.postgres_db or not self.postgres_user or not self.postgres_password or self.postgres_user.lower() in forbidden or self.postgres_password.lower() in forbidden:
                raise ValueError("Explicit PostgreSQL credentials are required in production")
            minio_user = self.minio_root_user or self.minio_access_key
            minio_password = self.minio_root_password or self.minio_secret_key
            if not minio_user or not minio_password or minio_user.lower() in forbidden or minio_password.lower() in forbidden:
                raise ValueError("Explicit non-default MinIO credentials are required in production")
            if len(self.admin_password) < 12 or self.admin_password.lower() in forbidden or not self.cookie_secure:
                raise ValueError("Strong admin password and secure cookies are required in production")
        return self

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        missing = [
            name for name, value in {
                "POSTGRES_DB": self.postgres_db,
                "POSTGRES_USER": self.postgres_user,
                "POSTGRES_PASSWORD": self.postgres_password,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Database configuration is incomplete. Set DATABASE_URL or "
                f"the missing PostgreSQL variables: {', '.join(missing)}."
            )
        user = quote(self.postgres_user or "", safe="")
        password = quote(self.postgres_password or "", safe="")
        db = quote(self.postgres_db or "", safe="")
        return f"postgresql+psycopg://{user}:{password}@{self.postgres_host}:{self.postgres_port}/{db}"

settings = Settings()
