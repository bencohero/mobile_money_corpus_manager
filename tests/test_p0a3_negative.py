import io
import os
import re
import subprocess
import tempfile
import threading
import wave
import uuid
import hashlib
from concurrent.futures import ThreadPoolExecutor
import httpx
import pytest
from sqlalchemy.exc import IntegrityError
from app import main
from app.db import SessionLocal
from app.models import Recording, User
from app.storage import get_bytes, put_file, delete_file, stat_file

BASE = "http://app-test:8000"

def token(c):
    return c.cookies.get("csrf_token")

def login(name, password):
    c = httpx.Client(base_url=BASE, follow_redirects=False, timeout=30)
    page = c.get("/login")
    r = c.post("/login", data={"username": name, "password": password, "csrf_token": page.cookies.get("csrf_token") or c.cookies.get("csrf_token")})
    assert r.status_code == 303
    return c

def wav(seconds):
    out=io.BytesIO()
    with wave.open(out,"wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(16000)
        f.writeframes(b"\0\0"*int(16000*seconds))
    return out.getvalue()

def ensure_http_fixture():
    """Create the negative-test corpus instead of relying on another module's order."""
    with SessionLocal() as db:
        existing = db.query(Recording).join(User, Recording.participant_id == User.participant_id).filter(User.username == "p0a2-participant").first()
        if existing:
            return
    admin = login("admin", os.environ["ADMIN_PASSWORD"])
    users_page = admin.get("/users").text
    if "p0a2-participant" not in users_page:
        response = admin.post("/participants", data={
            "participant_code": "P0A2_S001",
            "username": "p0a2-participant",
            "password": "p0a2-participant-password",
            "language": "mos",
            "consent_obtained": "on",
            "csrf_token": token(admin),
        })
        assert response.status_code == 303
    users_page = admin.get("/users").text
    if "p0a2-other" not in users_page:
        response = admin.post("/participants", data={
            "participant_code": "P0A2_S002",
            "username": "p0a2-other",
            "password": "p0a2-other-password",
            "language": "mos",
            "consent_obtained": "on",
            "csrf_token": token(admin),
        })
        assert response.status_code == 303
    for username, password, role in (
        ("p0a2-transcriber", "p0a2-transcriber-password", "TRANSCRIBER"),
        ("p0a2-validator", "p0a2-validator-password", "VALIDATOR"),
    ):
        if username not in admin.get("/users").text:
            response = admin.post("/users", data={
                "username": username,
                "password": password,
                "role": role,
                "csrf_token": token(admin),
            })
            assert response.status_code == 303
    owner = login("p0a2-participant", "p0a2-participant-password")
    utterance = re.search(r'<option value="(\d+)"', owner.get("/record").text).group(1)
    response = owner.post(
        "/api/recordings",
        data={"utterance_id": utterance, "idempotency_key": uuid.uuid4().hex, "condition": "CLEAN"},
        files={"audio": ("fixture.wav", wav(.8), "audio/wav")},
        headers={"X-CSRF-Token": token(owner)},
    )
    assert response.status_code == 200, response.text
    owner.close(); admin.close()

def remaining_recording():
    ensure_http_fixture()
    with SessionLocal() as db:
        owner_id = db.query(User.participant_id).filter(User.username == "p0a2-participant").scalar()
        r=db.query(Recording).filter(Recording.participant_id == owner_id).order_by(Recording.id.desc()).first()
        assert r is not None
        return r.id, r.participant_id, r.raw_object, r.wav_object

def test_http_permission_matrix_idor_sessions_and_csrf():
    rid, pid, _, _ = remaining_recording()
    admin=login("admin", os.environ["ADMIN_PASSWORD"])
    owner=login("p0a2-participant","p0a2-participant-password")
    tier=login("p0a2-other","p0a2-other-password")
    trans=login("p0a2-transcriber","p0a2-transcriber-password")
    validator=login("p0a2-validator","p0a2-validator-password")
    assert admin.get("/").status_code == 200
    assert admin.get("/participants").status_code == 200
    assert admin.get("/users").status_code == 200
    assert admin.get("/recordings").status_code == 200
    assert owner.get("/").status_code == 200
    assert owner.get("/record").status_code == 200
    assert owner.get("/recordings").status_code == 200
    assert owner.get(f"/audio/{rid}").status_code == 200
    assert owner.get(f"/transcribe/{rid}").status_code == 200
    assert owner.get("/participants").status_code == 403
    assert owner.get("/users").status_code == 403
    assert owner.get("/export/recordings.csv").status_code == 403
    assert owner.get(f"/audio/{rid+99999}").status_code == 404
    assert tier.get(f"/audio/{rid}").status_code == 403
    assert tier.get(f"/transcribe/{rid}").status_code == 403
    assert tier.post(f"/verify/{rid}", data={"decision":"VERIFIED","csrf_token":token(tier)}).status_code == 403
    assert trans.get("/recordings").status_code == 200
    assert trans.get(f"/audio/{rid}").status_code == 200
    assert trans.get(f"/transcribe/{rid}").status_code == 200
    assert trans.get("/participants").status_code == 403
    assert trans.get("/export/recordings.csv").status_code == 403
    assert trans.post(f"/verify/{rid}", data={"decision":"VERIFIED","csrf_token":token(trans)}).status_code == 403
    assert validator.get("/recordings").status_code == 200
    assert validator.get(f"/audio/{rid}").status_code == 200
    assert validator.get(f"/transcribe/{rid}").status_code == 200
    assert validator.get("/users").status_code == 403
    assert validator.get("/export/recordings.csv").status_code == 403
    assert validator.post(f"/recordings/{rid}/delete", data={"csrf_token":token(validator)}).status_code == 403
    anonymous=httpx.Client(base_url=BASE,follow_redirects=False)
    assert anonymous.get("/").status_code == 303
    assert anonymous.get("/recordings").status_code == 401
    assert anonymous.post("/logout",data={"csrf_token":"x"}).status_code == 403
    bad=httpx.Client(base_url=BASE,follow_redirects=False)
    bad.cookies.set("session","invalid")
    assert bad.get("/recordings").status_code == 401
    assert owner.post("/logout",data={"csrf_token":"wrong"}).status_code == 403
    assert owner.post(f"/transcribe/{rid}",data={"reference_transcription":"x","csrf_token":""}).status_code == 403
    for c in (admin,owner,tier,trans,validator,anonymous,bad): c.close()

def test_audio_negative_inputs_have_controlled_responses_and_no_ready_rows():
    ensure_http_fixture()
    c=login("p0a2-participant","p0a2-participant-password")
    utterance=re.search(r'<option value="(\d+)"',c.get("/record").text).group(1)
    cases=[(31,b"","audio/wav",400),(32,b"not audio","audio/wav",422),(33,os.urandom(128),"audio/wav",422),(34,wav(0.05),"audio/wav",422)]
    for take,body,mime,expected in cases:
        r=c.post("/api/recordings",data={"utterance_id":utterance,"idempotency_key":uuid.uuid4().hex,"condition":"CLEAN"},files={"audio":("x.wav",body,mime)},headers={"X-CSRF-Token":token(c)})
        assert r.status_code == expected, (take,r.status_code,r.text)
        assert "Traceback" not in r.text and "/tmp" not in r.text
        if "recording_id" in r.json():
            rid = r.json()["recording_id"]
            with SessionLocal() as db:
                assert db.get(Recording, rid).sync_status == "ERROR"
            admin=login("admin",os.environ["ADMIN_PASSWORD"])
            assert admin.post(f"/recordings/{rid}/delete",data={"csrf_token":token(admin)}).status_code==303
            admin.close()
    c.close()

def test_concurrent_uploads_return_distinct_takes_and_valid_objects():
    ensure_http_fixture()
    c1=login("p0a2-participant","p0a2-participant-password")
    c2=login("p0a2-participant","p0a2-participant-password")
    utterance=re.search(r'<option value="(\d+)"',c1.get("/record").text).group(1)
    def send(c):
        return c.post("/api/recordings",data={"utterance_id":utterance,"idempotency_key":uuid.uuid4().hex,"condition":"CLEAN"},files={"audio":("x.wav",wav(.8),"audio/wav")},headers={"X-CSRF-Token":token(c)})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(send,[c1,c2]))
    assert sorted(r.status_code for r in results)==[200,200]
    assert len({r.json()["take_number"] for r in results}) == 2
    ids = [r.json()["recording_id"] for r in results]
    with SessionLocal() as db:
        rows=db.query(Recording).filter(Recording.id.in_(ids)).all()
        assert len(rows)==2
        for row in rows:
            for kind in ("raw", "wav"):
                data = get_bytes(getattr(row, kind + "_object"))
                assert len(data) == getattr(row, kind + "_size_bytes")
                assert hashlib.sha256(data).hexdigest() == getattr(row, kind + "_sha256")
    admin=login("admin",os.environ["ADMIN_PASSWORD"])
    for rid in ids:
        assert admin.post(f"/recordings/{rid}/delete",data={"csrf_token":token(admin)}).status_code==303
    for c in (c1,c2,admin): c.close()

