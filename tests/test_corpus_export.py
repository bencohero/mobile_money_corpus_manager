import csv
import hashlib
import io
import json
import tempfile
import wave
import zipfile
from datetime import datetime
from types import SimpleNamespace

import pytest

from app import corpus_export


class FakeQuery:
    def __init__(self, rows): self.rows = rows
    def order_by(self, *_): return self
    def filter(self, *_): return self
    def join(self, *_): return self
    def filter_by(self, **_): return self
    def all(self): return self.rows


class FakeDB:
    def __init__(self, rows): self.rows = rows
    def query(self, *_): return FakeQuery(self.rows)


def wav_bytes(rate=16000, channels=1, width=2, frames=160):
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setnchannels(channels); wav.setsampwidth(width); wav.setframerate(rate)
        wav.writeframes(b"\0" * frames * channels * width)
    return out.getvalue()


def record(data, *, status="VERIFIED", verification="VERIFIED", condition="CLEAN", text="tẽst mooré"):
    digest = hashlib.sha256(data).hexdigest()
    return SimpleNamespace(
        id=1, audio_id="mos_0001_UTT_CLEAN_T01", participant_id=1, utterance_id=1,
        take_number=1, condition=condition, raw_object="raw/x", wav_object="normalized/x.wav",
        wav_size_bytes=len(data), wav_sha256=digest, status=status,
        created_at=datetime(2026, 9, 5),
        participant=SimpleNamespace(participant_code="mos_0001", language="mos", gender=None),
        utterance=SimpleNamespace(utterance_code="UTT", intent="balance", amount=None, counterparty=None, period=None),
        transcription=SimpleNamespace(reference_transcription=text, normalized_transcription=text,
                                      verification_status=verification),
    )


class FakeResponse:
    def __init__(self, data): self.stream = io.BytesIO(data); self.closed = False
    def read(self, size): return self.stream.read(size)
    def close(self): self.closed = True
    def release_conn(self): pass


def test_build_export_contains_audio_metadata_manifest_and_checksums(monkeypatch):
    data = wav_bytes()
    rec = record(data)
    response = FakeResponse(data)
    monkeypatch.setattr(corpus_export.storage, "stat_file", lambda _: SimpleNamespace(size=len(data)))
    monkeypatch.setattr(corpus_export.storage.client, "get_object", lambda *_: response)
    filters = corpus_export.parse_filters("benchmark", "", "", "", "", "", "", "", "", "true")
    path, prefix = corpus_export.build_export(FakeDB([rec]), filters)
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            assert f"{prefix}/audio/clean/{rec.audio_id}.wav" in names
            assert f"{prefix}/metadata/recordings.csv" in names
            assert f"{prefix}/metadata/metadata.csv" in names
            manifest = json.loads(archive.read(f"{prefix}/metadata/manifest.json"))
            assert manifest["recording_count"] == 1
            assert manifest["audio_format"]["sample_rate_hz"] == 16000
            rows = list(csv.DictReader(io.StringIO(archive.read(f"{prefix}/metadata/recordings.csv").decode())))
            assert rows[0]["wav_size_bytes"] == str(len(data))
            sums = archive.read(f"{prefix}/SHA256SUMS").decode()
            assert hashlib.sha256(archive.read(f"{prefix}/audio/clean/{rec.audio_id}.wav")).hexdigest() in sums
            assert "minio" not in archive.read(f"{prefix}/metadata/recordings.csv").decode().lower()
    finally:
        path.unlink(missing_ok=True)
    assert response.closed


def test_benchmark_strict_rejects_unverified_without_archive(monkeypatch):
    data = wav_bytes()
    rec = record(data, status="TRANSCRIBED", verification="PENDING")
    filters = corpus_export.parse_filters("benchmark", "", "", "", "", "", "", "", "", "true")
    with pytest.raises(corpus_export.HTTPException) as error:
        corpus_export.build_export(FakeDB([rec]), filters)
    assert error.value.status_code == 404


def test_parse_filters_rejects_unknown_values():
    with pytest.raises(Exception):
        corpus_export.parse_filters("benchmark", "UNKNOWN", "", "", "", "", "", "", "", "true")
