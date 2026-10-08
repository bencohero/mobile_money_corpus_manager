import os
import importlib
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.auth import verify_password
from app.db import Base, SessionLocal
from app.models import AuditLog, Participant, User, Workshop, WorkshopCode
from app.participant_registration import (
    RegistrationError,
    format_login_id,
    register_participant,
    workshop_code_hash,
)


def payload(code="workshop-secret", password="correct horse battery staple", **participant):
    fields = {"language": "mos", "age_group": "25-34", "gender": "F", "region": "Centre", "consent_obtained": True}
    fields.update(participant)
    return {"workshop_code": code, "password": password, "password_confirmation": password, "participant": fields}


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        admin = User(username="admin-unit", password_hash="unused", role="ADMIN")
        db.add(admin); db.flush()
        workshop = Workshop(name="Unit workshop")
        db.add(workshop); db.flush()
        db.add(WorkshopCode(workshop_id=workshop.id, label="Unit", code_hash=workshop_code_hash("workshop-secret"), created_by_user_id=admin.id))
        db.commit()
        yield db


@pytest.mark.parametrize("number,expected", [(1, "MOS_001"), (2, "MOS_002"), (9, "MOS_009"), (10, "MOS_010"), (99, "MOS_099"), (100, "MOS_100"), (999, "MOS_999"), (1000, "MOS_1000")])
def test_identifier_format_boundaries(number, expected):
    assert format_login_id(number) == expected
    assert re.fullmatch(r"MOS_[0-9]{3,}", expected)


def test_registration_creates_atomic_link_and_secure_password(sqlite_session):
    result = register_participant(sqlite_session, payload(), number_allocator=lambda _: 1)
    assert result.login_id == "MOS_001"
    user = sqlite_session.get(User, result.user_id)
    participant = sqlite_session.get(Participant, result.participant_id)
    assert user.role == "PARTICIPANT" and user.is_active
    assert user.participant_id == participant.id
    assert user.username == participant.participant_code == "MOS_001"
    assert user.password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", user.password_hash)
    assert sqlite_session.query(WorkshopCode).one().use_count == 1


@pytest.mark.parametrize("field,value", [("role", "admin"), ("role", "validator"), ("role", "transcriber"), ("is_superuser", True), ("is_active", True), ("permissions", ["admin"]), ("username", "MOS_999"), ("sequence_number", 999)])
def test_public_identity_and_privilege_fields_are_rejected(sqlite_session, field, value):
    body = payload(); body[field] = value
    with pytest.raises(RegistrationError, match="interdits"):
        register_participant(sqlite_session, body, number_allocator=lambda _: 1)
    assert sqlite_session.query(Participant).count() == 0


@pytest.mark.parametrize("change", [
    {"workshop_code": "wrong"},
    {"workshop_code": ""},
    {"password_confirmation": "different password"},
    {"password": "short", "password_confirmation": "short"},
])
def test_invalid_registration_has_no_partial_rows(sqlite_session, change):
    body = payload(); body.update(change)
    with pytest.raises(RegistrationError):
        register_participant(sqlite_session, body, number_allocator=lambda _: 1)
    assert sqlite_session.query(Participant).count() == 0
    assert sqlite_session.query(User).filter_by(role="PARTICIPANT").count() == 0
    assert sqlite_session.query(WorkshopCode).one().use_count == 0


def test_constraint_failure_rolls_back_participant_and_workshop_usage(sqlite_session):
    sqlite_session.add(User(username="MOS_001", password_hash="existing", role="TRANSCRIBER")); sqlite_session.commit()
    with pytest.raises(RegistrationError):
        register_participant(sqlite_session, payload(), number_allocator=lambda _: 1)
    assert sqlite_session.query(Participant).count() == 0
    assert sqlite_session.query(WorkshopCode).one().use_count == 0


@pytest.mark.parametrize("state", ["inactive", "future", "expired", "full"])
def test_workshop_state_is_enforced(sqlite_session, state):
    workshop = sqlite_session.query(WorkshopCode).one()
    now = datetime.utcnow()
    if state == "inactive": workshop.is_active = False
    if state == "future": workshop.starts_at = now + timedelta(hours=1)
    if state == "expired": workshop.expires_at = now
    if state == "full": workshop.max_registrations = 1; workshop.use_count = 1
    sqlite_session.commit()
    with pytest.raises(RegistrationError, match="code d'atelier"):
        register_participant(sqlite_session, payload(), now=now, number_allocator=lambda _: 1)


