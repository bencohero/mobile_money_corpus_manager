import hashlib
import io
import os
import re
import shutil
import subprocess
import uuid
import wave
import wave
from types import SimpleNamespace

import pytest
from minio import Minio
from sqlalchemy import event
from sqlalchemy.orm import Session as OrmSession
from starlette.testclient import TestClient

from app import main, storage
from app.auth import hash_password
from app.db import SessionLocal
from app.models import AuditLog, Participant, Recording, User
from scripts.reconcile import classify_storage_error


def wav_bytes(seconds=0.8, channels=1, width=2, rate=16000):
    out = io.BytesIO()
    with wave.open(out, "wb") as f:
        f.setnchannels(channels); f.setsampwidth(width); f.setframerate(rate)
        f.writeframes(b"\0" * int(rate * seconds * channels * width))
    return out.getvalue()


def login(client, username, password):
    page = client.get("/login")
    csrf = page.cookies.get("csrf_token") or client.cookies.get("csrf_token")
    response = client.post("/login", data={"username": username, "password": password, "csrf_token": csrf})
    assert response.status_code == 303


def seed_users():
    suffix = uuid.uuid4().hex[:10]
    with SessionLocal() as db:
        participant = Participant(participant_code=f"REMED_{suffix}", language="mos", consent_obtained=True)
        db.add(participant); db.flush()
        owner = User(username=f"owner_{suffix}", password_hash=hash_password("owner-password-only"), role="PARTICIPANT", participant_id=participant.id)
        transcriber = User(username=f"trans_{suffix}", password_hash=hash_password("trans-password-only"), role="TRANSCRIBER")
        validator = User(username=f"valid_{suffix}", password_hash=hash_password("valid-password-only"), role="VALIDATOR")
        db.add_all([owner, transcriber, validator]); db.commit()
        return participant.id, participant.participant_code, owner.username, transcriber.username, validator.username


@pytest.fixture
def context():
    ids = seed_users()
    try:
        with TestClient(main.app, follow_redirects=False) as client:
            yield client, ids
    finally:
        with SessionLocal() as db:
            users = db.query(User).filter(User.username.in_(ids[2:])).all()
            participant = db.get(Participant, ids[0])
            db.query(AuditLog).filter(AuditLog.user_id.in_([u.id for u in users])).delete(synchronize_session=False)
            for user in users: db.delete(user)
            if participant:
                for rec in list(participant.recordings):
                    for name in (rec.raw_object, rec.wav_object):
                        try: storage.delete_file(name)
                        except Exception: pass
                    db.delete(rec)
                db.delete(participant)
            db.commit()


def utterance_id(client):
    match = re.search(r'<option value="(\d+)"', client.get("/record").text)
    assert match
    return match.group(1)


def upload(client, utterance, take, body=None, mime="audio/wav"):
    return client.post("/api/recordings",
        data={"utterance_id": utterance, "take_number": str(take), "condition": "CLEAN"},
        files={"audio": ("synthetic.wav", body if body is not None else wav_bytes(), mime)},
        headers={"X-CSRF-Token": client.cookies.get("csrf_token")})


def test_real_minio_unavailable_before_upload_has_controlled_rollback(context):
    client, (_, _, owner_name, _, _) = context
    login(client, owner_name, "owner-password-only"); utterance = utterance_id(client)
    original = storage.client
    storage.client = Minio("minio-test:19999", access_key="test-only", secret_key="test-only", secure=False)
    try: response = upload(client, utterance, 801)
    finally: storage.client = original
    assert response.status_code == 502
    assert "Traceback" not in response.text and "/tmp" not in response.text
    with SessionLocal() as db: assert db.query(Recording).filter_by(take_number=801).count() == 0
    assert client.get("/recordings").status_code == 200


def test_second_object_failure_compensates_real_raw_object(context, monkeypatch):
    client, (_, code, owner_name, _, _) = context
    login(client, owner_name, "owner-password-only"); utterance = utterance_id(client)
    original, calls = main.put_file, []
    def fail_second(name, *args, **kwargs):
        calls.append(name)
        if len(calls) == 2: raise RuntimeError("isolated second object failure")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(main, "put_file", fail_second)
    response = upload(client, utterance, 802)
    assert response.status_code == 502 and len(calls) == 2
    with SessionLocal() as db: assert db.query(Recording).filter_by(take_number=802).count() == 0
    assert list(storage.list_files(f"raw/{code}")) == []
    assert list(storage.list_files(f"normalized/{code}")) == []