def test_real_http_export_work_and_benchmark_mixed_statuses():
    import re, uuid, httpx
    base = "http://app-test:8000"
    admin = httpx.Client(base_url=base, follow_redirects=False, timeout=30)
    suffix = uuid.uuid4().hex[:10]
    code = f"e2_{suffix}"
    username = f"e2_{suffix}"
    recording_ids = []
    try:
        admin.get("/login")
        csrf = admin.cookies.get("csrf_token")
        assert admin.post("/login", data={"username": "admin", "password": "p0a2-admin-password-only", "csrf_token": csrf}).status_code == 303
        response = admin.post("/participants", data={"participant_code": code, "username": username, "password": "e2-participant-password", "language": "mos", "consent_obtained": "on", "csrf_token": admin.cookies.get("csrf_token")})
        assert response.status_code == 303
        page = admin.get("/record").text
        participant_id = re.search(r'<option value="(\d+)">'+re.escape(code)+r'</option>', page).group(1)
        utterance_id = re.search(r'<select id="utterance">.*?<option value="(\d+)"', page, re.S).group(1)
        audio = wav_bytes(frames=8000)
        for take, condition in ((1, "CLEAN"), (2, "NOISY"), (3, "CLEAN")):
            response = admin.post("/api/recordings", data={"participant_id": participant_id, "utterance_id": utterance_id, "idempotency_key": uuid.uuid4().hex, "condition": condition}, files={"audio": (f"{condition.lower()}-{take}.wav", audio, "audio/wav")}, headers={"X-CSRF-Token": admin.cookies.get("csrf_token")})
            assert response.status_code == 200, response.text
            recording_ids.append(response.json()["recording_id"])
        csrf = admin.cookies.get("csrf_token")
        assert admin.post(f"/transcribe/{recording_ids[0]}", data={"reference_transcription": "bẽ n yẽlga", "normalized_transcription": "bẽ n yẽlga", "csrf_token": csrf}).status_code == 303
        assert admin.post(f"/verify/{recording_ids[0]}", data={"decision": "VERIFIED", "comment": "", "csrf_token": csrf}).status_code == 303
        assert admin.post(f"/transcribe/{recording_ids[1]}", data={"reference_transcription": "n yibeogo", "normalized_transcription": "n yibeogo", "csrf_token": csrf}).status_code == 303
        work = admin.post("/admin/export/corpus", data={"mode": "work", "participant": code, "strict": "true", "csrf_token": csrf})
        assert work.status_code == 200, work.text
        work_zip = zipfile.ZipFile(io.BytesIO(work.content))
        prefix = work_zip.namelist()[0].split("/", 1)[0]
        rows = list(csv.DictReader(io.StringIO(work_zip.read(f"{prefix}/metadata/recordings.csv").decode("utf-8"))))
        assert len(rows) == 3 and {row["status"] for row in rows} == {"VERIFIED", "TRANSCRIBED", "RECORDED"}
        assert sum(not row["reference_transcription"] for row in rows) == 1
        work_zip.close()
        benchmark = admin.post("/admin/export/corpus", data={"mode": "benchmark", "participant": code, "strict": "true", "csrf_token": csrf})
        assert benchmark.status_code == 200, benchmark.text
        benchmark_zip = zipfile.ZipFile(io.BytesIO(benchmark.content))
        prefix = benchmark_zip.namelist()[0].split("/", 1)[0]
        rows = list(csv.DictReader(io.StringIO(benchmark_zip.read(f"{prefix}/metadata/recordings.csv").decode("utf-8"))))
        manifest = json.loads(benchmark_zip.read(f"{prefix}/metadata/manifest.json"))
        assert len(rows) == 1 and rows[0]["status"] == "VERIFIED"
        assert manifest["recording_count"] == 1 and manifest["excluded_count"] == 2
        benchmark_zip.close()
    finally:
        admin.close()

