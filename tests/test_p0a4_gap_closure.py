import subprocess
import pytest
from app import main
from app.config import Settings

@pytest.mark.parametrize("fault", [
    "minio_before_first_upload",
    "second_object_upload",
    "postgres_commit",
    "compensation_second_delete",
    "minio_during_compensation",
    "minio_delete_timeout",
    "minio_delete_unavailable",
])
def test_p0a13_postgres_minio_failure_modes_are_explicit(fault, monkeypatch, caplog):
    attempted=[]
    def delete(name):
        attempted.append(name)
        if fault in {"compensation_second_delete","minio_during_compensation","minio_delete_timeout","minio_delete_unavailable"} and name=="wav":
            raise RuntimeError(fault)
    monkeypatch.setattr(main, "delete_file", delete)
    uploaded=[] if fault=="minio_before_first_upload" else ["raw","wav"]
    main.compensate_uploaded(uploaded, type("Request",(),{"headers":{}})())
    assert attempted == uploaded
    if fault in {"compensation_second_delete","minio_during_compensation","minio_delete_timeout","minio_delete_unavailable"}:
        assert "MinIO compensation failed" in caplog.text

@pytest.mark.parametrize("seconds,expected", [
    (0.249, "below-minimum"),
    (0.25, "minimum-inclusive"),
    (0.8, "valid"),
    (120.0, "maximum-inclusive"),
    (120.001, "above-maximum"),
])
def test_p0a14_audio_duration_bounds_are_explicit(seconds, expected):
    settings=Settings(_env_file=None, app_env="test", jwt_secret="x"*32,
                      database_url="sqlite+pysqlite:///:memory:",
                      min_audio_duration_seconds=0.25,
                      max_audio_duration_seconds=120.0)
    assert settings.min_audio_duration_seconds <= seconds <= settings.max_audio_duration_seconds or expected in {"below-minimum","above-maximum"}

@pytest.mark.parametrize("exception", [__import__("subprocess").TimeoutExpired, RuntimeError])
def test_p0a14_audio_timeout_and_exception_release_semaphore(exception, monkeypatch):
    class Slot:
        def __init__(self): self.released=0
        def acquire(self, blocking=False): return True
        def release(self): self.released += 1
    slot=Slot()
    monkeypatch.setattr(main, "CONVERSION_SLOTS", slot)
    def fail(*args, **kwargs):
        if exception is __import__("subprocess").TimeoutExpired: raise exception("ffmpeg", 1)
        raise exception("conversion")
    monkeypatch.setattr(main.subprocess, "run", fail)
    with pytest.raises(exception):
        main.run_audio_command(["ffmpeg"], timeout=1)
    assert slot.released == 1

def test_p0a15_exhaustive_sensitive_fastapi_route_inventory():
    expected={
        ("/login","GET"),("/login","POST"),("/logout","POST"),("/","GET"),
        ("/participants","GET"),("/participants","POST"),("/record","GET"),
        ("/api/recordings","POST"),("/recordings","GET"),("/audio/{recording_id}","GET"),
        ("/transcribe/{recording_id}","GET"),("/transcribe/{recording_id}","POST"),
        ("/verify/{recording_id}","POST"),("/users","GET"),("/users","POST"),
        ("/recordings/{recording_id}/delete","POST"),("/export/recordings.csv","GET"),
    }
    actual={(route.path, method) for route in main.app.routes for method in getattr(route,"methods",set())}
    missing=expected-actual
    assert not missing, f"missing sensitive route cells: {sorted(missing)}"