def test_commit_failure_compensates_both_real_objects_and_session_recovers(context):
    client, (_, code, owner_name, _, _) = context
    login(client, owner_name, "owner-password-only"); utterance = utterance_id(client)
    armed = {"value": True}
    def fail_once(session):
        if armed["value"]:
            armed["value"] = False; raise RuntimeError("isolated database commit failure")
    event.listen(OrmSession, "before_commit", fail_once)
    try: response = upload(client, utterance, 803)
    finally: event.remove(OrmSession, "before_commit", fail_once)
    assert response.status_code == 502
    with SessionLocal() as db: assert db.query(Recording).filter_by(take_number=803).count() == 0
    assert list(storage.list_files(f"raw/{code}")) == []
    assert list(storage.list_files(f"normalized/{code}")) == []
    assert client.get("/recordings").status_code == 200


def test_partial_compensation_leaves_real_orphan_detected_by_reconcile(context, monkeypatch):
    client, (_, code, owner_name, _, _) = context
    login(client, owner_name, "owner-password-only"); utterance = utterance_id(client)
    original_put, original_delete = main.put_file, main.delete_file
    def fail_wav(name, *args, **kwargs):
        if name.startswith("normalized/"): raise RuntimeError("isolated WAV failure")
        return original_put(name, *args, **kwargs)
    def fail_raw_delete(name):
        if name.startswith("raw/"): raise PermissionError("isolated compensation permission failure")
        return original_delete(name)
    monkeypatch.setattr(main, "put_file", fail_wav); monkeypatch.setattr(main, "delete_file", fail_raw_delete)
    response = upload(client, utterance, 804)
    assert response.status_code == 502 and list(storage.list_files(f"raw/{code}"))
    result = subprocess.run(["python3", "scripts/reconcile.py", "--json"], capture_output=True, text=True)
    assert result.returncode == 1 and "orphan_object" in result.stdout
    for obj in list(storage.list_files(f"raw/{code}")): original_delete(obj.object_name)


def test_partial_delete_is_not_silent_and_retry_succeeds(context, monkeypatch):
    client, (_, code, owner_name, _, _) = context
    login(client, owner_name, "owner-password-only")
    response = upload(client, utterance_id(client), 805); assert response.status_code == 200
    rid = response.json()["recording_id"]; admin = TestClient(main.app, follow_redirects=False); login(admin, "admin", os.environ["ADMIN_PASSWORD"]); original = main.delete_file; calls = []
    def fail_second(name):
        calls.append(name)
        if len(calls) == 2: raise TimeoutError("isolated MinIO timeout")
        return original(name)
    monkeypatch.setattr(main, "delete_file", fail_second)
    failed = admin.post(f"/recordings/{rid}/delete", data={"csrf_token": admin.cookies.get("csrf_token")})
    assert failed.status_code == 502 and "timeout" not in failed.text.lower()
    with SessionLocal() as db: assert db.get(Recording, rid) is not None
    assert list(storage.list_files(f"normalized/{code}"))
    monkeypatch.setattr(main, "delete_file", original)
    assert admin.post(f"/recordings/{rid}/delete", data={"csrf_token": admin.cookies.get("csrf_token")}).status_code == 303
    assert list(storage.list_files(f"raw/{code}")) == [] and list(storage.list_files(f"normalized/{code}")) == []


@pytest.mark.parametrize("exc,expected", [(TimeoutError("timeout"), "storage_timeout"), (PermissionError("denied"), "storage_permission_denied"), (ConnectionRefusedError("refused"), "storage_unavailable"), (RuntimeError("backend"), "storage_error")])
def test_reconcile_storage_errors_are_distinct(exc, expected):
    assert classify_storage_error(exc) == expected


@pytest.mark.parametrize("seconds,expected", [(0.249, 422), (0.25, 200), (0.8, 200), (120.0, 200), (120.001, 422)])
def test_duration_boundaries_cross_upload_route(context, monkeypatch, seconds, expected):
    client, (_, _, owner_name, _, _) = context
    login(client, owner_name, "owner-password-only"); utterance = utterance_id(client)
    def fake_command(args, **kwargs):
        if args[0] == "ffmpeg": shutil.copy(args[5], args[-1]); return SimpleNamespace(stdout="", stderr=b"")
        return SimpleNamespace(stdout=str(seconds), stderr="")
    monkeypatch.setattr(main, "run_audio_command", fake_command)
    take = 810 + (0.249, 0.25, 0.8, 120.0, 120.001).index(seconds); response = upload(client, utterance, take)
    assert response.status_code == expected and "Traceback" not in response.text and "/tmp" not in response.text
    with SessionLocal() as db:
        rows = db.query(Recording).filter_by(take_number=take).all()
        assert bool(rows) is (expected == 200)
        if rows: assert rows[0].sync_status == "READY"