def test_benchmark_strict_false_excludes_technical_anomaly_and_counts_it(monkeypatch):
    data = wav_bytes(frames=8000)
    valid = record(data)
    invalid = record(data)
    invalid.audio_id = "mos_0002_UTT_CLEAN_T01"
    invalid.wav_object = "normalized/invalid.wav"
    invalid.wav_size_bytes = len(data)
    invalid.wav_sha256 = hashlib.sha256(data).hexdigest()
    responses = {"normalized/x.wav": FakeResponse(data), "normalized/invalid.wav": FakeResponse(b"corrupt")}
    monkeypatch.setattr(corpus_export.storage, "stat_file", lambda name: SimpleNamespace(size=len(data)))
    monkeypatch.setattr(corpus_export.storage.client, "get_object", lambda _, name: responses[name])
    filters = corpus_export.parse_filters("benchmark", "", "", "", "", "", "", "", "", "false")
    path, prefix = corpus_export.build_export(FakeDB([valid, invalid]), filters)
    try:
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read(f"{prefix}/metadata/manifest.json"))
            assert manifest["recording_count"] == 1
            assert manifest["excluded_count"] == 1
            assert manifest["exclusions"] == {"checksum_mismatch": 1}
            rows = list(csv.DictReader(io.StringIO(archive.read(f"{prefix}/metadata/recordings.csv").decode())))
            assert len(rows) == 1
    finally:
        path.unlink(missing_ok=True)
    assert responses["normalized/invalid.wav"].closed


def test_minio_reads_are_bounded_and_released(monkeypatch):
    data = wav_bytes(frames=8000)
    records = []
    responses = {}
    for index in range(3):
        rec = record(data)
        rec.audio_id = f"mos_000{index + 1}_UTT_CLEAN_T01"
        rec.wav_object = f"normalized/{index}.wav"
        records.append(rec)
        responses[rec.wav_object] = FakeResponse(data)
    calls = []
    original_read = FakeResponse.read
    def instrumented(self, size):
        calls.append(size)
        return original_read(self, size)
    monkeypatch.setattr(FakeResponse, "read", instrumented)
    monkeypatch.setattr(corpus_export.storage, "stat_file", lambda name: SimpleNamespace(size=len(data)))
    monkeypatch.setattr(corpus_export.storage.client, "get_object", lambda _, name: responses[name])
    filters = corpus_export.parse_filters("benchmark", "", "", "", "", "", "", "", "", "true")
    path, _ = corpus_export.build_export(FakeDB(records), filters)
    path.unlink(missing_ok=True)
    assert calls and max(calls) <= corpus_export.BLOCK_SIZE
    assert all(response.closed for response in responses.values())


def test_unsafe_audio_id_fails_without_creating_archive(monkeypatch):
    data = wav_bytes(frames=8000)
    rec = record(data)
    rec.audio_id = "../escape"
    filters = corpus_export.parse_filters("work", "", "", "", "", "", "", "", "", "true")
    with pytest.raises(corpus_export.ExportFailure) as error:
        corpus_export.build_export(FakeDB([rec]), filters)
    assert error.value.classification == "duplicate_archive_path"


def test_real_http_export_permissions_and_csrf():
    import httpx, re, uuid
    base = "http://app-test:8000"
    admin = httpx.Client(base_url=base, follow_redirects=False, timeout=30)
    suffix = uuid.uuid4().hex[:10]
    code = f"perm_{suffix}"
    participant_user = f"part_{suffix}"
    transcriber_user = f"trans_{suffix}"
    validator_user = f"valid_{suffix}"
    try:
        admin.get("/login")
        csrf = admin.cookies.get("csrf_token")
        assert admin.post("/login", data={"username": "admin", "password": "p0a2-admin-password-only", "csrf_token": csrf}).status_code == 303
        for role, username, password in (("TRANSCRIBER", transcriber_user, "p0e2-transcriber-password"), ("VALIDATOR", validator_user, "p0e2-validator-password")):
            response = admin.post("/users", data={"username": username, "password": password, "role": role, "csrf_token": admin.cookies.get("csrf_token")})
            assert response.status_code == 303
        response = admin.post("/participants", data={"participant_code": code, "username": participant_user, "password": "p0e2-participant-password", "language": "mos", "consent_obtained": "on", "csrf_token": admin.cookies.get("csrf_token")})
        assert response.status_code == 303
        clients = [httpx.Client(base_url=base, follow_redirects=False, timeout=30) for _ in range(3)]
        try:
            for client, username, password in zip(clients, (participant_user, transcriber_user, validator_user), ("p0e2-participant-password", "p0e2-transcriber-password", "p0e2-validator-password")):
                client.get("/login")
                token = client.cookies.get("csrf_token")
                assert client.post("/login", data={"username": username, "password": password, "csrf_token": token}).status_code == 303
                assert client.get("/admin/export").status_code == 403
                assert client.post("/admin/export/corpus", data={}).status_code == 403
            anonymous = httpx.Client(base_url=base, follow_redirects=False, timeout=30)
            invalid = httpx.Client(base_url=base, follow_redirects=False, timeout=30)
            try:
                assert anonymous.get("/admin/export").status_code == 401
                invalid.cookies.set("session", "invalid")
                assert invalid.get("/admin/export").status_code == 401
            finally:
                anonymous.close(); invalid.close()
            token = admin.cookies.get("csrf_token")
            assert admin.post("/admin/export/corpus", data={"mode": "work"}).status_code == 403
            assert admin.post("/admin/export/corpus", data={"mode": "work", "csrf_token": ""}).status_code == 403
            assert admin.post("/admin/export/corpus", data={"mode": "work", "csrf_token": "wrong"}).status_code == 403
            other = httpx.Client(base_url=base, follow_redirects=False, timeout=30)
            try:
                other.get("/login")
                other_token = other.cookies.get("csrf_token")
                assert other.post("/login", data={"username": "admin", "password": "p0a2-admin-password-only", "csrf_token": other_token}).status_code == 303
                assert admin.post("/admin/export/corpus", data={"mode": "work", "csrf_token": other.cookies.get("csrf_token")}).status_code == 403
            finally:
                other.close()
            assert admin.post("/admin/export/corpus", data={"mode": "work", "participant": code, "csrf_token": token}).status_code == 404
        finally:
            for client in clients: client.close()
    finally:
        admin.close()

