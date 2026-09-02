from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str | None = None
    postgres_db: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str = "mobile-money-corpus-db"
    postgres_port: int = 5432

    jwt_secret: str
    access_token_minutes: int = 720
    cookie_secure: bool = True
    max_audio_mb: int = 50
    ffmpeg_timeout_seconds: int = 60

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
