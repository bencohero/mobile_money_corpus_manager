import argparse
import socket
from app.db import SessionLocal
from app.models import Recording
from app.storage import stat_file, list_files

def classify_storage_error(exc):
    from minio.error import S3Error
    code = getattr(exc, "code", None)
    if code in {"NoSuchKey", "NoSuchObject", "NotFound"}: return "db_without_object"
    if code in {"AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"}: return "storage_permission_denied"
    if isinstance(exc, (TimeoutError, socket.timeout)) or "timeout" in type(exc).__name__.lower(): return "storage_timeout"
    if isinstance(exc, PermissionError): return "storage_permission_denied"
    if isinstance(exc, (ConnectionError, ConnectionRefusedError, OSError)): return "storage_unavailable"
    return "storage_error"
def main():
    parser = argparse.ArgumentParser(description="Read-only PostgreSQL/MinIO reconciliation")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    db = SessionLocal(); expected=set(); findings=[]
    try:
        for rec in db.query(Recording).all():
            if rec.sync_status not in {"READY"}: findings.append({"type":"intermediate_recording","recording_id":rec.id,"status":rec.sync_status})
            for kind, name, size, digest in [("raw", rec.raw_object, rec.raw_size_bytes, rec.raw_sha256), ("wav", rec.wav_object, rec.wav_size_bytes, rec.wav_sha256)]:
                expected.add(name)
                try:
                    info=stat_file(name)
                    if rec.sync_status == "ERROR":
                        findings.append({"type":"failed_recording_object","recording_id":rec.id,"kind":kind})
                    if size is not None and info.size != size: findings.append({"type":"size_mismatch","object":name})
                    if digest:
                        import hashlib
                        data = __import__("app.storage", fromlist=["get_bytes"]).get_bytes(name)
                        if hashlib.sha256(data).hexdigest() != digest: findings.append({"type":"checksum_mismatch","object":name})
                except Exception as exc:
                    classification = classify_storage_error(exc)
                    # ERROR remains visible above, but successful compensation means
                    # absent objects are expected. Never mistake access errors for absence.
                    if not (rec.sync_status == "ERROR" and classification == "db_without_object"):
                        findings.append({"type": classification, "recording_id": rec.id, "kind": kind})
        for obj in list_files():
            if obj.object_name not in expected: findings.append({"type":"orphan_object","object":obj.object_name})
    finally: db.close()
    import json
    print(json.dumps(findings, ensure_ascii=False, indent=2))
    return 1 if findings else 0
if __name__ == "__main__": raise SystemExit(main())