def _postgres_available():
    return os.environ.get("DATABASE_URL", "").startswith("postgresql")


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL migration test")
def test_migration_initializes_sequence_after_historical_mos_identifier():
    engine = create_engine(os.environ["DATABASE_URL"])
    schema = "registration_history_" + uuid.uuid4().hex
    migration = importlib.import_module("migrations.versions.0004_participant_self_registration")
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        connection.execute(text("CREATE TABLE participants (id integer PRIMARY KEY, participant_code varchar(30) NOT NULL UNIQUE)"))
        connection.execute(text("CREATE TABLE users (id integer PRIMARY KEY, username varchar(80) NOT NULL UNIQUE, participant_id integer REFERENCES participants(id))"))
        connection.execute(text("INSERT INTO participants VALUES (1, 'MOS_999')"))
        connection.execute(text("INSERT INTO users VALUES (1, 'MOS_999', 1)"))
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            migration.upgrade()
        assert connection.execute(text("SELECT nextval('participant_login_number_seq')")).scalar_one() == 1000
        assert connection.execute(text("SELECT count(*) FROM workshop_codes")).scalar_one() == 0
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL concurrency test")
@pytest.mark.parametrize("count", [10, 30, 50])
def test_concurrent_registrations_are_unique_and_complete(monkeypatch, count):
    import app.participant_registration as service
    monkeypatch.setattr(service, "hash_password", lambda value: "test-hash-" + str(len(value)))
    code = "concurrency-" + uuid.uuid4().hex
    with SessionLocal() as db:
        admin = db.query(User).filter_by(role="ADMIN").first()
        business_workshop = Workshop(name="Concurrency " + code)
        db.add(business_workshop); db.flush()
        workshop = WorkshopCode(workshop_id=business_workshop.id, label="Concurrency", code_hash=workshop_code_hash(code), max_registrations=count, created_by_user_id=admin.id)
        db.add(workshop); db.commit(); workshop_id = workshop.id; business_workshop_id = business_workshop.id

    def create_one(_):
        with SessionLocal() as db:
            return register_participant(db, payload(code=code, region=""))

    with ThreadPoolExecutor(max_workers=count) as pool:
        results = list(pool.map(create_one, range(count)))
    login_ids = [result.login_id for result in results]
    assert len(set(login_ids)) == count
    assert all(re.fullmatch(r"MOS_[0-9]{3,}", value) for value in login_ids)
    with SessionLocal() as db:
        workshop = db.get(WorkshopCode, workshop_id)
        assert workshop.use_count == count
        user_ids = [result.user_id for result in results]
        participant_ids = [result.participant_id for result in results]
        assert db.query(User).filter(User.id.in_(user_ids), User.participant_id.is_(None)).count() == 0
        db.query(AuditLog).filter(AuditLog.user_id.in_(user_ids)).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        db.query(Participant).filter(Participant.id.in_(participant_ids)).delete(synchronize_session=False)
        db.delete(workshop); db.delete(db.get(Workshop, business_workshop_id)); db.commit()


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL concurrency test")
def test_last_workshop_place_cannot_be_oversubscribed(monkeypatch):
    import app.participant_registration as service
    monkeypatch.setattr(service, "hash_password", lambda _: "test-hash")
    code = "last-place-" + uuid.uuid4().hex
    with SessionLocal() as db:
        admin = db.query(User).filter_by(role="ADMIN").first()
        business_workshop = Workshop(name="Last place " + code)
        db.add(business_workshop); db.flush()
        workshop = WorkshopCode(workshop_id=business_workshop.id, label="Last place", code_hash=workshop_code_hash(code), max_registrations=1, created_by_user_id=admin.id)
        db.add(workshop); db.commit(); workshop_id = workshop.id; business_workshop_id = business_workshop.id
    barrier = threading.Barrier(10)
    def attempt(_):
        barrier.wait()
        try:
            with SessionLocal() as db:
                return register_participant(db, payload(code=code, region=""))
        except RegistrationError:
            return None
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(attempt, range(10)))
    successful = [result for result in results if result]
    assert len(successful) == 1
    result = successful[0]
    with SessionLocal() as db:
        assert db.get(WorkshopCode, workshop_id).use_count == 1
        db.query(AuditLog).filter_by(user_id=result.user_id).delete()
        db.query(User).filter_by(id=result.user_id).delete()
        db.query(Participant).filter_by(id=result.participant_id).delete()
        db.query(WorkshopCode).filter_by(id=workshop_id).delete(); db.delete(db.get(Workshop, business_workshop_id)); db.commit()