@pytest.mark.parametrize("kind", ["ffmpeg_timeout", "ffprobe_timeout", "wav_empty"])
def test_audio_failures_cross_upload_route_without_ready(context, monkeypatch, kind):
    client, (_, _, owner_name, _, _) = context
    login(client, owner_name, "owner-password-only"); utterance = utterance_id(client)
    def fail_command(args, **kwargs):
        if kind == "ffmpeg_timeout" or (kind == "ffprobe_timeout" and args[0] == "ffprobe"):
            raise subprocess.TimeoutExpired(args[0], 1)
        if kind == "wav_empty": open(args[-1], "wb").close()
        else: shutil.copy(args[5], args[-1])
        return SimpleNamespace(stdout="0.8", stderr=b"")
    monkeypatch.setattr(main, "run_audio_command", fail_command)
    take = 850 + ["ffmpeg_timeout", "ffprobe_timeout", "wav_empty"].index(kind)
    response = upload(client, utterance, take)
    assert response.status_code in {422, 502} and "Traceback" not in response.text and "/tmp" not in response.text
    with SessionLocal() as db: assert db.query(Recording).filter_by(take_number=take).count() == 0


def test_real_checksum_and_wav_properties(context):
    client, (_, _, owner_name, _, _) = context
    login(client, owner_name, "owner-password-only")
    response = upload(client, utterance_id(client), 860); assert response.status_code == 200
    with SessionLocal() as db:
        rec = db.get(Recording, response.json()["recording_id"])
        names = rec.raw_object, rec.wav_object
        metadata = rec.raw_sha256, rec.wav_sha256, rec.raw_size_bytes, rec.wav_size_bytes
    raw, normalized = storage.get_bytes(names[0]), storage.get_bytes(names[1])
    assert hashlib.sha256(raw).hexdigest() == metadata[0] and len(raw) == metadata[2]
    assert hashlib.sha256(normalized).hexdigest() == metadata[1] and len(normalized) == metadata[3]
    with wave.open(io.BytesIO(normalized), "rb") as f:
        assert (f.getnchannels(), f.getsampwidth(), f.getframerate()) == (1, 2, 16000) and f.getnframes() > 0


def test_real_http_permission_matrix_and_csrf(context):
    _, ids = context
    admin, owner, trans, valid, anon = [TestClient(main.app, follow_redirects=False) for _ in range(5)]
    try:
        login(admin, "admin", os.environ["ADMIN_PASSWORD"]); login(owner, ids[2], "owner-password-only")
        login(trans, ids[3], "trans-password-only"); login(valid, ids[4], "valid-password-only")
        response = upload(owner, utterance_id(owner), 870); assert response.status_code == 200
        rid = response.json()["recording_id"]
        assert admin.get("/").status_code == 200 and admin.get("/participants").status_code == 200 and admin.get("/users").status_code == 200
        assert owner.get("/").status_code == 200 and owner.get("/recordings").status_code == 200
        assert trans.get("/recordings").status_code == 200 and valid.get("/recordings").status_code == 200
        assert anon.get("/").status_code == 303 and anon.get("/recordings").status_code == 401
        assert owner.get(f"/audio/{rid}").status_code == 200 and trans.get(f"/audio/{rid}").status_code == 200 and valid.get(f"/audio/{rid}").status_code == 200
        assert owner.get(f"/audio/{rid + 999999}").status_code == 404
        assert trans.post(f"/verify/{rid}", data={"decision":"VERIFIED","csrf_token":trans.cookies.get("csrf_token")}).status_code == 403
        assert valid.post(f"/recordings/{rid}/delete", data={"csrf_token":valid.cookies.get("csrf_token")}).status_code == 403
        assert owner.get("/participants").status_code == 403 and trans.get("/users").status_code == 403 and valid.get("/users").status_code == 403
        assert owner.get("/export/recordings.csv").status_code == 403 and trans.get("/export/recordings.csv").status_code == 403 and valid.get("/export/recordings.csv").status_code == 403
        assert owner.post(f"/transcribe/{rid}", data={"reference_transcription":"x","normalized_transcription":"x","csrf_token":"wrong"}).status_code == 403
        assert owner.post("/logout", data={"csrf_token":""}).status_code == 403
        bad = TestClient(main.app, follow_redirects=False); bad.cookies.set("session", "invalid"); assert bad.get("/recordings").status_code == 401
    finally:
        for c in (admin, owner, trans, valid, anon): c.close()
