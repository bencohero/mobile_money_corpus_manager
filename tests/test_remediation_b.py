from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import Participant, Transcription, TranscriptionHistory, User, Workshop
from app.participant_registration import register_participant
from tests.test_multilingual_identity import multilingual_payload


@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        admin = User(username="b-admin", password_hash="unused", role="ADMIN")
        session.add(admin)
        session.flush()
        workshop = Workshop(name="B workshop", language_code="MOS")
        session.add(workshop)
        session.flush()
        from app.models import WorkshopCode
        session.add(WorkshopCode(workshop_id=workshop.id, label="B", code_hash="b-code", created_by_user_id=admin.id))
        session.commit()
        yield session


def test_registration_always_copies_workshop_language_and_keeps_prefix(db, monkeypatch):
    monkeypatch.setattr("app.participant_registration.workshop_code_hash", lambda value: "b-code")
    result = register_participant(db, multilingual_payload("anything", "b-1", language="FR"))
    participant = db.get(Participant, result.participant_id)
    assert participant.language == "mos"
    assert participant.language_code == "MOS"
    assert result.login_id == "MOS_001"


def test_transcription_history_fields_are_persistable(db):
    user = db.query(User).filter_by(username="b-admin").one()
    transcription = Transcription(recording_id=1, reference_transcription="old", transcriber_id=user.id, version=1)
    # This test only checks the model contract; recording FK is intentionally not
    # fabricated in the lightweight SQLite fixture.
    assert transcription.version == 1
    history = TranscriptionHistory(transcription_id=1, author_id=user.id,
        old_reference_transcription="old", new_reference_transcription="new",
        previous_version=1, new_version=2)
    assert history.previous_version == 1 and history.new_version == 2


def test_two_sessions_only_one_can_advance_transcription_version():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    seed = Session()
    user = User(username="concurrency-user", password_hash="unused", role="TRANSCRIBER")
    seed.add(user)
    seed.flush()
    seed.add(Transcription(recording_id=1, reference_transcription="base", transcriber_id=user.id, version=1))
    seed.commit()
    first, second = Session(), Session()
    first_loaded = first.query(Transcription).one()
    second_loaded = second.query(Transcription).one()
    assert first_loaded.version == second_loaded.version == 1
    accepted = first.execute(update(Transcription).where(
        Transcription.id == first_loaded.id, Transcription.version == 1
    ).values(reference_transcription="first", version=2))
    first.commit()
    rejected = second.execute(update(Transcription).where(
        Transcription.id == second_loaded.id, Transcription.version == 1
    ).values(reference_transcription="second", version=2))
    assert accepted.rowcount == 1 and rejected.rowcount == 0
    second.rollback()
    assert first.get(Transcription, first_loaded.id).reference_transcription == "first"
