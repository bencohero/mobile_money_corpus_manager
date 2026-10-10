from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import main


class FakeDB:
    def __init__(self, recording=None, fail=False):
        self.recording = recording
        self.fail = fail
        self.get_calls = 0
        self.commit_calls = 0

    def execute(self, _statement):
        if self.fail:
            raise RuntimeError("database unavailable")
        return object()

    def get(self, *_args):
        self.get_calls += 1
        return self.recording

    def commit(self):
        self.commit_calls += 1


def test_liveness_does_not_require_dependencies():
    assert main.health() == {"status": "ok"}


def test_readiness_requires_database_and_minio(monkeypatch):
    monkeypatch.setattr(main, "check_ready", lambda: True)
    assert main.readiness(FakeDB()) == {"status": "ready"}

    monkeypatch.setattr(main, "check_ready", lambda: False)
    with pytest.raises(HTTPException) as error:
        main.readiness(FakeDB())
    assert error.value.status_code == 503

    with pytest.raises(HTTPException) as error:
        main.readiness(FakeDB(fail=True))
    assert error.value.status_code == 503


def _recording():
    return SimpleNamespace(
        id=7,
        sync_status="READY",
        status="TRANSCRIBED",
        transcription=SimpleNamespace(
            verification_status="PENDING",
            verifier_id=None,
            verifier_comment=None,
        ),
    )


@pytest.mark.parametrize("decision", ["", "UNKNOWN", "verified", "NEEDS_REVIEW ", "VERIFIED\n"])
def test_invalid_verification_decision_is_rejected_without_mutation(monkeypatch, decision):
    recording = _recording()
    db = FakeDB(recording)
    monkeypatch.setattr(main, "require", lambda *_args, **_kwargs: SimpleNamespace(id=99, role="VALIDATOR"))
    monkeypatch.setattr(main, "check_csrf", lambda *_args, **_kwargs: None)

    with pytest.raises(HTTPException) as error:
        main.verify(7, SimpleNamespace(), decision, "new comment", "csrf", db)

    assert error.value.status_code == 400
    assert db.get_calls == 0
    assert db.commit_calls == 0
    assert recording.status == "TRANSCRIBED"
    assert recording.transcription.verification_status == "PENDING"
    assert recording.transcription.verifier_id is None
    assert recording.transcription.verifier_comment is None


@pytest.mark.parametrize("decision,expected", [
    ("VERIFIED", ("VERIFIED", "VERIFIED")),
    ("NEEDS_REVIEW", ("NEEDS_REVIEW", "NEEDS_REVIEW")),
    ("REJECTED", ("REJECTED", "REJECTED")),
])
def test_valid_verification_decisions_update_expected_state(monkeypatch, decision, expected):
    recording = _recording()
    db = FakeDB(recording)
    monkeypatch.setattr(main, "require", lambda *_args, **_kwargs: SimpleNamespace(id=99, role="VALIDATOR"))
    monkeypatch.setattr(main, "check_csrf", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(main, "audit", lambda *_args, **_kwargs: None)

    response = main.verify(7, SimpleNamespace(), decision, "comment", "csrf", db)

    assert response.status_code == 303
    assert (recording.status, recording.transcription.verification_status) == expected
    assert recording.transcription.verifier_id == 99
    assert recording.transcription.verifier_comment == "comment"
    assert db.commit_calls == 1