def test_compensation_attempts_all_objects_even_if_one_delete_fails(monkeypatch, caplog):
    seen=[]
    def remove(name):
        seen.append(name)
        if name=="raw": raise RuntimeError("network")
    monkeypatch.setattr(main,"delete_file",remove)
    main.compensate_uploaded(["raw","wav"], type("R",(),{"headers":{}})())
    assert seen==["raw","wav"]
    assert "MinIO compensation failed" in caplog.text

def test_audio_command_releases_slot_after_exception():
    class S:
        def __init__(self): self.n=0
        def acquire(self,blocking=False): return True
        def release(self): self.n+=1
    s=S()
    main.CONVERSION_SLOTS=s
    with pytest.raises(subprocess.CalledProcessError):
        main.run_audio_command(["false"], check=True)
    assert s.n==1

def test_reconciliation_detects_checksum_and_size_mismatch():
    rid,_,raw,wavname=remaining_recording()
    with SessionLocal() as db:
        r=db.get(Recording,rid); old=(r.raw_size_bytes,r.raw_sha256,r.sync_status)
        r.raw_size_bytes=(r.raw_size_bytes or 0)+1; r.raw_sha256="0"*64; r.sync_status="PENDING"; db.commit()
    try:
        p=subprocess.run(["python3","scripts/reconcile.py","--json"],capture_output=True,text=True)
        assert p.returncode==1
        assert "size_mismatch" in p.stdout and "checksum_mismatch" in p.stdout and "intermediate_recording" in p.stdout
    finally:
        with SessionLocal() as db:
            r=db.get(Recording,rid); r.raw_size_bytes,r.raw_sha256,r.sync_status=old; db.commit()
