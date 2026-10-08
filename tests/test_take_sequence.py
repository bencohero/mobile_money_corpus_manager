"""Real PostgreSQL/MinIO regression tests; only the dedicated test stack."""
import hashlib
import io
import uuid
import wave
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from threading import Event
import json
import subprocess

import pytest
from sqlalchemy import inspect, text
from starlette.testclient import TestClient

from app import main, storage
from app.db import SessionLocal, engine
from app.models import Participant, Utterance, Recording, User, Workshop
from app.auth import create_token


def audio_bytes(sample=0):
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        wav.writeframes(sample.to_bytes(2, "little", signed=True) * 8000)
    return out.getvalue()


@pytest.fixture
def scope():
    assert engine.url.host == "db-test" and engine.url.database == "p0a2_test"
    tag = uuid.uuid4().hex[:12]
    with SessionLocal() as db:
        workshop = Workshop(name=f"Sequence test {tag}")
        db.add(workshop); db.flush()
        ps = [Participant(workshop_id=workshop.id, participant_code=f"SEQ_{tag}_{i}", consent_obtained=True) for i in range(2)]
        us = [Utterance(utterance_code=f"SEQ_{tag}_{i}", intent="SAME", scenario_fr="Synthetic") for i in range(2)]
        db.add_all(ps + us); db.flush()
        user = User(username=f"SEQ_{tag}", password_hash="unused", role="ADMIN")
        db.add(user); db.commit()
        ids = ([p.id for p in ps], [u.id for u in us], user.id, workshop.id)
    yield ids
    with SessionLocal() as db:
        for rec in db.query(Recording).filter(Recording.participant_id.in_(ids[0])):
            for name in (rec.raw_object, rec.wav_object): storage.delete_file(name)
        for table in ("recording_submissions", "recording_take_counters"):
            if inspect(engine).has_table(table):
                db.execute(text(f"DELETE FROM {table} WHERE participant_id IN (:a,:b)"), dict(a=ids[0][0], b=ids[0][1]))
        db.execute(text("DELETE FROM audit_logs WHERE user_id=:id"), dict(id=ids[2]))
        db.query(Recording).filter(Recording.participant_id.in_(ids[0])).delete()
        db.query(User).filter_by(id=ids[2]).delete()
        db.query(Participant).filter(Participant.id.in_(ids[0])).delete()
        db.query(Utterance).filter(Utterance.id.in_(ids[1])).delete()
        db.delete(db.get(Workshop, ids[3]))
        db.commit()


def client_for(uid):
    c = TestClient(main.app, follow_redirects=False)
    with SessionLocal() as db:
        c.cookies.set("session", create_token(db.get(User, uid)))
    c.cookies.set("csrf_token", "sequence-tests")
    return c


def send(scope, *, p=0, u=0, condition="CLEAN", key=None, body=None, **extra):
    with client_for(scope[2]) as c:
        return c.post("/api/recordings", data={"participant_id": scope[0][p], "utterance_id": scope[1][u], "condition": condition, "idempotency_key": key or uuid.uuid4().hex, **extra}, files={"audio": ("synthetic.wav", audio_bytes() if body is None else body, "audio/wav")}, headers={"X-CSRF-Token": "sequence-tests"})


def preview(scope, p=0, u=0, condition="CLEAN"):
    with client_for(scope[2]) as c:
        return c.get("/api/recordings/next-take", params={"participant_id": scope[0][p], "utterance_id": scope[1][u], "condition": condition})


def test_sequences_follow_complete_key(scope):
    # T01-05, T13-16, T21, T24
    assert preview(scope).json() == {"next_take_number": 1, "reserved": False}
    for kwargs, expected in [({}, 1), ({}, 2), ({"u": 1}, 1), ({}, 3), ({"condition": "NOISY"}, 1), ({"p": 1}, 1)]:
        r = send(scope, **kwargs)
        assert r.status_code == 200, r.text
        assert r.json()["take_number"] == expected
        assert r.json()["status"] == "READY"
    with SessionLocal() as db:
        db.get(Utterance, scope[1][0]).intent = "RENAMED"; db.commit()
    assert preview(scope).json()["next_take_number"] == 4


def test_client_cannot_choose_number(scope):
    assert send(scope, take_number="999").status_code == 400
    assert send(scope).json()["take_number"] == 1


def test_idempotence_and_fingerprint(scope):
    key = uuid.uuid4().hex
    first = send(scope, key=key)
    second = send(scope, key=key)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert send(scope, key=key, body=audio_bytes(1)).status_code == 409
    assert send(scope, key=key, p=1).status_code == 409
    assert preview(scope).json()["next_take_number"] == 2