def test_filter_validation_and_csv_jsonl_safety(monkeypatch):
    invalids = [
        ("bad", "", "", "", "", "", "", "", "", "true"),
        ("work", "BAD", "", "", "", "", "", "", "", "true"),
        ("work", "", "BAD", "", "", "", "", "", "", "true"),
        ("work", "", "", "BAD", "", "", "", "", "", "true"),
        ("work", "", "", "", "", "", "maybe", "", "", "true"),
        ("work", "", "", "", "", "", "", "2026-09-10", "2026-09-01", "true"),
        ("work", "", "", "", "", "", "", "not-date", "", "true"),
        ("work", "", "", "", "", "", "", "", "", "maybe"),
    ]
    for args in invalids:
        with pytest.raises(corpus_export.HTTPException) as error:
            corpus_export.parse_filters(*args)
        assert error.value.status_code == 400
    data = wav_bytes(frames=8000)
    rec = record(data, text="=SUM(1,1) mooré")
    monkeypatch.setattr(corpus_export.storage, "stat_file", lambda _: SimpleNamespace(size=len(data)))
    response = FakeResponse(data)
    monkeypatch.setattr(corpus_export.storage.client, "get_object", lambda *_: response)
    filters = corpus_export.parse_filters("work", "", "", "", "", "", "", "", "", "true")
    path, prefix = corpus_export.build_export(FakeDB([rec]), filters)
    try:
        with zipfile.ZipFile(path) as archive:
            csv_text = archive.read(f"{prefix}/metadata/recordings.csv").decode("utf-8")
            jsonl_text = archive.read(f"{prefix}/metadata/recordings.jsonl").decode("utf-8")
            assert "'=SUM(1,1) mooré" in csv_text
            assert '"reference_transcription": "=SUM(1,1) mooré"' in jsonl_text
            assert "minio" not in csv_text.lower() and "/tmp" not in jsonl_text
    finally:
        path.unlink(missing_ok=True)


def test_stream_file_early_close_removes_archive(tmp_path):
    path = tmp_path / "archive.zip"
    path.write_bytes(b"x" * (corpus_export.BLOCK_SIZE + 10))
    stream = corpus_export.stream_file(path)
    assert next(stream)
    stream.close()
    assert not path.exists()

@pytest.mark.parametrize("exc,expected", [
    (TimeoutError("timeout"), "storage_timeout"),
    (PermissionError("denied"), "storage_permission_denied"),
    (ConnectionError("down"), "storage_unavailable"),
])
def test_storage_failure_classifications(exc, expected):
    assert corpus_export.classify_storage_error(exc) == expected


def test_strict_true_fails_on_admissible_missing_object():
    rec = record(wav_bytes(frames=8000))
    rec.wav_object = ""
    filters = corpus_export.parse_filters("benchmark", "", "", "", "", "", "", "", "", "true")
    with pytest.raises(corpus_export.ExportFailure) as error:
        corpus_export.build_export(FakeDB([rec]), filters)
    assert error.value.classification == "db_without_object"
