import pytest
from app.config import Settings
def test_test_configuration_is_valid():
    settings = Settings(_env_file=None, app_env="test", jwt_secret="x"*32, database_url="sqlite+pysqlite:///:memory:")
    assert settings.app_env == "test"
def test_production_rejects_short_jwt():
    with pytest.raises(ValueError):
        Settings(_env_file=None, app_env="production", jwt_secret="short", database_url="postgresql+psycopg://u:p@db/x", postgres_db="x", postgres_user="u", postgres_password="p", minio_root_user="u", minio_root_password="p", admin_password="strong-password", cookie_secure=True)
def test_production_requires_secure_cookie():
    with pytest.raises(ValueError):
        Settings(_env_file=None, app_env="production", jwt_secret="x"*32, database_url="postgresql+psycopg://u:p@db/x", postgres_db="x", postgres_user="u", postgres_password="different", minio_root_user="different", minio_root_password="different", admin_password="strong-password", cookie_secure=False)
def test_production_error_does_not_contain_secret():
    secret="x"*32
    with pytest.raises(ValueError) as exc:
        Settings(_env_file=None, app_env="production", jwt_secret=secret, database_url="postgresql+psycopg://u:p@db/x", postgres_db="x", postgres_user="u", postgres_password="different", minio_root_user="different", minio_root_password="different", admin_password="strong-password", cookie_secure=False)
    assert secret not in str(exc.value)


def test_production_requires_distinct_workshop_code_secret():
    with pytest.raises(ValueError, match="WORKSHOP_CODE_SECRET"):
        Settings(_env_file=None, app_env="production", jwt_secret="j"*32, database_url="postgresql+psycopg://u:p@db/x", postgres_db="x", postgres_user="different", postgres_password="different", minio_root_user="different", minio_root_password="different", admin_password="strong-password", cookie_secure=True)


def test_production_accepts_strong_workshop_code_secret():
    value = Settings(_env_file=None, app_env="production", jwt_secret="j"*32, workshop_code_secret="w"*32, database_url="postgresql+psycopg://u:p@db/x", postgres_db="x", postgres_user="different", postgres_password="different", minio_root_user="different", minio_root_password="different", admin_password="strong-password", cookie_secure=True)
    assert value.workshop_code_secret == "w"*32


def test_production_rejects_default_minio_credentials():
    with pytest.raises(ValueError, match="non-default MinIO"):
        Settings(_env_file=None, app_env="production", jwt_secret="j"*32, workshop_code_secret="w"*32, database_url="postgresql+psycopg://u:p@db/x", postgres_db="x", postgres_user="different", postgres_password="different", minio_root_user="minioadmin", minio_root_password="minioadmin", admin_password="strong-password", cookie_secure=True)
