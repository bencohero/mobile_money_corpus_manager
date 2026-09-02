from io import BytesIO
from minio import Minio
from .config import settings

# The bundled MinIO service is initialized with MINIO_ROOT_USER/MINIO_ROOT_PASSWORD.
# Prefer those values so the app and the MinIO container cannot drift when an
# old .env still contains stale MINIO_ACCESS_KEY/MINIO_SECRET_KEY values.
access_key = settings.minio_root_user or settings.minio_access_key
secret_key = settings.minio_root_password or settings.minio_secret_key

if not access_key or not secret_key:
    raise RuntimeError(
        "MinIO credentials are missing. Set MINIO_ACCESS_KEY/MINIO_SECRET_KEY "
        "or MINIO_ROOT_USER/MINIO_ROOT_PASSWORD."
    )

client = Minio(
    settings.minio_endpoint,
    access_key=access_key,
    secret_key=secret_key,
    secure=settings.minio_secure,
)

def ensure_bucket():
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)

def put_file(object_name: str, path: str, content_type: str):
    size = __import__("os").path.getsize(path)
    with open(path, "rb") as f:
        client.put_object(settings.minio_bucket, object_name, f, size, content_type=content_type)

def delete_file(object_name: str):
    client.remove_object(settings.minio_bucket, object_name)

def get_bytes(object_name: str) -> bytes:
    resp = client.get_object(settings.minio_bucket, object_name)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()
