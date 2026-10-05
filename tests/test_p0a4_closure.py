import json
import os
import subprocess
import tempfile
from pathlib import Path
from app.db import SessionLocal
from app.models import Recording
from app.storage import put_file, delete_file, get_bytes
from minio.error import S3Error
import app.storage as storage

def run_reconcile():
    return subprocess.run(["python3","scripts/reconcile.py","--json"],capture_output=True,text=True)

def test_reconciliation_exhaustive_artificial_anomalies_is_read_only():
    with SessionLocal() as db:
        rec=db.query(Recording).order_by(Recording.id.desc()).first()
        rid=rec.id
        original={"raw_size_bytes":rec.raw_size_bytes,"wav_size_bytes":rec.wav_size_bytes,
                  "raw_sha256":rec.raw_sha256,"wav_sha256":rec.wav_sha256,
                  "sync_status":rec.sync_status,"sync_error":rec.sync_error}
        raw_name,wav_name=rec.raw_object,rec.wav_object
    raw_data=get_bytes(raw_name); wav_data=get_bytes(wav_name)
    orphan_raw="raw/P0A4_ORPHAN/orphan.raw"
    orphan_wav="normalized/P0A4_ORPHAN/orphan.wav"
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"x"
        p.write_bytes(b"orphan")
        put_file(orphan_raw,str(p),"application/octet-stream")
        put_file(orphan_wav,str(p),"audio/wav")
    delete_file(raw_name); delete_file(wav_name)
    with SessionLocal() as db:
        rec=db.get(Recording,rid)
        rec.raw_size_bytes=(rec.raw_size_bytes or 0)+1
        rec.wav_size_bytes=(rec.wav_size_bytes or 0)+1
        rec.raw_sha256="0"*64; rec.wav_sha256="1"*64
        rec.sync_status="PENDING"; rec.sync_error="synthetic failure"; db.commit()
    before=(raw_name,wav_name,orphan_raw,orphan_wav)
    try:
        result=run_reconcile()
        assert result.returncode==1
        findings=json.loads(result.stdout)
        types={x["type"] for x in findings}
        assert {"db_without_object","orphan_object","intermediate_recording"} <= types
        assert "0"*64 not in result.stdout
        with SessionLocal() as db:
            rec=db.get(Recording,rid)
            assert rec.sync_status=="PENDING"
            assert rec.raw_size_bytes==original["raw_size_bytes"]+1
    finally:
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw"; p.write_bytes(raw_data); put_file(raw_name,str(p),"application/octet-stream")
            p.write_bytes(wav_data); put_file(wav_name,str(p),"audio/wav")
        delete_file(orphan_raw); delete_file(orphan_wav)
        with SessionLocal() as db:
            rec=db.get(Recording,rid)
            for key,value in original.items(): setattr(rec,key,value)
            db.commit()

def test_minio_not_found_is_distinguished_from_generic_failure(monkeypatch):
    class MissingClient:
        def remove_object(self,*args,**kwargs):
            raise S3Error("NoSuchKey","missing","/x","req","host",None)
    monkeypatch.setattr(storage,"client",MissingClient())
    storage.delete_file("missing")
    class DownClient:
        def remove_object(self,*args,**kwargs):
            raise RuntimeError("minio unavailable")
    monkeypatch.setattr(storage,"client",DownClient())
    try:
        storage.delete_file("down")
    except RuntimeError as exc:
        assert "unavailable" in str(exc)
    else:
        raise AssertionError("generic MinIO failure was hidden")
