import io
import os
import re
import subprocess
import wave
import uuid
import httpx
from sqlalchemy import select
from app.db import SessionLocal
from app.models import Recording
from app.storage import stat_file
BASE = "http://app-test:8000"
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
def login(username, password):
    client = httpx.Client(base_url=BASE, follow_redirects=False, timeout=20)
    page = client.get("/login")
    csrf = client.cookies.get("csrf_token")
    response = client.post("/login", data={"username": username, "password": password, "csrf_token": csrf})
    assert response.status_code == 303
    return client
def wav_bytes(seconds=0.8):
    out = io.BytesIO()
    with wave.open(out, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(16000)
        f.writeframes(b"\x00\x00" * int(16000 * seconds))
    return out.getvalue()
def csrf(client):
    return client.cookies.get("csrf_token")
def create_participant(admin, code, username, password):
    # The isolated stack is persistent; permit repeated runs without deleting fixtures.
    if code in admin.get("/participants").text: return
    response = admin.post("/participants", data={"participant_code": code, "username": username, "password": password, "language": "mos", "consent_obtained": "on", "csrf_token": csrf(admin)})
    assert response.status_code == 303
def create_user(admin, username, password, role):
    if username in admin.get("/users").text: return
    response = admin.post("/users", data={"username": username, "password": password, "role": role, "csrf_token": csrf(admin)})
    assert response.status_code == 303
def test_end_to_end_http_postgres_minio_permissions_and_reconcile():
    admin = login("admin", ADMIN_PASSWORD)
    assert admin.get("/health").status_code == 200
    create_participant(admin, "P0A2_S001", "p0a2-participant", "p0a2-participant-password")
    create_participant(admin, "P0A2_S002", "p0a2-other", "p0a2-other-password")
    create_user(admin, "p0a2-transcriber", "p0a2-transcriber-password", "TRANSCRIBER")
    create_user(admin, "p0a2-validator", "p0a2-validator-password", "VALIDATOR")
    participant = login("p0a2-participant", "p0a2-participant-password")
    page = participant.get("/record")
    utterance_id = re.search(r'<option value="(\d+)"', page.text).group(1)
    files = {"audio": ("synthetic.wav", wav_bytes(), "audio/wav")}
    data = {"utterance_id": utterance_id, "idempotency_key": uuid.uuid4().hex, "condition": "CLEAN"}
    response = participant.post("/api/recordings", data=data, files=files, headers={"X-CSRF-Token": csrf(participant)})
    assert response.status_code == 200, response.text
    recording_id = response.json()["recording_id"]
    response2 = participant.post("/api/recordings", data={**data, "idempotency_key": uuid.uuid4().hex}, files=files, headers={"X-CSRF-Token": csrf(participant)})
    assert response2.status_code == 200
    assert response2.json()["take_number"] == response.json()["take_number"] + 1
    with SessionLocal() as db:
        rec = db.get(Recording, recording_id)
        assert rec and rec.participant.participant_code == "P0A2_S001"
        assert rec.sync_status == "READY"
        assert rec.duration_ms and rec.duration_ms > 0
        assert rec.raw_sha256 and len(rec.raw_sha256) == 64
        assert rec.wav_sha256 and len(rec.wav_sha256) == 64
        assert rec.raw_size_bytes and rec.wav_size_bytes
        raw_name, wav_name = rec.raw_object, rec.wav_object
    assert stat_file(raw_name).size == rec.raw_size_bytes
    assert stat_file(wav_name).size == rec.wav_size_bytes
    assert participant.get(f"/audio/{recording_id}").status_code == 200
    other = login("p0a2-other", "p0a2-other-password")
    assert other.get(f"/audio/{recording_id}").status_code == 403
    assert other.get("/export/recordings.csv").status_code == 403
    transcriber = login("p0a2-transcriber", "p0a2-transcriber-password")
    assert transcriber.post(f"/transcribe/{recording_id}", data={"reference_transcription": "synthetic test", "normalized_transcription": "synthetic test", "csrf_token": csrf(transcriber)}).status_code == 303
    validator = login("p0a2-validator", "p0a2-validator-password")
    assert validator.post(f"/verify/{recording_id}", data={"decision": "NEEDS_REVIEW", "comment": "corriger", "csrf_token": csrf(validator)}).status_code == 303
    assert transcriber.post(f"/transcribe/{recording_id}", data={"reference_transcription": "synthetic test corrected", "normalized_transcription": "synthetic test corrected", "csrf_token": csrf(transcriber)}).status_code == 303
    assert validator.post(f"/verify/{recording_id}", data={"decision": "VERIFIED", "comment": "", "csrf_token": csrf(validator)}).status_code == 303
    export = admin.get("/export/recordings.csv")
    assert export.status_code == 200 and "audio_id" in export.text and "P0A2_S001" in export.text
    assert admin.post(f"/recordings/{recording_id}/delete", data={"csrf_token": csrf(admin)}).status_code == 303
    with SessionLocal() as db:
        assert db.get(Recording, recording_id) is None
    assert other.post("/recordings/1/delete", data={"csrf_token": csrf(other)}).status_code == 403
    reconcile = subprocess.run(["python", "scripts/reconcile.py", "--json"], capture_output=True, text=True)
    assert reconcile.returncode == 0, reconcile.stdout + reconcile.stderr
    admin.close(); participant.close(); other.close(); transcriber.close(); validator.close()
def test_http_csrf_and_invalid_audio_are_rejected():
    client = login("p0a2-participant", "p0a2-participant-password")
    assert client.get("/record").status_code == 200
    utterance_id = re.search(r'<option value="(\d+)"', client.get("/record").text).group(1)
    no_csrf = client.post("/api/recordings", data={"utterance_id": utterance_id, "idempotency_key": uuid.uuid4().hex, "condition": "CLEAN"}, files={"audio": ("bad.wav", b"not-audio", "audio/wav")})
    assert no_csrf.status_code == 403
    invalid = client.post("/api/recordings", data={"utterance_id": utterance_id, "idempotency_key": uuid.uuid4().hex, "condition": "CLEAN"}, files={"audio": ("bad.wav", b"not-audio", "audio/wav")}, headers={"X-CSRF-Token": csrf(client)})
    assert invalid.status_code in {422, 502}
    admin = login("admin", ADMIN_PASSWORD)
    assert admin.post(f'/recordings/{invalid.json()["recording_id"]}/delete', data={"csrf_token": csrf(admin)}).status_code == 303
    admin.close()
    client.close()