def test_concurrent_uploads_keep_distinct_verified_objects(scope, monkeypatch):
    barrier = Barrier(2)
    original = main.put_file
    def put(name, *args):
        if name.startswith("raw/"): barrier.wait(timeout=20)
        return original(name, *args)
    monkeypatch.setattr(main, "put_file", put)
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(lambda n: send(scope, body=audio_bytes(n)), (1, 2)))
    assert [r.status_code for r in responses] == [200, 200]
    assert sorted(r.json()["take_number"] for r in responses) == [1, 2]
    with SessionLocal() as db:
        rows = db.query(Recording).filter_by(participant_id=scope[0][0]).all()
        assert len(rows) == 2
        names = set()
        for rec in rows:
            assert rec.sync_status == "READY"
            for kind in ("raw", "wav"):
                name = getattr(rec, kind + "_object"); names.add(name)
                data = storage.get_bytes(name)
                assert len(data) == getattr(rec, kind + "_size_bytes")
                assert hashlib.sha256(data).hexdigest() == getattr(rec, kind + "_sha256")
        assert len(names) == 4
        actual = {o.object_name for o in storage.list_files() if any(o.object_name == n for n in names)}
        assert actual == names
    reconciliation = subprocess.run(["python", "scripts/reconcile.py", "--json"], capture_output=True, text=True)
    findings = json.loads(reconciliation.stdout)
    assert not [f for f in findings if f.get("object") in names or f.get("recording_id") in [r.json()["recording_id"] for r in responses]]


@pytest.mark.parametrize("failed_put", [1, 2])
def test_failed_storage_consumes_number_and_is_idempotent(scope, monkeypatch, failed_put):
    original = main.put_file
    calls = []
    def put(name, *args):
        calls.append(name)
        if len(calls) == failed_put: raise RuntimeError("synthetic failure")
        return original(name, *args)
    monkeypatch.setattr(main, "put_file", put)
    key = uuid.uuid4().hex
    response = send(scope, key=key)
    assert response.status_code == 502
    assert send(scope, key=key).status_code == 502
    assert len(calls) == failed_put
    with SessionLocal() as db:
        rec = db.query(Recording).filter_by(participant_id=scope[0][0]).one()
        assert rec.take_number == 1 and rec.sync_status == "ERROR"
    monkeypatch.setattr(main, "put_file", original)
    assert send(scope).json()["take_number"] == 2


def test_conversion_failure_consumes_number(scope):
    assert send(scope, body=b"invalid audio").status_code == 422
    assert send(scope).json()["take_number"] == 2


def test_rejection_and_deletion_do_not_release_number(scope):
    first = send(scope).json()
    with SessionLocal() as db:
        db.get(Recording, first["recording_id"]).status = "REJECTED"; db.commit()
    second = send(scope).json()
    with client_for(scope[2]) as c:
        assert c.post(f'/recordings/{second["recording_id"]}/delete', data={"csrf_token": "sequence-tests"}).status_code == 303
    assert send(scope).json()["take_number"] == 3


def test_limit_and_schema(scope):
    from app.take_sequence import allocate_next_take, TakeLimitReached
    with SessionLocal() as db:
        for i in range(999):
            assert allocate_next_take(db, scope[0][0], scope[1][0], "CLEAN") == i + 1
        db.commit()
    assert preview(scope).status_code == 409
    assert send(scope).status_code == 409
    with SessionLocal() as db, pytest.raises(TakeLimitReached):
        allocate_next_take(db, scope[0][0], scope[1][0], "CLEAN")
    constraints = inspect(engine).get_unique_constraints("recordings")
    assert next(c["column_names"] for c in constraints if c["name"] == "uq_recording_take") == ["participant_id", "utterance_id", "condition", "take_number"]
    assert "ck_recordings_take_range" in {c["name"] for c in inspect(engine).get_check_constraints("recordings")}


def test_same_key_concurrent_pending_then_same_result(scope, monkeypatch):
    entered, release = Event(), Event()
    original = main.put_file
    def put(name, *args):
        if name.startswith("raw/"):
            entered.set(); assert release.wait(15)
        return original(name, *args)
    monkeypatch.setattr(main, "put_file", put)
    key = uuid.uuid4().hex
    with ThreadPoolExecutor(2) as pool:
        first = pool.submit(send, scope, key=key)
        assert entered.wait(15)
        try:
            pending = send(scope, key=key)
            assert pending.status_code == 202 and pending.json()["status"] == "PENDING"
            assert preview(scope).json()["next_take_number"] == 2
        finally: release.set()
        complete = first.result()
    assert complete.status_code == 200
    assert send(scope, key=key).json() == complete.json()


@pytest.mark.parametrize("committed", [False, True])
def test_finalization_failure_resolves_commit_outcome(scope, monkeypatch, committed):
    original = main.finish_recording
    def finish(*args):
        if committed: original(*args)
        raise RuntimeError("synthetic lost commit response")
    monkeypatch.setattr(main, "finish_recording", finish)
    response = send(scope)
    assert response.status_code == (200 if committed else 502)
    with SessionLocal() as db:
        rec = db.get(Recording, response.json()["recording_id"])
        assert rec.sync_status == ("READY" if committed else "ERROR")
        objects = list(storage.list_files(rec.raw_object)) + list(storage.list_files(rec.wav_object))
        assert len(objects) == (2 if committed else 0)


