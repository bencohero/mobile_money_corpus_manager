import io
import hashlib
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.testclient import TestClient

from app import main, storage
from app.auth import create_token
from app.db import SessionLocal
from app.models import Participant, Recording, User, Workshop, Utterance


class _Response:
    def __init__(self, data):
        self.data = io.BytesIO(data)
        self.closed = False
        self.released = False

    def read(self, size):
        return self.data.read(size)

    def close(self):
        self.closed = True

    def release_conn(self):
        self.released = True


class _FailingResponse(_Response):
    def read(self, size):
        if self.data.tell():
            raise ConnectionError("client disconnected")
        return super().read(size)


def _request(headers=None):
    return Request({"type": "http", "method": "GET", "path": "/audio/1", "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()], "query_string": b""})


def test_storage_stream_releases_minio_response(monkeypatch):
    response = _Response(b"0123456789")
    monkeypatch.setattr(storage.client, "get_object", lambda *args, **kwargs: response)
    assert b"".join(storage.stream_file("audio.wav", offset=2, length=4, chunk_size=2)) == b"0123456789"
    assert response.closed and response.released


def test_storage_stream_releases_after_interrupted_read(monkeypatch):
    response = _FailingResponse(b"0123456789")
    monkeypatch.setattr(storage.client, "get_object", lambda *args, **kwargs: response)
    with pytest.raises(ConnectionError):
        list(storage.stream_file("audio.wav"))
    assert response.closed and response.released


def test_audio_range_headers_and_416(monkeypatch):
    recording = SimpleNamespace(id=1, wav_object="audio.wav", sync_status="READY", participant_id=10)
    monkeypatch.setattr(main, "require", lambda *args, **kwargs: SimpleNamespace(role="TRANSCRIBER", participant_id=None))
    monkeypatch.setattr(main, "stat_file", lambda _: SimpleNamespace(size=10, content_type="audio/wav"))
    monkeypatch.setattr(main, "stream_storage_file", lambda *args, **kwargs: iter([b"2345"]))
    db = SimpleNamespace(get=lambda *_: recording)
    partial = main.audio(1, _request({"Range": "bytes=2-5"}), db)
    assert partial.status_code == 206
    assert partial.headers["content-range"] == "bytes 2-5/10"
    invalid = main.audio(1, _request({"Range": "bytes=20-30"}), db)
    assert invalid.status_code == 416
    assert invalid.headers["content-range"] == "bytes */10"


def test_http_audio_storage_failure_is_502(monkeypatch):
    recording = SimpleNamespace(id=1, wav_object="audio.wav", sync_status="READY", participant_id=10)
    monkeypatch.setattr(main, "require", lambda *args, **kwargs: SimpleNamespace(role="TRANSCRIBER", participant_id=None))
    monkeypatch.setattr(main, "stat_file", lambda _: (_ for _ in ()).throw(ConnectionError("MinIO down")))
    with pytest.raises(HTTPException) as error:
        main.audio(1, _request(), SimpleNamespace(get=lambda *_: recording))
    assert error.value.status_code == 502


def test_http_audio_ranges_against_minio():
    data = bytes(range(256)) * 8
    suffix = uuid.uuid4().hex[:10]
    with SessionLocal() as db:
        workshop = db.query(Workshop).first()
        participant = Participant(workshop_id=workshop.id, participant_code=f"C1_{suffix}", language="mos", language_code="MOS", consent_obtained=True)
        utterance = db.query(Utterance).first()
        user = User(username=f"c1_audio_{suffix}", password_hash="unused", role="PARTICIPANT", participant=participant)
        db.add_all([participant, user]); db.flush()
        name = f"c1/{suffix}.wav"
        recording = Recording(workshop_id=workshop.id, participant_id=participant.id, utterance_id=utterance.id,
                              audio_id=f"C1_{suffix}", condition="CLEAN", raw_object=f"c1/{suffix}.raw",
                              wav_object=name, status="RECORDED", sync_status="READY", wav_size_bytes=len(data),
                              wav_sha256=hashlib.sha256(data).hexdigest())
        db.add(recording); db.commit(); recording_id, user_id, participant_id = recording.id, user.id, participant.id
        path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        path.write(data); path.close()
    try:
        storage.put_file(name, path.name, "audio/wav")
        with SessionLocal() as db:
            client = TestClient(main.app, follow_redirects=False)
            client.cookies.set("session", create_token(db.get(User, user_id)))
            full = client.get(f"/audio/{recording_id}")
            assert full.status_code == 200 and full.content == data
            assert full.headers["accept-ranges"] == "bytes"
            assert full.headers["content-length"] == str(len(data))
            for header, expected in (("bytes=100-", data[100:]), ("bytes=-500", data[-500:])):
                response = client.get(f"/audio/{recording_id}", headers={"Range": header})
                assert response.status_code == 206 and response.content == expected
                assert response.headers["content-range"].startswith("bytes ")
            for header in ("bytes=999999-", "not-a-range", "bytes=1-2,4-5"):
                assert client.get(f"/audio/{recording_id}", headers={"Range": header}).status_code == 416
            assert client.get("/audio/999999999", headers={"Range": "bytes=0-1"}).status_code == 404
    finally:
        storage.delete_file(name)
        Path(path.name).unlink(missing_ok=True)
        with SessionLocal() as db:
            db.query(Recording).filter_by(id=recording_id).delete()
            db.query(User).filter_by(id=user_id).delete()
            db.query(Participant).filter_by(id=participant_id).delete()
            db.commit()
