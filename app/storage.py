from minio import Minio
import urllib3
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

_http_timeout = urllib3.Timeout(connect=3.0, read=3.0)
_http_client = urllib3.PoolManager(
    cert_reqs="CERT_REQUIRED" if settings.minio_secure else "CERT_NONE",
    timeout=_http_timeout,
    retries=False,
)

client = Minio(
    settings.minio_endpoint,
    access_key=access_key,
    secret_key=secret_key,
    secure=settings.minio_secure,
    http_client=_http_client,
)

def ensure_bucket():
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def check_ready() -> bool:
    """Check MinIO connectivity and bucket availability with bounded client timeouts."""
    return bool(client.bucket_exists(settings.minio_bucket))

def put_file(object_name: str, path: str, content_type: str):
    size = __import__("os").path.getsize(path)
    with open(path, "rb") as f:
        client.put_object(settings.minio_bucket, object_name, f, size, content_type=content_type)

def delete_file(object_name: str):
    from minio.error import S3Error
    try:
        client.remove_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        if exc.code not in {"NoSuchKey", "NoSuchObject", "NotFound"}:
            raise

def stat_file(object_name: str):
    return client.stat_object(settings.minio_bucket, object_name)

def verify_file(object_name: str, expected_size: int, expected_sha256: str):
    """Verify remote bytes with bounded reads before publishing READY."""
    import hashlib
    if stat_file(object_name).size != expected_size:
        raise ValueError("stored object size mismatch")
    response = client.get_object(settings.minio_bucket, object_name)
    digest, size = hashlib.sha256(), 0
    try:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > expected_size: raise ValueError("stored object exceeds expected size")
            digest.update(chunk)
    finally:
        response.close()
        response.release_conn()
    if size != expected_size or digest.hexdigest() != expected_sha256:
        raise ValueError("stored object checksum mismatch")

def list_files(prefix: str = ""):
    return client.list_objects(settings.minio_bucket, prefix=prefix, recursive=True)

def get_bytes(object_name: str) -> bytes:
    resp = client.get_object(settings.minio_bucket, object_name)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()


def stream_file(object_name: str, offset: int = 0, length: int | None = None,
                chunk_size: int = 1024 * 1024):
    """Yield an object in bounded chunks and always release the MinIO response."""
    response = client.get_object(settings.minio_bucket, object_name,
                                 offset=offset, length=length)
    try:
        while chunk := response.read(chunk_size):
            yield chunk
    finally:
        response.close()
        response.release_conn()
