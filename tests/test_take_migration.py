"""Migration rehearsal inside a transaction-local schema on db-test only."""
import importlib
import uuid

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect, text

from app.db import engine


@pytest.mark.parametrize("drift", [False, True])
def test_upgrade_preserves_history_and_repairs_stamped_schema(drift):
    assert engine.url.host == "db-test" and engine.url.database == "p0a2_test"
    with engine.connect() as conn:
        transaction = conn.begin()
        try:
            schema = "seq_migration_" + uuid.uuid4().hex
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            ctx = MigrationContext.configure(conn)
            with Operations.context(ctx):
                importlib.import_module("migrations.versions.0001_initial").upgrade()
                importlib.import_module("migrations.versions.0002_p0a_recording_sync").upgrade()
                conn.execute(text("CREATE TABLE alembic_version (version_num varchar(32) PRIMARY KEY)"))
                conn.execute(text("INSERT INTO alembic_version VALUES ('0002_p0a_recording_sync')"))
                if drift:
                    conn.execute(text("ALTER TABLE recordings DROP CONSTRAINT uq_recording_take"))
                    conn.execute(text("ALTER TABLE recordings ADD CONSTRAINT uq_recording_take UNIQUE (participant_id,utterance_id,take_number)"))
                conn.execute(text("INSERT INTO participants (id,participant_code,created_at) VALUES (1,'synthetic',now())"))
                conn.execute(text("INSERT INTO utterances (id,utterance_code,intent,scenario_fr) VALUES (1,'U','I','S')"))
                conn.execute(text("INSERT INTO recordings (audio_id,participant_id,utterance_id,take_number,condition,raw_object,wav_object,created_at) VALUES ('old',1,1,8,'CLEAN','raw/old','wav/old',now())"))
                importlib.import_module("migrations.versions.0003_take_sequences").upgrade()
            assert conn.execute(text("SELECT take_number,raw_object FROM recordings")).one() == (8, "raw/old")
            assert conn.execute(text("SELECT last_take_number FROM recording_take_counters")).scalar_one() == 8
            constraints = inspect(conn).get_unique_constraints("recordings", schema=schema)
            assert next(c["column_names"] for c in constraints if c["name"] == "uq_recording_take") == ["participant_id", "utterance_id", "condition", "take_number"]
            checks = inspect(conn).get_check_constraints("recordings", schema=schema)
            assert any(c["name"] == "ck_recordings_take_range" and "999" in c["sqltext"] for c in checks)
        finally:
            transaction.rollback()
