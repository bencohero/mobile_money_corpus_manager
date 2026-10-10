import re

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Participant, ParticipantLanguageSequence, ParticipantRegistrationRequest, User, Workshop, WorkshopCode
from app.participant_registration import register_participant, workshop_code_hash


def multilingual_payload(code, key, language="mos"):
    return {
        "workshop_code": code,
        "idempotency_key": key,
        "password": "correct horse battery staple",
        "password_confirmation": "correct horse battery staple",
        "participant": {"language": language, "age_group": "25-34", "gender": "F", "region": "Centre", "consent_obtained": True},
    }


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        admin = User(username="identity-admin", password_hash="unused", role="ADMIN")
        db.add(admin)
        db.flush()
        workshop = Workshop(name="Bootstrap workshop", language_code="MOS")
        db.add(workshop)
        db.flush()
        db.add(WorkshopCode(workshop_id=workshop.id, label="Bootstrap", code_hash=workshop_code_hash("workshop-secret"), created_by_user_id=admin.id))
        db.commit()
        yield db


def add_workshop(db, admin, name, language, code):
    workshop = Workshop(name=name, language_code=language)
    db.add(workshop)
    db.flush()
    db.add(WorkshopCode(workshop_id=workshop.id, label=name, code_hash=workshop_code_hash(code), created_by_user_id=admin.id))
    db.commit()
    return workshop


def test_language_sequences_are_independent_and_shared(sqlite_session):
    admin = sqlite_session.query(WorkshopCode).one().created_by
    fr = add_workshop(sqlite_session, admin, "Français", "FR", "fr-code")
    mos = add_workshop(sqlite_session, admin, "Moore", "MOS", "mos-code")
    fr_result = register_participant(sqlite_session, multilingual_payload("fr-code", "fr-1", "fr"))
    mos_result = register_participant(sqlite_session, multilingual_payload("mos-code", "mos-1"))
    fr_result_2 = register_participant(sqlite_session, multilingual_payload("fr-code", "fr-2", "fr"))
    assert fr_result.login_id == "FR_001"
    assert mos_result.login_id == "MOS_001"
    assert fr_result_2.login_id == "FR_002"
    assert sqlite_session.get(Participant, fr_result.participant_id).workshop_id == fr.id
    assert sqlite_session.get(ParticipantLanguageSequence, "MOS").last_number == 1


def test_registration_idempotency_returns_same_identity(sqlite_session):
    admin = sqlite_session.query(WorkshopCode).one().created_by
    add_workshop(sqlite_session, admin, "Idempotent", "DYU", "dyu-code")
    body = multilingual_payload("dyu-code", "same-request", "dyu")
    first = register_participant(sqlite_session, body)
    second = register_participant(sqlite_session, body)
    assert second == first
    assert sqlite_session.query(Participant).count() == 1
    assert sqlite_session.query(ParticipantRegistrationRequest).count() == 1


def test_unknown_historical_workshop_requires_explicit_attribution(sqlite_session):
    admin = sqlite_session.query(WorkshopCode).one().created_by
    workshop = add_workshop(sqlite_session, admin, "Historique", "MOS", "historical-code")
    workshop.language_code = None
    sqlite_session.commit()
    with pytest.raises(ValueError, match="attribuée"):
        register_participant(sqlite_session, multilingual_payload("historical-code", "historical-1"))


def test_client_language_is_ignored_and_workshop_language_wins(sqlite_session):
    admin = sqlite_session.query(WorkshopCode).one().created_by
    add_workshop(sqlite_session, admin, "Mooré only", "MOS", "mos-only")
    result = register_participant(sqlite_session, multilingual_payload("mos-only", "mos-only-1", "fr"))
    participant = sqlite_session.get(Participant, result.participant_id)
    assert result.login_id == "MOS_001"
    assert participant.language == "mos"