def test_compensation_failure_visible_in_reconciliation(scope, monkeypatch):
    original = main.put_file
    def put(name, *args):
        if name.startswith("normalized/"): raise RuntimeError("synthetic PUT failure")
        return original(name, *args)
    def fail_delete(name): raise RuntimeError("synthetic compensation failure")
    monkeypatch.setattr(main, "put_file", put)
    monkeypatch.setattr(main, "delete_file", fail_delete)
    response = send(scope)
    assert response.status_code == 502
    check = subprocess.run(["python", "scripts/reconcile.py", "--json"], capture_output=True, text=True)
    assert check.returncode == 1
    assert any(f["type"] == "failed_recording_object" and f["recording_id"] == response.json()["recording_id"] for f in json.loads(check.stdout))


def test_deleted_idempotent_receipt_cannot_recreate_audio(scope):
    key = uuid.uuid4().hex
    first = send(scope, key=key).json()
    with client_for(scope[2]) as c:
        assert c.post(f'/recordings/{first["recording_id"]}/delete', data={"csrf_token": "sequence-tests"}).status_code == 303
    assert send(scope, key=key).status_code == 410
    assert preview(scope).json()["next_take_number"] == 2


def test_participant_cannot_read_or_submit_other_participant(scope):
    with SessionLocal() as db:
        user = db.get(User, scope[2]); user.role = "PARTICIPANT"; user.participant_id = scope[0][0]; db.commit()
    assert preview(scope, p=1).status_code == 403
    assert send(scope, p=1).status_code == 403
    assert send(scope).json()["take_number"] == 1
    with SessionLocal() as db:
        db.get(User, scope[2]).participant_id = None; db.commit()


def test_inactive_utterance_rejected_without_consuming(scope):
    with SessionLocal() as db:
        db.get(Utterance, scope[1][0]).active = False; db.commit()
    assert send(scope).status_code == 400
    assert preview(scope).status_code == 400
    with SessionLocal() as db:
        db.get(Utterance, scope[1][0]).active = True; db.commit()
    assert preview(scope).json()["next_take_number"] == 1


def test_same_key_is_scoped_to_authenticated_user(scope):
    key = uuid.uuid4().hex
    first = send(scope, key=key).json()
    with SessionLocal() as db:
        second_user = User(username="seq-other-" + uuid.uuid4().hex[:12], password_hash="unused", role="PARTICIPANT", participant_id=scope[0][1])
        db.add(second_user); db.commit(); uid = second_user.id
    try:
        with client_for(uid) as c:
            response = c.post("/api/recordings", data={"utterance_id":scope[1][0], "condition":"CLEAN", "idempotency_key":key}, files={"audio":("x.wav",audio_bytes(3),"audio/wav")}, headers={"X-CSRF-Token":"sequence-tests"})
            assert response.status_code == 200
            assert response.json()["recording_id"] != first["recording_id"]
            assert response.json()["take_number"] == 1
            assert c.get(f'/audio/{first["recording_id"]}').status_code == 403
    finally:
        with SessionLocal() as db:
            db.execute(text("DELETE FROM audit_logs WHERE user_id=:id"), {"id":uid})
            db.execute(text("DELETE FROM recording_submissions WHERE user_id=:id"), {"id":uid})
            db.query(User).filter_by(id=uid).delete(); db.commit()


def test_unavailable_database_after_storage_keeps_pending_objects(scope, monkeypatch):
    def fail(*args, **kwargs): raise RuntimeError("synthetic database unavailable")
    monkeypatch.setattr(main, "finish_recording", fail)
    monkeypatch.setattr(main, "mark_recording_error", fail)
    key = uuid.uuid4().hex
    assert send(scope, key=key).status_code == 503
    retry = send(scope, key=key)
    assert retry.status_code == 202
    with SessionLocal() as db:
        rec = db.get(Recording, retry.json()["recording_id"])
        assert rec.sync_status == "PENDING"
        assert storage.stat_file(rec.raw_object).size > 0
        assert storage.stat_file(rec.wav_object).size > 0


def test_export_keeps_logical_names(scope):
    import zipfile
    from app.corpus_export import build_export, parse_filters
    response = send(scope).json()
    with SessionLocal() as db:
        rec = db.get(Recording, response["recording_id"])
        assert rec.audio_id not in rec.raw_object and rec.audio_id not in rec.wav_object
        filters = parse_filters("work", "", "", "", rec.participant.participant_code, "", "", "", "", "true")
        path, prefix = build_export(db, filters)
        try:
            with zipfile.ZipFile(path) as archive:
                assert archive.read(f'{prefix}/audio/clean/{rec.audio_id}.wav') == storage.get_bytes(rec.wav_object)
                metadata = json.loads(archive.read(f"{prefix}/metadata/recordings.jsonl").decode().strip())
                assert metadata["take_number"] == 1
        finally: path.unlink()
