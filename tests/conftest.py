import os
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "p0a1-test-jwt-secret-not-production-32-chars")
os.environ.setdefault("MINIO_ACCESS_KEY", "p0a1-test")
os.environ.setdefault("MINIO_SECRET_KEY", "p0a1-test-password")
