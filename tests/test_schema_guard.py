import pytest

import app.schema_guard as guard


class _ScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


class _DB:
    def __init__(self, revisions):
        self.revisions = revisions

    def execute(self, _statement):
        return _ScalarResult(self.revisions)


def test_schema_guard_rejects_stale_database(monkeypatch):
    monkeypatch.setattr(guard, "migration_heads", lambda: ("0004_participant_registration",))
    with pytest.raises(guard.SchemaRevisionError, match="Current revision: 0002_p0a_recording_sync"):
        guard.assert_schema_current(_DB(["0002_p0a_recording_sync"]))


def test_schema_guard_accepts_current_database(monkeypatch):
    monkeypatch.setattr(guard, "migration_heads", lambda: ("0004_participant_registration",))
    guard.assert_schema_current(_DB(["0004_participant_registration"]))
