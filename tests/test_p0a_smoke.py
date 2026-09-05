import os
os.environ.setdefault("APP_ENV","test")
os.environ.setdefault("JWT_SECRET","test-secret-with-more-than-32-characters-12345")
os.environ.setdefault("DATABASE_URL","sqlite+pysqlite:///:memory:")
os.environ.setdefault("MINIO_ACCESS_KEY","test-user")
os.environ.setdefault("MINIO_SECRET_KEY","test-password")
def test_configuration_imports():
    from app.config import Settings
    value=Settings(_env_file=None, jwt_secret=os.environ["JWT_SECRET"], app_env="test", database_url=os.environ["DATABASE_URL"])
    assert value.cookie_secure is False
    assert value.max_concurrent_conversions >= 1
